#!/usr/bin/env python3
"""Saved-fill support connectivity and full-width dedicated U12.2 GND return.

Derived from audit_support_connectivity.py. Exactly the sealed 13 replacements
are permitted; the GND via is checked as a plane connection, not an antipad.
Every new signal via retains the 0.127 mm saved-plane gap requirement.
"""
import argparse
import json
import math
from pathlib import Path
import sys

from validate_servo23_stage import (GROUND_ALLOW, ROOT, add_basis_arguments,
    load_for_args, read, recheck, sha)
sys.path.insert(0, str(ROOT / 'native-tools'))
from check_protection_paths import make_graph, geometry, pieces
from audit_rewritten_entries import annular_sections, section_at
from shapely import unary_union
from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon

BASE_SUPPORT_SHA = {'stage37': '2c6fefc49dabf5cf1eafe477dedc78c01f6d82ad07fd9aabb6b106d06f86df31',
                    'stage38': '771bbc06431dc787a5464995360a786212995bfd862f1c7e662f4de18e856a66'}


def objects(native, net):
    return [o for o in native['objects'] if o['net'] == net] + [
        {'uuid': z['uuid'], 'kind': 'zone', 'net': net, 'copper': z['filled'],
         'drill': None, 'plated': False}
        for z in native['zones'] if not z['rule'] and z['net'] == net]


def groups(native, net):
    out = []
    for group in make_graph(objects(native, net)):
        pads = {v['object']['uuid']: v['object']['key'] for v in group if v['object']['kind'] == 'pad'}
        if pads:
            out.append({'pads': sorted(pads.values()), 'pad_uuids': sorted(pads)})
    return sorted(out, key=lambda q: q['pad_uuids'])


def pad_entry(track, pad, layer):
    inside = geometry(pad['inside'][layer])
    actual = inside.difference(geometry(pad['drill']['outside'])) if pad.get('drill') else inside
    xy = next(p for p in [track['start'], track['end']] if inside.contains(Point(p)))
    q = track['end'] if xy == track['start'] else track['start']
    length = math.dist(xy, q)
    normal = [-(q[1] - xy[1]) / length, (q[0] - xy[0]) / length]
    half = track['width'] / 2
    section = section_at(xy, normal, half)
    assert actual.convex_hull.difference(actual).area < 1e-12
    guarded = actual.buffer(-.000001)
    valid = translate(guarded, normal[0] * half, normal[1] * half).intersection(
        translate(guarded, -normal[0] * half, -normal[1] * half))
    entry = LineString([xy, q]).intersection(valid)
    passed = inside.contains(Point(xy)) and section.difference(actual).length <= 1e-8 and entry.length > 0
    assert passed, 'Dedicated return does not enter U12.2 at full .25 mm width'
    return {'passed': passed, 'pad': pad['key'], 'pad_uuid': pad['uuid'],
            'track_uuid': track['uuid'], 'width_mm': track['width'],
            'full_width_actual_pad_section_mm': list(section.coords),
            'section_missing_mm': section.difference(actual).length,
            'full_width_transverse_entry_length_mm': entry.length,
            'transverse_entry_extra_inward_reserve_mm': .000001}


