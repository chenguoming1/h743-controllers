from pathlib import Path
import pcbnew as k,sys,json,math,hashlib,importlib.util,collections,re,copy
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);P=O/'hardware/nexus-style-fc.kicad_pcb';SP=S/'hardware/nexus-style-fc.kicad_pcb';R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(SP)==tr['source_board_sha256'];source_hash=sha(SP);candidate_hash=sha(P);spec=importlib.util.spec_from_file_location('validator',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
uid=lambda x:x.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));shape=lambda o,l:o.GetEffectiveShape(l)
def collide(a,b,c=0):
 z=a.Collide(b,c);return z[0] if isinstance(z,tuple) else bool(z)
a,b=[k.LoadBoard(str(f)) for f in [SP,P]];ls=list(b.GetEnabledLayers().CuStack());at={uid(x):x for x in a.GetTracks()};bt={uid(x):x for x in b.GetTracks()};ap={uid(p):p for f in a.GetFootprints() for p in f.Pads()};bp={uid(p):p for f in b.GetFootprints() for p in f.Pads()};rm={u for r in tr['routes'] for u in r['removed_uuids']};newtrackids={u for r in tr['routes'] for u in r['new_uuids']};nv={v['uuid'] for v in tr['new_vias']};add=newtrackids|nv;assert set(at)-set(bt)==rm and set(bt)-set(at)==add
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
  if u in mv:assert w in rm or w in mv or (u=='c27d2d45-e833-42bd-ad22-d9ecb563eb6c' and w=='c55aeac1-9aec-4a5f-aa93-6a2f39041cca'),('Unaccounted old moved-via port',u,w)
  if w in mv:assert u in rm or u in mv or (w=='c27d2d45-e833-42bd-ad22-d9ecb563eb6c' and u=='c55aeac1-9aec-4a5f-aa93-6a2f39041cca'),('Unaccounted old moved-via port',w,u)
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

returnproof=json.loads((O/'cc1-return-topology.json').read_text());assert returnproof['status']=='PASS' and returnproof['all_existing_shield_spoke_copper_preserved'] and returnproof['source_board_sha256']==source_hash and returnproof['candidate_board_sha256']==candidate_hash
newvia={v['name']:v['uuid'] for v in tr['new_vias']}
oldports={
 'VBUS_B':['7d7654f5-0c35-4c86-b13a-4a939d4a81f3','9ba2e202-dd04-4557-a123-3f7be124bb16','a0acdbb8-872d-437f-8618-d0dda7792258','cb9e70ce-a3b8-44ce-992e-91d641842571'],
 'CC1_F':['470695eb-4bba-40ff-86e5-1ae479293bbf','d706c2b1-cac5-4e1a-a5cc-a5f3f22ea074'],
 'CC1_B':['255df64a-d141-4ace-a9d1-62db4c009fae','470695eb-4bba-40ff-86e5-1ae479293bbf'],
 'CC1_In3':[],
 'VBUS_C_F':['1da27a5a-6e85-4823-b1bb-e39294f7fcec','448d3407-3e9b-4d32-a791-106cb8074ddf','c5d17ea9-45e4-456a-a87e-a2a7387c5f84'],
 'VBUS_C_In2':['448d3407-3e9b-4d32-a791-106cb8074ddf','e585a894-f9ca-4ca8-a469-3926f53c3771'],
 'R20_GND_B':['a987abba-83fc-489d-b1ce-ea1a24bce685','c55aeac1-9aec-4a5f-aa93-6a2f39041cca','f3b26300-209a-441a-b917-158227e4afba']}
