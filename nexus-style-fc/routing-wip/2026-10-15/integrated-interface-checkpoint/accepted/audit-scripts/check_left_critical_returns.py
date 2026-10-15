from pathlib import Path
import pcbnew as k, json,math,sys,hashlib,collections
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/routing-continuation/r62-input-cap-star');captr=json.loads((S/'transaction.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda o:o.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));area=lambda p:abs(p.Area())/1e12
clone=lambda p:k.SHAPE_POLY_SET(p)
def subtract(a,b):p=clone(a);p.BooleanSubtract(b);return p
def intersect(a,b):p=clone(a);p.BooleanIntersection(b);return p
def polygon(o,l,clearance=0):
 p=k.SHAPE_POLY_SET();o.TransformShapeToPolygon(p,l,round(clearance*1e6),1,k.ERROR_INSIDE)
 if isinstance(o,k.PCB_VIA):
  hole=k.PCB_TRACK(o.GetBoard());hole.SetStart(o.GetPosition());hole.SetEnd(o.GetPosition());hole.SetLayer(l);hole.SetWidth(o.GetDrillValue());hp=k.SHAPE_POLY_SET();hole.TransformShapeToPolygon(hp,l,0,1,k.ERROR_OUTSIDE);p.BooleanSubtract(hp)
 return p
def rectangle(points):
 p=k.SHAPE_POLY_SET();c=k.SHAPE_LINE_CHAIN()
 for pt in points:c.Append(vec(pt))
 c.SetClosed(True);p.AddOutline(c);return p
def patch(v,g):
 c=xy(v.GetPosition());rad=v.GetWidth(k.F_Cu)/2e6;drill=v.GetDrillValue()/2e6
 if rad<.225-1e-9 or drill>.100+1e-9:return None
 for angle in range(0,360,15):
  a=math.radians(angle);d=(math.cos(a),math.sin(a));n=(-d[1],d[0]);pts=[(c[0]+(.15+ax*.01)*d[0]+ny*.0635*n[0],c[1]+(.15+ax*.01)*d[1]+ny*.0635*n[1]) for ax,ny in [(-1,-1),(1,-1),(1,1),(-1,1)]]
  if area(subtract(rectangle(pts),g))<1e-10:return {'angle_deg':angle,'width_mm':.127,'depth_mm':.02,'corners':pts}
 return None
def hit(a,b):
 r=k.SHAPE.Collide(a,b,0);return r[0] if isinstance(r,tuple) else bool(r)
