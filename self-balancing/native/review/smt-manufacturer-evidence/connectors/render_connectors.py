#!/usr/bin/python3
import os,json,pathlib
os.environ['MPLCONFIGDIR']='/tmp/p3-connector-mpl'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle
O=pathlib.Path(__file__).parent
d=json.loads((O/'native-connectors.json').read_text())
fig,axes=plt.subplots(2,2,figsize=(13,13))
for ax,r in zip(axes.flat,['J3','J4','J5','J2']):
 q=d['connectors'][r]
 for s in q['graphics']:
  l=s['layer']
  if 'Fab' in l or 'Courtyard' in l:
   color='#1379a5' if 'Fab' in l else '#777777'
   ax.plot([s['start_mm'][0],s['end_mm'][0]],[s['start_mm'][1],s['end_mm'][1]],color=color,lw=1.6 if 'Fab' in l else .7,ls='-' if 'Fab' in l else '--')
 plotted=set()
 for pad in q['pads']:
  x,y=pad['native_xy_mm'];a,b,c,e=pad['bbox_mm'];key=(x,y,a,b,c,e)
  if key in plotted:continue
  plotted.add(key)
  shape=Rectangle((a,b),c-a,e-b,facecolor='#e39c30',edgecolor='#704d10',lw=.6,alpha=.85)
  ax.add_patch(shape)
  dx,dy=pad['drill_local_mm']
  if dx:
   if pad['angle_deg'] in [90,270]:dx,dy=dy,dx
   radius=min(dx,dy)/2
   ax.add_patch(FancyBboxPatch((x-dx/2,y-dy/2),dx,dy,boxstyle=f'round,pad=0,rounding_size={radius}',facecolor='white',edgecolor='black',lw=.7))
  label=pad['number']
  if label and label not in ['S1','MP']:ax.text(x,y,label,ha='center',va='center',fontsize=6)
 edge=0 if r in ['J3','J4'] else 38
 ax.axvline(edge,color='#b32130',lw=2,label='Actual board edge')
 x,y=q['native_anchor_mm'];ax.plot(x,y,'k+',ms=9,mew=1.3);ax.text(x+.15,y+.2,'Native anchor',fontsize=7)
 bx,by=q['native_body_center_mm'];ax.plot(bx,by,'o',color='#1379a5',ms=3)
 if r=='J2':
  ax.add_patch(Rectangle((30.68,15.53),7.35,8.94,fill=False,edgecolor='#24a084',linestyle=':',lw=2))
  ax.axvline(37.54,color='#24a084',linestyle=':',lw=1)
  note='Fab mouth: X38.000\nHRO nominal mouth: X38.030\nHRO reference PCB edge: X37.540\nFront holes: native 0.60×1.20\nHRO recommendation: 0.60×1.40'
  ax.set_xlim(28.8,40.3);ax.set_ylim(26,14)
 else:
  note='Fab mouth inset: 0.625 mm\nNearest MP copper inset: 0.425 mm\nCourtyard overhang: 0.080 mm\nAll connector pads are SMD'
  if r=='J3':note+='\nJ3 body-to-land datum unqualified'
  ax.set_xlim(-1.1,8) if r in ['J3','J4'] else ax.set_xlim(30.3,39.2)
  body=q['graphic_bounds_mm']['B.Fab'];ax.set_ylim(body[3]+2,body[1]-2)
 ax.text(.02,.02,note,transform=ax.transAxes,fontsize=8,va='bottom',bbox={'facecolor':'white','alpha':.9,'edgecolor':'#cccccc'})
 ax.set_title(r+' | '+q['side']+' | native board coordinates',fontsize=11)
 ax.set_aspect('equal');ax.grid(alpha=.15);ax.set_xlabel('Native X (mm)');ax.set_ylabel('Native Y (mm, down)')
fig.suptitle('P3 connector geometry: source SHA 0850991d…795c3696\nOrange = native pad bounding boxes; blue = Fab; grey dashed = courtyard; red = board edge',fontsize=12)
fig.tight_layout(rect=[0,0,.99,.955]);fig.savefig(O/'connector-edge-evidence.png',dpi=180)
