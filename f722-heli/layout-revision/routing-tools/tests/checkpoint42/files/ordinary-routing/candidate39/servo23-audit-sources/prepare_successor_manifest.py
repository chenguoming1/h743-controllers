#!/usr/bin/env python3
"""Describe exact additive records for a separately qualified stage successor.

This creates a reviewable comparison manifest, not adoption or route approval.
Use its printed SHA explicitly when rerunning the full rewritten-entry audit.
"""
import argparse
import json
from pathlib import Path
from validate_servo23_stage import (ORDINARY_OWNER_CONTRACT_SHA, SOURCE_SHA,
    add_basis_arguments, checked, index, load_basis, read, recheck, sha,
    validate_additive_successor)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    add_basis_arguments(ap)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    assert args.candidate and not args.addition_manifest and not args.addition_manifest_sha256
    # Resolve the same explicitly selected pinned basis without treating the new
    # candidate as accepted. Candidate validation follows manifest construction.
    from validate_servo23_stage import load_for_args
    candidate = args.candidate
    args.candidate = None
    basis, _, _, _ = load_for_args(args)
    native = read(candidate / 'f722-heli.native.json')
    amap = read(candidate / 'f722-heli.logical-route-map.json')
    old, now = index(basis['stage']['objects']), index(native['objects'])
    added = sorted(set(now) - set(old))
    manifest = {'schema': 'f722-servo23-exact-additive-successor/v1',
                'accepted37_board_sha256': SOURCE_SHA,
                'stage_board_sha256': basis['binding']['stage_board'],
                'stage_native_sha256': basis['binding']['stage_native'],
                'candidate_board_sha256': sha(candidate / 'f722-heli.kicad_pcb'),
                'candidate_native_sha256': sha(candidate / 'f722-heli.native.json'),
                'candidate_map_sha256': sha(candidate / 'f722-heli.logical-route-map.json'),
                'added_native_objects': [now[uid] for uid in added],
                'added_logical_owners': {uid: amap['logical_route_map'][uid] for uid in added},
                'adoption_claimed': False,
                'limits': 'Exact additive record binding only. Native endpoint, process, support, DRC, reference, protection and other owner gates remain mandatory.'}
    # Check the same exact invariance rules before writing the artifact.
    from validate_servo23_stage import validate_successor_records
    owners = checked(Path(__file__).with_name('ordinary-owner-contract.json'), ORDINARY_OWNER_CONTRACT_SHA)
    validate_successor_records(basis, native, amap, manifest, owners['ordinary_logical_owners'])
    assert native['board_sha256'] == amap['board_sha256'] == manifest['candidate_board_sha256']
    args.out.write_text(json.dumps(manifest, indent=2) + '\n')
    digest = sha(args.out)
    validate_additive_successor(basis, candidate, args.out, digest)
    recheck(basis)
    print(json.dumps({'passed': True, 'added_objects': len(added), 'manifest': str(args.out),
                      'manifest_sha256': digest, 'adoption_claimed': False}))


if __name__ == '__main__':
    main()
