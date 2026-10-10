#!/usr/bin/env python3
"""Read-only exact candidate43 -> candidate44 DSM tree geometry audit.

Imports proved geometry primitives without invoking their main entrypoints.
The audit writes only its own receipt. Negative controls mutate private records.
No native-board, canonical, Git, JVM, or numerical-power operations are performed.
Run from ordinary-routing: PYTHONPATH=../python-deps python3.12 dsm44-audits/audit_dsm44_entries_support.py
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
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT.parent / 'python-deps'), str(ROOT / 'dsm40-audits'), str(ROOT / 'dsm41-audits')]
from audit_dsm40_entries_return import geom, groups, join_entry, pad_entry, record_sha, run_check, synthetic_track
from audit_dsm41_entries_return import via_entry
from shapely.geometry import Point

SOURCE = ROOT / 'candidate43'
CANDIDATE = ROOT / 'candidate44'
SOURCE_SHA = '1ee7174a578dffe4d5ef3ae8b39d8dc88f28b80395539263a65f23be234c21e6'
CANDIDATE_SHA = '02d2090ad7220a64a8f4a1a259d522f7b0bca3e15214b73107491d17626bd51f'
PROPOSAL_SHA = '9798bd44a63920ff5e561d7e570b73684050eb5ee330f7e4314b42e2dd13a4ac'
MANIFEST = HERE / 'input-hashes.json'
read = lambda path: json.loads(Path(path).read_text())
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()


def indexed(native):
    result = {obj['uuid']: obj for obj in native['objects']}
    assert len(result) == len(native['objects']), 'Duplicate object UUID'
    return result


def check_files():
    bound = read(MANIFEST)
    for relative, digest in bound.items():
        assert sha(ROOT / relative) == digest, 'Bound input changed: ' + relative
    return bound


def exact_contract(before, after, proposal, receipt, source_map, candidate_map):
    assert before['board_sha256'] == SOURCE_SHA and after['board_sha256'] == CANDIDATE_SHA
    assert before['source_unchanged'] and after['source_unchanged']
    assert receipt['source_board_sha256'] == proposal['source_board_sha256'] == SOURCE_SHA
    assert receipt['board_sha256'] == CANDIDATE_SHA
    assert receipt['source_native_sha256'] == proposal['source_native_sha256'] == sha(SOURCE / 'f722-heli.native.json')
    assert receipt['source_map_sha256'] == sha(SOURCE / 'f722-heli.logical-route-map.json')
    assert receipt['proposal_sha256'] == sha(CANDIDATE / 'complete-tree-proposal.json') == PROPOSAL_SHA
    assert receipt['constructor_sha256'] == sha(CANDIDATE / 'construct_dsm_tree44.used.py')
    old, new = indexed(before), indexed(after)
    removed, added = set(old) - set(new), set(new) - set(old)
    retained = set(old) & set(new)
    assert removed == set(proposal['remove_copper_uuids']) == {obj['uuid'] for obj in receipt['removed_source_records']}
    assert len(removed) == 2 and all(old[u]['kind'] == 'track' and old[u]['net'] == '+5V_BEC' and old[u]['width'] == .6 for u in removed)
    assert all(obj == old[obj['uuid']] for obj in receipt['removed_source_records'])
    assert added == {obj['uuid'] for obj in receipt['added_records']} and len(added) == 37
    assert all(obj == new[obj['uuid']] for obj in receipt['added_records'])
    assert len(retained) == 1902 and all(old[u] == new[u] for u in retained), 'A retained source object changed'
    assert len(before['footprints']) == len(after['footprints']) == 156
    for key in set(before) - {'board_sha256', 'objects', 'zones'}:
        assert before[key] == after[key], 'Source native metadata changed: ' + key
    strip_fill = lambda z: {key: value for key, value in z.items() if key not in ['filled', 'fill_representation']}
    assert list(map(strip_fill, before['zones'])) == list(map(strip_fill, after['zones'])), 'Zone definition changed'
    assert proposal['footprint_changes'] == receipt['changed_pad_records'] == receipt['changed_footprint_records'] == []
    assert receipt['all_other_source_native_objects_exact'] == 1902
    assert receipt['all_156_footprints_exact'] and receipt['all_existing_signal_objects_exact'] and receipt['all_GND_native_objects_exact']
    assert receipt['BEC_width_preserved_mm'] == .6
    expected = {}
    for path in proposal['paths']:
        assert path['net'] in ['DSM_RX_MCU', '+5V_BEC']
        assert path['width_mm'] == (.6 if path['net'] == '+5V_BEC' else .127)
        for i, (a, b) in enumerate(zip(path['points_mm'], path['points_mm'][1:])):
            label = path['label'] + '/' + str(i)
            uid = str(uuid.uuid5(uuid.NAMESPACE_URL, SOURCE_SHA + '/' + PROPOSAL_SHA + '/' + label))
            obj = new[uid]
            assert obj['kind'] == 'track' and obj['net'] == path['net'] and obj['width'] == path['width_mm']
            assert obj['start'] == [round(v, 6) for v in a] and obj['end'] == [round(v, 6) for v in b]
            assert list(obj['copper']) == [path['layer']] and obj['width_by_layer'] == {path['layer']: path['width_mm']}
            assert math.dist(obj['start'], obj['end']) > 0
            expected[uid] = {'uuid': uid, 'net': path['net'], 'proposal_record': label}
    for row in proposal['vias']:
        label = row['label'] + '/via'
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, SOURCE_SHA + '/' + PROPOSAL_SHA + '/' + label))
        obj = new[uid]
        assert obj['kind'] == 'via' and obj['net'] == row['net'] == 'DSM_RX_MCU'
        assert obj['xy'] == row['xy_mm'] and obj['width'] == row['diameter_mm'] == .45
        assert obj['drill']['width'] == row['drill_mm'] == .2 and obj['plated']
        assert row['tented_both_faces'] and obj['tented'] == {'F.Mask': True, 'B.Mask': True}
        assert obj['top_layer'] == 'F.Cu' and obj['bottom_layer'] == 'B.Cu'
        assert obj['barrel_layers'] == after['copper_layers']
        assert set(obj['copper']) == set(after['copper_layers'])
        expected[uid] = {'uuid': uid, 'net': 'DSM_RX_MCU', 'proposal_record': label}
    assert set(expected) == added
    assert {row['uuid']: row for row in receipt['added_proposal_correspondence']} == expected
    count = collections.Counter(new[u]['kind'] + ':' + new[u]['net'] for u in added)
    assert dict(count) == {'track:DSM_RX_MCU': 29, 'track:+5V_BEC': 3, 'via:DSM_RX_MCU': 5}
    assert source_map['board_sha256'] == SOURCE_SHA and candidate_map['board_sha256'] == CANDIDATE_SHA
    assert candidate_map['source_sha256'] == SOURCE_SHA
    om, nm = source_map['logical_route_map'], candidate_map['logical_route_map']
    expected_map = {u: v for u, v in om.items() if u not in removed}
    expected_map.update({u: 'DSM_RX_MCU' for u in added if new[u]['net'] == 'DSM_RX_MCU'})
    assert nm == expected_map, 'Logical route map differs from the exact transaction'
    assert not set(nm) - set(new)
    return {'passed': True, 'source_objects': len(old), 'candidate_objects': len(new),
        'retained_source_objects_exact': len(retained), 'retained_records_sha256': record_sha({u: old[u] for u in sorted(retained)}),
        'removed_uuids': sorted(removed), 'added_uuids': sorted(added), 'added_counts': dict(count),
        'all_156_footprints_exact': True, 'all_existing_pads_exact': True, 'all_existing_signal_objects_exact': True,
        'all_GND_objects_exact': True, 'zone_definitions_outline_stackup_exact': True, 'logical_map_transaction_exact': True,
        'saved_fills_recomputed_and_checked_by_support_graph': True,
        'removed_record_sha256': {u: record_sha(old[u]) for u in sorted(removed)},
        'added_record_sha256': {u: record_sha(new[u]) for u in sorted(added)}}


def endpoint_audit(before, after):
    old, new = indexed(before), indexed(after)
    tracks = [o for o in after['objects'] if o['kind'] == 'track']
    pads = [o for o in after['objects'] if o['kind'] == 'pad']
    vias = [o for o in after['objects'] if o['kind'] == 'via']
    entries, joins, annular, classified = [], [], [], []
    seen = set()
    for track in tracks:
        if track['uuid'] in old:
            continue
        width = .6 if track['net'] == '+5V_BEC' else .127
        assert track['width'] == width
        for layer in track['copper']:
            for endpoint in ['start', 'end']:
                xy = track[endpoint]
                hp = [p for p in pads if p['net'] == track['net'] and layer in p['inside'] and geom(p['inside'][layer]).contains(Point(xy))]
                ht = [t for t in tracks if t['uuid'] != track['uuid'] and t['net'] == track['net'] and layer in t['copper'] and xy in [t['start'], t['end']]]
                hv = [v for v in vias if v['net'] == track['net'] and layer in v['copper'] and v['xy'] == xy]
                row = {'track_uuid': track['uuid'], 'net': track['net'], 'layer': layer, 'endpoint': endpoint,
                    'xy_mm': xy, 'required_width_mm': width, 'pads': [p['key'] for p in hp],
                    'exact_join_tracks': [t['uuid'] for t in ht], 'vias': [v['uuid'] for v in hv], 'resolved': bool(hp or ht or hv)}
                classified.append(row)
                for p in hp:
                    entries.append(pad_entry(track, p, layer, endpoint))
                for t in ht:
                    key = ('join',) + tuple(sorted([t['uuid'], track['uuid']])) + (layer,)
                    if key not in seen:
                        seen.add(key)
                        proof = join_entry(track, t, layer, width)
                        proof['retained_source_track_uuids'] = sorted(u for u in proof['track_uuids'] if u in old)
                        proof['retained_source_records_exact'] = all(new[u] == old[u] for u in proof['retained_source_track_uuids'])
                        joins.append(proof)
                for via in hv:
                    key = ('via', track['uuid'], via['uuid'], layer)
                    if key not in seen:
                        seen.add(key)
                        annular.append(via_entry(track, via, layer, after))
    return entries, joins, annular, classified


def rejected(name, callback):
    try:
        callback()
    except (AssertionError, KeyError) as error:
        return {'name': name, 'rejected': True, 'refusal': str(error) or type(error).__name__}
    return {'name': name, 'rejected': False}


def controls(before, after, proposal, receipt, smap, cmap, entries, joins, annular, cut_contract):
    result = []
    old, new = indexed(before), indexed(after)
    contract = lambda native: exact_contract(before, native, proposal, receipt, smap, cmap)
    for entry in entries:
        track = copy.deepcopy(new[entry['track_uuid']])
        track['width'] = 2.0
        witness = pad_entry(track, new[entry['pad_uuid']], entry['layer'], entry['endpoint'])
        result.append({'name': 'oversized_full_width_pad_entry_' + entry['pad'], 'rejected': not witness['passed'], 'witness': witness})
    for via_uuid in sorted({a['via_uuid'] for a in annular}):
        row = next(a for a in annular if a['via_uuid'] == via_uuid)
        via = copy.deepcopy(new[via_uuid])
        via['drill']['outside'] = copy.deepcopy(via['copper'][row['layer']])
        witness = via_entry(new[row['track_uuid']], via, row['layer'], after)
        result.append({'name': 'drill_only_annulus_' + via_uuid, 'rejected': not witness['passed'], 'witness': witness})
    for join in [j for j in joins if j['net'] == '+5V_BEC']:
        a, b = [new[u] for u in join['track_uuids']]
        narrower = synthetic_track(a['start'], a['end'], .59, '+5V_BEC', join['layer'])
        witness = join_entry(narrower, b, join['layer'], .6)
        result.append({'name': 'narrowed_BEC_exact_join_' + a['uuid'] + '_' + b['uuid'], 'rejected': not witness['passed'], 'witness': witness})
    signal_join = next(j for j in joins if j['net'] == 'DSM_RX_MCU')
    a, b = [new[u] for u in signal_join['track_uuids']]
    narrower = synthetic_track(a['start'], a['end'], .126, a['net'], signal_join['layer'])
    witness = join_entry(narrower, b, signal_join['layer'], .127)
    result.append({'name': 'narrowed_DSM_exact_join', 'rejected': not witness['passed'], 'witness': witness})
    a = synthetic_track([1, 1], [2, 1], .6, '+5V_BEC', 'In3.Cu')
    b = synthetic_track([2.5, 1], [3, 1], .6, '+5V_BEC', 'In3.Cu')
    witness = join_entry(a, b, 'In3.Cu', .6)
    result.append({'name': 'positive_sliver_without_exact_BEC_endpoint', 'rejected': not witness['passed'] and witness['native_polygon_overlap_mm2'] > 0, 'witness': witness})
    retained_uid = next(u for u in old if old[u]['kind'] == 'track' and old[u]['net'] == '+3V3_CORE')
    changed = dict(new[retained_uid], width=new[retained_uid]['width'] + .001)
    mutant = dict(after, objects=[changed if o['uuid'] == retained_uid else o for o in after['objects']])
    result.append(rejected('retained_source_record_mutation', lambda: contract(mutant)))
    new_uid = next(u for u in new if u not in old)
    mutant = dict(after, objects=[o for o in after['objects'] if o['uuid'] != new_uid])
    result.append(rejected('declared_new_object_removed', lambda: contract(mutant)))
    mutant = dict(after, objects=after['objects'] + [synthetic_track([1, 1], [2, 2], .127, 'DSM_RX_MCU')])
    result.append(rejected('undeclared_object_added', lambda: contract(mutant)))
    removed_uid = next(u for u in old if u not in new)
    mutant = dict(after, objects=after['objects'] + [old[removed_uid]])
    result.append(rejected('removed_BEC_source_object_restored', lambda: contract(mutant)))
    fp = copy.deepcopy(after['footprints'])
    fp[0]['xy'][0] += .001
    mutant = dict(after, footprints=fp)
    result.append(rejected('retained_footprint_mutation', lambda: contract(mutant)))
    wrong_map = copy.deepcopy(cmap)
    wrong_map['logical_route_map'][new_uid] = 'undeclared_owner'
    result.append(rejected('logical_owner_transaction_mutation', lambda: exact_contract(before, after, proposal, receipt, smap, wrong_map)))
    r38_track = next(e['track_uuid'] for e in entries if e['pad'] == 'R38.2')
    mutant = dict(after, objects=[o for o in after['objects'] if o['uuid'] != r38_track])
    broken = groups(mutant, 'DSM_RX_MCU')
    result.append({'name': 'R38_tree_branch_removed', 'rejected': len(broken) > 1, 'pad_groups': broken})
    bypass = synthetic_track([15.38, 23.82448], [16.26, 23.59], .127, 'DSM_RX_EXT')
    mutant = dict(after, objects=after['objects'] + [bypass])
    cut = run_check(mutant, cut_contract)
    result.append({'name': 'outside_D7_actual_pad_bypass', 'rejected': not cut['complete_clamp_first_path_passes'], 'witness': cut})
    return result


def main():
    bound = check_files()
    before, after = [read(path / 'f722-heli.native.json') for path in [SOURCE, CANDIDATE]]
    assert sha(SOURCE / 'f722-heli.kicad_pcb') == SOURCE_SHA
    assert sha(CANDIDATE / 'f722-heli.kicad_pcb') == CANDIDATE_SHA
    proposal = read(CANDIDATE / 'complete-tree-proposal.json')
    receipt = read(CANDIDATE / 'construction-provenance.json')
    smap, cmap = [read(path / 'f722-heli.logical-route-map.json') for path in [SOURCE, CANDIDATE]]
    contract = exact_contract(before, after, proposal, receipt, smap, cmap)
    old, new = indexed(before), indexed(after)
    removed, added = set(old) - set(new), set(new) - set(old)
    source_fixed, candidate_fixed = [read(p / 'fixed-explicit-native-ids.json') for p in [SOURCE, CANDIDATE]]
    assert set(candidate_fixed) == (set(source_fixed) - removed) | added
    assert sha(SOURCE / 'poses-native.json') == sha(CANDIDATE / 'poses-native.json')
    project = read(CANDIDATE / 'project-input-preservation.json')
    assert project['source_board_sha256'] == SOURCE_SHA and project['board_sha256'] == CANDIDATE_SHA
    assert project['files'] == read(SOURCE / 'project-input-preservation.json')['files']
    for row in project['files']:
        assert sha(SOURCE / row['path']) == sha(CANDIDATE / row['path']) == row['sha256']
    entries, joins, annular, classified = endpoint_audit(before, after)
    direct_failures = [e for e in entries if not e['passed']]
    print(json.dumps({'stage': 'entries', 'direct_pad_entry_failures': direct_failures, 'pad_entries': len(entries),
        'joins': len(joins), 'annular_entries': len(annular), 'track_endpoints': len(classified)}), flush=True)
    base = read(SOURCE / 'power-audit.json')
    assert base['passed'] and base['board_sha256'] == SOURCE_SHA and len(base['nets']) == 28
    assert base['native_sha256'] == sha(SOURCE / 'f722-heli.native.json')
    support = {}
    for net, evidence in base['nets'].items():
        source_groups, target_groups = groups(before, net), groups(after, net)
        support[net] = {'passed': source_groups == evidence['groups'] == target_groups and len(target_groups) == 1,
            'source_groups_match_prior_wrapper': source_groups == evidence['groups'],
            'source_groups_exactly_preserved': source_groups == target_groups, 'groups': target_groups}
    dsm_before, dsm_after = groups(before, 'DSM_RX_MCU'), groups(after, 'DSM_RX_MCU')
    dsm_complete = len(dsm_after) == 1 and dsm_after[0]['pads'] == ['R38.2', 'R71.2', 'U1.43']
    assert len(dsm_before) == 3
    other_nets = sorted({o['net'] for o in before['objects']} - set(base['nets']) - {'DSM_RX_MCU', ''})
    preserved = {}
    for net in other_nets:
        aa, bb = groups(before, net), groups(after, net)
        preserved[net] = {'passed': aa == bb, 'source_groups': aa, 'candidate_groups': bb}
    cut_contract = {'net': 'DSM_RX_EXT', 'clamp': 'D7.1', 'source': 'J12.3', 'target': 'R38.1', 'minimum_gap_required_mm': .127}
    source_cut, cut = run_check(before, cut_contract), run_check(after, cut_contract)
    negative = controls(before, after, proposal, receipt, smap, cmap, entries, joins, annular, cut_contract)
    new_vias = {u for u in added if new[u]['kind'] == 'via'}
    via_inventory = {u: {'entries': [a for a in annular if a['via_uuid'] == u],
        'used_layers': sorted({a['layer'] for a in annular if a['via_uuid'] == u})} for u in sorted(new_vias)}
    bec_source_joins = [j for j in joins if j['net'] == '+5V_BEC' and j['retained_source_track_uuids']]
    rechecked = check_files() == bound
    gates = {'exact_source_and_transaction_contract': contract['passed'],
        'all_three_direct_finite_full_width_pad_entries': len(entries) == 3 and {e['pad'] for e in entries} == {'R38.2', 'R71.2', 'U1.43'} and all(e['passed'] for e in entries),
        'all_signal_and_BEC_joins_full_required_width': all(j['passed'] for j in joins),
        'two_BEC_replacement_endpoints_join_exact_retained_060_tracks': len(bec_source_joins) == 2 and all(j['required_width_mm'] == .6 and j['retained_source_records_exact'] and j['passed'] for j in bec_source_joins),
        'all_five_signal_vias_have_two_finite_actual_annular_entries': len(via_inventory) == 5 and len(annular) == 10 and all(len(v['entries']) == len(v['used_layers']) == 2 and all(a['passed'] for a in v['entries']) for v in via_inventory.values()),
        'all_64_new_track_endpoints_resolved': len(classified) == 64 and all(e['resolved'] for e in classified),
        'all_28_support_groups_exactly_preserved': len(support) == 28 and all(v['passed'] for v in support.values()),
        'complete_DSM_three_pad_tree': dsm_complete,
        'all_other_signal_pad_partitions_preserved': all(v['passed'] for v in preserved.values()),
        'complete_outside_D7_pad_cut_exactly_preserved': source_cut == cut and cut['complete_clamp_first_path_passes'],
        'negative_controls_rejected': all(c['rejected'] for c in negative),
        'input_hashes_rechecked_unchanged': rechecked}
    report = {'schema': 'f722-dsm44-entry-support-audit/v1', 'passed': all(gates.values()), 'gates': gates,
        'source_board_sha256': SOURCE_SHA, 'board_sha256': CANDIDATE_SHA,
        'source_native_sha256': sha(SOURCE / 'f722-heli.native.json'), 'candidate_native_sha256': sha(CANDIDATE / 'f722-heli.native.json'),
        'script_sha256': sha(__file__), 'input_manifest_sha256': sha(MANIFEST), 'input_hashes': bound,
        'exact_transaction': contract, 'strict_pad_entries': entries, 'direct_pad_entry_failures_preserved': direct_failures,
        'full_width_signal_and_BEC_joins': joins, 'BEC_replacement_retained_track_joins': bec_source_joins,
        'finite_actual_annular_entries': annular, 'signal_via_inventory': via_inventory,
        'new_track_endpoint_classification': classified, 'nets': support,
        'DSM_RX_MCU': {'passed': dsm_complete, 'source_groups': dsm_before, 'candidate_groups': dsm_after},
        'all_other_signal_pad_partitions': preserved, 'actual_D7_pad_cut': cut,
        'source_D7_cut_exactly_equal': source_cut == cut, 'negative_controls': negative,
        'numerical_power_VCAP_applicable': False, 'fresh_numerical_BEC_power_revalidation_required': True,
        'adoption_claimed': False, 'engine_success_claimed': False,
        'limits': ['Finite nominal native pad/track/annulus copper and copper-only pad partitions. No loaded power, VCAP, ESD transient, thermal, impedance, timing, assembly or manufacturing-tolerance qualification.',
            'Native DRC, reference, complete actual-I/O, parity, process, mechanical, and acceptance gates remain separately owned.',
            'BEC replacement endpoints enter exact retained 0.6 mm native tracks. They are classified as full-width native track joins; an isolated via disk is not their endpoint target.',
            'All existing objects other than the two declared BEC tracks are exact. Saved zone fills may change and are used directly for support connectivity checks.']}
    output = HERE / 'candidate44-entry-support.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'gates': gates, 'pad_entries': len(entries), 'full_width_joins': len(joins),
        'finite_annular_entries': len(annular), 'new_track_endpoints': len(classified), 'support_nets': len(support),
        'other_signal_nets': len(preserved), 'negative_controls': len(negative),
        'failed_controls': [c['name'] for c in negative if not c['rejected']],
        'D7_outside_pad_gap_mm': cut['minimum_gap_measured_mm'], 'output': str(output)}, indent=2), flush=True)
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
