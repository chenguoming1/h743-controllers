"""Build the sealed SERVO2/3 joint plan as an isolated, incomplete native stage.

The exact thirteen-object allowance includes one dedicated TVS ground return.
No output is accepted until SERVO3 P1 is completed and all native gates pass.
Run with the private KiCad Python runtime.
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

SOURCE = ROOT / 'candidate38'
ORIGIN = ROOT / 'candidate37'
OUT = ROOT / 'servo23-native-stage38'
PLAN = ROOT / 'servo23-joint-plan/plan.json'
SCREEN = ROOT / 'servo23-joint-plan/screen.json'
SOURCE_SHA = '95bb984bf046fef2d96c6e59d9e00696f504d35f89e3340fdf076cd7c9249c9f'
ORIGIN_SHA = '2a73d9b7dad3a14b0d00c80e81e0ba8a817b50179c15692aad39fde9920c2115'
PLAN_SHA = '1c359be7580340a182738f556cb9becb22106d66d88b06b011de61a263c81f88'
SCREEN_SHA = '8c72c56fd3f766620c42c8ff717f30a487896f2aab7c64ea62aff25f0cd02101'
ALLOW = {
    '039a63ec-d4b3-4367-a89e-61ffdd1dd9ef', '099a20ee-ccb7-487c-aa08-047b49e9d92b',
    '25c69f42-1efb-412a-bb87-f081745cab23', '4bdbc594-f503-4ac4-887a-602087e810a5',
    '651dd4bb-367c-4146-91ab-c7b2cafdcd9c', '734de095-936a-4d15-b30d-c37b0f7663bb',
    '7aa57d39-de74-4e59-ae7e-b321426a2b13', '7af3595c-7d69-471b-9895-586d3b074e8b',
    '8113afab-5370-4609-8346-a5e532efa35b', '9edf22b5-bde9-45f0-86ea-6aefaf3051b5',
    'c284754f-ab23-4ce9-ae72-2662dc7fce81', 'e3d66729-7dcf-4a0e-a0c5-5720860b1f0a',
    'f0ab58ba-6fac-49f0-aa28-85653a9eb251',
}
GROUND_ALLOW = {
    '4bdbc594-f503-4ac4-887a-602087e810a5',
    '651dd4bb-367c-4146-91ab-c7b2cafdcd9c',
    '7aa57d39-de74-4e59-ae7e-b321426a2b13',
}
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
read = lambda path: json.loads(Path(path).read_text())
write = lambda path, obj: Path(path).write_text(json.dumps(obj, indent=2) + '\n')
nm = lambda value: round(value * 1e6)

assert sha(PLAN) == PLAN_SHA and sha(SCREEN) == SCREEN_SHA
plan, screen = read(PLAN), read(SCREEN)
assert screen['all_nominal_screens_pass'] and not plan['construction_complete']
assert {o['uuid'] for o in plan['remove_exact_objects']} == ALLOW
assert not plan['changed_footprint_poses']
for rel, digest in plan['source_hashes'].items():
    assert sha(ROOT.parent / rel) == digest, rel
board_path = SOURCE / 'f722-heli.kicad_pcb'
native = read(SOURCE / 'f722-heli.native.json')
route_map = read(SOURCE / 'f722-heli.logical-route-map.json')
assert sha(board_path) == native['board_sha256'] == route_map['board_sha256'] == SOURCE_SHA
before = {o['uuid']: o for o in native['objects']}
assert all(before[u]['net'] == ('GND' if u in GROUND_ALLOW else 'SERVO2_MCU') for u in ALLOW)
assert all(before[u]['kind'] in {'track', 'via'} for u in ALLOW)
# Geometry was checked in the compatible analysis runtime; bind those exact inputs.
origin=read(ORIGIN/'f722-heli.native.json')
origin_objects={o['uuid']:o for o in origin['objects']}
assert origin['board_sha256']==sha(ORIGIN/'f722-heli.kicad_pcb')==ORIGIN_SHA
assert all(before.get(uid)==obj for uid,obj in origin_objects.items())
continuation_added=[o for uid,o in before.items() if uid not in origin_objects]
assert len(continuation_added)==21 and all(o['net']=='RPM_LV' and o['kind']in {'track','via'}for o in continuation_added)
continuation_proof=read(ROOT/'servo23-joint-plan/continuation38-recheck.json')
assert continuation_proof['passed'] and continuation_proof['origin_source_board_sha256']==ORIGIN_SHA and continuation_proof['current_source_board_sha256']==SOURCE_SHA
assert continuation_proof['plan_sha256']==PLAN_SHA
assert continuation_proof['source_native_sha256']==sha(SOURCE/'f722-heli.native.json')
assert continuation_proof['source_map_sha256']==sha(SOURCE/'f722-heli.logical-route-map.json')
assert continuation_proof['helper_sha256']==sha(ROOT/'recheck_servo23_continuation38.py')
assert continuation_proof['checks'] and all(q['gap_mm']>=q['required_mm']for q in continuation_proof['checks'])
assert not OUT.exists()
shutil.copytree(SOURCE, OUT, ignore=shutil.ignore_patterns(
    '*.json', '*.log', '*.png', '*.svg', '*.py', '*.ses', '*.md', '*.patch', '*.kicad_prl', '__pycache__'))
shutil.copy2(SOURCE / 'parts.json', OUT / 'parts.json')
b = p.LoadBoard(str(board_path))
tracks = {t.m_Uuid.AsString(): t for t in b.GetTracks()}
for uid in sorted(ALLOW):
    b.Remove(tracks[uid])
mapping = {u: v for u, v in route_map['logical_route_map'].items() if u not in ALLOW}
added, held = [], []
for row in plan['replacement_and_new_routes']:
    if row['name'] == 'S3P1-inner-exit-only':
        continue  # A dangling segment is not needed to expose the plated via to the router.
    net = row['physical_net']
    assert net in {'SERVO2_MCU', 'SERVO3_MCU', 'GND'}
    items = []
    if row['kind'] == 'track':
        width = .25 if net == 'GND' else .127
        assert row['width_mm'] == width
        assert row['layer'] in {'F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu'}
        assert net != 'GND' or row['name'] == 'U12.2-return'
        for aa, bb in zip(row['points_mm'], row['points_mm'][1:]):
            assert aa != bb
            item = p.PCB_TRACK(b)
            item.SetStart(p.VECTOR2I(*map(nm, aa)))
            item.SetEnd(p.VECTOR2I(*map(nm, bb)))
            item.SetWidth(nm(width))
            item.SetLayer(b.GetLayerID(row['layer']))
            items.append(item)
    else:
        assert row['kind'] == 'via' and row['diameter_mm'] == .45 and row['drill_mm'] == .20
        item = p.PCB_VIA(b)
        item.SetPosition(p.VECTOR2I(*map(nm, row['xy_mm'])))
        item.SetWidth(450000)
        item.SetDrill(200000)
        item.SetViaType(p.VIATYPE_THROUGH)
        item.SetLayerPair(p.F_Cu, p.B_Cu)
        item.SetFrontTentingMode(p.TENTING_MODE_TENTED)
        item.SetBackTentingMode(p.TENTING_MODE_TENTED)
        items.append(item)
    for item in items:
        item.SetNet(b.FindNet(net))
        b.Add(item)
        held.append(item)
        uid = item.m_Uuid.AsString()
        added.append({'uuid': uid, 'plan_name': row['name'], 'net': net, 'logical_net': row['logical_net']})
        if net != 'GND':
            mapping[uid] = row['logical_net']
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
assert set(before) - set(current) == ALLOW
assert set(current) - set(before) == {o['uuid'] for o in added}
assert all(current[u] == o for u, o in before.items() if u not in ALLOW)
assert all(current[o['uuid']]['net'] == o['net'] for o in added)
assert all(native[k] == after[k] for k in ['footprints', 'edge_cuts', 'copper_layers'])
def zone_contract(zone):
    return {k: v for k, v in zone.items() if k not in {'filled', 'fill_representation'}}
assert list(map(zone_contract, native['zones'])) == list(map(zone_contract, after['zones']))
assert all(z['net'] == 'GND' and set(z['layers']) <= {'In1.Cu', 'In4.Cu'}
           and all(z['filled'].get(l) for l in z['layers']) for z in after['zones'] if not z['rule'])
(OUT / 'f722-heli.native.json').write_text(json.dumps(after, separators=(',', ':')) + '\n')
write(OUT / 'f722-heli.logical-route-map.json', {
    'schema': 'f722-logical-route-map/v1', 'board_sha256': sha(output),
    'source_sha256': SOURCE_SHA, 'logical_route_map': mapping})
prior_fixed = set(read(ROOT / 'model-candidate37-ready/fixed-explicit-native-ids.json'))
fixed = (prior_fixed - ALLOW) | {o['uuid'] for o in added if o['net'] != 'GND'} | {o['uuid'] for o in continuation_added}
assert fixed <= set(current)
write(OUT / 'fixed-explicit-native-ids.json', sorted(fixed))
receipt = {
    'schema': 'f722-isolated-servo23-native-stage/v1',
    'status': 'unaccepted_partial_stage_SERVO3_P1_continuation_required',
    'source_board_sha256': SOURCE_SHA, 'board_sha256': sha(output),
    'plan_sha256': PLAN_SHA, 'screen_sha256': SCREEN_SHA, 'constructor_sha256': sha(__file__),
    'removed_source_objects': [before[u] for u in sorted(ALLOW)],
    'added_objects': added, 'all_other_source_objects_exact': len(before) - len(ALLOW),
    'all_poses_pads_outline_layers_exact': True, 'reference_plane_refill_performed': True,
    'omitted_plan_rows': ['S3P1-inner-exit-only'],
    'omission_reason': 'Avoid a deliberately dangling inner segment; the plated via is available on every routable layer.',
    'remaining_connection': 'SERVO3_MCU::P1 via(14.85,9.06) to U1.25',
    'ground_return_before_after': plan['ground_return'],
    'direct_engine_output': False, 'numerical_power_VCAP_applicable': False,
    'native_gates_required': True, 'adoption_requested': False,
}
receipt['origin_plan_source_board_sha256'] = ORIGIN_SHA
receipt['explicit_additive_continuation_recheck'] = 'continuation-recheck.json'
write(OUT / 'continuation-recheck.json', continuation_proof)
write(OUT / 'construction-provenance.json', receipt)
shutil.copy2(__file__, OUT / 'stage_servo23_native38.used.py')
print(json.dumps({k: receipt[k] for k in ['board_sha256', 'status', 'all_other_source_objects_exact']}))
