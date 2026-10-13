#!/usr/bin/env python3
"""Read-only source/receipt reconciliation; no geometry, graph, mesh or solve."""
import gc
import gzip
import hashlib
import json
from pathlib import Path
import resource

ROOT=Path('historical/source-tree')
HERE=Path('historical/preparation')
PACKET=HERE/'bound-adapter'
OLD=ROOT/'power-tx-core-diagnostic-v1'
CANDIDATE=Path('historical/native-v5')

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for c in iter(lambda:f.read(1048576),b''):h.update(c)
    return h.hexdigest()

def read(p):return json.loads(Path(p).read_bytes())
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def row(p):return {'path':str(p),'sha256':sha(p)}
def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')

def main():
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    selected=read(HERE/'source-selection.json'); source=selected['source']
    historical=read(OLD/'source-selection.json')
    old_raw=gzip.decompress(Path(historical['native']['path']).read_bytes())
    assert hashlib.sha256(old_raw).hexdigest()==historical['native']['sha256']
    old=json.loads(old_raw);del old_raw
    old_records={o['uuid']:digest(o) for o in old['objects']}
    old_holes={o['uuid']:digest(o) for o in old['objects'] if o.get('drill')}
    old_zones={z['uuid']:digest(z) for z in old['zones']}
    del old;gc.collect()
    raw=gzip.decompress(Path(source['native']['path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==source['native']['sha256']
    native=json.loads(raw);del raw
    assert native['board_sha256']==source['board']['sha256'] and native['source_unchanged']
    records={o['uuid']:digest(o) for o in native['objects']}
    holes={o['uuid']:digest(o) for o in native['objects'] if o.get('drill')}
    delta=read('historical/locator-b05349f5a8ee242c/candidate-delta.json')
    added={o['uuid'] for o in delta['add_tracks']}
    assert set(records)-set(old_records)==added and not set(old_records)-set(records)
    assert all(records[k]==v for k,v in old_records.items())
    assert holes==old_holes and len(holes)==328
    selection_result=read(source['diagnostic_result']['path'])
    for name in ['structural-edit-ledger.json','paired-native-proof.json','physical-audit.json']:
        assert sha(CANDIDATE/name)==selection_result['files'][name]
    structural=read(source['structural_edit_ledger']['path'])
    assert structural['ordinary_refill_reopen_exact'] and sha(source['refill_reopen']['path'])==source['board']['sha256']
    assert structural['raw_source']['board_stackup_netlist_settings_unchanged']
    actual_zones={z['uuid']:z for z in native['zones']}
    for z in structural['zone_fill_ledger']:
        assert digest(actual_zones[z['zone_uuid']]['filled'][z['layer']])==z['candidate_fill_sha256']
    scope=read(PACKET/'preparation/scope.json'); metadata=read(PACKET/'native-primitive-parameters.json')
    assert metadata['scope_sha256']==sha(PACKET/'preparation/scope.json')
    assert metadata['board_sha256']==source['board']['sha256'] and metadata['native_sha256']==source['native']['sha256']
    assert metadata['pads']==read(OLD/'native-primitive-parameters.json')['pads']
    assert len(metadata['pads'])==268 and len(scope['required_return_uuids'])==44
    physical=read(CANDIDATE/'physical-audit.json')
    assert physical['candidate_board_sha256']==source['board']['sha256'] and physical['candidate_native_sha256']==source['native']['sha256']
    assert len(physical['new_candidate_gates'])==19 and all(v is True for v in physical['new_candidate_gates'].values())
    support=read(PACKET/'support.json'); engine=support['engine_report']
    assert support['board_sha256']==source['board']['sha256'] and support['native_sha256']==source['native']['sha256']
    assert engine['passed'] and all(v is True for v in engine['gates'].values())
    assert engine['physical_holes_included']==328 and engine['all_holes_remove_copper_irrespective_of_net']
    assert set(engine['nets'])==set(scope['pad_inventory']) and len(engine['nets'])==15
    for net,pads in scope['pad_inventory'].items():
        value=engine['nets'][net]
        assert value['complete'] and value['pad_group_count']==1 and len(value['groups'])==1
        assert value['groups'][0]['pad_identity']==pads
    assert set(engine['required_returns'])==set(scope['required_return_uuids'])
    for uid,value in engine['required_returns'].items():
        assert value['component_count']==1 and value['reaches_saved_planes'] and value['saved_plane_witnesses']
        for witness in value['saved_plane_witnesses']:
            z=actual_zones[witness['uuid']]
            assert z['net']=='GND' and not z['rule'] and z['filled'][witness['layer']]
    settings=read(ROOT/'power-recovery-prep/prepared-native7-v4-disabled/compiler-settings.disabled.json')
    old_review=read(OLD/'physical-review-v1/physical-assumptions.json')
    assert old_review['passed'] and old_review['material']==settings['material']
    report={'schema':'f722-in4-current-dc-input-reconciliation/v1','passed':True,
      'board_sha256':source['board']['sha256'],'native_sha256':source['native']['sha256'],
      'all2470_original_records_exact':len(old_records)==2470,'exactly10_additive_RX_records':len(added)==10,
      'all328_drill_owner_records_and_actual_spans_exact':True,'all268_current_primitive_pad_metadata_exact':True,
      'all15_current_networks_complete':True,'all44_returns_reach_current_saved_planes':True,
      'fresh_fill_hashes_match_structural_receipt':True,'all19_native_physical_gates_pass':True,
      'model_material_and_barrel_assumptions_unchanged':True,
      'review_scope':'Exact current source and fresh support receipt reconciliation. Prior numerical results are not transferred.',
      'geometry_graph_mesh_solver_executed_by_this_checker':False,
      'reference_AC_thermal_flight_manufacturing_qualified':False,
      'checker':row(Path(__file__)),'support':row(PACKET/'support.json'),
      'native_physical_review':row(CANDIDATE/'physical-audit.json'),
      'source3_assumption_scope':row(OLD/'physical-review-v1/physical-assumptions.json')}
    save(PACKET/'current-dc-input-reconciliation.json',report)
    evidence=[PACKET/'current-dc-input-reconciliation.json',PACKET/'support.json',PACKET/'native-primitive-parameters.json',
      PACKET/'preparation/terminal-audit.json',CANDIDATE/'structural-edit-ledger.json',CANDIDATE/'physical-audit.json',
      OLD/'physical-review-v1/physical-assumptions.json',PACKET/'preparation-checks-evidence.json',Path(__file__)]
    assumptions={'schema':'f722-intermediate-dc-physical-review/v1','passed':True,
      'board_sha256':source['board']['sha256'],'native_sha256':source['native']['sha256'],
      'checks':dict.fromkeys(['saved_fill_matches_source','modeled_conductor_dimensions','all_physical_drill_voids',
        'modeled_terminal_geometry','modeled_copper_and_barrel_assumptions'],True),
      'material':settings['material'],'evidence':[row(q) for q in evidence],
      'scope':'Current-source DC computational geometry/assumptions reconciliation only',
      'source3_dimensions_method':'Every original native record, including all modeled copper/barrels/drills, exactly matches source3; fresh exact primitive metadata and current fill/support are independently bound.',
      'limitations':old_review.get('review_notes',[]),
      'final_source':False,'electrical_acceptance_claimed':False,'manufacturing_release':False,'numerical_execution_authorized':False}
    save(PACKET/'physical-assumptions.json',assumptions)
    print(json.dumps({'reconciliation':row(PACKET/'current-dc-input-reconciliation.json'),'physical_assumptions':row(PACKET/'physical-assumptions.json')}))

if __name__=='__main__':main()
