#!/usr/bin/env python3
"""Run current static checks with output redirected only to independent-review.
Mutations are in-memory; candidate files are never changed."""
import sys,json,hashlib,copy,contextlib,io
from pathlib import Path
sys.dont_write_bytecode=True
root=Path('/workspace/scratch/8a35c1f26232/nexus-header-redesign-20261015');c=root/'candidate-01/nexus-style-fc';review=root/'independent-review'
sys.path.insert(0,str(c/'tools'));import sexpr as s;import apply_header_interface as a
anchors=json.loads((c/'tools/header_interface_r54_anchors.json').read_text());result={}
for which,rel in [('main','hardware/nexus-style-fc.kicad_pcb'),('child','hardware/header-board/nexus-header-board.kicad_pcb')]:
 raw=(root/'rollback-r54-source/nexus-style-fc'/rel).read_text();b=s.parse(raw);fp=next(f for f in s.find(b,'footprint') if a.ref(f)=='J1');p=s.find(fp,'pad')[0];s.find(p,'at')[0][1]='777'
 try:a.guard(s.dump(b),which,anchors);rejected=False
 except AssertionError:rejected=True
 result[which+'_mutated_anchor_rejected_normal_python']=rejected
for t in ('transaction-r54-01','transaction-r54-02-hardened'):
 manifest=json.loads((root/t/'source-manifest.json').read_text())
 result[t]={
 'source_manifest_hashes_match':{k:hashlib.sha256(Path(v['path']).read_bytes()).hexdigest()==v['sha256'] for k,v in manifest['sources'].items()},
 'rollback_bytes_match_sources':{k:(root/t/'rollback'/Path(v['path']).name).read_bytes()==Path(v['path']).read_bytes() for k,v in manifest['sources'].items()},
 'implementation_bindings_match_current':{k:hashlib.sha256((c/k).read_bytes()).hexdigest()==v for k,v in manifest.get('implementation_sha256',{}).items()},
 'main_equals_candidate':(root/t/'nexus-style-fc.kicad_pcb').read_bytes()==(c/'hardware/nexus-style-fc.kicad_pcb').read_bytes(),
 'child_equals_candidate':(root/t/'header-board/nexus-header-board.kicad_pcb').read_bytes()==(c/'hardware/header-board/nexus-header-board.kicad_pcb').read_bytes()}
for optimization in (1,2):
 ns={'__file__':str(c/'tools/apply_header_interface.py'),'__name__':'review_optimized_guard'}
 try:exec(compile((c/'tools/apply_header_interface.py').read_text(),str(c/'tools/apply_header_interface.py'),'exec',optimize=optimization),ns);refused=False
 except SystemExit as exc:refused=str(exc)
 result[f'optimization_{optimization}_refused_before_work']=refused
# Redirect this checker's report writes into the only authorized review directory.
checker=c/'tools/check_header_interface_static.py';code=checker.read_text();old="OUT=ROOT/'docs/header-interface-candidate';OUT.mkdir(parents=True,exist_ok=True)";assert code.count(old)==1
code=code.replace(old,f"OUT=Path({str(review/'rechecked-static')!r});OUT.mkdir(parents=True,exist_ok=True)")
with contextlib.redirect_stdout(io.StringIO()):exec(compile(code,str(checker),'exec'),{'__file__':str(checker),'__name__':'independent_checker_recheck'})
result['hardened_static_checker_passes']=True
# Verify changed native geometry is actually rejected. Intercept reading only.
original_read=Path.read_text
for target,label in [(c/'hardware/nexus-style-fc.kicad_pcb','main_deleted_cutout_edge'),(c/'hardware/header-board/nexus-header-board.kicad_pcb','child_shifted_root_arc')]:
 board=s.parse(original_read(target))
 if label.startswith('main'):
  fp=next(f for f in s.find(board,'footprint') if a.ref(f)=='J1');removed=next(n for n in fp if isinstance(n,list) and n[0]=='fp_line' and s.text(s.find(n,'layer')[0][1])=='Edge.Cuts');fp.remove(removed)
 else:
  arc=next(n for n in s.find(board,'gr_arc') if float(s.find(n,'start')[0][2])>108);s.find(arc,'mid')[0][2]=str(float(s.find(arc,'mid')[0][2])-.01)
 tampered=s.dump(board)
 def hooked(self,*args,**kwargs):return tampered if self==target else original_read(self,*args,**kwargs)
 Path.read_text=hooked
 try:
  with contextlib.redirect_stdout(io.StringIO()):exec(compile(code,str(checker),'exec'),{'__file__':str(checker),'__name__':'independent_checker_negative'})
  rejected=False
 except AssertionError:rejected=True
 finally:Path.read_text=original_read
 result[label+'_rejected']=rejected
(review/'guard-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
