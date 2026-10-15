from pathlib import Path
import pcbnew as k,json,hashlib,sys,shutil,importlib.util
sys.path.insert(0,'/workspace/shared/nexus-recovery-evidence');from apply_en_cut import children,field
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');S=R/'routing-continuation/r60-r4-r18';O=R/'routing-continuation/r61-six-clearances';assert not O.exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();P=S/'hardware/nexus-style-fc.kicad_pcb';assert sha(P)=='db583aaa5a1c2ddac33e42a174bd614504dc21b86b953bd0ec93d8360903f4b8';paths=[R/'r58-three-clearances-review/transaction-proposal.json',R/'r59-sda-vsys-review/sda-scl-imu-transaction.json',R/'r59-sda-vsys-review/vsys-transaction.json'];plans=[json.loads(p.read_text()) for p in paths];spec=importlib.util.spec_from_file_location('V',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V);s=P.read_text();nodes={field(s[a:z],'uuid').strip(chr(34)):s[a:z] for a,z in children(s) if s[a:z].startswith(('(segment','(arc','(via'))};rm=[];added=[];matched={}
for plan in plans:
 blocks={x['uuid']:x['source_text'] for x in plan['removed_blocks']} if 'removed_blocks'in plan else plan['remove_expected_blocks']
 for u in plan['removed_uuids']:
  assert V.canonical(V.parse_sexpr(nodes[u]))==V.canonical(V.parse_sexpr(blocks[u])),('Stale donor',u);rm.append(u);matched[u]=nodes[u]
 added+=plan['added_primitives']
assert len(rm)==len(set(rm));assert len({x['uuid'] for x in added})==len(added);assert not {x['uuid'] for x in added}&set(nodes)
for u in rm:s=s.replace(nodes[u],'')
blocks=[]
for d in added:
 if d['kind']=='via':block=f'(via (at {d["at"][0]} {d["at"][1]}) (size {d["diameter"]}) (drill {d["drill"]}) (layers "F.Cu" "B.Cu") (net "{d["net"]}") (uuid "{d["uuid"]}"))'
 else:
  mid=f' (mid {d["mid"][0]} {d["mid"][1]})' if d['kind']=='arc' else '';block=f'({d["kind"]} (start {d["start"][0]} {d["start"][1]}){mid} (end {d["end"][0]} {d["end"][1]}) (width {d["width"]}) (layer "{d["layer"]}") (net "{d["net"]}") (uuid "{d["uuid"]}"))'
 blocks.append(block)
pos=s.rfind(')');s=s[:pos]+'\n'.join(blocks)+'\n'+s[pos:];shutil.copytree(S/'hardware',O/'hardware');OP=O/'hardware/nexus-style-fc.kicad_pcb';OP.write_text(s);shutil.copy2(S/'current-main-binding.json',O/'current-main-binding.json');Q=O/'source-review';Q.mkdir()
for i,p in enumerate(paths):shutil.copy2(p,Q/(str(i)+'-'+p.name))
b=k.LoadBoard(str(OP));uid=lambda o:o.m_Uuid.AsString();objs={**{uid(t):t for t in b.GetTracks()},**{uid(p):p for f in b.GetFootprints() for p in f.Pads()},**{uid(x):x for x in b.GetDrawings() if isinstance(x,k.PCB_SHAPE) and x.GetNetname()}};obs=[]
for d in added:
 o=objs[d['uuid']]
 for u,q in objs.items():
  if u==d['uuid'] or o.GetNetCode()==q.GetNetCode():continue
  for l in b.GetEnabledLayers().CuStack():
   if o.IsOnLayer(l) and q.IsOnLayer(l):
    hit=k.SHAPE.Collide(o.GetEffectiveShape(l),q.GetEffectiveShape(l),127002);hit=hit[0] if isinstance(hit,tuple) else hit
    if hit:obs.append({'new':d['uuid'],'obstacle':u,'net':q.GetNetname(),'layer':b.GetLayerName(l)})
tr={'status':'Bounded six-clearance complete transaction, native checks pending','source_directory':str(S),'source_board_sha256':sha(P),'source_schematic_sha256':sha(S/'hardware/nexus-style-fc.kicad_sch'),'proposal_sources':[{'path':str(p),'sha256':sha(p)} for p in paths],'source_rebase':'Every exact removed native record from r58/r59 matched r60; all accepted USB, R4/R18, buck and previous contacts remain outside the donor set.','removed_uuids':rm,'removed_records':matched,'added_primitives':added,'retained_taper_primitives':json.loads((S/'transaction.json').read_text())['retained_taper_primitives'],'initial_copper_screen_at_0_127002_mm':obs,'stopping_bound':'One exact combined six-error trial. Reject any new/worse native pair, missing complete port or unproved full-width entry. No part, pad, net, footprint, stack, outline, rule or new width exception. Later approved C27/J4 redesign is separate.'};(O/'transaction.json').write_text(json.dumps(tr,indent=2)+'\n');assert not obs,obs;print(json.dumps({'removed':len(rm),'added':len(added),'candidate_pre_refill_sha256':sha(OP),'screen_obstructions':obs}))
