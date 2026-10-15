#!/usr/bin/env python3
"""Dimensioned 2D engineering preview from native candidate contacts + shared contour definition.
Not a native KiCad/3D validation, fabrication drawing, or physical-fit certificate.
"""
import json,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,PathPatch,FancyBboxPatch,Circle
from matplotlib.path import Path as MPath
import header_interface_geometry as g
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/header-interface-candidate'
report=json.loads((OUT/'static-validation.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
fig=plt.figure(figsize=(16,12),facecolor='white')
grid=fig.add_gridspec(3,2,height_ratios=[.85,1.2,.95],hspace=.4,wspace=.18)
axm=fig.add_subplot(grid[0,:]);axc=fig.add_subplot(grid[1,0]);axs=fig.add_subplot(grid[1,1]);axt=fig.add_subplot(grid[2,:]);axt.axis('off')
fig.suptitle('Nexus header-interface candidate 01 | UNFINISHED',fontsize=20,fontweight='bold',y=.982)
fig.text(.5,.945,'Dimensions in mm. Native-text / analytic study only. Do not fabricate or assemble from this candidate.',ha='center',color='#b33434',fontsize=12)
colors={'main':'#d7e7de','child':'#d7e7de','slot':'white','inner':'#da8753','outer':'#528ec7'}

def dim(ax,a,b,label,off=0):
    ax.annotate('',xy=a,xytext=b,arrowprops={'arrowstyle':'|-|','lw':.8,'color':'#495467'})
    ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+off,label,ha='center',va='bottom',fontsize=9,color='#334155',bbox={'fc':'white','ec':'none','pad':.6})

def child_poly():
    # exact semicircle samples, <=0.001 mm sagitta at R0.5 (preview only).
    pts=[(0,-7.9),(0,0)]
    for sh in g.tab_outline():
        if sh[0]=='line':pts.append(sh[-1])
        else:
            a,m,b=sh[1:];cx=(a[0]+b[0])/2;r=.5
            pts += [(cx+r*math.cos(math.pi+k*math.pi/80),r*math.sin(math.pi+k*math.pi/80)) for k in range(1,81)]
    pts += [(22.4,-7.9)]
    pts += [(21.9+.5*math.cos(k*math.pi/80),-7.9-.5*math.sin(k*math.pi/80)) for k in range(1,41)]
    pts += [(.5,-8.4)]
    pts += [(.5-.5*math.sin(k*math.pi/80),-7.9-.5*math.cos(k*math.pi/80)) for k in range(1,41)]
    return pts

# Main mating band, top-view orientation; contact copper is on B.Cu.
axm.set_title('Main board: actual routed cutouts and B.Cu lands (top-view coordinates)',loc='left',fontweight='bold')
axm.add_patch(FancyBboxPatch((0,0),22.4,7,boxstyle='round,pad=0,rounding_size=0.5',fc=colors['main'],ec='#385749'))
for cx,cy in g.SLOT_CENTERS:
    axm.add_patch(FancyBboxPatch((cx-5,cy-1.05),10,2.1,boxstyle='round,pad=0,rounding_size=0.5',fc='white',ec='#263546',lw=1.3))
for p in report['mating_pads']:
    if p['board']!='main':continue
    x0,y0,x1,y1=p['box'];color=colors['outer' if y0<1.1 else 'inner'];axm.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fc=color,ec='white',lw=.5));axm.text((x0+x1)/2,(y0+y1)/2,p['net'],ha='center',va='center',fontsize=9)
for c in (5.6,16.8):axm.axvline(c,color='#8390a3',lw=.7,ls=':')
dim(axm,(.6,2.4),(10.6,2.4),'10.0 full length',-.1)
dim(axm,(11.8,2.4),(21.8,2.4),'10.0 full length',-.1)
dim(axm,(5.6,-.65),(16.8,-.65),'11.2 centre pitch',-.1)
axm.annotate('R0.5 × 8',xy=(.75,1.5),xytext=(1.2,-.15),arrowprops={'arrowstyle':'-','lw':.8},fontsize=9)
axm.annotate('2.1 width',xy=(10.5,2.0),xytext=(10.7,3.1),fontsize=9,arrowprops={'arrowstyle':'-','lw':.8})
axm.text(.1,5.15,'Nominal ligaments: outer 0.60 | centre 1.20 | front 1.35. Main lands: ≥0.35 to slot / outline.',fontsize=10)
axm.text(.1,5.7,'Inner lands: signal 1.2 / power 1.6 wide × 0.85 deep. Outer strips: 9.8 × 0.65. Body and connectors unchanged.',fontsize=10)
axm.set_xlim(-.6,23);axm.set_ylim(6,-1.1);axm.set_aspect('equal');axm.axis('off')
# Child outline: physical outer face orientation, overlay inner contacts explicitly identified.
axc.set_title('Child board: true tab / relief contour',loc='left',fontweight='bold')
poly=child_poly();axc.add_patch(plt.Polygon(poly,closed=True,fc=colors['child'],ec='#385749',lw=1.2))
for cx in (5.6,16.8):axc.add_patch(Rectangle((cx-7.892/2,0),7.892,2.346,fc=colors['outer'],alpha=.5))
for p in report['mating_pads']:
    if p['board']!='child' or p['ref'].startswith('K'):continue
    x0,y0,x1,y1=p['box'];axc.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fc=colors['inner'],ec='white',lw=.5));axc.text((x0+x1)/2,1.17,p['net'],rotation=90,ha='center',va='center',fontsize=7)
