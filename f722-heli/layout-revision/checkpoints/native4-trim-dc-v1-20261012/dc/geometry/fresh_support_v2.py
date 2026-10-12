"""Disabled conservative primitive support integration; no final approval.

Original native contours remain immutable evidence. Derived copper/drill bounds
are separate analytic integer-IU geometry. No buffer/epsilon/repair is used.
"""
from collections import defaultdict
import copy
from decimal import Decimal
import sys
import conservative_primitives as primitive
import disabled_binding as b
import fresh_support as graph
import exact_native4_polygon

PRODUCTION_EXECUTION_ENABLED = False
BUDGET_IU = 10
MODEL = 'f722-conservative-native-support-proposal/v2'
SHAPE_CODES = {'circle': 0, 'rectangle': 1, 'oval': 2, 'roundrect': 4, 'custom': 6}


def same_ring(a, c):
    if len(a) != len(c):
        return False
    for ring in (c, list(reversed(c))):
        if any(a == ring[i:] + ring[:i] for i in range(len(ring))):
            return True
    return False


def iu(value):
    exact = Decimal(str(value)) * 1000000
    b.require(exact.is_finite() and exact == exact.to_integral_value(), 'Source coordinate is not exact native IU')
    return int(exact)


def point(values):
    b.require(len(values) == 2, 'Native coordinate needs two dimensions')
    return [iu(value) for value in values]


def contours_to_IU(rows):
    return [{'outer': [point(p) for p in row['outer']],
             'holes': [[point(p) for p in hole] for hole in row.get('holes', [])]} for row in rows]


def contour(hull):
    return [{'outer': [list(p) for p in hull], 'holes': []}]


def rotation_quarters(matrix):
    for q in range(4):
        if matrix == [list(primitive.rotate((1, 0), q)), list(primitive.rotate((0, 1), q))]:
            return q
    raise b.Refused('Unsupported or nonorthogonal native integer transform')


def validate_metadata(native, scope, metadata, native_sha=None):
    b.require(metadata.get('schema') == 'f722-native-primitive-parameter-sidecar/v1' and
              metadata.get('board_sha256') == native['board_sha256'] and metadata.get('native_version') == '10.0.6' and
              metadata.get('source_unchanged') is True and metadata.get('PCB_or_route_model_mutated') is False and
              metadata.get('refill_performed') is False and metadata.get('support_graph_or_power_qualification') is False,
              'Stale or unreviewed exact native primitive sidecar')
    b.require(metadata.get('original_pad_inner_outer_contours_exactly_reproduced') is True and
              metadata.get('raw_custom_source_geometry_exactly_reproduced') is True,
              'Exact source/native primitive equality missing')
    if native_sha is not None:
        b.require(metadata.get('native_sha256') == native_sha, 'Primitive sidecar native byte identity differs')
    required = {uid: (net, key) for net, rows in scope['pad_inventory'].items() for uid, key in rows.items()}
    b.require(set(metadata['pads']) == set(required), 'Primitive physical pad UUID coverage differs')
    actual = {obj['uuid']: obj for obj in native['objects'] if obj['kind'] == 'pad'}
    b.require(len(actual) == sum(obj['kind'] == 'pad' for obj in native['objects']), 'Duplicate native pad UUID')
    for uid, (net, key) in required.items():
        obj, row = actual[uid], metadata['pads'][uid]
        b.require(row['uuid'] == uid and row['key'] == key == obj['key'] and row['net'] == net == obj['net'],
                  'Primitive actual pad UUID/name/net differs')
        b.require(row['position_IU'] == point(obj['xy']) and row['absolute_angle_degrees'] == obj['angle'] and
                  row['footprint_uuid'] == obj['footprint_uuid'] and row['plated'] == obj['plated'] and
                  row['npth'] == obj['npth'] and row['barrel_layers'] == obj['barrel_layers'],
                  'Primitive actual pad pose/plating differs')
        angle = Decimal(str(row['absolute_angle_degrees']))
        b.require(angle.is_finite() and angle % 90 == 0, 'Unsupported nonorthogonal actual pad angle')
        b.require(rotation_quarters(row['official_integer_rotation_matrix_columns']) == (-int(angle / 90)) % 4,
                  'Native integer transform disagrees with actual pad angle')
        source_drill = obj.get('drill')
        expected_drill = None if source_drill is None else {k: source_drill[k] for k in ['start', 'end', 'width']}
        b.require(row['actual_drill_primitive_mm'] == expected_drill, 'Actual pad drill primitive differs')
        b.require(set(row['layers']) == set(obj['copper']), 'Primitive actual copper layer coverage differs')
        for layer, data in row['layers'].items():
            b.require(SHAPE_CODES.get(data['shape']) == data['shape_code'] == obj['shape_by_layer'][layer] and
                      data['size_IU'] == point(obj['size']) and data['offset_IU'] == point(obj['offset']) == [0, 0] and
                      data['copper_center_IU'] == row['position_IU'] and data['original_inner_and_outer_contours_reproduced'] is True,
                      'Primitive actual layer shape/offset/center differs')
    return actual


