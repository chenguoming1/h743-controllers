"""Rebind an actual engine session to an additive intermediate native import.

This is an importer-only projection. It does not create a fresh routing model or
claim another engine run. The native importer must retain every current object.
"""
import argparse
import hashlib
import json
from pathlib import Path

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
ap = argparse.ArgumentParser(description=__doc__)
for name in ['source', 'origin-model', 'session', 'engine-report', 'out']:
    ap.add_argument('--' + name, type=Path, required=True)
a = ap.parse_args()
origin = json.loads(a.origin_model.read_text())
report = json.loads(a.engine_report.read_text())
source_board = a.source / 'f722-heli.kicad_pcb'
source_native = a.source / 'f722-heli.native.json'
native = json.loads(source_native.read_text())
prior = json.loads(Path(origin['physical_native']).read_text())
logical = json.loads((a.source / 'f722-heli.logical-route-map.json').read_text())
assert report['model_sha256'] == sha(a.origin_model)
assert report['board_sha256'] == origin['board_sha256'] == sha(origin['physical_board'])
assert native['board_sha256'] == logical['board_sha256'] == sha(source_board)
before = {o['uuid']: o for o in prior['objects']}
current = {o['uuid']: o for o in native['objects']}
assert all(current.get(uid) == o for uid, o in before.items())
assert all(prior[k] == native[k] for k in ['zones', 'edge_cuts', 'footprints', 'copper_layers'])
added = set(current) - set(before)
assert added and added <= set(logical['logical_route_map'])
assert all(current[uid]['kind'] == 'track' and current[uid]['width'] == .127
           and set(current[uid]['copper']) <= {'F.Cu', 'B.Cu'} for uid in added)
model = {key: origin[key] for key in ['aliases', 'ordinary_nets', 'routable_layers',
                                    'regenerable_reference_zones']}
model.update(physical_board=str(source_board.resolve()), physical_native=str(source_native.resolve()),
             board_sha256=sha(source_board), native_sha256=sha(source_native),
             mutable_source_ids=sorted(set(origin['mutable_source_ids']) | added),
             source_logical_nets=logical['logical_route_map'], engine_planning_model=False,
             replay_import_projection=True, origin_full_model_sha256=sha(a.origin_model))
a.out.mkdir(parents=True, exist_ok=False)
mp = a.out / 'import-model.json'
mp.write_text(json.dumps(model, indent=2) + '\n')
receipt = dict(schema='f722-additive-session-rebind/v1', origin_board_sha256=origin['board_sha256'],
               source_board_sha256=sha(source_board), origin_model_sha256=sha(a.origin_model),
               actual_engine_report_sha256=sha(a.engine_report), actual_session_sha256=sha(a.session),
               importer_projection_sha256=sha(mp), intermediate_native_sha256=sha(source_native),
               intermediate_import_sha256=sha(a.source / 'f722-heli.import.json'),
               intermediate_additions=sorted(added), all_origin_native_objects_exact=True,
               all_origin_fills_drills_and_poses_exact=True, engine_rerun_claimed=False,
               mandatory_result_gate='Every intermediate source object must remain exact; native SES union, refill, DRC, endpoints and process gates remain required.')
report['origin_engine_report_sha256'] = sha(a.engine_report)
report['origin_model_sha256'] = report['model_sha256']
report['origin_board_sha256'] = report['board_sha256']
report['model_sha256'] = sha(mp)
report['board_sha256'] = sha(source_board)
report['replay_projection_only'] = True
(a.out / 'engine-report.json').write_text(json.dumps(report, indent=2) + '\n')
(a.out / 'rebind.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
