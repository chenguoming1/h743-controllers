from pathlib import Path
import pcbnew as k,json,hashlib,math,collections
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'mechanical-integration/main-signal-slot-08';P=O/'hardware/nexus-style-fc.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();H=sha(P);assert H=='ccd8865f6785fd1cdec0214a08fe409faed4d47bb01e8474f09264ee36acab99';b=k.LoadBoard(str(P));uid=lambda o:o.m_Uuid.AsString();xy=lambda p:[p.x/1e6,p.y/1e6];vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));area=lambda p:abs(p.Area())/1e12;ts={uid(t):t for t in b.GetTracks()};tr=json.loads((O/'transaction.json').read_text());ret=json.loads((O/'usb-reference-return-verification.json').read_text());assert ret['candidate_board_sha256']==H

def poly(o,l,c=0,error=k.ERROR_INSIDE):
 p=k.SHAPE_POLY_SET();o.TransformShapeToPolygon(p,l,round(c*1e6),1,error);return p
def sub(a,b):p=k.SHAPE_POLY_SET(a);p.BooleanSubtract(b);return p
def line(a,z,w,l):
 t=k.PCB_TRACK(b);t.SetStart(vec(a));t.SetEnd(vec(z));t.SetWidth(round(w*1e6));t.SetLayer(l);return t
gs={}
for l in [k.In1_Cu,k.In4_Cu]:
 g=k.SHAPE_POLY_SET()
 for z in b.Zones():
  if z.GetNetname()=='GND' and z.IsOnLayer(l) and not z.GetIsRuleArea():g.BooleanAdd(z.GetFilledPolysList(l))
 assert g.OutlineCount()==1
 for t in ts.values():
  if isinstance(t,k.PCB_VIA):g.BooleanSubtract(poly(line(xy(t.GetPosition()),xy(t.GetPosition()),t.GetDrillValue()/1e6,l),l,error=k.ERROR_OUTSIDE))
 gs[l]=g
route=next(r for r in tr['routes'] if r['name']=='RPM_restore_In2');rpm=k.SHAPE_POLY_SET()
for u in route['new_uuids']:assert ts[u].GetLayer()==k.In2_Cu and ts[u].GetWidth()==127000;rpm.BooleanAdd(poly(ts[u],k.In2_Cu))
missing=sub(rpm,gs[k.In1_Cu]);env=k.SHAPE_POLY_SET();endpoints=['8d4e76ee-941f-4cc6-8549-2fd09506e82a','a7fcb347-a27d-4b04-b06a-966c6999035b']
for u in endpoints:env.BooleanAdd(poly(line(xy(ts[u].GetPosition()),xy(ts[u].GetPosition()),.85,k.In1_Cu),k.In1_Cu,error=k.ERROR_OUTSIDE))
outside=sub(missing,env)
trans=[];contacts=ret['measurements']['candidate']['finite_ground_via_component_contacts']
for u in endpoints:
 row={'RPM_via':u,'position':xy(ts[u].GetPosition()),'nearest_finite_ground_transfer':[]}
 for l in ['In1.Cu:0','In4.Cu:0']:
  near=sorted((q for q in contacts if q['component']==l),key=lambda q:math.dist(row['position'],q['position']))[:1];assert near
  row['nearest_finite_ground_transfer']+=[dict(q,distance_mm=math.dist(row['position'],q['position'])) for q in near]
 trans.append(row)
old=json.loads((R/'mechanical-integration/main-left-vias-06-return-supplement/coplanar-return-verification.json').read_text());direct=[]
for q in old['local_return_detours']:
 if q.get('path_length_mm',0)<9:continue
 a,z=q['path_points'][0],q['path_points'][-1];sweep=poly(line(a,z,.127,k.In4_Cu),k.In4_Cu,error=k.ERROR_OUTSIDE);loss=area(sub(sweep,gs[k.In4_Cu]));direct.append({'retained_B_track':q['B_track'],'net':q['net'],'old_grid_witness_length_mm':q['path_length_mm'],'new_direct_witness_length_mm':math.dist(a,z),'width_mm':.127,'endpoints':[a,z],'uncovered_swept_area_mm2':loss,'contained':loss<1e-8})
assert len(direct)==2 and all(q['contained'] for q in direct),direct
escq=next(q for q in old['local_return_detours'] if q['net']=='ESC');probe=escq['crossing_or_antipad_probe'];v=ts['7f1a6800-531b-461e-9871-0bd4c34be2f3'] if '7f1a6800-531b-461e-9871-0bd4c34be2f3' in ts else next(t for u,t in ts.items() if u.startswith('7f1a6800'));assert v.GetNetname()=='ESC';opening=poly(line(xy(v.GetPosition()),xy(v.GetPosition()),.85,k.In4_Cu),k.In4_Cu,error=k.ERROR_OUTSIDE);region=poly(line(probe,probe,.4,k.In4_Cu),k.In4_Cu,error=k.ERROR_OUTSIDE);uncovered=sub(region,gs[k.In4_Cu]);unexplained=sub(uncovered,opening);esc={'retained_B_track':escq['B_track'],'same_old_probe':probe,'local_measurement_radius_mm':.2,'own_ESC_via':uid(v),'via_position':xy(v.GetPosition()),'probe_to_own_via_mm':math.dist(probe,xy(v.GetPosition())),'own_antipad_radius_mm':.425,'probe_inside_own_antipad':math.dist(probe,xy(v.GetPosition()))<.425,'local_uncovered_ground_mm2':area(uncovered),'uncovered_outside_own_ESC_antipad_mm2':area(unexplained),'interpretation':'The old endpoint-search probe is inside the retained ESC transition antipad. The exact local disk is used to distinguish that necessary transition opening from the removed RPM trench; no missing endpoint is called a disconnected plane.'};assert esc['probe_inside_own_antipad'] and area(unexplained)<1e-8,esc
report={'status':'MEASURED restored RPM In2 reference and direct TAIL return witnesses','candidate_sha256':H,'RPM_actual_full_width_projection':{'copper_area_mm2':area(rpm),'uncovered_In1_area_mm2':area(missing),'transition_envelope_radius_mm':.425,'uncovered_outside_two_transition_envelopes_mm2':area(outside),'outside_bound_components':outside.OutlineCount()},'RPM_transition_finite_ground_contacts':trans,'TAIL_direct_ground_witnesses':direct,'ESC_same_probe_classification':esc,'qualification':'Finite geometry and restored direct .127 mm ground witnesses do not establish SI/EMI or return impedance. Nearest actual ground-transfer distances are measurements, not arbitrary acceptance thresholds.'};(O/'rpm-return-restoration.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
