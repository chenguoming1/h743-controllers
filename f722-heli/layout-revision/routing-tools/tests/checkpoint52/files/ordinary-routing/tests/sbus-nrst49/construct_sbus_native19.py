"""Build a source-bound complete EXT/NRST delta; owner alone adopts."""
import pathlib,sys,json,hashlib,uuid,shutil,argparse
import pcbnew as p
parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--proposal',required=True);parser.add_argument('--screen',required=True);parser.add_argument('--out',required=True);args=parser.parse_args()
S=pathlib.Path(args.source).resolve();P=pathlib.Path(args.proposal).resolve();Q=pathlib.Path(args.screen).resolve();D=pathlib.Path(args.out).resolve();read=lambda f:json.loads(pathlib.Path(f).read_text());sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest();write=lambda f,x:pathlib.Path(f).write_text(json.dumps(x,indent=2)+'\n')
proposal=read(P);screen=read(Q);expected=sha(S/'f722-heli.kicad_pcb');old=read(S/'f722-heli.native.json');assert expected==old['board_sha256']==proposal['source_board_sha256']==screen['source_board_sha256'];assert screen['passed'] and screen['proposal_sha256']==sha(P);assert proposal['all_surface_branches_found']and proposal['all_trunks_found'];D.mkdir(exist_ok=False)
project=read(S/'project-input-preservation.json')
for row in project['files']:
 assert sha(S/row['path'])==row['sha256'];dest=D/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/row['path'],dest)
b=p.LoadBoard(str(S/'f722-heli.kicad_pcb'));b.thisown=False;original={t.m_Uuid.AsString():t for t in b.GetTracks()};removed=set(proposal['removed_source_ids']);assert removed<=original.keys()
for k in removed:original[k].thisown=False;b.Remove(original[k])
f=next(f for f in b.GetFootprints()if f.GetReference()=='R45');assert f.GetLayerName()=='F.Cu'and f.GetOrientationDegrees()==0;f.SetPosition(p.VECTOR2I(11650000,21800000))
held=[];ids=[];routeids=[];viaids=[];logical={}
for ri,r in enumerate(proposal['routes']):
 row=[]
 for i,(a,z)in enumerate(zip(r['points'],r['points'][1:])):
  assert a!=z;t=p.PCB_TRACK(b);u=str(uuid.uuid5(uuid.NAMESPACE_URL,expected+'/sbus-r45/'+sha(P)+'/track/'+str(ri)+'/'+str(i)));t.SetUuid(p.KIID(u));t.SetNet(b.FindNet(r['net']));t.SetLayer(b.GetLayerID(r['layer']));t.SetWidth(round(r['width']*1e6));t.SetStart(p.VECTOR2I(*[round(x*1e6)for x in a]));t.SetEnd(p.VECTOR2I(*[round(x*1e6)for x in z]));b.Add(t);t.thisown=False;held.append(t);ids.append(u);row.append(u);logical[u]=r.get('logical_net',r['net'])
 routeids.append(row)
for i,v in enumerate(proposal['vias']):
 t=p.PCB_VIA(b);u=str(uuid.uuid5(uuid.NAMESPACE_URL,expected+'/sbus-r45/'+sha(P)+'/via/'+str(i)));t.SetUuid(p.KIID(u));t.SetNet(b.FindNet(v['net']));t.SetPosition(p.VECTOR2I(*[round(x*1e6)for x in v['xy']]));t.SetWidth(450000);t.SetDrill(200000);t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t);t.thisown=False;held.append(t);ids.append(u);viaids.append(u);logical[u]=v.get('logical_net',v['net'])
p.SaveBoard(str(D/'f722-heli.kicad_pcb'),b)
write(D/'construction-transaction.json',dict(source_dir=str(S),source_board_sha256=expected,board_sha256=sha(D/'f722-heli.kicad_pcb'),source_native_sha256=sha(S/'f722-heli.native.json'),source_object_count=len(old['objects']),retained_object_count=len(old['objects'])-len(removed),removed_source_ids=sorted(removed),added_ids=ids,route_ids=routeids,via_ids=viaids,logical_map_additions=logical,constructor_sha256=sha(__file__),proposal_sha256=sha(P),screen_sha256=sha(Q),native_refill_performed=False,native_export_and_validation_pending=True))
for name in ['parts.json','poses-native.json']:shutil.copy2(S/name,D/name)
shutil.copy2(P,D/'proposal.json');shutil.copy2(Q,D/'preconstruction-screen.json');write(D/'project-input-preservation.json',dict(source_board_sha256=expected,board_sha256=sha(D/'f722-heli.kicad_pcb'),all_listed_non_board_project_inputs_byte_identical=True,files=project['files']))
print(json.dumps(dict(board_sha256=sha(D/'f722-heli.kicad_pcb'),tracks=len(ids)-len(viaids),vias=len(viaids),native_export_pending=True)))

poses=read(D/'poses-native.json');poses['R45']=[11.65,21.8,0,'F.Cu'];write(D/'poses-native.json',poses)
