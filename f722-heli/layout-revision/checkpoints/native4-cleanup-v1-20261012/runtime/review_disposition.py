"""Exact source-bound saved-contact predicates; no geometry execution."""

CORE='fbaaee06-6e3d-5b45-b993-1fb424b507ee';CORE_VIA='18a1add5-6c53-4a95-80c9-5d3c184890c1'


CORE='fbaaee06-6e3d-5b45-b993-1fb424b507ee';CORE_VIA='18a1add5-6c53-4a95-80c9-5d3c184890c1'


VX={'2f68e32c-4199-4e40-bffa-04055f629681','916c3c9a-af23-4966-abb1-0f5d540569e7','bff99bb6-bcb9-43ee-97db-c5cf44f4a799','ca49f8ab-b5a6-4faf-9e5c-d77b66ae33bd','dc033951-9af9-426d-84f7-e3be434c25d3'}


GATES={'all_new_track_endpoints_union_or_annulus_supported','RED_retained_B_lead_full_width_join','VX_polygon_all_original_terminal_contacts_supported'}


def section(row,width):
 best=row['best'];return bool(best) and best['passed'] is True and best['nominal_width_mm']==width and best['contiguous_width_mm']>=width-.00002 and best['clip_boundary_margin_mm']>.00002 and len(best['section_mm'])==2


def evaluate(local,raw,partial):
 core=local['CORE'];red=local['RED'];peers={r['peer_uuid']:r for r in local['VX_peers']};far=local['VX_source_ports'][1];near=local['VX_source_ports'][0]
 endpoint_fails=[r for r in raw['new_track_endpoint_support'] if not r['passed']]
 core_ok=(len(endpoint_fails)==1 and endpoint_fails[0]['track_uuid']==CORE and core['track_record']['uuid']==CORE and core['via_record']['uuid']==CORE_VIA and core['actual_plated_barrel']['plated'] is True and 'In3.Cu' in core['actual_plated_barrel']['barrel_layers'] and core['drill_boundary_contact_length_mm']>0 and section(core['continuous_annulus_sections'],.4) and len(core['source_track_attachments'])==1 and section(core['source_track_attachments'][0]['continuous_sections'],.4))
 red_ok=(red['retained_track']['uuid']=='5080bbb8-ecda-5e64-af43-0365b1e0ab69' and set(red['support_UUIDs'])=={'dee086ad-0653-55a8-a0da-35d0f8e6dae7','2754fcb2-b9e9-5c3b-8023-61718c16e5e6'} and raw['RED_retained_join']['new_track_width_witness']['passed'] and red['via_plus_new_join_frozen_witness']['passed'] and red['via_plus_new_join_frozen_witness']['native_contiguous_covered_width_mm']>=.127-.00002 and section(red['via_plus_new_join_continuous_sections'],.127))
 contacts=(set(peers)==VX and all(r['lost_source_contact_mm2']<=1e-14 and r['source_contact_mm2']>0 and r['candidate_contact_mm2']>0 and r['local_same_net_union_source_minus_candidate_mm2']<=1e-14 for r in peers.values()))
 if set(peers)==VX:
  full=peers['2f68e32c-4199-4e40-bffa-04055f629681'];side=peers['bff99bb6-bcb9-43ee-97db-c5cf44f4a799'];joint=peers['dc033951-9af9-426d-84f7-e3be434c25d3'];wide=peers['916c3c9a-af23-4966-abb1-0f5d540569e7'];branch=peers['ca49f8ab-b5a6-4faf-9e5c-d77b66ae33bd']
  barrels=(all(r['actual_plated_barrel'] is True and 'In2.Cu' in r['physical_barrel_layers'] for r in [full,side,joint]) and full['candidate_annulus_uncovered_by_all_other_VX_mm2']==full['original_annulus_uncovered_by_all_other_VX_mm2']==0 and joint['candidate_annulus_uncovered_by_all_other_VX_mm2']==joint['original_annulus_uncovered_by_all_other_VX_mm2']==0 and side['candidate_annulus_uncovered_by_all_other_VX_mm2']==side['original_annulus_uncovered_by_all_other_VX_mm2'] and side['candidate_barrel_contact_boundary_length_mm']==side['source_barrel_contact_boundary_length_mm']>0)
  tracks=(section(wide['candidate_continuous_pairwise_sections'],1.2) and branch['source_pairwise_witness']['passed'] is False and branch['candidate_pairwise_witness']['passed'] is False and section(branch['source_all_VX_support_continuous_sections'],.8) and section(branch['all_VX_support_continuous_sections'],.8))
  ports=(near['point']==[25.3,9.] and section(near['candidate_drill_subtracted_polygon_section'],1.2) and far['point']==full['xy']==[28.,10.9] and far['inside_actual_drill'] is True and far['source_whole_VX_union_section']['best'] is None and far['candidate_whole_VX_union_section']['best'] is None and section(far['candidate_polygon_without_drill_subtraction_section'],1.2))
 else:barrels=tracks=ports=False
 preservation=(raw['native5_lost_pad_pair_count']==raw['native6_lost_pad_pair_count']==raw['native7_lost_pad_pair_count']==0 and raw['diagnostic_gates']['all_surviving_native5_object_fragments_preserved'] and raw['diagnostic_gates']['every_new_copper_fragment_reaches_real_pad'])
 other=all(v for key,v in raw['diagnostic_gates'].items() if key not in GATES|{'R34_to_actual_RX_IO1_improved_and_safe_partial_path'})
 return {'CORE_actual_full_width_annular_entry_and_barrel':bool(core_ok),'RED_actual_new_join_plus_via_full_width_support':bool(red_ok),'VX_all_five_original_contact_regions_preserved':contacts,'VX_actual_source_barrel_support_preserved':barrels,'VX_existing_track_full_width_union_support_preserved':tracks,'VX_drilled_terminal_and_external_port_geometry_accounted_for':ports,'all_baseline_pad_and_retained_fragment_relationships_preserved':preservation,'all_other_raw_physical_obligations_passed':other,'accepted_narrow_partial_RX_evidence_retained':partial['partial_RX_disposition']['partial_RX_progress_gate_passed']}

