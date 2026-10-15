from pathlib import Path
import pcbnew as k,sys,json,math,hashlib,importlib.util,collections,re,copy
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);P=O/'hardware/nexus-style-fc.kicad_pcb';SP=S/'hardware/nexus-style-fc.kicad_pcb';R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(SP)==tr['source_board_sha256'];source_hash=sha(SP);candidate_hash=sha(P);spec=importlib.util.spec_from_file_location('validator',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
uid=lambda x:x.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));shape=lambda o,l:o.GetEffectiveShape(l)
def collide(a,b,c=0):
 z=a.Collide(b,c);return z[0] if isinstance(z,tuple) else bool(z)
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
j=json.loads((O/'source-proposal.json').read_text());a,b=[k.LoadBoard(str(f)) for f in [SP,P]];ls=list(b.GetEnabledLayers().CuStack());at={uid(x):x for x in a.GetTracks()};bt={uid(x):x for x in b.GetTracks()};ap={uid(p):p for f in a.GetFootprints() for p in f.Pads()};bp={uid(p):p for f in b.GetFootprints() for p in f.Pads()};aa={**at,**ap};bb={**bt,**bp};rm={x['uuid'] for x in tr['removed_items']};add={x['uuid'] for x in tr['new_items']};mp=tr['proposal_to_native_uuid'];assert set(at)-set(bt)==rm and set(bt)-set(at)==add
st,ct=[V.parse_sexpr(f.read_text()) for f in [SP,P]];inv=V.invariant_checks(a,b,st,ct);assert inv['status']=='pass',inv
for tag in ['segment','arc','via']:
 x,y=[V.keyed_nodes(V.children(t,tag)) for t in [st,ct]];assert {u:z for u,z in x.items() if u not in rm}=={u:z for u,z in y.items() if u not in add},('Unplanned copper change',tag)
for item in tr['new_items']:
 t=bt[item['uuid']];assert t.GetNetname()==item['net']
 if item['kind']=='via':
  assert isinstance(t,k.PCB_VIA) and xy(t.GetPosition())==tuple(item['at']) and t.GetDrillValue()==200000 and t.GetWidth(k.F_Cu)==450000 and all(t.IsOnLayer(l) for l in ls)
  n=next(n for n in V.children(ct,'via') if V.source_uuid(n)==uid(t));assert V.children(n,'tenting') in [[['tenting','front','back']], [['tenting',['front','yes'],['back','yes']]]]
 else:assert not isinstance(t,k.PCB_VIA) and t.GetLayer()==b.GetLayerID(item['layers'][0]) and t.GetWidth()==250000 and xy(t.GetStart())==tuple(item['start']) and xy(t.GetEnd())==tuple(item['end'])
# Exhaustive source physical ports, including area/midspan contacts, independent of endpoint graph.
ports=set();old_donor_contacts=[]
for u in sorted(rm):
 t=at[u]
 for w,q in aa.items():
  if w==u:continue
  layers=[l for l in ls if t.IsOnLayer(l) and q.IsOnLayer(l) and collide(shape(t,l),shape(q,l))]
  if layers:
   assert q.GetNetCode()==t.GetNetCode(),('Source donor foreign contact',u,w)
   old_donor_contacts.append({'a':u,'b':w,'layers':[a.GetLayerName(l) for l in layers]})
   if w not in rm:ports.add(w)
assert ports==set(tr['expected_external_ports']),(ports,tr['expected_external_ports'])
# Every untouched original contact remains physically present.
seen=set();retained=[];conn=a.GetConnectivity()
for u,t in at.items():
 for q in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
  w=uid(q);obj=aa[w];key=tuple(sorted([u,w]));layers=[l for l in ls if t.IsOnLayer(l) and obj.IsOnLayer(l) and collide(shape(t,l),shape(obj,l))]
  if u==w or key in seen or not layers:continue
  seen.add(key)
  if u not in rm and w not in rm:
   assert any(collide(shape(bt[u],l),shape(bb[w],l)) for l in layers),('Retained contact lost',key);retained.append(key)
# Complete new route joints: exact endpoints for same-layer tracks and finite annular entry on each via layer.
chains=[['proposal:OUT_F:'+str(i) for i in range(4)],['proposal:IN_F:'+str(i) for i in range(2)]]
for ids in chains:
 ts=[bt[mp[u]] for u in ids]
 for t,q in zip(ts,ts[1:]):assert xy(t.GetEnd())==xy(q.GetStart()) and t.GetWidth()==q.GetWidth()==250000 and t.GetLayer()==q.GetLayer()
annular=[];via=bt[mp['proposal:VSYS_via']]
for name in ['proposal:IN_B:0','proposal:IN_F:0']:
 t=bt[mp[name]];proof=finite_patch(t,via,t.GetLayer());assert proof,(name,'new via full-width entry');annular.append(proof)
