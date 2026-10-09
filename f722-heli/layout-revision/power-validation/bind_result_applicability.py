#!/usr/bin/env python3
"""Bind an archived conditional result to exactly equal modeled inputs; no solve."""
import argparse
import json
from pathlib import Path
from compare_power_geometry import compare,digest
from copper_fem import Refused
from validate_static import preflight,sha256
from summarize_combined_pilot import classify_scopes


JOB_KEYS=['material','mesh_spacings_mm','convergence','limits','networks','unit_transfers','loops','cases','assumption_record_sha256']


def compare_jobs(reference,other):
    rows={key:{'identical':reference[key]==other[key],'reference_sha256':digest(reference[key]),
               'compared_sha256':digest(other[key])}for key in JOB_KEYS}
    if not all(row['identical']for row in rows.values()):raise Refused('Changed circuit/material/contact/grid/acceptance job inputs')
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['reference_freeze','reference_ledger','result','target_freeze','target_ledger','out']:
        p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():p.error('Preserve existing applicability receipt')
    reference=preflight(args.reference_freeze,args.reference_ledger)
    target=preflight(args.target_freeze,args.target_ledger)
    result=json.loads(args.result.read_text())
    if result.get('status')=='REFUSED':raise Refused('Incomplete result cannot establish complete scope applicability')
    for key in ['board_sha256','freeze_sha256','ledger_sha256']:
        if result[key]!=reference[key]:raise Refused('Archived result/source identity mismatch')
    jobs=compare_jobs(reference['ledger'],target['ledger'])
    a=reference['manifest'];b=target['manifest']
    if a['analysis_source_sha256']!=b['analysis_source_sha256']:raise Refused('Runtime identity differs')
    if a['compiler_source_sha256']!=b['compiler_source_sha256']:raise Refused('Case compiler identity differs')
    if a['scope']!=b['scope']:raise Refused('Cannot transfer a result to another qualification scope')
    if a['files']['parts']['sha256']!=b['files']['parts']['sha256']:raise Refused('Selected parts differ')
    geometry=compare(reference['files']['geometry'],target['files']['geometry'],
                     reference['files']['board'],target['files']['board'],args.reference_ledger)
    if not geometry['exact_structured_inputs_identical']:raise Refused('Modeled native geometry differs')
    scopes=classify_scopes(result,reference['ledger'])
    receipt={'schema':'f722-exact-result-applicability/v1','passed':True,
      'meaning':'Archived numerical result applies to the exact modeled power/copper/return/loop job on the compared source. Original result identity remains unchanged; no new solve or final-board qualification.',
      'original_numerical_board_sha256':reference['board_sha256'],'applicable_board_sha256':target['board_sha256'],
      'original_native_sha256':a['files']['geometry']['sha256'],'applicable_native_sha256':b['files']['geometry']['sha256'],
      'actual_result_sha256':sha256(args.result),'original_freeze_sha256':reference['freeze_sha256'],'original_ledger_sha256':reference['ledger_sha256'],
      'applicability_freeze_sha256':target['freeze_sha256'],'applicability_ledger_sha256':target['ledger_sha256'],
      'job_identity_checks':jobs,'runtime_source_sha256':a['analysis_source_sha256'],'compiler_source_sha256':a['compiler_source_sha256'],
      'selected_parts_sha256':a['files']['parts']['sha256'],'exact_geometry_comparison':geometry,
      'scope_decisions':{key:value for key,value in scopes.items()if not isinstance(value,list)},
      'failed_illustrative_checks':[row for row in scopes['illustrative_voltage_checks']if not row['pass']],
      'required_case_count':scopes['required_case_count'],'illustrative_case_count':scopes['illustrative_case_count'],
      'VCAP_loop_count':scopes['VCAP_loop_count'],'all_guards_and_case_definitions_unchanged':True,
      'original_result_file_modified':False,'numeric_cache_transferred':False,'new_numerical_run':False,
      'native_DRC_scopes':{'original':reference['drc'],'applicable':target['drc']},
      'conditional_envelope':result['limitations']+[
        'Only the exact enumerated job applies. Broader source/circuit corners and final routed-board review remain incomplete.',
        'The original overallfalse is retained: one overloaded same-BEC lost-feed illustration fails four servo floors.',
        'Measured harness remains unset; uniform copper temperature/material and off-condition device terms remain modeled assumptions.'],
      'binding_script_sha256':sha256(__file__)}
    args.out.write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'passed':True,'receipt_sha256':sha256(args.out),'original_numerical_board_sha256':reference['board_sha256'],
      'applicable_board_sha256':target['board_sha256'],'actual_result_sha256':receipt['actual_result_sha256'],
      'scope_decisions':receipt['scope_decisions']}))


if __name__=='__main__':main()
