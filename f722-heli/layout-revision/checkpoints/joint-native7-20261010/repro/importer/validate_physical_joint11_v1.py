#!/usr/bin/env python3
"""Serial owner-leased physical gates, with explicit per-stage outputs and scope.

Select one or more stages to match the owner's bounded lease. Existing checker
algorithms and clearance thresholds are unchanged. Failed gate outputs remain
diagnostic; this script does not adopt, route, normalize pads or alter the PCB.
"""
import argparse
import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from common_joint11 import HERE, ROOT, read, require, sha, validate_lease, write


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate', required=True, type=Path)
    ap.add_argument('--lease', required=True, type=Path)
    ap.add_argument('--stage', choices=['mechanics', 'process', 'critical', 'bonded', 'support'], action='append', required=True)
    ap.add_argument('--diagnostic', action='store_true')
    args = ap.parse_args()
    candidate = args.candidate.resolve()
    require(candidate.is_relative_to(HERE / 'candidates'), 'Candidate outside isolated version')
    spec = read(candidate / 'import-spec.json')
    transaction = candidate / 'selected-transaction.json'
    board = candidate / 'f722-heli.kicad_pcb'
    board_hash = sha(board)
    native_path = candidate / ('diagnostic-native-export.json' if args.diagnostic else 'f722-heli.native.json')
    native = read(native_path)
    require(native['board_sha256'] == board_hash, 'Stale native export')
    receipt = read(candidate / ('native-pad-structure-diagnostic.json' if args.diagnostic else 'construction-provenance.json'))
    require(receipt['board_sha256'] == board_hash and receipt['transaction_sha256'] == sha(transaction), 'Source receipt is stale')
    if args.diagnostic:
        require(not receipt['full_native_footprint_structure_differences_from_declared_operations'], 'Unexplained footprint structure change')
    source = ROOT / spec['source_project_directory']
    require(sha(source / 'f722-heli.kicad_pcb') == spec['source_board_sha256'], 'Source checkpoint changed')
    runtime = Path(spec['runtime']['directory'])
    scripts = ROOT / 'repo/f722-heli/layout-revision/scripts'
    bindings = read(HERE / 'physical-gate-tool-bindings-v1.json')
    for name, expected in bindings['files'].items():
        require(sha(ROOT / name) == expected, f'Physical gate tool changed: {name}')
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'python-deps'), MPLCONFIGDIR='/tmp/f722-joint-mpl')
    stages = list(dict.fromkeys(args.stage))
    all_results = {}
    for stage in stages:
        validate_lease(args.lease, 'physical_' + stage, transaction, candidate, spec)
        reports = candidate / (('diagnostic-' if args.diagnostic else '') + 'physical-' + stage + '-v1')
        reports.mkdir(exist_ok=False)
        commands = []

        def run(name, argv, allowed=(0, 1)):
            validate_lease(args.lease, 'physical_' + stage, transaction, candidate, spec)
            with (reports / (name + '.log')).open('x') as log:
                result = subprocess.run([str(x) for x in argv], env=env, stdout=log, stderr=subprocess.STDOUT)
            commands.append({'name': name, 'argv': [str(x) for x in argv], 'returncode': result.returncode,
                             'log_sha256': sha(reports / (name + '.log'))})
            require(result.returncode in allowed, f'{stage}/{name} failed unexpectedly; retained log')
            require(sha(board) == board_hash, 'Read-only physical gate changed PCB')

        if stage == 'mechanics':
            poses = {f['ref']: f['xy'] + [f['angle'], f['side']] for f in native['footprints']}
            declared = read(candidate / 'selected-poses.json')['changes']
            source_native = read(source / 'f722-heli.native.json')
            for f in source_native['footprints']:
                required = declared[f['ref']]['after'] if f['ref'] in declared else f['xy'] + [f['angle'], f['side']]
                actual = poses[f['ref']]
                require(actual[:2] == required[:2] and (actual[2] - required[2]) % 360 == 0 and actual[3] == required[3], 'Actual pose differs from source-bound target')
            write(reports / 'all-156-target-poses.json', poses)
            run('export', [runtime / 'python', scripts / 'export_mechanical_geometry.py', '--board', board,
                          '--source', source / 'f722-heli.kicad_pcb', '--out', reports / 'native-mechanical.json'], (0,))
            run('audit', [sys.executable, scripts / 'audit_mechanical_geometry.py', '--geometry', reports / 'native-mechanical.json',
                         '--poses', reports / 'all-156-target-poses.json', '--out', reports / 'mechanical-audit.json'])
            result = read(reports / 'mechanical-audit.json')
            brief = {'passed': result['passed'], 'gates': result['gates']}
        elif stage == 'process':
            run('process', [sys.executable, scripts / 'check_via_process.py', '--geometry', native_path, '--out', reports / 'process.json'])
            result = read(reports / 'process.json')
            brief = {k: result[k] for k in ('passed', 'total', 'board_sha256') if k in result}
        elif stage == 'critical':
            run('critical', [runtime / 'python', scripts / 'check_critical_connectivity.py', board, reports / 'critical.json'])
            run('firmware', [runtime / 'python', scripts / 'check_firmware_pinmap.py', '--board', board,
                             '--contract', ROOT / 'repo/f722-heli/validation/firmware-pinmap.json', '--out', reports / 'firmware.json'])
            result = read(reports / 'critical.json')
            firmware = read(reports / 'firmware.json')
            brief = {'fault_count': len(result['faults']),
                     'incomplete_critical_nets': [r['net'] for r in result['fullnet_connectivity'] if not r['complete']],
                     'missing_critical_ground_returns': [r['pad'] for r in result['critical_ground_returns'] if not r['connected_to_ground_plane']],
                     'firmware_passed': firmware['passed']}
            brief['passed'] = not (brief['fault_count'] or brief['incomplete_critical_nets'] or brief['missing_critical_ground_returns']) and brief['firmware_passed']
        elif stage == 'bonded':
            brief = {}
            for successor in spec['versioned_contract_successors']['expected_successor_contracts']:
                kind = successor['kind']
                contract = copy.deepcopy(successor['expected_content'])
                original = read(ROOT / contract['source_contract']['path'])
                require(contract['checks'] == original['checks'], 'Physical cut cases/thresholds changed')
                require(len(contract['checks']) == (18 if kind == 'candidate' else 22), 'Full cut inventory is required')
                contract['board_sha256'] = board_hash
                contract_path = reports / (kind + '-contracts.json')
                write(contract_path, contract)
                run(kind, [sys.executable, ROOT / 'repo/f722-heli/layout-revision/protection-review/tools/check_protection_paths.py',
                           '--geometry', native_path, '--contracts', contract_path, '--out', reports / (kind + '-cuts.json')])
                result = read(reports / (kind + '-cuts.json'))
                brief[kind] = {'passed': result['passed'], 'total': result['total'], 'all_pass': result['all_pass'],
                               'failed_cases': [r['id'] for r in result['checks'] if not r['complete_clamp_first_path_passes']]}
            brief['passed'] = all(brief[k]['all_pass'] for k in ('candidate', 'actual_io'))
        else:
            run('support', [sys.executable, HERE / 'check_full_support_joint11_v1.py', '--native', native_path,
                            '--board', board, '--source', source, '--transaction', transaction, '--out', reports / 'full-support.json'])
            result = read(reports / 'full-support.json')
            brief = {'passed': result['passed'], 'original_28_support_groups_complete': result['original_28_support_groups_complete'],
                     'original_critical_nets_complete': result['original_critical_nets_complete'],
                     'incomplete_nets': [n for n, r in result['nets'].items() if not r['complete']],
                     'missing_ground_returns': [n for n, ok in result['required_returns_reach_actual_saved_planes'].items() if not ok]}
        summary = {'schema': 'f722-joint-physical-stage/v1', 'stage': stage, 'board_sha256': board_hash,
                   'transaction_sha256': sha(transaction), 'native_export_sha256': sha(native_path),
                   'tool_bindings_sha256': sha(HERE / 'physical-gate-tool-bindings-v1.json'),
                   'diagnostic_only': args.diagnostic, 'result': brief, 'commands': commands,
                   'finite_entry_reference_AC_power_qualification_not_established': True, 'adoption_claimed': False}
        write(reports / 'summary.json', summary)
        all_results[stage] = brief
        print(json.dumps({'stage': stage, **brief}), flush=True)
        if stage in ('mechanics', 'process', 'critical'):
            require(brief.get('passed') is True, f'{stage} gate failed; stop for owner review without waiver')
    require(sha(board) == board_hash, 'Physical gates changed PCB')
    raise SystemExit(0 if all(r.get('passed') is True for r in all_results.values()) else 1)


if __name__ == '__main__':
    main()
