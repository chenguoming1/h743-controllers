from pathlib import Path
import pcbnew as k,json,hashlib,sys,math,heapq,collections
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda x:x.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));j=json.loads((O/'source-proposal.json').read_text());mp=tr['proposal_to_native_uuid'];ERROR=500

def clone(p):return k.SHAPE_POLY_SET(p)
def poly_of(t,l):
 q=k.SHAPE_POLY_SET();t.TransformShapeToPolygon(q,l,0,ERROR,k.ERROR_OUTSIDE);return q

def hit(a,b):
 r=a.Collide(b,0);return r[0] if isinstance(r,tuple) else bool(r)

def rectangle(points):
 q=k.SHAPE_POLY_SET();c=k.SHAPE_LINE_CHAIN()
 for p in points:c.Append(vec(p))
 c.SetClosed(True);q.AddOutline(c);return q

def area_missing(shape,ground):
 q=clone(shape);q.BooleanSubtract(ground);return abs(q.Area())/1e12

def patch_at(via,poly):
 p=xy(via.GetPosition());rad=via.GetWidth(k.F_Cu)/2e6;drill=via.GetDrillValue()/2e6
 for angle in range(0,360,15):
  a=math.radians(angle);d=(math.cos(a),math.sin(a));n=(-d[1],d[0]);c=(p[0]+.15*d[0],p[1]+.15*d[1]);points=[(c[0]+ax*.01*d[0]+ny*.0635*n[0],c[1]+ax*.01*d[1]+ny*.0635*n[1]) for ax,ny in [(-1,-1),(1,-1),(1,1),(-1,1)]]
  if not all(drill+.001<math.dist(p,x)<rad for x in points):continue
  if area_missing(rectangle(points),poly)<1e-10:return {'angle_deg':angle,'annular_patch_width_mm':.127,'axial_depth_mm':.02,'corners':points}
 return None

