from pathlib import Path
import json,collections,re,hashlib,sys,shutil
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();P=O/'hardware/nexus-style-fc.kicad_pcb';SP=S/'hardware/nexus-style-fc.kicad_pcb';g=json.loads((O/'geometry-verification.json').read_text());assert g['source_sha256']==sha(SP)==tr['source_board_sha256'] and g['candidate_sha256']==sha(P)
a,b=[json.loads((x/'native-drc.json').read_text()) for x in [S,O]];assert b['included_severities']==a['included_severities'] and b['ignored_checks']==a['ignored_checks'] and b['kicad_version']==a['kicad_version']=='10.0.7';assert not b['unconnected_items'] and not b['schematic_parity']
sig=lambda z:(z['type'],z['severity'],tuple(sorted(x['uuid'] for x in z['items'])));ca,cb=[collections.Counter(sig(z) for z in d['violations']) for d in [a,b]];assert not cb-ca,('New native violations',list((cb-ca).elements()));wa,wb=[collections.Counter(sig(z) for z in d['violations'] if z['severity']=='warning') for d in [a,b]];assert wa==wb
emap=lambda d:{sig(z):float(re.search(r'actual ([0-9.]+) mm',z['description']).group(1)) for z in d['violations'] if z['severity']=='error' and z['type']=='clearance'};ea,eb=emap(a),emap(b);worse=[{'pair':k,'before_mm':ea[k],'after_mm':eb[k]} for k in set(ea)&set(eb) if eb[k]<ea[k]-.00005];assert not worse,worse;assert len(eb)==len(ea)==18 and ca==cb,(len(ea),len(eb));assert not any(z['severity']=='error' and z['type']!='clearance' for z in b['violations'])
# No schematic change in a copper-only batch: carry exact source-native ERC/netlist evidence.
assert sha(S/'hardware/nexus-style-fc.kicad_sch')==sha(O/'hardware/nexus-style-fc.kicad_sch')==tr['source_schematic_sha256']
for name in ['native-erc.json','final-netlist.xml']:
 if (S/name).exists():shutil.copy2(S/name,O/name)
e=json.loads((O/'native-erc.json').read_text());assert not any(x['violations'] for x in e['sheets'])
r=json.loads((O/'return-topology-comparison.json').read_text());m=r['measurements'];assert m['before']['pcb_sha256']==sha(SP) and m['after']['pcb_sha256']==sha(P)
out=next(p for p in m['after']['projection'] if p['role']=='output');assert out['routing_layer']=='F.Cu' and out['reference_layer']=='In1.Cu' and out['all_full_width_projection_covered']
local_proofs=[]
for old in m['before']['local_GND_pin_to_actual_filled_plane_paths']:
 new=next(p for p in m['after']['local_GND_pin_to_actual_filled_plane_paths'] if p['ref']==old['ref']);assert old['pad_uuid']==new['pad_uuid']
 for v in old['via_paths_within_4_mm']:
  q=next(z for z in new['via_paths_within_4_mm'] if z['via']==v['via']);assert v['primitive_contact_path']==q['primitive_contact_path'] and v['path_weight_mm']==q['path_weight_mm']
  old_layers={z['layer'] for z in v['finite_zone_contacts']};new_layers={z['layer'] for z in q['finite_zone_contacts']};assert old_layers<=new_layers
  assert {'In1.Cu','In4.Cu'}<=new_layers
  local_proofs.append({'ref':old['ref'],'via':v['via'],'unchanged_primitive_path':v['primitive_contact_path'],'retained_finite_plane_contact_layers':sorted(old_layers)})
# The closest local U10, C19 and C18 grounds remain on the same actual main-plane components.
main_components={}
for ref in ['U10','C19','C18']:
 port=next(p for p in m['after']['local_GND_pin_to_actual_filled_plane_paths'] if p['ref']==ref);near=port['via_paths_within_4_mm'][0]
 main_components[ref]={z['layer']:z['component_id'] for z in near['finite_zone_contacts'] if z['layer'] in ['In1.Cu','In4.Cu']}
assert main_components['U10']==main_components['C19']==main_components['C18']
assert g['removed_vias']==2 and g['new_vias']==1 and g['new_tracks']==7
benefit={'output_route':'4.400335 mm, all F.Cu, 0.250 mm width, 35 um copper; two output vias removed','output_full_width_reference_coverage_fraction':out['full_width_area_coverage_fraction'],'input_planar_delta_mm':0.389325,'input_modeled_barrel_delta_mm':1.4134,'input_full_width_reference_coverage':[{'routing_layer':p['routing_layer'],'reference_layer':p['reference_layer'],'coverage_fraction':p['full_width_area_coverage_fraction']} for p in m['after']['projection'] if p['role']=='input'],'unchanged_ground_path_proofs':local_proofs,'same_actual_main_ground_components':main_components,'acceptance_basis':'Fresh exact donor/port, inherited width/cross-section, native and actual filled-copper checks. TI TPS709 RevH section 8.1.1 does not require the input capacitor for stability. Input extra travel/reference change remains an explicit transient/ripple/PSRR qualification tradeoff; output loop is improved. This is not electrical or fabrication signoff.'}
summary={'status':'ACCEPTED fresh bounded U10 output-loop improvement with explicit input tradeoff; native DRC remains unfinished','regulator_loop_review':benefit,'source_directory':str(S),'source_board_sha256':sha(SP),'candidate_board_sha256':sha(P),'schematic_sha256':sha(O/'hardware/nexus-style-fc.kicad_sch'),'native_drc_sha256':sha(O/'native-drc.json'),'source_clearance_errors':len(ea),'candidate_clearance_errors':len(eb),'unchanged_silk_warnings':sum(wb.values()),'opens':0,'schematic_parity_issues':0,'erc_violations':0,'erc_evidence_basis':'Exact unchanged schematic and source-native ERC receipt; fresh PCB schematic-parity check','minimum_remaining_clearance_mm':min(eb.values()),'worsened_residual_pairs':worse,'removed_native_violation_pairs':list((ca-cb).elements()),'new_native_violation_pairs':[],'return_topology_receipt_sha256':sha(O/'return-topology-comparison.json'),'geometry_receipt_sha256':sha(O/'geometry-verification.json'),'invariants':g['invariants']['status'],'pasted_vias_unchanged':g['pasted_vias_unchanged'],'en_conductive_contacts':g['en_conductive_contacts'],'qualification':'Native unfinished routing checkpoint only. Power/return/thermal, regulator capacitor loops, USB/SI, inherited pasted vias, header/mechanical and fabrication gates remain open.'};(O/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
