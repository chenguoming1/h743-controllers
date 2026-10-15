from pathlib import Path
import json,sys,copy,hashlib
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sys.path.insert(0,str(R/'latest-main/nexus-style-fc/tools'));import validate_nexus_reroute as V
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();P=O/'hardware/nexus-style-fc.kicad_pcb';assert sha(S/'hardware/nexus-style-fc.kicad_pcb')==tr['source_board_sha256'];a,b=[V.parse_sexpr((d/'hardware/nexus-style-fc.kicad_pcb').read_text()) for d in [S,O]];rm=set(tr['removed_uuids']);adds={r['uuid']:r for r in tr['added_primitives']};moves={r['uuid']:r for r in tr['moved_vias']};norm=copy.deepcopy(b)
for n in V.children(norm,'via'):
 u=V.source_uuid(n)
 if u in moves:
  pos=V.children(n,'at')[0];assert list(map(float,pos[1:]))==moves[u]['to'];pos[1:]=[str(x) for x in moves[u]['from']]
for tag in ['segment','arc','via','gr_poly','gr_line','gr_arc','gr_text','group']:
 aa,bb=[V.keyed_nodes(V.children(t,tag)) for t in [a,norm]];assert {u:n for u,n in aa.items() if u not in rm}=={u:n for u,n in bb.items() if u not in adds},('Unexpected retained copper or drawings delta',tag)
af,bf=[{V.source_uuid(f):f for f in V.children(t,'footprint')} for t in [a,b]];c27='795bfe33-ea30-466e-973a-9e365271c33f';d5='4de4cc0b-35ff-4573-b4d0-cdb0a7b77e62';c31='c78ee91d-4dd0-53ff-a419-47fdc6ec662c';assert set(bf)-set(af)=={c31} and not set(af)-set(bf)
for u in af:
 if u==c27:continue
 c=copy.deepcopy(bf[u])
 if u==d5:
  at=V.children(c,'at')[0];assert list(map(float,at[1:]))==[102.28,126.18,180];at[2]='125.78'
 assert V.canonical(af[u])==V.canonical(c),('Unapproved original footprint delta',u)
for tag in ['layers','setup','general','zone']:
 if tag=='zone':assert V.zone_definitions(a)==V.zone_definitions(b)
 else:assert V.canonical(V.children(a,tag))==V.canonical(V.children(b,tag))
# Every original pad UUID/net survives; exactly two C31 nodes are added.
def pads(root):
 return {V.source_uuid(p):V.canonical(V.children(p,'net')) for f in V.children(root,'footprint') for p in V.children(f,'pad')}
ap,bp=map(pads,[a,b]);assert set(bp)-set(ap)=={'c93fcd51-5f39-5fd3-92e1-b34e74c41795','bc8e3c02-8f7b-5051-a554-14638d99f653'} and all(bp[u]==n for u,n in ap.items())
# Native UUID uniqueness is checked recursively.
def ids(t):
 out=[]
 if isinstance(t,list):
  if t and V.atom(t[0])=='uuid':out.append(V.atom(t[1]))
  for q in t:out.extend(ids(q))
 return out
uu=ids(b);assert len(set(uu))==len(uu)
out={'status':'PASS: exact retained copper, original pad UUID/net map, all original footprints except exact C27/D5 scope, stack/outline/rules; exactly one C31 footprint and two pins added','source_sha256':tr['source_board_sha256'],'candidate_sha256':sha(P),'original_pad_nodes':len(ap),'final_pad_nodes':len(bp),'unique_uuids':len(uu),'candidate_schema_sha256':sha(O/'hardware/nexus-style-fc.kicad_sch')};(O/'source-scope-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
