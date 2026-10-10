#!/usr/bin/env python3
"""Bounded stdlib-only recovery and receipt checks; no native geometry execution."""
import argparse, ast, contextlib, copy, hashlib, importlib.util, io, json, re, runpy, sys, tempfile, types, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base-project',type=Path,required=True);ap.add_argument('--historical-workspace',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 raw=module('v17_raw',ROOT/'tests/checkpoint47/materialize.py');e=raw.Evidence();index=e.index['files'];excluded=e.index['excluded_files'];recovered=e.index['recovered_files'];ident=read(ROOT/'checks/v17-source-identity.json')
 recovery=module('v17_recovery',ROOT/'sessions/recovery-v17/rebuild_historical_source.py');packet=ROOT/'sessions/recovery-v17';manifest=read(packet/'paired-files.json');negatives=[]
 def reject(name,f):
  try:f()
  except (AssertionError,ValueError,KeyError,FileNotFoundError):negatives.append(name)
  else:raise AssertionError('Accepted invalid evidence: '+name)
 def original(n):return (index.get(n) or excluded.get(n) or recovered[n])['sha256']
 for name in index:e.verify(name)
 for name in excluded:reject('excluded raw unavailable '+name,lambda name=name:e.bytes(name))
 if a.historical_workspace:
  for n,row in {**index,**excluded,**recovered}.items():assert sha(a.historical_workspace/n)==row['sha256'],n
 projects=[];transactions=[];cuts={};saved_controls=0
 with tempfile.TemporaryDirectory(prefix='v17-evidence-') as t:
  tmp=Path(t)
  for label in manifest['sources']:
   outputs=recovery.prepare_project(a.base_project,label,packet)
   for name,b in outputs.items():
    p=tmp/'ordinary-routing'/label/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
   projects.append({'source':label,'paired_files':len(outputs),'board_sha256':sha(tmp/'ordinary-routing'/label/'f722-heli.kicad_pcb')})
  for n in index:e.put(n,tmp)
  for n,row in recovered.items():assert sha(tmp/n)==row['sha256'],n
  j=lambda n:read(tmp/n)
  # Original pure parser definitions, without importing its unrelated pcbnew CLI.
  parser_path=tmp/'ordinary-routing/tests/mpn-parity/apply_metadata_copy.py';tree=ast.parse(parser_path.read_text());wanted={'Atom','Node','parse','children','child','value','properties','shape'}
  nodes=[n for n in tree.body if (isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in wanted) or (isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='TOKEN' for x in n.targets))]
  parser=types.ModuleType('apply_metadata_copy');parser.__dict__.update(re=re,json=json);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(parser_path),'exec'),parser.__dict__)
  prior_module=sys.modules.get('apply_metadata_copy');sys.modules['apply_metadata_copy']=parser
  support=module('v17_support',tmp/'integrated-routing/verify_support_adoption.py')
  for num,opens,kind,net,case_count,channels in [(46,33,'additive','RPM_HV',12,10),(47,32,'coordinated','SBUS_HV',13,11)]:
   c=f'ordinary-routing/candidate{num}/';old=f'ordinary-routing/candidate{num-1}/';review=f'checkpoint{opens}-review/';worker=f'ordinary-routing/tests/hv{num-1}/';board=original(c+'f722-heli.kicad_pcb');source=original(old+'f722-heli.kicad_pcb')
   assert ident['expected_boards'][f'candidate{num}']==board
   handoff=j(c+'route-handoff.json');adopt=j(c+'owner-adoption.json');native=j(c+'owner-summary.json');provenance=j(c+'construction-provenance.json');imp=j(c+'f722-heli.import.json')
   assert original(c+'route-handoff.json')==ident['sealed_handoffs'][str(num)]['sha256']
   for name,digest in handoff['files'].items():assert original(c+name)==digest,(c,name)
   for name,digest in j(c+'input-hashes.json').items():assert original(name)==digest,name
   assert handoff['board_sha256']==adopt['board_sha256']==native['board_sha256']==provenance['board_sha256']==board
   assert handoff['integration_source_sha256']==provenance['source_board_sha256']==source
   assert handoff['owner_adoption_pending'] is True and adopt['native_unfinished_connections']==opens
   assert adopt['native_errors']==adopt['native_warnings']==0 and not adopt['numerical_applicability']
   assert native['drc']==native['drc-all']=={'unconnected':opens,'errors':0,'warnings':0}
   assert not j(c+'owner-drc-parity.json')['schematic_parity'] and not j(c+'owner-drc-parity.json')['violations']
   assert not any(x['violations'] for x in j(c+'owner-erc.json')['sheets'])
   for section in ['process','mechanical','parity','firmware']:assert native[section]['passed'] and native[section]['board_sha256']==board
   assert native['critical']['connected_nets']==native['critical']['total_nets']==16 and not native['critical']['faults'] and not native['critical']['missing_ground_returns']
   for key,path in [('native_gate_receipt_sha256',c+'owner-summary.json'),('integration_receipt_sha256',review+'owner-'+kind+'-integration.json'),('reference_comparison_sha256',review+f'comparison-{opens+1}-to-{opens}.json'),('actual_io_receipt_sha256',c+'protection-actual-io.json')]:assert adopt[key]==original(path)
   owner=j(review+'owner-review-run.json');assert owner['board_sha256']==board and owner['previous_board_sha256']==source and owner['native_count']==opens and owner['sealed_native_receipts_verified']
   assert {r['command']:r['exit_code'] for r in owner['commands']}=={kind:0,'reference':0,'i2c':2,'actual-io22':1,'spi':0}
   assert provenance['constructor_sha256']==original(c+'construct.used.py')==original(worker+'construct.py')
   assert provenance['source_native_sha256']==original(old+'f722-heli.native.json') and provenance['source_map_sha256']==original(old+'f722-heli.logical-route-map.json')
   proposal='rpm-F-final-proposal.json' if num==46 else 'complete-joint-refined.json'
   assert provenance['proposal_sha256']==original(c+proposal)==original(worker+proposal)
   assert not provenance['changed_pad_records'] and not provenance['changed_footprint_records'] and provenance['all_156_footprints_exact']
   assert imp['passed'] and imp['source_sha256']==source and imp['output_sha256']==board and not imp['direct_engine_output'] and not imp['engine_routing_succeeded'] and not imp['fresh_model_zero_control_performed']
   assert imp['construction_provenance_sha256']==original(c+'construction-provenance.json') and imp['logical_route_map_sha256']==original(c+'f722-heli.logical-route-map.json')
   assert not imp['numerical_power_VCAP_applicable']
   # Replay exact saved owner integration source using its exact pure parser subset.
   path=tmp/f'integrated-routing/check_{kind}_integration.py';out=tmp/f'integration{num}.json';nets=[net] if num==46 else ['SBUS_HV','+3V3_CORE','ADC_DIV_MID'];argv=sys.argv
   sys.argv=[str(path),str(tmp/old/'f722-heli.kicad_pcb'),str(tmp/c/'f722-heli.kicad_pcb'),'--out',str(out)]+[x for n in nets for x in ['--net',n]]
   try:
    with contextlib.redirect_stdout(io.StringIO()):state=runpy.run_path(str(path),run_name='__main__')
   finally:sys.argv=argv
   integration=read(out);assert integration==j(c+f'native-{kind}-integration.json')==j(review+f'owner-{kind}-integration.json')
   assert integration['retained_footprints']==156 and integration['unchanged_zone_designs']==3
   assert all(parser.shape(fp)==parser.shape(state['nf'][uid]) for uid,fp in state['of'].items())
   assert sum(len(parser.children(fp,'pad')) for fp in state['nf'].values())==558
   assert len(integration['added_objects'])==(9 if num==46 else 23)
   assert len(integration.get('removed_objects',[]))==(0 if num==46 else 4) and not integration.get('changed_objects',[])
   added={r['uuid'] for r in provenance['added_records']};removed={r['uuid'] for r in provenance['removed_source_records']}
   assert added=={r['uuid'] for r in integration['added_objects']} and removed=={r['uuid'] for r in integration.get('removed_objects',[])}
   nodes={parser.value(n,'uuid'):n for k in ['segment','via','arc'] for n in parser.children(state['n'],k)}
   point=lambda node,key:[float(x.value) for x in parser.child(node,key).items[1:]]
   def track(uid,net,layer,width,start,end):
    node=nodes[uid];assert uid in added and node.items[0].value=='segment' and parser.value(node,'net')==net and parser.value(node,'layer')==layer
    assert float(parser.value(node,'width'))==width and point(node,'start')==start and point(node,'end')==end
   if num==46:
    points=j(worker+proposal)['points'];assert len(points)==10
    for i,(start,end) in enumerate(zip(points,points[1:])):
     uid=str(uuid.uuid5(uuid.NAMESPACE_URL,source+'/hv45/RPM_HV-P0/'+original(worker+proposal)+'/'+str(i)));track(uid,'RPM_HV','F.Cu',.127,start,end)
   else:
    built=j(c+'constructed-paths.json');assert set(built['removed_source_uuids'])==removed
    expected_ids=set();proposal_hash=original(worker+proposal)
    for row in built['paths']:
     for i,(start,end) in enumerate(zip(row['points'],row['points'][1:])):
      uid=str(uuid.uuid5(uuid.NAMESPACE_URL,source+'/'+proposal_hash+'/'+row['label']+'/'+str(i)));expected_ids.add(uid)
      track(uid,row['net'],row['layer'],row['width'],[round(v,6) for v in start],[round(v,6) for v in end])
    for row in built['vias']:
     uid=str(uuid.uuid5(uuid.NAMESPACE_URL,source+'/'+proposal_hash+'/'+row['label']));expected_ids.add(uid);node=nodes[uid]
     assert node.items[0].value=='via' and parser.value(node,'net')==row['net'] and point(node,'at')==row['xy']
     assert float(parser.value(node,'size'))==.45 and float(parser.value(node,'drill'))==.2
    assert expected_ids==added
   before_map=j(old+'f722-heli.logical-route-map.json')['logical_route_map'];after_map=j(c+'f722-heli.logical-route-map.json')['logical_route_map'];expected={u:v for u,v in before_map.items() if u not in removed}
   for row in provenance['added_records']:
    if row['net']==net:expected[row['uuid']]=net+('::P0' if num==46 else '::P1')
    elif row['net']=='ADC_DIV_MID':expected[row['uuid']]=row['net']
   assert after_map==expected and set(j(c+'fixed-explicit-native-ids.json'))==(set(j(old+'fixed-explicit-native-ids.json'))-removed)|added
   assert j(c+'poses-native.json')==j(old+'poses-native.json')
   for row in j(c+'project-input-preservation.json')['files']:assert sha(tmp/c/row['path'])==sha(tmp/old/row['path'])==row['sha256']
   audit=j(c+'entry-support-audit.json');wrapper=j(c+'power-audit.json');prior=j(old+'power-audit.json')
   def bind(w):
    assert w['passed'] is audit['passed'] is True and w['schema']=='f722-native-support-audit/v1'
    assert w['board_sha256']==audit['board_sha256']==board and w['source_board_sha256']==audit['source_board_sha256']==source
    assert w['native_sha256']==audit['native_sha256']==original(c+'f722-heli.native.json') and w['source_native_sha256']==audit['source_native_sha256']==original(old+'f722-heli.native.json')
    assert w['audit_sha256']==original(c+'entry-support-audit.json') and w['audit']=='entry-support-audit.json'
    assert w['source_audit_sha256']==original(old+'power-audit.json') and w['audit_source_sha256']==audit['audit_source_sha256']==original(c+'audit.used.py')==original(worker+'audit.py')
    assert not w['numerical_power_VCAP_applicable'] and not audit['numerical_power_VCAP_applicable']
    assert w['nets']==audit['nets'] and len(w['nets'])==28 and len(audit['gates'])==11 and all(v is True for v in audit['gates'].values())
    for n,row in w['nets'].items():assert row['complete'] and row['pad_group_count']==1 and row['groups']==prior['nets'][n]['groups'] and row['source_groups_exactly_preserved']
   bind(wrapper)
   for k,value in [('board_sha256','0'*64),('audit_sha256','0'*64),('source_audit_sha256','0'*64),('native_sha256','0'*64),('numerical_power_VCAP_applicable',True)]:
    bad=copy.deepcopy(wrapper);bad[k]=value;reject(f'{num} wrapper binding {k}',lambda bad=bad:bind(bad))
   compat=support.verify(wrapper,prior,source,board,tmp/c);assert compat=={'passed':True,'nets':28,'typed_audit_binding_checked':False}
   saved=j(c+'support-wrapper-compatibility.json');assert saved['support_wrapper_sha256']==original(c+'power-audit.json') and saved['verifier_sha256']==original('integrated-routing/verify_support_adoption.py') and all(saved[k]==v for k,v in compat.items())
   assert len(audit['strict_pad_entries'])==2 and all(x['passed'] for x in audit['strict_pad_entries'])
   assert len(audit['full_width_joins'])==(8 if num==46 else 18) and all(x['passed'] for x in audit['full_width_joins'])
   controls=audit['negative_controls'];assert len(controls)==(5 if num==46 else 11) and all(x['rejected'] for x in controls);saved_controls+=len(controls)
   if num==46:
    assert audit['new_track_endpoints_checked']==18 and provenance['new_vias']==0 and not provenance['native_refill_performed']
    assert audit['RPM_HV_current_groups'][0]['pads']==['Q1.3','R25.2','U16.1']
   else:
    assert len(audit['classified_endpoints'])==40 and all(x['resolved'] for x in audit['classified_endpoints'])
    assert len(audit['finite_actual_annular_entries'])==8 and all(x['passed'] for x in audit['finite_actual_annular_entries'])
    assert audit['SBUS_after_groups'][0]['pads']==['Q2.3','R26.2','U16.2'] and provenance['new_signal_vias']==2 and provenance['replaced_CORE_vias']==1 and provenance['native_refill_performed']
    assert audit['CORE_local_feed_review']['width_mm']==.2 and audit['CORE_local_feed_review']['source_ends_unchanged'] and audit['CORE_local_feed_review']['numerical_applicability_pending']
    transaction=j(c+'coordinated-change-receipt.json');assert transaction['added_candidate_records']==provenance['added_records'] and transaction['removed_source_records']==provenance['removed_source_records']
    assert transaction['all_other_source_objects_exact']==1946 and transaction['construction_provenance_sha256']==original(c+'construction-provenance.json')
    for field,name in [('complete_rewritten_entry_receipt_sha256','entry-support-audit.json'),('support_receipt_sha256','power-audit.json'),('actual_io_receipt_sha256','protection-actual-io.json')]:assert transaction[field]==original(c+name)
    assert imp['coordinated_change_receipt_sha256']==original(c+'coordinated-change-receipt.json') and not transaction['engine_success_claimed']
   actual=j(c+'protection-actual-io.json');assert actual==j(review+'actual-io22.json') and actual['board_sha256']==board and actual['geometry_sha256']==original(c+'f722-heli.native.json') and actual['source_unchanged']
   assert (actual['passed'],actual['total'],actual['all_pass'])==(case_count,22,False)
   passing=[x for x in actual['checks'] if x['complete_clamp_first_path_passes']];assert len({(x['net'],x['clamp']) for x in passing})==channels
   cuts[num]={x['net']:x for x in actual['checks'] if x['net'] in ['RPM_HV','SBUS_HV']}
   for n in ['RPM_HV'] if num==46 else ['RPM_HV','SBUS_HV']:
    cut=cuts[num][n];assert cut['complete_clamp_first_path_passes'] and cut['source_target_physically_disconnected_after_removing_actual_pad_copper'] and cut['minimum_gap_measured_mm']>0
   comparison=j(c+f'reference-comparison{num-1}.json');assert comparison==j(review+f'comparison-{opens+1}-to-{opens}.json') and comparison['before_board_sha256']==source and comparison['after_board_sha256']==board
   assert comparison['critical_object_geometry_identical'] and not comparison['critical_object_differences'] and all(v==0 for row in comparison['net_numeric_deltas_after_minus_before'].values() for v in row.values())
   assert all(v['lost_GND_overlap_with_trace_width_mm2']==0 for row in comparison['ground_fill_changes'].values() for v in row['critical_trace_proximity'].values())
   assert j(old+'reference-snapshot/critical-reference.json')['nets']==j(c+'reference-snapshot/critical-reference.json')['nets']==j(review+'snapshot/critical-reference.json')['nets']
   for folder in [old+'reference-snapshot/',c+'reference-snapshot/',review+'snapshot/']:
    report=j(folder+'critical-reference.json');signals=j(folder+'native-signals.json');assert signals['geometry_sha256']==report['sources']['native-geometry.json']==original(folder+'native-geometry.json') and report['sources']['native-signals.json']==original(folder+'native-signals.json')
   assert j(c+'i2c-geometry-review.json')['I2C_final_status']=='NOT_QUALIFIED' and j(c+'stock-spi-binding.json')['passed']
   assert not j(c+'power-revalidation-required.json')['numerical_power_and_VCAP_applicability']
   transactions.append({'candidate':num,'native_open_connections':opens,'actual_cases':case_count,'actual_channels':channels,'added_copper_objects':len(added),'removed_copper_objects':len(removed),'owner_integration_replayed':True,'saved_finite_controls':len(controls)})
  if prior_module is None:sys.modules.pop('apply_metadata_copy',None)
  else:sys.modules['apply_metadata_copy']=prior_module
  assert cuts[46]['RPM_HV']['minimum_gap_measured_mm']==cuts[47]['RPM_HV']['minimum_gap_measured_mm']
  assert abs(cuts[47]['SBUS_HV']['minimum_gap_measured_mm']-.4208)<1e-12
  assert abs(cuts[47]['RPM_HV']['minimum_gap_measured_mm']-.5775051678605436)<1e-12
  for name,row in ident['frozen_helpers'].items():assert original(name)==row['sha256']
  for label in ['candidate46','candidate47']:
   data=(a.base_project/'f722-heli.kicad_pcb').read_bytes();delta=read(packet/(label+'.f722-heli.kicad_pcb.delta.json'))
   for name,bb,dd in [('wrong base',data+b'\n',delta),('wrong target',data,dict(delta,target_sha256='0'*64)),('invalid range',data,dict(delta,operations=[[0,len(data)+1]])),('invalid operation',data,dict(delta,operations=[{}]))]:reject(label+' '+name,lambda bb=bb,dd=dd:recovery.reconstruct(bb,dd))
  for name in ['../escape','/absolute','safe/../escape','windows\\escape']:reject('unsafe path '+name,lambda name=name:raw.safe(name))
 status=read(ROOT/'status.json');assert status['native_open_connections']==32 and status['actual_io_cases_passed']==13 and status['actual_io_channels_passed']==11 and not status['numerical_power_and_VCAP_applicability'] and not status['fabrication_ready']
 result={'passed':True,'scope':'Exact paired45/46/47 recovery; hashes of all selected and sealed dependency paths; original owner additive/coordinated parser checks and support-adapter replay; full receipt binding. Saved finite geometry, actual pad cuts, DRC, reference and refill receipts are checked, not reexecuted.','verifier_source_sha256':sha(__file__),'recovered_projects':projects,'raw_files_verified':len(index),'excluded_raw_files':len(excluded),'negative_controls_passed':len(negatives),'negative_controls':negatives,'original_source_hash_checks_performed':bool(a.historical_workspace),'transactions':transactions,'preserved_finite_controls':saved_controls,'sealed_handoffs_byte_exact':True,'all_sealed_dependency_bytes_included':False,'parsed_total_footprints':156,'parsed_total_pads':558,'deterministic_constructor_geometry_checked':True,'owner_pure_parser_integration_reexecuted':True,'owner_native_geometry_integration_reexecuted':False,'actual_owner_support_adapter_reexecuted':True,'full_entry_binding_separately_verified':True,'RPM_HV_cut_mm':cuts[47]['RPM_HV']['minimum_gap_measured_mm'],'SBUS_HV_cut_mm':cuts[47]['SBUS_HV']['minimum_gap_measured_mm'],'native_replay_inputs_complete':False,'full_finite_geometry_audit_reexecuted':False,'native_DRC_reexecuted':False,'JVM_router_refill_or_power_solve_executed':False,'numerical_power_and_VCAP_applicability':False,'I2C_electrical_status':'NOT_QUALIFIED','native_open_connections':32,'native_errors':0,'native_warnings':0}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
