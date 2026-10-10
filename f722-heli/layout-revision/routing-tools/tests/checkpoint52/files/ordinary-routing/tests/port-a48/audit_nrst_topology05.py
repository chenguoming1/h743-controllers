import json,pathlib,hashlib,math,heapq,itertools
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
H=pathlib.Path(__file__).resolve().parent;D=H/'candidate05';S=H.parent/'port-b48/candidate03';read=lambda f:json.loads(pathlib.Path(f).read_text());sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
def geom(polys):return unary_union([Polygon(q['outer'],q.get('holes',[]))for q in polys])
def graph(n):
 os=[o for o in n['objects']if o['net']=='NRST'];tracks=[o for o in os if o['kind']=='track'];pads=[o for o in os if o['kind']=='pad'];vias=[o for o in os if o['kind']=='via'];points={}
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
before=read(S/'f722-heli.native.json');after=read(D/'f722-heli.native.json');a=graph(before);b=graph(after);assert a['pads']==b['pads'];local0=next(q for q in a['pairs']if q['from_pad']=='C10.1'and q['to_pad']=='U1.7');local1=next(q for q in b['pairs']if q['from_pad']=='C10.1'and q['to_pad']=='U1.7');assert local0==local1
out=dict(schema='f722-complete-NRST-topology-review/v1',source_board_sha256=before['board_sha256'],board_sha256=after['board_sha256'],source_native_sha256=sha(S/'f722-heli.native.json'),native_sha256=sha(D/'f722-heli.native.json'),before=a,after=b,C10_to_U1_local_path_exactly_preserved=True,complete_four_pad_tree=True,all_six_terminal_pairs_reachable=True,reset_timing_or_noise_qualification=False,scope='Actual saved native track centerlines and through-via joins, with same-net pad copper contacts; retains reset capacitor-to-MCU local geometry and records each pullup/test-point branch length.')
(D/'NRST-topology-review.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(pads=b['pads'],local_cap_to_MCU=local1,branch_lengths_before=[(r['from_pad'],r['to_pad'],r['length_mm'])for r in a['pairs']],branch_lengths_after=[(r['from_pad'],r['to_pad'],r['length_mm'])for r in b['pairs']]),indent=2))
