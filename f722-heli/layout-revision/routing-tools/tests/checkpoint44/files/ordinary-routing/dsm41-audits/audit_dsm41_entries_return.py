#!/usr/bin/env python3
"""Read-only, exact source39 -> isolated40 -> candidate41 geometry audit.

Reuses sealed DSM40 geometry predicates without altering their contracts or
writing their reports. Every mutation control is a private in-memory copy.
"""
import collections
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT.parent / 'python-deps'), str(ROOT / 'dsm40-audits')]
import audit_dsm40_entries_return as previous
from audit_dsm40_entries_return import (
    annular_sections, geom, groups, join_entry, linear_parts, make_graph,
    objects, pad_entry, plane_corridor, read, record_sha, retained_r26_entry,
    return_proof, run_check, section_at, sha, synthetic_track, translate_record,
)
from shapely import unary_union
from shapely.geometry import LineString, Point, Polygon

SOURCE = ROOT / 'candidate39'
STAGE = ROOT / 'candidate40'
CANDIDATE = ROOT / 'candidate41'
MANIFEST = HERE / 'input-hashes.json'
BOUND = read(MANIFEST)
SOURCE_SHA = '246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7'
STAGE_SHA = 'ea6c41fef86c1f66dbf6e2ce24b58858313c5c83f2a518e53385d48aad734ed5'
FINAL_SHA = '539d9547eb8c4d5984481293ae10cee34355ee838dff11ab43b00cca270ceae2'
CORE_OLD = {'564d43f4-fb99-4ccd-80b4-4580af7617f8', 'b6cf7bc9-8a4c-4cb5-b764-038d677651c3'}
R26_IN = 'c757d812-b2ab-5312-b48b-a9c5f876313e'
R26_RETAINED = '24af4ff1-59b1-43d4-8282-48cf7056a156'
R70_ILIM = 'f4fd956a-48a5-5fdd-a0ca-95d7ca25294a'
R70_GND = '47fd1f9b-ce66-5195-b301-70f14b6cbbe0'
C70_TRACKS = {'C70.1': '475d63bb-6fc3-4bd9-8d5d-5012ed082346',
              'C70.2': 'fc56f459-cc2f-4bdb-86dc-69e20d3ab646'}


def check_files():
    previous.check_files()
    for path, expected in BOUND.items():
        assert sha(ROOT / path) == expected, 'Changed bound input: ' + path


def indexed(native, field='objects'):
    result = {o['uuid']: o for o in native[field]}
    assert len(result) == len(native[field]), 'Duplicate native UUID'
    return result


def changes(before, after):
    old, new = indexed(before), indexed(after)
    return old.keys() - new.keys(), new.keys() - old.keys(), {
        u for u in old.keys() & new.keys() if old[u] != new[u]}


def check_stage41(before, after, proposal, receipt):
    assert before['board_sha256'] == receipt['source_board_sha256'] == proposal['source_board_sha256'] == STAGE_SHA
    assert after['board_sha256'] == receipt['board_sha256'] == FINAL_SHA
    assert receipt['accepted_origin_board_sha256'] == SOURCE_SHA
    assert receipt['source_native_sha256'] == proposal['source_native_sha256'] == BOUND['candidate40/f722-heli.native.json']
    assert receipt['source_map_sha256'] == BOUND['candidate40/f722-heli.logical-route-map.json']
    assert receipt['proposal_sha256'] == BOUND['candidate41/proposal40.json'] == BOUND['tests/dsm-core-feed40/proposal40.json']
    assert receipt['constructor_sha256'] == BOUND['candidate41/construct_dsm_clear41.py']
    for n in [before, after]:
        assert n['schema'] == 'kicad-native-copper/v1' and n['maximum_polygon_error_mm'] == .00001
        assert n['copper_error_location'] == 'ERROR_OUTSIDE' and n['pad_cut_error_location'] == 'ERROR_INSIDE'
        assert n['source_unchanged'] and n['units'] == 'mm'
    old, new = indexed(before), indexed(after)
    removed, added, changed = changes(before, after)
    assert (len(removed), len(added), len(changed)) == (5, 9, 6)
    assert removed == set(proposal['remove_track_uuids'])
    assert {o['uuid']: o for o in receipt['removed_source_records']} == {u: old[u] for u in removed}
    assert {o['uuid']: o for o in receipt['added_records']} == {u: new[u] for u in added}
    assert all(old[u]['kind'] == 'track' for u in removed)
    assert collections.Counter(old[u]['net'] for u in removed) == collections.Counter({'+3V3_CORE': 2, 'DSM_RX_EXT': 1, 'DSM_ILIM': 1, 'GND': 1})
    moves = {p['ref']: p for p in proposal['move_footprints']}
    assert set(moves) == {'R38', 'R70', 'C70'} and len(proposal['move_footprints']) == 3
    assert {p['before']['uuid'] for p in receipt['changed_pad_records']} == changed
    for pair in receipt['changed_pad_records']:
        uid = pair['before']['uuid']
        a, b = old[uid], new[uid]
        assert pair == {'before': a, 'after': b}
        assert a['kind'] == b['kind'] == 'pad' and a['ref'] in moves
        move = moves[a['ref']]
        assert move['before_pose'][2:] == move['after_pose'][2:]
        dx, dy = [move['after_pose'][i] - move['before_pose'][i] for i in range(2)]
        assert b == translate_record(a, dx, dy), 'Nontranslation pad change: ' + a['key']
    oldfp, newfp = indexed(before, 'footprints'), indexed(after, 'footprints')
    assert oldfp.keys() == newfp.keys()
    changedfp = {u for u in oldfp if oldfp[u] != newfp[u]}
    assert len(changedfp) == 3 and {oldfp[u]['ref'] for u in changedfp} == set(moves)
    assert {p['before']['uuid'] for p in receipt['changed_footprint_records']} == changedfp
    for pair in receipt['changed_footprint_records']:
        uid = pair['before']['uuid']
        a, b = oldfp[uid], newfp[uid]
        assert pair == {'before': a, 'after': b}
        move = moves[a['ref']]
        dx, dy = [move['after_pose'][i] - move['before_pose'][i] for i in range(2)]
        assert a['xy'] == move['before_pose'][:2] and b['xy'] == move['after_pose'][:2]
        assert b == translate_record(a, dx, dy), 'Nontranslation footprint change: ' + a['ref']
    expected_ids = set()
    for label, path in proposal['add_paths'].items():
        for i, (a, b) in enumerate(zip(path['points'], path['points'][1:])):
            uid = str(uuid.uuid5(uuid.NAMESPACE_URL, STAGE_SHA + '/' + receipt['proposal_sha256'] + '/' + label + '/' + str(i)))
            expected_ids.add(uid)
            t = new[uid]
            assert t['kind'] == 'track' and t['net'] == path['net']
            assert t['start'] == a and t['end'] == b and t['width'] == path['width']
            assert list(t['copper']) == [path['layer']]
    assert added == expected_ids and proposal['add_vias'] == []
    assert receipt['power_width_revision_explicit'] == {'net': '+3V3_CORE', 'before_width_mm': .3,
        'after_width_mm': .25, 'after_length_mm': proposal['add_paths']['CORE']['length_mm'], 'fresh_DC_required': True}
    unchanged = set(old) & set(new) - changed
    assert len(unchanged) == receipt['all_other_source_native_objects_exact'] == 1855
    zone = lambda z: {k: v for k, v in z.items() if k not in {'filled', 'fill_representation'}}
    assert list(map(zone, before['zones'])) == list(map(zone, after['zones']))
    for key in ['edge_cuts', 'outline_with_npth', 'copper_layers', 'copper_layer_ids', 'board_thickness_mm']:
        assert before[key] == after[key], key
    return {'passed': True, 'removed_count': 5, 'added_count': 9, 'translated_pad_count': 6,
            'translated_footprint_count': 3, 'other_source_objects_exact': 1855,
            'unchanged_uuid_record_digest': record_sha({u: old[u] for u in sorted(unchanged)})}


