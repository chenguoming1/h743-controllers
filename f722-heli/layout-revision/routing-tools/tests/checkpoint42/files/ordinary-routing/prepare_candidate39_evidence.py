"""Prepare honest source-bound construction evidence; this does not adopt or seal."""
from pathlib import Path
import collections
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent
D = ROOT / 'candidate39'
S = ROOT / 'candidate38'
STAGE = ROOT / 'servo23-native-stage38'
SEED = ROOT / 'servo23-native-stage38-exit'
read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
write = lambda p, v: Path(p).write_text(json.dumps(v, indent=2) + '\n')
source, current = read(S / 'f722-heli.native.json'), read(D / 'f722-heli.native.json')
before = {o['uuid']: o for o in source['objects']}
after = {o['uuid']: o for o in current['objects']}
old_map = read(S / 'f722-heli.logical-route-map.json')['logical_route_map']
new_map = read(D / 'f722-heli.logical-route-map.json')['logical_route_map']
stage_proof = read(STAGE / 'construction-provenance.json')
removed = set(before) - set(after)
added = set(after) - set(before)
assert removed == {o['uuid'] for o in stage_proof['removed_source_objects']}
assert len(removed) == 13 and len(added) == 46
assert all(after[u] == o for u, o in before.items() if u not in removed)
assert all(new_map.get(u) == owner for u, owner in old_map.items() if u not in removed)
assert all(source[k] == current[k] for k in ['footprints', 'edge_cuts', 'copper_layers'])
h = sha(D / 'f722-heli.kicad_pcb')
assert h == current['board_sha256'] == '246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7'
assert source['board_sha256'] == sha(S / 'f722-heli.kicad_pcb')
assert read(D / 'servo23-complete-rewritten-entries.json')['passed']
assert read(D / 'servo23-complete-support-return.json')['passed']
assert read(D / 'owner-summary.json')['drc'] == {'unconnected': 42, 'errors': 0, 'warnings': 0}
copies = {
    STAGE / 'construction-provenance.json': 'joint-stage-construction.json',
    STAGE / 'continuation-recheck.json': 'accepted38-rebind.json',
    SEED / 'construction-provenance.json': 'exit-seed-construction.json',
    SEED / 'native-library-dependency-copy.json': 'exit-seed-library-context.json',
    ROOT / 'servo23-joint-plan/plan.json': 'joint-plan.json',
    ROOT / 'servo23-joint-plan/screen.json': 'joint-plan-screen.json',
    ROOT / 'servo3-entry-access-review/report.json': 'p1-native-and-engine-screen.json',
    ROOT / 'servo3-entry-access-review/selected-proposal-supplement.json': 'p1-selected-proposal-supplement.json',
    ROOT / 'model-servo23-stage38-ready/servo_p1.attempt-ledger.json': 'unseeded-engine-refusal.json',
    ROOT / 'model-servo23-stage38-ready/servo_p1.bounded-run.json': 'unseeded-engine-bound.json',
    ROOT / 'model-servo23-stage38-exit-ready/servo_p1_seed.attempt-ledger.json': 'seeded-engine-refusal.json',
    ROOT / 'model-servo23-stage38-exit-ready/servo_p1_seed.bounded-run.json': 'seeded-engine-bound.json',
    ROOT / 'model-servo23-stage38-ready/zero-parity.json': 'joint-stage-zero-parity.json',
    ROOT / 'model-servo23-stage38-exit-ready/zero-parity.json': 'exit-seed-zero-parity.json',
    D / 'servo23-complete-rewritten-entries.json': 'endpoint-audit.json',
    D / 'servo23-complete-support-return.json': 'power-audit.json',
}
for src, name in copies.items():
    shutil.copy2(src, D / name)
