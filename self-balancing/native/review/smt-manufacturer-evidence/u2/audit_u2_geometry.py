#!/usr/bin/python3
"""Read-only U2 native/Gerber geometry audit against TI DSG0008A 4218900/E.

All output is written next to this script. Never saves the loaded board.
Terminal geometry is explicitly constructed; no JLC model is inferred.
"""
import os
os.environ.setdefault('XDG_CONFIG_HOME', '/tmp/u2-kicad-config')
os.environ.setdefault('MPLCONFIGDIR', '/tmp/u2-matplotlib')
import csv, hashlib, itertools, json, math, pathlib, re
import pcbnew as p
import numpy as np
from scipy.integrate import quad
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Patch

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT/'controller-r3s-green/controller.kicad_pcb'
EXPECTED = '0850991d8aacd22138487804c24eefbae634a21ba218c18196f13fad795c3696'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(BOARD) == EXPECTED, 'Audit is bound to the supplied P3 board bytes'
b = p.LoadBoard(str(BOARD))
f = next(f for f in b.GetFootprints() if f.GetReference() == 'U2')
assert f.GetOrientationDegrees() == 0
mm=p.ToMM
cx,cy=mm(f.GetPosition().x),mm(f.GetPosition().y)
pads={a.GetNumber():a for a in f.Pads() if a.IsOnLayer(p.F_Cu)}
paste=[a for a in f.Pads() if a.IsOnLayer(p.F_Paste)]

def rr_area(length,width,r): return length*width-(4-math.pi)*r*r
def rr_span(y,length,width,r,center=.95):
    if abs(y)>width/2: return None
    dy=max(abs(y)-(width/2-r),0)
    dx=math.sqrt(max(r*r-dy*dy,0))
    half=length/2-r+dx
    return center-half,center+half

def overlap(body,lead_length,lead_width,pad_length,pad_width,pad_r,shape='rectangular',dy=0):
    """Integrate true rounded-land intersection with terminal envelope in radial coordinates."""
    outer=body/2;inner=outer-lead_length;tr=lead_width/2
    def lead_span(y):
        if abs(y-dy)>tr: return None
        left=inner
        if shape=='round_inner': left=inner+tr-math.sqrt(max(tr*tr-(y-dy)**2,0))
        return left,outer
    def width(y):
        ps=rr_span(y,pad_length,pad_width,pad_r);ls=lead_span(y)
        return max(0,min(ps[1],ls[1])-max(ps[0],ls[0])) if ps and ls else 0
    low=max(-pad_width/2,dy-tr);high=min(pad_width/2,dy+tr)
    knots=sorted(set([low,high]+[v for v in [-pad_width/2+pad_r,pad_width/2-pad_r,dy] if low<v<high]))
    area=sum(quad(width,a,z,epsabs=1e-12,epsrel=1e-11,limit=200)[0] for a,z in zip(knots,knots[1:])) if high>low else 0
    terminal_area=lead_length*lead_width
    if shape=='round_inner':terminal_area-=(2-math.pi/2)*tr*tr
    copper_area=rr_area(pad_length,pad_width,pad_r)
    return dict(toe_mm=.95+pad_length/2-outer,heel_mm=inner-(.95-pad_length/2),side_plus_mm=pad_width/2-(dy+tr),side_minus_mm=pad_width/2+(dy-tr),intersection_mm2=area,terminal_area_mm2=terminal_area,land_area_mm2=copper_area,intersection_over_terminal=area/terminal_area,intersection_over_land=area/copper_area)

cases=[]
for body,L,W,shape in itertools.product([1.9,2,2.1],[.2,.3,.4],[.18,.25,.32],['rectangular','round_inner']):
    cases.append(dict(body_width_mm=body,terminal_length_mm=L,terminal_width_mm=W,terminal_shape=shape,native=overlap(body,L,W,.6,.25,.0625,shape),ti_example=overlap(body,L,W,.5,.25,.05,shape)))
