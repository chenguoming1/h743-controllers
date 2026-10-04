#!/usr/bin/python3
"""Read-only D4 audit; writes derived evidence only beside this script."""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re

os.environ.setdefault('MPLCONFIGDIR', '/tmp/d4-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon
import numpy as np
from scipy.integrate import quad
import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = Path('/workspace/shared/storm32-redesign/controller-r3s-green')
EXPECTED = '0850991d8aacd22138487804c24eefbae634a21ba218c18196f13fad795c3696'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(ROOT / 'controller.kicad_pcb') == EXPECTED
board = pcbnew.LoadBoard(str(ROOT / 'controller.kicad_pcb'))
fp = next(f for f in board.GetFootprints() if f.GetReference() == 'D4')
mm = lambda v: [v.x / 1e6, v.y / 1e6]
pads = []
for p in fp.Pads():
    pads.append(dict(number=p.GetNumber(), net=p.GetNetname(), position_native_mm=mm(p.GetPosition()),
                     size_mm=mm(p.GetSize()), roundrect_radius_mm=p.GetRoundRectCornerRadius()/1e6,
                     mask_expansion_mm=p.GetSolderMaskExpansion(pcbnew.F_Mask)/1e6,
                     paste_margin_mm=mm(p.GetSolderPasteMargin(pcbnew.F_Paste))))
rows = {}
for name in ['JLC_BOM.csv', 'JLC_CPL.csv', 'JLC_CPL_NATIVE_AUDIT.csv']:
    with (ROOT / 'release/assembly' / name).open() as f:
        rows[name] = [r for r in csv.DictReader(f) if any(v == 'D4' for v in r.values())]

gdir = ROOT / 'release/single-board-gerbers'
mask_polygons = []
for region in (gdir/'controller-F_Mask.gts').read_text().split('G36*')[1:]:
    region = region.split('G37*')[0]
    pts = [(int(x)/1e6, int(y)/1e6) for x,y in re.findall(r'X(-?\d+)Y(-?\d+)D0[12]\*',region)]
    if not pts: continue
    bb = [min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]
    if bb[0] < 36.7 and bb[2] > 34.5 and bb[1] < 12 and bb[3] > 11.1:
        mask_polygons.append(dict(bounds_mm=bb, points_mm=pts))
assert len(mask_polygons) == 2
right_mask = [(x-35.6,y-11.55) for x,y in mask_polygons[1]['points_mm']]

def polyarea(poly):
    return abs(sum(poly[i][0]*poly[(i+1)%len(poly)][1] - poly[(i+1)%len(poly)][0]*poly[i][1]
                   for i in range(len(poly))))/2 if poly else 0

def clip(poly, axis, bound, greater):
    result=[]
    if not poly: return result
    inside=lambda p: p[axis] >= bound if greater else p[axis] <= bound
    for a,b in zip(poly,poly[1:]+poly[:1]):
        ai,bi=inside(a),inside(b)
        if ai: result.append(a)
        if ai != bi:
            t=(bound-a[axis])/(b[axis]-a[axis])
            result.append(tuple(a[j]+t*(b[j]-a[j]) for j in (0,1)))
    return result

def mask_overlap(L,b,dx=0,dy=0):
    poly=right_mask
    for axis,bound,greater in [(0,.525+dx-L/2,True),(0,.525+dx+L/2,False),
                               (1,dy-b/2,True),(1,dy+b/2,False)]:
        poly=clip(poly,axis,bound,greater)
    return polyarea(poly)

R=.1375
def halfheight(x):
    if x < .35 or x > .9: return 0
    d=max(.4875-x, x-.7625, 0)
    return .4-R+math.sqrt(max(0,R*R-d*d))

def overlap(L,b,dx=0,dy=0,rounded=True):
    xlo=max(.35,.525+dx-L/2); xhi=min(.9,.525+dx+L/2)
    if xhi<=xlo: return 0
    if not rounded:
        return (xhi-xlo)*max(0,min(.4,dy+b/2)-max(-.4,dy-b/2))
    def width(x):
        h=halfheight(x)
        return max(0,min(h,dy+b/2)-max(-h,dy-b/2))
    points=[v for v in [.4875,.7625] if xlo<v<xhi]
    return quad(width,xlo,xhi,points=points,epsabs=1e-11)[0]

def case(label,L,b,dx=0,dy=0):
    areas=dict(st_rectangular_land=overlap(L,b,dx,dy,False),
               native_copper_and_paste=overlap(L,b,dx,dy,True),
               exported_mask_exposed=mask_overlap(L,b,dx,dy))
    return dict(label=label,L_mm=L,b_mm=b,e_mm=1.05,dx_mm=dx,dy_mm=dy,
                toe_mm=.9-(.525+dx+L/2),heel_mm=(.525+dx-L/2)-.35,
                side_low_mm=(dy-b/2)+.4,side_high_mm=.4-(dy+b/2),
                terminal_envelope_area_mm2=L*b,intersection_areas_mm2=areas,
                overlap_ratios={k:v/(L*b) for k,v in areas.items()})

cases=[case(label,L,b) for label,L,b in [('min',.30,.75),('nominal',.35,.80),('max',.40,.85)]]
dimension_grid=[case(f'L{L:.2f}_b{b:.2f}',float(L),float(b)) for L in np.linspace(.3,.4,21) for b in np.linspace(.75,.85,21)]
sensitivities=[case(f'max_dx{dx:+.3f}_dy{dy:+.3f}',.4,.85,dx,dy)
               for dx,dy in [(0,0),(-.025,0),(.025,0),(0,.025),(-.025,.025),(-.05,.05),(.05,.05)]]
files=[ROOT/'controller.kicad_pcb',ROOT/'controller.kicad_pro',
       ROOT/'release/assembly/JLC_BOM.csv',ROOT/'release/assembly/JLC_CPL.csv',
       ROOT/'release/assembly/JLC_CPL_NATIVE_AUDIT.csv',ROOT/'inputs/user-corrected-JLC_CPL.csv',
       *[gdir/n for n in ['controller-F_Cu.gtl','controller-F_Mask.gts','controller-F_Paste.gtp']],
       HERE/'sources/st-esda7p120-1u1m-DS14419-Rev4.pdf']
out=dict(board_sha256=EXPECTED,manufacturer_source='https://www.st.com/resource/en/datasheet/esda7p120-1u1m.pdf',
         manufacturer_revision='DS14419 Rev 4 March 2025; pp1,9,10',
         footprint_position_native_mm=mm(fp.GetPosition()),angle_degrees=fp.GetOrientationDegrees(),
         aux_origin_native_mm=mm(board.GetDesignSettings().GetAuxOrigin()),pads=pads,assembly_rows=rows,
         mask_polygons=mask_polygons,land_areas_mm2=dict(st_rectangle=.55*.8,
         native_roundrect=.55*.8-(4-math.pi)*R*R,export_mask_polygon=polyarea(right_mask)),
         cases=cases,dimension_grid_extrema={key:dict(min=min(c['overlap_ratios'][key] for c in dimension_grid),
         max=max(c['overlap_ratios'][key] for c in dimension_grid)) for key in cases[0]['overlap_ratios']},
         placement_sensitivity_not_specified_tolerance=sensitivities,
         limitations=['e=1.05 mm is typical only; terminal location tolerance is not specified in Table 11',
         'Terminal modeled as b by L rectangle; undimensioned pin-1 chamfer is not inferred',
         'No etch/mask registration/stencil/placement process tolerance supplied; sensitivity is illustrative only',
         'Supplier DFM component pin model and overlap semantics were not available'],
         files_sha256={str(p):sha(p) for p in files})
(HERE/'geometry-audit.json').write_text(json.dumps(out,indent=2)+'\n')
with (HERE/'tolerance-cases.csv').open('w') as f:
    w=csv.writer(f); w.writerow(['case','L_mm','b_mm','dx_mm','dy_mm','toe_mm','heel_mm','side_low_mm','side_high_mm',
                               'ST_rect_overlap','native_round_overlap','mask_exposed_overlap'])
    for c in cases+sensitivities:
        w.writerow([c[k] for k in ['label','L_mm','b_mm','dx_mm','dy_mm','toe_mm','heel_mm','side_low_mm','side_high_mm']]+
                   list(c['overlap_ratios'].values()))

fig,axs=plt.subplots(1,3,figsize=(14.8,5.6),sharex=True,sharey=True)
for ax,c in zip(axs,cases):
    ax.add_patch(Rectangle((-.8,-.5),1.6,1,fill=False,edgecolor='#6b7280',linestyle=':',linewidth=1.1))
    for sgn in [-1,1]:
        x=sgn*.625-.275
        ax.add_patch(Rectangle((x,-.4),.55,.8,fill=False,edgecolor='#2563eb',linestyle='--',linewidth=1.6))
        ax.add_patch(FancyBboxPatch((x,-.4),.55,.8,boxstyle=f'round,pad=0,rounding_size={R}',
                                  facecolor='#fbbf24',edgecolor='#b45309',alpha=.75,linewidth=1.2))
        pts=np.array(right_mask); pts[:,0]*=sgn
        ax.add_patch(Polygon(pts,closed=True,fill=False,edgecolor='#7c3aed',linewidth=.8))
        L,b=c['L_mm'],c['b_mm']; x=sgn*.525-L/2
        ax.add_patch(Rectangle((x,-b/2),L,b,facecolor='#059669',edgecolor='#065f46',alpha=.32,linewidth=2))
    rr=c['overlap_ratios']
    ax.set_title(f"{c['label'].capitalize()} terminal {L:.2f} × {b:.2f} mm\n"
                 f"ST rectangle {100*rr['st_rectangular_land']:.2f}% | copper {100*rr['native_copper_and_paste']:.2f}%\n"
                 f"Exposed through mask {100*rr['exported_mask_exposed']:.2f}%",fontsize=10)
    ax.text(-.625,-.56,'1 · K · USB_VBUS',ha='center',va='top',fontsize=8)
    ax.text(.625,-.56,'2 · A · GND',ha='center',va='top',fontsize=8)
    ax.set_aspect('equal'); ax.set_xlim(-1.03,1.03); ax.set_ylim(-.72,.7)
    ax.set_xlabel('mm relative to D4 center'); ax.grid(alpha=.14)
axs[0].set_ylabel('Top view: native board +Y downward\n(symmetric terminal envelopes)')
fig.suptitle('D4 / ESDA7P120-1U1M · P3 native land versus ST DS14419 Rev 4',fontsize=14,fontweight='bold',y=.99)
fig.text(.5,.11,'Blue dashed: ST rectangular recommendation  ·  Amber: native copper/paste R0.1375\n'
         'Purple: exported mask polygon  ·  Green: terminal rectangular envelope  ·  Dotted: nominal package body',
         ha='center',fontsize=10)
fig.text(.5,.015,'Assumptions: e=1.05 mm typical, centered placement; L/b from ST min/typ/max. Pin-1 chamfer is undimensioned and omitted.\n'
         'These are geometric overlaps, not solder-joint qualification or the unavailable JLC component model.',ha='center',fontsize=9,color='#4b5563')
fig.subplots_adjust(left=.06,right=.99,top=.81,bottom=.29,wspace=.15)
fig.savefig(HERE/'d4-overlap-overlay.png',dpi=180)
fig.savefig(HERE/'d4-overlap-overlay.svg')
assert sha(ROOT/'controller.kicad_pcb') == EXPECTED
print(json.dumps(dict(cases=cases,areas=out['land_areas_mm2'],unchanged_native_sha256=EXPECTED),indent=2))
