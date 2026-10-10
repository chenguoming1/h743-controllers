import pcbnew as p,json,pathlib,hashlib,uuid,shutil,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[2];S=R/'ordinary-routing/candidate50';D=H/'candidate03';P=H/'native-proposal50.json';sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest();read=lambda f:json.loads(pathlib.Path(f).read_text());write=lambda f,x:pathlib.Path(f).write_text(json.dumps(x,indent=2)+'\n')
q=read(P);expected=q['source_board_sha256'];assert sha(S/'f722-heli.kicad_pcb')==expected and sha(S/'f722-heli.native.json')==q['source_native_sha256']
for f,h in q['input_hashes'].items():assert sha(R/f)==h,f
screen=read(H/'declared-transaction50-screen.json');assert screen['passed'] and screen['proposal_sha256']==sha(P) and screen['source_board_sha256']==expected
D.mkdir(exist_ok=False);project=read(S/'project-input-preservation.json')
for row in project['files']:
 assert sha(S/row['path'])==row['sha256'];out=D/row['path'];out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/row['path'],out)
b=p.LoadBoard(str(S/'f722-heli.kicad_pcb'));b.thisown=False;fps={f.GetReference():f for f in b.GetFootprints()}
for ref,t in q['footprint_transforms'].items():
 f=fps[ref];before,after=t['before'],t['after'];assert f.GetPosition()==p.VECTOR2I(*[round(v*1e6)for v in before[:2]])
 if before[3]!=after[3]:f.Flip(f.GetPosition(),t['flip_left_right'])
 f.SetOrientationDegrees(after[2]);f.SetPosition(p.VECTOR2I(*[round(v*1e6)for v in after[:2]]))
removed=[];held=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString()in q['remove_source_track_ids']:removed.append(t.m_Uuid.AsString());t.thisown=False;b.Remove(t);held.append(t)
assert set(removed)==set(q['remove_source_track_ids'])
added=[];routeids={};viaids={}
def track(uid,net,layer,width,s,e):
 t=p.PCB_TRACK(b);t.SetUuid(p.KIID(uid));t.SetNet(b.FindNet(net));t.SetLayer(b.GetLayerID(layer));t.SetWidth(round(width*1e6));t.SetStart(p.VECTOR2I(*[round(v*1e6)for v in s]));t.SetEnd(p.VECTOR2I(*[round(v*1e6)for v in e]));b.Add(t);t.thisown=False;held.append(t);added.append(uid);return uid
for o in q['native_replacement_tracks']:track(o['uuid'],o['net'],next(iter(o['copper'])),o['width'],o['start'],o['end'])
for rr in q['routes']:
 ids=[]
 for i,(s,e)in enumerate(zip(rr['points'],rr['points'][1:])):
  uid=str(uuid.uuid5(uuid.NAMESPACE_URL,expected+'/'+sha(P)+'/'+rr['name']+'/'+str(i)));ids.append(track(uid,rr['net'],rr['layer'],rr['width'],s,e))
 routeids[rr['name']]=ids
for v in q['vias']:
 uid=str(uuid.uuid5(uuid.NAMESPACE_URL,expected+'/'+sha(P)+'/via/'+v['name']));t=p.PCB_VIA(b);t.SetUuid(p.KIID(uid));t.SetNet(b.FindNet(v['net']));t.SetPosition(p.VECTOR2I(*[round(x*1e6)for x in v['xy']]));t.SetWidth(450000);t.SetDrill(200000);t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t);t.thisown=False;held.append(t);added.append(uid);viaids[v['name']]=uid
p.SaveBoard(str(D/'f722-heli.kicad_pcb'),b);poses=read(S/'poses-native.json');poses.update({k:t['after']for k,t in q['footprint_transforms'].items()});write(D/'poses-native.json',poses);write(D/'construction-primitive-receipt.json',dict(source_board_sha256=expected,unfilled_board_sha256=sha(D/'f722-heli.kicad_pcb'),proposal_sha256=sha(P),constructor_sha256=sha(__file__),routes=routeids,vias=viaids,removed_or_replaced_ids=removed,added_or_replaced_ids=added));shutil.copy2(P,D/'proposal.json');shutil.copy2(S/'parts.json',D/'parts.json');print(json.dumps({'saved':str(D),'tracks_vias_added_or_replaced':len(added),'unfilled_sha256':sha(D/'f722-heli.kicad_pcb')}))