named={
    'nominal_rectangular':(2,.3,.25,'rectangular'),
    'nominal_round_inner':(2,.3,.25,'round_inner'),
    'maximum_terminal_nominal_body':(2,.4,.32,'rectangular'),
    'maximum_terminal_minimum_body':(1.9,.4,.32,'rectangular'),
    'maximum_terminal_maximum_body':(2.1,.4,.32,'rectangular'),
    'minimum_terminal_nominal_body':(2,.2,.18,'rectangular'),
}
summary={name:dict(body_width_mm=values[0],terminal_length_mm=values[1],terminal_width_mm=values[2],terminal_shape=values[3],native=overlap(*values[:3],.6,.25,.0625,values[3]),ti_example=overlap(*values[:3],.5,.25,.05,values[3])) for name,values in named.items()}
pin_names={'1':'PGND','2':'VIN','3':'EN','4':'AGND','5':'FB','6':'VOS','7':'SW','8':'PG','9':'EP'}
records=[]
for number,a in sorted(pads.items(),key=lambda x:int(x[0])):
    x,y=mm(a.GetPosition().x),mm(a.GetPosition().y)
    rec=dict(pin=number,function=pin_names[number],native_xy_mm=[x,y],manufacturing_xy_mm=[x,38-y],local_native_xy_mm=[x-cx,y-cy],size_mm=[mm(a.GetSize().x),mm(a.GetSize().y)],radius_mm=mm(a.GetRoundRectCornerRadius()),net=a.GetNetname())
    if number!='9':
        assert np.allclose(rec['size_mm'],[.6,.25]) and abs(rec['radius_mm']-.0625)<1e-9
        rec['nominal_rectangular_metrics']=summary['nominal_rectangular']['native']
        rec['max_rectangular_terminal_min_body_metrics']=summary['maximum_terminal_minimum_body']['native']
        rec['dimension_only_margin_ranges_mm']={'toe':[.2,.3],'heel':[-.1,.2],'side_each':[-.035,.035]}
    records.append(rec)

gerber=ROOT/'controller-r3s-green/release/single-board-gerbers/controller-F_Cu.gtl'
text=gerber.read_text();gm={}
current_aperture=None;current_pin=None
for line in text.splitlines():
    match=re.fullmatch(r'D(\d+)\*',line)
    if match:current_aperture=int(match[1])
    match=re.fullmatch(r'%TO.P,U2,(\d+)\*%',line)
    if match:current_pin=match[1]
    if current_pin:
        match=re.fullmatch(r'X(-?\d+)Y(-?\d+)D03\*',line)
        if match:
            gm[current_pin]={'aperture':current_aperture,'xy_mm':[int(match[1])/1e6,int(match[2])/1e6]};current_pin=None
for r in records:
    assert np.allclose(gm[r['pin']]['xy_mm'],r['manufacturing_xy_mm'])
    assert gm[r['pin']]['aperture']==(12 if r['pin']=='9' else 11)