construction = {
    'schema': 'f722-explicit-coordinated-native-transaction/v1', 'passed': True,
    'source_board_sha256': source['board_sha256'], 'board_sha256': h,
    'source_native_sha256': sha(S / 'f722-heli.native.json'),
    'candidate_native_sha256': sha(D / 'f722-heli.native.json'),
    'source_map_sha256': sha(S / 'f722-heli.logical-route-map.json'),
    'candidate_map_sha256': sha(D / 'f722-heli.logical-route-map.json'),
    'removed_source_records': [before[u] for u in sorted(removed)],
    'added_candidate_records': [after[u] for u in sorted(added)],
    'removed_logical_owners': {u: old_map.get(u) for u in sorted(removed)},
    'added_logical_owners': {u: new_map.get(u) for u in sorted(added)},
    'all_other_source_objects_exact': len(before) - len(removed),
    'all_retained_logical_owners_exact': True,
    'all_poses_pads_outline_layers_exact': True,
    'removed_counts': dict(collections.Counter(o['kind'] + ':' + o['net'] for u, o in before.items() if u in removed)),
    'added_counts': dict(collections.Counter(o['kind'] + ':' + o['net'] for u, o in after.items() if u in added)),
    'dedicated_ground_change': 'Only the two declared U12.2 .25 mm return tracks and its one .45/.20 mm tented via are replaced. No other GND objects change.',
    'ground_return_complete_receipt': 'servo23-complete-support-return.json',
    'ground_return_complete_receipt_sha256': sha(D / 'servo23-complete-support-return.json'),
    'actual_io_receipt_sha256': sha(D / 'protection-actual-io.json'),
    'complete_rewritten_entry_receipt_sha256': sha(D / 'servo23-complete-rewritten-entries.json'),
    'engine_success_claimed': False, 'numerical_power_VCAP_applicable': False,
    'adoption_claimed': False,
}
write(D / 'coordinated-change-receipt.json', construction)
write(D / 'f722-heli.import.json', {
    'schema': 'f722-explicit-coordinated-native-construction-receipt/v1',
    'passed': True, 'scope': 'Exact construction, identities and declared removals; owner acceptance and numerical qualification remain separate.',
    'source_sha256': source['board_sha256'], 'output_sha256': h,
    'construction_source_sha256': read(D / 'construction-provenance.json')['source_board_sha256'],
    'direct_engine_output': False, 'engine_routing_succeeded': False,
    'engine_partial_geometry_adopted': False,
    'ses_engine_native_geometry_equal': False,
    'session_artifact': None,
    'construction_kind': 'Explicit coordinated SERVO2/3 and dedicated U12.2 return reconstruction, followed by sealed native-screened SERVO3 P1 construction.',
    'coordinated_change_receipt': 'coordinated-change-receipt.json',
    'coordinated_change_receipt_sha256': sha(D / 'coordinated-change-receipt.json'),
    'construction_provenance': 'construction-provenance.json',
    'construction_provenance_sha256': sha(D / 'construction-provenance.json'),
    'logical_route_map_artifact': 'f722-heli.logical-route-map.json',
    'logical_route_map_sha256': sha(D / 'f722-heli.logical-route-map.json'),
    'undeclared_native_changes': 0, 'footprints_preserved': 156,
    'reference_plane_refill_performed': True, 'numerical_power_VCAP_applicable': False,
})
write(D / 'power-revalidation-required.json', {
    'board_sha256': h, 'numerical_power_and_VCAP_applicability': False,
    'last_fully_bound_numerical_candidate': 'candidate24',
    'last_fully_bound_numerical_receipt': 'static-power-validation/candidate24-power-result-applicability.json',
    'last_fully_bound_numerical_receipt_sha256': '8373a599fe81a58571422fc4a1f4fe3afb65acad2fd7b3528eef43d575edce11',
    'reason': 'Declared TVS ground-return relocation, signal-via changes and refilled GND planes versus accepted38. Existing numerical power/VCAP results cannot be inherited.',
    'geometric_support_continuity_passed': True,
    'transient_return_qualification_claimed': False,
})
shutil.copy2(__file__, D / 'prepare_candidate39_evidence.used.py')
print(json.dumps({'board_sha256': h, 'removed': len(removed), 'added': len(added), 'unchanged': len(before) - len(removed), 'direct_engine_output': False}))
