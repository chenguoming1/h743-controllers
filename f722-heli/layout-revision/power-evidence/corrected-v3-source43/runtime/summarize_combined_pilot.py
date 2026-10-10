#!/usr/bin/env python3
"""Classify the required voltage, VCAP, numerical and illustrative scopes separately."""
import argparse
import json
from pathlib import Path
from summarize_loaded_pilot import summarize as summarize_loaded,sha,canonical
from report_actual_sinks import extract as actual_sink_report
from model_contract import check_ledger


def classify_scopes(result,ledger):
    cases={c['name']:c for c in ledger['cases']}
    required={name for name,c in cases.items()if c['scope']in ['classic','capacity','usb_configuration']}
    illustrations={name for name,c in cases.items()if c['scope']=='same_BEC_illustrative'}
    if required|illustrations!=set(cases):raise ValueError('Unclassified case scope')
    if result.get('status')=='REFUSED' or len(result.get('runs',[]))!=len(ledger['mesh_spacings_mm']):
        return {'required_scope_acceptance':None,'VCAP_acceptance':None,'numerical_acceptance':False,
          'illustrative_observations_complete':False,'meaning':'Incomplete numerical work cannot qualify any complete two-grid scope.'}
    assert [r['spacing_mm']for r in result['runs']]==ledger['mesh_spacings_mm']
    for run in result['runs']:assert {c['case']for c in run['cases']}==set(cases)
    required_nets={net for name in required for net in cases[name]['nets']}
    loop_names={loop['name']for loop in ledger.get('loops',[])}
    loop_nets={leg['net']for loop in ledger.get('loops',[])for leg in loop['legs']}
    impedance={row['net']:row for row in result['impedance_sensitivity']}
    assert required_nets|loop_nets<=set(impedance)
    margins=result['voltage_margin_checks'];tolerance=ledger['convergence']['absolute_voltage_V']
    def rows(scope):return [r for r in margins if r['case']in scope]
    def voltage_pass(scope):
        return all(r['pass']for r in rows(scope))and all(c['static_probe_pass']for run in result['runs']for c in run['cases']if c['case']in scope)
    resistance={row['name']:row for row in result.get('resistance_margin_checks',[])}
    for run in result['runs']:assert {row['name']for row in run.get('loops',[])}==loop_names
    vcap=(all(impedance[net]['pass']for net in loop_nets)and all(resistance[name]['pass']for name in loop_names)
           and all(row['pass']for run in result['runs']for row in run['loops']))if loop_names else None
    return {'required_scope_acceptance':all(impedance[net]['pass']for net in required_nets)and voltage_pass(required),
      'required_case_count':len(required),'required_voltage_checks':rows(required),
      'required_voltage_convergence':all(row['change_V']<=tolerance for row in rows(required)),
      'VCAP_acceptance':vcap,'VCAP_loop_count':len(loop_names),
      'VCAP_resistance_checks':[resistance[name]for name in sorted(loop_names)],
      'VCAP_meaning':'DC copper and barrel leg sum only; excludes R16 resistance, capacitor ESR and all AC/stability effects.',
      'numerical_acceptance':all(row['pass']for row in impedance.values())and all(row['change_V']<=tolerance for row in margins),
      'numerical_meaning':'Completed runner residual/KCL/energy guards, all network impedance sensitivities and all declared voltage-grid sensitivities; not a rigorous discretization bound.',
      'illustrative_observations_complete':True,'illustrative_case_count':len(illustrations),
      'illustrative_threshold_and_margin_pass':voltage_pass(illustrations),
      'illustrative_voltage_checks':rows(illustrations),
      'illustrative_meaning':'7.4 V same-BEC finite-lead illustrations include lost-feed/high-load cases beyond stated continuous capability, without assigned duration; not required operating envelopes.',
      'runner_overall_boolean':result['conditional_static_screen_pass'],
      'runner_boolean_meaning':'Original unchanged conjunction of every selected case, loop and runner guard, including the illustrations.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['result','freeze','ledger','out']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():parser.error('Preserve existing summary')
    result=json.loads(args.result.read_text());ledger=json.loads(args.ledger.read_text())
    assert result['freeze_sha256']==sha(args.freeze)and result['ledger_sha256']==sha(args.ledger)
    check_ledger(ledger,ledger['model_contract'],full=True)
    scopes=classify_scopes(result,ledger)
    sink_report=actual_sink_report(result,ledger,json.loads(args.freeze.read_text())['files']['board']['sha256'],sha(args.ledger),sha(args.freeze))
    if result.get('status')=='REFUSED':
        summary={key:value for key,value in result.items()if key in ['status','reason','conditional_static_screen_pass','board_sha256','freeze_sha256','ledger_sha256','geometry_reproduction','linear_solver_diagnostics']}
        summary.update(result_sha256=sha(args.result),completed_unqualified_grid_count=len(result.get('partial_runs_unqualified',[])))
    else:
        summary=summarize_loaded(args.result,args.freeze,args.ledger)
        summary['status']='Completed scoped numerical run; see separate scope decisions and unchanged runner boolean.'
        summary['base_summarizer_sha256']=summary.pop('summarizer_sha256')
        summary['limitations']=result['limitations']+[
          'Required-scope acceptance is conditional on the explicit source/material/device/contact inputs; omitted corner sweeps remain incomplete.',
          'Modeled harness profiles are illustrative; measured harness remains unset.',
          'USB configuration disconnects external loads; a 3 V operating input minimum does not establish the separate 4.3 V accuracy conditions.',
          'The 0.50 A DSM capacity case does not inherit classic 20 mA receiver accuracy.',
          'This source still has unrelated ordinary opens; later drills/fills require a fresh source audit and rebind.']
        summary['VCAP_runs']=[{'spacing_mm':run['spacing_mm'],'loops':[{k:v for k,v in row.items()if k!='legs'}for row in run['loops']]}for run in result['runs']]
        loop_fields=[];loop_references=0
        definitions={loop['name']:loop for loop in ledger['loops']}
        for run in result['runs']:
            for loop in run['loops']:
                assert loop['maximum_ohm']==definitions[loop['name']]['maximum_ohm']
                assert [leg['net']for leg in loop['legs']]==[leg['net']for leg in definitions[loop['name']]['legs']]
                for leg in loop['legs']:
                    field=leg['field'];loop_fields.append(field)
                    for ref in field['native_edge_noding_refs'].values():
                        assert ref['sha256']==canonical(result['geometry_certificates'][ref['certificate_key']])
                        loop_references+=1
        summary['verification']['VCAP_geometry_references_checked']=loop_references
        summary['VCAP_numerical_extrema']={'maximum_KCL_residual_A':max(f['KCL_max_residual_A']for f in loop_fields),
          'maximum_energy_error_W':max(abs(f['copper_loss_W']-f['port_power_W'])for f in loop_fields),
          'maximum_linear_residual_to_required_ratio':max(f['linear_solver_diagnostics']['last_direct_solve']['residual_norm_history_A'][-1]/f['linear_solver_diagnostics']['last_direct_solve']['required_residual_norm_A']for f in loop_fields)}
        summary['geometry']['maximum_inserted_grid_rounding_error_mm']=max(c.get('maximum_grid_intersection_rounding_error_mm',0.)for c in result['geometry_certificates'].values())
    summary.update(scope_decisions=scopes,actual_sink_report=sink_report,summarizer_sha256=sha(__file__))
    args.out.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'summary_sha256':sha(args.out),'scope_decisions':{k:v for k,v in scopes.items()if not isinstance(v,list)}}))


if __name__=='__main__':main()
