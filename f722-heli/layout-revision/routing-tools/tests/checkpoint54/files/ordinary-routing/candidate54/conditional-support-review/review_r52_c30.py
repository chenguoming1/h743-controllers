#!/usr/bin/env python3
"""Candidate06 R52/C30 conditional DC evidence; no board, solver, or old-report mutation."""
import hashlib,json,math
from pathlib import Path
H=Path(__file__).resolve().parent;C=H.parent;T=C.parent;R=T.parents[2]
paths={'board':C/'f722-heli.kicad_pcb','native':C/'f722-heli.native.json','proposal':C/'proposal.json','source14_proposal':T/'dedicated-u12-ground15/separated-returns14-proposal.json','quiet_alternatives':T/'dedicated-u12-ground15/quiet-return-alternatives14.json','construction_provenance':C/'construction-provenance.json','native_gate_summary':C/'owner-summary.json','TI_datasheet':R/'independent-core-voltage-review/sources/TPS25947.pdf','TI_text':R/'independent-core-voltage-review/sources/TPS25947.txt'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={k:sha(p) for k,p in paths.items()}
assert before['board']=='24121b0e46d9a71207cd21e7cf599412c00796d48eb9af5f63ffcf92e5f2ca42'
assert before['proposal']==before['source14_proposal']
assert before['TI_datasheet']=='8f96de389903091650d4f462dcfad3210071c3ae7093623a7978f34baf8a65b4'
n=json.loads(paths['native'].read_text());p=json.loads(paths['proposal'].read_text());prov=json.loads(paths['construction_provenance'].read_text());gates=json.loads(paths['native_gate_summary'].read_text())
assert n['board_sha256']==prov['board_sha256']==gates['board_sha256']==before['board']
assert p['source_board_sha256']==prov['source_board_sha256']=='73dbae05954b8edec4143d91248bf38c40537f83e8f5f3fed51744105169d6c7'
obs={o['uuid']:o for o in n['objects']};pad={o['key']:o for o in n['objects'] if o['kind']=='pad'}
parts={f['ref']:{k:f[k] for k in ['ref','value','xy','angle','side','fpid']} for f in n['footprints'] if f['ref'] in ['U5','R52','C30']}
assert parts['U5']['value']=='TPS259472ARPWR' and parts['R52']['value']=='750R / 1%' and parts['C30']['value']=='220nF / 16V / X7R'
for key,net in [('R52.1','EFUSE_ILM'),('R52.2','GND'),('U5.9','EFUSE_ILM'),('U5.8','GND'),('C30.1','ADC_BEC'),('C30.2','GND')]:assert pad[key]['net']==net
lead=obs['1bcd528f-ccfa-587e-9940-c40bbcdadd1c'];shared=obs['3971ab08-e156-4148-8f93-1a9c4636b51f'];v=obs['b931d764-eacd-41bd-af16-b2f6764a796a']
assert lead['start']==pad['R52.2']['xy'] and lead['end']==shared['start']==pad['C30.2']['xy']
assert shared['end']==v['xy']==[16.4574,15.8435]
assert lead['width']==.2 and shared['width']==.25 and set(shared['copper'])=={'F.Cu'}
assert next(x for x in p['paths'] if x['name']=='R52_via_C30_ground')['points']==[lead['start'],lead['end']]
device_ground_ids=['de2656d9-6b4b-4d85-a9e0-6b4a94bc80d3','804e54e5-1a24-4bf1-99a3-c7f8860e3573','5273dbcd-421f-42fd-a2c1-9c9d539d2d2c','6570cc7d-4117-40de-b942-62e04dce1497','c58df576-e0f7-4e7f-bf3a-40da1b455eb1']
def brief(o):return {k:o[k] for k in ['uuid','kind','key','net','xy','start','end','width'] if k in o}
length=lambda o:math.dist(o['start'],o['end'])
L=length(shared);rho20=1.724e-8;alpha=.00393;temperature=105;rho=rho20*(1+alpha*(temperature-20));thickness=15e-6;w=shared['width']*1e-3
r=rho*L*1e-3/(w*thickness);rail=2.;gainmax=200e-6;i=rail*gainmax
result={
 'status':'Conditional local R52/C30 review only; microvolt DC calculation does not establish low-noise ILM return or transient qualification.',
 'inputs':{k:{'path':str(v),'sha256':before[k]} for k,v in paths.items()},
 'board_sha256':before['board'],'source14_board_sha256':p['source_board_sha256'],'source14_proposal_byte_identical':True,
 'parts':parts,'pads':{k:brief(pad[k]) for k in ['R52.1','R52.2','C30.1','C30.2','U5.8','U5.9']},
 'paths':{'R52_to_C30':dict(brief(lead),length_mm=length(lead)),'shared_C30_to_via':dict(brief(shared),length_mm=L),'shared_via':dict(brief(v),drill_mm=v['drill']['width'],barrel_layers=v['barrel_layers']),'R52_to_first_plane_trace_centerline_mm':length(lead)+L,'U5_actual_GND_pin8_trace_records':[brief(obs[k]) for k in device_ground_ids],'U5_actual_GND_pin8_trace_centerline_mm':sum(length(obs[k]) for k in device_ground_ids),'U5_actual_GND_pin8_via':brief(obs['a9f49556-537f-4939-b5d5-d397fabd55ad']),'unchanged_ILM_signal_trace':brief(obs['ba8578ee-4584-4db5-ab85-d7cb5a9a6c71'])},
 'conditional_shared_copper_DC':{'rho20_assumed_ohm_m':rho20,'alpha_assumed_per_C':alpha,'copper_temperature_assumed_C':temperature,'rho105_ohm_m':rho,'thickness_assumed_um':15,'width_mm':.25,'length_mm':L,'formula':'rho20 * (1 + alpha*(105-20)) * L/(w*t)','resistance_ohm':r,'rail_normal_current_assumed_A':rail,'TI_GIMON_min_max_uA_per_A':[165,200],'ILM_max_current_A':i,'shared_drop_V':i*r,'shared_drop_uV':i*r*1e6,'fraction_of_nominal_750ohm_ppm':r/750*1e6,'nominal_R52_voltage_at_this_IMON_V':750*i,'shared_copper_dissipation_W':i*i*r,'excluded':['Via barrel/contact resistance','Ground-plane and U5.8 return impedance','Etch, width and copper-thickness manufacturing tolerances','C30 charging, ADC sampling and injected noise currents','Transient inductance/coupling','Overload/current-limit/fault behavior']},
 'TI_source':{'url':'https://www.ti.com/lit/ds/symlink/tps25947.pdf','document':'SLVSFC9C Rev. C, May 2026','gain_location':'Section 6.5, printed p10','gain_conditions':'At 2 A use the 1–5.5 A row with IOUT < ILIM. Table defaults include VIN=12V, RILM=549 ohm, −40°C≤TJ≤125°C; calculation is conditional under applicable stated specifications, not a measured 750-ohm circuit guarantee.','layout_location':'Section 8.4.1, printed pp62–63','pin_location':'Table 5-1, printed p5: actual device GND is pin8; ILM is pin9','layout_summary':'Short support-component returns to the device GND pin; quiet analog ground, separation from switching/noisy nodes; ILM parasitic capacitance below 50 pF.'},
 'decision':'Small resistive contribution at the specified normal operating point is supported. Coupling to the ADC_BEC capacitor return and the non-direct return to U5.8 remain unqualified. Prefer a verified quiet eFuse/device-ground return if routable; this review does not select or construct the fallback.',
 'existing_native_status_read_only':{'summary':str(paths['native_gate_summary']),'native_refill_performed':prov['native_refill_performed'],'critical_ground_return_faults':gates['critical']['faults'],'DRC':gates['drc'],'protection':gates['protection'],'note':'Existing gate results only, no checks rerun and no global acceptance inferred.'},
 'all_read_inputs_unchanged':True}
quiet=json.loads(paths['quiet_alternatives'].read_text())
assert before['quiet_alternatives']=='c4669bbbf554a8e2662a7df0de874776f373b75351c7673dc891babfbd16f4b7'
assert quiet['board_sha256']==p['source_board_sha256'] and quiet['width_mm']==.2
result['conditional_shared_copper_DC']['95_percent_IACS_sensitivity']={'definition':'Scale the stated approximately 100% IACS rho20 by 1/0.95, with the same assumed temperature coefficient.','rho105_ohm_m':rho/.95,'resistance_ohm':r/.95,'at_total_eFuse_2A_IMON_A':.0004,'at_total_eFuse_2A_drop_uV':r/.95*.0004*1e6,'at_datasheet_5p5A_illustration_IMON_A':.0011,'at_datasheet_5p5A_illustration_drop_uV':r/.95*.0011*1e6,'fraction_of_750ohm_ppm':r/.95/750*1e6}
result['load_scope_correction']='The external 2 A rail load is not a bound on total U5 current. Core/DSM loads can contribute when supplied through U5. The 0.4 mA illustration assumes total U5 IOUT is 2 A. The 5.5 A × 200 µA/A = 1.1 mA figure is a datasheet gain illustration only, not this board continuous-current rating or assurance that the selected 750-ohm current-limit setting permits 5.5 A normal operation. GIMON row still requires IOUT < ILIM.'
result['bounded_quiet_return_receipt']={k:v for k,v in quiet.items() if k not in ['R52_reachable_region','removed_ground_tracks']}
result['decision']='Small local DC resistive contribution is supported conditionally. ADC_BEC charge/sampling/noise coupling and device-ground potential remain unqualified. The supplied exact fixed-signal 0.20-mm F.Cu domain blocks the quiet R51 and actual U5.8 targets, while C30 is reachable; this is a local structural blocker, not global infeasibility. No fallback routing or broad diagnostic was run.'
assert before=={k:sha(v) for k,v in paths.items()}
(H/'evidence.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'shared_length_mm':L,'shared_R_ohm':r,'normal_IMON_upper_A':i,'shared_drop_uV':i*r*1e6,'inputs_unchanged':True},indent=2))
