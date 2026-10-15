"""Read-only source copper and saved-fill visualization."""
import sys
sys.path.insert(0,'/workspace/shared/nexus-usb-stack-review/r57-inner-pair')
from source_context import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle
R=D/'reference';r=json.loads((R/'reference-analysis.json').read_text());p=np.load(R/'numerical-projection.npz');P=p['centers'];N=p['normals']
fig,axs=plt.subplots(1,3,figsize=(13,15),sharex=True,sharey=True)
colors={'3V3':'#dd8000','5V':'#c5163c','5V_BUCK':'#7c32b3','5V_SENSE':'#147d72','DSM_DATA':'#147ac4','SPI1_MISO':'#bf5b00'}
for ax,l in zip(axs,['In1.Cu','In2.Cu','In4.Cu']):
 for pts,ids in zip(fills[l],fill_ids[l]):ax.add_patch(Polygon(pts,color='#cce3cf',lw=0,zorder=1))
 if l=='In2.Cu':
  for o in r['non_ground_in2_tracks']:
   t=o['source']; a=t['start'];b=t['end'];ax.plot([a[0],b[0]],[a[1],b[1]],color=colors.get(t['net'],'#888888'),lw=t['width']*45,solid_capstyle='round',alpha=.72,zorder=2)
  for o in r['non_ground_through_vias']:
   v=o['source'];ax.add_patch(Circle(v['at'],v['diameter']/2,ec='#333333',fc='#cccccc',lw=.7,zorder=2))
  for net,y in [('5V_BUCK',123.63),('3V3',120.32),('5V',118.1),('5V_SENSE',115.33),('SPI1_MISO',113.85),('DSM_DATA',112.05),('3V3',111.05)]:
   ax.text(111.75,y,net,color=colors[net],fontsize=8,ha='right',va='center',bbox=dict(fc='white',ec='none',alpha=.85),zorder=6)
 for off in [-.1385,.1385]:
  q=P+off*N;ax.plot(q[:,0],q[:,1],color='#0054ff',lw=.15*45,alpha=.75,zorder=3)
 for off in [-.2135,.2135]:
  q=P+off*N;ax.plot(q[:,0],q[:,1],color='#001a60',lw=.5,zorder=4)
 mask=~p['in2'][:,3] if l=='In2.Cu' else ~p['in1' if l=='In1.Cu' else 'in4'][:,3]
 ax.scatter(P[mask,0],P[mask,1],s=.4,c='black',zorder=5)
 ax.set_title(l+' saved GND projection');ax.set_xlim(108.85,111.9);ax.set_ylim(124.2,110.65);ax.set_aspect('equal');ax.grid(alpha=.2);ax.set_xlabel('x (mm)')
axs[0].set_ylabel('y (mm)');fig.suptitle('r57 fixed In3 .150/.127/.150 trunk, north endpoint y110.85\nGreen: retained saved GND; blue: proposed In3 lanes; black center marks: missing saved GND\nProjection only; no refill, finite connectivity, or impedance claim',fontsize=12)
fig.tight_layout();fig.savefig(R/'saved-reference-and-crossings.png',dpi=160);plt.close(fig)
