#!/usr/bin/env python3
"""Verify or recover frozen routing inputs using only the Python standard library.

This does not import any routing source, construct geometry, or run native tools.
"""
import argparse
import ast
import hashlib
import json
import lzma
import os
from pathlib import Path, PurePosixPath
import subprocess


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe(root, relative):
    name = PurePosixPath(relative)
    if name.is_absolute() or '..' in name.parts:
        raise ValueError('Unsafe relative path: ' + relative)
    path = root.joinpath(*name.parts)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Path escapes selected root: ' + relative)
    return path


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args],
                                   env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))


def check(root, repo):
    manifest = json.loads((root / 'FILES.sha256.json').read_text())
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
              if p.is_file() and p.relative_to(root).as_posix() != 'FILES.sha256.json'}
    assert actual == set(manifest), 'Package differs from exact allowlist'
    for name, expected in manifest.items():
        assert digest(safe(root, name).read_bytes()) == expected, name
    public = json.loads((root / 'PUBLIC_SOURCE_ALLOWLIST.json').read_text())
    assert set(public['files']) == actual | {'FILES.sha256.json'}
    index = json.loads((root / 'raw-evidence.json').read_text())
    base = index['base']
    # The local checkpoint and published PR may have different commit IDs but
    # the identical frozen tree. Read by tree identity for portable recovery.
    assert git(repo, 'cat-file', '-t', base['tree']).decode().strip() == 'tree'
    payloads = {}
    py_count = json_count = 0
    for name, row in index['files'].items():
        if 'base_git_path' in row:
            data = git(repo, 'show', base['tree'] + ':' + row['base_git_path'])
        elif 'compressed_file' in row:
            packed = safe(root, row['compressed_file']).read_bytes()
            assert digest(packed) == row['compressed_sha256'], name
            data = lzma.decompress(packed)
        else:
            data = safe(root, row['file']).read_bytes()
        assert len(data) == row['bytes'] and digest(data) == row['sha256'], name
        if name.endswith('.py'):
            ast.parse(data, filename=name)
            py_count += 1
        elif name.endswith('.json'):
            json.loads(data)
            json_count += 1
        payloads[name] = data
    required = json.loads((root / 'DEPENDENCIES.json').read_text())
    for row in required['local_import_edges'] + required['runtime_file_edges']:
        assert row['to'] in payloads, row
    prefix = 'ordinary-routing/tests/native13-access/'
    recovery = json.loads(payloads[prefix + 'RECOVERY-native11-joint-v5.json'])
    for section in ('files', 'native_input_files'):
        for name, expected in recovery[section].items():
            assert digest(payloads['ordinary-routing/' + name]) == expected, name
    completed = json.loads(payloads[prefix + 'dedicated-IMU-DSM-CS-complete11.json'])
    for name, expected in completed['imported_recipe_hashes'].items():
        assert digest(payloads['ordinary-routing/' + name]) == expected, name
    assert completed['complete'] and completed['all_terminal_partitions_preserved']
    assert completed['full_CS_tree_complete'] and completed['dedicated_return_contact_pass']
    assert all(row['passed'] for key in ('route_checks', 'via_checks') for row in completed[key])
    recorded = json.loads(payloads[prefix + 'dedicated-joint-recorded-transaction11.json'])
    for name, expected in recorded['imported_code_hashes'].items():
        assert digest(payloads['ordinary-routing/' + name]) == expected, name
    assert recorded['constructor_argument_capture']
    assert recorded['all_selected_new_shapes_match_recorded_constructor_bytes']
    assert len(recorded['added_copper']) == 89 and len(recorded['changed_pad_records']) == 18
    assert sorted(recorded['missing_actual_pad_keys']) == ['R43.1', 'R43.2', 'R44.1', 'R44.2']
    assert not recorded['native_candidate'] and not recorded['complete_pad_inventory']
    boot = json.loads(payloads[prefix + 'BOOT-complete-current-peer-sealed11.json'])
    assert boot['complete_actual_BOOT_tree'] and boot['all_finite_pass']
    assert len(boot['actual_terminal_groups']['SW1.2']) == 2
    review_prefix = prefix + 'review-imu-return11/'
    review = json.loads(payloads[review_prefix + 'review.json'])
    external = json.loads((root / 'EXTERNAL_MANUFACTURER_EVIDENCE.json').read_text())['files']
    for row in review['source_files']:
        if row['path'] in payloads:
            assert digest(payloads[row['path']]) == row['sha256'], row['path']
        else:
            assert external[row['path']]['sha256'] == row['sha256'], row['path']
    for name, row in json.loads(payloads[review_prefix + 'FILES.sha256.json']).items():
        if review_prefix + name in payloads:
            assert digest(payloads[review_prefix + name]) == row['sha256'], name
        else:
            assert external[review_prefix + name]['sha256'] == row['sha256'], name
    identities = json.loads(payloads[prefix + 'review-joint-identities11.json'])
    for row in identities['reviewed_files']:
        assert digest(payloads[row['path']]) == row['sha256'], row['path']
    return payloads, dict(passed=True, package_file_count=len(manifest) + 1,
                         restored_file_count=len(payloads), restored_bytes=sum(map(len, payloads.values())),
                         python_syntax_files=py_count, json_syntax_files=json_count,
                         external_manufacturer_payloads_omitted=len(external),
                         native_or_geometry_execution=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-repo', type=Path, required=True)
    parser.add_argument('--out', type=Path, help='New isolated workspace; omit for verification only')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    payloads, result = check(root, args.base_repo.resolve())
    if args.out is not None:
        target = args.out.resolve()
        assert not target.exists(), 'Output must not already exist'
        target.mkdir(parents=True)
        for name, data in payloads.items():
            path = safe(target, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for name, data in payloads.items():
            assert safe(target, name).read_bytes() == data, name
        result['materialized'] = str(target)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
