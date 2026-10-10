import plan,json,time,math,heapq
from shapely.geometry import Point,LineString,box
import shapely
m=plan.m;started=time.monotonic();net='RPM_HV';keys=['R25.2','U16.1'];obs=plan.trace_obs(net,'F.Cu',keys[1])[0]
roi=box(9,12,20.3,22);free=roi.difference(plan.solid(obs,roi.bounds));shapely.prepare(free)
a,b=[plan.KEY[k]['xy']for k in keys];STEP=.04
# Ordinary-grid planning is not the acceptance gate; each final line is checked
# against the unbuffered native polygons and exact physical distances below.
def xy(n):return [round(a[0]+n[0]*STEP,6),round(a[1]+n[1]*STEP,6)]
def okay(p):return free.covers(LineString(p))
q=[(math.dist(a,b),0,(0,0))];dist={(0,0):0};prev={};goal=None;last=None;visited=0
while q and time.monotonic()-started<30 and visited<60000:
 _,cost,node=heapq.heappop(q)
 if cost!=dist[node]:continue
 pt=xy(node);visited+=1
 if math.dist(pt,b)<.35 and okay([pt,b]):goal=node;last=b;break
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
  nxt=(node[0]+dx,node[1]+dy);nc=cost+STEP*math.hypot(dx,dy)
  if nc>=dist.get(nxt,1e30):continue
  npt=xy(nxt)
  if not free.covers(Point(npt)) or not okay([pt,npt]):continue
  dist[nxt]=nc;prev[nxt]=node;heapq.heappush(q,(nc+math.dist(npt,b),nc,nxt))
out={'source_board_sha256':m.EXPECTED,'net':net,'found':goal is not None,'visited':visited,'seconds':time.monotonic()-started,'roi':roi.bounds,'step':STEP}
if goal:
 rev=[goal]
 while rev[-1]!=(0,0):rev.append(prev[rev[-1]])
 path=[xy(n)for n in reversed(rev)]+[last]
 simplified=[path[0]];i=0
 while i<len(path)-1:
  for j in range(len(path)-1,i,-1):
   if okay([path[i],path[j]]):simplified.append(path[j]);i=j;break
 out['raw_points']=path;out['points']=simplified
 rr=m.check(LineString(simplified),obs,True);out['minimum']=rr[0];out['nearest']=rr[:10];out['violations']=[r for r in rr if r['extra_clearance_mm']<m.ERROR];out['length']=LineString(simplified).length
(plan.HERE/'rpm-F-route.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['raw_points','nearest']},indent=2))
