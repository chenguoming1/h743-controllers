#!/usr/bin/env python3
"""Cleanly apply V15, run portable controls, and reject malformed delta inputs."""
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--delta', type=Path, required=True)
    parser.add_argument('--base-project', type=Path, required=True)
    parser.add_argument('--zip-sha256', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.base = args.base.resolve()
    args.delta = args.delta.resolve()
    args.base_project = args.base_project.resolve()
    spec = importlib.util.spec_from_file_location('apply_v15', ROOT / 'tools/apply_source_delta_v15.py')
    apply = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(apply)
    before = {str(p.relative_to(ROOT)): sha(p) for p in ROOT.rglob('*') if p.is_file()}
    files, metadata = apply.prepare(args.base, args.delta, args.zip_sha256)
    assert {name: hashlib.sha256(data).hexdigest() for name, data in files.items()} == before
    negatives = []

    def reject(label, operation):
        try:
            operation()
        except (ValueError, KeyError, AssertionError):
            negatives.append(label)
        else:
            raise AssertionError('Invalid delta accepted: ' + label)

    reject('wrong ZIP digest', lambda: apply.prepare(args.base, args.delta, '0' * 64))
    reject('wrong manifest digest', lambda: apply.verify_tree(files, '0' * 64))
    bad_files = dict(files)
    bad_files['README.md'] += b'\n'
    reject('tampered tree payload', lambda: apply.verify_tree(bad_files, metadata['new_manifest_sha256']))
    with tempfile.TemporaryDirectory(prefix='v15-clean-portable-') as temp:
        tmp = Path(temp)
        rebuilt = tmp / 'rebuilt'
        rebuilt.mkdir()
        for name, data in files.items():
            target = rebuilt / apply.relative(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        result_path = tmp / 'portable.json'
        result = subprocess.run([sys.executable, '-B', str(rebuilt / 'tests/verify_v15_evidence.py'),
            '--base-project', str(args.base_project), '--out', str(result_path)],
            cwd=tmp, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), capture_output=True, text=True)
        assert result.returncode == 0, (result.stdout, result.stderr)
        portable = json.loads(result_path.read_bytes())
        assert portable['passed'] and not portable['original_source_hash_checks_performed']
        with zipfile.ZipFile(args.delta) as archive:
            entries = [(name, archive.read(name)) for name in archive.namelist()]
        unsafe = tmp / 'unsafe.zip'
        with zipfile.ZipFile(unsafe, 'w') as archive:
            for name, data in entries:
                archive.writestr(name, data)
            archive.writestr('../escape', b'rejected')
        reject('unsafe archive path despite matching supplied ZIP digest', lambda: apply.prepare(args.base, unsafe, sha(unsafe)))
        tampered = tmp / 'tampered.zip'
        with zipfile.ZipFile(tampered, 'w') as archive:
            for name, data in entries:
                archive.writestr(name, data + b'\n' if name == 'changed/README.md' else data)
        reject('changed payload hash mismatch despite matching supplied ZIP digest', lambda: apply.prepare(args.base, tampered, sha(tampered)))
        assert {str(p.relative_to(rebuilt)): sha(p) for p in rebuilt.rglob('*') if p.is_file()} == before
    assert {str(p.relative_to(ROOT)): sha(p) for p in ROOT.rglob('*') if p.is_file()} == before
    assert sha(args.base / 'FILES.sha256.json') == apply.BASE_MANIFEST
    result = {'passed': True, 'zip_sha256': sha(args.delta), 'zip_bytes': args.delta.stat().st_size,
        'base_manifest_sha256': apply.BASE_MANIFEST, 'new_manifest_sha256': metadata['new_manifest_sha256'],
        'clean_delta_application_verified': True, 'portable_verifier_passes_without_historical_workspace': True,
        'required_external_input': 'Hash-pinned candidate43/V14 accepted43 paired project,61 bound files including parts.json',
        'exact_recovered_projects': len(portable['recovered_projects']), 'selected_evidence_files_verified': portable['raw_files_verified'],
        'excluded_raw_files': portable['excluded_raw_files'],
        'native_replay_inputs_complete': False,
        'real_reference_classifier_reexecuted': False,
        'evidence_negative_controls': portable['negative_controls_passed'],
        'delta_negative_controls': len(negatives), 'delta_negative_control_names': negatives,
        'total_negative_controls': portable['negative_controls_passed'] + len(negatives),
        'heavy_or_native_execution_performed': False, 'numerical_power_and_VCAP_applicability': False,
        'sealed_staging_untouched': True, 'immutable_v14_base_unchanged': True,
        'verifier_source_sha256': sha(__file__)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
