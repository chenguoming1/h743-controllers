"""Seal the completed source17 SERVO1 transaction after required native gates."""
import pathlib,json,hashlib,shutil
H=pathlib.Path(__file__).resolve().parent;R=H.parents[2];D=H/'candidate04';S=R/'ordinary-routing/tests/sbus-nrst49/candidate02'
read=lambda p:json.loads(pathlib.Path(p).read_text());sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();write=lambda p,v:pathlib.Path(p).write_text(json.dumps(v,indent=2)+'\n')
h=sha(D/'f722-heli.kicad_pcb');old=sha(S/'f722-heli.kicad_pcb');s=read(D/'owner-summary.json')
assert h=='755545e8198e9a3649c0e07533c23e67010d91ab6a8b09556d7463e064ac89eb' and old=='71d33748909bb960c5829973642272460607d8521831a6212975f7de6790d660'
assert h==s['board_sha256'] and s['drc']==s['drc-all']==dict(unconnected=15,errors=0,warnings=0)
for k in ['process','mechanical','parity','firmware']:assert s[k]['passed'] and s[k]['board_sha256']==h
assert not read(D/'owner-drc-parity.json')['schematic_parity'];assert not s['critical']['faults'] and s['critical']['connected_nets']==16
assert not any(sh.get('violations') for sh in read(D/'owner-erc.json').get('sheets',[]))
for name in ['entry-support-audit.json','power-audit.json','native-coordinated-integration.json','stock-spi-binding.json','conditional-support-review/native-binding.json']:
 q=read(D/name);assert q['passed'] and q['board_sha256']==h
cut=read(D/'protection-actual-io.json');base=read(S/'protection-actual-io.json');assert cut['passed']==19 and cut['total']==22
passed=lambda d:{r['id'] for r in d['checks'] if r['complete_clamp_first_path_passes']}
assert passed(base)<passed(cut) and passed(cut)-passed(base)=={'published-02'}
comp=read(D/'reference-comparison17.json');assert comp['critical_object_geometry_identical']
assert all(v==0 for n,row in comp['net_numeric_deltas_after_minus_before'].items() for k,v in row.items() if (n,k)!=('USB_N','physical_GND_trace_width_missing_mm2'))
assert comp['net_numeric_deltas_after_minus_before']['USB_N']['physical_GND_trace_width_missing_mm2']==2.6376462125554667e-10
c=read(H/'reference-classification-servo1-17.json');assert c['source_binding_verified'] and c['before_board_sha256']==old and c['after_board_sha256']==h and c['missing_centerline_geometries_exactly_equal'] and c['exact_containment_predicate_disagreement_count']==0
assert c['all_changed_critical_projection_residuals_outside_unchanged_own_windows_empty'] and c['all_changed_critical_projection_residuals_outside_actual_hole_window_intersections_empty']
reg=D/'reference-region-review';reg.mkdir(exist_ok=True)
for name in ['reference-classification-servo1-17.json','reference-classification-servo1-17.log','classify_reference_delta.py']:shutil.copy2(H/name,reg/name)
for name in ['construct_servo1_complete17.py','audit_servo1_complete17.py','extra_servo1_gates17.py','finish_servo1_review17.py','export_servo1_reference.py','check_servo1_reference.py','seal_servo1_complete17.py','validate_servo1_complete17.py','ser1_complete17_geometry.py']:
 shutil.copy2(H/name,D/(pathlib.Path(name).stem+'.used.py'))
