import json,pathlib,sys,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[3]/'python-deps'))
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
HERE=pathlib.Path(__file__).resolve().parent;D=HERE/'candidate01';n=json.load(open(D/'f722-heli.native.json'));m=json.load(open(D/'owner-mechanical-geometry.json'))['current']['footprints']
def geom(p):return unary_union([Polygon(q['outer'],q['holes'])for q in p])
def parts(g):return list(g.geoms)if hasattr(g,'geoms')else[g]
fig,axs=plt.subplots(1,2,figsize=(14,8))
for ax,layer,roi in zip(axs,['B.Cu','F.Cu'],[(14.5,6.5,18,13.5),(19.2,16,24.2,19)]):
 for o in n['objects']:
  if layer not in o['copper']:continue
  g=geom(o['copper'][layer]);color='orange'if o['net']=='ADC_BUS'else('#777777'if o['net']=='GND'else'#477faa')
  if not g.intersects(box(*roi)):continue
  for p in parts(g):
   if p.geom_type=='Polygon':ax.fill(*p.exterior.xy,color=color,alpha=.55)
  if o['kind']=='pad':ax.text(*o['xy'],o['key'],fontsize=7,ha='center')
 for r,f in m.items():
  for p in parts(geom(f['courtyards'].get(layer,[]))):
   if p.geom_type=='Polygon'and p.intersects(box(*roi)):ax.plot(*p.exterior.xy,color='#333333',lw=.5,alpha=.4)
 ax.set(xlim=(roi[0],roi[2]),ylim=(roi[3],roi[1]),title=layer+' actual native copper/courtyards');ax.set_aspect('equal');ax.grid(alpha=.2)
fig.suptitle('ADC_BUS complete tree: C31 inward relocation and R43 portal; orange = ADC_BUS');fig.savefig(D/'placement-detail.png',dpi=150)
