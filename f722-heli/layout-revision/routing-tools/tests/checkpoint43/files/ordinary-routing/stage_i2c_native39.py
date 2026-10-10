"""Build the explicit partial I2C/R8/supply hypothesis on accepted candidate39.

No adoption: R7, both trunks and the removed PORT_C P0 transition must be
completed, and pose/power/reference effects independently reviewed.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import pcbnew as p

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'native-tools'))
from export_native_copper import export
SOURCE = ROOT / 'candidate39'
OUT = ROOT / 'i2c-native-stage39'
PROPOSAL = ROOT / 'tests/i2c-candidate39-local/selected-i2c-rebind39.json'
SOURCE_SHA = '246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7'
PROPOSAL_SHA = '94dbda5651914199107ba75b475d585a06a15aca287200335e173fcff6de3a45'
ALLOW = {'0e6f0faf-8c32-4664-a3bc-ae37381c0f90', '3413f8ef-c004-41b3-9dcc-3e63b3ffec61', '6a9e5e14-fdf0-43c9-bfa1-f9d7993c77f2', 'a0065c8a-5f87-41f3-92f2-0ea3e8c0598f', 'd61e1419-f97a-418d-93a5-f013edf6e7f4', 'fdeef86c-c702-4a15-a273-0602f22a19d1'}
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
read = lambda path: json.loads(Path(path).read_text())
write = lambda path, value: Path(path).write_text(json.dumps(value, indent=2) + '\n')
nm = lambda value: round(value * 1e6)
native = read(SOURCE / 'f722-heli.native.json')
route_map = read(SOURCE / 'f722-heli.logical-route-map.json')
assert sha(SOURCE / 'f722-heli.kicad_pcb') == native['board_sha256'] == route_map['board_sha256'] == SOURCE_SHA
assert sha(PROPOSAL) == PROPOSAL_SHA
proposal = read(PROPOSAL)
assert proposal['source_board_sha256'] == SOURCE_SHA and proposal['all_selected_geometry_checks_pass']
assert set(proposal['selected_hypothesis']['removed_existing_object_ids']) == ALLOW
assert proposal['selected_hypothesis']['R8_center_mm'] == [23.5,24.0]
before = {o['uuid']: o for o in native['objects']}
assert all(before[u]['net'] in {'+3V3_CORE','PORT_C_TX_EXT'} for u in ALLOW)
assert sum(before[u]['net']=='+3V3_CORE' for u in ALLOW)==2
assert not OUT.exists()
OUT.mkdir()
for row in read(SOURCE / 'project-input-preservation.json')['files']:
    src=SOURCE / row['path'];dst=OUT / row['path']
    assert sha(src)==row['sha256']
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
b=p.LoadBoard(str(SOURCE/'f722-heli.kicad_pcb'))
tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
for uid in sorted(ALLOW):b.Remove(tracks[uid])
r8=next(f for f in b.GetFootprints() if f.GetReference()=='R8')
assert r8.GetPosition()==p.VECTOR2I(23500000,23600000)
r8.SetPosition(p.VECTOR2I(23500000,24000000))
mapping={u:o for u,o in route_map['logical_route_map'].items() if u not in ALLOW}
added=[];held=[]
for index,row in enumerate(proposal['paths']):
    assert row['net'] in {'BARO_SCL','BARO_SDA','+3V3_CORE'}
    assert row['width_mm']==(.2 if row['net']=='+3V3_CORE' else .127)
    assert row['layer'] in {'F.Cu','B.Cu'}
    for aa,bb in zip(row['points_mm'],row['points_mm'][1:]):
        item=p.PCB_TRACK(b);item.SetStart(p.VECTOR2I(*map(nm,aa)));item.SetEnd(p.VECTOR2I(*map(nm,bb)));item.SetWidth(nm(row['width_mm']));item.SetLayer(b.GetLayerID(row['layer']));item.SetNet(b.FindNet(row['net']));b.Add(item);held.append(item)
        uid=item.m_Uuid.AsString();added.append({'uuid':uid,'net':row['net'],'proposal_path_index':index})
        if row['net'].startswith('BARO_'):mapping[uid]=row['net']
for index,row in enumerate(proposal['vias']):
    assert row['net'] in {'BARO_SCL','BARO_SDA'} and row['diameter_mm']==.45 and row['drill_mm']==.20
    item=p.PCB_VIA(b);item.SetPosition(p.VECTOR2I(*map(nm,row['xy_mm'])));item.SetWidth(450000);item.SetDrill(200000);item.SetViaType(p.VIATYPE_THROUGH);item.SetLayerPair(p.F_Cu,p.B_Cu);item.SetFrontTentingMode(p.TENTING_MODE_TENTED);item.SetBackTentingMode(p.TENTING_MODE_TENTED);item.SetNet(b.FindNet(row['net']));b.Add(item);held.append(item)
    uid=item.m_Uuid.AsString();added.append({'uuid':uid,'net':row['net'],'proposal_via_index':index});mapping[uid]=row['net']
assert len(added)==15
output=OUT/'f722-heli.kicad_pcb';p.SaveBoard(str(output),b)
b=p.LoadBoard(str(output));sm=p.GetSettingsManager();assert sm.LoadProject(str(OUT/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(OUT/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(output),b)
after=export(output);current={o['uuid']:o for o in after['objects']};changed={u for u in before.keys()&current.keys() if before[u]!=current[u]}
assert set(before)-set(current)==ALLOW and set(current)-set(before)=={o['uuid'] for o in added}
assert len(changed)==2 and all(before[u]['ref']=='R8' and before[u]['kind']=='pad' for u in changed)
assert all(current[u]['net']==before[u]['net'] and current[u]['xy']==[before[u]['xy'][0],round(before[u]['xy'][1]+.4,6)] for u in changed)
old_fp={f['uuid']:f for f in native['footprints']};new_fp={f['uuid']:f for f in after['footprints']};changed_fp={u for u in old_fp if old_fp[u]!=new_fp[u]}
assert len(changed_fp)==1 and next(iter(new_fp[u]['ref'] for u in changed_fp))=='R8'
assert all(native[k]==after[k] for k in ['edge_cuts','outline_with_npth','copper_layers'])
zone_contract=lambda z:{k:v for k,v in z.items() if k not in {'filled','fill_representation'}}
assert list(map(zone_contract,native['zones']))==list(map(zone_contract,after['zones']))
(OUT/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n')
write(OUT/'f722-heli.logical-route-map.json',{'schema':'f722-logical-route-map/v1','board_sha256':sha(output),'source_sha256':SOURCE_SHA,'logical_route_map':mapping})
write(OUT/'fixed-explicit-native-ids.json',sorted((set(read(SOURCE/'fixed-explicit-native-ids.json'))-ALLOW)|{o['uuid'] for o in added if o['net'].startswith('BARO_')}))
poses=read(ROOT.parent/'integrated-routing/trial27/poses-native.json');assert poses['R8']==[23.5,23.6,90.0,'B.Cu'];poses['R8']=[23.5,24.0,90.0,'B.Cu'];write(OUT/'poses-native.json',poses)
receipt={'schema':'f722-isolated-I2C-native-hypothesis/v1','status':'partial_joint_candidate_not_adopted','source_board_sha256':SOURCE_SHA,'board_sha256':sha(output),'proposal_sha256':PROPOSAL_SHA,'constructor_sha256':sha(__file__),'source_native_sha256':sha(SOURCE/'f722-heli.native.json'),'source_map_sha256':sha(SOURCE/'f722-heli.logical-route-map.json'),'removed_source_records':[before[u] for u in sorted(ALLOW)],'added_records':added,'changed_pad_records':[{'before':before[u],'after':current[u]} for u in sorted(changed)],'changed_footprint_records':[{'before':old_fp[u],'after':new_fp[u]} for u in sorted(changed_fp)],'all_other_source_native_objects_exact':len(before)-len(ALLOW)-len(changed),'remaining':['Restore PORT_C_TX_EXT::P0','Complete SCL R7 branch and MCU/sensor trunk','Complete SDA MCU/sensor trunk'],'reference_refill_performed':True,'native_gates_pending':True,'pose_change_explicit':True,'power_topology_change_explicit':True,'fresh_power_DC_reference_revalidation_required':True,'numerical_power_VCAP_applicable':False,'direct_engine_output':False,'adoption_requested':False}
write(OUT/'construction-provenance.json',receipt);shutil.copy2(PROPOSAL,OUT/'selected-I2C-hypothesis.json');shutil.copy2(__file__,OUT/'stage_i2c_native39.used.py')
print(json.dumps({k:receipt[k] for k in ['board_sha256','status','all_other_source_native_objects_exact']}))
