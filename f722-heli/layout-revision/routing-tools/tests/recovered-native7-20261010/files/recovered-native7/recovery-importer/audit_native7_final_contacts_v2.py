#!/usr/bin/env python3
"""Separate, fail-closed native contact audit. Import and --check-inputs are geometry-free.

An actual board audit needs a separately hash-bound owner job lease. Synthetic
tests may exercise the pure geometry helpers on fabricated shapes only. No
native API, routing, contour repair, simplification, or native file mutation.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import datetime as dt
import importlib.metadata
import math
from pathlib import Path

import import_native7_incremental_v1 as imp

IMPORTER_SHA = 'cf783fd61fd229927f89aa2741d88500d598a445f306ab1031fca9ef49232653'
LEDGER_SHA = 'f321cb2ea9aff2dc601f7b762ac09c03b6f95d286d634ee2140692726d91b450'
PACKET_SHA = 'b161ae1c4df8632c38bea543c4ddb07e5dcb67afd734f86ef4d931cc1584a051'
SCOPE_SHA = 'b70b00911dbcade6e97470d6a5cb593a122b20af1dcc4672e00711c107f61534'
PROTECTED = {'PORT_C_RX_EXT', 'PORT_C_TX_EXT'}
FILES = {'source_native', 'final_native', 'candidate_board', 'plan', 'provenance',
         'role_sidecar', 'historical_ledger', 'common_packet', 'C_scope', 'source_logical_map'}
STAGE = 'final_native_contact_audit'
REQUIRED_NETS = {'FLASH_SCK', 'FLASH_MISO', 'FLASH_MOSI', 'FLASH_CS', 'PORT_B_RX_MCU',
                 'PORT_B_TX_MCU', 'PORT_C_RX_MCU', 'PORT_C_TX_MCU', 'PORT_C_RX_EXT',
                 'PORT_C_TX_EXT', 'DSM_RX_MCU', 'IMU_CS', 'LED_GREEN_K', 'VX_PROTECTED'}


def validate_role_sidecar(sidecar, plan, plan_sha, provenance):
    imp.exact_keys(sidecar, ['schema', 'source', 'plan_sha256', 'recipes'], 'protected role sidecar')
    imp.require(sidecar['schema'] == 'f722-native7-protected-role-sidecar/v1' and
                sidecar['source'] == plan['source'] and sidecar['plan_sha256'] == plan_sha,
                'Protected sidecar source/plan mismatch')
    expected = {r['name']: r for r in plan['added_copper'] if r['net'] in PROTECTED}
    actual = imp.unique(sidecar['recipes'], key='name')
    imp.require(set(actual) == set(expected), 'Missing/extra protected recipe roles')
    for name, row in actual.items():
        imp.exact_keys(row, ['name', 'net', 'logical_net', 'role'], 'protected role recipe')
        imp.require(row['role'] in ('upstream', 'downstream') and
                    all(row[k] == expected[name][k] for k in ('name', 'net', 'logical_net')),
                    'Protected recipe role/identity mismatch: ' + name)
    return {row['uuid']: actual[row['name']]['role'] for row in provenance['recipe_to_native_UUIDs']
            if row['name'] in actual}


def load_bound_inputs(request_path):
    """Hashes and JSON identities only. Does not import Shapely or load CAD."""
    request = imp.read(request_path)
    imp.exact_keys(request, ['schema', 'files'], 'contact audit request')
    imp.require(request['schema'] == 'f722-native7-final-contact-request/v1' and
                set(request['files']) == FILES, 'Missing/extra contact evidence files')
    imp.require(imp.sha(imp.__file__) == IMPORTER_SHA, 'Frozen importer dependency changed')
    data = {}
    for name, binding in request['files'].items():
        imp.exact_keys(binding, ['path', 'sha256'], 'evidence file binding')
        path = Path(binding['path'])
        imp.require(path.is_absolute() and path.is_file() and imp.sha(path) == binding['sha256'],
                    'Missing or changed bound evidence: ' + name)
        if name != 'candidate_board':
            data[name] = imp.read(path)
    expected_pins = {'source_native': imp.SOURCE_BINDINGS['native_sha256'],
                     'source_logical_map': imp.SOURCE_BINDINGS['logical_map_sha256'],
                     'historical_ledger': LEDGER_SHA, 'common_packet': PACKET_SHA, 'C_scope': SCOPE_SHA}
    for name, expected in expected_pins.items():
        imp.require(request['files'][name]['sha256'] == expected, 'Wrong frozen evidence: ' + name)
    source, final, plan, proof = (data[n] for n in ('source_native', 'final_native', 'plan', 'provenance'))
    ledger, packet, scope = (data[n] for n in ('historical_ledger', 'common_packet', 'C_scope'))
    imp.require(plan['source'] == imp.SOURCE_BINDINGS and plan['schema'] == imp.PLAN_SCHEMA, 'Wrong native7 plan')
    imp.require(data['source_logical_map']['board_sha256'] == imp.SOURCE_BINDINGS['board_sha256'], 'Stale source logical map')
    imp.validate_plan(plan, source, data['source_logical_map']['logical_route_map'])
    imp.require(source['board_sha256'] == imp.SOURCE_BINDINGS['board_sha256'], 'Stale source native export')
    imp.require(proof['schema'] == 'f722-native7-incremental-import-receipt/v1' and
                proof['status'] == 'CONSTRUCTION_VERIFIED_NOT_ACCEPTED' and proof['acceptance_claimed'] is False and
                proof['importer_sha256'] == IMPORTER_SHA and proof['source'] == imp.SOURCE_BINDINGS,
                'Missing exact construction provenance')
    for field, name in [('plan_sha256', 'plan'), ('native_sha256', 'final_native'), ('board_sha256', 'candidate_board')]:
        imp.require(proof[field] == request['files'][name]['sha256'], 'Construction binding mismatch: ' + field)
    imp.require(final['board_sha256'] == proof['board_sha256'] and final['native_build'] == source['native_build'] == '10.0.6+dfsg-1',
                'Final native board/build mismatch')
    imp.require(final['maximum_polygon_error_mm'] == source['maximum_polygon_error_mm'] == .00001,
                'Unexpected native polygon error bound')
    old, now = imp.unique(source['objects']), imp.unique(final['objects'])
    removed = imp.unique([r['record'] for r in plan['removed_native_records']])
    imp.require(len(removed) == 90 and set(removed) == set(packet['removed_native_ids']), 'Must retain the exact 90-cut joint scope')
    for row in plan['removed_native_records']:
        record = row['record']
        imp.require(record['uuid'] in old and record == old[record['uuid']] and
                    row['full_record_sha256'] == imp.record_sha(record) and record['kind'] in ('track', 'via', 'arc'),
                    'Source removal record/hash mismatch')
    imp.require(set(old) - set(now) == set(removed), 'Final removals differ')
    imp.require(all(now[uid] == old[uid] for uid in set(old) & set(now)), 'Undeclared retained native change')
    imp.require(source['footprints'] == final['footprints'], 'Final footprint inventory changed')
    for key in ('copper_layers', 'copper_layer_ids', 'edge_cuts', 'outline_with_npth', 'board_thickness_mm'):
        imp.require(source[key] == final[key], 'Undeclared native board change: ' + key)
    source_zones, final_zones = imp.unique(source['zones']), imp.unique(final['zones'])
    imp.require(set(source_zones) == set(final_zones), 'Native zone inventory changed')
    metadata = lambda z: {k: v for k, v in z.items() if k not in ('filled', 'fill_representation')}
    imp.require(all(metadata(source_zones[uid]) == metadata(final_zones[uid]) for uid in source_zones), 'Native zone outlines/metadata changed')
    recipes = imp.unique(plan['added_copper'], key='name')
    mappings = imp.unique(proof['recipe_to_native_UUIDs'])
    expected = {}
    for recipe in recipes.values():
        indices = range(len(recipe['points']) - 1) if recipe['kind'] == 'track' else [None]
        for index in indices:
            uid = imp.native_uuid(proof['plan_sha256'], recipe['name'], index)
            expected[uid] = (recipe['name'], index)
    imp.require(set(expected) == set(mappings) == set(now) - set(old), 'Incomplete final recipe-to-UUID mapping')
    added_records = imp.unique(proof['added_native_records'])
    imp.require(set(added_records) == set(expected), 'Incomplete new native records in provenance')
    for uid, (name, index) in expected.items():
        row = mappings[uid]
        imp.require(row['name'] == name and row['segment_index'] == index and
                    row['full_record_sha256'] == imp.record_sha(now[uid]) and added_records[uid] == now[uid],
                    'Native recipe mapping/record mismatch: ' + uid)
    imp.require(ledger['packet_sha256'] == PACKET_SHA and ledger['native_cut_count'] == 90 and
                sum(r['new_required_merges'] for r in ledger['nets']) == 9, 'Historical restoration ledger mismatch')
    imp.require(scope['native_binding']['sha256'] == imp.SOURCE_BINDINGS['native_sha256'], 'Protected source scope mismatch')
    roles = validate_role_sidecar(data['role_sidecar'], plan, proof['plan_sha256'], proof)
    protected_source = {uid for uid, row in old.items() if row['net'] in PROTECTED}
    imp.require(protected_source == set(scope['protected_branch_role_metadata']), 'Incomplete protected source-role inventory')
    data.update(request=request, source_records=old, final_records=now, added_ids=set(expected), added_roles=roles)
    return data


def validate_lease(path, request_path, output):
    lease = imp.read(path)
    imp.exact_keys(lease, ['schema', 'active', 'owner', 'lease_id', 'stage', 'request_sha256',
                            'validator_sha256', 'output_path', 'issued_utc', 'expires_utc'], 'contact-audit lease')
    imp.require(lease['schema'] == 'f722-native7-contact-audit-owner-lease/v1' and lease['active'] is True and
                lease['stage'] == STAGE and lease['request_sha256'] == imp.sha(request_path) and
                lease['validator_sha256'] == imp.sha(__file__) and lease['output_path'] == str(output),
                'No exact owner contact-audit job permission')
    imp.require(all(isinstance(lease[k], str) and lease[k].strip() for k in ('owner', 'lease_id')), 'Lease owner/ID missing')
    issued, expires = [dt.datetime.fromisoformat(lease[k].replace('Z', '+00:00')) for k in ('issued_utc', 'expires_utc')]
    imp.require(issued.tzinfo is not None and expires.tzinfo is not None and
                issued <= dt.datetime.now(dt.timezone.utc) < expires and expires - issued <= dt.timedelta(hours=2),
                'Contact-audit lease expired/future/unbounded')
    return lease


def geometry_modules():
    from shapely.geometry import Polygon, LineString, Point
    from shapely.ops import unary_union
    from shapely.strtree import STRtree
    return Polygon, LineString, Point, unary_union, STRtree


def polygon_parts(shape):
    if shape.is_empty:
        return []
    if shape.geom_type == 'Polygon':
        return [shape]
    return [p for child in getattr(shape, 'geoms', ()) for p in polygon_parts(child)]


def native_polygons(rows):
    Polygon, _, _, unary_union, _ = geometry_modules()
    shapes = [Polygon(row['outer'], row.get('holes', [])) for row in rows]
    imp.require(all(p.is_valid and not p.is_empty and p.area > 0 for p in shapes), 'Invalid/degenerate native polygon; no repair permitted')
    return unary_union(shapes)


def hole_map(records, copper_layers):
    """A physical drill removes copper from every intersecting object/net."""
    _, _, _, unary_union, _ = geometry_modules()
    rows = defaultdict(list)
    for record in records:
        if not record.get('drill'):
            continue
        hole = native_polygons(record['drill']['outside'])
        layers = copper_layers if record.get('npth') else record.get('barrel_layers', [])
        imp.require(bool(layers), 'Drilled object lacks physical drill-layer evidence')
        for layer in layers:
            rows[layer].append(hole)
    return {layer: unary_union(shapes) for layer, shapes in rows.items()}


def conductive_shapes(record, global_holes=None):
    """Boolean drill subtraction only; original native contours remain untouched."""
    hole = native_polygons(record['drill']['outside']) if record.get('drill') else None
    copper = {layer: native_polygons(rows) for layer, rows in record['copper'].items() if rows}
    shapes = {layer: shape.difference(hole) if hole is not None else shape for layer, shape in copper.items()}
    if global_holes:
        shapes = {layer: shape.difference(global_holes[layer]) if layer in global_holes else shape
                  for layer, shape in shapes.items()}
    imp.require(all(p.is_valid for p in shapes.values()), 'Invalid drill-subtracted native geometry')
    return shapes, hole


def partition_native(records, *, subtract_region=None, omit_ids=frozenset(), global_holes=None):
    """Positive-area lateral edges; vertical edges require a declared physical barrel.

    A disconnected copper island on a plated object is not automatically bonded
    to its other layers: it must touch a nonzero-length part of the drill boundary.
    """
    _, _, _, _, STRtree = geometry_modules()
    if global_holes is None:
        layers = {layer for row in records for layer in row['copper']}
        global_holes = hole_map(records, layers)
    nodes, by_layer, by_barrel = [], defaultdict(list), defaultdict(list)
    shapes_by_id, holes = {}, {}
    for record in records:
        uid = record['uuid']
        if uid in omit_ids:
            continue
        shapes, hole = conductive_shapes(record, global_holes)
        holes[uid] = hole
        if subtract_region:
            shapes = {layer: shape.difference(subtract_region[layer]) if layer in subtract_region else shape
                      for layer, shape in shapes.items()}
        shapes_by_id[uid] = shapes
        for layer, shape in shapes.items():
            for index, polygon in enumerate(polygon_parts(shape)):
                pos = len(nodes)
                nodes.append({'uuid': uid, 'layer': layer, 'fragment': index, 'shape': polygon})
                by_layer[layer].append(pos)
                if record.get('plated') is True and hole is not None and layer in record.get('barrel_layers', []):
                    contact_length = polygon.boundary.intersection(hole.boundary).length
                    if contact_length > 0:
                        by_barrel[uid].append(pos)
    parent = list(range(len(nodes)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def join(a, b):
        parent[find(a)] = find(b)
    contacts = {}
    for layer, indices in by_layer.items():
        tree = STRtree([nodes[i]['shape'] for i in indices])
        for local, i in enumerate(indices):
            for j0 in tree.query(nodes[i]['shape'], predicate='intersects'):
                if int(j0) <= local:
                    continue
                j = indices[int(j0)]
                area = nodes[i]['shape'].intersection(nodes[j]['shape']).area
                if area > 0:
                    join(i, j)
                    a, b = sorted((nodes[i]['uuid'], nodes[j]['uuid']))
                    if a != b:
                        key = (a, b, layer)
                        contacts[key] = contacts.get(key, 0) + area
    for positions in by_barrel.values():
        for position in positions[1:]:
            join(positions[0], position)
    groups, memberships = defaultdict(set), defaultdict(set)
    for i, node in enumerate(nodes):
        root = find(i)
        groups[root].add(node['uuid'])
        memberships[node['uuid']].add(root)
    return {'groups': list(groups.values()), 'memberships': memberships, 'contacts': contacts,
            'shapes': shapes_by_id, 'holes': holes}


def line_parts(shape):
    if shape.is_empty:
        return []
    if shape.geom_type in ('LineString', 'LinearRing'):
        return [shape]
    return [p for child in getattr(shape, 'geoms', ()) for p in line_parts(child)]


def full_width_witness(track, own_shape, peer_shape, layer, error_mm, *, at_endpoint=None):
    """Measure contiguous native copper coverage of a normal width section.

    Candidate sections use exact native centerline endpoints and midpoints of
    its exact conductive-overlap intervals. No contour is buffered or snapped.
    Annular intervals are already drill-subtracted by the caller.
    """
    _, LineString, Point, _, _ = geometry_modules()
    imp.require(track['kind'] == 'track', 'A straight native track is required for a width witness')
    a, b, width = track['start'], track['end'], track['width']
    length = math.dist(a, b)
    imp.require(length > 0 and width > 2 * error_mm, 'Degenerate track width/length')
    line = LineString([a, b])
    overlap = own_shape.intersection(peer_shape)
    points = [at_endpoint] if at_endpoint is not None else [a, b]
    if at_endpoint is None:
        for part in line_parts(line.intersection(overlap)):
            if part.length > 0:
                points.append(list(part.interpolate(.5, normalized=True).coords[0]))
    nx, ny = -(b[1] - a[1]) / length, (b[0] - a[0]) / length
    best = None
    for point in points:
        if point is None or not overlap.covers(Point(point)):
            continue
        section = LineString([(point[0] - nx * width / 2, point[1] - ny * width / 2),
                              (point[0] + nx * width / 2, point[1] + ny * width / 2)])
        spans = line_parts(section.intersection(overlap))
        covered = max((span.length for span in spans), default=0.)
        witness = {'point': list(point), 'layer': layer, 'section': list(map(list, section.coords)),
                   'nominal_track_width_mm': width, 'native_contiguous_covered_width_mm': covered,
                   'exporter_two_boundary_tolerance_mm': 2 * error_mm,
                   'error_adjusted_width_lower_bound_mm': max(0., covered - 2 * error_mm),
                   'positive_overlap_area_mm2': overlap.area,
                   'passed': overlap.area > 0 and covered >= width - 2 * error_mm}
        if best is None or covered > best['native_contiguous_covered_width_mm']:
            best = witness
    return best or {'layer': layer, 'nominal_track_width_mm': width, 'native_contiguous_covered_width_mm': 0.,
                    'positive_overlap_area_mm2': overlap.area, 'passed': False, 'reason': 'No finite full-width section found'}


def unchanged_primary_witness(primary, branch_witness, layer, partition,
                              source_records, source_partition, error_mm):
    """Prove an unchanged wider primary continues through a narrower branch join.

    This is a local native-copper certificate, not a current-capacity claim. A
    retained UUID alone is insufficient: the record and conductive geometry
    must match the source, and a full-width interior strip must survive on both
    sides of the join. Endpoint joins cannot use this exception.
    """
    Polygon, LineString, Point, _, _ = geometry_modules()
    uid = primary['uuid']
    original = source_records.get(uid)
    record_equal = original == primary
    old_shapes = (source_partition or {}).get('shapes', {}).get(uid, {})
    now_shapes = partition['shapes'][uid]
    shapes_equal = (bool(old_shapes) and set(old_shapes) == set(now_shapes) and
                    all(old_shapes[k].equals(now_shapes[k]) for k in old_shapes))
    result = {'primary_uuid': uid, 'layer': layer, 'nominal_primary_width_mm': primary['width'],
              'source_record_sha256': imp.record_sha(original) if original else None,
              'final_record_sha256': imp.record_sha(primary),
              'exact_native_record_unchanged': record_equal,
              'all_layer_conductive_geometry_unchanged': shapes_equal,
              'passed': False, 'reason': 'Missing unchanged interior primary continuity evidence'}
    if not record_equal or not shapes_equal or not branch_witness.get('passed') or 'point' not in branch_witness:
        return result
    a, b, width = primary['start'], primary['end'], primary['width']
    length = math.dist(a, b)
    if length == 0 or width <= 2 * error_mm:
        return result
    line = LineString([a, b])
    station = line.project(Point(branch_witness['point']))
    half_length = width / 2
    endpoint_margin = min(station, length - station)
    result.update(projected_primary_station_mm=station, primary_length_mm=length,
                  distance_to_nearest_primary_endpoint_mm=endpoint_margin,
                  required_interior_margin_mm=half_length + 2 * error_mm)
    if endpoint_margin <= half_length + 2 * error_mm:
        result['reason'] = 'Join is at or too near a primary endpoint; retain serial width obligation'
        return result
    center = line.interpolate(station)
    x, y = center.x, center.y
    dx, dy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    nx, ny = -dy, dx
    half_width = (width - 2 * error_mm) / 2
    corners = [[x + s * dx * half_length + t * nx * half_width,
                y + s * dy * half_length + t * ny * half_width]
               for s, t in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
    strip = Polygon(corners)
    uncovered = strip.difference(now_shapes[layer]).area
    passed = strip.area > 0 and uncovered == 0
    result.update(native_interior_strip=corners, required_strip_width_mm=2 * half_width,
                  required_strip_length_mm=2 * half_length,
                  exporter_two_boundary_tolerance_mm=2 * error_mm,
                  uncovered_strip_area_mm2=uncovered, passed=passed,
                  reason=None if passed else 'Primary full-width interior strip is not continuous')
    return result


def boundary_witnesses(records, partition, contact_ids, error_mm, *, moving_ids=None,
                       source_records=(), source_partition=None):
    """Enumerate selected contacts, attributing width obligations independently.

    ``contact_ids`` selects rows; ``moving_ids`` contains only new or actually
    changed geometry. Omitting moving_ids audits both sides as a raw baseline.
    """
    by = {r['uuid']: r for r in records}
    source_by = {r['uuid']: r for r in source_records}
    moving_ids = set(contact_ids) if moving_ids is None else set(moving_ids)
    rows = []
    for (left, right, layer), area in sorted(partition['contacts'].items()):
        if left not in contact_ids and right not in contact_ids:
            continue
        choices = [by[uid] for uid in (left, right) if by[uid]['kind'] == 'track']
        moving = [r for r in choices if r['uuid'] in moving_ids]
        required = moving or choices
        sections = []
        def add_section(track, obligation):
            peer = right if track['uuid'] == left else left
            sections.append({'track_uuid': track['uuid'], 'peer_uuid': peer,
                             'width_obligation': obligation,
                             **full_width_witness(track, partition['shapes'][track['uuid']][layer],
                                                  partition['shapes'][peer][layer], layer, error_mm)})
        for track in required:
            add_section(track, 'new_or_geometrically_affected_track' if track in moving else 'retained_or_baseline_track')
        primary_proofs = []
        if moving:
            for primary in choices:
                if primary['uuid'] in moving_ids:
                    continue
                narrower = [s for s in sections if s['nominal_track_width_mm'] + 2 * error_mm < primary['width']]
                proofs = [dict(unchanged_primary_witness(primary, section, layer, partition, source_by,
                                                        source_partition, error_mm),
                               joining_track_uuid=section['track_uuid']) for section in narrower]
                primary_proofs.extend(proofs)
                if proofs and not all(p['passed'] for p in proofs):
                    # A narrow serial replacement cannot masquerade as an
                    # unchanged branch merely because a donor UUID survived.
                    add_section(primary, 'wider_retained_track_without_unchanged_interior_continuity')
        annular = []
        if not sections:
            for uid, peer in ((left, right), (right, left)):
                record = by[uid]
                hole = partition['holes'][uid]
                if hole is None or record.get('plated') is not True or layer not in record.get('barrel_layers', []):
                    continue
                land = partition['shapes'][uid][layer]
                uncovered = land.difference(partition['shapes'][peer][layer]).area
                annular.append({'barrel_uuid': uid, 'peer_uuid': peer, 'layer': layer,
                                'native_annular_area_mm2': land.area, 'uncovered_annular_area_mm2': uncovered,
                                'passed': land.area > 0 and uncovered == 0,
                                'method': 'Entire actual drill-subtracted land covered by peer native copper'})
        passed = all(r['passed'] for r in sections) if sections else any(r['passed'] for r in annular)
        rows.append({'left_uuid': left, 'right_uuid': right, 'layer': layer, 'positive_overlap_area_mm2': area,
                     'drill_subtraction_applied': partition['holes'][left] is not None or partition['holes'][right] is not None,
                     'witnesses': sections, 'full_annular_witnesses': annular, 'passed': passed,
                     'moving_track_UUIDs': sorted(r['uuid'] for r in moving),
                     'unchanged_primary_continuity_witnesses': primary_proofs,
                     'missing_evidence_reason': None if passed else 'No complete track-width section or full-annular-coverage proof'})
    return rows


def compare_contact_findings(records, graph, source_records, source_graph, affected_ids, error_mm):
    """Keep raw source, changed final, and unchanged inherited findings separate."""
    old_rows = boundary_witnesses(source_records, source_graph, set(source_graph['shapes']), error_mm)
    old_by_pair = {(r['left_uuid'], r['right_uuid'], r['layer']): r for r in old_rows}
    final_rows = boundary_witnesses(records, graph, set(graph['shapes']), error_mm,
                                   moving_ids=affected_ids, source_records=source_records,
                                   source_partition=source_graph)
    boundaries, inherited = [], []
    for row in final_rows:
        if {row['left_uuid'], row['right_uuid']} & affected_ids:
            boundaries.append(dict(row, classification='new_or_geometrically_affected_contact'))
        else:
            old_row = old_by_pair.get((row['left_uuid'], row['right_uuid'], row['layer']))
            imp.require(old_row is not None, 'Unchanged contact lacks source comparison evidence')
            inherited.append({'classification': 'unchanged_inherited_contact',
                              'source_native_finding': old_row, 'final_native_finding': row,
                              'inherited_limitation_still_unresolved': not row['passed'],
                              'treated_as_new_regression': False, 'waived': False})
    return old_rows, boundaries, inherited


def endpoint_witnesses(plan, provenance, records, partition, error_mm):
    """Both exterior ends of each full polyline need physical support.

    Via/PTH-center endpoints use drill-subtracted annular sections along their
    adjacent native segment, rather than falsely counting copper in the hole.
    """
    by = {r['uuid']: r for r in records}
    mapping = {(r['name'], r['segment_index']): r['uuid'] for r in provenance['recipe_to_native_UUIDs']}
    rows = []
    for recipe in plan['added_copper']:
        if recipe['kind'] != 'track' or mapping[(recipe['name'], 0)] not in by:
            continue
        own_recipe_ids = {uid for (name, index), uid in mapping.items() if name == recipe['name']}
        for index, point in [(0, recipe['points'][0]), (len(recipe['points']) - 2, recipe['points'][-1])]:
            uid = mapping[(recipe['name'], index)]
            track, layer = by[uid], recipe['layer']
            witnesses = []
            for peer_uid, peer in by.items():
                if peer_uid in own_recipe_ids or peer['net'] != recipe['net'] or layer not in partition['shapes'].get(peer_uid, {}):
                    continue
                peer_hole = partition['holes'][peer_uid]
                _, _, Point, _, _ = geometry_modules()
                in_hole = peer_hole is not None and peer_hole.covers(Point(point))
                witness = full_width_witness(track, partition['shapes'][uid][layer], partition['shapes'][peer_uid][layer],
                                             layer, error_mm, at_endpoint=None if in_hole else point)
                if witness['passed']:
                    witnesses.append({'peer_uuid': peer_uid, 'annular_endpoint': in_hole, **witness})
            rows.append({'recipe_name': recipe['name'], 'native_segment_uuid': uid, 'endpoint': point,
                         'witnesses': witnesses, 'passed': bool(witnesses)})
    return rows


def native_records_with_fills(native):
    rows = list(native['objects'])
    rows.extend({'uuid': z['uuid'], 'net': z['net'], 'kind': 'saved_native_zone',
                 'copper': z['filled'], 'drill': None, 'plated': False, 'barrel_layers': []}
                for z in native['zones'] if not z['rule'] and any(z['filled'].values()))
    return rows


def group_disposition(source_connected, final_connected):
    if source_connected and not final_connected:
        return 'new_positive_area_connectivity_regression'
    if not source_connected and not final_connected:
        return 'inherited_positive_area_limitation_still_unresolved'
    return 'restored_positive_area_connectivity' if not source_connected else 'source_positive_area_connectivity_preserved'


def protected_cut_checks(data, records, error_mm, global_holes):
    """Recheck the actual bonded-pad cut on final native copper using bound roles."""
    _, _, _, unary_union, _ = geometry_modules()
    source_roles = data['C_scope']['protected_branch_role_metadata']
    source = data['source_records']
    rows = []
    for net, bonded, upstream, downstream in [('PORT_C_RX_EXT', 'U15.1', 'J11.1', 'R34.1'),
                                              ('PORT_C_TX_EXT', 'U15.2', 'J11.2', 'R35.1')]:
        objects = [r for r in records if r['net'] == net]
        pads = {r['key']: r for r in objects if r['kind'] == 'pad'}
        imp.require(all(k in pads for k in (bonded, upstream, downstream)), 'Protected actual pad missing')
        cut, _ = conductive_shapes(pads[bonded])
        graph = partition_native(objects, subtract_region=cut, omit_ids={pads[bonded]['uuid']}, global_holes=global_holes)
        membership = graph['memberships']
        disconnected = not membership[pads[upstream]['uuid']].intersection(membership[pads[downstream]['uuid']])
        branches = {'upstream': defaultdict(list), 'downstream': defaultdict(list)}
        for record in objects:
            uid = record['uuid']
            if uid == pads[bonded]['uuid']:
                continue
            role = source_roles[uid]['role'] if uid in source else data['added_roles'].get(uid)
            imp.require(role in branches, 'Missing final protected branch role: ' + uid)
            for layer, shape in graph['shapes'][uid].items():
                if not shape.is_empty:
                    branches[role][layer].append(shape)
        spacing = []
        for layer in sorted(set(branches['upstream']) & set(branches['downstream'])):
            gap = unary_union(branches['upstream'][layer]).distance(unary_union(branches['downstream'][layer]))
            spacing.append({'layer': layer, 'native_outside_pad_gap_mm': gap,
                            'required_gap_mm': .127 + error_mm, 'passed': gap >= .127 + error_mm})
        rows.append({'net': net, 'removed_actual_bonded_pad': bonded, 'no_external_bypass': disconnected,
                     'outside_pad_branch_spacing': spacing,
                     'passed': disconnected and bool(spacing) and all(r['passed'] for r in spacing)})
    return rows


def audit_data(data):
    """Actual full-board geometry; called only after owner-lease validation."""
    imp.require(importlib.metadata.version('shapely') == '2.2.0', 'Use the pinned Shapely 2.2.0 analysis environment')
    error = data['final_native']['maximum_polygon_error_mm']
    final_records = native_records_with_fills(data['final_native'])
    source_records = native_records_with_fills(data['source_native'])
    final_holes = hole_map(final_records, data['final_native']['copper_layers'])
    source_holes = hole_map(source_records, data['source_native']['copper_layers'])
    source_zones = imp.unique(data['source_native']['zones'])
    changed_fills = {z['uuid'] for z in data['final_native']['zones']
                     if z['uuid'] in source_zones and z['filled'] != source_zones[z['uuid']]['filled']}
    nets = (REQUIRED_NETS | {r['net'] for r in data['historical_ledger']['nets']} |
            {r['net'] for r in data['plan']['added_copper']})
    partitions, source_partitions = {}, {}
    boundaries, endpoints, complete_nets, source_findings, inherited_findings = [], [], [], [], []
    affected_ids = set(data['added_ids']) | changed_fills
    for net in sorted(nets):
        rows = [r for r in final_records if r['net'] == net]
        graph = partition_native(rows, global_holes=final_holes)
        partitions[net] = graph
        original_rows = [r for r in source_records if r['net'] == net]
        original = partition_native(original_rows, global_holes=source_holes)
        source_partitions[net] = original
        for uid in set(original['shapes']) & set(graph['shapes']):
            left, right = original['shapes'][uid], graph['shapes'][uid]
            if set(left) != set(right) or any(not left[layer].equals(right[layer]) for layer in left):
                affected_ids.add(uid)
        if net in REQUIRED_NETS:
            complete_nets.append({'net': net, 'positive_area_component_count': len(graph['groups']),
                                  'source_positive_area_component_count': len(original['groups']),
                                  'disposition': group_disposition(len(original['groups']) == 1, len(graph['groups']) == 1),
                                  'passed': len(graph['groups']) == 1})
        old_rows, changed_rows, inherited_rows = compare_contact_findings(
            rows, graph, original_rows, original, affected_ids, error)
        source_findings.extend(dict(row, net=net) for row in old_rows)
        boundaries.extend(dict(row, net=net) for row in changed_rows)
        inherited_findings.extend(dict(row, net=net) for row in inherited_rows)
        endpoints.extend(endpoint_witnesses(data['plan'], data['provenance'], rows, graph, error))
    group_checks = []
    for row in data['historical_ledger']['nets']:
        for index, terminal_ids in enumerate(row['source_terminal_components']):
            def closed(graph):
                memberships = [graph['memberships'].get(uid, set()) for uid in terminal_ids]
                return bool(memberships) and bool(set.intersection(*memberships))
            group_checks.append({'net': row['net'], 'historical_group_index': index,
                                 'all_original_terminal_UUIDs': terminal_ids,
                                 'historical_raw_intersects_group_preserved_unchanged': True,
                                 'source_positive_area_connected': closed(source_partitions[row['net']]),
                                 'final_positive_area_connected': closed(partitions[row['net']]),
                                 'disposition': group_disposition(closed(source_partitions[row['net']]), closed(partitions[row['net']])),
                                 'uses_exact_final_saved_fill': row['net'] == 'GND',
                                 'passed': closed(partitions[row['net']])})
    protected = protected_cut_checks(data, final_records, error, final_holes)
    contact_ids = {uid for row in boundaries if row['passed'] for uid in (row['left_uuid'], row['right_uuid'])}
    added_inventory = [{'uuid': uid, 'has_verified_native_contact': uid in contact_ids, 'passed': uid in contact_ids}
                       for uid in sorted(data['added_ids'])]
    evidence = complete_nets + group_checks + boundaries + endpoints + protected + added_inventory
    return {'schema': 'f722-native7-final-native-contact-audit/v2',
            'contact_and_topology_gate_passed': bool(evidence) and all(r['passed'] for r in evidence),
            'gate_scope': 'Declared new or geometrically affected contacts, all original terminal-group restorations, complete required nets, and final TVS isolation; unchanged inherited width limitations are reported separately and not waived',
            'new_or_affected_full_width_contact_gate_passed': all(r['passed'] for r in boundaries + endpoints + added_inventory),
            'source_board_sha256': imp.SOURCE_BINDINGS['board_sha256'],
            'final_board_sha256': data['final_native']['board_sha256'],
            'bound_evidence': data['request']['files'],
            'historical_raw_ledger_sha256': LEDGER_SHA, 'historical_ledger_modified': False,
            'changed_saved_zone_fill_UUIDs_requiring_new_contact_witnesses': sorted(changed_fills),
            'all_new_or_geometrically_affected_UUIDs': sorted(affected_ids),
            'original_required_restoration_merges': 9, 'all_original_terminal_group_checks': group_checks,
            'all_required_physical_net_checks': complete_nets,
            'all_new_contact_boundary_witnesses': boundaries, 'all_polyline_endpoint_witnesses': endpoints,
            'source_native_contact_findings': source_findings,
            'unchanged_inherited_contact_findings': inherited_findings,
            'unresolved_inherited_contact_limitation_count': sum(r['inherited_limitation_still_unresolved'] for r in inherited_findings),
            'inherited_findings_waived': False, 'whole_board_contact_acceptance_claimed': False,
            'all_new_objects_have_verified_contact': added_inventory,
            'actual_TVS_pad_cut_checks': protected,
            'method': {'same_layer_edges': 'positive native copper overlap area only',
                       'vertical_edges': 'declared plated barrel layers with nonzero drill-boundary contact',
                       'holes': 'subtract exact exported outside physical drill contours from all intersecting copper, including other nets',
                       'width': 'contiguous native section coverage >= declared width minus twice exporter polygon error',
                       'width_attribution': 'actual new/affected tracks; wider retained primary exempted only by exact source record/geometry equality and full-width interior continuity strip',
                       'polygon_error_mm': error, 'contour_repair_simplification_snapping_buffering': False},
            'limitations': ['A positive-area overlap is measured on exported native polygons at their stated error bound.',
                            'Full-width means nominal declared width within the explicitly reported 2e-5 mm two-boundary tolerance.',
                            'Joins without a straight-track width witness require full native annular-land coverage; otherwise they fail as missing evidence.',
                            'The unchanged-primary certificate proves local interior continuity only; primary endpoint joins conservatively retain the wider serial-width obligation. It does not certify network-wide current capacity or serial-width preservation beyond the audited joins.',
                            'This is a contact/topology gate only. It does not establish DRC/clearance, ERC/parity, AC/ESD performance, return/reference quality, thermal/current capacity or manufacturing acceptance.',
                            'Saved final ground fill is checked for DC contact only; no return-path or plane-neck qualification is implied.'],
            'acceptance_claimed': False, 'adoption_claimed': False}


def audit_final_native_contacts(request_path, lease_path, output_path):
    """Public callable API. Write one new report only after exact owner permission."""
    request_path, lease_path, output = map(Path, (request_path, lease_path, output_path))
    imp.require(output.is_absolute() and output == output.resolve() and not output.exists(), 'Use a new absolute report path')
    request_sha, lease_sha = imp.sha(request_path), imp.sha(lease_path)
    data = load_bound_inputs(request_path)
    lease = validate_lease(lease_path, request_path, output)
    report = audit_data(data)
    imp.require(imp.sha(request_path) == request_sha and imp.sha(lease_path) == lease_sha, 'Job inputs changed during audit')
    load_bound_inputs(request_path)
    validate_lease(lease_path, request_path, output)
    report.update(request_sha256=request_sha, validator_sha256=imp.sha(__file__), lease_id=lease['lease_id'])
    imp.write(output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--check-inputs', action='store_true')
    parser.add_argument('--lease', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.check_inputs:
        imp.require(args.lease is None and args.out is None, 'Input-only check takes no lease/output')
        load_bound_inputs(args.request)
        print(imp.canonical({'input_validation_passed': True, 'geometry_run': False, 'acceptance_claimed': False}))
    else:
        imp.require(args.lease is not None and args.out is not None, 'Actual geometry requires --lease and --out')
        report = audit_final_native_contacts(args.request, args.lease, args.out)
        print(imp.canonical({'contact_and_topology_gate_passed': report['contact_and_topology_gate_passed'],
                             'report': str(args.out), 'report_sha256': imp.sha(args.out), 'acceptance_claimed': False}))
        if not report['contact_and_topology_gate_passed']:
            raise SystemExit(2)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise SystemExit(str(error)) from error
