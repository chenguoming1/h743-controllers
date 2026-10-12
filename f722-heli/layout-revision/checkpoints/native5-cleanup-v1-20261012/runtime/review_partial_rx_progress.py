"""Exact bounded partial-RX review and negative controls."""
import copy

GATE='R34_to_actual_RX_IO1_improved_and_safe_partial_path'


SOURCE='1904a95f-ded8-4123-a94a-79e3bebb7a86'


IO='76401567-1405-4a22-b70c-0a7f2502777e'


NC='85f6ae89-da40-4223-9e1c-51ee8cc2f22f'


TARGET='e1836b38-f5b7-467f-aa6e-2b94f3177ac6'


NET='PORT_C_RX_EXT'


def require(ok,message):
 if not ok:raise ValueError(message)


def inventory(native):
 rows=[r for r in native['objects'] if r['net']==NET]
 return {'complete_inventory_from_bound_native':True,'net':NET,'zone_count':sum(z['net']==NET for z in native['zones']),'objects':[{'uuid':r['uuid'],'kind':r['kind'],'key':r.get('key'),'layers':sorted(r['copper']),'has_copper_on_every_declared_layer':bool(r['copper']) and all(bool(v) for v in r['copper'].values())} for r in rows]}


def evaluate(report,inv):
 case=next(r for r in report['all22_actual_IO_cuts'] if r['original_raw_contract']['contract']['clamp']=='U15.1')
 rx=case['candidate'];net=next(r for r in report['all_physical_nets'] if r['net']==NET)
 branch=next(r for r in report['updated_branch_cut_checks'] if r['declared_candidate_branch_contract']['net']==NET)
 source=next((r for r in inv['objects'] if r['uuid']==SOURCE),None);others=[r for r in inv['objects'] if r['uuid']!=SOURCE]
 source_layers=set(source['layers']) if source else set();other_layers={l for r in others for l in r['layers']}
 all_ids={r['uuid'] for r in inv['objects']};pads={r['uuid'] for r in inv['objects'] if r['kind']=='pad'}
 inventory_known=bool(inv.get('complete_inventory_from_bound_native')) and inv['net']==NET and inv['zone_count']==0 and len(all_ids)==len(inv['objects'])==7 and pads=={SOURCE,IO,NC,TARGET} and all(r['kind'] in ['pad','track'] and r['has_copper_on_every_declared_layer'] and r['layers'] for r in inv['objects'])
 isolated_source_partition=sorted(map(sorted,net['candidate_raw_pad_partition']))==sorted([[SOURCE],sorted([IO,NC,TARGET])])
 # Conservative supersets suffice: every remaining RX object is on the opposite
 # outer copper layer, so neither endpoint's post-cut fragment set can share it.
 # Saved fills, vias, extra records and unknown/empty contours fail this scope.
 no_shared_layer=inventory_known and source_layers=={'F.Cu'} and other_layers=={'B.Cu'} and isolated_source_partition
 widths=rx.get('connected_branch_full_width',[]);target=next((r for r in widths if r['role']=='target'),{})
 gaps=rx.get('outside_pad_gaps',[])
 gap_evidence=(bool(gaps) and all(g['passed'] for g in gaps)) or (not gaps and no_shared_layer)
 checks={
  'full_RX_stays_explicitly_incomplete':rx['status']=='INCOMPLETE_BEFORE_CUT' and rx['passed'] is False and rx['full_actual_function_connected'] is False and rx['source_to_actual_IO_connected'] is False,
  'actual_R34_to_IO1_connected':rx['target_to_actual_IO_connected'] is True,
  'new_RX_physical_pad_relationships':bool(net['native6_new_pad_pairs']) and bool(net['native7_new_pad_pairs']),
  'raw_pad_pair_preservation':not net['native6_lost_pad_pairs'] and not net['native7_lost_pad_pairs'] and report['native6_lost_pad_pair_count']==report['native7_lost_pad_pair_count']==0,
  'multi_layer_cut_no_bypass_and_endpoint_survival':rx['no_outside_actual_pad_bypass'] is True and branch['all_external_pads_survive_actual_IO_cut'] is True and branch['other_endpoint_reaches_NC_after_actual_IO_cut'] is False,
  'connected_R34_branch_full_width':target.get('connected_before_actual_IO_cut') is True and target.get('survives_cut') is True and target.get('passed_when_connected') is True and bool(target.get('full_width_same_side_witnesses')) and any(w['passed'] for w in target['full_width_same_side_witnesses']),
  'declared_actual_IO_NC_branch_passed':branch['passed'] is True and branch['NC_internal_continuity_assumed'] is False,
  'gap_evidence_or_proved_no_common_conductive_layer':gap_evidence,
 }
 return {'checks':checks,'partial_RX_progress_gate_passed':all(checks.values()),'full_RX_protection_passed':False,'full_RX_status':rx['status'],'raw_gap_list':gaps,'empty_gap_disposition':'PROVED_NO_COMMON_CONDUCTIVE_LAYER' if not gaps and no_shared_layer else 'REJECT_EMPTY_GAPS_LAYER_PROOF_MISSING' if not gaps else 'RAW_SAME_LAYER_GAPS_RETAINED','layer_proof':{'complete_inventory_known':inventory_known,'source_cut_component_layer_superset':sorted(source_layers),'target_cut_component_layer_superset':sorted(other_layers),'common_layers':sorted(source_layers&other_layers),'isolated_source_partition':isolated_source_partition,'proof_is_conservative_object_layer_superset':True},'raw_false_gate_preserved':report['diagnostic_gates'][GATE],'raw_all_required_checks_passed_preserved':report['all_required_topology_and_support_checks_passed']}


def controls(report,inv):
 result=evaluate(report,inv);require(result['partial_RX_progress_gate_passed'],'Positive bounded RX disposition failed');rows=[{'name':'actual_bound_partial_RX_positive','passed':True}]
 def reject(name,edit_report=None,edit_inventory=None):
  a,b=copy.deepcopy(report),copy.deepcopy(inv)
  if edit_report:edit_report(a)
  if edit_inventory:edit_inventory(b)
  require(not evaluate(a,b)['partial_RX_progress_gate_passed'],name+' unexpectedly accepted');rows.append({'name':name,'passed':True})
 def rx(a):return next(x['candidate'] for x in a['all22_actual_IO_cuts'] if x['original_raw_contract']['contract']['clamp']=='U15.1')
 reject('shared_layer_empty_gap_rejected',edit_inventory=lambda a:a['objects'][-1].update(layers=['F.Cu','B.Cu']))
 reject('unknown_inventory_empty_gap_rejected',edit_inventory=lambda a:a.update(complete_inventory_from_bound_native=False))
 reject('RX_zone_without_cut_layer_proof_rejected',edit_inventory=lambda a:a.update(zone_count=1))
 reject('multi_layer_bypass_rejected',edit_report=lambda a:rx(a).update(no_outside_actual_pad_bypass=False))
 reject('target_disconnected_rejected',edit_report=lambda a:rx(a).update(target_to_actual_IO_connected=False))
 reject('target_full_width_failure_rejected',edit_report=lambda a:next(w for w in rx(a)['connected_branch_full_width'] if w['role']=='target').update(passed_when_connected=False))
 reject('unrelated_baseline_pair_loss_rejected',edit_report=lambda a:a.update(native6_lost_pad_pair_count=1))
 reject('full_RX_claim_rejected_by_partial_disposition',edit_report=lambda a:rx(a).update(full_actual_function_connected=True,status='IO_CUT_PASS',passed=True))
 return rows

