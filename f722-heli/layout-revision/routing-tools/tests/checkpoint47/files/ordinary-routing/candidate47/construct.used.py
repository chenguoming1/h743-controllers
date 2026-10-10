import pathlib,sys,json,hashlib,uuid,shutil
import pcbnew as p
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];S=ROOT/'ordinary-routing/candidate46';D=H/'candidate01';EXPECTED='87c5ced471edaf2e0ace382d4236bc1787efb869b7ae759c53d87ee76165c0cb'
sys.path.insert(0,str(ROOT/'ordinary-routing/native-tools'));from export_native_copper import export
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest();read=lambda f:json.loads(pathlib.Path(f).read_text());write=lambda f,x:pathlib.Path(f).write_text(json.dumps(x,indent=2)+'\n');nm=lambda x:round(x*1e6)
P=H/'complete-joint-refined.json';r=read(P);PHASH=sha(P);before=read(S/'f722-heli.native.json');mapping=read(S/'f722-heli.logical-route-map.json');assert sha(S/'f722-heli.kicad_pcb')==r['source_board_sha256']==before['board_sha256']==mapping['board_sha256']==EXPECTED and r['complete'];assert len(r['routes'])==3 and all(x['found']and not x.get('violations')for x in r['routes'])
remove=set(read(H/'refined-local-repair-results.json')['removed_only_in_hypothesis']);old={o['uuid']:o for o in before['objects']};assert len(remove)==4 and all(old[u]['net']in ['+3V3_CORE','ADC_DIV_MID']for u in remove)
D.mkdir(exist_ok=False);project=read(S/'project-input-preservation.json')
for row in project['files']:
 assert sha(S/row['path'])==row['sha256'];out=D/row['path'];out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/row['path'],out)
b=p.LoadBoard(str(S/'f722-heli.kicad_pcb'));native={t.m_Uuid.AsString():t for t in b.GetTracks()}
for u in remove:b.Remove(native[u])
paths=[{'label':t['label'],'net':'SBUS_HV','layer':t['layer'],'points':t['points'],'width':.127}for t in r['routes']]+[{'label':'repair'+str(i),**t}for i,t in enumerate(r['repairs'])];vias=[{'label':'CORE-via','net':'+3V3_CORE','xy':r['COREvia']}]+[{'label':'SBUS-via'+str(i),'net':'SBUS_HV','xy':q}for i,q in enumerate(r['SBUSvias'])];ids=[];held=[];corr=[];route_map={u:v for u,v in mapping['logical_route_map'].items()if u not in remove}
def add(o,net,label):
 u=str(uuid.uuid5(uuid.NAMESPACE_URL,EXPECTED+'/'+PHASH+'/'+label));o.SetUuid(p.KIID(u));o.SetNet(b.FindNet(net));b.Add(o);held.append(o);ids.append(u);corr.append({'uuid':u,'net':net,'label':label})
 if net=='SBUS_HV':route_map[u]='SBUS_HV::P1'
 if net=='ADC_DIV_MID':route_map[u]=net
for row in paths:
 assert row['width']==(.2 if row['net']=='+3V3_CORE'else.127)
 for i,(a,z)in enumerate(zip(row['points'],row['points'][1:])):
  o=p.PCB_TRACK(b);o.SetLayer(b.GetLayerID(row['layer']));o.SetWidth(nm(row['width']));o.SetStart(p.VECTOR2I(*map(nm,a)));o.SetEnd(p.VECTOR2I(*map(nm,z)));add(o,row['net'],row['label']+'/'+str(i))
for row in vias:
 o=p.PCB_VIA(b);o.SetPosition(p.VECTOR2I(*map(nm,row['xy'])));o.SetWidth(450000);o.SetDrill(200000);o.SetViaType(p.VIATYPE_THROUGH);o.SetLayerPair(p.F_Cu,p.B_Cu);o.SetFrontTentingMode(p.TENTING_MODE_TENTED);o.SetBackTentingMode(p.TENTING_MODE_TENTED);add(o,row['net'],row['label'])
out=D/'f722-heli.kicad_pcb';p.SaveBoard(str(out),b);b=p.LoadBoard(str(out));sm=p.GetSettingsManager();assert sm.LoadProject(str(D/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(D/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(out),b)
after=export(out);now={o['uuid']:o for o in after['objects']};assert set(old)-set(now)==remove and set(now)-set(old)==set(ids);assert all(now[u]==o for u,o in old.items()if u not in remove)
for k in ['footprints','edge_cuts','outline_with_npth','copper_layers','copper_layer_ids','board_thickness_mm']:assert before[k]==after[k],k
zone=lambda z:{k:v for k,v in z.items()if k not in ['filled','fill_representation']};assert list(map(zone,before['zones']))==list(map(zone,after['zones']))
(D/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n');shutil.copy2(S/'poses-native.json',D/'poses-native.json');shutil.copy2(S/'parts.json',D/'parts.json')
write(D/'f722-heli.logical-route-map.json',{'schema':'f722-logical-route-map/v1','board_sha256':sha(out),'source_sha256':EXPECTED,'logical_route_map':route_map});write(D/'fixed-explicit-native-ids.json',sorted((set(read(S/'fixed-explicit-native-ids.json'))-remove)|set(ids)))
write(D/'construction-provenance.json',{'schema':'f722-SBUS-coordinated-native-construction/v1','source_board_sha256':EXPECTED,'board_sha256':sha(out),'source_native_sha256':sha(S/'f722-heli.native.json'),'source_map_sha256':sha(S/'f722-heli.logical-route-map.json'),'constructor_sha256':sha(__file__),'proposal_sha256':PHASH,'added_records':[now[u]for u in ids],'removed_source_records':[old[u]for u in sorted(remove)],'added_proposal_correspondence':corr,'changed_pad_records':[],'changed_footprint_records':[],'all_other_source_native_objects_exact':len(old)-len(remove),'all_156_footprints_exact':True,'all_GND_native_objects_exact':True,'all_RPM_HV_native_records_exact':True,'zone_definitions_exact':True,'native_refill_performed':True,'new_signal_vias':2,'replaced_CORE_vias':1,'numerical_power_VCAP_applicable':False,'adoption_claimed':False})
write(D/'project-input-preservation.json',{'source_board_sha256':EXPECTED,'board_sha256':sha(out),'all_listed_non_board_project_inputs_byte_identical':True,'files':project['files']});write(D/'constructed-paths.json',{'paths':paths,'vias':vias,'removed_source_uuids':sorted(remove),'source_board_sha256':EXPECTED,'board_sha256':sha(out)})
for n in ['complete-joint-proposal.json','complete-joint-refined.json','refined-local-repair-results.json','planned_adc_obstacles.json']:shutil.copy2(H/n,D/n)
print(json.dumps({'board_sha256':sha(out),'added':len(ids),'removed':len(remove),'retained':len(old)-len(remove)}))