files=[BOARD,gerber,ROOT/'controller-r3s-green/release/single-board-gerbers/controller-F_Paste.gtp',ROOT/'controller-r3s-green/release/single-board-gerbers/controller-F_Mask.gts',ROOT/'controller-r3s-green/release/assembly/JLC_CPL.csv',ROOT/'controller-r3s-green/release/assembly/JLC_CPL_NATIVE_AUDIT.csv',ROOT/'controller-r3s-green/inputs/user-corrected-JLC_CPL.csv',ROOT/'controller-r3s-green/release/assembly/JLC_BOM.csv',ROOT/'research/controller-r3s-stage20-buck-stencil-result.json',ROOT/'research/audit_controller_r3s_buck_stencil.py',HERE/'tps62162-current-ti.pdf',HERE/'current-stencil-audit.json']
hashes={str(path.relative_to(ROOT)):sha(path) for path in files}
cpl={str(path.relative_to(ROOT)):next(r for r in csv.DictReader(path.open()) if r['Designator']=='U2') for path in files if path.suffix=='.csv' and 'BOM' not in path.name}
xs=np.linspace(-.125,.125,20001)
differences=[rr_span(y,.5,.25,.05)[0]-rr_span(y,.6,.25,.0625)[0] for y in xs]
stencil=json.loads((HERE/'current-stencil-audit.json').read_text());assert not stencil['errors'];assert not stencil['holes_in_apertures']
out=dict(board_sha256=sha(BOARD),source=dict(url='https://www.ti.com/lit/ds/symlink/tps62162.pdf',datasheet='SLVSAM2E, Rev E, May 2017 with current package appendix',package='DSG0008A 4218900/E 08/2022',pdf_pages_1_based=[4,39,40,41],pdf_sha256=sha(HERE/'tps62162-current-ti.pdf')),assumptions=['Package centered at native/CPL origin, manufacturer top-view pin 1 at top left, no rotation or translation error','Nominal terminal dimensions are midpoint of min/max; they are a constructed comparison case, not a separate TI nominal specification','Dimension-only grid does not apply composite positional tolerance, PCB fabrication or assembly placement error','Two terminal variants: rectangular envelope and the drawing alternative with inward semicircle; results do not assert JLC uses either variant','Overlap definition here is explicit intersection/terminal area; intersection/land is also included, and neither is assigned to JLC without its definition'],footprint=dict(origin_native_mm=[cx,cy],origin_manufacturing_mm=[cx,38-cy],orientation_deg=0),pins=records,gerber_pins=gm,cpl=cpl,case_summary=summary,all_centered_dimension_cases=cases,containment=dict(native_contains_entire_ti_example=True,min_horizontal_extension_mm=min(differences),max_horizontal_extension_mm=max(differences),transverse_edge_margin_mm=0,corner_exception=False,native_land_area_mm2=rr_area(.6,.25,.0625),ti_land_area_mm2=rr_area(.5,.25,.05)),stencil=stencil,hashes=hashes)
(HERE/'geometry-audit.json').write_text(json.dumps(out,indent=2)+'\n')
with (HERE/'per-pin-metrics.csv').open('w') as outcsv:
    fields=['pin','function','native_x_mm','native_y_mm','manufacturing_x_mm','manufacturing_y_mm','net','nominal_toe_mm','nominal_heel_mm','nominal_side_each_mm','nominal_intersection_mm2','nominal_lead_overlap_ratio','maxlead_minbody_intersection_mm2','maxlead_minbody_lead_overlap_ratio']
    writer=csv.DictWriter(outcsv,fieldnames=fields);writer.writeheader()
    for rec in records[:-1]:
        n=rec['nominal_rectangular_metrics'];w=rec['max_rectangular_terminal_min_body_metrics']
        writer.writerow(dict(pin=rec['pin'],function=rec['function'],native_x_mm=rec['native_xy_mm'][0],native_y_mm=rec['native_xy_mm'][1],manufacturing_x_mm=rec['manufacturing_xy_mm'][0],manufacturing_y_mm=rec['manufacturing_xy_mm'][1],net=rec['net'],nominal_toe_mm=round(n['toe_mm'],8),nominal_heel_mm=round(n['heel_mm'],8),nominal_side_each_mm=round(n['side_plus_mm'],8),nominal_intersection_mm2=round(n['intersection_mm2'],9),nominal_lead_overlap_ratio=round(n['intersection_over_terminal'],9),maxlead_minbody_intersection_mm2=round(w['intersection_mm2'],9),maxlead_minbody_lead_overlap_ratio=round(w['intersection_over_terminal'],9)))

