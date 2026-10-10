"""Seal the complete shared PORT_A/PORT_B native checkpoint; never mutate copper."""
import hashlib, json, pathlib, shutil, sys
H=pathlib.Path(__file__).resolve().parent; R=H.parents[2]; D=H/'candidate05'; B=H.parent/'port-b48/candidate03'; S=R/'ordinary-routing/candidate50'
read=lambda p:json.loads(pathlib.Path(p).read_text())
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write(name,value): (D/name).write_text(json.dumps(value,indent=2)+'\n')
h=sha(D/'f722-heli.kicad_pcb'); old=sha(S/'f722-heli.kicad_pcb'); bh=sha(B/'f722-heli.kicad_pcb')
assert h=='80eb38da7100fd677862b8d3bc161329b278c410614f3b15460b5a5c863a75e6'
summary=read(D/'owner-summary.json'); assert summary['board_sha256']==h
assert summary['drc']==summary['drc-all']==dict(unconnected=19,errors=0,warnings=0)
for k in ['process','mechanical','parity','firmware']: assert summary[k]['passed'] and summary[k]['board_sha256']==h
assert not read(D/'owner-drc-parity.json')['schematic_parity']
assert all(not sheet['violations'] for sheet in read(D/'owner-erc.json')['sheets'])
assert not summary['critical']['faults'] and summary['critical']['connected_nets']==16
for name in ['entry-support-audit.json','power-audit.json','native-coordinated-integration.json','remaining-MCU-access.json','reference-runtime-index-proof-v2-verification.json']:
 q=read(D/name); assert q['passed'] and q['board_sha256']==h, name
ref=read(D/'combined-signal-reference-review.json'); assert ref['board_sha256']==h
assert ref['all_new_tracks_reference_complete_outside_explicit_own_via_windows']
assert ref['all_full_footprints_exact']==156 and ref['all_full_pad_records_exact']==558
assert all(x['all_reference_outside_own_windows_empty'] for x in ref['summary'].values())
for name in ['reference-comparison-B03.json','reference-comparison50.json']:
 q=read(D/name); assert all(all(v==0 for v in row.values())for row in q['net_numeric_deltas_after_minus_before'].values())
proof=read(D/'reference-runtime-index-proof-v2.json'); assert proof['passed'] and len(proof['negative_controls'])==10
audit=read(D/'entry-support-audit.json'); assert audit['total_reviewed_track_endpoints']==96 and all(x['rejected'] for x in audit['negative_controls'])
nrst=read(D/'NRST-topology-review.json'); assert nrst['board_sha256']==h and nrst['C10_to_U1_local_path_exactly_preserved'] and nrst['complete_four_pad_tree'] and nrst['all_six_terminal_pairs_reachable']
protect=read(D/'protection-actual-io.json')
complete={x['net']:x for x in protect['checks']}
for net in ['PORT_A_RX_EXT','PORT_A_TX_EXT','PORT_B_RX_EXT','PORT_B_TX_EXT']: assert complete[net]['complete_clamp_first_path_passes']

# Independently recompute the cumulative transaction from saved native records.
n=read(D/'f722-heli.native.json'); n0=read(S/'f722-heli.native.json'); nb=read(B/'f722-heli.native.json')
by=lambda data:{o['uuid']:o for o in data['objects']}
physical=lambda o:{k:v for k,v in o.items() if k!='net_code'}
x,y,z=by(n0),by(n),by(nb)
removed=sorted(x.keys()-y.keys()); added=sorted(y.keys()-x.keys()); changed=sorted(k for k in x.keys()&y.keys() if physical(x[k])!=physical(y[k]))
cum=read(D/'cumulative50-transaction.json')
assert removed==cum['removed_ids'] and added==cum['added_ids'] and changed==cum['changed_ids']
assert len(x)==2045 and len(y)==2139 and len(x.keys()&y.keys())-len(changed)==2001
assert sorted({x[k]['net'] for k in removed+changed}|{y[k]['net']for k in added+changed})==cum['actual_changed_nets']==cum['allowed_changed_nets']
assert n['footprints']==nb['footprints']; assert len(n['footprints'])==156
assert sum(o['kind']=='pad'for o in y.values())==558
assert all(physical(o)==physical(y[k])for k,o in z.items()if o['kind']=='pad')
prov=read(D/'construction-provenance.json'); assert prov['retained_object_count']==2083 and prov['source_object_count']==2097
assert len(prov['added_records'])==54 and len(prov['removed_source_records'])==12 and len(prov['changed_records'])==2
write('cumulative50-native-transaction-verification.json',dict(passed=True,source_board_sha256=old,board_sha256=h,source_object_count=len(x),retained_object_count=2001,added_object_count=len(added),removed_object_count=len(removed),changed_object_count=len(changed),native_object_count=len(y),actual_changed_nets=cum['actual_changed_nets'],footprint_transforms=cum['footprint_transforms'],all156_full_footprints_and558_full_pad_records_exact_vs_B03=True,method='Exact saved native object comparison excluding only runtime net_code; no coordinate or polygon normalization.'))

