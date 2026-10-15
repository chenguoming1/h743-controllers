from pathlib import Path
import pcbnew as k,sys,json,math,hashlib,importlib.util,copy
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);P=O/'hardware/nexus-style-fc.kicad_pcb';SP=S/'hardware/nexus-style-fc.kicad_pcb';R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(SP)==tr['source_board_sha256'];source_hash=sha(SP);candidate_hash=sha(P);spec=importlib.util.spec_from_file_location('validator',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V);uid=lambda x:x.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6)
def hit(a,b,c=0):
 z=k.SHAPE.Collide(a,b,c);return z[0] if isinstance(z,tuple) else bool(z)
a,b=[k.LoadBoard(str(f)) for f in [SP,P]];ls=list(b.GetEnabledLayers().CuStack());at={uid(x):x for x in a.GetTracks()};bt={uid(x):x for x in b.GetTracks()};ap={uid(p):p for f in a.GetFootprints() for p in f.Pads()};bp={uid(p):p for f in b.GetFootprints() for p in f.Pads()};add={u for r in tr['routes'] for u in r['new_uuids']};mv={m['uuid'] for m in tr['moved_vias']};assert not set(at)-set(bt) and set(bt)-set(at)==add and len(add)==2 and len(mv)==2
st,ct=[V.parse_sexpr(f.read_text()) for f in [SP,P]];inv=V.invariant_checks(a,b,st,ct);assert inv['status']=='pass',inv;norm=copy.deepcopy(ct)
for m in tr['moved_vias']:
 u=m['uuid'];assert isinstance(at[u],k.PCB_VIA) and isinstance(bt[u],k.PCB_VIA);assert xy(at[u].GetPosition())==tuple(m['from']) and xy(bt[u].GetPosition())==tuple(m['to']);assert bt[u].GetDrillValue()==200000 and all(bt[u].GetWidth(l)==450000 for l in ls);n=next(n for n in V.children(norm,'via') if V.source_uuid(n)==u);V.children(n,'at')[0][1:]=[str(x) for x in m['from']]
for tag in ['segment','arc','via']:
 aa,bb=[V.keyed_nodes(V.children(t,tag)) for t in [st,norm]];assert aa=={u:z for u,z in bb.items() if u not in add},('Unplanned copper change',tag)
seen=set();retained=[];via_ports={u:set() for u in mv};conn=a.GetConnectivity()
for u,t in at.items():
 for q in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
  w=uid(q);obj=at.get(w) or ap.get(w);key=tuple(sorted([u,w]));layers=[l for l in ls if t.IsOnLayer(l) and obj.IsOnLayer(l) and hit(t.GetEffectiveShape(l),obj.GetEffectiveShape(l))]
  if u==w or key in seen or not layers:continue
  seen.add(key)
  for inside,outside in [(u,w),(w,u)]:
   if inside in mv:assert layers==[k.F_Cu],('Unaccounted opposite-layer donor',inside,outside,layers);via_ports[inside].add(outside)
  if u not in mv and w not in mv:
   q=bt.get(w) or bp.get(w);assert any(hit(bt[u].GetEffectiveShape(l),q.GetEffectiveShape(l)) for l in layers);retained.append(key)
