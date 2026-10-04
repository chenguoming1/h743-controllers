#!/usr/bin/python3
"""Read-only P3 U11 NAND copper/mask/paste/package audit; never saves the board."""
import os
os.environ.setdefault('XDG_CONFIG_HOME','/tmp/u11-kicad-config')
os.environ.setdefault('MPLCONFIGDIR','/tmp/u11-mpl-config')
import csv, hashlib, itertools, json, math, pathlib, re
import pcbnew as p
import numpy as np
from scipy.integrate import quad
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon, Patch
from matplotlib.path import Path

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BOARD=ROOT/'controller-r3s-green/controller.kicad_pcb'
EXPECTED='0850991d8aacd22138487804c24eefbae634a21ba218c18196f13fad795c3696'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(BOARD)==EXPECTED
b=p.LoadBoard(str(BOARD)); f=next(f for f in b.GetFootprints() if f.GetReference()=='U11')
mm=p.ToMM;cx,cy=mm(f.GetPosition().x),mm(f.GetPosition().y)
assert np.allclose([cx,cy,f.GetOrientationDegrees()],[20.55,20.375,180])
gerbers=ROOT/'controller-r3s-green/release/single-board-gerbers'
def rr_area(l,w,r):return l*w-(4-math.pi)*r*r
def overlap(D,L,W,shape='rectangular'):
    outer=D/2;inner=outer-L;r=.125
    def width(y):
        span=.2+math.sqrt(max(0,r*r-max(0,abs(y)-.125)**2))
        li=inner if shape=='rectangular' else inner+W/2-math.sqrt(max(0,(W/2)**2-y*y))
        return max(0,min(3.75+span,outer)-max(3.75-span,li))
    knots=sorted(set([-W/2,W/2]+[v for v in [-.125,0,.125] if -W/2<v<W/2]))
    area=sum(quad(width,a,z,epsabs=1e-12,epsrel=1e-11)[0] for a,z in zip(knots,knots[1:]))
    la=L*W-(0 if shape=='rectangular' else (2-math.pi/2)*(W/2)**2)
    return dict(intersection_mm2=area,lead_area_mm2=la,overlap_ratio=area/la,toe_mm=4.075-outer,heel_mm=inner-3.425,side_mm=(.5-W)/2)

cases=[dict(D_mm=D,L_mm=L,b_mm=W,shape=S,**overlap(D,L,W,S)) for D,L,W,S in itertools.product([7.9,8,8.1],[.45,.5,.55],[.35,.4,.48],['rectangular','round_inner_assumption'])]
named={name:dict(D_mm=D,L_mm=L,b_mm=W,shape=S,**overlap(D,L,W,S)) for name,D,L,W,S in [
 ('nominal_rectangular',8,.5,.4,'rectangular'),('maximum_lead_minimum_body_rectangular',7.9,.55,.48,'rectangular'),
 ('maximum_lead_nominal_body_rectangular',8,.55,.48,'rectangular'),('maximum_lead_maximum_body_rectangular',8.1,.55,.48,'rectangular'),
 ('nominal_round_inner',8,.5,.4,'round_inner_assumption'),('maximum_lead_minimum_body_round_inner',7.9,.55,.48,'round_inner_assumption')]}

def parse_flashes(path):
    aps={};flashes=[];ap=None;component=None;pin=None
    for line in path.read_text().splitlines():
        m=re.fullmatch(r'%ADD(\d+)([^,]+),(.+)\*%',line)
        if m:aps[int(m[1])]={'type':m[2],'parameters':[float(v) for v in m[3].split('X')],'source':line}
        m=re.fullmatch(r'D(\d+)\*',line)
        if m:ap=int(m[1])
        m=re.fullmatch(r'%TO.P,([^,]+),([^*]+)\*%',line)
        if m:component,pin=m[1],m[2]
        m=re.fullmatch(r'%TO.C,([^*]+)\*%',line)
        if m:component=m[1];pin=None
        if line=='%TD*%':component=pin=None
        m=re.fullmatch(r'X(-?\d+)Y(-?\d+)D03\*',line)
        if m and component=='U11':flashes.append(dict(aperture=ap,pin=pin,xy_mm=[int(m[1])/1e6,int(m[2])/1e6]))
    return aps,flashes
