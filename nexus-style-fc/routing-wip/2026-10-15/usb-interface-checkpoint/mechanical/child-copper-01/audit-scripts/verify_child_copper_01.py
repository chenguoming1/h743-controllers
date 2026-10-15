from pathlib import Path
import pcbnew as k,json,sys,hashlib,collections,importlib.util,math
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'mechanical-integration/child-copper-01';tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);SP=Path(tr['source']['path']);P=O/'hardware/header-board/nexus-header-board.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(SP)==tr['source']['sha256'];spec=importlib.util.spec_from_file_location('V',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V);a,b=[k.LoadBoard(str(p)) for p in [SP,P]];st,ct=[V.parse_sexpr(p.read_text()) for p in [SP,P]];inv=V.invariant_checks(a,b,st,ct);assert inv['status']=='pass',inv
rm=set(tr['removed_or_replaced_uuids']);new=set(tr['replacement_uuids']);uid=lambda o:o.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);ls=list(b.GetEnabledLayers().CuStack());area=lambda p:abs(p.Area())/1e12
for tag in ['segment','arc','via','gr_poly','gr_line','gr_arc','gr_text','group']:
 aa,bb=[V.keyed_nodes(V.children(t,tag)) for t in [st,ct]];assert {u:v for u,v in aa.items() if u not in rm}=={u:v for u,v in bb.items() if u not in new},('Unexpected node change',tag)
at,bt=[{uid(t):t for t in x.GetTracks()} for x in [a,b]];ap,bp=[{uid(p):p for f in x.GetFootprints() for p in f.Pads()} for x in [a,b]];objs={**bt,**bp};assert len(bt)==76 and len([t for t in bt.values() if isinstance(t,k.PCB_VIA)])==3
for r in tr['routes']:
 for d in r['replacement_segments']:
  t=bt[d['uuid']];assert t.GetNetname()==r['net'] and t.GetWidth()==round(r['original_width_mm']*1e6) and b.GetLayerName(t.GetLayer())=='B.Cu';assert xy(t.GetStart())==tuple(d['start']) and xy(t.GetEnd())==tuple(d['end'])
def hit(x,y):
 z=k.SHAPE.Collide(x,y,0);return z[0] if isinstance(z,tuple) else bool(z)
def contacts(x,y):return [l for l in ls if x.IsOnLayer(l) and y.IsOnLayer(l) and hit(x.GetEffectiveShape(l),y.GetEffectiveShape(l))]
def poly(o,l):
 p=k.SHAPE_POLY_SET();o.TransformShapeToPolygon(p,l,0,1,k.ERROR_INSIDE);return p
def overlap(x,y):p=k.SHAPE_POLY_SET(x);p.BooleanIntersection(y);return area(p)
retained=0;external=collections.defaultdict(set);seen=set()
for u,t in at.items():
 for w,q in {**at,**ap}.items():
  pair=tuple(sorted([u,w]))
  if u==w or pair in seen or t.GetNetname()!=q.GetNetname() or not contacts(t,q):continue
  seen.add(pair)
  if u not in rm and w not in rm:assert contacts(objs[u],objs[w]),('original retained contact lost',u,w);retained+=1
  if u in rm and w not in rm:external[t.GetNetname()].add(w)
  if w in rm and u not in rm:external[t.GetNetname()].add(u)
components=[];terminal=[];ports=[]
for r in tr['routes']:
 net=r['net'];ids=[u for u,o in objs.items() if o.GetNetname()==net];adj={u:set() for u in ids}
 for i,u in enumerate(ids):
  for w in ids[:i]:
   if contacts(objs[u],objs[w]):adj[u].add(w);adj[w].add(u)
 seed=r['replacement_segments'][0]['uuid'];reached={seed};todo=[seed]
 while todo:
  u=todo.pop()
  for w in adj[u]-reached:reached.add(w);todo.append(w)
 pp={u for u,p in bp.items() if p.GetNetname()==net};assert pp<=reached and external[net]<=reached;components.append({'net':net,'all_physical_pad_uuids':sorted(pp),'all_pads_physically_connected_without_fills':True,'external_ports':sorted(external[net]),'component_size':len(reached)})
 for u in external[net]:
  q=objs[u];matches=[]
  for d in r['replacement_segments']:
   t=bt[d['uuid']]
   if not contacts(t,q):continue
   if u in bt:
    joint={xy(t.GetStart()),xy(t.GetEnd())}&{xy(q.GetStart()),xy(q.GetEnd())}
    if joint and t.GetWidth()>=q.GetWidth():matches.append({'new_track':uid(t),'exact_centerline_joints':sorted(joint),'width_mm':t.GetWidth()/1e6})
   else:matches.append({'new_track':uid(t),'finite_pad_overlap_mm2':overlap(poly(t,k.B_Cu),poly(q,k.B_Cu))})
  assert matches,(net,u);ports.append({'net':net,'port':u,'proofs':matches})
 p=bp[r['terminal_port']['pad_uuid']];last=bt[r['replacement_segments'][-1]['uuid']];assert xy(last.GetEnd())==xy(p.GetPosition());disk=k.PCB_TRACK(b);disk.SetLayer(k.B_Cu);disk.SetStart(p.GetPosition());disk.SetEnd(p.GetPosition());disk.SetWidth(last.GetWidth());d=poly(disk,k.B_Cu);d.BooleanSubtract(poly(p,k.B_Cu));assert area(d)<1e-10;terminal.append({'net':net,'pad':uid(p),'width_mm':last.GetWidth()/1e6,'endpoint_center':xy(p.GetPosition()),'full_width_round_cap_missing_area_mm2':area(d),'pad_boundary_margin_mm':min(xy(p.GetSize()))/2-last.GetWidth()/2e6})
