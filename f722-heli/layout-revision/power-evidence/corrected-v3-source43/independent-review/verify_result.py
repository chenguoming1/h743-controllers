import json,hashlib,math
from pathlib import Path
from types import SimpleNamespace
import plan_power_revalidation as p
import model_contract as contract
import report_actual_sinks as reporter
root=Path('.').resolve();job=root/'job-candidate43';released=job/'released';read=lambda path:json.loads(path.read_text());sha=p.sha
plan_path=root/'plan-candidate43.json';plan_sha='a1051215a798f9851003cea94d0c0bbb300419c2ccee77e4ee6ebcee62306b7c'
plan=p.load_bound_plan(plan_path,plan_sha);launch=p.bound_launch(SimpleNamespace(plan_sha=plan_sha),plan)
assert sha(released/'result.json')=='1466a094fc40cfbed24fbda76d5445bad9c06d951389e2440ed6b0cd3b13bac9'
assert sha(job/'combined-summary.json')=='030fa2ae528c45d9f0207eac4fb9b93c74cc84cf3296035f995d869bf0409550'==launch['summary_sha256']
f=read(released/'freeze.json');l=read(released/'ledger.json');s=read(job/'combined-summary.json');r=read(released/'result.json')
for row in f['files'].values():assert sha(released/row['path'])==row['sha256']
for name,h in f['analysis_source_sha256'].items():assert sha(released/'solver-source'/name)==h
contract.check_ledger(l,plan['model_contract'],full=True)
assert sha(p.ACCEPTED_BOARD)==r['board_sha256']==plan['scope']['board_sha256']
assert l['freeze_manifest_sha256']==sha(released/'freeze.json')==r['freeze_sha256']
assert sha(released/'ledger.json')==r['ledger_sha256']
assert r.get('status')!='REFUSED' and len(r['runs'])==2 and not r.get('partial_runs_unqualified')
assert [run['spacing_mm'] for run in r['runs']]==l['mesh_spacings_mm']==[.12,.09]
byname={x['name']:x for x in l['cases']};required={n for n,c in byname.items() if c['scope'] in ['classic','capacity','usb_configuration']};illustrative={n for n,c in byname.items() if c['scope']=='same_BEC_illustrative'}
assert len(required)==294 and len(illustrative)==11 and required|illustrative==set(byname)
failures=[];point_checks=0;report_checks=0;field_checks=0;refs=0;case_checks=0
cert_hashes={n:p.canonical(v) for n,v in r['geometry_certificates'].items()}
def check_refs(block):
 global refs
 for ref in block['native_edge_noding_refs'].values():
  assert ref['sha256']==cert_hashes[ref['certificate_key']];refs+=1
for run in r['runs']:
 assert [c['case'] for c in run['cases']]==list(byname)
 assert [b['net'] for b in run['ports']]==[n['net'] for n in l['networks']]
 for port,network in zip(run['ports'],l['networks']):
  assert set(port['contacts'])==set(network['contacts']);check_refs(port)
 for row in run['cases']:
  c=byname[row['case']];assert row['case_definition_sha256']==c['case_definition_sha256'];case_checks+=1
  assert [v['name'] for v in row['probes']]==[v['name'] for v in c['probes']]
  assert [v['name'] for v in row['report_only_probes']]==[v['name'] for v in c['report_only_probes']]
  for probe,definition in zip(row['probes'],c['probes']):
   v=row['voltage_V'][definition['p']]-row['voltage_V'][definition['n']]
   assert math.isfinite(v) and abs(v-probe['voltage_V'])<1e-10
   assert all(probe.get(k)==definition.get(k) for k in ['minimum_V','maximum_V'])
   valid=definition.get('minimum_V',-math.inf)<=v<=definition.get('maximum_V',math.inf)
   assert probe['pass'] is valid;point_checks+=1
   if not valid:failures.append({'grid':run['spacing_mm'],'case':row['case'],'scope':c['scope'],'probe':probe['name'],'voltage_V':v,'floor_V':definition.get('minimum_V')})
  assert row['static_probe_pass'] is all(p['pass'] for p in row['probes'])
  for probe,definition in zip(row['report_only_probes'],c['report_only_probes']):
   assert abs(row['voltage_V'][definition['p']]-row['voltage_V'][definition['n']]-probe['voltage_V'])<1e-10
   assert probe['acceptance_limit'] is False;report_checks+=1
  assert set(row['fields'])==set(c['nets'])
  assert row['equation_residual_max']<=1e-7
  assert abs(row['power_W']['balance_error'])<=max(1e-8,abs(row['power_W']['source_delivery'])*1e-8)
  loss=sum(x['copper_loss_W'] for x in row['fields'].values())
  assert abs(loss-row['power_W']['copper_loss'])<=max(1e-8,abs(loss)*1e-6)
  for field in row['fields'].values():
   check_refs(field);diag=field['linear_solver_diagnostics']['last_direct_solve']
   assert diag['converged'] and diag['residual_norm_history_A'][-1]<=diag['required_residual_norm_A'];field_checks+=1
  for conv in row['converters']:assert abs(conv['power_balance_error_W'])<=1e-8
 for row,definition in zip(run['loops'],l['loops']):
  assert row['name']==definition['name'] and row['maximum_ohm']==definition['maximum_ohm']==.035
  assert abs(row['resistance_ohm']-sum(v['resistance_ohm'] for v in row['legs']))<1e-12
  assert row['pass'] is (row['resistance_ohm']<=.035)
  for leg in row['legs']:check_refs(leg['field'])
