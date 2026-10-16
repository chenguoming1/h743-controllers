import pcbnew as k,json,sys,hashlib,math
from pathlib import Path
sys.path.insert(0,'/workspace/shared/nexus-main-placement-fix/scripts');from router import col,xy,vec
from apply_dfm_leaf_and_sw_fix import REMOVE,SW,NEW
root=Path(__file__).parent
source=Path(sys.argv[1] if len(sys.argv)>1 else '/workspace/shared/nexus-main-placement-fix/stage33/hardware/nexus-style-fc.kicad_pcb')
target=Path(sys.argv[2] if len(sys.argv)>2 else root.parents[1]/'hardware/nexus-style-fc.kicad_pcb')
output=Path(sys.argv[3] if len(sys.argv)>3 else root/'saved-stage35-native-proof.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();sh,th=sha(source),sha(target)
old=k.LoadBoard(str(source));b=k.LoadBoard(str(target));layers=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.In3_Cu,k.In4_Cu,k.B_Cu]
uid=lambda o:o.m_Uuid.AsString()
def inventory(board):
 out={}
 for t in board.GetTracks():
  v=[t.GetClass(),t.GetNetname(),t.GetNetCode(),t.GetLayer(),xy(t.GetStart()),xy(t.GetEnd()),t.GetWidth(k.F_Cu) if t.GetClass()=='PCB_VIA' else t.GetWidth()]
  if t.GetClass()=='PCB_ARC':v+=[xy(t.GetMid())]
  if t.GetClass()=='PCB_VIA':v+=[t.GetDrillValue(),tuple(t.GetLayerSet().Seq())]
  out[uid(t)]=v
 return out
before=inventory(old);after=inventory(b)
assert set(before)-set(after)==set(REMOVE)
assert set(after)-set(before)=={NEW}
assert {u for u in set(after)&set(before) if after[u]!=before[u]}=={SW}
def padmap(board):
 return sorted((f.GetReference(),p.GetNumber(),uid(p),p.GetNetname(),p.GetNetCode(),xy(p.GetPosition()),xy(p.GetSize()),p.GetOrientationDegrees(),f.GetLayer(),tuple(p.GetLayerSet().Seq()),p.GetShape(),p.GetAttribute(),xy(p.GetDrillSize())) for f in board.GetFootprints() for p in f.Pads())
assert padmap(old)==padmap(b)
tracks=list(b.GetTracks());pads=[p for f in b.GetFootprints() for p in f.Pads()]
obs=tracks+pads
for board in [old,b]:assert all(z.GetNetname()=='GND' for z in board.Zones() if not z.GetIsRuleArea()),'Graph requires new non-GND zone handling'
def graph(board,net):
 objects=[o for o in list(board.GetTracks())+[p for f in board.GetFootprints() for p in f.Pads()] if o.GetNetname()==net];edges={uid(o):set() for o in objects}
 for i,a in enumerate(objects):
  for z in objects[i+1:]:
   if any(a.IsOnLayer(l) and z.IsOnLayer(l) and col(a.GetEffectiveShape(l),z.GetEffectiveShape(l),0) for l in layers):edges[uid(a)].add(uid(z));edges[uid(z)].add(uid(a))
 pending=set(edges);cs=[]
 while pending:
  todo=[next(iter(pending))];seen=set()
  while todo:
   u=todo.pop()
   if u in seen:continue
   seen.add(u);todo.extend(edges[u]-seen)
  pending-=seen;cs.append(dict(objects=len(seen),pads=sorted([o.GetParentFootprint().GetReference()+'.'+o.GetNumber() for o in objects if uid(o) in seen and o.GetClass()=='PAD'])))
 return cs
components={n:dict(before=graph(old,n),after=graph(b,n)) for n in ['3V3_SENS','SW_5V']}
for n,c in components.items():assert len(c['before'])==len(c['after'])==1 and c['before'][0]['pads']==c['after'][0]['pads']
assert len(components['3V3_SENS']['after'][0]['pads'])==15
assert components['SW_5V']['after'][0]['pads']==['L1.1','U5.1','U5.2','U5.3']
newitems=[t for t in tracks if uid(t) in [SW,NEW]]
assert len(newitems)==2
for t in newitems:assert t.GetWidth()==250000 and t.GetLayer()==k.B_Cu and t.GetNetname()=='SW_5V'
assert xy(next(t for t in newitems if uid(t)==SW).GetEnd())==(103.55,110.65)
assert xy(next(t for t in newitems if uid(t)==NEW).GetStart())==(103.55,110.65)
# Includes physical copper pads and tracks; no B.Cu drawing exists on this source.
drawings=list(b.GetDrawings())+[d for f in b.GetFootprints() for d in f.GraphicalItems()]
assert not any(d.IsOnLayer(k.B_Cu) for d in drawings),'New bottom drawing requires explicit clearance review'
hits=[]
for t in newitems:
 for o in obs:
  if not o.IsOnLayer(k.B_Cu) or o.GetNetname()=='SW_5V':continue
  if col(t.GetEffectiveShape(k.B_Cu),o.GetEffectiveShape(k.B_Cu),127002):hits.append([uid(t),uid(o),o.GetNetname()])
