import json,pathlib,hashlib,math,heapq,itertools
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
H=pathlib.Path(__file__).resolve().parent;D=H/'candidate05';S=H.parent/'port-b48/candidate03';read=lambda f:json.loads(pathlib.Path(f).read_text());sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
def geom(polys):return unary_union([Polygon(q['outer'],q.get('holes',[]))for q in polys])
def graph(n,net):
 os=[o for o in n['objects']if o['net']==net];tracks=[o for o in os if o['kind']=='track'];pads=[o for o in os if o['kind']=='pad'];vias=[o for o in os if o['kind']=='via'];points={}
 for t in tracks:
  l=next(iter(t['copper']));points.setdefault(l,set()).update([tuple(t['start']),tuple(t['end'])])
 for v in vias:
  for l in v['barrel_layers']:points.setdefault(l,set()).add(tuple(v['xy']))
 adj={}
 def edge(a,b,w,uid):adj.setdefault(a,[]).append((b,w,uid));adj.setdefault(b,[]).append((a,w,uid))
 for t in tracks:
  l=next(iter(t['copper']));line=LineString([t['start'],t['end']]);qq=sorted([(line.project(Point(xy)),xy)for xy in points[l]if line.distance(Point(xy))<1e-7])
  for (da,a),(db,b)in zip(qq,qq[1:]):edge((l,*a),(l,*b),db-da,t['uuid'])
 for v in vias:
  for a,b in zip(v['barrel_layers'],v['barrel_layers'][1:]):edge((a,*v['xy']),(b,*v['xy']),0,v['uuid'])
 for p in pads:
  for l,ps in p['inside'].items():
   g=geom(ps)
   for xy in points.get(l,[]):
    if g.covers(Point(xy)):edge(p['key'],(l,*xy),math.dist(p['xy'],xy),p['uuid'])
 def path(a,b):
  q=[(0,0,a)];dist={a:0};prev={};serial=0
  while q:
   cost,_,u=heapq.heappop(q)
   if cost!=dist[u]:continue
   if u==b:break
   for v,w,uid in adj.get(u,[]):
    nc=cost+w
    if nc<dist.get(v,1e99):dist[v]=nc;prev[v]=(u,uid);serial+=1;heapq.heappush(q,(nc,serial,v))
  assert b in dist,(a,b);uids=[];v=b
  while v!=a:v,uid=prev[v];uids.append(uid)
  return dict(from_pad=a,to_pad=b,length_mm=dist[b],path_object_ids=list(reversed(uids)))
 return dict(pads={p['key']:p['xy']for p in pads},track_count=len(tracks),via_count=len(vias),total_track_length_mm=sum(LineString([t['start'],t['end']]).length for t in tracks),pairs=[path(a,b)for a,b in itertools.combinations(sorted(p['key']for p in pads),2)],adjacency_node_count=len(adj))

n=read(D/'f722-heli.native.json');rows={}
for net,source,clamp,target in [('PORT_A_RX_EXT','J9.1','U14.1','R30.1'),('PORT_A_TX_EXT','J9.2','U14.2','R31.1')]:
 g=graph(n,net)
 def get(a,b):return next(r for r in g['pairs']if {r['from_pad'],r['to_pad']}=={a,b})
 rows[net]=dict(connector_to_actual_clamp=get(source,clamp),actual_clamp_to_resistor=get(clamp,target),complete_connector_to_resistor=get(source,target),total_track_length_mm=g['total_track_length_mm'],vias=g['via_count'],native_pad_tree=g['pads'])
(D/'PORT_A-branch-lengths.json').write_text(json.dumps(dict(board_sha256=n['board_sha256'],branches=rows,scope='Native saved track-centerline shortest paths through actual pad contacts and plated-through transitions; via vertical length is excluded.'),indent=2)+'\n');print(json.dumps({net:{k:r['length_mm']for k,r in row.items()if isinstance(r,dict)and 'length_mm'in r}for net,row in rows.items()},indent=2))
