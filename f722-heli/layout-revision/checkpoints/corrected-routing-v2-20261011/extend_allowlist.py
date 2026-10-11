#!/usr/bin/env python3
"""Append closed router-v4 and sealed importer-v4 to the immutable prior plan."""
import collections
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'recovery-corrected-routing-checkpoint-prep-20261011'
FROZEN = ROOT / 'publication-frozen-negotiated-routing-v1-20261011'
PREFIX = 'f722-heli/layout-revision/checkpoints/negotiated-routing-v1-20261011/'
BASE = 'recovery-negotiated-routing-20261011/'
IMPORT = 'recovered-native7/recovery-importer/current-negotiated-import-v4/'


def sha(path):
    p = ROOT / path
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text())


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    assert sha(PRIOR / 'PREPARATION-SEAL.json') == 'c192dcc2e32fa02eedd2440862fc8e3085ea5a6724fd173b2ce736d6bc01ccbd'
    for name, row in read(PRIOR / 'PREPARATION-SEAL.json')['files'].items():
        assert sha(PRIOR / name) == row['sha256']
    old = read(PRIOR / 'source-allowlist.json')
    regen = read(PRIOR / 'regeneration-map.json')
    entries = {row['path']: row for row in old['source_entries']}
    frozen = read(FROZEN / 'payload' / PREFIX / 'reconstruction-map.json')
    expected = {}
    reasons = collections.defaultdict(set)

    def add(path, pin=None, reason='closed successor evidence'):
        p = Path(path)
        if p.is_absolute():
            p = p.relative_to(ROOT)
        path = str(p)
        assert '..' not in p.parts and '__pycache__' not in p.parts
        assert path != IMPORT + 'source-preparation.json', 'Superseded unsealed preparation excluded'
        if pin and expected.get(path):
            assert expected[path] == pin
        expected[path] = pin or expected.get(path)
        reasons[path].add(reason)

    router = BASE + 'negotiated-v4/'
    terminal = read(router + 'run/execution-receipt.json')
    assert sha(router + 'run/execution-receipt.json') == '286046b8528238f9cbbe212b3dbb6036ecfd682170b2e82397e245cd2d5f782d'
    assert terminal['passed'] is False and terminal['source_files_unchanged'] and terminal['lane_released']
    for row in terminal['saved_checkpoint_files']:
        add(row['path'], row['sha256'], 'closed v4 checkpoint receipt')
    for p in sorted((ROOT / router / 'run').rglob('*')):
        if p.is_file():
            assert not p.name.endswith('.next')
            add(p.relative_to(ROOT), reason='closed v4 raw terminal evidence')
    for name in ['composition-receipt.json', 'routing.dsn']:
        add(router + 'model/' + name, reason='closed v4 composition evidence')
    composition = read(router + 'model/composition-receipt.json')
    regen['files'][router + 'model/model.json'] = {'kind': 'regenerate', 'expected_sha256': composition['model_sha256'],
        'bytes': (ROOT / router / 'model/model.json').stat().st_size, 'contract': router + 'contract.json',
        'stage': 'composition', 'hash_authority': 'terminal v4 saved composition receipt', 'execution_during_preparation': False}
    seal_path = IMPORT + 'PREPARATION-SEAL.json'
    assert sha(seal_path) == 'acecee77ded1303549b61741e57f18be8894d82b6c8289af8403cccc9e7baebc'
    add(seal_path, sha(seal_path), 'immutable importer-v4 source seal')
    for row in read(seal_path)['files']:
        assert (Path(row['path'])).stat().st_size == row['bytes']
        add(row['path'], row['sha256'], 'immutable importer-v4 source seal')
    for path, pin in read(IMPORT + 'native-dependencies.json')['files'].items():
        add(path, pin, 'importer-v4 native dependency')
    for row in read(IMPORT + 'source-preparation-final.json')['source_files'].values():
        add(row['path'], row['sha256'], 'importer-v4 final source preparation')
    plan = read(IMPORT + 'terminal-diagnostic-native-plan.json')
    for path, pin in plan['source_files'].items():
        add(path, pin, 'importer-v4 terminal native plan dependency')
    binding = read(IMPORT + 'terminal-diagnostic-binding.json')
    for row in binding['files'] + [binding['producer_receipt']]:
        add(row['path'], row['sha256'], 'importer-v4 bound incomplete v2 candidate')
    diagnostic_path = IMPORT + 'diagnostic-terminal-review-v1.json'
    assert sha(diagnostic_path) == '12ae567d92d09809b3071537b0ded593cbefd7ea1b231a47c5bffb2be3449439'
    diagnostic = read(diagnostic_path)
    assert diagnostic['supervisor_exit_code'] == 0 and diagnostic['shared_lane_released_verified']
    add(diagnostic_path, sha(diagnostic_path), 'terminal native diagnostic exact inventory review')
    for row in diagnostic['terminal_output_files']:
        assert Path(row['path']).stat().st_size == row['bytes']
        add(row['path'], row['sha256'], 'terminal native diagnostic output or historical issued lease')
    assert len(diagnostic['terminal_output_files']) == 88
    # Preserve the runtime restoration recipe and small signed/pinned provenance;
    # do not duplicate official binaries or package archives.
    for name in ['README.md', 'validation.json', 'RESTORATION-REPORT.json', 'restore_runtime.py', 'package-manifest.json',
                 'provenance/packages-verified.json', 'provenance/wrapper-source-identities.json',
                 'provenance/signature-verification.txt', 'provenance/snapshot-index-pinned-comparison.json']:
        add('kicad10-runtime/' + name, reason='official native runtime restoration provenance')

    for path, pin in sorted(expected.items()):
        p = ROOT / path
        assert p.is_file(), path
        if path in regen['files']:
            old_regen = regen['files'][path]
            expected_pin = old_regen.get('expected_sha256', old_regen.get('entry', {}).get('expected_sha256'))
            assert pin is None or expected_pin == pin
            continue
        if path.startswith('kicad10-runtime/root/'):
            assert pin
            regen['files'][path] = {'kind': 'restore_official_runtime', 'expected_sha256': pin, 'bytes': p.stat().st_size,
                'recipe': 'kicad10-runtime/restore_runtime.py', 'manifest': 'kicad10-runtime/package-manifest.json',
                'runtime_version': '10.0.6+dfsg-1', 'capture_binary': False}
            continue
        digest = sha(path)
        assert pin is None or digest == pin, ('changed source', path)
        if path in entries:
            assert entries[path]['sha256'] == digest, ('old sealed source changed', path)
            continue
        data_size = p.stat().st_size
        git = hashlib.sha1(b'blob ' + str(data_size).encode() + b'\0')
        with p.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                git.update(chunk)
        row = {'path': path, 'sha256': digest, 'git_blob_sha': git.hexdigest(), 'bytes': data_size,
               'bytes_verified': True, 'reasons': sorted(reasons[path])}
        if digest in frozen['objects']:
            row['storage'] = 'reuse_frozen_negotiated_v1_object'
            row['source'] = {'checkpoint_manifest_sha256': '5db551817f51f75df2c66613c78c799c227634543a287278388c735535d67af5',
                'reconstruction_map': PREFIX + 'reconstruction-map.json', 'object_sha256': digest,
                'prior_storage': frozen['objects'][digest],
                'restore_alias': next(k for k, value in frozen['restore_files'].items() if value == digest),
                'publication_status': 'FROZEN_LOCAL_PUBLICATION_PENDING'}
        else:
            row['storage'] = 'capture_unique_successor_object'
        entries[path] = row
    objects = {}
    for row in entries.values():
        objects.setdefault(row['sha256'], {'bytes': row['bytes'], 'storage': row['storage'],
            'representative_path': row['path'], 'aliases': []})['aliases'].append(row['path'])
    stats = {mode: {'paths': sum(row['storage'] == mode for row in entries.values()),
                    'unique_objects': sum(row['storage'] == mode for row in objects.values()),
                    'unique_bytes': sum(row['bytes'] for row in objects.values() if row['storage'] == mode)}
             for mode in sorted({row['storage'] for row in entries.values()})}
    checkpoints = []
    initial_exact = sha(router + 'run/candidate.fixed-traces-before.exact')
    for num in range(1, 7):
        stem = router + 'run/candidate.checkpoints/checkpoint-' + str(num).zfill(4)
        d = read(stem + '.after.json')
        assert sha(stem + '.fixed-traces-after.exact') == initial_exact
        checkpoints.append({'report_path': stem + '.after.json', 'report_sha256': sha(stem + '.after.json'),
            'session_path': stem + '.ses', 'session_sha256': sha(stem + '.ses'),
            'fixed_trace_sha256': initial_exact, 'fixed_trace_equal_to_initial': True,
            'missing_required_joins': sum(max(0, len(x['groups']) - 1) for x in d['required_logical_connectivity']),
            'connected_roles': sum(x['engine_all_items_connected'] for x in d['required_logical_connectivity'])})
    write('source-allowlist.json', {'schema': 'f722-corrected-routing-recovery-plan/v2', 'status': 'LOCAL_APPEND_ONLY_PREPARATION_ALL_BOUND_EXECTIONS_TERMINAL',
        'source_entries': sorted(entries.values(), key=lambda x: x['path']), 'unique_objects': objects, 'statistics': stats,
        'immutable_prior_plan_seal_sha256': 'c192dcc2e32fa02eedd2440862fc8e3085ea5a6724fd173b2ce736d6bc01ccbd',
        'frozen_local_predecessor': old['frozen_local_predecessor'], 'inherited_source_paths_unchanged': len(old['source_entries']),
        'native_diagnostic_outputs': 'TERMINAL_87_FILE_TREE_AND_HISTORICAL_LEASE_BOUND', 'accepted_board': 'native7',
        'numerical_power': 'STALE', 'native_acceptance': False, 'compression_not_performed': True})
    regen['schema'] = 'f722-corrected-routing-regeneration-plan/v2'
    regen['v4_runtime_outputs'] = 'CLOSED_RAW_ROUTER_OUTPUTS_INCLUDED_MODELS_REGENERATE'
    write('regeneration-map.json', regen)
    status = read(PRIOR / 'evidence-status.json')
    status['schema'] = 'f722-corrected-routing-evidence-status/v2'
    status['v4_status'] = 'FAILED_ZERO_LENGTH_FIXED_TRACE_GATE_AFTER_PASS1_CLEANUP_NO_FINAL_EXPORT'
    status['v4_terminal_receipt_sha256'] = sha(router + 'run/execution-receipt.json')
    status['v4_terminal_elapsed_seconds'] = terminal['elapsed_seconds']
    status['v4_six_last_good_checkpoints'] = checkpoints
    status['v4_final_report_and_session_absent'] = all(not (ROOT / router / 'run' / name).exists() for name in ['candidate.after.json', 'candidate.ses'])
    status['importer_v4'] = {'seal_sha256': 'acecee77ded1303549b61741e57f18be8894d82b6c8289af8403cccc9e7baebc',
        'sealed_source_files': 16, 'bound_candidate': 'incomplete negotiated-v2 terminal; 5 of 19 roles',
        'retained_mutable_source_records': 21, 'removed_mutable_source_records': 121,
        'converted_tracks': 56, 'converted_vias': 3, 'additional_fixed_tracks': 6,
        'superseded_all142_removal_evidence_preserved_as_superseded': True,
        'native_execution_request_is_historical_pregrant_state': True,
        'native_diagnostic_result': 'TERMINAL_DIAGNOSTIC_ONLY_17_OPENS_28_WARNINGS_NO_OTHER_DRC_ERRORS',
        'native_diagnostic_review_sha256': sha(diagnostic_path),
        'native_control_receipt_sha256': '6eef8bbfd6c073068edac418bbd22a8b1d19e9b3717f4b751fb30f9ff4ded705',
        'native_export_sha256': 'b1e44d81375bc292c156b21f9e35b593b3164319615082080748396ffd85cb40',
        'ERC_and_parity_zero': True, 'full_record_and_syntax_checks_passed': True,
        'historical_issued_lease_is_provenance_only_not_new_execution_permission': True}
    write('evidence-status.json', status)
    write('preparation-verification.json', {'schema': 'f722-corrected-successor-byte-preparation/v2',
        'paths': len(entries), 'objects': len(objects), 'inherited350_source_entries_unchanged': all(entries[x['path']] == x for x in old['source_entries']),
        'new_sources_rehashed': True, 'importer_v4_all16_source_files_seal_verified': True,
        'all_six_closed_v4_checkpoint_triplets_bound': True, 'native_diagnostic_terminal88_rows_hash_verified': True,
        'no_active_native_diagnostic_output_included': True,
        'old_sealed_plan_and_frozen_v1_untouched': True, 'heavy_lock_acquired': False, 'external_writes': False,
        'statistics': stats})
    print(json.dumps({'paths': len(entries), 'objects': len(objects), 'regenerated': len(regen['files']), 'statistics': stats}, indent=2))


if __name__ == '__main__':
    main()
