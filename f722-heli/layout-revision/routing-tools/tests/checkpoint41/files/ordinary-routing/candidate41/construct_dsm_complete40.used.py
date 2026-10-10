"""Construct source-bound DSM/D7/RPM/SBUS joint candidate; gates remain separate."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import uuid
import pcbnew as p

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'native-tools'))
from export_native_copper import export
SOURCE = ROOT / 'candidate39'
OUT = ROOT / 'candidate40'
PROPOSAL = ROOT / 'tests/dsm-coordinated-return/proposal39.json'
SOURCE_SHA = '246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7'
PROPOSAL_SHA = '9fe7a34d9abc85ecf453367f213c57edb29da36866c6cd7c61fd7d97b1a03d57'
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
read = lambda path: json.loads(Path(path).read_text())
write = lambda path, value: Path(path).write_text(json.dumps(value, indent=2) + '\n')
nm = lambda value: round(value * 1e6)
native = read(SOURCE / 'f722-heli.native.json')
route_map = read(SOURCE / 'f722-heli.logical-route-map.json')
assert sha(SOURCE / 'f722-heli.kicad_pcb') == native['board_sha256'] == route_map['board_sha256'] == SOURCE_SHA
assert sha(PROPOSAL) == PROPOSAL_SHA
proposal = read(PROPOSAL)
assert proposal['source_board_sha256'] == SOURCE_SHA
assert proposal['source_native_sha256'] == sha(SOURCE / 'f722-heli.native.json')
before = {o['uuid']: o for o in native['objects']}
remove = {o['uuid'] for o in proposal['remove_copper']}
assert len(remove) == 4 and {before[u]['net'] for u in remove} == {'GND','RPM_LV','SBUS_HV'}
assert len(proposal['add_tracks']) == 4 and set(proposal['footprint_changes']) == {'R38','R70'}
assert not OUT.exists()
OUT.mkdir()
for row in read(SOURCE / 'project-input-preservation.json')['files']:
    src=SOURCE / row['path']; dst=OUT / row['path']
    assert sha(src) == row['sha256']
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
b=p.LoadBoard(str(SOURCE/'f722-heli.kicad_pcb'))
tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
for uid in sorted(remove): b.Remove(tracks[uid])
fp={f.GetReference():f for f in b.GetFootprints()}
for ref,change in proposal['footprint_changes'].items():
    f=fp[ref]; old=change['before']; new=change['after']
    assert f.GetPosition()==p.VECTOR2I(*map(nm,old[:2]))
    assert abs(f.GetOrientationDegrees()-old[2])<1e-7 and old[2:]==new[2:]
    assert b.GetLayerName(f.GetLayer())==old[3]
    f.SetPosition(p.VECTOR2I(*map(nm,new[:2])))
mapping={u:o for u,o in route_map['logical_route_map'].items() if u not in remove}
added=[]; held=[]
owners={'DSM_RX_EXT':'DSM_RX_EXT','SBUS_HV':'SBUS_HV::P0','RPM_LV':'RPM_LV'}
def add(item,net,label):
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,SOURCE_SHA+'/'+PROPOSAL_SHA+'/'+label))
    item.SetUuid(p.KIID(uid)); item.SetNet(b.FindNet(net)); b.Add(item); held.append(item)
    added.append({'uuid':uid,'net':net,'proposal_record':label})
    if net in owners: mapping[uid]=owners[net]
for row in proposal['add_tracks']:
    assert row['width_mm']==(.25 if row['net']=='GND' else .127)
    for i,(aa,bb) in enumerate(zip(row['points_mm'],row['points_mm'][1:])):
        item=p.PCB_TRACK(b); item.SetStart(p.VECTOR2I(*map(nm,aa))); item.SetEnd(p.VECTOR2I(*map(nm,bb))); item.SetWidth(nm(row['width_mm'])); item.SetLayer(b.GetLayerID(row['layer']))
        add(item,row['net'],row['name']+'/track/'+str(i))
row=proposal['add_via']; assert row['net']=='GND' and row['diameter_mm']==.45 and row['drill_mm']==.2 and row['tented_both_faces']
item=p.PCB_VIA(b); item.SetPosition(p.VECTOR2I(*map(nm,row['xy_mm']))); item.SetWidth(450000); item.SetDrill(200000); item.SetViaType(p.VIATYPE_THROUGH); item.SetLayerPair(p.F_Cu,p.B_Cu); item.SetFrontTentingMode(p.TENTING_MODE_TENTED); item.SetBackTentingMode(p.TENTING_MODE_TENTED); add(item,'GND','GND/via')
assert len(added)==13
output=OUT/'f722-heli.kicad_pcb'; p.SaveBoard(str(output),b)
b=p.LoadBoard(str(output)); sm=p.GetSettingsManager(); assert sm.LoadProject(str(OUT/'f722-heli.kicad_pro')); b.SetProject(sm.GetProject(str(OUT/'f722-heli.kicad_pro'))); b.SynchronizeNetsAndNetClasses(False); b.BuildConnectivity(); assert p.ZONE_FILLER(b).Fill(b.Zones()); p.SaveBoard(str(output),b)
after=export(output); current={o['uuid']:o for o in after['objects']}
changed={u for u in before.keys()&current.keys() if before[u]!=current[u]}
assert set(before)-set(current)==remove and set(current)-set(before)=={o['uuid'] for o in added}
assert len(changed)==4 and {before[u]['ref'] for u in changed}=={'R38','R70'}
for u in changed:
    a=before[u]; z=current[u]; c=proposal['footprint_changes'][a['ref']]['pads'][a['number']]
    assert a['kind']==z['kind']=='pad' and a['net']==z['net']==c['net'] and a['xy']==c['before'] and z['xy']==c['after']
old_fp={f['uuid']:f for f in native['footprints']}; new_fp={f['uuid']:f for f in after['footprints']}
changed_fp={u for u in old_fp if old_fp[u]!=new_fp[u]}
assert len(changed_fp)==2 and {new_fp[u]['ref'] for u in changed_fp}=={'R38','R70'}
assert all(current[u]==before[u] for u in proposal['preserve_original_J12_branch_uuids'])
assert all(native[k]==after[k] for k in ['edge_cuts','outline_with_npth','copper_layers'])
zone_contract=lambda z:{k:v for k,v in z.items() if k not in {'filled','fill_representation'}}
assert list(map(zone_contract,native['zones']))==list(map(zone_contract,after['zones']))
(OUT/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n')
write(OUT/'f722-heli.logical-route-map.json',{'schema':'f722-logical-route-map/v1','board_sha256':sha(output),'source_sha256':SOURCE_SHA,'logical_route_map':mapping})
write(OUT/'fixed-explicit-native-ids.json',sorted((set(read(SOURCE/'fixed-explicit-native-ids.json'))-remove)|{o['uuid'] for o in added if o['net']!='GND'}))
poses=read(ROOT.parent/'integrated-routing/trial27/poses-native.json')
for ref,c in proposal['footprint_changes'].items():
    assert poses[ref]==c['before']; poses[ref]=c['after']
write(OUT/'poses-native.json',poses)
receipt={'schema':'f722-coordinated-DSM-native-construction/v1','status':'complete_joint_geometry_constructed_native_and_scoped_assembly_review_pending','source_board_sha256':SOURCE_SHA,'board_sha256':sha(output),'proposal_sha256':PROPOSAL_SHA,'constructor_sha256':sha(__file__),'source_native_sha256':sha(SOURCE/'f722-heli.native.json'),'source_map_sha256':sha(SOURCE/'f722-heli.logical-route-map.json'),'removed_source_records':[before[u] for u in sorted(remove)],'added_records':[current[o['uuid']] for o in added],'added_proposal_correspondence':added,'changed_pad_records':[{'before':before[u],'after':current[u]} for u in sorted(changed)],'changed_footprint_records':[{'before':old_fp[u],'after':new_fp[u]} for u in sorted(changed_fp)],'all_other_source_native_objects_exact':len(before)-len(remove)-len(changed),'source_J12_branch_exact':True,'reference_refill_performed':True,'native_gates_pending':True,'pose_changes_explicit':True,'ground_return_change_explicit':True,'numerical_power_VCAP_applicable':False,'direct_engine_output':False,'engine_routing_succeeded':False,'adoption_requested':False}
write(OUT/'construction-provenance.json',receipt); shutil.copy2(PROPOSAL,OUT/'coordinated-route-proposal.json'); shutil.copy2(__file__,OUT/'construct_dsm_complete40.used.py')
print(json.dumps({k:receipt[k] for k in ['board_sha256','status','all_other_source_native_objects_exact']}))