shutil.copy2(H/'servo1-complete-geometry17.json',D/'proposal-geometry-screen.json')
shutil.copy2(H/'finish-servo1-review17.log',D/'conditional-support-review/native-binding.log')
prov=read(D/'construction-provenance.json');audit=read(D/'entry-support-audit.json');geo=read(D/'signal-geometry-details.json');ev=read(D/'conditional-signal-review/electrical-evidence.json')
assert prov['source_board_sha256']==old and prov['board_sha256']==h and prov['all_other_155_footprints_exact']
assert len(prov['removed_source_records'])==38 and len(prov['added_records'])==74
assert len(audit['endpoint_inventory'])==136 and audit['new_tracks']==68 and audit['new_vias']==6 and len(audit['nets'])==28 and len(audit['signal_groups'])==20
assert all(audit['gates'].values()) and all(n['rejected'] for n in audit['negative_controls'])
assert geo['board_sha256']==h and len(geo['via_process_margins'])==6 and len(geo['SERVO1_outside_window_width_fragments'])==4
assert ev['board_sha256']==h and ev['assessment']['geometry_checkpoint_recommended_conditionally'] and not ev['assessment']['electrical_release_qualified']
inputs=read(D/'project-input-preservation.json');assert inputs['all_listed_non_board_project_inputs_byte_identical']
for r in inputs['files']:assert sha(D/r['path'])==r['sha256']==sha(S/r['path'])
allowed=['SERVO1_MCU','SERVO2_MCU','ESC_MCU','RPM_LV','GND','VX_RAW','EFUSE_EN']
write(D/'coordinated-change-receipt.json',dict(schema='f722-SERVO1-complete-native-reconstruction/v1',source_board_sha256=old,board_sha256=h,changed_nets=allowed,removed_source_objects=prov['removed_source_records'],added_objects=prov['added_records'],changed_pad_records=prov['changed_pad_records'],changed_footprint_records=prov['changed_footprint_records'],all_other_155_full_footprints_exact=True,all28_support_groups_restored=True,ADC_BUS_ADC_DIV_MID_CORE_HSE_objects_exact=True,both_original_Y1_ground_paths_exact=True,all_completed_signal_groups_preserved=True,raw_constructor_native_gates_pending_flag_superseded_by_sealed_receipts=True,conditional_signal_review='conditional-signal-review/SERVO1-electrical-review.md',conditional_support_review='conditional-support-review/NATIVE-SUPPORT-REVIEW.md',numerical_power_VCAP_applicable=False,signal_quality_qualified=False,owner_adoption_claimed=False))
(D/'README.md').write_text('''# Complete SERVO1 native candidate04

The exact source17 reconstruction closes R20.2–U12.1–U1.56 and reduces17 opens to15, with zero native errors/warnings. Board SHA-256: `755545e8198e9a3649c0e07533c23e67010d91ab6a8b09556d7463e064ac89eb`.

All136 new track endpoints and six ordinary tented0.45/0.20 mm vias pass finite native entry checks. All28 support partitions,20 completed signal groups,16 critical nets, strict schematic parity, ERC, firmware, native process and declared pose gates pass. Actual I/O cuts pass19/22, adding SERVO1 with0.143294148 mm gap and preserving every prior pass. R50 shifts only +0.25 mm inward;155 other full footprints, both original crystal grounds, ADC and CORE geometry remain exact.

The protected SERVO1 copper totals44.120258 mm; the drawn MCU-to-clamp branch is18.058336 mm with two vias. Four exact outside-window reference width fragments total0.000134787127 mm²; centerline outside own windows is zero. The raw USB_N width delta is retained and classified entirely within unchanged own-via windows. Full source-bound evidence is in signal-geometry-details.json and reference-region-review.

Read conditional-signal-review/SERVO1-electrical-review.md and conditional-support-review/NATIVE-SUPPORT-REVIEW.md. U12 shares a1.681160 mm/0.25 mm lead and existing via with eFuse control returns. ESD coupling, waveform, AC return and fresh loaded-power/VCAP qualification remain open. This is a geometric prototype checkpoint pending independent owner adoption, not electrical release. Earlier failed/incomplete routing and support alternatives remain preserved outside this sealed directory.
''')
handoff=dict(schema='f722-native-route-handoff/v1',status='sealed_native_15_open_complete_SERVO1_geometric_prototype_pending_owner_review',board_sha256=h,integration_source_sha256=old,drc=dict(unconnected=15,errors=0,warnings=0,strict_schematic_parity=0,ERC_violations=0),pose_reference=str((D/'poses-native.json').relative_to(R)),declared_footprint_transforms='declared-footprint-transforms.json',coordinated=True,allowed_changed_nets=allowed,all_other_155_full_footprints_exact=True,only_R50_translated_inward_0p25mm=True,removed_source_objects=38,added_native_objects=74,new_tracks=68,new_signal_vias=6,completed_net='SERVO1_MCU',restored_complete_nets=['SERVO2_MCU','ESC_MCU','RPM_LV','GND','VX_RAW','EFUSE_EN'],entry_support_audit='entry-support-audit.json',finite_new_endpoints=136,support_groups_preserved=28,actual_IO_cuts_passed=19,actual_IO_contracts=22,added_actual_IO_pass='published-02',raw_critical_object_geometry_identical=True,critical_reference_deltas_exactly_zero=False,USB_N_raw_trace_width_missing_delta_mm2=2.6376462125554667e-10,reference_window_classification='reference-region-review/reference-classification-servo1-17.json',missing_centerline_geometries_exactly_equal=True,actual_hole_predicate_disagreements=0,SERVO1_reference='servo1-reference/critical-reference.json',SERVO1_reference_residuals='signal-geometry-details.json',SERVO1_total_track_length_mm=44.12025835529574,SERVO1_MCU_to_clamp_drawn_inventory_mm=18.05833636472116,conditional_signal_review='conditional-signal-review/SERVO1-electrical-review.md',conditional_support_review='conditional-support-review/NATIVE-SUPPORT-REVIEW.md',stock_GPIO_speed='LOW_OSPEEDR00',conditional_model_evidence_only=True,signal_quality_qualified=False,protection_transient_qualified=False,reference_AC_qualified=False,both_original_Y1_returns_exact=True,ADC_BUS_ADC_DIV_MID_CORE_objects_exact=True,I2C_electrical_status='NOT_QUALIFIED',numerical_power_VCAP_applicable=False,owner_adoption_pending=True,direct_engine_output=False,fresh_router_zero_replay_performed=False)
handoff['files']={str(q.relative_to(D)):sha(q) for q in sorted(D.rglob('*')) if q.is_file() and q.name!='route-handoff.json'};write(D/'route-handoff.json',handoff)
assert all(sha(D/p)==v for p,v in handoff['files'].items()) and sha(D/'f722-heli.kicad_pcb')==h
print(json.dumps(dict(board_sha256=h,handoff_sha256=sha(D/'route-handoff.json'),files=len(handoff['files']),remaining=15,status=handoff['status'])))
