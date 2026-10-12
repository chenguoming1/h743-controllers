#!/usr/bin/env python3
"""Prepare the corrected primary/VCAP job from compiled evidence; never solve."""
import argparse,copy,json,os,shutil
from pathlib import Path
from copper_fem import Refused
from validate_static import preflight,read_json,sha256
from compile_power_ledger import check_cases,save
from audit_native_ports import audit_ports
from model_contract import check_ledger,REVISION
from power_case_model import digest

def select_cases(primary):
    check_ledger(primary,primary.get('model_contract',{}),full=True)
    return copy.deepcopy(primary['cases'])


def select_scope(primary,cases,refined_combined=False):
    if not refined_combined:raise Refused('Corrected primary requires both reviewed grids and all five VCAP loops')
    check_ledger(primary,primary.get('model_contract',{}),full=True)
    if digest(cases)!=primary['model_contract']['job_sha256']['cases']:
        raise Refused('Corrected selected case definitions changed')
    networks=copy.deepcopy(primary['networks']);loops=copy.deepcopy(primary['loops'])
    check_cases(cases,networks)
    return networks,loops


def checked_extra_evidence(paths,board_sha256,native_sha256):
    rows=[];names=set()
    for raw in paths:
        path=Path(raw);name=path.name
        if name in names:raise Refused('Duplicate additional evidence basename')
        names.add(name);data=read_json(path)
        if data.get('board_sha256')!=board_sha256:raise Refused('Stale additional source evidence: '+name)
        if 'passed'in data and data['passed']is not True:raise Refused('Failed additional source evidence: '+name)
        if 'native_sha256'in data and data['native_sha256']!=native_sha256:raise Refused('Additional evidence uses a different native export: '+name)
        rows.append({'path':path,'name':name,'sha256':sha256(path)})
    return rows

