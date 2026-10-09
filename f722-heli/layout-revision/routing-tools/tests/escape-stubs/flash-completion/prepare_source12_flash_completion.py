#!/usr/bin/env python3
"""Bounded, read-only native-polygon proof of the complete FLASH_WP_N construction on source12."""
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

BOARD = ROOT / 'candidate12/f722-heli.kicad_pcb'
NATIVE = ROOT / 'candidate12/f722-heli.native.json'
RAW = ROOT / 'model-candidate09-cleanup/located-topology.json'
EXPECTED = '508b5a36ed12795c4a2486b699f321f0f9867e29717175455e8fd7fc6f1f525a'
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
assert json.loads(RAW.read_text())['source_board_sha256'] == '544491a48469d418ed47cf5da12b6b9406db282d60a3cda77b154f6ed11a869d'  # Historical topology provenance only
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



STUB = [[30.95, 21.365], [31.1203, 21.365], START]
FULL_PATHS = [('U3.3-pad-to-seed-via', 'B.Cu', STUB),
              ('seed-via-to-return-via', 'In2.Cu', PATHS['In2.Cu']),
              ('return-via-to-R5.2', 'B.Cu', PATHS['B.Cu'])]
NEW_VIAS = [('seed-via', START), ('return-via', VIA)]


def main():
    source_paths = [BOARD, NATIVE, RAW]
    historical_paths = [HERE/'proposal.json', HERE/'native-exact-witnesses.json',
                        HERE/'prepare_flash_completion.py']
    original_hashes = {str(path): sha(path) for path in source_paths + historical_paths}
    assert {o['kind'] for o, *_ in OBJECTS if o['net'] == NET} == {'pad'}, 'Source12 must have only the two FLASH pads before construction'
    raw = json.loads(RAW.read_text())
    proof = {'source_board_sha256': EXPECTED, 'source_hashes': original_hashes,
             'native_version': N['native_version'], 'maximum_polygon_error_mm': ERROR,
             'historical_raw_topology': raw,
             'scope': 'Fresh read-only exact-distance proof against source12 including accepted ADC copper. Full FLASH construction includes two newly added vias and the U3.3 seed stub. Only listed regenerable GND fills on In1/In4 are excluded. No board/source/JVM/solver mutation; native import/refill/DRC remain required.',
             'paths': [], 'vias': []}
    proposals = []
    cross = []
    for name, layer, points in FULL_PATHS:
        trace_obs, via_obs, excluded = obstacles(layer)
        path = LineString(points)
        assert OUTLINE.covers(path) and path.is_simple
        checks = check(path, trace_obs)
        assert all(row['pass_with_polygon_error'] for row in checks), (name, checks[:3])
        segments = []
        for i, (a, b) in enumerate(zip(points, points[1:])):
            dx, dy = b[0]-a[0], b[1]-a[1]
            assert abs(dx)<1e-9 or abs(dy)<1e-9 or abs(abs(dx)-abs(dy))<1e-9
            segment = LineString([a,b]);rows = check(segment, trace_obs)
            assert all(row['pass_with_polygon_error'] for row in rows)
            segments.append({'index': i, 'points_mm': [a,b], 'length_mm': segment.length,
                             'all_obstacle_checks': rows})
        self_checks = []
        for i, a in enumerate(segments):
            for j, b in enumerate(segments):
                if j <= i+1:
                    continue
                distance = LineString(a['points_mm']).distance(LineString(b['points_mm']))
                gap = distance-2*HALF
                assert gap > ERROR, (name,i,j,gap)
                self_checks.append({'segment_a': i, 'segment_b': j,
                                    'centerline_distance_mm': distance,
                                    'same_net_physical_gap_mm': gap,
                                    'nonadjacent_copper_disjoint': True})
        proposal = {'name': name, 'net': NET, 'net_code': next(o['net_code'] for o,*_ in OBJECTS if o['net']==NET),
                    'layer': layer, 'width_mm': .127, 'points_mm': points,
                    'corner_count': len(points), 'length_mm': path.length,
                    'minimum_excess_clearance_mm': checks[0]['extra_clearance_mm'],
                    'nearest_constraints': checks[:8], 'trace_obstacle_count': len(trace_obs),
                    'excluded_regenerable_gnd_zone_ids': excluded,
                    'all_segments_octilinear': True, 'centerline_simple': True,
                    'inside_native_outline_with_npth': True,
                    'all_native_checks_pass_with_polygon_error': True,
                    'self_path_nonadjacent_checks': self_checks}
        proposals.append(proposal)
        proof['paths'].append({**proposal, 'segments': segments, 'all_path_obstacle_checks': checks})
    via_proposals = []
    for name, xy in NEW_VIAS:
        checks = check(Point(xy), via_obs)
        assert OUTLINE.covers(Point(xy)) and all(row['pass_with_polygon_error'] for row in checks), (name,checks[:3])
        proposal = {'name': name, 'net': NET, 'xy_mm': xy, 'diameter_mm': .45, 'drill_mm': .20,
                    'type': 'through', 'layers': ['F.Cu','B.Cu'],
                    'minimum_excess_clearance_mm': checks[0]['extra_clearance_mm'],
                    'obstacle_count': len(checks),
                    'obstacle_category_counts': dict(collections.Counter(row['category'] for row in checks)),
                    'nearest_constraints': checks[:8],
                    'all_native_checks_pass_with_polygon_error': True}
        via_proposals.append(proposal)
        proof['vias'].append({**proposal, 'all_obstacle_checks': checks})
    # All new copper belongs to the same net. Check unintentional same-layer contact,
    # all new drill pairs, and full-width annular transit at every intended via join.
    for i, (name_a, layer_a, points_a) in enumerate(FULL_PATHS):
        for name_b, layer_b, points_b in FULL_PATHS[i+1:]:
            if layer_a != layer_b:
                cross.append({'category':'path_to_path','a':name_a,'b':name_b,
                              'distinct_layers':True,'copper_clearance_required':False})
                continue
            distance = LineString(points_a).distance(LineString(points_b))
            gap = distance-2*HALF
            assert gap > .127+ERROR
            cross.append({'category':'same_layer_distinct_paths','a':name_a,'b':name_b,
                          'centerline_distance_mm':distance,'physical_gap_mm':gap,
                          'extra_vs_0_127_mm':gap-.127,'pass':True})
    distance = Point(START).distance(Point(VIA))
    cross.extend([{'category':'new_via_to_new_via_copper','physical_gap_mm':distance-2*VIA_RADIUS,
                   'required_gap_mm':.127,'pass':distance-2*VIA_RADIUS>.127+ERROR},
                  {'category':'new_via_to_new_via_drill','physical_gap_mm':distance-2*DRILL_RADIUS,
                   'required_gap_mm':.25,'pass':distance-2*DRILL_RADIUS>.25+ERROR}])
    assert all(row.get('pass',True) for row in cross)
    annular = []
    for via_name, xy in NEW_VIAS:
        for path_name, layer, points in FULL_PATHS:
            if points[0] == xy or points[-1] == xy:
                next_point = points[1] if points[0] == xy else points[-2]
                dx,dy = next_point[0]-xy[0],next_point[1]-xy[1]
                length = math.hypot(dx,dy);assert length > .17
                ux,uy=dx/length,dy/length;radius=.17
                center=[xy[0]+radius*ux,xy[1]+radius*uy]
                ends=[[center[0]-HALF*uy,center[1]+HALF*ux],
                      [center[0]+HALF*uy,center[1]-HALF*ux]]
                inner_gap=radius-DRILL_RADIUS
                outer_gap=VIA_RADIUS-math.hypot(radius,HALF)
                assert min(inner_gap,outer_gap)>ERROR
                annular.append({'via':via_name,'path':path_name,'layer':layer,
                                'intended_endpoint_at_via_center':True,
                                'full_width_transverse_section_mm':ends,
                                'section_width_mm':2*HALF,
                                'section_radial_distance_mm':radius,
                                'clearance_from_drill_mm':inner_gap,
                                'clearance_inside_annular_outer_edge_mm':outer_gap,
                                'full_width_annular_transit_passed':True})
            else:
                distance=Point(xy).distance(LineString(points));gap=distance-VIA_RADIUS-HALF
                assert gap>.127+ERROR
                cross.append({'category':'via_to_nonincident_path','via':via_name,'path':path_name,
                              'physical_gap_mm':gap,'extra_vs_0_127_mm':gap-.127,'pass':True})
    entries=[]
    for key, layer, points in [('U3.3','B.Cu',STUB[:2]),('R5.2','B.Cu',PATHS['B.Cu'][-2:])]:
        pad=next(obj for obj,*_ in OBJECTS if obj.get('key')==key)
        inside=geom(pad['inside'][layer]);entry=LineString(points)
        excess=entry.distance(inside.boundary)-HALF
        assert pad['net']==NET and inside.covers(entry) and excess>ERROR
        entries.append({'pad_key':key,'pad_uuid':pad['uuid'],'footprint_uuid':pad['footprint_uuid'],
                        'layer':layer,'points_mm':points,'length_mm':entry.length,
                        'centerline_inside_native_pad':True,
                        'full_width_containment_excess_mm':excess,
                        'full_width_native_inside_polygon_passed':True})
    proof.update(interpath_and_via_checks=cross,full_width_annular_transit=annular,
                 endpoint_entries=entries)
    assert all(sha(Path(path))==expected for path,expected in original_hashes.items())
    proof['sources_and_historical_proof_unchanged']=True
    proof_path=HERE/'source12-native-exact-witnesses.json'
    proof_path.write_text(json.dumps(proof,indent=2)+'\n')
    result={'status':'source12_native_polygon_full_construction_pass_pending_native_import_refill_drc',
            'source_board_sha256':EXPECTED,'source_hashes':original_hashes,
            'proof':{'path':str(proof_path),'sha256':sha(proof_path)},
            'script_sha256':sha(Path(__file__)),
            'paths':proposals,'new_vias':via_proposals,'endpoint_entries':entries,
            'interpath_and_via_checks':cross,'full_width_annular_transit':annular,
            'sources_and_historical_proof_unchanged':True,
            'rules_mm':{'trace_width':.127,'foreign_copper_gap':.127,'edge_npth_copper_gap':.254,
                        'via_diameter':.45,'via_drill':.20,'drill_to_drill_gap':.25,
                        'drill_to_all_smt_masks_gap':.20},
            'scope':'Includes accepted source12 ADC copper. This adds both FLASH vias and the complete seed stub; source12 has only U3.3 and R5.2 pads on FLASH_WP_N.',
            'pending':['Native import and ground refill/saved-fill checks.',
                       'Native strict DRC, process, full-net connectivity and original identity gates.']}
    (HERE/'source12-proposal.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],
                      'paths':[{'name':p['name'],'layer':p['layer'],'corners':p['corner_count'],
                                'length_mm':p['length_mm'],'min_excess_mm':p['minimum_excess_clearance_mm']}
                               for p in proposals],
                      'vias':[{'name':v['name'],'xy_mm':v['xy_mm'],
                               'min_excess_mm':v['minimum_excess_clearance_mm']}
                              for v in via_proposals],
                      'endpoint_entries':entries,'annular_join_count':len(annular),
                      'proposal':str(HERE/'source12-proposal.json')},indent=2))


if __name__=='__main__':
    main()