boards={};data={};fills={}
refs={'F.Cu':['In1.Cu'],'B.Cu':['In4.Cu'],'In1.Cu':['F.Cu','In2.Cu'],'In3.Cu':['In2.Cu','In4.Cu']}
for label,D in [('source',S),('candidate',O)]:
 print('Loading',label,flush=True);b=k.LoadBoard(str(D/'hardware/nexus-style-fc.kicad_pcb'));boards[label]=b;ts={uid(x):x for x in b.GetTracks()};pads={uid(p):p for f in b.GetFootprints() for p in f.Pads()};gs={};cs={};adj={};contact=[];byvia=collections.defaultdict(set)
 for l in b.GetEnabledLayers().CuStack():
  name=b.GetLayerName(l);g=k.SHAPE_POLY_SET()
  for z in b.Zones():
   if not z.GetIsRuleArea() and z.IsOnLayer(l) and z.GetNetname()=='GND':g.BooleanAdd(z.GetFilledPolysList(l))
  gs[name]=g
  for i in range(g.OutlineCount()):key=f'{name}:{i}';cs[key]=g.UnitSet(i);adj[key]=set()
 gvs={u:t for u,t in ts.items() if isinstance(t,k.PCB_VIA) and t.GetNetname()=='GND'}
 for u,v in gvs.items():
  box=v.GetBoundingBox()
  for key,g in cs.items():
   if not g.BBox().Intersects(box):continue
   proof=patch(v,g)
   if proof:contact.append({'via':u,'position':xy(v.GetPosition()),'component':key,'annular_patch':proof});byvia[u].add(key)
  for key in byvia[u]:adj[key]|=byvia[u]-{key}
 roots={max((q for q in cs if q.startswith(l+':')),key=lambda q:area(cs[q])) for l in ['In1.Cu','In4.Cu']};connected={next(iter(roots))};todo=list(connected)
 while todo:
  n=todo.pop()
  for q in adj[n]-connected:connected.add(q);todo.append(q)
 assert roots<=connected,('Main In1/In4 roots lack finite interlayer witness',label)
 projection=[];reference_components=set();unions={}
 conductors={**{u:t for u,t in ts.items() if not isinstance(t,k.PCB_VIA)},**{uid(x):x for x in b.GetDrawings() if isinstance(x,k.PCB_SHAPE) and x.GetNetname() in ['USB_DP','USB_DM']}}
 for net in ['USB_DP','USB_DM']:
  for layer,reference in refs.items():
   l=b.GetLayerID(layer);objects=[o for o in conductors.values() if o.GetNetname()==net and o.GetLayer()==l];p=k.SHAPE_POLY_SET()
   for o in objects:p.BooleanAdd(polygon(o,l))
   if not objects:continue
   unions[net,layer]=p
   for rl in reference:
    hitcs=[]
    for key,g in cs.items():
     if key.startswith(rl+':') and p.BBox().Intersects(g.BBox()):
      overlap=area(intersect(p,g))
      if overlap>1e-10:hitcs.append({'component':key,'overlap_area_mm2':overlap,'finite_via_connected_to_main_ground':key in connected});reference_components.add(key)
    uncovered=area(subtract(p,gs[rl]));projection.append({'net':net,'routing_layer':layer,'reference_layer':rl,'conductor_object_count':len(objects),'full_width_copper_union_area_mm2':area(p),'projected_ground_overlap_area_mm2':area(intersect(p,gs[rl])),'uncovered_area_mm2':uncovered,'uncovered_fraction':uncovered/area(p),'touched_actual_components':hitcs})
 transitions=[]
 for u,v in ts.items():
  if not isinstance(v,k.PCB_VIA) or v.GetNetname() not in ['USB_DP','USB_DM']:continue
  layers=sorted({b.GetLayerName(t.GetLayer()) for t in ts.values() if not isinstance(t,k.PCB_VIA) and t.GetNetname()==v.GetNetname() and hit(t.GetEffectiveShape(t.GetLayer()),v.GetEffectiveShape(t.GetLayer()))});wanted=sorted(set(r for l in layers for r in refs.get(l,[])));nearest=[]
  for rl in wanted:
   candidates=[]
   for w,g in gvs.items():
    comps=[c for c in byvia[w] if c.startswith(rl+':') and c in connected]
    if comps:candidates.append((math.dist(xy(v.GetPosition()),xy(g.GetPosition())),w,comps))
   if candidates:
    dist,w,comps=min(candidates);nearest.append({'reference_layer':rl,'distance_center_mm':dist,'ground_via':w,'ground_via_position':xy(gvs[w].GetPosition()),'finite_contact_components':comps})
   else:nearest.append({'reference_layer':rl,'finite_main_ground_contact_witness':None})
  transitions.append({'via':u,'net':v.GetNetname(),'position':xy(v.GetPosition()),'incident_routing_layers':layers,'nearest_measured_finite_ground_vias':nearest})
 # Actual retained ground paths from protection/decoupling pads to finite main-plane vias.
 groundobjs={**{u:t for u,t in ts.items() if t.GetNetname()=='GND'},**{u:p for u,p in pads.items() if p.GetNetname()=='GND'}};gadj={u:[] for u in groundobjs};proofedges={}
 for u,o in groundobjs.items():
  for w,q in groundobjs.items():
   if w>=u:continue
   for l in b.GetEnabledLayers().CuStack():
    if o.IsOnLayer(l) and q.IsOnLayer(l) and o.GetBoundingBox().Intersects(q.GetBoundingBox()) and hit(o.GetEffectiveShape(l),q.GetEffectiveShape(l)):
     overlap=area(intersect(polygon(o,l),polygon(q,l)))
     if overlap>1e-6:gadj[u].append(w);gadj[w].append(u);proofedges[tuple(sorted([u,w]))]={'layer':b.GetLayerName(l),'finite_overlap_area_mm2':overlap};break
 targets=[u for u,p in pads.items() if p.GetNetname()=='GND' and p.GetParentFootprint().GetReference() in ['C28','U7','C27','C31','U14','U10','C18','C19','C6','C11','U1','U5','C15','C21','C22','U11','U2','C12','C13']];groundpaths=[]
 for target in targets:
  todo=[(target,[target])];seen={target};found=None
  while todo:
   u,path=todo.pop(0)
   if u in byvia and any(q in connected and q.startswith(('In1.Cu:','In4.Cu:')) for q in byvia[u]):found=path;break
   for w in gadj[u]:
    if w not in seen:seen.add(w);todo.append((w,path+[w]))
  # Some inherited decoupling pads attach through a finite filled outer-plane island rather than an explicit trace.
  if not found:
   todo=[(target,[target])];seen={target}
   while todo and not found:
    u,path=todo.pop(0);obj=groundobjs[u]
    for component,g in cs.items():
     if component not in connected:continue
     lname=component.split(':')[0];layer=b.GetLayerID(lname)
     if not obj.IsOnLayer(layer) or not obj.GetBoundingBox().Intersects(g.BBox()):continue
     overlap=area(intersect(polygon(obj,layer),g))
     if overlap<=1e-6:continue
     witnesses=[v for v in byvia if component in byvia[v]]
     if not witnesses:continue
     v=min(witnesses,key=lambda v:math.dist(xy(obj.GetPosition()),xy(gvs[v].GetPosition())))
     proofedges[tuple(sorted([u,component]))]={'layer':lname,'finite_overlap_area_mm2':overlap,'kind':'actual pad/track to filled component finite intersection'}
     proofedges[tuple(sorted([component,v]))]=next(c for c in contact if c['via']==v and c['component']==component)
     found=path+[component,v];break
    for w in gadj[u]:
     if w not in seen:seen.add(w);todo.append((w,path+[w]))
  assert found,('No finite main-plane ground witness including actual filled outer-plane paths',label,target)
  groundpaths.append({'pad':target,'ref':pads[target].GetParentFootprint().GetReference(),'pin':pads[target].GetNumber(),'finite_copper_path_to_ground_via':found,'edge_proofs':[proofedges[tuple(sorted([aa,bb]))] for aa,bb in zip(found,found[1:])],'via_main_component_contacts':sorted(q for q in byvia[found[-1]] if q in connected)})
 data[label]={'board_sha256':sha(D/'hardware/nexus-style-fc.kicad_pcb'),'filled_components':[{'id':q,'area_mm2':area(g),'finite_via_connected_to_main_ground':q in connected} for q,g in cs.items()],'main_plane_root_components':sorted(roots),'finite_ground_via_component_contacts':contact,'full_width_usb_projection':projection,'reference_components_without_finite_via_path':sorted(reference_components-connected),'usb_transition_ground_via_distances':transitions,'U7_C28_actual_finite_ground_paths':groundpaths};fills[label]=gs
 print(label,'components',len(cs),'contacts',len(contact),'unproved referenced',len(reference_components-connected),flush=True)
