#!/usr/bin/env python3
"""Read-only candidate40 audit. Explicit DSM39→40 contract; no SERVO basis override.

Imports only geometry primitives, never the SERVO validation entrypoints.
Every input is hash-bound. Controls operate on private in-memory copies only.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT.parent / 'python-deps'), str(ROOT / 'servo23-audits'), str(ROOT / 'native-tools')]
from audit_rewritten_entries import geom, section_at, annular_sections, linear_parts
from check_protection_paths import make_graph, geometry, pieces, run_check
from shapely import unary_union
from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon

SOURCE = ROOT / 'candidate39'
CANDIDATE = ROOT / 'candidate40'
BOUND = {
    SOURCE / 'f722-heli.kicad_pcb': '246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7',
    SOURCE / 'f722-heli.native.json': 'e99bb7888b98c5dd44e44a04b51789ac9dcc47b3fd6b07d1446295acf5b2c577',
    SOURCE / 'f722-heli.logical-route-map.json': '0593aa1353fd84afa9c1a3a53c2af2d8826ff67033356580b3330783c394c25f',
    SOURCE / 'power-audit.json': 'ae15005d976a69a9002419e5d5ce7030e961a47f3f010b17b04f81315607a499',
    CANDIDATE / 'f722-heli.kicad_pcb': 'ea6c41fef86c1f66dbf6e2ce24b58858313c5c83f2a518e53385d48aad734ed5',
    CANDIDATE / 'f722-heli.native.json': '02e51d8bc3a8934ad9aa9bb0ee1b8cfb13b22f62c99bd8aec8cc8d73b410daf6',
    CANDIDATE / 'construction-provenance.json': 'fabae4bd802d0f199b2c5d3d2ed4980a43a4c2a00d10d539e9aed53a64d4cd86',
    CANDIDATE / 'coordinated-route-proposal.json': '9fe7a34d9abc85ecf453367f213c57edb29da36866c6cd7c61fd7d97b1a03d57',
    CANDIDATE / 'construct_dsm_complete40.used.py': 'c1e4891680f6980331c628f2f4c3698a12c48e2a9c12b1725d58a9f301413324',
    ROOT / 'servo23-audits/audit_rewritten_entries.py': '0204d88d8264fd7dae31c7603f11a164a2f9735ccaf8fe71fb57c0bdece0b4dc',
    ROOT / 'servo23-audits/audit_support_and_return.py': '17b366c3c2c0da6279e4bd1567805e784ec1e44ac3f2d156d6fe88afde4174da',
    ROOT / 'native-tools/check_protection_paths.py': '4bf5c8e49c379898ef8ce9da5410c5a47260a072c7ac387a27b07258be90c976',
}
read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
record_sha = lambda o: hashlib.sha256(json.dumps(o, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def check_files():
    for path, expected in BOUND.items():
        assert sha(path) == expected, f'Input changed: {path}'


def translate_record(obj, dx, dy):
    """Exact 1 nm IU translation, preserving all non-position fields."""
    result = copy.deepcopy(obj)
    def xy(q):
        return [round(q[0] + dx, 6), round(q[1] + dy, 6)]
    for key in ['xy', 'start', 'end', 'mid', 'center']:
        if key in result:
            result[key] = xy(result[key])
    for key in ['copper', 'inside', 'mask']:
        for polygons in result.get(key, {}).values():
            if key == 'mask':
                polygons = polygons['polygons']
            for polygon in polygons:
                polygon['outer'] = list(map(xy, polygon['outer']))
                polygon['holes'] = [list(map(xy, hole)) for hole in polygon.get('holes', [])]
    if 'graphics' in result:
        result['graphics'] = [translate_record(g, dx, dy) for g in result['graphics']]
    assert not result.get('drill'), 'Translation contract permits only undrilled SMDs'
    return result


def source_contract(before, after, proposal, receipt):
    assert before['board_sha256'] == BOUND[SOURCE / 'f722-heli.kicad_pcb']
    assert after['board_sha256'] == BOUND[CANDIDATE / 'f722-heli.kicad_pcb']
    assert receipt['source_board_sha256'] == before['board_sha256']
    assert receipt['board_sha256'] == after['board_sha256']
    assert receipt['proposal_sha256'] == BOUND[CANDIDATE / 'coordinated-route-proposal.json']
    assert receipt['source_native_sha256'] == BOUND[SOURCE / 'f722-heli.native.json']
    for n in [before, after]:
        assert n['schema'] == 'kicad-native-copper/v1'
        assert n['maximum_polygon_error_mm'] == .00001
        assert n['copper_error_location'] == 'ERROR_OUTSIDE' and n['pad_cut_error_location'] == 'ERROR_INSIDE'
        assert n['source_unchanged']
    old, new = [{o['uuid']: o for o in n['objects']} for n in [before, after]]
    removed, added = set(old) - set(new), set(new) - set(old)
    changed = {u for u in old.keys() & new.keys() if old[u] != new[u]}
    assert len(removed) == 4 and len(added) == 13 and len(changed) == 4
    assert removed == {o['uuid'] for o in proposal['remove_copper']}
    assert {o['uuid']: o for o in receipt['removed_source_records']} == {u: old[u] for u in removed}
    assert {o['uuid']: o for o in receipt['added_records']} == {u: new[u] for u in added}
    assert {p['before']['uuid'] for p in receipt['changed_pad_records']} == changed
    for p in receipt['changed_pad_records']:
        assert p['before'] == old[p['before']['uuid']] and p['after'] == new[p['after']['uuid']]
    assert set(proposal['footprint_changes']) == {'R38', 'R70'}
    for uid in changed:
        a, b = old[uid], new[uid]
        assert a['kind'] == b['kind'] == 'pad' and a['ref'] in {'R38', 'R70'}
        change = proposal['footprint_changes'][a['ref']]
        dx, dy = [change['after'][i] - change['before'][i] for i in range(2)]
        assert b == translate_record(a, dx, dy), f'Nontranslation pad change: {a["key"]}'
        expected = change['pads'][a['number']]
        assert a['net'] == b['net'] == expected['net']
        assert a['xy'] == expected['before'] and b['xy'] == expected['after']
    oldfp, newfp = [{o['uuid']: o for o in n['footprints']} for n in [before, after]]
    assert set(oldfp) == set(newfp)
    fpchanged = {u for u in oldfp if oldfp[u] != newfp[u]}
    assert len(fpchanged) == 2 and {oldfp[u]['ref'] for u in fpchanged} == {'R38', 'R70'}
    assert {p['before']['uuid'] for p in receipt['changed_footprint_records']} == fpchanged
    for pair in receipt['changed_footprint_records']:
        assert pair['before'] == oldfp[pair['before']['uuid']] and pair['after'] == newfp[pair['after']['uuid']]
    for uid in fpchanged:
        a, b = oldfp[uid], newfp[uid]
        change = proposal['footprint_changes'][a['ref']]
        assert change['before'][2:] == change['after'][2:]
        dx, dy = [change['after'][i] - change['before'][i] for i in range(2)]
        assert b == translate_record(a, dx, dy), f'Nontranslation footprint change: {a["ref"]}'
    zone_contract = lambda z: {k: v for k, v in z.items() if k not in {'filled', 'fill_representation'}}
    assert list(map(zone_contract, before['zones'])) == list(map(zone_contract, after['zones']))
    for key in ['edge_cuts', 'outline_with_npth', 'copper_layers', 'board_thickness_mm']:
        assert before[key] == after[key], key
    expected_ids = set()
    for route in proposal['add_tracks']:
        for i, (aa, bb) in enumerate(zip(route['points_mm'], route['points_mm'][1:])):
            label = route['name'] + '/track/' + str(i)
            uid = str(uuid.uuid5(uuid.NAMESPACE_URL, before['board_sha256'] + '/' + receipt['proposal_sha256'] + '/' + label))
            expected_ids.add(uid)
            t = new[uid]
            assert t['kind'] == 'track' and t['net'] == route['net']
            assert t['start'] == aa and t['end'] == bb and t['width'] == route['width_mm']
            assert list(t['copper']) == [route['layer']]
    via_id = str(uuid.uuid5(uuid.NAMESPACE_URL, before['board_sha256'] + '/' + receipt['proposal_sha256'] + '/GND/via'))
    expected_ids.add(via_id)
    via = new[via_id]
    assert via['kind'] == 'via' and via['net'] == 'GND' and via['xy'] == proposal['add_via']['xy_mm']
    assert via['width'] == .45 and via['drill']['width'] == .2 and via['plated']
    assert via['top_layer'] == 'F.Cu' and via['bottom_layer'] == 'B.Cu'
    assert via['tented'] == {'F.Mask': True, 'B.Mask': True}
    assert added == expected_ids
    assert all(old[u] == new[u] for u in proposal['preserve_original_J12_branch_uuids'])
    unchanged = sorted(set(old) & set(new) - changed)
    assert len(unchanged) == receipt['all_other_source_native_objects_exact'] == 1849
    return {
        'passed': True, 'source_object_count': len(old), 'candidate_object_count': len(new),
        'removed': [{'uuid': u, 'net': old[u]['net'], 'record_sha256': record_sha(old[u])} for u in sorted(removed)],
        'added': [{'uuid': u, 'net': new[u]['net'], 'record_sha256': record_sha(new[u])} for u in sorted(added)],
        'translated_pads': [{'key': old[u]['key'], 'uuid': u, 'before_xy': old[u]['xy'], 'after_xy': new[u]['xy'],
                             'before_record_sha256': record_sha(old[u]), 'after_record_sha256': record_sha(new[u])} for u in sorted(changed)],
        'translated_footprints': [{'ref': oldfp[u]['ref'], 'uuid': u, 'before_record_sha256': record_sha(oldfp[u]),
                                  'after_record_sha256': record_sha(newfp[u])} for u in sorted(fpchanged)],
        'all_other_1849_objects_exact': True, 'unchanged_uuid_record_digest': record_sha({u: old[u] for u in unchanged}),
        'preserved_J12_branch_uuids': proposal['preserve_original_J12_branch_uuids'],
        'zone_definitions_outline_stackup_exact': True,
    }


def pad_entry(track, pad, layer, endpoint):
    actual = geom(pad['inside'][layer])
    assert not pad.get('drill') and actual.convex_hull.difference(actual).area < 1e-12
    xy = track[endpoint]
    q = track['end' if endpoint == 'start' else 'start']
    length = math.dist(xy, q)
    normal = [-(q[1] - xy[1]) / length, (q[0] - xy[0]) / length]
    half = track['width'] / 2
    section = section_at(xy, normal, half)
    guarded = actual.buffer(-.000001)
    allowed = translate(guarded, normal[0] * half, normal[1] * half).intersection(
        translate(guarded, -normal[0] * half, -normal[1] * half))
    entry = LineString([xy, q]).intersection(allowed)
    strips = []
    for interval in linear_parts(entry):
        aa, bb = [list(interval.interpolate(f, normalized=True).coords[0]) for f in [.25, .75]]
        ca, cb = [list(section_at(c, normal, half).coords) for c in [aa, bb]]
        rect = Polygon([ca[0], ca[1], cb[1], cb[0]])
        missing = rect.difference(actual).area
        if missing <= 1e-12:
            strips.append({'length_mm': math.dist(aa, bb), 'polygon_mm': list(rect.exterior.coords),
                           'area_outside_actual_pad_mm2': missing, 'boundary_reserve_mm': rect.distance(actual.boundary)})
    passed = actual.contains(Point(xy)) and section.difference(actual).length <= 1e-8 and entry.length > 0 and bool(strips)
    return {'passed': passed, 'pad': pad['key'], 'pad_uuid': pad['uuid'], 'net': pad['net'],
            'track_uuid': track['uuid'], 'layer': layer, 'endpoint': endpoint, 'xy_mm': xy, 'width_mm': track['width'],
            'center_inside_native_pad': actual.contains(Point(xy)), 'full_width_section_mm': list(section.coords),
            'section_missing_mm': section.difference(actual).length, 'transverse_entry_length_mm': entry.length,
            'transverse_entry_wkt': entry.wkt, 'finite_full_width_strips': strips, 'inward_reserve_mm': .000001}


def join_entry(a, b, layer, width):
    common = sorted(set(map(tuple, [a['start'], a['end']])) & set(map(tuple, [b['start'], b['end']])))
    copper_a, copper_b = [geom(t['copper'][layer]) for t in [a, b]]
    overlap = copper_a.intersection(copper_b)
    # KiCad straight-track primitives are closed round-ended capsules. Exact
    # coincident ends and minimum widths therefore prove a common full-width
    # disk analytically, independent of approximation at curved polygon edges.
    # This is stronger than a generic positive-area or center-contact test.
    passed = bool(common) and a['width'] >= width and b['width'] >= width and overlap.area > 0
    return {'passed': passed, 'net': a['net'], 'track_uuids': sorted([a['uuid'], b['uuid']]),
            'layer': layer, 'exact_common_native_endpoint_mm': common, 'required_width_mm': width,
            'native_widths_mm': [a['width'], b['width']], 'native_polygon_overlap_mm2': overlap.area,
            'analytic_common_disk_diameter_mm': min(a['width'], b['width']) if common else 0,
            'analytic_common_disk_area_mm2': math.pi * (min(a['width'], b['width']) / 2) ** 2 if common else 0,
            'proof': 'Exact native straight round-ended track primitives; common endpoint plus unchanged minimum width yields a shared disk of full diameter. Native polygons additionally must have positive actual overlap.'}


def objects(native, net):
    return [o for o in native['objects'] if o['net'] == net] + [
        {'uuid': z['uuid'], 'kind': 'zone', 'net': net, 'copper': z['filled'], 'drill': None, 'plated': False}
        for z in native['zones'] if not z['rule'] and z['net'] == net]


def groups(native, net):
    result = []
    for group in make_graph(objects(native, net)):
        pads = {v['object']['uuid']: v['object']['key'] for v in group if v['object']['kind'] == 'pad'}
        if pads:
            result.append({'pads': sorted(pads.values()), 'pad_uuids': sorted(pads)})
    return sorted(result, key=lambda row: row['pad_uuids'])


def plane_corridor(saved_actual, actual_annulus, via_xy):
    width = .25
    eroded_parts = pieces(saved_actual.buffer(-(width / 2), join_style=2))
    if not eroded_parts:
        return None
    bulk = max(eroded_parts, key=lambda p: p.area)
    for step in range(72):
        theta = step * math.pi / 36
        unit = [math.cos(theta), math.sin(theta)]
        start = [via_xy[i] + .15 * unit[i] for i in range(2)]
        end = [via_xy[i] + .75 * unit[i] for i in range(2)]
        cross = section_at(start, [-unit[1], unit[0]], width / 2)
        strip = LineString([start, end]).buffer(width / 2, cap_style=2)
        missing_cross = cross.difference(actual_annulus).length
        missing_strip = strip.difference(saved_actual).area
        if missing_cross <= 1e-8 and missing_strip <= 1e-12 and bulk.contains(Point(end)):
            return {'width_mm': width, 'centerline_mm': [start, end], 'length_mm': math.dist(start, end),
                    'strip_polygon_mm': list(strip.exterior.coords), 'annular_section_missing_mm': missing_cross,
                    'strip_area_outside_saved_actual_copper_mm2': missing_strip,
                    'dominant_eroded_component_area_mm2': bulk.area, 'erosion_radius_mm': width / 2,
                    'target_inside_dominant_eroded_component': True}
    return None


def return_proof(native, selected):
    pad = next(o for o in native['objects'] if o.get('key') == 'D7.2')
    via = next(o for o in selected if o['kind'] == 'via')
    tracks = [o for o in selected if o['kind'] == 'track']
    error = native['maximum_polygon_error_mm']
    direct = make_graph([pad, *selected])
    direct_ok = len(direct) == 1
    annulus = geom(via['copper']['B.Cu']).buffer(-error).difference(geom(via['drill']['outside']))
    contacts = []
    for track in tracks:
        witnesses, overlap = annular_sections(track, annulus, error)
        if witnesses:
            contacts.append({'track_uuid': track['uuid'], 'width_mm': track['width'],
                             'actual_annular_centerline_length_mm': overlap, 'finite_full_width_annular_strips': witnesses})
    pad_entries = [pad_entry(t, pad, 'B.Cu', endpoint) for t in tracks for endpoint in ['start', 'end']
                   if geom(pad['inside']['B.Cu']).contains(Point(t[endpoint]))]
    ground_graph = make_graph(objects(native, 'GND'))
    connected = [g for g in ground_graph if {pad['uuid'], via['uuid']} <= {n['object']['uuid'] for n in g}]
    drills = unary_union([geom(o['drill']['outside']) for o in native['objects'] if o.get('drill')])
    planes = []
    for layer in ['In1.Cu', 'In4.Cu']:
        zones = [z for z in native['zones'] if not z['rule'] and z['net'] == 'GND' and layer in z['filled']]
        fill = unary_union([geom(z['filled'][layer]) for z in zones])
        saved_actual = fill.buffer(-error, join_style=2).difference(drills)
        actual_annulus = geom(via['copper'][layer]).buffer(-error).difference(geom(via['drill']['outside']))
        missing = actual_annulus.difference(saved_actual).area
        corridor = plane_corridor(saved_actual, actual_annulus, via['xy'])
        connected_zones = sorted({n['object']['uuid'] for g in connected for n in g if n['layer'] == layer and n['object']['kind'] == 'zone'})
        planes.append({'layer': layer, 'passed': missing <= 1e-12 and corridor is not None and bool(connected_zones),
                       'annulus_area_outside_saved_actual_plane_mm2': missing, 'annulus_area_mm2': actual_annulus.area,
                       'connected_saved_zone_uuids': connected_zones, 'plane_inward_reserve_mm': error,
                       'all_native_drill_voids_subtracted': True, 'full_width_plane_corridor': corridor})
    passed = direct_ok and bool(contacts) and all(p['passed'] for p in pad_entries) and len(connected) == 1 and all(p['passed'] for p in planes)
    return {'passed': passed, 'pad': 'D7.2', 'width_mm': .25, 'track_uuids': sorted(t['uuid'] for t in tracks),
            'via_uuid': via['uuid'], 'via_xy_mm': via['xy'], 'via_diameter_mm': via['width'], 'drill_mm': via['drill']['width'],
            'direct_dedicated_graph_without_other_serial_copper': direct_ok,
            'centerline_length_mm': sum(math.dist(t['start'], t['end']) for t in tracks),
            'strict_pad_entries': pad_entries, 'back_actual_annular_contacts': contacts,
            'saved_planes': planes, 'saved_pad_via_ground_group_count': len(connected),
            'new_neck_below_025_mm_excluded': all(p['passed'] for p in planes)}


def synthetic_track(aa, bb, width, net='GND', layer='B.Cu'):
    g = LineString([aa, bb]).buffer(width / 2, quad_segs=64)
    return {'uuid': 'in-memory-negative-control', 'kind': 'track', 'net': net, 'start': aa, 'end': bb, 'width': width,
            'copper': {layer: [{'outer': list(g.exterior.coords), 'holes': []}]}, 'drill': None, 'plated': False}


def retained_r26_entry(before, after):
    """One explicit retained-junction proof, not a shared-pad exemption."""
    old, new = [{o['uuid']: o for o in n['objects']} for n in [before, after]]
    incoming = new['c757d812-b2ab-5312-b48b-a9c5f876313e']
    retained = new['24af4ff1-59b1-43d4-8282-48cf7056a156']
    replaced = old['4deb196b-8a4a-4837-97d6-ddceb3751d97']
    pad = new['8d042e6a-9fcd-424c-a429-05c3658bc800']
    assert retained['width'] == .127, 'Retained entry must retain full .127 native width'
    assert pad['key'] == 'R26.2' and retained == old[retained['uuid']] and pad == old[pad['uuid']]
    assert incoming['start'] == retained['start'] == replaced['start'] == [12.36223, 24.3097]
    assert incoming['width'] == retained['width'] == replaced['width'] == .127
    assert list(incoming['copper']) == list(retained['copper']) == ['F.Cu']
    error = after['maximum_polygon_error_mm']
    incoming_actual = geom(incoming['copper']['F.Cu']).buffer(-error)
    retained_actual = geom(retained['copper']['F.Cu']).buffer(-error)
    pad_actual = geom(pad['inside']['F.Cu'])
    actual_union = incoming_actual.union(retained_actual).union(pad_actual)
    start, end = [12.40223, 24.3097], pad['xy']
    length = math.dist(start, end)
    direction = [(end[i] - start[i]) / length for i in range(2)]
    normal = [-direction[1], direction[0]]
    start_section = section_at(start, normal, .127 / 2)
    end_section = section_at(end, normal, .127 / 2)
    strip = LineString([start, end]).buffer(.127 / 2, cap_style=2)
    source_direct = pad_entry(replaced, pad, 'F.Cu', 'start')
    retained_entries = [pad_entry(retained, pad, 'F.Cu', ep) for ep in ['start', 'end']]
    missing = strip.difference(actual_union).area
    boundary_reserve = strip.distance(actual_union.boundary)
    start_missing = start_section.difference(incoming_actual).length
    end_missing = end_section.difference(pad_actual).length
    passed = missing <= 1e-12 and boundary_reserve > error and start_missing <= 1e-8 and end_missing <= 1e-8 and all(e['passed'] for e in retained_entries)
    # Preserve both terminal sections but remove an internal crossing strip.
    middle = [(start[i] + end[i]) / 2 for i in range(2)]
    notch = section_at(middle, normal, .2).buffer(.005, cap_style=2)
    notched = actual_union.difference(notch)
    broken_area = strip.difference(notched).area
    control = {'name': 'R26_corridor_internal_cut_rejected_despite_intact_terminal_sections',
               'rejected': broken_area > 1e-12 and start_section.difference(notched).length <= 1e-8 and end_section.difference(notched).length <= 1e-8,
               'strip_area_outside_notched_copper_mm2': broken_area}
    return {
        'passed': passed, 'classification': 'exact_source_bound_retained_track_junction_with_separate_verified_pad_entry',
        'pad': pad['key'], 'incoming_track_uuid': incoming['uuid'], 'retained_track_uuid': retained['uuid'],
        'retained_track_and_pad_exact_source_records': True, 'shared_native_endpoint_mm': incoming['start'],
        'incoming_record_sha256': record_sha(incoming), 'retained_record_sha256': record_sha(retained),
        'actual_pad_record_sha256': record_sha(pad), 'replaced_source_record_sha256': record_sha(replaced),
        'direct_incoming_transverse_entry_remains_false': True,
        'source39_replaced_track_had_identical_direct_entry_failure': not source_direct['passed'],
        'source39_direct_entry_witness': source_direct, 'retained_track_strict_pad_entries': retained_entries,
        'full_width_actual_copper_corridor': {'width_mm': .127, 'length_mm': length,
            'centerline_mm': [start, end], 'polygon_mm': list(strip.exterior.coords),
            'area_outside_actual_copper_mm2': missing, 'minimum_boundary_reserve_mm': boundary_reserve,
            'start_section_mm': list(start_section.coords), 'end_section_mm': list(end_section.coords),
            'start_section_missing_from_new_track_mm': start_missing, 'end_section_missing_from_actual_pad_mm': end_missing,
            'new_and_retained_track_polygon_inward_reserve_mm': error, 'pad_geometry': 'native ERROR_INSIDE'},
        'scope': 'Only this identified R26.2 junction is accepted by the explicit finite full-width corridor. The direct-pad endpoint predicate remains false; no other shared-pad endpoint is exempted.'}, control


def main():
    check_files()
    before, after = [read(d / 'f722-heli.native.json') for d in [SOURCE, CANDIDATE]]
    receipt = read(CANDIDATE / 'construction-provenance.json')
    proposal = read(CANDIDATE / 'coordinated-route-proposal.json')
    base = read(SOURCE / 'power-audit.json')
    contract = source_contract(before, after, proposal, receipt)
    old, new = [{o['uuid']: o for o in n['objects']} for n in [before, after]]
    added = [o for u, o in new.items() if u not in old]
    tracks = [o for o in after['objects'] if o['kind'] == 'track']
    pads = [o for o in after['objects'] if o['kind'] == 'pad']
    entries, joins, endpoint_classification = [], [], []
    seen_entries, seen_joins = set(), set()
    # Check every new endpoint, every pad endpoint it lies in, all exact joins,
    # and separately both retained R70 entries after the pad translations.
    for track in [o for o in added if o['kind'] == 'track']:
        for layer in track['copper']:
            for endpoint in ['start', 'end']:
                xy = track[endpoint]
                hitpads = [p for p in pads if p['net'] == track['net'] and layer in p['inside'] and geom(p['inside'][layer]).contains(Point(xy))]
                hittracks = [t for t in tracks if t['uuid'] != track['uuid'] and t['net'] == track['net'] and layer in t['copper'] and xy in [t['start'], t['end']]]
                hitvias = [v for v in after['objects'] if v['kind'] == 'via' and v['net'] == track['net'] and layer in v['copper'] and v['xy'] == xy]
                endpoint_classification.append({'track_uuid': track['uuid'], 'endpoint': endpoint, 'layer': layer, 'xy_mm': xy,
                                                'pads': [p['key'] for p in hitpads], 'exact_join_tracks': [t['uuid'] for t in hittracks],
                                                'vias': [v['uuid'] for v in hitvias], 'resolved': bool(hitpads or hittracks or hitvias)})
                for pad in hitpads:
                    key = track['uuid'], pad['uuid'], layer, endpoint
                    if key not in seen_entries:
                        seen_entries.add(key)
                        entries.append(pad_entry(track, pad, layer, endpoint))
                for t in hittracks:
                    key = tuple(sorted([track['uuid'], t['uuid']])) + (layer,)
                    if key not in seen_joins:
                        seen_joins.add(key)
                        joins.append(join_entry(track, t, layer, .25 if track['net'] == 'GND' else .127))
    for pad in [p for p in pads if p.get('ref') == 'R70']:
        retained = [t for t in tracks if t['uuid'] in old and t['net'] == pad['net'] and 'B.Cu' in t['copper']]
        matches = [(t, ep) for t in retained for ep in ['start', 'end'] if geom(pad['inside']['B.Cu']).contains(Point(t[ep]))]
        assert len(matches) == 1, (pad['key'], len(matches))
        t, ep = matches[0]
        assert t == old[t['uuid']]
        entry = pad_entry(t, pad, 'B.Cu', ep)
        entry['retained_source_track_exact'] = True
        entries.append(entry)
    assert base['passed'] and base['board_sha256'] == before['board_sha256'] and len(base['nets']) == 28
    support = {}
    for net in base['nets']:
        a, b = groups(before, net), groups(after, net)
        assert a == base['nets'][net]['groups'], f'Baseline support mismatch: {net}'
        support[net] = {'passed': a == b and len(b) == 1, 'groups': b, 'source_groups_exactly_preserved': a == b}
    topology = {}
    for net in ['RPM_LV', 'SBUS_HV', 'DSM_RX_MCU']:
        a, b = groups(before, net), groups(after, net)
        topology[net] = {'passed': a == b, 'before_groups': a, 'after_groups': b}
    dsm = groups(after, 'DSM_RX_EXT')
    topology['DSM_RX_EXT'] = {'passed': len(dsm) == 1 and dsm[0]['pads'] == ['D7.1', 'J12.3', 'R38.1'], 'after_groups': dsm}
    ground = return_proof(after, [o for o in added if o['net'] == 'GND'])
    retained_r26, r26_control = retained_r26_entry(before, after)
    direct_failures = [e for e in entries if not e['passed']]
    exact_r26_failure = lambda e: e['track_uuid'] == 'c757d812-b2ab-5312-b48b-a9c5f876313e' and e['pad'] == 'R26.2' and e['layer'] == 'F.Cu' and e['endpoint'] == 'start'
    effective_entry_pass = all(e['passed'] or (exact_r26_failure(e) and retained_r26['passed']) for e in entries)
    assert len(direct_failures) == 1 and exact_r26_failure(direct_failures[0])
    cut_contract = {'net': 'DSM_RX_EXT', 'clamp': 'D7.1', 'source': 'J12.3', 'target': 'R38.1', 'minimum_gap_required_mm': .127}
    cut = run_check(after, cut_contract)
    controls = [r26_control]
    for name in ['removed', 'narrowed']:
        mutant = copy.deepcopy(after)
        if name == 'removed':
            mutant['objects'] = [o for o in mutant['objects'] if o['uuid'] != '24af4ff1-59b1-43d4-8282-48cf7056a156']
        else:
            t = next(o for o in mutant['objects'] if o['uuid'] == '24af4ff1-59b1-43d4-8282-48cf7056a156')
            replacement = synthetic_track(t['start'], t['end'], .1, t['net'], 'F.Cu')
            t['width'], t['copper'] = replacement['width'], replacement['copper']
        try:
            retained_r26_entry(before, mutant)
            rejected, reason = False, None
        except (KeyError, AssertionError) as exc:
            rejected, reason = True, str(exc)
        controls.append({'name': 'R26_required_retained_entry_' + name + '_rejected', 'rejected': rejected,
                         'reason': reason, 'note': 'Refuses this source-bound retained-junction classification when its required retained path is missing or narrower. Pad copper alone is not substituted for the specified retained entry.'})
    # Strict-entry control: .25 mm horizontal strip in the .25 mm-high pad is
    # tangent only. Positive copper overlap/center contact must not pass it.
    d7 = next(p for p in pads if p['key'] == 'D7.2')
    tangent = pad_entry(synthetic_track(d7['xy'], [16.4, 24.2], .25), d7, 'B.Cu', 'start')
    controls.append({'name': 'D7_025mm_pad_height_horizontal_tangency_rejected', 'rejected': not tangent['passed'], 'witness': tangent})
    via = next(o for o in added if o['kind'] == 'via')
    annulus = geom(via['copper']['B.Cu']).buffer(-after['maximum_polygon_error_mm']).difference(geom(via['drill']['outside']))
    drillspur = synthetic_track(via['xy'], [via['xy'][0] + .02, via['xy'][1]], .025)
    ws, overlap = annular_sections(drillspur, annulus, after['maximum_polygon_error_mm'])
    controls.append({'name': 'drill_only_center_contact_rejected', 'rejected': not ws and overlap == 0, 'actual_centerline_overlap_mm': overlap, 'strip_count': len(ws)})
    # Retained copper changes cannot pass merely because all intended pads connect.
    mutant = copy.deepcopy(after)
    next(o for o in mutant['objects'] if o['uuid'] == '30154a77-e29e-465a-aa6f-a2ea55289eb9')['width'] = .199
    try:
        source_contract(before, mutant, proposal, receipt)
        rejected = False
    except AssertionError:
        rejected = True
    controls.append({'name': 'unlisted_retained_track_mutation_rejected', 'rejected': rejected})
    mutant = copy.deepcopy(after)
    next(o for o in mutant['objects'] if o.get('key') == 'R70.1')['net'] = 'GND'
    try:
        source_contract(before, mutant, proposal, receipt)
        rejected = False
    except AssertionError:
        rejected = True
    controls.append({'name': 'translated_pad_net_mutation_rejected', 'rejected': rejected})
    a, b = [new[u] for u in joins[0]['track_uuids']]
    short = synthetic_track(a['start'], a['end'], .1, a['net'], joins[0]['layer'])
    control = join_entry(short, b, joins[0]['layer'], .127)
    controls.append({'name': 'shared_center_but_narrow_track_join_rejected', 'rejected': not control['passed'], 'witness': control})
    mutant = copy.deepcopy(after)
    mutant['objects'] = [o for o in mutant['objects'] if o['uuid'] != '30154a77-e29e-465a-aa6f-a2ea55289eb9']
    broken = groups(mutant, 'DSM_ILIM')
    controls.append({'name': 'R70_support_disconnect_rejected', 'rejected': len(broken) != 1, 'pad_groups': broken})
    mutant = dict(after, objects=after['objects'] + [synthetic_track([15.38, 23.82448], [16.26, 23.59], .127, 'DSM_RX_EXT')])
    bypass = run_check(mutant, cut_contract)
    controls.append({'name': 'outside_D7_pad_bypass_rejected', 'rejected': not bypass['complete_clamp_first_path_passes'],
                     'connected_after_cut': not bypass['source_target_physically_disconnected_after_removing_actual_pad_copper'],
                     'after_cut_pad_groups': bypass['after_cut_pad_groups']})
    # Deliberately disconnected/necked saved copper, only in memory. Same via
    # annulus remains, but a .20 mm neck cannot prove a .25 mm route to bulk.
    x, y = via['xy']
    outer = geom(via['copper']['B.Cu']).buffer(-after['maximum_polygon_error_mm'])
    drill = geom(via['drill']['outside'])
    bulk = Polygon([(x + .55, y - 1), (x + 2, y - 1), (x + 2, y + 1), (x + .55, y + 1)])
    neck = LineString([[x, y], [x + .65, y]]).buffer(.1, cap_style=2)
    narrow = outer.union(neck).union(bulk).difference(drill)
    control = plane_corridor(narrow, annulus, via['xy'])
    controls.append({'name': '020mm_saved_plane_neck_rejected', 'rejected': control is None, 'witness': control})
    isolated = plane_corridor(annulus, annulus, via['xy'])
    controls.append({'name': 'isolated_saved_annulus_rejected', 'rejected': isolated is None, 'witness': isolated})
    check_files()
    gates = {
        'source_contract': contract['passed'], 'strict_pad_entries_or_explicit_R26_retained_corridor': effective_entry_pass,
        'ordinary_full_width_joins': all(j['passed'] for j in joins),
        'all_new_endpoints_resolved': all(e['resolved'] for e in endpoint_classification),
        'support_groups': all(s['passed'] for s in support.values()),
        'signal_topology': all(t['passed'] for t in topology.values()),
        'dedicated_return': ground['passed'], 'actual_D7_cut': cut['complete_clamp_first_path_passes'],
        'negative_controls': all(c['rejected'] for c in controls), 'source_recheck_unchanged': True,
    }
    report = {
        'schema': 'f722-dsm40-entry-return-audit/v1', 'passed': all(gates.values()), 'gates': gates,
        'source_board_sha256': before['board_sha256'], 'candidate_board_sha256': after['board_sha256'],
        'script_sha256': sha(__file__), 'input_hashes': {str(p.relative_to(ROOT)): v for p, v in BOUND.items()},
        'source_change_contract': contract, 'strict_pad_entries': entries, 'ordinary_track_joins': joins,
        'direct_pad_entry_failures_preserved': direct_failures, 'explicit_retained_R26_junction': retained_r26,
        'new_endpoint_classification': endpoint_classification, 'support_nets': support, 'signal_topology': topology,
        'dedicated_D7_ground_return': ground, 'actual_D7_pad_cut': cut, 'negative_controls': controls,
        'limits': ['Nominal native geometry and saved-fill continuity/width only. No ESD transient, loaded-power, impedance, inductance, thermal, assembly, or manufacturing-tolerance qualification.',
                   'Candidate39 and candidate40 are immutable inputs. Exact coordinated DSM source contract is independent of the separate SERVO source contract; importing geometry primitives does not accept a different SERVO basis.',
                   'Native DRC, process, reference, parity, mechanical, and final adoption gates remain separately owned. DSM_RX_MCU and SBUS_HV retain their existing pad-group topology; this report does not assert whole-board completion.'],
    }
    output = HERE / 'candidate40-entry-return.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'gates': gates, 'pad_entries': len(entries), 'full_width_joins': len(joins),
                      'support_nets': len(support), 'negative_controls': len(controls), 'D7_outside_pad_gap_mm': cut['minimum_gap_measured_mm'],
                      'return_length_mm': ground['centerline_length_mm'], 'report': str(output)}, indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
