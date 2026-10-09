#!/usr/bin/env python3
"""Capture only accepted 34/35/37 and refused raw36 provenance; no native work."""
import argparse
import difflib
import hashlib
import json
import shutil
from pathlib import Path

BASE_MANIFEST='749c4e20e4dbdb2bbb0bbb91e517a71c14817ffee2adda310cc28c2c26c3e024'
BASE_ZIP='e9953844bbb38196b26fb08d8c13b866dbfc79fcbfcb50d51923c7ce4c3adbbe'
EXPECTED={33:'1fe3090e0674c51083b924a077bb068ba8afa4041b6f92fa74ce6b9612c178a6',34:'49f5d0c7139202b51ad753906b63042449bb8cc15bdb0e688ea6253ed14385c3',35:'a76a523b70a39f1096de40da9e91037bbdf8030f7fcd17e5d92fb20d45690a6a',36:'9c8e03d1cde2e309f223aab44554ced81986437828a81602d42b271f5c3b6ba4',37:'2a73d9b7dad3a14b0d00c80e81e0ba8a817b50179c15692aad39fde9920c2115'}
HANDOFFS={34:'de40925b2432c2c378accd22ec6ec01a626958b5251159e8ad2981f2998b5efa',35:'27a1f374b4946857b88e9f48dbee8af300b859e9db021410476a4b5e6a312064',37:'be1aee520044dd420b87582e0ce4a15a6bc30ca5b72ab2b318d490ad0f44beaa'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);a=ap.parse_args()
    root=a.workspace.resolve();stage=Path(__file__).resolve().parents[1];base=root/'public-source-ready-v10'
    assert sha(base/'FILES.sha256.json')==BASE_MANIFEST and sha(root/'routing-source-v10-delta.zip')==BASE_ZIP
    sources,projections={},{}
    def portable(v):
        if isinstance(v,dict):return {portable(k):portable(x) for k,x in v.items()}
        if isinstance(v,list):return [portable(x) for x in v]
        if isinstance(v,str):
            v=v.replace(str(root)+'/', '').replace(str(root.parent)+'/', '')
            assert '/workspace/' not in v,v
        return v
    def capture(src,dst,transform=None,scope=None):
        p=root/src;q=stage/dst;q.parent.mkdir(parents=True,exist_ok=True)
        if transform or '/workspace/' in p.read_text():
            d=portable(read(p));write(q,transform(d) if transform else d)
            projections[dst]=dict(historical_path=src,historical_file_sha256=sha(p),historical_bytes=p.stat().st_size,portable_file_sha256=sha(q),projection=scope or 'Historical workspace prefixes removed; JSON values otherwise retained.')
        else:
            shutil.copyfile(p,q);sources[dst]=dict(historical_path=src,sha256=sha(p),bytes=p.stat().st_size)
    for c,h in EXPECTED.items():assert sha(root/f'candidate{c}/f722-heli.kicad_pcb')==h
    for c in range(34,38):
        for p in sorted((root/f'candidate{c}').glob('*.json')):
            if p.name in {'parts.json','f722-heli.native.json','owner-native.json','owner-mechanical-geometry.json'}:continue
            capture(str(p.relative_to(root)),f'checks/candidate{c}-'+p.name)
        if c in HANDOFFS:assert sha(stage/f'checks/candidate{c}-route-handoff.json')==HANDOFFS[c]
    for c,opens,prior in [(34,48,49),(35,47,48),(37,45,47)]:
        for name in ['owner-review-run.json','stock-spi-binding.json','current-review.json','actual-io22.json','owner-additive-integration.json',f'comparison-{prior}-to-{opens}.json']:
            capture(f'../checkpoint{opens}-review/'+name,f'checks/candidate{c}-'+('critical-reference-comparison.json' if name.startswith('comparison-') else name))
    used={}
    for c in [34,35,37]:
        for p in sorted((root/f'candidate{c}').glob('*.used.py')):
            digest=sha(p);matches=[x for x in stage.rglob('*.py') if sha(x)==digest]
            if matches:dst=str(matches[0].relative_to(stage))
            else:
                dst='tools/checkpoint45/'+p.name;capture(str(p.relative_to(root)),dst)
            used[f'candidate{c}/'+p.name]=dict(packet_path=dst,sha256=digest)
    fields=['board_sha256','aliases','ordinary_nets','routable_layers','mutable_source_ids','source_logical_nets','regenerable_reference_zones']
    for c,source,label,n in [(34,33,'engine48','07'),(35,34,'engine47','08'),(36,35,'raw45-refused36','09')]:
        mpath=f'model-candidate{source}-ready/model.json';m=read(root/mpath);folder=f'model-candidate{source}-ready/filtered{n}.successes/final';packet='sessions/'+label
        capture(folder+'/snapshot.ses',packet+'/session.ses')
        capture(folder+'/snapshot.after.json',packet+'/engine-report.json',lambda d:dict(d,areas=[]),'Exact route geometry and metadata retained; fixed guard area arrays omitted.')
        capture(folder+'/receipt.json',packet+'/selected-checkpoint-receipt.json')
        capture(f'model-candidate{source}-ready/filtered{n}.bounded-run.json',packet+'/bounded-run.json')
        for p in sorted((root/f'model-candidate{source}-ready/filtered{n}.successes').glob('count*/receipt.json')):
            capture(str(p.relative_to(root)),packet+'/'+p.parent.name+'-receipt.json')
        write(stage/packet/'import-contract.json',{k:m[k] for k in fields})
        importer=used[f'candidate{34 if c==36 else c}/import_session.used.py']
        write(stage/packet/'source-identity.json',dict(kind='actual_engine_session',board_sha256=m['board_sha256'],native_sha256=m['native_sha256'],model_sha256=sha(root/mpath),historical_model_path=mpath,source_candidate=f'candidate{source}',candidate=f'candidate{c}',candidate_sha256=EXPECTED[c],session_sha256=sha(stage/packet/'session.ses'),engine_report_sha256=sha(stage/packet/'engine-report.json'),historical_engine_report_sha256=sha(root/folder/'snapshot.after.json'),import_contract_sha256=sha(stage/packet/'import-contract.json'),import_contract_fields=fields,full_model_included=False,importer_source_path=importer['packet_path'],importer_source_sha256=importer['sha256'],import_arguments=['--preserve-unaffected-fills'] if c==35 else [],engine_insertion_succeeded=True,adopted_geometry=c!=36,native_replay_reexecuted_for_v11=False,numerical_power_and_VCAP_applicability=False,portable_path_projections='checks/v11-portable-projections.json'))
    for c in [34,35,37]:
        mpath=f'model-candidate{c}-ready/model.json';m=read(root/mpath)
        for n in ['zero-parity.json','imported-zero.import.json','fixed-explicit-native-ids.json','summary.json']:
            capture(f'model-candidate{c}-ready/'+n,f'checks/source{c}-'+n)
        write(stage/f'checks/source{c}-fixed-preservation-contract.json',dict(historical_model_sha256=sha(root/mpath),board_sha256=m['board_sha256'],mutable_source_ids=m['mutable_source_ids'],source_logical_nets=m['source_logical_nets'],adapter_sources=m['adapter_sources'],full_model_included=False))
    rec=stage/'sessions/recovery45';rec.mkdir(exist_ok=True)
    script=(base/'sessions/recovery49/rebuild_historical_source.py').read_text().replace('("candidate28", "candidate29", "candidate30", "candidate31", "candidate32", "candidate33")','("candidate33", "candidate34", "candidate35", "candidate36", "candidate37")').replace('candidate28 project recovered by V9','candidate33 project recovered by V10')
    (rec/'rebuild_historical_source.py').write_text(script)
    manifest=read(base/'sessions/recovery49/paired-files.json');manifest['sources']={};manifest['base_label']='candidate33 / accepted49'
    b=(root/'candidate33/f722-heli.kicad_pcb').read_bytes();manifest['required_base_files']['f722-heli.kicad_pcb']=dict(sha256=EXPECTED[33],bytes=len(b))
    manifest['base_recovery']=dict(script='sessions/recovery49/rebuild_historical_source.py',source='candidate33',required_external_project='Hash-pinned candidate22/accepted62 paired project',immutable_v10_manifest_sha256=BASE_MANIFEST)
    lines=b.splitlines(keepends=True);offsets=[0]
    for line in lines:offsets.append(offsets[-1]+len(line))
    for c in range(33,38):
        for name,info in manifest['required_base_files'].items():
            if name!='f722-heli.kicad_pcb':assert sha(root/f'candidate{c}'/name)==info['sha256'],(c,name)
        target=(root/f'candidate{c}/f722-heli.kicad_pcb').read_bytes();entries={}
        if c!=33:
            t=target.splitlines(keepends=True);operations=[]
            for tag,i,j,k,l in difflib.SequenceMatcher(None,lines,t,autojunk=True).get_opcodes():
                if tag=='equal':operations.append([offsets[i],offsets[j]-offsets[i]])
                elif tag in ['replace','insert']:operations.append(b''.join(t[k:l]).decode())
            name=f'candidate{c}.f722-heli.kicad_pcb.delta.json';write(rec/name,dict(schema='f722-historical-source-copy-delta/v1',base_sha256=EXPECTED[33],target_sha256=EXPECTED[c],target_bytes=len(target),operations=operations));entries['f722-heli.kicad_pcb']=dict(file=name,sha256=sha(rec/name))
        manifest['sources'][f'candidate{c}']=dict(source_label=f'candidate{c}',purpose='Exact paired bytes; raw36 is refused. No new native qualification.',board_sha256=EXPECTED[c],board_bytes=len(target),unchanged_paired_files=len(manifest['required_base_files'])-1,deltas=entries)
    write(rec/'paired-files.json',manifest)
    overwritten=[]
    for c in HANDOFFS:
        for n,h in read(root/f'candidate{c}/route-handoff.json')['files'].items():
            if sha(root/f'candidate{c}'/n)!=h:overwritten.append(dict(candidate=c,file=n,sealed_sha256=h,current_sha256=sha(root/f'candidate{c}'/n)))
    assert not overwritten
    capture('routing-source-v10-delta.portable-verification.json','checks/inherited-v10-portable-verification.json')
    write(stage/'checks/v11-portable-projections.json',dict(schema='f722-portable-path-projections/v1',files=projections,historical_dependency_hashes_unchanged=True))
    write(stage/'checks/v11-source-identity.json',dict(schema='f722-v11-source-selection/v1',base_manifest_sha256=BASE_MANIFEST,base_zip_sha256=BASE_ZIP,sources=sources,used_sources=used,expected_boards=EXPECTED,sealed_handoffs=HANDOFFS,sealed_handoff_dependencies_overwritten=overwritten,cutoff_candidate=37,raw36_refused=True,historical_java_baseline_unchanged=True,current_diagnostics_overlay='tests/complete-path-diagnostics/InsertFoundConnectionAlgo.java',heavy_execution_performed=False,candidate37_owner_adopted=True))
    status=read(base/'status.json');status.update(checkpoint='candidate37-source-v11',candidate37_owner_adopted=True,latest_owner_adopted_candidate=37,candidate_board_sha256=EXPECTED[37],native_open_connections=45,ordinary_nets_complete=19,actual_bonded_io_cuts_passed=9,actual_bonded_io_channels_passed=7,actual_bonded_io_channels_total=20,source37_zero_import_byte_identical=True,raw36_refused=True,strict_cutoff_candidate=37)
    write(stage/'status.json',status)
    print(json.dumps(dict(exact_receipts=len(sources),portable_projections=len(projections),paired_recovery_targets=4,session_packets=3,cutoff_candidate=37)))
if __name__=='__main__':main()