assert not hits

def gap(a,z,limit=500000):
 if col(a,z,0):return 0
 if not col(a,z,limit):return None
 lo,hi=0,limit
 while hi-lo>1:
  m=(hi+lo)//2
  if col(a,z,m):hi=m
  else:lo=m
 return hi/1e6
u5=[p for p in pads if p.GetParentFootprint().GetReference()=='U5'];u5gaps=[]
for p in u5:
 gg=[gap(t.GetEffectiveShape(k.B_Cu),p.GetEffectiveShape(k.B_Cu)) for t in newitems];g=min([g for g in gg if g is not None],default=None)
 if g is not None:u5gaps.append(dict(pad=p.GetNumber(),net=p.GetNetname(),gap_mm=g))
assert next(r for r in u5gaps if r['pad']=='3')['gap_mm']>=.235
# All positive gaps for JLC's oval class against 0.25/0.50 mm bottom track/via apertures.
small_gaps=[]
for t in tracks:
 if not t.IsOnLayer(k.B_Cu) or (t.GetWidth(k.B_Cu) if t.GetClass()=='PCB_VIA' else t.GetWidth()) not in [250000,500000]:continue
 for p in pads:
  if not p.IsOnLayer(k.B_Cu) or sorted(xy(p.GetSize()))!=[.28,.85]:continue
  g=gap(t.GetEffectiveShape(k.B_Cu),p.GetEffectiveShape(k.B_Cu),150000)
  if g is not None and g>0:small_gaps.append(dict(track=uid(t),net=t.GetNetname(),pad=p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),pad_net=p.GetNetname(),gap_mm=g))
assert min(r['gap_mm'] for r in small_gaps)>.11
# No newly exposed front 0.25-mm endpoint. Require cap-level contact if center is uncovered.
free=[]
for t in tracks:
 if t.GetClass()=='PCB_VIA' or t.GetLayer()!=k.F_Cu or t.GetWidth()!=250000:continue
 for label,p in [('start',t.GetStart()),('end',t.GetEnd())]:
  same=[o for o in obs if uid(o)!=uid(t) and o.IsOnLayer(k.F_Cu) and o.GetNetname()==t.GetNetname()]
  center=[o for o in same if col(k.SHAPE_CIRCLE(p,1),o.GetEffectiveShape(k.F_Cu),0)]
  cap=[o for o in same if col(k.SHAPE_CIRCLE(p,125000),o.GetEffectiveShape(k.F_Cu),0)]
  fill=[z for z in b.Zones() if z.GetLayer()==k.F_Cu and z.GetNetname()==t.GetNetname() and z.GetFilledPolysList(k.F_Cu).Contains(p)]
  if not center and not cap and not fill:free.append(dict(uuid=uid(t),net=t.GetNetname(),endpoint=label,at=xy(p)))
assert not free
# Every retained sensor-rail via's per-layer physical contacts unchanged. Its drill/outer geometry already matched.
def via_contacts(board):
 oo=list(board.GetTracks())+[p for f in board.GetFootprints() for p in f.Pads()];out={}
 for v in oo:
  if v.GetClass()!='PCB_VIA' or v.GetNetname()!='3V3_SENS' or uid(v) in REMOVE:continue
  out[uid(v)]={board.GetLayerName(l):sorted([uid(o) for o in oo if uid(o)!=uid(v) and o.GetNetname()==v.GetNetname() and o.IsOnLayer(l) and col(v.GetEffectiveShape(l),o.GetEffectiveShape(l),0)]) for l in layers if v.IsOnLayer(l)}
 return out
vc=via_contacts(b);assert vc==via_contacts(old)
# Physical SW contact witnesses (all bottom SMD, no SW vias).
swcontacts=[]
for p in pads:
 if p.GetNetname()!='SW_5V':continue
 contacts=[uid(t) for t in tracks if t.GetNetname()=='SW_5V' and col(t.GetEffectiveShape(k.B_Cu),p.GetEffectiveShape(k.B_Cu),0)]
 assert contacts;swcontacts.append(dict(pad=p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),at=xy(p.GetPosition()),tracks=contacts))
assert sha(source)==sh and sha(target)==th
out=dict(native_version=k.GetBuildVersion(),source=str(source),source_sha256=sh,target=str(target),target_sha256=th,read_only_native_validation=True,all_pad_identities_nets_geometry_preserved=True,removed_objects=sorted(REMOVE),changed_track=SW,added_track=NEW,exact_native_inventory_delta=True,components=components,new_sw_foreign_copper_hits_at_0p127002mm=hits,new_sw_u5_pad_gaps_mm=u5gaps,remaining_bottom_oval_class_gaps_below_0p15mm=small_gaps,front_0p25mm_unconnected_endpoints=free,retained_sensor_via_contacts_unchanged=vc,sw_pad_contacts=swcontacts,source_and_target_hashes_unchanged=True,scope='Read-only geometry/contact checks. Native DRC and fresh Gerber receipts are bound separately in the final verification summary.')
output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
