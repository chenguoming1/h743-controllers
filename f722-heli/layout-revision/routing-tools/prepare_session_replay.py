#!/usr/bin/env python3
"""Bind a compact, hash-verified actual session packet to its exact source board.
This is an importer-only projection, never a fresh routing model or routing run.
"""
import argparse, hashlib, json
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument('--packet',type=Path,required=True)
ap.add_argument('--source-board',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();root=a.packet
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
identity=json.loads((root/'source-identity.json').read_text())
assert sha(a.source_board)==identity['board_sha256'],'Wrong frozen source board'
assert sha(root/'session.ses')==identity['session_sha256']
assert sha(root/'engine-report.json')==identity['engine_report_sha256']
assert sha(root/'import-contract.json')==identity['import_contract_sha256']
model=json.loads((root/'import-contract.json').read_text())
assert model['board_sha256']==identity['board_sha256']
model['physical_board']=str(a.source_board.resolve())
model['origin_full_model_sha256']=identity['model_sha256']
model['replay_import_projection']=True
report=json.loads((root/'engine-report.json').read_text())
assert report['model_sha256']==identity['model_sha256']
a.out.mkdir(parents=True,exist_ok=True);mp=a.out/'model.json'
mp.write_text(json.dumps(model,indent=2)+'\n')
report['origin_engine_report_sha256']=identity['engine_report_sha256']
report['origin_model_sha256']=report['model_sha256']
report['model_sha256']=sha(mp);report['replay_projection_only']=True
(a.out/'engine-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('Verified source/session/report identity; prepared importer-only projection.')
