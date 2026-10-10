"""Bounded complete additive RPM_MCU proposal on exact full SBUS17 copper."""
import pathlib,json,sys,hashlib,math,time,signal,heapq
H=pathlib.Path(__file__).resolve().parent;R=H.parents[2];sys.path[:0]=[str(R/'ordinary-routing/tests/port-b48'),str(R/'repo/f722-heli/layout-revision/signal-review/native')]
import native_geometry as s,shapely
from shapely.geometry import Point,LineString
from shapely import unary_union
from check_signal_geometry import copper_entries
from check_critical_reference import ground_geometry,REFERENCE
D=R/'ordinary-routing/tests/servo48/candidate04';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());n=read(D/'f722-heli.native.json');assert n['board_sha256']==sha(D/'f722-heli.kicad_pcb')=='755545e8198e9a3649c0e07533c23e67010d91ab6a8b09556d7463e064ac89eb';s.N=n;s.EXPECTED=n['board_sha256'];s.OUTLINE=s.geom(n['outline_with_npth']['polygons']);s.OBJECTS=[(o,{l:s.geom(ps)for l,ps in o['copper'].items()},{l:s.geom(v['polygons'])for l,v in o.get('mask',{}).items()}if o.get('smd')else{},s.geom(o['drill']['outside'])if o.get('drill')else None)for o in n['objects']];KEY={o['key']:o for o in n['objects']if o['kind']=='pad'}
net='RPM_MCU';MCU=[15.079367,9.594711];TARGET=[13.21,23.02];ANCHOR=[14.425,22.35];vias=[dict(name='RPM-MCU',net=net,xy=MCU),dict(name='RPM-clamp-target',net=net,xy=TARGET)];reservations=[('FLASH_CS',[23.90716,9.90146]),('FLASH_SCK',[19.57724,10.43289]),('FLASH_MISO',[25.40268,10.82928]),('FLASH_MOSI',[21.27,11.59])]
flash_file=R/'ordinary-routing/tests/joint-flash-group/fixed-flash17-reservation-objects.json';assert sha(flash_file)=='1bd0096a0fa4d929f63027b7edb01e58f77235b9869bd4b0e4a2da759e0ec82f';flash=read(flash_file)
# Reservations are additions only. Never import the private group's support removals.
flash_reservations=[(o,{l:s.geom(ps)for l,ps in o['copper'].items()},{l:s.geom(v['polygons'])for l,v in o.get('mask',{}).items()}if o.get('smd')else{},s.geom(o['drill']['outside'])if o.get('drill')else None)for o in flash['objects']]
red_file=R/'ordinary-routing/tests/boot-led48/red-surface-escape49.json';red=read(red_file);flash_reservations.extend([(dict(uuid='reserved-RED-MCU',kind='track',net='LED_RED_K'),{'B.Cu':LineString(red['path_B_mm']).buffer(.0635,quad_segs=128)},{},None),(dict(uuid='reserved-RED-via',kind='via',net='LED_RED_K',xy=red['via_mm'],barrel_layers=n['copper_layers']),{l:Point(red['via_mm']).buffer(.225,quad_segs=128)for l in n['copper_layers']},{},Point(red['via_mm']).buffer(.1,quad_segs=128))])
s.OBJECTS+=flash_reservations
reservations=[(o['net'],o['xy'])for o,_,_,_ in flash_reservations if o['kind']=='via']
_,_,ground,_=ground_geometry(n,copper_entries(n));own=unary_union([Point(v['xy']).buffer(.225+.127+.01,quad_segs=96)for v in vias]);clamp=s.geom(KEY['U13.6']['copper']['B.Cu']);source=[o for o in n['objects']if o['net']==net and(o['kind']=='track'or o.get('key')=='R39.2')]
def parts(g):return[p for p in(g.geoms if hasattr(g,'geoms')else[g])if p.geom_type=='Polygon'and not p.is_empty]
def obstacles(layer,guard=False):
 obs=s.obstacles(net,layer)[0]
 for o,c,m,d in s.OBJECTS:
  if d is not None and not o.get('npth')and o['net']!=net:obs.append(dict(object=o['uuid'],layers=o['barrel_layers'],geometry=d,category='foreign_drill_to_track_copper',required_center_distance_mm=.2635))
 if guard:
  for o in source:obs.append(dict(object=o.get('key',o['uuid']),layers=['B.Cu'],geometry=s.geom(o['copper']['B.Cu']),category='source_branch_clamp_bypass_guard',required_center_distance_mm=.1905))
 return obs
def free(obs,layer,guard):
 expanded=unary_union([o['geometry'].buffer((o['required_center_distance_mm']+.0001)/math.cos(math.pi/128),quad_segs=32)for o in obs if o['category']!='edge_npth_copper']);g=s.OUTLINE.buffer(-.3176).difference(expanded);g=g.intersection(ground[REFERENCE[layer]].union(own).buffer(-.0636))
 if guard:g=g.difference(clamp.buffer(.0636))
 return g
def route(start,end,layer,guard=False):
 assert s.OUTLINE.covers(LineString([start,end]));obs=obstacles(layer,guard);comp=next((p for p in parts(free(obs,layer,guard))if p.covers(Point(start))and p.covers(Point(end))),None)
 if comp is None:return dict(passed=False,layer=layer,reason='No common full-outline copper-and-reference component')
 shapely.prepare(comp);tris=list(shapely.constrained_delaunay_triangles(comp).geoms);centers=[tuple(t.centroid.coords[0])for t in tris];edges={};adj=[{}for _ in tris]
 for j,t in enumerate(tris):
  coords=list(t.exterior.coords)
  for a,b in zip(coords,coords[1:]):
   key=tuple(sorted((a,b)))
   if key in edges:
    k=edges[key];mid=((a[0]+b[0])/2,(a[1]+b[1])/2);cost=math.dist(centers[j],mid)+math.dist(centers[k],mid);adj[j][k]=(cost,mid);adj[k][j]=(cost,mid)
   else:edges[key]=j
 si=next(j for j,t in enumerate(tris)if t.covers(Point(start)));ei=next(j for j,t in enumerate(tris)if t.covers(Point(end)));queue=[(0,si)];dist={si:0};prev={}
 while queue:
  cost,j=heapq.heappop(queue)
  if cost!=dist[j]:continue
  if j==ei:break
  for k,(w,_)in adj[j].items():
   new=cost+w
   if new<dist.get(k,1e100):dist[k]=new;prev[k]=j;heapq.heappush(queue,(new,k))
 assert ei in dist;seq=[ei]
 while seq[-1]!=si:seq.append(prev[seq[-1]])
 seq.reverse();raw=[start]
 for a,b in zip(seq,seq[1:]):raw.extend([centers[a],adj[a][b][1]])
 raw.extend([centers[ei],end]);points=[raw[0]];j=0
 while j<len(raw)-1:
  k=len(raw)-1
  while k>j+1 and not comp.covers(LineString([raw[j],raw[k]])):k-=1
  points.append(raw[k]);j=k
 points=[[round(x,6),round(y,6)]for x,y in points];line=LineString(points);z=s.check(line,obs);missing=line.buffer(.06351,quad_segs=128).difference(ground[REFERENCE[layer]].union(own));return dict(passed=z[0]['extra_clearance_mm']>=.00001 and missing.is_empty,net=net,layer=layer,width=.127,points=points,length_mm=line.length,nearest=z[:3],reference_width_outside_own_windows_mm2=missing.area,triangles=len(tris))
