"""Add the complete native-screened SCL trunk to the isolated I2C stage."""
import hashlib,json,shutil,sys,uuid
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'native-tools'))
from export_native_copper import export
SOURCE=ROOT/'i2c-native-stage39-master-sda'
OUT=ROOT/'i2c-native-stage39-complete-trunks'
P=ROOT/'tests/i2c-candidate39-joint/current-scl-native-bridge-proposal.json'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
read=lambda path:json.loads(Path(path).read_text())
write=lambda path,value:Path(path).write_text(json.dumps(value,indent=2)+'\n')
q=read(P); native=read(SOURCE/'f722-heli.native.json'); lm=read(SOURCE/'f722-heli.logical-route-map.json')
h=sha(SOURCE/'f722-heli.kicad_pcb')
assert h==q['source_board_sha256']==native['board_sha256']==lm['board_sha256']=='24c8794a471a49d9901adf236950af6faa29d5efb4a8a3b718cd5228d4d501ec'
assert sha(SOURCE/'f722-heli.native.json')==q['source_native_sha256']
assert q['complete_geometry_found'] and q['via']['pass']
assert all(r['native_check']['pass'] for r in q['routes'])
assert not OUT.exists(); OUT.mkdir()
for row in read(ROOT/'candidate39/project-input-preservation.json')['files']:
    src=SOURCE/row['path'];dst=OUT/row['path'];assert sha(src)==row['sha256'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
b=p.LoadBoard(str(SOURCE/'f722-heli.kicad_pcb')); mapping=dict(lm['logical_route_map']);added=[];held=[]
nm=lambda x:round(x*1e6)
def add(item,label):
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,h+'/'+sha(P)+'/'+label));item.SetUuid(p.KIID(uid));item.SetNet(b.FindNet('BARO_SCL'));b.Add(item);held.append(item);added.append(uid);mapping[uid]='BARO_SCL'
for j,r in enumerate(q['routes']):
    assert r['layer'] in ['In2.Cu','In3.Cu']
    for i,(a,z) in enumerate(zip(r['points_mm'],r['points_mm'][1:])):
        dx,dy=abs(a[0]-z[0]),abs(a[1]-z[1]);assert min(dx,dy)<1e-9 or abs(dx-dy)<1e-8
        t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*map(nm,a)));t.SetEnd(p.VECTOR2I(*map(nm,z)));t.SetWidth(127000);t.SetLayer(b.GetLayerID(r['layer']));add(t,f'track/{j}/{i}')
v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(*map(nm,q['via']['xy_mm'])));v.SetWidth(450000);v.SetDrill(200000);v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetFrontTentingMode(p.TENTING_MODE_TENTED);v.SetBackTentingMode(p.TENTING_MODE_TENTED);add(v,'via')
assert len(added)==6
output=OUT/'f722-heli.kicad_pcb';p.SaveBoard(str(output),b)
b=p.LoadBoard(str(output));sm=p.GetSettingsManager();assert sm.LoadProject(str(OUT/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(OUT/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(output),b)
after=export(output); before={o['uuid']:o for o in native['objects']};current={o['uuid']:o for o in after['objects']}
assert set(current)-set(before)==set(added) and all(current[u]==o for u,o in before.items())
assert all(native[k]==after[k] for k in ['footprints','edge_cuts','outline_with_npth','copper_layers'])
zone=lambda z:{k:v for k,v in z.items() if k not in {'filled','fill_representation'}}
assert list(map(zone,native['zones']))==list(map(zone,after['zones']))
(OUT/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n')
write(OUT/'f722-heli.logical-route-map.json',{'schema':'f722-logical-route-map/v1','board_sha256':sha(output),'source_sha256':h,'logical_route_map':mapping})
write(OUT/'fixed-explicit-native-ids.json',sorted(set(read(SOURCE/'fixed-explicit-native-ids.json'))|set(added)))
shutil.copy2(SOURCE/'poses-native.json',OUT/'poses-native.json')
receipt={'schema':'f722-I2C-complete-trunks-native-stage/v1','status':'partial_joint_candidate_PORT_C_reconstruction_pending','source_board_sha256':h,'accepted_origin_board_sha256':'246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7','board_sha256':sha(output),'constructor_sha256':sha(__file__),'proposal_sha256':sha(P),'source_native_sha256':sha(SOURCE/'f722-heli.native.json'),'source_map_sha256':sha(SOURCE/'f722-heli.logical-route-map.json'),'added_records':[current[u] for u in added],'all_source_objects_exact':len(before),'all_poses_exact_to_source':True,'remaining':['Restore protected PORT_C_TX_EXT::P0','Rebind accepted DSM41 transaction if adopted','All finite-entry/support/I2C/reference checks and fresh numerical power review'],'numerical_power_VCAP_applicable':False,'direct_engine_output':False,'engine_routing_succeeded':False,'adoption_claimed':False}
write(OUT/'construction-provenance.json',receipt)
for f in [P,Path(__file__)]:shutil.copy2(f,OUT/f.name)
print(json.dumps({'board_sha256':receipt['board_sha256'],'added_tracks':5,'added_vias':1,'retained_objects_exact':len(before),'status':receipt['status']}))
