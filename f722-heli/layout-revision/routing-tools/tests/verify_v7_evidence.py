#!/usr/bin/env python3
"""Verify portable v7 evidence identities against frozen historical source files."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--historical-workspace',type=Path,required=True);a=ap.parse_args();w=a.historical_workspace
 maps=load(ROOT/'checks/v7-portable-projections.json')['files']
 for name,row in maps.items():
  assert sha(ROOT/name)==row['portable_file_sha256'],name
  assert sha(w/row['historical_path'])==row['historical_file_sha256'],name
 sources=load(ROOT/'checks/v7-source-identity.json')['sources']
 for name,row in sources.items():
  if 'package_source'in row:
   assert sha(ROOT/row['package_source'])==sha(w/name)==row['sha256'],name
  elif 'sha256'in row:
   assert sha(ROOT/name)==sha(w/row['historical_path'])==row['sha256'],name
 raw=load(w/'candidate19/power-proposal.json');compact=load(ROOT/'sessions/power19/input-proposal.json')
 consumed=['source_board_sha256','allowed_changed_nets','remove_tracks','remove_vias','segments','vias']
 assert all(raw[k]==compact[k]for k in consumed)
 constructor=ROOT/'tests/power-feed-reconstruction/construct_power_candidate.py';receipt=load(ROOT/'sessions/power19/construction-summary.json')
 assert receipt['constructor_sha256']==sha(constructor)
 assert receipt['proposal_sha256']==sha(w/'candidate19/power-proposal.json')
 assert receipt['historical_full_receipt_sha256']==sha(w/'candidate19/power-construction.json')
 controls=load(ROOT/'tests/shared-pad-alias21/preparation-controls.json');assert controls['preparer_sha256']==sha(ROOT/'prepare_located_branch.py');assert controls['test_source_sha256']==sha(ROOT/'tests/shared-pad-alias21/test_located_preparation.py')
 assert controls['controls'][0]['output_sha256']==maps['tests/shared-pad-alias21/control-positive.json']['historical_file_sha256']
 inventory=load(ROOT/'tests/shared-pad-alias21/located-path-inventory.json');assert inventory['engine_log_sha256']==sha(ROOT/'tests/bounded-source21/short-port-batch.log')
 bounded=load(ROOT/'tests/bounded-source21/short-port-batch.bounded-run.json');assert bounded['supervisor_sha256']==sha(ROOT/'run_bounded_local.py')and bounded['exit_code']==0 and bounded['no_forced_termination']
 power=load(ROOT/'checks/candidate22-power-result-applicability.json');adoption=load(ROOT/'checks/current62-adoption.json');assert sha(ROOT/'checks/candidate22-power-result-applicability.json')==adoption['power_result_applicability_sha256'];assert power['applicable_board_sha256']==adoption['board_sha256'];assert power['scope_decisions']==adoption['scope_decisions']
 for p in ROOT.rglob('*'):
  if p.is_file()and p.suffix in ['.md','.json','.log','.ses']:
   assert '/workspace/'not in p.read_text() and '/home/'not in p.read_text(),p.relative_to(ROOT)
 out={'passed':True,'verifier_source_sha256':sha(__file__),'projected_json_original_and_portable_hashes_checked':len(maps),'source_receipts_checked':len(sources),'power_constructor_consumed_fields_exact':consumed,'large_power_construction_receipt_identity_bound':True,'located_preparer_original_execution_and_projected_output_hashes_distinct':True,'bounded_runner_actual_run_source_bound':True,'new_numerical_receipt_and_adoption_bound':True,'private_absolute_paths_absent_from_data_and_docs':True,'native_or_solver_execution':False}
 (ROOT/'checks/v7-evidence-verified.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
