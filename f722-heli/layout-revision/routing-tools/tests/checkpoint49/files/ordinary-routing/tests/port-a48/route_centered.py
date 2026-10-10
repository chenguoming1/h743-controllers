import inspect_access as a
import shapely,numpy as np
from shapely.geometry import Point,LineString,box
import time,heapq,math,json,sys
m=a.m
plan=json.loads((a.HERE/'compact-mcu-proposal.json').read_text())
m.OBJECTS=[q for q in m.OBJECTS if q[0]['uuid'] not in plan['removed_source_ids']]
for i,p in enumerate(plan['paths']):
 o=dict(uuid='proposal-path-'+str(i),net=p['net'],kind='track');m.OBJECTS.append((o,{p['layer']:LineString(p['points']).buffer(.0635,quad_segs=32)},{},None))
for i,v in enumerate(plan['vias']+[dict(net='+3V3_CORE',xy=[14.7,7.2]),dict(net='PORT_B_RX_MCU',xy=[17.93,10.79]),dict(net='RPM_MCU',xy=[15.1,9.59])]):
 o=dict(uuid='reserved-via-'+str(i),net=v['net'],kind='via',barrel_layers=m.N['copper_layers']);m.OBJECTS.append((o,{l:Point(v['xy']).buffer(.225,quad_segs=32)for l in m.N['copper_layers']},{},Point(v['xy']).buffer(.1,quad_segs=32)))
servo=json.loads((a.HERE.parent/'servo48/completion-search-inner-negative.json').read_text())
for i,p in enumerate(servo['routes'][:7]):
 o=dict(uuid='servo-reservation-route-'+str(i),net=p['net'],kind='track');m.OBJECTS.append((o,{p['layer']:LineString(p['points']).buffer(p['width']/2,quad_segs=32)},{},None))

# Reserve the concurrent complete flash fanouts, without adopting their board.
j=json.loads((a.HERE.parent/'joint-flash-group/native-stage48/f722-heli.native.json').read_text())
sourceids={o['uuid']for o,_,_,_ in m.OBJECTS};reserved=[]
for o in j['objects']:
 if o['uuid']in sourceids or o['net']=='FLASH_MOSI':continue
 m.OBJECTS.append((o,{l:m.geom(ps)for l,ps in o['copper'].items()},{l:m.geom(v['polygons'])for l,v in o.get('mask',{}).items()}if o.get('smd')else{},m.geom(o['drill']['outside'])if o.get('drill')else None));reserved.append(o['uuid'])

def route(net,layer,start,end,seconds=35,name=None,step=.025):
 t0=time.monotonic();obs=a.obs(net,layer)[0];free=m.OUTLINE.difference(a.solid(obs).buffer(.005));shapely.prepare(free);roi=(9.8,4.5,22.6,14.6)
 def xy(n):return(round(start[0]+n[0]*step,6),round(start[1]+n[1]*step,6))
 def okay(p):return free.covers(LineString(p))
 xmin,xmax=math.floor((roi[0]-start[0])/step),math.ceil((roi[2]-start[0])/step);ymin,ymax=math.floor((roi[1]-start[1])/step),math.ceil((roi[3]-start[1])/step)
 xx=np.arange(xmin,xmax+1);yy=np.arange(ymin,ymax+1);X,Y=np.meshgrid(start[0]+xx*step,start[1]+yy*step,indexing='ij');legal=shapely.contains_xy(free,X,Y)
 def legalnode(n):return xmin<=n[0]<=xmax and ymin<=n[1]<=ymax and legal[n[0]-xmin,n[1]-ymin]
 q=[(math.dist(start,end),0,(0,0))];dist={(0,0):0};prev={};goal=None;visited=0
 while q and time.monotonic()-t0<seconds and visited<600000:
  _,cost,node=heapq.heappop(q)
  if cost!=dist[node]:continue
  pt=xy(node);visited+=1
  if math.dist(pt,end)<.7 and okay([pt,end]):goal=node;break
  for dx,dy in[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
   nxt=(node[0]+dx,node[1]+dy);nc=cost+step*math.hypot(dx,dy)
   if nc>=dist.get(nxt,1e30)or not legalnode(nxt):continue
   npt=xy(nxt)
   if not okay([pt,npt]):continue
   dist[nxt]=nc;prev[nxt]=node;heapq.heappush(q,(nc+1.3*math.dist(npt,end),nc,nxt))
 out={'source_board_sha256':m.EXPECTED,'net':net,'layer':layer,'found':goal is not None,'visited':visited,'seconds':time.monotonic()-t0,'step':step,'roi':roi,'reserved_joint_flash_ids':reserved}
 if goal is not None:
  rev=[goal]
  while rev[-1]!=(0,0):rev.append(prev[rev[-1]])
  path=[xy(n)for n in reversed(rev)]+[end];simple=[path[0]];i=0
  while i<len(path)-1:
   for k in range(len(path)-1,i,-1):
    if okay([path[i],path[k]]):simple.append(path[k]);i=k;break
  rr=m.check(LineString(simple),obs,True);out.update(points=simple,length=LineString(simple).length,minimum=rr[0],violations=[r for r in rr if r['extra_clearance_mm']<m.ERROR],nearest=rr[:10])
 print(json.dumps({k:v for k,v in out.items()if k not in['nearest','reserved_joint_flash_ids']},indent=2),flush=True)
 (a.HERE/((name or net+'-'+layer)+'.json')).write_text(json.dumps(out,indent=2)+'\n');return out

if __name__=='__main__':
 for layer in ['In2.Cu','In3.Cu']:
  r=route('PORT_A_RX_MCU',layer,[12.45,5.55],[16.6,10.88],40,'rx-centered-'+layer,step=.04)
  if r['found']:break
