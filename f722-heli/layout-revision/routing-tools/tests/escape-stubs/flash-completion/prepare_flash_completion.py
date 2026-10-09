#!/usr/bin/env python3
"""Bounded, read-only native-polygon proof of a simpler FLASH_WP_N completion."""
import collections
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT.parent / 'python-deps'))
import shapely
from shapely import unary_union
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import nearest_points

BOARD = ROOT / 'candidate09/f722-heli.kicad_pcb'
NATIVE = ROOT / 'candidate09/f722-heli.native.json'
RAW = ROOT / 'model-candidate09-cleanup/located-topology.json'
EXPECTED = '544491a48469d418ed47cf5da12b6b9406db282d60a3cda77b154f6ed11a869d'
NET = 'FLASH_WP_N'
HALF, VIA_RADIUS, DRILL_RADIUS = .0635, .225, .1
VIA = [30.21631, 24.55996]
START = [31.5, 20.9853]
PATHS = {
    'In2.Cu': [START, [30.21631, 22.26899], VIA],
    'B.Cu': [VIA, [29.72977, 25.0465], [28.9515, 25.0465],
             [28.775, 24.87], [28.775, 24.1], [28.165, 23.49],
             [27.485, 23.49], [27.285, 23.49]],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geom(polygons):
    parts = [Polygon(p['outer'], p.get('holes', [])) for p in polygons]
    assert all(p.is_valid for p in parts)
    result = unary_union(parts)
    assert result.is_valid
    return result


N = json.loads(NATIVE.read_text())
assert sha(BOARD) == N['board_sha256'] == EXPECTED
assert json.loads(RAW.read_text())['source_board_sha256'] == EXPECTED
ERROR = N['maximum_polygon_error_mm']
OUTLINE = geom(N['outline_with_npth']['polygons'])
OBJECTS = [(o, {layer: geom(p) for layer, p in o['copper'].items()},
            {layer: geom(p['polygons']) for layer, p in o.get('mask', {}).items()}
            if o.get('smd') else {},
            geom(o['drill']['outside']) if o.get('drill') else None)
           for o in N['objects']]


def obstacles(layer):
    trace, via, excluded = [], [], []

    def add(target, obj, category, gap, radius, geometry, layers):
        target.append({'object': obj.get('key', obj['uuid']), 'uuid': obj['uuid'],
                       'net': obj.get('net'), 'kind': obj.get('kind', 'zone'),
                       'category': category, 'layers': layers,
                       'required_physical_gap_mm': gap, 'moving_radius_mm': radius,
                       'required_center_distance_mm': gap + radius, 'geometry': geometry})

    for obj, copper, masks, drill in OBJECTS:
        if obj['net'] != NET:
            for name, geometry in copper.items():
                if name == layer:
                    add(trace, obj, 'foreign_copper', .127, HALF, geometry, [name])
                add(via, obj, 'foreign_copper', .127, VIA_RADIUS, geometry, [name])
        for name, geometry in masks.items():
            add(via, obj, 'all_smt_masks_no_net_exception', .20, DRILL_RADIUS, geometry, [name])
        if drill is not None:
            add(via, obj, 'all_drills_no_net_exception', .25, DRILL_RADIUS, drill,
                obj.get('barrel_layers', []))
            if obj.get('npth'):
                add(trace, obj, 'npth_copper', .254, HALF, drill, [])
                add(via, obj, 'npth_copper', .254, VIA_RADIUS, drill, [])
    for zone in N['zones']:
        if zone['rule']:
            geometry = geom(zone['outline'])
            if layer in zone['layers'] and (zone['forbid']['tracks'] or zone['forbid']['copper']):
                add(trace, zone, 'rule_keepout', 0, HALF, geometry, zone['layers'])
            if zone['layers'] and (zone['forbid']['vias'] or zone['forbid']['copper']):
                add(via, zone, 'rule_keepout', 0, VIA_RADIUS, geometry, zone['layers'])
        elif zone['net'] == 'GND' and set(zone['layers']) <= {'In1.Cu', 'In4.Cu'}:
            excluded.append(zone['uuid'])
        elif zone['net'] != NET:
            for name, polygons in zone['filled'].items():
                geometry = geom(polygons)
                if name == layer:
                    add(trace, zone, 'foreign_zone_copper', .127, HALF, geometry, [name])
                add(via, zone, 'foreign_zone_copper', .127, VIA_RADIUS, geometry, [name])
    for target, radius in [(trace, HALF), (via, VIA_RADIUS)]:
        target.append({'object': 'board-outline-including-npth', 'uuid': None, 'net': None,
                       'kind': 'outline', 'category': 'edge_npth_copper', 'layers': [],
                       'required_physical_gap_mm': .254, 'moving_radius_mm': radius,
                       'required_center_distance_mm': .254 + radius, 'geometry': OUTLINE.boundary})
    return trace, via, excluded


def check(moving, obs):
    rows = []
    for obstacle in obs:
        distance = moving.distance(obstacle['geometry'])
        a, b = nearest_points(moving, obstacle['geometry'])
        margin = distance - obstacle['required_center_distance_mm']
        row = {key: value for key, value in obstacle.items() if key != 'geometry'}
        row.update(center_distance_mm=distance,
                   physical_gap_mm=distance - obstacle['moving_radius_mm'],
                   extra_clearance_mm=margin,
                   pass_nominal=margin >= -1e-9,
                   pass_with_polygon_error=margin >= ERROR,
                   witness_on_moving_centerline_mm=list(a.coords[0]),
                   witness_on_native_obstacle_mm=list(b.coords[0]))
        rows.append(row)
    return sorted(rows, key=lambda row: row['extra_clearance_mm'])


def main():
    original_hashes = {str(path): sha(path) for path in [BOARD, NATIVE, RAW]}
    raw = json.loads(RAW.read_text())
    raw_paths = {p['layer']: p['requested_corners_mm'] for p in raw['raw_located_paths']
                 if p['net'] == NET}
    proof = {'source_hashes': original_hashes, 'native_version': N['native_version'],
             'maximum_polygon_error_mm': ERROR, 'raw_topology': raw,
             'scope': 'Read-only local geometric proposal; no board, raw topology, model, JVM or solver mutation. Exact Euclidean distances to conservative native polygons; no geometry repair or clearance relaxation. Only enumerated regenerable In1/In4 GND fills are excluded. Native import/refill/DRC and merged-ADC checks remain required.',
             'layers': []}
    proposals = []
    for layer, points in PATHS.items():
        trace, via, excluded = obstacles(layer)
        path = LineString(points)
        assert OUTLINE.covers(path)
        checks = check(path, trace)
        assert all(row['pass_with_polygon_error'] for row in checks)
        segments = []
        for i, (a, b) in enumerate(zip(points, points[1:])):
            dx, dy = b[0] - a[0], b[1] - a[1]
            assert abs(dx) < 1e-9 or abs(dy) < 1e-9 or abs(abs(dx) - abs(dy)) < 1e-9
            segment = LineString([a, b])
            segment_checks = check(segment, trace)
            assert all(row['pass_with_polygon_error'] for row in segment_checks)
            segments.append({'index': i, 'points_mm': [a, b], 'length_mm': segment.length,
                             'all_obstacle_checks': segment_checks})
        raw_checks = check(LineString(raw_paths[layer]), trace)
        proposal = {'net': NET, 'layer': layer, 'width_mm': .127, 'points_mm': points,
                    'corner_count': len(points), 'length_mm': path.length,
                    'raw_corner_count': len(raw_paths[layer]),
                    'raw_length_mm': LineString(raw_paths[layer]).length,
                    'minimum_excess_clearance_mm': checks[0]['extra_clearance_mm'],
                    'nearest_constraints': checks[:8],
                    'raw_nearest_constraints': raw_checks[:4],
                    'trace_obstacle_count': len(trace),
                    'excluded_regenerable_gnd_zone_ids': excluded,
                    'all_segments_octilinear': True,
                    'inside_native_outline_with_npth': True,
                    'all_checks_pass_with_native_polygon_error': True}
        proposals.append(proposal)
        proof['layers'].append({**proposal, 'segments': segments, 'all_path_obstacle_checks': checks})

    via_checks = check(Point(VIA), via)
    assert OUTLINE.covers(Point(VIA))
    assert all(row['pass_with_polygon_error'] for row in via_checks)
    via_proposal = {'net': NET, 'xy_mm': VIA, 'diameter_mm': .45, 'drill_mm': .20,
                    'type': 'through', 'layers': ['F.Cu', 'B.Cu'],
                    'minimum_excess_clearance_mm': via_checks[0]['extra_clearance_mm'],
                    'obstacle_count': len(via_checks),
                    'obstacle_category_counts': dict(collections.Counter(row['category'] for row in via_checks)),
                    'nearest_constraints': via_checks[:8],
                    'all_checks_pass_with_native_polygon_error': True}
    pad = next(obj for obj, *_ in OBJECTS if obj.get('key') == 'R5.2')
    inside = geom(pad['inside']['B.Cu'])
    entry = LineString(PATHS['B.Cu'][-2:])
    entry_margin = entry.distance(inside.boundary) - HALF
    assert inside.covers(entry) and entry_margin > ERROR
    entry_evidence = {'pad_key': 'R5.2', 'pad_uuid': pad['uuid'], 'net': pad['net'],
                      'points_mm': PATHS['B.Cu'][-2:], 'length_mm': entry.length,
                      'centerline_inside_native_pad': True,
                      'full_width_containment_excess_mm': entry_margin,
                      'full_width_native_inside_polygon_passed': True}
    start_via = next(obj for obj, *_ in OBJECTS if obj['kind'] == 'via'
                     and obj['uuid'] == 'd41c1d0a-2833-4d09-b76c-706923526c40')
    assert start_via['net'] == NET and start_via['xy'] == START
    proof.update(new_via={**via_proposal, 'all_obstacle_checks': via_checks},
                 destination_pad_entry=entry_evidence, existing_start_via=start_via)
    assert all(sha(Path(path)) == expected for path, expected in original_hashes.items())
    proof['source_recheck_unchanged'] = True
    proof_path = HERE / 'native-exact-witnesses.json'
    proof_path.write_text(json.dumps(proof, indent=2) + '\n')
    result = {'status': 'native_polygon_proposal_pass_pending_native_import_refill_drc',
              'source_hashes': original_hashes,
              'proof': {'path': str(proof_path), 'sha256': sha(proof_path)},
              'script_sha256': sha(Path(__file__)),
              'rules_mm': {'trace_width': .127, 'foreign_copper_gap': .127,
                           'edge_and_npth_copper_gap': .254, 'via_diameter': .45,
                           'via_drill': .20, 'drill_to_drill_gap': .25,
                           'via_drill_to_all_smt_masks_gap': .20},
              'paths': proposals, 'new_via': via_proposal,
              'destination_pad_entry': entry_evidence,
              'existing_start_via_uuid': start_via['uuid'],
              'source_recheck_unchanged': True,
              'pending': ['Native import with unchanged source identities.',
                          'Native ground refill and saved-fill checks.',
                          'Strict native DRC, process and full-net connectivity.',
                          'Recheck against any newly added ADC route or other concurrent geometry.']}
    (HERE / 'proposal.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'],
                      'paths': [{'layer': p['layer'], 'points_mm': p['points_mm'],
                                 'length_mm': p['length_mm'],
                                 'minimum_excess_clearance_mm': p['minimum_excess_clearance_mm']}
                                for p in proposals],
                      'via_minimum_excess_mm': via_proposal['minimum_excess_clearance_mm'],
                      'entry': entry_evidence, 'proposal': str(HERE / 'proposal.json')}, indent=2))


if __name__ == '__main__':
    main()
