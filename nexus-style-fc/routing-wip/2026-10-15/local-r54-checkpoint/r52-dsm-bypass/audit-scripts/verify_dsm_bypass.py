from pathlib import Path
import pcbnew as k,sys,json,math,hashlib,importlib.util,collections,re,copy
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);P=O/'hardware/nexus-style-fc.kicad_pcb';SP=S/'hardware/nexus-style-fc.kicad_pcb';R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(SP)==tr['source_board_sha256'];source_hash=sha(SP);candidate_hash=sha(P);spec=importlib.util.spec_from_file_location('validator',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
uid=lambda x:x.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));shape=lambda o,l:o.GetEffectiveShape(l)
def collide(a,b,c=0):
 z=a.Collide(b,c);return z[0] if isinstance(z,tuple) else bool(z)
a,b=[k.LoadBoard(str(f)) for f in [SP,P]];ls=list(b.GetEnabledLayers().CuStack());at={uid(x):x for x in a.GetTracks()};bt={uid(x):x for x in b.GetTracks()};ap={uid(p):p for f in a.GetFootprints() for p in f.Pads()};bp={uid(p):p for f in b.GetFootprints() for p in f.Pads()};rm={u for r in tr['routes'] for u in r['removed_uuids']};add={u for r in tr['routes'] for u in r['new_uuids']};assert set(at)-set(bt)==rm and set(bt)-set(at)==add
st,ct=[V.parse_sexpr(f.read_text()) for f in [SP,P]];inv=V.invariant_checks(a,b,st,ct);assert inv['status']=='pass',inv
moves={m['uuid']:m for m in tr['moved_vias']};mv=set(moves);norm=copy.deepcopy(ct)
for u,m in moves.items():
 assert isinstance(at[u],k.PCB_VIA) and isinstance(bt[u],k.PCB_VIA)
 assert xy(at[u].GetPosition())==tuple(m['from']) and xy(bt[u].GetPosition())==tuple(m['to'])
 assert bt[u].GetDrillValue()==round(m['drill_mm']*1e6) and all(bt[u].GetWidth(l)==round(m['size_mm']*1e6) for l in ls if bt[u].IsOnLayer(l))
 nodes=[n for n in V.children(norm,'via') if V.source_uuid(n)==u];assert len(nodes)==1;pos=V.children(nodes[0],'at');assert len(pos)==1;pos[0][1:]=[str(x) for x in m['from']]

for tag in ['segment','arc','via']:
 aa,bb=[V.keyed_nodes(V.children(t,tag)) for t in [st,norm]];assert {u:z for u,z in aa.items() if u not in rm}=={u:z for u,z in bb.items() if u not in add},('Unplanned copper change',tag)
seen=set();old_pairs=[];retained=[];conn=a.GetConnectivity()
for u,t in at.items():
 for q in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
  w=uid(q);obj=at.get(w) or ap.get(w);key=tuple(sorted([u,w]));layers=[l for l in ls if t.IsOnLayer(l) and obj.IsOnLayer(l) and collide(shape(t,l),shape(obj,l))]
  if u==w or key in seen or not layers:continue
  seen.add(key);old_pairs.append((u,w,layers))
  if u in mv:assert w in rm or w in mv,('Unaccounted old moved-via port',u,w)
  if w in mv:assert u in rm or u in mv,('Unaccounted old moved-via port',w,u)
  if u not in rm|mv and w not in rm|mv:
   nq=bt.get(w) or bp.get(w);assert any(collide(shape(bt[u],l),shape(nq,l)) for l in layers),('Retained contact lost',key);retained.append(key)
