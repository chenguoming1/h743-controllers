#!/usr/bin/env python3
"""Read-only candidate02 delta validation; no native runtime."""
import sys,json,copy,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
R=Path('/workspace/scratch/8a35c1f26232/nexus-header-redesign-20261015');C=R/'candidate-02/nexus-style-fc';O=R/'rollback-r54-source/nexus-style-fc';C1=R/'candidate-01/nexus-style-fc';T=R/'transaction-r54-03-candidate02'
sys.path.insert(0,str(C/'tools'));import sexpr as s;import apply_header_interface as tx

def one(n,k):return s.find(n,k)[0]
def keepout(b):return {tx.uid(z):z for z in s.find(b,'zone') if s.find(z,'keepout')}
def bbox(z):
 pts=s.find(one(one(z,'polygon'),'pts'),'xy');p=[list(map(float,v[1:3])) for v in pts]
 return [min(x for x,y in p),min(y for x,y in p),max(x for x,y in p),max(y for x,y in p)]
old=s.parse((O/'hardware/nexus-style-fc.kicad_pcb').read_text());new=s.parse((C/'hardware/nexus-style-fc.kicad_pcb').read_text());prior=s.parse((C1/'hardware/nexus-style-fc.kicad_pcb').read_text());olds,news=keepout(old),keepout(new)
r={'same_keepout_uuids':olds.keys()==news.keys(),'keepouts':{},'candidate01_to02':{}}
for u in olds:
 a,b=copy.deepcopy(olds[u]),copy.deepcopy(news[u]);aa,bb=bbox(a),bbox(b)
 r['keepouts'][u]={'source_bounds':aa,'candidate_bounds':bb,'source_permissions':one(a,'keepout'),'candidate_permissions':one(b,'keepout'),'permissions_exact':one(a,'keepout')==one(b,'keepout'),'candidate_layers':one(b,'layers'),'lateral_bounds_exact':aa[0]==bb[0] and aa[2]==bb[2],'expected_y_bounds':bb[1]==101.05 and bb[3]==103.75,'new_encloses_old':bb[0]<=aa[0] and bb[1]<=aa[1] and bb[2]>=aa[2] and bb[3]>=aa[3]}
 a.remove(one(a,'polygon'));b.remove(one(b,'polygon'));r['keepouts'][u]['everything_except_polygon_exact']=a==b
# Ensure candidate02 changes exactly J1 attr and two keepout polygons from candidate01.
patched=copy.deepcopy(prior);j=next(f for f in s.find(patched,'footprint') if tx.ref(f)=='J1');one(j,'attr')[1:]=['smd']
for z in s.find(patched,'zone'):
 if s.find(z,'keepout'):
  a=one(z,'polygon');a[:]=copy.deepcopy(one(news[tx.uid(z)],'polygon'))
r['candidate01_to02']['only_J1_attr_and_two_keepout_polygons_changed']=patched==new
r['candidate01_to02']['child_board_byte_identical']=(C1/'hardware/header-board/nexus-header-board.kicad_pcb').read_bytes()==(C/'hardware/header-board/nexus-header-board.kicad_pcb').read_bytes()
r['candidate01_to02']['main_J1_attr']=one(next(f for f in s.find(new,'footprint') if tx.ref(f)=='J1'),'attr')
m=json.loads((T/'source-manifest.json').read_text());r['source_bindings']={k:hashlib.sha256(Path(v['path']).read_bytes()).hexdigest()==v['sha256'] for k,v in m['sources'].items()};r['implementation_bindings']={k:hashlib.sha256((C/k).read_bytes()).hexdigest()==v for k,v in m['implementation_sha256'].items()}
r['transaction_outputs_match']={rel:(T/rel).read_bytes()==(C/'hardware'/rel).read_bytes() for rel in ('nexus-style-fc.kicad_pcb','header-board/nexus-header-board.kicad_pcb','header-board/nexus-header-board.kicad_sch')}
anchors=json.loads((C/'tools/header_interface_r54_anchors.json').read_text())
r['negative_source_keepout_tests']={}
for key,mutate in [('boundary',lambda z:one(one(z,'polygon'),'pts')[1].__setitem__(1,'100.09')),('permissions',lambda z:one(one(z,'keepout'),'tracks').__setitem__(1,'allowed'))]:
 b=copy.deepcopy(old);mutate(next(z for z in s.find(b,'zone') if s.find(z,'keepout')))
 try:tx.guard(s.dump(b),'main',anchors);fail=False
 except AssertionError:fail=True
 r['negative_source_keepout_tests'][key+'_rejected']=fail
print(json.dumps(r,indent=2))