def plane_proof(native, via):
    result = []
    error = native['maximum_polygon_error_mm']
    # Physical holes pierce the plane even where the saved zone polygon spans
    # same-net copper. Remove every exported ERROR_OUTSIDE drill explicitly.
    drills = unary_union([geometry(o['drill']['outside']) for o in native['objects'] if o.get('drill')])
    ground_graph = make_graph(objects(native, 'GND'))
    pad = next(o for o in native['objects'] if o.get('key') == 'U12.2')
    connected_groups = [g for g in ground_graph if any(n['object']['uuid'] == via['uuid'] for n in g)
                        and any(n['object']['uuid'] == pad['uuid'] for n in g)]
    assert len(connected_groups) == 1, 'Return via is not in saved U12.2 GND network'
    for layer in ['In1.Cu', 'In4.Cu']:
        zones = [z for z in native['zones'] if not z['rule'] and z['net'] == 'GND' and layer in z['filled']]
        assert zones
        fill = unary_union([geometry(z['filled'][layer]) for z in zones])
        actual_annulus = geometry(via['copper'][layer]).buffer(-error).difference(geometry(via['drill']['outside']))
        saved_actual = fill.buffer(-error, join_style=2).difference(drills)
        missing = actual_annulus.difference(saved_actual).area
        assert missing <= 1e-12, (layer, 'GND annulus not fully connected to saved fill', missing)
        common_zones = sorted({n['object']['uuid'] for n in connected_groups[0]
                              if n['layer'] == layer and n['object']['kind'] == 'zone'})
        assert common_zones, 'Saved plane absent from GND connected group'
        # A .25 mm-wide finite corridor reaches the dominant .25 mm-eroded
        # plane component. This rules out a new narrow neck immediately beyond
        # the dedicated via; it does not qualify impedance or transient current.
        width = .25
        eroded = saved_actual.buffer(-(width / 2), join_style=2)
        bulk = max(pieces(eroded), key=lambda p: p.area)
        witness = None
        for step in range(72):
            theta = step * math.pi / 36
            unit = [math.cos(theta), math.sin(theta)]
            start = [via['xy'][i] + .15 * unit[i] for i in range(2)]
            end = [via['xy'][i] + .75 * unit[i] for i in range(2)]
            normal = [-unit[1], unit[0]]
            cross = section_at(start, normal, width / 2)
            section_missing = cross.difference(actual_annulus).length
            strip = LineString([start, end]).buffer(width / 2, cap_style=2)
            if (section_missing <= 1e-8 and strip.difference(saved_actual).area <= 1e-12
                    and bulk.contains(Point(end))):
                witness = {'width_mm': width, 'centerline_mm': [start, end],
                           'length_mm': math.dist(start, end), 'strip_polygon_mm': list(strip.exterior.coords),
                           'annular_start_section_missing_mm': section_missing,
                           'strip_area_outside_saved_actual_copper_mm2': strip.difference(saved_actual).area,
                           'connected_bulk_eroded_area_mm2': bulk.area,
                           'bulk_erosion_radius_mm': width / 2,
                           'target_in_dominant_eroded_plane_component': True}
                break
        assert witness, (layer, 'No full-width return-to-bulk-plane witness')
        result.append({'layer': layer, 'via_uuid': via['uuid'], 'via_xy_mm': via['xy'],
                       'saved_ground_network_connected': True, 'connected_saved_zone_uuids': common_zones,
                       'conservative_actual_annulus_area_mm2': actual_annulus.area,
                       'annulus_area_outside_saved_actual_plane_mm2': missing,
                       'full_actual_annulus_covered': True, 'plane_inward_reserve_mm': error,
                       'all_drill_voids_subtracted': True, 'full_width_plane_corridor': witness,
                       'passed': True})
    return result


