"""Quasi-static 2D finite-volume differential impedance sensitivity study.

Solve div(epsilon grad V)=0 with the pair at +0.5/-0.5 V. Solve the identical
geometry in vacuum. Cdiff=2U/Vdiff^2; Zdiff=1/(c sqrt(Cdiff*Cdiff_vacuum)).
Exact odd-mode for symmetric sections; an energy-based differential estimate
for asymmetric sections, which may also convert differential/common modes.
Metal is perfect; signal cross sections optionally use the stated etch taper.
Other metal is rectangular. Floating foreign conductors have zero
net charge. Crossings are treated as longitudinally uniform 2D sections, not
their real finite 3D extent. No loss, etch, roughness, vias, masks, pads or ESD.
"""
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

OUT = Path(__file__).resolve().parent
EPS0 = 8.8541878188e-12
C0 = 299792458.

def mesh_axis(bounds, fine, focused):
    """Aligned coordinate nodes; fine spacing close to every metal edge."""
    bounds = sorted(set(round(float(v),10) for v in bounds))
    values=[]
    for a,b in zip(bounds,bounds[1:]):
        middle=(a+b)/2
        step=fine if focused(middle) else max(fine,.025)
        values.extend(np.linspace(a,b,max(1,math.ceil((b-a)/step))+1)[:-1])
    return np.r_[values,bounds[-1]]

def solve(config, fine=.005, halfspan=2.5, vacuum=False, retain=False):
    # rect=(left,right,top,bottom,label), dimensions mm. Labels: 0 GND,
    # 1 D+, 2 D-, >=3 isolated floating conductor net.
    rects=config['rects']; ylo,yhi=config['extent_y']; dielectric=config['dielectric']
    xedges=[v for r in rects for v in r[:2] if -halfspan<v<halfspan]
    yedges=[v for r in rects for v in r[2:4]]+[v for slab in dielectric for v in slab[:2]]
    xbounds=[-halfspan,halfspan,-.6,.6]+xedges
    ybounds=[ylo,yhi]+yedges
    # Keep high resolution at all metal surfaces, not just at the signal pair.
    for edge in xedges:
        xbounds += [max(-halfspan,edge-.035),min(halfspan,edge+.035)]
    for edge in yedges:
        ybounds += [max(ylo,edge-.035),min(yhi,edge+.035)]
    x=mesh_axis(xbounds,fine,lambda q: abs(q)<.6 or any(abs(q-e)<.036 for e in xedges))
    y=mesh_axis(ybounds,fine,lambda q: any(abs(q-e)<.036 for e in yedges))
    nx,ny=len(x),len(y);xx,yy=np.meshgrid(x,y)
    label=np.full((ny,nx),-1,dtype=int)
    for left,right,top,bottom,net in rects:
        etch = config.get('signal_top_width_reduction_mm',0) if net in (1,2) else 0
        taper = etch/2*np.clip((bottom-yy)/(bottom-top),0,1) if bottom>top else 0
        mask=(xx>=left+taper-1e-9)&(xx<=right-taper+1e-9)&(yy>=top-1e-9)&(yy<=bottom+1e-9)
        collision=mask&(label>=0)&(label!=net)
        assert not collision.any(), 'Overlapping conductor labels'
        label[mask]=net
    # Full reference planes top/bottom; finite-domain grounded side walls.
    label[0,:]=config.get('top_label',0)
    label[-1,:]=config.get('bottom_label',0)
    if config.get('ground_side_walls',True):label[:,0]=label[:,-1]=0
    dx=np.diff(x);dy=np.diff(y)
    dualx=np.r_[dx[0]/2,(dx[:-1]+dx[1:])/2,dx[-1]/2]
    dualy=np.r_[dy[0]/2,(dy[:-1]+dy[1:])/2,dy[-1]/2]
    def er_integral(a,b):
        if vacuum:return b-a
        return sum(max(0,min(b,z)-max(a,s))*er for s,z,er in dielectric)
    ya=np.r_[y[0],(y[:-1]+y[1:])/2];yz=np.r_[(y[:-1]+y[1:])/2,y[-1]]
    face_er_dy=np.array([er_integral(a,b) for a,b in zip(ya,yz)])
    midpoint_er=np.array([1. if vacuum else sum(er for a,b,er in dielectric if a-1e-10<(p+q)/2<b+1e-10) for p,q in zip(y[:-1],y[1:])])
    assert np.all(midpoint_er>0)
    gh=EPS0*face_er_dy[:,None]/dx[None,:]
    gv=EPS0*midpoint_er[:,None]*dualx[None,:]/dy[:,None]
    ids=np.arange(nx*ny).reshape(ny,nx)
    a=np.r_[ids[:,:-1].ravel(),ids[:-1,:].ravel()]
    z=np.r_[ids[:,1:].ravel(),ids[1:,:].ravel()]
    g=np.r_[gh.ravel(),gv.ravel()]
    labs=label.ravel(); free=np.flatnonzero(labs<0)
    unknown=np.full(nx*ny,-1,dtype=int);unknown[free]=np.arange(len(free))
    count=len(free)
    for net in sorted(set(labs[labs>=3])):
        unknown[labs==net]=count;count+=1
    voltage=np.zeros(nx*ny);voltage[labs==1]=.5;voltage[labs==2]=-.5
    ua,uz=unknown[a],unknown[z]
    active=~((ua>=0)&(ua==uz));a,z,g,ua,uz=(v[active] for v in (a,z,g,ua,uz))
    rows=[];cols=[];vals=[];rhs=np.zeros(count)
    for u,v,other in [(ua,uz,z),(uz,ua,a)]:
        good=u>=0
        rows.append(u[good]);cols.append(u[good]);vals.append(g[good])
        both=good&(v>=0)
        rows.append(u[both]);cols.append(v[both]);vals.append(-g[both])
        fixed=good&(v<0)
        np.add.at(rhs,u[fixed],g[fixed]*voltage[other[fixed]])
    matrix=coo_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(count,count)).tocsr()
    solution=spsolve(matrix,rhs)
    voltage[unknown>=0]=solution[unknown[unknown>=0]]
    diff=voltage[a]-voltage[z]
    # Sum edge epsilon*E^2 volume = 2U. For 1 V differential excitation,
    # this is Cdiff. Geometric units cancel since both coordinates use mm.
    capacitance=float(np.dot(g,diff*diff))
    charge={}
    for net in sorted(set(labs[labs>=0])):
        charge[str(net)]=float(np.sum((labs[a]==net)*g*diff)-np.sum((labs[z]==net)*g*diff))
    residual=float(np.max(np.abs(matrix@solution-rhs)))
    answer=dict(capacitance_F_per_m=capacitance,nodes=int(nx*ny),unknowns=count,
                max_residual_C_per_m=residual,charge_C_per_m=charge)
    if retain:answer.update(x=x,y=y,voltage=voltage.reshape(ny,nx),labels=label)
    return answer

