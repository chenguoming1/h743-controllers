#!/usr/bin/env python3
"""Append and verify this WIP source overlay after the predecessor's cold restore.

Uses only the Python standard library. Never imports restored modules or executes
routing, geometry, KiCad, native-board, or electrical-qualification code.
"""
import argparse
import hashlib
import json
import lzma
from pathlib import Path
import tarfile
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def relative(value):
    p=Path(value)
    if not value or p.is_absolute() or '..' in p.parts or str(p)!=value:
        raise ValueError('Unsafe relative path: '+str(value))
    return p


def safe_path(root,value):
    path=root/relative(value)
    for p in [path,*path.parents]:
        if p==root:break
        if p.is_symlink():raise ValueError('Symlink refused: '+str(p))
    if not path.resolve().is_relative_to(root):raise ValueError('Path escapes root')
    return path


def verify_bytes(data,row):
    if len(data)!=row['bytes'] or digest(data)!=row['sha256'] or git_blob(data)!=row['git_blob_sha']:
        raise ValueError('Byte/hash mismatch: '+row.get('restore_path',row.get('path','object')))


def verify_file(path,row):
    if not path.is_file() or path.is_symlink():raise ValueError('Required regular file unavailable: '+str(path))
    size=path.stat().st_size;h=hashlib.sha256();g=hashlib.sha1(b'blob '+str(size).encode()+b'\0')
    with path.open('rb') as f:
        while data:=f.read(1024*1024):h.update(data);g.update(data)
    if size!=row['bytes'] or h.hexdigest()!=row['sha256'] or g.hexdigest()!=row['git_blob_sha']:
        raise ValueError('Byte/hash mismatch: '+str(path))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True,help='Predecessor restore output; only new files will be added')
    parser.add_argument('--previous-package',type=Path,required=True,help='Published routing-recovery-20261011 package directory')
    args=parser.parse_args();package=Path(__file__).resolve().parent
    raw=(package/'overlay-inventory.json').read_bytes();inventory=json.loads(raw)
    index=json.loads((package/'archive-index.json').read_bytes())
    if digest(raw)!=index['source_inventory_sha256']:raise ValueError('Archive inventory binding mismatch')
    if args.workspace.is_symlink() or args.previous_package.is_symlink():raise ValueError('Root symlink refused')
    workspace=args.workspace.resolve();previous=args.previous_package.resolve()
    if not workspace.is_dir():raise ValueError('Restore predecessor into the workspace first')
    for row in inventory['previous_package_files']:verify_file(safe_path(previous,row['path']),row)
    prior=json.loads((previous/'recovery-inventory.json').read_bytes())
    if len(prior['files'])!=344:raise ValueError('Unexpected predecessor inventory')
    prior_map={r['restore_path']:r for r in prior['files']}
    for row in prior['files']:verify_file(safe_path(workspace,row['restore_path']),row)
    additions=[];reused=[];paths=set()
    for row in inventory['files']:
        path=safe_path(workspace,row['restore_path'])
        if row['restore_path'] in paths:raise ValueError('Duplicate restore path')
        paths.add(row['restore_path'])
        if row['storage']=='previous':
            old=prior_map.get(row['previous_restore_path'])
            if not old or row['previous_restore_path']!=row['restore_path'] or any(old[k]!=row[k] for k in ['bytes','sha256','git_blob_sha']):
                raise ValueError('Invalid predecessor reuse binding')
            verify_file(path,row);reused.append(row)
        elif row['storage']=='overlay':
            if path.exists():raise ValueError('Refusing to overwrite existing path: '+row['restore_path'])
            additions.append(row)
        else:raise ValueError('Unknown storage mode')
    wanted={r['sha256']:r for r in additions}
    if len(wanted)!=len(additions):raise ValueError('Unexpected duplicate overlay object')
    with tempfile.TemporaryDirectory(prefix='f722-west-overlay-',dir=workspace.parent) as tmp:
        tmp=Path(tmp);archive=tmp/'overlay.tar.xz';h=hashlib.sha256();length=0
        with archive.open('wb') as out:
            for row in index['chunks']:
                data=safe_path(package,row['path']).read_bytes();verify_bytes(data,row)
                if len(data)>index['max_raw_chunk_bytes']:raise ValueError('Chunk exceeds transport bound')
                out.write(data);h.update(data);length+=len(data)
        if h.hexdigest()!=index['archive_sha256'] or length!=index['archive_bytes']:raise ValueError('Archive mismatch')
        found=set()
        with lzma.open(archive,'rb') as xz:
            with tarfile.open(fileobj=xz,mode='r|') as tf:
                for member in tf:
                    key=member.name.removeprefix('objects/')
                    if not member.isfile() or member.name!='objects/'+key or key not in wanted or key in found or member.size!=wanted[key]['bytes']:
                        raise ValueError('Unexpected archive member: '+member.name)
                    data=tf.extractfile(member).read();verify_bytes(data,wanted[key]);(tmp/key).write_bytes(data);found.add(key)
            while xz.read(1024*1024):pass
        if found!=set(wanted):raise ValueError('Missing archive objects')
        # All source, destination, archive and checksum checks finish before writes.
        for row in additions:
            target=safe_path(workspace,row['restore_path']);target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as f:f.write((tmp/row['sha256']).read_bytes())
    for row in inventory['files']:verify_file(safe_path(workspace,row['restore_path']),row)
    for row in prior['files']:verify_file(safe_path(workspace,row['restore_path']),row)
    contract=json.loads((workspace/inventory['contract_path']).read_bytes())
    current={r['restore_path']:r for r in inventory['files']}
    for row in contract['source_files']:
        bound=current.get(row['path'])
        if not bound or bound['sha256']!=row['sha256']:raise ValueError('Contract dependency missing or mismatched')
        verify_file(safe_path(workspace,row['path']),bound)
    checkpoint=json.loads((workspace/inventory['checkpoint_path']).read_bytes())
    terminal=json.loads((workspace/inventory['terminal_result_path']).read_bytes())
    contract_sha=current[inventory['contract_path']]['sha256']
    if checkpoint['contract_sha256']!=contract_sha or terminal['contract_sha256']!=contract_sha:raise ValueError('Result contract binding mismatch')
    if checkpoint['full_physical_snapshot_sha256']!='46e7740e81b3a03e7b2f7d9c230b9bb97abd45e4fd85742c25b45452a53a61b5':raise ValueError('Positive snapshot mismatch')
    receipt=json.loads((workspace/inventory['ground_review_receipt_path']).read_bytes())
    if current[receipt['review_path']]['sha256']!=receipt['review_sha256']:raise ValueError('Ground review mismatch')
    for row in receipt['source_bindings']:
        if current[row['path']]['sha256']!=row['sha256']:raise ValueError('Ground-review source mismatch')
    print(json.dumps({'schema':'f722-west-tx-bridge-overlay-restore-result/v1','previous_paths_verified_before_and_after':len(prior['files']),
        'current_scope_paths_verified':len(current),'current_contract_dependencies_verified':len(contract['source_files']),
        'reused_previous_paths':len(reused),'added_paths':len(additions),'combined_workspace_paths':len(prior_map|current),
        'all_size_sha256_git_blob_checks_passed':True,'xz_crc64_verified':True,'ground_review_bindings_verified':True,
        'positive_snapshot_sha256':checkpoint['full_physical_snapshot_sha256'],'positive_checkpoint_complete_guard_passed':checkpoint['complete_guard']['passed'],
        'complete_planning_witness':checkpoint['complete_planning_witness'],'terminal_failure_preserved':terminal['terminal_reason'],
        'native_edited':False,'engineering_code_executed':False},indent=2))


if __name__=='__main__':main()