def return_geometry(native, selected, expected, require_planes=True):
    pad = next(o for o in native['objects'] if o.get('key') == 'U12.2')
    tracks = [o for o in selected if o['kind'] == 'track']
    vias = [o for o in selected if o['kind'] == 'via']
    assert len(tracks) == 2 and len(vias) == 1
    assert all(o['net'] == 'GND' for o in selected)
    assert all(o['width'] == .25 and list(o['copper']) == ['F.Cu'] for o in tracks)
    via = vias[0]
    assert via['xy'] == expected['via_xy_mm'] and via['width'] == .45 and via['drill']['width'] == .20
    observed = sorted((tuple(t['start']), tuple(t['end'])) for t in tracks)
    expected_segments = sorted((tuple(a), tuple(b)) for a, b in zip(expected['points_mm'], expected['points_mm'][1:]))
    assert observed == expected_segments
    length = sum(math.dist(t['start'], t['end']) for t in tracks)
    assert abs(length - expected['centerline_length_mm']) < 1e-12
    direct = make_graph([pad, *selected])
    assert len(direct) == 1, 'Dedicated return needs other shared copper to be continuous'
    error = native['maximum_polygon_error_mm']
    annulus = geometry(via['copper']['F.Cu']).buffer(-error).difference(geometry(via['drill']['outside']))
    contacts = []
    for track in tracks:
        witnesses, overlap = annular_sections(track, annulus, error)
        if witnesses:
            contacts.append({'track_uuid': track['uuid'], 'width_mm': track['width'],
                             'actual_annular_centerline_length_mm': overlap, 'full_width_annular_witnesses': witnesses})
    assert contacts, 'Dedicated return lacks full .25 mm actual annular entry'
    pad_track = next(t for t in tracks if any(geometry(pad['inside']['F.Cu']).contains(Point(p))
                                            for p in [t['start'], t['end']]))
    pad_result = pad_entry(pad_track, pad, 'F.Cu')
    planes = plane_proof(native, via) if require_planes else []
    return {'passed': True, 'width_mm': .25, 'centerline_length_mm': length,
            'points_mm': expected['points_mm'], 'via_count': 1, 'via_xy_mm': via['xy'],
            'diameter_mm': via['width'], 'drill_mm': via['drill']['width'],
            'track_uuids': sorted(t['uuid'] for t in tracks), 'via_uuid': via['uuid'],
            'pad_entry': pad_result, 'actual_annular_front_entries': contacts,
            'direct_dedicated_path_without_other_serial_copper': True,
            'new_narrow_shared_neck_introduced': False, 'saved_plane_connections': planes}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    add_basis_arguments(ap)
    ap.add_argument('--source-audit', type=Path, default=ROOT / 'candidate37/power-audit.json')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    basis, after, _, extra = load_for_args(args)
    before = basis['before']
    if args.basis == 'stage38' and args.source_audit == ROOT / 'candidate37/power-audit.json':
        args.source_audit = ROOT / 'candidate38/power-audit.json'
    base_support_sha = BASE_SUPPORT_SHA[args.basis]
    assert sha(args.source_audit) == base_support_sha, 'Wrong baseline support audit'
    base = read(args.source_audit)
    assert base['passed'] and base['board_sha256'] == before['board_sha256']
    rows = {}
    for net in base['nets']:
        result = groups(after, net)
        assert len(result) == 1, (net, len(result))
        rows[net] = {'pad_group_count': len(result), 'groups': result}
    assert len(rows) == 28
    assert groups(before, 'GND') == rows['GND']['groups']
    old = {o['uuid']: o for o in before['objects']}
    vias = [o for o in after['objects'] if o['uuid'] not in old and o['kind'] == 'via']
    signal_vias = [o for o in vias if o['net'] != 'GND']
    ground_vias = [o for o in vias if o['net'] == 'GND']
    assert len(ground_vias) == 1
    planes = []
    for zone in after['zones']:
        previous = next(z for z in before['zones'] if z['uuid'] == zone['uuid'])
        if zone['rule'] or zone['net'] != 'GND' or not set(zone['layers']) <= {'In1.Cu', 'In4.Cu'}:
            continue
        for layer, polygons in zone['filled'].items():
            fill, old_fill = geometry(polygons), geometry(previous['filled'][layer])
            gaps = [{'via': v['uuid'], 'net': v['net'], 'gap_mm': fill.distance(geometry(v['copper'][layer]))}
                    for v in signal_vias]
            assert all(row['gap_mm'] >= .127 for row in gaps), (layer, gaps)
            planes.append({'layer': layer, 'source_holes': sum(len(p['holes']) for p in previous['filled'][layer]),
                           'result_holes': sum(len(p['holes']) for p in polygons),
                           'source_outlines': len(previous['filled'][layer]), 'result_outlines': len(polygons),
                           'new_signal_via_gaps': gaps, 'minimum_signal_via_gap_required_mm': .127,
                           'added_fill_area_mm2': fill.difference(old_fill).area,
                           'removed_fill_area_mm2': old_fill.difference(fill).area})
    prior_return = [o for o in before['objects'] if o['uuid'] in GROUND_ALLOW]
    new_ground_ids = {o['uuid'] for o in basis['receipt']['added_objects'] if o['net'] == 'GND'}
    current_return = [o for o in after['objects'] if o['uuid'] in new_ground_ids]
    ground_before = return_geometry(before, prior_return, basis['plan']['ground_return']['before'])
    ground_after = return_geometry(after, current_return, basis['plan']['ground_return']['after'])
    recheck(basis)
    report = {'passed': True, 'status': 'all_28_support_nets_connected_and_dedicated_return_verified',
              'board_sha256': after['board_sha256'], 'source_board_sha256': before['board_sha256'],
              'native_sha256': sha((args.candidate or args.stage) / 'f722-heli.native.json'),
              'source_native_sha256': sha(args.source / 'f722-heli.native.json'),
              'source_audit_sha256': base_support_sha, 'audit_source_sha256': sha(__file__),
              'validator_sha256': sha(Path(__file__).with_name('validate_servo23_stage.py')),
              'annular_helper_sha256': sha(Path(__file__).with_name('audit_rewritten_entries.py')),
              'native_graph_helper_sha256': sha(ROOT / 'native-tools/check_protection_paths.py'),
              'strict_servo23_construction': basis['report'], 'additive_successor': extra,
              'ground_native_pad_groups_exactly_preserved': True, 'nets': rows, 'planes': planes,
              'ground_return': {'before': ground_before, 'after': ground_after,
                                'length_change_mm': ground_after['centerline_length_mm'] - ground_before['centerline_length_mm'],
                                'new_narrow_shared_neck_introduced': False,
                                'transient_electrical_quality_claimed': False},
              'method': 'Fresh native copper/barrel/saved-fill pad graph. Strict exact13 change contract. Dedicated GND pad and actual-annular entry plus full saved-plane annulus and .25 mm corridor into dominant eroded plane component; all drill voids subtracted for corridor proof.',
              'limits': ['Nominal continuity and width evidence only; no loaded, impedance, surge, transient, thermal or inductance qualification.',
                         'SERVO3 P1 is still incomplete in the sealed stage. This support pass is not candidate adoption.',
                         'Full native DRC/process/mechanical/parity/critical-reference/protection gates remain separate.']}
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': True, 'support_nets': len(rows), 'signal_vias': len(signal_vias),
                      'ground_width_mm': .25, 'length_before_mm': ground_before['centerline_length_mm'],
                      'length_after_mm': ground_after['centerline_length_mm'], 'planes_verified': 2,
                      'out': str(args.out)}))


if __name__ == '__main__':
    main()
