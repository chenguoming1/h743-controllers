#!/usr/bin/env python3
"""Plan/stage/explicitly release one immutable source-bound F722 numerical job.

The plan command probes interpreter/package identities only. It never exports,
compiles, meshes or solves. Stage is mesh-free. Launch alone starts the heavy job.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from support_receipt import verify_support,verify_files as verify_support_files,select_approved_poses

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parent
ACCEPTED_BOARD=PROJECT/'repo/f722-heli/layout-revision/hardware/f722-heli.kicad_pcb'
SOURCE_FILES=['f722-heli.kicad_pcb','owner-native.json','parts.json','owner-parity.json','owner-process.json',
 'owner-mechanical.json','owner-critical.json','power-audit.json','owner-drc.json','owner-drc-all.json',
 'owner-protection.json','owner-supplemental.json','owner-summary.json','owner-adoption.json',
 'power-revalidation-required.json','owner-mechanical-geometry.json','owner-firmware.json']
TOOLS=['compile_power_ledger.py','power_case_model.py','model_contract.py','prepare_loaded_pilot.py','run_bounded_pilot.py',
 'copper_fem.py','dc_circuit.py','validate_static.py','audit_native_ports.py','native_edge_noding.py','mesh_cache.py',
 'summarize_loaded_pilot.py','summarize_combined_pilot.py','report_actual_sinks.py','support_receipt.py','owner_support_contract.py']
JOB_KEYS=['cases','networks','loops','material','mesh_spacings_mm','convergence','limits']

class Refused(RuntimeError):pass
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def refuse(condition,why):
    if condition:raise Refused(why)
def local_output(p):
    p=Path(p).resolve()
    refuse(not p.is_relative_to(ROOT) or p==ROOT,'Output must be isolated under power-terminal-correction-v3')
    return p
def inventory(directory,names):return {name:sha(Path(directory)/name) for name in names}
def verify_inventory(directory,records):
    for name,expected in records.items():
        refuse(sha(Path(directory)/name)!=expected,'Source/runtime changed: '+name)

def child_environment():
    refuse(sys.flags.optimize!=0,'Optimized Python disables verification; run without -O')
    env=dict(os.environ,PYTHONPATH=str(PROJECT/'python-deps'),PYTHONDONTWRITEBYTECODE='1',PYTHONOPTIMIZE='0')
    env.pop('PYTHONHOME',None)
    for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','BLIS_NUM_THREADS','NUMEXPR_NUM_THREADS']:env[key]='1'
    return env

def runtime_identity():
    probe="""import importlib,importlib.metadata,json,hashlib,sys
