#!/usr/bin/env python3
"""Build an add-only native import packet from an explicitly reviewed network.

This creates a small import contract, not a planning model or engine route. All
existing native objects are immutable; the normal importer and native gates
still check the independently represented proposed geometry.
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['source-board', 'source-native', 'logical-route-map', 'role-model', 'proposal', 'out']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    native = json.loads(args.source_native.read_text())
    roles = json.loads(args.role_model.read_text())
    handoff = json.loads(args.logical_route_map.read_text())
    proposal = json.loads(args.proposal.read_text())
    board_hash = sha(args.source_board)
    assert native['board_sha256'] == handoff['board_sha256'] == board_hash
    assert proposal['source_board']['sha256'] == board_hash
    assert proposal['source_native']['sha256'] == sha(args.source_native)
    assert proposal['immutable_existing_geometry'] and not proposal['remove_existing_objects']
    assert sha(proposal['proof_receipt']['path']) == proposal['proof_receipt']['sha256']
    assert sha(proposal['proposal_receipt']['path']) == proposal['proposal_receipt']['sha256']
    proof = json.loads(Path(proposal['proposal_receipt']['path']).read_text())
    assert proof['sources_and_historical_proof_unchanged']
    for path, checked in zip(proposal['paths'], proof['paths'], strict=True):
        assert all(path[k] == checked[k] for k in ['net', 'layer', 'width_mm', 'points_mm'])
        assert checked['minimum_excess_clearance_mm'] >= 0
    for via, checked in zip(proposal['vias'], proof['new_vias'], strict=True):
        assert all(via[k] == checked[k] for k in ['net', 'xy_mm', 'diameter_mm', 'drill_mm'])
        assert checked['minimum_excess_clearance_mm'] >= 0
    assert all(x.get('pass', True) for x in proof['interpath_and_via_checks'])
    assert all(x['full_width_native_inside_polygon_passed'] for x in proof['endpoint_entries'])
    assert all(x['full_width_annular_transit_passed'] for x in proof['full_width_annular_transit'])
    reference = json.loads(Path(roles['physical_native']).read_text())
    byid = {o['uuid']: o for o in native['objects']}
    assert all(byid.get(o['uuid']) == o for o in reference['objects'] if o['kind'] == 'pad'), 'Pad geometry or pinout changed from logical role definitions'
    for uid, logical in handoff['logical_route_map'].items():
        assert byid[uid]['net'] == roles['aliases'][logical]
    net = proposal['net']
    assert net in roles['ordinary_nets'] and roles['aliases'][net] == net
    assert not any(o['kind'] != 'pad' and o['net'] == net for o in native['objects']), 'Use a continuation-aware constructor for existing net copper'
    routes, wires, vias = [], [], []
    for path in proposal['paths']:
        assert path['net'] == net and path['width_mm'] == .127
        assert path['layer'] in roles['routable_layers']
        points = [[round(v * 1e5) for v in xy] for xy in path['points_mm']]
        assert [[v / 1e5 for v in xy] for xy in points] == path['points_mm']
        assert len(points) >= 2 and all(a != b and (a[0] == b[0] or a[1] == b[1] or abs(a[0] - b[0]) == abs(a[1] - b[1])) for a, b in zip(points, points[1:]))
        wires.append('(wire (path ' + path['layer'] + ' 12700 ' + ' '.join(f'{x} {-y}' for x, y in points) + ') (type route))')
        routes.append({'kind': 'track', 'fixed': 'NOT_FIXED', 'nets': [net], 'layer': path['layer'], 'width': .127, 'points': path['points_mm']})
    seen = set()
    for via in proposal['vias']:
        assert via['net'] == net and via['diameter_mm'] == .45 and via['drill_mm'] == .20
        xy = via['xy_mm']
        point = tuple(round(v * 1e5) for v in xy)
        assert [v / 1e5 for v in point] == xy and point not in seen
        seen.add(point)
        vias.append(f'(via VIA_450_200 {point[0]} {-point[1]})')
        routes.append({'kind': 'via', 'fixed': 'NOT_FIXED', 'nets': [net], 'xy': xy, 'diameter': .45, 'drill': .20})
    assert routes and len(seen) == 2
    zones = [z['uuid'] for z in native['zones'] if not z['rule'] and z['net'] == 'GND' and set(z['layers']) <= {'In1.Cu', 'In4.Cu'}]
    assert len(zones) == 2
    contract = {'schema': 'f722-native-add-only-import/v1', 'engine_planning_model': False, 'physical_board': str(args.source_board.resolve()), 'physical_native': str(args.source_native.resolve()), 'board_sha256': board_hash, 'native_sha256': sha(args.source_native), 'aliases': roles['aliases'], 'ordinary_nets': roles['ordinary_nets'], 'routable_layers': roles['routable_layers'], 'mutable_source_ids': [], 'source_logical_nets': handoff['logical_route_map'], 'regenerable_reference_zones': zones, 'logical_role_definition_sha256': sha(args.role_model), 'input_logical_map_sha256': sha(args.logical_route_map), 'all_source_copper_fixed': True}
    args.out.mkdir(parents=True, exist_ok=True)
    model = args.out / 'native-construction-model.json'
    model.write_text(json.dumps(contract, indent=2) + '\n')
    session = args.out / 'constructed.ses'
    session.write_text('(session "explicit-native-network" (routes (resolution mm 100000) (network_out (net ' + json.dumps(net) + ' ' + ' '.join(wires + vias) + '))))\n')
    receipt = {'kind': 'explicit_native_network_construction', 'engine_routing_performed': False, 'engine_insertion_succeeded': False, 'source_board_sha256': board_hash, 'source_native_sha256': sha(args.source_native), 'proposal_sha256': sha(args.proposal), 'proposal_proof_sha256': proposal['proof_receipt']['sha256'], 'construction_source_sha256': sha(__file__), 'import_contract_sha256': sha(model), 'all_source_native_objects_fixed': True, 'source_objects_removal_allowed': False, 'new_net': net, 'new_tracks': sum(len(p['points_mm']) - 1 for p in proposal['paths']), 'new_vias': len(vias), 'native_refill_drc_process_protection_endpoint_and_connectivity_validation_required': True}
    report = args.out / 'constructed-report.json'
    report.write_text(json.dumps({'board_sha256': board_hash, 'model_sha256': sha(model), 'routes': routes, 'route_construction': receipt, 'route_solver_used': False, 'native_validation_required': True}, indent=2) + '\n')
    receipt.update(session_sha256=sha(session), report_sha256=sha(report))
    (args.out / 'construction.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
