#!/usr/bin/env python3
"""Incremental V11 identities, exact recovery and subset controls; standard library only."""
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
def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def run(args,ok=True):
    r=subprocess.run([str(x) for x in args],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True)
    assert (r.returncode==0)==ok,(args,r.stdout,r.stderr)
    return r
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base-project',type=Path,required=True);ap.add_argument('--historical-workspace',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    identity=read(ROOT/'checks/v11-source-identity.json');expected=identity['expected_boards'];sources=identity['sources'];projections=read(ROOT/'checks/v11-portable-projections.json')['files'];status=read(ROOT/'status.json')
    receipt=lambda n:read(ROOT/'checks'/n)
    original=lambda n:sources['checks/'+n]['sha256'] if 'checks/'+n in sources else projections['checks/'+n]['historical_file_sha256']
    for n,i in sources.items():
        assert sha(ROOT/n)==i['sha256'],n
        if a.historical_workspace:assert sha(a.historical_workspace/i['historical_path'])==i['sha256'],n
    for n,i in projections.items():
        assert sha(ROOT/n)==i['portable_file_sha256'] and '/workspace/' not in (ROOT/n).read_text(),n
        if a.historical_workspace:assert sha(a.historical_workspace/i['historical_path'])==i['historical_file_sha256'],n
    for i in identity['used_sources'].values():assert sha(ROOT/i['packet_path'])==i['sha256']
    assert identity['cutoff_candidate']==37 and identity['raw36_refused'] and not identity['sealed_handoff_dependencies_overwritten']
    assert status['latest_owner_adopted_candidate']==37 and status['candidate_board_sha256']==expected['37']
    assert not status['numerical_power_and_VCAP_applicability'] and status['last_fully_bound_numerical_candidate']==24 and status['numerical_power_stale_since_candidate']==26
    inherited=receipt('inherited-v10-portable-verification.json');assert inherited['passed'] and inherited['zip_sha256']==identity['base_zip_sha256'] and inherited['new_manifest_sha256']==identity['base_manifest_sha256']
    for c,opens in [(34,48),(35,47),(37,45)]:
        owner=receipt(f'candidate{c}-owner-summary.json');handoff=receipt(f'candidate{c}-route-handoff.json');adopted=receipt(f'candidate{c}-owner-adoption.json')
        assert sha(ROOT/f'checks/candidate{c}-route-handoff.json')==identity['sealed_handoffs'][str(c)]
        assert owner['board_sha256']==handoff['board_sha256']==adopted['board_sha256']==expected[str(c)]
        assert owner['drc']==owner['drc-all']==dict(unconnected=opens,errors=0,warnings=0)
        for gate in ['process','mechanical','parity','firmware']:assert owner[gate]['passed'] and owner[gate]['board_sha256']==expected[str(c)]
        assert owner['critical']['connected_nets']==owner['critical']['total_nets']==16 and not owner['critical']['faults']
        assert receipt(f'candidate{c}-endpoint-audit.json')['passed']
        assert adopted['native_unfinished_connections']==opens and not adopted['numerical_applicability']
        for k,n in {'native_gate_receipt_sha256':'owner-summary.json','integration_receipt_sha256':'owner-additive-integration.json','reference_comparison_sha256':'critical-reference-comparison.json','actual_io_receipt_sha256':'protection-actual-io.json'}.items():assert adopted[k]==original(f'candidate{c}-'+n),(c,k)
        ref=receipt(f'candidate{c}-critical-reference-comparison.json');assert ref['after_board_sha256']==expected[str(c)] and ref['critical_object_geometry_identical']
        assert all(v==0 for n in ref['net_numeric_deltas_after_minus_before'].values() for v in n.values())
        assert all(row['lost_GND_overlap_with_trace_width_mm2']==0 for x in ref['ground_fill_changes'].values() for row in x['critical_trace_proximity'].values())
        ep=handoff['endpoint_summary'];assert ep['minimum_positive_pad_depth_mm']>0 and ep['minimum_full_width_pad_transverse_entry_length_mm']>0
        if c!=35:assert ep['minimum_full_width_annular_strip_length_mm']>0 and ep['minimum_annular_section_boundary_reserve_mm']>0
        io=receipt(f'candidate{c}-protection-actual-io.json');assert len(io['checks'])==22 and sum(x['complete_clamp_first_path_passes'] for x in io['checks'])==9
    ref=receipt('candidate37-critical-reference-comparison.json')
    assert all(x['physical_GND_lost_mm2']==0.3926085766365002 for x in ref['ground_fill_changes'].values())
    proof=receipt('candidate35-exact-source-reference-proof.json');assert proof['saved_zones_and_fills_exact'] and proof['all_source_drills_and_masks_exact'] and proof['new_drills']==0
    imp35=receipt('candidate35-f722-heli.import.json');assert imp35['preserve_unaffected_fills_requested'] and imp35['unaffected_fill_preconditions_verified'] and not imp35['reference_plane_refill_performed']
    refusal=receipt('candidate36-route-refusal.json');assert refusal['drc']==dict(unconnected=45,errors=0,warnings=1) and refusal['status']=='refused_unaccepted_engine_candidate'
    assert not receipt('candidate36-endpoint-audit.json')['passed']
    imp=receipt('candidate37-f722-heli.import.json');assert imp['source_sha256']==expected['35'] and imp['immediate_construction_source_sha256']==expected['36'] and imp['output_sha256']==expected['37']
    assert not imp['direct_engine_output'] and not imp['ses_engine_native_geometry_equal'] and imp['raw_import_ses_engine_native_geometry_equal']
    assert imp['tracks_added_relative_to_accepted_source']==9 and imp['vias_added_relative_to_accepted_source']==1 and imp['all_accepted_source_objects_exact']==1793
    for key,n in [('raw_import_receipt_sha256','raw-engine-import.json'),('cleanup_receipt_sha256','tail-repair.json'),('cleanup_recipe_sha256','tail-repair-recipe.json'),('engine_lineage_receipt_sha256','engine-lineage.json'),('logical_route_map_sha256','f722-heli.logical-route-map.json')]:assert imp[key]==original('candidate37-'+n)
    assert original('candidate37-raw-engine-import.json')==original('candidate36-f722-heli.import.json')
    for c in [34,35,37]:
        zero=receipt(f'source{c}-zero-parity.json');zimp=receipt(f'source{c}-imported-zero.import.json');contract=receipt(f'source{c}-fixed-preservation-contract.json');fixed=receipt(f'source{c}-fixed-explicit-native-ids.json')
        assert zero['passed'] and not zero['errors'] and zero['board_sha256']==expected[str(c)]
        assert zimp['source_sha256']==zimp['output_sha256']==expected[str(c)] and zimp['routes_added']==zimp['routes_removed']==0
        assert contract['historical_model_sha256']==zero['model_sha256'] and set(fixed).isdisjoint(contract['mutable_source_ids'])
        for n,h in contract['adapter_sources'].items():
            p=ROOT/('tests/complete-path-diagnostics/InsertFoundConnectionAlgo.java' if n=='src/app/freerouting/autoroute/InsertFoundConnectionAlgo.java' else n)
            assert sha(p)==h,(c,n)
    assert receipt('source37-zero-parity.json')['model_sha256']=='326a5176556b8994d70ff07ff61a9fc300134865091559e5129aae5c5e5ef599'
    negatives=[];recovered=[];packets=[]
    def reject(label,operation):
        try:operation()
        except (ValueError,KeyError,FileNotFoundError,AssertionError):negatives.append(label)
        else:raise AssertionError('Bad input accepted: '+label)
    recpath=ROOT/'sessions/recovery45/rebuild_historical_source.py';recovery=module('recovery45',recpath)
    with tempfile.TemporaryDirectory(prefix='v11-evidence-') as temp:
        tmp=Path(temp)
        for c,base,which in [(26,None,57),(28,26,55),(33,28,49)]:
            run([sys.executable,'-B',ROOT/f'sessions/recovery{which}/rebuild_historical_source.py','project','--base-project',tmp/f'candidate{base}' if base else a.base_project.resolve(),'--source',f'candidate{c}','--out',tmp/f'candidate{c}'])
        for c in range(34,38):
            out=tmp/f'candidate{c}';run([sys.executable,'-B',recpath,'project','--base-project',tmp/'candidate33','--source',f'candidate{c}','--out',out])
            assert sha(out/'f722-heli.kicad_pcb')==expected[str(c)] and sum(p.is_file() for p in out.rglob('*'))==62
            recovered.append(dict(candidate=c,board_sha256=expected[str(c)],functional_paired_files=62,adopted=c!=36))
        for label in ['engine48','engine47','raw45-refused36']:
            packet=ROOT/'sessions'/label;i=read(packet/'source-identity.json');assert sha(ROOT/i['importer_source_path'])==i['importer_source_sha256']
            run([sys.executable,'-B',ROOT/'tests/verify_session_packet.py','--packet',packet,'--out',tmp/(label+'.json')])
            board=tmp/i['source_candidate']/'f722-heli.kicad_pcb';out=tmp/(label+'-projection')
            run([sys.executable,'-B',ROOT/'prepare_session_replay.py','--packet',packet,'--source-board',board,'--out',out]);assert read(out/'engine-report.json')['model_sha256']==sha(out/'model.json')
            selected=read(packet/'selected-checkpoint-receipt.json');assert selected['session_sha256']==i['session_sha256'] and selected['report_sha256']==i['historical_engine_report_sha256'] and selected['route_counters']['routed_count']>0
            assert all(read(p)['attempt']['result']=='ROUTED' for p in packet.glob('count*-receipt.json'))
            c=37 if label=='raw45-refused36' else int(i['candidate'].removeprefix('candidate'))
            lineage=receipt(f'candidate{c}-engine-lineage.json')
            assert lineage['session_sha256']==i['session_sha256'] and lineage['engine_report_sha256']==i['historical_engine_report_sha256'] and lineage['model_sha256']==i['model_sha256']
            assert lineage['bounded_run_sha256']==sha(packet/'bounded-run.json')
            assert lineage['engine_successes']==len(list(packet.glob('count*-receipt.json')))
            assert lineage['post_router_cleanup']==(c==37)
            for n,h in lineage['engine_source_hashes'].items():
                source=ROOT/('tests/complete-path-diagnostics/InsertFoundConnectionAlgo.java' if n=='src/app/freerouting/autoroute/InsertFoundConnectionAlgo.java' else n)
                assert sha(source)==h
            wrong=tmp/(label+'-wrong.kicad_pcb');wrong.write_bytes(board.read_bytes()+b'\n')
            run([sys.executable,'-B',ROOT/'prepare_session_replay.py','--packet',packet,'--source-board',wrong,'--out',tmp/(label+'-bad')],False);negatives.append(label+':wrong source board')
            for n in ['session.ses','engine-report.json','import-contract.json']:
                bad=tmp/(label+'-bad-'+n);shutil.copytree(packet,bad);(bad/n).write_bytes((bad/n).read_bytes()+b'\n')
                run([sys.executable,'-B',ROOT/'prepare_session_replay.py','--packet',bad,'--source-board',board,'--out',tmp/(label+'-bad-out')],False);negatives.append(label+':tampered '+n)
            packets.append(dict(packet=label,ses_report_geometry_equal=True,projection_rebinding_verified=True,actual_engine_session=True,adopted_geometry=i['adopted_geometry'],native_replay_executed=False))
        # Parse exact recovered boards with the importer's pure parser, not pcbnew.
        tree=ast.parse((ROOT/'import_session_v8.py').read_text());names={'parse','children','child'};ns={'re':re,'json':json};exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names],type_ignores=[]),'historical-parser','exec'),ns)
        child,children=ns['child'],ns['children']
        trees={c:ns['parse']((tmp/f'candidate{c}/f722-heli.kicad_pcb').read_text()) for c in range(33,38)}
        records=lambda tree:{child(o,'uuid')[1]:o for o in tree if isinstance(o,list) and o and o[0] in ['segment','via','arc']}
        boards={c:records(t) for c,t in trees.items()}
        for before,after,tracks,vias in [(33,34,11,2),(34,35,3,0),(35,37,9,1)]:
            b,n=boards[before],boards[after];assert all(n.get(uid)==o for uid,o in b.items())
            added=[o for uid,o in n.items() if uid not in b];assert sum(o[0]=='segment' for o in added)==tracks and sum(o[0]=='via' for o in added)==vias
        assert children(trees[34],'zone')==children(trees[35],'zone')
        recipe=receipt('candidate37-tail-repair-recipe.json');repair=receipt('candidate37-tail-repair.json')
        assert not recipe['trims'] and len(recipe['remove'])==1 and repair['recipe_sha256']==original('candidate37-tail-repair-recipe.json') and repair['repair_source_sha256']==sha(ROOT/'repair_new_route_tails.py')
        def subset(b,raw,clean,removed):
            assert all(raw.get(uid)==o==clean.get(uid) for uid,o in b.items())
            assert set(raw)-set(clean)==set(removed) and not set(clean)-set(raw)
            assert all(raw[uid]==o for uid,o in clean.items()) and set(removed).isdisjoint(b)
        subset(boards[35],boards[36],boards[37],recipe['remove'])
        assert [o for o in trees[36] if not (isinstance(o,list) and o and o[0]=='segment' and child(o,'uuid')[1] in recipe['remove'])]==trees[37]
        maps={c:receipt(f'candidate{c}-f722-heli.logical-route-map.json')['logical_route_map'] for c in range(34,38)}
        assert {k:v for k,v in maps[36].items() if k not in recipe['remove']}==maps[37]==imp['logical_route_map']
        assert set(maps[37])<=set(boards[37]) and all(maps[37].get(k)==v for k,v in maps[35].items())
        reject('undeclared tail removal',lambda:subset(boards[35],boards[36],boards[37],[]))
        bad=copy.deepcopy(boards[37]);bad.pop(next(iter(boards[35])));reject('accepted source object removal',lambda:subset(boards[35],boards[36],bad,recipe['remove']))
        bad=copy.deepcopy(boards[37]);bad[next(iter(bad))].append(['unexpected','mutation']);reject('retained native object mutation',lambda:subset(boards[35],boards[36],bad,recipe['remove']))
        delta=read(ROOT/'sessions/recovery45/candidate37.f722-heli.kicad_pcb.delta.json');b=(tmp/'candidate33/f722-heli.kicad_pcb').read_bytes()
        for n,base,d in [('wrong recovery source',b+b'\n',delta),('wrong target hash',b,dict(delta,target_sha256='0'*64)),('out-of-range copy',b,dict(delta,operations=[[0,len(b)+1]])),('invalid operation',b,dict(delta,operations=[{'exec':'forbidden'}])),('unsupported transform',b,dict(delta,base_transform='forbidden'))]:reject(n,lambda b=base,d=d:recovery.reconstruct(b,d))
        bad=tmp/'bad-paired';shutil.copytree(tmp/'candidate33',bad);(bad/'f722-heli.kicad_pro').write_bytes(b'invalid');reject('tampered paired project',lambda:recovery.prepare_project(bad,'candidate37',ROOT/'sessions/recovery45'))
        for p in ['../escape','/absolute','safe/../escape','windows\\escape']:reject('unsafe recovery path:'+p,lambda p=p:recovery.relative_path(p))
    result=dict(passed=True,verifier_source_sha256=sha(__file__),scope='Incremental V11 source bindings, exact paired recovery, SES/report parsing, owner/reference/zero receipt bindings, and exact parsed native subset checks. Historical V10 controls retained by hash; no native qualification reexecuted.',base_manifest_sha256=identity['base_manifest_sha256'],recovered_projects=recovered,packets=packets,negative_controls_passed=len(negatives),negative_controls=negatives,original_source_hash_checks_performed=bool(a.historical_workspace),exact_candidate35_saved_zones_reverified=True,exact_raw36_to37_subset_reverified=True,sealed_handoffs_byte_exact=True,owner_adoptions_and_reference_comparisons_bound=True,source37_zero_import_historical_binding_verified=True,historical_v10_verification_retained_by_hash=True,native_replay_reexecuted=False,native_DRC_reexecuted=False,endpoint_geometry_reexecuted=False,JVM_router_refill_or_power_solve_executed=False,numerical_power_and_VCAP_applicability=False,native_open_connections=45,native_errors=0,native_warnings=0)
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
