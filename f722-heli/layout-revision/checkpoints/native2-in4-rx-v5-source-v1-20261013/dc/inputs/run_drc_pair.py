#!/usr/bin/env python3
"""Fresh read-only native6 DRC pair; requires an exact owner lease and shared lane."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = Path('historical/source-tree')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_bytes())

def row(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}

def require(value, message):
    if not value:
        raise RuntimeError(message)

def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')

def run(lease_path, lease_sha):
    require(sha(lease_path) == lease_sha, 'Lease hash changed')
    lease = read(lease_path)
    require(lease.get('schema') == 'f722-native6-drc-pair-owner-lease/v1' and lease.get('owner_granted') is True,
            'No exact owner DRC-only grant')
    require(lease['producer_sha256'] == sha(__file__), 'DRC producer changed')
    require(lease['pair_wall_seconds'] == 240 and lease['per_mode_seconds'] == 120 and
            lease['address_space_MiB'] == 4096 and lease['heavy_processes'] == lease['numerical_threads'] == 1,
            'DRC resource scope differs')
    require(lease['PCB_or_native_mutation_allowed'] is False and lease['numerical_execution_allowed'] is False,
            'DRC lease changed scope')
    require(datetime.now(timezone.utc) < datetime.fromisoformat(lease['expires_utc']), 'Lease expired')
    config_path = HERE / 'config.json'
    require(sha(config_path) == lease['config_sha256'], 'DRC configuration changed')
    config = read(config_path)
    out = Path(lease['output_path']).resolve()
    require(str(out) == config['output_path'] and out.parent == HERE.parent and not out.exists(), 'Output is not fresh exact destination')
    lock_path = ROOT / 'owner-heavy-lane.lock'
    require(str(lock_path) == lease['shared_owner_lane_lock'] and lock_path.is_file(), 'Wrong shared lane')
    with lock_path.open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = {path: sha(path) for path in config['bound_files']}
        require(before == config['bound_files'], 'Current source/runtime bytes changed')
        resource.setrlimit(resource.RLIMIT_AS, (4096 * 1024**2, 4096 * 1024**2))
        out.mkdir()
        save(out/'source-before.json', before)
        started = time.monotonic()
        packet = {'schema': 'f722-intermediate-drc-provenance/v1', 'modes': {}}
        records, failure = [], None
        env = dict(os.environ)
        for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','BLIS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:
            env[name] = '1'
        try:
            for mode in ['drc_normal', 'drc_all_track']:
                require(datetime.now(timezone.utc) < datetime.fromisoformat(lease['expires_utc']), 'Lease expired before mode')
                require(all(sha(path) == value for path,value in before.items()), 'Source/runtime changed between modes')
                command = config['commands'][mode]
                t = time.monotonic()
                with (out/(mode+'.stdout.log')).open('xb') as stdout, (out/(mode+'.stderr.log')).open('xb') as stderr:
                    result = subprocess.run(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                            timeout=min(120, 240-(time.monotonic()-started)))
                execution = {'stage': mode, 'returncode': result.returncode, 'command': command}
                save(out/(mode+'.exit.json'), execution)
                records.append({'mode':mode,'elapsed_seconds':time.monotonic()-t,'returncode':result.returncode})
                require(result.returncode == 0, 'Native DRC invocation failed: '+mode)
                require(all(sha(path) == value for path,value in before.items()), 'Source/runtime changed during DRC')
                report_path = Path(config['reports'][mode])
                report = read(report_path)
                require(report.get('$schema') == 'https://schemas.kicad.org/drc.v1.json' and
                        report.get('kicad_version') == '10.0.6' and report.get('source') == Path(config['source']['board']['path']).name and
                        report.get('coordinate_units') == 'mm' and sorted(report.get('included_severities', [])) == ['error','exclusion','warning'] and
                        report.get('ignored_checks') == [] and all(isinstance(report.get(k),list) for k in ['violations','unconnected_items','schematic_parity']),
                        'DRC report is incomplete or wrong source/version')
                identity = {key:value['sha256'] for key,value in config['source'].items()}
                receipt = {'schema':'f722-native-drc-source-receipt/v1','mode':mode,'source_before':identity,'source_after':identity,
                           'producer_sha256':sha(__file__),'report_sha256':sha(report_path),'execution_sha256':sha(out/(mode+'.exit.json'))}
                receipt_path = out/(mode+'.receipt.json')
                save(receipt_path, receipt)
                packet['modes'][mode] = {'receipt':row(receipt_path),'producer':row(__file__),
                    'project':config['source']['project'],'rules':config['source']['rules'],'execution':row(out/(mode+'.exit.json'))}
            require(sha(lease_path) == lease_sha and datetime.now(timezone.utc) < datetime.fromisoformat(lease['expires_utc']), 'Lease changed or expired')
            save(out/'drc-provenance.json', packet)
        except Exception as error:
            failure = str(error)
        finally:
            after = {path: sha(path) for path in config['bound_files']}
            save(out/'source-after.json', after)
            if before != after:
                failure = 'Source/runtime changed during DRC'
            receipt = {'schema':'f722-native6-drc-pair-execution/v1','lease':row(lease_path),'config':row(config_path),
                       'producer':row(__file__),'elapsed_seconds':time.monotonic()-started,'peak_child_RSS_KiB':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                       'stages':records,'completed':failure is None,'failure':failure,'sources_unchanged':before==after,
                       'source_before':row(out/'source-before.json'),'source_after':row(out/'source-after.json'),
                       'numerical_execution':False,'electrical_acceptance_claimed':False}
            save(out/'execution-receipt.json', receipt)
            print(json.dumps(receipt))
        return 0 if failure is None else 2

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lease', required=True)
    parser.add_argument('--lease-sha', required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.lease, args.lease_sha))
