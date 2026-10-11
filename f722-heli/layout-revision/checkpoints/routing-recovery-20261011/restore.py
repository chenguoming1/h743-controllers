#!/usr/bin/env python3
"""Restore exact recovery inputs from checked repository blobs and archive chunks.

This standard-library tool never imports recovered code, runs KiCad, or starts a solver.
"""
import argparse
import hashlib
import json
import lzma
from pathlib import Path
import subprocess
import tarfile
import tempfile
import zlib


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def verify(data, row):
    if len(data) != row['bytes'] or digest(data) != row['sha256'] or git_blob(data) != row['git_blob_sha']:
        raise ValueError('Exact byte/hash verification failed: '+row.get('restore_path',row.get('path','object')))
    if 'crc32' in row and f'{zlib.crc32(data):08x}' != row['crc32']:
        raise ValueError('CRC32 verification failed')


def safe_relative(value):
    p=Path(value)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        raise ValueError('Unsafe relative path')
    return p


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout',type=Path,required=True,help='Base/final repository checkout or matching base file tree')
    parser.add_argument('--output',type=Path,required=True,help='New empty recovery directory')
    args=parser.parse_args()
    package=Path(__file__).resolve().parent
    raw_inventory=(package/'recovery-inventory.json').read_bytes()
    inventory=json.loads(raw_inventory)
    index=json.loads((package/'archive-index.json').read_bytes())
    if digest(raw_inventory) != index['source_scope_sha256']:
        raise ValueError('Inventory binding does not match archive')
    output=args.output.resolve()
    if output.exists():
        raise ValueError('Output must be a new directory; refusing to overwrite files')
    output.parent.mkdir(parents=True,exist_ok=True)
    wanted={r['sha256']:r for r in inventory['files'] if r['storage']=='archive'}
    with tempfile.TemporaryDirectory(prefix='f722-recovery-',dir=output.parent) as tmp:
        tmp=Path(tmp)
        archive=tmp/'objects.tar.xz'
        h=hashlib.sha256();length=0
        with archive.open('wb') as out:
            for chunk in index['chunks']:
                data=(package/safe_relative(chunk['path'])).read_bytes()
                verify(data,chunk)
                if len(data)>index['max_raw_chunk_bytes']:raise ValueError('Chunk exceeds declared transport bound')
                out.write(data);h.update(data);length+=len(data)
        if h.hexdigest()!=index['archive_sha256'] or length!=index['archive_bytes']:
            raise ValueError('Reassembled archive mismatch')
        found=set()
        with lzma.open(archive,'rb') as xz:
            with tarfile.open(fileobj=xz,mode='r|') as tf:
                for member in tf:
                    key=member.name.removeprefix('objects/')
                    if not member.isfile() or member.name!='objects/'+key or key not in wanted or key in found:
                        raise ValueError('Unexpected archive member: '+member.name)
                    data=tf.extractfile(member).read()
                    verify(data,wanted[key]);(tmp/key).write_bytes(data);found.add(key)
            while xz.read(1024*1024):pass  # Consume EOF and verify XZ CRC64.
        if found!=set(wanted):raise ValueError('Missing archive objects')
        output.mkdir()
        base_count=0
        for row in inventory['files']:
            if row['storage']=='archive':data=(tmp/row['sha256']).read_bytes()
            else:
                data=None
                for path in row['base_repository_paths']:
                    candidate=args.checkout/safe_relative(path)
                    if candidate.is_file():
                        raw=candidate.read_bytes()
                        if git_blob(raw)==row['git_blob_sha']:data=raw;break
                if data is None:
                    result=subprocess.run(['git','-C',str(args.checkout),'cat-file','blob',row['git_blob_sha']],capture_output=True)
                    if result.returncode:raise ValueError('Required base blob unavailable: '+row['git_blob_sha'])
                    data=result.stdout
                base_count+=1
            verify(data,row)
            dest=output/safe_relative(row['restore_path'])
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        for row in inventory['files']:verify((output/row['restore_path']).read_bytes(),row)
        zip_checks=0
        for row in inventory['original_official_zip']['members']:
            verify((output/row['restore_path']).read_bytes(),row);zip_checks+=1
    report={'schema':'f722-routing-recovery-restore-result/v1','restored_paths':len(inventory['files']),
            'reused_base_paths':base_count,'archive_unique_objects':len(wanted),'archive_sha256':index['archive_sha256'],
            'all_size_sha256_git_blob_crc32_checks_passed':True,'xz_crc64_verified':True,
            'original_zip_member_crc32_checks':zip_checks,'original_zip_container_reproduced':False,
            'native_router_solver_or_recovered_code_executed':False}
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
