"""Strict physical/source equality for the approved annotation-only successor.
Five explicit footprint IDs, three attributes and seven exact graphic nodes are
allowed; no geometric copper/placement/net/rule exceptions are introduced.
"""
from pathlib import Path
import sys,json,copy,collections,hashlib
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');sys.path.insert(0,str(R/'assembly-annotation-cleanup'));import guarded_cleanup as G
S=R/'mechanical-integration/main-signal-slot-08';A=R/'mechanical-integration/main-assembly-annotation-09';C=Path(sys.argv[1]);M=json.loads(Path(sys.argv[2]).read_text())
# Caller supplies a simple exact {ref: {before: FPID, after: FPID}} mapping.
assert set(M)=={'J4','J6','D1','D2','D3'}
assert G.sha(S/G.BOARD)=='ccd8865f6785fd1cdec0214a08fe409faed4d47bb01e8474f09264ee36acab99'
assert G.sha(A/G.BOARD)=='282e48d05d5adb1a6933b5f29ea851c7452183f508bc3fae8264982b5e1121aa'
s=G.parse((S/G.BOARD).read_text());a=G.parse((A/G.BOARD).read_text());c=G.parse((C/G.BOARD).read_text());sf=G.footprint_map(s);af=G.footprint_map(a);cf=G.footprint_map(c)
assert set(sf)==set(af)==set(cf)
n=copy.deepcopy(c)
for ref,fp in G.footprint_map(n).items():
 if ref in M:
  assert af[ref].items[1]==M[ref]['before'] and fp.items[1]==M[ref]['after'],ref
  fp.items[1]=M[ref]['before']
 else:assert fp.items[1]==af[ref].items[1],ref
assert n.value()==a.value(),'Unexpected saved board change beyond five explicit FPIDs from sealed annotation trial'
assert G.normalized_protected(s)==G.normalized_protected(n),'Unexpected source board change outside exact annotations'
checks={}
for tag in ['segment','arc','via','zone','setup','layers','gr_line','gr_arc','gr_poly']:
 left=[z.value() for z in s.children(tag)];right=[z.value() for z in c.children(tag)];assert left==right,tag;checks[tag]={'count':len(left),'exact':True}
for ref in sf:
 for tag in ['pad','at','layer','property','path','model']:
  assert [z.value() for z in sf[ref].children(tag)]==[z.value() for z in cf[ref].children(tag)],(ref,tag)
for ref in G.ATTR_REFS:assert cf[ref].one('attr').value()==['attr','smd']
for ref in set(sf)-set(G.ATTR_REFS):assert [q.value() for q in sf[ref].children('attr')]==[q.value() for q in cf[ref].children('attr')],ref
for rel in ['hardware/nexus-style-fc.kicad_dru','manufacturing-project.kicad_pro','hardware/nexus-style-fc.kicad_pro','hardware/header-board/nexus-header-board.kicad_pcb','hardware/header-board/nexus-header-board.kicad_sch','hardware/library/NexusFC.3dshapes/nexus-header-board-root-relief-candidate.wrl']:
 assert G.sha(S/rel)==G.sha(C/rel),rel
D=json.loads((C/'native-drc.json').read_text());assert not D['unconnected_items'] and not D['schematic_parity'];assert not [v for v in D['violations'] if v['severity']=='error' or v['type'] in ['lib_footprint_mismatch','track_dangling']]
old=json.loads((A/'native-drc.json').read_text());sig=lambda v:(v['type'],v['severity'],v['description'],tuple(sorted(q['uuid'] for q in v['items'])))
assert collections.Counter(map(sig,D['violations']))==collections.Counter(sig(v) for v in old['violations'] if v['type']!='lib_footprint_mismatch'),'Unexpected diagnostic change'
result={'status':'PASS exact annotation-only physical geometry, return fills, source-net and complete diagnostic comparison','source_board_sha256':G.sha(S/G.BOARD),'source_annotation_board_sha256':G.sha(A/G.BOARD),'candidate_board_sha256':G.sha(C/G.BOARD),'candidate_schematic_sha256':G.sha(C/'hardware/nexus-style-fc.kicad_sch'),'explicit_FPID_mapping':M,'all_pads_parts_properties_nets_placements_models_exact':True,'full_copper_and_all_filled_zone_nodes_exact':True,'native_saved_board_equals_sealed_annotation_trial_except_five_FPID_values':True,'physical_nodes':checks,'counts':dict(collections.Counter(v['type']+':'+v['severity'] for v in D['violations'])),'errors':0,'opens':0,'physical_schematic_parity_findings':0,'library_mismatches':0,'qualification':'Exact physical copper and complete fill equality bind all stage08 finite-contact, return, mask/paste, USB and mechanical proofs. Only assembly type/silk and five source-consistent footprint identifiers change. Manufacturing/assembly/strength/current/SI qualifications remain open.'}
G.write_json(C/'geometry-verification.json',result);print(json.dumps(result,indent=2))
