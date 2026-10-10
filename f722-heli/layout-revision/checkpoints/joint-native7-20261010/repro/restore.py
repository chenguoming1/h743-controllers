#!/usr/bin/env python3
"""Verify/materialize this exact checkpoint in a fresh workspace; no Git writes.

Default mode performs host file/hash work only. --export-native explicitly runs
the pinned official KiCad exporter for the source and reference candidate, under
the caller's permitted native-job scheduling. It does not reconstruct/adopt a PCB.
"""
import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe(root, relative):
    relative = Path(relative)
    require(not relative.is_absolute() and '..' not in relative.parts, 'Unsafe manifest path')
    return root / relative


def verify_package():
    manifest = json.loads((PACKAGE / 'MANIFEST.json').read_text())
    observed = {str(p.relative_to(PACKAGE)) for p in PACKAGE.rglob('*') if p.is_file()}
    require(observed == set(manifest['files']) | {'MANIFEST.json'}, 'Unexpected/missing package files')
    for name, row in manifest['files'].items():
        path = safe(PACKAGE, name)
        require(not path.is_symlink(), 'Symlinks are not accepted in the package')
        data = path.read_bytes()
        require(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'] and
                git_blob(data) == row['git_blob_sha1'], 'Package identity mismatch: ' + name)
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repository', type=Path, help='A checkout of the exact required PR18/base tree')
    ap.add_argument('--workspace', type=Path, help='New empty restoration directory; must not already exist')
    ap.add_argument('--runtime', type=Path, help='Existing pinned official KiCad10 runtime directory')
    ap.add_argument('--verify-only', action='store_true')
    ap.add_argument('--export-native', action='store_true')
    args = ap.parse_args()
    manifest = verify_package()
    dep = json.loads((PACKAGE / 'repro/DEPENDENCIES.json').read_text())
    raw = gzip.decompress((PACKAGE / 'repro/selected-transaction.json.gz').read_bytes())
    require(len(raw) == dep['transaction']['source_bytes'] and hashlib.sha256(raw).hexdigest() == dep['transaction']['source_sha256'],
            'Lossless transaction restoration failed')
    if args.verify_only:
        print(json.dumps({'package_files_verified': len(manifest['files']), 'lossless_transaction_verified': True,
                          'native_execution': False, 'Git_writes': False}))
        return
    require(args.repository is not None and args.workspace is not None and args.runtime is not None,
            '--repository, --workspace and --runtime are required for restoration')
    repository, workspace, runtime = args.repository.resolve(), args.workspace.resolve(), args.runtime.resolve()
    require(not workspace.exists(), 'Refusing to overwrite an existing workspace')
    for row in dep['base_repository_files']:
        path = safe(repository, row['repository_path'])
        data = path.read_bytes()
        require(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'] and
                git_blob(data) == row['git_blob_sha1'], 'Required base file differs: ' + row['repository_path'])
    for name, expected in dep['runtime']['pinned_files'].items():
        require(digest(safe(runtime, name)) == expected, 'Pinned runtime input differs: ' + name)
    workspace.mkdir(parents=True, exist_ok=False)

    def copy(src, relative, expected=None):
        dest = safe(workspace, relative)
        require(not dest.exists(), 'Duplicate restoration destination: ' + str(relative))
        if expected:
            require(digest(src) == expected, 'Restoration input changed')
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        require(digest(dest) == digest(src), 'Restored file hash differs')
        return dest

    for row in dep['base_repository_files']:
        copy(safe(repository, row['repository_path']), row['restore_path'], row['sha256'])
    for row in dep['additional_exact_source_inputs']:
        copy(safe(PACKAGE, row['payload_path']), row['restore_path'], row['sha256'])
    importer_rel = Path(dep['original_importer_restore_directory'])
    for path in (PACKAGE / 'repro/importer').glob('*'):
        target = safe(workspace, importer_rel / path.name)
        if target.exists():
            require(digest(target) == digest(path), 'Inconsistent shared importer dependency')
        else:
            copy(path, importer_rel / path.name)
    original_spec = copy(PACKAGE / 'repro/import-spec.json', importer_rel / 'joint-native11-import-spec-v1.json')
    local_spec = json.loads(original_spec.read_text())
    old_runtime_path = local_spec['runtime']['directory']
    local_spec['runtime']['directory'] = str(runtime)
    relocated = safe(workspace, importer_rel / 'joint-native11-import-spec-v1.local.json')
    relocated.write_text(json.dumps(local_spec, indent=2) + '\n')
    transaction = safe(workspace, importer_rel / 'selected-transaction.json')
    transaction.write_bytes(raw)
    poses = copy(PACKAGE / 'repro/selected-poses.json', importer_rel / 'selected-poses.json')
    reference_rel = importer_rel / 'candidates/published-reference02'
    for path in (PACKAGE / 'hardware').rglob('*'):
        if path.is_file():
            copy(path, reference_rel / path.relative_to(PACKAGE / 'hardware'))
    reference = safe(workspace, reference_rel)
    pending = []
    for name, record, board in [
        ('source', dep['source_native_export'], workspace / dep['source_native_export']['regenerate_from']),
        ('candidate', dep['candidate_native_export'], reference / 'f722-heli.kicad_pcb')]:
        out = (workspace / record['restore_path']) if name == 'source' else reference / 'f722-heli.native.json'
        if args.export_native:
            exporter = workspace / dep['source_native_export']['exporter_restore_path']
            subprocess.run([str(runtime / 'python'), str(exporter), '--board', str(board), '--out', str(out)], check=True)
            require(digest(out) == record['sha256'], name + ' native regeneration SHA differs')
        else:
            pending.append({'name': name, 'output': str(out.relative_to(workspace)), 'expected_sha256': record['sha256']})
    receipt = {'schema': 'f722-joint-public-restore/v1', 'package_manifest_sha256': digest(PACKAGE / 'MANIFEST.json'),
        'required_base_tree': dep['base_tree_binding'], 'original_spec_sha256': digest(original_spec),
        'localized_spec_sha256': digest(relocated),
        'only_spec_configuration_change': {'field': 'runtime.directory', 'original': old_runtime_path, 'localized': str(runtime)},
        'transaction_sha256': digest(transaction), 'selected_poses_sha256': digest(poses),
        'reference_board_sha256': digest(reference / 'f722-heli.kicad_pcb'),
        'pending_native_exports': pending, 'native_export_executed': args.export_native,
        'source_geometry_or_net_inputs_changed': False, 'Git_or_canonical_adoption_actions': False}
    (workspace / 'RESTORE-RECEIPT.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'workspace': str(workspace), 'reference_project': str(reference / 'f722-heli.kicad_pro'),
                      'transaction_sha256': digest(transaction), 'pending_native_exports': len(pending),
                      'native_export_executed': args.export_native, 'Git_writes': False}))


if __name__ == '__main__':
    main()
