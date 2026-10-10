"""Bounded two-layer native geometry proposal with explicitly screened bridge vias."""
import hashlib,json,pathlib,heapq,math,time
import numpy as np,shapely
from shapely.geometry import Point,LineString,box
import native43_geometry as G
H=pathlib.Path(__file__).resolve().parent;A=(18.45,24.095);B=(26.0,22.6);step=.1;roi=box(12,8,39,25)
remove={'38e0887e-ae81-480f-82c7-f32e7ea12c27','cad1419a-e60e-4274-b9ad-78e419772ee4'}
G.OBJECTS=[z for z in G.OBJECTS if z[0]['uuid'] not in remove]
bec=[[15.021874,20.464544],[17.7,23.7],[17.7,24.8],[24.147805,24.648486]]
for i,(a,b) in enumerate(zip(bec,bec[1:])):G.OBJECTS.append(({'uuid':'proposed-BEC-'+str(i),'kind':'track','net':'+5V_BEC'},{'In3.Cu':LineString([a,b]).buffer(.3,quad_segs=256)}, {},None))
xs=np.arange(12,39.000001,step);ys=np.arange(8,25.000001,step);nx,ny=len(xs),len(ys);size=nx*ny;xy=np.array([(round(x,6),round(y,6)) for x in xs for y in ys]);pts=shapely.points(xy);Ts=[];Fs=[];t0=time.monotonic()
LAYERS=['F.Cu','B.Cu','In2.Cu','In3.Cu']
for layer in LAYERS:
 T,V,_=G.obstacles('DSM_RX_MCU',layer);T=[o for o in T if o['geometry'].distance(roi)<o['required_center_distance_mm']+.1];Ts.append(T)
 blocked=shapely.union_all([o['geometry'].buffer(o['required_center_distance_mm']+.01,quad_segs=32) for o in T]);Fs.append(~shapely.intersects(pts,blocked))
V=[o for o in V if o['geometry'].distance(roi)<o['required_center_distance_mm']+.1];blocked=shapely.union_all([o['geometry'].buffer(o['required_center_distance_mm']+.01,quad_segs=32) for o in V]);viafree=~shapely.intersects(pts,blocked)
def index(p):return int(round((p[0]-xs[0])/step))*ny+int(round((p[1]-ys[0])/step))
start,end=index(A),index(B);prev={};cost={l*size+start:0 for l in range(4)};queue=[(math.dist(A,B),l*size+start) for l in range(4)];visited=set();found=None
while queue and time.monotonic()-t0<35:
 _,u=heapq.heappop(queue)
 if u in visited:continue
 visited.add(u);l,k=divmod(u,size);i,j=divmod(k,ny)
 if k==end and l==2:found=u;break
 edges=[]
 for di,dj in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
  ii,jj=i+di,j+dj
  if not(0<=ii<nx and 0<=jj<ny):continue
  v=ii*ny+jj
  if not Fs[l][v]:continue
  if di and dj and(not Fs[l][ii*ny+j] or not Fs[l][i*ny+jj]):continue
  edges.append((l*size+v,step*math.hypot(di,dj)))
 if viafree[k]:
  edges.extend((nl*size+k,2.0) for nl in range(4) if nl!=l and Fs[nl][k])
 for v,weight in edges:
  c=cost[u]+weight
  if c<cost.get(v,math.inf):cost[v]=c;prev[v]=u;heapq.heappush(queue,(c+math.dist(xy[v%size],B),v))
r=dict(schema='f722-DSM-inner-bridge-proposal/v1',board_sha256=G.EXPECTED,script_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),native_sha256=hashlib.sha256(G.SOURCE.read_bytes()).hexdigest(),grid_step_mm=step,search_guard_mm=.01,via_grid_count=int(viafree.sum()),found=found is not None,visited=len(visited),seconds=time.monotonic()-t0)
if found is not None:
 ids=[found]
 while ids[-1] in prev:ids.append(prev[ids[-1]])
 ids.reverse();chunks=[];current=[];vl=[]
 for u in ids:
  l,k=divmod(u,size);p=list(A) if u==ids[0] else list(map(float,xy[k]))
  if current and l!=current[0]:chunks.append(current);vl.append(p);current=[]
  if not current:current=[l,[]]
  current[1].append(p)
 chunks.append(current);paths=[]
 for l,path in chunks:
  simple=[path[0]];i=0
  while i<len(path)-1:
   j=len(path)-1
   while j>i+1:
    line=LineString([path[i],path[j]])
    if all(line.distance(o['geometry'])-o['required_center_distance_mm']>=.01 for o in Ts[l]):break
    j-=1
   simple.append(path[j]);i=j
  rr=G.check(LineString(simple),Ts[l]);paths.append(dict(layer=LAYERS[l],points=simple,length_mm=LineString(simple).length,minimum_exact_excess_mm=rr[0]['extra_clearance_mm'],source_clear=rr[0]['extra_clearance_mm']>=G.ERROR,witnesses=rr[:5]))
 r.update(paths=paths,bridge_vias=[dict(xy=p,minimum_exact_excess_mm=G.check(Point(p),V)[0]['extra_clearance_mm']) for p in vl])
r['scope']='Native source clearance proposal only. New-object mutual via/track interactions, finite entries, actual refill/reference, complete R38 connection and native adoption gates pending. No board saved.'
(H/'R38-four-layer-branch-proposal.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
