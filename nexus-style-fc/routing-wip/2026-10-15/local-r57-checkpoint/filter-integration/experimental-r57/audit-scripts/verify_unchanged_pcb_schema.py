from pathlib import Path
import pcbnew as k,json,hashlib,sys,importlib.util,collections,xml.etree.ElementTree as ET,re
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();P=O/'hardware/nexus-style-fc.kicad_pcb';SP=S/'hardware/nexus-style-fc.kicad_pcb';assert sha(SP)==tr['source_board_sha256'];assert sha(O/'hardware/nexus-style-fc.kicad_sch')==tr['candidate_schema_sha256'];spec=importlib.util.spec_from_file_location('validator',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
a,b=[k.LoadBoard(str(p)) for p in [SP,P]];st,ct=[V.parse_sexpr(p.read_text()) for p in [SP,P]];inv=V.invariant_checks(a,b,st,ct);assert inv['status']=='pass',inv
for tag in ['segment','arc','via']:assert V.keyed_nodes(V.children(st,tag))==V.keyed_nodes(V.children(ct,tag)),tag
uid=lambda x:x.m_Uuid.AsString();at={uid(t):t for t in a.GetTracks()};bt={uid(t):t for t in b.GetTracks()};ap={uid(p):p for f in a.GetFootprints() for p in f.Pads()};bp={uid(p):p for f in b.GetFootprints() for p in f.Pads()};ls=list(b.GetEnabledLayers().CuStack())
def hit(x,y):
 q=x.Collide(y,0);return q[0] if isinstance(q,tuple) else bool(q)
conn=a.GetConnectivity();seen=set();retained=[]
for u,t in at.items():
 for q in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
  w=uid(q);obj=at.get(w) or ap.get(w);key=tuple(sorted([u,w]));layers=[l for l in ls if t.IsOnLayer(l) and obj.IsOnLayer(l) and hit(t.GetEffectiveShape(l),obj.GetEffectiveShape(l))]
  if u==w or key in seen or not layers:continue
  seen.add(key);new=bt.get(w) or bp.get(w);assert any(hit(bt[u].GetEffectiveShape(l),new.GetEffectiveShape(l)) for l in layers),key;retained.append(key)
pid='5f922c73-82b6-4073-8e98-d520c70499ca';p=bp[pid];assert p.GetNetname()=='unconnected-(U10-EN-Pad3)';contacts=[]
for l in ls:
 if not p.IsOnLayer(l):continue
 for u,q in {**bt,**bp}.items():
  if u!=pid and q.IsOnLayer(l) and hit(p.GetEffectiveShape(l),q.GetEffectiveShape(l)):contacts.append(u)
 for z in b.Zones():
  if z.IsOnLayer(l) and not z.GetIsRuleArea() and hit(p.GetEffectiveShape(l),z.GetFilledPolysList(l)):contacts.append(uid(z))
assert not contacts
x,y=[json.loads((d/'native-drc.json').read_text()) for d in [S,O]];assert x['included_severities']==y['included_severities'] and x['ignored_checks']==y['ignored_checks'] and y['kicad_version']=='10.0.7';assert not y['unconnected_items'] and not y['schematic_parity'];sig=lambda z:(z['type'],z['severity'],tuple(sorted(i['uuid'] for i in z['items'])),z['description']);assert collections.Counter(map(sig,x['violations']))==collections.Counter(map(sig,y['violations']))
e=json.loads((O/'native-erc.json').read_text());assert not any(z['violations'] for z in e['sheets'])
def pinmap(p):
 root=ET.parse(p).getroot();r={};detail={}
 for n in root.findall('nets/net'):
  for p in n.findall('node'):
   key=(p.get('ref'),p.get('pin'));assert key not in r;r[key]=n.get('name');detail[key]={'net':n.get('name'),'node':p.attrib,'node_count':len(n.findall('node'))}
 return r,detail
pm,pd=pinmap(O/'final-netlist.xml');old,_=pinmap(S/'final-netlist.xml');assert pm==old and len(pm)==347;boardpins={(f.GetReference(),p.GetNumber()):p.GetNetname().replace('{slash}','/') for f in b.GetFootprints() for p in f.Pads() if p.GetNumber()};assert all(boardpins.get(key)==net for key,net in pm.items());assert pd[('U10','3')]['node_count']==1 and 'no_connect' in pd[('U10','3')]['node']['pintype']
paste=V.drill_paste_contacts(b);assert paste==V.drill_paste_contacts(a)
for f in (S/'hardware').rglob('*'):
 if f.is_file() and str(f.relative_to(S/'hardware')) not in ['nexus-style-fc.kicad_pcb','nexus-style-fc.kicad_sch','sym-lib-table']:assert sha(f)==sha(O/'hardware'/f.relative_to(S/'hardware')),f
assert sha(O/'hardware/library/NexusReviewed.kicad_sym')=='d82a4b3cd2371f111ecb2cfc7708e13c65cb06bc746ca126a887bb7e3ab311ee';assert sha(O/'hardware/sym-lib-table')=='26236e95331fb80367290656a29c41e26d82a5e8515769733a3e4ae7326908c4'
errs=collections.Counter(z['type'] for z in y['violations'] if z['severity']=='error');gaps=[float(re.search(r'actual ([0-9.]+) mm',z['description']).group(1)) for z in y['violations'] if z['severity']=='error' and z['type']=='clearance'];out={'status':'PASS: exact project-local filter metadata schematic integrated with unchanged PCB geometry; manufacturing DRC remains unfinished','role':tr['role'],'source_main_commit_reported_by_owner':tr['source_main_commit_reported_by_owner'],'source_board_sha256':sha(SP),'candidate_board_sha256':sha(P),'schematic_sha256':sha(O/'hardware/nexus-style-fc.kicad_sch'),'project_sha256':sha(O/'hardware/nexus-style-fc.kicad_pro'),'rules_sha256':sha(O/'hardware/nexus-style-fc.kicad_dru'),'native_drc_sha256':sha(O/'native-drc.json'),'native_erc_sha256':sha(O/'native-erc.json'),'native_netlist_sha256':sha(O/'final-netlist.xml'),'native_error_count':sum(errs.values()),'native_errors_by_type':dict(errs),'unchanged_warnings':sum(z['severity']=='warning' for z in y['violations']),'opens':0,'parity_issues':0,'erc_violations':0,'exact_net_pin_pairs':len(pm),'source_schema_net_pin_delta':[],'en_no_connect_evidence':pd[('U10','3')],'en_conductive_contacts':contacts,'native_drc_pairs_and_descriptions_exactly_unchanged':True,'all_copper_primitive_definitions_exactly_unchanged':True,'retained_direct_contacts_preserved':len(retained),'invariants':inv,'pasted_via_contacts_unchanged':V.contact_summary(paste),'minimum_remaining_clearance_mm':min(gaps),'worsened_residual_pairs':[],'qualification':'Native source-bound integration only. Known DRC errors, remaining off-center power junctions, power/return/SI, ordinary pasted vias, header edge and mechanical and fabrication gates remain open.'};(O/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({key:out[key] for key in ['status','role','candidate_board_sha256','native_error_count','opens','parity_issues','erc_violations','exact_net_pin_pairs','retained_direct_contacts_preserved']},indent=2))
