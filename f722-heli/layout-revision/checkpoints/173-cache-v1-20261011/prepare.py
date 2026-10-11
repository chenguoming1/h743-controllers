#!/usr/bin/env python3
"""Prepare an exact closed-v6/v7/importer byte recovery plan; execute no engineering."""
import collections
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = 'recovery-negotiated-routing-20261011/'
IMPORT = 'recovered-native7/recovery-importer/'
PRIOR = [
 ('publication-frozen-negotiated-v5-20261011', 'negotiated-v5-20261011', '0c745bd6795b95c4d50d5a1bce6bff8ebddb540d689e59b711e1f246fe4e7d53'),
 ('publication-frozen-corrected-routing-v2-20261011', 'corrected-routing-v2-20261011', 'bdecb40f7471f90ac9a59f22bc9d8c213ee90651127d3815b89b7babb06de905'),
 ('publication-frozen-negotiated-routing-v1-20261011', 'negotiated-routing-v1-20261011', '5db551817f51f75df2c66613c78c799c227634543a287278388c735535d67af5')]
SEALS = {
 'current-negotiated-checkpoint-binding-v1': 'eca258bfa61527697a019855498d0af4452c50170c72dce05f53fcfa87ac5d61',
 'current-negotiated-import-173-v1': '3a942b17f3319fd7e6178e8edfc43c6e6e3b8080c3e86b17deb4088fb9d1131c',
 'current-negotiated-import-profile-v1': '87de98eed8d525b6fd3d2dbd5d4b6b69eb2bf42071910aa199d1d81a0530cdd1'}
PINS = {
 BASE+'negotiated-v6/run/execution-receipt.json': '6b01e172c2c6361951ba9a6dc0f9a76976634e4c1a6b0bb51e8fcb8412dd2cf5',
 BASE+'negotiated-v7/run/execution-receipt.json': '6892e27e3f2547faa1a5bbfc2b8bfc6670b9ebca072644cc86fab1f7efcb656d',
 BASE+'negotiated-v7/terminal-analysis/terminal-analysis.json': '3fe69f1d2332b7128c2d5066428b852cefc169838dd0e7cadf5901055cce170f',
 BASE+'statistics-baseline-control-v1/saved-output-reconciliation.json': 'bf1815df6561690c24fe3a6f3315b5d4c0fed43d5aa3605d232444ddfe8979ba'}
CACHE = {}
def identity(path):
 p=Path(path);p=p if p.is_absolute() else ROOT/p
 if str(p) in CACHE:return CACHE[str(p)]
 n=p.stat().st_size;h=hashlib.sha256();g=hashlib.sha1(b'blob '+str(n).encode()+b'\0')
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);g.update(b)
 CACHE[str(p)]={'bytes':n,'sha256':h.hexdigest(),'git_blob_sha':g.hexdigest()}
 return CACHE[str(p)]
def read(path):return json.loads((ROOT/path).read_text())
def write(name,x):
 with (HERE/name).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def regen_pin(row):return row.get('expected_sha256') or regen_pin(row['entry'])

