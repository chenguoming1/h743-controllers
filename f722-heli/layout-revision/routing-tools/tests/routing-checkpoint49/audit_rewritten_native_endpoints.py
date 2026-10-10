#!/usr/bin/env python3
"""Read-only endpoint and actual-annulus audit of native object additions."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT.parent / 'python-deps'))
from shapely import unary_union
from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geom(polygons):
    parts = [Polygon(p['outer'], p.get('holes', [])) for p in polygons]
    assert all(p.is_valid for p in parts)
    result = unary_union(parts)
    assert result.is_valid
    return result


def linear_parts(geometry):
    if geometry.geom_type == 'LineString':
        return [geometry] if geometry.length > 1e-9 else []
    if hasattr(geometry, 'geoms'):
        return [p for g in geometry.geoms for p in linear_parts(g)]
    return []


def section_at(center, normal, half_width):
    return LineString([(center[0] - normal[0] * half_width, center[1] - normal[1] * half_width),
                       (center[0] + normal[0] * half_width, center[1] + normal[1] * half_width)])


def annular_sections(track, actual, error):
    start, end = track['start'], track['end']
    line = LineString([start, end])
    length = line.length
    direction = [(end[0] - start[0]) / length, (end[1] - start[1]) / length]
    normal = [-direction[1], direction[0]]
    half = track['width'] / 2
    witnesses = []
    intervals = linear_parts(line.intersection(actual))
    for interval in intervals:
        choices = []
        for fraction in [.25, .5, .75]:
            point = interval.interpolate(fraction, normalized=True)
            xy = list(point.coords[0])
            section = section_at(xy, normal, half)
            full = section.difference(actual).length <= 1e-8
            margin = section.distance(actual.boundary) if full else 0
            if not full or margin <= error:
                continue
            # A finite full-width strip, not merely a centerline or zero-length point.
            axial = min(.01, margin, interval.length * .1)
            aa = [xy[i] - direction[i] * axial / 2 for i in range(2)]
            bb = [xy[i] + direction[i] * axial / 2 for i in range(2)]
            sec_a = list(section_at(aa, normal, half).coords)
            sec_b = list(section_at(bb, normal, half).coords)
            rectangle = Polygon([sec_a[0], sec_a[1], sec_b[1], sec_b[0]])
            rectangle_missing = rectangle.difference(actual).area
            if rectangle_missing > 1e-12:
                continue
            choices.append({'section_center_mm': xy,
                            'section_mm': list(section.coords),
                            'section_width_mm': section.length,
                            'full_width_actual_annulus_section': True,
                            'section_to_actual_annulus_boundary_mm': margin,
                            'full_width_strip_length_mm': axial,
                            'full_width_strip_polygon_mm': list(rectangle.exterior.coords),
                            'strip_area_outside_actual_annulus_mm2': rectangle_missing,
                            'centerline_actual_copper_interval_mm': list(interval.coords),
                            'centerline_actual_copper_interval_length_mm': interval.length})
        if choices:
            witnesses.append(max(choices, key=lambda x: x['section_to_actual_annulus_boundary_mm']))
    return witnesses, line.intersection(actual).length


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--rewrite-receipt', type=Path, required=True)
    args = ap.parse_args()
    source, candidate = args.source.resolve(), args.candidate.resolve()
    paths = [d / name for d in [source, candidate]
             for name in ['f722-heli.kicad_pcb', 'f722-heli.native.json']]
    hashes = {str(p): sha(p) for p in paths}
    before = json.loads((source / 'f722-heli.native.json').read_text())
    after = json.loads((candidate / 'f722-heli.native.json').read_text())
    assert before['board_sha256'] == hashes[str(source / 'f722-heli.kicad_pcb')]
    assert after['board_sha256'] == hashes[str(candidate / 'f722-heli.kicad_pcb')]
    prior = {o['uuid']: o for o in before['objects']}
    current = {o['uuid']: o for o in after['objects']}
    added = [o for uid, o in current.items() if uid not in prior]
    changed = [uid for uid in prior if uid in current and prior[uid] != current[uid]]
    removed = sorted(set(prior) - set(current))
    error = after['maximum_polygon_error_mm']
    import sys
    sys.path.insert(0, str(ROOT))
    from validate_ordinary_rewrite import validate
    allowed, rewrite = validate(before, after, args.rewrite_receipt, sha(source / 'f722-heli.native.json'))
    nets = sorted({o['net'] for o in added})
    pad_results, via_results, unresolved, classified_via_endpoints, redundant, incidental = [], [], [], [], [], []
    per_net = {}
    for net in nets:
        objects = [o for o in after['objects'] if o['net'] == net]
        tracks = [o for o in objects if o['kind'] == 'track']
        pads = [o for o in objects if o['kind'] == 'pad']
        vias = [o for o in objects if o['kind'] == 'via']
        new_tracks = [o for o in tracks if o['uuid'] not in prior or o['uuid'] in allowed]
        new_vias = [o for o in vias if o['uuid'] not in prior or o['uuid'] in allowed]
        degree = collections.Counter((layer, tuple(track[key])) for track in tracks
                                     for layer in track['copper'] for key in ['start', 'end'])
        pad_geometries = {(pad['uuid'], layer): geom(polygons)
                          for pad in pads for layer, polygons in pad['inside'].items()}
        via_geometries = {(via['uuid'], layer): geom(polygons)
                          for via in vias for layer, polygons in via['copper'].items()}
        for track in new_tracks:
            for layer in track['copper']:
                for key, other in [('start', 'end'), ('end', 'start')]:
                    xy, q = track[key], track[other]
                    if degree[(layer, tuple(xy))] != 1:
                        continue
                    point = Point(xy)
                    half = track['width'] / 2
                    near_vias = [via for via in vias if layer in via['copper']
                                 and via_geometries[via['uuid'], layer].distance(point) <= half + error]
                    if near_vias:
                        classified_via_endpoints.append({'net': net, 'track_uuid': track['uuid'],
                                                        'endpoint': key, 'xy_mm': xy, 'layer': layer,
                                                        'via_uuids': [v['uuid'] for v in near_vias],
                                                        'classification': 'via_endpoint_not_a_pad_termination'})
                        continue
                    choices = [pad for pad in pads if layer in pad['copper']]
                    if not choices:
                        unresolved.append({'net': net, 'track_uuid': track['uuid'], 'endpoint': key,
                                           'xy_mm': xy, 'layer': layer, 'reason': 'No pad or via on layer'})
                        continue
                    pad = min(choices, key=lambda p: pad_geometries[p['uuid'], layer].distance(point))
                    inside = pad_geometries[pad['uuid'], layer]
                    drilled = bool((pad.get('drill') or {}).get('outside'))
                    actual = inside.difference(geom(pad['drill']['outside'])) if drilled else inside
                    length = math.dist(xy, q)
                    normal = [-(q[1] - xy[1]) / length, (q[0] - xy[0]) / length]
                    section = section_at(xy, normal, half)
                    full = section.difference(actual).length <= 1e-8
                    # Match endpoint_witness for SMDs; subtract drilled voids for actual copper.
                    entry = LineString([xy, q]).intersection(actual.buffer(-(half + .000001)))
                    passed = entry.length > 0 if drilled else inside.contains(point) and full
                    transverse_entry = None
                    if not drilled:
                        # Every audited SMD pad is convex. For a convex polygon,
                        # containing both transverse endpoints contains the whole section.
                        assert actual.convex_hull.difference(actual).area < 1e-12
                        guarded = actual.buffer(-.000001)
                        allowed = translate(guarded, normal[0] * half, normal[1] * half).intersection(
                            translate(guarded, -normal[0] * half, -normal[1] * half))
                        transverse_entry = LineString([xy, q]).intersection(allowed)
                        passed = passed and transverse_entry.length > 0
                    pad_results.append({'net': net, 'track_uuid': track['uuid'], 'layer': layer,
                                        'endpoint': key, 'xy_mm': xy, 'other_end_mm': q,
                                        'pad': pad['key'], 'pad_uuid': pad['uuid'],
                                        'trace_width_mm': track['width'],
                                        'centerline_inside_native_pad': inside.contains(point),
                                        'centerline_to_actual_copper_gap_mm': actual.distance(point),
                                        'centerline_depth_inside_native_pad_mm': point.distance(inside.boundary)
                                        if inside.contains(point) else 0,
                                        'actual_copper_section_mm': list(section.coords),
                                        'actual_copper_section_overlap_mm': section.intersection(actual).length,
                                        'actual_copper_section_missing_mm': section.difference(actual).length,
                                        'full_width_actual_copper_termination': full,
                                        'native_track_actual_pad_overlap_mm2': geom(track['copper'][layer]).intersection(actual).area,
                                        'drill_void_subtracted': drilled,
                                        'full_width_annular_entry_length_mm': entry.length if drilled else None,
                                        'full_width_transverse_entry_length_mm': transverse_entry.length if transverse_entry is not None else None,
                                        'full_width_transverse_entry_wkt': transverse_entry.wkt if transverse_entry is not None else None,
                                        'transverse_entry_extra_inward_reserve_mm': .000001,
                                        'physical_entry_passed': passed})
        for via in new_vias:
            layers = []
            drill = geom(via['drill']['outside'])
            for layer, outer in [(layer, via_geometries[via['uuid'], layer]) for layer in via['copper']]:
                # Via export has ERROR_OUTSIDE copper, so contract inward by its stated error.
                conservative_outer = outer.buffer(-error)
                actual = conservative_outer.difference(drill)
                contacts = []
                for track in tracks:
                    if layer not in track['copper']:
                        continue
                    track_copper = geom(track['copper'][layer])
                    if track_copper.distance(outer) > error:
                        continue
                    witnesses, center_overlap = annular_sections(track, actual, error)
                    covered = track_copper.difference(outer).area <= 1e-12
                    line = LineString([track['start'], track['end']])
                    wholly_drill_centerline = drill.covers(line)
                    contact = {'track_uuid': track['uuid'], 'start_mm': track['start'],
                               'end_mm': track['end'], 'length_mm': line.length,
                               'trace_width_mm': track['width'],
                               'actual_annulus_overlap_mm2': track_copper.intersection(actual).area,
                               'centerline_actual_annulus_length_mm': center_overlap,
                               'full_width_actual_annulus_witnesses': witnesses,
                               'full_width_actual_annulus_passed': bool(witnesses),
                               'centerline_wholly_in_drill_void': wholly_drill_centerline,
                               'track_copper_wholly_within_existing_via_disk': covered}
                    if not witnesses and covered and wholly_drill_centerline:
                        contact['classification'] = 'redundant_buried_spur_not_annular_entry_evidence'
                        redundant.append({'net': net, 'via_uuid': via['uuid'], 'layer': layer, **contact})
                    elif witnesses:
                        contact['classification'] = 'verified_full_width_annular_contact'
                    else:
                        contact['classification'] = 'unverified_or_sliver_via_contact'
                    contacts.append(contact)
                if contacts:
                    verified = [c for c in contacts if c['full_width_actual_annulus_passed']]
                    for contact in contacts:
                        if contact['classification'] != 'unverified_or_sliver_via_contact':
                            continue
                        endpoints = {tuple(contact['start_mm']), tuple(contact['end_mm'])}
                        continuations = []
                        for target in verified:
                            common = endpoints & {tuple(target['start_mm']), tuple(target['end_mm'])}
                            if common and contact['trace_width_mm'] == target['trace_width_mm']:
                                continuations.append({'verified_track_uuid': target['track_uuid'],
                                                      'shared_centerline_endpoint_mm': sorted(common),
                                                      'equal_full_trace_width_mm': target['trace_width_mm']})
                        if continuations:
                            contact['classification'] = 'incidental_side_overlap_continues_to_verified_annular_entry'
                            contact['full_width_path_continuations'] = continuations
                            incidental.append({'net': net, 'via_uuid': via['uuid'], 'layer': layer, **contact})
                        else:
                            unresolved.append({'net': net, 'via_uuid': via['uuid'], 'layer': layer, **contact})
                    layers.append({'layer': layer, 'contacts': contacts,
                                   'full_width_actual_annular_entry_passed': any(c['full_width_actual_annulus_passed'] for c in contacts)})
            verified_layers = [row['layer'] for row in layers if row['full_width_actual_annular_entry_passed']]
            passed = len(verified_layers) >= 2 and all(row['full_width_actual_annular_entry_passed'] for row in layers)
            via_results.append({'net': net, 'via_uuid': via['uuid'], 'xy_mm': via['xy'],
                                'drill_mm': via['drill']['width'], 'width_by_layer_mm': via['width_by_layer'],
                                'drill_void_subtracted': True, 'outer_polygon_inward_reserve_mm': error,
                                'contact_layers': layers, 'verified_contact_layers': verified_layers,
                                'physical_layer_transfer_passed': passed})
        per_net[net] = {'reviewed_tracks': len(new_tracks), 'reviewed_vias': len(new_vias),
                        'total_native_tracks': len(tracks),
                        'new_pad_termination_count': sum(r['net'] == net for r in pad_results),
                        'scope': 'No additions to audit' if not new_tracks and not new_vias else 'New and explicitly rewritten-net source entries; full net connectivity remains separate'}
    failures = [r for r in pad_results if not r['physical_entry_passed']]
    via_failures = [r for r in via_results if not r['physical_layer_transfer_passed']]
    assert all(sha(Path(p)) == expected for p, expected in hashes.items())
    passed = not (failures or via_failures or unresolved or changed)
    report = {'status': 'PASS_WITH_REDUNDANT_VIA_SPUR' if passed and redundant else 'PASS' if passed else 'FAIL',
              'passed': passed, 'source_hashes': {str(Path(p).relative_to(ROOT.parent)): h for p, h in hashes.items()},
              'source_board_sha256': before['board_sha256'], 'candidate_board_sha256': after['board_sha256'],
              'audit_script_sha256': sha(Path(__file__)),
              'method': 'SMD checks follow endpoint_witness: native ERROR_INSIDE interior and complete transverse endpoint section. Vias are evaluated separately on actual annulus: conservative native outer polygon contracted by export error, minus native ERROR_OUTSIDE drill void. A finite full-width strip on each contacted layer proves annular entry; a point in the drill or endcap-only sliver does not. Buried redundant spurs are not counted as contact evidence.',
              'source_object_count': len(prior), 'candidate_object_count': len(current),
              'existing_object_records_unchanged': not changed and not removed,
              'ordinary_rewrite': rewrite,
              'changed_existing_object_uuids': changed, 'removed_object_uuids': removed,
              'added_objects': [{'uuid': o['uuid'], 'kind': o['kind'], 'net': o['net']} for o in added],
              'per_net': per_net, 'pad_terminations': pad_results,
              'via_endpoints_classified_separately': classified_via_endpoints,
              'via_annular_contacts': via_results, 'redundant_via_spurs': redundant,
              'incidental_via_side_overlaps_not_used_as_entry_evidence': incidental,
              'summary': {
                  'pad_terminations_verified': len(pad_results) - len(failures),
                  'minimum_positive_pad_depth_mm': min((r['centerline_depth_inside_native_pad_mm'] for r in pad_results), default=None),
                  'minimum_full_width_pad_transverse_entry_length_mm': min((r['full_width_transverse_entry_length_mm'] for r in pad_results if r['full_width_transverse_entry_length_mm'] is not None), default=None),
                  'full_width_actual_annular_strip_count': sum(len(c['full_width_actual_annulus_witnesses']) for v in via_results for l in v['contact_layers'] for c in l['contacts']),
                  'minimum_full_width_annular_strip_length_mm': min((w['full_width_strip_length_mm'] for v in via_results for l in v['contact_layers'] for c in l['contacts'] for w in c['full_width_actual_annulus_witnesses']), default=None),
                  'minimum_annular_section_boundary_reserve_mm': min((w['section_to_actual_annulus_boundary_mm'] for v in via_results for l in v['contact_layers'] for c in l['contacts'] for w in c['full_width_actual_annulus_witnesses']), default=None),
                  'redundant_via_spurs_retained_as_non_evidence': len(redundant),
                  'incidental_side_overlaps_not_used_as_entry_evidence': len(incidental),
              },
              'pad_failures': failures, 'via_failures': via_failures, 'unresolved_contacts': unresolved,
              'source_recheck_unchanged': True,
              'limits': ['This checks new and explicitly permitted rewritten-net source endpoints and contacts, not full routing completion.',
                         'Saved GND fills may change in the parent refill; fixed native object UUIDs and records are compared here.',
                         'Nominal geometry only; native DRC/process/connectivity remain separate owner gates.']}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'pad_termination_count': len(pad_results),
                      'new_via_count': len(via_results), 'unresolved_contacts': len(unresolved),
                      'redundant_spurs': [r['track_uuid'] for r in redundant],
                      'per_net': per_net, 'summary': report['summary'], 'report': str(args.out)}, indent=2))


if __name__ == '__main__':
    main()
