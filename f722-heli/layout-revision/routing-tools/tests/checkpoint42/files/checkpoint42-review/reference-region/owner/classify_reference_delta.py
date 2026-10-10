#!/usr/bin/env python3
"""Source-bound, read-only classification for the complete candidate39 source.

This intentionally does not change the older review helper's equality rule.
No tolerance, snapping, normalization, polygon repair, or short-piece filter.
Run from the rebuild root with PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=python-deps.
"""
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

import shapely
from shapely.geometry import LineString, Point, Polygon, mapping
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / 'repo/f722-heli/layout-revision/signal-review/native'
sys.path.insert(0, str(NATIVE))
from compare_reference_geometry import load, compare
from check_signal_geometry import CRITICAL, I2C, centerline, copper_entries, poly, validate_bindings
from check_critical_reference import REFERENCE, PLANES, ground_geometry, local_masks, drill_layers

BEFORE = ROOT / 'ordinary-routing/candidate38/f722-heli.kicad_pcb'
AFTER = ROOT / 'ordinary-routing/candidate39/f722-heli.kicad_pcb'
BS = ROOT / 'checkpoint44-review/snapshot'
AS = ROOT / 'ordinary-routing/candidate39/reference-snapshot'
COMPARISON = ROOT / 'ordinary-routing/candidate39/reference-comparison-to38.json'
EXPECTED = {
    BEFORE: '95bb984bf046fef2d96c6e59d9e00696f504d35f89e3340fdf076cd7c9249c9f',
    AFTER: '246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7',
}
WINDOW_FIELDS = ['via_uuid', 'via_xy_mm', 'local_window_radius_mm',
                 'nominal_land_radius_mm', 'via_own_clearance_mm',
                 'maximum_ground_zone_clearance_mm', 'classification_allowance_mm']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def atoms(geometry):
    if geometry.is_empty:
        return []
    if hasattr(geometry, 'geoms'):
        return [p for g in geometry.geoms for p in atoms(g)]
    return [geometry]


def describe(geometry):
    require(geometry.is_valid, 'Invalid geometry; no repair permitted')
    return {'geometry_type': geometry.geom_type, 'empty': geometry.is_empty,
            'length_mm': geometry.length, 'area_mm2': geometry.area,
            'bounds_mm': None if geometry.is_empty else list(geometry.bounds),
            'pieces': [{'geometry': mapping(p), 'length_mm': p.length,
                        'area_mm2': p.area, 'bounds_mm': list(p.bounds)}
                       for p in atoms(geometry)]}


def window(fact):
    # Exactly the existing window construction, including its pre-existing
    # allowance. No new allowance is introduced here.
    return Point(fact['via_xy_mm']).buffer(fact['local_window_radius_mm'], quad_segs=96)


def same_window(before, after):
    require(all(before[k] == after[k] for k in WINDOW_FIELDS), 'Own-via window changed')
    require(window(before).equals(window(after)), 'Own-via window geometry changed')


def check_binding(actual, expected):
    require(actual == expected, 'Board/source hash mismatch')


def contained(geometry, mask):
    remaining = geometry.difference(mask)
    return remaining.is_empty, remaining


