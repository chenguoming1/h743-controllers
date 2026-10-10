"""Add only the complete, source-checked RPM group; owner alone adopts."""
import pathlib,json,hashlib,uuid,shutil
import pcbnew as p
H=pathlib.Path(__file__).resolve().parent;R=H.parents[2];S=R/'ordinary-routing/tests/servo48/candidate04';D=H/'candidate01';P=H/'complete-layer-proposal.json';Q=H/'preconstruction-screen.json';read=lambda f:json.loads(f.read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();write=lambda name,q:(D/name).write_text(json.dumps(q,indent=2)+'\n')
q=read(P);screen=read(Q);expected=sha(S/'f722-heli.kicad_pcb');assert expected==q['source_board_sha256']==screen['source_board_sha256'];assert q['complete']and screen['passed']and screen['proposal_sha256']==sha(P);assert q['removed_source_ids']==[];D.mkdir(exist_ok=False)
project=read(S/'project-input-preservation.json')
for row in project['files']:
 assert sha(S/row['path'])==row['sha256'];dest=D/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/row['path'],dest)
b=p.LoadBoard(str(S/'f722-heli.kicad_pcb'));b.thisown=False;held=[];routes={};vias={};added=[]
for r in q['routes']:
 assert r['net']=='RPM_MCU';ids=[]
 for i,(a,z)in enumerate(zip(r['points'],r['points'][1:])):
  assert a!=z;t=p.PCB_TRACK(b);uid=str(uuid.uuid5(uuid.NAMESPACE_URL,expected+'/complete-RPM/'+sha(P)+'/'+r['name']+'/'+str(i)));t.SetUuid(p.KIID(uid));t.SetNet(b.FindNet(r['net']));t.SetLayer(b.GetLayerID(r['layer']));t.SetWidth(127000);t.SetStart(p.VECTOR2I(*[round(v*1e6)for v in a]));t.SetEnd(p.VECTOR2I(*[round(v*1e6)for v in z]));b.Add(t);t.thisown=False;held.append(t);ids.append(uid);added.append(uid)
 routes[r['name']]=ids
for v in q['vias']:
 t=p.PCB_VIA(b);uid=str(uuid.uuid5(uuid.NAMESPACE_URL,expected+'/complete-RPM/'+sha(P)+'/via/'+v['name']));t.SetUuid(p.KIID(uid));t.SetNet(b.FindNet('RPM_MCU'));t.SetPosition(p.VECTOR2I(*[round(x*1e6)for x in v['xy']]));t.SetWidth(450000);t.SetDrill(200000);t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t);t.thisown=False;held.append(t);vias[v['name']]=uid;added.append(uid)
p.SaveBoard(str(D/'f722-heli.kicad_pcb'),b)
for f in ['parts.json','poses-native.json']:shutil.copy2(S/f,D/f)
shutil.copy2(P,D/'proposal.json');shutil.copy2(Q,D/'preconstruction-screen.json');write('construction-primitive-receipt.json',dict(source_board_sha256=expected,source_native_sha256=sha(S/'f722-heli.native.json'),unfilled_board_sha256=sha(D/'f722-heli.kicad_pcb'),routes=routes,vias=vias,added_ids=added,removed_source_ids=[],constructor_sha256=sha(pathlib.Path(__file__)),proposal_sha256=sha(P),screen_sha256=sha(Q)));write('project-input-preservation.json',dict(source_board_sha256=expected,board_sha256=sha(D/'f722-heli.kicad_pcb'),all_listed_non_board_project_inputs_byte_identical=True,files=project['files']));print(json.dumps(dict(saved=str(D),tracks=len(added)-len(vias),vias=len(vias))))