def pad_bounds(row, layer):
    info = row['layers'][layer]
    center, size = info['copper_center_IU'], info['size_IU']
    q = rotation_quarters(row['official_integer_rotation_matrix_columns'])
    if info['shape'] != 'custom':
        b.require(info['custom'] is None, 'Standard pad unexpectedly declares custom primitives')
        packet = primitive.pad(center, size, info['shape'], q, info['corner_radius_IU'], BUDGET_IU)
        return contour(packet['inner_IU']), contour(packet['outer_IU']), packet
    custom = info['custom']
    b.require(custom and custom['exact_source_primitive_equality'] is True and
              custom['anchor_center_IU'] == center and custom['anchor_size_IU'] == size,
              'Custom source/anchor binding differs')
    anchor_kind = {'rect': 'rectangle', 'circle': 'circle'}.get(custom['anchor_shape'])
    b.require(anchor_kind is not None and custom['anchor_shape_code'] == {'rect': 1, 'circle': 0}.get(custom['anchor_shape']),
              'Unsupported or inconsistent native custom anchor')
    anchor = primitive.pad(center, size, anchor_kind, q, None, BUDGET_IU)
    raw = []
    b.require(len(custom['raw_primitives']) == 1, 'Unsupported custom primitive inventory')
    for item in custom['raw_primitives']:
        b.require(item['type'] == 'filled_polygon' and item['width_IU'] == 0 and item['filled'] is True and
                  item['native_merged_polygon_equals_exact_stored_polygon'] is True,
                  'Unknown/stroked/unfilled custom primitive')
        local = item['native_merged_pad_local_IU']
        world = item['native_world_IU']
        b.require(len(local) == len(world) == 1 and not local[0]['holes'] and not world[0]['holes'],
                  'Unsupported custom polygon outline/hole inventory')
        b.require(same_ring(item['raw_PCB_source_pad_local_IU'], local[0]['outer']),
                  'Exact stored custom polygon differs from native merged polygon')
        b.require(all(type(v) is int for ring in [item['raw_PCB_source_pad_local_IU'], local[0]['outer'], world[0]['outer']]
                      for p in ring for v in p), 'Custom geometry is not native integer IU')
        predicted = [[center[0]+primitive.rotate(tuple(p), q)[0], center[1]+primitive.rotate(tuple(p), q)[1]]
                     for p in local[0]['outer']]
        b.require(predicted == world[0]['outer'] and all(type(v) is int for p in predicted for v in p),
                  'Custom exact native world transform differs')
        # Raw custom polygons are intended source geometry. They are not replaced
        # by ideal curved pads or by a convex hull. The separate real anchor is
        # included with its own proved bounds, even if containment is inconclusive.
        graph.geometry(world)
        raw.extend(copy.deepcopy(world))
    return raw + contour(anchor['inner_IU']), raw + contour(anchor['outer_IU']), anchor


