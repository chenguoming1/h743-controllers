import pathlib,sys,json,hashlib,uuid,shutil
import pcbnew as p
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[2];S=ROOT/'ordinary-routing/candidate45';D=HERE/'candidate01'
EXPECTED='9881a992b12fed90f17131ed627f12af77680cc2ddf95030adf8c564aaa24eb2'
sys.path.insert(0,str(ROOT/'ordinary-routing/native-tools'))
from export_native_copper import export
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest();read=lambda f:json.loads(pathlib.Path(f).read_text());write=lambda f,x:pathlib.Path(f).write_text(json.dumps(x,indent=2)+'\n')
assert sha(S/'f722-heli.kicad_pcb')==EXPECTED
old=read(S/'f722-heli.native.json');mapping=read(S/'f722-heli.logical-route-map.json');proposal=read(HERE/'rpm-F-final-proposal.json');assert old['board_sha256']==mapping['board_sha256']==proposal['source_board_sha256']==EXPECTED
assert proposal['found'] and not proposal['violations'] and proposal['minimum']['extra_clearance_mm']>=old['maximum_polygon_error_mm']
D.mkdir(exist_ok=False);project=read(S/'project-input-preservation.json')
for row in project['files']:
 assert sha(S/row['path'])==row['sha256'];out=D/row['path'];out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/row['path'],out)
b=p.LoadBoard(str(S/'f722-heli.kicad_pcb'));points=proposal['points'];newids=[];held=[]
for i,(a,z) in enumerate(zip(points,points[1:])):
 t=p.PCB_TRACK(b);u=str(uuid.uuid5(uuid.NAMESPACE_URL,EXPECTED+'/hv45/RPM_HV-P0/'+sha(HERE/'rpm-F-final-proposal.json')+'/'+str(i)));t.SetUuid(p.KIID(u));t.SetNet(b.FindNet('RPM_HV'));t.SetLayer(p.F_Cu);t.SetWidth(127000);t.SetStart(p.VECTOR2I(*[round(x*1e6)for x in a]));t.SetEnd(p.VECTOR2I(*[round(x*1e6)for x in z]));b.Add(t);newids.append(u);held.append(t)
out=D/'f722-heli.kicad_pcb';p.SaveBoard(str(out),b)
after=export(out);before={o['uuid']:o for o in old['objects']};now={o['uuid']:o for o in after['objects']};assert set(now)-set(before)==set(newids) and not set(before)-set(now);assert all(now[u]==o for u,o in before.items())
for key in ['footprints','edge_cuts','outline_with_npth','copper_layers','copper_layer_ids','board_thickness_mm','zones']:assert old[key]==after[key],key
(D/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n');shutil.copy2(S/'poses-native.json',D/'poses-native.json')
route_map=mapping['logical_route_map'];route_map.update({u:'RPM_HV::P0'for u in newids});write(D/'f722-heli.logical-route-map.json',{'schema':'f722-logical-route-map/v1','board_sha256':sha(out),'source_sha256':EXPECTED,'logical_route_map':route_map});write(D/'fixed-explicit-native-ids.json',sorted(set(read(S/'fixed-explicit-native-ids.json'))|set(newids)))
write(D/'construction-provenance.json',{'schema':'f722-HV-native-additive-construction/v1','source_board_sha256':EXPECTED,'board_sha256':sha(out),'source_native_sha256':sha(S/'f722-heli.native.json'),'source_map_sha256':sha(S/'f722-heli.logical-route-map.json'),'constructor_sha256':sha(__file__),'proposal_sha256':sha(HERE/'rpm-F-final-proposal.json'),'added_records':[now[u]for u in newids],'removed_source_records':[],'changed_pad_records':[],'changed_footprint_records':[],'all_source_native_objects_exact':len(before),'all_156_footprints_exact':True,'all_existing_route_copper_exact':True,'all_saved_zone_records_exact':True,'native_refill_performed':False,'native_refill_required':False,'no_refill_reason':'Only F.Cu tracks added; no new vias and no non-rule F.Cu zones. Saved ground planes remain byte-record exact.','new_vias':0,'numerical_power_VCAP_applicable':False,'adoption_claimed':False})
assert not any(not z['rule']and'F.Cu'in z['layers']for z in old['zones'])
write(D/'project-input-preservation.json',{'source_board_sha256':EXPECTED,'board_sha256':sha(out),'all_listed_non_board_project_inputs_byte_identical':True,'files':project['files']});print(json.dumps({'board_sha256':sha(out),'added_tracks':len(newids),'all_source_objects_exact':len(before)}))