def prepare(compiled,out,release=False,refined_combined=False,extra_evidence=(),owner_released_board_sha=None):
    compiled=Path(compiled);out=Path(out)
    if out.exists():raise Refused('Loaded pilot output already exists')
    context=preflight(compiled/'freeze.json',compiled/'ledger-primary.json');primary=context['ledger']
    if release and owner_released_board_sha!=context['board_sha256']:
        raise Refused('Explicit owner release for this exact corrected source is required')
    extra=checked_extra_evidence(extra_evidence,context['board_sha256'],context['manifest']['files']['geometry']['sha256'])
    cases=select_cases(primary)
    networks,loops=select_scope(primary,cases,refined_combined)
    out.mkdir(parents=True);runtime=out/'solver-source';runtime.mkdir()
    freeze=copy.deepcopy(context['manifest']);freeze['tested_nets']=[n['net']for n in networks]
    freeze['source_stage']=context['manifest']['source_stage']+'; corrected primary and five-loop conditional diagnostic'
    freeze['numerical_execution_authorized']=release
    freeze['pilot_resource_limits']={'overall_wall_seconds':1500 if refined_combined else 1200,'address_space_MiB':4096,'heavy_processes':1,'BLAS_threads':1,'OpenMP_threads':1}
    for spec in freeze['files'].values():spec['path']=os.path.relpath((compiled/spec['path']).resolve(),out.resolve())
    if extra:
        (out/'source-evidence').mkdir()
        for row in extra:
            destination=out/'source-evidence'/row['name'];shutil.copyfile(row['path'],destination)
            if sha256(destination)!=row['sha256']:raise Refused('Additional source evidence changed during copying')
            freeze['files']['source_evidence_'+row['name']]={'path':'source-evidence/'+row['name'],'sha256':row['sha256']}
    for name in [*freeze['analysis_source_sha256'],'run_bounded_pilot.py']:
        shutil.copyfile(Path(__file__).parent/name,runtime/name);source_digest=sha256(runtime/name)
        if name in freeze['analysis_source_sha256']and source_digest!=freeze['analysis_source_sha256'][name]:raise Refused('Solver changed after compilation: '+name)
        freeze['files']['pilot_source_'+name]={'path':'solver-source/'+name,'sha256':source_digest}
    save(out/'freeze.json',freeze)
    ledger={**primary,'freeze_manifest_sha256':sha256(out/'freeze.json'),'case_family':'corrected-primary-and-VCAP','source_stage':freeze['source_stage'],'networks':networks,'cases':cases,'loops':loops,'unit_transfers':[]}
    save(out/'ledger.json',ledger);preflight(out/'freeze.json',out/'ledger.json')
    port_audit=audit_ports(context['files']['board'],context['files']['geometry'],out/'ledger.json',context['files']['connectivity'],context['files']['critical'])
    if not port_audit['passed']:raise Refused('Prepared finite-contact/alias/loop audit failed')
    save(out/'port-audit.json',port_audit)
    counts=primary['model_contract']['counts']
    plan={'schema':'f722-corrected-loaded-plan/v2','status':'PREPARED INPUTS; NO BOARD SOLVE',
      'board_sha256':context['board_sha256'],'freeze_sha256':sha256(out/'freeze.json'),
      'ledger_sha256':sha256(out/'ledger.json'),'numerical_execution_authorized':release,
      'model_revision':REVISION,'model_contract_sha256':digest(primary['model_contract']),
      'case_count':len(cases),'families':{'required':counts['required'],'illustrative':counts['illustrative']},
      'nets':counts['networks'],'contacts':counts['contacts'],'ground_contacts':counts['ground_contacts'],
      'mesh_spacings_mm':ledger['mesh_spacings_mm'],'loops':len(loops),'port_audit_sha256':sha256(out/'port-audit.json'),
      'extra_source_evidence_sha256':{row['name']:row['sha256']for row in extra},
      'ground_operator':'Fresh exact source/contact/grid identity; no historical cache or package-ground sharing assumption added.',
      'acceptance_scopes':'Actual supply pad/mode and DSM/ABC limits, numerical checks, VCAP loops and illustrations remain separately reported.',
      'limits':ledger['limits'],'resource_bounds':freeze['pilot_resource_limits'],
      'runtime_estimate':'Not yet measured for corrected305 cases and new contacts; caps remain1500s/4096MiB, with no silent coarsening.',
      'reuse':'Reuse only within the exact fresh network/contact/grid fingerprint. Case-count growth does not scale factorization cost linearly.',
      'limitations':['Conditional20mA branches/1ohm hot ferrites are engineering acceptance bounds, not manufacturer hot-DCR guarantees.',
                    'Current-polytope vertex coverage does not establish nonlinear interior extrema.',
                    'Package/exposed-pad current sharing, component temperature, AC, startup, VDDA tracking and signal-level gaps remain explicit.',
                    'Historical146/140/5532 corner postprocessing is disabled until regenerated.'],
      'cases':[{'name':c['name'],'case_definition_sha256':c['case_definition_sha256'],'scope':c['scope'],'parameters':c['parameters']}for c in cases],
      'prepare_source_sha256':sha256(__file__)}
    save(out/'pilot-plan.json',plan);return plan

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compiled',required=True);p.add_argument('--out',required=True);p.add_argument('--release',action='store_true')
    p.add_argument('--refined-combined',action='store_true',help='Reviewed corrected primary, .12/.09 grids and five VCAP loops; fresh dynamic contact identity')
    p.add_argument('--owner-released-board-sha',help='Required only for release; exact explicit routing-owner source SHA')
    p.add_argument('--evidence',action='append',default=[],help='Additional passed source-bound native receipt to copy and hash; repeat as needed')
    a=p.parse_args();r=prepare(a.compiled,a.out,a.release,a.refined_combined,a.evidence,a.owner_released_board_sha)
    print(json.dumps({k:r[k]for k in ['board_sha256','freeze_sha256','ledger_sha256','case_count','families','nets','contacts','loops','numerical_execution_authorized']}))

if __name__=='__main__':main()
