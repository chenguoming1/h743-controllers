#!/usr/bin/env python3
"""Prepare closed guard/native173 recovery; no engineering execution or compression."""
import collections
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
BASE='recovery-negotiated-routing-20261011/'
IMPORT='recovered-native7/recovery-importer/'
GUARD=BASE+'guard-merge-control-v1/'
OFFSET=BASE+'guard-offset-attribution-v1/'
SOURCE_ARCHIVE=BASE+'vendor-artifacts/freerouting-2.1.0-source.tar.gz'
DIAG=IMPORT+'current-negotiated-terminal-v7-diagnostic-v2/'
REVIEW=DIAG+'terminal-review-v1/terminal-review.json'
REVIEW_PIN='0f91db711ba724e1c1fad81a58fe60e01a341cb66b6e8529eb3329f27eb5e12d'
GUARD_PIN='b4afd0cf50ae1f79770632ce543340d95e86618afd088a3178e594e790356a2e'
SEALS={
 'current-negotiated-import-profile-v2':'4969f0bfc05590fb5f531a03ef8bbefe87024fad33e4dd567aa678d7325e6d1e',
 'current-negotiated-terminal-v7-diagnostic-v2':'3c23364c6a0a1509cee828b04e3a9f28f07da80689943fdf5ee9101ecb420604',
 'current-negotiated-contact-request-v1':'c9263c9237f38d2103bb0329c741153cfe651fb7b262c0f9cf688f9a28efb090'}
PRIOR=[
 ('publication-frozen-173-cache-20261011','173-cache-v1-20261011','8049e70e2f3329b8e55ce350678f2eb47c0acefae29d0460e57c966b8ba2ce2b'),
 ('publication-frozen-negotiated-v5-20261011','negotiated-v5-20261011','0c745bd6795b95c4d50d5a1bce6bff8ebddb540d689e59b711e1f246fe4e7d53'),
 ('publication-frozen-corrected-routing-v2-20261011','corrected-routing-v2-20261011','bdecb40f7471f90ac9a59f22bc9d8c213ee90651127d3815b89b7babb06de905')]
CACHE={}
def identity(path):
 p=Path(path);p=p if p.is_absolute() else ROOT/p
 if str(p) in CACHE:return CACHE[str(p)]
 n=p.stat().st_size;h=hashlib.sha256();g=hashlib.sha1(b'blob '+str(n).encode()+b'\0')
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);g.update(b)
 CACHE[str(p)]={'bytes':n,'sha256':h.hexdigest(),'git_blob_sha':g.hexdigest()}
 return CACHE[str(p)]

def read(path):return json.loads((ROOT/path).read_text())

def regen_pin(row):return row.get('expected_sha256') or regen_pin(row['entry'])

def write(name,value):
 with (HERE/name).open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')

