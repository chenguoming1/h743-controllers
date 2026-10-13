#!/usr/bin/env python3
"""Review native0 drilled support and declared U15 static support; no geometry work."""
import gzip,hashlib,json,resource
from pathlib import Path
P=Path(__file__).resolve().parent;H=P.parent
C=Path('historical/native0')
A=Path('historical/locator-6d0a0b8843614fb6/bound-adapter')
R=Path('historical/source-tree')
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def row(p):return {'path':str(p),'sha256':sha(p)}
def save(n,x):
 with (P/n).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
selection=read(H/'source-selection.json');source=selection['source']
for record in selection['required_receipts'].values():assert sha(record['path'])==record['sha256']
assert sha(P/'source-identity-evidence.json')==sha(H/'SOURCE-IDENTITY-REVIEW.json')
id=read(P/'source-identity-evidence.json')
assert id['passed'] and id['all_undeclared_native_records_exact'] and id['all_558_pad_identity_net_tuples_exact']
assert id['all107_finite_contact_definitions_and_actual_terminal_records_unchanged']
assert id['current_actual_drilled_object_count']==331 and id['all329_retained_drilled_records_exact']
assert len(id['declared_added_drill_UUIDs'])==2 and len(id['declared_removed_drill_UUIDs'])==1
assert id['board_sha256']==source['board']['sha256'] and id['native_logical_sha256']==source['native']['sha256']
with gzip.open(source['native']['path'],'rb') as f:raw=f.read(50*1024**2)
assert hashlib.sha256(raw).hexdigest()==source['native']['sha256'];native=json.loads(raw);del raw
assert len([o for o in native['objects'] if o.get('drill')])==331
scope=read(P/'preparation/scope.json');metadata=read(P/'native-primitive-parameters.json');old=read(A/'native-primitive-parameters.json')
assert metadata['scope_sha256']==sha(P/'preparation/scope.json') and metadata['board_sha256']==source['board']['sha256'] and metadata['native_sha256']==source['native']['sha256']
assert metadata['original_pad_inner_outer_contours_exactly_reproduced'] and metadata['raw_custom_source_geometry_exactly_reproduced']
assert set(metadata['pads'])==set(old['pads']) and len(metadata['pads'])==268 and len(scope['required_return_uuids'])==44
changed={u for u in metadata['pads'] if metadata['pads'][u]!=old['pads'][u]};assert changed==set(id['declared_changed_power_pad_UUIDs'])
objects={o['uuid']:o for o in native['objects']}
for u in changed:
 m=metadata['pads'][u];o=objects[u];b=old['pads'][u]
 assert m['key'] in ('U15.3','U15.8') and m['key']==o['key'] and m['net']==o['net']=='GND'
 assert m['position_IU']==[round(x*1000000) for x in o['xy']] and m['absolute_angle_degrees']%360==o['angle']%360==90
 assert set(m['layers'])==set(o['copper'])=={'B.Cu'} and m['footprint_uuid']==o['footprint_uuid']==b['footprint_uuid']
 layer=m['layers']['B.Cu'];prior=b['layers']['B.Cu'];assert layer['original_inner_and_outer_contours_reproduced'] and layer['custom']['exact_source_primitive_equality']
 assert layer['size_IU']==prior['size_IU'] and layer['offset_IU']==prior['offset_IU']
 assert [x['raw_PCB_source_pad_local_IU'] for x in layer['custom']['raw_primitives']]==[x['raw_PCB_source_pad_local_IU'] for x in prior['custom']['raw_primitives']]
physical=read(C/'physical-audit.json');assert physical['candidate_board_sha256']==source['board']['sha256'] and physical['candidate_native_sha256']==source['native']['sha256']
assert physical['all_22_full_protection_passed'] and physical['all_required_new_checks_passed']
assert all(v is True for v in physical['new_candidate_gates'].values())
support=read(P/'support.json');engine=support['engine_report']
assert support['board_sha256']==source['board']['sha256'] and support['native_sha256']==source['native']['sha256']
assert engine['passed'] and all(v is True for v in engine['gates'].values())
assert engine['physical_holes_included']==331 and engine['all_holes_remove_copper_irrespective_of_net']
assert set(engine['nets'])==set(scope['pad_inventory']) and len(engine['nets'])==15
for net,pads in scope['pad_inventory'].items():
 value=engine['nets'][net];assert value['complete'] and value['pad_group_count']==1 and len(value['groups'])==1 and value['groups'][0]['pad_identity']==pads