# Preserve every B handoff receipt and its exact hash, including the intermediate residual.
bd=H.parent/'port-b48'; hand=read(bd/'HANDOFF50-TO-COMBINED19.json')
assert hand['combined_corrected_board_sha256']==h
lineage=D/'lineage'; lineage.mkdir(exist_ok=True)
external=[]
for row in hand['files']:
 p=R/row['path']; assert sha(p)==row['sha256'],p
 target=lineage/row['path']; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,target)
 external.append(dict(source=row['path'],sha256=row['sha256'],copied_as=str(target.relative_to(D))))
for name in ['proposal.json','construction-provenance.json','declared-footprint-transforms.json','coordinated-change-receipt.json','owner-summary.json','quick-drc.json','new-route-reference-review.json']:
 p=B/name
 if p.exists():
  target=lineage/'B03'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
  external.append(dict(source=str(p.relative_to(R)),sha256=sha(p),copied_as=str(target.relative_to(D))))
for dirname,names in {'candidate02':['quick-drc.json'],'candidate03':['new-route-reference-review.json','proposal.json'],'candidate04':['new-route-reference-review.json','combined-signal-reference-review.json','return-correction-review.json','proposal.json']}.items():
 for name in names:
  p=H/dirname/name; assert p.exists(),p
  target=lineage/dirname/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
  external.append(dict(source=str(p.relative_to(R)),sha256=sha(p),copied_as=str(target.relative_to(D))))
write('lineage-receipt-bindings.json',dict(board_sha256=h,files=external,raw_B_RX_and_A_reference_residuals_preserved=True,raw_dangling_SBUS_warning_preserved=True,B_native_intermediate_adoption_not_assumed=True))

