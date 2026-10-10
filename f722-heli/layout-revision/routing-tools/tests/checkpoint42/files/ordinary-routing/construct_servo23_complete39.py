"""Complete the explicit SERVO2/3 stage with the sealed native-screened P1 path.

Run with private KiCad Python. Engine searches failed; this is a declared native
construction, never direct-engine provenance or acceptance.
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
SOURCE = ROOT / 'servo23-native-stage38-exit'
ORIGIN = ROOT / 'servo23-native-stage38'
OUT = ROOT / 'candidate39'
PROPOSAL = ROOT / 'servo3-entry-access-review/route-proposal.json'
SOURCE_SHA = '6616644413f202295d134d67483e525e3f04277947f9620b4baa787cf370ace9'
ORIGIN_SHA = 'e93f1a1814f8b2bfd6341be9522a053a71db2706d7d81ee2984f6bd82a6c8aa5'
PROPOSAL_SHA = 'a0bd9c5a677eef9c06d7f96e7c189f47a6bcb19e6c13f855916bbeadaf373ba1'
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
read = lambda path: json.loads(Path(path).read_text())
write = lambda path, value: Path(path).write_text(json.dumps(value, indent=2) + '\n')
nm = lambda value: round(value * 1e6)
native = read(SOURCE / 'f722-heli.native.json')
route_map = read(SOURCE / 'f722-heli.logical-route-map.json')
assert sha(SOURCE / 'f722-heli.kicad_pcb') == native['board_sha256'] == route_map['board_sha256'] == SOURCE_SHA
assert sha(PROPOSAL) == PROPOSAL_SHA
proposal = read(PROPOSAL)
assert proposal['source_board_sha256'] == ORIGIN_SHA
assert proposal['physical_net'] == 'SERVO3_MCU' and proposal['logical_net'] == 'SERVO3_MCU::P1'
assert all(x > 0 for x in proposal['minimum_extra_clearance_mm'].values())
assert proposal['routes'][0]['points_mm'] == [[14.85, 9.06], [16.5, 9.06], [16.96, 8.6], [21.15, 8.6], [22.0, 9.45]]
assert proposal['routes'][2]['points_mm'] == [[22.0, 9.45], [22.0, 9.14], [21.209999, 9.14], [21.209999, 8.125]]
origin = read(ORIGIN / 'f722-heli.native.json')
before = {o['uuid']: o for o in native['objects']}
original = {o['uuid']: o for o in origin['objects']}
assert sha(ORIGIN / 'f722-heli.kicad_pcb') == origin['board_sha256'] == ORIGIN_SHA
assert all(before.get(u) == o for u, o in original.items())
seed_ids = set(before) - set(original)
assert len(seed_ids) == 1
seed = before[next(iter(seed_ids))]
assert seed['kind'] == 'track' and seed['net'] == 'SERVO3_MCU'
assert seed['start'] == [14.85, 9.06] and seed['end'] == [16.5, 9.06]
assert route_map['logical_route_map'][seed['uuid']] == 'SERVO3_MCU::P1'
assert not OUT.exists()
shutil.copytree(SOURCE, OUT, ignore=shutil.ignore_patterns('*.json', '*.log', '*.png', '*.svg', '*.py', '*.ses', '*.md', '*.kicad_prl', '__pycache__'))
shutil.copy2(SOURCE / 'parts.json', OUT / 'parts.json')
b = p.LoadBoard(str(SOURCE / 'f722-heli.kicad_pcb'))
mapping = dict(route_map['logical_route_map'])
added = []
held = []
for row_index, row in enumerate(proposal['routes']):
    items = []
    if row['kind'] == 'track':
        assert row['width_mm'] == .127 and row['layer'] in {'In2.Cu', 'B.Cu'}
        points = row['points_mm'][1:] if row_index == 0 else row['points_mm']
        for aa, bb in zip(points, points[1:]):
            item = p.PCB_TRACK(b)
            item.SetStart(p.VECTOR2I(*map(nm, aa)))
            item.SetEnd(p.VECTOR2I(*map(nm, bb)))
            item.SetWidth(127000)
            item.SetLayer(b.GetLayerID(row['layer']))
            items.append(item)
    else:
        assert row['kind'] == 'via' and row['xy_mm'] == [22.0, 9.45]
        assert row['diameter_mm'] == .45 and row['drill_mm'] == .20
        assert row['tented'] == {'F.Mask': True, 'B.Mask': True}
        item = p.PCB_VIA(b)
        item.SetPosition(p.VECTOR2I(22000000, 9450000))
        item.SetWidth(450000)
        item.SetDrill(200000)
        item.SetViaType(p.VIATYPE_THROUGH)
        item.SetLayerPair(p.F_Cu, p.B_Cu)
        item.SetFrontTentingMode(p.TENTING_MODE_TENTED)
        item.SetBackTentingMode(p.TENTING_MODE_TENTED)
        items.append(item)
    for item in items:
        item.SetNet(b.FindNet('SERVO3_MCU'))
        b.Add(item)
        held.append(item)
        uid = item.m_Uuid.AsString()
        mapping[uid] = 'SERVO3_MCU::P1'
        added.append(uid)
assert len(added) == 7
output = OUT / 'f722-heli.kicad_pcb'
p.SaveBoard(str(output), b)
b = p.LoadBoard(str(output))
sm = p.GetSettingsManager()
assert sm.LoadProject(str(OUT / 'f722-heli.kicad_pro'))
b.SetProject(sm.GetProject(str(OUT / 'f722-heli.kicad_pro')))
b.SynchronizeNetsAndNetClasses(False)
b.BuildConnectivity()
assert p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(output), b)
after = export(output)
current = {o['uuid']: o for o in after['objects']}
assert set(current) - set(before) == set(added)
assert all(current.get(u) == o for u, o in before.items())
assert all(native[k] == after[k] for k in ['footprints', 'edge_cuts', 'copper_layers'])
zone_contract = lambda z: {k: v for k, v in z.items() if k not in {'filled', 'fill_representation'}}
assert list(map(zone_contract, native['zones'])) == list(map(zone_contract, after['zones']))
(OUT / 'f722-heli.native.json').write_text(json.dumps(after, separators=(',', ':')) + '\n')
write(OUT / 'f722-heli.logical-route-map.json', {'schema': 'f722-logical-route-map/v1', 'board_sha256': sha(output), 'source_sha256': SOURCE_SHA, 'logical_route_map': mapping})
write(OUT / 'fixed-explicit-native-ids.json', sorted(set(read(SOURCE / 'fixed-explicit-native-ids.json')) | set(added)))
receipt = {
    'schema': 'f722-complete-servo23-native-construction/v1',
    'status': 'complete_geometry_constructed_native_gates_pending',
    'source_board_sha256': SOURCE_SHA, 'original_joint_stage_sha256': ORIGIN_SHA,
    'accepted_source_sha256': '95bb984bf046fef2d96c6e59d9e00696f504d35f89e3340fdf076cd7c9249c9f',
    'board_sha256': sha(output), 'proposal_sha256': PROPOSAL_SHA,
    'constructor_sha256': sha(__file__), 'source_native_sha256': sha(SOURCE / 'f722-heli.native.json'),
    'source_route_map_sha256': sha(SOURCE / 'f722-heli.logical-route-map.json'),
    'new_native_records': [current[u] for u in added], 'new_logical_owner': 'SERVO3_MCU::P1',
    'seed_record_retained_exact': seed, 'source_objects_preserved_exact': len(before),
    'source_objects_removed': 0, 'poses_pads_outline_layers_exact': True,
    'reference_plane_refill_performed': True, 'direct_engine_output': False,
    'engine_routing_succeeded': False, 'engine_partial_geometry_adopted': False,
    'construction_kind': 'Sealed native geometry proposal after two failed bounded searches',
    'numerical_power_VCAP_applicable': False, 'adoption_requested': False,
}
write(OUT / 'construction-provenance.json', receipt)
shutil.copy2(PROPOSAL, OUT / 'p1-route-proposal.json')
shutil.copy2(__file__, OUT / 'construct_servo23_complete39.used.py')
print(json.dumps({k: receipt[k] for k in ['board_sha256', 'status', 'source_objects_preserved_exact']}))
