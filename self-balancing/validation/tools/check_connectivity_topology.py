#!/usr/bin/python3
"""Read-only physical copper component proof, independent of native airwire counts.

Every actual pad and every via is a labeled fixed terminal. Per-layer effective
copper contacts form graph edges; plated pads/vias join their copper layers.
Each filled zone island is a separate graph node, so disconnected islands cannot
silently join. Compares all terminal partitions, checks every live pad net, and
reports conductor islands with no pad or no fixed terminal. No board is saved.
"""
import argparse, collections, hashlib, json, os, pathlib, time
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
from approved_cleanup_common import load_cleanup
P5='6e2031b040ce8f3a534c2f73abb0091e25b3e6adcab982463264ad8898d65cf8'
ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=pathlib.Path,required=True);ap.add_argument('--candidate',type=pathlib.Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--exceptions',type=pathlib.Path);ap.add_argument('--selfcheck',action='store_true');a=ap.parse_args()
cleanup=load_cleanup(json.loads(a.exceptions.read_text()),a.sha256) if a.exceptions else None
retired={'via:'+q['uuid'] for q in cleanup['removed_via_records']} if cleanup else set()
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
assert sha(a.baseline)==P5 and sha(a.candidate)==a.sha256
uid=lambda t:t.m_Uuid.AsString()
def live(net):return bool(net) and not net.startswith('unconnected-')
def partitions(path):
 b=p.LoadBoard(str(path));layers=list(b.GetEnabledLayers().CuStack());items=[];keep=[]
 for t in list(b.GetTracks())+[pd for f in b.GetFootprints() for pd in f.Pads()]:
  net=t.GetNetname()
  if not live(net):continue
  kind='via' if isinstance(t,p.PCB_VIA) else 'pad' if isinstance(t,p.PAD) else 'track'
  label=('pad:'+t.GetParentFootprint().GetReference()+'.'+t.GetNumber()+':'+uid(t)) if kind=='pad' else ('via:'+uid(t)) if kind=='via' else None
  shapes={l:t.GetEffectiveShape(l) for l in layers if t.IsOnLayer(l)}
  items.append({'uuid':uid(t),'kind':kind,'net':net,'label':label,'shapes':shapes})
 for z in b.Zones():
  if z.GetIsRuleArea() or not live(z.GetNetname()):continue
  for l in layers:
   if not z.IsOnLayer(l) or not z.HasFilledPolysForLayer(l):continue
   ps=z.GetFilledPolysList(l)
   for j in range(ps.OutlineCount()):
    shape=p.SHAPE_POLY_SET(ps.COutline(j))
    for k in range(ps.HoleCount(j)):shape.AddHole(ps.CHole(j,k),0)
    keep.append(shape)
    items.append({'uuid':uid(z)+':'+b.GetLayerName(l)+':'+str(j),'kind':'zone_island','net':z.GetNetname(),'label':None,'shapes':{l:shape}})
 parents=list(range(len(items)))
 def root(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 def union(i,j):parents[root(i)]=root(j)
 buckets=collections.defaultdict(list);contacts=collections.Counter()
 for i,item in enumerate(items):
  for l,s in item['shapes'].items():
   bb=s.BBox();buckets[(item['net'],l)].append((bb.GetLeft(),bb.GetRight(),bb.GetTop(),bb.GetBottom(),i,s))
 for (net,l),rows in buckets.items():
  rows.sort(key=lambda r:r[0])
  for i,row in enumerate(rows):
   left,right,top,bottom,index,s=row
   for q in rows[i+1:]:
    if q[0]>right:break
    if q[2]>bottom or q[3]<top:continue
    if s.GetClearance(q[5])<=0:
     union(index,q[4]);contacts[b.GetLayerName(l)]+=1
 groups=collections.defaultdict(list)
 for i,t in enumerate(items):groups[(t['net'],root(i))].append(t)
 nets={}
 for (net,_),objects in groups.items():
  entry=nets.setdefault(net,{'pad_partitions':[],'fixed_terminal_partitions':[],'copper_components':[],'padless_components':[],'terminal_free_components':[]})
  pads=sorted(q['label'] for q in objects if q['kind']=='pad');anchors=sorted(q['label'] for q in objects if q['label'])
  row={'pads':pads,'fixed_terminals':anchors,'object_count':len(objects),'kinds':dict(collections.Counter(q['kind'] for q in objects)),'objects':sorted(q['uuid'] for q in objects)}
  entry['copper_components'].append(row)
  if pads:entry['pad_partitions'].append(pads)
  else:entry['padless_components'].append(row)
  if anchors:entry['fixed_terminal_partitions'].append(anchors)
  else:entry['terminal_free_components'].append(row)
 for row in nets.values():
  row['pad_partitions'].sort();row['fixed_terminal_partitions'].sort()
 # Distinct native connectivity implementation cross-checks non-ground pad clusters.
 b.BuildConnectivity();conn=b.GetConnectivity();native={};by_net=collections.defaultdict(list)
 for t in list(b.GetTracks())+[pd for f in b.GetFootprints() for pd in f.Pads()]:
  if live(t.GetNetname()) and t.GetNetname()!='GND':by_net[t.GetNetname()].append(t)
 for net,ts in by_net.items():
  par={uid(t):uid(t) for t in ts}
  def nr(k):
   while par[k]!=k:par[k]=par[par[k]];k=par[k]
   return k
  for t in ts:
   for adj in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
    other=uid(adj)
    if other in par:par[nr(uid(t))]=nr(other)
  ng=collections.defaultdict(list)
  for t in ts:
   if isinstance(t,p.PAD):ng[nr(uid(t))].append('pad:'+t.GetParentFootprint().GetReference()+'.'+t.GetNumber()+':'+uid(t))
  native[net]=sorted(sorted(v) for v in ng.values())
 disagreements={n:{'physical':nets[n]['pad_partitions'],'native':g} for n,g in native.items() if nets[n]['pad_partitions']!=g}
 return {'nets':dict(sorted(nets.items())),'physical_contact_edges_by_layer':dict(contacts),'native_non_ground_crosscheck_disagreements':disagreements,'objects':len(items),'ground_pad_count':sum(len(g) for g in nets['GND']['pad_partitions']),'ground_fixed_terminal_count':sum(len(g) for g in nets['GND']['fixed_terminal_partitions'])}
before=partitions(a.baseline);after=partitions(a.candidate);errors=[];changed={}
for net in sorted(set(before['nets'])|set(after['nets'])):
 x=before['nets'].get(net,{});y=after['nets'].get(net,{})
 surviving=sorted(sorted(t for t in g if t not in retired) for g in x.get('fixed_terminal_partitions',[]) if any(t not in retired for t in g))
 if surviving!=y.get('fixed_terminal_partitions'):
  changed[net]={'before':x.get('fixed_terminal_partitions'),'after':y.get('fixed_terminal_partitions')};errors.append('Fixed-terminal physical connectivity changed: '+net)
 if len(y.get('pad_partitions',[]))>1:errors.append('Disconnected pad components: '+net)
 if len(y.get('terminal_free_components',[]))>len(x.get('terminal_free_components',[])):errors.append('New isolated copper fragments: '+net)
 if len(y.get('padless_components',[]))>len(x.get('padless_components',[])):errors.append('New copper components without any pad: '+net)
for name,data in [('baseline',before),('candidate',after)]:
 if data['native_non_ground_crosscheck_disagreements']:errors.append(name+' independent shape/native connectivity disagreement')
assert sha(a.baseline)==P5 and sha(a.candidate)==a.sha256,'Native sources changed during audit'
if not a.selfcheck and a.sha256==P5:errors.append('Unchanged P5 cannot certify P6 cleanup')
result={'status':('BASELINE HARNESS SELF-CHECK PASS; NOT P6 ACCEPTANCE' if a.selfcheck else 'PASS PHYSICAL PAD/VIA CONNECTIVITY TOPOLOGY') if not errors else 'NOT PASSED','baseline_sha256':P5,'candidate_sha256':a.sha256,'errors':errors,'changed_fixed_terminal_partitions':changed,'baseline':before,'candidate':after,'method':__doc__,'limits':'Proves labeled electrical connectivity and island topology. It does not claim identical geometric path shapes, propagation delay, SI, EMI, impedance, physical reliability, or abstract graph isomorphism within same-net copper junctions.'}
result['explicitly_retired_redundant_via_labels']=sorted(retired)
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'errors':errors,'net_count':len(after['nets']),'ground_pad_count':after['ground_pad_count'],'ground_fixed_terminal_count':after['ground_fixed_terminal_count'],'physical_contact_edges_by_layer':after['physical_contact_edges_by_layer'],'report':str(a.out)},indent=2));raise SystemExit(bool(errors))