# Recheck the last two-track repair against actual saved ground, without changing contours.
sys.path.insert(0,str(R/'repo/f722-heli/layout-revision/signal-review/native'))
from check_critical_reference import ground_geometry
from check_signal_geometry import copper_entries
na=read(H/'candidate04/f722-heli.native.json')
_,_,g0,_=ground_geometry(na,copper_entries(na)); _,_,g1,_=ground_geometry(n,copper_entries(n))
ground={l:dict(lost_area_mm2=g0[l].difference(g1[l]).area,gained_area_mm2=g1[l].difference(g0[l]).area,exact_set_equal=g0[l].equals(g1[l]))for l in ['In1.Cu','In4.Cu']}
assert all(v['exact_set_equal'] and v['lost_area_mm2']==v['gained_area_mm2']==0 for v in ground.values())
write('final-return-correction-review.json',dict(source_board_sha256=na['board_sha256'],board_sha256=h,patch_review='composed-patch-review.json',patch_receipt_sha256=sha(bd/'rx-reference-repair-on-A04.json'),all_ground_physical_sets=ground,final_projection='combined-signal-reference-review.json',final_projection_sha256=sha(D/'combined-signal-reference-review.json'),all8_interface_nets_width_and_centerline_complete_outside_own_via_windows=True,raw_residuals_preserved='lineage-receipt-bindings.json',no_polygon_repair_or_threshold_rounding=True,AC_return_qualified=False))
power_paths=read(B/'conditional-power-path-review.json')
bp=read(bd/'combined19-power-path-binding.json'); assert bp['board_sha256']==h and bp['geometric_observation_rebind_passed']
write('power-revalidation-required.json',dict(board_sha256=h,source_board_sha256=old,numerical_power_and_VCAP_applicability=False,geometric_support_continuity_passed=True,all28_support_groups_exact=True,reference_planes_refilled=True,reason='New signal via antipads, the C58 ground-lead rebuild and CORE feed reconstruction change actual current and return geometry. Historical numerical power, VCAP and regulator-stability evidence is not applicable.',C58_full_ground_witness_before_after_mm=[power_paths['C58'][k]['planar_ground_witness_center_length_mm']for k in ['source50','candidate22']],C58_external_planar_loop_before_after_mm=[power_paths['C58'][k]['complete_external_planar_loop_witness_length_mm']for k in ['source50','candidate22']],C58_witness_is_one_possible_plane_path_not_shortest_or_unique_AC_return=True,C74_feed_width_mm=.4,C74_feed_length_before_after_mm=[power_paths['C74'][k]['feed_via_to_positive_pad']['planar_track_length_mm']for k in ['source50','candidate22']],C74_finite_annular_rectangle_connectivity_only_not_ampacity_or_process_margin=True,CORE_feed_width_mm=.3,CORE_bridge_length_before_after_mm=[power_paths['CORE']['removed_track_length_mm'],power_paths['CORE']['replacement_track_length_mm']],source_bound_exact_paths_and_widths=str((lineage/'ordinary-routing/tests/port-b48/candidate03/conditional-power-path-review.json').relative_to(D)),actual_final_plane_witness_binding=str((lineage/'ordinary-routing/tests/port-b48/combined19-power-path-binding.json').relative_to(D)),transient_qualification_claimed=False,I2C_electrical_status='NOT_QUALIFIED'))
write('coordinated-change-receipt.json',dict(schema='f722-shared-PORT-A-PORT-B-native-reconstruction/v1',source_board_sha256=bh,cumulative_source_board_sha256=old,board_sha256=h,allowed_changed_nets=['PORT_A_RX_EXT','PORT_A_TX_EXT','NRST','PORT_B_RX_MCU'],cumulative_allowed_changed_nets=cum['allowed_changed_nets'],source_object_count=2097,retained_object_count=2083,removed_source_objects=prov['removed_source_records'],added_objects=prov['added_records'],changed_source_objects=prov['changed_source_records'],all156_full_footprints_and558_full_pad_records_exact_vs_B03=True,cumulative_footprint_transforms=cum['footprint_transforms'],cumulative_transaction='cumulative50-transaction.json',complete_NRST_topology='NRST-topology-review.json',PORT_A_branch_lengths='PORT_A-branch-lengths.json',remaining_access='remaining-MCU-access.json',reference_projection='combined-signal-reference-review.json',B_local_reference_correction='shared-B-return-patch.json',B_reference_and_power_receipts='lineage-receipt-bindings.json',all28_support_groups_restored=True,provisional_SBUS_escape_stub_and_via_omitted=True,reserved_SBUS_portal_mm=[17.12882,6.83933],numerical_power_VCAP_applicable=False,owner_adoption_claimed=False))
write('f722-heli.import.json',dict(schema='f722-explicit-coordinated-native-construction-receipt/v1',passed=True,source_sha256=bh,output_sha256=h,cumulative_source_sha256=old,construction_source_sha256=bh,construction_kind='Complete protected PORT_A external RX/TX branches, full NRST transition restoration and exact two-track PORT_B RX reference correction on complete B03.',direct_engine_output=False,engine_routing_succeeded=False,engine_partial_geometry_adopted=False,ses_engine_native_geometry_equal=False,session_artifact=None,coordinated_change_receipt='coordinated-change-receipt.json',coordinated_change_receipt_sha256=sha(D/'coordinated-change-receipt.json'),construction_provenance='construction-provenance.json',construction_provenance_sha256=sha(D/'construction-provenance.json'),logical_route_map_artifact='f722-heli.logical-route-map.json',logical_route_map_sha256=sha(D/'f722-heli.logical-route-map.json'),undeclared_native_changes=0,footprints_preserved=156,footprints_transformed=0,cumulative_footprints_transformed=3,reference_plane_refill_performed=True,fresh_model_zero_control_performed=False,numerical_power_VCAP_applicable=False,owner_review_pending=True))