def finite_patch(track,port,l):
 aa,zz=xy(track.GetStart()),xy(track.GetEnd());length=math.dist(aa,zz);dr=((zz[0]-aa[0])/length,(zz[1]-aa[1])/length);n=(-dr[1],dr[0]);rad=track.GetWidth()/2e6;cen=xy(port.GetPosition());proj=sum((cen[i]-aa[i])*dr[i] for i in range(2));off=abs(sum((cen[i]-aa[i])*n[i] for i in range(2)));candidates=[proj+d for d in [0,.12,-.12,.15,-.15,.18,-.18]]+[i*length/200 for i in range(1,200)]
 for q in candidates:
  if not .01<=q<=length-.01:continue
  corners=[(aa[0]+(q+s*.01)*dr[0]+c*rad*n[0],aa[1]+(q+s*.01)*dr[1]+c*rad*n[1]) for s in [-1,1] for c in [-1,1]]
  if not all(collide(shape(port,l),vec(pt)) for pt in corners):continue
  dist=math.hypot(max(abs(proj-q)-.01,0),max(off-rad,0))
  if isinstance(port,k.PCB_VIA) and dist<port.GetDrillValue()/2e6+.001:continue
  return {'kind':'finite full-width entry','new_track':uid(track),'port':uid(port),'width_mm':2*rad,'axial_depth_mm':.02,'corners':corners,'minimum_distance_from_port_center_mm':dist}
 return None
# Exhaustive direct physical port inventory, independent of endpoint graphs.
ports=set()
for u in rm:
 for w,obj in {**at,**ap}.items():
  if w==u:continue
  layers=[l for l in ls if at[u].IsOnLayer(l) and obj.IsOnLayer(l) and collide(shape(at[u],l),shape(obj,l))]
  if layers:
   assert obj.GetNetname()=='DSM_DATA'
   if w not in rm:ports.add(w)
assert ports==set(tr['expected_external_ports'])
route_proofs=[];route_ts={}
for r in tr['routes']:
 l=b.GetLayerID(r['layer']);new=[bt[u] for u in r['new_uuids']];route_ts[r['name']]=new
 for i,t in enumerate(new):
  assert not isinstance(t,k.PCB_VIA) and t.GetNetname()=='DSM_DATA' and t.GetLayer()==l and t.GetWidth()==127000
  assert xy(t.GetStart())==tuple(r['points'][i]) and xy(t.GetEnd())==tuple(r['points'][i+1])
  if i:assert xy(new[i-1].GetEnd())==xy(t.GetStart())
 route_proofs.append({'route':r['name'],'layer':r['layer'],'width_mm':.127,'new_length_mm':sum(t.GetLength()/1e6 for t in new),'points':r['points']})
top=bt[tr['existing_top_via']];bottom=bt[tr['existing_bottom_via']];annular=[]
for t,v in [(route_ts['DSM_B'][0],top),(route_ts['DSM_B'][-1],bottom),(route_ts['DSM_F'][0],bottom)]:
 p=finite_patch(t,v,t.GetLayer());assert p;annular.append(p)
upper=['f4258c4b-d39a-4aef-9243-ffd1d7e75bf2','77201ee5-9b4c-4173-b410-91a623eb23d2','6968e172-efb0-45fa-a496-1e5a81c809dc']
upperjoints=[]
for u,w in zip(upper,upper[1:]):
 t,q=bt[u],bt[w];assert t.GetWidth()==q.GetWidth()==127000 and t.GetLayer()==q.GetLayer()==k.F_Cu
 common=set([xy(t.GetStart()),xy(t.GetEnd())])&set([xy(q.GetStart()),xy(q.GetEnd())]);assert common and collide(shape(t,k.F_Cu),shape(q,k.F_Cu));upperjoints.append({'a':u,'b':w,'full_width_shared_endpoints':list(common)})
