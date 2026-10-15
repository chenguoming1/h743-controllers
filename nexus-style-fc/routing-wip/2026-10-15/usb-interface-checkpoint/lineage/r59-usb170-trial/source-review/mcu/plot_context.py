import sys
sys.path.insert(0,'/workspace/shared/nexus-usb-stack-review/r57-inner-pair')
from static_clearance import *
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Polygon
from matplotlib.transforms import Affine2D
colors={n:plt.get_cmap('tab20')(i%20) for i,n in enumerate(sorted(set(t['net'] for t in tracks)))}
for layer in ['B.Cu','In2.Cu','F.Cu','In3.Cu']:
 fig,ax=plt.subplots(figsize=(17,14),dpi=150)
 for t in tracks:
  if t['layer']==layer and any(108<=p[0]<=119 and 103.5<=p[1]<=113 for p in [t['start'],t['end']]):
   ax.plot(*zip(t['start'],t['end']),c='red' if t['net'].startswith('USB_') else colors[t['net']],lw=t['width']*30,alpha=.8)
   mid=np.mean([t['start'],t['end']],axis=0)
   if 108<=mid[0]<=119 and 103.5<=mid[1]<=113:ax.text(*mid,t['net'],fontsize=5)
 for v in vias:
  if 108<=v['at'][0]<=119 and 103.5<=v['at'][1]<=113:
   ax.add_patch(Circle(v['at'],v['diameter']/2,color='red' if v['net'].startswith('USB_') else colors[v['net']],alpha=.6));ax.text(*v['at'],v['net'],fontsize=6)
 for p in pads:
  if layer not in p['layers'] and '*.Cu' not in p['layers']:continue
  if 108<=p['at'][0]<=119 and 103.5<=p['at'][1]<=113:
   sx,sy=p['size'];x,y=p['at'];cs=np.array([[-sx/2,-sy/2],[sx/2,-sy/2],[sx/2,sy/2],[-sx/2,sy/2]])
   theta=math.radians(-p['rotation']);rot=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
   cs=cs@rot.T+[x,y];ax.add_patch(Polygon(cs,facecolor='gray',alpha=.4));ax.text(x,y,p['ref']+'.'+p['pin']+' '+p['net'],fontsize=6,rotation=90 if sy>1 else 0)
 ax.set_xlim(108,119);ax.set_ylim(113,103.5);ax.set_aspect('equal');ax.set_xticks(np.arange(108,119.1,.25),minor=True);ax.set_yticks(np.arange(103.5,113.1,.25),minor=True);ax.grid(which='both',alpha=.25);ax.set_title(layer)
 fig.savefig(D/'mcu'/f'{layer}.png');plt.close(fig)
print('USB MCU')
for t in usbtracks:
 if any(108<=p[0]<=119 and 103.5<=p[1]<=113 for p in [t['start'],t['end']]):print(json.dumps(t))
