from pathlib import Path
import sys,json,shutil,subprocess,copy
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');sys.path.insert(0,str(R/'assembly-annotation-cleanup'));import guarded_cleanup as G
L=R/'mechanical-integration';S=L/'main-signal-slot-08';A=L/'main-assembly-annotation-09';O=L/'main-assembly-annotation-10';M=R/'assembly-annotation-cleanup/local-variant-remedy';assert not O.exists()
assert G.sha(S/G.BOARD)=='ccd8865f6785fd1cdec0214a08fe409faed4d47bb01e8474f09264ee36acab99';assert G.sha(A/G.BOARD)=='282e48d05d5adb1a6933b5f29ea851c7452183f508bc3fae8264982b5e1121aa'
T=M/'source-candidate-final/source-variant-transaction.json';assert G.sha(T)=='109a1aeb7c6161543404f984fa99586dade230cd1c30ae8c4c3e93974c5bb365';assert G.sha(M/'install_source_overlay.py')=='0654c7b048d8cea2a0b09c66dea287e7f666f97a3bf64bc5ddf2278115cdb9f7'
pre=json.loads((L/'annotation-variant-preflight-10-fixed/verification.json').read_text());assert pre['status'].startswith('PASS')
mapping=json.loads((M/'fpid-mapping.json').read_text());assert G.sha(M/'fpid-mapping.json')==pre['mapping_sha256'];before=(A/G.BOARD).read_text();root=G.parse(before);fps=G.footprint_map(root);sf=G.footprint_map(G.parse((S/G.BOARD).read_text()));edits=[]
for ref,row in mapping.items():
 f=fps[ref];assert G.csha(f.value())==row['stage09_footprint_canonical_sha256'];assert G.csha(sf[ref].value())==row['stage08_footprint_canonical_sha256'];assert f.items[1]==row['old_fpid'];old=G.raw(before,f);new=G.replace_once(old,'(footprint '+json.dumps(row['old_fpid']),'(footprint '+json.dumps(row['new_fpid']));edits.append((f.start,f.end,new))
after=G.apply_replacements(before,edits);check=G.parse(after);n=copy.deepcopy(check)
for ref,row in mapping.items():G.footprint_map(n)[ref].items[1]=row['old_fpid']
assert n.value()==root.value() and G.normalized_protected(n)==G.normalized_protected(G.parse((S/G.BOARD).read_text()))
O.mkdir()
for d in ['hardware','tools']:shutil.copytree(S/d,O/d,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for f in ['manufacturing-project.kicad_pro','current-main-binding.json','child-model-binding.json']:shutil.copy2(S/f,O/f)
(O/G.BOARD).write_text(after);pcbhash=G.sha(O/G.BOARD)
p=subprocess.run([sys.executable,str(M/'install_source_overlay.py'),'--candidate',str(O),'--expected-pcb-sha256',pcbhash,'--expected-transaction-sha256',G.sha(T)],text=True,capture_output=True);(O/'source-overlay-install.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
shutil.copy2(T,O/'source-variant-transaction.json');shutil.copy2(M/'fpid-mapping.json',O/'source-fpid-mapping.json');G.write_json(O/'fpid-mapping.json',{r:{'before':q['old_fpid'],'after':q['new_fpid']} for r,q in mapping.items()});shutil.copytree(L/'annotation-variant-preflight-10-fixed',O/'native-library-preflight');shutil.copy2(A/'annotation-transaction.json',O/'original-annotation-transaction.json')
G.write_json(O/'annotation-integration-transaction.json',{'status':'PREPARED isolated source-consistent annotation successor; native acceptance pending','source_board_sha256':G.sha(S/G.BOARD),'artwork_board_sha256':G.sha(A/G.BOARD),'candidate_pre_native_sha256':pcbhash,'source_overlay_sha256':G.sha(T),'source_fpid_mapping_sha256':G.sha(M/'fpid-mapping.json'),'candidate_schematic_sha256':G.sha(O/'hardware/nexus-style-fc.kicad_sch'),'geometry_scope':'No copper, pad, net, part, position, model, rule or filled-zone change; approved three attributes/seven graphic nodes plus exactly five footprint IDs only.','main_only_source_overlay':json.loads(T.read_text())['overlay_files']});print(p.stdout);print('prepared PCB',pcbhash)