helpers=['seal_ext05.py','remaining_access05.py','compose_shared_return_patch.py','finalize_composed05.py','construct_ext.py','refill_ext.py','bind_return_corrected.py','audit_ext_entries05.py','extra_ext_gates05.py','reference_combined_routes05.py','audit_nrst_topology05.py','audit_ext_branch_lengths05.py','record_return_correction.py','native_geometry_ext50.py','inspect_ext50.py']
for name in helpers: shutil.copy2(H/name,D/(pathlib.Path(name).stem+'.used.py'))
write('README.json',dict(board_sha256=h,status='Native-verified checkpoint19, awaiting independent owner adoption; still an incomplete board.',completed='All PORT_A and PORT_B external protected branches plus B MCU routes and SWDIO; full NRST replacement restored.',native_drc=summary['drc'],all_four_UART_actual_bonded_pad_cut_checks_pass=True,total_actual_IO22_passed=17,total_actual_IO22=22,remaining_protection_nets=[x['net']for x in protect['checks']if not x['complete_clamp_first_path_passes']],return_scope='Actual saved reference projection is empty outside explicit own-via windows on all eight reviewed interface nets. This is a geometric screen, not AC return, impedance, timing, EMC, hardware or flight qualification.',conditional_power='power-revalidation-required.json',I2C_electrical_status='NOT_QUALIFIED',owner_adoption_pending=True))
handoff=dict(schema='f722-native-route-handoff/v1',status='frozen_native_verified_19_open_complete_PORT_A_PORT_B_geometric_WIP_pending_owner_review',board_sha256=h,integration_source_sha256=bh,cumulative_integration_source_sha256=old,drc=dict(unconnected=19,errors=0,warnings=0,strict_schematic_parity=0,ERC_violations=0),coordinated=True,allowed_changed_nets=['PORT_A_RX_EXT','PORT_A_TX_EXT','NRST','PORT_B_RX_MCU'],cumulative_allowed_changed_nets=cum['allowed_changed_nets'],declared_footprint_transforms='declared-footprint-transforms.json',cumulative_footprint_transforms=cum['footprint_transforms'],all156_full_footprints_and558_full_pads_exact_vs_B03=True,source_object_count=2097,retained_object_count=2083,removed_source_objects=12,added_native_objects=54,changed_source_objects=2,new_signal_vias=8,entry_support_audit='entry-support-audit.json',finite_new_and_changed_endpoints=96,endpoint_negative_controls=18,remaining_MCU_access_review='remaining-MCU-access.json',complete_NRST_review='NRST-topology-review.json',PORT_A_complete_branch_lengths='PORT_A-branch-lengths.json',all8_new_interface_reference_review='combined-signal-reference-review.json',raw_critical_object_geometry_identical_vs50=False,critical_reference_runtime_net_index_proof='reference-runtime-index-proof-v2.json',critical_reference_report_and_numeric_deltas_exact=True,reference_negative_controls=10,actual_ground_plane_changes_preserved=True,cumulative_native_transaction='cumulative50-transaction.json',B_sealed_evidence_and_raw_failures='lineage-receipt-bindings.json',C74_annular_witness_connectivity_only=True,numerical_power_VCAP_applicable=False,signal_quality_qualified=False,protection_transient_qualified=False,reference_AC_qualified=False,I2C_electrical_status='NOT_QUALIFIED',owner_adoption_pending=True,direct_engine_output=False,fresh_router_zero_replay_performed=False)
handoff['files']={str(q.relative_to(D)):sha(q)for q in sorted(D.rglob('*'))if q.is_file()and q!=D/'route-handoff.json'}
write('route-handoff.json',handoff)
assert all(sha(D/path)==digest for path,digest in handoff['files'].items())
assert sha(D/'f722-heli.kicad_pcb')==h
print(json.dumps(dict(board_sha256=h,status=handoff['status'],files=len(handoff['files']),handoff_sha256=sha(D/'route-handoff.json'))))
