#!/usr/bin/env python3
"""Read-only unit controls for the exact additive-successor contract."""
import argparse
import copy
import json
from pathlib import Path
import tempfile
from validate_servo23_stage import (ORDINARY_OWNER_CONTRACT_SHA, SOURCE_SHA,
    add_basis_arguments, checked, load_for_args, recheck, sha,
    validate_additive_successor, validate_successor_records)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    add_basis_arguments(ap)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    basis, stage, stage_map, successor = load_for_args(args)
    assert successor is None
    owners = checked(Path(__file__).with_name('ordinary-owner-contract.json'), ORDINARY_OWNER_CONTRACT_SHA)['ordinary_logical_owners']
    synthetic = copy.deepcopy(next(o for o in stage['objects'] if o['kind'] == 'track' and o['net'] == 'SERVO3_MCU'))
    synthetic['uuid'] = 'in-memory-successor-contract-control'
    after = dict(stage, objects=stage['objects'] + [synthetic])
    amap = dict(stage_map, logical_route_map={**stage_map['logical_route_map'], synthetic['uuid']: 'SERVO3_MCU::P1'})
    manifest = {'added_native_objects': [synthetic], 'added_logical_owners': {synthetic['uuid']: 'SERVO3_MCU::P1'}}
    assert validate_successor_records(basis, after, amap, manifest, owners) == [synthetic['uuid']]
    controls = []

    def reject(name, changed_after=after, changed_map=amap, changed_manifest=manifest):
        try:
            validate_successor_records(basis, changed_after, changed_map, changed_manifest, owners)
        except AssertionError as exc:
            controls.append({'control': name, 'rejected': True, 'reason': str(exc)})
            return
        raise AssertionError(f'Control accepted: {name}')

    fixed = next(o for o in stage['objects'] if o['kind'] == 'via' and o['net'] == 'GND')
    moved = copy.deepcopy(fixed)
    moved['xy'][0] += .01
    reject('successor_moved_fixed_ground_via', changed_after=dict(after, objects=[moved if o['uuid'] == fixed['uuid'] else o for o in after['objects']]))
    reject('successor_removed_fixed_ground', changed_after=dict(after, objects=[o for o in after['objects'] if o['uuid'] != fixed['uuid']]))
    wrong = copy.deepcopy(amap)
    old_owner_id = next(iter(stage_map['logical_route_map']))
    wrong['logical_route_map'][old_owner_id] = 'invalid-owner'
    reject('successor_changed_existing_owner', changed_map=wrong)
    wrong = copy.deepcopy(amap)
    wrong['logical_route_map'][synthetic['uuid']] = 'SERVO3_MCU::P0'
    reject('successor_wrong_manifest_owner', changed_map=wrong)
    reject('successor_undeclared_new_object', changed_manifest={'added_native_objects': [], 'added_logical_owners': {}})
    wrong = copy.deepcopy(manifest)
    wrong['added_native_objects'][0]['start'][0] += .01
    reject('successor_manifest_geometry_mismatch', changed_manifest=wrong)
    for net in ['USB_P', 'GND']:
        obj = copy.deepcopy(synthetic)
        obj['net'] = net
        data = dict(after, objects=stage['objects'] + [obj])
        mapping = dict(stage_map, logical_route_map={**stage_map['logical_route_map'], obj['uuid']: net})
        declaration = {'added_native_objects': [obj], 'added_logical_owners': {obj['uuid']: net}}
        reject(f'successor_declared_nonordinary_{net}', data, mapping, declaration)
    # File-bound wrapper positive/no-op control and explicit source/hash controls.
    no_op = {'schema': 'f722-servo23-exact-additive-successor/v1', 'accepted37_board_sha256': SOURCE_SHA,
             'stage_board_sha256': basis['binding']['stage_board'], 'stage_native_sha256': basis['binding']['stage_native'],
             'candidate_board_sha256': basis['binding']['stage_board'], 'candidate_native_sha256': basis['binding']['stage_native'],
             'candidate_map_sha256': basis['binding']['stage_map'], 'added_native_objects': [], 'added_logical_owners': {}}
    original_seals = dict(basis['sealed_paths'])
    with tempfile.TemporaryDirectory(prefix='servo23-manifest-controls-') as temporary:
        path = Path(temporary) / 'manifest.json'
        path.write_text(json.dumps(no_op))
        validate_additive_successor(basis, args.stage, path, sha(path))
        try:
            validate_additive_successor(basis, args.stage, path, '0' * 64)
        except AssertionError as exc:
            controls.append({'control': 'successor_wrong_manifest_digest', 'rejected': True, 'reason': str(exc)})
        else:
            raise AssertionError('Wrong manifest digest accepted')
        no_op['stage_board_sha256'] = '0' * 64
        path.write_text(json.dumps(no_op))
        try:
            validate_additive_successor(basis, args.stage, path, sha(path))
        except AssertionError:
            controls.append({'control': 'successor_wrong_stage_source', 'rejected': True})
        else:
            raise AssertionError('Wrong stage source accepted')
    # Temporary altered negative-control manifests are not actual audit inputs.
    basis['sealed_paths'] = original_seals
    recheck(basis)
    result = {'passed': True, 'basis': args.basis, 'board_sha256': stage['board_sha256'],
              'positive_controls': ['in_memory_exact_ordinary_addition', 'file_bound_empty_addition_manifest'],
              'negative_controls': controls, 'source_boards_written': False,
              'qualification_claimed_for_synthetic_geometry': False,
              'validator_sha256': sha(Path(__file__).with_name('validate_servo23_stage.py')),
              'audit_script_sha256': sha(__file__)}
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': True, 'negative_controls_rejected': len(controls), 'out': str(args.out)}))


if __name__ == '__main__':
    main()
