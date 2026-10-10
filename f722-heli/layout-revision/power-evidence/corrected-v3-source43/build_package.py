#!/usr/bin/env python3
"""Build local evidence from a completed exact job; never runs a numerical solver."""
import argparse,gzip,hashlib,io,json,shutil,tarfile
from pathlib import Path
from compact_report import compact

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def dump(path,obj):path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def compress(src,dst):
    with Path(src).open('rb') as f,Path(dst).open('wb') as o,gzip.GzipFile(filename='',mode='wb',fileobj=o,mtime=0,compresslevel=6) as g:shutil.copyfileobj(f,g,1048576)
def main():
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--recovery',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parent; w=a.workspace.resolve(); impl=w/'power-terminal-correction-v3';job=impl/'job-candidate43'
    if (root/'MANIFEST.json').exists():raise SystemExit('Refusing to overwrite a sealed package')
    for x in ['runtime','provenance','evidence']: (root/x).mkdir(exist_ok=True)
    summary=json.loads((job/'combined-summary.json').read_text());launch=json.loads((job/'launch-receipt.json').read_text())
    if sha(job/'released/result.json')!=launch['result_sha256'] or sha(job/'combined-summary.json')!=launch['summary_sha256']:raise ValueError('Completed output identity changed')
    for f in (job/'tools').glob('*.py'):shutil.copyfile(f,root/'runtime'/f.name)
    for name in ['plan_power_revalidation.py','build_model_inputs.py','exact_native_contours.py']:shutil.copyfile(impl/name,root/'runtime'/name)
    for name in ['README.md','MODEL-REVIEW.json','MANIFEST.json','test-result.json','test-run.txt','implementation.diff','implementation-v2-v3.diff','historical-runtime-sha256.json']:
        shutil.copyfile(impl/name,root/'provenance'/name)
    for name in ['plan-candidate43.json','compiler-settings.json']:shutil.copyfile(impl/name,root/'provenance'/name)
    for name in ['launch-receipt.json','stage-receipt.json','preflight.json']:shutil.copyfile(job/name,root/'provenance'/name)
    model=json.loads((impl/'MODEL-REVIEW.json').read_text())
    evidence=[]
    for rel,expected in model['evidence_sha256'].items():
        src=w/rel
        if sha(src)!=expected:raise ValueError('Changed model evidence '+rel)
        target=root/'evidence'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
        evidence.append(dict(original=rel,package=str(target.relative_to(root)),sha256=expected))
    dump(root/'evidence/index.json',evidence)
    compress(job/'combined-summary.json',root/'combined-summary.json.gz')
    dump(root/'compact-report.json',compact(summary,launch))
    plan=json.loads((impl/'plan-candidate43.json').read_text())
    dump(root/'runtime/original-environment.json',plan['execution_runtime'])
    (root/'runtime/requirements.txt').write_text('\n'.join(k+'=='+v['version'] for k,v in plan['execution_runtime']['packages'].items())+'\n')
    members={}
    # Complete stage inventory and released inputs retain original relative layout.
    for f in sorted(job.rglob('*')):
        rel=f.relative_to(job)
        if not f.is_file() or rel.parts[0]=='mesh-cache' or rel.as_posix() in ['released/result.json','combined-summary.json'] or '__pycache__' in rel.parts:continue
        members['job/'+rel.as_posix()]=f
    # Source-only receipts outside the freeze are retained to verify original source inventory.
    for rel,expected in plan['source_files_sha256'].items():
        src=Path(plan['source'])/rel
        if sha(src)!=expected:raise ValueError('Changed source '+rel)
        members['source/'+rel]=src
    members['source/poses-native.json']=Path(plan['inputs']['poses']['path'])
    inventory={n:dict(sha256=sha(f),bytes=f.stat().st_size) for n,f in members.items()}
    dump(root/'payload-inventory.json',inventory)
    with (root/'frozen-inputs.tar.gz').open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as gz,tarfile.open(fileobj=gz,mode='w|') as tar:
        first_by_hash={}
        for name,src in sorted(members.items()):
            info=tarfile.TarInfo(name);info.mode=0o644;info.mtime=0;digest=inventory[name]['sha256']
            if digest in first_by_hash:
                info.type=tarfile.LNKTYPE;info.linkname=first_by_hash[digest];tar.addfile(info)
            else:
                data=src.read_bytes();info.size=len(data);tar.addfile(info,io.BytesIO(data));first_by_hash[digest]=name
    a.recovery.mkdir(parents=True,exist_ok=True); recovery=a.recovery/'result.json.gz'
    if not recovery.exists():compress(job/'released/result.json',recovery)
    h=hashlib.sha256();size=0
    with gzip.open(recovery,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b);size+=len(b)
    if h.hexdigest()!=launch['result_sha256']:raise ValueError('Recovery decompression hash mismatch')
    recovery_receipt=dict(schema='f722-exact-raw-recovery/v1',compressed_filename='result.json.gz',compressed_sha256=sha(recovery),compressed_bytes=recovery.stat().st_size,raw_sha256=h.hexdigest(),raw_bytes=size,verified_decompression=True,local_only=True)
    dump(a.recovery/'RECOVERY.json',recovery_receipt);dump(root/'provenance/raw-recovery-identity.json',recovery_receipt)
    print(json.dumps(dict(package=str(root),payload_bytes=(root/'frozen-inputs.tar.gz').stat().st_size,payload_members=len(members),recovery=str(recovery),recovery_bytes=recovery.stat().st_size)))
if __name__=='__main__':main()