# Captured JLC help defines the denominator as lead area. P2 detail captures are
# preserved with explicit provenance; P3 category-count equivalence is separate.
capture_root=pathlib.Path('/workspace/scratch/8a35c1f26232/jlcdfm-p3-review')
out['supplier_rule']={'ratio_definition':'lead/pad intersection area divided by lead area','danger_boundary':.75,'warning_boundary':.9,'U2_reported_ratio':.44,'object':'i274x.RoundRect.d11','selected_pin_number':None,'model_terminal_geometry':None,'model_pose_verified':False,'edge_threshold_numeric':None,'detail_capture_project':'629258777493983233 (corrected-CPL P2)','P3_project':'629271171624820737','P3_evidence':'P3 SMT category counts match corrected-CPL P2; native U2 copper/paste and pose are unchanged'}
paste_path=ROOT/'controller-r3s-green/release/single-board-gerbers/controller-F_Paste.gtp'
paste_lines=paste_path.read_text().splitlines()
capture=[];component=None;aperture=None;ep_flashes=[]
for line_number,line in enumerate(paste_lines,1):
    if line.startswith('%TO.C,'):component=line.split(',')[1].split('*')[0]
    if line=='%TD*%':component=None
    dm=re.fullmatch(r'D(\d+)\*',line)
    if dm:aperture=int(dm[1])
    if line.startswith('%ADD11') or line.startswith('%TF.FileFunction') or component=='U2':
        capture.append({'line':line_number,'text':line})
    fm=re.fullmatch(r'X(-?\d+)Y(-?\d+)D03\*',line)
    if component=='U2' and aperture==11 and fm:
        ep_flashes.append({'line':line_number,'xy_mm':[int(fm[1])/1e6,int(fm[2])/1e6]})
assert len(ep_flashes)==2
window_area=rr_area(.9,.7,.05);ep_area=rr_area(.9,1.6,.05)
split_evidence={'interpretation':'Strong numerical and aperture/component-association evidence of a split-paste-window being compared to full exposed-pad lead; not proof of the JLC i274x source-file mapping','source_file':str(paste_path.relative_to(ROOT)),'source_sha256':sha(paste_path),'file_function':'Paste,Top','aperture':11,'component_attribute':'%TO.C,U2*%','flashes':ep_flashes,'gerber_excerpts':capture,'single_window_dimensions_mm':[.9,.7],'single_window_corner_radius_mm':.05,'single_window_area_mm2':window_area,'nominal_ep_dimensions_mm':[.9,1.6],'rounded_ep_corner_radius_mm':.05,'rounded_ep_area_mm2':ep_area,'rectangular_ep_area_mm2':.9*1.6,'single_window_over_rounded_ep':window_area/ep_area,'both_windows_over_rounded_ep':2*window_area/ep_area,'single_window_over_rectangular_ep':window_area/(.9*1.6),'both_windows_over_rectangular_ep':2*window_area/(.9*1.6),'displayed_two_decimal_ratio':format(window_area/ep_area,'.2f'),'jlc_reported_ratio':.44,'source_layer_mapping_confirmed':False,'actual_jlc_ep_polygon_confirmed':False,'caution':'Aperture numbers are file-local. F.Cu ADD11 is a signal land, whereas F.Paste ADD11 is this EP window. The object name alone cannot select a source file. The denominator cases are explicit geometric hypotheses; the actual package/model EP shape and tolerance are not known.'}
assert split_evidence['displayed_two_decimal_ratio']=='0.44'
out['split_stencil_recognition_evidence']=split_evidence
out['supplier_rule']['object_source_layer']=None
out['supplier_rule']['aperture11_candidates']={'F.Cu':'0.60 x 0.25 R0.0625 signal land, pins 1-8','F.Paste':'0.90 x 0.70 R0.05 exposed-pad paste window, two U2 flashes'}
(HERE/'split-stencil-evidence.json').write_text(json.dumps(split_evidence,indent=2)+'\n')
for kind in ['pin-inner','pin-left','pin-right','lead-pad-overlap']:
    source=capture_root/f'corrected-cpl-smt-{kind}.txt'
    destination=HERE/source.name
    destination.write_bytes(source.read_bytes())
    out['hashes'][str(destination.relative_to(ROOT))]=sha(destination)