from pathlib import Path
rows={}
for name in ['numpy','scipy','shapely','sexpdata']:
 m=importlib.import_module(name);p=Path(m.__file__).resolve()
 rows[name]={'version':getattr(m,'__version__',None) or importlib.metadata.version(name),'module_path':str(p),'module_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
print(json.dumps({'executable':str(Path(sys.executable).resolve()),'version':sys.version,'packages':rows}))
"""
    result=subprocess.run([sys.executable,'-B','-c',probe],env=child_environment(),capture_output=True,text=True,check=True,timeout=30)
    identity=json.loads(result.stdout);identity['executable_sha256']=sha(identity['executable'])
    expected={'numpy':'2.2.6','scipy':'1.17.0','shapely':'2.2.0','sexpdata':'1.0.2'}
    refuse(sys.version_info[:2]!=(3,12),'Use the reviewed Python 3.12 runtime')
    refuse({k:v['version'] for k,v in identity['packages'].items()}!=expected,'Numerical dependency versions differ from reviewed environment')
    return identity


def inspect_source(source,expected,accepted_board):
    source=Path(source).resolve();board=source/'f722-heli.kicad_pcb'
    refuse(sha(board)!=expected,'Candidate board differs from explicit expected SHA-256')
    refuse(sha(accepted_board)!=expected,'Accepted canonical board moved; re-plan the intended accepted source')
    records=inventory(source,SOURCE_FILES)
    data={n:read(source/n) for n in SOURCE_FILES if n.endswith('.json')}
    bound_names=set(data)-{'parts.json','owner-drc.json','owner-drc-all.json','owner-mechanical-geometry.json'}
    for name in bound_names:
        d=data[name]
        refuse(d.get('board_sha256')!=expected,'Stale source receipt: '+name)
    for name in ['owner-parity.json','owner-process.json','owner-mechanical.json','power-audit.json','owner-firmware.json']:
        refuse(data[name].get('passed')is not True,'Required source gate failed: '+name)
    native=data['owner-native.json'];summary=data['owner-summary.json']
    refuse(native.get('source_unchanged')is not True,'Native exporter changed source')
    refuse(data['owner-process.json'].get('geometry_sha256')!=records['owner-native.json'],'Process/native binding differs')
    support=verify_support(source,source/'owner-native.json')
    refuse(support['board_sha256']!=expected or support['native_sha256']!=records['owner-native.json'],'Verified support/native binding differs')
    refuse(data['owner-mechanical.json']['input_hashes']['owner-mechanical-geometry.json']!=records['owner-mechanical-geometry.json'],'Mechanical export binding differs')
    refuse(data['owner-adoption.json']['native_gate_receipt_sha256']!=records['owner-summary.json'],'Adoption/native owner receipt binding differs')
    refuse(data['owner-critical.json'].get('faults') or summary['critical'].get('missing_ground_returns'),'Critical geometry/return fault')
    for name in ['drc','drc-all']:
        d=summary[name];raw=data['owner-'+name+'.json']
        refuse(d['errors'] or d['warnings'],'Native DRC errors/warnings remain')
        refuse(raw.get('ignored_checks') or raw.get('schematic_parity'),'Ignored checks or schematic parity faults remain')
        refuse(d['unconnected']!=len(raw['unconnected_items']),'DRC count/receipt mismatch')
        refuse(any(v['severity'] in ['error','warning'] for v in raw['violations']),'Raw DRC violation remains')
    refuse(data['owner-adoption.json'].get('native_unfinished_connections')!=summary['drc']['unconnected'],'Adoption does not bind current open count')
    verify_inventory(source,records)
    return records,dict(board_sha256=expected,native_sha256=records['owner-native.json'],
        support_evidence_files_sha256=support['evidence_files_sha256'],support_verified_chain=support['verified_chain'],
        native_version=native['native_version'],opens=summary['drc']['unconnected'],errors=0,warnings=0,
        via_count=data['owner-process.json']['via_count'],unique_drill_count=data['owner-process.json']['unique_drill_count'],
        preserved_incomplete_protection=summary['protection'],preserved_incomplete_supplemental=summary['supplemental'])


def inspect_model_review(path,expected):
    path=Path(path).resolve()
    refuse(sha(path)!=expected,'Explicit owner-reviewed implementation SHA differs')
    review=read(path)
    refuse(review.get('schema')!='f722-corrected-implementation-review/v3','Unknown corrected implementation review')
    refuse(set(review['runtime_source_sha256'])!=set(TOOLS),'Reviewed runtime inventory is incomplete')
    refuse(review.get('launcher_sha256')!=sha(__file__),'Reviewed launcher changed')
    verify_inventory(ROOT,review['runtime_source_sha256'])
    verify_inventory(ROOT,review['model_inputs_sha256'])
    for name,expected in review['evidence_sha256'].items():
        refuse(sha(PROJECT/name)!=expected,'Manufacturer/branch review evidence changed: '+name)
    return review


def make_plan(args):
    out=local_output(args.out);job=local_output(args.job)
    refuse(out.exists() or job.exists(),'Use fresh plan and job destinations')
    refuse(out==job or out.is_relative_to(job),'Plan output must be outside its future job directory')
    review=inspect_model_review(args.model_review,args.owner_reviewed_model_sha)
    source=Path(args.source).resolve();accepted=Path(args.accepted_board).resolve()
    refuse(accepted!=ACCEPTED_BOARD.resolve(),'Do not override the canonical board to evade a moved-source refusal')
    records,scope=inspect_source(source,args.expected_board_sha,accepted)
    reference=PROJECT/'static-power-validation/pilot-candidate19-operator-refined-released/ledger.json'
    old=read(reference)
    refuse(sha(reference)!=review['historical_ledger_sha256'],'Historical reference changed')
    runtime=inventory(ROOT,TOOLS)
    model=read(ROOT/'case-plan.corrected.disabled.json')['model_contract']
    refuse(canonical(model)!=review['model_contract_sha256'],'Reviewed corrected model contract changed')
    settings=read(ROOT/'compiler-settings.json')
    for key in ['material','mesh_spacings_mm','convergence','limits']:
        refuse(settings[key]!=old[key],'Preserved physics/numerical policy changed: '+key)
    settings['source_stage']='Fresh corrected conditional prototype validation of exact board '+args.expected_board_sha+'; no historical numerical result reused'
    settings['owner_reviewed_model_sha256']=args.owner_reviewed_model_sha
    mechanical=read(source/'owner-mechanical.json')
    poses=select_approved_poses(source,mechanical,getattr(args,'poses',None))
    paths={'case_plan':ROOT/'case-plan.corrected.disabled.json',
           'registry':ROOT/'terminal-registry.corrected.disabled.json',
           'model_review':Path(args.model_review).resolve(),
           'poses':poses}
    refuse(mechanical['input_hashes']['poses-native.json']!=sha(paths['poses']),'Approved mechanical pose input changed; review explicit pose selection')
    counts=model['counts']
    plan=dict(schema='f722-corrected-power-revalidation-plan/v3',status='PLANNING ONLY; NO COMPILE OR NUMERICAL RUN',
      heavy_execution_enabled=False,source=str(source),accepted_board=str(accepted),job=str(job),scope=scope,
      source_files_sha256=records,runtime_source_sha256=runtime,wrapper_sha256=sha(__file__),
      execution_runtime=runtime_identity(),
      inputs={key:dict(path=str(path),sha256=sha(path)) for key,path in paths.items()},
      reviewed_model=dict(path=str(Path(args.model_review).resolve()),sha256=args.owner_reviewed_model_sha),
      model_contract=model,
      reference_ledger=dict(path=str(reference),sha256=sha(reference)),
      reference_preserved_physics_sha256={k:canonical(old[k]) for k in ['material','mesh_spacings_mm','convergence','limits','loops']},
      compiler_settings=settings,required_case_count=counts['required'],illustrative_case_count=counts['illustrative'],
      VCAP_loop_count=counts['loops'],grids_mm=settings['mesh_spacings_mm'],
      net_count=counts['networks'],contact_count=counts['contacts'],GND_contact_count=counts['ground_contacts'],
      resource_bounds=dict(wall_seconds=1500,address_space_MiB=4096,numerical_threads=1,heavy_processes=1),
      slot_lock=str(PROJECT/'static-power-validation/.f722-heavy-slot.lock'),
      slot_policy='Owner must stop/release ordinary routing before launch. Shared advisory lock excludes cooperating launchers only.',
      cache_policy='Fresh corrected job/cache directory. No historical cache copying or rewritten identity headers.',
      estimates=dict(status='UNMEASURED corrected workload; previous873.1s is historical context only',
                     interpretation='305 cases do not imply4.18x factorization time; changed contacts and added rails require new matrices, with additional circuit and loaded-field work.'),
      postprocessing='DISABLED: old146/140/5532 corner and sensitivity pipeline requires corrected regeneration.',
      qualification='Enumerated conditional prototype DC checks; current-polytope coverage is not a proof of nonlinear interior extrema or flight qualification.')
    out.parent.mkdir(parents=True,exist_ok=True);save(out,plan)
    return dict(plan=str(out),plan_sha256=sha(out),job=str(job),source_scope=scope,heavy_run_started=False)


def load_bound_plan(path,expected):
    refuse(sha(path)!=expected,'Plan hash differs from explicit expected digest')
    p=read(path);refuse(p.get('schema')!='f722-corrected-power-revalidation-plan/v3','Unexpected plan schema')
    refuse(p['wrapper_sha256']!=sha(__file__),'Launcher changed after planning; re-plan')
    refuse(p['execution_runtime']!=runtime_identity(),'Interpreter or numerical dependency identity changed; re-plan')
    verify_inventory(p['source'],p['source_files_sha256']);verify_inventory(ROOT,p['runtime_source_sha256'])
    verify_support_files(p['scope']['support_evidence_files_sha256'])
    refuse(Path(p['accepted_board']).resolve()!=ACCEPTED_BOARD.resolve(),'Plan canonical board path changed')
    refuse(sha(p['accepted_board'])!=p['scope']['board_sha256'],'Accepted canonical board moved; re-plan')
    for row in p['inputs'].values():refuse(sha(row['path'])!=row['sha256'],'Plan/registry/pose/source-bound input changed')
    refuse(sha(p['reference_ledger']['path'])!=p['reference_ledger']['sha256'],'Reference job changed')
    review=inspect_model_review(p['reviewed_model']['path'],p['reviewed_model']['sha256'])
    refuse(canonical(p['model_contract'])!=review['model_contract_sha256'],'Plan corrected model differs from owner review')
    refuse(p['compiler_settings'].get('owner_reviewed_model_sha256')!=p['reviewed_model']['sha256'],'Compiler owner-review identity differs from plan')
    local_output(p['job'])
    return p


def checked_command(argv,log,allowed=(0,),timeout=600):
    env=child_environment()
    with Path(log).open('x') as stream:
        result=subprocess.run([str(v) for v in argv],stdout=stream,stderr=subprocess.STDOUT,env=env,timeout=timeout)
    refuse(allowed is not None and result.returncode not in allowed,'Command refused/failed; preserved log: '+str(log))
    return result.returncode


def job_check(plan,directory):
    from model_contract import check_ledger
    ledger=read(Path(directory)/'ledger.json')
    check_ledger(ledger,plan['model_contract'],full=True)
    for key,expected in plan['reference_preserved_physics_sha256'].items():
        refuse(canonical(ledger[key])!=expected,'Preserved physical/numerical job changed: '+key)
    p=read(Path(directory)/'pilot-plan.json')
    refuse(p['board_sha256']!=plan['scope']['board_sha256'],'Prepared source differs')
    refuse(p['model_contract_sha256']!=canonical(plan['model_contract']),'Prepared corrected model differs')


def stage(args,plan):
    job=Path(plan['job']);refuse(job.exists(),'Job already exists; do not overwrite or mix identities')
    job.mkdir();(job/'tools').mkdir();(job/'inputs').mkdir()
    for name,expected in plan['runtime_source_sha256'].items():
        shutil.copyfile(ROOT/name,job/'tools'/name);refuse(sha(job/'tools'/name)!=expected,'Tool copy changed')
    for key,row in plan['inputs'].items():
        target=job/'inputs'/(key+'.json');shutil.copyfile(row['path'],target)
        refuse(sha(target)!=row['sha256'],'Pinned input copy changed')
    save(job/'compiler-settings.json',plan['compiler_settings'])
    checked_command([sys.executable,job/'tools/compile_power_ledger.py','--source',plan['source'],
      '--plan',job/'inputs/case_plan.json','--registry',job/'inputs/registry.json','--settings',job/'compiler-settings.json',
      '--out',job/'compiled'],job/'compile.log')
    checked_command([sys.executable,job/'tools/prepare_loaded_pilot.py','--compiled',job/'compiled','--out',job/'prepared',
      '--refined-combined','--evidence',Path(plan['source'])/'power-audit.json'],job/'prepare.log')
    job_check(plan,job/'prepared')
    checked_command([sys.executable,job/'prepared/solver-source/validate_static.py','--freeze',job/'prepared/freeze.json',
      '--ledger',job/'prepared/ledger.json','--out',job/'preflight.json'],job/'preflight.log')
    load_bound_plan(args.plan,args.plan_sha)
    files={str(p.relative_to(job)):sha(p) for p in job.rglob('*') if p.is_file()}
    receipt=dict(schema='f722-staged-revalidation/v1',plan_sha256=args.plan_sha,board_sha256=plan['scope']['board_sha256'],
                 heavy_execution_enabled=False,new_meshes=0,new_loaded_fields=0,files_sha256=files)
    save(job/'stage-receipt.json',receipt)
    return dict(status='STAGED AND PREFLIGHTED; NO MESH OR SOLVE',stage_receipt_sha256=sha(job/'stage-receipt.json'))


def require_release(plan,value):
    refuse(value!=plan['scope']['board_sha256'],'Explicit owner heavy-slot release for this exact board is required')


def bound_stage(args,plan):
    job=Path(plan['job']);receipt=read(job/'stage-receipt.json')
    refuse(receipt.get('plan_sha256')!=args.plan_sha or receipt.get('board_sha256')!=plan['scope']['board_sha256'],'Staged job belongs to a different plan/board')
    verify_inventory(job,receipt['files_sha256'])
    return receipt


def released_identity(plan):
    job=Path(plan['job']);released=job/'released';freeze=read(released/'freeze.json')
    board=freeze['files']['board'];board_path=(released/board['path']).resolve()
    refuse(board['sha256']!=plan['scope']['board_sha256'] or sha(board_path)!=plan['scope']['board_sha256'],'Released board differs from selected plan')
    job_check(plan,released)
    return dict(board_sha256=sha(board_path),freeze_sha256=sha(released/'freeze.json'),ledger_sha256=sha(released/'ledger.json'))


def launch(args,plan):
    require_release(plan,args.owner_released_board_sha)
    job=Path(plan['job']);receipt=bound_stage(args,plan)
    for name in ['released','mesh-cache','launch-receipt.json']:
        refuse((job/name).exists(),'Preserve prior launch/result/cache; use a fresh job')
    with Path(plan['slot_lock']).open('a+') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise Refused('Exclusive numerical slot is occupied')
        started=time.monotonic()
        output=dict(status='RELEASE STARTED; NO QUALIFICATION',plan_sha256=args.plan_sha,
                    board_sha256=plan['scope']['board_sha256'],stage_receipt_sha256=sha(job/'stage-receipt.json'),
                    original_runner_exit_code=None,result_written=False,summary_status='NOT RUN')
        save(job/'launch-receipt.json',output)
        try:
            checked_command([sys.executable,job/'tools/prepare_loaded_pilot.py','--compiled',job/'compiled','--out',job/'released',
              '--refined-combined','--release','--owner-released-board-sha',plan['scope']['board_sha256'],'--evidence',Path(plan['source'])/'power-audit.json'],job/'release.log')
            identity=released_identity(plan);output.update(identity)
            load_bound_plan(args.plan,args.plan_sha);bound_stage(args,plan)
            (job/'mesh-cache').mkdir()
            code=checked_command([sys.executable,job/'released/solver-source/run_bounded_pilot.py',
              '--freeze',job/'released/freeze.json','--ledger',job/'released/ledger.json','--out',job/'released/result.json',
              '--wall-seconds','1500','--memory-mib','4096','--mesh-cache',job/'mesh-cache'],job/'run.log',allowed=None,timeout=1530)
            present=(job/'released/result.json').exists()
            output.update(status='COMPLETED SELECTED NUMERICAL JOB' if code in [0,1] and present else 'REFUSED OR INCOMPLETE; NO QUALIFICATION',
              original_runner_exit_code=code,result_written=present,result_sha256=sha(job/'released/result.json') if present else None,
              wall_seconds=time.monotonic()-started,added_corner_loaded_fields=False,
              required_illustrative_and_VCAP_decisions='See combined-summary.json; exit1 and illustrative failures are not rewritten.')
            save(job/'launch-receipt.json',output)
            refuse(released_identity(plan)!=identity,'Released source changed during solve')
            load_bound_plan(args.plan,args.plan_sha);bound_stage(args,plan)
            if present and code in [0,1,2] and all(k in read(job/'released/result.json') for k in ['freeze_sha256','ledger_sha256']):
                checked_command([sys.executable,job/'tools/summarize_combined_pilot.py','--result',job/'released/result.json',
                  '--freeze',job/'released/freeze.json','--ledger',job/'released/ledger.json','--out',job/'combined-summary.json'],job/'summary.log')
                output['summary_status']='COMPLETED';output['summary_sha256']=sha(job/'combined-summary.json')
            refuse(released_identity(plan)!=identity or (present and sha(job/'released/result.json')!=output['result_sha256']),'Released source/result changed during summary')
            load_bound_plan(args.plan,args.plan_sha);bound_stage(args,plan)
            return output
        except Exception as exc:
            output.update(status='REFUSED OR INCOMPLETE; NO QUALIFICATION',failure_type=type(exc).__name__,failure=str(exc))
            if (job/'released/result.json').exists():output.update(result_written=True,result_sha256=sha(job/'released/result.json'))
            raise
        finally:
            output['wall_seconds']=time.monotonic()-started
            save(job/'launch-receipt.json',output)
            fcntl.flock(lock,fcntl.LOCK_UN)


def bound_launch(args,plan):
    job=Path(plan['job']);bound_stage(args,plan);receipt=read(job/'launch-receipt.json')
    refuse(receipt.get('plan_sha256')!=args.plan_sha,'Launch belongs to a different plan')
    refuse(receipt.get('stage_receipt_sha256')!=sha(job/'stage-receipt.json'),'Stage receipt changed after launch')
    refuse(receipt.get('original_runner_exit_code') not in [0,1] or receipt.get('failure_type'),'No verified completed field result to replay')
    identity=released_identity(plan)
    refuse(any(receipt.get(k)!=v for k,v in identity.items()),'Released identities differ from launch receipt')
    refuse(sha(job/'released/result.json')!=receipt.get('result_sha256'),'Completed result changed')
    result=read(job/'released/result.json')
    refuse(any(result.get(k)!=identity[k] for k in ['freeze_sha256','ledger_sha256']),'Completed result belongs to different released inputs')
    return receipt


def post(args,plan):
    raise Refused('Historical146/140/5532 replay is disabled. Regenerate source-bound corrected corner/sensitivity definitions before any future replay.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('plan');p.add_argument('--source',required=True);p.add_argument('--expected-board-sha',required=True)
    p.add_argument('--accepted-board',default=str(PROJECT/'repo/f722-heli/layout-revision/hardware/f722-heli.kicad_pcb'))
    p.add_argument('--job',required=True);p.add_argument('--out',required=True)
    p.add_argument('--poses',help='Optional explicit approved pose input; must match the selected source mechanical receipt SHA. Default: source-local poses-native.json')
    p.add_argument('--model-review',default=str(ROOT/'MODEL-REVIEW.json'))
    p.add_argument('--owner-reviewed-model-sha',required=True,help='Explicit SHA of this implementation after owner review; no historical approval inheritance')
    for mode in ['stage','launch','post']:
        p=sub.add_parser(mode);p.add_argument('--plan',required=True);p.add_argument('--plan-sha',required=True)
        if mode=='launch':p.add_argument('--owner-released-board-sha',required=True)
    args=parser.parse_args()
    if args.mode=='plan':result=make_plan(args)
    else:
        plan=load_bound_plan(args.plan,args.plan_sha)
        result={'stage':stage,'launch':launch,'post':post}[args.mode](args,plan)
    print(json.dumps(result,allow_nan=False))

if __name__=='__main__':main()
