from pathlib import Path
import pcbnew as k, json,math,sys,hashlib,collections
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr.get('return_source_directory',tr['source_directory']));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda o:o.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));area=lambda p:abs(p.Area())/1e12
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
 targets=[u for u,p in pads.items() if p.GetNetname()=='GND' and p.GetParentFootprint().GetReference() in ['C28','U7']];groundpaths=[]
 for target in targets:
  todo=[(target,[target])];seen={target};found=None
  while todo:
   u,path=todo.pop(0)
   if u in byvia and any(q in connected and q.startswith(('In1.Cu:','In4.Cu:')) for q in byvia[u]):found=path;break
   for w in gadj[u]:
    if w not in seen:seen.add(w);todo.append((w,path+[w]))
  assert found,('No finite main-plane ground witness',label,target)
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
