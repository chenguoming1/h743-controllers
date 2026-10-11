#!/usr/bin/env python3
"""Bounded, exclusive byte-only package build; no engineering code is imported."""
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
PREP = ROOT / 'recovery-negotiated-checkpoint-prep-20261011'
PREFIX = 'f722-heli/layout-revision/checkpoints/negotiated-routing-v1-20261011/'
PACKAGE = HERE / 'payload' / PREFIX
PRIOR = ROOT / 'publication-frozen-paired-hub-recovery-20261011'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def copy_checked(source, target, digest, size):
    assert source.is_file() and source.resolve() == source
    target.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with source.open('rb') as src, target.open('xb') as dst:
        for chunk in iter(lambda: src.read(1024 * 1024), b''):
            dst.write(chunk)
            h.update(chunk)
    assert target.stat().st_size == size and h.hexdigest() == digest, ('changed source', str(source))


def main():
    assert not PACKAGE.exists() and not (HERE / 'HEAVY-TERMINAL.json').exists()
    lock = open(ROOT / 'owner-heavy-lane.lock', 'a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    started = time.monotonic()
    state = {'schema': 'f722-byte-package-heavy-terminal/v1', 'passed': False,
             'maximum_seconds': 60, 'maximum_address_space_bytes': 1073741824,
             'one_CPU_affinity': True, 'geometry_native_router_execution': False,
             'external_writes': False, 'stage': 'freeze'}
    def alarm(*_):
        raise TimeoutError('60-second package grant expired')
    signal.signal(signal.SIGALRM, alarm)
    signal.alarm(60)
    resource.setrlimit(resource.RLIMIT_AS, (1073741824, 1073741824))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    try:
        raw = (PREP / 'source-allowlist.json').read_bytes()
        allow = json.loads(raw)
        assert len(allow['source_entries']) == 286
        assert len(allow['unique_objects']) == 250
        terminal_path = ROOT / 'recovery-negotiated-routing-20261011/negotiated-v1/run/execution-receipt.json'
        terminal = json.loads(terminal_path.read_text())
        assert terminal['passed'] is False and terminal['source_files_unchanged'] and terminal['lane_released']
        for version, digest in [('v1', 'ae73ac797612fcce8ad89fa6900eee3e6b87c3daee5b93391fed9cc49a30a08f'),
                                ('v2', '70eb9d8bbda826c507109d9b9de6d6cab3984c359e64c0a69a83399fc6b45771')]:
            folder = ROOT / ('recovered-native7/recovery-importer/current-negotiated-import-' + version)
            assert sha(folder / 'PREPARATION-SEAL.json') == digest
            for name, row in json.loads((folder / 'PREPARATION-SEAL.json').read_text())['files'].items():
                assert (folder / name).stat().st_size == row['bytes'] and sha(folder / name) == row['sha256']
        PACKAGE.mkdir(parents=True)
        frozen = HERE / 'frozen-objects'
        frozen.mkdir()
        repository = HERE / 'predecessor-fixture/repository'
        predecessor = HERE / 'predecessor-fixture/restored'
        bysha = {}
        targets = {}
        for row in allow['source_entries']:
            assert '/negotiated-v2/' not in row['path']
            targets[row['path']] = row['sha256']
            bysha.setdefault(row['sha256'], row)
        objects, fixture_rows = {}, []
        for digest, row in sorted(bysha.items()):
            size = row['bytes']
            obj = {'bytes': size, 'git_blob_sha': row['git_blob_sha']}
            if row['storage'] == 'capture_unique_new_bytes_once':
                obj['storage'] = 'archive'
                destination = frozen / digest
            elif row['storage'] == 'reuse_repository_blob':
                obj['storage'] = 'published'
                obj['published_source'] = dict(row['published_source'], kind='repository_blob')
                destination = repository / row['published_source']['repository_path']
            else:
                assert row['storage'] == 'reuse_predecessor_recovery_object'
                obj['storage'] = 'published'
                obj['published_source'] = {'kind': 'published_recovery_member',
                    'restore_path': row['published_source']['known_restore_alias'],
                    'git_blob_sha': row['git_blob_sha'], 'predecessor_provenance': row['published_source']}
                destination = predecessor / row['published_source']['known_restore_alias']
            copy_checked(ROOT / row['path'], destination, digest, size)
            if obj['storage'] == 'published':
                fixture_rows.append({'sha256': digest, 'bytes': size, 'git_blob_sha': row['git_blob_sha'],
                    'local_source': row['path'], 'published_source': obj['published_source']})
            objects[digest] = obj
        # Recheck all aliases as well as the content representatives frozen above.
        for row in allow['source_entries']:
            assert (ROOT / row['path']).stat().st_size == row['bytes'] and sha(ROOT / row['path']) == row['sha256']
        write(PACKAGE / 'reconstruction-map.json', {
            'schema': 'f722-negotiated-v1-recovery-map/v1', 'original_workspace_root': str(ROOT),
            'objects': objects, 'restore_files': dict(sorted(targets.items())),
            'predecessor': allow['remote_predecessor'],
            'generated_and_official_dependencies': 'regeneration-map.json',
            'source_allowlist_sha256': hashlib.sha256(raw).hexdigest(),
            'status': 'WIP_FAILED_TRIAL_NO_ROUTING_REDUCTION', 'accepted_or_adopted': False,
            'accepted_board': 'native7', 'numerical_power_status': 'STALE',
            'limitations': ['Restores source/control/evidence bytes only. Generated models and official artifacts require their separate hash-checked recipes.',
                'No successor diagnostic is included. No engineering replay or native qualification was performed by packaging.']})
        write(PACKAGE / 'PREDECESSOR-FIXTURE.json', {'schema': 'f722-published-byte-fixture/v1',
             'authority': 'Exact local bytes checked against the complete owner-verified predecessor tree and published recovery map; not a fresh network checkout.',
             'objects': fixture_rows, 'predecessor_tree': allow['remote_predecessor']['tree'],
             'remote_head_independently_checked_by_packager': False})
        for name in ['source-allowlist.json', 'regeneration-map.json', 'evidence-status.json', 'preparation-verification.json', 'import-seal-verification.json']:
            shutil.copyfile(PREP / name, PACKAGE / name)
        shutil.copyfile(HERE / 'restore.py', PACKAGE / 'restore.py')
        captured = sorted(h for h, row in objects.items() if row['storage'] == 'archive')
        assert len(captured) == 158 and captured.count('0c717e78d2819daf2cf14d6773efc680fc78d436bc42e2638ce931064bc549b8') == 1
        state['stage'] = 'compress'
        archive = HERE / 'recovery-objects.tar.xz'
        with archive.open('xb') as rawfile:
            with lzma.LZMAFile(rawfile, 'w', format=lzma.FORMAT_XZ, check=lzma.CHECK_CRC64, preset=0) as compressed:
                with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.USTAR_FORMAT) as tar:
                    for digest in captured:
                        item = tarfile.TarInfo('objects/' + digest)
                        item.size = objects[digest]['bytes']
                        item.mtime = item.uid = item.gid = 0
                        item.mode = 0o644
                        item.uname = item.gname = ''
                        with (frozen / digest).open('rb') as stream:
                            tar.addfile(item, stream)
        archive_row = {'bytes': archive.stat().st_size, 'sha256': sha(archive)}
        parts = []
        with archive.open('rb') as stream:
            index = 0
            while True:
                chunk = stream.read(8 * 1024 * 1024)
                if not chunk:
                    break
                index += 1
                name = 'recovery-objects.tar.xz.part' + str(index).zfill(3)
                (PACKAGE / name).write_bytes(chunk)
                parts.append({'path': name, 'bytes': len(chunk), 'sha256': hashlib.sha256(chunk).hexdigest()})
        write(PACKAGE / 'archive-index.json', {'schema': 'f722-negotiated-recovery-archive-index/v1',
            'archive': archive_row, 'parts': parts,
            'reconstruction_map': {'path': 'reconstruction-map.json', 'bytes': (PACKAGE / 'reconstruction-map.json').stat().st_size,
                                   'sha256': sha(PACKAGE / 'reconstruction-map.json')},
            'format': 'Sorted SHA256 USTAR objects; uid/gid/mtime zero; mode 0644; XZ CRC64 preset 0, one thread',
            'maximum_binary_part_bytes': 8 * 1024 * 1024, 'connector_request_limit_bytes': 16 * 1024 * 1024,
            'request_metadata_reserve_bytes': 1024 * 1024, 'archive_contains_only_unique_new_content': True})
        state['stage'] = 'cold-byte-restore'
        spec = importlib.util.spec_from_file_location('byte_only_restore', HERE / 'restore.py')
        restore = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(restore)
        result = restore.restore(PACKAGE, repository, predecessor, HERE / 'cold-restored')
        assert result['files'] == 286 and result['archive_members_stream_verified'] == 158
        try:
            restore.restore(PACKAGE, repository, predecessor, HERE / 'cold-restored')
        except ValueError as e:
            assert str(e) == 'Output must be absent'
        else:
            raise AssertionError('Existing output was not rejected')
        result['existing_output_rejected_before_write'] = True
        result['predecessor_fixture_verified_objects'] = len(fixture_rows)
        result['unique_native_payload_count'] = 1
        result['paired_hardware_files'] = 61
        write(PACKAGE / 'RESTORE-VERIFICATION.json', result)
        write(PACKAGE / 'VERIFY-ARCHIVE.json', {'schema': 'f722-byte-only-archive-verification/v1',
            'archive': archive_row, 'archive_unique_objects': len(captured),
            'archive_uncompressed_content_bytes': sum(objects[h]['bytes'] for h in captured),
            'all_members_stream_verified': True, 'exact_parts_reassembly_verified': True,
            'deterministic_member_order_and_metadata_verified': True,
            'restored_paths': result['files'], 'restored_unique_objects': len(objects),
            'restored_files_sha256_size_and_git_blob_verified': True,
            'restore_verification_sha256': sha(PACKAGE / 'RESTORE-VERIFICATION.json'),
            'original_native_member_count': 1, 'compression_preset': 0,
            'native_geometry_router_execution': False, 'external_writes': False})
        state.update(passed=True, stage='complete', archive=archive_row, parts=len(parts), restored_paths=286)
    except Exception as e:
        state['error'] = repr(e)
    finally:
        signal.alarm(0)
        state['elapsed_seconds'] = time.monotonic() - started
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()
        state['heavy_lane_released'] = True
        write(HERE / 'HEAVY-TERMINAL.json', state)
        print(json.dumps(state, indent=2), flush=True)
    return 0 if state['passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
