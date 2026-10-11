#!/usr/bin/env python3
"""Prepare only the closed v5 trial and final static expanded-scope proposal."""
import collections
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD = ROOT / 'publication-frozen-corrected-routing-v2-20261011'
OLD_PREFIX = 'f722-heli/layout-revision/checkpoints/corrected-routing-v2-20261011/'
PACKAGE = OLD / 'payload' / OLD_PREFIX
BASE = 'recovery-negotiated-routing-20261011/'
V5 = BASE + 'negotiated-v5/'
PROPOSAL = BASE + 'expanded-scope-planning-v1/'


def identity(path):
    p = ROOT / path
    h = hashlib.sha256()
    g = hashlib.sha1(b'blob ' + str(p.stat().st_size).encode() + b'\0')
    with p.open('rb') as stream:
        for b in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(b); g.update(b)
    return {'bytes': p.stat().st_size, 'sha256': h.hexdigest(), 'git_blob_sha': g.hexdigest()}


def read(path):
    return json.loads((ROOT / path).read_text())


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def pin_of(row):
    return row.get('expected_sha256') or pin_of(row['entry'])


def main():
    old_manifest = read(OLD / 'manifest.json')
    assert identity(OLD / 'manifest.json')['sha256'] == 'bdecb40f7471f90ac9a59f22bc9d8c213ee90651127d3815b89b7babb06de905'
    prior = read(PACKAGE / 'reconstruction-map.json')
    prior_regen = read(PACKAGE / 'regeneration-map.json')['files']
    terminal = read(V5 + 'run/execution-receipt.json')
    assert identity(V5 + 'run/execution-receipt.json')['sha256'] == '723937c8ec4f12dbb9fb40b6fa16356f83f4f9ee4fbb9e7b508cd9287c45a890'
    assert terminal['passed'] is False and terminal['source_files_unchanged'] and terminal['lane_released']
    assert identity(PROPOSAL + 'proposal.json')['sha256'] == 'e467092fccd9b6dec32f5c692da25803529d300e6be9be6ab7da1bdfd58048ae'
    requested = {}; reasons = collections.defaultdict(set)
    def add(path, pin=None, why='closed v5 scope'):
        p = Path(path)
        if p.is_absolute(): p = p.relative_to(ROOT)
        path = str(p)
        assert '..' not in p.parts and '__pycache__' not in p.parts
        assert not any(x in path for x in ['negotiated-v6/', 'expanded-173', 'cache-control'])
        if pin and requested.get(path): assert requested[path] == pin
        requested[path] = pin or requested.get(path); reasons[path].add(why)
    for row in read(V5 + 'contract.json')['source_files'] + read(PROPOSAL + 'proposal.json')['source_files']:
        add(row['path'], row['sha256'], 'exact contract/proposal dependency')
    for row in terminal['saved_checkpoint_files']:
        add(row['path'], row['sha256'], 'terminal checkpoint inventory')
    for group in [V5, PROPOSAL]:
        for p in sorted((ROOT / group).rglob('*')):
            if not p.is_file() or 'build' in p.parts or '__pycache__' in p.parts: continue
            assert not p.name.endswith('.next')
            add(p.relative_to(ROOT))
    generated = {}; rows = []; objects = {}
    for path, pin in sorted(requested.items()):
        p = ROOT / path; assert p.is_file()
        if path in prior_regen:
            assert pin is None or pin_of(prior_regen[path]) == pin
            generated[path] = {'kind': 'inherited_corrected_v2_regeneration', 'entry': prior_regen[path],
                'predecessor_manifest_sha256': 'bdecb40f7471f90ac9a59f22bc9d8c213ee90651127d3815b89b7babb06de905'}
            continue
        if path == V5 + 'model/model.json':
            digest = read(V5 + 'model/composition-receipt.json')['model_sha256']
            assert pin == digest
            generated[path] = {'kind': 'regenerate', 'expected_sha256': digest, 'bytes': p.stat().st_size,
                'contract': V5 + 'contract.json', 'stage': 'composition', 'execution_performed': False}
            continue
        result = identity(path); assert pin is None or pin == result['sha256'], ('Changed source', path)
        digest = result['sha256']; row = dict(path=path, reasons=sorted(reasons[path]), bytes_verified=True, **result)
        if digest in prior['objects']:
            row['storage'] = 'reuse_frozen_corrected_v2_object'
            row['source'] = {'checkpoint_manifest_sha256': 'bdecb40f7471f90ac9a59f22bc9d8c213ee90651127d3815b89b7babb06de905',
                'restore_alias': next(k for k,v in prior['restore_files'].items() if v == digest),
                'object_sha256': digest, 'prior_storage': prior['objects'][digest], 'publication_status': 'LOCAL_ONLY'}
        else: row['storage'] = 'capture_unique_successor_object'
        rows.append(row)
        objects.setdefault(digest, {'bytes': row['bytes'], 'storage': row['storage'], 'representative_path': path, 'aliases': []})['aliases'].append(path)
    checkpoints = []; initial = identity(V5 + 'run/candidate.fixed-traces-before.exact')['sha256']
    for index in range(1,20):
        stem = V5 + 'run/candidate.checkpoints/checkpoint-' + str(index).zfill(4)
        data = read(stem + '.after.json')
        assert identity(stem + '.fixed-traces-after.exact')['sha256'] == initial
        checkpoints.append({'index': index, 'report': dict(path=stem+'.after.json', **identity(stem+'.after.json')),
            'session': dict(path=stem+'.ses', **identity(stem+'.ses')), 'fixed_trace_sha256': initial,
            'missing_required_joins': sum(max(0,len(x['groups'])-1) for x in data['required_logical_connectivity']),
            'role_count': len(data['required_logical_connectivity']), 'route_counters': data.get('route_counters')})
    progress = read(V5 + 'run/candidate.progress.json')
    assert progress['report_sha256'] == checkpoints[-1]['report']['sha256'] and progress['session_sha256'] == checkpoints[-1]['session']['sha256']
    assert progress['ses_save_read_only_verified'] and not progress['pending_route_geometry']
    assert all(not (ROOT / V5 / 'run' / x).exists() for x in ['candidate.after.json','candidate.ses'])
    log = (ROOT / V5 / 'run/negotiation.log').read_text()
    assert 'OutOfMemoryError: Java heap space' in log
    completed = [json.loads(line.removeprefix('ROUTE_PROGRESS ')) for line in log.splitlines() if line.startswith('ROUTE_PROGRESS ') and '"pass_completed"' in line]
    fullpasses = {}
    for event in completed:
        number = event['attempt']['pass_completed']
        fullpasses[number] = event['missing_required_joins']
    assert fullpasses == {1:17,2:17,3:16}
    stats = {mode: {'paths': sum(r['storage']==mode for r in rows), 'unique_objects': sum(r['storage']==mode for r in objects.values()),
                    'unique_bytes': sum(r['bytes']for r in objects.values()if r['storage']==mode)}for mode in sorted({r['storage']for r in rows})}
    write('source-allowlist.json', {'schema':'f722-v5-local-recovery-plan/v1','source_entries':rows,'unique_objects':objects,'statistics':stats,
        'frozen_local_predecessor':{'manifest':str(OLD/'manifest.json'),'manifest_sha256':'bdecb40f7471f90ac9a59f22bc9d8c213ee90651127d3815b89b7babb06de905',
            'expected_tree':old_manifest['expected_final_tree'],'remote_publication_verified':False}, 'future173_cache_successors_excluded':True})
    write('regeneration-map.json', {'schema':'f722-v5-regeneration-map/v1','files':generated,'engineering_replay_performed':False})
    write('evidence-status.json', {'schema':'f722-v5-terminal-status/v1','status':'FAILED_JAVA_HEAP_OOM_NO_FINAL_EXPORT',
        'receipt_sha256':'723937c8ec4f12dbb9fb40b6fa16356f83f4f9ee4fbb9e7b508cd9287c45a890','elapsed_seconds':terminal['elapsed_seconds'],
        'complete_checkpoints':checkpoints,'latest_progress_pair_hash_bound':True,'all_exact_trace_baselines_equal':True,
        'completed_pass_missing_joins':fullpasses,'best_source_missing_joins':13,'final_report_session_absent':True,
        'proposal_sha256':'e467092fccd9b6dec32f5c692da25803529d300e6be9be6ab7da1bdfd58048ae',
        'proposal_status':'STATIC_PROPOSAL_ONLY_NOT_ADOPTED_SCOPE','accepted_board':'native7','native_acceptance':False,'numerical_power':'STALE'})
    write('preparation-verification.json', {'source_paths':len(rows),'unique_objects':len(objects),'new_sources_rehashed':True,'all19_checkpoint_triplets_bound':True,
        'raw_exact_fixed_primitive_baseline_preserved':True,'later_successor_paths_included':False,'heavy_lock_acquired':False,'external_writes':False})
    print(json.dumps({'paths':len(rows),'objects':len(objects),'regeneration_paths':len(generated),'statistics':stats},indent=2))


if __name__ == '__main__': main()