def drill_bound(obj):
    drill = obj.get('drill')
    if not drill:
        return None
    b.require(obj['kind'] in {'pad', 'via'}, 'Unexpected physical-hole owner')
    packet = primitive.capsule(point(drill['start']), point(drill['end']), iu(drill['width']), BUDGET_IU)
    return {'start': point(drill['start']), 'end': point(drill['end']), 'width': iu(drill['width']),
            'inside': contour(packet['inner_IU']), 'outside': contour(packet['outer_IU']),
            'analytic_bound': packet['schema']}


def derived_objects(native, scope, metadata):
    """Build separately labelled analytic geometry; raw inputs are never changed."""
    result, all_holes, counts = [], [], defaultdict(int)
    for obj in native['objects']:
        hole = drill_bound(obj)
        if hole:
            all_holes.append({'uuid': obj['uuid'], 'kind': obj['kind'], 'npth': obj.get('npth', False),
                              'plated': obj.get('plated', False), 'barrel_layers': obj.get('barrel_layers', []), 'drill': hole})
        if obj['net'] not in scope['pad_inventory']:
            continue
        row = {key: copy.deepcopy(obj[key]) for key in ['uuid', 'kind', 'net']}
        for key in ['key', 'number', 'npth', 'plated', 'barrel_layers']:
            if key in obj:
                row[key] = copy.deepcopy(obj[key])
        row.update(copper={}, inside={}, drill=hole, derived_model=MODEL, coordinates='native_integer_IU')
        for layer in obj['copper']:
            if obj['kind'] == 'pad':
                b.require(obj['uuid'] in metadata['pads'], 'A scoped pad lacks exact native metadata')
                inner, outer, packet = pad_bounds(metadata['pads'][obj['uuid']], layer)
            elif obj['kind'] == 'track':
                packet = primitive.capsule(point(obj['start']), point(obj['end']), iu(obj['width_by_layer'][layer]), BUDGET_IU)
                inner, outer = contour(packet['inner_IU']), contour(packet['outer_IU'])
            elif obj['kind'] == 'copper_polygon':
                inner, outer, packet = exact_native4_polygon.bounds(obj, layer)
            elif obj['kind'] == 'via':
                packet = primitive.capsule(point(obj['xy']), point(obj['xy']), iu(obj['width_by_layer'][layer]), BUDGET_IU)
                inner, outer = contour(packet['inner_IU']), contour(packet['outer_IU'])
            else:
                raise b.Refused('Unsupported analytic native conductor: ' + obj['kind'])
            row['inside'][layer], row['copper'][layer] = inner, outer
            counts[obj['kind'] + '_layer_bounds'] += 1
        result.append(row)
    return result, all_holes, dict(counts)


def audit_native(native, scope, *, metadata, native_sha=None, fixture=False):
    b.require(not sys.flags.optimize, 'Nonoptimized support implementation required')
    if fixture:
        b.require(native.get('fixture_only') is True and len(native['objects']) <= 64 and
                  len(scope['pad_inventory']) <= 4 and len(native['zones']) <= 8,
                  'Fixture limits exclude a full-board audit')
    else:
        b.require(PRODUCTION_EXECUTION_ENABLED, 'Conservative full-board support is disabled pending an explicit owner control lease and review')
    return _audit_native_verified(native, scope, metadata=metadata, native_sha=native_sha, fixture=fixture)


