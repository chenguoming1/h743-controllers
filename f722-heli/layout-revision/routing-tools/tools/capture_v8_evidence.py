#!/usr/bin/env python3
"""Capture bounded candidate23 refusal, accepted24 completion and accepted25/26 evidence.

Reads the historical workspace; never routes, imports, refills, or launches a
numerical solve. Retains original byte hashes beside every portable projection.
"""
import argparse, difflib, hashlib, json, shutil
from pathlib import Path

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);a=ap.parse_args()
 root=a.workspace.resolve();stage=Path(__file__).resolve().parents[1];maps={};sources={}
 def copy(src,dst):
  p=root/src;q=stage/dst;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);sources[dst]={'historical_path':src,'sha256':sha(p)}
 def portable(obj):
  if isinstance(obj,dict):return {portable(k):portable(v)for k,v in obj.items()}
  if isinstance(obj,list):return [portable(v)for v in obj]
  if isinstance(obj,str):
   obj=obj.replace(str(root.parent)+'/', '').replace(str(root)+'/', '')
   assert '/workspace/' not in obj,'Unmapped absolute workspace path'
  return obj
 def project(src,dst,transform=None,scope=None):
  p=root/src;d=json.loads(p.read_text());out=portable(d)
  if transform:out=transform(out)
  write(stage/dst,out);maps[dst]={'historical_path':src,'historical_file_sha256':sha(p),'historical_bytes':p.stat().st_size,'portable_file_sha256':sha(stage/dst),'projection':scope or 'JSON values retained except package-relative historical path strings; whitespace normalized.'};return out
 # Keep V7's root importer byte-identical for historical receipts. New frozen
 # importers live beside it, so their normal root-relative dependencies work.
 copy('candidate23/import_session.used.py','import_session_candidate23.py')
 copy('candidate25/import_session.used.py','import_session_v8.py')
 assert sha(root/'candidate25/route_geometry.used.py')==sha(stage/'route_geometry.py')
 sources['candidate25/route_geometry.used.py']={'package_source':'route_geometry.py','sha256':sha(stage/'route_geometry.py')}
 for src,dst in [('candidate24/complete_native_pad_entries.used.py','complete_native_pad_entries.py'),('candidate24/audit_pad_completion.used.py','tests/routing-checkpoint57/audit_pad_completion.historical.py'),('candidate25/audit_unchanged_power.used.py','tests/routing-checkpoint57/audit_unchanged_power.py'),('candidate25/audit_native_endpoints.used.py','tests/routing-checkpoint57/audit_native_endpoints.py')]:copy(src,dst)
 for c in [25,26]:project(f'candidate{c}/owner-adoption.json',f'checks/candidate{c}-owner-adoption.json')
 # Historical refusal is retained as an actual failure, not hidden by later24.
 for name in ['endpoint-audit.json','f722-heli.import.json','f722-heli.logical-route-map.json']:
  project('candidate23/'+name,'checks/candidate23-'+name)
 copy('candidate23/endpoint-audit.log','checks/candidate23-endpoint-audit.log')
 for c in [24,25,26]:
  names=['route-handoff.json','engine-lineage.json','endpoint-audit.json','owner-summary.json','owner-additive-integration.json','f722-heli.logical-route-map.json','power-audit.json','unchanged-power-reference.json','owner-mechanical.json','owner-drc-parity.json','owner-drc.json','owner-drc-all.json','owner-critical.json','owner-process.json','owner-parity.json','owner-firmware.json','owner-actual-io22.json' if c==24 else 'protection-actual-io.json']
  if c==26:names.remove('unchanged-power-reference.json');names+=['f722-heli.import.json','session-rebind.json','power-revalidation-required.json']
  for name in names:project(f'candidate{c}/'+name,f'checks/candidate{c}-'+name)
 for name in ['pad-entry-completion.json','pad-entry-confinement.json']:project('candidate24/'+name,'checks/candidate24-'+name)
 for name in ['worker-summary.json','worker-mechanical.json','f722-heli.import.json']:project('candidate25/'+name,'checks/candidate25-'+name)
 copy('candidate25/worker-validation.log','checks/candidate25-worker-validation.log')
 project('../integrated-routing/trial27/poses-native.json','checks/current-pose-targets.json')
 project('../static-power-validation/candidate24-power-result-applicability.json','checks/candidate24-power-result-applicability.json')
 for source in [22,24,26]:
  for name in ['zero-parity.json','imported-zero.import.json','router-readiness.json','summary.json']:
   project(f'model-candidate{source}-ready/'+name,f'checks/source{source}-'+name)
 project('model-candidate24-ready/fixed-pad-entry-ids.json','checks/source24-fixed-pad-entry-ids.json')
 project('model-candidate26-ready/fixed-pad-entry-ids.json','checks/source26-fixed-pad-entry-ids.json')
 project('../checkpoint57-review/comparison-60-to-57.json','checks/candidate26-critical-reference-comparison.json')
 copy('candidate26/prepare_engine_continuation_import.used.py','prepare_engine_continuation_import.py')
 assert sha(root/'candidate26/import_session.used.py')==sha(stage/'import_session_v8.py')
 # Candidate23 report contains large fixed guard polygons; importer only reads
 # routes. Preserve all routes/contact partitions and original report identity.
 for c,source,packet,ses,report in [
  (23,22,'engine60-refused23','candidate23/engine-broad01.ses','candidate23/engine-broad01.after.json'),
  (25,24,'accepted58','model-candidate24-ready/filtered01.successes/second/snapshot.ses','model-candidate24-ready/filtered01.successes/second/snapshot.after.json'),
  (26,25,'accepted57','model-candidate24-ready/filtered01.successes/final/snapshot.ses','model-candidate24-ready/via-continuation25/engine-report.json')]:
  folder='sessions/'+packet;modelpath='model-candidate24-ready/via-continuation25/import-model.json'if c==26 else f'model-candidate{source}-ready/model.json';model=json.loads((root/modelpath).read_text());origin_report=sha(root/report)
  copy(ses,folder+'/session.ses')
  projection=project(report,folder+'/engine-report.json',lambda d:dict(d,areas=[]),'Importer-only projection: all route geometry, contact partitions and run metadata retained; fixed guard areas omitted (already empty for selected25); original full report byte identity retained.')
  keys=['board_sha256','aliases','ordinary_nets','routable_layers','mutable_source_ids','source_logical_nets','regenerable_reference_zones']
  contract={k:model[k]for k in keys};write(stage/folder/'import-contract.json',contract)
  identity={'kind':'actual_engine_insertions_with_historical_native_import','board_sha256':model['board_sha256'],'native_sha256':model['native_sha256'],'candidate_sha256':sha(root/f'candidate{c}/f722-heli.kicad_pcb'),'model_sha256':sha(root/modelpath),'session_sha256':sha(stage/folder/'session.ses'),'engine_report_sha256':sha(stage/folder/'engine-report.json'),'historical_engine_report_sha256':origin_report,'import_contract_sha256':sha(stage/folder/'import-contract.json'),'import_contract_fields':keys,'full_model_included':False,'importer_source_path':'import_session_candidate23.py'if c==23 else 'import_session_v8.py','importer_source_sha256':sha(stage/('import_session_candidate23.py'if c==23 else 'import_session_v8.py')),'import_arguments':[]if c==26 else ['--preserve-unaffected-fills'],'native_replay_reexecuted_for_v8':False,'new_tracks':{23:14,25:10,26:6}[c],'new_vias':1 if c==26 else 0,'source_candidate':f'candidate{source}','historical_native_import_receipt':f'checks/candidate{c}-f722-heli.import.json','endpoint_disposition':'REFUSED: two narrow full-width entries; repaired separately by candidate24'if c==23 else ('PASS: two pad entries and two actual annular strips; retained redundant spur is non-evidence'if c==26 else 'PASS: all four full-width entries'),'portable_path_projections':'checks/v8-portable-projections.json'}
  assert projection['model_sha256']==identity['model_sha256']
  write(stage/folder/'source-identity.json',identity)
  sources[folder+'/import-contract.json']={'historical_path':modelpath,'historical_full_sha256':identity['model_sha256'],'compact_sha256':sha(stage/folder/'import-contract.json'),'fields':keys}
  if c==26:
   project('model-candidate24-ready/filtered01.successes/final/receipt.json',folder+'/selected-checkpoint-receipt.json')
   project('model-candidate24-ready/filtered01.successes/final/snapshot.after.json',folder+'/original-engine-report.json',lambda d:dict(d,areas=[]),'Actual final engine report compact projection; no geometry fields changed; full original byte hash retained.')
   project('model-candidate24-ready/via-continuation25/rebind.json',folder+'/session-rebind.json')
   project(modelpath,folder+'/historical-import-projection.json')
  if c==25:project('model-candidate24-ready/filtered01.successes/second/receipt.json',folder+'/selected-checkpoint-receipt.json')
 # Exact paired recovery is anchored to the existing accepted62/candidate22
 # project. Text deltas preserve exact UUIDs and serialization, not a reroute.
 rec=stage/'sessions/recovery57';rec.mkdir(exist_ok=True)
 script=(stage/'sessions/recovery62/rebuild_historical_source.py').read_text().replace('("candidate16", "candidate19", "candidate20", "candidate21")','("candidate22", "candidate23", "candidate24", "candidate25", "candidate26")')
 (rec/'rebuild_historical_source.py').write_text(script)
 manifest=json.loads((stage/'sessions/recovery62/paired-files.json').read_text());manifest['sources']={};manifest['optional_omitted_files']={'library/README.md':{'reason':'Nonfunctional library documentation not copied into candidates23–25; not required for import recovery.'}};manifest['required_base_files'].pop('library/README.md');base=(root/'candidate22/f722-heli.kicad_pcb').read_bytes();lines=base.splitlines(keepends=True);offsets=[0]
 for l in lines:offsets.append(offsets[-1]+len(l))
 for c in [22,23,24,25,26]:
  target=(root/f'candidate{c}/f722-heli.kicad_pcb').read_bytes();deltas={}
  for name,info in manifest['required_base_files'].items():
   if name!='f722-heli.kicad_pcb':assert sha(root/f'candidate{c}'/name)==info['sha256'],(c,name)
  if c!=22:
   targetlines=target.splitlines(keepends=True);ops=[]
   for tag,i,j,k,l in difflib.SequenceMatcher(None,lines,targetlines,autojunk=True).get_opcodes():
    if tag=='equal':ops.append([offsets[i],offsets[j]-offsets[i]])
    elif tag in ['replace','insert']:ops.append(b''.join(targetlines[k:l]).decode())
   delta={'schema':'f722-historical-source-copy-delta/v1','base_sha256':hashlib.sha256(base).hexdigest(),'target_sha256':hashlib.sha256(target).hexdigest(),'target_bytes':len(target),'operations':ops}
   name=f'candidate{c}.f722-heli.kicad_pcb.delta.json';write(rec/name,delta);deltas={'f722-heli.kicad_pcb':{'file':name,'sha256':sha(rec/name)}}
  manifest['sources'][f'candidate{c}']={'source_label':f'candidate{c}','purpose':'Exact source/endpoint-recovery provenance; byte recovery is not native replay.','board_sha256':hashlib.sha256(target).hexdigest(),'board_bytes':len(target),'unchanged_paired_files':len(manifest['required_base_files'])-1,'deltas':deltas}
 write(rec/'paired-files.json',manifest)
 superseded=[]
 for c in [24,25,26]:
  handoff=json.loads((root/f'candidate{c}/route-handoff.json').read_text())
  for name,oldhash in handoff['files'].items():
   f=root/f'candidate{c}'/name
   if f.exists()and sha(f)!=oldhash:superseded.append({'candidate':c,'filename':name,'historical_handoff_sha256':oldhash,'current_owner_file_sha256':sha(f),'historical_bytes_retained':False})
 write(stage/'checks/v8-historical-receipt-status.json',{'historical_handoffs_retained_unchanged_except_path_projection':True,'later_owner_receipts_recorded_separately':True,'overwritten_historical_receipts':superseded,'limitation':'Original overwritten receipt hashes remain in historical handoffs; their bytes are not claimed to be bundled. Current owner summaries and fresh DRC receipts are bound separately.'})
 write(stage/'checks/v8-portable-projections.json',{'schema':'f722-portable-path-projections/v1','files':maps,'historical_dependency_hashes_unchanged':True,'explanation':'Portable projections retain historical original hashes; full models, fixed report guards and full native exports are external inputs, not bundled.'})
 write(stage/'checks/v8-source-identity.json',{'schema':'f722-v8-source-selection/v1','base_manifest_sha256':sha(stage.parent/'public-source-ready-v7/FILES.sha256.json'),'sources':sources,'java_sources_byte_identical_to_v7':all(p.read_bytes()==(stage.parent/'public-source-ready-v7'/p.relative_to(stage)).read_bytes()for p in(stage/'src').rglob('*')if p.is_file()),'v7_root_importer_retained_exact':sha(stage/'import_session.py')==sha(stage.parent/'public-source-ready-v7/import_session.py'),'selected25_checkpoint':'model-candidate24-ready/filtered01.successes/second','selected26_checkpoint':'model-candidate24-ready/filtered01.successes/final','final_third_success_belongs_only_to26':True,'unfinished_filtered02_excluded':True,'heavy_execution_performed':False})
 print(json.dumps({'projected_files':len(maps),'source_receipts':len(sources),'stage':stage.name}))
if __name__=='__main__':main()
