#!/usr/bin/env python3
"""Capture the frozen candidate19–22 sources and compact receipts into v7 staging.

Use --workspace for the historical routing workspace. This reads source files
only; it does not alter candidates, route, or execute native imports.
"""
import argparse, hashlib, json, shutil
from pathlib import Path

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);a=ap.parse_args()
 root=a.workspace.resolve();stage=Path(__file__).resolve().parents[1];maps={};sources={}
 def copy(src,dst=None):
  dst=dst or src;p=root/src;q=stage/dst;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);sources[dst]={'historical_path':src,'sha256':sha(p)}
 def portable(obj):
  if isinstance(obj,dict): return {portable(k):portable(v)for k,v in obj.items()}
  if isinstance(obj,list): return [portable(v)for v in obj]
  if isinstance(obj,str):
   obj=obj.replace(str(root)+'/', '')
   if '/workspace/' in obj: raise AssertionError('Unmapped workspace path')
  return obj
 def project(src,dst,transform=None):
  p=root/src;d=json.loads(p.read_text());out=portable(d)
  if transform:out=transform(out)
  write(stage/dst,out);maps[dst]={'historical_path':src,'historical_file_sha256':sha(p),'portable_file_sha256':sha(stage/dst),'projection':'Package-relative historical paths; original byte identity remains separate. '+('Compact field selection, geometry values retained.' if transform else 'JSON values retained except path strings.')};return out
 for f in ['audit_outer_additions.py','prepare_screened_local.py','prepare_located_branch.py','run_bounded_local.py']: copy(f)
 for f in ['construct_power_candidate.py','audit_power_transaction.py','audit_endpoints.py','prepare_clamp_bridges.py','audit_clamp_applicability.py','prepare_peripheral.py','scan_c59.py']:
  copy('tests/power-feed-reconstruction/'+f)
 for f in ['prepare_port_b_native.py','screen.py','bbox-control.py']:copy('tests/local-closures20/'+f)
 for f in ['prove_shared_pad.py','test_located_preparation.py','REPRODUCE.md','proof.json','preparation-controls.json','source-reference-hashes.json','located-path-inventory.json','negative-outside-pad-input.json','negative-outside-pad-input.log']:
  copy('tests/shared-pad-alias21/'+f)
 project('tests/shared-pad-alias21/control-positive.json','tests/shared-pad-alias21/control-positive.json')
 project('tests/shared-pad-alias21/reproduced-proposal.json','tests/shared-pad-alias21/reproduced-proposal.json')
 for f in ['raw-located-path.json','partial-pad-cut-contract.json']:
  copy('candidate22/'+f,'tests/local-closures20/'+('port-b-located-path.json' if f=='raw-located-path.json' else f))
 for f in ['short-port-batch.log','short-port-batch.bounded-run.json','short-port-batch.progress.json','zero-parity.json']:
  copy('model-candidate21-ready/'+f,'tests/bounded-source21/'+f)
 assert sha(stage/'run_bounded_local.py')==json.loads((stage/'tests/bounded-source21/short-port-batch.bounded-run.json').read_text())['supervisor_sha256']
 # Preserve raw source/acceptance receipts. Their old pending statuses are historical.
 for c in [19,20,21,22]:
  for name in ['route-handoff.json','owner-summary.json','f722-heli.logical-route-map.json','power-audit.json']:
   project(f'candidate{c}/{name}',f'checks/candidate{c}-{name}')
  for name in (['owner-coordinated-integration.json','power-endpoints.json','peripheral-margin-receipt.json','c59-pose-screen.json'] if c==19 else ['owner-additive-integration.json','unchanged-power-reference.json','f722-heli.import.json']):
   project(f'candidate{c}/{name}',f'checks/candidate{c}-{name}')
 for name in ['partial-pad-cut.json','coverage-scope.json']:
  project('candidate22/'+name,'checks/candidate22-'+name)
 project('candidate21/bbox-control.json','tests/local-closures20/bbox-control.json')
 # Operational power proposal excludes diagnostic object polygons but retains every transaction argument.
 powerkeys=['schema','source_board_sha256','allowed_changed_nets','remove_tracks','remove_vias','segments','vias','inputs','old_bec_long_path','poses','combined_companion_screen_sha256']
 project('candidate19/power-proposal.json','sessions/power19/input-proposal.json',lambda d:{k:d[k]for k in powerkeys})
 d=json.loads((root/'candidate19/power-construction.json').read_text());summary={k:v for k,v in d.items()if k not in ['removed_objects','added_objects']}
 for k in ['removed_objects','added_objects']:
  summary[k+'_summary']=[{kk:vv for kk,vv in o.items()if kk in ['uuid','kind','net','start','end','width','xy','diameter','barrel_layers']}for o in d[k]]
 summary['historical_full_receipt_sha256']=sha(root/'candidate19/power-construction.json');summary['historical_full_receipt_bytes']=(root/'candidate19/power-construction.json').stat().st_size
 summary['omission']='Large exact native polygons are omitted. Reconstruct them by the retained source-bound native generator; historical full receipt identity is retained.'
 write(stage/'sessions/power19/construction-summary.json',summary)
 sources['sessions/power19/construction-summary.json']={'historical_path':'candidate19/power-construction.json','historical_full_sha256':summary['historical_full_receipt_sha256'],'compact_sha256':sha(stage/'sessions/power19/construction-summary.json')}
 for c,opens,proposal in [(20,65,'proposal.json'),(21,63,'screened-proposal.json'),(22,62,'located-native-proposal.json')]:
  packet=f'sessions/accepted{opens}'
  copy(f'candidate{c}/constructed.ses',packet+'/session.ses');copy(f'candidate{c}/constructed-report.json',packet+'/engine-report.json')
  contract=project(f'candidate{c}/native-construction-model.json',packet+'/original-import-contract.json')
  minimal={k:v for k,v in contract.items()if k!='physical_native'};write(stage/packet/'import-contract.json',minimal)
  project(f'candidate{c}/{proposal}',packet+'/input-proposal.json',(lambda d:{k:v for k,v in d.items()if k not in ['rejected_or_screened','cross_layer_skipped']})if c==21 else None)
  if c!=20:copy(f'candidate{c}/construction.json',packet+'/historical-construction.json')
  if c==22:copy('candidate22/raw-located-path.json',packet+'/raw-located-path.json')
  source=json.loads((root/f'candidate{c}/native-construction-model.json').read_text());report=json.loads((stage/packet/'engine-report.json').read_text())
  identity={'kind':'explicit_native_add_only_construction','board_sha256':source['board_sha256'],'native_sha256':source['native_sha256'],'model_sha256':sha(root/f'candidate{c}/native-construction-model.json'),'candidate_sha256':sha(root/f'candidate{c}/f722-heli.kicad_pcb'),'historical_original_import_contract_sha256':sha(root/f'candidate{c}/native-construction-model.json'),'original_import_contract_sha256':sha(stage/packet/'original-import-contract.json'),'historical_input_proposal_sha256':sha(root/f'candidate{c}/{proposal}'),'input_proposal_sha256':sha(stage/packet/'input-proposal.json'),'session_sha256':sha(stage/packet/'session.ses'),'engine_report_sha256':sha(stage/packet/'engine-report.json'),'import_contract_sha256':sha(stage/packet/'import-contract.json'),'portable_path_projections':'checks/v7-portable-projections.json','stock_engine_insertion_succeeded':False,'native_replay_reexecuted_for_v7':False,'new_tracks':{20:4,21:2,22:3}[c],'new_vias':0,'source_candidate':f'candidate{c-1}','historical_native_import_receipt':f'checks/candidate{c}-f722-heli.import.json'}
  assert identity['model_sha256']==report['model_sha256']
  write(stage/packet/'source-identity.json',identity)
 # Bind exact used source receipts without duplicating the same source in history folders.
 for c in [19,20,21,22]:
  for used in (root/f'candidate{c}').glob('*.used.py'):
   stem=used.name.replace('.used.py','.py');options=[stage/stem,stage/'tests/power-feed-reconstruction'/stem,stage/'tests/local-closures20'/stem]
   found=next((p for p in options if p.exists()and sha(p)==sha(used)),None)
   assert found,used
   sources[f'candidate{c}/{used.name}']={'package_source':str(found.relative_to(stage)),'sha256':sha(used)}
 write(stage/'checks/v7-portable-projections.json',{'schema':'f722-portable-path-projections/v1','path_base':'package root; external historical paths are documented inputs','files':maps,'historical_dependency_hashes_unchanged':True,'explanation':'Historical receipts retain original input hashes. The replay source identities explicitly bind projected contracts/proposals. A stored historical path does not imply an omitted model is bundled.'})
 write(stage/'checks/v7-source-identity.json',{'schema':'f722-v7-source-selection/v1','base_manifest_sha256':sha(stage.parent/'public-source-ready-v6/FILES.sha256.json'),'sources':sources,'java_sources_byte_identical_to_v6':all(p.read_bytes()==(stage.parent/'public-source-ready-v6'/p.relative_to(stage)).read_bytes()for p in(stage/'src').rglob('*')if p.is_file()),'importer_byte_identical_to_v6':(stage/'import_session.py').read_bytes()==(stage.parent/'public-source-ready-v6/import_session.py').read_bytes(),'later_trials_excluded':True})
 print(json.dumps({'projected_files':len(maps),'source_receipts':len(sources),'stage':stage.name}))
if __name__=='__main__':main()