def impedance(config, fine=.005, halfspan=2.5):
    start=time.monotonic();actual=solve(config,fine,halfspan);vac=solve(config,fine,halfspan,vacuum=True)
    return dict(name=config['name'],mesh_mm=fine,halfspan_mm=halfspan,
                differential_ohm=1/(C0*math.sqrt(actual['capacitance_F_per_m']*vac['capacitance_F_per_m'])),
                effective_er=actual['capacitance_F_per_m']/vac['capacitance_F_per_m'],
                dielectric=actual,vacuum=vac,elapsed_s=time.monotonic()-start)

def ideal(name, top_gap, bottom_gap, er_top, er_bottom, width=.17, gap=.127, thickness=.0152, coplanar=None):
    top=top_gap;bottom=top+thickness;end=bottom+bottom_gap
    rects=[(-gap/2-width,-gap/2,top,bottom,1),(gap/2,gap/2+width,top,bottom,2)]
    if coplanar is not None:
        rects += [(-5,-gap/2-width-coplanar,top,bottom,0),(gap/2+width+coplanar,5,top,bottom,0)]
    return dict(name=name,rects=rects,extent_y=(0,end),dielectric=[(0,bottom,er_top),(bottom,end,er_bottom)])

def main():
    sections=json.loads((OUT/'sections.json').read_text())
    cases=[]
    cases.append(ideal('CAD ideal solid In2/In4 planes',.1532,.5500,4.16,4.6))
    remote=ideal('CAD ideal In2 absent; solid In1/In4 planes',.1532+.0152+.55,.55,4.16,4.6)
    # Preserve actual upper core dielectric instead of assigning all Er=4.16.
    remote['dielectric']=[(0,.55,4.6),(.55,.55+.0152+.1532+.0152,4.16),(.55+.0152+.1532+.0152,remote['extent_y'][1],4.6)]
    cases.append(remote)
    cases.append(ideal('JLC3313 standard ideal planes at current width',.1088,.55,4.16,4.6))
    cases.append(ideal('JLC3313 standard ideal planes at synthesized 0.1171 width',.1088,.55,4.16,4.6,width=.1171))
    # Real local GND/foreign-net intervals on In2 and In3. Remote reference
    # planes are deliberately idealized as solid In1/In4 for this sensitivity.
    for section in sections['sections']:
        for foreign in ['floating','AC-grounded']:
            config=dict(name=f"CAD slice y={section['y_mm']:.1f}, foreign nets {foreign}",
                        extent_y=remote['extent_y'],dielectric=remote['dielectric'],rects=[])
            netlabels={'GND':0,'USB_DP':1,'USB_DN':2};nextlabel=3
            for layer,top in [('In2.Cu',.55),('In3.Cu',.55+.0152+.1532)]:
                for net,intervals in section['copper'][layer].items():
                    if net not in netlabels:
                        netlabels[net]=0 if foreign=='AC-grounded' else nextlabel
                        nextlabel+=1
                    for left,right in intervals:
                        config['rects'].append((left,right,top,top+.0152,netlabels[net]))
            cases.append(config)
    (OUT/'model-input.json').write_text(json.dumps(dict(source_sha256=sections['sha256'],method=__doc__,cases=cases),indent=2))
    results=[]
    for i,case in enumerate(cases):
        for fine in ([.010,.005,.0025] if i<4 else [.005,.0025]):
            answer=impedance(case,fine);results.append(answer)
            print(case['name'],fine,round(answer['differential_ohm'],3),flush=True)
            (OUT/'results.json').write_text(json.dumps(dict(source_sha256=sections['sha256'],method=__doc__,results=results),indent=2))
    # Domain-width convergence on the two ideal CAD cases.
    domain=[impedance(cases[i],.0025,halfspan=4.) for i in [0,1]]
    (OUT/'domain-convergence.json').write_text(json.dumps(domain,indent=2))

