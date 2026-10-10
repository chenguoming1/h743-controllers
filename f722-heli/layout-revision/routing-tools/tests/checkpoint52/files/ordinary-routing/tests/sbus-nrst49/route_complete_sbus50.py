"""Bounded complete SBUS reconstruction, retaining every accepted50 support function."""
import composite_sbus50 as g
import hashlib,heapq,json,math,time
from pathlib import Path
import shapely
from shapely import unary_union
from shapely.geometry import Point,LineString
s=g.s;H=g.H;R=g.R;START=time.monotonic();BUDGET=115;RESERVE=.0005;OUT=H/'complete-sbus50-proposal01.json'
ports=json.loads((H/'selected-ports-preflight50-v2.json').read_text())
assert all(v['passed']for scenario in ports['results']for v in scenario['vias']+scenario['paths'])
BASE=list(s.OBJECTS);ids={o['uuid']for o,c,m,d in BASE}
changed_ids={o['uuid']for o in g.transition['removed_source_records']}
changed_ids|={o['uuid']for o in g.tail['objects']if o['net']=='SBUS_LV'and o['kind']=='track'and o['uuid']!='187f794e-f820-4425-869b-0ca552a872a2'}
changed_ids|={o['uuid']for o in g.tail['objects']if o.get('ref')=='R45'}
restored=[]
for o in g.tail['objects']:
 if o['uuid']not in ids and o['uuid']not in changed_ids:BASE.append(g.entry(o));restored.append(o['uuid'])
# Preserve both original and proposed component copper/masks where unrelated peers move them.
byid={o['uuid']:o for o,c,m,d in BASE}
for o in g.tail['objects']:
 if o['kind']=='pad'and o['uuid']not in changed_ids and o['uuid']in byid and o['xy']!=byid[o['uuid']].get('xy'):
  q=dict(o,uuid='accepted50-pose-reservation-'+o['uuid']);BASE.append(g.entry(q))
extra_input_bindings={}
bp=R/'tests/port-b48/complete50-route-proposal.json'
if bp.exists():
 extra_input_bindings[str(bp.relative_to(R))]=g.sha(bp)
 for i,p in enumerate(json.loads(bp.read_text())['routes']):
  if p['layer']=='F.Cu':BASE.append((dict(uuid='complete-B-surface-'+str(i),net=p['net'],kind='track'),{'F.Cu':LineString(p['points']).buffer(.0635/math.cos(math.pi/512),quad_segs=128)},{},None))
txp=R/'tests/port-b48/tx-cdt50-reserved.json'
tx=json.loads(txp.read_text());assert tx['passed']and tx['source_board_sha256']==g.tail['board_sha256'];extra_input_bindings[str(txp.relative_to(R))]=g.sha(txp)
BASE.append((dict(uuid='complete-B-reserved-TX-inner',net=tx['net'],kind='track'),{tx['layer']:LineString(tx['points']).buffer(.0635/math.cos(math.pi/512),quad_segs=128)},{},None))
VIA=[]
for v in ports['via_assignments']:
 v=dict(v);v['logical']=('SBUS_MCU::SRC'if v['name']=='MCU-clamp-source'else'SBUS_MCU::DST')if v['net']=='SBUS_MCU'else v['net'];VIA.append(v)
ROUTES=[];ATTEMPTS=[];clamp=s.geom(g.KEY['U13.1']['inside']['B.Cu'])
def parts(x):return[p for p in(x.geoms if hasattr(x,'geoms')else[x])if p.geom_type=='Polygon'and not p.is_empty]
def install(logical):
 objects=[]
 for o,c,m,d in BASE:
  q=dict(o)
  if q['net']=='SBUS_MCU':q['net']='SBUS_MCU::SRC'if q.get('key')=='R45.2'else logical if q.get('key')=='U13.1'else'SBUS_MCU::DST'
  objects.append((q,c,m,d))
 for v in VIA:
  o=dict(uuid='selected-'+v['name'],net=v['logical'],kind='via',barrel_layers=s.N['copper_layers']);objects.append((o,{l:Point(v['xy']).buffer(.225/math.cos(math.pi/512),quad_segs=128)for l in s.N['copper_layers']},{},Point(v['xy']).buffer(.1/math.cos(math.pi/512),quad_segs=128)))
 for i,r in enumerate(ROUTES):
  cu=LineString(r['points']).buffer(.0635/math.cos(math.pi/512),quad_segs=128)
  if r['logical'].startswith('SBUS_MCU::')and r['logical']!=logical and r['layer']=='B.Cu':cu=cu.difference(clamp)
  objects.append((dict(uuid='selected-route-'+str(i),kind='track',net=r['logical']),{r['layer']:cu},{},None))
 s.OBJECTS=objects
def obstacles(logical,layer):install(logical);return s.obstacles(logical,layer)[0]
def free_region(logical,layer,avoid_clamp=False):
 obs=obstacles(logical,layer)
 solid=unary_union([o['geometry'].buffer((o['required_center_distance_mm']+s.ERROR+RESERVE)/math.cos(math.pi/128),quad_segs=32)for o in obs if o['category']!='edge_npth_copper'])
 free=s.OUTLINE.buffer(-(.3175+s.ERROR+RESERVE)).difference(solid)
 if avoid_clamp:free=free.difference(clamp.buffer(.0635+s.ERROR+RESERVE))
 return free,obs
def connected(logical,layer,a,b):
 free,_=free_region(logical,layer);return any(p.covers(Point(a))and p.covers(Point(b))for p in parts(free))
