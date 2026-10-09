#!/usr/bin/env python3
"""Prepare a bounded 73-case diagnostic from a newly compiled frozen source; no solve."""
import argparse,copy,json,os,shutil
from pathlib import Path
from copper_fem import Refused
from validate_static import preflight,read_json,sha256
from compile_power_ledger import check_cases,save
from audit_native_ports import audit_ports

SERVO_PAIRS=[('moderate','equal20m'),('moderate','paired_J8_weak'),
 ('moderate','crossed_J6_positive_strong'),('moderate','J6_feed_lost'),('moderate','J8_feed_lost'),
 ('heavy_S1_905X','equal40m'),('heavy_S2_905X','paired_J8_weak'),('heavy_S3_905X','crossed_J6_positive_strong'),
 ('all_cyclic_805X','equal40m'),('all_cyclic_905X','paired_J8_weak'),('all_cyclic_905X','J6_feed_lost')]

def select_cases(all_cases):
    minimum=[c for c in all_cases if c['scope']in ['classic','capacity']and c['supply']=='BEC'and c['parameters']['input_at_defined_source_V']==5.]
    usb=[c for c in all_cases if c['scope']=='usb_configuration'and c['parameters']['input_at_defined_source_V']==4.33 and c['parameters']['allocation_vertex']in ['mcu_vdd19','flash']]
    servo=[]
    for profile,feed in SERVO_PAIRS:
        rows=[c for c in all_cases if c['scope']=='same_BEC_illustrative'and c['parameters']['servo_profile']==profile and c['parameters']['feed_profile']==feed and c['parameters']['allocation_vertex']=='mcu_vdd19'and c['parameters']['DSM_A']==(.02 if profile=='moderate'else .50)]
        if len(rows)!=1:raise Refused('Missing or duplicate exact servo diagnostic selector: '+profile+'/'+feed)
        servo.extend(rows)
    if (len(minimum),len(usb),len(servo))!=(60,2,11):raise Refused('Loaded diagnostic selection changed; review scope explicitly')
    if len({c['name']for c in minimum+usb+servo})!=73:raise Refused('Duplicate selected diagnostic case')
    for case in minimum:
        if any(load['name'].endswith('_servo_illustration')for load in case['loads']):raise Refused('Incompatible servo load in 5 V diagnostic')
    for case in usb:
        if case['parameters']['DSM_A']or case['parameters']['ABC_ports']or any(load['name'].endswith('_servo_illustration')for load in case['loads']):raise Refused('External load in USB-only diagnostic')
    return copy.deepcopy(minimum+usb+servo)

def select_scope(primary,cases,refined_combined=False):
    loops=copy.deepcopy(primary.get('loops',[]))if refined_combined else []
    if refined_combined:
        expected=[{'name':'VCAP_copper_to_'+pad,'maximum_ohm':.035,
                   'legs':[{'net':'VCAP','source':'U1.30','sink':'R16.1'},
                           {'net':'VCAP_CAP','source':'R16.2','sink':'C7.1'},
                           {'net':'GND','source':'C7.2','sink':pad}]}for pad in ['U1.12','U1.18','U1.31','U1.47','U1.63']]
        if [{k:loop[k]for k in ['name','maximum_ohm','legs']}for loop in loops]!=expected:
            raise Refused('The refined combined scope requires the five exact 35mOhm VCAP copper loops')
        if primary['mesh_spacings_mm']!=[.12,.09]:raise Refused('Refined combined scope requires the approved .12/.09 grids')
    used={r[k]for case in cases for category in ['sources','resistors','loads','converters','probes','report_only_probes']for r in case.get(category,[])for k in ['p','n','in_p','in_n','out_p','out_n','sense_p','sense_n']if k in r}
    used.update(key for loop in loops for leg in loop['legs']for key in [leg['source'],leg['sink']])
    networks=[{'net':n['net'],'contacts':{k:v for k,v in n['contacts'].items()if k in used}}for n in primary['networks']]
    networks=[n for n in networks if n['contacts']]
    if any(len(n['contacts'])<2 for n in networks):raise Refused('One-port loaded network')
    if refined_combined and (len(networks),sum(len(n['contacts'])for n in networks),len(next(n['contacts']for n in networks if n['net']=='GND')))!=(13,99,41):
        raise Refused('Changed refined network/contact scope requires review')
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

