#!/usr/bin/env python3
"""Capture bounded 29–33 provenance and recovery; no native/JVM/solver work."""
import argparse
import difflib
import hashlib
import json
import shutil
from pathlib import Path

BASE_MANIFEST = 'd7fc5052b8f672f13d4fa031d23953f05916d01460b1da25fdb2e29d6da0f9d2'
BASE_ZIP = '985475c549cec9c51a4d0ba425eb318ad4c6b9ea02868b50c19d2b9cfdc8d9a8'
EXPECTED = {28:'3afc574bdd766292932323c54fd198cc2cb88ab93617a434fe5d104ab01838d2',29:'6285a27dc5cbe240f3a0df5bac489b7141956be5033d7326a72b49c630a042ae',30:'a38795cf06c9b8e531b1253abbf34ef4029b80d930ed8c982aff9f2b5076f1d6',31:'a650e7df94cea3a171cf7dc16d0b951f6f8b069c2bb587100310ef22ffe40c28',32:'20072f5ed493d88dda69d61a69d8c6d9bcad9aa6d7eabed93ca060aa473cb035',33:'1fe3090e0674c51083b924a077bb068ba8afa4041b6f92fa74ce6b9612c178a6'}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_bytes())
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--workspace',type=Path,required=True)
    ap.add_argument('--adopted33',action='store_true',help='Use only after owner explicitly reports adoption.')
    a=ap.parse_args();root=a.workspace.resolve();stage=Path(__file__).resolve().parents[1];base=root/'public-source-ready-v9'
    assert sha(base/'FILES.sha256.json')==BASE_MANIFEST and sha(root/'routing-source-v9-delta.zip')==BASE_ZIP
    projections,sources={},{}
    def portable(v):
        if isinstance(v,dict): return {portable(k):portable(x) for k,x in v.items()}
        if isinstance(v,list): return [portable(x) for x in v]
        if isinstance(v,str):
            v=v.replace(str(root)+'/', '').replace(str(root.parent)+'/', '')
            assert '/workspace/' not in v,v
        return v
    def copy(src,dst):
        p,q=root/src,stage/dst;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
        sources[dst]={'historical_path':src,'sha256':sha(p)}
    def project(src,dst,transform=None,scope=None):
        p=root/src;d=portable(read(p));d=transform(d) if transform else d;write(stage/dst,d)
        projections[dst]={'historical_path':src,'historical_file_sha256':sha(p),'historical_bytes':p.stat().st_size,'portable_file_sha256':sha(stage/dst),'projection':scope or 'JSON data unchanged except historical paths made relative and whitespace normalized.'}
        return d
    for c,digest in EXPECTED.items(): assert sha(root/f'candidate{c}/f722-heli.kicad_pcb')==digest
    for c in range(29,34):
        for p in sorted((root/f'candidate{c}').glob('*.json')):
            if p.name in {'parts.json','f722-heli.native.json','owner-native.json','owner-mechanical-geometry.json','owner-adoption.json'}:continue
            project(str(p.relative_to(root)),f'checks/candidate{c}-'+p.name)
        if c in [30,31,32] or c==33 and a.adopted33:
            copy(f'candidate{c}/owner-adoption.json',f'checks/candidate{c}-owner-adoption.json')
    for c,opens,prior in [(30,53,55),(31,52,53),(32,50,52),(33,49,50)]:
        folder=f'../checkpoint{opens}-review/'
        project(folder+f'comparison-{prior}-to-{opens}.json',f'checks/candidate{c}-critical-reference-comparison.json')
        for name in ['owner-additive-integration.json','owner-coordinated-integration.json','reference-change-review.json','actual-io22.json']:
            if (root/folder/name).exists():project(folder+name,f'checks/candidate{c}-'+name)
    copy('../repo/f722-heli/layout-revision/signal-review/native/review_reference_window_change.py','tests/routing-checkpoint49/review_reference_window_change.py')
    for name in ['compare_reference_geometry.py','check_signal_geometry.py','check_critical_reference.py']:
        copy('../repo/f722-heli/layout-revision/signal-review/native/'+name,'tests/routing-checkpoint49/'+name)
    for src,dst in {
        'candidate30/repair_new_route_tails.used.py':'repair_new_route_tails.py',
        'candidate32/run_bounded_search.used.py':'run_bounded_search.py',
        'candidate32/preserve_success_checkpoints.used.py':'preserve_success_checkpoints.py',
        'candidate33/construct_servo2_joint.used.py':'construct_servo2_joint.py',
        'candidate33/validate_ordinary_rewrite.used.py':'validate_ordinary_rewrite.py',
        'candidate33/audit_support_after_ordinary_rewrite.used.py':'audit_support_after_ordinary_rewrite.py',
        'candidate33/audit_rewritten_native_endpoints.used.py':'tests/routing-checkpoint49/audit_rewritten_native_endpoints.py',
        'candidate33/audit_source_change_controls.used.py':'tests/servo2-joint32/audit_source_change_controls.py',
    }.items():copy(src,dst)
    for c in [30,31,32,33]:
        for name,dst in [('import_session.used.py','import_session_v8.py'),('route_geometry.used.py','route_geometry.py'),('audit_native_endpoints.used.py','tests/routing-checkpoint55/audit_native_endpoints.py')]:
            assert sha(root/f'candidate{c}'/name)==sha(stage/dst)
    for p in sorted((root/'servo2-local-review').glob('*.py')):copy(str(p.relative_to(root)),str(p.relative_to(root)))
    project('servo2-local-review/review.json','servo2-local-review/review.json')
    for name in ['support-audit-scope.patch','endpoint-audit-scope.patch']:copy('tests/servo2-joint32/'+name,'tests/servo2-joint32/'+name)
    fields=['board_sha256','aliases','ordinary_nets','routable_layers','mutable_source_ids','source_logical_nets','regenerable_reference_zones']
    packet_specs=[
        (29,28,'raw53','model-candidate28-ready/model.json','model-candidate28-ready/filtered03.successes/final',True),
        (31,30,'native52','tests/located-porta-tx28/prepared-on30/native-construction-model.json','tests/located-porta-tx28/prepared-on30',False),
        (32,31,'engine50','model-candidate31-ready/model.json','model-candidate31-ready/filtered05.successes/final',True),
        (None,31,'servo2-origin-count2','model-candidate31-ready/model.json','model-candidate31-ready/filtered05.successes/count2',True),
        (33,32,'coordinated49','tests/servo2-joint32/native-construction-model.json','tests/servo2-joint32',False)]
    for c,source,label,model_src,folder,engine in packet_specs:
        model=read(root/model_src);packet='sessions/'+label
        ses=folder+('/snapshot.ses' if engine else '/constructed.ses')
        report=folder+('/snapshot.after.json' if engine else '/constructed-report.json')
        copy(ses,packet+'/session.ses')
        project(report,packet+'/engine-report.json',lambda d:dict(d,areas=[]) if 'areas' in d else d,'All route geometry and metadata retained; fixed guard area arrays omitted when present.')
        write(stage/packet/'import-contract.json',{k:model[k] for k in fields})
        identity=dict(kind=('actual_engine_session' if engine else 'explicit_native_construction'),board_sha256=model['board_sha256'],native_sha256=model['native_sha256'],model_sha256=sha(root/model_src),historical_model_path=model_src,source_candidate=f'candidate{source}',candidate=f'candidate{c}' if c else None,candidate_sha256=EXPECTED[c] if c else None,session_sha256=sha(stage/packet/'session.ses'),engine_report_sha256=sha(stage/packet/'engine-report.json'),historical_engine_report_sha256=sha(root/report),import_contract_sha256=sha(stage/packet/'import-contract.json'),import_contract_fields=fields,full_model_included=False,importer_source_path='import_session_v8.py',importer_source_sha256=sha(stage/'import_session_v8.py'),import_arguments=['--preserve-unaffected-fills'] if c==31 else [],engine_insertion_succeeded=engine,native_replay_reexecuted_for_v10=False,numerical_power_and_VCAP_applicability=False,portable_path_projections='checks/v10-portable-projections.json',adopted_geometry=False if c in [None,29] else True if c in [31,32] else a.adopted33)
        write(stage/packet/'source-identity.json',identity)
        if engine:project(folder+'/receipt.json',packet+'/selected-checkpoint-receipt.json')
        else:
            project(folder+'/construction.json',packet+'/native-construction.json')
            project(model_src,packet+'/original-import-contract.json')
    # The compact, sufficient constructor inputs are projections, not native exports.
    native=read(root/'candidate32/f722-heli.native.json');logical=read(root/'candidate32/f722-heli.logical-route-map.json')['logical_route_map']
    project('candidate32/f722-heli.native.json','tests/servo2-joint32/inputs/source-native-projection.json',lambda d:{'board_sha256':d['board_sha256'],'objects':[o for o in d['objects'] if logical.get(o['uuid'])=='SERVO2_MCU::P0']},'Exact 15 SERVO2 P0 object records and board identity only. Not a full native geometry export.')
    project('model-candidate32-ready/model.json','tests/servo2-joint32/inputs/role-projection.json',lambda d:{k:d[k] for k in fields},'Only constructor role and import-contract fields. Not an engine planning model.')
    for src,dst in [('tests/servo2-joint32/construction.json','tests/servo2-joint32/construction.json'),('tests/located-porta-tx28/located-receipt.json','tests/located-porta-tx28/located-receipt.json'),('tests/located-porta-tx28/proposal-on30.json','tests/located-porta-tx28/proposal-on30.json')]:project(src,dst)
    src='tests/located-porta-tx28/captured-engine.log'
    lines=[line for line in (root/src).read_text().splitlines() if line.startswith('INSERT_DIAGNOSTIC ') and json.loads(line[len('INSERT_DIAGNOSTIC '):])['net']=='PORT_A_TX_EXT::P0']
    (stage/src).write_text('\n'.join(lines)+'\n')
    projections[src]={'historical_path':src,'historical_file_sha256':sha(root/src),'historical_bytes':(root/src).stat().st_size,'portable_file_sha256':sha(stage/src),'projection':'Exact PORT_A_TX_EXT::P0 diagnostic lines; unrelated progress omitted.'}
    # Freeze zero controls only after complete receipts exist.
    for c in [31,32,33]:
        model_src=f'model-candidate{c}-ready/model.json';m=read(root/model_src)
        for n in ['zero-parity.json','imported-zero.import.json','fixed-explicit-native-ids.json','summary.json']:
            project(f'model-candidate{c}-ready/'+n,f'checks/source{c}-'+n)
        assert read(root/f'model-candidate{c}-ready/zero-parity.json')['passed']
        write(stage/f'checks/source{c}-fixed-preservation-contract.json',dict(historical_model_sha256=sha(root/model_src),board_sha256=m['board_sha256'],mutable_source_ids=m['mutable_source_ids'],source_logical_nets=m['source_logical_nets'],adapter_sources=m['adapter_sources'],full_model_included=False))
    diag='staged-complete-path-diagnostics-20261009/'
    for n in ['complete-located-connection.patch','REPORT.md','stage_and_verify.py']:copy(diag+n,'tests/complete-path-diagnostics/'+n)
    for n in ['baseline-identity.json','static-verification.json','promotion-identity.json']:project(diag+n,'tests/complete-path-diagnostics/'+n)
    java='src/app/freerouting/autoroute/InsertFoundConnectionAlgo.java'
    copy(java,'tests/complete-path-diagnostics/InsertFoundConnectionAlgo.java')
    assert sha(root/(diag+'baseline/'+java))==sha(stage/java)
    for n in ['located06-outcome.json','located06.bounded-run.json']:project('model-candidate32-ready/'+n,'tests/complete-path-diagnostics/'+n)
    project(diag+'runtime-verification.json','tests/complete-path-diagnostics/runtime-verification.json')
    copy(diag+'runtime-located-records.log','tests/complete-path-diagnostics/runtime-located-records.log')
    project('model-candidate33-ready/filtered07.bounded-run.json','tests/complete-path-diagnostics/filtered07.bounded-run.json')
    project('model-candidate33-ready/filtered07.successes/count1/receipt.json','tests/complete-path-diagnostics/filtered07-count1-receipt.json')
    # Exact paired geometry is recovered with pure byte copy deltas from candidate28.
    rec=stage/'sessions/recovery49';rec.mkdir(exist_ok=True)
    script=(stage/'sessions/recovery55/rebuild_historical_source.py').read_text().replace('("candidate26", "candidate27", "candidate28")','("candidate28", "candidate29", "candidate30", "candidate31", "candidate32", "candidate33")').replace('candidate26 project recovered by V8','candidate28 project recovered by V9')
    (rec/'rebuild_historical_source.py').write_text(script)
    manifest=read(stage/'sessions/recovery55/paired-files.json');manifest['sources']={};manifest['base_label']='candidate28 / accepted55'
    b=(root/'candidate28/f722-heli.kicad_pcb').read_bytes();manifest['required_base_files']['f722-heli.kicad_pcb']={'sha256':EXPECTED[28],'bytes':len(b)}
    manifest['base_recovery']={'script':'sessions/recovery55/rebuild_historical_source.py','source':'candidate28','prior_recovery':'sessions/recovery57/rebuild_historical_source.py','required_external_project':'Hash-pinned candidate22/accepted62 paired project','immutable_v9_manifest_sha256':BASE_MANIFEST}
    lines=b.splitlines(keepends=True);offsets=[0]
    for line in lines:offsets.append(offsets[-1]+len(line))
    for c in range(28,34):
        for name,info in manifest['required_base_files'].items():
            if name!='f722-heli.kicad_pcb':assert sha(root/f'candidate{c}'/name)==info['sha256'],(c,name)
        target=(root/f'candidate{c}/f722-heli.kicad_pcb').read_bytes();entries={}
        if c!=28:
            t=target.splitlines(keepends=True);operations=[]
            for tag,i,j,k,l in difflib.SequenceMatcher(None,lines,t,autojunk=True).get_opcodes():
                if tag=='equal':operations.append([offsets[i],offsets[j]-offsets[i]])
                elif tag in ['replace','insert']:operations.append(b''.join(t[k:l]).decode())
            name=f'candidate{c}.f722-heli.kicad_pcb.delta.json'
            write(rec/name,dict(schema='f722-historical-source-copy-delta/v1',base_sha256=EXPECTED[28],target_sha256=EXPECTED[c],target_bytes=len(target),operations=operations))
            entries['f722-heli.kicad_pcb']={'file':name,'sha256':sha(rec/name)}
        manifest['sources'][f'candidate{c}']=dict(source_label=f'candidate{c}',purpose='Exact paired historical bytes only. Candidate29 is refused. No fresh native or electrical qualification.',board_sha256=EXPECTED[c],board_bytes=len(target),unchanged_paired_files=len(manifest['required_base_files'])-1,deltas=entries)
    write(rec/'paired-files.json',manifest)
    overwritten=[]
    for c in range(30,34):
        for name,old in read(root/f'candidate{c}/route-handoff.json')['files'].items():
            p=root/f'candidate{c}'/name
            if p.exists() and sha(p)!=old:overwritten.append(dict(candidate=c,filename=name,historical_handoff_sha256=old,current_owner_file_sha256=sha(p),historical_bytes_retained=False))
    write(stage/'checks/v10-historical-receipt-status.json',dict(historical_handoffs_preserved_except_path_projection=True,later_owner_receipts_recorded_separately=True,overwritten_historical_receipts=overwritten,candidate29_refused=True,candidate33_owner_adopted=a.adopted33))
    write(stage/'checks/v10-portable-projections.json',dict(schema='f722-portable-path-projections/v1',files=projections,historical_dependency_hashes_unchanged=True))
    write(stage/'checks/v10-source-identity.json',dict(schema='f722-v10-source-selection/v1',base_manifest_sha256=BASE_MANIFEST,base_zip_sha256=BASE_ZIP,sources=sources,expected_boards=EXPECTED,historical_java_baseline_unchanged=True,current_diagnostics_overlay='tests/complete-path-diagnostics/InsertFoundConnectionAlgo.java',heavy_execution_performed=False,candidate33_owner_adopted=a.adopted33))
    write(stage/'status.json',dict(checkpoint='candidate33-source-v10',status='unfinished',candidate33_owner_adopted=a.adopted33,latest_owner_adopted_candidate=33 if a.adopted33 else 32,candidate_board_sha256=EXPECTED[33],native_open_connections=49,native_errors=0,native_warnings=0,strict_schematic_parity=0,ordinary_nets_complete=17,ordinary_nets_total=51,actual_bonded_io_cuts_passed=8,actual_bonded_io_cuts_total=22,support_nets_geometrically_connected=28,numerical_power_and_VCAP_applicability=False,last_fully_bound_numerical_candidate=24,last_fully_bound_numerical_board_sha256='8373a599fe81a58571422fc4a1f4fe3afb65acad2fd7b3528eef43d575edce11',numerical_power_stale_since_candidate=26,fabrication_ready=False,source33_zero_import_byte_identical=True,fresh_native_replay_performed_by_packaging=False))
    print(json.dumps({'projected_files':len(projections),'source_receipts':len(sources),'candidate33_owner_adopted':a.adopted33}))

if __name__=='__main__':main()
