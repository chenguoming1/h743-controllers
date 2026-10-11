#!/usr/bin/env python3
"""Freeze a sealed successor allowlist and verify a bounded byte-only restore."""
import fcntl
import hashlib
import importlib.util
import json
import lzma
import os
from pathlib import Path
import resource
import shutil
import signal
import tarfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PREP = ROOT / 'recovery-v5-checkpoint-prep-20261011'
PREDECESSOR = ROOT / 'publication-frozen-corrected-routing-v2-20261011'
PREFIX = 'f722-heli/layout-revision/checkpoints/negotiated-v5-20261011/'
PACKAGE = HERE / 'payload' / PREFIX


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def copy_checked(source, destination, digest, size):
    assert source.is_file() and source.resolve() == source
    destination.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with source.open('rb') as src, destination.open('xb') as dst:
        for chunk in iter(lambda: src.read(1024 * 1024), b''):
            h.update(chunk)
            dst.write(chunk)
    assert h.hexdigest() == digest and destination.stat().st_size == size, ('Source changed', str(source))


def main():
    assert not PACKAGE.exists() and not (HERE / 'HEAVY-TERMINAL.json').exists()
    seal = json.loads((PREP / 'PREPARATION-SEAL.json').read_text())
    assert seal['status'] == 'SEALED_LOCAL_PLAN_READY_FOR_BYTE_FREEZE'
    for name, row in seal['files'].items():
        assert sha(PREP / name) == row['sha256'] and (PREP / name).stat().st_size == row['bytes']
    assert sha(PREDECESSOR / 'manifest.json') == 'bdecb40f7471f90ac9a59f22bc9d8c213ee90651127d3815b89b7babb06de905'
    lock = open(ROOT / 'owner-heavy-lane.lock', 'a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    started = time.monotonic()
    result = {'schema': 'f722-successor-byte-package-terminal/v1', 'passed': False, 'stage': 'freeze',
        'maximum_seconds': 60, 'maximum_address_space_bytes': 1073741824, 'one_CPU_affinity': True,
        'native_geometry_router_execution': False, 'external_writes': False}
    def alarm(*_):
        raise TimeoutError('60-second byte package grant expired')
    signal.signal(signal.SIGALRM, alarm)
    signal.alarm(60)
    resource.setrlimit(resource.RLIMIT_AS, (1073741824, 1073741824))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    try:
        allow = json.loads((PREP / 'source-allowlist.json').read_text())
        entries = allow['source_entries']
        assert len(entries) == seal['source_paths']
        PACKAGE.mkdir(parents=True)
        frozen = HERE / 'frozen-objects'
        frozen.mkdir()
        fixture = HERE / 'predecessor-fixture/restored'
        repository = HERE / 'predecessor-fixture/repository'
        repository.mkdir(parents=True)
        representatives, targets = {}, {}
        for row in entries:
            representatives.setdefault(row['sha256'], row)
            targets[row['path']] = row['sha256']
        objects, fixture_rows = {}, []
        for digest, row in sorted(representatives.items()):
            obj = {'bytes': row['bytes'], 'git_blob_sha': row['git_blob_sha']}
            if row['storage'] == 'capture_unique_successor_object':
                obj['storage'] = 'archive'
                source = ROOT / row['path']
                destination = frozen / digest
            elif row['storage'] == 'reuse_frozen_corrected_v2_object':
                obj['storage'] = 'published'
                alias = row['source']['restore_alias']
                obj['published_source'] = {'kind': 'published_recovery_member', 'restore_path': alias,
                    'git_blob_sha': row['git_blob_sha'], 'frozen_checkpoint_source': row['source']}
                source = PREDECESSOR / 'cold-restored' / alias
                destination = fixture / alias
                fixture_rows.append({'sha256': digest, 'bytes': row['bytes'], 'restore_alias': alias,
                    'source': 'independently verified corrected-v2 cold restore', 'git_blob_sha': row['git_blob_sha']})
            else:
                raise ValueError('Unexpected storage class: ' + row['storage'])
            copy_checked(source, destination, digest, row['bytes'])
            objects[digest] = obj
        for row in entries:
            assert sha(ROOT / row['path']) == row['sha256'] and (ROOT / row['path']).stat().st_size == row['bytes']
        write(PACKAGE / 'reconstruction-map.json', {'schema': 'f722-corrected-routing-recovery-map/v2',
            'original_workspace_root': str(ROOT), 'objects': objects, 'restore_files': dict(sorted(targets.items())),
            'local_frozen_predecessor': allow['frozen_local_predecessor'],
            'source_allowlist_sha256': sha(PREP / 'source-allowlist.json'),
            'status': 'WIP_V5_FAILED_JAVA_HEAP_OOM_NO_FINAL_EXPORT',
            'accepted_board': 'native7', 'native_acceptance': False, 'numerical_power': 'STALE',
            'generated_and_official_dependencies': 'regeneration-map.json',
            'publication_dependency': 'Corrected-v2 remains a frozen local predecessor; this delta has no external publication authorization.'})
        write(PACKAGE / 'PREDECESSOR-FIXTURE.json', {'schema': 'f722-successor-byte-fixture/v1', 'objects': fixture_rows,
            'corrected_v2_manifest_sha256': 'bdecb40f7471f90ac9a59f22bc9d8c213ee90651127d3815b89b7babb06de905',
            'source_is_previously_verified_cold_restore': True, 'remote_availability_asserted': False})
        for name in seal['files']:
            shutil.copyfile(PREP / name, PACKAGE / name)
        shutil.copyfile(PREP / 'PREPARATION-SEAL.json', PACKAGE / 'PREPARATION-SEAL.json')
        shutil.copyfile(HERE / 'restore.py', PACKAGE / 'restore.py')
        capture = sorted(h for h, row in objects.items() if row['storage'] == 'archive')
        result['stage'] = 'compress'
        archive = HERE / 'recovery-objects.tar.xz'
        with archive.open('xb') as stream:
            with lzma.LZMAFile(stream, 'w', format=lzma.FORMAT_XZ, check=lzma.CHECK_CRC64, preset=0) as compressed:
                with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.USTAR_FORMAT) as tar:
                    for digest in capture:
                        item = tarfile.TarInfo('objects/' + digest)
                        item.size = objects[digest]['bytes']
                        item.mtime = item.uid = item.gid = 0
                        item.mode = 0o644
                        item.uname = item.gname = ''
                        with (frozen / digest).open('rb') as source:
                            tar.addfile(item, source)
        archive_row = {'bytes': archive.stat().st_size, 'sha256': sha(archive)}
        parts = []
        with archive.open('rb') as stream:
            index = 0
            while True:
                data = stream.read(8 * 1024 * 1024)
                if not data:
                    break
                index += 1
                name = 'recovery-objects.tar.xz.part' + str(index).zfill(3)
                (PACKAGE / name).write_bytes(data)
                parts.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        write(PACKAGE / 'archive-index.json', {'schema': 'f722-successor-recovery-archive-index/v1',
            'archive': archive_row, 'parts': parts, 'reconstruction_map': {'path': 'reconstruction-map.json',
                'bytes': (PACKAGE / 'reconstruction-map.json').stat().st_size, 'sha256': sha(PACKAGE / 'reconstruction-map.json')},
            'format': 'Sorted SHA256 USTAR; uid/gid/mtime zero; mode 0644; XZ CRC64 preset0 one thread',
            'maximum_binary_part_bytes': 8388608, 'connector_request_limit_bytes': 16777216,
            'request_metadata_reserve_bytes': 1048576})
        result['stage'] = 'cold-byte-restore'
        spec = importlib.util.spec_from_file_location('byte_only_restore', HERE / 'restore.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        restored = module.restore(PACKAGE, repository, fixture, HERE / 'cold-restored')
        assert restored['files'] == len(entries) and restored['archive_members_stream_verified'] == len(capture)
        try:
            module.restore(PACKAGE, repository, fixture, HERE / 'cold-restored')
        except ValueError as e:
            assert str(e) == 'Output must be absent'
        else:
            raise AssertionError('Existing output not rejected')
        restored['existing_output_rejected_before_write'] = True
        restored['reused_corrected_v2_objects'] = len(fixture_rows)
        write(PACKAGE / 'RESTORE-VERIFICATION.json', restored)
        write(PACKAGE / 'VERIFY-ARCHIVE.json', {'schema': 'f722-successor-byte-archive-verification/v1',
            'archive': archive_row, 'archive_unique_objects': len(capture),
            'archive_uncompressed_bytes': sum(objects[h]['bytes'] for h in capture),
            'all_members_stream_verified': True, 'exact_parts_reassembly_verified': True,
            'deterministic_order_and_metadata_verified': True, 'restored_paths': len(entries),
            'restored_unique_objects': len(objects), 'all_size_sha256_git_blob_checks_passed': True,
            'restore_verification_sha256': sha(PACKAGE / 'RESTORE-VERIFICATION.json'),
            'native_geometry_router_execution': False, 'external_writes': False})
        result.update(passed=True, stage='complete', archive=archive_row, archive_unique_objects=len(capture),
                      parts=len(parts), restored_paths=len(entries), unique_objects=len(objects))
    except Exception as e:
        result['error'] = repr(e)
    finally:
        signal.alarm(0)
        result['elapsed_seconds'] = time.monotonic() - started
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()
        result['heavy_lane_released'] = True
        write(HERE / 'HEAVY-TERMINAL.json', result)
        print(json.dumps(result, indent=2), flush=True)
    return 0 if result['passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