changes=[]
for l in fills['source']:
 a,b=fills['source'][l],fills['candidate'][l];changes.append({'layer':l,'removed_ground_area_mm2':area(subtract(a,b)),'added_ground_area_mm2':area(subtract(b,a)),'source_component_count':a.OutlineCount(),'candidate_component_count':b.OutlineCount()})
b=boards['candidate'];envelope=k.SHAPE_POLY_SET();records=[]
for t in b.GetTracks():
 if not isinstance(t,k.PCB_VIA) and t.GetNetname()=='USB_DP' and t.GetLayer()==k.In1_Cu:
  envelope.BooleanAdd(polygon(t,k.In1_Cu,.2));records.append(uid(t))
loss=subtract(fills['source']['In1.Cu'],fills['candidate']['In1.Cu']);local=intersect(loss,envelope);localbox=local.BBox();join={'DP_In1_track_uuids':records,'scope':'Actual source-to-candidate In1 ground removal intersected with the new DP join copper inflated by 0.200 mm. Overlapping antipads/donor changes prevent exclusive causal attribution.','ground_loss_within_join_envelope_mm2':area(local),'ground_added_within_join_envelope_mm2':area(intersect(subtract(fills['candidate']['In1.Cu'],fills['source']['In1.Cu']),envelope)),'lost_copper_bbox_mm':{'position':xy(localbox.GetPosition()),'size':xy(localbox.GetSize())},'lost_region_count':local.OutlineCount()}
out={'status':'MEASURED: exact filled reference components and finite return witnesses; system qualification remains open','source_board_sha256':data['source']['board_sha256'],'candidate_board_sha256':data['candidate']['board_sha256'],'source_to_candidate_plane_changes':changes,'compact_DP_In1_join_plane_cut':join,'measurements':data,'method':'Native KiCad polygons with 1 nm inside approximation. Full-width projection is area of actual trace/taper copper, not a centerline sample. A plane-component graph uses explicit .127 x .020 mm patches outside each .200 mm ground-via drill and inside its .450 mm annulus; no zero-area or zone-definition connectivity is inferred. Unproved reference components are retained in the report rather than treated as disconnected. U7/C28 ground-path overlaps are finite and all original geometry is independently invariant-checked.','qualification':'Neither projection percentage nor nearest-via distance establishes return impedance. Mixed In2/In4 reference, DP In1 plane cut/coupling under connector DM, fabrication tolerance, USB impedance and common-mode behavior remain engineering gates. Existing 96 finite shield-spoke regions and U10/C18/C19 paths are separately reverified in this same candidate.'};(O/'usb-reference-return-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'plane_changes':changes,'join_cut':join,'unproved_reference_components':data['candidate']['reference_components_without_finite_via_path']},indent=2))

# Additional source-bound capacitor return and VIN-transition witnesses.
capreturn={}
for label in ['source','candidate']:
 d=data[label]; bs=boards[label]; tt={uid(t):t for t in bs.GetTracks()}; contacts=d['finite_ground_via_component_contacts']; roots=set(d['main_plane_root_components']); moved=[]
 for v in captr['moved_vias']+[r for r in captr['added_primitives'] if r['kind']=='via']:
  u=v['uuid']
  if u not in tt or tt[u].GetNetname()!='GND':continue
  proofs=[q for q in contacts if q['via']==u and q['component'] in roots]
  assert {q['component'].split(':')[0] for q in proofs}=={'In1.Cu','In4.Cu'},(label,'moved/new ground via not finite-root attached',u)
  moved.append({'via':u,'position':xy(tt[u].GetPosition()),'main_plane_proofs':proofs})
 transitions=[]
 for v in captr['added_primitives']:
  if v['kind']!='via' or v['net']!='VSYS' or v['uuid'] not in tt:continue
  pos=xy(tt[v['uuid']].GetPosition());near=[]
  for q in contacts:
   if q['component'] not in roots:continue
   dist=math.dist(pos,q['position'])
   near.append((dist,q['via'],q['component'],q['position'],q['annular_patch']))
  near.sort();unique={}
  for q in near:
   if q[1] not in unique:unique[q[1]]={'distance_mm':q[0],'via':q[1],'position':q[3],'finite_main_components':[]}
   unique[q[1]]['finite_main_components'].append(q[2])
  transitions.append({'signal_via':v['uuid'],'role':v['proposal_id'],'position':pos,'nearest_five_finite_ground_transfers':list(unique.values())[:5]})
 proj=[]
 if label=='candidate':
  groups=collections.defaultdict(list)
  for q in captr['added_primitives']:
   if q['kind']=='segment':groups[(q['proposal_id'].split('/')[0],q['layer'])].append(q['uuid'])
  for (role,lay),ids in groups.items():
   if not role.startswith(('VIN','EN','GND','C27','C31','west','VX')):continue
   union=k.SHAPE_POLY_SET()
   for u in ids:union.BooleanAdd(polygon(tt[u],tt[u].GetLayer()))
   for ref in refs.get(lay,[]):
    g=fills[label][ref];proj.append({'role':role,'layer':lay,'reference':ref,'uuids':ids,'full_copper_area_mm2':area(union),'uncovered_area_mm2':area(subtract(union,g)),'overlap_area_mm2':area(intersect(union,g))})
 capreturn[label]={'moved_or_new_ground_via_main_plane_contacts':moved,'U10_C18_C19_U14_C27_C31_U7_C28_finite_ground_paths':d['U7_C28_actual_finite_ground_paths'],'VIN_EN_cap_transition_ground_transfers':transitions,'new_power_return_full_width_projection':proj}
(O/'cap-input-actual-return-verification.json').write_text(json.dumps({'status':'PASS finite main-plane attachments and explicit pad-to-via paths; impedance/HF-loop qualification remains open','source_sha256':data['source']['board_sha256'],'candidate_sha256':data['candidate']['board_sha256'],'measurements':capreturn,'qualification':'Actual refill polygons and finite conductive patches establish topology. They do not establish high-frequency input impedance, loop inductance or assembly tent integrity.'},indent=2)+'\n')
print('CAP INPUT FINITE RETURNS PASS',flush=True)
