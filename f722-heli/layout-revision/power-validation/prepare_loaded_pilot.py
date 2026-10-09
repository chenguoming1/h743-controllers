#!/usr/bin/env python3
"""Prepare a bounded 73-case diagnostic from a newly compiled frozen source; no solve."""
import argparse,copy,json,os,shutil
from pathlib import Path
from copper_fem import Refused
from validate_static import preflight,read_json,sha256
from compile_power_ledger import check_cases,save

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

def prepare(compiled,out,release=False):
    compiled=Path(compiled);out=Path(out)
    if out.exists():raise Refused('Loaded pilot output already exists')
    context=preflight(compiled/'freeze.json',compiled/'ledger-primary.json');primary=context['ledger']
    cases=select_cases(primary['cases'])
    used={r[k]for case in cases for category in ['sources','resistors','loads','converters','probes','report_only_probes']for r in case.get(category,[])for k in ['p','n','in_p','in_n','out_p','out_n','sense_p','sense_n']if k in r}
    networks=[{'net':n['net'],'contacts':{k:v for k,v in n['contacts'].items()if k in used}}for n in primary['networks']]
    networks=[n for n in networks if n['contacts']]
    if any(len(n['contacts'])<2 for n in networks):raise Refused('One-port loaded network')
    check_cases(cases,networks)
    out.mkdir(parents=True);runtime=out/'solver-source';runtime.mkdir()
    freeze=copy.deepcopy(context['manifest']);freeze['tested_nets']=[n['net']for n in networks]
    freeze['source_stage']=context['manifest']['source_stage']+'; bounded 73-case loaded diagnostic'
    freeze['numerical_execution_authorized']=release
    freeze['pilot_resource_limits']={'overall_wall_seconds':1200,'address_space_MiB':4096,'heavy_processes':1,'BLAS_threads':1,'OpenMP_threads':1}
    for spec in freeze['files'].values():spec['path']=os.path.relpath((compiled/spec['path']).resolve(),out.resolve())
    for name in [*freeze['analysis_source_sha256'],'run_bounded_pilot.py']:
        shutil.copyfile(Path(__file__).parent/name,runtime/name);digest=sha256(runtime/name)
        if name in freeze['analysis_source_sha256']and digest!=freeze['analysis_source_sha256'][name]:raise Refused('Solver changed after compilation: '+name)
        freeze['files']['pilot_source_'+name]={'path':'solver-source/'+name,'sha256':digest}
    save(out/'freeze.json',freeze)
    ledger={**primary,'freeze_manifest_sha256':sha256(out/'freeze.json'),'case_family':'bounded-loaded-diagnostic','source_stage':freeze['source_stage'],'networks':networks,'cases':cases,'loops':[],'unit_transfers':[]}
    save(out/'ledger.json',ledger);preflight(out/'freeze.json',out/'ledger.json')
    plan={'schema':'f722-loaded-pilot-plan/v1','status':'PREPARED INPUTS; NO BOARD SOLVE','board_sha256':context['board_sha256'],
      'freeze_sha256':sha256(out/'freeze.json'),'ledger_sha256':sha256(out/'ledger.json'),'numerical_execution_authorized':release,
      'case_count':73,'families':{'5V_minimum_electronics_classic_capacity':60,'4p33V_USB_configuration':2,'7p4V_same_BEC_illustrations':11},
      'nets':len(networks),'contacts':sum(len(n['contacts'])for n in networks),'mesh_spacings_mm':ledger['mesh_spacings_mm'],
      'limits':ledger['limits'],'resource_bounds':freeze['pilot_resource_limits'],
      'estimated_runtime_minutes':[4,10],'estimated_peak_memory_GiB':[1.3,2.0],
      'estimate_basis':'Measured six-port GND pilot: fine mesh558404 raw nodes/132244 equations/741648 triangles,122.2 s overall,1.22GB recorded RSS. More finite contacts require fresh matrices; runtime/memory estimates are not guarantees.',
      'reuse':'Build/checkpoint one matrix per exact network/contact/grid identity. Reuse its factor and port matrix across all selected cases; rebuild loaded fields from the same cached identity. No VCAP six-port GND cache is reused for a changed contact set.',
      'source_contact_assumptions':'All60 5.0V cases disconnect servo loads. USB4.33V cases disconnect external DSM, ABC and servos. Servo11 cases use7.4V and explicit illustrative finite four-conductor profiles; no measured harness is invented.',
      'servo_pairs':SERVO_PAIRS,'servo_allocation':'mcu_vdd19 is a fixed diagnostic illustration, not a proved weakest servo allocation',
      'threshold_scope':'Retain conditional classic DSM3.1394..3.465V and ABC4.8V pad floors, U9 operating3..17V, separate4.3V accuracy-condition headroom reports, local positive/return pads and finite contact resistors. Capacity DSM0.50A has no inherited classic accuracy guarantee. CORE sink voltage is reported without inventing a universal component floor.',
      'not_completed_by_this_subset':['12.6V and upper-output review','75/85/95% efficiency and90/120/150mOhm U8 sensitivities','line/load/leakage allowance sweeps','all same-BEC/feed/servo/return combinations','weakest-allocation dependent slices','measured harness/source/thermal/AC/flight qualification','final routed-board analysis after later drills/fills'],
      'cases':[{'name':c['name'],'case_definition_sha256':c['case_definition_sha256'],'scope':c['scope'],'parameters':c['parameters']}for c in cases],
      'prepare_source_sha256':sha256(__file__)}
    save(out/'pilot-plan.json',plan);return plan

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compiled',required=True);p.add_argument('--out',required=True);p.add_argument('--release',action='store_true')
    a=p.parse_args();r=prepare(a.compiled,a.out,a.release)
    print(json.dumps({k:r[k]for k in ['board_sha256','freeze_sha256','ledger_sha256','case_count','families','nets','contacts','numerical_execution_authorized']}))

if __name__=='__main__':main()
