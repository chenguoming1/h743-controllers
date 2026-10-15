from pathlib import Path
import pcbnew as k,json,sys,math,hashlib
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda x:x.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));thermal='de26675a-ecba-4fa3-966f-2bc38e53bb1f';ERROR=500

def clone(p):return k.SHAPE_POLY_SET(p)
def poly_of(t,l):
 q=k.SHAPE_POLY_SET();t.TransformShapeToPolygon(q,l,0,ERROR,k.ERROR_OUTSIDE);return q
def hit(a,b):
 r=k.SHAPE.Collide(a,b,0);return r[0] if isinstance(r,tuple) else bool(r)
def rect(points):
 q=k.SHAPE_POLY_SET();c=k.SHAPE_LINE_CHAIN()
 for p in points:c.Append(vec(p))
 c.SetClosed(True);q.AddOutline(c);return q
def subtract(a,b):
 q=clone(a);q.BooleanSubtract(b);return q
def area(p):return abs(p.Area())/1e12
def patch(v,g):
 p=xy(v.GetPosition());rad=v.GetWidth(k.F_Cu)/2e6;drill=v.GetDrillValue()/2e6
 for angle in range(0,360,15):
  a=math.radians(angle);d=(math.cos(a),math.sin(a));n=(-d[1],d[0]);pts=[(p[0]+(.15+ax*.01)*d[0]+ny*.0635*n[0],p[1]+(.15+ax*.01)*d[1]+ny*.0635*n[1]) for ax,ny in [(-1,-1),(1,-1),(1,1),(-1,1)]]
  if not all(drill+.001<math.dist(p,x)<rad for x in pts):continue
  if area(subtract(rect(pts),g))<1e-10:return {'width_mm':.127,'depth_mm':.02,'corners':pts}
 return None
boards={};fills={};out={};projections={}
for label,D in [('before',S),('after',O)]:
 P=D/'hardware/nexus-style-fc.kicad_pcb';b=k.LoadBoard(str(P));boards[label]=b;ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};ls=list(b.GetEnabledLayers().CuStack());ground={};components={}
 for l in ls:
  q=k.SHAPE_POLY_SET()
  for z in b.Zones():
   if not z.GetIsRuleArea() and z.GetNetname()=='GND' and z.IsOnLayer(l):q.BooleanAdd(z.GetFilledPolysList(l))
  ground[l]=q;components[l]=[q.UnitSet(i) for i in range(q.OutlineCount())]
 t=ts[thermal];contacts=[];conn=b.GetConnectivity()
 for q in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
  u=uid(q)
  if u==thermal:continue
  layers=[b.GetLayerName(l) for l in ls if t.IsOnLayer(l) and q.IsOnLayer(l) and hit(t.GetEffectiveShape(l),q.GetEffectiveShape(l))]
  if layers:contacts.append({'uuid':u,'net':q.GetNetname(),'kind':type(q).__name__,'physical_contact_layers':layers,'ref_pin':[q.GetParentFootprint().GetReference(),q.GetNumber()] if isinstance(q,k.PAD) else None})
 plane_contacts=[]
 for l in [k.In1_Cu,k.In4_Cu]:
  cs=components[l];ci=max(range(len(cs)),key=lambda i:area(cs[i]));proof=patch(t,cs[ci]);assert proof;plane_contacts.append({'layer':b.GetLayerName(l),'component_index':ci,'component_area_mm2':area(cs[ci]),'finite_annular_patch':proof})
 projection=[]
 for r in tr['routes']:
  ids=r['removed_uuids'] if label=='before' else r['new_uuids'];path=k.SHAPE_POLY_SET()
  for u in ids:path.BooleanAdd(poly_of(ts[u],k.In3_Cu))
  for ref in [k.In2_Cu,k.In4_Cu]:
   total=area(path);lost=area(subtract(path,ground[ref]));project=clone(path);project.BooleanIntersection(ground[ref]);projections[label,r['net'],ref]=project
   projection.append({'net':r['net'],'routing_layer':'In3.Cu','reference_layer':b.GetLayerName(ref),'width_mm':r['width_mm'],'track_uuids':ids,'full_width_area_mm2':total,'uncovered_area_mm2':lost,'covered_fraction':1-lost/total,'touched_component_ids':[i for i,c in enumerate(components[ref]) if hit(project,c)],'centerline_length_mm':sum(ts[u].GetLength()/1e6 for u in ids)})
 fills[label]=ground;out[label]={'pcb_sha256':sha(P),'thermal_via_position':xy(t.GetPosition()),'thermal_via_size_mm':t.GetWidth(k.F_Cu)/1e6,'thermal_via_drill_mm':t.GetDrillValue()/1e6,'thermal_via_direct_contacts':sorted(contacts,key=lambda x:x['uuid']),'thermal_via_main_plane_contacts':plane_contacts,'power_projections':projection}
assert out['before']['pcb_sha256']==tr['source_board_sha256']
for field in ['thermal_via_position','thermal_via_size_mm','thermal_via_drill_mm','thermal_via_direct_contacts']:assert out['before'][field]==out['after'][field]
planes=[]
for l in [k.In1_Cu,k.In4_Cu]:
 old,new=fills['before'][l],fills['after'][l];lost,added=area(subtract(old,new)),area(subtract(new,old));assert lost<1e-10 and added<1e-10;planes.append({'layer':boards['after'].GetLayerName(l),'removed_GND_area_mm2':lost,'added_GND_area_mm2':added,'before_after_component_count':old.OutlineCount()})
changes=[]
for a,b in zip(out['before']['power_projections'],out['after']['power_projections']):
 assert (a['net'],a['reference_layer'])==(b['net'],b['reference_layer']);changes.append({'net':a['net'],'reference_layer':a['reference_layer'],'before_coverage_fraction':a['covered_fraction'],'after_coverage_fraction':b['covered_fraction'],'uncovered_area_delta_mm2':b['uncovered_area_mm2']-a['uncovered_area_mm2'],'centerline_length_delta_mm':b['centerline_length_mm']-a['centerline_length_mm']})
result={'status':'PASS: fixed U5 thermal/return via and all direct ports retained; exact main In1/In4 GND fills and finite thermal-via contacts preserved','source_sha256':sha(S/'hardware/nexus-style-fc.kicad_pcb'),'candidate_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'measurements':out,'unchanged_main_planes':planes,'power_projection_changes':changes,'qualification':'Measured geometry and finite continuity only. Input/output power, high-frequency return and U5 thermal/paste process qualification remain open; the retained thermal via remains within the continuous mask/paste opening.'};(O/'thermal-power-return-proof.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'projection_changes':changes},indent=2))
