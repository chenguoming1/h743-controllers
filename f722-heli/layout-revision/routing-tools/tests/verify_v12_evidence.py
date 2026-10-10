#!/usr/bin/env python3
"""Incremental exact recovery/source/receipt controls for38→39; no native replay."""
import argparse,ast,copy,hashlib,importlib.util,json,re,tempfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base-project',type=Path,required=True);ap.add_argument('--historical-workspace',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 identity=read(ROOT/'checks/v12-source-identity.json');expected=identity['expected_boards'];recovery=module('recovery42',ROOT/'sessions/recovery42/rebuild_historical_source.py');raw=module('evidence42',ROOT/'tests/checkpoint42/materialize.py');negatives=[];recovered=[]
 def reject(label,op):
  try:op()
  except (ValueError,KeyError,AssertionError,FileNotFoundError):negatives.append(label)
  else:raise AssertionError('Accepted bad input: '+label)
 with raw.Evidence() as e,tempfile.TemporaryDirectory(prefix='v12-controls-') as td:
  tmp=Path(td);idx=e.index['files'];excluded=e.index['excluded_files'];j=e.json
  for n in idx:
   e.verify(n)
   if a.historical_workspace:assert sha(a.historical_workspace/n)==idx[n]['sha256'],n
  for n in excluded:
   reject('excluded input unavailable: '+n,lambda n=n:e.bytes(n))
   if a.historical_workspace:assert sha(a.historical_workspace/n)==excluded[n]['sha256'],n
  def orig(n):return (idx[n]if n in idx else excluded[n])['sha256']
  c38='ordinary-routing/candidate38/';c39='ordinary-routing/candidate39/'
  for c,opens in [(38,44),(39,42)]:
   pre=f'ordinary-routing/candidate{c}/';h=j(pre+'route-handoff.json');o=j(pre+'owner-summary.json');ad=j(pre+'owner-adoption.json')
   assert orig(pre+'route-handoff.json')==identity['sealed_handoffs'][str(c)]
   assert h['board_sha256']==o['board_sha256']==ad['board_sha256']==expected[f'candidate{c}']
   assert o['drc']==o['drc-all']==dict(unconnected=opens,errors=0,warnings=0)
   assert not ad['numerical_applicability'] and ad['native_unfinished_connections']==opens
   for n,want in h['files'].items():
    assert (expected[f'candidate{c}'] if n.endswith('.kicad_pcb') else orig(pre+n))==want,(c,n)
   assert ad['native_gate_receipt_sha256']==orig(pre+'owner-summary.json')
   assert j(pre+'endpoint-audit.json')['passed']
  assert len(j(c39+'route-handoff.json')['files'])==70
  construction=j(c38+'construction-provenance.json');assert construction['engine_result']=='FAILED' and not construction['direct_engine_output'] and not construction['engine_partial_geometry_adopted']
  coordinated=j(c39+'coordinated-change-receipt.json');assert coordinated['passed'] and not coordinated['engine_success_claimed'] and not coordinated['numerical_power_VCAP_applicable']
  assert len(coordinated['removed_source_records'])==13 and len(coordinated['added_candidate_records'])==46
  h=j(c39+'route-handoff.json');assert h['removed_tracks']==11 and h['removed_vias']==2 and h['added_tracks']==40 and h['added_vias']==6
  assert h['dedicated_GND_return']['both_saved_planes_full_annulus_and_bulk_corridor_verified']
  assert not h['dedicated_GND_return']['transient_qualification_claimed']
  assert len(j(c39+'protection-actual-io.json')['checks'])==22
  assert sum(x['complete_clamp_first_path_passes']for x in j(c39+'protection-actual-io.json')['checks'])==10
  for label in expected:
   outputs=recovery.prepare_project(a.base_project.resolve(),label,ROOT/'sessions/recovery42');out=tmp/'ordinary-routing'/label
   for path,data in outputs.items():p=out/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
   assert sha(out/'f722-heli.kicad_pcb')==expected[label] and len(outputs)==62
   recovered.append({'source':label,'board_sha256':expected[label],'paired_files':62})
  # Independently parse exact recovered native PCB records without pcbnew.
  tree=ast.parse((ROOT/'import_session_v8.py').read_text());ns={'re':re,'json':json};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in {'parse','children','child'}],type_ignores=[]),'pure-native-parser','exec'),ns)
  child=ns['child'];boards={}
  for label in expected:
   t=ns['parse']((tmp/'ordinary-routing'/label/'f722-heli.kicad_pcb').read_text());boards[label]={child(o,'uuid')[1]:o for o in t if isinstance(o,list)and o and o[0]in ['segment','via','arc']}
  b,n=boards['candidate37'],boards['candidate38'];assert all(n.get(u)==v for u,v in b.items());added=[v for u,v in n.items()if u not in b];assert sum(x[0]=='segment'for x in added)==20 and sum(x[0]=='via'for x in added)==1
  before,after=boards['candidate38'],boards['candidate39'];removed={o['uuid']for o in coordinated['removed_source_records']};added={o['uuid']for o in coordinated['added_candidate_records']}
  def transaction(b,a,rem,add):
   assert set(b)-set(a)==rem and set(a)-set(b)==add
   assert all(a.get(u)==v for u,v in b.items()if u not in rem)
  transaction(before,after,removed,added)
  reject('undeclared coordinated removal',lambda:transaction(before,after,set(),added))
  bad=copy.deepcopy(after);keep=next(u for u in before if u not in removed);bad[keep].append(['unexpected','edit']);reject('retained native record mutation',lambda:transaction(before,bad,removed,added))
  reject('undeclared coordinated addition',lambda:transaction(before,after,removed,set()))
  b=(a.base_project/'f722-heli.kicad_pcb').read_bytes();delta=read(ROOT/'sessions/recovery42/candidate39.f722-heli.kicad_pcb.delta.json')
  for name,source,d in [('wrong recovery source',b+b'\n',delta),('wrong target hash',b,dict(delta,target_sha256='0'*64)),('out-of-range copy',b,dict(delta,operations=[[0,len(b)+1]])),('invalid copy operation',b,dict(delta,operations=[{}]))]:reject(name,lambda source=source,d=d:recovery.reconstruct(source,d))
  for p in ['../escape','/absolute','safe/../escape','windows\\escape']:reject('unsafe path '+p,lambda p=p:raw.safe(p))
  for pre,prefix,refusal in [('ordinary-routing/model-servo23-stage38-ready/','servo_p1','unseeded-engine-refusal.json'),('ordinary-routing/model-servo23-stage38-exit-ready/','servo_p1_seed','seeded-engine-refusal.json')]:
   r=j(c39+refusal);assert r['completed_routes']==r['located_paths']==0 and r['engine_routes_exactly_equal_to_zero'] and r['session_byte_identical_to_zero']
   assert orig(pre+prefix+'.log')==r['log_sha256'];assert orig(pre+prefix+'.bounded-run.json')==r['bounded_run_sha256'];assert orig(pre+prefix+'.ses')==orig(pre+'zero.ses')
   ledger=j(pre+prefix+'.attempt-ledger.json');assert all(x['result']=='FAILED'for x in ledger['attempts'])
  ad=j(c39+'owner-adoption.json');clpath='checkpoint42-review/reference-region/owner/reference-classification.json';cl=j(clpath)
  assert ad['reference_window_classification']['classification_sha256']==orig(clpath)
  assert not cl['missing_centerline_geometries_exactly_equal'] and not cl['all_changed_critical_projection_geometry_inside_actual_hole_window_intersections']
  assert cl['exact_containment_predicate_disagreement_count']==4 and cl['classification_status']=='UNRESOLVED_ACTUAL_HOLE_BOUNDARY_PREDICATES'
  assert cl['all_changed_critical_projection_geometry_inside_unchanged_own_windows'] and cl['all_changed_critical_projection_residuals_outside_unchanged_own_windows_empty']
  for n,want in cl['source_hashes'].items():
   if n.endswith('.kicad_pcb'):assert sha(tmp/n)==want
   else:assert orig(n)==want
  # Original classification/owner binding receipts are preserved. Real geometry
  # inputs are excluded; no real classifier or complete-source helper replay claim.
  helper='integrated-routing/verify_reference_window_classification.py';e.put(helper,tmp);binding=module('binding42',tmp/helper)
  comparison=tmp/'synthetic-comparison.json';comparison.write_text('{}')
  fixture=dict(cl,source_hashes={'synthetic-comparison.json':sha(comparison)})
  path=tmp/'synthetic-classification.json';path.write_text(json.dumps(fixture))
  result=binding.verify(path,expected['candidate38'],expected['candidate39'],comparison,tmp)
  assert result['actual_hole_containment']is False and result['missing_centerline_geometries_exactly_equal']is False and result['actual_hole_predicate_disagreements']==4
  reject('synthetic wrong reference before hash',lambda:binding.verify(path,'0'*64,expected['candidate39'],comparison,tmp))
  reject('synthetic wrong reference after hash',lambda:binding.verify(path,expected['candidate38'],'0'*64,comparison,tmp))
  wrong=tmp/'wrong-comparison.json';wrong.write_text('[]');reject('synthetic unbound reference comparison',lambda:binding.verify(path,expected['candidate38'],expected['candidate39'],wrong,tmp))
  for key in ['source_binding_verified','all_changed_critical_projection_geometry_inside_unchanged_own_windows','all_changed_critical_projection_residuals_outside_unchanged_own_windows_empty']:
   bad=dict(fixture);bad[key]=False;path.write_text(json.dumps(bad));reject('synthetic false '+key,lambda:binding.verify(path,expected['candidate38'],expected['candidate39'],comparison,tmp))
  path.write_text(json.dumps(fixture));comparison.write_text('{}\n');reject('synthetic changed classification source',lambda:binding.verify(path,expected['candidate38'],expected['candidate39'],comparison,tmp))
  assert j(c39+'current-model-zero-parity.json')['passed']
  assert j(c39+'current-model-zero-import.json')['source_sha256']==j(c39+'current-model-zero-import.json')['output_sha256']==expected['candidate39']
  status=read(ROOT/'status.json');assert status['latest_owner_adopted_candidate']==39 and status['native_open_connections']==42 and not status['numerical_power_and_VCAP_applicability'] and not status['fabrication_ready']
 result={'passed':True,'verifier_source_sha256':sha(__file__),'scope':'Incremental selected source/receipt identities, exact62-file recoveries, parsed native transaction, selected failed-search evidence, original owner reference receipt bindings, synthetic helper rejection controls. Excluded raw inputs cannot be recovered or replayed by this packet.','recovered_projects':recovered,'raw_files_verified':len(idx),'negative_controls_passed':len(negatives),'negative_controls':negatives,'original_source_hash_checks_performed':bool(a.historical_workspace),'sealed_handoffs_byte_exact':True,'sealed_dependency_digests_preserved':True,'all_sealed_dependency_bytes_included':False,'owner_adoption_reference_receipts_bound':True,'real_reference_source_binding_reexecuted':False,'real_reference_classifier_reexecuted':False,'synthetic_reference_helper_controls_passed':True,'excluded_raw_files':len(excluded),'native_replay_inputs_complete':False,'strict_actual_hole_containment':False,'exact_centerline_equality':False,'actual_hole_predicate_disagreements':4,'native_DRC_reexecuted':False,'native_replay_reexecuted':False,'JVM_router_refill_or_power_solve_executed':False,'numerical_power_and_VCAP_applicability':False,'native_open_connections':42,'native_errors':0,'native_warnings':0}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
