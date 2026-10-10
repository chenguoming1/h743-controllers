#!/usr/bin/env python3
"""Incremental standard-library paired recovery and receipt/parser checks; no native replay."""
import argparse, ast, copy, hashlib, importlib.util, json, re, sys, tempfile, types, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def module(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 if sys.flags.optimize:raise RuntimeError('Verification requires assertions enabled')
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--base-project',type=Path,required=True);ap.add_argument('--historical-workspace',type=Path);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
 ident=read(ROOT/'checks/v16-source-identity.json');recovery=module('recovery_v16',ROOT/'sessions/recovery-v16/rebuild_historical_source.py');raw=module('raw45',ROOT/'tests/checkpoint45/materialize.py')
 negatives=[];recovered=[]
 def reject(name,fn):
  try:fn()
  except (ValueError,KeyError,AssertionError,FileNotFoundError):negatives.append(name)
  else:raise AssertionError('Invalid input accepted: '+name)
 with raw.Evidence() as evidence,tempfile.TemporaryDirectory(prefix='v16-evidence-') as td:
  tmp=Path(td);j=evidence.json;index=evidence.index['files'];excluded=evidence.index['excluded_files'];rec=evidence.index['recovered_files'];c44='ordinary-routing/candidate44/';c45='ordinary-routing/candidate45/'
  def original(name):
   for group in [index,excluded,rec]:
    if name in group:return group[name]['sha256']
   raise KeyError(name)
  for name in index:
   evidence.put(name,tmp)
   if args.historical_workspace:assert sha(args.historical_workspace/name)==index[name]['sha256'],name
  for name in excluded:
   reject('excluded raw unavailable: '+name,lambda name=name:evidence.bytes(name))
   if args.historical_workspace:assert sha(args.historical_workspace/name)==excluded[name]['sha256'],name
  for label,digest in ident['expected_boards'].items():
   outputs=recovery.prepare_project(args.base_project.resolve(),label,ROOT/'sessions/recovery-v16');out=tmp/'ordinary-routing'/label
   for relative,data in outputs.items():
    dest=out/relative;dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():assert dest.read_bytes()==data
    dest.write_bytes(data)
   assert len(outputs)==61 and sha(out/'f722-heli.kicad_pcb')==digest
   recovered.append({'source':label,'board_sha256':digest,'paired_files':len(outputs)})
  for name,row in rec.items():assert sha(tmp/name)==row['sha256'] and (tmp/name).stat().st_size==row['bytes'],name
  source,board=ident['expected_boards']['candidate44'],ident['expected_boards']['candidate45']
  handoff=j(c45+'route-handoff.json');assert original(c45+'route-handoff.json')==ident['sealed_handoff_sha256']
  assert len(handoff['files'])==ident['sealed_dependencies']
  for name,digest in handoff['files'].items():assert original(c45+name)==digest,name
  assert handoff['board_sha256']==board and handoff['integration_source_sha256']==source
  assert handoff['completed_net']=='NRST' and handoff['completed_terminals']==['C10.1','R1.2','TP5.1','U1.7']
  assert handoff['retained_native_track_via_arc_objects_exact']==1381 and handoff['all_other_155_footprints_exact']
  assert handoff['removed_source_objects']==0 and handoff['added_native_objects']==2
  assert (handoff['actual_io_passed'],handoff['actual_io_total'],handoff['actual_io_channels_passed'],handoff['actual_io_channels_total'])==(11,22,9,20)
  # The sealed worker handoff remains pending; the separate later owner receipt records adoption.
  assert handoff['owner_adoption_pending'] is True
  native,adoption=j(c45+'owner-summary.json'),j(c45+'owner-adoption.json')
  assert native['drc']==native['drc-all']==dict(unconnected=34,errors=0,warnings=0)
  assert native['board_sha256']==adoption['board_sha256']==board and adoption['native_unfinished_connections']==34
  assert adoption['numerical_applicability'] is False
  for field,name in [('native_gate_receipt_sha256',c45+'owner-summary.json'),('integration_receipt_sha256','checkpoint34-review/owner-coordinated-integration.json'),('reference_comparison_sha256','checkpoint34-review/comparison-35-to-34.json'),('actual_io_receipt_sha256',c45+'protection-actual-io.json')]:assert adoption[field]==original(name)
  for section in ['process','mechanical','parity','firmware']:assert native[section]['passed'] and native[section]['board_sha256']==board
  assert native['critical']['connected_nets']==native['critical']['total_nets']==16
  assert not native['critical']['faults'] and not native['critical']['missing_ground_returns']
  actual=j('checkpoint34-review/actual-io22.json');assert actual['board_sha256']==board and (actual['passed'],actual['total'],actual['all_pass'])==(11,22,False)
  construction=j(c45+'construction-provenance.json');transaction=j(c45+'coordinated-change-receipt.json')
  assert construction['source_board_sha256']==transaction['source_board_sha256']==source and construction['board_sha256']==transaction['board_sha256']==board
  assert construction['constructor_sha256']==original(c45+'construct.used.py')==original('ordinary-routing/tests/debug-testpoint44/construct.py')
  assert construction['removed_source_records']==transaction['removed_source_records']==[]
  assert construction['added_records']==transaction['added_candidate_records'] and len(construction['added_records'])==2
  assert construction['changed_pad_records']==transaction['changed_pad_records'] and len(construction['changed_pad_records'])==1
  assert construction['changed_footprint_records']==transaction['changed_footprint_records'] and len(construction['changed_footprint_records'])==1
  assert construction['all_other_source_native_objects_exact_except_net_code']==transaction['all_other_source_objects_exact_except_runtime_net_code']==1938
  assert construction['all_other_155_footprints_exact'] and construction['all_existing_route_copper_exact'] and construction['new_vias']==0
  assert not construction['numerical_power_VCAP_applicable'] and not transaction['engine_success_claimed']
  for name,digest in j(c45+'input-hashes.json').items():assert original(name)==digest,name
  audit=j(c45+'entry-support-audit.json');wrapper=j(c45+'power-audit.json');prior=j(c44+'power-audit.json')
  def full_binding(w,a):
   assert w['schema']=='f722-native-support-audit/v1' and w['passed'] is a['passed'] is True
   assert w['board_sha256']==a['board_sha256']==board and w['source_board_sha256']==a['source_board_sha256']==source
   assert w['native_sha256']==a['native_sha256']==original(c45+'f722-heli.native.json')
   assert w['source_native_sha256']==a['source_native_sha256']==original(c44+'f722-heli.native.json')
   assert w['audit']=='entry-support-audit.json' and w['audit_sha256']==original(c45+'entry-support-audit.json')
   assert w['audit_source_sha256']==a['audit_source_sha256']==original(c45+'audit.used.py')==original('ordinary-routing/tests/debug-testpoint44/audit.py')
   assert w['source_audit_sha256']==original(c44+'power-audit.json')
   assert len(a['gates'])==9 and all(v is True for v in a['gates'].values())
   assert not w['numerical_power_VCAP_applicable'] and not a['numerical_power_VCAP_applicable']
   assert len(w['nets'])==len(a['nets'])==len(prior['nets'])==28 and w['nets']==a['nets']
   for n,row in w['nets'].items():assert row['complete'] is True and row['source_groups_exactly_preserved'] is True and row['pad_group_count']==1 and row['groups']==prior['nets'][n]['groups']
  full_binding(wrapper,audit)
  for field,value in [('board_sha256',source),('native_sha256','0'*64),('audit_sha256','0'*64),('source_audit_sha256','0'*64),('audit_source_sha256','0'*64),('numerical_power_VCAP_applicable',True)]:
   bad=copy.deepcopy(wrapper);bad[field]=value;reject('portable wrapper binding '+field,lambda bad=bad:full_binding(bad,audit))
  support=module('support45',tmp/'integrated-routing/verify_support_adoption.py');compat=support.verify(wrapper,prior,source,board,tmp/c45)
  assert compat=={'passed':True,'nets':28,'typed_audit_binding_checked':False}
  saved=j(c45+'support-wrapper-compatibility.json');assert saved['support_wrapper_sha256']==original(c45+'power-audit.json') and saved['verifier_sha256']==original('integrated-routing/verify_support_adoption.py') and all(saved[k]==v for k,v in compat.items())
  assert len(audit['strict_pad_entries'])==3 and all(x['passed'] and x['width_mm']==.127 for x in audit['strict_pad_entries'])
  assert len(audit['full_width_joins'])==len(audit['finite_actual_annular_entries'])==1
  assert audit['full_width_joins'][0]['passed'] and audit['finite_actual_annular_entries'][0]['passed']
  assert len(audit['NRST_source_groups'])==2 and audit['NRST_current_groups'][0]['pads']==['C10.1','R1.2','TP5.1','U1.7'] and len(audit['NRST_current_groups'])==1
  probe=audit['probe_access'];assert probe['passed'] and probe['xy_mm']==[16.9,6.0] and probe['side']=='B.Cu' and probe['analytic_probe_clear_disk_diameter_mm']==1.4
  assert min(x['radial_probe_margin_mm'] for x in probe['nearest_bodies'])>0
  assert len(audit['negative_controls'])==5 and all(x['rejected'] for x in audit['negative_controls'])
  # Pure parser checks exact retained native board structures; no pcbnew/GEOS is imported.
  path=tmp/'ordinary-routing/tests/mpn-parity/apply_metadata_copy.py';parsed_module=ast.parse(path.read_text());wanted={'Atom','Node','parse','children','child','value','properties','shape'}
  nodes=[n for n in parsed_module.body if (isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in wanted) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TOKEN' for t in n.targets))]
  parser=types.ModuleType('portable_kicad_parser');parser.__dict__.update(re=re,json=json);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),parser.__dict__)
  parsed={label:parser.parse((tmp/'ordinary-routing'/label/'f722-heli.kicad_pcb').read_text()) for label in ['candidate44','candidate45']}
  def copper(root):return {parser.value(n,'uuid'):n for k in ['segment','via','arc'] for n in parser.children(root,k)}
  old,new=copper(parsed['candidate44']),copper(parsed['candidate45']);assert old.keys()<=new.keys() and len(old)==1381
  assert all(parser.shape(v)==parser.shape(new[k]) for k,v in old.items())
  added=set(new)-set(old);assert len(added)==2 and added=={x['uuid'] for x in construction['added_records']}
  points=[[16.9,6.0],[17.12882,6.22882],[17.12882,6.83933]]
  for i,(start,end) in enumerate(zip(points,points[1:])):
   uid=str(uuid.uuid5(uuid.NAMESPACE_URL,source+'/debug-testpoint44/NRST/'+str(i)));n=new[uid]
   assert uid in added and n.items[0].value=='segment' and parser.value(n,'net')=='NRST' and parser.value(n,'layer')=='B.Cu' and float(parser.value(n,'width'))==.127
   assert [float(v.value) for v in parser.child(n,'start').items[1:]]==start and [float(v.value) for v in parser.child(n,'end').items[1:]]==end
  footprints={k:{parser.properties(n)['Reference'].items[2].value:n for n in parser.children(v,'footprint')} for k,v in parsed.items()}
  assert len(footprints['candidate44'])==len(footprints['candidate45'])==156
  changed=[k for k,v in footprints['candidate44'].items() if parser.shape(v)!=parser.shape(footprints['candidate45'][k])];assert changed==['TP5']
  for label,pose in [('candidate44',[37.,23.8]),('candidate45',[16.9,6.])]:
   fp=footprints[label]['TP5'];assert [float(v.value) for v in parser.child(fp,'at').items[1:3]]==pose
   assert parser.value(fp,'layer')==('F.Cu' if label=='candidate44' else 'B.Cu')
   assert sum(len(parser.children(f,'pad')) for f in footprints[label].values())==558
  before_map,after_map=j(c44+'f722-heli.logical-route-map.json'),j(c45+'f722-heli.logical-route-map.json')
  assert after_map['logical_route_map']==dict(before_map['logical_route_map'],**{u:'NRST' for u in added})
  assert set(j(c45+'fixed-explicit-native-ids.json'))==set(j(c44+'fixed-explicit-native-ids.json'))|added
  poses0,poses1=j(c44+'poses-native.json'),j(c45+'poses-native.json');assert poses0['TP5']==[37.,23.8,0.,'F.Cu'];poses0['TP5']=[16.9,6.,0.,'B.Cu'];assert poses0==poses1
  for row in j(c45+'project-input-preservation.json')['files']:assert sha(tmp/c44/row['path'])==sha(tmp/c45/row['path'])==row['sha256']
  # Preserve raw false comparator; validate separate proof binding using exact hashes and saved reports.
  comparison=j('checkpoint34-review/comparison-35-to-34.json');assert comparison==j(c45+'reference-comparison44.json')
  proof=j(c45+'reference-runtime-index-proof.json');owner=j('checkpoint34-review/owner-runtime-index-verification.json')
  required_controls={'reject_net_change','reject_width_change','reject_uuid_change','reject_start_change','reject_copper_polygon_change','reject_omitted_UUID'}
  def proof_binding(p):
   assert p['schema']=='f722-exact-reference-runtime-net-index-proof/v1' and p['passed'] is True
   assert p['before_board_sha256']==comparison['before_board_sha256']==source and p['board_sha256']==comparison['after_board_sha256']==board
   assert p['raw_comparison_sha256']==original('checkpoint34-review/comparison-35-to-34.json')
   for prefix,folder in [('before',c44+'reference-snapshot/'),('after',c45+'reference-snapshot/')]:
    assert p[prefix+'_native_sha256']==original(folder+'native-geometry.json') and p[prefix+'_report_sha256']==original(folder+'critical-reference.json')
   assert p['script_sha256']==original(c45+'prove_reference_identity.used.py')==original('ordinary-routing/tests/debug-testpoint44/prove_reference_identity.py')
   assert p['critical_record_count']==153 and p['raw_difference_count']==83
   assert p['raw_critical_object_geometry_identical'] is comparison['critical_object_geometry_identical'] is False
   assert p['critical_physical_records_exact_except_runtime_net_code'] and p['each_raw_difference_is_only_net_code']
   diffs=p['raw_runtime_net_index_differences'];assert len(diffs)==83 and sorted(x['uuid'] for x in diffs)==comparison['critical_object_differences'] and all(x['changed_fields']==['net_code'] and x['before_net_code']!=x['after_net_code'] for x in diffs)
   assert {x['name'] for x in p['negative_controls'] if x['rejected'] is True}==required_controls
  proof_binding(proof)
  for field,value in [('board_sha256','0'*64),('raw_comparison_sha256','0'*64),('before_native_sha256','0'*64),('critical_record_count',152),('negative_controls',[])]:
   bad=copy.deepcopy(proof);bad[field]=value;reject('portable reference receipt binding '+field,lambda bad=bad:proof_binding(bad))
  assert original('checkpoint34-review/owner-runtime-index-verification.json')==ident['owner_review_sha256']
  assert len(owner['binding_negative_controls'])==5 and {x['mutation'] for x in owner['binding_negative_controls']}=={'board_sha256','raw_comparison_sha256','before_native_sha256','critical_record_count','negative_controls'} and all(x['rejected'] for x in owner['binding_negative_controls'])
  assert owner['passed'] and owner['receipt_sha256']==original(c45+'reference-runtime-index-proof.json') and owner['net_index_only_differences']==83
  assert all(owner[k]==v for k,v in adoption['reference_runtime_index_review'].items())
  assert j(c44+'reference-snapshot/critical-reference.json')['nets']==j(c45+'reference-snapshot/critical-reference.json')['nets']==j('checkpoint34-review/snapshot/critical-reference.json')['nets']
  assert all(v==0 for row in comparison['net_numeric_deltas_after_minus_before'].values() for v in row.values())
  assert all(x['physical_GND_lost_mm2']==x['physical_GND_gained_mm2']==0 for x in comparison['ground_fill_changes'].values())
  for folder in [c44+'reference-snapshot/',c45+'reference-snapshot/','checkpoint34-review/snapshot/']:
   report=j(folder+'critical-reference.json');signals=j(folder+'native-signals.json')
   assert signals['geometry_sha256']==report['sources']['native-geometry.json']==original(folder+'native-geometry.json')
   assert report['sources']['native-signals.json']==original(folder+'native-signals.json') and signals['source_unchanged'] is True
  for name,row in ident['frozen_owner_helpers'].items():assert original('integrated-routing/'+name)==row['sha256']
  repro=j('repro-34-placement/placement34-reproduction.json');assert repro['source_board_sha256']==board and repro['156_poses_exact'] and repro['558_complete_native_pad_records_exact'] and repro['paired_native_parity_passed']
  assert repro['placement_json_sha256']==original('repro-34-placement/placement.json')==original(c45+'poses-native.json') and repro['builder_sha256']==original('repro-34-placement/scripts/rebuild_placement.py')
  preview=j('checkpoint34-placement-preview/placement-preview-source.json');assert preview['routed_board_sha256']==board and preview['source_unchanged'] and preview['poses_sha256']==original(c45+'poses-native.json')
  for name,digest in preview['files_sha256'].items():assert original('checkpoint34-placement-preview/'+name)==digest
  assert j(c45+'i2c-geometry-review.json')['I2C_final_status']=='NOT_QUALIFIED'
  status=read(ROOT/'status.json');assert status['native_open_connections']==34 and not status['numerical_power_and_VCAP_applicability'] and not status['fabrication_ready']
  base=(args.base_project/'f722-heli.kicad_pcb').read_bytes();delta=read(ROOT/'sessions/recovery-v16/candidate45.f722-heli.kicad_pcb.delta.json')
  for name,bb,dd in [('wrong recovery source',base+b'\n',delta),('wrong target digest',base,dict(delta,target_sha256='0'*64)),('invalid range',base,dict(delta,operations=[[0,len(base)+1]])),('invalid operation',base,dict(delta,operations=[{}]))]:reject(name,lambda bb=bb,dd=dd:recovery.reconstruct(bb,dd))
  for name in ['../escape','/absolute','safe/../escape','windows\\escape']:reject('unsafe evidence path '+name,lambda name=name:raw.safe(name))
 result={'passed':True,'verifier_source_sha256':sha(__file__),'scope':'Incremental exact paired 44/45 recovery, sealed dependency hashes, exact parsed 1381 retained copper objects and 155 unchanged footprints, 2 deterministic NRST tracks, source-bound saved receipts, established support-adapter replay. Full native/probe/placement/runtime-geometry checks preserved, not rerun.','recovered_projects':recovered,'raw_files_verified':len(index),'excluded_raw_files':len(excluded),'negative_controls_passed':len(negatives),'negative_controls':negatives,'original_source_hash_checks_performed':bool(args.historical_workspace),'sealed_handoff_byte_exact':True,'all_sealed_dependency_bytes_included':False,'actual_owner_support_adapter_reexecuted':True,'owner_native_transaction_verifier_reexecuted':False,'owner_runtime_geometry_verifier_reexecuted':False,'raw_reference_comparator_false_preserved':True,'raw_runtime_net_index_differences':83,'physical_reference_records_in_saved_proof':153,'parsed_retained_copper_objects':1381,'parsed_exact_unchanged_footprints':155,'parsed_total_footprints':156,'parsed_total_pads':558,'added_tracks':2,'new_vias':0,'removed_objects':0,'preserved_worker_physical_mutation_controls':6,'preserved_owner_source_refusal_controls':5,'preserved_finite_probe_controls':5,'native_replay_inputs_complete':False,'full_width_probe_geometry_audit_reexecuted':False,'native_transform_or_placement_reexecuted':False,'native_DRC_reexecuted':False,'JVM_router_refill_or_power_solve_executed':False,'numerical_power_and_VCAP_applicability':False,'I2C_electrical_status':'NOT_QUALIFIED','native_open_connections':34,'native_errors':0,'native_warnings':0}
 args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
