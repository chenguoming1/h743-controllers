import pathlib,sys,json,hashlib,uuid,shutil
import pcbnew as p
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[2];S=ROOT/'ordinary-routing/candidate48';D=HERE/'candidate01'
EXPECTED='dcdd0e5655d098ceaffa7f40b6a21f1ca101429ac8eb142c50fa96df86697e68'
sys.path.insert(0,str(ROOT/'ordinary-routing/native-tools'))
from export_native_copper import export
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest();read=lambda f:json.loads(pathlib.Path(f).read_text());write=lambda f,x:pathlib.Path(f).write_text(json.dumps(x,indent=2)+'\n')
assert sha(S/'f722-heli.kicad_pcb')==EXPECTED
old=read(S/'f722-heli.native.json');mapping=read(S/'f722-heli.logical-route-map.json');proposal=read(HERE/'proposal.json');assert old['board_sha256']==mapping['board_sha256']==proposal['source_board_sha256']==EXPECTED and proposal['passed']
D.mkdir(exist_ok=False);project=read(S/'project-input-preservation.json')
for row in project['files']:
 assert sha(S/row['path'])==row['sha256'];out=D/row['path'];out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/row['path'],out)
b=p.LoadBoard(str(S/'f722-heli.kicad_pcb'));original_tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};removed=set(proposal['removed_source_ids']);assert len(removed)==6
for u in removed:b.Remove(original_tracks[u])
held=[];newids=[];routeids=[];viaids=[]
for ri,route in enumerate(proposal['routes']):
 ids=[]
 for i,(a,z)in enumerate(zip(route['points'],route['points'][1:])):
  assert a!=z;t=p.PCB_TRACK(b);u=str(uuid.uuid5(uuid.NAMESPACE_URL,EXPECTED+'/port-a48/'+sha(HERE/'proposal.json')+'/route/'+str(ri)+'/'+str(i)));t.SetUuid(p.KIID(u));t.SetNet(b.FindNet(route['net']));t.SetLayer(b.GetLayerID(route['layer']));t.SetWidth(round(route['width']*1e6));t.SetStart(p.VECTOR2I(*[round(x*1e6)for x in a]));t.SetEnd(p.VECTOR2I(*[round(x*1e6)for x in z]));b.Add(t);newids.append(u);ids.append(u);held.append(t)
 routeids.append(ids)
for i,via in enumerate(proposal['vias']):
 xy=via['xy'];t=p.PCB_VIA(b);u=str(uuid.uuid5(uuid.NAMESPACE_URL,EXPECTED+'/port-a48/'+sha(HERE/'proposal.json')+'/via/'+str(i)));t.SetUuid(p.KIID(u));t.SetNet(b.FindNet(via['net']));t.SetPosition(p.VECTOR2I(*[round(x*1e6)for x in xy]));t.SetWidth(450000);t.SetDrill(200000);t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t);newids.append(u);viaids.append(u);held.append(t)
out=D/'f722-heli.kicad_pcb';p.SaveBoard(str(out),b);b=p.LoadBoard(str(out));sm=p.GetSettingsManager();assert sm.LoadProject(str(D/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(D/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(out),b)
after=export(out);before={o['uuid']:o for o in old['objects']};now={o['uuid']:o for o in after['objects']};physical=lambda o:{k:v for k,v in o.items()if k!='net_code'};assert set(now)-set(before)==set(newids) and set(before)-set(now)==removed;assert all(physical(o)==physical(now[u])for u,o in before.items()if u not in removed);assert old['footprints']==after['footprints']
for key in ['edge_cuts','outline_with_npth','copper_layers','copper_layer_ids','board_thickness_mm']:assert old[key]==after[key]
zone=lambda z:{k:v for k,v in z.items()if k not in ['filled','fill_representation']};assert list(map(zone,old['zones']))==list(map(zone,after['zones']))
(D/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n');shutil.copy2(S/'poses-native.json',D/'poses-native.json')
route_map={u:v for u,v in mapping['logical_route_map'].items()if u not in removed};route_map.update({u:now[u]['net']for u in newids});write(D/'f722-heli.logical-route-map.json',{'schema':'f722-logical-route-map/v1','board_sha256':sha(out),'source_sha256':EXPECTED,'logical_route_map':route_map});write(D/'fixed-explicit-native-ids.json',sorted((set(read(S/'fixed-explicit-native-ids.json'))-removed)|set(newids)))
write(D/'declared-footprint-transforms.json',{'schema':'f722-declared-footprint-transforms/v1','source_board_sha256':EXPECTED,'board_sha256':sha(out),'changes':{}})
write(D/'construction-provenance.json',{'schema':'f722-PORT-A-native-construction/v1','source_board_sha256':EXPECTED,'board_sha256':sha(out),'source_native_sha256':sha(S/'f722-heli.native.json'),'source_map_sha256':sha(S/'f722-heli.logical-route-map.json'),'constructor_sha256':sha(__file__),'proposal_sha256':sha(HERE/'proposal.json'),'routes':routeids,'vias':viaids,'added_records':[now[u]for u in newids],'removed_source_records':[before[u]for u in sorted(removed)],'changed_pad_records':[],'changed_footprint_records':[],'all_other_source_native_objects_exact_except_net_code':len(before),'all_156_footprints_exact':True,'all_existing_route_copper_exact_except_declared_removals_and_net_code':True,'native_refill_performed':True,'new_vias':len(viaids),'numerical_power_VCAP_applicable':False,'adoption_claimed':False})
write(D/'project-input-preservation.json',{'source_board_sha256':EXPECTED,'board_sha256':sha(out),'all_listed_non_board_project_inputs_byte_identical':True,'files':project['files']});shutil.copy2(S/'parts.json',D/'parts.json');shutil.copy2(HERE/'proposal.json',D/'proposal.json')
print(json.dumps({'board_sha256':sha(out),'added_tracks':len(newids)-len(viaids),'vias':len(viaids)}))
