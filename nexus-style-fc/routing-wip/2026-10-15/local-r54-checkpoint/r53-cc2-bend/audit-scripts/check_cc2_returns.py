from pathlib import Path
import pcbnew as k,json,sys,hashlib
O=Path(sys.argv[1]).resolve();tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda x:x.m_Uuid.AsString()
def missing(a,b):
 p=k.SHAPE_POLY_SET(a);p.BooleanSubtract(b);return abs(p.Area())/1e12
bs=[k.LoadBoard(str(D/'hardware/nexus-style-fc.kicad_pcb')) for D in [S,O]];fills=[];projection=[];r=tr['routes'][0]
for label,b,ids in [('before',bs[0],r['removed_uuids']),('after',bs[1],r['new_uuids'])]:
 d={}
 for l in b.GetEnabledLayers().CuStack():
  p=k.SHAPE_POLY_SET()
  for z in b.Zones():
   if z.GetNetname()=='GND' and not z.GetIsRuleArea() and z.IsOnLayer(l):p.BooleanAdd(z.GetFilledPolysList(l))
  d[l]=p
 fills.append(d);ts={uid(t):t for t in b.GetTracks()};path=k.SHAPE_POLY_SET()
 for u in ids:ts[u].TransformShapeToPolygon(path,k.F_Cu,0,500,k.ERROR_OUTSIDE)
 area=abs(path.Area())/1e12;uncovered=missing(path,d[k.In1_Cu]);projection.append({'state':label,'routing_layer':'F.Cu','reference_layer':'In1.Cu','full_width_track_polygon_area_mm2':area,'uncovered_area_mm2':uncovered,'GND_fill_coverage_fraction':1-uncovered/area,'centerline_length_mm':sum(ts[u].GetLength()/1e6 for u in ids)})
plane=[]
for l in [k.In1_Cu,k.In4_Cu]:
 lost=missing(fills[0][l],fills[1][l]);added=missing(fills[1][l],fills[0][l]);assert lost==0 and added==0,(l,lost,added);plane.append({'layer':bs[1].GetLayerName(l),'lost_GND_area_mm2':lost,'added_GND_area_mm2':added,'exact_saved_filled_copper_equal':True})
assert projection[1]['GND_fill_coverage_fraction']>=projection[0]['GND_fill_coverage_fraction']
out={'status':'PASS: exact main-plane preservation and non-regressing scoped CC2 reference projection','source_board_sha256':sha(S/'hardware/nexus-style-fc.kicad_pcb'),'candidate_board_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'main_plane_comparison':plane,'full_width_projection':projection,'qualification':'The inherited partial GND-fill projection is measured, not called a continuous reference or USB/ESD qualification. All main-plane copper and original ground primitives remain unchanged; separate post-refill shield-spoke and R20/U7/J6 component checks are required.'};(O/'cc2-return-topology.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
