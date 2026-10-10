#!/usr/bin/env python3
"""Portable accepted 50/51/52 evidence and exact source recovery checks.

Only Python standard-library parsing, hash checks and support/adoption adapters.
Stored native geometry, transform, reference and finite controls are not replayed.
"""
import argparse,ast,copy,hashlib,importlib.util,json,re,sys,tempfile,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if sys.flags.optimize:raise RuntimeError('Assertions must be enabled')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base-project',type=Path,required=True);ap.add_argument('--historical-workspace',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 e=module('v20_raw',ROOT/'tests/checkpoint52/materialize.py').Evidence();identity=read(ROOT/'checks/v20-source-identity.json');packet=ROOT/'sessions/recovery-v20';manifest=read(packet/'paired-files.json');recovery=module('v20_recovery',packet/'rebuild_historical_source.py')
 index=e.index['files'];excluded=e.index['excluded_files'];recovered=e.index['recovered_files'];allrows={**index,**excluded,**recovered};neg=[]
 def reject(label,f):
  try:f()
  except (AssertionError,ValueError,KeyError,FileNotFoundError):neg.append(label)
  else:raise AssertionError('Invalid input accepted: '+label)
 def original(name):return allrows[name]['sha256']
 for n in index:e.verify(n)
 for n in excluded:reject('excluded raw input: '+n,lambda n=n:e.bytes(n))
 for n,row in identity['frozen_helpers'].items():assert original(n)==row['sha256']
 if a.historical_workspace:
  for n,row in allrows.items():
   source=e.index['frozen_alias_sources'].get(n,n)
   assert sha(a.historical_workspace/source)==row['sha256'],n
 projects=[];stages=[];parser_transactions=[];adoption_controls=[]
 with tempfile.TemporaryDirectory(prefix='v20-evidence-') as t:
  tmp=Path(t)
  for label,row in manifest['sources'].items():
   outputs=recovery.prepare_project(a.base_project,label,packet)
   for n,data in outputs.items():
    p=tmp/row['workspace_path']/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
   projects.append({'source':label,'paired_files':len(outputs),'board_sha256':sha(tmp/row['workspace_path']/'f722-heli.kicad_pcb')})
  for n in index:e.put(n,tmp)
  for n,row in recovered.items():assert sha(tmp/n)==row['sha256'],n
  j=lambda n:read(tmp/n)
  bs=j('ordinary-routing/tests/port-b48/candidate03/WORKER-FILES.sha256.json');assert len(bs['files'])==identity['sealed_worker_manifests']['B03']['files']==62
  for row in bs['files']:assert original('ordinary-routing/tests/port-b48/candidate03/'+row['path'])==row['sha256']
  for name,digest in identity['B03_constructor_input_hashes'].items():assert original(name)==digest
  lineage=j('ordinary-routing/candidate51/lineage-receipt-bindings.json')
  for row in lineage['files']:assert original('ordinary-routing/candidate51/'+row['copied_as'])==row['sha256']
  parserpath=tmp/'ordinary-routing/tests/mpn-parity/apply_metadata_copy.py';tree=ast.parse(parserpath.read_text());wanted={'Atom','Node','parse','children','child','value','properties','shape'}
  nodes=[n for n in tree.body if (isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in wanted) or (isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='TOKEN' for x in n.targets))]
  parser=types.ModuleType('v20_parser');parser.__dict__.update(re=re,json=json);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(parserpath),'exec'),parser.__dict__)
  keyed=lambda root,kind:{parser.value(n,'uuid'):n for n in parser.children(root,kind)}
  parsed={label:parser.parse((tmp/row['workspace_path']/'f722-heli.kicad_pcb').read_text())for label,row in manifest['sources'].items()}
  def transaction(old,new,receipt,changed_refs):
   before,after=parsed[old],parsed[new];oldob={u:n for k in ('segment','via','arc')for u,n in keyed(before,k).items()};newob={u:n for k in ('segment','via','arc')for u,n in keyed(after,k).items()}
   added=set(newob)-set(oldob);removed=set(oldob)-set(newob);changed={u for u in set(oldob)&set(newob)if parser.shape(oldob[u])!=parser.shape(newob[u])}
   assert added=={r['uuid']for r in receipt['added_objects']} and removed=={r['uuid']for r in receipt['removed_objects']} and changed=={r['uuid']for r in receipt['changed_objects']}
   for field,records,side in [('added_objects',newob,'after'),('removed_objects',oldob,'before')]:
    for r in receipt[field]:assert r[side]==parser.shape(records[r['uuid']]) and r['net'] in receipt['allowed_changed_nets']
   for r in receipt['changed_objects']:assert r['before']==parser.shape(oldob[r['uuid']]) and r['after']==parser.shape(newob[r['uuid']]) and r['net'] in receipt['allowed_changed_nets']
   of,nf=keyed(before,'footprint'),keyed(after,'footprint');assert set(of)==set(nf) and len(nf)==156;assert sum(len(parser.children(f,'pad'))for f in nf.values())==558
   actual={parser.properties(of[u])['Reference'].items[2].value for u in of if parser.shape(of[u])!=parser.shape(nf[u])};assert actual==set(changed_refs),(old,new,actual,changed_refs)
   def config(z):return [parser.shape(x)if isinstance(x,parser.Node)else x.value for x in z.items if not(isinstance(x,parser.Node)and x.items[0].value in ('filled_polygon','fill_segments'))]
   oz,nz=keyed(before,'zone'),keyed(after,'zone');assert set(oz)==set(nz) and all(config(oz[u])==config(nz[u])for u in oz)
   skip={'footprint','segment','via','arc','zone'};rest=lambda r:[parser.shape(x)if isinstance(x,parser.Node)else x.value for x in r.items if not(isinstance(x,parser.Node)and x.items[0].value in skip)]
   assert rest(before)==rest(after)
   parser_transactions.append({'source':old,'target':new,'added':len(added),'removed':len(removed),'changed':len(changed),'exact_unchanged_full_footprints':156-len(actual),'declared_changed_references':sorted(actual),'total_pads':558})
  support=module('v20_support',tmp/'integrated-routing/verify_support_adoption.py')
  adopt_verify=module('v20_adopt',tmp/'integrated-routing/verify_adoption_integration.py')
  for label,old,count,review,actual_cases in [('candidate50','candidate49',27,'checkpoint27-review',14),('candidate51','B03',19,'checkpoint19-owner-review',17),('candidate52','candidate51',17,'checkpoint17-owner-review',18)]:
   c='ordinary-routing/'+label+'/';source_folder=manifest['sources'][old]['workspace_path']+'/';board=identity['expected_boards'][label];source=identity['expected_boards'][old]
   hand=j(c+'route-handoff.json');seal=identity['sealed_worker_manifests'][label];assert original(c+'route-handoff.json')==seal['manifest']['sha256'];assert len(hand['files'])==seal['files']
   for n,digest in hand['files'].items():assert original(c+n)==digest,(label,n)
   native=j(c+'owner-summary.json');adopt=j(c+'owner-adoption.json');prov=j(c+'construction-provenance.json');imp=j(c+'f722-heli.import.json');audit=j(c+'entry-support-audit.json');wrapper=j(c+'power-audit.json');prior=j(source_folder+'power-audit.json')
   assert hand['board_sha256']==native['board_sha256']==adopt['board_sha256']==prov['board_sha256']==board
   assert hand['integration_source_sha256']==prov['source_board_sha256']==source
   assert native['drc']==native['drc-all']=={'unconnected':count,'errors':0,'warnings':0}
   assert adopt['native_unfinished_connections']==count and not adopt['numerical_applicability']
   assert native['critical']['connected_nets']==native['critical']['total_nets']==16 and not native['critical']['faults'] and not native['critical']['missing_ground_returns']
   for s in ('process','mechanical','parity','firmware'):assert native[s]['passed'] and native[s]['board_sha256']==board
   assert not j(c+'owner-drc-parity.json')['schematic_parity'] and not j(c+'owner-drc-parity.json')['violations'];assert not any(x['violations']for x in j(c+'owner-erc.json')['sheets'])
   assert imp['passed'] and imp['output_sha256']==board and imp['source_sha256']==source
   for key in ('direct_engine_output','engine_routing_succeeded','fresh_model_zero_control_performed','numerical_power_VCAP_applicable'):assert imp[key] is False
   assert prov['proposal_sha256']==original(c+'proposal.json') and prov['source_native_sha256']==original(source_folder+'f722-heli.native.json')
   assert prov['constructor_sha256'] in {v['sha256']for v in identity['frozen_helpers'].values()}
   assert imp['construction_provenance_sha256']==original(c+'construction-provenance.json') and imp['coordinated_change_receipt_sha256']==original(c+'coordinated-change-receipt.json')
   def bind(w):
    assert w['passed'] is audit['passed'] is True and w['board_sha256']==audit['board_sha256']==board and w['source_board_sha256']==audit['source_board_sha256']==source
    assert w['audit_sha256']==original(c+'entry-support-audit.json') and w['source_audit_sha256']==original(source_folder+'power-audit.json')
    assert w['native_sha256']==audit['native_sha256']==original(c+'f722-heli.native.json') and w['source_native_sha256']==audit['source_native_sha256']==original(source_folder+'f722-heli.native.json')
    assert w['nets']==audit['nets'] and len(w['nets'])==28 and all(audit['gates'].values()) and not w['numerical_power_VCAP_applicable']
    for n,r in w['nets'].items():assert r['complete'] and r['pad_group_count']==1 and r['groups']==prior['nets'][n]['groups'] and r['source_groups_exactly_preserved']
   bind(wrapper)
   for key,value in [('board_sha256','0'*64),('audit_sha256','0'*64),('native_sha256','0'*64),('numerical_power_VCAP_applicable',True)]:
    bad=copy.deepcopy(wrapper);bad[key]=value;reject(label+' support '+key,lambda bad=bad:bind(bad))
   assert support.verify(wrapper,prior,source,board,tmp/c)=={'passed':True,'nets':28,'typed_audit_binding_checked':False}
   assert all(r['rejected'] for r in audit['negative_controls'])
   cut=j(c+'protection-actual-io.json');assert cut['passed']==actual_cases and cut['total']==22
   owner=j(review+'/owner-review-run.json');assert owner['board_sha256']==board and owner['native_count']==count and owner['sealed_native_receipts_verified']
   assert {r['command']:r['exit_code']for r in owner['commands']}=={'coordinated':0,'reference':0,'i2c':2,'actual-io22':1,'spi':0}
   assert adopt['integration_receipt_sha256']==original(review+'/owner-coordinated-integration.json')
   transaction(old,label,j(c+'native-coordinated-integration.json'),['R45']if label=='candidate52'else [])
   stages.append({'candidate':label,'opens':count,'native_errors':0,'native_warnings':0,'seal_files':seal['files'],'actual_cases':[actual_cases,22],'stored_finite_controls':len(audit['negative_controls']),'support_adapter_reexecuted':True})
  transaction('candidate50','candidate51',j('checkpoint19-owner-review/owner-coordinated-integration.json'),['R33','TP1','U14'])
  transaction('candidate50','B03',j(manifest['sources']['B03']['workspace_path']+'/native-coordinated-integration.json'),['R33','TP1','U14'])
  for field in ('added_objects','removed_objects','changed_objects'):
   bad=copy.deepcopy(j('checkpoint19-owner-review/owner-coordinated-integration.json'));bad[field]=bad[field][1:]
   reject('parsed cumulative transaction omitted '+field,lambda bad=bad:transaction('candidate50','candidate51',bad,['R33','TP1','U14']))
  report=j('checkpoint19-owner-review/owner-coordinated-integration.json');before=identity['expected_boards']['candidate50'];after=identity['expected_boards']['candidate51'];assert adopt_verify.verify(report,before,after)
  for key,value in [('schema','bad'),('passed',False),('source_board_sha256','0'*64),('board_sha256','0'*64),('allowed_changed_nets',[])]:
   bad=copy.deepcopy(report);bad[key]=value;reject('cumulative adoption '+key,lambda bad=bad:adopt_verify.verify(bad,before,after));adoption_controls.append(key)
  assert 'AssertionError' in (tmp/'checkpoint19-review/coordinated.log').read_text()
  p=j('ordinary-routing/candidate51/reference-runtime-index-proof-v2.json');assert p['schema']=='f722-critical-reference-runtime-net-index-proof/v2' and p['passed'] and p['before_board_sha256']==before and p['board_sha256']==after
  assert p['verifier_sha256']==original('integrated-routing/verify_reference_runtime_indices.py') and p['raw_critical_object_geometry_identical'] is False and p['critical_physical_records_exact_except_runtime_net_code']
  assert p['critical_record_count']==153 and p['raw_difference_count']==147 and p['runtime_net_mapping_bijections_verified'] and p['each_raw_difference_is_only_net_code'] and p['all_critical_reference_net_reports_exact'] and p['all_numeric_projection_deltas_exactly_zero']
  assert p['all_saved_zone_records_exact'] is False and len(p['negative_controls'])==10 and all(r['rejected'] and r['verifier_invoked'] and r['metadata_hashes_rebound_after_mutation']for r in p['negative_controls'])
  compatibility=j('integrated-routing/runtime-index-v2-compatibility.json');assert compatibility['historical_v1_output_exact'] and len(compatibility['five_binding_refusals'])==5
  direct=j('ordinary-routing/candidate52/critical-projection-preservation.json');comparison=j('checkpoint17-owner-review/comparison-19-to-17.json');ref=j('checkpoint17-owner-review/reference-change-review.json')
  assert direct['numeric_deltas_retained']==comparison['net_numeric_deltas_after_minus_before'] and direct['numeric_deltas_retained']['BARO_SDA']['physical_GND_trace_width_missing_mm2']==-2.3792756653762126e-10
  assert direct['critical_objects_exact'] and direct['all_missing_centerline_geometries_equal'] and direct['all_outside_own_windows_geometries_equal'] and direct['all_changed_geometry_confined_to_own_windows'] and direct['maximum_actual_lost_ground_width_area_mm2']==0
  assert ref['passed'] and ref['comparison_sha256']==original('checkpoint17-owner-review/comparison-19-to-17.json')
  assert j('ordinary-routing/candidate51/combined-signal-reference-review.json')['all_new_tracks_reference_complete_outside_explicit_own_via_windows']
  assert j('ordinary-routing/candidate52/new-route-reference-review.json')['all_new_tracks_reference_complete_outside_explicit_own_via_windows']
  for label,folder in [('candidate51','checkpoint19-final'),('candidate52','checkpoint17')]:
   r=j(folder+'-placement-reproduction/placement-reproduction.json');preview=j(folder+'-placement-preview/placement-preview-source.json');board=identity['expected_boards'][label]
   assert r['source_board_sha256']==preview['routed_board_sha256']==board and r['156_poses_exact'] and r['558_complete_native_pad_records_exact'] and r['paired_native_parity_passed']
   assert r['placement_json_sha256']==preview['poses_sha256']==original('ordinary-routing/'+label+'/poses-native.json')
   for name,h in preview['files_sha256'].items():assert original(folder+'-placement-preview/'+name)==h
  # Exact delta parser refusal controls require no native operation.
  d=read(packet/'candidate52.f722-heli.kicad_pcb.delta.json');base=(a.base_project/'f722-heli.kicad_pcb').read_bytes()
  for key,value in [('base_sha256','0'*64),('target_sha256','0'*64),('target_bytes',-1),('operations',[[len(base)+1,1]]),('base_transform','unsupported')]:
   bad=copy.deepcopy(d);bad[key]=value;reject('paired recovery '+key,lambda bad=bad:recovery.reconstruct(base,bad))
  reject('unsafe recovery path',lambda:recovery.relative_path('../escape'))
 result={'passed':True,'verifier_source_sha256':sha(__file__),'recovered_projects':projects,'raw_files_verified':len(index),'excluded_raw_files':len(excluded),'frozen_helpers':len(identity['frozen_helpers']),'original_source_hash_checks_performed':bool(a.historical_workspace),'negative_controls_passed':len(neg),'negative_controls':neg,'stages':stages,'pure_parser_transactions':parser_transactions,'cumulative_adoption_adapter_controls_reexecuted':adoption_controls,'stored_runtime_v2_controls_preserved':10,'stored_v1_binding_controls_preserved':5,'current_BARO_SDA_width_delta_preserved':-2.3792756653762126e-10,'native_pose_transform_or_placement_reproduction_reexecuted':False,'native_DRC_reference_finite_classifier_or_access_reexecuted':False,'native_replay_inputs_complete':False,'heavy_or_native_execution_performed':False,'numerical_power_and_VCAP_applicability':False,'hardware_or_fabrication_qualification':False,'source43_power_scope':'Historical source43/37 only','scope':'Hash-exact paired source recovery, sealed receipt/source binding, pure syntax-tree transaction comparison and original support/cumulative-adoption adapter replay. Stored native findings are evidence, not package-time reruns.'}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