def prepare(compiled,out,release=False,refined_combined=False,extra_evidence=()):
    compiled=Path(compiled);out=Path(out)
    if out.exists():raise Refused('Loaded pilot output already exists')
    context=preflight(compiled/'freeze.json',compiled/'ledger-primary.json');primary=context['ledger']
    extra=checked_extra_evidence(extra_evidence,context['board_sha256'],context['manifest']['files']['geometry']['sha256'])
    cases=select_cases(primary['cases'])
    networks,loops=select_scope(primary,cases,refined_combined)
    out.mkdir(parents=True);runtime=out/'solver-source';runtime.mkdir()
    freeze=copy.deepcopy(context['manifest']);freeze['tested_nets']=[n['net']for n in networks]
    freeze['source_stage']=context['manifest']['source_stage']+('; refined 73-case and five-loop diagnostic'if refined_combined else '; bounded 73-case loaded diagnostic')
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
        shutil.copyfile(Path(__file__).parent/name,runtime/name);digest=sha256(runtime/name)
        if name in freeze['analysis_source_sha256']and digest!=freeze['analysis_source_sha256'][name]:raise Refused('Solver changed after compilation: '+name)
        freeze['files']['pilot_source_'+name]={'path':'solver-source/'+name,'sha256':digest}
    save(out/'freeze.json',freeze)
    ledger={**primary,'freeze_manifest_sha256':sha256(out/'freeze.json'),'case_family':'bounded-loaded-and-VCAP-diagnostic'if refined_combined else 'bounded-loaded-diagnostic','source_stage':freeze['source_stage'],'networks':networks,'cases':cases,'loops':loops,'unit_transfers':[]}
    save(out/'ledger.json',ledger);preflight(out/'freeze.json',out/'ledger.json')
    port_audit=audit_ports(context['files']['board'],context['files']['geometry'],out/'ledger.json',context['files']['connectivity'],context['files']['critical'])
    if not port_audit['passed']:raise Refused('Prepared finite-contact/alias/loop audit failed')
    save(out/'port-audit.json',port_audit)
    plan={'schema':'f722-loaded-pilot-plan/v1','status':'PREPARED INPUTS; NO BOARD SOLVE','board_sha256':context['board_sha256'],
      'freeze_sha256':sha256(out/'freeze.json'),'ledger_sha256':sha256(out/'ledger.json'),'numerical_execution_authorized':release,
      'case_count':73,'families':{'5V_minimum_electronics_classic_capacity':60,'4p33V_USB_configuration':2,'7p4V_same_BEC_illustrations':11},
      'nets':len(networks),'contacts':sum(len(n['contacts'])for n in networks),'mesh_spacings_mm':ledger['mesh_spacings_mm'],
      'loops':len(loops),'port_audit_sha256':sha256(out/'port-audit.json'),
      'extra_source_evidence_sha256':{row['name']:row['sha256']for row in extra},
      'ground_operator':'Fresh 41-contact operator including ideal finite C7.2; incompatible with the old40-contact loaded cache. Shared only within this exact source/contact/grid identity.'if refined_combined else '40-contact loaded GND operator; VCAP loops excluded.',
      'acceptance_scopes':'Loaded voltage and VCAP copper loop checks must be reported separately; overall failure does not erase individual scoped results.',
      'limits':ledger['limits'],'resource_bounds':freeze['pilot_resource_limits'],
      'estimated_runtime_minutes':[17.86,23.33]if refined_combined else [4,10],'estimated_peak_memory_GiB':[2.12,3.16]if refined_combined else [1.3,2.0],
      'estimate_basis':'Measured six-port GND pilot: fine mesh558404 raw nodes/132244 equations/741648 triangles,122.2 s overall,1.22GB recorded RSS. More finite contacts require fresh matrices; runtime/memory estimates are not guarantees.',
      'reuse':'Build/checkpoint one matrix per exact network/contact/grid identity. Reuse its factor and port matrix across all selected cases; rebuild loaded fields from the same cached identity. No VCAP six-port GND cache is reused for a changed contact set.',
      'source_contact_assumptions':'All60 5.0V cases disconnect servo loads. USB4.33V cases disconnect external DSM, ABC and servos. Servo11 cases use7.4V and explicit illustrative finite four-conductor profiles; no measured harness is invented.',
      'servo_pairs':SERVO_PAIRS,'servo_allocation':'mcu_vdd19 is a fixed diagnostic illustration, not a proved weakest servo allocation',
      'threshold_scope':'Retain conditional classic DSM3.1394..3.465V and ABC4.8V pad floors, U9 operating3..17V, separate4.3V accuracy-condition headroom reports, local positive/return pads and finite contact resistors. Capacity DSM0.50A has no inherited classic accuracy guarantee. CORE sink voltage is reported without inventing a universal component floor.',
      'not_completed_by_this_subset':['12.6V and upper-output review','75/85/95% efficiency and90/120/150mOhm U8 sensitivities','line/load/leakage allowance sweeps','all same-BEC/feed/servo/return combinations','weakest-allocation dependent slices','measured harness/source/thermal/AC/flight qualification','final routed-board analysis after later drills/fills'],
      'cases':[{'name':c['name'],'case_definition_sha256':c['case_definition_sha256'],'scope':c['scope'],'parameters':c['parameters']}for c in cases],
      'prepare_source_sha256':sha256(__file__)}
    if refined_combined:
        plan['estimate_basis']='Read-only extrapolation from completed .20/.15 loaded meshes, keeping actual contours: .12/.09 forecast plus30s VCAP allowance; upper time adds25%+60s. Memory upper is an explicit planning stress, not measured virtual-memory usage. No convergence or resource guarantee.'
        plan['reuse']='Build the new41-contact GND operator once per grid; share its live mesh for loops and its source-bound checkpoint/factor for loaded fields. Old40-contact and historical VCAP caches are incompatible.'
    save(out/'pilot-plan.json',plan);return plan

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compiled',required=True);p.add_argument('--out',required=True);p.add_argument('--release',action='store_true')
    p.add_argument('--refined-combined',action='store_true',help='Approved .12/.09,73-case,five-loop scope;25-minute cap, fresh41-contact GND operator')
    p.add_argument('--evidence',action='append',default=[],help='Additional passed source-bound native receipt to copy and hash; repeat as needed')
    a=p.parse_args();r=prepare(a.compiled,a.out,a.release,a.refined_combined,a.evidence)
    print(json.dumps({k:r[k]for k in ['board_sha256','freeze_sha256','ledger_sha256','case_count','families','nets','contacts','loops','numerical_execution_authorized']}))

if __name__=='__main__':main()
