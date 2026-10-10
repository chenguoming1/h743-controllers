import pathlib,sys,json,hashlib,uuid,shutil
import pcbnew as p
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
S=ROOT/'ordinary-routing/candidate44';D=HERE/'candidate01'
EXPECTED='02d2090ad7220a64a8f4a1a259d522f7b0bca3e15214b73107491d17626bd51f'
sys.path.insert(0,str(ROOT/'ordinary-routing/native-tools'))
from export_native_copper import export
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
read=lambda f:json.loads(pathlib.Path(f).read_text())
write=lambda f,x:pathlib.Path(f).write_text(json.dumps(x,indent=2)+'\n')
assert sha(S/'f722-heli.kicad_pcb')==EXPECTED
old=read(S/'f722-heli.native.json');mapping=read(S/'f722-heli.logical-route-map.json');assert old['board_sha256']==mapping['board_sha256']==EXPECTED
D.mkdir(exist_ok=False)
project=read(S/'project-input-preservation.json')
for row in project['files']:
 assert sha(S/row['path'])==row['sha256'];out=D/row['path'];out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/row['path'],out)
b=p.LoadBoard(str(S/'f722-heli.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};f=fps['TP5'];assert f.GetLayerName()=='F.Cu' and f.GetValue()=='SWD NRST';f.Flip(f.GetPosition(),False);f.SetOrientationDegrees(0);f.SetPosition(p.VECTOR2I(16900000,6000000))
points=[[16.9,6.0],[17.12882,6.22882],[17.12882,6.83933]];newids=[];held=[]
for i,(a,z) in enumerate(zip(points,points[1:])):
 t=p.PCB_TRACK(b);u=str(uuid.uuid5(uuid.NAMESPACE_URL,EXPECTED+'/debug-testpoint44/NRST/'+str(i)));t.SetUuid(p.KIID(u));t.SetNet(b.FindNet('NRST'));t.SetLayer(p.B_Cu);t.SetWidth(127000);t.SetStart(p.VECTOR2I(*[round(x*1e6)for x in a]));t.SetEnd(p.VECTOR2I(*[round(x*1e6)for x in z]));b.Add(t);newids.append(u);held.append(t)
out=D/'f722-heli.kicad_pcb';p.SaveBoard(str(out),b);b=p.LoadBoard(str(out));sm=p.GetSettingsManager();assert sm.LoadProject(str(D/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(D/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(out),b)
after=export(out);before={o['uuid']:o for o in old['objects']};now={o['uuid']:o for o in after['objects']};physical=lambda o:{k:v for k,v in o.items()if k!='net_code'};changed={u for u in before if physical(before[u])!=physical(now[u])};renumbered=[{'uuid':u,'net':before[u]['net'],'before_net_code':before[u]['net_code'],'after_net_code':now[u]['net_code']}for u in before if before[u]['net_code']!=now[u]['net_code']];assert set(now)-set(before)==set(newids) and set(before)-set(now)==set();assert len(changed)==1 and before[next(iter(changed))]['key']=='TP5.1'
oldfp={o['uuid']:o for o in old['footprints']};newfp={o['uuid']:o for o in after['footprints']};fpchanged={u for u in oldfp if oldfp[u]!=newfp[u]};assert len(fpchanged)==1 and oldfp[next(iter(fpchanged))]['ref']=='TP5'
for key in ['edge_cuts','outline_with_npth','copper_layers','copper_layer_ids','board_thickness_mm']:assert old[key]==after[key]
zone=lambda z:{k:v for k,v in z.items()if k not in ['filled','fill_representation']};assert list(map(zone,old['zones']))==list(map(zone,after['zones']))
(D/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n');poses=read(S/'poses-native.json');assert poses['TP5']==[37.0,23.8,0.0,'F.Cu'];poses['TP5']=[16.9,6.0,0.0,'B.Cu'];write(D/'poses-native.json',poses)
route_map=mapping['logical_route_map'];route_map.update({u:'NRST'for u in newids});write(D/'f722-heli.logical-route-map.json',{'schema':'f722-logical-route-map/v1','board_sha256':sha(out),'source_sha256':EXPECTED,'logical_route_map':route_map});write(D/'fixed-explicit-native-ids.json',sorted(set(read(S/'fixed-explicit-native-ids.json'))|set(newids)))
write(D/'declared-footprint-transforms.json',{'schema':'f722-declared-footprint-transforms/v1','source_board_sha256':EXPECTED,'board_sha256':sha(out),'changes':{'TP5':{'before':[37.0,23.8,0.0,'F.Cu'],'after':poses['TP5'],'flip_left_right':False}}})
write(D/'construction-provenance.json',{'schema':'f722-debug-testpoint-native-construction/v1','source_board_sha256':EXPECTED,'board_sha256':sha(out),'source_native_sha256':sha(S/'f722-heli.native.json'),'source_map_sha256':sha(S/'f722-heli.logical-route-map.json'),'constructor_sha256':sha(__file__),'added_records':[now[u]for u in newids],'removed_source_records':[],'changed_pad_records':[{'before':before[u],'after':now[u]}for u in changed],'changed_footprint_records':[{'before':oldfp[u],'after':newfp[u]}for u in fpchanged],'all_other_source_native_objects_exact_except_net_code':len(before)-len(changed),'runtime_net_code_reindexing':renumbered,'runtime_net_code_reindexing_scope':'Native name-to-integer lookup indices only; every retained net name and native board net identity is preserved. Raw before/after indices are retained here.','all_other_155_footprints_exact':True,'all_existing_route_copper_exact':True,'native_refill_performed':True,'new_vias':0,'numerical_power_VCAP_applicable':False,'adoption_claimed':False})
write(D/'project-input-preservation.json',{'source_board_sha256':EXPECTED,'board_sha256':sha(out),'all_listed_non_board_project_inputs_byte_identical':True,'files':project['files']})
print(json.dumps({'board_sha256':sha(out),'added_tracks':len(newids),'moved_footprints':['TP5']}))