def main():
 assert not (HERE/'PREPARATION-SEAL.json').exists()
 prior_objects={};prior_regen={};ancestors=[]
 for directory,checkpoint,pin in PRIOR:
  manifest=ROOT/directory/'manifest.json';assert identity(manifest)['sha256']==pin
  package=ROOT/directory/'payload/f722-heli/layout-revision/checkpoints'/checkpoint
  mapping=read(package/'reconstruction-map.json');reverse={}
  for path,digest in mapping['restore_files'].items():reverse.setdefault(digest,path)
  for digest,row in mapping['objects'].items():
   prior_objects.setdefault(digest,{'checkpoint_directory':directory,'checkpoint_manifest_sha256':pin,
    'reconstruction_map':str((package/'reconstruction-map.json').relative_to(ROOT)),
    'reconstruction_map_sha256':identity(package/'reconstruction-map.json')['sha256'],
    'restore_alias':reverse[digest],'object_sha256':digest,'bytes':row['bytes'],'git_blob_sha':row['git_blob_sha']})
  for path,row in read(package/'regeneration-map.json')['files'].items():prior_regen.setdefault(path,row)
  ancestors.append({'manifest_file':str(manifest),'manifest_sha256':pin,'checkpoint':checkpoint})
 requested={};reasons=collections.defaultdict(set)
 def add(path,pin=None,why='closed guard/native evidence'):
  p=Path(path);p=p.relative_to(ROOT) if p.is_absolute() else p;s=p.as_posix()
  assert '..' not in p.parts and '__pycache__' not in p.parts
  assert not any(x in s for x in ['offset-control','physical-offset','drill-containment','negotiated-v8/']),s
  assert (ROOT/p).is_file(),s
  if pin and requested.get(s):assert requested[s]==pin,('Conflicting pin',s)
  requested[s]=pin or requested.get(s);reasons[s].add(why)
 terminal=read(GUARD+'run/execution-receipt.json')
 assert identity(GUARD+'run/execution-receipt.json')['sha256']==GUARD_PIN
 assert not terminal['passed'] and not terminal['autorouting_executed'] and terminal['source_files_unchanged'] and terminal['lane_released']
 contract=read(GUARD+'contract.json')
 for row in contract['source_files']:add(row['path'],row['sha256'],'closed guard-control source contract')
 for p in sorted((ROOT/GUARD).rglob('*')):
  if not p.is_file() or any(x in p.parts for x in ['build','__pycache__','tmp']):continue
  assert not p.name.endswith('.next');add(p.relative_to(ROOT))
 for row in terminal['output_files']:add(row['path'],row['sha256'],'closed guard-control terminal output')
 offset_terminal=read(OFFSET+'run/execution-receipt.json')
 assert identity(OFFSET+'run/execution-receipt.json')['sha256']=='4c4d0c11204f383c5aecb6dfa5385eed78af934b41fa66ce82ed54cb6ed1abb9'
 assert offset_terminal['passed'] and offset_terminal['source_files_unchanged'] and offset_terminal['lane_released'] and not offset_terminal['physical_offset_contained']
 assert identity(OFFSET+'run/attribution.json')['sha256']=='6931eda6bcd1aea71b57fd4a215ef9b97326a4c7e6fc8762d726d310c92ecbae'
 assert identity(OFFSET+'run/offset-deficit-readout.json')['sha256']=='a7c3eea9a50d8797a915a29a21fdf8950e5e8aa018d22212ce2a094b88e97ecb'
 for row in read(OFFSET+'contract.json')['source_files']:add(row['path'],row['sha256'],'closed offset-attribution source contract')
 for group in [OFFSET,BASE+'guard-euclidean-witness-v1/']:
  for p in sorted((ROOT/group).rglob('*')):
   if p.is_file() and not any(x in p.parts for x in ['build','__pycache__','tmp']):add(p.relative_to(ROOT),why='closed offset/witness source or terminal evidence')
 for row in offset_terminal['output_files']:add(row['path'],row['sha256'],'closed offset-attribution terminal output')
 add(BASE+'vendor-artifacts/download-receipt.json',why='pinned official source archive provenance without duplicating archive')
 for group,pin in SEALS.items():
  seal=IMPORT+group+'/PREPARATION-SEAL.json';assert identity(seal)['sha256']==pin
  add(seal,pin,'sealed source/preparation packet')
  for row in read(seal)['files']:
   assert Path(row['path']).stat().st_size==row['bytes'];add(row['path'],row['sha256'],'sealed source/preparation packet')
 assert identity(REVIEW)['sha256']==REVIEW_PIN
 review=read(REVIEW);assert review['supervisor_exit_code']==0 and not review['accepted_or_adopted']
 assert len(review['terminal_output_files'])==95 and review['terminal_output_file_count']==87
 add(REVIEW,REVIEW_PIN,'terminal native diagnostic exact inventory review')
 add(DIAG+'terminal-review-v1/verify_saved_output.py',why='terminal native saved-output verifier source')
 aliascount=0
 for row in review['terminal_output_files']:
  assert Path(row['path']).stat().st_size==row['bytes'];add(row['path'],row['sha256'],'terminal native diagnostic output or historical lease')
  if 'unchanged_source_alias' in row:
   alias=row['unchanged_source_alias'];assert alias['sha256']==row['sha256'] and alias['bytes']==row['bytes']
   add(alias['path'],alias['sha256'],'verified unchanged paired source alias');aliascount+=1
 assert aliascount==62
 plan=read(DIAG+'native-plan.json')
 assert identity(DIAG+'native-plan.json')['sha256']==review['plan_sha256']
 for path,pin in plan['source_files'].items():add(path,pin,'exact executed native plan dependency')
 # Preserve prior sealed validator/profile packets needed by the new count-independent importer.
 for group,pin in [('current-negotiated-import-profile-v1','87de98eed8d525b6fd3d2dbd5d4b6b69eb2bf42071910aa199d1d81a0530cdd1'),('current-negotiated-import-v4','acecee77ded1303549b61741e57f18be8894d82b6c8289af8403cccc9e7baebc')]:
  path=IMPORT+group+'/PREPARATION-SEAL.json';assert identity(path)['sha256']==pin;add(path,pin,'prior immutable source packet')
  for row in read(path)['files']:add(row['path'],row['sha256'],'prior immutable source packet')
 request_path=IMPORT+'current-negotiated-contact-request-v1/request.template.json'
 assert identity(request_path)['sha256']=='bcde765026617c4b7b5f6ca158ee8e637a14ef1b673bbf691de62c5244b85dea'
 contact=read(request_path);assert len(contact['files'])==9 and not contact['geometry_execution_enabled']
 assert contact['proposed_runtime_request']['run_argv'] is None and all(v is None for v in contact['future_candidate_files'].values())
 for row in contact['files'].values():add(row['path'],row['sha256'],'disabled contact request pinned source/kernel/contract')
 # Explicit source dependency closure only; inherited objects already have sealed recovery closure.
 visited=set();unresolved=[]
 def references(x,context):
  if isinstance(x,dict):
   if isinstance(x.get('path'),str) and isinstance(x.get('sha256'),str) and len(x['sha256'])==64:
    p=Path(x['path']);choices=[p] if p.is_absolute() else [ROOT/p,ROOT/context/p];matches=[q for q in choices if q.is_file()]
    if matches:add(matches[0],x['sha256'],'explicit JSON dependency row')
    else:unresolved.append({'from':str(context),'row':x})
   for k,v in x.items():
    if isinstance(k,str) and isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v) and ('/' in k or '.' in k):
     p=Path(k);choices=[p] if p.is_absolute() else [ROOT/p];matches=[q for q in choices if q.is_file()]
     if matches:add(matches[0],v,'explicit JSON path-to-hash dependency')
    references(v,context)
  elif isinstance(x,list):
   for v in x:references(v,context)
 while True:
  todo=[s for s in requested if s not in visited]
  if not todo:break
  for path in todo:
   visited.add(path)
   if path in prior_regen or path==GUARD+'run/merged/model.json':continue
   p=ROOT/path;actual=identity(path)
   if actual['sha256'] in prior_objects:continue
   if p.suffix=='.json' and p.stat().st_size<1048576:references(read(path),p.parent.relative_to(ROOT))
 assert not unresolved,('Unresolved dependency rows',unresolved)
 generated={};rows=[];objects={}
 for path,pin in sorted(requested.items()):
  p=ROOT/path
  if path in prior_regen:
   assert pin is None or regen_pin(prior_regen[path])==pin,('Prior regeneration changed',path)
   generated[path]={'kind':'inherited_predecessor_regeneration','entry':prior_regen[path]};continue
  if path==SOURCE_ARCHIVE:
   artifact=next(x for x in read(BASE+'vendor-artifacts/download-receipt.json')['artifacts'] if x['path']==SOURCE_ARCHIVE)
   assert pin==artifact['expected_sha256']==artifact['actual_sha256']
   member_pins={k.split('!',1)[1]:v for k,v in read(GUARD+'tree-coverage-source-sha256.json')['sha256'].items() if k.startswith(SOURCE_ARCHIVE+'!')}
   generated[path]={'kind':'restore_pinned_official_source_archive','expected_sha256':pin,'bytes':artifact['bytes'],
     'source_url':artifact['source_url'],'resolved_source_url':artifact['resolved_url'],'provenance':BASE+'vendor-artifacts/download-receipt.json',
     'inspected_member_sha256':member_pins,'capture_archive':False,'fetch_or_execution_performed':False,
     'recipe':'Fetch the pinned official v2.1.0 archive, verify exact SHA-256 and size, then extract only required inspected members and verify their individual hashes. Executable experiment sources are preserved directly.'};continue
  if path==GUARD+'run/merged/model.json':
   digest=identity(path)['sha256'];assert digest=='71acea3d1abe32aeffa3c0b3cbe79bd78e4078715e8efcdd1e1d168dc22d9528' and (pin is None or pin==digest)
   stage=next(x for x in contract['stages'] if x['name']=='transform')
   generated[path]={'kind':'regenerate','expected_sha256':digest,'bytes':p.stat().st_size,'contract':GUARD+'contract.json',
    'contract_sha256':identity(GUARD+'contract.json')['sha256'],'stage':'transform','argv':stage['argv'],
    'source_model':BASE+'negotiated-v7/model/model.json','source_model_sha256':'fe7edfbcc0bb4b2d314165b7c312b0cd946276314e01ec66b627eebd63c7f8f0',
    'actual_receipt_preserved':GUARD+'run/merged/receipt.json','actual_pair_ledger_preserved':GUARD+'run/merged/pair-ledger.json',
    'require_fresh_execution_tree_and_absent_output':True,'never_overwrite_historical_evidence':True,'geometry_execution_performed':False,
    'model_status':'FAILED_INSTALLED_OLD_ENVELOPE_COVERAGE_NOT_QUALIFIED_FOR_ROUTING'};continue
  actual=identity(path);assert pin is None or actual['sha256']==pin,('Changed source',path)
  digest=actual['sha256'];row=dict(path=path,reasons=sorted(reasons[path]),bytes_verified=True,**actual)
  if digest in prior_objects:
   row['storage']='reuse_frozen_predecessor_object';row['source']=prior_objects[digest]
   assert row['bytes']==row['source']['bytes'] and row['git_blob_sha']==row['source']['git_blob_sha']
  else:row['storage']='capture_unique_successor_object'
  rows.append(row);objects.setdefault(digest,dict(bytes=row['bytes'],storage=row['storage'],representative_path=path,aliases=[]))['aliases'].append(path)
 stats={mode:{'paths':sum(r['storage']==mode for r in rows),'unique_objects':sum(r['storage']==mode for r in objects.values()),'unique_bytes':sum(r['bytes'] for r in objects.values() if r['storage']==mode)} for mode in sorted({r['storage'] for r in rows})}
 reconciliation=read(GUARD+'terminal-reconciliation.json')
 assert reconciliation['transform']['merged_pairs']==8224 and reconciliation['first_pair']['qualified_pairs']==0
 assert not reconciliation['accepted_model'] and not reconciliation['autorouting_executed']
 assert review['original_fixed_full_records_exact']==2214 and review['mutable_records_retained_exactly']==44 and review['actual_mutable_records_removed']==129 and review['actual_added_full_records_exact']==52 and review['result_objects']==2310
 assert review['raw_DRC_counts']=={'schematic_parity':0,'unconnected_items':16,'violations':21} and review['raw_ERC_count']==0
 byalias={}
 for row in rows:
  if 'source' in row:
   alias=row['source']['restore_alias'];value=(row['sha256'],row['bytes']);assert alias not in byalias or byalias[alias]==value;byalias[alias]=value
 write('source-allowlist.json',{'schema':'f722-native173-guard-recovery-plan/v1','source_entries':rows,'unique_objects':objects,'statistics':stats,
  'frozen_predecessors':ancestors,'verified_remote_predecessor':{'pull_request':22,'branch':'f722/negotiated-v5-20261011','head':'7f2e8d59db582ddbfdbbfc99c3398d905d6c6d97','tree':'239ad1109e636708566c1620f5df507c0f84198d','authority':'Owner supplied verified predecessor; later publication requires fresh remote verification.'},
  'active_drill_and_later_offset_successors_excluded':True,'compression_performed':False})
 write('regeneration-map.json',{'schema':'f722-native173-guard-regeneration-map/v1','files':generated,'engineering_replay_performed':False,
  'compiled_classes':'Recompile only pinned contract stages in a fresh execution tree; no current build directory is required for byte recovery.',
  'restore_before_replay':'Restore sealed historical evidence without regeneration. Engineering replay needs separate authority and original-path-compatible runtime; never overwrite failed receipts.'})
 write('evidence-status.json',{'schema':'f722-native173-guard-status/v1',
  'guard_control':{'receipt_sha256':GUARD_PIN,'elapsed_seconds':terminal['elapsed_seconds'],'status':'FAILED_FIRST_SLOW_TREE_OLD_ENVELOPE_COVERAGE_NO_QUALIFIED_MODEL_OR_ROUTES','raw_merged_pairs':8224,'qualified_pairs':0,'exact_raw_pair_ledger_preserved':True,'source_groups_equal':True,'actual_physical_offset_coverage_not_established':True,'terminal_reconciliation_sha256':identity(GUARD+'terminal-reconciliation.json')['sha256']},
  'closed_offset_attribution':{'receipt_sha256':'4c4d0c11204f383c5aecb6dfa5385eed78af934b41fa66ce82ed54cb6ed1abb9',
   'attribution_sha256':'6931eda6bcd1aea71b57fd4a215ef9b97326a4c7e6fc8762d726d310c92ecbae',
   'deficit_readout_sha256':'a7c3eea9a50d8797a915a29a21fdf8950e5e8aa018d22212ce2a094b88e97ecb',
   'control_passed':True,'regressions':6,'saved_metrics_reproduced':True,'physical_offset_contained':False,
   'failed_slow_halfplanes':'7/12','failed_fast_halfplanes':'4/8','all_reported_counterexamples_outside_both_models':True,
   'maximum_demonstrated_witness_nm':read(OFFSET+'run/offset-deficit-readout.json')['maximum_demonstrated_witness']['offset_deficit_nm_decimal'],
   'scope':'Enumerated support witnesses only; inherited engine-envelope undercoverage at these witnesses. No global bound, native-board violation, or harmlessness of the entire removed area is proved. Merge remains unqualified.'},
  'native_diagnostic':{'terminal_review_sha256':REVIEW_PIN,'terminal_output_rows':95,'output_tree_files':87,'unchanged_source_aliases':62,
   'native_export_sha256':review['native_sha256'],'board_sha256':review['board_sha256'],'control_receipt_sha256':review['control_receipt']['sha256'],
   'opens':16,'warnings':21,'other_DRC_errors':0,'ERC':0,'parity':0,'original_fixed_exact':2214,'mutable_retained_exact':44,'removed':129,'added':52,'final_objects':2310,
   'serializer_strict_rejection_preserved':True,'unmasked_track_disk_containment_failure_preserved':True,'scoped_actual_drill_subtraction_proof_preserved':True,
   'scope':'IMPORTER_VALIDATION_ONLY_NO_ELECTRICAL_EQUIVALENCE_THROUGH_DRILL_VOID','accepted_or_adopted':False},
  'source_seals':SEALS,'disabled_contact_request':{'sha256':identity(request_path)['sha256'],'pinned_input_count':9,'status':contact['status'],'geometry_execution_enabled':False,'current_role_fragment_dispatcher_missing':True,'future_candidate_inputs_empty':True,'no_argv_or_native_execution':True},
  'accepted_board':'native7','canonical_native_opens':7,'native_adoption':False,'numerical_power':'STALE'})
 write('preparation-verification.json',{'source_paths':len(rows),'unique_objects':len(objects),'regeneration_paths':len(generated),
  'all_selected_source_pins_verified':True,'terminal_native_inventory_95_rows_bound':True,'disabled_contact_nine_inputs_bound':True,
  'all_originals_preserved':True,'predecessor_aliases_collision_free':True,'heavy_lane_acquired':False,'compression_performed':False,'external_writes':False})
 print(json.dumps({'paths':len(rows),'objects':len(objects),'regeneration_paths':len(generated),'statistics':stats,
  'reuse_by_checkpoint':dict(collections.Counter(r['source']['checkpoint_directory'] for r in rows if 'source' in r))},indent=2))
if __name__=='__main__':main()
