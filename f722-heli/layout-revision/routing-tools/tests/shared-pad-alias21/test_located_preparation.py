"""Native-source regression for bounded located-path preparation; no board writes."""
import hashlib,json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
board=R/'candidate21/f722-heli.kicad_pcb';source_sha=sha(board)
args=[sys.executable,str(R/'prepare_located_branch.py'),'--board',str(board),'--native',str(board.with_suffix('.native.json')),'--logical-route-map',str(board.with_suffix('.logical-route-map.json')),'--model',str(R/'model-candidate21-ready/model.json'),'--located-receipt',str(R/'tests/local-closures20/port-b-located-path.json'),'--engine-log',str(R/'model-candidate21-ready/short-port-batch.log'),'--logical-net','PORT_B_RX_EXT::P0']
def invoke(name,replace=None,expected=0,contains=None):
 cmd=list(args)
 for flag,value in (replace or {}).items():cmd[cmd.index(flag)+1]=str(value)
 out=H/(name+'.json');cmd+=['--out',str(out)];p=subprocess.run(cmd,cwd=R,capture_output=True,text=True)
 (H/(name+'.log')).write_text(p.stdout+p.stderr)
 assert p.returncode==expected,(name,p.returncode,p.stdout,p.stderr)
 if contains:assert contains in p.stdout+p.stderr
 if expected:assert not out.exists()
 return dict(name=name,exit_code=p.returncode,accepted=not bool(p.returncode),output_sha256=sha(out)if out.exists()else None)
checks=[invoke('control-positive')]
actual=json.loads((H/'control-positive.json').read_text());accepted_geometry=json.loads((R/'candidate22/located-native-proposal.json').read_text())
assert actual['proposals'][0]['points_mm']==accepted_geometry['proposals'][0]['points_mm']
checks.append(invoke('control-wrong-source',{'--board':R/'candidate20/f722-heli.kicad_pcb'},1,'AssertionError'))
checks.append(invoke('control-wrong-alias',{'--logical-net':'PORT_B_RX_EXT::P1'},1,'Captured records differ'))
# This is deliberately synthetic diagnostic input, never an actual route claim.
raw=json.loads((R/'tests/local-closures20/port-b-located-path.json').read_text())
raw['records'][0]['requested_corners_mm']=[[29.625,5.5],[24.0,7.9],[24.0,7.4825]]
(H/'negative-outside-pad-input.json').write_text(json.dumps(raw,indent=2)+'\n')
(H/'negative-outside-pad-input.log').write_text('\n'.join('INSERT_DIAGNOSTIC '+json.dumps(x)for x in raw['records'])+'\n')
checks.append(invoke('control-outside-pad',{'--located-receipt':H/'negative-outside-pad-input.json','--engine-log':H/'negative-outside-pad-input.log'},1,'other_branch_outside_shared_pad'))
assert sha(board)==source_sha
result=dict(passed=True,source_board_sha256=source_sha,board_unchanged=True,preparer_sha256=sha(R/'prepare_located_branch.py'),test_source_sha256=sha(Path(__file__)),controls=checks,native_construction_result='Generic preparation reproduces the exact three segments already native-verified in frozen candidate22. Candidate22 adoption/loaded power remain separately pending.',synthetic_negative='Outside-pad diagnostic input/log are deliberately generated fixtures; no actual router result is claimed.')
(H/'preparation-controls.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
