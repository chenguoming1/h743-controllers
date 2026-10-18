import json, numpy as np, math, os
os.environ['MPLCONFIGDIR']='/tmp/nexus-servo-mpl'
from shapely.geometry import Polygon
from shapely import contains_xy
class Path:
 def __init__(self,points):self.polygon=Polygon(points)
 def contains_points(self,points):return contains_xy(self.polygon,points[:,0],points[:,1])
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu
from scipy.sparse.csgraph import connected_components
from pathlib import Path as FS
import sys
OUT=FS(__file__).resolve().parent; NAME=sys.argv[1] if len(sys.argv)>1 else 'four-layer'; LAYERS=['F.Cu','In1.Cu','In2.Cu','B.Cu'] if NAME=='four-layer' else ['F.Cu','B.Cu']; WEIGHTS={x:(55/60 if x.startswith('In') else 1) for x in LAYERS}; d=json.load(open(OUT/(NAME+'-geometry.json')))
# Small read-only DC sheet screen: source polygons never modified or refilled.
def grid(net,h):
 xs=np.arange(99.8+h/2,122.6,h);ys=np.arange(99.8+h/2,111.1,h); X,Y=np.meshgrid(xs,ys);pts=np.c_[X.ravel(),Y.ravel()];N=len(pts)
 mask=np.zeros((len(LAYERS),N),bool); terminal=np.full((len(LAYERS),N),-1,int)
 for z in d['zones']:
  if z['net']!=net:continue
  for ln,polys in z['filled'].items():
   li=LAYERS.index(ln)
   for p in polys:
    a=Path(p['outer']).contains_points(pts)
    for hole in p['holes']:a &= ~Path(hole).contains_points(pts)
    mask[li]|=a
 for t in d['tracks']:
  if t['net']!=net:continue
  if t['type']=='PCB_VIA':continue
  li=LAYERS.index(t['layer']);a=np.array(t['start']);b=np.array(t['end']);v=b-a
  s=np.clip(((pts-a)@v)/(v@v),0,1) if v@v>0 else np.zeros(N)
  mask[li] |= np.sum((pts-a-s[:,None]*v)**2,axis=1)<(t['width']/2)**2
 ports=[]
 for f in d['footprints']:
  for p in f['pads']:
   if p['net']!=net:continue
   x,y=p['xy'];w,ht=p['size']; a=(pts[:,0]-x);b=(pts[:,1]-y)
   shape=(a*a+b*b<(w/2)**2) if f['ref']=='J1' else ((abs(a)<w/2)&(abs(b)<ht/2))
   hole=a*a+b*b<(p['drill'][0]/2)**2 if p['drill'][0] else np.zeros(N,bool)
   for li,ln in enumerate(LAYERS):
    if ln in p['layers']:
     pid=len(ports);ports.append(f['ref']+'.'+p['number']+':'+ln)
     mask[li] |= shape
     mask[li] &= ~hole
     terminal[li,shape&~hole]=pid
 for v in d['tracks']:
  if v['net']!=net or v['type']!='PCB_VIA':continue
  x,y=v['start'];rr=(pts[:,0]-x)**2+(pts[:,1]-y)**2
  shape=rr<(v['width']/2)**2;hole=rr<(v['drill']/2)**2
  for li,ln in enumerate(LAYERS):
   if ln not in v['layers']:continue
   pid=len(ports);ports.append('VIA:'+v['uuid']+':'+ln)
   mask[li]|=shape;mask[li]&=~hole;terminal[li,shape&~hole]=pid
 # Each annular land face is ideal; opposite faces are NOT shorted here.
 # Finite barrel resistances are added explicitly by the circuit stage.
 # Internal within-land/pin/solder resistance is still excluded.
 node=np.full((len(LAYERS),N),-1,int);k=len(ports)
 for li in range(len(LAYERS)):
  for i in np.flatnonzero(mask[li]):
   if terminal[li,i]>=0:node[li,i]=terminal[li,i]
   else:node[li,i]=k;k+=1
 rr=[];cc=[];gg=[]
 for li in range(len(LAYERS)):
  a=node[li].reshape(Y.shape)
  for u,v in [(a[:,:-1],a[:,1:]),(a[:-1,:],a[1:,:])]:
   ok=(u>=0)&(v>=0)&(u!=v);u=u[ok];v=v[ok]
   rr.extend(np.r_[u,v,u,v]);cc.extend(np.r_[u,v,v,u]);gg.extend(np.r_[np.ones(len(u)*2),-np.ones(len(u)*2)]*WEIGHTS[LAYERS[li]])
 L=coo_matrix((gg,(rr,cc)),shape=(k,k)).tocsr();ncomp,labels=connected_components(L,directed=False)
 # Condense each terminal against all other terminals. Component islands excluded explicitly.
 used=np.flatnonzero(np.isin(labels,labels[:len(ports)]))
 missing=[]
 pidx=np.arange(len(ports)); internal=np.setdiff1d(used,pidx)
 f=splu(L[internal][:,internal].tocsc());A=L[internal][:,pidx].toarray()
 K=L[pidx][:,pidx].toarray()-A.T@f.solve(A)
 # unit sheet resistance matrix: V=A*ohms-per-square; finite pad electrodemodel.
 Z=None
 return {'source_sha256':d['sha256'],'net':net,'h_mm':h,'layers':LAYERS,'reference_um':60,'layer_weights':WEIGHTS,'ports':ports,'K_unit_sheet_S':K.tolist(),'Z_unit_sheet_ohm':Z,'nodes':k,'components':ncomp},(xs,ys,mask,terminal)

out=[]
for h in [.10,.075,.05]:
 for net in ['VX','GND']:
  a,_=grid(net,h);out.append(a);print(net,h,a['nodes'],len(a['ports']),flush=True)
(OUT/(NAME+'-sheet-model.json')).write_text(json.dumps(out,indent=2))
