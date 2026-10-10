#!/usr/bin/env python3
"""Verify portable receipts, and optionally replay one native source.

Receipt verification exits zero for internally consistent unfinished evidence.
Physical cut reports retain their own all_pass=False and expected exit code 1.
"""
import argparse
import hashlib
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parent.parent
RESULTS = ['legacy-original18', 'legacy-supplemental7', 'actual-io22', 'added-d7-1']


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count(checks):
    return {'passed': sum(c['complete_clamp_first_path_passes'] for c in checks), 'total': len(checks)}


def verify_source_receipts(source_id):
    directory = PACKET / 'receipts' / source_id
    receipt = load(directory / 'source.json')
    coverage = load(directory / 'coverage.json')
    terminals = load(directory / 'terminals.json')
    contracts = {name: load(PACKET / 'contracts' / (name + '.json')) for name in RESULTS}
    reports = {name: load(directory / (name + '.json')) for name in RESULTS}
    assert receipt['board_sha256'] == coverage['board_sha256'] == terminals['board_sha256']
    assert sha(directory / 'coverage.json') == receipt['coverage_sha256']
    assert sha(directory / 'terminals.json') == receipt['stored_terminal_inventory_sha256'] == coverage['native_terminals_sha256']
    for artifact in receipt['result_receipts']:
        assert sha(directory / artifact['artifact']) == artifact['sha256']
    for name, report in reports.items():
        assert report['board_sha256'] == receipt['board_sha256']
        assert report['contracts_sha256'] == sha(PACKET / 'contracts' / (name + '.json'))
        assert report['passed'] == count(report['checks'])['passed']
        assert report['total'] == len(report['checks']) == len(contracts[name]['checks'])
        assert report['all_pass'] == all(c['complete_clamp_first_path_passes'] for c in report['checks'])
        for contract, result in zip(contracts[name]['checks'], report['checks']):
            assert all(result[key] == value for key, value in contract.items())
    # New actual-I/O view is additive: all original actual-clamp and all
    # supplemental contract geometry fields must remain unchanged.
    original_checks = contracts['legacy-original18']['checks']
    legacy_actual = [c for c in original_checks if c['scope'] == 'actual_clamp']
    legacy_nc = [c for c in original_checks if c['scope'] == 'nc_routing_pad']
    assert len(legacy_actual) == 14 and len(legacy_nc) == 4
    actual = contracts['actual-io22']['checks']
    by_id = {c['id']: c for c in actual}
    for old in legacy_actual + contracts['legacy-supplemental7']['checks']:
        new = by_id[old['id']]
        assert new['historical_scope'] == old['scope']
        assert all(new[key] == value for key, value in old.items() if key != 'scope')
    assert len(actual) == 22 and contracts['added-d7-1']['checks'] == [by_id['actual-io-gap-01']]
    assert all(c['scope'] == 'actual_clamp' for c in actual)
    parts = {p['reference']: p for p in terminals['parts']}
    pads = {p['key']: p for p in terminals['terminals']}
    models = load(PACKET / 'sources/part-pin-map.json')['models']
    active, unused, nc_keys = set(), set(), set()
    for mpn, model in models.items():
        for ref in model['refs']:
            assert parts[ref]['fields']['MPN'] == mpn
            for number in model['io']:
                pad = pads[ref + '.' + number]
                (unused if pad['net'].startswith('unconnected-') else active).add(pad['key'])
            nc_keys.update(ref + '.' + number for number in model['nc'])
            assert all(pads[ref + '.' + number]['net'] == 'GND' for number in model['ground'])
            assert all(pads[ref + '.' + number]['net'] == '+3V3_CORE' for number in model['bias'])
    assert len(active) == 20 and unused == {'U13.4', 'U15.4', 'U15.5'}
    assert {c['clamp'] for c in actual} == active
    old_clamps = {c['clamp'] for c in legacy_actual + contracts['legacy-supplemental7']['checks']}
    assert active - old_clamps == {'D7.1'}
    for clamp in active:
        checks = [c for c in actual if c['clamp'] == clamp]
        endpoints = {c[key] for c in checks for key in ['source', 'clamp', 'target']}
        net = pads[clamp]['net']
        assert all(c['net'] == net for c in checks)
        assert all(pads[key]['net'] == net for key in endpoints)
        assert {p['key'] for p in terminals['terminals'] if p['net'] == net} - endpoints <= nc_keys
    original_results = reports['legacy-original18']['checks']
    assert count([c for c in original_results if c['scope'] == 'actual_clamp']) == receipt['original_actual_clamp']
    assert count([c for c in original_results if c['scope'] == 'nc_routing_pad']) == receipt['original_nc_routing_pad']
    assert count(reports['actual-io22']['checks']) == receipt['all_actual_clamp_cases']
    passed_channels = sum(all(c['complete_clamp_first_path_passes'] for c in reports['actual-io22']['checks'] if c['clamp'] == key) for key in active)
    assert {'passed': passed_channels, 'total': len(active)} == receipt['all_actual_clamp_channels']
    return receipt, terminals, reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=['source69', 'source62'])
    parser.add_argument('--board', type=Path)
    parser.add_argument('--geometry', type=Path)
    parser.add_argument('--terminals', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    selected = [args.source] if args.source else ['source69', 'source62']
    verified = {source: verify_source_receipts(source) for source in selected}
    replay_args = [args.board, args.geometry, args.terminals, args.out]
    if any(replay_args):
        if not all(replay_args) or args.source is None:
            parser.error('Replay requires --source, --board, --geometry, --terminals and --out together')
        from check_protection_paths import check_snapshot
        receipt, stored_terminals, stored_reports = verified[args.source]
        before = sha(args.board)
        snapshot = load(args.geometry)
        terminals = load(args.terminals)
        assert before == receipt['board_sha256'] == snapshot['board_sha256'] == terminals['board_sha256']
        assert snapshot['source_unchanged'] and terminals['source_unchanged']
        assert terminals['parts'] == stored_terminals['parts']
        assert terminals['terminals'] == stored_terminals['terminals']
        native_pads = {p['uuid']: p for p in snapshot['objects'] if p['kind'] == 'pad'}
        for pad in terminals['terminals']:
            native = native_pads[pad['uuid']]
            assert (native['key'], native['net'], native['xy']) == (pad['key'], pad['net'], pad['xy_mm'])
        args.out.mkdir(parents=True, exist_ok=True)
        result_counts = {}
        for name in RESULTS:
            contract_path = PACKET / 'contracts' / (name + '.json')
            result = check_snapshot(snapshot, load(contract_path))
            result['geometry_sha256'] = sha(args.geometry)
            result['contracts_sha256'] = sha(contract_path)
            assert result['checks'] == stored_reports[name]['checks'], (name, 'Source result changed')
            (args.out / (name + '.json')).write_text(json.dumps(result, indent=2) + '\n')
            result_counts[name] = {'passed': result['passed'], 'total': result['total'],
                                  'all_pass': result['all_pass'], 'generic_checker_expected_exit_code': 0 if result['all_pass'] else 1}
        assert before == sha(args.board), 'Native source changed during read-only replay'
        output = {'source_id': args.source, 'board_sha256': before,
                  'source_unchanged': True, 'all_stored_per_case_results_reproduced': True,
                  'result_counts': result_counts, 'protection_complete': False}
        (args.out / 'replay.json').write_text(json.dumps(output, indent=2) + '\n')
        print(json.dumps(output, indent=2))
    else:
        print(json.dumps({'portable_receipts_verified': selected,
                          'coverage_complete_for_scoped_signal_io': True,
                          'protection_complete': False}, indent=2))


if __name__ == '__main__':
    main()
