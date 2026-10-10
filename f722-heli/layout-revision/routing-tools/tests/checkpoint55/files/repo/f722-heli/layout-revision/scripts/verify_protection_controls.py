#!/usr/bin/env python3
"""Check golden replay, native broken/bypass controls and split-piece behavior."""
import argparse
import hashlib
import json
from pathlib import Path
from check_protection_paths import check_snapshot, run_check


def load(path):
    return json.loads(path.read_text())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--published-geometry', type=Path, required=True)
    ap.add_argument('--published-proof', type=Path, required=True)
    ap.add_argument('--contracts', type=Path, required=True)
    ap.add_argument('--controls', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    original = load(a.published_proof)
    golden = check_snapshot(load(a.published_geometry), load(a.contracts))
    exact = []
    for current, old in zip(golden['checks'], original['checks']):
        gaps_equal = all(x['gap_outside_actual_pad_mm'] == y['gap_outside_actual_pad_mm']
                         for x, y in zip(current['layer_gaps'], old['layer_gaps']))
        groups_equal = sorted(current['after_cut_pad_groups']) == sorted(old['after_cut_pad_groups'])
        membership_equal = all(current[k] == old[k] for k in ['source_objects', 'target_objects', 'before_cut'])
        exact.append({'id': current['id'], 'pass': current['complete_clamp_first_path_passes'],
                      'all_layer_gaps_exact': gaps_equal, 'pad_groups_equal': groups_equal,
                      'source_target_membership_exact': membership_equal})
    controls = []
    contract = load(a.contracts)['checks'][0]
    for kind in ['broken_source_lead', 'direct_front_bypass', 'plated_back_bypass']:
        snapshot = load(a.controls / (kind + '.json'))
        check = run_check(snapshot, contract)
        if kind == 'broken_source_lead':
            expected = not check['before_cut']['source_target_connected'] and not check['complete_clamp_first_path_passes']
        else:
            expected = (check['before_cut']['source_target_connected'] and
                        not check['source_target_physically_disconnected_after_removing_actual_pad_copper'] and
                        not check['complete_clamp_first_path_passes'])
        controls.append({'kind': kind, 'expected_outcome_observed': expected,
                         'board_sha256': snapshot['board_sha256'], 'result': check})
    split_contract = dict(id='control-single-object-split', net='TEST_SIGNAL', clamp='D1.1',
                          source='J1.1', target='R1.1', minimum_gap_required_mm=.127)
    split = run_check(load(a.controls / 'single_object_split.json'), split_contract)
    common_ids = set(split['source_objects']) & set(split['target_objects'])
    controls.append({'kind': 'single_object_split', 'expected_outcome_observed':
                     split['complete_clamp_first_path_passes'] and bool(common_ids),
                     'same_track_uuid_exists_in_both_separated_groups': sorted(common_ids), 'result': split})
    all_ok = (len(exact) == 18 and all(all(x[k] for k in ['pass', 'all_layer_gaps_exact', 'pad_groups_equal',
                                                       'source_target_membership_exact']) for x in exact)
              and all(x['expected_outcome_observed'] for x in controls))
    result = {'schema': 'f722-protection-regression-controls/v1', 'passed': all_ok,
              'published_board_sha256': golden['board_sha256'],
              'published_proof_sha256': hashlib.sha256(a.published_proof.read_bytes()).hexdigest(),
              'golden_exact_replay': exact, 'native_mutation_controls': controls,
              'scope': 'Control boards are intentionally defective test fixtures, not manufacturing candidates.'}
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': all_ok, 'golden_checks': len(exact), 'controls': len(controls),
                      'outcomes': {c['kind']: c['expected_outcome_observed'] for c in controls}}))
    raise SystemExit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