assert sum(len(x['all_physical_pad_uuids']) for x in components)==22
fills={};ground=[]
for label,board in [('source',a),('candidate',b)]:
 ps={uid(p):p for f in board.GetFootprints() for p in f.Pads()};ground_polys={}
 for l in ls:
  g=k.SHAPE_POLY_SET()
  for z in board.Zones():
   if z.GetNetname()=='GND' and z.IsOnLayer(l) and not z.GetIsRuleArea():g.BooleanAdd(z.GetFilledPolysList(l))
  ground_polys[board.GetLayerName(l)]=g;pad_contacts=[]
  for u,p in ps.items():
   if p.GetNetname()=='GND' and p.IsOnLayer(l):
    ar=overlap(poly(p,l),g)
    if ar>1e-8:pad_contacts.append({'pad':u,'reference':p.GetParentFootprint().GetReference(),'finite_fill_overlap_area_mm2':ar})
  ground.append({'state':label,'layer':board.GetLayerName(l),'filled_GND_area_mm2':area(g),'components':g.OutlineCount(),'finite_ground_pad_contacts':pad_contacts})
 fills[label]=ground_polys
changes=[]
for l in fills['source']:
 aa,bb=fills['source'][l],fills['candidate'][l];c=k.SHAPE_POLY_SET(aa);c.BooleanSubtract(bb);d=k.SHAPE_POLY_SET(bb);d.BooleanSubtract(aa);changes.append({'layer':l,'removed_area_mm2':area(c),'added_area_mm2':area(d)})
assert any(x['finite_ground_pad_contacts'] for x in ground if x['state']=='candidate')
for f in (S/'hardware/header-board').iterdir():
 if f.is_file() and f.suffix not in ['.kicad_pcb','.kicad_prl','.kicad_pro']:assert sha(f)==sha(O/'hardware/header-board'/f.name)
oldpro=json.loads((S/'hardware/header-board/nexus-header-board.kicad_pro').read_text());newpro=json.loads((O/'hardware/header-board/nexus-header-board.kicad_pro').read_text());normalized=json.loads(json.dumps(newpro))
for t in normalized['board']['design_settings']['teardrop_parameters']:assert t.pop('td_enabled') is False
for n in ['net_colors','netclass_assignments']:assert oldpro['net_settings'][n] is None and normalized['net_settings'][n]=={};normalized['net_settings'][n]=None
assert normalized==oldpro
import xml.etree.ElementTree as ET
xml=ET.parse(O/'final-netlist.xml');nmap={(n.attrib['ref'],n.attrib['pin']):net.attrib['name'] for net in xml.findall('./nets/net') for n in net.findall('node')};pmap={(p.GetParentFootprint().GetReference(),p.GetNumber()):p.GetNetname() for p in bp.values()};assert pmap=={x:y for x,y in nmap.items() if x in pmap};assert not set(nmap)-set(pmap)
audit={'status':'PASS exact six-donor/nine-segment child transaction, full-width ports and all 22 affected-net pads connected without relying on fills','source_board_sha256':sha(SP),'candidate_board_sha256':sha(P),'invariants':inv,'unchanged_original_direct_contacts_preserved':retained,'complete_net_components':components,'original_external_contact_proofs':ports,'full_width_terminal_caps':terminal,'actual_refilled_ground':ground,'source_to_candidate_fill_changes':changes,'native_netlist_pin_map_count':len(pmap),'project_serialization_only':{'source_sha256':sha(S/'hardware/header-board/nexus-header-board.kicad_pro'),'saved_sha256':sha(O/'hardware/header-board/nexus-header-board.kicad_pro'),'only_changes':'Three td_enabled:false default keys and empty net_colors/netclass_assignments dictionaries replacing null. Every other project node including all rules/severities/netclass floors is exact.'},'qualification':'Nominal copper and actual fill topology only; header fit/strength/assembly and main-board mechanical conflicts remain open. No claimed manufacturing release.'};(O/'geometry-verification.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps({k:audit[k] for k in ['status','source_board_sha256','candidate_board_sha256','unchanged_original_direct_contacts_preserved','source_to_candidate_fill_changes']},indent=2))
