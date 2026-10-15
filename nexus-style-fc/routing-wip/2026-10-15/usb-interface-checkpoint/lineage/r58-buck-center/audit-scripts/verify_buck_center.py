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
route_proofs=[]
replacements=tr['replacements'];mapping={r['source_uuid']:r['replacement']['uuid'] for r in replacements}
external=set()
for u,w,layers in old_pairs:
 if u in rm or w in rm:
  nu,nw=mapping.get(u,u),mapping.get(w,w);left=bt.get(nu) or bp.get(nu);right=bt.get(nw) or bp.get(nw)
  assert any(collide(shape(left,l),shape(right,l)) for l in layers),('Original direct contact lost',u,w)
  if u in rm and w not in rm:external.add(w)
  if w in rm and u not in rm:external.add(u)
assert external=={p['uuid'] for p in tr['expected_external_ports']},external

def whole_land(t,v,l):
 assert t.GetWidth()>=v.GetWidth(l) and xy(v.GetPosition()) in [xy(t.GetStart()),xy(t.GetEnd())]
 land=k.SHAPE_POLY_SET();v.TransformShapeToPolygon(land,l,0,50,k.ERROR_OUTSIDE);copper=k.SHAPE_POLY_SET();t.TransformShapeToPolygon(copper,l,0,50,k.ERROR_INSIDE);land.BooleanSubtract(copper);assert abs(land.Area())/1e12<1e-10
 return {'kind':'entire unchanged via land and annulus contained in centered inherited-width track round endpoint','track':uid(t),'via':uid(v),'layer':b.GetLayerName(l),'track_width_mm':t.GetWidth()/1e6,'via_land_diameter_mm':v.GetWidth(l)/1e6,'via_drill_mm':v.GetDrillValue()/1e6,'radial_cap_margin_mm':(t.GetWidth()-v.GetWidth(l))/2e6,'uncovered_land_area_mm2':abs(land.Area())/1e12,'limitation':'Whole annular geometry only; no current or thermal rating inferred.'}
for r in replacements:
 t=bt[r['replacement']['uuid']];old=at[r['source_uuid']];d=r['replacement'];l=t.GetLayer();v=bt[r['target_via']['uuid']]
 assert t.GetNetname()==old.GetNetname()=='5V_BUCK' and t.GetLayer()==old.GetLayer()==b.GetLayerID(d['layers'][0]) and t.GetWidth()==old.GetWidth()==round(d['width']*1e6)
 assert [list(xy(t.GetStart())),list(xy(t.GetEnd()))]==[d['start'],d['end']]
 assert v.GetDrillValue()==200000 and v.GetWidth(l)==450000 and xy(v.GetPosition()) in [xy(t.GetStart()),xy(t.GetEnd())]
 proof=whole_land(t,v,l) if t.GetWidth()==500000 else finite_patch(t,v,l);assert proof
 route_proofs.append({'source_track':uid(old),'new_track':uid(t),'net':t.GetNetname(),'layer':b.GetLayerName(l),'width_mm':t.GetWidth()/1e6,'old_length_mm':old.GetLength()/1e6,'new_length_mm':t.GetLength()/1e6,'target_annular_proof':proof})
ports=[]
for u in sorted(external):
 obj=bt.get(u) or bp.get(u);proof=None
 for nu in sorted(add):
  t=bt[nu];l=t.GetLayer()
  if not obj.IsOnLayer(l) or not collide(shape(t,l),shape(obj,l)):continue
  if isinstance(obj,k.PCB_VIA) and t.GetWidth()==500000 and xy(obj.GetPosition()) in [xy(t.GetStart()),xy(t.GetEnd())]:proof=whole_land(t,obj,l)
  elif isinstance(obj,k.PAD):proof=finite_patch(t,obj,l)
  elif not isinstance(obj,k.PCB_VIA):
   shared=set([xy(t.GetStart()),xy(t.GetEnd())])&set([xy(obj.GetStart()),xy(obj.GetEnd())])
   if shared and obj.GetWidth()==t.GetWidth():proof={'kind':'exact same-width centerline joint','port':u,'track':nu,'width_mm':t.GetWidth()/1e6,'shared_endpoints':list(shared)}
  if proof:break
 if not proof and u=='9d5086d7-6a97-4b07-abf0-0f00e1975b7c':
  bridge=bt['051424f8-a5f4-460c-b1bc-05616bc7fc20'];t=bt['ef6a9fb0-ba01-57aa-83fe-8b03d30cba2e'];assert obj.GetWidth()==bridge.GetWidth()==t.GetWidth()==500000 and obj.GetLayer()==bridge.GetLayer()==t.GetLayer()==k.B_Cu
  left=set([xy(t.GetStart()),xy(t.GetEnd())])&set([xy(bridge.GetStart()),xy(bridge.GetEnd())]);right=set([xy(obj.GetStart()),xy(obj.GetEnd())])&set([xy(bridge.GetStart()),xy(bridge.GetEnd())]);assert left and right
  proof={'kind':'exact full-width retained bridge path; incidental direct overlap also retained','port':u,'new_track':uid(t),'bridge':uid(bridge),'width_mm':.5,'new_joint':list(left),'old_joint':list(right),'unchanged_bridge_annulus':whole_land(bridge,bt['51a22cd5-55d6-4b2a-ab4e-1419692162c2'],k.B_Cu)}
 assert proof,('External full contact proof missing',u);ports.append({'port':u,'proof':proof})
route_proofs.append({'all_seven_external_ports':ports})
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
out={'status':'PASS: complete fixed-layer donor transactions and finite full-width port topology; native acceptance separate','source_sha256':source_hash,'candidate_sha256':candidate_hash,'invariants':inv,'removed_tracks':len(rm),'new_tracks':len(add),'moved_vias':tr['moved_vias'],'complete_via_definition_preserved_except_declared_position':True,'untouched_original_direct_contacts_preserved':len(retained),'route_physical_proofs':route_proofs,'new_copper_obstructions_at_0_127002_mm':obstacles,'power_width_floor':power,'pasted_vias_unchanged':V.contact_summary(paste_b),'en_conductive_contacts':encontacts,'qualification':'Preservation and local geometry checks only; power/return/SI/USB/regulator/pasted-via and fabrication gates remain open.'};(O/'geometry-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['status','candidate_sha256','untouched_original_direct_contacts_preserved','removed_tracks','new_tracks','en_conductive_contacts']}))
