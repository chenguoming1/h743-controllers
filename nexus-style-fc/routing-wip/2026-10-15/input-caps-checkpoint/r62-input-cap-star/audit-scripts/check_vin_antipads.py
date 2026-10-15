from pathlib import Path
import pcbnew as k,json,hashlib,math
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'routing-continuation/r62-input-cap-star';tr=json.loads((O/'transaction.json').read_text());b=k.LoadBoard(str(O/'hardware/nexus-style-fc.kicad_pcb'));ts={t.m_Uuid.AsString():t for t in b.GetTracks()};area=lambda p:abs(p.Area())/1e12

def poly(o,l):
 p=k.SHAPE_POLY_SET();o.TransformShapeToPolygon(p,l,0,1,k.ERROR_OUTSIDE);return p
records=[]
for role,layer,reference,viaids in [('VIN_F',k.F_Cu,k.In1_Cu,['cap_via','VIN_via']),('VIN_cap',k.B_Cu,k.In4_Cu,['cap_via']),('VIN_B',k.B_Cu,k.In4_Cu,['VIN_via'])]:
 p=k.SHAPE_POLY_SET();g=k.SHAPE_POLY_SET();openings=k.SHAPE_POLY_SET();centres=[]
 for r in tr['added_primitives']:
  if r['kind']=='segment' and r['proposal_id'].startswith(role+'/'):p.BooleanAdd(poly(ts[r['uuid']],layer))
  if r['kind']=='via' and r['proposal_id'] in viaids:
   v=ts[r['uuid']];t=k.PCB_TRACK(b);t.SetStart(v.GetPosition());t.SetEnd(v.GetPosition());t.SetWidth(850000);t.SetLayer(reference);openings.BooleanAdd(poly(t,reference));centres.append([v.GetPosition().x/1e6,v.GetPosition().y/1e6])
 for z in b.Zones():
  if z.GetNetname()=='GND' and z.IsOnLayer(reference) and not z.GetIsRuleArea():g.BooleanAdd(z.GetFilledPolysList(reference))
 miss=k.SHAPE_POLY_SET(p);miss.BooleanSubtract(g);outside=k.SHAPE_POLY_SET(miss);outside.BooleanSubtract(openings);maxdist=0
 for i in range(miss.OutlineCount()):
  q=miss.COutline(i)
  for j in range(q.PointCount()):
   pt=q.CPoint(j);pos=[pt.x/1e6,pt.y/1e6];maxdist=max(maxdist,min(math.dist(pos,c) for c in centres))
 records.append({'role':role,'routing_layer':b.GetLayerName(layer),'reference_layer':b.GetLayerName(reference),'uncovered_area_mm2':area(miss),'outside_explicit_nominal_0_425mm_via_openings_area_mm2':area(outside),'maximum_uncovered_vertex_distance_to_nearest_transition_center_mm':maxdist,'via_centres':centres,'nominal_antipad_radius_mm':.425})
out={'candidate_sha256':hashlib.sha256((O/'hardware/nexus-style-fc.kicad_pcb').read_bytes()).hexdigest(),'measurements':records,'method':'Actual filled GND subtracted from full-width native track polygons. Remainder compared with the explicit .225 mm via land plus .200 mm zone clearance openings, using 1 nm outside polygon approximations; residuals and maximum uncovered vertex radius reported without relaxed threshold.','qualification':'This locates projection gaps; it does not establish RF return impedance or local capacitor effective impedance.'};(O/'vin-transition-reference-detail.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
