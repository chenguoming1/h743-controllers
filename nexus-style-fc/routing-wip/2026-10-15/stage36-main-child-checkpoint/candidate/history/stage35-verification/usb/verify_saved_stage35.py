import pcbnew as k,json,hashlib,sys,math
from pathlib import Path
sys.path.insert(0,'/workspace/shared/nexus-main-placement-fix/scripts');from router import col,xy
root=Path(__file__).parent;stage=root.parents[1];src=stage/'hardware/nexus-style-fc.kicad_pcb';h=hashlib.sha256(src.read_bytes()).hexdigest();b=k.LoadBoard(str(src));baseline=Path('/workspace/shared/nexus-main-placement-fix/successor-work/usb-study/combined-proof-v2/hardware/nexus-style-fc.kicad_pcb');old=k.LoadBoard(str(baseline));names=['USB_DP','USB_DN'];receipt=json.load(open('/workspace/shared/nexus-main-placement-fix/successor-work/usb-study/bevel-v2-0p08.usb-bevel.json'));expected={x['uuid']:x for x in receipt['added_tracks']}
def inventory(b):
 out={}
 for t in b.GetTracks():
  if t.GetNetname() not in names:continue
  v=[t.GetClass(),t.GetNetname(),t.GetLayer(),list(xy(t.GetStart())),list(xy(t.GetEnd())),(t.GetWidth(k.B_Cu) if t.GetClass()=='PCB_VIA' else t.GetWidth())]
  if t.GetClass()=='PCB_ARC':v+=[list(xy(t.GetMid()))]
  elif t.GetClass()=='PCB_VIA':v+=[t.GetDrill()]
  out[t.m_Uuid.AsString()]=v
 return out
assert inventory(b)==inventory(old),'USB track/via/arc geometry drift'
def padmap(b):
 return sorted((f.GetReference(),p.GetNumber(),p.m_Uuid.AsString(),p.GetNetname(),xy(p.GetPosition()),xy(p.GetSize()),p.GetOrientationDegrees(),f.GetLayer()) for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() in names)
assert padmap(b)==padmap(old),'USB pad identity or geometry drift'
for n in names:assert b.DpCoupledNet(b.FindNet(n)).GetNetname()==names[1-names.index(n)]
assert b.FindNet('USB_DM') is None
tracks=list(b.GetTracks());pads=[(f,p) for f in b.GetFootprints() for p in f.Pads()];drawings=list(b.GetDrawings());obs=tracks+[p for f,p in pads]+drawings;diags=[]
for uid,e in expected.items():
 t=next(t for t in tracks if t.m_Uuid.AsString()==uid);assert xy(t.GetStart())==tuple(e['start']) and xy(t.GetEnd())==tuple(e['end']) and t.GetWidth()==150000 and t.GetLayer()==k.B_Cu
 hits=[]
 for o in obs:
  if not o.IsOnLayer(k.B_Cu) or not hasattr(o,'GetNetname') or o.GetNetname()==t.GetNetname():continue
  if col(t.GetEffectiveShape(k.B_Cu),o.GetEffectiveShape(k.B_Cu),127002):hits.append(o.m_Uuid.AsString())
 assert not hits;diags.append(dict(uuid=uid,net=t.GetNetname(),start=xy(t.GetStart()),end=xy(t.GetEnd()),foreign_copper_hits_at_0p127002mm=hits))
contacts=[]
for f,p in pads:
 if p.GetNetname() not in names:continue
 layer=k.F_Cu if f.GetReference()=='J6' else k.B_Cu;cs=[t.m_Uuid.AsString() for t in tracks if t.GetNetname()==p.GetNetname() and t.IsOnLayer(layer) and col(t.GetEffectiveShape(layer),p.GetEffectiveShape(layer),0)];assert cs;contacts.append(dict(reference=f.GetReference(),pad=p.GetNumber(),uuid=p.m_Uuid.AsString(),net=p.GetNetname(),layer=b.GetLayerName(layer),track_contacts=cs))
assert len(contacts)==10
# Prove USB taper identity by exact native polygon vertices and UUID.
def polys(b):
 result={}
 for t in b.GetDrawings():
  if hasattr(t,'GetNetname') and t.GetNetname() in names:
   ps=t.GetPolyShape();result[t.m_Uuid.AsString()]=[t.GetNetname(),t.GetLayer(),[[[q.CPoint(i).x,q.CPoint(i).y] for i in range(q.PointCount())] for q in [ps.Outline(j) for j in range(ps.OutlineCount())]]]
 return result
assert polys(b)==polys(old)
assert hashlib.sha256(src.read_bytes()).hexdigest()==h
out=dict(source=str(src),sha256=h,native_version=k.GetBuildVersion(),read_only=True,usb_track_via_arc_inventory_unchanged_from_v2=len(inventory(b)),usb_tapers_unchanged=len(polys(b)),all_ten_usb_pad_identities_geometry_unchanged=True,native_partners={n:b.DpCoupledNet(b.FindNet(n)).GetNetname() for n in names},net_codes={n:b.FindNet(n).GetNetCode() for n in names},four_v2_bevels=diags,all_ten_usb_pad_contacts=contacts,source_hash_unchanged=True);(root/'saved-stage35-native-proof.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['all_ten_usb_pad_contacts','four_v2_bevels']},indent=2))