newports=copy.deepcopy(oldports);newports['CC1_B']=['255df64a-d141-4ace-a9d1-62db4c009fae',newvia['CC1_R20_via']];newports['CC1_In3']=[newvia['CC1_R20_via'],'470695eb-4bba-40ff-86e5-1ae479293bbf'];newports['R20_GND_B']=['a987abba-83fc-489d-b1ce-ea1a24bce685',newvia['R20_GND_via']]
route_proofs=[]
for r in tr['routes']:
 old=set(r['removed_uuids']);ports=set()
 for u,w,layers in old_pairs:
  for inside,outside in [(u,w),(w,u)]:
   if inside in old and outside not in old:ports.add(outside)
 assert ports==set(oldports[r['name']]),(r['name'],'undeclared original external ports',ports);l=b.GetLayerID(r['layer']);new=[bt[u] for u in r['new_uuids']];assert len(new)==len(r['points'])-1
 for i,t in enumerate(new):
  assert not isinstance(t,k.PCB_VIA) and t.GetNetname()==r['net'] and t.GetLayer()==l and t.GetWidth()==round(r['width_mm']*1e6);assert xy(t.GetStart())==tuple(r['points'][i]) and xy(t.GetEnd())==tuple(r['points'][i+1])
  if i:assert xy(new[i-1].GetEnd())==xy(t.GetStart()) and new[i-1].GetWidth()==t.GetWidth()
 pp=[]
 for u in newports[r['name']]:
  obj=bt.get(u) or bp.get(u);assert obj.GetNetname()==r['net'] and obj.IsOnLayer(l);touch=[t for t in new if collide(shape(t,l),shape(obj,l))];assert touch,('Missing direct new port contact',r['name'],u);proof=None
  if isinstance(obj,k.PCB_TRACK) and not isinstance(obj,k.PCB_VIA):
   for t in touch:
    shared=set([xy(t.GetStart()),xy(t.GetEnd())])&set([xy(obj.GetStart()),xy(obj.GetEnd())])
    if shared and obj.GetWidth()>=t.GetWidth():proof={'kind':'exact common centerline endpoint with no width reduction','port':u,'new_track':uid(t),'shared_endpoints':list(shared),'new_width_mm':t.GetWidth()/1e6,'retained_width_mm':obj.GetWidth()/1e6};break
    if obj.GetWidth()>=t.GetWidth():
     proof=finite_patch(t,obj,l)
     if proof:break
  else:
   for t in touch:
    proof=finite_patch(t,obj,l)
    if proof:break
  if not proof and u not in mv|nv:
   for bridge_id,bridge in bt.items():
    if bridge_id in add|mv or isinstance(bridge,k.PCB_VIA) or bridge.GetNetname()!=r['net'] or bridge.GetLayer()!=l or bridge.GetWidth()<round(r['width_mm']*1e6):continue
    if isinstance(obj,k.PCB_TRACK) and not isinstance(obj,k.PCB_VIA):
     shared_port=set([xy(bridge.GetStart()),xy(bridge.GetEnd())])&set([xy(obj.GetStart()),xy(obj.GetEnd())]);entry={'kind':'retained same-width shared centerline endpoint','points':list(shared_port)} if shared_port and obj.GetWidth()>=bridge.GetWidth() else None
    else:entry=finite_patch(bridge,obj,l)
    if not entry:continue
    for t in new:
     shared=set([xy(t.GetStart()),xy(t.GetEnd())])&set([xy(bridge.GetStart()),xy(bridge.GetEnd())])
     join={'kind':'same-width exact shared centerline endpoint','points':list(shared)} if shared else finite_patch(t,bridge,l)
     if join:proof={'kind':'full-width path through unchanged retained donor','port':u,'new_track':uid(t),'retained_bridge':bridge_id,'new_to_bridge_entry':join,'bridge_width_mm':bridge.GetWidth()/1e6,'entry':entry};break
    if proof:break
  assert proof,('Full-width external contact unproved',r['name'],u);pp.append(proof)
 route_proofs.append({'name':r['name'],'net':r['net'],'layer':r['layer'],'width_mm':r['width_mm'],'old_external_ports':sorted(ports),'new_external_ports':newports[r['name']],'old_centerline_length_mm':sum(at[u].GetLength()/1e6 for u in old),'new_centerline_length_mm':sum(t.GetLength()/1e6 for t in new),'all_external_ports':pp,'consecutive_same_width_centerline_joints':len(new)-1})
# Explicitly connect the split CC1 routes through the two named vias; do not rely on a hidden same-net alternative.
assert set(newports['CC1_F'])&set(newports['CC1_In3'])=={'470695eb-4bba-40ff-86e5-1ae479293bbf'}
assert set(newports['CC1_In3'])&set(newports['CC1_B'])=={newvia['CC1_R20_via']}
# The only donor-to-plane conversion is the R20 GND branch, backed by the separate finite actual same-component proof.
gndpad=bp['c55aeac1-9aec-4a5f-aa93-6a2f39041cca'];bridge=bt['f3b26300-209a-441a-b917-158227e4afba'];assert collide(shape(gndpad,k.B_Cu),shape(bridge,k.B_Cu));ep_entry=finite_patch(bridge,gndpad,k.B_Cu);assert ep_entry
mvg=bt['c27d2d45-e833-42bd-ad22-d9ecb563eb6c'];assert collide(shape(mvg,k.B_Cu),shape(gndpad,k.B_Cu))
plane_conversion={'old_ports':['c55aeac1-9aec-4a5f-aa93-6a2f39041cca','f3b26300-209a-441a-b917-158227e4afba'],'new_ground_via':newvia['R20_GND_via'],'retained_direct_U7_EP_branch_full_width_entry':ep_entry,'finite_actual_same_plane_component_receipt_sha256':sha(O/'cc1-return-topology.json'),'return_comparison':returnproof['R20_return_comparison']}
for v in tr['new_vias']:
 q=bt[v['uuid']];assert isinstance(q,k.PCB_VIA) and q.GetNetname()==v['net'] and xy(q.GetPosition())==tuple(v['to']) and q.GetDrillValue()==200000 and all(q.GetWidth(l)==450000 and q.IsOnLayer(l) for l in ls)
 node=next(n for n in V.children(ct,'via') if V.source_uuid(n)==v['uuid']);tent=V.children(node,'tenting');assert tent in [[['tenting','front','back']],[['tenting',['front','yes'],['back','yes']]]],tent
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
out={'status':'PASS: complete CC1, power and ground transaction with finite full-width ports and explicit actual-plane return proof; native acceptance separate','source_sha256':source_hash,'candidate_sha256':candidate_hash,'invariants':inv,'removed_tracks':len(rm),'new_tracks':len(newtrackids),'new_via_count':len(nv),'moved_vias':tr['moved_vias'],'complete_via_definition_preserved_except_declared_position':True,'untouched_original_direct_contacts_preserved':len(retained),'route_physical_proofs':route_proofs,'new_vias':tr['new_vias'],'R20_explicit_plane_conversion':plane_conversion,'return_topology_receipt_sha256':sha(O/'cc1-return-topology.json'),'new_copper_obstructions_at_0_127002_mm':obstacles,'power_width_floor':power,'pasted_vias_unchanged':V.contact_summary(paste_b),'en_conductive_contacts':encontacts,'qualification':'Preservation and local geometry checks only; power/return/SI/USB/regulator/pasted-via and fabrication gates remain open.'};(O/'geometry-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['status','candidate_sha256','untouched_original_direct_contacts_preserved','removed_tracks','new_tracks','en_conductive_contacts']}))