def main():
    global BEFORE, AFTER, BS, AS, COMPARISON, EXPECTED
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before-board', type=Path, default=BEFORE)
    parser.add_argument('--after-board', type=Path, default=AFTER)
    parser.add_argument('--before-snapshot', type=Path, default=BS)
    parser.add_argument('--after-snapshot', type=Path, default=AS)
    parser.add_argument('--comparison', type=Path, default=COMPARISON)
    parser.add_argument('--expected-before-sha256', default=EXPECTED[BEFORE])
    parser.add_argument('--expected-after-sha256', default=EXPECTED[AFTER])
    parser.add_argument('--out', type=Path, default=Path(__file__).with_name('reference-classification.json'))
    args = parser.parse_args()
    BEFORE, AFTER = args.before_board.resolve(), args.after_board.resolve()
    BS, AS = args.before_snapshot.resolve(), args.after_snapshot.resolve()
    COMPARISON = args.comparison.resolve()
    EXPECTED = {BEFORE: args.expected_before_sha256, AFTER: args.expected_after_sha256}
    require(all(p.is_relative_to(ROOT) for p in [BEFORE, AFTER, BS, AS, COMPARISON]),
            'Source paths must remain inside the assigned rebuild workspace')
    require(args.out.resolve().parent == Path(__file__).resolve().parent,
            'Outputs must stay in this isolated review directory')
    paths = list(EXPECTED) + [COMPARISON, Path(__file__)]
    paths += [p / name for p in (BS, AS) for name in
              ('native-geometry.json', 'native-signals.json', 'critical-reference.json')]
    paths += [NATIVE / name for name in ('check_signal_geometry.py', 'check_critical_reference.py',
                                       'compare_reference_geometry.py', 'review_reference_window_change.py')]
    paths += [ROOT / 'checkpoint49-review/reference-change-review.json']
    paths += sorted((ROOT / 'ordinary-routing/servo23-reference-review').glob('*'))
    require(all(p.is_file() for p in paths), 'Expected source or preserved partial artifact missing')
    original_hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    for p, expected in EXPECTED.items():
        check_binding(sha(p), expected)
    B, A = load(BS, BEFORE), load(AS, AFTER)
    bg, bm, br = B
    ag, am, ar = A
    computed = compare(B, A)
    provided = json.loads(COMPARISON.read_text())
    require({k: v for k, v in provided.items() if k != 'sources'} == computed,
            'Provided comparison does not exactly equal recomputation')
    require(computed['critical_object_geometry_identical'], 'Critical copper objects changed')
    require(provided['sources']['before_report'] == sha(BS / 'critical-reference.json') and
            provided['sources']['after_report'] == sha(AS / 'critical-reference.json') and
            provided['sources']['compare_reference_geometry.py'] == sha(NATIVE / 'compare_reference_geometry.py'),
            'Comparison source binding mismatch')
    _, bz, bp, bc = ground_geometry(bg, copper_entries(bg))
    _, az, ap, ac = ground_geometry(ag, copper_entries(ag))
    bmask, bfacts, bholes = local_masks(bg, bm, bz)
    amask, afacts, aholes = local_masks(ag, am, az)
    target_nets = set(CRITICAL) | set(I2C)
    bo = {o['uuid']: o for o in bg['objects']}
    ao = {o['uuid']: o for o in ag['objects']}
    keys = [k for k in bmask if bo[k[0]]['net'] in target_nets]
    require(set(keys) == {k for k in amask if ao[k[0]]['net'] in target_nets}, 'Critical window keys changed')
    for k in keys:
        same_window(bfacts[k], afacts[k])
        require(bo[k[0]] == ao[k[0]], 'Source own-via object changed')
    plane_deltas = {l: {'added_missing': bp[l].difference(ap[l]),
                        'removed_missing': ap[l].difference(bp[l])} for l in PLANES}
    reports = [{t['track_uuid']: t for t in report['tracks']} for report in (br, ar)]
    require(set(reports[0]) == set(reports[1]), 'Critical report track set changed')
    rows, used_keys, hole_evidence = [], set(), {}

    def classify(geometry, own_keys, layer):
        raw_windows = unary_union([window(bfacts[k]) for k in own_keys])
        actual_masks = unary_union([m[k] for k in own_keys for m in (bmask, amask)])
        in_windows, outside_windows = contained(geometry, raw_windows)
        in_actual, outside_actual = contained(geometry, actual_masks)
        relationships = []
        if not geometry.is_empty:
            for k in own_keys:
                if not geometry.intersects(window(bfacts[k])):
                    continue
                used_keys.add(k)
                detail = {'via_uuid': k[0], 'reference_layer': k[1],
                          'window': {f: bfacts[k][f] for f in WINDOW_FIELDS},
                          'whole_geometry_inside_window': geometry.difference(window(bfacts[k])).is_empty,
                          'before_holes': [], 'after_holes': []}
                for state, facts, holes, graph in [('before', bfacts, bholes, bg), ('after', afacts, aholes, ag)]:
                    for hf in facts[k]['saved_holes']:
                        h = holes[layer][hf['hole_index']]
                        outside_hole = geometry.difference(h)
                        detail[state + '_holes'].append({
                            **hf, 'geometry_wkb_sha256': hashlib.sha256(h.wkb).hexdigest(),
                            'whole_geometry_covered_by_hole': h.covers(geometry),
                            'difference_from_hole_empty': outside_hole.is_empty,
                            'intersection_length_mm': geometry.intersection(h).length,
                            'intersection_area_mm2': geometry.intersection(h).area,
                            'outside_hole_length_mm': outside_hole.length,
                            'outside_hole_area_mm2': outside_hole.area,
                        })
                        evidence_key = f'{state}:{layer}:{hf["hole_index"]}'
                        hole_evidence[evidence_key] = {'facts': hf, 'geometry': describe(h)}
                relationships.append(detail)
        drill_hits = {}
        for state, graph in [('before', bg), ('after', ag)]:
            drill_hits[state] = [
                {'uuid': o['uuid'], 'net': o['net'], 'kind': o['kind'],
                 'drill_width_mm': o['drill']['width'],
                 'intersection': describe(geometry.intersection(poly(o['drill']['outside'])))}
                for o in graph['objects'] if layer in drill_layers(o, graph['copper_layers'])
                and not geometry.is_empty and geometry.intersects(poly(o['drill']['outside']))]
        windows_cover = geometry.is_empty or raw_windows.covers(geometry)
        masks_cover = geometry.is_empty or actual_masks.covers(geometry)
        return {**describe(geometry), 'difference_from_unchanged_own_windows_empty': in_windows,
                'difference_from_before_or_after_actual_hole_window_intersections_empty': in_actual,
                'unchanged_own_windows_cover_geometry': windows_cover,
                'before_or_after_actual_hole_window_intersections_cover_geometry': masks_cover,
                'exact_containment_predicates_agree': in_windows == windows_cover and in_actual == masks_cover,
                'actual_hole_window_mask_relation': None if geometry.is_empty else actual_masks.relate(geometry),
                'outside_unchanged_windows': describe(outside_windows),
                'outside_actual_hole_window_intersections': describe(outside_actual),
                'window_and_hole_relationships': relationships, 'actual_drill_intersections': drill_hits}

    for uid in reports[0]:
        t = bo[uid]
        require(t == ao[uid], 'Critical native track changed')
        l = next(iter(t['copper']))
        r = REFERENCE[l]
        own_keys = [k for k in keys if k[1] == r and bo[k[0]]['net'] == t['net']]
        for kind, source in [('centerline', centerline(t)), ('trace_width', poly(t['copper'][l]))]:
            missing_b, missing_a = source.difference(bp[r]), source.difference(ap[r])
            physical = {direction: source.intersection(change)
                        for direction, change in plane_deltas[r].items()}
            direct = {'added_missing': missing_a.difference(missing_b),
                      'removed_missing': missing_b.difference(missing_a)}
            if missing_b.equals(missing_a) and all(x.is_empty for x in physical.values()):
                continue
            field = 'physical_GND_centerline_missing_mm' if kind == 'centerline' else 'physical_GND_trace_width_missing_mm2'
            measure = 'length' if kind == 'centerline' else 'area'
            # Independently verify every recomputed native total exactly. Do not
            # infer equality from serialized class pieces, which apply filters.
            require(getattr(missing_b, measure) == reports[0][uid][field] and
                    getattr(missing_a, measure) == reports[1][uid][field], 'Track metric differs from source report')
            rows.append({'track_uuid': uid, 'net': t['net'], 'signal_layer': l, 'reference_layer': r,
                         'kind': kind, 'source_track_start_mm': t['start'], 'source_track_end_mm': t['end'],
                         'source_track_width_mm': t['width'],
                         'before_missing_measure': getattr(missing_b, measure),
                         'after_missing_measure': getattr(missing_a, measure),
                         'report_total_delta': reports[1][uid][field] - reports[0][uid][field],
                         'missing_geometries_exactly_equal': missing_b.equals(missing_a),
                         'physical_plane_change_projection': {d: classify(x, own_keys, r) for d, x in physical.items()},
                         'direct_missing_geometry_overlay': {d: classify(x, own_keys, r) for d, x in direct.items()},
                         'physical_projection_signed_measure': getattr(physical['added_missing'], measure) - getattr(physical['removed_missing'], measure),
                         'direct_overlay_signed_measure': getattr(direct['added_missing'], measure) - getattr(direct['removed_missing'], measure)})

    plane_summary = {}
    for layer, deltas in plane_deltas.items():
        all_windows = unary_union([window(bfacts[k]) for k in keys if k[1] == layer])
        plane_summary[layer] = {
            'physical_GND_lost_mm2': deltas['added_missing'].area,
            'physical_GND_gained_mm2': deltas['removed_missing'].area,
            'lost_GND_outside_all_unchanged_critical_own_windows_mm2': deltas['added_missing'].difference(all_windows).area,
            'gained_GND_outside_all_unchanged_critical_own_windows_mm2': deltas['removed_missing'].difference(all_windows).area,
            'scope': 'Whole-plane changes are real and are not approved by critical-projection window classification.'}
    classifications = [v for row in rows for method in ('physical_plane_change_projection', 'direct_missing_geometry_overlay')
                       for v in row[method].values()]
    all_window_residuals_empty = all(v['difference_from_unchanged_own_windows_empty'] for v in classifications)
    all_hole_residuals_empty = all(v['difference_from_before_or_after_actual_hole_window_intersections_empty'] for v in classifications)
    all_window_contained = all_window_residuals_empty and all(v['unchanged_own_windows_cover_geometry'] for v in classifications)
    all_hole_contained = all_hole_residuals_empty and all(v['before_or_after_actual_hole_window_intersections_cover_geometry'] for v in classifications)
    controls = []

    def expect_rejection(name, action):
        try:
            action()
        except ValueError as error:
            controls.append({'control': name, 'rejected': True, 'reason': str(error)})
            return
        raise ValueError('Rejection control accepted: ' + name)

    expect_rejection('wrong expected source hash', lambda: check_binding(sha(BEFORE), sha(AFTER)))
    altered = copy.deepcopy(bm)
    altered['geometry_sha256'] = am['geometry_sha256']
    expect_rejection('cross-bound snapshot geometry', lambda: validate_bindings(bg, altered, sha(BS / 'native-geometry.json'), sha(BEFORE)))
    mosi_key = ('743f60f6-99d7-40af-8adc-c8e9b0542c93', 'In1.Cu')
    changed_fact = copy.deepcopy(afacts[mosi_key])
    changed_fact['local_window_radius_mm'] *= 2
    expect_rejection('expanded own-via window', lambda: same_window(bfacts[mosi_key], changed_fact))
    valid_mask = unary_union([bmask[mosi_key], amask[mosi_key]])
    outside_line = LineString([[21.25, 10.425], [21.25, 10.435]])
    outside_width = Polygon([[21.245, 10.42], [21.255, 10.42], [21.255, 10.43], [21.245, 10.43]])
    for name, shape in [('merged-hole outside-own-window centerline', outside_line),
                        ('merged-hole outside-own-window width', outside_width)]:
        hole = bholes['In1.Cu'][bfacts[mosi_key]['saved_holes'][0]['hole_index']]
        require(hole.covers(shape), 'Control geometry must be in the same actual merged hole')
        expect_rejection(name, lambda s=shape: require(contained(s, valid_mask)[0], 'Changed geometry outside unchanged own window'))
    only_window = window(bfacts[mosi_key])
    require(not only_window.difference(valid_mask).is_empty, 'A missing-hole control region must exist')
    expect_rejection('window area without actual saved hole', lambda: require(contained(only_window.difference(valid_mask), valid_mask)[0], 'Changed geometry outside actual hole mask'))
    disagreements = [v for v in classifications if not v['exact_containment_predicates_agree']]
    if disagreements:
        expect_rejection('empty residual cannot override conflicting exact covers predicate',
                         lambda: require(all_hole_contained, 'Exact actual-hole containment unresolved'))

    require(original_hashes == {str(p.relative_to(ROOT)): sha(p) for p in paths}, 'Source changed during classification')
    result = {
        'schema': 'f722-candidate39-exact-source-extended-reference-classification/v1',
        'before_board_sha256': sha(BEFORE), 'after_board_sha256': sha(AFTER),
        'source_hashes': original_hashes, 'shapely_version': shapely.__version__,
        'geos_version': shapely.geos_version_string,
        'source_binding_verified': True, 'critical_copper_identical': True,
        'unchanged_critical_own_via_windows_verified': True,
        'critical_reference_tracks_examined': len(reports[0]),
        'missing_centerline_geometries_exactly_equal': all(row['missing_geometries_exactly_equal'] for row in rows if row['kind'] == 'centerline'),
        'all_changed_critical_projection_geometry_inside_unchanged_own_windows': all_window_contained,
        'all_changed_critical_projection_geometry_inside_actual_hole_window_intersections': all_hole_contained,
        'all_changed_critical_projection_residuals_outside_unchanged_own_windows_empty': all_window_residuals_empty,
        'all_changed_critical_projection_residuals_outside_actual_hole_window_intersections_empty': all_hole_residuals_empty,
        'exact_containment_predicate_disagreement_count': len(disagreements),
        'classification_status': ('CONTAINED_REFERENCE_REGION_ONLY' if all_window_contained and all_hole_contained else
                                  'UNRESOLVED_ACTUAL_HOLE_BOUNDARY_PREDICATES' if disagreements else 'OUTSIDE_WINDOW'),
        'own_window_location_classification': 'VERIFIED' if all_window_contained else 'UNRESOLVED_OR_OUTSIDE_WINDOW',
        'receipt_scope': 'Fresh source-bound reference-region review of the complete candidate39 board; no overall board adoption or functional signoff.',
        'final_adoption': False, 'old_receipt_reusable_as_is': False,
        'changed_critical_regions': rows,
        'numeric_differences_retained': computed['net_numeric_deltas_after_minus_before'],
        'whole_plane_changes': plane_summary,
        'actual_saved_hole_geometry': hole_evidence,
        'rejection_controls': controls,
        'method': [
            'Verify exact declared board, snapshot, report, comparison and helper hashes before and after this read-only run.',
            'Rebuild saved physical GND from actual zone/land/track polygons minus native outside-drill polygons on their actual layer spans.',
            'Primary changed projection is original source centerline or trace copper intersected with before-minus-after or after-minus-before physical GND.',
            'Also preserve direct subtraction of independently clipped missing geometries. Non-collinear floating-point line representations may produce entire before/after intervals; those results are retained and classified separately.',
            'Both methods must leave empty residual geometry outside unchanged same-net windows and before-or-after actual saved-hole intersections. Entire merged holes receive no exemption.',
            'Containment also checks the exact covers predicate. Empty difference does not override a conflicting covers result; predicate disagreement remains unresolved.',
            'Every nonempty geometry is retained. No epsilon, rounding, snapping, polygon repair, filtering, or normalization to zero is introduced.'
        ],
        'limits': [
            'This is a fresh location classification for the complete candidate39 source, not overall board adoption, functional signoff, or exact centerline equality.',
            'The existing helper and checkpoint49 receipt require exact centerline equality and cannot be reused as-is.',
            'Floating-point overlay lengths/areas and subtraction of totals differ by retained nonzero amounts; no equality claim is made between those alternative computations.',
            'The MOSI added centerline and width results have empty difference from the actual-hole masks but false covers results. This strict boundary-containment disagreement is unresolved, not accepted.',
            'Whole-plane changes outside critical own-via windows remain real and need separate source-bound power/VCAP and functional assessment.',
            'This receipt binds the complete candidate39 source; any later successor or changed board must repeat the source-bound comparison and classification on its own hash.',
            'No KiCad refill, native board mutation, FEM, impedance, return-current, timing, fabrication or flight qualification was performed.'
        ]}
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['classification_status', 'missing_centerline_geometries_exactly_equal',
          'all_changed_critical_projection_geometry_inside_unchanged_own_windows',
          'all_changed_critical_projection_geometry_inside_actual_hole_window_intersections',
          'all_changed_critical_projection_residuals_outside_actual_hole_window_intersections_empty',
          'exact_containment_predicate_disagreement_count',
          'critical_reference_tracks_examined', 'whole_plane_changes', 'rejection_controls']}, indent=2))


if __name__ == '__main__':
    main()