cap,cu=parse_flashes(gerbers/'controller-B_Cu.gbl')
pap,pa=parse_flashes(gerbers/'controller-B_Paste.gbp')
assert len(cu)==9 and len(pa)==12
assert [c['aperture'] for c in cu]==[16]*8+[17]
assert [c['aperture'] for c in pa]==[13]*4+[14]*8
assert np.allclose(cap[16]['parameters'],[.125,.2,.125,-.2,.125,-.2,-.125,.2,-.125,0])
assert cap[17]['type']=='R' and cap[17]['parameters']==[3.4,4.3]
assert np.allclose(pap[13]['parameters'],[.25,.435,.615,-.435,.615,-.435,-.615,.435,-.615,0])
assert np.allclose(pap[14]['parameters'],cap[16]['parameters'])

# Mask output has explicit polygon regions, not aperture flashes; locate by pad center.
regions=[];points=None
for line in (gerbers/'controller-B_Mask.gbs').read_text().splitlines():
    if line=='G36*':points=[]
    if line=='G37*':
        if points:regions.append(np.array(points))
        points=None
    if points is not None:
        m=re.fullmatch(r'X(-?\d+)Y(-?\d+)D0[12]\*',line)
        if m:points.append([int(m[1])/1e6,int(m[2])/1e6])
pins=[];windows=[]
functions={'1':'/CS','2':'DO/IO1','3':'/WP/IO2','4':'GND','5':'DI/IO0','6':'CLK','7':'/HOLD/IO3','8':'VCC','9':'EP, electrically unconnected inside package'}
for a in f.Pads():
    x,y=mm(a.GetPosition().x),mm(a.GetPosition().y)
    rec=dict(pin=a.GetNumber(),native_xy_mm=[x,y],gerber_cpl_xy_mm=[x,38-y],local_native_xy_mm=[x-cx,y-cy],size_mm=[mm(a.GetSize().x),mm(a.GetSize().y)],shape='rectangle' if a.GetShape()==p.PAD_SHAPE_RECT else 'roundrect',radius_mm=0 if a.GetShape()==p.PAD_SHAPE_RECT else mm(a.GetRoundRectCornerRadius()),net=a.GetNetname(),layers=[b.GetLayerName(i) for i in a.GetLayerSet().Seq()])
    if rec['pin']:
        rec['function']=functions[rec['pin']]
        matches=[r for r in regions if Path(r).contains_point(rec['gerber_cpl_xy_mm'])]
        assert len(matches)==1
        poly=matches[0];bbox=np.r_[poly.min(axis=0),poly.max(axis=0)]
        rec['mask_opening_bbox_gerber_mm']=bbox.tolist();rec['mask_opening_size_mm']=(bbox[2:]-bbox[:2]).tolist()
        rec['mask_expansion_mm']=mm(a.GetSolderMaskExpansion(p.B_Mask))
        assert np.allclose(rec['mask_opening_size_mm'],rec['size_mm']) and rec['mask_expansion_mm']==0
        cf=next(c for c in cu if c['pin']==rec['pin']);assert np.allclose(cf['xy_mm'],rec['gerber_cpl_xy_mm']);rec['copper_aperture']=cf['aperture']
        pins.append(rec)
    else:windows.append(rec)
assert len(pins)==9 and len(windows)==4
for r in windows:
    assert np.allclose(r['size_mm'],[1.37,1.73]) and r['radius_mm']==.25
    assert any(np.allclose(r['gerber_cpl_xy_mm'],q['xy_mm']) and q['aperture']==13 for q in pa)
for r in pins[:8]:assert np.allclose(r['size_mm'],[.65,.5]) and r['radius_mm']==.125

