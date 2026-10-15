#!/usr/bin/env python3
"""Pure-source replay, selector, installer and fail-closed negative tests. No KiCad."""
import copy,importlib.util,json,os,pathlib,shutil,subprocess,sys,tempfile
if not __debug__: raise SystemExit('Refusing optimized Python: active guards are required')
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));from prepare_source_variants import prepare,load_design,sha,SOURCE_SHA,BOARD
T=HERE/'source-candidate-final/source-variant-transaction.json';t=json.loads(T.read_text());S=pathlib.Path(t['stage08_source']);A=pathlib.Path(t['stage09_artwork_source']);rows=[]
def record(name,passed=True):assert passed,name;rows.append({'test':name,'pass':True})
def install(C,sha_arg=SOURCE_SHA):
 return subprocess.run([sys.executable,'-B',str(HERE/'install_source_overlay.py'),'--candidate',str(C),'--expected-pcb-sha256',sha_arg,'--expected-transaction-sha256',sha(T)],text=True,capture_output=True)
with tempfile.TemporaryDirectory(prefix='nexus-variant-test-') as td:
 root=pathlib.Path(td);replay=root/'replay';r=prepare(S,A,replay)
 record('full guarded pure-source replay reproduces all eleven overlay hashes',r['overlay_files']==t['overlay_files'])
 record('replay preserves exact stage08 routed board',sha(replay/BOARD)==SOURCE_SHA)
 record('main selector leaves legacy PARTS unchanged',load_design(S,'test_old').PARTS==load_design(replay,'test_new').PARTS)
 d=load_design(replay,'test_selector');x=d.get_main_parts();x[0]['value']='test mutation';record('selector returns independent deep copies',x!=d.get_main_parts() and d.PARTS==load_design(S,'test_old2').PARTS)
 pp={p['ref']:p for p in d.get_main_parts()};record('J3 and J5 retain shared generic library',pp['J3']['fp']==pp['J5']['fp']=='NexusFC:CONN-SMD_4P-P1.25_BM04B-GHS-TBT-LF-SN')
 C=root/'install';C.mkdir()
 for f in ['hardware','tools']:shutil.copytree(S/f,C/f,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 result=install(C,'0'*64);record('installer rejects incorrect board hash before writes',result.returncode!=0 and sha(C/'tools/design.py')==t['source_input_sha256']['tools/design.py'])
 bad=C/'tools/assembly_annotations.py';bad.write_text('obsolete runtime helper\n');result=install(C);record('installer rejects obsolete stage09 helper',result.returncode!=0);bad.unlink()
 design=C/'tools/design.py';original=design.read_bytes();design.write_bytes(original+b'\n# changed\n');result=install(C);record('installer rejects changed source module before writes',result.returncode!=0);design.write_bytes(original)
 variant=C/t['overlay_files'][0]['path'];variant.write_text('unexpected variant');result=install(C);record('installer rejects existing variant before writes',result.returncode!=0);variant.unlink()
 result=install(C);record('guarded overlay installs successfully',result.returncode==0)
 record('installed source equals prepared eleven-file overlay',all(sha(C/x['path'])==x['new_sha256'] for x in t['overlay_files']))
 record('installer never modifies routed PCB',sha(C/BOARD)==SOURCE_SHA)
 result=install(C);record('repeated overlay fails closed',result.returncode!=0)
 try:prepare(S,A,replay)
 except AssertionError:record('preparation rejects existing output')
 else:raise AssertionError('existing output accepted')
 for file in HERE.glob('*.py'):compile(file.read_text(),str(file),'exec')
 record('all helper Python files compile without importing native modules')
(HERE/'source-test-results.json').write_text(json.dumps({'status':'PASS pure source; native checks not run','tests':rows,'source_transaction_sha256':sha(T),'prepare_script_sha256':sha(HERE/'prepare_source_variants.py'),'installer_sha256':sha(HERE/'install_source_overlay.py')},indent=2)+'\n')
print('PASS',len(rows),'pure-source replay/control/negative tests')