p=finite_patch(bt[upper[-1]],top,k.F_Cu);assert p;annular.append(p)
# The retained J2 DSM pad entry remains a finite full-width contact to the upper donor.
j2=bp['e22b4130-083a-495b-9c23-b8c63feb03ed'];j2proof=finite_patch(bt[upper[0]],j2,k.F_Cu);assert j2proof
stub=bt['4b8974ed-bdd7-49d3-891a-6735916d0283'];assert stub.GetNetname()=='DSM_DATA' and stub.GetLayer()==k.F_Cu
contained=max(math.dist(xy(p),xy(bottom.GetPosition())) for p in [stub.GetStart(),stub.GetEnd()])+stub.GetWidth()/2e6;assert contained<bottom.GetWidth(k.F_Cu)/2e6
lower=bt['e29db36d-b2b4-4217-99c2-53d850c577a7'];newf=route_ts['DSM_F'][0];assert lower.GetWidth()==newf.GetWidth()==127000 and lower.GetLayer()==newf.GetLayer()==k.F_Cu;assert xy(newf.GetEnd())==xy(lower.GetStart())==(100.66,114.496)
assert ports==set(upper+[uid(stub),uid(lower),uid(bottom)])
route_proofs.append({'all_source_external_ports_accounted':sorted(ports),'upper_retained_full_width_joints':upperjoints,'existing_via_annular_entries':annular,'unchanged_J2_pad_full_width_entry':j2proof,'via_contained_stub':{'uuid':uid(stub),'radius_bound_mm':contained,'via_radius_mm':.225,'proof':'Retained tiny stub lies within the unchanged via disk; replacement F and B tracks have explicit full-width plated-annulus entries.'},'downstream_fixed_endpoint':[100.66,114.496]})
obstacles=[]
for u in add|mv:
 t=bt[u]
 for l in ls:
  if not t.IsOnLayer(l):continue
  for w,obj in {**bt,**bp}.items():
   if w!=u and obj.GetNetCode()!=t.GetNetCode() and obj.IsOnLayer(l) and collide(shape(t,l),shape(obj,l),127002):obstacles.append({'track_or_via':u,'obstacle':w,'net':obj.GetNetname(),'layer':b.GetLayerName(l)})
assert not obstacles,obstacles
power=V.power_width_preservation(a,b);assert power['status']=='pass';paste_a,paste_b=V.drill_paste_contacts(a),V.drill_paste_contacts(b);assert paste_a==paste_b
pid='5f922c73-82b6-4073-8e98-d520c70499ca';p=bp[pid];assert p.GetNetname()=='unconnected-(U10-EN-Pad3)';encontacts=[]
for l in ls:
 if not p.IsOnLayer(l):continue
 for u,obj in {**bt,**bp}.items():
  if u!=pid and obj.IsOnLayer(l) and collide(shape(p,l),shape(obj,l)):encontacts.append(u)
 for z in b.Zones():
  if z.IsOnLayer(l) and not z.GetIsRuleArea() and collide(shape(p,l),z.GetFilledPolysList(l)):encontacts.append(uid(z))
assert not encontacts
for f in (S/'hardware').rglob('*'):
 if f.is_file() and f.name!='nexus-style-fc.kicad_pcb':assert sha(f)==sha(O/'hardware'/f.relative_to(S/'hardware')),(f,'support file changed')
assert sha(SP)==source_hash and sha(P)==candidate_hash
out={'status':'PASS: complete DSM donor bypass and finite full-width ports through unchanged existing vias; native acceptance separate','source_sha256':source_hash,'candidate_sha256':candidate_hash,'invariants':inv,'removed_tracks':len(rm),'new_tracks':len(add),'moved_vias':tr['moved_vias'],'complete_via_definition_preserved_except_declared_position':True,'untouched_original_direct_contacts_preserved':len(retained),'route_physical_proofs':route_proofs,'new_copper_obstructions_at_0_127002_mm':obstacles,'power_width_floor':power,'pasted_vias_unchanged':V.contact_summary(paste_b),'en_conductive_contacts':encontacts,'qualification':'Preservation and local geometry checks only; power/return/SI/USB/regulator/pasted-via and fabrication gates remain open.'};(O/'geometry-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['status','candidate_sha256','untouched_original_direct_contacts_preserved','removed_tracks','new_tracks','en_conductive_contacts']}))
