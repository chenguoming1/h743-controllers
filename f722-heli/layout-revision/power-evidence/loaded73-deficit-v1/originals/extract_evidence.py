#!/usr/bin/env python3
"""Extract compact, hash-checked receipts from the released run; no solver calls."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).parent
RELEASE = ROOT/'static-power-validation/pilot-candidate15-loaded73-released'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
freeze = json.loads((RELEASE/'freeze.json').read_text())
checked = []
for name, row in freeze['files'].items():
    path = (RELEASE/row['path']).resolve()
    actual = sha(path)
    assert actual == row['sha256'], (name, actual)
    checked.append({'name':name,'path':str(path.relative_to(ROOT)),'sha256':actual})
result = json.loads((RELEASE/'result.json').read_text())
assert sha(RELEASE/'result.json') == '0780cece1cf4194220a542f9d7f65cc6be3dc457b9bbfaf74bd5a07fa3a1d9ac'
ledger = json.loads((RELEASE/'ledger.json').read_text())
native_path = (RELEASE/freeze['files']['geometry']['path']).resolve()
native = json.loads(native_path.read_text())
case_name = 'classic_BEC5_AB_mcu_vdd19_baseline'
case = next(c for c in result['runs'][1]['cases'] if c['case'] == case_name)
definition = next(c for c in ledger['cases'] if c['name'] == case_name)
assert case['case_definition_sha256'] == definition['case_definition_sha256']
v=case['voltage_V']
drop = {'U6_to_U7_copper_V':v['U6.OUT_7_8']-v['U7.3'],'U7_switch_V':v['U7.3']-v['DEV_U7_OUT'],
        'U6_to_feedback_top_V':v['U6.OUT_7_8']-v['R54.1']}
for port in ['J9','J10']:
    drop[port]={'downstream_positive_copper_V':v['DEV_U7_OUT']-v[port+'.3'],
                'return_to_source_ground_V':v[port+'.4'], 'local_pad_voltage_V':v[port+'.3']-v[port+'.4']}
pin_refs=['U6','U7','R54','R55','J9','J10','J11']
pins=[{k:o.get(k) for k in ['uuid','key','net','xy','all_layers']} for o in native['objects'] if o.get('key','').split('.')[0] in pin_refs and o.get('number')]
servo=next(c for c in result['runs'][1]['cases'] if c['case']=='same_BEC_all_cyclic_905X_J6_feed_lost_capacity__sample_mcu_vdd19')
evidence={'schema':'f722-independent-power-drop-extract/v1','result_sha256':sha(RELEASE/'result.json'),
 'frozen_inputs_verified':checked,'representative_case':case_name,'case_definition_sha256':case['case_definition_sha256'],
 'case_parameters':definition['parameters'],'terminal_mapping':pins,
 'voltage_V':v,'drop_decomposition':drop,'converters':case['converters'],'resistors':case['resistors'],
 'BEC_port_injections':next(p for p in case['port_injections'] if p['net']=='+5V_BEC'),
 'BEC_field':{k:case['fields']['+5V_BEC'][k] for k in ['copper_loss_W','sheet_loss_W','layer_sheet_loss_W','barrels']},
 'BEC_unit_transfer_ohm':next(p for p in result['runs'][1]['ports'] if p['net']=='+5V_BEC')['impedance_ohm'][-1][-1],
 'representative_servo_illustration':{'name':servo['case'],'probes':servo['probes'],'source_current_A':servo['source_current_A'],'resistors':servo['resistors']},
 'no_new_solver_run':True}
(OUT/'source-bound-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps({'frozen_files_verified':len(checked),'extract_sha256':sha(OUT/'source-bound-evidence.json'),'drops':drop},indent=2))
