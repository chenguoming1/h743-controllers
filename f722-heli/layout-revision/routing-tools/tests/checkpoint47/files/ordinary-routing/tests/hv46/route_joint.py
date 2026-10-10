import joint_hypothesis as j
import plan,json,time,math,heapq
import shapely
from shapely.geometry import Point,LineString,box
m=j.m;started=time.monotonic();results=[]
def route(layer,a,b,bounds,step):
 begun=time.monotonic();roi=box(*bounds);obs=j.obstacles(layer);free=roi.difference(plan.solid(obs,bounds));shapely.prepare(free)
 def xy(n):return [round(a[0]+n[0]*step,6),round(a[1]+n[1]*step,6)]
 def okay(p):return free.covers(LineString(p))
 for p in m.paths2(a,b):
  if okay(p):
   checks=j.tracecheck(layer,p)
   if checks[0]['extra_clearance_mm']>=m.ERROR:return {'layer':layer,'found':True,'points':p,'minimum':checks[0],'length':LineString(p).length,'kind':'direct'}
 queue=[(math.dist(a,b),0,(0,0))];dist={(0,0):0};prev={};goal=None;visited=0
 while queue and time.monotonic()-started<30 and visited<60000:
  _,cost,node=heapq.heappop(queue)
  if cost!=dist[node]:continue
  pt=xy(node);visited+=1
  if math.dist(pt,b)<.15 and okay([pt,b]):goal=node;break
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
   nxt=(node[0]+dx,node[1]+dy);nc=cost+step*math.hypot(dx,dy)
   if nc>=dist.get(nxt,1e30):continue
   npt=xy(nxt)
   if not free.covers(Point(npt))or not okay([pt,npt]):continue
   dist[nxt]=nc;prev[nxt]=node;heapq.heappush(queue,(nc+math.dist(npt,b),nc,nxt))
 r={'layer':layer,'found':goal is not None,'visited':visited,'seconds':time.monotonic()-begun,'roi':bounds,'step':step,'origin':a,'target':b}
 if goal is not None:
  rev=[goal]
  while rev[-1]!=(0,0):rev.append(prev[rev[-1]])
  path=[xy(n)for n in reversed(rev)]+[b];simplified=[path[0]];i=0
  while i<len(path)-1:
   for k in range(len(path)-1,i,-1):
    if okay([path[i],path[k]]):simplified.append(path[k]);i=k;break
  checks=j.tracecheck(layer,simplified);r.update(points=simplified,raw_points=path,minimum=checks[0],violations=[o for o in checks if o['extra_clearance_mm']<m.ERROR],length=LineString(simplified).length)
 return r
for label,layer,a,b,bounds,step in [('Q2escape','F.Cu',[19.55,7.9125],j.SOURCE,[16.7,6.4,22.4,9.9],.02),('U16escape','F.Cu',j.TARGET,[18.7,17.1375],[18,16,20,18.8],.02),('In3trunk','In3.Cu',j.SOURCE,j.TARGET,[16,8.5,23,19.2],.04),('In2trunk','In2.Cu',j.SOURCE,j.TARGET,[16,8.5,23,19.2],.04),('Btrunk','B.Cu',j.SOURCE,j.TARGET,[16,8.5,23,19.2],.04)]:
 if label=='In2trunk'and results[-1]['found']:break
 if label=='Btrunk'and results[-1]['found']:break
 r=route(layer,a,b,bounds,step);r['label']=label;results.append(r);print(json.dumps({k:v for k,v in r.items()if k!='raw_points'}),flush=True)
 if not r['found']and label in ['Q2escape','U16escape']:break
out={'source_board_sha256':m.EXPECTED,'routes':results,'repairs':j.repairs,'COREvia':j.CORE['xy'],'SBUSvias':[j.SOURCE,j.TARGET],'complete':len(results)>=3 and all(x['found']and not x.get('violations') for x in results[:2])and any(x['found']and not x.get('violations')for x in results[2:]),'seconds':time.monotonic()-started,'native_board_constructed':False}
(plan.HERE/'complete-joint-proposal.json').write_text(json.dumps(out,indent=2)+'\n')
