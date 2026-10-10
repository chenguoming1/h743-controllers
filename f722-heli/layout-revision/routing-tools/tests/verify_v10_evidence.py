#!/usr/bin/env python3
"""Portable source/recovery/rejection checks; no PCB runtime, JVM or solve."""
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def run(args,ok=True):
    r=subprocess.run([str(x) for x in args],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True)
    assert (r.returncode==0)==ok,(args,r.stdout,r.stderr)
    return r

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base-project',type=Path,required=True);ap.add_argument('--historical-workspace',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    source=read(ROOT/'checks/v10-source-identity.json');expected=source['expected_boards'];projections=read(ROOT/'checks/v10-portable-projections.json')['files'];status=read(ROOT/'status.json')
    receipt=lambda n:read(ROOT/'checks'/n)
    original=lambda n:projections['checks/'+n]['historical_file_sha256']
    for name,info in projections.items():
        assert sha(ROOT/name)==info['portable_file_sha256'],name
        assert '/workspace/' not in (ROOT/name).read_text(),name
        if a.historical_workspace:assert sha(a.historical_workspace/info['historical_path'])==info['historical_file_sha256'],name
    for name,info in source['sources'].items():
        assert sha(ROOT/name)==info['sha256'],name
        if a.historical_workspace:assert sha(a.historical_workspace/info['historical_path'])==info['sha256'],name
    assert status['numerical_power_and_VCAP_applicability'] is False and status['last_fully_bound_numerical_candidate']==24 and status['numerical_power_stale_since_candidate']==26
    refusal=receipt('candidate29-route-refusal.json');assert refusal['status']=='not_accepted' and not refusal['endpoint_passed'] and refusal['native_warnings']==3
    assert receipt('candidate29-endpoint-audit.json')['passed'] is False
    for c,opens in [(30,53),(31,52),(32,50),(33,49)]:
        owner=receipt(f'candidate{c}-owner-summary.json');handoff=receipt(f'candidate{c}-route-handoff.json')
        assert owner['board_sha256']==expected[str(c)]==handoff['board_sha256']
        assert owner['drc']==owner['drc-all']==dict(unconnected=opens,errors=0,warnings=0)
        for gate in ['process','mechanical','parity','firmware']:assert owner[gate]['passed'] and owner[gate]['board_sha256']==expected[str(c)]
        assert owner['critical']['connected_nets']==owner['critical']['total_nets']==16 and not owner['critical']['faults']
        assert receipt(f'candidate{c}-endpoint-audit.json')['passed']
        if c<33 or status['candidate33_owner_adopted']:
            adopted=receipt(f'candidate{c}-owner-adoption.json')
            assert adopted['board_sha256']==expected[str(c)] and adopted['native_unfinished_connections']==opens and not adopted['numerical_applicability']
            bindings={'native_gate_receipt_sha256':'owner-summary.json','reference_comparison_sha256':'critical-reference-comparison.json','actual_io_receipt_sha256':'protection-actual-io.json'}
            if c<33:bindings['additive_receipt_sha256']='owner-additive-integration.json'
            else:bindings.update(integration_receipt_sha256='owner-coordinated-integration.json',reference_change_review_sha256='reference-change-review.json')
            for k,n in bindings.items():assert adopted[k]==original(f'candidate{c}-'+n),(c,k)
    for c in [31,33]:
        proof=receipt(f'candidate{c}-construction-provenance.json');assert not proof['actual_engine_inserted_success'] and not proof['direct_engine_session_output']
    lineage=receipt('candidate32-engine-lineage.json');assert lineage['engine_successes']==3 and lineage['net_reduction']==2 and not lineage['post_router_cleanup']
    for name,digest in lineage['engine_source_hashes'].items():assert sha(ROOT/name)==digest
    handoff=receipt('candidate33-route-handoff.json');assert handoff['ordinary_fully_connected_physical_nets']==17 and handoff['source_track_objects_removed']==6 and handoff['source_existing_uuid_records_edited']==0
    io=receipt('candidate33-protection-actual-io.json');passed=[x for x in io['checks'] if x['complete_clamp_first_path_passes']]
    assert len(io['checks'])==22 and len(passed)==8
    servo=[x for x in passed if x['net']=='SERVO2_MCU' and x['clamp']=='U12.3'];assert len(servo)==1
    assert abs(servo[0]['minimum_gap_measured_mm']-.132)<1e-12
    assert all(x['overlap_outside_actual_pad_mm2']==0 for x in servo[0]['layer_gaps'])
    reference=receipt('candidate33-reference-change-review.json')
    assert reference['passed'] and reference['critical_copper_identical'] and reference['all_missing_centerline_geometries_equal'] and reference['all_missing_width_geometry_outside_existing_own_via_windows_equal']
    assert reference['comparison_sha256']==original('candidate33-critical-reference-comparison.json')
    assert reference['script_sha256']==sha(ROOT/'tests/routing-checkpoint49/review_reference_window_change.py')
    numeric=reference['numeric_differences_retained'];assert numeric['IMU_MISO']['physical_GND_trace_width_missing_mm2']==6.17441728301138e-09 and numeric['USB_N']['physical_GND_trace_width_missing_mm2']==-6.838594690528055e-10
    assert all(x['entirely_inside_unchanged_own_via_windows_and_before_or_after_actual_holes'] for x in reference['changed_regions'])
    for c in [31,32,33]:
        zero=receipt(f'source{c}-zero-parity.json');imp=receipt(f'source{c}-imported-zero.import.json');fixed=receipt(f'source{c}-fixed-explicit-native-ids.json');contract=receipt(f'source{c}-fixed-preservation-contract.json')
        assert zero['passed'] and not zero['errors'] and zero['board_sha256']==expected[str(c)]
        assert imp['source_sha256']==imp['output_sha256']==expected[str(c)] and imp['routes_added']==imp['routes_removed']==0
        assert set(fixed).isdisjoint(contract['mutable_source_ids'])
    diag=ROOT/'tests/complete-path-diagnostics';promotion=read(diag/'promotion-identity.json');static=read(diag/'static-verification.json');outcome=read(diag/'located06-outcome.json')
    java='src/app/freerouting/autoroute/InsertFoundConnectionAlgo.java';baseline=(ROOT/java).read_text();overlay=(diag/'InsertFoundConnectionAlgo.java').read_text()
    assert sha(ROOT/java)==static['baseline_source_sha256'] and sha(diag/'InsertFoundConnectionAlgo.java')==static['staged_source_sha256']
    call='    new_instance.diagnosticLocatedConnection(p_connection);\n';start=overlay.index('  /** Snapshot only:');end=overlay.index('  /**\n   * Creates a new instance of InsertFoundConnectionAlgo',start);helpers=overlay[start:end]
    assert overlay.replace(helpers,'',1).replace(call,'',1)==baseline
    assert not re.search(r'(?:connection|trace|item|board|ctrl)\.[\w.\[\]]+\s*(?:=(?!=)|\+=|-=|\+\+|--)',helpers)
    assert len(promotion['changed_files'])==2 and not promotion['physical_or_routing_logic_changed'] and promotion['zero_import_byte_identical']
    assert outcome['successes']==outcome['new_complete_path_records']==0 and outcome['final_session_byte_identical_to_zero']
    runtime=read(diag/'runtime-verification.json');assert runtime['passed'] and runtime['no_native_success_claim'] and runtime['terminal_engine_attempt_result']=='ROUTED'
    assert runtime['source_board_sha256']==expected['33'] and runtime['preserved_record_excerpt_sha256']==sha(diag/'runtime-located-records.log') and runtime['diagnostic_source_sha256']==sha(diag/'InsertFoundConnectionAlgo.java')
    assert runtime['bounded_run_receipt_sha256']==projections['tests/complete-path-diagnostics/filtered07.bounded-run.json']['historical_file_sha256']
    routed=read(diag/'filtered07-count1-receipt.json');assert routed['attempt']['net']==runtime['net'] and routed['attempt']['result']=='ROUTED' and routed['board_sha256']==runtime['source_board_sha256'] and routed['model_sha256']==runtime['model_sha256']
    log=[json.loads(line.removeprefix('INSERT_DIAGNOSTIC ')) for line in (diag/'runtime-located-records.log').read_text().splitlines()]
    full=[x for x in log if x['stage']=='located_connection'];traces=[x for x in log if x['stage']=='located_trace'];assert len(full)==1 and len(traces)==3 and full[0]['status']=='located_only'
    connection=full[0];assert len(connection['via_transitions'])==2 and connection['target_endpoint']['native_uuid'] and connection['start_endpoint']['native_uuid']
    for x,y in zip(connection['traces'],traces):
        for key in ['layer','half_width_mm','requested_corners_mm']:assert x[key]==y[key]
    for v in connection['via_transitions']:
        i=v['before_trace_index'];assert v['point_mm']==connection['traces'][i]['requested_corners_mm'][0]==connection['traces'][i-1]['requested_corners_mm'][-1]
    adapters=receipt('source33-fixed-preservation-contract.json')['adapter_sources']
    assert [(n,d) for n,d in adapters.items() if sha(ROOT/n)!=d]==[(java,sha(diag/'InsertFoundConnectionAlgo.java'))]
    assert receipt('source33-fixed-preservation-contract.json')['historical_model_sha256']==receipt('source33-zero-parity.json')['model_sha256']=='1e26454313ed16a325e7925707dbdf88589dec8d9d9564f2a91f59bf4e51e051'
    negatives=[];recovered=[];packets=[]
    def reject(label,operation):
        try:operation()
        except (ValueError,KeyError,FileNotFoundError,AssertionError):negatives.append(label)
        else:raise AssertionError('Bad input accepted: '+label)
    recpath=ROOT/'sessions/recovery49/rebuild_historical_source.py';recovery=module('recovery49',recpath)
    with tempfile.TemporaryDirectory(prefix='v10-evidence-') as temp:
        tmp=Path(temp)
        overlay_copy=tmp/'overlay';shutil.copytree(ROOT/'src',overlay_copy/'src')
        run([sys.executable,'-B',ROOT/'tools/activate_diagnostics_overlay.py','--root',overlay_copy])
        assert sha(overlay_copy/java)==sha(diag/'InsertFoundConnectionAlgo.java')
        run([sys.executable,'-B',ROOT/'tools/activate_diagnostics_overlay.py','--root',overlay_copy,'--restore-baseline'])
        assert sha(overlay_copy/java)==sha(ROOT/java)
        (overlay_copy/java).write_bytes(b'unexpected baseline')
        run([sys.executable,'-B',ROOT/'tools/activate_diagnostics_overlay.py','--root',overlay_copy],False);negatives.append('wrong diagnostic activation baseline')
        for source_id,base_id,script in [(26,None,'recovery57'),(28,26,'recovery55')]:
            run([sys.executable,'-B',ROOT/f'sessions/{script}/rebuild_historical_source.py','project','--base-project',tmp/f'candidate{base_id}' if base_id else a.base_project.resolve(),'--source',f'candidate{source_id}','--out',tmp/f'candidate{source_id}'])
        for c in range(29,34):
            out=tmp/f'candidate{c}';run([sys.executable,'-B',recpath,'project','--base-project',tmp/'candidate28','--source',f'candidate{c}','--out',out])
            assert sha(out/'f722-heli.kicad_pcb')==expected[str(c)]
            count=sum(p.is_file() for p in out.rglob('*'));assert count==62
            recovered.append(dict(candidate=c,board_sha256=expected[str(c)],functional_paired_files=count))
        for label in ['raw53','native52','engine50','servo2-origin-count2','coordinated49']:
            packet=ROOT/'sessions'/label;identity=read(packet/'source-identity.json');assert sha(ROOT/identity['importer_source_path'])==identity['importer_source_sha256']
            run([sys.executable,'-B',ROOT/'tests/verify_session_packet.py','--packet',packet,'--out',tmp/(label+'.json')])
            board=tmp/identity['source_candidate']/'f722-heli.kicad_pcb';out=tmp/(label+'-projection')
            run([sys.executable,'-B',ROOT/'prepare_session_replay.py','--packet',packet,'--source-board',board,'--out',out])
            bound=read(out/'engine-report.json');assert bound['model_sha256']==sha(out/'model.json')
            wrong=tmp/(label+'-wrong.kicad_pcb');wrong.write_bytes(board.read_bytes()+b'\n')
            run([sys.executable,'-B',ROOT/'prepare_session_replay.py','--packet',packet,'--source-board',wrong,'--out',tmp/(label+'-bad')],False);negatives.append(label+':wrong source board')
            for name in ['session.ses','engine-report.json','import-contract.json']:
                bad=tmp/(label+'-bad-'+name);shutil.copytree(packet,bad);(bad/name).write_bytes((bad/name).read_bytes()+b'\n')
                run([sys.executable,'-B',ROOT/'prepare_session_replay.py','--packet',bad,'--source-board',board,'--out',tmp/(label+'-bad-out')],False);negatives.append(label+':tampered '+name)
            packets.append(dict(packet=label,ses_report_geometry_equal=True,projection_rebinding_verified=True,engine_insertion_succeeded=identity['engine_insertion_succeeded'],adopted_geometry=identity['adopted_geometry'],native_replay_executed=False))
        # Re-execute the exact constructor with sufficient, explicitly reduced inputs.
        construct=tmp/'constructor';(construct/'candidate32').mkdir(parents=True)
        shutil.copyfile(tmp/'candidate32/f722-heli.kicad_pcb',construct/'candidate32/f722-heli.kicad_pcb')
        for src,dst in [('construct_servo2_joint.py','construct_servo2_joint.py'),('checks/candidate32-f722-heli.logical-route-map.json','candidate32/f722-heli.logical-route-map.json'),('tests/servo2-joint32/inputs/source-native-projection.json','candidate32/f722-heli.native.json'),('tests/servo2-joint32/inputs/role-projection.json','model-candidate32-ready/model.json'),('sessions/servo2-origin-count2/engine-report.json','model-candidate31-ready/filtered05.successes/count2/snapshot.after.json')]:
            p=construct/dst;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/src,p)
        run([sys.executable,'-B',construct/'construct_servo2_joint.py'])
        made=construct/'tests/servo2-joint32';historical=ROOT/'sessions/coordinated49'
        assert sha(made/'constructed.ses')==sha(historical/'session.ses')
        assert read(made/'constructed-report.json')['routes']==read(historical/'engine-report.json')['routes']
        for k,v in read(historical/'import-contract.json').items():assert read(made/'native-construction-model.json')[k]==v
        # Apply the unchanged source-scope validator to exact parsed native PCB records.
        tree=ast.parse((ROOT/'import_session_v8.py').read_text());names={'parse','children','child'};ns={'re':re,'json':json};exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names],type_ignores=[]),'historical-parser','exec'),ns)
        def records(c):
            board=tmp/f'candidate{c}/f722-heli.kicad_pcb';x=ns['parse'](board.read_text());children=ns['children'];child=ns['child'];nets={n[1]:n[2] for n in children(x,'net')}
            objs=[dict(uuid=child(o,'uuid')[1],kind='track' if o[0]=='segment' else 'via',net=nets.get(child(o,'net')[1],child(o,'net')[1]),native_record=o) for o in x if isinstance(o,list) and o and o[0] in ['segment','via']]
            return dict(board_sha256=sha(board),objects=objs,footprints=children(x,'footprint'),edge_cuts=[o for o in x if isinstance(o,list) and o and o[0].startswith('gr_')],copper_layers=child(x,'layers'))
        before,after=records(32),records(33);validator=module('ordinary_scope',ROOT/'validate_ordinary_rewrite.py');proof=receipt('candidate33-source-change-controls.json');construction=receipt('candidate33-coordinated-change-receipt.json');rp=ROOT/'checks/candidate33-coordinated-change-receipt.json'
        # Raw29 is refused; verify repaired30 changes exactly the two declared
        # new endpoints and one deleted new spur while preserving source28.
        source28,raw29,repaired30=records(28),records(29),records(30)
        by=lambda d:{o['uuid']:o for o in d['objects']}
        b28,b29,b30=map(by,[source28,raw29,repaired30]);recipe=receipt('candidate30-tail-repair-recipe.json');repair=receipt('candidate30-tail-repair.json')
        assert repair['repair_source_sha256']==sha(ROOT/'repair_new_route_tails.py')
        assert repair['recipe_sha256']==original('candidate30-tail-repair-recipe.json')
        assert all(b29.get(uid)==o==b30.get(uid) for uid,o in b28.items())
        assert set(b29)-set(b30)==set(recipe['remove']) and not set(b30)-set(b29)
        altered={uid for uid in b29.keys() & b30.keys() if b29[uid]!=b30[uid]};assert altered=={x['uuid'] for x in recipe['trims']}
        for row in recipe['trims']:
            old,new=b29[row['uuid']]['native_record'],b30[row['uuid']]['native_record'];endpoint=row['endpoint'];anchor=b30[row['anchor_via_uuid']]['native_record'];target=ns['child'](new,endpoint)
            assert list(map(float,target[1:]))==row['new_xy_mm']==list(map(float,ns['child'](anchor,'at')[1:]))
            assert [target if isinstance(x,list) and x and x[0]==endpoint else x for x in old]==new
        assert source28['footprints']==raw29['footprints']==repaired30['footprints']
        allowed,actual=validator.validate(before,after,rp,construction['source_native_sha256'])
        for k in ['actual_removed_uuids','actual_added_uuids','existing_uuid_records_edited']:assert actual[k]==proof['source_change'][k]
        old={o['uuid']:o for o in before['objects']};now={o['uuid']:o for o in after['objects']};lm0=receipt('candidate32-f722-heli.logical-route-map.json')['logical_route_map'];lm1=receipt('candidate33-f722-heli.logical-route-map.json')['logical_route_map']
        changed={uid:dict(before=alias,after=lm1[uid]) for uid,alias in lm0.items() if uid in now and lm1[uid]!=alias};assert changed==construction['logical_reassignments']==proof['exact_logical_reassignments']
        assert all(old[uid]==now[uid] and old[uid]['kind']=='via' for uid in changed)
        ground=next(o for o in before['objects'] if o['kind']=='via' and o['net']=='GND')
        cases=[];r=copy.deepcopy(construction);r['mutable_route_uuids'].append(ground['uuid']);cases.append(('wrong-net allowance',after,r))
        q=copy.deepcopy(after);q['objects']=[o for o in q['objects'] if o['uuid']!=ground['uuid']];cases.append(('undeclared ground removal',q,construction))
        r=copy.deepcopy(construction);r['source_board_sha256']='0'*64;cases.append(('stale rewrite source',after,r))
        q=copy.deepcopy(after);next(o for o in q['objects'] if o['uuid'] in changed)['native_record'].append(['at','0','0']);cases.append(('existing via record mutation',q,construction))
        q=copy.deepcopy(after);next(o for o in q['objects'] if o['uuid'] not in old)['net']='USB_P';cases.append(('new copper on wrong net',q,construction))
        for name,q,r in cases:
            p=tmp/'bad-rewrite.json';write(p,r);reject(name,lambda q=q,p=p:validator.validate(before,q,p,construction['source_native_sha256']))
        delta=read(ROOT/'sessions/recovery49/candidate33.f722-heli.kicad_pcb.delta.json');b=(tmp/'candidate28/f722-heli.kicad_pcb').read_bytes()
        for name,base,d in [('wrong recovery source',b+b'\n',delta),('wrong target hash',b,dict(delta,target_sha256='0'*64)),('out-of-range copy',b,dict(delta,operations=[[0,len(b)+1]])),('invalid delta operation',b,dict(delta,operations=[{'exec':'forbidden'}])),('unsupported transform',b,dict(delta,base_transform='forbidden'))]:reject(name,lambda b=base,d=d:recovery.reconstruct(b,d))
        bad=tmp/'bad-paired';shutil.copytree(tmp/'candidate28',bad);(bad/'f722-heli.kicad_pro').write_bytes(b'invalid')
        reject('tampered paired project',lambda:recovery.prepare_project(bad,'candidate33',ROOT/'sessions/recovery49'))
        for path in ['../escape','/absolute','safe/../escape','windows\\escape']:reject('unsafe recovery path:'+path,lambda p=path:recovery.relative_path(p))
    result=dict(passed=True,verifier_source_sha256=sha(__file__),scope='Portable historical binding, exact paired recovery, SES/report parsing, exact SERVO2 constructor session reproduction, parsed PCB record rewrite controls, diagnostic source overlay checks. No new native geometry qualification.',base_manifest_sha256=source['base_manifest_sha256'],recovered_projects=recovered,packets=packets,negative_controls_passed=len(negatives),negative_controls=negatives,original_source_hash_checks_performed=bool(a.historical_workspace),servo2_constructor_exact_session_reproduced=True,servo2_constructor_inputs_are_projections=True,source_rewrite_controls_reexecuted_on_exact_board_records=True,critical_reference_nonzero_deltas_retained=True,diagnostic_overlay_static_check_passed=True,diagnostic_overlay_activation_restore_verified=True,diagnostic_located_connection_runtime_exercised=True,diagnostic_runtime_reexecuted_by_packaging=False,source33_zero_import_historical_binding_verified=True,candidate33_owner_adopted=status['candidate33_owner_adopted'],native_replay_reexecuted=False,native_DRC_reexecuted=False,endpoint_geometry_reexecuted=False,JVM_router_refill_or_power_solve_executed=False,numerical_power_and_VCAP_applicability=False,native_open_connections=49,native_errors=0,native_warnings=0)
    write(a.out,result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
