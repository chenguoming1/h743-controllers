#!/usr/bin/env python3
"""Validate source staging, write full manifests, and emit a base-bound delta ZIP."""
import argparse
import ast
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

BASE_MANIFEST_SHA256 = '96187ae69afc1f7136982eb16a63673cef8f639a4ee67cfadef8a56d61f6f7fe'
FORBIDDEN_SUFFIXES = {'.pyc', '.pyo', '.class', '.jar', '.kicad_pcb', '.brd', '.dsn', '.so', '.dll', '.zip'}
FORBIDDEN_PARTS = {'__pycache__', '.git', 'build', 'node_modules', 'dream_notes', 'agent_notes', 'private-notes'}
SYNTHETIC_FIXTURES = {
    'tests/failed-search-state/fixture/model.json',
    'tests/failed-search-state/fixture/routing.dsn',
    'tests/end-queue-stop/fixture/model.json',
    'tests/end-queue-stop/fixture/routing.dsn',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def files(root):
    result = {}
    for path in root.rglob('*'):
        assert not path.is_symlink(), f'Symlink excluded: {path}'
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        assert not (set(rel.parts) & FORBIDDEN_PARTS), rel
        fixture = str(rel) in SYNTHETIC_FIXTURES
        assert path.suffix.lower() not in FORBIDDEN_SUFFIXES or fixture, rel
        assert path.name not in {'model.json', 'native.json', 'owner-native.json'} or fixture, rel
        if fixture:
            assert path.stat().st_size < 8192, rel
            if path.name == 'model.json':
                assert json.loads(path.read_text())['synthetic_only'] is True, rel
            else:
                assert path.read_text().startswith('(pcb '), rel
        assert path.stat().st_size < 2_000_000, f'Large payload excluded: {rel}'
        result[str(rel)] = sha(path)
    return dict(sorted(result.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', type=Path, required=True)
    ap.add_argument('--staging', type=Path, required=True)
    ap.add_argument('--out-prefix', type=Path, required=True)
    args = ap.parse_args()
    base = args.base.resolve()
    stage = args.staging.resolve()
    assert base != stage
    assert sha(base / 'FILES.sha256.json') == BASE_MANIFEST_SHA256
    base_files = files(base)
    base_manifest = json.loads((base / 'FILES.sha256.json').read_text())
    assert {k: v for k, v in base_files.items() if k != 'FILES.sha256.json'} == base_manifest
    assert set(json.loads((base / 'PUBLIC_SOURCE_ALLOWLIST.json').read_text())['files']) == set(base_files)
    current = files(stage)
    python_files = []
    shell_files = []
    for name in current:
        path = stage / name
        if path.suffix == '.py':
            compile(ast.parse(path.read_text(), filename=name), name, 'exec')
            python_files.append(name)
        elif path.suffix == '.json':
            json.loads(path.read_text())
        elif path.suffix == '.sh':
            subprocess.run(['bash', '-n', str(path)], check=True)
            shell_files.append(name)
    write(stage / 'checks/source-package-validation.json', {
        'passed': True,
        'scope': 'Source/evidence allowlist, exclusions, Python/JSON/shell syntax; selected historical raw data compressed losslessly. No JVM, native PCB operation, or route search.',
        'base_manifest_sha256': BASE_MANIFEST_SHA256,
        'python_sources_compiled_in_memory': python_files,
        'shell_sources_syntax_checked': shell_files,
        'cache_files_created': False,
        'uncompressed_large_exports_and_boards_excluded': True,
        'selected_authoritative_transaction_receipt_losslessly_compressed': True,
        'full_raw_diagnostic_container_included': False,
    })
    current = files(stage)
    all_names = sorted(set(current) | {'FILES.sha256.json', 'PUBLIC_SOURCE_ALLOWLIST.json'})
    write(stage / 'PUBLIC_SOURCE_ALLOWLIST.json', {
        'status': 'unfinished_explicit_native_construction_checkpoint_v21',
        'base_manifest_sha256': BASE_MANIFEST_SHA256,
        'native_open_connections': 14,
        'files': all_names,
    })
    current = files(stage)
    current.pop('FILES.sha256.json', None)
    write(stage / 'FILES.sha256.json', current)
    current = files(stage)
    changed = {k: v for k, v in current.items() if base_files.get(k) != v}
    deleted = sorted(set(base_files) - set(current))
    metadata = {
        'schema': 'f722-source-delta/v1',
        'base_manifest_sha256': BASE_MANIFEST_SHA256,
        'new_manifest_sha256': sha(stage / 'FILES.sha256.json'),
        'base_allowlist_sha256': sha(base / 'PUBLIC_SOURCE_ALLOWLIST.json'),
        'new_allowlist_sha256': sha(stage / 'PUBLIC_SOURCE_ALLOWLIST.json'),
        'payload_directory': 'changed',
        'application': 'Verify the complete immutable V20 base, apply changed/ relative to its root, remove only listed deleted_files, then verify the complete new manifest and allowlist.',
        'changed_files_sha256': changed, 'deleted_files': deleted,
        'unchanged_file_count': len(current) - len(changed), 'full_file_count': len(current),
        'unfinished': True, 'checkpoint': 'owner-adopted candidate54/14 native opens,0 errors,0 warnings',
        'base_delta_zip_sha256': '7c5fda16f2f1dc4cddd15212879e5a0205f4d9e0e036844261c17272e88da88f',
        'candidate_board_sha256': '24121b0e46d9a71207cd21e7cf599412c00796d48eb9af5f63ffcf92e5f2ca42',
        'latest_included_candidate': 54, 'actual_io_cases': [20,22],
        'historical_SERVO15_RPM14_separately_adopted': False,
        'native_replay_inputs_complete': False, 'heavy_or_native_execution_performed': False,
        'numerical_power_and_VCAP_applicability': False, 'source43_power_result_scope': 'Historical source43/37 only',
        'cumulative_USB_N_width_delta_retained_mm2': 2.6376462125554667e-10,
        'RPM_width_residue_retained_mm2': 2.725130554532544e-05,

    }
    args.out_prefix.parent.mkdir(parents=True, exist_ok=True)
    meta_path = Path(str(args.out_prefix) + '.metadata.json')
    zip_path = Path(str(args.out_prefix) + '.zip')
    write(meta_path, metadata)
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        def put(name, content):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 9, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
        put('DELTA.json', meta_path.read_bytes())
        for name in changed:
            put('changed/' + name, (stage / name).read_bytes())
    # Verify complete delta application in memory; no broad second source-tree copy.
    rebuilt = {name:(base/name).read_bytes() for name in base_files}
    with zipfile.ZipFile(zip_path) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(changed) + 1
        for name, digest in changed.items():
            data=archive.read('changed/'+name)
            assert hashlib.sha256(data).hexdigest()==digest
            rebuilt[name]=data
    for name in deleted: del rebuilt[name]
    assert {name:hashlib.sha256(data).hexdigest() for name,data in rebuilt.items()}==current
    assert sha(base / 'FILES.sha256.json') == BASE_MANIFEST_SHA256
    result = {
        'passed': True,
        'base_unchanged': True,
        'delta_application_reconstructs_exact_staging': True,
        'changed_file_count': len(changed),
        'deleted_file_count': len(deleted),
        'full_file_count': len(current),
        'zip_bytes': zip_path.stat().st_size,
        'zip_sha256': sha(zip_path),
        'metadata_sha256': sha(meta_path),
        'new_manifest_sha256': metadata['new_manifest_sha256'],
    }
    write(Path(str(args.out_prefix) + '.verification.json'), result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
