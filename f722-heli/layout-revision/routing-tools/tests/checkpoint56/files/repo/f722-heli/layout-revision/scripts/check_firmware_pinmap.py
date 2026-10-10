"""Check pinned stock Nexus MCU assignments against this native PCB."""
import argparse,hashlib,json
from pathlib import Path
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--contract',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
b=p.LoadBoard(str(a.board));u=next(f for f in b.GetFootprints() if f.GetReference()=='U1');pins={x.GetNumber():x.GetNetname() for x in u.Pads()};contract=json.loads(a.contract.read_text());rows=[]
for c in contract['checks']:
 pin=c['package_pin'];expected=c['expected_net'];actual=pins.get(pin);rows.append(dict(resource=c['resource'],index=c.get('index'),gpio=c.get('gpio'),pin=pin,expected=expected,actual=actual,passed=actual==expected))
r=dict(board_sha256=hashlib.sha256(a.board.read_bytes()).hexdigest(),contract_sha256=hashlib.sha256(a.contract.read_bytes()).hexdigest(),pinned_target=contract['pinned_target'],scope='Native MCU pad assignments only; no firmware runtime, routed timing or physical qualification',passed=all(x['passed'] for x in rows),checks=rows);a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'checks':len(rows)}));raise SystemExit(0 if r['passed'] else 1)