for k in range(7):
    for yy in (-7.38,-4.84,-2.3):axc.add_patch(Circle((3.58+k*2.54,yy),.75,fill=False,ec='#7d6850',lw=.8))
axc.text(11.2,-5.9,'3 × 7 connector: unchanged',ha='center',fontsize=9)
axc.axhline(0,color='#9a5151',lw=.7,ls='--')
for a,b in g.TABS:dim(axc,(a,3.0),(b,3.0),'8.4',.5)
dim(axc,(0,-9.2),(22.4,-9.2),'22.4 body width',-.1)
axc.annotate('R0.5 root reliefs × 4\nopen to exterior',xy=(10.3,-.5),xytext=(8,-3),ha='center',fontsize=9,arrowprops={'arrowstyle':'->','lw':.8})
axc.text(11.2,4.6,'Tab length 2.6; nominal copper inset 0.254\nBlue: outer strips. Orange: inner lands overlaid.',ha='center',fontsize=9)
axc.set_xlim(-1,23.4);axc.set_ylim(5.3,-9.8);axc.set_aspect('equal');axc.axis('off')
# Nominal assembled section: no asserted solder profile or component envelope.
axs.set_title('Nominal section through slot centre',loc='left',fontweight='bold')
axs.add_patch(Rectangle((0,0),1.35,1.6,fc=colors['main'],ec='#385749'))
axs.add_patch(Rectangle((3.45,0),2.05,1.6,fc=colors['main'],ec='#385749'))
axs.add_patch(Rectangle((1.6,-3),1.6,5.6,fc=colors['child'],ec='#385749'))
axs.plot([1.6,1.6],[0,2.346],lw=3,color=colors['outer']);axs.plot([3.2,3.2],[0,2.346],lw=3,color=colors['inner'])
axs.plot([.35,1],[1.6,1.6],lw=3,color=colors['outer']);axs.plot([3.8,4.65],[1.6,1.6],lw=3,color=colors['inner'])
dim(axs,(1.6,-2.2),(3.2,-2.2),'1.6 child',-.15)
dim(axs,(1.35,-.6),(3.45,-.6),'2.1 slot',-.15)
axs.annotate('0.746 exposed copper\n(0.586 at 1.76 main thickness)',xy=(3.2,2),xytext=(3.8,3.5),fontsize=9,ha='left',arrowprops={'arrowstyle':'->','lw':.8})
axs.annotate('0.60 nominal solder reach\non each face; fillet not qualified',xy=(3.5,1.65),xytext=(-1.0,4.2),fontsize=9,arrowprops={'arrowstyle':'->','lw':.8})
axs.text(5,0.7,'1.6\nmain',ha='center',fontsize=9)
axs.set_xlim(-1.3,8.5);axs.set_ylim(5,-3.4);axs.set_aspect('equal');axs.axis('off')
# Findings have concise bounded meaning.
left='FIT SCREEN (rigid, centred, perpendicular)\nNominal total play: x 1.466 / y 0.500.\nAdverse sizes: x 0.710 / y 0.140 at R0.5.\nAdd illustrative 0.40 pitch mismatch: x budget 0.310.\nAt R0.60: remaining total x budget only 0.162.\nLoose endpoint: x 1.990 / y 0.860. Fixture required.\nThese assumed tolerances are not process acceptance.'
right='QUALIFICATION GATES\nFlat seating lands: 0.40 / 0.80 / 0.40 nominal.\nIllustrative ±0.10 finished copper alignment retains\n≥1.10 signal / ≥1.50 power x-overlap; verify every net.\nReduced exposed copper / strip area needs current & load tests.\nNo laminate rating, load limit, native DRC or 3D fit approval.\nLocal rerouting + refill + native ERC/parity still required.'
axt.text(.01,.97,left,va='top',linespacing=1.55,fontsize=11);axt.text(.53,.97,right,va='top',linespacing=1.55,fontsize=11)
fig.text(.06,.028,'Bound to main 5d67813b1669… / child f89abf8e2169… | schematic unchanged except child K1/K2 footprint identifiers | Candidate 01',fontsize=8,color='#555')
fig.subplots_adjust(top=.91,bottom=.08,left=.05,right=.98)
for ext in ('svg','png','pdf'):fig.savefig(OUT/f'header-interface-dimensioned-preview.{ext}',dpi=180)
print(OUT/'header-interface-dimensioned-preview.png')