for name in ['p3-smt-comparison.json','p3-upload-provenance.json']:
    source=ROOT/'controller-r3s-green/review/supplier-p3-evidence'/name
    out['hashes'][str(source.relative_to(ROOT))]=sha(source)
out['assumptions'][-1]='Overlap uses intersection/lead area, matching captured JLC help. JLC terminal polygon, selected pin and registration are not available; intersection/land is a separate diagnostic only.'
(HERE/'geometry-audit.json').write_text(json.dumps(out,indent=2)+'\n')

# Engineering evidence diagram, directly from extracted geometry and explicit terminal assumptions.
plt.rcParams.update({'font.size':11,'axes.titlesize':13,'axes.labelsize':11})
fig,axes=plt.subplots(1,2,figsize=(14,7),gridspec_kw={'width_ratios':[1.05,1]})
nativecolor='#cf9639';ticolor='#1596ba';leadcolor='#6844c4'
def rr(ax,x,y,l,w,r,**kwargs):
    ax.add_patch(FancyBboxPatch((x-l/2,y-w/2),l,w,boxstyle=f'round,pad=0,rounding_size={r}',**kwargs))
ax=axes[0]
ax.add_patch(Rectangle((-1,-1),2,2,fill=False,ec='#505050',lw=1.5,ls='--'))
for rec in records:
    x,y=rec['local_native_xy_mm'];l,w=rec['size_mm'];r=rec['radius_mm']
    rr(ax,x,y,l,w,r,fc=nativecolor,ec='#8b6020',alpha=.65)
    if rec['pin']!='9':
        rr(ax,x,y,.5,.25,.05,fc='none',ec=ticolor,lw=1.5)
        lx=-1 if x<0 else .7
        ax.add_patch(Rectangle((lx,y-.125),.3,.25,fc=leadcolor,ec=leadcolor,alpha=.5))
        ax.text(x+(-.50 if x<0 else .50),y,f"{rec['pin']} {rec['function']}",va='center',ha='center',fontsize=10)
    else: ax.text(0,0,'EP 9\n0.9 × 1.6',ha='center',va='center',fontsize=10)
ax.plot([-1.11],[-1.11],marker='v',color='black',ms=8)
ax.text(0,1.55,'Native coordinates: y increases downward\nBody = 2.00 × 2.00 nominal; pin pitch = 0.50',ha='center',fontsize=10)
ax.set(xlim=(-2.2,2.2),ylim=(1.85,-1.6),xlabel='Local x (mm)',ylabel='Local native y (mm)')
ax.set_aspect('equal');ax.grid(alpha=.18);ax.set_title('U2: P3 copper + TI land + nominal terminals')
ax=axes[1]
rr(ax,.95,0,.6,.25,.0625,fc=nativecolor,ec='#8b6020',alpha=.65)
rr(ax,.95,0,.5,.25,.05,fc='none',ec=ticolor,lw=2)
ax.add_patch(Rectangle((.7,-.125),.3,.25,fc=leadcolor,ec=leadcolor,alpha=.5))
ax.axvline(1,color='#505050',ls='--',lw=1,label='Nominal body edge')
def dim(x0,x1,y,label):
    ax.annotate('',xy=(x1,y),xytext=(x0,y),arrowprops={'arrowstyle':'|-|','lw':1,'color':'#333333'})
    ax.text((x0+x1)/2,y-.018,label,ha='center',va='bottom',fontsize=10)
