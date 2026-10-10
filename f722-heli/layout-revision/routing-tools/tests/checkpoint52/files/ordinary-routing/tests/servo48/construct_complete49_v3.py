"""Native successor from accepted49; no canonical or repository mutation."""
import pathlib,sys,json,hashlib,uuid,shutil
import pcbnew as p
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];S=R/'candidate49';D=H/'candidate03';EXPECTED='15499b28bb63a8c2326c8c7e73dbac4198b8333b05325ab35653825848ae9069'
sys.path.insert(0,str(R/'native-tools'));from export_native_copper import export
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest();read=lambda f:json.loads(pathlib.Path(f).read_text());write=lambda f,x:pathlib.Path(f).write_text(json.dumps(x,indent=2)+'\n')
P=H/'complete-proposal49-v3.json';plan=read(P);assert plan['source_sha256']==sha(S/'f722-heli.kicad_pcb')==EXPECTED and plan['all_paths_found'];native=read(S/'f722-heli.native.json');mapping=read(S/'f722-heli.logical-route-map.json');assert native['board_sha256']==mapping['board_sha256']==EXPECTED
D.mkdir(exist_ok=False);project=read(S/'project-input-preservation.json')
for row in project['files']:
 assert sha(S/row['path'])==row['sha256'];out=D/row['path'];out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/row['path'],out)
b=p.LoadBoard(str(S/'f722-heli.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};f=fps['R23'];assert [p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)]==[13.85,7.8] and f.GetLayerName()=='F.Cu';remove=set(plan['removed']);oldtracks={t.m_Uuid.AsString():t for t in b.GetTracks()};assert remove<=oldtracks.keys()
for u in remove:b.Remove(oldtracks[u])
held=[];newids=[];routeids=[];viaids=[];rmap={u:v for u,v in mapping['logical_route_map'].items()if u not in remove}
def add(t,net,label,owner):
 u=str(uuid.uuid5(uuid.NAMESPACE_URL,EXPECTED+'/'+sha(P)+'/'+label));t.SetUuid(p.KIID(u));t.SetNet(b.FindNet(net));b.Add(t);held.append(t);newids.append(u)
 if owner:rmap[u]=owner
 return u
for ri,r in enumerate(plan['routes']):
 ids=[];owner=r.get('owner',r['net'] if r['net']!='+3V3_CORE' else None)
 for i,(aa,bb)in enumerate(zip(r['points'],r['points'][1:])):
  if aa==bb:continue
  t=p.PCB_TRACK(b);t.SetLayer(b.GetLayerID(r['layer']));t.SetWidth(round(r['width']*1e6));t.SetStart(p.VECTOR2I(*[round(v*1e6)for v in aa]));t.SetEnd(p.VECTOR2I(*[round(v*1e6)for v in bb]));ids.append(add(t,r['net'],f'route/{ri}/{i}',owner))
 routeids.append(ids)
for vi,r in enumerate(plan['vias']):
 t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(*[round(v*1e6)for v in r['xy']]));t.SetWidth(450000);t.SetDrill(200000);t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);viaids.append(add(t,r['net'],f'via/{vi}','TAIL_MCU::P1'if r['net']=='TAIL_MCU'else None))
out=D/'f722-heli.kicad_pcb';p.SaveBoard(str(out),b);b=p.LoadBoard(str(out));sm=p.GetSettingsManager();assert sm.LoadProject(str(D/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(D/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(out),b)
after=export(out);old={o['uuid']:o for o in native['objects']};now={o['uuid']:o for o in after['objects']};physical=lambda o:{k:v for k,v in o.items()if k!='net_code'};changed={u for u in old.keys()&now.keys()if physical(old[u])!=physical(now[u])};assert not changed;assert old.keys()-now.keys()==remove and now.keys()-old.keys()==set(newids);oldfp={f['uuid']:f for f in native['footprints']};newfp={f['uuid']:f for f in after['footprints']};fc={u for u in oldfp if oldfp[u]!=newfp[u]};assert not fc
for k in ['edge_cuts','outline_with_npth','copper_layers','copper_layer_ids','board_thickness_mm']:assert native[k]==after[k]
zone=lambda z:{k:v for k,v in z.items()if k not in ['filled','fill_representation']};assert list(map(zone,native['zones']))==list(map(zone,after['zones']))
(D/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n');poses=read(S/'poses-native.json');assert poses['R23']==[13.85,7.8,0.0,'F.Cu'];write(D/'poses-native.json',poses)
write(D/'f722-heli.logical-route-map.json',{'schema':'f722-logical-route-map/v1','board_sha256':sha(out),'source_sha256':EXPECTED,'logical_route_map':rmap});write(D/'fixed-explicit-native-ids.json',sorted((set(read(S/'fixed-explicit-native-ids.json'))-remove)|set(newids)))
write(D/'construction-provenance.json',{'schema':'f722-complete-TAIL-native-construction/v1','source_board_sha256':EXPECTED,'board_sha256':sha(out),'source_native_sha256':sha(S/'f722-heli.native.json'),'source_map_sha256':sha(S/'f722-heli.logical-route-map.json'),'constructor_sha256':sha(__file__),'proposal_sha256':sha(P),'routes':routeids,'vias':viaids,'added_records':[now[u]for u in newids],'removed_source_records':[old[u]for u in sorted(remove)],'changed_pad_records':[{'before':old[u],'after':now[u]}for u in changed],'changed_footprint_records':[{'before':oldfp[u],'after':newfp[u]}for u in fc],'all_other_source_native_objects_exact_except_net_code':len(old)-len(changed)-len(remove),'all_156_footprints_exact':True,'native_refill_performed':True,'native_gates_pending':True,'numerical_power_VCAP_applicable':False,'adoption_claimed':False})
write(D/'project-input-preservation.json',{'source_board_sha256':EXPECTED,'board_sha256':sha(out),'all_listed_non_board_project_inputs_byte_identical':True,'files':project['files']});shutil.copy2(S/'parts.json',D/'parts.json');shutil.copy2(P,D/'proposal.json');shutil.copy2(__file__,D/'construct.used.py');print(json.dumps({'board_sha256':sha(out),'tracks':len(newids)-len(viaids),'vias':len(viaids),'removed':len(remove),'moved':[]}))
