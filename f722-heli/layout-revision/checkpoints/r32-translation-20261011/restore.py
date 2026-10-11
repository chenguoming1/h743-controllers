#!/usr/bin/env python3
"""Append and verify the R32 source-only milestone after both predecessor restores.

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
    parser.add_argument('--routing-package',type=Path,required=True,help='Published routing-recovery-20261011 package directory')
    parser.add_argument('--previous-package',type=Path,required=True,help='Published west-tx-bridge-20261011 package directory')
    args=parser.parse_args();package=Path(__file__).resolve().parent
    raw=(package/'overlay-inventory.json').read_bytes();inventory=json.loads(raw)
    index=json.loads((package/'archive-index.json').read_bytes())
    if digest(raw)!=index['source_inventory_sha256']:raise ValueError('Archive inventory binding mismatch')
    if args.workspace.is_symlink() or args.previous_package.is_symlink() or args.routing_package.is_symlink():raise ValueError('Root symlink refused')
    workspace=args.workspace.resolve();previous=args.previous_package.resolve();routing=args.routing_package.resolve()
    if not workspace.is_dir():raise ValueError('Restore predecessor into the workspace first')
    packages={'publication-frozen-routing-recovery-20261011':routing,'publication-frozen-west-tx-bridge-20261011':previous}
    for row in inventory['previous_package_files']:verify_file(safe_path(packages[row['package']],row['path']),row)
    prior_map={}
    for directory,name in [(routing,'recovery-inventory.json'),(previous,'overlay-inventory.json')]:
        for row in json.loads((directory/name).read_bytes())['files']:
            old=prior_map.get(row['restore_path'])
            if old and any(old[k]!=row[k] for k in ['bytes','sha256','git_blob_sha']):
                raise ValueError('Conflicting predecessor inventories')
            prior_map[row['restore_path']]=row
    if len(prior_map)!=inventory['summary']['previous_complete_restore_paths']:
        raise ValueError('Unexpected predecessor inventory')
    prior={'files':list(prior_map.values())}
    for row in prior['files']:verify_file(safe_path(workspace,row['restore_path']),row)
    additions=[];reused=[];paths=set()
    for row in inventory['files']:
        path=safe_path(workspace,row['restore_path'])
        if row['restore_path'] in paths:raise ValueError('Duplicate restore path')
        paths.add(row['restore_path'])
        if row['storage']=='previous':
            old=prior_map.get(row['restore_path'])
            if not old or any(old[k]!=row[k] for k in ['bytes','sha256','git_blob_sha']):
                raise ValueError('Invalid predecessor reuse binding')
            verify_file(path,row);reused.append(row)
        elif row['storage']=='overlay':
            if path.exists():raise ValueError('Refusing to overwrite existing path: '+row['restore_path'])
            additions.append(row)
        else:raise ValueError('Unknown storage mode')
    wanted={r['sha256']:r for r in additions}
    if len(wanted)!=index['unique_objects']:raise ValueError('Unexpected overlay object count')
    with tempfile.TemporaryDirectory(prefix='f722-r32-overlay-',dir=workspace.parent) as tmp:
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
    replay=json.loads((workspace/inventory['replay_checkpoint_path']).read_bytes())
    contract_sha=current[inventory['contract_path']]['sha256']
    original_contract='recovered-native7/recovery-flash/native7-R32-translation-complete-contract-v3.json'
    if checkpoint['contract_sha256']!=current[original_contract]['sha256']:
        raise ValueError('Positive checkpoint original contract binding mismatch')
    if replay['contract_sha256']!=contract_sha or terminal['contract_sha256']!=contract_sha:
        raise ValueError('Current result contract binding mismatch')
    for receipt in [checkpoint,replay]:
        if receipt['full_physical_snapshot_sha256']!=inventory['required_positive_snapshot_sha256']:
            raise ValueError('Positive snapshot mismatch')
        if not receipt['complete_guard']['passed'] or not receipt['finite_contact_support_checks']['passed']:
            raise ValueError('Positive checkpoint receipt mismatch')
        if receipt['complete_planning_witness'] or receipt['native_edited']:
            raise ValueError('Unexpected native/completion claim')
    for row in terminal['accepted_checkpoints']:
        if current[row['path']]['sha256']!=row['sha256']:raise ValueError('Accepted replay checkpoint mismatch')
    seal=json.loads((workspace/inventory['preparation_seal_path']).read_bytes())
    for row in seal['files']:
        if current[row['path']]['sha256']!=row['sha256']:raise ValueError('Preparation seal dependency mismatch')
    if len(contract['source_files'])!=288 or seal['source_bindings_verified']!=288:
        raise ValueError('Contract closure size mismatch')
    trials=[]
    for trial in terminal['ABC_crossover_trials']:
        checks=trial['complete_guard']['ordinary']['checks']+trial['complete_guard']['external']
        cuts=[c['net'] for c in checks if not c['connected']]
        if len(checks)!=12 or len(cuts)!=10 or trial['complete_guard']['passed']:
            raise ValueError('Failed complete-tree guard receipt mismatch')
        if not trial['contacts']['passed'] or not all(c['passed'] for c in trial['checks']):
            raise ValueError('Finite/contact receipt mismatch')
        if not next(c for c in checks if c['net']=='ABC_PG')['physically_complete']:
            raise ValueError('ABC tree receipt mismatch')
        if trial['complete'] or not trial['rolled_back_entire_batch']:
            raise ValueError('Failed batch was not discarded')
        trials.append({'index':trial['index'],'peer_demand_cuts':cuts,'whole_batch_rolled_back':True})
    if len(trials)!=2 or terminal['complete_planning_witness'] or terminal['native_edited'] or not terminal['all_source_files_unchanged']:
        raise ValueError('Terminal result receipt mismatch')
    print(json.dumps({'schema':'f722-r32-translation-overlay-restore-result/v1',
        'previous_paths_verified_before_and_after':len(prior['files']),
        'current_scope_paths_verified':len(current),'current_contract_dependencies_verified':len(contract['source_files']),
        'reused_previous_paths':len(reused),'added_paths':len(additions),'combined_workspace_paths':len(prior_map|current),
        'all_size_sha256_git_blob_checks_passed':True,'xz_crc64_verified':True,'preparation_seal_bindings_verified':True,
        'positive_snapshot_sha256':checkpoint['full_physical_snapshot_sha256'],
        'positive_original_and_current_replay_receipts_verified':True,'current_failed_outcome_trials':trials,
        'complete_planning_witness':False,'terminal_failure_preserved':terminal['terminal_reason'],
        'native_edited':False,'engineering_code_executed':False},indent=2))



if __name__=='__main__':main()
