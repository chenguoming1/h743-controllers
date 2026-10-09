#!/usr/bin/env python3
"""Materialize dependent sensitivities only from bound numerical baseline ranks."""
import argparse
import copy
import math
from pathlib import Path
from copper_fem import Refused
from validate_static import read_json,sha256,preflight
from compile_power_ledger import materialize,check_cases,save,stamp_cases
from power_case_model import case_factory


def metrics(row):
    values={}
    for p in row.get('probes',[]):
        if 'minimum_V'in p:values[p['name']+':lower']=p['voltage_V']-p['minimum_V']
        if 'maximum_V'in p:values[p['name']+':upper']=p['maximum_V']-p['voltage_V']
    for p in row.get('report_only_probes',[]):
        values[p['name']+':report_only']=p['voltage_V']-p.get('comparison_floor_V',0)
    if not values or any(not math.isfinite(v)for v in values.values()):
        raise Refused('Missing/nonfinite ranking metrics')
    return values


def select_vertices(candidates,results):
    if any(c['name']not in results for c in candidates):raise Refused('Baseline ranking is incomplete')
    rows=[(c,metrics(results[c['name']]))for c in candidates]
    if any(set(m)!=set(rows[0][1])for _,m in rows):raise Refused('Ranking metric sets differ')
    selected={}
    for metric in rows[0][1]:
        c,values=min(rows,key=lambda item:(item[1][metric],item[0]['parameters']['allocation_vertex']))
        vertex=c['parameters']['allocation_vertex']
        selected.setdefault(vertex,[]).append({'metric':metric,'value_V':values[metric],'baseline_case':c['name']})
    return selected


