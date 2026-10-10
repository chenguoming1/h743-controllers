"""Extend the isolated I2C stage with reviewed R7 move/SDA route and feed cleanup."""
import copy,hashlib,json,shutil,sys,uuid
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'native-tools'))
from export_native_copper import export
SOURCE=ROOT/'i2c-native-stage39'; ORIGIN=ROOT/'candidate39'; OUT=ROOT/'i2c-native-stage39-master-sda'
SOURCE_SHA='e78a7a1b5db02a678360769eace59c900304b830a35c5303797760e4efa539f2'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
read=lambda path:json.loads(Path(path).read_text())
write=lambda path,value:Path(path).write_text(json.dumps(value,indent=2)+'\n')
nm=lambda x:round(x*1e6)
P=ROOT/'tests/i2c-candidate39-master-pullup/selected-R7-master39.json'
Q=ROOT/'tests/i2c-candidate39-joint/sda-native-bridge-proposal.json'
C=ROOT/'tests/i2c-candidate39-joint/relocated-R7-feed-cleanup-proposal.json'
assert sha(P)=='7cfe6f1b213f72a476b511cd569050ae6b07a0b3b623203e8bc7d4f2dd25422b'
assert sha(Q)=='2295091013c658d9708c3ff02174e348c4f5211ad1a4b1965342f76753f810e2'
assert sha(C)=='ce64ab2e51d3dd8a347a48d3968aa3caa3f8afb288a233f40a3b1ac52233fdfa'
rp,sp,cp=read(P),read(Q),read(C)
assert rp['all_local_checks_pass'] and sp['complete_geometry_found'] and sp['via']['pass']
assert cp['source_stage_board_sha256']==SOURCE_SHA and cp['all_source_core_supply_pads_retained_in_one_copper_component']
native=read(SOURCE/'f722-heli.native.json');lm=read(SOURCE/'f722-heli.logical-route-map.json')
assert sha(SOURCE/'f722-heli.kicad_pcb')==native['board_sha256']==lm['board_sha256']==SOURCE_SHA
before={o['uuid']:o for o in native['objects']}; remove={o['uuid'] for o in cp['removed_source_records']}
assert len(remove)==5 and all(before[o['uuid']]==o for o in cp['removed_source_records'])
assert not OUT.exists();OUT.mkdir()
for row in read(ORIGIN/'project-input-preservation.json')['files']:
    src=SOURCE/row['path']; dst=OUT/row['path']; assert sha(src)==row['sha256'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
b=p.LoadBoard(str(SOURCE/'f722-heli.kicad_pcb'))
tracks={item.m_Uuid.AsString():item for item in b.GetTracks()}
for uid in sorted(remove):b.Remove(tracks[uid])
r7=next(f for f in b.GetFootprints() if f.GetReference()=='R7')
assert r7.GetPosition()==p.VECTOR2I(23500000,21600000) and r7.GetLayer()==p.B_Cu and r7.GetOrientationDegrees()==90
r7.Flip(r7.GetPosition(),False); r7.SetOrientationDegrees(-90); r7.SetPosition(p.VECTOR2I(19369000,14373000))
mapping={u:v for u,v in lm['logical_route_map'].items() if u not in remove};added=[];held=[]
def add(item,net,label):
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,SOURCE_SHA+'/'+sha(P)+'/'+sha(Q)+'/'+label));item.SetUuid(p.KIID(uid));item.SetNet(b.FindNet(net));b.Add(item);held.append(item);added.append(uid)
    if net.startswith('BARO_'):mapping[uid]=net
paths=rp['paths']+[{'net':'BARO_SDA','layer':r['layer'],'width_mm':.127,'points_mm':r['points_mm']} for r in sp['routes']]
for j,row in enumerate(paths):
    assert row['width_mm']==(.2 if row['net']=='+3V3_CORE' else .127)
    for i,(a,z) in enumerate(zip(row['points_mm'],row['points_mm'][1:])):
        dx=abs(z[0]-a[0]);dy=abs(z[1]-a[1]);assert min(dx,dy)<1e-9 or abs(dx-dy)<1e-8
        t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*map(nm,a)));t.SetEnd(p.VECTOR2I(*map(nm,z)));t.SetWidth(nm(row['width_mm']));t.SetLayer(b.GetLayerID(row['layer']));add(t,row['net'],f'path/{j}/{i}')