def composed_contract(before, stage, after, p40, r40, p41, r41):
    first = previous.source_contract(before, stage, p40, r40)
    second = check_stage41(stage, after, p41, r41)
    old, mid, new = [indexed(n) for n in [before, stage, after]]
    removed, added, changed = changes(before, after)
    assert (len(removed), len(added), len(changed)) == (8, 21, 6)
    oldfp, newfp = indexed(before, 'footprints'), indexed(after, 'footprints')
    fpchanged = {u for u in oldfp if oldfp[u] != newfp[u]}
    assert len(fpchanged) == 3
    for uid in changed:
        a, b = old[uid], new[uid]
        assert a['kind'] == b['kind'] == 'pad' and a['ref'] in {'R38', 'R70', 'C70'}
        assert b == translate_record(a, b['xy'][0] - a['xy'][0], b['xy'][1] - a['xy'][1])
    for uid in fpchanged:
        a, b = oldfp[uid], newfp[uid]
        assert b == translate_record(a, b['xy'][0] - a['xy'][0], b['xy'][1] - a['xy'][1])
    ephemeral = (set(mid) - set(old)) - set(new)
    assert ephemeral == {'021879e2-963d-5f8c-9894-8e9bd725f061'}
    assert all(old[u] == new[u] for u in p40['preserve_original_J12_branch_uuids'])
    preserved = sorted(set(old) & set(new) - changed)
    assert len(preserved) == 1843
    return {'passed': True, 'source39_to_isolated40': first, 'isolated40_to_candidate41': second,
            'removed_count': len(removed), 'added_count': len(added), 'translated_pad_count': len(changed),
            'translated_footprint_count': len(fpchanged), 'other_source_objects_exact': len(preserved),
            'unchanged_uuid_record_digest': record_sha({u: old[u] for u in preserved}),
            'stage40_added_then_removed_uuid': sorted(ephemeral),
            'original_J12_branch_uuids_exact': p40['preserve_original_J12_branch_uuids'],
            'translated_pads': [{'key': old[u]['key'], 'uuid': u, 'before_xy_mm': old[u]['xy'],
                                 'after_xy_mm': new[u]['xy'], 'before_record_sha256': record_sha(old[u]),
                                 'after_record_sha256': record_sha(new[u])} for u in sorted(changed)],
            'translated_footprints': [{'ref': oldfp[u]['ref'], 'uuid': u, 'before_xy_mm': oldfp[u]['xy'],
                                       'after_xy_mm': newfp[u]['xy'], 'before_record_sha256': record_sha(oldfp[u]),
                                       'after_record_sha256': record_sha(newfp[u])} for u in sorted(fpchanged)]}


def via_entry(track, via, layer, native):
    error = native['maximum_polygon_error_mm']
    actual = geom(via['copper'][layer]).buffer(-error).difference(geom(via['drill']['outside']))
    witnesses, overlap = annular_sections(track, actual, error)
    return {'passed': bool(witnesses), 'track_uuid': track['uuid'], 'via_uuid': via['uuid'],
            'net': track['net'], 'layer': layer, 'width_mm': track['width'],
            'actual_annular_centerline_length_mm': overlap, 'finite_full_width_annular_strips': witnesses,
            'outward_drill_void_subtracted': True, 'copper_inward_reserve_mm': error}