def validation_and_etch():
    checks=[]
    # Analytic parallel plates with homogeneous and series dielectrics;
    # insulated sides remove fringing and give exact independent references.
    for dielectric in [[(0,.2,4.6)],[(0,.08,4.),(.08,.2,2.)]]:
        config=dict(name='parallel plate analytic check',rects=[],extent_y=(0,.2),
                    dielectric=dielectric,top_label=1,bottom_label=2,ground_side_walls=False)
        actual=solve(config,.005,halfspan=1.)
        expected=EPS0*2./sum((b-a)/er for a,b,er in dielectric)
        relative=abs(actual['capacitance_F_per_m']/expected-1)
        assert relative<1e-8
        checks.append(dict(dielectric=dielectric,expected_F_per_m=expected,
                           calculated_F_per_m=actual['capacitance_F_per_m'],relative_error=relative))
    cases=json.loads((OUT/'model-input.json').read_text())['cases']
    # JLC states top width = base width - 0.7 mil. Treat that as a
    # trapezoidal signal-only sensitivity; real copper edges are unmeasured.
    etch=[]
    for i,case in enumerate(cases):
        case['signal_top_width_reduction_mm']=.7*.0254
        for fine in ([.0025,.00125] if i<4 else [.0025]):
            result=impedance(case,fine);result['top_width_reduction_mm']=.7*.0254
            etch.append(result)
            print('ETCH',case['name'],fine,round(result['differential_ohm'],3),flush=True)
            (OUT/'etch-sensitivity.json').write_text(json.dumps(etch,indent=2))
    (OUT/'numerical-validation.json').write_text(json.dumps(checks,indent=2))

if __name__=='__main__':
    import sys
    validation_and_etch() if '--etch' in sys.argv else main()
