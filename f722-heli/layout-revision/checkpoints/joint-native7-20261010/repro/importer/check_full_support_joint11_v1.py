#!/usr/bin/env python3
"""Full native physical graph for all 28 support groups, critical and changed nets.

Uses the existing conservative copper/drill/saved-fill contact graph. It does not
assume retained copper or plane geometry is unchanged, does not invent same-net
edges, and does not imply current, noise, ADC settling, AC or ESD qualification.
Run only through the owner-leased physical-gate orchestrator.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path
from common_joint11 import ROOT, physical, read, require, sha, write


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native', required=True, type=Path)
    ap.add_argument('--board', required=True, type=Path)
    ap.add_argument('--source', required=True, type=Path)
    ap.add_argument('--transaction', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    args = ap.parse_args()
    snapshot = read(args.native)
    source = read(args.source / 'f722-heli.native.json')
    baseline = read(args.source / 'power-audit.json')
    critical = read(args.source / 'owner-critical.json')
    transaction = read(args.transaction)
    require(snapshot['board_sha256'] == sha(args.board), 'Stale actual native data')
    require(source['board_sha256'] == baseline['board_sha256'] == transaction['source_board_sha256'], 'Source support binding mismatch')
    require(len(baseline['nets']) == 28, 'Source support inventory is not 28')
    sys.path.insert(0, str(ROOT / 'python-deps'))
    helper_path = ROOT / 'repo/f722-heli/layout-revision/protection-review/tools/check_protection_paths.py'
    module_spec = importlib.util.spec_from_file_location('joint11_physical_graph', helper_path)
    graph = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(graph)
    changed_nets = {o['net'] for o in transaction['removed_native_records']}
    changed_nets |= {o['recipe']['net'] for o in transaction['added_copper']}
    changed_nets |= {pair[side]['net'] for pair in transaction['changed_pad_records'] for side in ('before', 'after')}
    support_nets = set(baseline['nets'])
    critical_nets = {q['net'] for q in critical['fullnet_connectivity']}
    flash_nets = {o['net'] for o in source['objects'] if o['net'].startswith('FLASH_')}
    all_nets = support_nets | critical_nets | changed_nets | flash_nets | {'ADC_BUS', 'ADC_DIV_MID', 'BOOT0'}
    all_nets = {n for n in all_nets if n and not n.startswith('unconnected-')}

    def objects(native, net):
        return [o for o in native['objects'] if o['net'] == net] + [
            {'uuid': z['uuid'], 'kind': 'zone', 'net': net, 'copper': z['filled'], 'drill': None, 'plated': False}
            for z in native['zones'] if not z['rule'] and z['net'] == net]

    rows = {}
    for net in sorted(all_nets):
        items = objects(snapshot, net)
        groups = graph.make_graph(items)
        pads = {o['uuid']: o['key'] for o in items if o['kind'] == 'pad'}
        pad_groups = []
        padless_groups = []
        for group in groups:
            members = {node['object']['uuid']: node['object']['key'] for node in group if node['object']['kind'] == 'pad'}
            if members:
                pad_groups.append({'pad_uuids': sorted(members), 'pad_keys': sorted(members.values()),
                                   'saved_plane_UUIDs': sorted({node['object']['uuid'] for node in group if node['object']['kind'] == 'zone'}),
                                   'saved_plane_layers': sorted({node['layer'] for node in group if node['object']['kind'] == 'zone'})})
            else:
                padless_groups.append({'object_UUIDs': sorted({node['object']['uuid'] for node in group}),
                                       'layers': sorted({node['layer'] for node in group})})
        observed = {uid for group in pad_groups for uid in group['pad_uuids']}
        complete = len(pad_groups) == 1 and observed == set(pads) and bool(pads)
        rows[net] = {'physical_pad_count': len(pads), 'pad_group_count': len(pad_groups),
                     'groups': sorted(pad_groups, key=lambda x: x['pad_uuids']), 'complete': complete,
                     'missing_pad_UUIDs': sorted(set(pads) - observed), 'original_support_group': net in support_nets,
                     'original_critical_net': net in critical_nets, 'selected_transaction_changed_net': net in changed_nets,
                     'padless_disconnected_copper_groups': padless_groups,
                     'cycle_freedom_not_proved': True}
    ground = rows['GND']
    actual_ground_keys = sorted(o['key'] for o in snapshot['objects'] if o['kind'] == 'pad' and o['net'] == 'GND')
    source_ground_keys = sorted(o['key'] for o in source['objects'] if o['kind'] == 'pad' and o['net'] == 'GND')
    explicit_terminals = {
        'ADC_BUS': ['U1.10', 'C31.1', 'R42.2', 'R43.1'], 'ADC_DIV_MID': ['R43.2', 'R44.1'],
        'BOOT0': ['U1.60', 'R2.1', 'SW1.2'],
        'PORT_C_RX_EXT': ['J11.1', 'U15.10', 'U15.1', 'R34.1'],
        'PORT_C_TX_EXT': ['J11.2', 'U15.9', 'U15.2', 'R35.1'],
        'PORT_C_RX_MCU': ['R34.2', 'U1.28'], 'PORT_C_TX_MCU': ['R35.2', 'U1.29']}
    terminal_checks = {}
    actual_pads = {o['uuid']: o for o in snapshot['objects'] if o['kind'] == 'pad'}
    source_pads = {o['uuid']: o for o in source['objects'] if o['kind'] == 'pad'}
    expected_pad_nets = {uid: o['net'] for uid, o in source_pads.items()}
    for pair in transaction['changed_pad_records']:
        expected_pad_nets[pair['before']['uuid']] = pair['after']['net']
    actual_pad_nets = {uid: o['net'] for uid, o in actual_pads.items()}
    source_pad_identity_inventory_preserved = (set(source_pads) == set(actual_pads) and len(actual_pads) == 558 and
        all((o['key'], o['ref'], o['number'], o['footprint_uuid']) ==
            (actual_pads[uid]['key'], actual_pads[uid]['ref'], actual_pads[uid]['number'], actual_pads[uid]['footprint_uuid'])
            for uid, o in source_pads.items()))
    for net, terminals in explicit_terminals.items():
        row = rows[net]
        terminal_UUIDs = {uid for uid, p in actual_pads.items() if p['key'] in terminals and p['net'] == net}
        present_keys = {actual_pads[uid]['key'] for uid in terminal_UUIDs}
        terminal_checks[net] = {'required': terminals, 'all_physical_terminal_UUIDs': sorted(terminal_UUIDs),
            'all_in_one_physical_component': present_keys == set(terminals) and any(terminal_UUIDs <= set(g['pad_uuids']) for g in row['groups'])}
    required_returns = ['U15.3', 'U15.8', 'U2.6', 'U2.7', 'U2.9', 'C11.2', 'C13.2', 'C31.2', 'R44.2', 'R2.2']
    returns = {key: any(key in g['pad_keys'] and g['saved_plane_UUIDs'] for g in ground['groups']) for key in required_returns}
    result = {'schema': 'f722-joint-full-physical-support/v1', 'board_sha256': snapshot['board_sha256'],
        'source_board_sha256': source['board_sha256'], 'native_sha256': sha(args.native),
        'transaction_sha256': sha(args.transaction), 'helper_sha256': sha(helper_path),
        'source_support_audit_sha256': sha(args.source / 'power-audit.json'),
        'nets': rows, 'original_28_support_groups_complete': all(rows[n]['complete'] for n in support_nets),
        'original_critical_nets_complete': all(rows[n]['complete'] for n in critical_nets),
        'all_reviewed_nets_complete': all(row['complete'] for row in rows.values()),
        'explicit_actual_terminal_checks': terminal_checks, 'required_returns_reach_actual_saved_planes': returns,
        'ground_pad_identity_inventory_preserved': actual_ground_keys == source_ground_keys,
        'all_558_source_pad_UUID_identities_preserved': source_pad_identity_inventory_preserved,
        'all_pad_nets_equal_source_plus_declared_two_NC_edits': actual_pad_nets == expected_pad_nets,
        'required_returns_saved_plane_layers': {key: sorted({layer for g in ground['groups'] if key in g['pad_keys'] for layer in g['saved_plane_layers']}) for key in required_returns},
        'dedicated_returns_finite_annulus_necks_and_cycle_freedom_not_proved': True,
        'method': 'Existing physical graph over actual native copper, real drilled/plated barrels and native saved fill; no package-internal or virtual same-net edges.',
        'finite_entry_widths_and_layer_specific_reference_gaps_not_checked_here': True,
        'numerical_power_VCAP_ADC_AC_ESD_qualification_performed': False,
        'construction_or_adoption_claimed': False}
    result['passed'] = (result['all_reviewed_nets_complete'] and all(returns.values()) and
                        result['ground_pad_identity_inventory_preserved'] and source_pad_identity_inventory_preserved and
                        actual_pad_nets == expected_pad_nets and all(v['all_in_one_physical_component'] for v in terminal_checks.values()))
    write(args.out, result)
    print(json.dumps({'passed': result['passed'], 'nets_checked': len(rows),
        'incomplete_nets': [n for n, r in rows.items() if not r['complete']],
        'original_28_support_groups_complete': result['original_28_support_groups_complete'],
        'missing_ground_returns': [n for n, ok in returns.items() if not ok]}))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
