#!/usr/bin/env python3
"""Apply the V15 delta to an immutable, fully verified V14 source package.

Standard library only. Supply the separately published ZIP SHA-256. Output must
not exist; every input and resulting file hash is verified before any write.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath

BASE_MANIFEST = '1163f669a266b135b8f88ba8fab5ceb31fea0fd2f2f570ec015399d1a676d52a'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def relative(name):
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError('Unsafe relative path')
    path = PurePosixPath(name)
    if path.is_absolute() or any(p in ('', '.', '..') for p in name.split('/')):
        raise ValueError('Unsafe relative path')
    return Path(*path.parts)

def verify_tree(files, expected_manifest):
    if digest(files['FILES.sha256.json']) != expected_manifest:
        raise ValueError('Manifest hash mismatch')
    manifest = json.loads(files['FILES.sha256.json'])
    for name in manifest:
        relative(name)
    actual = {name: digest(data) for name, data in files.items() if name != 'FILES.sha256.json'}
    if actual != manifest:
        raise ValueError('Complete file manifest mismatch')
    allowlist = json.loads(files['PUBLIC_SOURCE_ALLOWLIST.json'])['files']
    if len(allowlist) != len(set(allowlist)) or set(allowlist) != set(files):
        raise ValueError('Complete allowlist mismatch')

def prepare(base, archive_path, expected_zip):
    if digest(archive_path.read_bytes()) != expected_zip:
        raise ValueError('ZIP hash mismatch')
    files = {}
    for path in base.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlinks are excluded')
        if path.is_file():
            name = path.relative_to(base).as_posix()
            relative(name)
            files[name] = path.read_bytes()
    verify_tree(files, BASE_MANIFEST)
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive member')
        for name in names:
            relative(name)
        metadata = json.loads(archive.read('DELTA.json'))
        if metadata['schema'] != 'f722-source-delta/v1' or metadata['base_manifest_sha256'] != BASE_MANIFEST:
            raise ValueError('Wrong source delta/base')
        if metadata['base_allowlist_sha256'] != digest(files['PUBLIC_SOURCE_ALLOWLIST.json']):
            raise ValueError('Base allowlist hash mismatch')
        changed = metadata['changed_files_sha256']
        if set(names) != {'DELTA.json'} | {'changed/' + name for name in changed}:
            raise ValueError('Unexpected archive member')
        deleted = metadata['deleted_files']
        if len(deleted) != len(set(deleted)) or set(changed) & set(deleted):
            raise ValueError('Invalid deletion list')
        for name, wanted in changed.items():
            relative(name)
            data = archive.read('changed/' + name)
            if digest(data) != wanted:
                raise ValueError('Changed file hash mismatch')
            files[name] = data
        for name in deleted:
            relative(name)
            del files[name]
        verify_tree(files, metadata['new_manifest_sha256'])
        if digest(files['PUBLIC_SOURCE_ALLOWLIST.json']) != metadata['new_allowlist_sha256']:
            raise ValueError('New allowlist hash mismatch')
        if len(files) != metadata['full_file_count']:
            raise ValueError('New file count mismatch')
    return files, metadata

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--delta', type=Path, required=True)
    parser.add_argument('--zip-sha256', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('Output must not already exist')
    files, metadata = prepare(args.base, args.delta, args.zip_sha256)
    args.out.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        target = args.out / relative(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
    print(json.dumps({'passed': True, 'files': len(files), 'new_manifest_sha256': metadata['new_manifest_sha256']}))

if __name__ == '__main__':
    main()