proofs=[]
for r in tr['routes']:
 u=r['moved_via'];ports=via_ports[u];assert ports==set(r['expected_source_direct_ports']);t=bt[r['new_uuids'][0]];assert t.GetLayer()==k.F_Cu and t.GetWidth()==450000 and t.GetNetname()=='GND';assert xy(t.GetStart())==xy(at[u].GetPosition()) and xy(t.GetEnd())==xy(bt[u].GetPosition());assert at[u].GetWidth(k.F_Cu)==bt[u].GetWidth(k.F_Cu)==t.GetWidth()
 # A round-ended segment contains the entire radius-width/2 disk centered at either endpoint.
 # Exact equality of centers and diameters proves full old-land and new-annulus containment without a crescent-contact exception.
 contacts=[]
 for p in sorted(ports):
  q=bt.get(p) or bp.get(p);assert q.IsOnLayer(k.F_Cu) and q.GetNetname()=='GND' and hit(t.GetEffectiveShape(k.F_Cu),q.GetEffectiveShape(k.F_Cu));contacts.append({'uuid':p,'kind':type(q).__name__,'proof':'Entire original via F.Cu disk is contained in the unchanged-diameter round endpoint of the new track, so every original pad/track overlap area is retained; original donor geometry is exact.'})
 proofs.append({'via':u,'old_center':xy(at[u].GetPosition()),'new_center':xy(bt[u].GetPosition()),'new_track':uid(t),'track_width_mm':.45,'added_centerline_length_mm':t.GetLength()/1e6,'full_old_land_disk_retained':True,'full_new_via_annulus_contained_by_track':True,'complete_original_ports':contacts})
obstacles=[]
for u in add|mv:
 t=bt[u]
 for l in ls:
  if not t.IsOnLayer(l):continue
  for w,obj in {**bt,**bp}.items():
   if u!=w and obj.IsOnLayer(l) and obj.GetNetCode()!=t.GetNetCode() and hit(t.GetEffectiveShape(l),obj.GetEffectiveShape(l),127002):obstacles.append({'item':u,'obstacle':w,'layer':b.GetLayerName(l),'net':obj.GetNetname()})
assert not obstacles,obstacles
power=V.power_width_preservation(a,b);assert power['status']=='pass';pa,pb=V.drill_paste_contacts(a),V.drill_paste_contacts(b);removed=[p for p in pa if p['via_uuid'] in mv];assert len(removed)==2 and {p['via_uuid'] for p in removed}==mv and [p for p in pa if p['via_uuid'] not in mv]==pb
pid='5f922c73-82b6-4073-8e98-d520c70499ca';p=bp[pid];assert p.GetNetname()=='unconnected-(U10-EN-Pad3)';en=[]
for l in ls:
 if not p.IsOnLayer(l):continue
 for u,obj in {**bt,**bp}.items():
  if u!=pid and obj.IsOnLayer(l) and hit(p.GetEffectiveShape(l),obj.GetEffectiveShape(l)):en.append(u)
 for z in b.Zones():
  if z.IsOnLayer(l) and not z.GetIsRuleArea() and hit(p.GetEffectiveShape(l),z.GetFilledPolysList(l)):en.append(uid(z))
assert not en
for f in (S/'hardware').rglob('*'):
 if f.is_file() and f.name!='nexus-style-fc.kicad_pcb':assert sha(f)==sha(O/'hardware'/f.relative_to(S/'hardware'))
assert sha(SP)==source_hash and sha(P)==candidate_hash
out={'status':'PASS: two complete ordinary off-pad GND relocations retain all original copper contacts and entire original outer land, with no narrowing or other geometry change; native/return/mask acceptance separate','source_sha256':source_hash,'candidate_sha256':candidate_hash,'invariants':inv,'removed_tracks':0,'new_tracks':2,'moved_vias':tr['moved_vias'],'untouched_original_direct_contacts_preserved':len(retained),'route_physical_proofs':proofs,'new_copper_obstructions_at_0_127002_mm':obstacles,'power_width_floor':power,'source_pasted_vias':V.contact_summary(pa),'candidate_pasted_vias':V.contact_summary(pb),'exact_removed_paste_contacts':removed,'no_other_paste_contact_changes':True,'en_conductive_contacts':en,'qualification':'Only two inherited drill/pasted-pad contacts removed geometrically. Remaining pasted vias, actual masks/paste, thermal/return, power, USB and fabrication qualification remain open.'};(O/'geometry-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({x:out[x] for x in ['status','candidate_sha256','untouched_original_direct_contacts_preserved','source_pasted_vias','candidate_pasted_vias']}))