def endpoint_audit(before, after):
    old, new = indexed(before), indexed(after)
    tracks = [o for o in after['objects'] if o['kind'] == 'track']
    pads = [o for o in after['objects'] if o['kind'] == 'pad']
    vias = [o for o in after['objects'] if o['kind'] == 'via']
    added = [o for o in tracks if o['uuid'] not in old]
    entries, joins, annular, classified = [], [], [], []
    seen_entries, seen_joins, seen_annular = set(), set(), set()
    for track in added:
        required_width = .25 if track['net'] == '+3V3_CORE' or (track['net'] == 'GND' and track['uuid'] != R70_GND) else .2 if track['net'] == 'DSM_ILIM' or track['uuid'] == R70_GND else .127
        assert track['width'] == required_width
        for layer in track['copper']:
            for endpoint in ['start', 'end']:
                xy = track[endpoint]
                hitpads = [p for p in pads if p['net'] == track['net'] and layer in p['inside'] and geom(p['inside'][layer]).contains(Point(xy))]
                hittracks = [t for t in tracks if t['uuid'] != track['uuid'] and t['net'] == track['net'] and layer in t['copper'] and xy in [t['start'], t['end']]]
                hitvias = [v for v in vias if v['net'] == track['net'] and layer in v['copper'] and v['xy'] == xy]
                classified.append({'track_uuid': track['uuid'], 'net': track['net'], 'endpoint': endpoint,
                    'layer': layer, 'xy_mm': xy, 'required_width_mm': required_width,
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
                        joins.append(join_entry(track, t, layer, required_width))
                for via in hitvias:
                    key = track['uuid'], via['uuid'], layer
                    if key not in seen_annular:
                        seen_annular.add(key)
                        annular.append(via_entry(track, via, layer, after))
    # Every retained track terminating inside each moved pad must also be audited.
    moved = [p for p in pads if p['uuid'] in old and old[p['uuid']] != p]
    moved_inventory = []
    for pad in moved:
        matches = []
        for track in tracks:
            if track['net'] != pad['net']:
                continue
            for layer in track['copper'].keys() & pad['inside'].keys():
                for endpoint in ['start', 'end']:
                    if geom(pad['inside'][layer]).contains(Point(track[endpoint])):
                        matches.append({'track_uuid': track['uuid'], 'layer': layer, 'endpoint': endpoint})
                        key = track['uuid'], pad['uuid'], layer, endpoint
                        if key not in seen_entries:
                            seen_entries.add(key)
                            entry = pad_entry(track, pad, layer, endpoint)
                            entry['retained_source_track_exact'] = track['uuid'] in old and track == old[track['uuid']]
                            entries.append(entry)
        # The short final DSM segment sits wholly inside R38.1: both ends,
        # plus the preceding bend's end, are independently checked.
        expected_count = {'R38.1': 3, 'R38.2': 0, 'R70.1': 1, 'R70.2': 1, 'C70.1': 1, 'C70.2': 1}
        assert len(matches) == expected_count[pad['key']], (pad['key'], matches)
        moved_inventory.append({'pad': pad['key'], 'track_entries': matches,
                                'status': 'existing_open_MCU_continuation' if pad['key'] == 'R38.2' else 'entry_audited'})
    return entries, joins, annular, classified, moved_inventory


def cap_in_retained_copper(track, endpoint, retained, layer, native):
    """Finite full endpoint disk inclusion, with stated export error deducted."""
    xy, radius = track[endpoint], track['width'] / 2
    actual = unary_union([geom(o['copper'][layer]).buffer(-native['maximum_polygon_error_mm']) for o in retained])
    center = Point(xy)
    reserve = center.distance(actual.boundary) - radius
    # Distance to boundary proves containment of the complete analytic disk,
    # not only an inscribed polygonal approximation to that disk.
    passed = actual.contains(center) and reserve > 0
    return {'passed': passed, 'track_uuid': track['uuid'], 'endpoint': endpoint, 'xy_mm': xy,
            'required_full_disk_diameter_mm': track['width'], 'analytic_disk_area_mm2': math.pi * radius ** 2,
            'retained_uuids': [o['uuid'] for o in retained], 'native_widths_mm': [o['width'] for o in retained],
            'full_analytic_disk_in_conservative_retained_copper': passed, 'minimum_radial_reserve_mm': reserve,
            'copper_inward_reserve_mm': native['maximum_polygon_error_mm']}


def new_r38_junction(after):
    """One explicit finite new-track/pad corridor; never a general exemption."""
    new = indexed(after)
    incoming = new['eab3f753-c84f-52be-b8d6-98fc84242d63']
    continuation = new['ace32a9d-722d-57a5-9890-0e87e2a8f1a5']
    pad = new['7c18f691-25a4-435e-a236-e074e113b363']
    assert pad['key'] == 'R38.1' and pad['xy'] == [17.09, 23.46]
    assert incoming['start'] == [16.7, 23.59] and incoming['end'] == continuation['start'] == [16.83, 23.46]
    assert continuation['end'] == pad['xy']
    assert incoming['width'] == continuation['width'] == .127
    assert incoming['net'] == continuation['net'] == pad['net'] == 'DSM_RX_EXT'
    assert list(incoming['copper']) == list(continuation['copper']) == ['B.Cu']
    direct = pad_entry(incoming, pad, 'B.Cu', 'end')
    assert not direct['passed'], 'Preserve the actual direct-entry failure'
    entries = [pad_entry(continuation, pad, 'B.Cu', ep) for ep in ['start', 'end']]
    join = join_entry(incoming, continuation, 'B.Cu', .127)
    error = after['maximum_polygon_error_mm']
    incoming_actual = geom(incoming['copper']['B.Cu']).buffer(-error)
    continuation_actual = geom(continuation['copper']['B.Cu']).buffer(-error)
    pad_actual = geom(pad['inside']['B.Cu'])
    actual = incoming_actual.union(continuation_actual).union(pad_actual)
    start, end = [16.81, 23.48], pad['xy']
    length = math.dist(start, end)
    direction = [(end[i] - start[i]) / length for i in range(2)]
    normal = [-direction[1], direction[0]]
    aa, bb = [section_at(q, normal, .127 / 2) for q in [start, end]]
    strip = Polygon([aa.coords[0], aa.coords[1], bb.coords[1], bb.coords[0]])
    missing = strip.difference(actual).area
    start_missing, end_missing = aa.difference(incoming_actual).length, bb.difference(pad_actual).length
    reserve = strip.distance(actual.boundary)
    passed = (join['passed'] and all(e['passed'] for e in entries) and missing <= 1e-12
              and start_missing <= 1e-8 and end_missing <= 1e-8 and reserve > error)
    middle = [(start[i] + end[i]) / 2 for i in range(2)]
    notched = actual.difference(section_at(middle, normal, .2).buffer(.005, cap_style=2))
    broken = strip.difference(notched).area
    control = {'name': 'R38_corridor_internal_cut_rejected_despite_intact_terminal_sections',
               'rejected': broken > 1e-12 and aa.difference(notched).length <= 1e-8 and bb.difference(notched).length <= 1e-8,
               'strip_area_outside_notched_copper_mm2': broken}
    return {'passed': passed, 'classification': 'exact_new_track_junction_with_finite_full_width_actual_copper_corridor',
            'pad': 'R38.1', 'incoming_track_uuid': incoming['uuid'], 'continuation_track_uuid': continuation['uuid'],
            'incoming_record_sha256': record_sha(incoming), 'continuation_record_sha256': record_sha(continuation),
            'actual_pad_record_sha256': record_sha(pad), 'direct_incoming_transverse_entry_remains_false': True,
            'direct_entry_witness': direct, 'continuation_strict_pad_entries': entries, 'full_width_track_join': join,
            'full_width_actual_copper_corridor': {'width_mm': .127, 'length_mm': length, 'centerline_mm': [start, end],
                'polygon_mm': list(strip.exterior.coords), 'area_outside_actual_copper_mm2': missing,
                'minimum_boundary_reserve_mm': reserve, 'start_section_mm': list(aa.coords), 'end_section_mm': list(bb.coords),
                'start_section_missing_from_incoming_track_mm': start_missing, 'end_section_missing_from_actual_pad_mm': end_missing,
                'track_polygon_inward_reserve_mm': error, 'pad_geometry': 'native ERROR_INSIDE'},
            'scope': 'Only the named R38.1 incoming end is classified here. Both direct failures remain false. The separate retained R26 source-bound criterion is unchanged.'}, control


def c70_review(before, after, entries):
    old, new = indexed(before), indexed(after)
    pads = {p['key']: p for p in after['objects'] if p['kind'] == 'pad'}
    rows = []
    for key, uid in C70_TRACKS.items():
        pad, track = pads[key], new[uid]
        assert track == old[uid]
        assert track['width'] == (.3 if key == 'C70.1' else .4)
        es = [e for e in entries if e['pad'] == key and e['track_uuid'] == uid]
        assert len(es) == 1
        actual, center = geom(pad['inside']['B.Cu']), Point(es[0]['xy_mm'])
        reserve = center.distance(actual.boundary) - track['width'] / 2
        rows.append({'pad': key, 'track_uuid': uid, 'source39_track_exact': True, 'track_record_sha256': record_sha(track),
                     'width_mm': track['width'], 'strict_entry': es[0], 'full_endpoint_disk_reserve_mm': reserve,
                     'passed': es[0]['passed'] and reserve > 0})
    return {'passed': all(r['passed'] for r in rows), 'entries': rows,
            'pad_translation_mm': [0, .06], 'C4_pad_and_footprint_records_exact':
            all(new[u] == o for u, o in old.items() if o.get('ref') == 'C4') and
            all(indexed(before, 'footprints')[u] == o for u, o in indexed(after, 'footprints').items() if o.get('ref') == 'C4'),
            'qualification': 'Retained supply/ground copper and finite pad entries only; transient decoupling not qualified.'}


def power_topology(before, after):
    old, new = indexed(before), indexed(after)
    core_new = [o for u, o in new.items() if u not in old and o['net'] == '+3V3_CORE']
    assert len(core_new) == 4 and all(o['width'] == .25 for o in core_new)
    source_cut = dict(before, objects=[o for o in before['objects'] if o['uuid'] not in CORE_OLD])
    final_cut = dict(after, objects=[o for o in after['objects'] if o not in core_new])
    a, b = groups(source_cut, '+3V3_CORE'), groups(final_cut, '+3V3_CORE')
    assert a == b and len(a) == 2
    isolated = ['C4.1', 'C6.1', 'U1.1', 'U1.64', 'U13.5']
    assert isolated in [g['pads'] for g in a]
    source_group = next(g for g in a if g['pads'] != isolated)
    assert 'U11.4' in source_group['pads']
    full = groups(after, '+3V3_CORE')
    assert len(full) == 1 and len(full[0]['pad_uuids']) == 47 and len(set(full[0]['pads'])) == 46
    transitions = []
    for track in core_new:
        for endpoint in ['start', 'end']:
            retained = [o for u, o in new.items() if u in old and o['kind'] == 'track' and o['net'] == '+3V3_CORE'
                        and 'B.Cu' in o['copper'] and track[endpoint] in [o['start'], o['end']]]
            if retained:
                assert all(o == old[o['uuid']] and o['width'] == .3 for o in retained)
                transitions.append(cap_in_retained_copper(track, endpoint, retained, 'B.Cu', after))
    assert len(transitions) == 2
    return {'passed': a == b and all(t['passed'] for t in transitions),
            'CORE_distinct_pad_key_count': 46, 'CORE_native_pad_object_count': 47,
            'restored_single_CORE_group': full,
            'before_and_after_bridge_removed_pad_groups_equal': True, 'bridge_removed_pad_groups': a,
            'downstream_pad_keys': isolated, 'U11_4_and_DSM_supply_remain_on_source_side': True,
            'new_width_mm': .25, 'new_length_mm': sum(math.dist(t['start'], t['end']) for t in core_new),
            'removed_width_mm': .3, 'removed_length_mm': sum(math.dist(old[u]['start'], old[u]['end']) for u in CORE_OLD),
            'full_width_retained_feed_transitions': transitions, 'chip_internal_conduction_assumed': False,
            'numerical_power_VCAP_applicable': False, 'fresh_source_bound_numerical_power': 'pending_separately_owned',
            'qualification': 'Geometry and copper-only topology. No CORE voltage floor is inferred; classic DSM floor is not applied to CORE sinks.'}


def r70_return(after, annular):
    new = indexed(after)
    track = new[R70_GND]
    contact = next(a for a in annular if a['track_uuid'] == R70_GND)
    via = new[contact['via_uuid']]
    pad = next(o for o in after['objects'] if o.get('key') == 'R70.2')
    direct = make_graph([pad, track, via])
    gnd = make_graph(objects(after, 'GND'))
    joined = [g for g in gnd if {pad['uuid'], via['uuid']} <= {n['object']['uuid'] for n in g}]
    assert len(direct) == len(joined) == 1
    drills = unary_union([geom(o['drill']['outside']) for o in after['objects'] if o.get('drill')])
    planes = []
    for layer in ['In1.Cu', 'In4.Cu']:
        fill = unary_union([geom(z['filled'][layer]) for z in after['zones'] if not z['rule'] and z['net'] == 'GND' and layer in z['filled']])
        actual = fill.buffer(-after['maximum_polygon_error_mm'], join_style=2).difference(drills)
        annulus = geom(via['copper'][layer]).buffer(-after['maximum_polygon_error_mm']).difference(geom(via['drill']['outside']))
        corridor = plane_corridor(actual, annulus, via['xy'])
        missing = annulus.difference(actual).area
        zones = sorted({n['object']['uuid'] for n in joined[0] if n['layer'] == layer and n['object']['kind'] == 'zone'})
        planes.append({'layer': layer, 'passed': missing <= 1e-12 and corridor is not None and bool(zones),
                       'annulus_outside_saved_plane_mm2': missing, 'full_width_025mm_plane_corridor': corridor,
                       'connected_saved_zone_uuids': zones, 'all_drill_voids_subtracted': True})
    return {'passed': contact['passed'] and all(p['passed'] for p in planes), 'track_uuid': R70_GND,
            'width_mm': .2, 'direct_pad_track_via_graph': len(direct) == 1, 'via_uuid': via['uuid'],
            'actual_annular_entry': contact, 'saved_planes': planes,
            'length_mm': math.dist(track['start'], track['end'])}


def rejected(name, callback):
    try:
        result = callback()
        return {'name': name, 'rejected': False, 'unexpected_result': result}
    except (AssertionError, KeyError) as exc:
        return {'name': name, 'rejected': True, 'reason': str(exc) or type(exc).__name__}


def negative_controls(before, stage, after, p40, r40, p41, r41, joins, cut_contract, annular, r26_control):
    new = indexed(after)
    controls = [r26_control]
    for label in ['removed', 'narrowed']:
        mutant = copy.deepcopy(after)
        if label == 'removed':
            mutant['objects'] = [o for o in mutant['objects'] if o['uuid'] != R26_RETAINED]
        else:
            t = indexed(mutant)[R26_RETAINED]
            replacement = synthetic_track(t['start'], t['end'], .1, t['net'], 'F.Cu')
            t['width'], t['copper'] = replacement['width'], replacement['copper']
        controls.append(rejected('R26_required_retained_entry_' + label + '_rejected', lambda: retained_r26_entry(before, mutant)))
    d7 = next(o for o in after['objects'] if o.get('key') == 'D7.2')
    tangent = pad_entry(synthetic_track(d7['xy'], [16.4, 24.2], .25), d7, 'B.Cu', 'start')
    controls.append({'name': 'D7_025mm_pad_height_horizontal_tangency_rejected', 'rejected': not tangent['passed'], 'witness': tangent})
    via = next(o for o in after['objects'] if o['uuid'] not in indexed(before) and o['kind'] == 'via')
    ring = geom(via['copper']['B.Cu']).buffer(-after['maximum_polygon_error_mm']).difference(geom(via['drill']['outside']))
    spur = synthetic_track(via['xy'], [via['xy'][0] + .02, via['xy'][1]], .025)
    ws, overlap = annular_sections(spur, ring, after['maximum_polygon_error_mm'])
    controls.append({'name': 'drill_only_center_contact_rejected', 'rejected': not ws and overlap == 0,
                     'actual_centerline_overlap_mm': overlap, 'strip_count': len(ws)})
    # All inventory/pose controls exercise the complete composed contract.
    mutations = [
        ('unlisted_retained_track_mutation_rejected', R26_RETAINED, 'width', .199),
        ('translated_pad_net_mutation_rejected', 'd95d58d3-c100-4822-ba4d-4080cfbfe943', 'net', 'GND'),
        ('new_CORE_track_width_mutation_rejected', '482e48d7-c868-5052-94a6-1564f1c48451', 'width', .249),
        ('new_CORE_track_layer_mutation_rejected', '482e48d7-c868-5052-94a6-1564f1c48451', 'copper',
         {'F.Cu': new['482e48d7-c868-5052-94a6-1564f1c48451']['copper']['B.Cu']}),
        ('C70_pad_pose_mutation_rejected', 'ef7c7be8-9ad0-45d5-a891-4e7eb739bf9e', 'xy', [19.225, 24.661]),
        ('new_R70_GND_width_mutation_rejected', R70_GND, 'width', .199),
        ('retained_C70_supply_mutation_rejected', C70_TRACKS['C70.1'], 'width', .299),
    ]
    contract = lambda n: composed_contract(before, stage, n, p40, r40, p41, r41)
    for name, uid, field, value in mutations:
        mutant = copy.deepcopy(after)
        indexed(mutant)[uid][field] = value
        controls.append(rejected(name, lambda: contract(mutant)))
    mutant = copy.deepcopy(after)
    fp = next(f for f in mutant['footprints'] if f['ref'] == 'C70')
    fp['xy'][1] += .001
    controls.append(rejected('C70_footprint_pose_mutation_rejected', lambda: contract(mutant)))
    mutant = dict(after, objects=after['objects'] + [indexed(before)[next(iter(sorted(CORE_OLD)))]])
    controls.append(rejected('removed_source_CORE_object_restored_rejected', lambda: contract(mutant)))
    mutant = dict(after, objects=[o for o in after['objects'] if o['uuid'] != '482e48d7-c868-5052-94a6-1564f1c48451'])
    controls.append(rejected('new_CORE_object_missing_rejected', lambda: contract(mutant)))
    mutant = dict(after, objects=after['objects'] + [synthetic_track([1, 1], [2, 2], .25, '+3V3_CORE')])
    controls.append(rejected('undeclared_new_object_rejected', lambda: contract(mutant)))
    for net, threshold in [('SBUS_HV', .127), ('+3V3_CORE', .25)]:
        join = next(j for j in joins if j['net'] == net)
        a, b = [new[u] for u in join['track_uuids']]
        short = synthetic_track(a['start'], a['end'], threshold - .01, a['net'], join['layer'])
        witness = join_entry(short, b, join['layer'], threshold)
        controls.append({'name': net + '_shared_center_narrow_join_rejected', 'rejected': not witness['passed'], 'witness': witness})
    mutant = dict(after, objects=[o for o in after['objects'] if o['uuid'] != R70_ILIM])
    broken = groups(mutant, 'DSM_ILIM')
    controls.append({'name': 'R70_support_disconnect_rejected', 'rejected': len(broken) != 1, 'pad_groups': broken})
    mutant = dict(after, objects=after['objects'] + [synthetic_track([15.38, 23.82448], [16.26, 23.59], .127, 'DSM_RX_EXT')])
    bypass = run_check(mutant, cut_contract)
    controls.append({'name': 'outside_D7_pad_bypass_rejected', 'rejected': not bypass['complete_clamp_first_path_passes'],
                     'connected_after_cut': not bypass['source_target_physically_disconnected_after_removing_actual_pad_copper'],
                     'after_cut_pad_groups': bypass['after_cut_pad_groups']})
    x, y = via['xy']
    outer = geom(via['copper']['B.Cu']).buffer(-after['maximum_polygon_error_mm'])
    drill = geom(via['drill']['outside'])
    bulk = Polygon([(x + .55, y - 1), (x + 2, y - 1), (x + 2, y + 1), (x + .55, y + 1)])
    neck = LineString([[x, y], [x + .65, y]]).buffer(.1, cap_style=2)
    narrow = outer.union(neck).union(bulk).difference(drill)
    witness = plane_corridor(narrow, ring, via['xy'])
    controls.append({'name': '020mm_saved_plane_neck_rejected', 'rejected': witness is None, 'witness': witness})
    witness = plane_corridor(ring, ring, via['xy'])
    controls.append({'name': 'isolated_saved_annulus_rejected', 'rejected': witness is None, 'witness': witness})
    # Separate geometric controls go beyond the immutable-record checks.
    core = next(o for o in after['objects'] if o['net'] == '+3V3_CORE' and o['uuid'] not in indexed(before))
    point = core['end']
    a = synthetic_track([point[0] - .5, point[1]], point, .25, '+3V3_CORE')
    b = synthetic_track([point[0] + .18, point[1]], [point[0] + .5, point[1]], .25, '+3V3_CORE')
    witness = join_entry(a, b, 'B.Cu', .25)
    controls.append({'name': 'CORE_positive_sliver_overlap_without_exact_junction_rejected',
                     'rejected': not witness['passed'] and witness['native_polygon_overlap_mm2'] > 0, 'witness': witness})
    c70 = next(o for o in after['objects'] if o.get('key') == 'C70.2')
    t = new[C70_TRACKS['C70.2']]
    moved = translate_record(c70, 0, .6)
    ep = next(ep for ep in ['start', 'end'] if geom(c70['inside']['B.Cu']).contains(Point(t[ep])))
    witness = pad_entry(t, moved, 'B.Cu', ep)
    controls.append({'name': 'C70_shifted_pad_losing_full_entry_rejected', 'rejected': not witness['passed'], 'witness': witness})
    contact = next(a for a in annular if a['track_uuid'] == R70_GND)
    rv = new[contact['via_uuid']]
    drill_contact = synthetic_track(rv['xy'], [rv['xy'][0] + .02, rv['xy'][1]], .025)
    witness = via_entry(drill_contact, rv, 'B.Cu', after)
    controls.append({'name': 'R70_drill_only_return_contact_rejected', 'rejected': not witness['passed'], 'witness': witness})
    return controls


def main():
    check_files()
    before, stage, after = [read(d / 'f722-heli.native.json') for d in [SOURCE, STAGE, CANDIDATE]]
    p40, r40 = [read(STAGE / p) for p in ['coordinated-route-proposal.json', 'construction-provenance.json']]
    p41, r41 = [read(CANDIDATE / p) for p in ['proposal40.json', 'construction-provenance.json']]
    contract = composed_contract(before, stage, after, p40, r40, p41, r41)
    print('Exact coordinated source39 -> 40 -> 41 contract passed', flush=True)
    entries, joins, annular, endpoints, moved = endpoint_audit(before, after)
    r26, r26_control = retained_r26_entry(before, after)
    r38, r38_control = new_r38_junction(after)
    direct_failures = [e for e in entries if not e['passed']]
    exact_r26 = lambda e: e['track_uuid'] == R26_IN and e['pad'] == 'R26.2' and e['layer'] == 'F.Cu' and e['endpoint'] == 'start'
    exact_r38 = lambda e: e['track_uuid'] == 'eab3f753-c84f-52be-b8d6-98fc84242d63' and e['pad'] == 'R38.1' and e['layer'] == 'B.Cu' and e['endpoint'] == 'end'
    assert len(direct_failures) == 2 and sum(map(exact_r26, direct_failures)) == sum(map(exact_r38, direct_failures)) == 1
    entry_pass = all(e['passed'] or (exact_r26(e) and r26['passed']) or (exact_r38(e) and r38['passed']) for e in entries)
    print('Entry inventory: %d pad entries, %d joins, %d annular entries, %d endpoints' % (len(entries), len(joins), len(annular), len(endpoints)), flush=True)
    base = read(SOURCE / 'power-audit.json')
    assert base['passed'] and base['board_sha256'] == SOURCE_SHA and len(base['nets']) == 28
    support = {}
    for net in base['nets']:
        a, b = groups(before, net), groups(after, net)
        assert a == base['nets'][net]['groups'], 'Baseline support mismatch: ' + net
        support[net] = {'passed': a == b and len(b) == 1, 'groups': b, 'source_groups_exactly_preserved': a == b}
    topology = {}
    for net in ['RPM_LV', 'SBUS_HV', 'DSM_RX_MCU', 'GND']:
        a, b = groups(before, net), groups(after, net)
        topology[net] = {'passed': a == b, 'before_groups': a, 'after_groups': b}
    dsm = groups(after, 'DSM_RX_EXT')
    topology['DSM_RX_EXT'] = {'passed': len(dsm) == 1 and dsm[0]['pads'] == ['D7.1', 'J12.3', 'R38.1'], 'after_groups': dsm}
    c70 = c70_review(before, after, entries)
    power = power_topology(before, after)
    old = indexed(before)
    d7_selected = [o for o in after['objects'] if o['uuid'] not in old and o['net'] == 'GND' and o['uuid'] != R70_GND]
    assert len(d7_selected) == 3
    ground = return_proof(after, d7_selected)
    r70 = r70_return(after, annular)
    cut_contract = {'net': 'DSM_RX_EXT', 'clamp': 'D7.1', 'source': 'J12.3', 'target': 'R38.1', 'minimum_gap_required_mm': .127}
    cut = run_check(after, cut_contract)
    controls = negative_controls(before, stage, after, p40, r40, p41, r41, joins, cut_contract, annular, r26_control)
    controls.append(r38_control)
    for label in ['removed', 'narrowed']:
        mutant = copy.deepcopy(after)
        uid = 'ace32a9d-722d-57a5-9890-0e87e2a8f1a5'
        if label == 'removed':
            mutant['objects'] = [o for o in mutant['objects'] if o['uuid'] != uid]
        else:
            indexed(mutant)[uid]['width'] = .126
        controls.append(rejected('R38_required_new_continuation_' + label + '_rejected', lambda: new_r38_junction(mutant)))
    oldmap, newmap = [read(d / 'f722-heli.logical-route-map.json') for d in [SOURCE, CANDIDATE]]
    assert oldmap['board_sha256'] == SOURCE_SHA and newmap['board_sha256'] == FINAL_SHA
    om, nm = oldmap['logical_route_map'], newmap['logical_route_map']
    new = indexed(after)
    removed, added, changed = changes(before, after)
    assert all(om.get(u) == nm.get(u) for u in set(old) & set(new))
    assert not set(nm) - set(new)
    stage_summary = read(STAGE / 'owner-summary.json')
    stage_drc = read(STAGE / 'owner-drc-all.json')
    assert stage_summary['board_sha256'] == STAGE_SHA and stage_summary['drc-all'] == {'unconnected': 41, 'errors': 3, 'warnings': 0}
    assert len(stage_drc['violations']) == 3 and all(v['type'] == 'courtyards_overlap' and v['severity'] == 'error' for v in stage_drc['violations'])
    actual_io = read(CANDIDATE / 'protection-actual-io.json')
    assert actual_io['board_sha256'] == FINAL_SHA and actual_io['geometry_sha256'] == BOUND['candidate41/f722-heli.native.json']
    assert actual_io['profile'] == 'actual-bonded-signal-io-22' and actual_io['passed'] == 11 and actual_io['total'] == 22
    assert not actual_io['all_pass'] and actual_io['source_unchanged']
    check_files()
    gates = {'exact_composed_source_contract': contract['passed'],
        'strict_pad_entries_or_two_explicit_finite_corridors': entry_pass,
        'all_changed_track_junctions_full_required_width': all(j['passed'] for j in joins),
        'all_changed_via_entries_finite_actual_annular_strips': all(a['passed'] for a in annular),
        'all_new_endpoints_resolved': all(e['resolved'] for e in endpoints),
        'all_28_support_groups_preserved': all(s['passed'] for s in support.values()),
        'signal_and_ground_topology': all(t['passed'] for t in topology.values()),
        'C70_retained_supply_ground_entries': c70['passed'] and c70['C4_pad_and_footprint_records_exact'],
        'changed_CORE_feed_geometry_and_topology': power['passed'], 'R70_return': r70['passed'],
        'dedicated_D7_return': ground['passed'], 'actual_D7_cut': cut['complete_clamp_first_path_passes'],
        'negative_controls': all(c['rejected'] for c in controls), 'inputs_rechecked_unchanged': True}
    report = {'schema': 'f722-dsm41-entry-return-audit/v1', 'passed': all(gates.values()), 'gates': gates,
        'source_board_sha256': SOURCE_SHA, 'isolated_stage_board_sha256': STAGE_SHA, 'candidate_board_sha256': FINAL_SHA,
        'script_sha256': sha(__file__), 'input_manifest_sha256': sha(MANIFEST), 'input_hashes': BOUND,
        'source_change_contract': contract, 'strict_pad_entries': entries, 'ordinary_support_CORE_track_joins': joins,
        'finite_actual_annular_entries': annular, 'direct_pad_entry_failures_preserved': direct_failures,
        'explicit_retained_R26_junction': r26, 'explicit_new_R38_junction': r38, 'new_endpoint_classification': endpoints,
        'moved_pad_entry_inventory': moved, 'support_nets': support, 'signal_and_ground_topology': topology,
        'C70_retained_entries': c70, 'changed_CORE_feed': power, 'R70_ground_return': r70,
        'dedicated_D7_ground_return': ground, 'actual_D7_pad_cut': cut, 'negative_controls': controls,
        'isolated_stage40_not_accepted': {'board_sha256': STAGE_SHA, 'native_DRC': stage_summary['drc-all'],
            'rejected_courtyard_violations': stage_drc['violations'], 'accepted_as_intermediate': False},
        'numerical_power_VCAP_applicable': False, 'adoption_claimed': False,
        'complete_actual_io_report': {'path': 'candidate41/protection-actual-io.json',
            'sha256': BOUND['candidate41/protection-actual-io.json'], 'passed': 11, 'total': 22, 'all_pass': False,
            'scope': 'Separately owned complete 22-case report; its 11 unfinished paths are not made passing by this scoped DSM audit.'},
        'limits': ['Nominal native geometry and saved-fill continuity/width only. No ESD transient, numerical loaded-power, impedance, inductance, thermal, assembly, or manufacturing-tolerance qualification.',
                   'Source39 and isolated source40 are immutable. Complete candidate41 geometry is checked directly against accepted source39 and the two exact construction stages; source40 is not accepted by chaining.',
                   'Fresh numerical sheet/barrel and VCAP validation remains separately owned. New CORE width is explicitly .25 mm, previously .30 mm; this report gives no voltage-budget pass.',
                   'Native DRC, process, reference, parity, mechanical and adoption gates remain separately owned. R38.2 MCU continuation and existing SBUS/DSM MCU pad partitions remain open.']}
    output = HERE / 'candidate41-entry-return.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    oldfp, newfp = indexed(before, 'footprints'), indexed(after, 'footprints')
    changedfp = {u for u in oldfp if oldfp[u] != newfp[u]}
    receipt = {'schema': 'f722-explicit-coordinated-native-transaction/v1', 'passed': report['passed'],
        'source_board_sha256': SOURCE_SHA, 'board_sha256': FINAL_SHA,
        'source_native_sha256': BOUND['candidate39/f722-heli.native.json'], 'candidate_native_sha256': BOUND['candidate41/f722-heli.native.json'],
        'source_map_sha256': BOUND['candidate39/f722-heli.logical-route-map.json'], 'candidate_map_sha256': BOUND['candidate41/f722-heli.logical-route-map.json'],
        'removed_source_records': [old[u] for u in sorted(removed)], 'added_candidate_records': [new[u] for u in sorted(added)],
        'changed_pad_records': [{'before': old[u], 'after': new[u]} for u in sorted(changed)],
        'changed_footprint_records': [{'before': oldfp[u], 'after': newfp[u]} for u in sorted(changedfp)],
        'removed_logical_owners': {u: om.get(u) for u in sorted(removed)}, 'added_logical_owners': {u: nm.get(u) for u in sorted(added)},
        'all_other_source_objects_exact': 1843, 'all_retained_logical_owners_exact': True,
        'all_poses_pads_outline_layers_exact': False,
        'all_undeclared_poses_pads_outline_layers_exact': True, 'declared_pad_translations': 6, 'declared_footprint_translations': 3,
        'removed_counts': dict(collections.Counter(old[u]['kind'] + ':' + old[u]['net'] for u in removed)),
        'added_counts': dict(collections.Counter(new[u]['kind'] + ':' + new[u]['net'] for u in added)),
        'staged_provenance': {'accepted_origin_board_sha256': SOURCE_SHA, 'isolated_stage_board_sha256': STAGE_SHA,
            'isolated_stage_not_accepted': True, 'isolated_stage_rejected_courtyard_errors': 3,
            'source39_to40_construction_receipt_sha256': BOUND['candidate40/construction-provenance.json'],
            'source40_to41_construction_receipt_sha256': BOUND['candidate41/construction-provenance.json'],
            'source40_DRC_sha256': BOUND['candidate40/owner-drc-all.json'],
            'stage40_added_then_removed_uuid': contract['stage40_added_then_removed_uuid']},
        'dedicated_ground_change': 'New dedicated D7.2 .25 mm return pair and .45/.20 mm tented via; R70 .20 mm GND track replaced after pad translation; C70 .40 mm ground track retained with a finite full-width translated-pad entry.',
        'changed_power_feed': power,
        'ground_return_complete_receipt': 'candidate41-entry-return.json', 'ground_return_complete_receipt_sha256': sha(output),
        'complete_rewritten_entry_receipt_sha256': sha(output),
        'scoped_D7_actual_pad_cut_receipt_sha256': sha(output),
        'actual_io_receipt': 'protection-actual-io.json', 'actual_io_receipt_sha256': BOUND['candidate41/protection-actual-io.json'],
        'actual_io_passed': 11, 'actual_io_total': 22, 'actual_io_all_pass': False,
        'script_sha256': sha(__file__), 'input_manifest_sha256': sha(MANIFEST),
        'engine_success_claimed': False, 'numerical_power_VCAP_applicable': False, 'fresh_numerical_power_required': True,
        'adoption_claimed': False}
    (HERE / 'coordinated-change-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'gates': gates, 'pad_entries': len(entries), 'joins': len(joins),
        'annular_entries': len(annular), 'endpoints': len(endpoints), 'support_nets': len(support),
        'negative_controls': len(controls), 'control_failures': [c['name'] for c in controls if not c['rejected']],
        'D7_outside_pad_gap_mm': cut['minimum_gap_measured_mm'], 'D7_return_length_mm': ground['centerline_length_mm'],
        'report': str(output)}, indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
