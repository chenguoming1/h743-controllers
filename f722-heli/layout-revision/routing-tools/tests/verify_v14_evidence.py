#!/usr/bin/env python3
"""Bounded standard-library V14 recovery and receipt checks; no native audit replay."""
import argparse,ast,contextlib,copy,hashlib,importlib.util,io,json,re,runpy,sys,tempfile,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base-project',type=Path,required=True);ap.add_argument('--historical-workspace',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 ident=read(ROOT/'checks/v14-source-identity.json');recovery=module('recovery43',ROOT/'sessions/recovery43/rebuild_historical_source.py');raw=module('raw43',ROOT/'tests/checkpoint43/materialize.py');neg=[];recovered=[]
 def reject(n,op):
  try:op()
  except (ValueError,KeyError,AssertionError,FileNotFoundError):neg.append(n)
  else:raise AssertionError('Invalid input accepted: '+n)
 with raw.Evidence() as e,tempfile.TemporaryDirectory(prefix='v14-evidence-') as td:
  tmp=Path(td);j=e.json;idx=e.index['files'];excluded=e.index['excluded_files'];rec=e.index['recovered_files'];c41='ordinary-routing/candidate41/';c42='ordinary-routing/candidate42/';c43='ordinary-routing/candidate43/'
  def original(n):
   for group in [idx,excluded,rec]:
    if n in group:return group[n]['sha256']
   raise KeyError(n)
  for n in idx:
   e.put(n,tmp)
   if a.historical_workspace:assert sha(a.historical_workspace/n)==idx[n]['sha256'],n
  for n in excluded:
   reject('excluded raw bytes unavailable: '+n,lambda n=n:e.bytes(n))
   if a.historical_workspace:assert sha(a.historical_workspace/n)==excluded[n]['sha256'],n
  for label,digest in ident['expected_boards'].items():
   outputs=recovery.prepare_project(a.base_project.resolve(),label,ROOT/'sessions/recovery43');out=tmp/'ordinary-routing'/label
   for path,data in outputs.items():
    p=out/path;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==data
    p.write_bytes(data)
   assert len(outputs)==61 and sha(out/'f722-heli.kicad_pcb')==digest
   recovered.append({'source':label,'board_sha256':digest,'paired_files':len(outputs)})
  h=j(c43+'route-handoff.json');assert original(c43+'route-handoff.json')==ident['sealed_handoff_sha256'] and len(h['files'])==54
  for n,d in h['files'].items():assert original(c43+n)==d,n
  ad=j(c43+'owner-adoption.json');native=j(c43+'owner-summary.json');board=ident['expected_boards']['candidate43'];source=ident['expected_boards']['candidate41']
  assert native['drc']==native['drc-all']==dict(unconnected=37,errors=0,warnings=0)
  assert ad['board_sha256']==native['board_sha256']==board and ad['native_unfinished_connections']==37 and not ad['numerical_applicability']
  for field,n in [('native_gate_receipt_sha256',c43+'owner-summary.json'),('integration_receipt_sha256','checkpoint37-review/owner-coordinated-integration.json'),('reference_comparison_sha256','checkpoint37-review/comparison-41-to-37.json'),('actual_io_receipt_sha256',c43+'protection-actual-io.json')]:assert ad[field]==original(n)
  audit=j(c43+'i2c-entry-support-audit.json');assert audit['passed'] and len(audit['gates'])==12 and all(v is True for v in audit['gates'].values())
  assert audit['strict_pad_entries_all_pass'] is False and len(audit['direct_pad_entry_failures_preserved'])==2
  assert all(x['passed'] is False and x['pad']=='R8.1' for x in audit['direct_pad_entry_failures_preserved'])
  corridors=audit['explicit_R8_retained_junction']['corridors'];assert len(corridors)==2
  for x in corridors:assert x['passed'] and x['direct_pad_entry_remains_false'] and x['width_mm']==.2 and x['length_mm']>0 and x['area_outside_actual_copper_mm2']==0 and x['minimum_boundary_reserve_mm']>0
  assert len(audit['negative_controls'])==8 and all(x['rejected'] for x in audit['negative_controls'])
  narrow=[x for x in audit['negative_controls'] if 'section_only_rejected' in x];assert len(narrow)==2 and all(x['section_only_rejected'] is False and x['full_native_width_join_guard']['passed'] is False and x['rejected'] is True for x in narrow)
  old_control=j(c43+'isolated42-section-only-control-refusal.json');assert old_control['passed'] is False
  old_direct=j(c43+'isolated42-direct-entry-refusal.json');assert old_direct['passed'] is False
  geometry=j(c43+'i2c-geometry-review.json');oldgeo=j(c43+'isolated42-topology-refusal.json')
  assert geometry['I2C_final_status']=='NOT_QUALIFIED' and oldgeo['nets']['BARO_SDA']['topology']['supported'] is False
  for n in ['BARO_SCL','BARO_SDA']:
   t=geometry['nets'][n]['topology'];assert t['supported'] and t['component_count']==1 and t['cycle_rank']==0 and t['native_all_copper_connected'] and t['native_all_terminals_connected']
  r=j(c43+'intentional-i2c-review/intentional-i2c-acceptance.json');assert r['source41_board_sha256']==source and r['board_sha256']==board
  assert r['eligible_for_geometric_WIP_adoption'] and not r['electrical_qualified'] and r['fresh_power_VCAP_numerical_revalidation_required'] and len(r['guards'])==10 and all(r['guards'].values())
  for n,d in r['sources'].items():assert original(n)==d,n
  comparison=j('checkpoint37-review/comparison-41-to-37.json');assert comparison['critical_object_geometry_identical'] is False
  metrics=comparison['net_numeric_deltas_after_minus_before'];assert len(metrics)==12 and all(all(v==0 for v in row.values()) for n,row in metrics.items() if n not in {'BARO_SCL','BARO_SDA'})
  assert r['I2C_reference_totals']['BARO_SCL']['physical_missing_trace_width_mm2_by_class']['saved_void_or_edge_outside_own_window']>0
  reserves=j(c43+'nominal-clearance-reserves.json');assert not reserves['manufacturing_tolerance_allowance_claimed'] and len(reserves['rules'])==2 and all(x['nominal_actual_mm']>x['required_mm']==.127 for x in reserves['rules'])
  transaction=j(c43+'coordinated-change-receipt.json');assert transaction['passed'] and len(transaction['removed_source_records'])==7 and len(transaction['added_candidate_records'])==41 and len(transaction['changed_pad_records'])==6 and len(transaction['changed_footprint_records'])==3 and transaction['all_other_source_objects_exact']==1857
  assert not transaction['engine_success_claimed'] and not transaction['numerical_power_VCAP_applicable']
  construction=j(c43+'construction-provenance.json');cleanup=construction['topology_cleanup'];assert len(cleanup['removed_stage_records'])==len(cleanup['added_stage_records'])==5 and cleanup['poses_vias_power_objects_exact_to42']
  assert construction['constructor_sha256']==original(c43+'construct_i2c_topology43.py') and construction['source42_construction_receipt_sha256']==original(c42+'construction-provenance.json')
  for name,d in cleanup['screen_inputs'].items():assert original('ordinary-routing/tests/i2c-candidate39-portc/'+name)==d
  assert construction['final_portal_proposal_sha256']==original('ordinary-routing/tests/i2c-candidate39-portc/small-cap-portal-screen.json')
  # Source39 staging stays explicit and is not promoted to an adopted board.
  stages=[('i2c-native-stage39','stage_i2c_native39.py',{'proposal_sha256':'i2c-candidate39-local/selected-i2c-rebind39.json'}),('i2c-native-stage39-master-sda','stage_i2c_master_sda39.py',{'R7_proposal_sha256':'i2c-candidate39-master-pullup/selected-R7-master39.json','SDA_proposal_sha256':'i2c-candidate39-joint/sda-native-bridge-proposal.json','feed_cleanup_proposal_sha256':'i2c-candidate39-joint/relocated-R7-feed-cleanup-proposal.json'}),('i2c-native-stage39-complete-trunks','stage_i2c_complete_trunks39.py',{'proposal_sha256':'i2c-candidate39-joint/current-scl-native-bridge-proposal.json'})]
  for label,script,proposals in stages:
   provenance=j('ordinary-routing/'+label+'/construction-provenance.json');assert provenance['constructor_sha256']==original('ordinary-routing/'+script) and provenance['board_sha256']==ident['expected_boards'][label]
   for field,name in proposals.items():assert provenance[field]==original('ordinary-routing/tests/'+name)
   assert provenance['numerical_power_VCAP_applicable'] is False and provenance['direct_engine_output'] is False
  # Load the unchanged owner's pure KiCad parser only; do not import pcbnew.
  path=tmp/'ordinary-routing/tests/mpn-parity/apply_metadata_copy.py';tree=ast.parse(path.read_text());wanted={'Atom','Node','parse','children','child','value','properties','shape'}
  nodes=[n for n in tree.body if (isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in wanted) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TOKEN' for t in n.targets))]
  parser=types.ModuleType('apply_metadata_copy');parser.__dict__.update(re=re,json=json);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),parser.__dict__)
  sys.modules['apply_metadata_copy']=parser
  parsed={label:parser.parse((tmp/'ordinary-routing'/label/'f722-heli.kicad_pcb').read_text()) for label in ['candidate41','candidate42','candidate43']}
  def copper(root):return {parser.value(x,'uuid'):parser.shape(x) for kind in ['segment','via','arc'] for x in parser.children(root,kind)}
  boards={k:copper(v) for k,v in parsed.items()}
  for before,after,removed,added in [('candidate41','candidate42',j(c42+'construction-provenance.json')['removed_source_records'],j(c42+'construction-provenance.json')['added_candidate_records']),('candidate42','candidate43',cleanup['removed_stage_records'],cleanup['added_stage_records']),('candidate41','candidate43',transaction['removed_source_records'],transaction['added_candidate_records'])]:
   b,n=boards[before],boards[after];rem={x['uuid'] for x in removed};add={x['uuid'] for x in added};assert set(b)-set(n)==rem and set(n)-set(b)==add and all(n[k]==v for k,v in b.items() if k not in rem)
  owner=j('checkpoint37-review/owner-coordinated-integration.json')
  for x in owner['removed_objects']:assert boards['candidate41'][x['uuid']]==x['before']
  for x in owner['added_objects']:assert boards['candidate43'][x['uuid']]==x['after']
  assert not owner['changed_objects'] and len(owner['removed_objects'])==7 and len(owner['added_objects'])==41
  def footprints(root):return {parser.properties(f)['Reference'].items[2].value:f for f in parser.children(root,'footprint')}
  fps={k:footprints(v) for k,v in parsed.items()};assert all(len(x)==156 for x in fps.values())
  assert {n for n in fps['candidate41'] if parser.shape(fps['candidate41'][n])!=parser.shape(fps['candidate43'][n])}=={'R7','R8','C69'}
  assert all(parser.shape(fps['candidate42'][n])==parser.shape(fps['candidate43'][n]) for n in fps['candidate42'])
  semantic=hashlib.sha256(json.dumps([parser.shape(f) for f in parser.children(parsed['candidate43'],'footprint')],separators=(',',':')).encode()).hexdigest()
  assert semantic==owner['footprint_transform_review']['predicted_footprint_semantic_sha256']
  declaration=j('integrated-routing/declared-transforms41-to43.json');assert declaration['board_sha256']==board and declaration['source_board_sha256']==source
  assert owner['footprint_transform_review']['declaration_sha256']==original('integrated-routing/declared-transforms41-to43.json')
  assert declaration['changes']['R7']['flip_left_right'] is False
  # Rerun the exact typed support adapter and all seven of its independent controls.
  sys.path.insert(0,str(tmp/'integrated-routing'))
  with contextlib.redirect_stdout(io.StringIO()):runpy.run_path(str(tmp/'integrated-routing/test_support_i2c_adoption.py'),run_name='__main__')
  controls=read(tmp/'integrated-routing/support-i2c-adoption-controls.json');assert controls==j('integrated-routing/support-i2c-adoption-controls.json') and len(controls['controls'])==7 and all(x['rejected'] for x in controls['controls']);neg.extend('typed support: '+x['name'] for x in controls['controls'])
  assert len(j('integrated-routing/intentional-i2c-controls.json')['controls'])==9 and len(j('integrated-routing/footprint-transform-controls.json')['controls'])==10
  assert all(x['rejected'] for name in ['intentional-i2c-controls.json','footprint-transform-controls.json'] for x in j('integrated-routing/'+name)['controls'])
  for x in j(c43+'project-input-preservation.json')['files']:assert sha(tmp/c43/x['path'])==x['sha256']
  b=(tmp/c43/'f722-heli.kicad_pcb').read_bytes()
  for name,path in [('placement-preview.pcb.delta.json','checkpoint37-placement-preview/preview.kicad_pcb'),('recipe-placement.pcb.delta.json','repro-37-placement/hardware/f722-heli.kicad_pcb')]:
   data=recovery.reconstruct(b,read(ROOT/'sessions/recovery43'/name));assert hashlib.sha256(data).hexdigest()==original(path);tree=parser.parse(data.decode());assert len(parser.children(tree,'footprint'))==156
   if name.startswith('placement-preview'):assert not parser.children(tree,'segment') and not parser.children(tree,'via')
   else:
    recipe_fps=footprints(tree)
    assert sum(len(parser.children(fp,'pad')) for fp in recipe_fps.values())==558
    for ref,fp in fps['candidate43'].items():
     assert parser.shape(parser.child(fp,'at'))==parser.shape(parser.child(recipe_fps[ref],'at')) and parser.value(fp,'layer')==parser.value(recipe_fps[ref],'layer')
     assert [parser.shape(p) for p in parser.children(fp,'pad')]==[parser.shape(p) for p in parser.children(recipe_fps[ref],'pad')],ref
  recipe=j('repro-37-placement/placement37-reproduction.json');assert recipe['source_board_sha256']==board and recipe['156_poses_exact'] and recipe['558_complete_native_pad_records_exact'] and recipe['paired_native_parity_passed']
  assert recipe['builder_sha256']==original('repro-37-placement/scripts/rebuild_placement.py') and recipe['placement_json_sha256']==original(c43+'poses-native.json')==original('repro-37-placement/placement.json')
  preview=j('checkpoint37-placement-preview/placement-preview-source.json');visual=j('checkpoint37-placement-preview/visual-review.json');assert preview['routed_board_sha256']==visual['board_sha256']==board and preview['poses_sha256']==original(c43+'poses-native.json') and preview['source_unchanged']
  assert visual['preview_source_sha256']==original('checkpoint37-placement-preview/placement-preview-source.json')
  for collection in [preview['files_sha256'],visual['images_sha256']]:
   for n,d in collection.items():assert original('checkpoint37-placement-preview/'+n)==d
  base=(a.base_project/'f722-heli.kicad_pcb').read_bytes();delta=read(ROOT/'sessions/recovery43/candidate43.f722-heli.kicad_pcb.delta.json')
  for name,bb,dd in [('wrong recovery source',base+b'\n',delta),('wrong target digest',base,dict(delta,target_sha256='0'*64)),('invalid range',base,dict(delta,operations=[[0,len(base)+1]])),('invalid operation',base,dict(delta,operations=[{}]))]:reject(name,lambda bb=bb,dd=dd:recovery.reconstruct(bb,dd))
  for name in ['../escape','/absolute','safe/../escape','windows\\escape']:reject('unsafe evidence path '+name,lambda name=name:raw.safe(name))
  status=read(ROOT/'status.json');assert status['native_open_connections']==37 and not status['numerical_power_and_VCAP_applicability'] and not status['fabrication_ready']
 result={'passed':True,'verifier_source_sha256':sha(__file__),'scope':'Incremental exact paired byte recovery, exact source/evidence and sealed dependency bindings, parsed native copper transactions and footprint identities, typed owner support adapter plus its seven controls, exact recipe pad/pose and preview recovery. Historical full-width/reference/transform/native receipts checked for identity and stated results; their underlying native audits are not rerun.','recovered_projects':recovered,'raw_files_verified':len(idx),'excluded_raw_files':len(excluded),'negative_controls_passed':len(neg),'negative_controls':neg,'original_source_hash_checks_performed':bool(a.historical_workspace),'sealed_handoff_byte_exact':True,'sealed_dependency_digests_preserved':True,'all_sealed_dependency_bytes_included':False,'actual_owner_support_adapter_reexecuted':True,'native_footprint_transform_prediction_reexecuted':False,'owner_intentional_reference_helper_reexecuted':False,'historical_transform_controls_preserved':10,'historical_intentional_I2C_controls_preserved':9,'historical_geometric_controls_preserved':8,'recipe_558_complete_pad_records_rechecked':True,'parsed_copper_transactions_rechecked':True,'native_replay_inputs_complete':False,'real_reference_classifier_reexecuted':False,'full_width_geometric_audit_reexecuted':False,'native_DRC_reexecuted':False,'JVM_router_refill_or_power_solve_executed':False,'placement_render_reexecuted':False,'numerical_power_and_VCAP_applicability':False,'I2C_electrical_status':'NOT_QUALIFIED','native_open_connections':37,'native_errors':0,'native_warnings':0}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
