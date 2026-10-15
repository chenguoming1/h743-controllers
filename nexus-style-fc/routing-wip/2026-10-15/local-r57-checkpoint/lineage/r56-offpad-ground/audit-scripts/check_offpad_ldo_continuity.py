from pathlib import Path
import pcbnew as k,json,hashlib,sys,math,heapq,collections
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda x:x.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');r51=R/'routing-continuation/r51-ldo-output';mp=json.loads((r51/'transaction.json').read_text())['proposal_to_native_uuid'];ERROR=500

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
checks=[]
for before,after in zip(results['before']['projection'],results['after']['projection']):
 assert [before[k] for k in ['role','routing_layer','reference_layer','track_uuids','full_width_copper_polygon_area_mm2']]==[after[k] for k in ['role','routing_layer','reference_layer','track_uuids','full_width_copper_polygon_area_mm2']]
 assert after['uncovered_full_width_copper_area_mm2']<=before['uncovered_full_width_copper_area_mm2']+1e-10
 assert after['covered_projected_area_after_0_0635_mm_GND_erosion_mm2']>=before['covered_projected_area_after_0_0635_mm_GND_erosion_mm2']-1e-10
 checks.append({'role':before['role'],'layer':before['routing_layer'],'reference':before['reference_layer'],'before_coverage_fraction':before['full_width_area_coverage_fraction'],'after_coverage_fraction':after['full_width_area_coverage_fraction']})
for before,after in zip(results['before']['local_GND_pin_to_actual_filled_plane_paths'],results['after']['local_GND_pin_to_actual_filled_plane_paths']):
 assert before['pad_uuid']==after['pad_uuid'];old={p['via']:p for p in before['via_paths_within_4_mm']};new={p['via']:p for p in after['via_paths_within_4_mm']};assert set(old)==set(new)
 for u,p in old.items():
  q=new[u];added={i for r in tr['routes'] for i in r['new_uuids']};moved={m['uuid'] for m in tr['moved_vias']}
  if u in moved:
   assert [i for i in q['primitive_contact_path'] if i not in added]==p['primitive_contact_path']
   via_route=next(r for r in tr['routes'] if r['moved_via']==u);assert set(q['primitive_contact_path'])&added==set(via_route['new_uuids'])
   assert abs((q['path_weight_mm']-p['path_weight_mm'])-math.dist(*via_route['points']))<1e-8
  else:assert p['primitive_contact_path']==q['primitive_contact_path'] and p['path_weight_mm']==q['path_weight_mm']
  for layer in ['In1.Cu','In4.Cu']:
   assert any(c['layer']==layer for c in p['finite_zone_contacts']) and any(c['layer']==layer for c in q['finite_zone_contacts'])
out={'status':'PASS: retained U10 input/output full-width reference projection does not regress, and C18/C19/U10 local GND paths retain finite In1/In4 contacts, with only the explicit added secondary J2 dogbone length','measurements':results,'projection_checks':checks,'intentional_secondary_return_delta':'C18 main and other local return paths are unchanged; the secondary path through J2 lower GND via adds the exact new 0.250 mm full-land-width dogbone.', 'limitation':'Geometric retention only; inherited input reference, transient/PSRR, capacitor and regulator qualification gaps remain explicit.'};(O/'ldo-return-continuity.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