def main():
 assert not (HERE/'PREPARATION-SEAL.json').exists()
 prior_objects={}; prior_regen={}; ancestors=[]
 for directory,checkpoint,pin in PRIOR:
  manifest=ROOT/directory/'manifest.json';assert identity(manifest)['sha256']==pin
  package=ROOT/directory/'payload/f722-heli/layout-revision/checkpoints'/checkpoint
  mapping=read(package/'reconstruction-map.json')
  reverse={}
  for path,digest in mapping['restore_files'].items():reverse.setdefault(digest,path)
  for digest,row in mapping['objects'].items():
   prior_objects.setdefault(digest,{'checkpoint_directory':directory,'checkpoint_manifest_sha256':pin,
      'reconstruction_map':str((package/'reconstruction-map.json').relative_to(ROOT)),
      'reconstruction_map_sha256':identity(package/'reconstruction-map.json')['sha256'],
      'restore_alias':reverse[digest],'object_sha256':digest,'bytes':row['bytes'],'git_blob_sha':row['git_blob_sha']})
  for path,row in read(package/'regeneration-map.json')['files'].items():prior_regen.setdefault(path,row)
  ancestors.append({'manifest_file':str(manifest),'manifest_sha256':pin,'checkpoint':checkpoint})
 requested={};reasons=collections.defaultdict(set)
 def add(path,pin=None,why='closed source or evidence'):
  p=Path(path);p=p.relative_to(ROOT) if p.is_absolute() else p
  s=p.as_posix();assert '..' not in p.parts and '__pycache__' not in p.parts
  assert not any(x in s for x in ['triangle-simpl','tree-simpl','negotiated-v8/','173-diagnostic','terminal-diagnostic-v7'])
  assert not s.startswith(IMPORT+'current-negotiated-import-profile-v1/outputs/')
  assert (ROOT/p).is_file(),s
  if pin and requested.get(s):assert requested[s]==pin,('Conflicting pin',s)
  requested[s]=pin or requested.get(s);reasons[s].add(why)
 for path,pin in PINS.items():assert identity(path)['sha256']==pin;add(path,pin,'closed terminal authority')
 for group in ['negotiated-v6','statistics-baseline-control-v1','negotiated-v7']:
  prefix=BASE+group+'/'
  for row in read(prefix+'contract.json')['source_files']:add(row['path'],row['sha256'],'exact sealed source contract dependency')
  for p in sorted((ROOT/prefix).rglob('*')):
   if not p.is_file() or any(x in p.parts for x in ['build','__pycache__','statistics-cache']):continue
   assert not p.name.endswith('.next');add(p.relative_to(ROOT))
  terminal=read(prefix+'run/execution-receipt.json')
  for row in terminal.get('saved_checkpoint_files',[])+terminal.get('output_files',[]):add(row['path'],row['sha256'],'terminal output inventory')
  for stage in terminal.get('stages',[]):
   if stage.get('log_path') and stage.get('log_sha256'):add(stage['log_path'],stage['log_sha256'],'historical command log')
  for path in terminal.get('other_temp_files_retained',[]):
   assert path.endswith('/statistics-cache/freerouting/freerouting.log');add(path,why='terminal producer retained engine log')
 for group,pin in SEALS.items():
  seal=IMPORT+group+'/PREPARATION-SEAL.json';assert identity(seal)['sha256']==pin;add(seal,pin,'sealed importer source packet')
  for row in read(seal)['files']:
   assert (Path(row['path'])).stat().st_size==row['bytes'];add(row['path'],row['sha256'],'sealed importer source packet')
 # Prior v4 supplies pinned validators, native writer dependencies, the exact paired source and runtime recipes.
 old=IMPORT+'current-negotiated-import-v4/'
 seal=old+'PREPARATION-SEAL.json';assert identity(seal)['sha256']=='acecee77ded1303549b61741e57f18be8894d82b6c8289af8403cccc9e7baebc'
 add(seal,identity(seal)['sha256'],'prior frozen validator/native dependency seal')
 for row in read(seal)['files']:add(row['path'],row['sha256'],'prior frozen validator/native dependency')
 for path,pin in read(old+'native-dependencies.json')['files'].items():add(path,pin,'native runtime/paired-source dependency')
 for row in read(old+'source-preparation-final.json')['source_files'].values():add(row['path'],row['sha256'],'prior source preparation dependency')
 for path,pin in read(old+'terminal-diagnostic-native-plan.json')['source_files'].items():add(path,pin,'prior native writer dependency')
 for name in ['README.md','validation.json','RESTORATION-REPORT.json','restore_runtime.py','package-manifest.json','provenance/packages-verified.json','provenance/wrapper-source-identities.json','provenance/signature-verification.txt','provenance/snapshot-index-pinned-comparison.json']:
  add('kicad10-runtime/'+name,why='official runtime pinned restoration recipe')
 # Follow explicit path+SHA rows in newly selected small JSON source/control records.
 # Existing archived objects and generated models retain their predecessor closure.
 visited=set();unresolved=[]
 def references(x,context):
  if isinstance(x,dict):
   if isinstance(x.get('path'),str) and isinstance(x.get('sha256'),str) and len(x['sha256'])==64:
    p=Path(x['path']);choices=[p] if p.is_absolute() else [ROOT/p,ROOT/context/p]
    matches=[q for q in choices if q.is_file()]
    if matches:add(matches[0],x['sha256'],'explicit JSON dependency row')
    else:unresolved.append({'from':str(context),'row':x})
   for k,v in x.items():
    if isinstance(k,str) and isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v) and ('/' in k or '.' in k):
     p=Path(k);choices=[p] if p.is_absolute() else [ROOT/p]
     matches=[q for q in choices if q.is_file()]
     if matches:add(matches[0],v,'explicit JSON path-to-hash dependency')
    references(v,context)
  elif isinstance(x,list):
   for v in x:references(v,context)
 while True:
  todo=[s for s in requested if s not in visited]
  if not todo:break
  for path in todo:
   visited.add(path)
   if path in prior_regen or path.endswith('/model/model.json'):continue
   p=ROOT/path;idn=identity(path)
   if idn['sha256'] in prior_objects:continue
   if p.suffix=='.json' and p.stat().st_size<1048576:references(read(path),p.parent.relative_to(ROOT))
 assert not unresolved,('Unresolved explicit source dependencies',unresolved)
 generated={};rows=[];objects={}
 for path,pin in sorted(requested.items()):
  p=ROOT/path
  if path in prior_regen:
   assert pin is None or regen_pin(prior_regen[path])==pin,('Prior regeneration changed',path)
   generated[path]={'kind':'inherited_predecessor_regeneration','entry':prior_regen[path]};continue
  if path in [BASE+'negotiated-v6/model/model.json',BASE+'negotiated-v7/model/model.json']:
   version=path.split('/')[-3];composition=BASE+version+'/model/composition-receipt.json'
   digest=read(composition)['model_sha256'];assert pin is None or digest==pin
   script=BASE+version+('/prepare_negotiated_model_v6.py' if version=='negotiated-v6' else '/prepare_runtime_metadata.py')
   generated[path]={'kind':'regenerate','expected_sha256':digest,'bytes':p.stat().st_size,
     'recipe_file':script,'recipe_sha256':identity(script)['sha256'],'composition_receipt':composition,
     'composition_receipt_sha256':identity(composition)['sha256'],
     'argv':['/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python',str(ROOT/script)],
     'prerequisite':'restore/regenerate v5 model and pinned dependencies' if version=='negotiated-v6' else 'restore/regenerate v6 model then derive only declared runtime metadata',
     'require_fresh_execution_tree_and_absent_model_output':True,'original_workspace_root':str(ROOT),
     'never_overwrite_historical_receipts_or_originals':True,'execution_performed':False};continue
  result=identity(path);assert pin is None or pin==result['sha256'],('Changed source',path)
  digest=result['sha256'];row=dict(path=path,reasons=sorted(reasons[path]),bytes_verified=True,**result)
  if digest in prior_objects:
   row['storage']='reuse_frozen_predecessor_object';row['source']=prior_objects[digest]
   assert row['bytes']==row['source']['bytes'] and row['git_blob_sha']==row['source']['git_blob_sha']
  else:row['storage']='capture_unique_successor_object'
  rows.append(row);objects.setdefault(digest,dict(bytes=row['bytes'],storage=row['storage'],representative_path=path,aliases=[]))['aliases'].append(path)
 # Bind every complete saved checkpoint and final pair without running geometry.
 v7=BASE+'negotiated-v7/';terminal=read(v7+'run/execution-receipt.json')
 assert terminal['passed'] and terminal['source_files_unchanged'] and terminal['lane_released']
 assert terminal['native_acceptance'] is False and terminal['engine_connected_role_count']==6
 fixed=identity(v7+'run/candidate.fixed-traces-before.exact')['sha256'];checkpoints=[]
 for i in range(1,17):
  stem=v7+'run/candidate.checkpoints/checkpoint-'+str(i).zfill(4);report=read(stem+'.after.json')
  assert identity(stem+'.fixed-traces-after.exact')['sha256']==fixed
  checkpoints.append({'index':i,'report':dict(path=stem+'.after.json',**identity(stem+'.after.json')),
    'session':dict(path=stem+'.ses',**identity(stem+'.ses')),'fixed_trace_sha256':fixed,
    'missing_required_joins':sum(max(0,len(x['groups'])-1) for x in report['required_logical_connectivity'])})
 assert len(terminal['saved_checkpoint_files'])==48
 final=read(v7+'run/candidate.after.json');finaljoins=sum(max(0,len(x['groups'])-1) for x in final['required_logical_connectivity']);assert finaljoins==16
 analysis=read(v7+'terminal-analysis/terminal-analysis.json');passes=[{'pass':x['pass'],'joins':x['required_joins']} for x in analysis['complete_passes']]
 assert passes==[{'pass':1,'joins':18},{'pass':2,'joins':17},{'pass':3,'joins':17}]
 assert identity(v7+'run/candidate.fixed-traces-after.exact')['sha256']==fixed
 v6=read(BASE+'negotiated-v6/run/execution-receipt.json');assert not v6['passed'] and not v6['saved_checkpoint_files']
 assert 'Exact statistics key exceeds 536870912 bytes' in (ROOT/BASE/'negotiated-v6/run/negotiation.log').read_text()
 control=read(BASE+'statistics-baseline-control-v1/saved-output-reconciliation.json')
 assert control['control_passed'] and control['supervisor_exit_code']==1 and not control['supervisor_success_claimed']
 stats={mode:{'paths':sum(r['storage']==mode for r in rows),'unique_objects':sum(r['storage']==mode for r in objects.values()),'unique_bytes':sum(r['bytes'] for r in objects.values() if r['storage']==mode)} for mode in sorted({r['storage'] for r in rows})}
 write('source-allowlist.json',{'schema':'f722-173-cache-recovery-plan/v1','source_entries':rows,'unique_objects':objects,'statistics':stats,
   'frozen_predecessors':ancestors,'predecessor_publication':'Owner reports verified v5 archive / PR22; exact remote ancestry must be rebound before any later publication.',
   'active_triangle_tree_successors_excluded':True,'active_native_diagnostic_outputs_excluded':True})
 write('regeneration-map.json',{'schema':'f722-173-cache-regeneration-map/v1','files':generated,'engineering_replay_performed':False,
   'compiled_classes':'Recompile the explicitly bound source-contract compile stages with pinned ECJ/JDK; current builds are omitted unless inherited exact class dependencies require pinned regeneration.',
   'restore_before_replay':'Restore historical evidence first. Regenerate in a separate original-path-compatible execution tree with model output absent; never overwrite preserved evidence.'})
 write('evidence-status.json',{'schema':'f722-173-cache-evidence-status/v1','terminal_pins':PINS,
   'v6':{'status':'FAILED_SAFE_EXACT_KEY_CAP_BEFORE_ROUTING_NO_CHECKPOINTS','elapsed_seconds':v6['elapsed_seconds'],'raw_receipt_preserved':True},
   'statistics_control':{'status':'JAVA_CONTROLS_PASSED_SUPERVISOR_FAILED_SAVED_OUTPUTS_RECONCILED','supervisor_exit_code':1,'supervisor_success_claimed':False,'source_bindings_unchanged':435,'reconciliation_sha256':PINS[BASE+'statistics-baseline-control-v1/saved-output-reconciliation.json']},
   'v7':{'status':'TERMINAL_COOPERATIVE_STOP_INCOMPLETE_NOT_ADOPTED','elapsed_seconds':terminal['elapsed_seconds'],'wrapper_passed':True,
     'connected_roles':6,'total_roles':19,'initial_required_joins':13,'final_required_joins':finaljoins,'completed_passes':passes,
     'complete_checkpoints':checkpoints,'final_report':dict(path=v7+'run/candidate.after.json',**identity(v7+'run/candidate.after.json')),
     'final_session':dict(path=v7+'run/candidate.ses',**identity(v7+'run/candidate.ses')),'all_exact_trace_baselines_equal':True},
   'importer_seals':SEALS,'importer_test_counts':{'selected_checkpoint_binder':16,'173_source_adapter':10,'concrete_profile':43},
   'synthetic_initial_conversion_is_not_routed_candidate':True,'canonical_native_open_count':7,'accepted_board':'native7','native_adoption':False,'numerical_power':'STALE'})
 write('preparation-verification.json',{'source_paths':len(rows),'unique_objects':len(objects),'regeneration_paths':len(generated),
   'all_selected_source_pins_verified':True,'all16_checkpoint_triplets_bound':True,'terminal_pair_bound':True,
   'statistics_supervisor_failure_preserved':True,'all_originals_preserved':True,'heavy_lock_acquired':False,'compression_performed':False,'external_writes':False})
 print(json.dumps({'paths':len(rows),'objects':len(objects),'regeneration_paths':len(generated),'statistics':stats,
   'reuse_by_checkpoint':dict(collections.Counter(r['source']['checkpoint_directory'] for r in rows if 'source' in r))},indent=2))
if __name__=='__main__':main()
