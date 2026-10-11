#!/usr/bin/env python3
"""Deterministic byte-only recovery packaging; never imports engineering code."""
import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path
import shutil
import tarfile

HERE = Path(__file__).resolve().parent
BINDER = HERE.parent
ROOT = BINDER.parents[2]
ALLOW = BINDER / 'recovery-file-allowlist.json'
FLASH = 'recovered-native7/recovery-flash/'
ROUTING = {
    FLASH + 'native7-R32-translation-checkpoint-01-v12.json': 'da3f7897960e746402d59731d36ef0619921b73a11e6553fdf61ed92eb181a0f',
    FLASH + 'native7-R32-translation-complete-contract-v12.json': '6c7aed71ef07fa9475dbcbb6b52bee19e6df5e9d21fe6245fbd0ae31632fc111',
    FLASH + 'native7-R32-translation-complete-result-v12.json': '85c937b0219dd08ff893dbbaba42d6077287b325f99cdb27ff9a8208e460d91f',
}
NATIVE_SHA = 'ef924ac03c069313072650357ca094dc71c5919f218d3c8904d87cbe46ae3e83'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def run(binder_names):
    allow = json.loads(ALLOW.read_text())
    tree_path = allow['publication_evidence']['tree_inventory']
    tree = json.loads((ROOT / tree_path).read_text())
    bygit = {}
    for path, row in tree['records'].items():
        bygit.setdefault(row['sha'], []).append(path)
    bysha = {}
    for invpath in allow['publication_evidence']['inventory_sources']:
        for row in json.loads((ROOT / invpath).read_text())['files']:
            if row.get('storage') in ('archive', 'overlay'):
                bysha.setdefault(row['sha256'], {'kind': 'published_recovery_member',
                    'inventory': invpath, 'restore_path': row['restore_path'],
                    'storage': row['storage'], 'git_blob_sha': row['git_blob_sha']})
    objects, sources = {}, {}
    targets = dict(allow['explicit_restore_files'])
    for group in allow['hardware_sets']:
        for root in group['restore_directories']:
            for name, digest in group['files'].items():
                targets[root + '/' + name] = digest

    def add(path, expected=None, published=None):
        p = ROOT / path
        assert p.resolve() == p and p.is_file(), path
        data = p.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        assert expected is None or digest == expected, ('Source changed', path)
        targets[path] = digest
        if digest not in objects:
            blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if published is None:
                refs = bygit.get(blob, [])
                published = ({'kind': 'repository_blob', 'repository_path': refs[0],
                    'git_blob_sha': blob, 'tree_inventory': tree_path} if refs else bysha.get(digest))
            objects[digest] = {'bytes': len(data), 'storage': 'published' if published else 'archive'}
            if published:
                assert published['git_blob_sha'] == blob
                objects[digest]['published_source'] = published
            sources[digest] = p
        return digest

    for digest, row in (allow['capture_once'] | allow['reuse_published']).items():
        add(row['local_source_path'], digest, row.get('published_source'))
    add(str(ALLOW.relative_to(ROOT)))
    for name in binder_names:
        assert Path(name).name == name and (BINDER / name).is_file(), name
        add(str((BINDER / name).relative_to(ROOT)))
    for path, digest in ROUTING.items():
        add(path, digest)
    contract = json.loads((ROOT / (FLASH + 'native7-R32-translation-complete-contract-v12.json')).read_text())
    assert len(contract['source_files']) == 319
    for row in contract['source_files']:
        add(row['path'], row['sha256'])
    checkpoint = json.loads((ROOT / (FLASH + 'native7-R32-translation-checkpoint-01-v12.json')).read_text())
    assert checkpoint['complete_planning_witness'] is False
    assert checkpoint['full_physical_snapshot_sha256'] == '44b04c614326c4b8457169999774897bf926b72e19d5055160fcf9edba635a62'
    assert set(targets.values()) <= set(objects)
    # Prove every alias currently resolves to exactly its recorded content.
    for path, digest in targets.items():
        assert sha(ROOT / path) == digest, ('Alias changed', path)
    mapping = {'schema': 'f722-current-pair-plus-v12-recovery-map/v1',
        'original_workspace_root': str(ROOT),
        'objects': dict(sorted(objects.items())), 'restore_files': dict(sorted(targets.items())),
        'paired_base': allow['verified_milestone'],
        'routing_milestone': {'source_paths_and_sha256': ROUTING,
            'physical_snapshot_sha256': checkpoint['full_physical_snapshot_sha256'],
            'complete_planning_witness': False, 'accepted_or_adopted': False,
            'scope': 'Verified partial planning entry: actual ABC_PG U6.2 source entry through In3 to a new barrel at the retired FLASH_CS site. All 13 repair demands remain reachable; FLASH_CS has three separate groups awaiting physical reconstruction. Restricted ABC continuation failed, and full joint routing remains incomplete.',
            'source_contract_entries': len(contract['source_files'])},
        'published_evidence': allow['publication_evidence'],
        'limitations': allow['restore_and_verification_notes'] + [
            'Later v12 checkpoint/contract/result and its 319 exact source dependencies are added by this map. Historical diagnostic files enter only if explicitly pinned by that contract.',
            'Byte restoration is relocatable; frozen engineering verifiers may retain absolute-path prerequisites. No restored script is executed by restoration.',
            'Unchanged canonical guard and full official KiCad runtime remain the supervisor prerequisites described in the included allowlist.']}
    map_path = HERE / 'reconstruction-map.json'
    write(map_path, mapping)
    captured = sorted(h for h, row in objects.items() if row['storage'] == 'archive')
    archive = HERE / 'recovery-objects.tar.xz'
    with archive.open('xb') as raw:
        with lzma.LZMAFile(raw, 'w', format=lzma.FORMAT_XZ, check=lzma.CHECK_CRC64, preset=6) as compressed:
            with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.USTAR_FORMAT) as tar:
                for digest in captured:
                    row = objects[digest]
                    info = tarfile.TarInfo('objects/' + digest)
                    info.size = row['bytes']; info.mtime = 0; info.mode = 0o644
                    info.uid = info.gid = 0; info.uname = info.gname = ''
                    with sources[digest].open('rb') as stream:
                        tar.addfile(info, stream)
    archive_row = {'bytes': archive.stat().st_size, 'sha256': sha(archive)}
    seen = []
    with lzma.open(archive, 'rb') as compressed:
        with tarfile.open(fileobj=compressed, mode='r|') as tar:
            for member in tar:
                assert member.isfile() and member.mtime == 0 and member.uid == member.gid == 0
                digest = member.name.removeprefix('objects/')
                assert member.name == 'objects/' + digest and digest in captured and digest not in seen
                assert member.size == objects[digest]['bytes']
                h = hashlib.sha256(); size = 0
                with tar.extractfile(member) as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        h.update(chunk); size += len(chunk)
                assert h.hexdigest() == digest and size == member.size
                seen.append(digest)
    assert seen == captured and NATIVE_SHA in seen
    # Reserve one MiB for request JSON/metadata; account for base64 expansion.
    request_cap = 16 * 1024 * 1024
    estimated = 4 * ((archive_row['bytes'] + 2) // 3) + 1024 * 1024
    parts = []
    if estimated > request_cap:
        with archive.open('rb') as stream:
            number = 1
            while True:
                data = stream.read(8 * 1024 * 1024)
                if not data:
                    break
                name = 'recovery-objects.tar.xz.part' + str(number).zfill(3)
                with (HERE / name).open('xb') as dst:
                    dst.write(data)
                parts.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
                number += 1
    else:
        parts = [dict(archive_row, path=archive.name)]
    h = hashlib.sha256(); size = 0
    for part in parts:
        with (HERE / part['path']).open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(chunk); size += len(chunk)
    assert h.hexdigest() == archive_row['sha256'] and size == archive_row['bytes']
    if len(parts) > 1:
        archive.unlink()  # Only the just-created duplicate full archive; deliver its verified parts.
    index = {'schema': 'f722-current-recovery-archive-index/v1', 'archive': archive_row,
        'parts': parts, 'reconstruction_map': {'path': map_path.name, 'bytes': map_path.stat().st_size, 'sha256': sha(map_path)},
        'format': 'USTAR, sorted SHA256 object members, uid/gid/mtime zero, mode 0644; XZ CRC64 preset 6',
        'archive_contains_only_unique_new_content': True,
        'connector_request_limit_bytes': request_cap, 'request_metadata_reserve_bytes': 1024 * 1024,
        'maximum_binary_part_bytes_when_split': 8 * 1024 * 1024}
    write(HERE / 'archive-index.json', index)
    verification = {'schema': 'f722-byte-only-archive-verification/v1',
        'archive_and_every_member_sha256_verified': True, 'archive_member_order_and_metadata_verified': True,
        'archive_unique_objects': len(captured), 'archive_uncompressed_content_bytes': sum(objects[h]['bytes'] for h in captured),
        'published_objects': len(objects) - len(captured), 'restore_file_paths': len(targets),
        'all_restore_source_paths_rehashed': True, 'exact_part_reassembly_sha256': archive_row['sha256'],
        'original_native_sha256': NATIVE_SHA, 'original_native_bytes': objects[NATIVE_SHA]['bytes'],
        'original_native_member_count': seen.count(NATIVE_SHA), 'binder_files': binder_names,
        'routing_contract_sources_verified': 319, 'complete_planning_witness': False,
        'native_geometry_solver_execution': False, 'external_writes': False,
        'cold_byte_restore_pending': True}
    write(HERE / 'VERIFY-ARCHIVE.json', verification)
    print(json.dumps({'archive': archive_row, 'parts': parts, 'verification': verification}, sort_keys=True, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sealed-binder-files', nargs='+', required=True)
    args = ap.parse_args()
    run(args.sealed_binder_files)