def activate(compiled,result_path,out):
    compiled=Path(compiled);out=Path(out)
    if out.exists():raise Refused('Ranked output already exists')
    receipt=read_json(compiled/'compile-receipt.json');result_hash=sha256(result_path);result=read_json(result_path)
    baseline=read_json(compiled/'ledger-baseline.json');primary=read_json(compiled/'ledger-primary.json')
    context=preflight(compiled/'freeze.json',compiled/'ledger-primary.json')
    if context['manifest'].get('numerical_execution_authorized')is not True:
        raise Refused('No released numerical run can belong to this disabled freeze')
    if result.get('schema')!='f722-scoped-static-result/v1' or result.get('board_sha256')!=receipt['board_sha256']:
        raise Refused('Not a numerical result for this exact source')
    if result.get('freeze_sha256')!=sha256(compiled/'freeze.json'):
        raise Refused('Ranking result belongs to another frozen evidence set')
    known={receipt['families'][x]['ledger_sha256']for x in ['baseline','primary']}
    if result.get('ledger_sha256')not in known:raise Refused('Ranking result is not bound to the compiled baseline or primary ledger')
    for name in ['baseline','primary']:
        if sha256(compiled/('ledger-'+name+'.json'))!=receipt['families'][name]['ledger_sha256']:
            raise Refused('Compiled ledger changed after its receipt')
    if len(result.get('runs',[]))<2 or not result.get('impedance_sensitivity')or not all(x.get('pass')is True for x in result['impedance_sensitivity']):
        raise Refused('Ranking requires successful native mesh sensitivity evidence')
    if not result.get('voltage_margin_checks') or any(x['change_V']>baseline['convergence']['absolute_voltage_V']for x in result['voltage_margin_checks']):
        raise Refused('Voltage sensitivity is inadequate for allocation ranking')
    if [r['spacing_mm']for r in result['runs']][-2:]!=baseline['mesh_spacings_mm'][-2:]:
        raise Refused('Ranking result used different numerical grids')
    final_rows=result['runs'][-1]['cases']
    results={r['case']:r for r in final_rows}
    if len(results)!=len(final_rows):raise Refused('Duplicate numerical result case names')
    definitions={c['name']:c['case_definition_sha256']for c in primary['cases']}
    for name,expected in context['manifest'].get('analysis_source_sha256',{}).items():
        if name in ['copper_fem.py','dc_circuit.py','validate_static.py']and result.get('software',{}).get('source_sha256',{}).get(name)!=expected:
            raise Refused('Ranking solver source differs from the compiled source')
    for row in final_rows:
        if row['case']not in definitions or row.get('case_definition_sha256')!=definitions[row['case']]:
            raise Refused('Numerical case is not bound to its resolved definition')
        residual=row.get('equation_residual_max',float('inf'))
        if not math.isfinite(residual)or residual>1e-7:
            raise Refused('Ranking requires conserved circuit results')
    if not {c['name']for c in baseline['cases']}<=set(results):raise Refused('Not all baseline allocations were solved')
    plan=read_json(compiled/'input/case-plan.json');deferred=read_json(compiled/'deferred-case-plan.json')
    if sha256(compiled/'deferred-case-plan.json')!=receipt.get('deferred_case_plan_sha256'):
        raise Refused('Deferred case plan changed after compilation')
    if deferred['freeze_sha256']!=sha256(compiled/'freeze.json')or deferred['baseline_ledger_sha256']!=sha256(compiled/'ledger-baseline.json'):
        raise Refused('Deferred definitions are stale')
    make_case,_=case_factory(plan);vertices=plan['proposed_case_dimensions']['electronics_allocation_vertices']
    abc={'AB':['J9','J10'],'AC':['J9','J11'],'BC':['J10','J11'],'NONE':[]}
    cases=[];rankings=[]
    for spec in deferred['slices']:
        candidates=[c for c in baseline['cases']if c['scope']==spec['scope']and c['supply']==spec['supply']
                    and c['parameters']['input_at_defined_source_V']==spec['vin']and c['parameters']['ABC_ports']==abc[spec['pair']]]
        if len(candidates)!=len(vertices):raise Refused('Expected every declared baseline vertex in a ranking context')
        selected=select_vertices(candidates,results)
        for vertex,reasons in selected.items():
            c=materialize(make_case(spec['scope'],spec['vin'],spec['pair'],vertex,spec['profile'],supply=spec['supply']),vertices)
            c['allocation_basis']={'type':'weakest sampled baseline metric','source_result_sha256':result_hash,'reasons':reasons}
            c['assumptions'].append('Selected from baseline ranks only; expand vertices if this sensitivity changes ranking or leaves unresolved margin.')
            cases.append(c)
        rankings.append({'context':spec,'selected_vertices':selected})
    upper=read_json(compiled/'ledger-upper.json');upper_pending=[]
    for pair in ['NONE','AB','AC','BC']:
        candidates=[c for c in upper['cases']if c['parameters']['ABC_ports']==abc[pair]]
        if not {c['name']for c in candidates}<=set(results):
            upper_pending.append(pair);continue
        selected=select_vertices(candidates,results)
        for error in deferred['upper_additional_errors']:
            for vertex,reasons in selected.items():
                original=next(c for c in candidates if c['parameters']['allocation_vertex']==vertex)
                c=copy.deepcopy(original);c['name']+='__added_upper_'+str(int(100*error))+'pct'
                for converter in c['converters']:converter['voltage_V']*=1+error
                c['parameters']['additional_output_error_fraction']=error
                c['regulation_scope']['additional_output_error_fraction']=error
                c['allocation_basis']={'type':'weakest sampled upper baseline metric','source_result_sha256':result_hash,'reasons':reasons}
                cases.append(c)
    check_cases(cases,primary['networks'])
    stamp_cases(cases)
    ledger={**primary,'case_family':'ranked-dependent-sensitivities','cases':cases,
             'ranking_source_sha256':result_hash,'ranking_result':str(Path(result_path).name)}
    out.mkdir(parents=True);save(out/'ledger-ranked.json',ledger)
    preflight(compiled/'freeze.json',out/'ledger-ranked.json')
    if sha256(result_path)!=result_hash:raise Refused('Numerical ranking input changed during compilation')
    save(out/'ranking-receipt.json',{'status':'MATERIALIZED FROM NUMERICAL BASELINE; NO NEW SOLVE',
       'board_sha256':receipt['board_sha256'],'freeze_sha256':sha256(compiled/'freeze.json'),
       'ledger_sha256':sha256(out/'ledger-ranked.json'),'source_result_sha256':result_hash,
       'ranking_compiler_sha256':sha256(Path(__file__)),
       'cases':len(cases),'rankings':rankings,'upper_contexts_still_deferred':upper_pending,
       'scope':'Weakest among declared baseline vertices; no universal combined-corner or measured-harness guarantee'})
    return len(cases)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['compiled','result','out']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(activate(a.compiled,a.result,a.out))


if __name__=='__main__':main()
