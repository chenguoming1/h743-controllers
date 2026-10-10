import json,pathlib,hashlib,shutil,pcbnew as p
H=pathlib.Path(__file__).resolve().parent;S=H/'candidate04';D=H/'candidate05';P=H.parent/'port-b48/rx-reference-repair-on-A04.json';read=lambda f:json.loads(pathlib.Path(f).read_text());sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest();write=lambda f,x:pathlib.Path(f).write_text(json.dumps(x,indent=2)+'\n')
q=read(P);assert q['passed']and sha(S/'f722-heli.kicad_pcb')==q['source_board_sha256']and sha(S/'f722-heli.native.json')==q['source_native_sha256'];D.mkdir(exist_ok=False);project=read(S/'project-input-preservation.json')
for r in project['files']:
 assert sha(S/r['path'])==r['sha256'];dest=D/r['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/r['path'],dest)
b=p.LoadBoard(str(S/'f722-heli.kicad_pcb'));b.thisown=False;tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};old={o['uuid']:o for o in read(S/'f722-heli.native.json')['objects']}
for row in q['changes']:
 t=tracks[row['uuid']];assert t.GetNetname()==row['net']and t.GetWidth()==round(row['width']*1e6);t.SetStart(p.VECTOR2I(*[round(x*1e6)for x in row['start']]));t.SetEnd(p.VECTOR2I(*[round(x*1e6)for x in row['end']]))
p.SaveBoard(str(D/'f722-heli.kicad_pcb'),b)
for name in ['poses-native.json','parts.json']:shutil.copy2(S/name,D/name)
write(D/'patch-primitive-receipt.json',dict(source_board_sha256=q['source_board_sha256'],unfilled_board_sha256=sha(D/'f722-heli.kicad_pcb'),source_native_sha256=q['source_native_sha256'],patch_receipt_sha256=sha(P),constructor_sha256=sha(__file__),changed_ids=[r['uuid']for r in q['changes']],old_native_tracks=q['old_native_tracks'],changes=q['changes'],no_via_or_pose_changes=True));shutil.copy2(P,D/'shared-B-return-patch.json');write(D/'project-input-preservation.json',dict(project,board_sha256=sha(D/'f722-heli.kicad_pcb')))
print(json.dumps(dict(unfilled_board_sha256=sha(D/'f722-heli.kicad_pcb'),changed_tracks=2)))
