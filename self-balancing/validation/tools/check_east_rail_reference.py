#!/usr/bin/python3
"""Independent exact local DC-rail edge/return geometry disposition."""
import os,json,hashlib,math
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
D=Path(__file__).resolve().parent;SRC=Path('/workspace/shared/storm32-redesign/research/controller-r3s-p6-route-cleanup/candidate-attachments.kicad_pcb');PACK=Path('/workspace/shared/storm32-redesign/research/controller-r3s-p6-route-cleanup/east-rail-reference-disposition.json');sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();packet=json.loads(PACK.read_text());H=packet['source_sha256'];assert sha(SRC)==H;b=p.LoadBoard(str(SRC));tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};record=lambda t:{'id':t.m_Uuid.AsString(),'net':t.GetNetname(),'layer':t.GetLayerName(),'start':[t.GetStart().x/1e6,t.GetStart().y/1e6],'end':[t.GetEnd().x/1e6,t.GetEnd().y/1e6],'width_mm':t.GetWidth()/1e6};errors=[]
for r in packet['removed']:assert record(tracks[r['id']])==r
r=packet['proposed_track'];assert r['net']=='3V3_CORE' and r['layer']=='B.Cu' and r['width_mm']==.45 and r['start']==[37.5,26.2] and r['end']==[37.5,26.7]
t=p.PCB_TRACK(b);t.SetLayer(p.B_Cu);t.SetNetCode(tracks[packet['removed'][0]['id']].GetNetCode());t.SetWidth(450000);t.SetStart(p.VECTOR2I(37500000,26200000));t.SetEnd(p.VECTOR2I(37500000,26700000))
def copper(tt):
 out=p.SHAPE_POLY_SET()
 for v in tt:
  q=p.SHAPE_POLY_SET();v.TransformShapeToPolygon(q,p.B_Cu,0,100,p.ERROR_OUTSIDE);out.BooleanAdd(q)
 return out
plane=p.SHAPE_POLY_SET();outer=p.SHAPE_POLY_SET()
for z in b.Zones():
 if z.GetNetname()=='GND' and not z.GetIsRuleArea() and z.IsOnLayer(p.In4_Cu):plane.BooleanAdd(z.GetFilledPolysList(p.In4_Cu))
for oi in range(plane.OutlineCount()):outer.BooleanAdd(p.SHAPE_POLY_SET(plane.COutline(oi)))
for v in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]:
 if isinstance(v,p.PCB_VIA) or isinstance(v,p.PAD) and v.HasHole():
  hole=p.SHAPE_POLY_SET();v.GetEffectiveHoleShape().TransformToPolygon(hole,100,p.ERROR_OUTSIDE);plane.BooleanSubtract(hole)
old=copper([v for v in b.GetTracks() if not isinstance(v,p.PCB_VIA) and v.GetNetname()=='3V3_CORE' and v.GetLayer()==p.B_Cu]);old.BooleanSubtract(plane);unsupported=copper([t]);unsupported.BooleanSubtract(plane);added=p.SHAPE_POLY_SET(unsupported);added.BooleanSubtract(old);inside=p.SHAPE_POLY_SET(added);inside.BooleanIntersection(outer)
ct=p.PCB_TRACK(b);ct.SetLayer(p.B_Cu);ct.SetWidth(1000);ct.SetStart(t.GetStart());ct.SetEnd(t.GetEnd());center=copper([ct]);center.BooleanSubtract(plane)
rectangle=p.SHAPE_POLY_SET();rectangle.NewOutline()
for x,y in [(37.05,26.0),(37.649,26.0),(37.649,26.9),(37.05,26.9)]:rectangle.Append(round(x*1e6),round(y*1e6))
missing=p.SHAPE_POLY_SET(rectangle);missing.BooleanSubtract(plane)
via=tracks['6205b157-b859-4a01-8c91-789457fec278'];gap=t.GetEffectiveShape(p.B_Cu).GetClearance(via.GetEffectiveShape(p.B_Cu))/1e6
bb=added.BBox();bbox=[bb.GetLeft()/1e6,bb.GetTop()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6]
if inside.Area()!=0:errors.append('Newly unsupported copper intersects reference outer contour/internal hole')
if center.Area()!=0:errors.append('Centerline loses reference')
if missing.Area()!=0:errors.append('Declared broad inward GND rectangle is interrupted')
if gap<.15:errors.append('Local fixed GND via clearance below .15mm')
if bbox[0]<37.649999 or bbox[2]>37.725001:errors.append('Unsupported extent exceeds declared outward edge strip')
if added.Area()/1e12>.005391978843+1e-12:errors.append('Unsupported added area exceeds declared bound')
report={'status':'ACCEPT EXACT DC-RAIL OUTER-EDGE EXCEPTION; FINAL FULL GATES REQUIRED' if not errors else 'NOT ACCEPTED','source':str(SRC),'source_sha256':H,'proposal_path':str(PACK),'proposal_sha256':sha(PACK),'errors':errors,'net':'3V3_CORE','layer':'B.Cu','exact_proposal':r,'exact_removed':packet['removed'],'native_polygon_error_nm':100,'area_comparison_basis':'Candidate proposal minus all source 3V3_CORE B.Cu uncovered copper, not only the two replaced primitives','declared_local_pair_area_bound_mm2':.005391978843,'new_unsupported_mm2':added.Area()/1e12,'new_unsupported_bbox_mm':bbox,'new_unsupported_inside_reference_outer_contour_mm2':inside.Area()/1e12,'one_um_centerline_tube_unsupported_mm2':center.Area()/1e12,'plane_outer_edge_x_mm':37.65,'trace_center_x_mm':37.5,'outward_centerline_to_plane_edge_mm':.15,'supported_width_mm':.375,'unsupported_outward_width_mm':.075,'supported_fraction_of_nominal_width':.375/.45,'broad_continuous_inward_ground_rectangle_mm':[37.05,26.0,37.649,26.9],'ground_rectangle_missing_area_mm2':missing.Area()/1e12,'ground_return_via_uuid':via.m_Uuid.AsString(),'ground_return_via_xy_mm':[via.GetPosition().x/1e6,via.GetPosition().y/1e6],'trace_to_ground_via_copper_gap_mm':gap,'trace_outer_edge_to_board_edge_mm':.275,'assessment':'This exact regulated DC rail repair replaces a .335410mm physical neck with a continuous .450mm stroke. Its centerline and .375mm of its width remain referenced; only the outward .075mm strip overhangs the unchanged board-edge-side plane boundary. There is no internal foreign-hole/slot exposure, and a continuous broad inward GND strip plus fixed nearby return via remain unchanged. Accept as this specific asymmetric DC return geometry, not a general high-speed/reference waiver.','limits':'Does not claim a tested load-current rating, impedance, or physical thermal/EMI performance. All planes, return vias and source geometry must remain fixed; further inward movement would violate the .150mm foreign-via clearance. Final topology, clearance, attachment, and visual checks remain mandatory.'}
assert sha(SRC)==H;(D/'east-rail-reference-independent.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