# All holes are outside even the maximum-dimension EP rectangle.
near_vias=[];holes_under_ep=[]
for t in b.GetTracks():
    if not isinstance(t,p.PCB_VIA):continue
    x,y=mm(t.GetPosition().x),mm(t.GetPosition().y);dr=mm(t.GetDrillValue())/2
    dx=max(0,abs(x-cx)-3.45/2);dy=max(0,abs(y-cy)-4.35/2)
    gap=math.hypot(dx,dy)-dr
    if gap<1:near_vias.append(dict(native_xy_mm=[x,y],hole_diameter_mm=2*dr,gap_to_max_ep_rectangle_mm=gap))
    if gap<0:holes_under_ep.append(near_vias[-1])
assert not holes_under_ep
ep_area=3.4*4.3-.4*.4/2
window_area=rr_area(1.37,1.73,.25)
window_max_x_minus_y=.85+1.075+(.685-.25)+(.865-.25)+math.sqrt(2)*.25
assert window_max_x_minus_y < 1.7+2.15-.4
ep=dict(copper_size_mm=[3.4,4.3],copper_area_mm2=3.4*4.3,nominal_package_size_mm=[3.4,4.3],package_pin1_chamfer_mm=.4,nominal_chamfered_package_area_mm2=ep_area,
 copper_nominal_overlap_ratio=1,copper_max_rectangle_overlap_ratio=3.4*4.3/(3.45*4.35),copper_max_chamfered_overlap_ratio=(3.4*4.3-.35*.35/2)/(3.45*4.35-.4*.4/2),
 paste_window_count=4,paste_window_size_mm=[1.37,1.73],paste_window_radius_mm=.25,paste_window_area_mm2=window_area,paste_total_area_mm2=4*window_area,
 paste_coverage_of_rectangular_copper_ratio=4*window_area/(3.4*4.3),paste_coverage_of_chamfered_nominal_ep_ratio=4*window_area/ep_area,
 single_window_over_chamfered_nominal_ep_ratio=window_area/ep_area,single_window_over_rectangular_nominal_ep_ratio=window_area/(3.4*4.3),paste_web_xy_mm=[.33,.42],paste_to_chamfer_perpendicular_clearance_mm=(1.7+2.15-.4-window_max_x_minus_y)/math.sqrt(2),near_vias=near_vias,holes_under_max_ep=holes_under_ep)
cplfiles=[ROOT/'controller-r3s-green/release/assembly'/v for v in ['JLC_CPL.csv','JLC_CPL_NATIVE_AUDIT.csv']]
cpl={x.name:next(r for r in csv.DictReader(x.open()) if r['Designator']=='U11') for x in cplfiles}
bomfile=ROOT/'controller-r3s-green/release/assembly/JLC_BOM.csv'
out=dict(board_sha256=EXPECTED,board_unchanged=True,footprint=dict(name=str(f.GetFPID().GetLibItemName()),side='Bottom',native_origin_mm=[cx,cy],gerber_cpl_origin_mm=[cx,38-cy],native_rotation_deg=180),cpl=cpl,
 bom=next(r for r in csv.DictReader(bomfile.open()) if r['Designator']=='U11'),pins=pins,paste_windows=windows,
 gerbers=dict(copper_flashes=cu,paste_flashes=pa,copper_apertures={str(i):cap[i] for i in [13,16,17]},paste_apertures={str(i):pap[i] for i in [13,14]},mask_type='Polygon regions; exact same bounding dimensions as native copper lands'),
 cases=named,dimension_grid=cases,exposed_pad=ep,
 suggested_winbond_lands=dict(source='AN0000009 Rev2, printed pp20–21; WSON8 8x6; axes rotated to native orientation',signal_copper_size_mm=[1.5,.8],signal_copper_centers_x_mm=[-4.15,4.15],signal_copper_inner_gap_mm=6.8,signal_stencil_size_mm=[1.4,.7],signal_stencil_inner_gap_mm=7,ep_copper_size_mm=[3.25,4.05],ep_stencil_holes_count=5,ep_stencil_hole_diameter_mm=.65,stencil_thickness_mm=.1,native_is_exact_match=False),
 supplier_rule=dict(report_ratio=.16,object='i274x.RoundRect.d13',selected_pin=None,model_polygon=None,registration_verified=False,definition='lead/pad intersection area divided by lead area',danger_below=.75,warning_below=.9),
 assumptions=['Package centered and manufacturer-aligned at the native footprint; no supplier model pose inferred.',
 'Rectangular terminal is an envelope; round-inner variant assumes radius b/2 from the illustrated shape, because no terminal radius is dimensioned.',
 'Dimension grid covers min/nom/max package D and terminal L/b, not unquantified lead positional error, fabrication or assembly tolerances.',
 'No observation identifies supplier d13 with any exported aperture or selected terminal. Single EP paste window reproduces 0.16 numerically, but is only a land-recognition hypothesis.',
 '180-degree rotational symmetry of the eight land locations means overlap alone cannot prove electrical pin-1 orientation. Supplier CPL0 and native180 use unverified different rotation conventions.',
 'Winbond official current download entry redirects to a 403 response. Live Mouser-hosted manufacturer PDF was checked as April17,2024 RevL; no newer source is claimed.'])
