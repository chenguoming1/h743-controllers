#!/usr/bin/env python3
"""Review fresh native1 support against exact sources; never computes geometry."""
import gzip,hashlib,json,resource
from pathlib import Path

P=Path(__file__).resolve().parent
H=P.parent
C=Path('historical/native1')
A=Path('historical/locator-860439a62c3b97f3/bound-adapter')
R=Path('historical/source-tree')
SUPPLEMENT=R/'recovery-negotiated-routing-20261011/native1-MOSI-BARO-contact-supplement-v1/DISPOSITION.json'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def row(p):return {'path':str(p),'sha256':sha(p)}
def save(n,x):
    with (P/n).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
selection=read(H/'source-selection.json');source=selection['source']
for record in selection['required_receipts'].values():assert sha(record['path'])==record['sha256']
assert sha(P/'source-identity-evidence.json')==sha(H/'SOURCE-IDENTITY-REVIEW.json')
identity=read(P/'source-identity-evidence.json')
assert identity['passed'] and identity['all_modeled_native_object_records_exact'] and identity['all558_pad_records_exact']
assert identity['current_actual_drilled_object_count']==330 and identity['new_drilled_objects_exactly_match_two_declared_vias']
assert identity['board_sha256']==source['board']['sha256'] and identity['native_logical_sha256']==source['native']['sha256']
with gzip.open(source['native']['path'],'rb') as f:raw=f.read(50*1024**2)
assert hashlib.sha256(raw).hexdigest()==source['native']['sha256']
native=json.loads(raw);del raw
assert len([o for o in native['objects'] if o.get('drill')])==330
scope=read(P/'preparation/scope.json');metadata=read(P/'native-primitive-parameters.json')
assert metadata['scope_sha256']==sha(P/'preparation/scope.json')
assert metadata['board_sha256']==source['board']['sha256'] and metadata['native_sha256']==source['native']['sha256']
assert metadata['pads']==read(A/'native-primitive-parameters.json')['pads']
assert len(metadata['pads'])==268 and len(scope['required_return_uuids'])==44
physical=read(C/'physical-audit.json');supplement=read(SUPPLEMENT)
failed={k:v for k,v in physical['new_candidate_gates'].items() if v is not True}
assert failed=={'inherited_scoped_contact_disposition_still_exact':False}
assert supplement['candidate_board_sha256']==source['board']['sha256']
assert supplement['candidate_native_logical_sha256']==source['native']['sha256']
assert supplement['raw_audit_sha256']==sha(C/'physical-audit.json')
assert supplement['fresh_exact_disposition_passed'] and supplement['raw_inherited_applicability_gate'] is False
assert supplement['general_predicate_relaxed'] is False and supplement['source_DC_transferred'] is False
support=read(P/'support.json');engine=support['engine_report']
assert support['board_sha256']==source['board']['sha256'] and support['native_sha256']==source['native']['sha256']
assert engine['passed'] and all(v is True for v in engine['gates'].values())
assert engine['physical_holes_included']==330 and engine['all_holes_remove_copper_irrespective_of_net']
assert set(engine['nets'])==set(scope['pad_inventory']) and len(engine['nets'])==15
for net,pads in scope['pad_inventory'].items():
    value=engine['nets'][net]
    assert value['complete'] and value['pad_group_count']==1 and len(value['groups'])==1
    assert value['groups'][0]['pad_identity']==pads
assert set(engine['required_returns'])==set(scope['required_return_uuids'])
zones={z['uuid']:z for z in native['zones']}
for uid,value in engine['required_returns'].items():
    assert value['component_count']==1 and value['reaches_saved_planes'] and value['saved_plane_witnesses']
    for witness in value['saved_plane_witnesses']:
        zone=zones[witness['uuid']]
        assert zone['net']=='GND' and not zone['rule'] and zone['filled'][witness['layer']]
settings=read(R/'power-recovery-prep/prepared-native7-v4-disabled/compiler-settings.disabled.json')
save('current-dc-input-reconciliation.json',{
 'schema':'f722-native1-current-dc-input-reconciliation/v1','passed':True,
 'board_sha256':source['board']['sha256'],'native_sha256':source['native']['sha256'],
 'exact_declared_edit_and_source_identity_review':row(H/'SOURCE-IDENTITY-REVIEW.json'),
 'actual_drill_count':330,'all_original328_drills_preserved':True,'two_added_drilled_vias_bound':True,
 'all268_current_primitive_pad_metadata_exact':True,'all15_current_networks_complete':True,
 'all44_returns_reach_current_saved_planes':True,'raw_false_native_gate_preserved':failed,
 'scoped_contact_window_supplement':row(SUPPLEMENT),'no_general_gate_relaxed':True,
 'model_material_and_barrel_assumptions_unchanged':True,'support':row(P/'support.json'),
 'native_physical_review':row(C/'physical-audit.json'),'checker':row(Path(__file__)),
 'geometry_graph_mesh_solver_executed_by_this_checker':False,'historical_DC_transferred':False,
 'reference_AC_thermal_flight_manufacturing_qualified':False})
evidence=[P/'current-dc-input-reconciliation.json',P/'source-identity-evidence.json',P/'support.json',
 P/'native-primitive-parameters.json',P/'preparation/terminal-audit.json',C/'structural-edit-ledger.json',
 C/'physical-audit.json',SUPPLEMENT,Path(__file__)]
save('physical-assumptions.json',{
 'schema':'f722-intermediate-dc-physical-review/v1','passed':True,
 'board_sha256':source['board']['sha256'],'native_sha256':source['native']['sha256'],
 'checks':dict.fromkeys(['saved_fill_matches_source','modeled_conductor_dimensions','all_physical_drill_voids',
     'modeled_terminal_geometry','modeled_copper_and_barrel_assumptions'],True),
 'material':settings['material'],'evidence':[row(p) for p in evidence],
 'scope':'Current native1 computational DC physical assumptions only',
 'limitations':[
   'All current power conductor, terminal and original drill records match accepted source2. Exact signal-only25-track/two-via/one-cut edits are separately bound.',
   'The actual330 physical holes, including both new through vias, remove copper on every physically spanned layer irrespective of net. Current saved fill is used.',
   'Fresh268-pad metadata,15-network conservative support and44 actual return-to-plane witnesses are current-source evidence.107 finite contacts require the separate compile audit.',
   'The inherited scoped contact-applicability flag remains false. Its exact candidate-specific VX window supplement is bound separately; no general predicate is relaxed.',
   '105C,0.015mm copper and plating,95%IACS and source-stackup barrel spans are unchanged conditional assumptions, not thermal or manufacturing guarantees.',
   'All305 cases, both grids and fiveVCAP loops remain required; historical required passes and the18.560916291A failed illustration are not transferred.',
   'Ideal lands, annuli and package distribution remain model assumptions; AC, startup, thermal, flight and final board qualification are outside this review.'],
 'final_source':False,'electrical_acceptance_claimed':False,'manufacturing_release':False,'numerical_execution_authorized':False})
print(json.dumps({'reconciliation':row(P/'current-dc-input-reconciliation.json'),'physical_assumptions':row(P/'physical-assumptions.json')}))
