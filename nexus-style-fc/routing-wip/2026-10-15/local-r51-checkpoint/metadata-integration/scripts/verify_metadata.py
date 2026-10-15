from pathlib import Path
import pcbnew as k,json,hashlib,sys,importlib.util,collections,xml.etree.ElementTree as ET,re,copy
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();P=O/'hardware/nexus-style-fc.kicad_pcb';SP=S/'hardware/nexus-style-fc.kicad_pcb';assert sha(SP)==tr['source_board_sha256'];assert sha(O/'hardware/nexus-style-fc.kicad_sch')==tr['candidate_schema_sha256'];spec=importlib.util.spec_from_file_location('validator',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
a,b=[k.LoadBoard(str(p)) for p in [SP,P]];st,ct=[V.parse_sexpr(p.read_text()) for p in [SP,P]];normalized=copy.deepcopy(st);fu=tr['approved_footprint_uuid'];d=tr['approved_metadata_delta']
sf=next(f for f in V.children(st,'footprint') if V.source_uuid(f)==fu);nf=next(f for f in V.children(normalized,'footprint') if V.source_uuid(f)==fu);cf=next(f for f in V.children(ct,'footprint') if V.source_uuid(f)==fu)
assert next(V.atom(n[2]) for n in V.children(sf,'property') if V.atom(n[1])=='Reference')=='U10'
prop=next(n for n in V.children(nf,'property') if V.atom(n[1])=='LCSC Part');assert V.source_uuid(prop)==d['removed_property_uuid'] and V.atom(prop[2])==d['removed_property_value']=='C82942';nf.remove(prop);assert not any(V.atom(n[1])=='LCSC Part' for n in V.children(cf,'property'))
descr=V.children(nf,'descr');assert len(descr)==1 and V.atom(descr[0][1])==d['old_lib_description']=='ME6211C33M5G-N';descr[0][1]=['string',d['new_lib_description']]
assert V.canonical(nf)==V.canonical(cf),'Any other U10 property or footprint edit is prohibited'
inv=V.invariant_checks(a,b,normalized,ct);assert inv['status']=='pass',inv
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
# Metadata does not justify any filled-copper change: compare exact native polygons on every filled layer.
za={uid(z):z for z in a.Zones()};zb={uid(z):z for z in b.Zones()};assert za.keys()==zb.keys();zone_checks=[]
for u,z in za.items():
 for l in ls:
  if not z.IsOnLayer(l):continue
  old=z.GetFilledPolysList(l);new=zb[u].GetFilledPolysList(l);minus=k.SHAPE_POLY_SET(old);minus.BooleanSubtract(new);plus=k.SHAPE_POLY_SET(new);plus.BooleanSubtract(old);lost=abs(minus.Area())/1e12;added=abs(plus.Area())/1e12;assert lost==0 and added==0,(u,l,lost,added);zone_checks.append({'zone':u,'layer':a.GetLayerName(l),'lost_area_mm2':lost,'added_area_mm2':added})
for f in (S/'hardware').rglob('*'):
 if f.is_file() and f.name not in ['nexus-style-fc.kicad_pcb','nexus-style-fc.kicad_sch']:assert sha(f)==sha(O/'hardware'/f.relative_to(S/'hardware')),f
errs=collections.Counter(z['type'] for z in y['violations'] if z['severity']=='error');gaps=[float(re.search(r'actual ([0-9.]+) mm',z['description']).group(1)) for z in y['violations'] if z['severity']=='error' and z['type']=='clearance'];out={'status':'PASS: exact U10 donor-metadata cleanup; selected-part fields, copper and physical geometry unchanged; manufacturing DRC remains unfinished','role':tr['role'],'source_main_commit_reported_by_owner':tr['source_main_commit_reported_by_owner'],'source_board_sha256':sha(SP),'source_schematic_sha256':sha(S/'hardware/nexus-style-fc.kicad_sch'),'candidate_board_sha256':sha(P),'schematic_sha256':sha(O/'hardware/nexus-style-fc.kicad_sch'),'project_sha256':sha(O/'hardware/nexus-style-fc.kicad_pro'),'rules_sha256':sha(O/'hardware/nexus-style-fc.kicad_dru'),'native_drc_sha256':sha(O/'native-drc.json'),'erc_evidence_basis':'Fresh native ERC on exact unchanged schematic; experimental copy carries the byte-identical canonical ERC receipt','native_erc_sha256':sha(O/'native-erc.json'),'native_netlist_sha256':sha(O/'final-netlist.xml'),'native_error_count':sum(errs.values()),'native_errors_by_type':dict(errs),'unchanged_warnings':sum(z['severity']=='warning' for z in y['violations']),'opens':0,'parity_issues':0,'erc_violations':0,'exact_net_pin_pairs':len(pm),'source_schema_net_pin_delta':[],'approved_U10_metadata_delta':d,'U10_only_invariant_normalization':'Remove only exact stale LCSC Part property UUID/value and replace only footprint lib-description; every other property and footprint node remains exact.','en_no_connect_evidence':pd[('U10','3')],'en_conductive_contacts':contacts,'native_drc_pairs_and_descriptions_exactly_unchanged':True,'all_copper_primitive_definitions_exactly_unchanged':True,'all_saved_filled_copper_areas_exactly_unchanged':zone_checks,'retained_direct_contacts_preserved':len(retained),'invariants':inv,'pasted_via_contacts_unchanged':V.contact_summary(paste),'minimum_remaining_clearance_mm':min(gaps),'worsened_residual_pairs':[],'qualification':'Native source-bound integration only. Known DRC errors, regulator effective capacitance and loops, power/return/SI, ordinary pasted vias, header edge and mechanical and fabrication gates remain open.'};(O/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({key:out[key] for key in ['status','role','candidate_board_sha256','native_error_count','opens','parity_issues','erc_violations','exact_net_pin_pairs','retained_direct_contacts_preserved']},indent=2))