port_proofs=[];ce=bt['ce0c83ec-dabe-41bb-a4f2-460dd49ca91c'];stubids={'96b12e5e-968d-4500-97cd-2fe832e967c6','f526e6a3-c8c8-473d-81cb-48d54ae7aaaa'}
for u in sorted(ports):
 obj=bb[u];proof=None
 if u in stubids:
  # Unchanged terminal stubs lie wholly inside the unchanged upstream via disk.
  assert isinstance(obj,k.PCB_TRACK) and obj.GetNetname()==ce.GetNetname();rad=max(math.dist(xy(p),xy(ce.GetPosition())) for p in [obj.GetStart(),obj.GetEnd()])+obj.GetWidth()/2e6;assert rad<ce.GetWidth(k.F_Cu)/2e6;assert collide(shape(obj,k.F_Cu),shape(ce,k.F_Cu));entry=finite_patch(bt[mp['proposal:IN_B:0']],ce,k.B_Cu);assert entry
  proof={'kind':'unchanged wholly via-contained stub; full-width replacement enters same plated annulus on B.Cu','port':u,'containing_via':uid(ce),'copper_containment_margin_mm':ce.GetWidth(k.F_Cu)/2e6-rad,'replacement_annular_entry':entry}
 else:
  for w in add:
   t=bt[w]
   if isinstance(t,k.PCB_VIA) or t.GetNetname()!=obj.GetNetname() or not obj.IsOnLayer(t.GetLayer()) or not collide(shape(t,t.GetLayer()),shape(obj,t.GetLayer())):continue
   if isinstance(obj,k.PAD) or isinstance(obj,k.PCB_VIA):proof=finite_patch(t,obj,t.GetLayer())
   else:
    shared=set([xy(t.GetStart()),xy(t.GetEnd())])&set([xy(obj.GetStart()),xy(obj.GetEnd())])
    if shared and t.GetWidth()>=obj.GetWidth():proof={'kind':'exact shared centerline endpoint; replacement at least retained branch width','port':u,'replacement_track':w,'shared_endpoints':list(shared),'replacement_width_mm':t.GetWidth()/1e6,'retained_width_mm':obj.GetWidth()/1e6}
   if proof:break
 assert proof,('External full-width contact unproved',u);port_proofs.append(proof)
# All unchanged C18 serial contacts, complete replacement to input, and direct C19 GND chain.
retained_c18=[]
for e in j['retained']['C18_serial_source_contact_edges']:
 u,w=e['a'],e['b']
 if u in rm or w in rm:continue
 common=[l for l in ls if bb[u].IsOnLayer(l) and bb[w].IsOnLayer(l) and collide(shape(bb[u],l),shape(bb[w],l))];assert common;retained_c18.append({'a':u,'b':w,'layers':[b.GetLayerName(l) for l in common]})
gndids=['0c2644fc-74b6-44df-8fe2-efdd67e19a51','0e6f7d27-c86a-48a8-b273-5095c1cb41da','14bc041b-ae7c-41de-af46-a97528a3dcf6','ad3d5f69-4db4-4e49-a09a-3a335bf5e76c']
for u,w in zip(gndids,gndids[1:]):assert bb[u].GetNetname()==bb[w].GetNetname()=='GND' and collide(shape(bb[u],k.F_Cu),shape(bb[w],k.F_Cu))
obstacles=[];nearest=[]
for u in add:
 t=bt[u]
 for l in ls:
  if not t.IsOnLayer(l):continue
  for w,obj in bb.items():
   if w==u or obj.GetNetCode()==t.GetNetCode() or not obj.IsOnLayer(l):continue
   if collide(shape(t,l),shape(obj,l),127002):obstacles.append({'new_item':u,'obstacle':w,'net':obj.GetNetname(),'layer':b.GetLayerName(l)})
   if collide(shape(t,l),shape(obj,l),150000):
    lo,hi=0,150000
    while hi-lo>1:
     mid=(lo+hi)//2
     if collide(shape(t,l),shape(obj,l),mid):hi=mid
     else:lo=mid
    nearest.append({'new_item':u,'obstacle':w,'net':obj.GetNetname(),'layer':b.GetLayerName(l),'gap_mm_upper':hi/1e6})
assert not obstacles,obstacles
power=V.power_width_preservation(a,b);assert power['status']=='pass';paste_a,paste_b=V.drill_paste_contacts(a),V.drill_paste_contacts(b);assert paste_a==paste_b
pid='5f922c73-82b6-4073-8e98-d520c70499ca';p=bp[pid];assert p.GetNetname()=='unconnected-(U10-EN-Pad3)';en=[]
for l in ls:
 if not p.IsOnLayer(l):continue
 for u,obj in bb.items():
  if u!=pid and obj.IsOnLayer(l) and collide(shape(p,l),shape(obj,l)):en.append(u)
 for z in b.Zones():
  if z.IsOnLayer(l) and not z.GetIsRuleArea() and collide(shape(p,l),z.GetFilledPolysList(l)):en.append(uid(z))
assert not en
for f in (S/'hardware').rglob('*'):
 if f.is_file() and f.name!='nexus-style-fc.kicad_pcb':assert sha(f)==sha(O/'hardware'/f.relative_to(S/'hardware')),(f,'support file changed')
assert sha(SP)==source_hash and sha(P)==candidate_hash
out={'status':'PASS: U10 complete atomic donor paths and finite full-width physical ports; native and return qualification separate','source_sha256':source_hash,'candidate_sha256':candidate_hash,'invariants':inv,'removed_tracks':sum(x['kind']=='segment' for x in tr['removed_items']),'removed_vias':sum(x['kind']=='via' for x in tr['removed_items']),'new_tracks':7,'new_vias':1,'untouched_original_direct_contacts_preserved':len(retained),'source_donor_contacts':old_donor_contacts,'all_eight_external_port_proofs':port_proofs,'new_via_full_width_annular_entries':annular,'retained_C18_upstream_contact_edges':retained_c18,'direct_C19_GND_chain_preserved':gndids,'new_copper_obstructions_at_0_127002_mm':obstacles,'new_copper_gaps_under_0_150_mm':sorted(nearest,key=lambda x:x['gap_mm_upper']),'power_width_floor':power,'pasted_vias_unchanged':V.contact_summary(paste_b),'en_conductive_contacts':en,'qualification':'Geometry only. Actual post-refill full-width reference connectivity and input tradeoff require separate review. C19 effective capacitance/ESR and stability remain unqualified.'};(O/'geometry-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({key:out[key] for key in ['status','candidate_sha256','untouched_original_direct_contacts_preserved','new_copper_gaps_under_0_150_mm','en_conductive_contacts']},indent=2))
