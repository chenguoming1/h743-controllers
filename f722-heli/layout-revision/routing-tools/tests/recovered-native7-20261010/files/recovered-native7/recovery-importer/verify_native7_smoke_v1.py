#!/usr/bin/env python3
"""Host-only proof that an authorized smoke candidate preserves native copper geometry."""
import argparse
from collections import Counter
from pathlib import Path

import import_native7_incremental_v1 as imp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    source, logical, hardware = imp.source_inputs()
    plan = imp.read(args.plan)
    validated = imp.validate_plan(plan, source, logical)
    receipt = imp.read(args.candidate / 'construction-provenance.json')
    after = imp.read(args.candidate / 'f722-heli.native.json')
    imp.require(receipt['status'] == 'CONSTRUCTION_VERIFIED_NOT_ACCEPTED' and receipt['acceptance_claimed'] is False,
                'Construction proof missing or incorrectly accepted')
    imp.require(receipt['source'] == imp.SOURCE_BINDINGS and receipt['plan_sha256'] == imp.sha(args.plan), 'Smoke source/plan mismatch')
    imp.require(receipt['board_sha256'] == imp.sha(args.candidate / 'f722-heli.kicad_pcb') == after['board_sha256'], 'Smoke board changed')
    imp.require(receipt['native_sha256'] == imp.sha(args.candidate / 'f722-heli.native.json'), 'Smoke native changed')
    without_uuid = lambda records: Counter(imp.canonical({k: v for k, v in row.items() if k != 'uuid'}) for row in records)
    imp.require(without_uuid(source['objects']) == without_uuid(after['objects']), 'Smoke changes full native copper geometry or physical net identity')
    imp.require(source['footprints'] == after['footprints'], 'Smoke changes footprints')
    for name, expected in hardware.items():
        imp.require(name == 'f722-heli.kicad_pcb' or imp.sha(args.candidate / name) == expected, 'Smoke changed paired hardware')
    old, new = imp.unique(source['objects']), imp.unique(after['objects'])
    removed = set(validated['removed'])
    expected_new = {row['uuid'] for row in receipt['recipe_to_native_UUIDs']}
    imp.require(set(old) - set(new) == removed and set(new) - set(old) == expected_new, 'Smoke identity replacement differs')
    current_logical = imp.read(args.candidate / 'f722-heli.logical-route-map.json')
    imp.require(current_logical['board_sha256'] == after['board_sha256'], 'Smoke logical map is stale')
    expected_logical = {uid: net for uid, net in logical.items() if uid not in removed}
    recipes = {r['name']: r for r in plan['added_copper']}
    for row in receipt['recipe_to_native_UUIDs']:
        expected_logical[row['uuid']] = recipes[row['name']]['logical_net']
    imp.require(current_logical['logical_route_map'] == expected_logical, 'Smoke logical identity changed')
    proof = {'schema': 'f722-native7-importer-smoke-proof/v1', 'board_sha256': after['board_sha256'],
             'native_sha256': receipt['native_sha256'], 'plan_sha256': receipt['plan_sha256'],
             'all_copper_native_geometry_and_nets_identical_ignoring_declared_UUID_replacements': True,
             'retained_logical_roles_identical': True, 'paired_non_board_hardware_byte_identical': True,
             'declared_removed_UUIDs': sorted(removed), 'declared_new_UUIDs': sorted(expected_new),
             'changed_zone_fills': receipt['changed_zone_fills'],
             'existing_DRC_ERC_warnings_and_open_connections_not_evaluated': True, 'acceptance_claimed': False}
    if args.out:
        imp.write(args.out, proof)
    print(imp.canonical(proof))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise SystemExit(str(error)) from error
