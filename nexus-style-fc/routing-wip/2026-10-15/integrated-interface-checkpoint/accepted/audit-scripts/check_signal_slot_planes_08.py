from pathlib import Path
import pcbnew as k,json,hashlib,sys,collections,math
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();uid=lambda o:o.m_Uuid.AsString();area=lambda p:abs(p.Area())/1e12;xy=lambda p:[p.x/1e6,p.y/1e6]
def poly(o,l,c=0):
 p=k.SHAPE_POLY_SET();o.TransformShapeToPolygon(p,l,round(c*1e6),1,k.ERROR_INSIDE);return p
def sub(a,b):p=k.SHAPE_POLY_SET(a);p.BooleanSubtract(b);return p
def inter(a,b):p=k.SHAPE_POLY_SET(a);p.BooleanIntersection(b);return p
boards={};fills={};tracks={};sets={}
for label,D in [('source',S),('candidate',O)]:
 b=k.LoadBoard(str(D/'hardware/nexus-style-fc.kicad_pcb'));boards[label]=b;tracks[label]={uid(t):t for t in b.GetTracks()};gs={}
 for l in b.GetEnabledLayers().CuStack():
  p=k.SHAPE_POLY_SET()
  for z in b.Zones():
   if z.GetNetname()=='GND' and z.IsOnLayer(l) and not z.GetIsRuleArea():p.BooleanAdd(z.GetFilledPolysList(l))
  gs[b.GetLayerName(l)]=p
 fills[label]=gs
losses={};gains={};changes=[]
for l in fills['source']:
 a,b=fills['source'][l],fills['candidate'][l];lost,gained=sub(a,b),sub(b,a);losses[l]=lost;gains[l]=gained
 changes.append({'layer':l,'source_components':a.OutlineCount(),'candidate_components':b.OutlineCount(),'source_largest_component_area_mm2':max([area(a.UnitSet(i)) for i in range(a.OutlineCount())] or [0]),'candidate_largest_component_area_mm2':max([area(b.UnitSet(i)) for i in range(b.OutlineCount())] or [0]),'ground_removed_mm2':area(lost),'ground_added_mm2':area(gained)})
# Quantify exactly which retained conductors lose projection over the changed main planes.
changes_to_retained=[];common=set(tracks['source'])&set(tracks['candidate'])-set(r['uuid'] for r in tr['moved_vias']);b=boards['candidate']
for layer,ref in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu'),('In2.Cu','In1.Cu')]:
 l=b.GetLayerID(layer);groups=collections.defaultdict(list)
 for u in common:
  t=tracks['candidate'][u]
  if not isinstance(t,k.PCB_VIA) and t.GetLayer()==l and t.GetNetname()!='GND':groups[t.GetNetname()].append(t)
 for net,items in groups.items():
  p=k.SHAPE_POLY_SET()
  for t in items:p.BooleanAdd(poly(t,l))
  lost=area(inter(p,losses[ref]));gained=area(inter(p,gains[ref]));
  if lost>1e-9 or gained>1e-9:changes_to_retained.append({'net':net,'routing_layer':layer,'reference_layer':ref,'lost_projected_ground_mm2':lost,'gained_projected_ground_mm2':gained,'source_full_width_projected_ground_mm2':area(inter(p,fills['source'][ref])),'candidate_full_width_projected_ground_mm2':area(inter(p,fills['candidate'][ref])),'affected_track_uuids':[uid(t) for t in items if area(inter(poly(t,l),losses[ref]))>1e-9]})
# All complete donor paths: measure their actual nearest physical references and lengths.
projections=[]
for route in tr['routes']:
 for label,ids in [('source',route['removed_uuids']),('candidate',route['new_uuids'])]:
  b=boards[label];bylayer=collections.defaultdict(list)
  for u in ids:bylayer[b.GetLayerName(tracks[label][u].GetLayer())].append(tracks[label][u])
  for layer,items in bylayer.items():
   p=k.SHAPE_POLY_SET();length=0;l=b.GetLayerID(layer)
   for t in items:
    assert t.GetWidth()==127000;p.BooleanAdd(poly(t,l));length+=t.GetLength()/1e6
   refs={'In2.Cu':['In1.Cu','In3.Cu'],'In4.Cu':['In3.Cu','B.Cu']}[layer]
   for ref in refs:projections.append({'route':route['name'],'state':label,'routing_layer':layer,'reference_layer':ref,'length_mm':length,'copper_union_area_mm2':area(p),'ground_overlap_mm2':area(inter(p,fills[label][ref])),'uncovered_area_mm2':area(sub(p,fills[label][ref]))})
# Full source/accepted critical-return proofs run separately; this records all actual plane losses/gains.
out={'status':'MEASURED integrated slot/refill and restored In2 signal tradeoff','source_sha256':sha(S/'hardware/nexus-style-fc.kicad_pcb'),'candidate_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'plane_changes':changes,'complete_donor_adjacent_reference_projection':projections,'changed_retained_conductor_projection':sorted(changes_to_retained,key=lambda q:q['lost_projected_ground_mm2'],reverse=True),'qualification':'Actual polygon measurements do not establish impedance or physical strength. Finite main-plane/ground-pad connections, cap-star/U5/U10/USB/shield continuity are independently required. No percentage threshold is used.'};(O/'signal-slot-plane-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
