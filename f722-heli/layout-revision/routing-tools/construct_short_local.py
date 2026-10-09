#!/usr/bin/env python3
"""Create an add-only SES import packet for a reviewed same-face native proposal."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ['proposal', 'logical-route-map', 'out']:
        ap.add_argument('--' + name, type=Path, required=True)
    a = ap.parse_args()
    proposal = json.loads(a.proposal.read_text())
    source = proposal['source_identity']
    board = Path(source['board_path'])
    native_path = Path(source['native_path'])
    role_path = Path(source['model_path'])
    assert sha(board) == source['board_sha256']
    assert sha(native_path) == source['native_sha256']
    assert sha(role_path) == source['model_sha256']
    assert sha(proposal['proof_receipt']['path']) == proposal['proof_receipt']['sha256']
    assert proposal['source_recheck_unchanged']
    native = json.loads(native_path.read_text())
    roles = json.loads(role_path.read_text())
    handoff = json.loads(a.logical_route_map.read_text())
    assert native['board_sha256'] == roles['board_sha256'] == handoff['board_sha256'] == sha(board)
    by_id = {o['uuid']: o for o in native['objects']}
    assert all(by_id[uid]['net'] == roles['aliases'][net] for uid, net in handoff['logical_route_map'].items())
    routes, networks = [], []
    for p in proposal['proposals']:
        net, layer, points = p['net'], p['layer'], p['points_mm']
        assert roles['aliases'][net] == net and net in roles['ordinary_nets']
        assert p['logical_role'] == roles['roles'][net] and p['logical_role']['kind'] == 'ordinary'
        assert layer in ['F.Cu', 'B.Cu'] and p['width_mm'] == .127 and not p['vias']
        assert p['all_nominal_native_polygon_checks_pass'] and p['minimum_extra_clearance_mm'] >= 0
        assert all(x['full_round_cap_inside_actual_native_pad'] for x in p['endpoint_full_width_entry'])
        assert all(p[k] in p['logical_role']['terminals'] for k in ['pad_uuid', 'target_pad_uuid'])
        assert not any(o['kind'] != 'pad' and o['net'] == net for o in native['objects'])
        # This no-refill constructor is deliberately limited to outside layers
        # with no copper zone. It cannot silently reuse stale plane antipads.
        assert not any(not z['rule'] and layer in z['layers'] for z in native['zones'])
        integers = [[round(v * 100000) for v in xy] for xy in points]
        assert [[v / 100000 for v in xy] for xy in integers] == points
        assert len(points) >= 2 and all(x != y and (x[0] == y[0] or x[1] == y[1] or abs(x[0]-y[0]) == abs(x[1]-y[1])) for x, y in zip(integers, integers[1:]))
        routes.append({'kind': 'track', 'fixed': 'NOT_FIXED', 'nets': [net], 'layer': layer, 'width': .127, 'points': points})
        wire = '(wire (path ' + layer + ' 12700 ' + ' '.join(f'{x} {-y}' for x, y in integers) + ') (type route))'
        networks.append('(net ' + json.dumps(net) + ' ' + wire + ')')
    assert routes
    a.out.mkdir(parents=True, exist_ok=True)
    contract = {'schema': 'f722-native-add-only-import/v1', 'engine_planning_model': False, 'physical_board': str(board.resolve()), 'physical_native': str(native_path.resolve()), 'board_sha256': sha(board), 'native_sha256': sha(native_path), 'aliases': roles['aliases'], 'ordinary_nets': roles['ordinary_nets'], 'routable_layers': roles['routable_layers'], 'mutable_source_ids': [], 'source_logical_nets': handoff['logical_route_map'], 'regenerable_reference_zones': [], 'all_source_copper_fixed': True, 'reference_plane_policy': 'No new vias or inner-layer copper; no copper zones on the changed outside layer; every saved zone retained exactly.'}
    model = a.out / 'native-construction-model.json'
    model.write_text(json.dumps(contract, indent=2) + '\n')
    session = a.out / 'constructed.ses'
    session.write_text('(session "explicit-native-local" (routes (resolution mm 100000) (network_out ' + ' '.join(networks) + ')))\n')
    report = {'board_sha256': sha(board), 'model_sha256': sha(model), 'routes': routes, 'route_solver_used': False, 'native_validation_required': True}
    (a.out / 'constructed-report.json').write_text(json.dumps(report, indent=2) + '\n')
    receipt = {'kind': 'explicit_native_short_local_construction', 'engine_routing_performed': False, 'source_board_sha256': sha(board), 'source_native_sha256': sha(native_path), 'proposal_sha256': sha(a.proposal), 'proof_sha256': proposal['proof_receipt']['sha256'], 'constructor_sha256': sha(__file__), 'model_sha256': sha(model), 'session_sha256': sha(session), 'source_objects_removal_allowed': False, 'new_tracks': sum(len(r['points']) - 1 for r in routes), 'new_vias': 0, 'reference_plane_refill_required': False, 'exact_saved_reference_plane_preservation_required': True, 'native_gates_required': True}
    (a.out / 'construction.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
