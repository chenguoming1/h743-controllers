#!/usr/bin/env python3
"""Verify V8 compact provenance and exact recovery without native or JVM work.

The historical workspace is optional and verifies the projections against full
original receipts/models. It does not execute those models. Native import,
endpoint geometry audits, DRC, refill and numerical solves are not reexecuted.
"""
import argparse,ast,hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def run(args,ok=True):
 p=subprocess.run([str(x)for x in args],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True)
 assert (p.returncode==0)==ok,(args,p.stdout,p.stderr)
 return p

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base-project',type=Path,required=True);ap.add_argument('--historical-workspace',type=Path);a=ap.parse_args();a.base_project=a.base_project.resolve();a.historical_workspace=a.historical_workspace.resolve()if a.historical_workspace else None
 projections=load(ROOT/'checks/v8-portable-projections.json')['files']
 for name,row in projections.items():
  assert sha(ROOT/name)==row['portable_file_sha256'],name
  assert '/workspace/'not in (ROOT/name).read_text(),name
  if a.historical_workspace:assert sha(a.historical_workspace/row['historical_path'])==row['historical_file_sha256'],name
 identities=load(ROOT/'checks/v8-source-identity.json');assert identities['final_third_success_belongs_only_to26']and identities['unfinished_filtered02_excluded']
 for name,row in identities['sources'].items():
  if 'sha256'in row:assert sha(ROOT/row.get('package_source',name))==row['sha256']
 posehash=projections['checks/current-pose-targets.json']['historical_file_sha256']
 assert posehash=='9c84633da6de3d501d7ca258bcf4a8051b965af728929f8cd7587e20f73e2bae'
 for name in ['candidate24-owner-mechanical.json','candidate25-owner-mechanical.json','candidate25-worker-mechanical.json','candidate26-owner-mechanical.json']:
  m=load(ROOT/'checks'/name);assert m['passed']and m['input_hashes']['poses-native.json']==posehash
 worker=load(ROOT/'checks/candidate25-worker-summary.json')
 assert ['owner-mechanical',1]in worker['commands']and ['worker-mechanical-correct-current-poses',0]in worker['commands']
 refused=load(ROOT/'checks/candidate23-endpoint-audit.json');assert refused['passed']is False and len(refused['pad_failures'])==2 and not refused['via_failures']and not refused['unresolved_contacts']
 completion=load(ROOT/'checks/candidate24-pad-entry-completion.json');confinement=load(ROOT/'checks/candidate24-pad-entry-confinement.json')
 assert len(completion['extensions'])==2 and completion['new_vias']==0 and not completion['refill_performed']
 assert {r['original_route_uuid']for r in completion['extensions']}=={r['track_uuid']for r in refused['pad_failures']}
 assert completion['input_audit_sha256']==projections['checks/candidate23-endpoint-audit.json']['historical_file_sha256']
 assert confinement['passed']and all(r['outside_pad_new_copper_contained_in_previous_track']for r in confinement['rows'])
 assert set(load(ROOT/'checks/source24-fixed-pad-entry-ids.json'))=={r['uuid']for r in completion['extensions']}
 for c,opens in [(24,60),(25,58),(26,57)]:
  h=load(ROOT/f'checks/candidate{c}-route-handoff.json');owner=load(ROOT/f'checks/candidate{c}-owner-summary.json');end=load(ROOT/f'checks/candidate{c}-endpoint-audit.json');power=load(ROOT/('checks/candidate'+str(c)+'-'+('power-revalidation-required.json'if c==26 else 'unchanged-power-reference.json')))
  assert h['drc']==dict(unconnected=opens,errors=0,warnings=0,strict_schematic_parity=0)
  assert owner['drc']==dict(unconnected=opens,errors=0,warnings=0)
  assert end['passed']and end['summary']['pad_terminations_verified']==(2 if c==26 else 4) and not end['pad_failures']
  if c==26:
   assert power['numerical_applicability']is False and power['source25_fills_equal']is False and power['new_vias']==1
   assert end['summary']['full_width_actual_annular_strip_count']==2 and end['summary']['redundant_via_spurs_retained_as_non_evidence']==1
  else:assert power['passed']and power['all_footprints_poses_saved_zones_drills_and_power_domains_exact']and power['new_vias']==0
 reference=load(ROOT/'checks/candidate26-critical-reference-comparison.json');assert reference['critical_object_geometry_identical']and not reference['critical_object_differences']
 assert all(v==0 for row in reference['net_numeric_deltas_after_minus_before'].values()for v in row.values())
 assert all(row['lost_GND_overlap_with_trace_width_mm2']==0 for layer in reference['ground_fill_changes'].values()for row in layer['critical_trace_proximity'].values())
 for c in [22,24,26]:
  zero=load(ROOT/f'checks/source{c}-zero-parity.json');assert zero['passed']and not zero['errors']
 for c in [25,26]:
  adoption=load(ROOT/f'checks/candidate{c}-owner-adoption.json')
  for field,filename in [('native_gate_receipt_sha256','owner-summary.json'),('endpoint_receipt_sha256','endpoint-audit.json'),('additive_receipt_sha256','owner-additive-integration.json')]:
   assert adoption[field]==projections[f'checks/candidate{c}-'+filename]['historical_file_sha256']
  if c==26:
   assert adoption['numerical_applicability']is False
   assert adoption['reference_comparison_sha256']==projections['checks/candidate26-critical-reference-comparison.json']['historical_file_sha256']
 # Exact historical recovery includes all functional paired files and board
 # byte identities. It makes no fresh geometry/qualification claim.
 recovery_path=ROOT/'sessions/recovery57/rebuild_historical_source.py';spec=importlib.util.spec_from_file_location('v8_recovery',recovery_path);recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)
 recovered=[];packets=[];negative=0
 with tempfile.TemporaryDirectory(prefix='v8-evidence-',dir=ROOT.parent)as temp:
  tmp=Path(temp)
  for c in [22,23,24,25,26]:
   out=tmp/f'candidate{c}';run([sys.executable,'-B',recovery_path,'project','--base-project',a.base_project,'--source',f'candidate{c}','--out',out]);recovered.append({'candidate':c,'board_sha256':sha(out/'f722-heli.kicad_pcb'),'functional_paired_files':len(list(p for p in out.rglob('*')if p.is_file()))})
  for c,source,name in [(23,22,'engine60-refused23'),(25,24,'accepted58'),(26,25,'accepted57')]:
   packet=ROOT/'sessions'/name;identity=load(packet/'source-identity.json');board=tmp/f'candidate{source}/f722-heli.kicad_pcb';assert sha(board)==identity['board_sha256']
   assert sha(tmp/f'candidate{c}/f722-heli.kicad_pcb')==identity['candidate_sha256']
   assert sha(ROOT/identity['importer_source_path'])==identity['importer_source_sha256']
   funcs={'parse','children','child','ses_routes','nm','key','from_snapshot'}
   def parser(path):return [ast.dump(n,include_attributes=False)for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name in funcs]
   assert parser(ROOT/'import_session.py')==parser(ROOT/identity['importer_source_path'])
   resultpath=tmp/f'packet{c}.json';run([sys.executable,'-B','tests/verify_session_packet.py','--packet',packet,'--out',resultpath]);result=load(resultpath)
   contract=load(packet/'import-contract.json');report=load(packet/'engine-report.json');native=load(ROOT/identity['historical_native_import_receipt'])
   assert native['source_sha256']==identity['board_sha256']and native['output_sha256']==identity['candidate_sha256']and native['session_sha256']==identity['session_sha256']and native['model_sha256']==identity['model_sha256']
   assert native['routes_added']==identity['new_tracks']+identity['new_vias']and native['routes_removed']==0 and native['reference_plane_refill_performed']==(c==26)
   if c==25:
    receipt=load(packet/'selected-checkpoint-receipt.json');lineage=load(ROOT/'checks/candidate25-engine-lineage.json')
    assert receipt['session_sha256']==lineage['session_sha256']==identity['session_sha256']
    assert receipt['report_sha256']==lineage['actual_checkpoint_report_sha256']==identity['historical_engine_report_sha256']
    assert receipt['route_counters']['routed_count']==report['route_counters']['routed_count']==2
    assert lineage['actual_checkpoint'].endswith('/second')
    assert set(load(ROOT/'checks/source24-fixed-pad-entry-ids.json')).isdisjoint(contract['mutable_source_ids'])
   if c==26:
    receipt=load(packet/'selected-checkpoint-receipt.json');rebind=load(packet/'session-rebind.json');original=load(packet/'original-engine-report.json')
    assert receipt['session_sha256']==rebind['actual_session_sha256']==identity['session_sha256']
    assert receipt['report_sha256']==rebind['actual_engine_report_sha256']==report['origin_engine_report_sha256']
    assert receipt['route_counters']['routed_count']==original['route_counters']['routed_count']==3
    assert rebind['importer_projection_sha256']==identity['model_sha256']and rebind['source_board_sha256']==identity['board_sha256']
    assert rebind['origin_board_sha256']==load(ROOT/'sessions/accepted58/source-identity.json')['board_sha256']
    assert report['routes']==original['routes']and report['origin_model_sha256']==rebind['origin_model_sha256']
    assert set(rebind['intermediate_additions']).issubset(contract['mutable_source_ids'])and len(rebind['intermediate_additions'])==10
    assert set(load(ROOT/'checks/source24-fixed-pad-entry-ids.json')).isdisjoint(contract['mutable_source_ids'])
   if a.historical_workspace:
    modelpath=a.historical_workspace/('model-candidate24-ready/via-continuation25/import-model.json'if c==26 else f'model-candidate{source}-ready/model.json')
    model=load(modelpath);assert all(model[k]==v for k,v in contract.items())
    assert sha(modelpath)==identity['model_sha256']
    row=projections[str((packet/'engine-report.json').relative_to(ROOT))];raw=load(a.historical_workspace/row['historical_path']);raw['areas']=[];assert raw==report
   projection=tmp/f'projection{c}';run([sys.executable,'-B','prepare_session_replay.py','--packet',packet,'--source-board',board,'--out',projection]);bound=load(projection/'engine-report.json')
   assert bound['model_sha256']==sha(projection/'model.json')and bound['origin_engine_report_sha256']==identity['engine_report_sha256']
   wrong=tmp/f'wrong{c}.kicad_pcb';wrong.write_bytes(board.read_bytes()+b'\n');run([sys.executable,'-B','prepare_session_replay.py','--packet',packet,'--source-board',wrong,'--out',tmp/f'bad-source{c}'],False);negative+=1
   for file in ['session.ses','engine-report.json','import-contract.json']:
    altered=tmp/f'tampered{c}-{file}';shutil.copytree(packet,altered);(altered/file).write_bytes((altered/file).read_bytes()+b'\n');run([sys.executable,'-B','prepare_session_replay.py','--packet',altered,'--source-board',board,'--out',tmp/f'bad{c}-{file}'],False);negative+=1
   result.update(packet='sessions/'+name,exact_paired_source_recovered=True,original_report_projection_verified=bool(a.historical_workspace),import_contract_original_field_projection_verified=bool(a.historical_workspace),projection_rebinding_verified=True,wrong_source_and_three_tamper_controls_passed=True,new_tracks=identity['new_tracks'],new_vias=identity['new_vias'],native_replay_executed=False)
   write(ROOT/f'checks/candidate{c}-v8-packet-verified.json',result);packets.append(result)
  delta=load(ROOT/'sessions/recovery57/candidate24.f722-heli.kicad_pcb.delta.json');base=(a.base_project/'f722-heli.kicad_pcb').read_bytes()
  for badbase,baddelta in [(base+b'\n',delta),(base,dict(delta,target_sha256='0'*64)),(base,dict(delta,operations=[[0,len(base)+1]]))]:
   try:recovery.reconstruct(badbase,baddelta)
   except ValueError:negative+=1
   else:raise AssertionError('Bad recovery input accepted')
 result={'passed':True,'verifier_source_sha256':sha(__file__),'scope':'Portable identity, exact source/paired-file recovery, preserved endpoint refusal/completion receipts, selected25/26 checkpoints and pure importer parser/projection checks. No fresh native qualification.','recovered_projects':recovered,'packets':[r['packet']for r in packets],'negative_controls_passed':negative,'original_projection_checks_performed':bool(a.historical_workspace),'native_replay_reexecuted':False,'native_DRC_reexecuted':False,'endpoint_geometry_reexecuted':False,'JVM_router_refill_or_power_solve_executed':False}
 write(ROOT/'checks/v8-evidence-verified.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