results={}
for label,D in [('before',S),('after',O)]:
 P=D/'hardware/nexus-style-fc.kicad_pcb';b=k.LoadBoard(str(P));ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};ls=list(b.GetEnabledLayers().CuStack());ground={};components={}
 for l in ls:
  q=k.SHAPE_POLY_SET()
  for z in b.Zones():
   if not z.GetIsRuleArea() and z.GetNetname()=='GND' and z.IsOnLayer(l):q.BooleanAdd(z.GetFilledPolysList(l))
  if q.OutlineCount():ground[l]=q;components[l]=[q.UnitSet(i) for i in range(q.OutlineCount())]
 groups=[]
 if label=='before':
  for name,items in [('output',j['remove']['output_items']),('input',j['remove']['input_items'])]:
   for l in sorted({t['layers'][0] for t in items if t['kind']=='segment'}):groups.append((name,l,[t['uuid'] for t in items if t['kind']=='segment' and t['layers'][0]==l]))
 else:
  groups=[('output','F.Cu',[mp['proposal:OUT_F:'+str(i)] for i in range(4)]),('input','B.Cu',[mp['proposal:IN_B:0']]),('input','F.Cu',[mp['proposal:IN_F:'+str(i)] for i in range(2)])]
 projection=[]
 for role,layer,ids in groups:
  l=b.GetLayerID(layer);ref=k.In1_Cu if l==k.F_Cu else k.In4_Cu if l==k.B_Cu else k.In2_Cu;refs=[ref]+([k.In4_Cu] if l==k.In3_Cu else []);path=k.SHAPE_POLY_SET()
  for u in ids:path.BooleanAdd(poly_of(ts[u],l))
  for ref in refs:
   q=ground[ref];total=abs(path.Area())/1e12;missing=area_missing(path,q);project=clone(path);project.BooleanIntersection(q);ids_touch=[i for i,c in enumerate(components[ref]) if hit(project,c)];eroded=clone(q);eroded.Deflate(63500,k.CORNER_STRATEGY_ROUND_ALL_CORNERS,ERROR);safe=clone(path);safe.BooleanIntersection(eroded);safeids=[i for i in range(eroded.OutlineCount()) if hit(safe,eroded.UnitSet(i))]
   projection.append({'role':role,'routing_layer':layer,'reference_layer':b.GetLayerName(ref),'track_uuids':ids,'full_width_copper_polygon_area_mm2':total,'uncovered_full_width_copper_area_mm2':missing,'full_width_area_coverage_fraction':1-missing/total,'all_full_width_projection_covered':missing<1e-10,'touched_original_ground_component_ids':ids_touch,'ground_component_areas_mm2':[abs(c.Area())/1e12 for c in components[ref]],'covered_projected_area_after_0_0635_mm_GND_erosion_mm2':abs(safe.Area())/1e12,'touched_eroded_component_ids':safeids,'eroded_component_areas_mm2':[abs(eroded.UnitSet(i).Area())/1e12 for i in safeids]})
 # Unchanged direct GND primitive topology from local pins to through vias, then finite contact with each actual filled component.
 objs={u:q for u,q in {**ts,**ps}.items() if q.GetNetname()=='GND'};adj=collections.defaultdict(list);conn=b.GetConnectivity()
 for u,t in ts.items():
  if t.GetNetname()!='GND':continue
  for q in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
   w=uid(q)
   if w not in objs or w==u:continue
   common=[l for l in ls if t.IsOnLayer(l) and objs[w].IsOnLayer(l) and hit(t.GetEffectiveShape(l),objs[w].GetEffectiveShape(l))]
   if common:adj[u].append(w);adj[w].append(u)
 local=[]
 for ref,pin in [('U10','2'),('C19','2'),('C18','2')]:
  p=next(p for p in ps.values() if p.GetParentFootprint().GetReference()==ref and p.GetNumber()==pin);heap=[(0,uid(p),[uid(p)])];seen=set();paths=[]
  while heap:
   cost,u,path=heapq.heappop(heap)
   if u in seen:continue
   seen.add(u);obj=objs[u]
   if isinstance(obj,k.PCB_VIA) and math.dist(xy(p.GetPosition()),xy(obj.GetPosition()))<=4:
    contacts=[]
    for l,cps in components.items():
     for ci,c in enumerate(cps):
      proof=patch_at(obj,c)
      if proof:contacts.append({'layer':b.GetLayerName(l),'component_id':ci,'component_area_mm2':abs(c.Area())/1e12,'finite_annular_contact':proof})
    paths.append({'via':u,'at':xy(obj.GetPosition()),'primitive_contact_path':path,'path_weight_mm':cost,'finite_zone_contacts':contacts})
   for w in adj[u]:
    q=objs[w];weight=q.GetLength()/1e6 if isinstance(q,k.PCB_TRACK) and not isinstance(q,k.PCB_VIA) else 0;heapq.heappush(heap,(cost+weight,w,path+[w]))
  paths=sorted(paths,key=lambda x:x['path_weight_mm']);local.append({'ref':ref,'pin':pin,'pad_uuid':uid(p),'via_paths_within_4_mm':paths[:5],'path_weight_limit':'Sum of traversed whole track centerline lengths; not pad-center electrical loop length. Connectivity paths retain inherited widths and contacts.'})
 results[label]={'pcb_sha256':sha(P),'projection':projection,'local_GND_pin_to_actual_filled_plane_paths':local}
assert results['before']['pcb_sha256']==tr['source_board_sha256']
out={'status':'Measured post-native-refill full-width GND projection and finite plane contact topology; qualification remains open','method':'Native full-width track polygons with conservative 0.0005 mm arc approximation; polygon Boolean intersection/subtraction with saved GND fills, including holes. Separate 0.0635 mm ground erosion exposes narrow connections; no centerline-only coverage claim. Local GND primitive physical-contact paths terminate at through-via annular patches of 0.127 by 0.020 mm contained in actual same-plane components. These geometric checks do not establish high-frequency return impedance or regulator stability.','measurements':results,'explicit_tradeoff':{'input_planar_delta_mm':.389325,'input_modeled_barrel_delta_mm':1.4134,'C19_effective_capacitance_and_ESR':'Separate manufacturer review; not qualified by routing.'}};(O/'return-topology-comparison.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'measurements':{label:{'pcb_sha256':x['pcb_sha256'],'projection':[ {k:v for k,v in p.items() if k not in ['track_uuids','ground_component_areas_mm2','eroded_component_areas_mm2']} for p in x['projection']],'GND_ports':[{'ref':p['ref'],'via_path_count':len(p['via_paths_within_4_mm'])} for p in x['local_GND_pin_to_actual_filled_plane_paths']]} for label,x in results.items()}},indent=2))