def save(complete=False):
 out=dict(schema='f722-complete-SBUS-native-corridor-proposal/v1',accepted_source_board_sha256=g.tail['board_sha256'],bindings=g.bindings,extra_bindings=extra_input_bindings,restored_accepted50_support_reservations=restored,pose=[11.65,21.8,0,'F.Cu'],NRST_source_receipt='transition-proposal-v2.json',vias=VIA,selected_routes=ROUTES,attempts=ATTEMPTS,native_outline_bounds=list(s.OUTLINE.bounds),search_domain='full native outline; no crop',reserve_mm=RESERVE,wall_seconds=time.monotonic()-START,complete_declared_group=complete,scope='Geometric complete-group proposal only. Native DRC, process, all actual clamp cuts, finite entries, full net/support/reference/source gates are required before owner adoption.')
 OUT.write_text(json.dumps(out,indent=2)+'\n')
def route(logical,layer,start,end,name,prefix=None):
 if time.monotonic()-START>BUDGET:return dict(passed=False,reason='wall_budget',name=name)
 assert s.OUTLINE.covers(Point(start))and s.OUTLINE.covers(Point(end))
 if prefix:assert s.OUTLINE.covers(LineString(prefix))
 free,obs=free_region(logical,layer,avoid_clamp=bool(prefix));comp=next((p for p in parts(free)if p.covers(Point(start))and p.covers(Point(end))),None)
 out=dict(logical=logical,net=logical.split('::')[0],layer=layer,name=name,passed=False,points=[])
 if comp is None:out['reason']='no_same_continuous_component';return out
 points=None
 for pp in s.paths2(start,end):
  if comp.covers(LineString(pp)):points=pp;break
 if points is None:
  triangles=list(shapely.constrained_delaunay_triangles(comp).geoms);centers=[tuple(t.centroid.coords[0])for t in triangles];edges={};adj=[{}for _ in triangles]
  for j,t in enumerate(triangles):
   coords=list(t.exterior.coords)
   for a,b in zip(coords,coords[1:]):
    key=tuple(sorted((a,b)))
    if key in edges:
     k=edges[key];mid=((a[0]+b[0])/2,(a[1]+b[1])/2);cost=math.dist(centers[j],mid)+math.dist(centers[k],mid);adj[j][k]=(cost,mid);adj[k][j]=(cost,mid)
    else:edges[key]=j
  si=next(j for j,t in enumerate(triangles)if t.covers(Point(start)));ei=next(j for j,t in enumerate(triangles)if t.covers(Point(end)));queue=[(0,si)];dist={si:0};prev={}
  while queue:
   cost,j=heapq.heappop(queue)
   if cost!=dist[j]:continue
   if j==ei:break
   if time.monotonic()-START>BUDGET:out['reason']='wall_budget_in_CDT';return out
   for k,(w,mid)in adj[j].items():
    nc=cost+w
    if nc<dist.get(k,1e100):dist[k]=nc;prev[k]=j;heapq.heappush(queue,(nc,k))
  assert ei in dist
  seq=[ei]
  while seq[-1]!=si:seq.append(prev[seq[-1]])
  seq.reverse();raw=[start]
  for a,b in zip(seq,seq[1:]):raw.extend([centers[a],adj[a][b][1]])
  raw.extend([centers[ei],end]);points=[raw[0]];j=0
  while j<len(raw)-1:
   k=len(raw)-1
   while k>j+1 and not comp.covers(LineString([raw[j],raw[k]])):k-=1
   points.append(raw[k]);j=k
  out['triangles']=len(triangles)
 points=[(round(x,6),round(y,6))for x,y in points]
 if prefix:points=prefix[:-1]+points
 rr=s.check(LineString(points),obs,True);out.update(points=points,width=.127,length_mm=LineString(points).length,passed=rr[0]['pass_with_polygon_error'],nearest=rr[:3],violations=[r for r in rr if r['extra_clearance_mm']<s.ERROR]);return out
def record(r,select=False):
 ATTEMPTS.append(r)
 if select and r['passed']:ROUTES.append(r)
 save();print(json.dumps({k:r.get(k)for k in ['name','logical','layer','passed','reason','length_mm']}),flush=True)
def main():
 for p in ports['paths']:
  logical='SBUS_MCU::SRC'if p['name']=='MCU-clamp-source-F'else'SBUS_MCU::DST'if p['net']=='SBUS_MCU'else p['net']
  obs=obstacles(logical,p['layer']);rr=s.check(LineString(p['points']),obs,True);r=dict(**p,logical=logical,width=.127,length_mm=LineString(p['points']).length,passed=rr[0]['pass_with_polygon_error'],nearest=rr[:3],violations=[r for r in rr if r['extra_clearance_mm']<s.ERROR]);record(r,True)
  if not r['passed']:return
 r=route('SBUS_MCU::SRC','B.Cu',[12.175,22.35],[11.147874,19.73],'MCU-clamp-source-B',prefix=[[11.925,22.35],[12.175,22.35]]);record(r,True)
 if not r['passed']:return
 checkpoint=list(ROUTES)
 for layer in ['In2.Cu','In3.Cu']:
  ROUTES[:]=checkpoint
  r=route('SBUS_LV',layer,[18.344327,11.231475],[9.290186,20.576637],'LV-inner-'+layer);record(r,True)
  if not r['passed']:continue
  for dstlayer in ['In3.Cu','In2.Cu']:
   if not connected('SBUS_MCU::DST',dstlayer,[10.420675,22.290979],[17.12882,6.83933]):
    record(dict(name='MCU-inner-'+dstlayer,logical='SBUS_MCU::DST',layer=dstlayer,passed=False,reason='no_same_continuous_component'));continue
   r=route('SBUS_MCU::DST',dstlayer,[10.420675,22.290979],[17.12882,6.83933],'MCU-inner-'+dstlayer);record(r,True)
   if r['passed']:save(True);return
 save(False)
if __name__=='__main__':main()