def _audit_native_verified(native, scope, *, metadata, native_sha=None, fixture=False):
    graph.native_header(native)
    before = b.digest(native)
    validate_metadata(native, scope, metadata, native_sha)
    actual = b.pad_inventory(native, scope['pad_inventory'])
    b.require(actual == scope['pad_inventory'], 'Required actual source pad inventory differs')
    all_uuids = [obj['uuid'] for obj in native['objects']] + [zone['uuid'] for zone in native['zones']]
    b.require(len(all_uuids) == len(set(all_uuids)), 'Duplicate native object/zone UUID')
    material = graph.exact_board_material({'edge_cuts': [{**edge, 'start': point(edge['start']), 'end': point(edge['end'])}
                                                        for edge in native['edge_cuts']]})
    objects, holes, counts = derived_objects(native, scope, metadata)
    drill_voids, all_drills = graph.global_drills({'objects': holes, 'copper_layers': native['copper_layers']})
    rows, returns = {}, {}
    for net in sorted(scope['pad_inventory']):
        conductors = [obj for obj in objects if obj['net'] == net]
        for zone in native['zones']:
            if zone['rule'] or zone['net'] != net:
                continue
            b.require(set(zone['filled']) <= set(zone['layers']), 'Saved fill layer inventory differs')
            copper = {layer: contours_to_IU(polygons) for layer, polygons in zone['filled'].items()}
            conductors.append({'uuid': zone['uuid'], 'kind': 'zone', 'net': net, 'copper': copper,
                               'inside': copper, 'drill': None, 'plated': False, 'barrel_layers': [],
                               'derived_model': 'exact_saved_native_fill_integer_IU'})
        groups = graph.physical_groups(conductors, native['copper_layers'], material, drill_voids, all_drills)
        pad_groups = []
        for group in groups:
            pads = {node['object']['uuid']: node['object']['key'] for node in group
                    if node['object']['kind'] == 'pad' and node['object'].get('number')}
            if not pads:
                continue
            witnesses = [{'uuid': uid, 'layer': layer} for uid, layer in sorted({(node['object']['uuid'], node['layer'])
                         for node in group if node['object']['kind'] == 'zone' and net == 'GND'})]
            pad_groups.append({'pad_uuids': sorted(pads), 'pad_identity': pads, 'saved_plane_witnesses': witnesses,
                               'object_layer_witnesses': sorted({(node['object']['uuid'], node['layer']) for node in group})})
            for uid, layers in scope['required_return_uuids'].items():
                if uid not in pads:
                    continue
                result = returns.setdefault(uid, {'component_count': 0, 'reaches_saved_planes': True, 'saved_plane_witnesses': []})
                result['component_count'] += 1
                result['reaches_saved_planes'] &= bool(witnesses) and set(layers) <= {w['layer'] for w in witnesses}
                result['saved_plane_witnesses'].extend(witnesses)
        observed = [uid for group in pad_groups for uid in group['pad_uuids']]
        complete = len(pad_groups) == 1 and len(observed) == len(set(observed)) and set(observed) == set(actual[net])
        rows[net] = {'complete': complete, 'pad_group_count': len(pad_groups), 'groups': pad_groups,
                     'physical_pad_count': len(actual[net]),
                     'failure_interpretation': None if complete else 'Conservative topology inconclusive; no physical disconnect demonstrated'}
    for uid in scope['required_return_uuids']:
        result = returns.setdefault(uid, {'component_count': 0, 'reaches_saved_planes': False, 'saved_plane_witnesses': []})
        result['reaches_saved_planes'] &= result['component_count'] == 1
    b.require(b.digest(native) == before, 'Raw source data mutated during derivation')
    gates = dict.fromkeys(b.SUPPORT_GATES, True)
    gates['all_required_groups_complete'] = all(row['complete'] for row in rows.values())
    gates['required_returns_reach_saved_planes'] = all(row['reaches_saved_planes'] for row in returns.values())
    return {'schema': MODEL, 'passed': all(gates.values()), 'gates': gates, 'board_sha256': native['board_sha256'],
            'native_sha256': native_sha, 'nets': rows, 'required_returns': returns, 'counts': counts,
            'physical_holes_included': len(holes), 'all_holes_remove_copper_irrespective_of_net': True,
            'source_native_contours_unchanged': True, 'original_raw_bound_failure_preserved': True,
            'geometry_coordinates': 'integer native IU in GEOS; 1 IU = 0.000001 mm',
            'contact_epsilon_IU': 0, 'primitive_error_budget_IU': BUDGET_IU, 'fixture_only': fixture,
            'method': 'Proved analytic primitive inner copper and outer drill bounds; exact stored custom polygons and saved fill; actual board clipping; real supported barrels only; no buffer, epsilon, repair or package edges.',
            'final_source': False, 'numerical_acceptance_claimed': False, 'electrical_acceptance_claimed': False,
            'full_width_annular_reference_and_power_qualification': False}
