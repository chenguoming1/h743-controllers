"""Recheck published scalar DC results; the omitted full raw field stream is not reverified."""
import argparse,gzip,hashlib,json,math,pathlib,resource,shutil,time
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(90,90))
import replay
P=pathlib.Path(__file__).resolve().parent
B='84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd';N='04d8ecd80edf004f3226f204f23adba51692a498ae38edc183debeffb704603d';M='285961cbf0d79d0ae28e2e2a84b256380da8c6a922b6977a2495b7554c922a95'
def require(ok,msg):
 if not ok:raise ValueError(msg)
def read(p):
 with (gzip.open(p,'rt') if str(p).endswith('.gz') else pathlib.Path(p).open()) as f:return json.load(f,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON '+x)))
def canonical(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def close(a,b):return math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-14)
parser=argparse.ArgumentParser();parser.add_argument('--out',type=pathlib.Path);args=parser.parse_args();start=time.monotonic()
verified=replay.verify();l=replay.portable_ledger();f=read(P/'freeze.json')
r=read(P/'evidence/reduced-result.json.gz');s=read(P/'evidence/result-summary.json');t=read(P/'evidence/run-terminal-review.json');v=read(P/'evidence/RESULT-REVIEW.json');run=read(P/'evidence/run-receipt.json');normalization=read(P/'NORMALIZATION.json')
require(r['board_sha256']==run['board_sha256']==v['board_sha256']==B and run['native_sha256']==f['files']['native']['sha256']==N,'current source identity')
require(canonical(l['model_contract'])==M and f['model_contract']==l['model_contract'] and v['model_contract_sha256']==M,'current model identity')
require(t['result_complete_storage_verified'] and t['all_bound_sources_unchanged'] and t['watchdog_stop'] is None,'historical terminal receipt')
require(t['returncode']==run['exit_code']==1,'complete overall-false solver exit')
require(t['result_storage']==run['result_storage'] and t['result_storage']['stored_sha256']==normalization['original_raw_result_stored_sha256'] and t['result_storage']['logical_sha256']==normalization['original_raw_result_logical_sha256'],'historical raw identity')
require(r['streaming_reduction']['raw_result_sha256']==normalization['original_raw_result_stored_sha256'] and v['complete_raw_reduction_exact_case_and_certificate_review_passed'],'bound historical raw-verification receipt')
require(s['full_two_grid_result'] and not s['partial_results_qualified'] and not s['electrical_final_acceptance_claimed'] and not r['scope_is_final_board'] and not r['thermal_or_flight_qualification'],'qualification scope')
require(all(r['material'][k]==x for k,x in l['material'].items()) and not r['material']['thermal_prediction'] and not r['stackup']['fabricator_acceptance'],'material scope')
defs={c['name']:c for c in l['cases']};require(len(defs)==len(l['cases'])==305,'case inventory')
required={n for n,c in defs.items() if c['scope']!='same_BEC_illustrative'};illustrative=set(defs)-required
require((len(required),len(illustrative),len(l['loops']))==(294,11,5),'scope/loops')
for c in l['cases']:require(canonical({k:x for k,x in c.items() if k!='case_definition_sha256'})==c['case_definition_sha256'],'case definition changed')
require([g['spacing_mm'] for g in r['runs']]==l['mesh_spacings_mm']==[.12,.09],'two grids')
probe_count=0;grids=[];loop_rows=[];all_static_failures=[];extrema={};servo_rows=[];max_probe_node_error=0.0;max_equation=0.0;loop_numerics=[]
for g in r['runs']:
 require([c['case'] for c in g['cases']]==[c['name'] for c in l['cases']],'case coverage/order')
 require([p['net'] for p in g['ports']]==[n['net'] for n in l['networks']],'network coverage')
 for p,n in zip(g['ports'],l['networks']):
  require(set(p['contacts'])==set(n['contacts']) and len(p['contacts'])==len(set(p['contacts'])) and p['reference']==p['contacts'][0],'actual contacts')
  z=p['impedance_ohm'];require(len(z)==len(p['contacts'])-1 and all(len(zr)==len(z) for zr in z),'impedance dimensions')
  asym=max([abs(z[i][j]-z[j][i]) for i in range(len(z)) for j in range(len(z))]+[0]);require(asym<=1e-7 and close(asym,p['reciprocity_error_ohm']),'reciprocity')
 failures=[]
 for c in g['cases']:
  d=defs[c['case']];scope='required' if c['case'] in required else 'illustrative';require(c['case_definition_sha256']==d['case_definition_sha256'],'case identity')
  require(c['equation_residual_max']<=1e-7,'circuit residual');max_equation=max(max_equation,c['equation_residual_max'])
  require([p['name'] for p in c['probes']]==[p['name'] for p in d['probes']],'probe coverage/order')
  for p,dp in zip(c['probes'],d['probes']):
   probe_count+=1;require(p.get('minimum_V')==dp.get('minimum_V') and p.get('maximum_V')==dp.get('maximum_V'),'probe limits')
   node_voltage=c['voltage_V'][dp['p']]-c['voltage_V'][dp['n']];max_probe_node_error=max(max_probe_node_error,abs(node_voltage-p['voltage_V']));require(close(node_voltage,p['voltage_V']),'probe not actual differential pad voltage')
   passed=p.get('minimum_V',-math.inf)<=node_voltage<=p.get('maximum_V',math.inf);require(passed==p['pass'],'probe pass')
   pr={'case':c['case'],'scope':scope,'spacing_mm':g['spacing_mm'],'p':dp['p'],'n':dp['n'],**p}
   if not passed:failures.append(pr)
   key=(scope,p['name'],g['spacing_mm']);e=extrema.setdefault(key,{'scope':scope,'probe':p['name'],'spacing_mm':g['spacing_mm'],'p':dp['p'],'n':dp['n'],'minimum_V':p.get('minimum_V'),'maximum_V':p.get('maximum_V'),'min_observed_V':p['voltage_V'],'min_case':c['case'],'max_observed_V':p['voltage_V'],'max_case':c['case']})
   if p['voltage_V']<e['min_observed_V']:e['min_observed_V']=p['voltage_V'];e['min_case']=c['case']
   if p['voltage_V']>e['max_observed_V']:e['max_observed_V']=p['voltage_V'];e['max_case']=c['case']
  require(c['static_probe_pass']==all(p['pass'] for p in c['probes']),'case static flag')
  if scope=='illustrative':
   current=-c['source_current_A']['one_external_BEC'];require(current>0,'BEC source current convention')
   servo_rows.append({'case':c['case'],'spacing_mm':g['spacing_mm'],'servo_only_A':d['current_budget_checks']['servo_subtotal_A'],'total_BEC_source_A':current,'difference_from_version_qualified_10A_continuous_A':current-10,'exceeds_version_qualified_10A_continuous':current>10,'servo_pad_V':{p['name']:p['voltage_V'] for p in c['probes'] if 'servo_board_pad' in p['name']},'static_probe_pass':c['static_probe_pass']})
 require([x['name'] for x in g['loops']]==[x['name'] for x in l['loops']],'VCAP loop coverage')
 for x,d in zip(g['loops'],l['loops']):
  require(close(sum(z['resistance_ohm'] for z in x['legs']),x['resistance_ohm']) and x['maximum_ohm']==d['maximum_ohm'] and x['pass']==(x['resistance_ohm']<=x['maximum_ohm']),'VCAP leg sum/limit')
  require([z['net'] for z in x['legs']]==[z['net'] for z in d['legs']],'VCAP leg identities')
  for z in x['legs']:
   diagnostics=z['field']['linear_solver_diagnostics'];last=diagnostics['last_direct_solve'];require(last['converged'] and last['residual_norm_history_A'][-1]<=last['required_residual_norm_A'],'VCAP direct solve convergence')
   require(diagnostics['finite_matrix'] and diagnostics['physical_element_operator']['positive_area_elements_discarded']==0,'VCAP element preservation')
   loop_numerics.append({'spacing_mm':g['spacing_mm'],'loop':x['name'],'net':z['net'],'final_residual_A':last['residual_norm_history_A'][-1],'required_residual_A':last['required_residual_norm_A'],'converged':last['converged']})
  loop_rows.append({'spacing_mm':g['spacing_mm'],**{k:x[k] for k in ['name','resistance_ohm','maximum_ohm','pass']}})
 all_static_failures+=failures;grids.append({'spacing_mm':g['spacing_mm'],'required_cases':294,'illustrative_cases':11,'failed_probes':failures})
coarse,fine=r['runs'];tol=l['convergence'];numerics=[];margins=[];resistance=[]
for a,b in zip(coarse['ports'],fine['ports']):
 require(a['net']==b['net'] and a['contacts']==b['contacts'],'cross-grid port identity')
 delta=max([abs(x-y) for ar,br in zip(a['impedance_ohm'],b['impedance_ohm']) for x,y in zip(ar,br)]+[0]);allowed=max(tol['absolute_impedance_ohm'],tol['relative_impedance']*max([abs(x) for br in b['impedance_ohm'] for x in br]+[0]));numerics.append({'net':b['net'],'max_impedance_change_ohm':delta,'allowed_ohm':allowed,'pass':delta<=allowed})
require(numerics==r['impedance_sensitivity'],'impedance recomputation')
for a,b in zip(coarse['cases'],fine['cases']):
 require(a['case']==b['case'] and len(a['probes'])==len(b['probes']),'cross-grid case identity')
 for x,y in zip(a['probes'],b['probes']):
  require(x['name']==y['name'],'cross-grid probe');delta=abs(x['voltage_V']-y['voltage_V']);margin=min(y['voltage_V']-y.get('minimum_V',-math.inf),y.get('maximum_V',math.inf)-y['voltage_V']);guard=max(delta,tol['absolute_voltage_V']);margins.append({'case':b['case'],'probe':y['name'],'change_V':delta,'margin_V':margin,'numerical_guard_V':guard,'pass':delta<=tol['absolute_voltage_V'] and margin>=guard})
require(margins==r['voltage_margin_checks'],'voltage convergence/margin recomputation')
for category in ['unit_transfers','loops']:
 require(len(coarse[category])==len(fine[category]),'resistance inventory')
 for a,b in zip(coarse[category],fine[category]):
  require(a['name']==b['name'],'resistance identity')
  if b.get('maximum_ohm') is None:continue
  delta=abs(a['resistance_ohm']-b['resistance_ohm']);guard=max(delta,tol['absolute_impedance_ohm']);margin=b['maximum_ohm']-b['resistance_ohm'];resistance.append({'name':b['name'],'change_ohm':delta,'margin_ohm':margin,'numerical_guard_ohm':guard,'pass':margin>=guard})
require(resistance==r['resistance_margin_checks'],'resistance margin recomputation')
rf=[x for x in all_static_failures if x['scope']=='required'];rm=[x for x in margins if x['case'] in required and not x['pass']];im=[x for x in margins if x['case'] in illustrative and not x['pass']]
require(rm==s['required_voltage_margin_failures']==v['required_voltage_margin_failures'] and im==s['illustrative_voltage_margin_failures']==v['illustrative_voltage_margin_failures'],'complete failure preservation')
required_pass=not rf and not rm and all(x['pass'] for x in numerics+resistance+loop_rows)
overall=all(c['static_probe_pass'] for g in r['runs'] for c in g['cases']) and all(x['pass'] for x in numerics+margins+resistance+loop_rows) and all(x.get('pass') is not False for g in r['runs'] for x in g['unit_transfers'])
require(overall==r['conditional_static_screen_pass']==s['conditional_static_screen_pass']==v['overall_conditional_static_screen_pass']==False,'raw overall false preserved')
for g in [.12,.09]:require(sum(x['exceeds_version_qualified_10A_continuous'] for x in servo_rows if x['spacing_mm']==g)==6,'six heavy BEC cases comparison')
require(v['certificate_inventory']['certificates']==v['certificate_inventory']['unique_referenced']==150 and v['certificate_inventory']['all_hashes_exact'] and v['certificate_inventory']['native_vertices_changed']==0 and v['certificate_inventory']['epsilon_merging'] is False,'raw certificate verification')
require(probe_count==9500 and len(loop_numerics)==30,'complete probe/VCAP numerical coverage')
report={'schema':'native0-portable-reduced-DC-review/v1','board_sha256':B,'model_contract_sha256':M,'verified_package':verified,'complete_case_rows':610,'actual_pad_probe_rows':probe_count,'maximum_probe_vs_node_voltage_error_V':max_probe_node_error,'grids':grids,'impedance_sensitivity':numerics,'VCAP_loops':loop_rows,'VCAP_leg_numerical_checks':loop_numerics,'resistance_margin_checks':resistance,'required_static_failures':rf,'required_voltage_margin_failures':rm,'illustrative_voltage_margin_failures':im,'required_conditional_DC_pass':required_pass,'raw_overall_conditional_static_screen_pass_preserved':overall,'servo_illustrations':servo_rows,'full_raw_field_stream_reverified':False,'raw_archive_in_package':False,'historical_raw_verifier_receipt_is_evidence_only':True,'source_or_model_modified':False,'solver_executed':False,'scope':'Complete reduced scalar arithmetic review; full raw field/certificate reconciliation requires omitted original raw or a fresh bounded replay. No thermal, AC, ESD, flight or final-board qualification.','resources':{'elapsed_seconds':time.monotonic()-start,'peak_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'address_space_limit_MiB':512}}
if args.out:
 require(args.out.resolve().is_relative_to(pathlib.Path('/tmp').resolve()),'Write review output under /tmp')
 require(shutil.disk_usage(args.out.parent).free>=128*1024**2,'128MiB output reserve')
 with args.out.open('x') as out:json.dump(report,out,indent=2,allow_nan=False);out.write('\n')
 print(json.dumps({'report':str(args.out),'sha256':replay.sha(args.out),'required_conditional_DC_pass':required_pass,'raw_overall':overall,'probe_rows':probe_count,'resources':report['resources']}))
else:print(json.dumps(report,indent=2,allow_nan=False))
