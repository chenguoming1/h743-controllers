"""Trim only declared, unaccepted engine tails; preserve adopted source copper.

Every replacement segment must be a collinear subset at the same width. Vias,
drills and saved fills stay exact. Native connectivity, DRC and entry gates must
run again on the isolated output; this is not another engine routing success.
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
import pcbnew as p

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'native-tools'))
from export_native_copper import export

ap = argparse.ArgumentParser(description=__doc__)
for name in ['accepted-source', 'raw-source', 'recipe', 'out']:
    ap.add_argument('--' + name, type=Path, required=True)
a = ap.parse_args()
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
read = lambda path: json.loads(Path(path).read_text())
accepted = read(a.accepted_source / 'f722-heli.native.json')
raw = read(a.raw_source / 'f722-heli.native.json')
recipe = read(a.recipe)
logical = read(a.raw_source / 'f722-heli.logical-route-map.json')
assert accepted['board_sha256'] == sha(a.accepted_source / 'f722-heli.kicad_pcb')
assert raw['board_sha256'] == logical['board_sha256'] == recipe['raw_board_sha256'] == sha(a.raw_source / 'f722-heli.kicad_pcb')
prior = {o['uuid']: o for o in accepted['objects']}
before = {o['uuid']: o for o in raw['objects']}
assert all(before.get(uid) == o for uid, o in prior.items())
changed = {r['uuid'] for r in recipe['trims']}
removed = set(recipe['remove'])
assert not changed & removed and not (changed | removed) & set(prior)
assert all(before[uid]['kind'] == 'track' for uid in changed | removed)
board = p.LoadBoard(str(a.raw_source / 'f722-heli.kicad_pcb'))
tracks = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
rows = []
for row in recipe['trims']:
    old = before[row['uuid']]
    endpoint, new = row['endpoint'], row['new_xy_mm']
    assert endpoint in ['start', 'end'] and old['width'] == .127
    start, end = old['start'], old['end']
    dx, dy = end[0] - start[0], end[1] - start[1]
    nx, ny = new[0] - start[0], new[1] - start[1]
    assert abs(dx * ny - dy * nx) < 1e-9
    parameter = (dx * nx + dy * ny) / (dx * dx + dy * dy)
    assert 0 < parameter < 1
    via = before[row['anchor_via_uuid']]
    assert via['kind'] == 'via' and via['net'] == old['net'] and via['xy'] == new
    point = p.VECTOR2I(*[round(v * 1e6) for v in new])
    getattr(tracks[row['uuid']], 'SetStart' if endpoint == 'start' else 'SetEnd')(point)
    rows.append(dict(**row, old_xy_mm=old[endpoint], old_segment=[start, end],
                     collinear_subset_parameter=parameter, same_width_mm=.127,
                     no_added_mathematical_track_copper=True))
for uid in removed:
    board.Remove(tracks[uid])
assert not a.out.exists()
shutil.copytree(a.raw_source, a.out, ignore=shutil.ignore_patterns(
    '*.json', '*.log', '*.png', '*.svg', '*.py', '*.ses', '*.md', '*.kicad_prl', '__pycache__'))
shutil.copy2(a.raw_source / 'parts.json', a.out / 'parts.json')
output = a.out / 'f722-heli.kicad_pcb'
p.SaveBoard(str(output), board)
native = export(output)
after = {o['uuid']: o for o in native['objects']}
assert set(before) - set(after) == removed and not set(after) - set(before)
assert {uid for uid in set(before) & set(after) if before[uid] != after[uid]} == changed
assert all(after.get(uid) == o for uid, o in prior.items())
assert all(raw[key] == native[key] for key in ['footprints', 'zones', 'edge_cuts', 'copper_layers'])
assert [o for o in raw['objects'] if o.get('drill')] == [o for o in native['objects'] if o.get('drill')]
(a.out / 'f722-heli.native.json').write_text(json.dumps(native, separators=(',', ':')) + '\n')
logical.update(board_sha256=sha(output), source_sha256=sha(a.raw_source / 'f722-heli.kicad_pcb'))
logical['logical_route_map'] = {uid: net for uid, net in logical['logical_route_map'].items() if uid in after}
(a.out / 'f722-heli.logical-route-map.json').write_text(json.dumps(logical, indent=2) + '\n')
receipt = dict(schema='f722-unaccepted-route-tail-repair/v1',
               accepted_source_sha256=accepted['board_sha256'], raw_source_sha256=raw['board_sha256'],
               board_sha256=sha(output), recipe_sha256=sha(a.recipe), repair_source_sha256=sha(__file__),
               all_accepted_source_objects_exact=len(prior), changed_new_tracks=rows,
               removed_new_tracks=[before[uid] for uid in sorted(removed)],
               new_vias=0, all_raw_vias_drills_fills_poses_exact=True, refill_performed=False,
               route_solver_used=False, native_validation_required=True)
(a.out / 'tail-repair.json').write_text(json.dumps(receipt, indent=2) + '\n')
shutil.copy2(__file__, a.out / 'repair_new_route_tails.used.py')
print(json.dumps({k: v for k, v in receipt.items() if k != 'removed_new_tracks'}))
