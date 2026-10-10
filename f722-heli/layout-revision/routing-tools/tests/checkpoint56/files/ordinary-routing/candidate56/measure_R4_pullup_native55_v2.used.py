"""Native full-net and actual terminal centerline ledger; no waveform qualification."""
import json,pathlib,hashlib,math,heapq
from collections import defaultdict
H=pathlib.Path(__file__).resolve().parent;D=H/'candidate02';S=H.parents[1]/'candidate55'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();a=read(D/'f722-heli.native.json');b=read(S/'f722-heli.native.json');prov=read(D/'construction-provenance.json')
nets=sorted({o['net']for o in prov['added_records']});bykey={o['key']:o for o in a['objects']if o['kind']=='pad'}
ledger={}
for net in nets:
 def measure(n):
  ts=[o for o in n['objects']if o['net']==net and o['kind']=='track'];return dict(track_count=len(ts),total_native_track_centerline_mm=sum(math.dist(o['start'],o['end'])for o in ts),by_layer_mm={l:sum(math.dist(o['start'],o['end'])for o in ts if l in o['copper'])for l in n['copper_layers']},via_count=sum(o['net']==net and o['kind']=='via'for o in n['objects']))
 ledger[net]=dict(before=measure(b),after=measure(a),added_track_centerline_mm=sum(math.dist(o['start'],o['end'])for o in prov['added_records']if o['net']==net and o['kind']=='track'))
# Raw graph keeps every actual saved endpoint. Noded crossings and pad contact are
# checked separately by entry/support audit; lengths below follow named centerline paths.
def path(net,ak,bk):
 adj=defaultdict(list)
 def edge(x,y,w,uid):adj[x].append((y,w,uid));adj[y].append((x,w,uid))
 for o in a['objects']:
  if o['net']!=net:continue
  if o['kind']=='track':
   l=next(iter(o['copper']));edge((l,*o['start']),(l,*o['end']),math.dist(o['start'],o['end']),o['uuid'])
  elif o['kind']=='via':
   ls=list(o['copper'])
   for l in ls[1:]:edge((ls[0],*o['xy']),(l,*o['xy']),0,o['uuid'])
 pa,pb=bykey[ak],bykey[bk];assert pa['net']==pb['net']==net
 starts=[(l,*pa['xy'])for l in pa['copper']];ends={(l,*pb['xy'])for l in pb['copper']};cost={x:0 for x in starts};prev={};queue=[(0,x)for x in starts];heapq.heapify(queue);end=None
 while queue:
  d,u=heapq.heappop(queue)
  if d!=cost[u]:continue
  if u in ends:end=u;break
  for v,w,uid in adj[u]:
   nd=d+w
   if nd<cost.get(v,math.inf):cost[v]=nd;prev[v]=(u,uid,w);heapq.heappush(queue,(nd,v))
 assert end is not None,(net,ak,bk)
 chain=[];x=end
 while x not in starts:
  u,uid,w=prev[x];chain.append(dict(uuid=uid,length_mm=w,from_layer=u[0],to_layer=x[0]));x=u
 chain.reverse();return dict(net=net,from_pad=ak,to_pad=bk,trace_centerline_mm=cost[end],barrel_length_excluded=True,path=chain)
pairs=[('FLASH_CS','R4.2','U3.1'),('+3V3_CORE','R4.1','C15.1')]
out=dict(schema='f722-R4-pullup-native-length-ledger55/v1',board_sha256=a['board_sha256'],source_board_sha256=b['board_sha256'],native_sha256=sha(D/'f722-heli.native.json'),nets=ledger,actual_terminal_paths=[path(*p)for p in pairs],limits='Track centerline geometry, exact native vertices and zero-length layer changes at actual via centers. Barrel length, electrical flight time, loading and waveform response are excluded. Full native connectivity is separately audited.')
(D/'native-length-ledger.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({r['net']+':'+r['from_pad']+'->'+r['to_pad']:r['trace_centerline_mm']for r in out['actual_terminal_paths']}))
