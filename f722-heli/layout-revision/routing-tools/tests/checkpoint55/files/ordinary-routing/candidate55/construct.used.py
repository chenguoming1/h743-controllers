"""Construct one immutable smaller GREEN checkpoint on exact accepted54."""
import pathlib,sys,json,hashlib,uuid,shutil
import pcbnew as p
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];S=R/'candidate54';D=H/'small-candidate01'
EXPECTED='24121b0e46d9a71207cd21e7cf599412c00796d48eb9af5f63ffcf92e5f2ca42'
sys.path.insert(0,str(R/'native-tools'));from export_native_copper import export
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest();read=lambda f:json.loads(pathlib.Path(f).read_text());write=lambda f,x:pathlib.Path(f).write_text(json.dumps(x,indent=2)+'\n')
P=H/'small-GREEN-complete-proposal54.json';plan=read(P);assert plan['complete_all_donor_geometry'];assert plan['source_board_sha256']==sha(S/'f722-heli.kicad_pcb')==EXPECTED
native=read(S/'f722-heli.native.json');mapping=read(S/'f722-heli.logical-route-map.json');assert native['board_sha256']==mapping['board_sha256']==EXPECTED
assert sha(S/'f722-heli.native.json')==plan['source_native_sha256']
D.mkdir(exist_ok=False);project=read(S/'project-input-preservation.json')
for row in project['files']:
 assert sha(S/row['path'])==row['sha256'];out=D/row['path'];out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/row['path'],out)
b=p.LoadBoard(str(S/'f722-heli.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};remove={o['uuid']for o in plan['removed_source_records']};oldtracks={t.m_Uuid.AsString():t for t in b.GetTracks()};assert remove<=oldtracks.keys()
for u in remove:b.Remove(oldtracks[u])
for t in plan['footprint_transforms']:
 f=fps[t['ref']];a=t['after'];assert b.GetLayerName(f.GetLayer())==a['side'];f.SetPosition(p.VECTOR2I(*[round(v*1e6)for v in a['xy']]));f.SetOrientationDegrees(a['angle'])
held=[];newids=[];routeids=[];viaids=[];rmap={u:v for u,v in mapping['logical_route_map'].items()if u not in remove}
def add(t,net,label):
 u=str(uuid.uuid5(uuid.NAMESPACE_URL,EXPECTED+'/'+sha(P)+'/'+label));t.SetUuid(p.KIID(u));t.SetNet(b.FindNet(net));b.Add(t);held.append(t);newids.append(u);rmap[u]=net;return u
for ri,r in enumerate(plan['routes']):
 ids=[]
 for i,(aa,bb)in enumerate(zip(r['points'],r['points'][1:])):
  if aa==bb:continue
  t=p.PCB_TRACK(b);t.SetLayer(b.GetLayerID(r['layer']));t.SetWidth(round(r['width']*1e6));t.SetStart(p.VECTOR2I(*[round(v*1e6)for v in aa]));t.SetEnd(p.VECTOR2I(*[round(v*1e6)for v in bb]));ids.append(add(t,r['net'],f'route/{ri}/{i}'))
 routeids.append(ids)
for vi,r in enumerate(plan['vias']):
 t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(*[round(v*1e6)for v in r['xy']]));t.SetWidth(round(r['diameter_mm']*1e6));t.SetDrill(round(r['drill_mm']*1e6));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);viaids.append(add(t,r['net'],f'via/{vi}'))
out=D/'f722-heli.kicad_pcb';p.SaveBoard(str(out),b);b=p.LoadBoard(str(out));sm=p.GetSettingsManager();assert sm.LoadProject(str(D/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(D/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(out),b)
after=export(out);old={o['uuid']:o for o in native['objects']};now={o['uuid']:o for o in after['objects']};physical=lambda o:{k:v for k,v in o.items()if k!='net_code'};changed={u for u in old.keys()&now.keys()if physical(old[u])!=physical(now[u])};assert {old[u].get('ref')for u in changed}=={'R44'} and len(changed)==2
assert old.keys()-now.keys()==remove and now.keys()-old.keys()==set(newids)
oldfp={f['uuid']:f for f in native['footprints']};newfp={f['uuid']:f for f in after['footprints']};fc={u for u in oldfp if oldfp[u]!=newfp[u]};assert {oldfp[u]['ref']for u in fc}=={'R44'}
for k in ['edge_cuts','outline_with_npth','copper_layers','copper_layer_ids','board_thickness_mm']:assert native[k]==after[k]
zone=lambda z:{k:v for k,v in z.items()if k not in ['filled','fill_representation']};assert list(map(zone,native['zones']))==list(map(zone,after['zones']))
(D/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n')
poses=read(S/'poses-native.json')
for u in fc:
 f=newfp[u];poses[f['ref']]=f['xy']+[f['angle'],f['side']]
write(D/'poses-native.json',poses)
write(D/'f722-heli.logical-route-map.json',{'schema':'f722-logical-route-map/v1','board_sha256':sha(out),'source_sha256':EXPECTED,'logical_route_map':rmap});write(D/'fixed-explicit-native-ids.json',sorted((set(read(S/'fixed-explicit-native-ids.json'))-remove)|set(newids)))
write(D/'construction-provenance.json',{'schema':'f722-small-GREEN-native-construction54/v1','source_board_sha256':EXPECTED,'board_sha256':sha(out),'source_native_sha256':sha(S/'f722-heli.native.json'),'source_map_sha256':sha(S/'f722-heli.logical-route-map.json'),'constructor_sha256':sha(__file__),'proposal_sha256':sha(P),'routes':routeids,'vias':viaids,'added_records':[now[u]for u in newids],'removed_source_records':[old[u]for u in sorted(remove)],'changed_pad_records':[{'before':old[u],'after':now[u]}for u in sorted(changed)],'changed_footprint_records':[{'before':oldfp[u],'after':newfp[u]}for u in sorted(fc)],'all_other_source_native_objects_exact_except_net_code':len(old)-len(changed)-len(remove),'native_refill_performed':True,'native_gates_pending':True,'electrical_acceptance_claimed':False,'adoption_claimed':False})
write(D/'project-input-preservation.json',{'source_board_sha256':EXPECTED,'board_sha256':sha(out),'all_listed_non_board_project_inputs_byte_identical':True,'files':project['files']});shutil.copy2(S/'parts.json',D/'parts.json');shutil.copy2(P,D/'proposal.json');shutil.copy2(__file__,D/'construct.used.py');print(json.dumps({'board_sha256':sha(out),'tracks':len(newids)-len(viaids),'vias':len(viaids),'removed':len(remove),'moved':['R44']}),flush=True)
