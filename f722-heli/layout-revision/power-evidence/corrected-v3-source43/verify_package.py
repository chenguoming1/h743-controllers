#!/usr/bin/env python3
"""Verify/extract the portable packet. Optional preflight and raw replay never solve."""
import argparse,gzip,hashlib,json,os,shutil,subprocess,sys,tarfile,tempfile
from pathlib import Path,PurePosixPath
from compact_report import compact

BOARD='1ee7174a578dffe4d5ef3ae8b39d8dc88f28b80395539263a65f23be234c21e6'
RAW='1466a094fc40cfbed24fbda76d5445bad9c06d951389e2440ed6b0cd3b13bac9'
SUMMARY='030fa2ae528c45d9f0207eac4fb9b93c74cc84cf3296035f995d869bf0409550'
def require(condition,message):
    if not condition:raise ValueError(message)
def digest_stream(f):
    h=hashlib.sha256();n=0
    for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
    return h.hexdigest(),n
def sha(p):
    with Path(p).open('rb')as f:return digest_stream(f)[0]
def load(p):return json.loads(Path(p).read_text())
def safe_name(name):
    p=PurePosixPath(name)
    require(not p.is_absolute() and all(x not in ['','..']for x in p.parts),'Unsafe archive member '+name)
    return p

def extract(root,destination,inventory):
    require(not destination.exists(),'Extraction target already exists; preserve it')
    destination.mkdir(parents=True);seen=set()
    with tarfile.open(root/'frozen-inputs.tar.gz','r:gz')as tar:
        for member in tar:
            safe_name(member.name);require(member.name in inventory and member.name not in seen,'Unexpected or duplicate archive member '+member.name)
            target=destination/member.name;target.parent.mkdir(parents=True,exist_ok=True)
            if member.islnk():
                safe_name(member.linkname);require(member.linkname in seen,'Hardlink must refer to a preceding verified member')
                shutil.copyfile(destination/member.linkname,target)
            else:
                require(member.isfile(),'Only files and verified prior hardlinks are permitted')
                with tar.extractfile(member)as f,target.open('xb')as out:shutil.copyfileobj(f,out,1048576)
            expected=inventory[member.name]
            require(target.stat().st_size==expected['bytes'] and sha(target)==expected['sha256'],'Payload mismatch '+member.name)
            seen.add(member.name)
    require(seen==set(inventory),'Incomplete payload')
    return len(seen)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--extract',type=Path);p.add_argument('--preflight',action='store_true');p.add_argument('--raw-result',type=Path,help='Original result.json or exact recovery result.json.gz; hash/replay it, without solving');a=p.parse_args()
    require(not sys.flags.optimize,'Do not run with -O: preserved runtime assertions must remain active')
    root=Path(__file__).resolve().parent;manifest=load(root/'MANIFEST.json')
    for rel,entry in manifest['files'].items():
        f=root/rel;require(f.is_file()and f.stat().st_size==entry['bytes']and sha(f)==entry['sha256'],'Package file mismatch '+rel)
    with gzip.open(root/'combined-summary.json.gz','rb')as f:b=f.read()
    require(hashlib.sha256(b).hexdigest()==SUMMARY,'Combined summary identity mismatch');summary=json.loads(b)
    require(summary['board_sha256']==BOARD and summary['result_sha256']==RAW,'Wrong candidate or result')
    launch=load(root/'provenance/launch-receipt.json');require(compact(summary,launch)==load(root/'compact-report.json'),'Compact report is not the exact deterministic projection')
    with tempfile.TemporaryDirectory(prefix='f722-evidence-verify-')as temporary:
        temp=Path(temporary);destination=a.extract.resolve()if a.extract else temp/'payload'
        count=extract(root,destination,load(root/'payload-inventory.json'));job=destination/'job';freeze_path=job/'released/freeze.json';freeze=load(freeze_path);ledger=load(job/'released/ledger.json')
        require(ledger['freeze_manifest_sha256']==sha(freeze_path)==launch['freeze_sha256'],'Freeze binding mismatch')
        require(sha(job/'released/ledger.json')==launch['ledger_sha256'],'Ledger binding mismatch')
        for key,spec in freeze['files'].items():
            path=(freeze_path.parent/spec['path']).resolve();require(path.is_relative_to(destination.resolve()),'Freeze dependency escapes payload '+key)
            require(path.is_file()and sha(path)==spec['sha256'],'Missing/changed frozen dependency '+key)
        require(len(freeze['files'])==40,'Unexpected dependency count')
        for name,expected in freeze['analysis_source_sha256'].items():require(sha(job/'released/solver-source'/name)==expected,'Changed solver source '+name)
        stage=load(root/'provenance/stage-receipt.json')
        require(sha(job/'stage-receipt.json')==launch['stage_receipt_sha256'],'Stage receipt identity mismatch')
        for rel,expected in stage['files_sha256'].items():require(sha(job/rel)==expected,'Incomplete stage snapshot '+rel)
        plan=load(root/'provenance/plan-candidate43.json');require(sha(root/'provenance/plan-candidate43.json')==launch['plan_sha256'],'Plan identity mismatch')
        for rel,expected in plan['source_files_sha256'].items():require(sha(destination/'source'/rel)==expected,'Incomplete source inventory '+rel)
        for rel,expected in plan['runtime_source_sha256'].items():require(sha(root/'runtime'/rel)==expected,'Changed copied runtime '+rel)
        for src in load(root/'evidence/index.json'):require(sha(root/src['package'])==src['sha256'],'Changed model evidence')
        sys.path.insert(0,str(root/'runtime'));from model_contract import check_ledger
        check_ledger(ledger,ledger['model_contract'],full=True)
        result=dict(status='PASS: packet integrity and deterministic summary projection',board_sha256=BOARD,raw_result_sha256=RAW,summary_sha256=SUMMARY,payload_files=count,freeze_dependencies_checked=40,stage_files_checked=len(stage['files_sha256']),source_files_checked=len(plan['source_files_sha256']),case_definitions_checked=len(ledger['cases']),raw_result_replay=False,heavy_numerical_run=False,preflight=False)
        env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
        if a.preflight:
            cmd=[sys.executable,'-B',str(job/'released/solver-source/validate_static.py'),'--freeze',str(freeze_path),'--ledger',str(job/'released/ledger.json'),'--out',str(temp/'preflight.json')]
            cp=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=90)
            require(cp.returncode==0,'Mesh-free preflight refused: '+cp.stdout+cp.stderr)
            result['preflight']=load(temp/'preflight.json')
        if a.raw_result:
            raw=a.raw_result.resolve()
            if raw.suffix=='.gz':
                target=temp/'result.json'
                with gzip.open(raw,'rb')as f,target.open('xb')as out:shutil.copyfileobj(f,out,1048576)
                raw=target
            require(sha(raw)==RAW,'Raw result identity mismatch')
            cmd=[sys.executable,'-B',str(root/'runtime/summarize_combined_pilot.py'),'--result',str(raw),'--freeze',str(freeze_path),'--ledger',str(job/'released/ledger.json'),'--out',str(temp/'replayed-summary.json')]
            cp=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=180)
            require(cp.returncode==0,'Raw summary replay refused: '+cp.stdout+cp.stderr)
            require(sha(temp/'replayed-summary.json')==SUMMARY,'Raw replay changed the exact summary')
            result['raw_result_replay']=True
        print(json.dumps(result,indent=2))
if __name__=='__main__':
    try:main()
    except Exception as exc:raise SystemExit('REFUSED: '+str(exc))