files=[BOARD,*cplfiles,bomfile,*(gerbers/n for n in ['controller-B_Cu.gbl','controller-B_Mask.gbs','controller-B_Paste.gbp']),HERE/'sources/Winbond-W25N01GV-RevL.pdf',HERE/'sources/Winbond-AN0000009-Rev2.pdf',HERE/'p3-bottom-overlap-u11.txt']
out['sha256']={str(x.relative_to(ROOT)):sha(x) for x in files}
(HERE/'geometry-audit.json').write_text(json.dumps(out,indent=2)+'\n')
with (HERE/'dimension-cases.csv').open('w') as fo:
    w=csv.DictWriter(fo,fieldnames=cases[0].keys());w.writeheader();w.writerows(cases)

# Direct geometry visualization. Native top view, y down; bottom component-face view is mirrored in x.
plt.rcParams.update({'font.size':10,'axes.titlesize':12})
fig,axes=plt.subplots(1,3,figsize=(18,7),gridspec_kw={'width_ratios':[1.3,1,1]})
gold='#d29a36';purple='#7151bd';blue='#187da1';green='#2e926b'
def rr(ax,x,y,L,W,R,**kw):ax.add_patch(FancyBboxPatch((x-L/2,y-W/2),L,W,boxstyle=f'round,pad=0,rounding_size={R}',**kw))
ax=axes[0];ax.add_patch(Rectangle((-4,-3),8,6,fill=False,ec='#777777',ls='--'))
for r in pins:
    x,y=r['local_native_xy_mm'];L,W=r['size_mm'];R=r['radius_mm']
    rr(ax,x,y,L,W,R,fc=gold,ec='#825410',alpha=.6)
    if r['pin']!='9':
        side=1 if x>0 else -1
        ax.add_patch(Rectangle((side*4.15-.75,y-.4),1.5,.8,fill=False,ec=blue,lw=1.4))
        ax.add_patch(Rectangle((side*3.75-.25,y-.2),.5,.4,fc=purple,alpha=.65))
        ax.text(side*5.15,y,r['pin'],va='center',ha='center')
