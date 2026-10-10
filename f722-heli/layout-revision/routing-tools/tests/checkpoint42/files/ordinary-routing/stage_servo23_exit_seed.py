"""Add the reviewed short In2 P1 exit to an isolated partial SERVO stage.

This search seed is not an accepted route. It preserves every source object,
pose, and saved fill. A complete successor requires all native gates.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys

import pcbnew as p

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'native-tools'))
from export_native_copper import export

SOURCE = ROOT / 'servo23-native-stage38'
OUT = ROOT / 'servo23-native-stage38-exit'
PLAN = ROOT / 'servo23-joint-plan/plan.json'
SOURCE_SHA = 'e93f1a1814f8b2bfd6341be9522a053a71db2706d7d81ee2984f6bd82a6c8aa5'
PLAN_SHA = '1c359be7580340a182738f556cb9becb22106d66d88b06b011de61a263c81f88'
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
read = lambda path: json.loads(Path(path).read_text())
write = lambda path, value: Path(path).write_text(json.dumps(value, indent=2) + '\n')
board_path = SOURCE / 'f722-heli.kicad_pcb'
native = read(SOURCE / 'f722-heli.native.json')
route_map = read(SOURCE / 'f722-heli.logical-route-map.json')
assert sha(board_path) == native['board_sha256'] == route_map['board_sha256'] == SOURCE_SHA
assert sha(PLAN) == PLAN_SHA
row = next(r for r in read(PLAN)['replacement_and_new_routes'] if r['name'] == 'S3P1-inner-exit-only')
assert row['points_mm'] == [[14.85, 9.06], [16.5, 9.06]]
assert row['layer'] == 'In2.Cu' and row['width_mm'] == .127
assert row['physical_net'] == 'SERVO3_MCU' and row['logical_net'] == 'SERVO3_MCU::P1'
assert not OUT.exists()
OUT.mkdir()
for src in SOURCE.iterdir():
    if src.suffix in {'.kicad_pro', '.kicad_sch', '.kicad_dru'} or src.name == 'parts.json':
        shutil.copy2(src, OUT / src.name)
b = p.LoadBoard(str(board_path))
item = p.PCB_TRACK(b)
item.SetStart(p.VECTOR2I(14850000, 9060000))
item.SetEnd(p.VECTOR2I(16500000, 9060000))
item.SetWidth(127000)
item.SetLayer(b.GetLayerID('In2.Cu'))
item.SetNet(b.FindNet('SERVO3_MCU'))
b.Add(item)
uid = item.m_Uuid.AsString()
output = OUT / 'f722-heli.kicad_pcb'
p.SaveBoard(str(output), b)
after = export(output)
before_objects = {o['uuid']: o for o in native['objects']}
after_objects = {o['uuid']: o for o in after['objects']}
assert set(after_objects) - set(before_objects) == {uid}
assert all(after_objects.get(u) == o for u, o in before_objects.items())
assert all(native[k] == after[k] for k in ['footprints', 'edge_cuts', 'copper_layers', 'zones'])
(OUT / 'f722-heli.native.json').write_text(json.dumps(after, separators=(',', ':')) + '\n')
mapping = dict(route_map['logical_route_map'])
mapping[uid] = row['logical_net']
write(OUT / 'f722-heli.logical-route-map.json', {
    'schema': 'f722-logical-route-map/v1', 'board_sha256': sha(output),
    'source_sha256': SOURCE_SHA, 'logical_route_map': mapping})
write(OUT / 'fixed-explicit-native-ids.json', sorted(set(read(SOURCE / 'fixed-explicit-native-ids.json')) | {uid}))
receipt = {
    'schema': 'f722-isolated-reviewed-exit-search-seed/v1',
    'status': 'partial_search_seed_not_accepted',
    'source_board_sha256': SOURCE_SHA, 'board_sha256': sha(output),
    'source_native_sha256': sha(SOURCE / 'f722-heli.native.json'),
    'source_map_sha256': sha(SOURCE / 'f722-heli.logical-route-map.json'),
    'plan_sha256': PLAN_SHA, 'constructor_sha256': sha(__file__),
    'added_native_record': after_objects[uid], 'logical_owner': row['logical_net'],
    'source_objects_exact': len(before_objects), 'source_objects_removed': 0,
    'poses_outline_layers_saved_fills_exact': True, 'new_drills': 0,
    'remaining_connection': 'SERVO3_MCU::P1 In2 endpoint(16.5,9.06) to U1.25',
    'native_refill_performed': False, 'direct_engine_output': False,
    'numerical_power_VCAP_applicable': False, 'adoption_requested': False,
}
write(OUT / 'construction-provenance.json', receipt)
shutil.copy2(__file__, OUT / 'stage_servo23_exit_seed.used.py')
print(json.dumps({k: receipt[k] for k in ['board_sha256', 'status', 'source_objects_exact']}))
