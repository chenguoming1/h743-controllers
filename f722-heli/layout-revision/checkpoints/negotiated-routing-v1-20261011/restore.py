#!/usr/bin/env python3
"""Restore exact recovery bytes from the package and published predecessors only."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile


def require(value, message):
    if not value:
        raise ValueError(message)


def safe_relative(value):
    p = PurePosixPath(value)
    require(isinstance(value, str) and value and p.parts and not p.is_absolute()
            and '..' not in p.parts and str(p) == value and '\\' not in value,
            'Unsafe relative path: ' + repr(value))
    return Path(*p.parts)


def file_hash(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def check_file(path, row):
    require(path.is_file() and path.resolve() == path, 'Missing or symlink source: ' + str(path))
    require(path.stat().st_size == row['bytes'] and file_hash(path) == row['sha256'],
            'Content mismatch: ' + str(path))


def restore(package, repository, predecessor, output):
    package, repository, predecessor, output = [p.resolve() for p in
                                               [package, repository, predecessor, output]]
    require(not output.exists(), 'Output must be absent')
    index = json.loads((package / 'archive-index.json').read_text())
    map_path = package / 'reconstruction-map.json'
    check_file(map_path, index['reconstruction_map'])
    manifest = json.loads(map_path.read_text())
    expected = manifest['objects']
    require(set(manifest['restore_files'].values()) <= set(expected), 'Missing content object')
    for p in manifest['restore_files']:
        safe_relative(p)
    # Work only in a newly created temporary directory. Never extract tar paths.
    with tempfile.TemporaryDirectory(prefix='f722-recovery-') as scratch:
        scratch = Path(scratch)
        archive = scratch / 'reassembled.tar.xz'
        with archive.open('xb') as dst:
            for part in index['parts']:
                source = package / safe_relative(part['path'])
                check_file(source, part)
                with source.open('rb') as src:
                    shutil.copyfileobj(src, dst)
        check_file(archive, index['archive'])
        objects = {}
        member_order = []
        with lzma.open(archive, 'rb') as compressed:
            with tarfile.open(fileobj=compressed, mode='r|') as tar:
                for member in tar:
                    require(member.isfile() and member.name.startswith('objects/'), 'Non-object tar member')
                    require(member.mtime == 0 and member.uid == member.gid == 0
                            and member.mode == 0o644 and member.uname == member.gname == '',
                            'Non-deterministic archive metadata')
                    digest = member.name.removeprefix('objects/')
                    require(digest in expected and expected[digest]['storage'] == 'archive'
                            and digest not in objects and member.name == 'objects/' + digest,
                            'Unexpected or duplicate object')
                    row = expected[digest]
                    require(member.size == row['bytes'], 'Tar member size mismatch')
                    path = scratch / digest
                    with tar.extractfile(member) as src, path.open('xb') as dst:
                        shutil.copyfileobj(src, dst)
                    check_file(path, dict(row, sha256=digest))
                    objects[digest] = path
                    member_order.append(digest)
        require(set(objects) == {h for h, row in expected.items() if row['storage'] == 'archive'},
                'Archive object set mismatch')
        require(member_order == sorted(member_order), 'Archive member order differs')
        for digest, row in expected.items():
            if row['storage'] == 'archive':
                continue
            source = row['published_source']
            if source['kind'] == 'repository_blob':
                path = repository / safe_relative(source['repository_path'])
            elif source['kind'] == 'published_recovery_member':
                path = predecessor / safe_relative(source['restore_path'])
            else:
                raise ValueError('Unsupported published source kind')
            check_file(path, dict(row, sha256=digest))
            git = hashlib.sha1(b'blob ' + str(row['bytes']).encode() + b'\0')
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    git.update(chunk)
            require(git.hexdigest() == source['git_blob_sha'], 'Published Git object mismatch')
            objects[digest] = path
        output.mkdir(parents=True, exist_ok=False)
        for relative, digest in sorted(manifest['restore_files'].items()):
            path = output / safe_relative(relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            with objects[digest].open('rb') as src, path.open('xb') as dst:
                shutil.copyfileobj(src, dst)
            check_file(path, dict(expected[digest], sha256=digest))
            git = hashlib.sha1(b'blob ' + str(expected[digest]['bytes']).encode() + b'\0')
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    git.update(chunk)
            require(git.hexdigest() == expected[digest]['git_blob_sha'], 'Restored alias Git blob differs')
    return {'schema': 'f722-byte-only-recovery-result/v1', 'files': len(manifest['restore_files']),
            'unique_objects': len(expected), 'all_bytes_and_hashes_verified': True,
            'archive_members_stream_verified': len(member_order),
            'archive_order_and_metadata_verified': True,
            'all_restored_git_blob_hashes_verified': True,
            'part_reassembly_verified': True,
            'native_or_geometry_executed': False, 'output': str(output)}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--package', type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument('--repository', type=Path, required=True)
    ap.add_argument('--published-workspace', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(restore(args.package, args.repository, args.published_workspace, args.output),
                     sort_keys=True, indent=2))
