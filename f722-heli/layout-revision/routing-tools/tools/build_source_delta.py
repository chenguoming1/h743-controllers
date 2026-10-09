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

BASE_MANIFEST_SHA256 = '13f0fa03eaf62d3ae16635109877499976843e7289f97372cb4e2143cdd180e6'
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
        'scope': 'Source-only allowlist, exclusions, Python/JSON/shell syntax. No JVM, native PCB operation, full model, or route search.',
        'base_manifest_sha256': BASE_MANIFEST_SHA256,
        'python_sources_compiled_in_memory': python_files,
        'shell_sources_syntax_checked': shell_files,
        'cache_files_created': False,
        'large_models_boards_binaries_excluded': True,
    })
    current = files(stage)
    all_names = sorted(set(current) | {'FILES.sha256.json', 'PUBLIC_SOURCE_ALLOWLIST.json'})
    write(stage / 'PUBLIC_SOURCE_ALLOWLIST.json', {
        'status': 'unfinished_source_and_native_constructed_routing_checkpoint_v9',
        'base_manifest_sha256': BASE_MANIFEST_SHA256,
        'native_open_connections': 55,
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
        'application': 'Verify the complete immutable v8 base, apply changed/ relative to its root, remove only listed deleted_files, then verify the complete new manifest and allowlist.',
        'changed_files_sha256': changed,
        'deleted_files': deleted,
        'unchanged_file_count': len(current) - len(changed),
        'full_file_count': len(current),
        'unfinished': True,
        'checkpoint': 'owner-adopted candidate28,55 native opens,0 errors,0 warnings',
        'base_delta_zip_sha256': '5566e05ad8e58e9bdaad815bcf066db6883a33f685066a6af4aed4eff298e96b',
        'candidate_board_sha256': '3afc574bdd766292932323c54fd198cc2cb88ab93617a434fe5d104ab01838d2',
        'numerical_power_and_VCAP_applicability': False,
        'heavy_or_native_execution_performed': False,
        'unfinished_source28_filtered03_included': False,
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
    with tempfile.TemporaryDirectory(prefix='v9-delta-check-', dir=args.out_prefix.parent) as temp:
        rebuilt = Path(temp) / 'rebuilt'
        shutil.copytree(base, rebuilt)
        with zipfile.ZipFile(zip_path) as archive:
            assert len(archive.namelist()) == len(changed) + 1
            for name, digest in changed.items():
                data = archive.read('changed/' + name)
                assert hashlib.sha256(data).hexdigest() == digest
                dest = rebuilt / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
        for name in deleted:
            (rebuilt / name).unlink()
        assert files(rebuilt) == current
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
