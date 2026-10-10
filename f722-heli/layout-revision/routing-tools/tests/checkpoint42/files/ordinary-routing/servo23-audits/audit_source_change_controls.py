#!/usr/bin/env python3
"""Exercise sealed SERVO2/3 contract with read-only in-memory negative controls."""
import argparse
import copy
import json
from pathlib import Path
from validate_servo23_stage import ALLOW, ROOT, add_basis_arguments, load_for_args, recheck, sha, validate_records


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    add_basis_arguments(ap)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    basis, _, _, extra = load_for_args(args)
    assert extra is None, 'Mutation controls apply to the sealed construction basis'
    original = [basis[k] for k in ['before', 'stage', 'before_map', 'stage_map', 'plan', 'screen', 'receipt']]
    controls = []

    def reject(name, slot, replacement):
        values = original[:]
        values[slot] = replacement
        try:
            validate_records(*values, binding_name=basis['binding_name'])
        except AssertionError as exc:
            controls.append({'control': name, 'rejected': True, 'reason': str(exc)})
            return
        raise AssertionError(f'Negative control accepted: {name}')

    before, after = original[:2]
    wrong = dict(before, board_sha256='0' * 64)
    reject('wrong_source_board', 0, wrong)
    wrong = copy.deepcopy(basis['stage_map'])
    uid = basis['receipt']['added_objects'][0]['uuid']
    wrong['logical_route_map'][uid] = 'SERVO2_MCU::P1'
    reject('wrong_constructed_logical_owner', 3, wrong)
    wrong = copy.deepcopy(basis['before_map'])
    uid = next(row['uuid'] for row in basis['plan']['remove_exact_objects'] if row['net'] != 'GND')
    wrong['logical_route_map'][uid] = 'SERVO3_MCU::P0'
    reject('wrong_removed_source_logical_owner', 2, wrong)
    ground = next(o for o in before['objects'] if o['net'] == 'GND' and o['kind'] == 'via' and o['uuid'] not in ALLOW)
    wrong = dict(after, objects=[o for o in after['objects'] if o['uuid'] != ground['uuid']])
    reject('undeclared_ground_removal', 1, wrong)
    added = copy.deepcopy(next(o for o in after['objects'] if o['uuid'] == basis['receipt']['added_objects'][0]['uuid']))
    added['uuid'], added['net'] = 'negative-control-other-net', 'USB_P'
    wrong = dict(after, objects=after['objects'] + [added])
    reject('other_net_addition', 1, wrong)
    moved = copy.deepcopy(ground)
    moved['xy'][0] += .01
    wrong = dict(after, objects=[moved if o['uuid'] == moved['uuid'] else o for o in after['objects']])
    reject('moved_existing_object', 1, wrong)
    added = copy.deepcopy(next(o for o in after['objects'] if o['uuid'] == basis['receipt']['added_objects'][0]['uuid']))
    added['start'][0] += .01
    wrong = dict(after, objects=[added if o['uuid'] == added['uuid'] else o for o in after['objects']])
    reject('constructed_track_differs_from_sealed_plan', 1, wrong)
    wrong = copy.deepcopy(basis['receipt'])
    wrong['omitted_plan_rows'] = []
    reject('undeclared_plan_omission', 6, wrong)
    recheck(basis)
    result = {'passed': True, 'construction': basis['report'], 'negative_controls': controls,
              'control_count': len(controls), 'validator_sha256': sha(Path(__file__).with_name('validate_servo23_stage.py')),
              'audit_script_sha256': sha(__file__), 'source_boards_written': False}
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': True, 'controls_rejected': len(controls), 'out': str(args.out)}))


if __name__ == '__main__':
    main()
