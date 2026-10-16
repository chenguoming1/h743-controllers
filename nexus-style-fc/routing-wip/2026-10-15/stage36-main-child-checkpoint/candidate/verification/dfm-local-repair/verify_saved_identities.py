"""Read-only native identity/contact preservation for USB and completed local DFM nets."""
import pcbnew as k,json,hashlib,sys
from pathlib import Path
sys.path.insert(0,'/workspace/shared/nexus-main-placement-fix/scripts');from router import col,xy
root=Path(__file__).resolve().parent;stage=root.parent.parent;prev=stage.parent/'stage35/hardware/nexus-style-fc.kicad_pcb';src=stage/'hardware/nexus-style-fc.kicad_pcb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hprev=sha(prev);h=sha(src)
assert hprev=='bf9a10563839b18071dedd1c4a71af60c25ac19e94f392adb1917955b1f4e95d'
assert h=='bed37199e8d62b8135a27b9e182f8e8f584f1a9fb722cb6efb5d4c87b2a320b8'
a=k.LoadBoard(str(prev));b=k.LoadBoard(str(src));usb=['USB_DP','USB_DN'];names=usb+['SW_5V','3V3_SENS'];uid=lambda o:o.m_Uuid.AsString()
def inv(board,nets):
 out={}
 for t in board.GetTracks():
  if t.GetNetname() not in nets:continue
  v=[t.GetClass(),t.GetNetname(),t.GetNetCode(),t.GetLayer(),xy(t.GetStart()),xy(t.GetEnd()),t.GetWidth(k.F_Cu) if t.GetClass()=='PCB_VIA' else t.GetWidth(),tuple(t.GetLayerSet().Seq())]
  if t.GetClass()=='PCB_ARC':v+=[xy(t.GetMid())]
  if t.GetClass()=='PCB_VIA':v+=[t.GetDrillValue()]
  out[uid(t)]=v
 return out

def pads(board,nets):
 return sorted((f.GetReference(),p.GetNumber(),uid(p),p.GetNetname(),p.GetNetCode(),xy(p.GetPosition()),xy(p.GetSize()),p.GetOrientationDegrees(),f.GetLayer(),tuple(p.GetLayerSet().Seq()),p.GetShape(),p.GetAttribute(),xy(p.GetDrillSize())) for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() in nets)
def polys(board):
 result={}
 for t in board.GetDrawings():
  if hasattr(t,'GetNetname') and t.GetNetname() in usb:
   ps=t.GetPolyShape();result[uid(t)]=[t.GetNetname(),t.GetLayer(),[[[q.CPoint(i).x,q.CPoint(i).y] for i in range(q.PointCount())] for q in [ps.Outline(j) for j in range(ps.OutlineCount())]]]
 return result
assert inv(a,names)==inv(b,names);assert pads(a,names)==pads(b,names);assert polys(a)==polys(b)
assert b.FindNet('USB_DM') is None
for n in usb:assert b.DpCoupledNet(b.FindNet(n)).GetNetname()==usb[1-usb.index(n)]
tracks=list(b.GetTracks());pad_contacts=[]
for f in b.GetFootprints():
 for p in f.Pads():
  if p.GetNetname() not in names:continue
  layer=f.GetLayer();cs=[uid(t) for t in tracks if t.GetNetname()==p.GetNetname() and t.IsOnLayer(layer) and col(t.GetEffectiveShape(layer),p.GetEffectiveShape(layer),0)]
  assert cs,(f.GetReference(),p.GetNumber())
  pad_contacts.append(dict(reference=f.GetReference(),pad=p.GetNumber(),uuid=uid(p),net=p.GetNetname(),layer=b.GetLayerName(layer),track_contacts=cs))
assert len([p for p in pad_contacts if p['net'] in usb])==10
assert len([p for p in pad_contacts if p['net']=='3V3_SENS'])==15
assert len([p for p in pad_contacts if p['net']=='SW_5V'])==4
# Identity means the verified conductive graph is identical for these track/pad-only nets.
assert not any(z.GetNetname() in names for z in b.Zones() if not z.GetIsRuleArea())
assert sha(src)==h and sha(prev)==hprev
proof=dict(status='PASS',native_version=k.GetBuildVersion(),source=str(src),sha256=h,previous_source=str(prev),previous_source_sha256=hprev,native_partners={n:b.DpCoupledNet(b.FindNet(n)).GetNetname() for n in usb},net_codes={n:b.FindNet(n).GetNetCode() for n in usb},native_routing_inventory_and_pad_identity_exactly_unchanged={n:dict(routing_items=len(inv(b,[n])),pads=len(pads(b,[n]))) for n in names},usb_tapers_unchanged=len(polys(b)),all_selected_pad_contacts=pad_contacts,no_selected_net_zones=True,all_selected_conductive_graphs_preserved_by_exact_identity=True,source_hashes_unchanged=True,scope='No board save/refill/DRC/export. Exact geometry/pad/taper identity preserves prior track/pad contact proofs. Stage36 reference-fill projections are not recomputed here; use stage35 qualification only within its stated scope.')
(root/'saved-identity-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='all_selected_pad_contacts'},indent=2))