via=p.PCB_VIA(b);via.SetPosition(p.VECTOR2I(*map(nm,sp['via']['xy_mm'])));via.SetWidth(450000);via.SetDrill(200000);via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetFrontTentingMode(p.TENTING_MODE_TENTED);via.SetBackTentingMode(p.TENTING_MODE_TENTED);add(via,'BARO_SDA','via/bridge')
assert len(added)==19
output=OUT/'f722-heli.kicad_pcb';p.SaveBoard(str(output),b)
b=p.LoadBoard(str(output));sm=p.GetSettingsManager();assert sm.LoadProject(str(OUT/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(OUT/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(output),b)
after=export(output);current={o['uuid']:o for o in after['objects']};changed={u for u in before.keys()&current.keys() if before[u]!=current[u]}
assert set(before)-set(current)==remove and set(current)-set(before)==set(added)
assert {before[u].get('key') for u in changed}=={'R7.1','R7.2'}
expected={o['uuid']:o for o in cp['relocated_R7_native_pads']}
for u in changed:
    # The read-only pose export intentionally omits invariant exporter fields
    # and mask expansion. Restore them from the exact source, not by omission.
    full=copy.deepcopy(before[u]); full.update({k:v for k,v in expected[u].items() if k!='mask'})
    full['all_layers']=[l.replace('B.','F.') for l in before[u]['all_layers']]
    full['shape_by_layer']={'F.Cu':before[u]['shape_by_layer']['B.Cu']}
    full['mask']={'F.Mask':{'expansion':before[u]['mask']['B.Mask']['expansion'],'polygons':expected[u]['mask']['F.Mask']['polygons']}}
    assert current[u]==full,('Unexpected R7 pad field',u)
oldfp={f['uuid']:f for f in native['footprints']};newfp={f['uuid']:f for f in after['footprints']}
assert {oldfp[u]['ref'] for u in oldfp if oldfp[u]!=newfp[u]}=={'R7'}
assert all(native[k]==after[k] for k in ['edge_cuts','outline_with_npth','copper_layers'])
zone=lambda z:{k:v for k,v in z.items() if k not in {'filled','fill_representation'}}
assert list(map(zone,native['zones']))==list(map(zone,after['zones']))
(OUT/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n')
write(OUT/'f722-heli.logical-route-map.json',{'schema':'f722-logical-route-map/v1','board_sha256':sha(output),'source_sha256':SOURCE_SHA,'logical_route_map':mapping})
write(OUT/'fixed-explicit-native-ids.json',sorted((set(read(SOURCE/'fixed-explicit-native-ids.json'))-remove)|{u for u in added if current[u]['net'].startswith('BARO_')}))
poses=read(SOURCE/'poses-native.json');assert poses['R7']==[23.5,21.6,90.0,'B.Cu'];poses['R7']=[19.369,14.373,-90.0,'F.Cu'];write(OUT/'poses-native.json',poses)
receipt={'schema':'f722-I2C-master-SDA-native-stage/v1','status':'partial_joint_candidate_not_adopted','source_board_sha256':SOURCE_SHA,'accepted_origin_board_sha256':'246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7','board_sha256':sha(output),'constructor_sha256':sha(__file__),'R7_proposal_sha256':sha(P),'SDA_proposal_sha256':sha(Q),'feed_cleanup_proposal_sha256':sha(C),'source_native_sha256':sha(SOURCE/'f722-heli.native.json'),'source_map_sha256':sha(SOURCE/'f722-heli.logical-route-map.json'),'removed_records':[before[u] for u in sorted(remove)],'added_records':[current[u] for u in added],'changed_pad_records':[{'before':before[u],'after':current[u]} for u in sorted(changed)],'changed_footprint_records':[{'before':oldfp[u],'after':newfp[u]} for u in oldfp if oldfp[u]!=newfp[u]],'all_other_source_objects_exact':len(before)-len(remove)-len(changed),'remaining':['Complete SCL MCU/sensor trunk','Restore protected PORT_C_TX_EXT::P0','All native finite-entry/pose/support/I2C/reference checks and fresh numerical power review'],'numerical_power_VCAP_applicable':False,'engine_routing_succeeded':False,'direct_engine_output':False,'adoption_claimed':False}
write(OUT/'construction-provenance.json',receipt)
for f in [P,Q,C,Path(__file__)]:shutil.copy2(f,OUT/f.name)
print(json.dumps({k:receipt[k] for k in ['board_sha256','status','all_other_source_objects_exact']}))
