#!/usr/bin/env python3
"""Verify or replay the exact published conditional DC model. No network access."""
import argparse
import copy
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
MIB=1024**2
THREAD_KEYS=('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','BLIS_NUM_THREADS',
             'VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')
MODEL_SHA='285961cbf0d79d0ae28e2e2a84b256380da8c6a922b6977a2495b7554c922a95'

def require(value,message):
    if not value:raise RuntimeError(message)

def load(path):
    with Path(path).open() as stream:return json.load(stream)

def sha(path,logical=False):
    digest=hashlib.sha256()
    with (gzip.open(path,'rb') if logical else Path(path).open('rb')) as stream:
        for block in iter(lambda:stream.read(MIB),b''):digest.update(block)
    return digest.hexdigest()

def save(path,data):
    with Path(path).open('x') as stream:json.dump(data,stream,indent=2,allow_nan=False);stream.write('\n')

def object_sha(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def verify():
    require(sys.flags.dont_write_bytecode and not sys.flags.optimize,'Use nonoptimized Python -B')
    package=load(HERE/'PACKAGE-MANIFEST.json')
    for row in package['files']+package['external_source_files']:
        path=HERE/row['path']
        require(path.is_file() and sha(path)==row['stored_sha256'],'Missing or changed package input: '+row['path'])
        if row.get('logical_sha256'):require(sha(path,True)==row['logical_sha256'],'Logical source differs: '+row['path'])
    sys.path.insert(0,str(HERE/'runtime'))
    from model_contract import check_inputs,registry_networks
    from power_case_model import build_cases
    plan=load(HERE/'model/case-plan.corrected.disabled.json')
    registry=load(HERE/'model/terminal-registry.corrected.disabled.json')
    settings=load(HERE/'model/compiler-settings.disabled.json')
    contract=check_inputs(plan,registry,settings)
    require(object_sha(contract)==MODEL_SHA,'Corrected model contract differs')
    families,_=build_cases(plan,settings)
    ledger=load(HERE/'ledger.json');freeze=load(HERE/'freeze.json')
    regenerated={'networks':registry_networks(registry),'cases':[c for rows in families.values() for c in rows],
                 'loops':plan['VCAP_copper_loops'],'unit_transfers':[],
                 **{k:settings[k] for k in ('material','mesh_spacings_mm','convergence','limits')}}
    for key,value in regenerated.items():require(ledger[key]==value,'Regenerated ledger differs: '+key)
    require(ledger['model_contract']==freeze['model_contract']==contract,'Ledger/freeze model contract differs')
    require(ledger['freeze_manifest_sha256']==sha(HERE/'freeze.json'),'Portable manifest link differs')
    counts={'networks':len(ledger['networks']),'contacts':sum(len(n['contacts']) for n in ledger['networks']),
            'required_cases':sum(c['scope']!='same_BEC_illustrative' for c in ledger['cases']),
            'illustrative_cases':sum(c['scope']=='same_BEC_illustrative' for c in ledger['cases']),
            'VCAP_loops':len(ledger['loops'])}
    require(counts=={'networks':15,'contacts':107,'required_cases':294,'illustrative_cases':11,'VCAP_loops':5},'Model census differs')
    for role,row in freeze['files'].items():
        path=HERE/row['path']
        require(sha(path,path.suffix=='.gz')==row['sha256'],'Frozen input differs: '+role)
    for name,expected in freeze['analysis_source_sha256'].items():
        require(sha(HERE/'runtime'/name)==expected,'Numerical source differs: '+name)
    return {'schema':'f722-portable-dc-source-verification/v1','passed':True,'counts':counts,
            'model_contract_sha256':MODEL_SHA,'portable_freeze_sha256':sha(HERE/'freeze.json'),
            'portable_ledger_sha256':sha(HERE/'ledger.json'),'package_manifest_sha256':sha(HERE/'PACKAGE-MANIFEST.json'),
            'mesh_or_numerical_execution_performed':False}

def relocate(freeze,destination):
    result=copy.deepcopy(freeze)
    for row in result['files'].values():row['path']=os.path.relpath(HERE/row['path'],destination)
    return result

def numeric_imports():
    import platform,numpy,scipy,shapely,sexpdata
    require((platform.python_version(),numpy.__version__,scipy.__version__,shapely.__version__,sexpdata.__version__)
            ==('3.12.14','2.2.6','1.17.0','2.2.0','1.0.2'),'Runtime versions differ from completed run')
    import validate_static,audit_native_ports
    return validate_static,audit_native_ports

def child(stage,out):
    resource.setrlimit(resource.RLIMIT_AS,(4096*MIB,4096*MIB))
    wall=600 if stage=='prepare' else 1800
    signal.signal(signal.SIGALRM,signal.SIG_DFL);signal.alarm(wall)
    verification=verify();validator,ports=numeric_imports()
    if stage=='prepare':
        dest=out/'prepared';require(not dest.exists(),'Fresh prepared destination required');dest.mkdir()
        freeze=relocate(load(HERE/'freeze.json'),dest);save(dest/'freeze.json',freeze)
        ledger=load(HERE/'ledger.json');ledger['freeze_manifest_sha256']=sha(dest/'freeze.json');save(dest/'ledger.json',ledger)
        context=validator.preflight(dest/'freeze.json',dest/'ledger.json')
        files={k:dest/v['path'] for k,v in freeze['files'].items()}
        audit=ports.audit_ports(files['board'],files['geometry'],dest/'ledger.json',files['connectivity'])
        require(audit['passed'] is True,'Finite-port audit did not pass');save(dest/'port-audit.json',audit)
        verify()
        save(dest/'receipt.json',{'schema':'f722-portable-dc-preflight/v1','passed':True,'verification':verification,
             'freeze_sha256':sha(dest/'freeze.json'),'ledger_sha256':sha(dest/'ledger.json'),
             'port_audit_sha256':sha(dest/'port-audit.json'),'DRC_outside_scope':context['drc'],
             'numerical_execution_performed':False})
        return 0
    prepared=out/'prepared';receipt=load(prepared/'receipt.json')
    require(receipt['passed'] is True and receipt['verification']==verification,'Prepared source or model changed')
    for name,key in [('freeze.json','freeze_sha256'),('ledger.json','ledger_sha256'),('port-audit.json','port_audit_sha256')]:
        require(sha(prepared/name)==receipt[key],'Prepared receipt changed: '+name)
    require(load(prepared/'port-audit.json')['passed'] is True,'Finite ports not passed')
    validator.preflight(prepared/'freeze.json',prepared/'ledger.json')
    dest=out/'run';require(not dest.exists(),'Fresh numerical destination required');dest.mkdir()
    freeze=relocate(load(HERE/'freeze.json'),dest)
    freeze['numerical_execution_authorized']=True
    freeze['pilot_resource_limits']={'overall_wall_seconds':1800,'address_space_MiB':4096,'heavy_processes':1,'BLAS_threads':1,'OpenMP_threads':1}
    save(dest/'freeze.json',freeze)
    ledger=load(HERE/'ledger.json');ledger['freeze_manifest_sha256']=sha(dest/'freeze.json');save(dest/'ledger.json',ledger)
    sys.argv=['validate_static.py','--freeze',str(dest/'freeze.json'),'--ledger',str(dest/'ledger.json'),
              '--out',str(dest/'result.json.gz'),'--run','--mesh-cache',str(dest/'mesh-cache')]
    code=validator.main();verify()
    from stream_result_gzip import verify_result
    storage=verify_result(dest/'result.json.gz') if (dest/'result.json.gz').exists() else None
    save(dest/'replay-receipt.json',{'schema':'f722-portable-dc-replay/v1','exit_code':code,'result_storage':storage,
         'verification':verification,'freeze_sha256':sha(dest/'freeze.json'),'ledger_sha256':sha(dest/'ledger.json'),
         'scope':'Conditional DC only; failed cases remain failures; no local AC/thermal or final board qualification'})
    return code

def size(root):return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())

