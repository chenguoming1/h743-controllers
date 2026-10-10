"""Bind completed candidate41 native evidence; does not adopt the board."""
from pathlib import Path
import hashlib
import json
import shutil

R = Path(__file__).resolve().parent
D, S, A = R/'candidate41', R/'candidate39', R/'dsm41-audits'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
def write(name, value):
    (D/name).write_text(json.dumps(value, indent=2)+'\n')

assert not (D/'route-handoff.json').exists(), 'A sealed handoff must not be overwritten'
h, source = sha(D/'f722-heli.kicad_pcb'), sha(S/'f722-heli.kicad_pcb')
assert h == '539d9547eb8c4d5984481293ae10cee34355ee838dff11ab43b00cca270ceae2'
assert source == '246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7'
assert sha(A/'candidate41-entry-return.json') == '90dcd3d6df49d122822a5a6db2b248e0669240bc284a6bae22bb5fa02886a73f'
assert sha(A/'coordinated-change-receipt.json') == '94262b7c3dc0469159be413e7518387fc65d5a0425a724e3b8af415fcf40cc95'
a = read(A/'candidate41-entry-return.json')
t = read(A/'coordinated-change-receipt.json')
assert a['passed'] and all(a['gates'].values()) and len(a['negative_controls']) == 28
assert a['candidate_board_sha256'] == t['board_sha256'] == h
assert a['source_board_sha256'] == t['source_board_sha256'] == source
assert t['candidate_map_sha256'] == sha(D/'f722-heli.logical-route-map.json')
assert t['actual_io_receipt_sha256'] == sha(D/'protection-actual-io.json')
assert read(D/'owner-summary.json')['drc'] == {'unconnected':41,'errors':0,'warnings':0}
ref = read(D/'reference-comparison-to39.json')
assert ref['critical_object_geometry_identical']
assert all(v == 0 for row in ref['net_numeric_deltas_after_minus_before'].values() for v in row.values())
for name in ['candidate41-entry-return.json','coordinated-change-receipt.json']:
    shutil.copy2(A/name, D/name)
(D/'audit-sources').mkdir()
for name in ['README.md','audit_dsm41_entries_return.py','input-hashes.json','check.log']:
    shutil.copy2(A/name, D/'audit-sources'/name)
for src, target in [
    (R/'candidate40/ISOLATED-REVIEW-STATUS.json','isolated40-refusal.json'),
    (R/'candidate40/owner-drc.json','isolated40-raw-drc.json'),
    (R/'candidate40/construction-provenance.json','isolated40-construction-provenance.json'),
    (R/'construct_dsm_complete40.py','construct_dsm_complete40.used.py'),
    (R/'tests/dsm-coordinated-return/proposal39.json','isolated40-proposal39.json'),
    (R.parent/'integrated-routing/declared-translations39-to41.json','declared-translations39-to41.json'),
]:
    shutil.copy2(src,D/target)
binding = {'board_sha256':h,'source_board_sha256':source,
           'audit':'candidate41-entry-return.json','audit_sha256':sha(D/'candidate41-entry-return.json')}
write('endpoint-audit.json', {
    'schema':'f722-complete-DSM-endpoint-audit-binding/v1','passed':True,**binding,
    'scope':'Finite full-width entries, explicit R26/R38 junction corridors and actual annular contacts; nominal native geometry only.',
    'new_track_endpoints_checked':len(a['new_endpoint_classification']),
    'direct_pad_entry_failures_preserved':a['direct_pad_entry_failures_preserved'],
    'separate_finite_corridors':{'R26':a['explicit_retained_R26_junction'],'R38':a['explicit_new_R38_junction']},
    'all_geometry_gates':a['gates'],'negative_control_count':28,
    'manufacturing_margin_claimed':False})
write('power-audit.json', {
    'schema':'f722-complete-DSM-support-audit-binding/v1','passed':True,**binding,
    'scope':'Copper-only support continuity and full-width local entries/returns. No numerical voltage-budget, thermal or transient pass.',
    'nets':a['support_nets'],'changed_CORE_feed':a['changed_CORE_feed'],
    'C70_retained_entries':a['C70_retained_entries'],'R70_ground_return':a['R70_ground_return'],
    'dedicated_D7_ground_return':a['dedicated_D7_ground_return'],
    'numerical_power_VCAP_applicable':False})
write('f722-heli.import.json', {
    'schema':'f722-explicit-coordinated-native-construction-receipt/v1','passed':True,
    'scope':'Exact native two-stage construction and direct accepted39-to41 transaction; adoption and fresh numerical qualification remain separate.',
    'source_sha256':source,'output_sha256':h,
    'construction_source_sha256':sha(R/'candidate40/f722-heli.kicad_pcb'),
    'construction_kind':'Complete actual-D7 protected branch and dedicated return; coordinated SBUS/RPM replacement, three passive translations and explicit CORE feed reconstruction.',
    'direct_engine_output':False,'engine_routing_succeeded':False,'engine_partial_geometry_adopted':False,
    'ses_engine_native_geometry_equal':False,'session_artifact':None,
    'coordinated_change_receipt':'coordinated-change-receipt.json',
    'coordinated_change_receipt_sha256':sha(D/'coordinated-change-receipt.json'),
    'construction_provenance':'construction-provenance.json',
    'construction_provenance_sha256':sha(D/'construction-provenance.json'),
    'logical_route_map_artifact':'f722-heli.logical-route-map.json',
    'logical_route_map_sha256':sha(D/'f722-heli.logical-route-map.json'),
    'undeclared_native_changes':0,'footprints_preserved':153,'declared_footprint_translations':3,
    'isolated40_accepted':False,'reference_plane_refill_performed':True,
    'fresh_model_zero_control_performed':False,'numerical_power_VCAP_applicable':False})