assert set(engine['required_returns'])==set(scope['required_return_uuids']);zones={z['uuid']:z for z in native['zones']}
for uid,value in engine['required_returns'].items():
 assert value['component_count']==1 and value['reaches_saved_planes'] and value['saved_plane_witnesses']
 for w in value['saved_plane_witnesses']:
  z=zones[w['uuid']];assert z['net']=='GND' and not z['rule'] and z['filled'][w['layer']]
settings=read(R/'power-recovery-prep/prepared-native7-v4-disabled/compiler-settings.disabled.json')
save('current-dc-input-reconciliation.json',{'schema':'f722-clean-native0-current-dc-input-reconciliation/v1','passed':True,'board_sha256':source['board']['sha256'],'native_sha256':source['native']['sha256'],'exact_declared_edit_and_source_identity_review':row(H/'SOURCE-IDENTITY-REVIEW.json'),'actual_drill_count':331,'all329_retained_drills_preserved':True,'two_added_and_one_removed_drill_bound':True,'all266_unmoved_primitive_pad_metadata_exact':True,'both_declared_U15_GND_pad_metadata_current_and_local_primitives_exact':sorted(changed),'U15_static_GND_support_in_current_all_pad_group':True,'U15_injected_load_or_transient_ESD_test_claimed':False,'all15_current_networks_complete':True,'all44_returns_reach_current_saved_planes':True,'native22_physical_gates_pass':True,'no_general_gate_relaxed':True,'model_material_and_barrel_assumptions_unchanged':True,'support':row(P/'support.json'),'native_physical_review':row(C/'physical-audit.json'),'checker':row(Path(__file__)),'geometry_graph_mesh_solver_executed_by_this_checker':False,'historical_DC_transferred':False,'reference_AC_thermal_flight_manufacturing_qualified':False})
evidence=[P/'current-dc-input-reconciliation.json',P/'source-identity-evidence.json',P/'support.json',P/'native-primitive-parameters.json',P/'preparation/terminal-audit.json',C/'structural-edit-ledger.json',C/'physical-audit.json',Path(__file__)]
save('physical-assumptions.json',{'schema':'f722-intermediate-dc-physical-review/v1','passed':True,'board_sha256':source['board']['sha256'],'native_sha256':source['native']['sha256'],'checks':dict.fromkeys(['saved_fill_matches_source','modeled_conductor_dimensions','all_physical_drill_voids','modeled_terminal_geometry','modeled_copper_and_barrel_assumptions'],True),'material':settings['material'],'evidence':[row(p) for p in evidence],'scope':'Current clean native0 computational DC physical assumptions only','limitations':['Declared U15.3/U15.8 pose and one-ground-track-to-three replacement are rebound; all107 injected-terminal records remain exact. U15 static support is not injected-load or transient-ESD validation.','All331 current physical holes remove copper on physically spanned layers irrespective of net. Fresh saved fill is used.','Fresh268-pad metadata,15-network conservative support and44 actual return-to-plane witnesses are current-source evidence.107 finite contacts require separate compile audit.','Prior native warnings and raw source equality failures remain historical; exact declared edits own their disposition, not model repairs.','105C,0.015mm copper and plating,95%IACS and source-stackup barrel spans are unchanged conditional assumptions, not thermal or manufacturing guarantees.','All294required+11illustrations,bothgrids,fiveVCAPloops andnumericalguards remain unchanged; native1passes and18.560994Afailedillustration do not transfer.','Required cases contain no servo loading. Every servo case remains an illustration; actual ESCversion/harness/contacts/thermal/timing remain separate suitability conditions.','Ideal lands,annuli andpackage distribution remain modelassumptions; AC,startup,thermal,flight andfinalboardqualification remain outside thisreview.'],'final_source':False,'electrical_acceptance_claimed':False,'manufacturing_release':False,'numerical_execution_authorized':False})
print(json.dumps({'reconciliation':row(P/'current-dc-input-reconciliation.json'),'physical_assumptions':row(P/'physical-assumptions.json')}))