def supervised(stage,out):
    out=out.resolve();require(out.is_relative_to(Path('/tmp').resolve()),'All generated output must be under /tmp')
    require(not out.is_relative_to(HERE),'Output must be outside the immutable package')
    verify()
    out.mkdir(parents=True,exist_ok=True)
    require(shutil.disk_usage(out).free>=800*MIB,'Need 800 MiB output-filesystem launch admission')
    require(shutil.disk_usage(HERE).free>=128*MIB,'Source-filesystem reserve below 128 MiB')
    wall=600 if stage=='prepare' else 1800
    with Path('/tmp/f722-portable-dc-heavy.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',**{k:'1' for k in THREAD_KEYS})
        cpu=min(os.sched_getaffinity(0))
        def limits():
            os.sched_setaffinity(0,{cpu});resource.setrlimit(resource.RLIMIT_AS,(4096*MIB,4096*MIB))
        started=time.monotonic();reason=None;minimum_free=shutil.disk_usage(out).free;peak=0
        with (out/(stage+'.stdout.log')).open('x') as stdout,(out/(stage+'.stderr.log')).open('x') as stderr:
            process=subprocess.Popen([sys.executable,'-B',str(HERE/'replay.py'),'_child',stage,'--out',str(out)],
                       env=env,stdout=stdout,stderr=stderr,preexec_fn=limits,start_new_session=True)
            while process.poll() is None:
                used=size(out)+size(HERE);peak=max(peak,used);free=shutil.disk_usage(out).free;minimum_free=min(minimum_free,free)
                if used>512*MIB:reason='Combined package/output cap exceeded'
                elif free<128*MIB or shutil.disk_usage(HERE).free<128*MIB:reason='Filesystem reserve below 128 MiB'
                elif time.monotonic()-started>wall+5:reason='Stage time bound exceeded'
                if reason:os.killpg(process.pid,signal.SIGKILL);break
                time.sleep(.5)
            code=process.wait()
        save(out/(stage+'.watchdog.json'),{'stage':stage,'returncode':code,'stopped_reason':reason,
             'elapsed_seconds':time.monotonic()-started,'peak_sampled_package_and_output_bytes':peak,
             'minimum_output_filesystem_free_bytes':minimum_free,'wall_seconds':wall,'address_space_MiB':4096,
             'CPU_count':1,'numerical_threads':1,'partial_results_qualified':False})
        return code if reason is None else 2

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['verify','prepare','run','_child'])
    parser.add_argument('child_stage',nargs='?',choices=['prepare','run'])
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if args.stage=='verify':print(json.dumps(verify(),indent=2));return 0
    require(args.out is not None,'--out is required')
    if args.stage=='_child':
        require(args.child_stage in ('prepare','run'),'Child stage is required')
        return child(args.child_stage,args.out)
    return supervised(args.stage,args.out)

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print('REFUSED: '+str(error),file=sys.stderr);raise SystemExit(2)
