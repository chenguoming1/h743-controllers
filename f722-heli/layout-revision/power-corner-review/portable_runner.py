#!/usr/bin/env python3
"""Verify/replay sealed F722 port circuits. Never build a mesh or a loaded field."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import time

from portable_model import (ROOT,PLAN,REFERENCE,Refused,allowance,apply_profile,bases,
    budget_margin,budget_profile,canonical,check_cases,compact_pair,endpoint_cases,
    ensure_generator_unchanged,extrema,profile_summary,profiles,read,resource_guard,
    save,scenario,solve_pair)

START_HASH=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def verify_manifest():
    manifest=read(ROOT/'manifest.json')
    for relative,spec in manifest['files'].items():
        path=ROOT/relative
        if path.resolve().is_relative_to(ROOT) is not True:raise Refused('Manifest path escapes packet')
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=spec['sha256'] or len(data)!=spec['bytes']:
            raise Refused('Changed or truncated packet file: '+relative)
    identities=read(ROOT/'source-identities.json')
    for key in ['original_solver','original_case_factory']:
        spec=identities[key]
        if hashlib.sha256((ROOT/spec['file']).read_bytes()).hexdigest()!=spec['sha256']:
            raise Refused('Original circuit/case source identity differs')
    return dict(manifest_sha256=hashlib.sha256((ROOT/'manifest.json').read_bytes()).hexdigest(),
                verified_file_count=len(manifest['files']),
                independently_verified_FEM=False,
                meaning='File integrity and sealed-input trust boundary only; omitted native/FEM/archive evidence is not re-created.')


def generated(packet):
    groups=bases(read(PLAN),read(REFERENCE/'ledger.json'))
    cases=[apply_profile(c,p) for group,plist in zip(groups,profiles()) for p in plist for c in group]
    check_cases(cases,packet['networks'])
    expected=read(ROOT/'expected-results.json')['sensitivity']
    if len(cases)!=expected['case_count'] or canonical(cases)!=expected['case_definitions_sha256']:
        raise Refused('Sensitivity case definitions differ from original ledger')
    return cases


def sampled(packet):
    cases={c['name']:c for c in generated(packet)}
    expected=read(ROOT/'expected-results.json');tolerance=expected['comparison_absolute_voltage_V']
    rows=[]
    for original in expected['sampled_cases']:
        c=cases[original['case']]
        if c['case_definition_sha256']!=original['case_definition_sha256']:raise Refused('Sample definition differs')
        result=compact_pair(c,packet);largest=0.
        for category in ['voltage_checks','report_only_grid_checks']:
            actual=result[category];prior=original[category]
            if [x['probe'] for x in actual]!=[x['probe'] for x in prior]:raise Refused('Sample probe set differs')
            for a,b in zip(actual,prior):
                for field in ['fine_voltage_V','change_V','numerical_guard_V','guarded_margin_V','guarded_comparison_headroom_V']:
                    if field in b:largest=max(largest,abs(a[field]-b[field]))
                for field in ['pass','voltage_grid_pass','acceptance_limit']:
                    if field in b and a[field]!=b[field]:raise Refused('Sample decision differs')
        if largest>tolerance:raise Refused('Sample voltage replay differs beyond comparison tolerance')
        rows.append(dict(case=c['name'],maximum_numeric_difference_V=largest,
                         exact_original_result_hash_match=canonical(result)==original['original_compact_result_sha256']))
    return dict(case_definition_count=len(cases),sampled_case_count=len(rows),paired_circuit_solves=2*len(rows),
                all_sample_comparisons_pass=True,comparison_tolerance_V=tolerance,checks=rows)


def endpoints(packet):
    cases=endpoint_cases(read(PLAN));expected=read(ROOT/'expected-results.json')['endpoint']
    if canonical(cases)!=expected['case_definitions_sha256']:raise Refused('Endpoint definitions differ')
    results=[solve_pair(c,packet) for c in cases]
    if sum(not r['port_voltage_checks_pass'] for r in results)!=expected['failed_case_count']:
        raise Refused('Endpoint voltage decisions differ')
    if not all(p['voltage_grid_pass'] for r in results for k in ['voltage_checks','report_only_grid_checks'] for p in r[k]):
        raise Refused('Endpoint report/acceptance grid check failed')
    actual_extrema=extrema(cases,results);largest=0.
    for key,row in expected['extrema'].items():
        for side in ['minimum','maximum']:
            largest=max(largest,abs(actual_extrema[key][side]['fine_voltage_V']-row[side]['fine_voltage_V']))
    if largest>1e-10:raise Refused('Endpoint extrema differ beyond replay tolerance')
    return dict(case_count=len(cases),paired_circuit_solves=2*len(cases),all_port_voltage_checks_pass=True,
                all_acceptance_and_report_grid_checks_pass=True,maximum_extremum_replay_difference_V=largest,
                exact_original_result_hash_match=canonical(results)==expected['results_sha256'])


def sweep(packet):
    cases=generated(packet);results=[compact_pair(c,packet) for c in cases]
    summaries=profile_summary(cases,results);expected=read(ROOT/'expected-results.json')['sensitivity']
    failed_case_count=sum(not r['port_voltage_checks_pass'] for r in results)
    if failed_case_count!=expected['failed_case_count']:
        raise Refused('Failed voltage case count differs')
    compact={}
    for name,p in summaries.items():
        prior=expected['profiles'][name]
        for key in ['cases','voltage_pass','all_grid_pass']:
            if p[key]!=prior[key]:raise Refused('Sensitivity profile decision differs: '+name)
        if len(p['failed_checks'])!=prior['failed_check_count']:raise Refused('Failed stress count differs')
        if abs(p['minimum_guarded_margin_V']-prior['minimum_guarded_margin_V'])>1e-10:
            raise Refused('Sensitivity profile margin differs: '+name)
        compact[name]={k:p[k] for k in ['cases','voltage_pass','all_grid_pass','minimum_guarded_margin_V','limiting_case','limiting_probe','minimum_USB_current_headroom_A']}
        compact[name]['failed_check_count']=len(p['failed_checks'])
    return dict(case_count=len(cases),paired_circuit_solves=2*len(cases),
                failed_voltage_case_count=failed_case_count,
                all_acceptance_and_report_grid_checks_pass=all(r['all_report_and_acceptance_grid_pass'] for r in results),
                original_profile_summaries_reproduced=True,profiles=compact)


def budget_setup(environment,target):
    lower,upper,_=bases(read(PLAN),read(REFERENCE/'ledger.json'))
    summary=read(ROOT/'results-summary.json')
    evidence=summary[environment+'_allowances'][target]
    cases=upper if target=='u9_upper_error' else lower
    if environment=='combined':
        high=target=='u9_upper_error'
        cases=[apply_profile(c,scenario(('held_upper_eta' if high else 'held_eta')+f'{a}_{b}',
                                       **({'high':True,'ifb':1e-7} if high else {}),eta6=a/100,eta9=b/100))
               for a in [75,85,95] for b in [75,85,95] for c in cases]
    return cases,evidence


def budget_check(packet,environment,target):
    cases,evidence=budget_setup(environment,target);base=evidence['held_profile']
    checks=[]
    for c in cases:
        p=budget_profile({**c.get('sensitivity_definition',{}),**base},target,evidence['safe_value'])
        result=compact_pair(apply_profile(c,p),packet);margin=budget_margin(result,target)
        if margin['margin_V']<0:raise Refused('Saved safe bracket no longer passes: '+c['name'])
        checks.append(margin)
    c=next(c for c in cases if c['name']==evidence['boundary_case'])
    p=budget_profile({**c.get('sensitivity_definition',{}),**base},target,evidence['failed_value'])
    result=compact_pair(apply_profile(c,p),packet);failure=budget_margin(result,target)
    if failure['margin_V']>=0 or failure['probe']!=evidence['boundary_reason']:
        raise Refused('Saved failed bracket no longer reproduces')
    return dict(environment=environment,target=target,complete_safe_contexts=len(cases),
                saved_safe_value=evidence['safe_value'],saved_failed_value=evidence['failed_value'],
                safe_contexts_pass=True,failed_bracket_reproduced=True,boundary_reason=failure['probe'],
                physical_boundary_resolved=evidence['physical_boundary_resolved'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['verify','sample','endpoints','sweep','budget-check','budget-search'])
    parser.add_argument('--environment',choices=['initial','combined'],default='combined')
    parser.add_argument('--target',choices=['u7','u8_accuracy','u8_operating','u6_error','u9_error','joint_error','u9_upper_error'],default='u7')
    parser.add_argument('--out',type=Path)
    args=parser.parse_args();resource_guard(300);started=time.monotonic()
    verification=verify_manifest();packet=read(ROOT/'inputs/verified-ports.json')
    if args.mode=='verify':result=verification
    elif args.mode=='sample':result=sampled(packet)
    elif args.mode=='endpoints':result=endpoints(packet)
    elif args.mode=='sweep':result=sweep(packet)
    elif args.mode=='budget-check':result=budget_check(packet,args.environment,args.target)
    else:
        cases,evidence=budget_setup(args.environment,args.target)
        result=allowance(cases,packet,evidence['held_profile'],args.target)
    ensure_generator_unchanged()
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=START_HASH:raise Refused('Runner changed after launch')
    output=dict(mode=args.mode,wall_seconds=time.monotonic()-started,packet_verification=verification,result=result,
                new_meshes=0,new_loaded_fields=0,loaded_field_acceptance=None,
                applicability='Historical source19 circuit guidance; preserved candidate24 receipt is separate. Candidate26 and changed geometry excluded.',
                resource_limits=dict(wall_seconds=300,address_space_GiB=4,numerical_threads=1))
    if args.out:
        if args.out.exists():raise Refused('Preserve existing output')
        save(args.out,output)
    print(json.dumps(output,allow_nan=False))


if __name__=='__main__':main()