coarse,fine=r['runs'];tol=l['convergence'];margins=[]
for a,b in zip(coarse['cases'],fine['cases']):
 for pa,pb in zip(a['probes'],b['probes']):
  delta=abs(pa['voltage_V']-pb['voltage_V']);margin=min(pb['voltage_V']-pb.get('minimum_V',-math.inf),pb.get('maximum_V',math.inf)-pb['voltage_V']);guard=max(delta,tol['absolute_voltage_V'])
  margins.append({'case':b['case'],'probe':pb['name'],'change_V':delta,'margin_V':margin,'numerical_guard_V':guard,'pass':delta<=tol['absolute_voltage_V'] and margin>=guard})
assert margins==r['voltage_margin_checks']
sensitivity=[]
for a,b in zip(coarse['ports'],fine['ports']):
 delta=max(abs(x-y) for aa,bb in zip(a['impedance_ohm'],b['impedance_ohm']) for x,y in zip(aa,bb));scale=max(abs(x) for row in b['impedance_ohm'] for x in row);allowed=max(tol['absolute_impedance_ohm'],tol['relative_impedance']*scale)
 sensitivity.append({'net':b['net'],'max_impedance_change_ohm':delta,'allowed_ohm':allowed,'pass':delta<=allowed})
assert sensitivity==r['impedance_sensitivity']
resistance=[]
for a,b in zip(coarse['loops'],fine['loops']):
 delta=abs(a['resistance_ohm']-b['resistance_ohm']);guard=max(delta,tol['absolute_impedance_ohm']);margin=b['maximum_ohm']-b['resistance_ohm']
 resistance.append({'name':b['name'],'change_ohm':delta,'margin_ohm':margin,'numerical_guard_ohm':guard,'pass':margin>=guard})
assert resistance==r['resistance_margin_checks']
assert all(x['pass'] for x in sensitivity+resistance) and all(x['change_V']<=tol['absolute_voltage_V'] for x in margins)
assert all(x['pass'] for x in margins if x['case'] in required)
assert all(c['static_probe_pass'] for run in r['runs'] for c in run['cases'] if c['case'] in required)
assert not r['conditional_static_screen_pass'] and launch['original_runner_exit_code']==1
assert all(x['scope']=='same_BEC_illustrative' for x in failures)
actual=reporter.extract(r,l,r['board_sha256'],sha(released/'ledger.json'),sha(released/'freeze.json'))
assert actual==s['actual_sink_report'] and len(actual['actual_supply_rows'])==6100 and not actual['sink_window_failures'] and not actual['sink_two_grid_failures']
assert s['scope_decisions']['required_scope_acceptance'] is True and s['scope_decisions']['VCAP_acceptance'] is True and s['scope_decisions']['numerical_acceptance'] is True and s['scope_decisions']['illustrative_threshold_and_margin_pass'] is False
assert sha(p.ACCEPTED_BOARD)==r['board_sha256']
print(json.dumps({'verified':True,'board_sha256':r['board_sha256'],'case_hash_checks':case_checks,'acceptance_probe_p_minus_n_checks':point_checks,'report_only_p_minus_n_checks':report_checks,'loaded_field_residual_checks':field_checks,'geometry_certificate_reference_checks':refs,'voltage_grid_guards':len(margins),'impedance_grid_guards':len(sensitivity),'VCAP_grid_guards':len(resistance),'actual_supply_rows':len(actual['actual_supply_rows']),'failures':failures,'required_actual_supply_fine_minima':{name:min(x['voltage_V'] for x in actual['actual_supply_rows'] if x['grid_mm']==.09 and x['scope']!='same_BEC_illustrative' and x['sink']==name) for name in sorted({x['sink'] for x in actual['actual_supply_rows']})},'loop_fine_ohm':{row['name']:row['resistance_ohm'] for row in fine['loops']}},indent=2))
