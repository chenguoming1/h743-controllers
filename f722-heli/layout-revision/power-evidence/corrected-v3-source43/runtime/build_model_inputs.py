#!/usr/bin/env python3
"""Generate immutable corrected model templates only; no compiler or solve."""
import hashlib,json
from pathlib import Path
from power_case_model import digest,context_receipt,require,REQUIRED_PADS
from model_contract import definition_contract

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')

def main():
    old_path=PROJECT/'static-power-validation/pilot-candidate19-operator-refined-released/ledger.json'
    require(sha(old_path)=='f811c4d93dd074e5d74fb000db2d1218d10199ceb7c0562173be437fda572951','Historical primary changed')
    old=read(old_path)
    paths={name:ROOT/name for name in ['case-plan.corrected.disabled.json','terminal-registry.corrected.disabled.json','compiler-settings.json']}
    require(not any(p.exists() for p in paths.values()),'Preserve existing model templates')
    settings=read(PROJECT/'static-power-validation/compiler-settings.candidate19-refined.json')
    settings.update(source_stage='Corrected physical terminals and actual downstream supply windows; conditional prototype only',
                    owner_reviewed_model_sha256=None)
    physical=read(PROJECT/'power-terminal-correction-v1/review-candidate41/ledger.proposed.disabled.json')
    registry={'schema':'f722-corrected-terminal-registry-disabled/v2','execution_enabled':False,
              'contacts':{name:{'net':n['net'],**spec} for n in physical['networks'] for name,spec in n['contacts'].items()}}
    audit=read(PROJECT/'independent-core-voltage-review/power-path-subcheck/audit.json')
    native=read(PROJECT/'ordinary-routing/candidate41/owner-native.json')
    parts=read(PROJECT/'ordinary-routing/candidate41/parts.json')
    pad_contract={row['key']:{'net':row['native_net'],'layers':sorted(row['native_copper_layers']),
                             'function':row['manufacturer_function']} for row in audit['pad_comparisons']}
    for key,(net,layer) in REQUIRED_PADS.items():
        pad_contract[key]={'net':net,'layers':[layer],'function':'See sealed independent CORE supply/pin review'}
    selected={ref:{'mpn':parts[ref]['mpn'],'proposed_footprint':parts[ref]['proposed_footprint']} for ref in
              ['U1','U2','U3','U4','U5','U6','U7','U8','U9','U10','U11','FB1','FB2','R54','R55','R16']}
    plan={'schema':'f722-corrected-case-plan-disabled/v2','execution_enabled':False,
          'historical_primary':old,'historical_primary_definition_sha256':digest(old),
          'historical_primary_file_sha256':sha(old_path),'historical_context_equivalence':context_receipt(old),
          'current_selected_parts':{ref:row['mpn'] for ref,row in selected.items()},
          'selected_part_contract':selected,'physical_pad_contract':pad_contract,
          'VCAP_copper_loops':old['loops'],
          'source_observation_only':{'board_sha256':native['board_sha256'],'native_sha256':sha(PROJECT/'ordinary-routing/candidate41/owner-native.json'),
                                     'meaning':'Does not freeze or authorize any future source; compiler and planner rebind physical evidence.'},
          'conditional_limits':{'BEC_electronics_A':.32,'USB_electronics_A':.30,'each_filtered_branch_A':.02,'IMU_shared_branch_A':.02,
                                'ferrite_hot_DCR_screen_ohm':1.,'manufacturer_hot_DCR_guarantee':False,'nonlinear_interior_extrema_proved':False,
                                'package_ground_current_split_proved':False,'copper_temperature_is_ambient':False},
          'evidence_sha256':{str(p.relative_to(PROJECT)):sha(p) for p in [
              PROJECT/'independent-core-voltage-review/REPORT.md',
              PROJECT/'independent-core-voltage-review/power-path-subcheck/audit.json',
              PROJECT/'independent-core-voltage-review/supply-limits.json',
              PROJECT/'repo/f722-heli/docs/passive-bom-evidence.md']}}
    plan['model_contract']=definition_contract(plan,registry,settings)
    registry['model_contract_sha256']=digest(plan['model_contract'])
    for key,value in [('case-plan.corrected.disabled.json',plan),('terminal-registry.corrected.disabled.json',registry),('compiler-settings.json',settings)]:save(paths[key],value)
    print(json.dumps({'model_contract_sha256':digest(plan['model_contract']),'counts':plan['model_contract']['counts'],
                      'context_equivalence':plan['historical_context_equivalence'],'compiled':False,'solved':False}))

if __name__=='__main__':main()