dim(.65,1.25,-.27,'P3 copper 0.60; R0.0625')
dim(.7,1.2,.23,'TI land / paste 0.50; R0.05')
dim(.7,1,-.19,'Nominal terminal 0.30')
dim(.65,.7,.36,'Heel +0.05')
dim(1,1.25,.36,'Toe +0.25')
ax.annotate('',xy=(1.31,.125),xytext=(1.31,-.125),arrowprops={'arrowstyle':'|-|','lw':1})
ax.text(1.33,0,'0.25\nwidth\n(all 3)',ha='left',va='center',fontsize=10)
ax.text(.96,.51,'Nominal side margin = 0 on both sides\nCopper contains the whole TI example land\nNominal rectangular lead overlap = '+f"{100*summary['nominal_rectangular']['native']['intersection_over_terminal']:.4f}%",ha='center',va='center',fontsize=10)
ax.set(xlim=(.55,1.49),ylim=(.61,-.39),xlabel='Distance outward from package center (mm)',ylabel='Local transverse offset (mm)')
ax.set_aspect('equal');ax.grid(alpha=.18);ax.set_title('Representative right-side pin (all 8 symmetric)')
fig.legend(handles=[Patch(fc=nativecolor,alpha=.65,label='Actual P3 copper'),Patch(fc='none',ec=ticolor,lw=2,label='TI example copper = actual lead paste'),Patch(fc=leadcolor,alpha=.5,label='Constructed nominal rectangular terminal')],loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.035),fontsize=10)
fig.suptitle('TPS62162DSGR / DSG0008A — manufacturer-aligned geometric comparison',fontsize=16,y=.98)
fig.text(.5,.008,'Source: ti.com/lit/ds/symlink/tps62162.pdf, DSG0008A 4218900/E, pages 39–41. P3 board SHA256: '+EXPECTED[:16]+'…\nTerminal pose shown is the manufacturer-aligned hypothesis; JLC model terminal geometry, selected pin and registration remain unverified.',ha='center',fontsize=8)
fig.subplots_adjust(top=.90,bottom=.18,left=.055,right=.97,wspace=.26)
fig.savefig(HERE/'u2-copper-ti-terminal-overlay.png',dpi=180)
fig.savefig(HERE/'u2-copper-ti-terminal-overlay.svg')

fig2,ax2=plt.subplots(figsize=(8,6))
rr(ax2,0,0,.9,1.6,.05,fc='#e1e1e1',ec='#626262',lw=2)
for wy in [-.45,.45]:
    rr(ax2,0,wy,.9,.7,.05,fc='#30a5ba',ec='#117488',lw=1.5,alpha=.85)
    ax2.text(0,wy,'F.Paste ADD11\n0.90 × 0.70; R0.05\n0.6278539816 mm²',ha='center',va='center',fontsize=12)
ax2.text(.70,0,'One window ÷ full EP\n= 0.4366604604\nrounds to JLC 0.44\n\nBoth windows ÷ full EP\n= 0.8733209208\n87.332% intended coverage',ha='left',va='center',fontsize=12)
ax2.set_xlim(-.7,2.15);ax2.set_ylim(-1.1,1.1);ax2.set_aspect('equal');ax2.axis('off')
fig2.suptitle('U2 0.44: split-stencil recognition hypothesis',fontsize=16,y=.95)
fig2.text(.5,.14,'Full nominal rounded EP: 0.90 × 1.60; R0.05; area 1.4378539816 mm²\nBoth ADD11 flashes are inside %TO.C,U2 in the actual P3 front-paste Gerber',ha='center',fontsize=11)
fig2.text(.5,.05,'The numerical match is strong evidence, not confirmed JLC object-to-layer mapping.\nAperture IDs are file-local: front-copper ADD11 is a different shape. No native change.',ha='center',fontsize=9)
fig2.subplots_adjust(top=.87,bottom=.21,left=.05,right=.98)
fig2.savefig(HERE/'u2-split-stencil-recognition.png',dpi=180)
print(json.dumps({'cases':summary,'containment':out['containment'],'outputs':['geometry-audit.json','per-pin-metrics.csv','u2-copper-ti-terminal-overlay.png','u2-copper-ti-terminal-overlay.svg']},indent=2))
assert sha(BOARD)==EXPECTED, 'Source was changed externally during the audit'
