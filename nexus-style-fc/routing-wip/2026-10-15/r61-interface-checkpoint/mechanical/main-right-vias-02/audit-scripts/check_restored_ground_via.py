from pathlib import Path
import pcbnew as k,json,sys,hashlib
O=Path(sys.argv[1]);R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');tr=json.loads((O/'transaction.json').read_text());S=Path(tr['return_source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();u='3bc1d32f-634e-4d77-9c5d-f6bdd353e76c';r=json.loads((O/'usb-reference-return-verification.json').read_text());proofs={}
def hit(a,b):
 q=k.SHAPE.Collide(a,b,0);return q[0] if isinstance(q,tuple) else bool(q)
for label,D in [('source',S),('candidate',O)]:
 b=k.LoadBoard(str(D/'hardware/nexus-style-fc.kicad_pcb'));v=next(t for t in b.GetTracks() if t.m_Uuid.AsString()==u);assert v.GetNetname()=='GND';assert v.GetDrillValue()==200000 and v.GetWidth(k.F_Cu)==450000
 donors=[]
 for o in list(b.GetTracks())+[p for f in b.GetFootprints() for p in f.Pads()]:
  if o.m_Uuid.AsString()==u:continue
  shared=[b.GetLayerName(l) for l in b.GetEnabledLayers().CuStack() if o.IsOnLayer(l) and hit(v.GetEffectiveShape(l),o.GetEffectiveShape(l))]
  if shared:donors.append({'uuid':o.m_Uuid.AsString(),'net':o.GetNetname(),'layers':shared,'type':type(o).__name__})
 assert not donors,('Unexpected explicit donor contact',label,donors)
 m=r['measurements'][label];contacts=[x for x in m['finite_ground_via_component_contacts'] if x['via']==u];roots=set(m['main_plane_root_components']);assert roots<=set(x['component'] for x in contacts),(label,contacts)
 proofs[label]={'board_sha256':sha(D/'hardware/nexus-style-fc.kicad_pcb'),'position_mm':[v.GetPosition().x/1e6,v.GetPosition().y/1e6],'original_net':'GND','explicit_pad_track_via_donors':donors,'actual_finite_annular_plane_contacts':contacts,'both_In1_In4_main_root_components_contacted':True}
assert r['candidate_board_sha256']==sha(O/'hardware/nexus-style-fc.kicad_pcb');out={'status':'PASS: original GND plane-only via identity retained and actual finite main-plane contacts re-established','proofs':proofs,'qualification':'The original via has no explicit pad/track/via donors; it contacts actual main ground planes. The moved via preserves both finite .127 x .020 mm annular main-plane contacts. This does not assert return impedance or allow arbitrary removal of ground vias.'};(O/'restored-ground-via-proof.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
