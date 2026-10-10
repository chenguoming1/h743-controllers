#!/usr/bin/env python3
"""Audit signal-I/O coverage without changing boards or historical contracts.

Run from the f722-layout-rebuild root after export_terminals.py and the public
native exporter. PYTHONPATH=python-deps supplies the existing Shapely runtime.
The audit can succeed while physical protection remains unfinished.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'actual-tvs-coverage-review'
PUBLIC = ROOT / 'repo/f722-heli/layout-revision'
CONTRACT_DIR = PUBLIC / 'checks/protection'
CHECKER = PUBLIC / 'scripts/check_protection_paths.py'
SOURCES = {
    'accepted69': ('candidate16', '9cf04c88ebd31d7e2c12bdb8a9f80e01b615a7bdb94a73fc2234208a2e0a14c8'),
    'isolated62': ('candidate22', 'fd8fd21062c61992ec992481d394e19a6a99cfe8ec58405ed1e391c5e3836bfa'),
}
MODELS = {
    'ESD9M5.0ST5G': {'refs': ['D3', 'D4', 'D5', 'D6', 'D7'], 'io': ['1'], 'ground': ['2'], 'nc': [], 'bias': [],
        'url': 'https://www.onsemi.com/download/data-sheet/pdf/esd9m5.0s-d.pdf',
        'basis': 'ESD9M5.0S/D Rev 9 (February 2024), unidirectional device on page 2; CASE 514AB STYLE 1 on page 4: pin 1 cathode, pin 2 anode.'},
    'USBLC6-4SC6': {'refs': ['U12', 'U13'], 'io': ['1', '3', '4', '6'], 'ground': ['2'], 'nc': [], 'bias': ['5'],
        'url': 'https://www.st.com/resource/en/datasheet/usblc6-4.pdf',
        'basis': 'DocID11068 Rev 7 (November 2015), page 1 Figure 1: I/O1 pin 1, I/O2 pin 3, I/O3 pin 4, I/O4 pin 6; GND pin 2, VBUS pin 5.'},
    'TPD4E05U06DQAR': {'refs': ['U14', 'U15'], 'io': ['1', '2', '4', '5'], 'ground': ['3', '8'], 'nc': ['6', '7', '9', '10'], 'bias': [],
        'url': 'https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf',
        'basis': 'SLVSBO7O Rev O (August 2024), page 4 Table 4-2 and Figure 4-3. Pins 1/2/4/5 are protected I/O; 3/8 GND; 6/7/9/10 NC. NC routing is optional and has no internal signal connection.'},
    'PESD15VS2UT,215': {'refs': ['U16'], 'io': ['1', '2'], 'ground': ['3'], 'nc': [], 'bias': [],
        'url': 'https://assets.nexperia.com/documents/data-sheet/PESD15VS2UT.pdf',
        'basis': 'Product data sheet 13 April 2023, page 2 Table 2: pin 1 K1 cathode, pin 2 K2 cathode, pin 3 common anode.'},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')


def counts(checks):
    return {'passed': sum(c['complete_clamp_first_path_passes'] for c in checks), 'total': len(checks)}


def main():
    preserved_paths = [CONTRACT_DIR / f for f in ['candidate-contracts.json', 'published-contracts.json', 'supplemental-contracts.json']]
    preserved_paths += [CHECKER, PUBLIC / 'scripts/export_native_copper.py', PUBLIC / 'scripts/build_protection_controls.py', PUBLIC / 'scripts/verify_protection_controls.py']
    preserved_paths += list(CONTRACT_DIR.glob('*controls*.json'))
    for candidate, _ in SOURCES.values():
        directory = ROOT / 'ordinary-routing' / candidate
        preserved_paths += [directory / name for name in ['f722-heli.kicad_pcb', 'owner-native.json', 'owner-protection.json', 'owner-supplemental.json']]
    preserved_before = {str(path.relative_to(ROOT)): sha(path) for path in preserved_paths}
    original = read(CONTRACT_DIR / 'candidate-contracts.json')
    supplemental = read(CONTRACT_DIR / 'supplemental-contracts.json')
    assert len(original['checks']) == 18 and len(supplemental['checks']) == 7
    historical_actual = [c for c in original['checks'] if c['scope'] == 'actual_clamp']
    nc_checks = [c for c in original['checks'] if c['scope'] == 'nc_routing_pad']
    assert len(historical_actual) == 14 and len(nc_checks) == 4
    gap_check = {'id': 'actual-io-gap-01', 'net': 'DSM_RX_EXT', 'clamp': 'D7.1',
                 'source': 'J12.3', 'target': 'R38.1', 'minimum_gap_required_mm': 0.127,
                 'scope': 'actual_clamp', 'coverage_origin': 'new_D7_signal_IO_review'}
    gap_contract = {'profile': 'actual-io-gap-1', 'method': original['method'],
        'basis': 'Additive review only: D7 is a fitted ESD9M5.0ST5G whose actual signal cathode was omitted from the historical 18 and supplemental 7. The 0.127 mm threshold is the existing actual-I/O review criterion, newly applied here; it is not a retroactive published requirement.',
        'checks': [gap_check]}
    actual_checks = []
    for profile, checks in [(original['profile'], historical_actual), (supplemental['profile'], supplemental['checks'])]:
        for check in checks:
            actual_checks.append(dict(check, scope='actual_clamp', historical_scope=check['scope'], coverage_origin=profile))
    actual_checks.append(gap_check)
    actual_contract = {'profile': 'actual-bonded-signal-io-22', 'method': original['method'],
        'basis': 'Separate complete inventory of 20 populated signal-clamp channels, represented by 22 source-to-target cases because USB P/N each have two connector contacts. It retains every historical actual-I/O endpoint and threshold and adds D7; it neither replaces historical reports nor includes NC cuts in actual_clamp counts.',
        'excluded_scope': 'D8/D9 power-rail TVS, ground-return and bias-plane qualification, downstream sides of series resistors, unused bonded channels, ESD transient stress/inductance and manufacturing qualification.',
        'checks': actual_checks}
    write(OUT / 'gap-contracts.json', gap_contract)
    write(OUT / 'actual-io-contracts.json', actual_contract)
    source_reports = {}
    for label, (candidate, expected_sha) in SOURCES.items():
        directory = OUT / label
        source = ROOT / 'ordinary-routing' / candidate
        board = source / 'f722-heli.kicad_pcb'
        native = read(directory / 'native.json')
        terminals = read(directory / 'terminals.json')
        assert sha(board) == expected_sha == native['board_sha256'] == terminals['board_sha256']
        assert native['source_unchanged'] and terminals['source_unchanged']
        by_key = {t['key']: t for t in terminals['terminals']}
        native_pads = {t['uuid']: t for t in native['objects'] if t['kind'] == 'pad'}
        for terminal in terminals['terminals']:
            pad = native_pads[terminal['uuid']]
            assert (pad['key'], pad['net'], pad['xy']) == (terminal['key'], terminal['net'], terminal['xy_mm'])
        parts = {part['reference']: part for part in terminals['parts']}
        channels, unused, nc_pads, returns, bias = [], [], [], [], []
        for mpn, model in MODELS.items():
            for ref in model['refs']:
                part = parts[ref]
                assert part['fields']['MPN'] == mpn, (ref, 'unexpected exact MPN')
                for number in model['io']:
                    terminal = by_key[ref + '.' + number]
                    if terminal['net'].startswith('unconnected-'):
                        unused.append(dict(terminal, mpn=mpn, reason='Native unused bonded I/O; no external path'))
                        continue
                    matches = [c for c in actual_checks if c['clamp'] == terminal['key'] and c['net'] == terminal['net']]
                    old_matches = [c for c in historical_actual + supplemental['checks'] if c['clamp'] == terminal['key'] and c['net'] == terminal['net']]
                    assert matches, ('Uncovered active bonded I/O', terminal)
                    for check in matches:
                        for endpoint in ['source', 'target']:
                            assert by_key[check[endpoint]]['net'] == check['net'], (check['id'], endpoint)
                    channels.append(dict(terminal, mpn=mpn, datasheet=model['url'],
                        existing_contract_ids=[c['id'] for c in old_matches],
                        actual_io_contract_ids=[c['id'] for c in matches],
                        terminals_on_net=[t for t in terminals['terminals'] if t['net'] == terminal['net']]))
                for number in model['nc']:
                    nc_pads.append(dict(by_key[ref + '.' + number], mpn=mpn, role='No internal signal bond; any same-net copper is an external routing convention'))
                for number in model['ground']:
                    terminal = by_key[ref + '.' + number]
                    assert terminal['net'] == 'GND', (terminal['key'], 'wrong ground net')
                    returns.append(terminal)
                for number in model['bias']:
                    terminal = by_key[ref + '.' + number]
                    assert terminal['net'] == '+3V3_CORE', (terminal['key'], 'wrong bias net')
                    bias.append(terminal)
        assert len(channels) == 20 and len(unused) == 3
        active_keys = {c['key'] for c in channels}
        assert {c['clamp'] for c in actual_checks} == active_keys
        assert {c['key'] for c in channels if not c['existing_contract_ids']} == {'D7.1'}
        # Every signal-net terminal is either a contract endpoint, the actual
        # clamp, or one of the explicitly excluded NC routing pads.
        nc_keys = {p['key'] for p in nc_pads}
        for channel in channels:
            checks = [c for c in actual_checks if c['clamp'] == channel['key']]
            expected_terminals = {c[k] for c in checks for k in ['source', 'clamp', 'target']}
            assert {t['key'] for t in channel['terminals_on_net']} - expected_terminals <= nc_keys
        jobs = [
            ('historical-original', CONTRACT_DIR / 'candidate-contracts.json'),
            ('historical-supplemental', CONTRACT_DIR / 'supplemental-contracts.json'),
            ('actual-io', OUT / 'actual-io-contracts.json'),
            ('gap-only', OUT / 'gap-contracts.json'),
        ]
        reports, executions = {}, []
        for name, contract_path in jobs:
            result_path = directory / (name + '.json')
            command = [sys.executable, str(CHECKER), '--geometry', str(directory / 'native.json'),
                       '--contracts', str(contract_path), '--out', str(result_path)]
            result = subprocess.run(command, capture_output=True, text=True)
            (directory / (name + '.log')).write_text(result.stdout + result.stderr)
            assert result.returncode in (0, 1), (name, result.stderr)
            report = read(result_path)
            assert result.returncode == (0 if report['all_pass'] else 1)
            assert report['board_sha256'] == expected_sha
            reports[name] = report
            executions.append({'command': command, 'exit_code': result.returncode,
                               'exit_interpretation': 'Expected unfinished geometry' if result.returncode == 1 else 'All selected paths pass'})
        for name, owner in [('historical-original', 'owner-protection.json'), ('historical-supplemental', 'owner-supplemental.json')]:
            assert reports[name]['checks'] == read(source / owner)['checks'], ('Historical result changed', label, name)
        dependencies = []
        for check in reports['actual-io']['checks']:
            before = check.get('before_cut', {})
            dependencies.append({
                'id': check['id'], 'net': check['net'], 'clamp': check['clamp'],
                'source_to_actual_clamp': {'from': check['source'], 'to': check['clamp'], 'connected': before.get('source_reaches_clamp', False)},
                'actual_clamp_to_target': {'from': check['clamp'], 'to': check['target'], 'connected': before.get('target_reaches_clamp', False)},
                'source_target_connected': before.get('source_target_connected', False),
                'actual_pad_cut_passes': check['complete_clamp_first_path_passes'],
                'full_check_artifact': 'actual-io.json',
                'before_cut_pad_groups': before.get('groups', []),
            })
        old_checks = reports['historical-original']['checks']
        completed_channels = sum(all(c['complete_clamp_first_path_passes'] for c in reports['actual-io']['checks'] if c['clamp'] == key) for key in active_keys)
        report = {
            'schema': 'f722-actual-tvs-coverage-audit/v1', 'source_label': label,
            'board_path': str(board.relative_to(ROOT)), 'board_sha256': expected_sha,
            'native_geometry_sha256': sha(directory / 'native.json'),
            'native_terminals_sha256': sha(directory / 'terminals.json'),
            'coverage_complete_for_scoped_populated_signal_io': True,
            'previous_coverage_channels': 19, 'applicable_channels': 20,
            'new_gap_channels': ['D7.1'],
            'physical_protection_complete': reports['actual-io']['all_pass'],
            'historical_original': counts(old_checks),
            'historical_actual_clamp': counts([c for c in old_checks if c['scope'] == 'actual_clamp']),
            'historical_nc_routing_pad': counts([c for c in old_checks if c['scope'] == 'nc_routing_pad']),
            'historical_supplemental': counts(reports['historical-supplemental']['checks']),
            'actual_clamp_cases': counts(reports['actual-io']['checks']),
            'actual_clamp_channels': {'passed': completed_channels, 'total': len(active_keys)},
            'new_gap_cases': counts(reports['gap-only']['checks']),
            'historical_results_reproduced_exactly': True,
            'channels': channels, 'unused_bonded_channels': unused,
            'nc_routing_pads': nc_pads, 'return_pad_net_assignments': returns,
            'bias_pad_net_assignments': bias,
            'ground_and_bias_connectivity_or_ESD_qualification_performed': False,
            'power_rail_TVS_excluded': [{**parts[ref], 'terminals': [t for t in terminals['terminals'] if t['ref'] == ref],
                'reason': 'Power-rail suppressor, outside the signal-I/O cut contract; no all-TVS qualification claim'} for ref in ['D8', 'D9']],
            'endpoint_dependencies': dependencies, 'executions': executions,
            'limitations': actual_contract['excluded_scope'],
        }
        write(directory / 'coverage.json', report)
        source_reports[label] = {k: report[k] for k in ['board_sha256', 'historical_original', 'historical_actual_clamp', 'historical_nc_routing_pad', 'historical_supplemental', 'actual_clamp_cases', 'actual_clamp_channels', 'new_gap_cases', 'physical_protection_complete']}
    preserved_after = {str(path.relative_to(ROOT)): sha(path) for path in preserved_paths}
    assert preserved_before == preserved_after, 'Existing board/contracts/checks changed during audit'
    summary = {
        'schema': 'f722-actual-tvs-coverage-review/v1',
        'conclusion': 'Existing scopes omit D7.1 DSM_RX_EXT. The separate additive packet covers all 20 populated signal I/O clamps with 22 endpoint cases. Both sources remain unfinished at 6/22 cases, or 4/20 distinct channels. NC routing results are separate.',
        'source_reports': source_reports,
        'datasheet_pin_basis': MODELS,
        'existing_artifacts_preserved': True, 'existing_artifact_sha256': preserved_after,
        'new_contract_sha256': {name: sha(OUT / name) for name in ['gap-contracts.json', 'actual-io-contracts.json']},
        'authority_note': 'Preserved protection/pinout is the user goal. NC-first is a retained historical engineering convention, not claimed user authority or an internal bond. Existing NC contracts remain unchanged and are reported separately.',
    }
    write(OUT / 'summary.json', summary)
    print(json.dumps(source_reports, indent=2))


if __name__ == '__main__':
    main()
