"""Source-bound centerline inventory and exact endpoint graph, no SI acceptance."""
import json,pathlib,math,heapq,collections,sys,hashlib
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
H=pathlib.Path(__file__).resolve().parent;R=H.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def geom(ps):return unary_union([Polygon(p['outer'],p.get('holes',[]))for p in ps])
def measure(native,cut):
 d=json.loads(native.read_text());c=json.loads(cut.read_text());contract=next(x for x in c['checks']if x['net']=='TAIL_MCU');obs=[o for o in d['objects']if o['net']in['TAIL_MCU','TAIL_EXT']];graph=collections.defaultdict(list)
 def node(l,xy):return(l,*xy)
 def edge(a,b,w,u):graph[a].append((b,w,u));graph[b].append((a,w,u))
 for t in obs:
  if t['kind']=='track':
   l=next(iter(t['copper']));edge(node(l,t['start']),node(l,t['end']),math.dist(t['start'],t['end']),t['uuid'])
 for v in obs:
  if v['kind']=='via':
   ns=[node(l,v['xy'])for l in v['barrel_layers']];root=('via',v['uuid'])
   for n in ns:edge(root,n,0,v['uuid'])
 for p in obs:
  if p['kind']!='pad':continue
  for l,ps in p['copper'].items():
   shape=geom(ps)
   for n in list(graph):
    if len(n)==3 and n[0]==l and shape.covers(Point(n[1:])):edge(('pad',p['key']),n,0,p['uuid'])
 paths={}
 for a,b in [('U1.55','U12.6'),('R23.2','U12.6'),('R23.1','J5.3')]:
  start=('pad',a);target=('pad',b);q=[(0,start)];dist={start:0};prev={}
  while q:
   cost,n=heapq.heappop(q)
   if cost!=dist[n]:continue
   if n==target:break
   for other,w,u in graph[n]:
    nc=cost+w
    if nc<dist.get(other,1e99):dist[other]=nc;prev[other]=(n,u);heapq.heappush(q,(nc,other))
  assert target in dist,(native,a,b)
  n=target;ids=[]
  while n!=start:n,u=prev[n];ids.append(u)
  ids=list(dict.fromkeys(reversed(ids)));ts=[o for o in obs if o['uuid']in ids and o['kind']=='track'];vs=[o for o in obs if o['uuid']in ids and o['kind']=='via'];layers=collections.defaultdict(float)
  for t in ts:layers[next(iter(t['copper']))]+=math.dist(t['start'],t['end'])
  paths[a+'__'+b]={'planar_track_length_mm':dist[target],'by_layer_mm':dict(layers),'via_count':len(vs),'via_xy_mm':[v['xy']for v in vs],'track_uuids':[t['uuid']for t in ts]}
 for side,key in [('target','U1.55__U12.6'),('source','R23.2__U12.6')]:
  ts=[o for o in obs if o['uuid']in contract[side+'_objects']and o['kind']=='track'];used=set(paths[key]['track_uuids']);paths[key]['branch_track_inventory_mm']=sum(math.dist(t['start'],t['end'])for t in ts);paths[key]['tracks_outside_unique_endpoint_path']=[t['uuid']for t in ts if t['uuid']not in used]
 return {'board_sha256':d['board_sha256'],'native_sha256':sha(native),'cut_report_sha256':sha(cut),'paths':paths,'total_TAIL_MCU_track_length_mm':sum(math.dist(o['start'],o['end'])for o in obs if o['net']=='TAIL_MCU'and o['kind']=='track'),'actual_clamp_cut_passes':contract['complete_clamp_first_path_passes'],'method':'Exact saved track endpoint graph; pad interiors and plated via centers link layers at zero planar length. Length counts whole native track centerlines including entries into lands. Via barrel propagation and internal package/pad distances are excluded. Outside-path tracks retained explicitly.'}
out={'historical':measure(R/'protection-checks/published-native.json',R/'protection-checks/published-recheck.json'),'candidate03':measure(H.parent/'candidate03/f722-heli.native.json',H.parent/'candidate03/protection-actual-io.json')}
(H/'tail-path-comparison.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:{'board':v['board_sha256'],'paths':{p:{a:b for a,b in row.items()if a not in['track_uuids']}for p,row in v['paths'].items()}}for k,v in out.items()}))
