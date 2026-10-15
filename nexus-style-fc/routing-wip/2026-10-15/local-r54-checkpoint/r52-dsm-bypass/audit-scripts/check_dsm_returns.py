from pathlib import Path
import pcbnew as k,json,sys,math,hashlib
O=Path(sys.argv[1]).resolve();tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda x:x.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6)
def missing(a,b):
 p=k.SHAPE_POLY_SET(a);p.BooleanSubtract(b);return abs(p.Area())/1e12
boards=[k.LoadBoard(str(D/'hardware/nexus-style-fc.kicad_pcb')) for D in [S,O]];fills=[]
for b in boards:
 d={}
 for l in b.GetEnabledLayers().CuStack():
  p=k.SHAPE_POLY_SET()
  for z in b.Zones():
   if z.GetNetname()=='GND' and not z.GetIsRuleArea() and z.IsOnLayer(l):p.BooleanAdd(z.GetFilledPolysList(l))
  d[l]=p
 fills.append(d)
plane=[]
for l in [k.In1_Cu,k.In4_Cu]:
 lost=missing(fills[0][l],fills[1][l]);added=missing(fills[1][l],fills[0][l]);assert lost==0 and added==0,(l,lost,added);plane.append({'layer':boards[1].GetLayerName(l),'lost_GND_area_mm2':lost,'added_GND_area_mm2':added,'exact_saved_filled_copper_equal':True})
b=boards[1];ts={uid(t):t for t in b.GetTracks()};r=next(r for r in tr['routes'] if r['name']=='DSM_B');path=k.SHAPE_POLY_SET()
for u in r['new_uuids']:ts[u].TransformShapeToPolygon(path,k.B_Cu,0,500,k.ERROR_OUTSIDE)
full_area=abs(path.Area())/1e12;full_missing=missing(path,fills[1][k.In4_Cu]);outside=k.SHAPE_POLY_SET(path);exclusions=[]
for u in [tr['existing_top_via'],tr['existing_bottom_via']]:
 c=xy(ts[u].GetPosition());poly=k.SHAPE_POLY_SET();line=k.SHAPE_LINE_CHAIN();radius=.426/math.cos(math.pi/128)
 for i in range(128):
  ang=2*math.pi*i/128;line.Append(k.VECTOR2I(round((c[0]+radius*math.cos(ang))*1e6),round((c[1]+radius*math.sin(ang))*1e6)))
 line.SetClosed(True);poly.AddOutline(line);outside.BooleanSubtract(poly);exclusions.append({'existing_via':u,'center':c,'antipad_reference_exclusion_radius_mm':.426,'basis':'.225 mm via radius + .200 mm plane clearance + .001 mm geometry tolerance; no new via or antipad.'})
g=fills[1][k.In4_Cu];best=max(range(g.OutlineCount()),key=lambda i:abs(g.UnitSet(i).Area()));component=g.UnitSet(best);missing_outside=missing(outside,component);assert missing_outside<1e-10,missing_outside
out={'status':'PASS: main GND planes exactly unchanged; new outer DSM route has continuous full-width In4 reference outside its two existing via antipads','source_board_sha256':sha(S/'hardware/nexus-style-fc.kicad_pcb'),'candidate_board_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'main_plane_comparison':plane,'new_B_route':{'full_track_polygon_area_mm2':full_area,'full_area_GND_coverage_fraction':1-full_missing/full_area,'outside_existing_antipads_area_mm2':abs(outside.Area())/1e12,'uncovered_area_outside_existing_antipads_mm2':missing_outside,'actual_ground_component_index':best,'actual_ground_component_area_mm2':abs(component.Area())/1e12,'exclusions':exclusions},'consequence':'The unchanged In1/In4 filled copper and unchanged original copper/ground vias preserve the previously proven U10/C18/C19 and R20/U7/J6 main-plane contacts. Separate shield-region comparison accompanies this receipt.','qualification':'Source-bound geometry and reference continuity only. Added travel through two already-existing via barrels and the changed signal path remain part of final signal-integrity review; no USB or system qualification is inferred.'};(O/'dsm-return-topology.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
