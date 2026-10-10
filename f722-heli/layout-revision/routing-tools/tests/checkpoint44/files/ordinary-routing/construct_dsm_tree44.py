"""Construct complete DSM tree and declared full-width BEC bend from accepted43."""
import hashlib,json,pathlib,shutil,sys,uuid
import pcbnew as p
R=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(R/'native-tools'));from export_native_copper import export
S=R/'candidate43';D=R/'candidate44';P=R/'tests/dsm-mcu-candidate43/complete-tree-proposal.json';EXPECTED='1ee7174a578dffe4d5ef3ae8b39d8dc88f28b80395539263a65f23be234c21e6';PHASH='9798bd44a63920ff5e561d7e570b73684050eb5ee330f7e4314b42e2dd13a4ac'
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest();read=lambda f:json.loads(pathlib.Path(f).read_text());write=lambda f,v:pathlib.Path(f).write_text(json.dumps(v,indent=2)+'\n');nm=lambda v:round(v*1e6)
proposal=read(P);native=read(S/'f722-heli.native.json');mapping=read(S/'f722-heli.logical-route-map.json');assert sha(P)==PHASH and sha(S/'f722-heli.kicad_pcb')==native['board_sha256']==mapping['board_sha256']==proposal['source_board_sha256']==EXPECTED
assert proposal['all_nominal_geometry_passed'] and proposal['footprint_changes']==[]
assert proposal['source_native_sha256']==sha(S/'f722-heli.native.json')
for path,h in proposal['input_sha256'].items():assert sha(R/path)==h
assert not D.exists();D.mkdir();project=read(S/'project-input-preservation.json')
for row in project['files']:
 assert sha(S/row['path'])==row['sha256'];out=D/row['path'];out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/row['path'],out)
b=p.LoadBoard(str(S/'f722-heli.kicad_pcb'));before={o['uuid']:o for o in native['objects']};remove=set(proposal['remove_copper_uuids']);assert len(remove)==2 and all(before[u]['kind']=='track' and before[u]['net']=='+5V_BEC' and before[u]['width']==.6 for u in remove)
old={t.m_Uuid.AsString():t for t in b.GetTracks()}
for u in remove:b.Remove(old[u])
newids=[];held=[];correspondence=[];route_map={u:v for u,v in mapping['logical_route_map'].items()if u not in remove}
def add(t,net,label):
 u=str(uuid.uuid5(uuid.NAMESPACE_URL,EXPECTED+'/'+PHASH+'/'+label));t.SetUuid(p.KIID(u));t.SetNet(b.FindNet(net));b.Add(t);held.append(t);newids.append(u);correspondence.append(dict(uuid=u,net=net,proposal_record=label))
 if net=='DSM_RX_MCU':route_map[u]=net
for row in proposal['paths']:
 assert row['width_mm']==(.6 if row['net']=='+5V_BEC' else .127)
 for i,(a,z)in enumerate(zip(row['points_mm'],row['points_mm'][1:])):
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*map(nm,a)));t.SetEnd(p.VECTOR2I(*map(nm,z)));t.SetWidth(nm(row['width_mm']));t.SetLayer(b.GetLayerID(row['layer']));add(t,row['net'],row['label']+'/'+str(i))
for v in proposal['vias']:
 assert v['net']=='DSM_RX_MCU' and v['diameter_mm']==.45 and v['drill_mm']==.2 and v['tented_both_faces']
 t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(*map(nm,v['xy_mm'])));t.SetWidth(450000);t.SetDrill(200000);t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);add(t,v['net'],v['label']+'/via')
out=D/'f722-heli.kicad_pcb';p.SaveBoard(str(out),b);b=p.LoadBoard(str(out));sm=p.GetSettingsManager();assert sm.LoadProject(str(D/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(D/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(out),b)
after=export(out);now={o['uuid']:o for o in after['objects']};assert set(before)-set(now)==remove and set(now)-set(before)==set(newids);assert all(now[u]==v for u,v in before.items()if u not in remove)
assert all(native[k]==after[k]for k in ['footprints','edge_cuts','outline_with_npth','copper_layers','copper_layer_ids','board_thickness_mm']);zone=lambda z:{k:v for k,v in z.items()if k not in ['filled','fill_representation']};assert list(map(zone,native['zones']))==list(map(zone,after['zones']))
(D/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n');write(D/'f722-heli.logical-route-map.json',{'schema':'f722-logical-route-map/v1','board_sha256':sha(out),'source_sha256':EXPECTED,'logical_route_map':route_map});write(D/'fixed-explicit-native-ids.json',sorted((set(read(S/'fixed-explicit-native-ids.json'))-remove)|set(newids)));shutil.copy2(S/'poses-native.json',D/'poses-native.json')
write(D/'project-input-preservation.json',{'source_board_sha256':EXPECTED,'board_sha256':sha(out),'all_listed_non_board_project_inputs_byte_identical':True,'files':project['files']})
r={'schema':'f722-complete-DSM-tree-native-construction/v1','source_board_sha256':EXPECTED,'board_sha256':sha(out),'source_native_sha256':sha(S/'f722-heli.native.json'),'source_map_sha256':sha(S/'f722-heli.logical-route-map.json'),'proposal_sha256':PHASH,'constructor_sha256':sha(__file__),'removed_source_records':[before[u]for u in sorted(remove)],'added_records':[now[u]for u in newids],'added_proposal_correspondence':correspondence,'changed_pad_records':[],'changed_footprint_records':[],'all_other_source_native_objects_exact':len(before)-len(remove),'all_156_footprints_exact':True,'all_existing_signal_objects_exact':True,'all_GND_native_objects_exact':True,'BEC_width_preserved_mm':.6,'native_refill_performed':True,'native_gates_pending':True,'direct_engine_output':False,'engine_routing_succeeded':False,'numerical_power_VCAP_applicable':False,'adoption_claimed':False}
write(D/'construction-provenance.json',r);shutil.copy2(P,D/'complete-tree-proposal.json');shutil.copy2(__file__,D/'construct_dsm_tree44.used.py');print(json.dumps({'board_sha256':r['board_sha256'],'added':len(newids),'removed':len(remove),'preserved':r['all_other_source_native_objects_exact']}))
