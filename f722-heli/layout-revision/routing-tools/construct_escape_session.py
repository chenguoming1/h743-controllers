#!/usr/bin/env python3
"""Construct explicitly proposed, pad-anchored via escapes for native validation.

This does not claim a successful engine route or complete net connection. Every
proposal must carry source-bound geometry evidence; native checks remain required.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

from shapely import unary_union
from shapely.geometry import LineString, Point, Polygon


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def geometry(polygons):
    return unary_union([Polygon(p['outer'], p.get('holes', [])) for p in polygons])


def network_end(text):
    start = text.index('(network_out')
    depth = 0
    quoted = escaped = False
    for i in range(start, len(text)):
        char = text[i]
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
            if depth == 0:
                return i
    raise ValueError('Unclosed network_out')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['model', 'native', 'base-session', 'base-report', 'proposals', 'out-prefix']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    model = json.loads(args.model.read_text())
    native = json.loads(args.native.read_text())
    report = json.loads(args.base_report.read_text())
    proposals = json.loads(args.proposals.read_text())
    source = proposals['source_identity']
    assert proposals['source_recheck_unchanged'], 'Proposal source proof is incomplete'
    assert sha(proposals['proof_receipt']['path']) == proposals['proof_receipt']['sha256']
    assert model['board_sha256'] == native['board_sha256'] == report['board_sha256'] == source['board_sha256']
    assert report['model_sha256'] == sha(args.model)
    assert model['native_sha256'] == sha(args.native) == source['native_sha256']
    assert sha(model['physical_board']) == model['board_sha256']
    text = args.base_session.read_text()
    assert re.search(r'\(resolution\s+mm\s+100000\)', text)
    blocks, routes, checks = [], [], []
    used = set()
    pads = {o['uuid']: o for o in native['objects'] if o['kind'] == 'pad'}
    for proposal in proposals['proposals']:
        assert proposal['all_checks_pass_nominal'] and proposal['all_checks_pass_with_native_polygon_error_reserve']
        net, layer = proposal['net'], proposal['layer']
        assert net in model['ordinary_nets'] and model['aliases'][net] == net
        assert net not in used and net not in model['source_logical_nets'].values(), 'Use a continuation-aware constructor for pre-existing routes'
        assert layer in model['routable_layers']
        assert proposal['width_mm'] == .127 and proposal['diameter_mm'] == .45 and proposal['drill_mm'] == .20
        assert not re.search(r'\(net\s+(?:' + re.escape(net) + '|' + re.escape(json.dumps(net)) + r')(?=\s|\))', text)
        used.add(net)
        points = [[round(v * 1e5) for v in xy] for xy in proposal['points_mm']]
        coords = [[v / 1e5 for v in xy] for xy in points]
        assert len(points) >= 2 and coords == proposal['points_mm'], 'Proposals must be exactly on the 10 nm engine grid'
        assert coords[-1] == proposal['via_xy_mm']
        assert all(a != b and (a[0] == b[0] or a[1] == b[1] or abs(a[0] - b[0]) == abs(a[1] - b[1])) for a, b in zip(points, points[1:]))
        pad = pads[proposal['pad_uuid']]
        assert pad['net'] == net and pad['key'] == proposal['pad_key'] and layer in pad['inside']
        interior = geometry(pad['inside'][layer])
        if (pad.get('drill') or {}).get('outside'):
            interior = interior.difference(geometry(pad['drill']['outside']))
        assert interior.contains(Point(coords[0])) and Point(coords[0]).distance(interior.boundary) >= .063501, 'Pad entry lacks a full-width interior witness'
        line = LineString(coords)
        gaps = []
        for obj in native['objects']:
            if obj['net'] != net and layer in obj['copper']:
                gaps.append({'uuid': obj['uuid'], 'key': obj.get('key'), 'net': obj['net'], 'gap_mm': line.distance(geometry(obj['copper'][layer])) - .0635})
        minimum = min(gaps, key=lambda x: x['gap_mm'])
        assert minimum['gap_mm'] >= .127, minimum
        checks.append({'net': net, 'pad': pad['key'], 'pad_uuid': pad['uuid'], 'pad_centerline_interior_depth_mm': Point(coords[0]).distance(interior.boundary), 'minimum_foreign_object_track_clearance': minimum, 'proposal': proposal})
        path = ' '.join(f'{x} {-y}' for x, y in points)
        x, y = points[-1]
        blocks.append(f'\n      (net {json.dumps(net)} (wire (path {layer} 12700 {path}) (type route)) (via VIA_450_200 {x} {-y}))\n    ')
        routes += [{'kind': 'track', 'fixed': 'NOT_FIXED', 'nets': [net], 'layer': layer, 'width': .127, 'points': coords}, {'kind': 'via', 'fixed': 'NOT_FIXED', 'nets': [net], 'xy': coords[-1], 'diameter': .45, 'drill': .20}]
    assert routes
    end = network_end(text)
    text = text[:end] + ''.join(blocks) + text[end:]
    receipt = {'kind': 'explicit_native_pad_anchored_via_escape_construction', 'engine_routing_performed': False, 'complete_net_connection_claimed': False, 'board_sha256': model['board_sha256'], 'model_sha256': sha(args.model), 'native_sha256': sha(args.native), 'base_session_sha256': sha(args.base_session), 'base_report_sha256': sha(args.base_report), 'proposal_sha256': sha(args.proposals), 'construction_source_sha256': sha(__file__), 'constructed_nets': sorted(used), 'checks': checks, 'native_drc_endpoint_protection_process_validation_required': True}
    report.pop('areas', None)
    report.pop('contact_partitions', None)
    report['route_construction'] = receipt
    report['native_validation_required'] = True
    report['routes'] += routes
    args.out_prefix.parent.mkdir(parents=True, exist_ok=True)
    ses = Path(str(args.out_prefix) + '.ses')
    result = Path(str(args.out_prefix) + '.constructed-report.json')
    ses.write_text(text)
    result.write_text(json.dumps(report, indent=2) + '\n')
    receipt.update(output_session_sha256=sha(ses), output_report_sha256=sha(result))
    Path(str(args.out_prefix) + '.construction.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'checks'}))


if __name__ == '__main__':
    main()