ax.plot([4],[-3],marker='o',color='black',ms=5);ax.text(3.1,-3.35,'Pin 1 / CS',ha='center')
ax.text(0,0,'EP copper\n3.40 × 4.30\nGND',ha='center',va='center')
ax.set(xlim=(-5.5,5.5),ylim=(3.65,-3.8),xlabel='Local native x (mm)',ylabel='Local native y (mm)',title='Actual P3 copper and Winbond suggestion')
ax.set_aspect('equal');ax.grid(alpha=.15)
ax=axes[1]
rr(ax,3.75,0,.65,.5,.125,fc=gold,ec='#825410',alpha=.6)
ax.add_patch(Rectangle((3.5,-.2),.5,.4,fc=purple,alpha=.55))
ax.add_patch(Rectangle((3.4,-.24),.55,.48,fill=False,ec=green,ls='--',lw=1.5))
ax.axvline(4,color='#777777',ls=':')
ax.annotate('',xy=(3.425,.38),xytext=(4.075,.38),arrowprops={'arrowstyle':'|-|'});ax.text(3.75,.405,'Native: 0.65 × 0.50; R0.125',ha='center',va='top')
ax.text(3.75,-.40,'Nominal lead: 0.50 × 0.40\nOverlap = 100%\nToe/heel = +0.075; sides = +0.050',ha='center',va='bottom')
ax.text(3.75,.62,'Largest rectangular lead + smallest body:\n0.55 × 0.48; D = 7.90\nOverlap = '+f"{named['maximum_lead_minimum_body_rectangular']['overlap_ratio']*100:.3f}%",ha='center',va='top',color=green)
ax.set(xlim=(3.18,4.32),ylim=(.95,-.8),xlabel='Distance from package center (mm)',ylabel='Transverse offset (mm)',title='Lead overlap in manufacturer-aligned pose')
ax.set_aspect('equal');ax.grid(alpha=.15)
ax=axes[2]
ax.add_patch(Rectangle((-1.7,-2.15),3.4,4.3,fc=gold,ec='#825410',alpha=.45))
poly=[(-1.7,-2.15),(1.3,-2.15),(1.7,-1.75),(1.7,2.15),(-1.7,2.15)]
ax.add_patch(Polygon(poly,fill=False,ec=purple,lw=2))
for i,r in enumerate(windows):
    x,y=r['local_native_xy_mm'];rr(ax,x,y,1.37,1.73,.25,fc=green,ec='#116542',alpha=.6)
    ax.text(x,y,'2.31645\nmm²',ha='center',va='center',fontsize=9)
ax.text(0,2.58,'ONE window / nominal EP = 0.15932\nAll four / nominal EP = 0.63726\nCopper / nominal EP = 1.00000',ha='center',va='top')
ax.text(0,-2.53,'EP includes 0.40 chamfer at pin 1\nSignal copper D16; EP copper D17\nEP paste windows D13 (native Gerber)',ha='center',va='bottom')
ax.set(xlim=(-2.15,2.15),ylim=(3.8,-3.7),xlabel='Local native x (mm)',ylabel='Local native y (mm)',title='0.16 reproduced by ONE paste window')
ax.set_aspect('equal');ax.grid(alpha=.15)
fig.legend(handles=[Patch(fc=gold,alpha=.6,label='P3 copper; mask opening same bounds'),Patch(fc=purple,alpha=.55,label='Winbond package / terminal'),Patch(fc='none',ec=blue,label='Winbond AN0000009 suggested land'),Patch(fc=green,alpha=.6,label='EP paste windows (right panel)')],loc='lower center',ncol=2,bbox_to_anchor=(.5,.035),frameon=False)
fig.suptitle('U11 W25N01GVZEIG: native/Gerber audit of the P3 SMT 0.16 report',fontsize=16,y=.98)
fig.text(.5,.012,'Sources: Winbond W25N01GV Rev L p64; AN0000009 Rev2 pp20–21. P3 board SHA256 '+EXPECTED[:16]+'…\nThe 0.16 paste-window match is a hypothesis, not a supplier-object mapping. Model polygons and registration remain unavailable.',ha='center',fontsize=9)
fig.subplots_adjust(left=.045,right=.99,top=.89,bottom=.21,wspace=.25)
fig.savefig(HERE/'u11-overlap-overlay.png',dpi=180);fig.savefig(HERE/'u11-overlap-overlay.svg')
assert sha(BOARD)==EXPECTED
print(json.dumps({'case_summary':named,'EP':ep,'minimum_centered_dimension_grid_ratio':min(c['overlap_ratio'] for c in cases),'outputs':['geometry-audit.json','dimension-cases.csv','u11-overlap-overlay.png','u11-overlap-overlay.svg']},indent=2))