write('power-revalidation-required.json', {
    'board_sha256':h,'numerical_power_and_VCAP_applicability':False,
    'last_fully_bound_numerical_candidate':'candidate24',
    'last_fully_bound_numerical_receipt':'static-power-validation/candidate24-power-result-applicability.json',
    'last_fully_bound_numerical_receipt_sha256':'8373a599fe81a58571422fc4a1f4fe3afb65acad2fd7b3528eef43d575edce11',
    'reason':'Explicit CORE feed width/length revision, D7 ground-return relocation, three passive translations and saved GND refill require fresh source-bound power/VCAP review.',
    'geometric_support_continuity_passed':True,
    'CORE_strip_increment_estimate_only':{'width_before_mm':0.30,'width_after_mm':0.25,'length_after_mm':2.466979964180315,'delta_R_milliohm_approx':2.15975,'full_electronics_envelope_A':0.32,'delta_V_millivolt_approx':0.69112,'fresh_DC_solve':False},
    'transient_return_qualification_claimed':False})
shutil.copy2(__file__,D/'seal_candidate41.used.py')
files = {str(p.relative_to(D)):sha(p) for p in sorted(D.iterdir()) if p.is_file() and (p.suffix in {'.json','.py','.png'} or p.name=='f722-heli.kicad_pcb')}
for sub in ['audit-sources','reference-snapshot']:
    files.update({str(p.relative_to(D)):sha(p) for p in sorted((D/sub).rglob('*')) if p.is_file()})
write('route-handoff.json', {
    'schema':'f722-native-route-handoff/v1',
    'status':'frozen_native_verified_41_open_complete_actual_D7_branch_pending_owner_review',
    'board_sha256':h,'integration_source_sha256':source,
    'drc':{'unconnected':41,'errors':0,'warnings':0,'strict_schematic_parity':0},
    'pose_reference':'ordinary-routing/candidate41/poses-native.json',
    'declared_footprint_translations':['C70','R38','R70'],
    'footprints_preserved_exact':153,
    'construction_kind':'Explicit coordinated native construction through rejected isolated40, followed by courtyard-clear CORE/pose revision; complete direct39-to41 transaction verified.',
    'engine_insertion_succeeded':False,'engine_partial_geometry_adopted':False,
    'source_objects_removed':8,'source_objects_retained_exact':1843,'added_tracks':20,'added_vias':1,
    'changed_pad_records':6,'changed_footprint_records':3,
    'all_non_board_project_inputs_preserved':60,'reference_refill_performed':True,
    'full_width_endpoint_passed':True,'direct_pad_failures_preserved':2,'explicit_full_width_corridors':2,
    'geometry_gates_passed':14,'negative_controls_passed':28,
    'new_protected_channel':'DSM_RX_EXT actual D7.1 cut J12.3 to R38.1 passes; R38.2 MCU continuation remains open.',
    'actual_D7_outside_pad_gap_mm':0.14813676113645813,
    'historical_routing_pad_cuts':{'passed':7,'total':18},
    'supplemental_pad_cuts':{'passed':5,'total':7},
    'actual_bonded_io_cases':{'passed':11,'total':22},
    'actual_bonded_io_channels':{'passed':9,'total':20},
    'critical_reference_scope':{'critical_object_geometry_identical':True,'all_reported_numeric_deltas_exactly_zero':True,'ground_loss_mm2_each_plane':0.03141808071999991,'ground_gain_mm2_each_plane':0.03141808071999997,'new_critical_width_overlap_mm2':0.0,'receipt':'reference-comparison-to39.json'},
    'required_continuation_map':'f722-heli.logical-route-map.json',
    'fresh_model':None,'fresh_model_zero_native_and_logical_parity_passed':False,
    'fresh_model_zero_status':'Not run on41; native explicit construction is the provenance.',
    'power_scope':'Support connectivity and local widths pass. CORE .30-to-.25 mm reconstruction and changed return/pose/fills require fresh numerical power and VCAP review; no inherited numerical pass.',
    'clearance_scope':'Nominal geometry only. Tiny positive courtyard, edge, clearance and annular witness reserves are not manufacturing or transient qualification.',
    'files':files})
assert all(sha(D/p)==v for p,v in files.items())
print(json.dumps({'board_sha256':h,'handoff_sha256':sha(D/'route-handoff.json'),'files_verified':len(files),'pose_reference':str(D/'poses-native.json')}))
