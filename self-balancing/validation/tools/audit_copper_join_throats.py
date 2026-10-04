#!/usr/bin/python3
"""Native-copper local join-width screening for every net/layer.

Every same-net contacting pair whose straight centerlines do not meet is
considered. An exact circle-lens lower bound proves many joins wide enough.
Remaining contacts are tested on the actual local native copper union including
all same-net tracks and pad/via lands. Erosion asks whether track-center anchors
remain connected through that local copper at the required width. Pad/via lands
are intentionally treated as terminal copper; via annulus attachment is audited
separately. This does not infer adequate neck width from nominal segment widths.
"""
import argparse,collections,hashlib,json,math,os,time
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
RAILS={'GND','3V3_CORE','VLOGIC_IN','+5V_STACK','VDDA','IMU_3V3','USB_VBUS','/power/USB_VBUS_SLEW','/power/BUCK_SW','/power/BUCK_VIN','/power/BUCK_OUT'}
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();uid=lambda t:t.m_Uuid.AsString();pt=lambda q:(q.x,q.y);mm=lambda q:[round(v/1e6,6) for v in q]
def project(q,a,b):
 d=(b[0]-a[0],b[1]-a[1]);den=d[0]**2+d[1]**2;t=max(0,min(1,((q[0]-a[0])*d[0]+(q[1]-a[1])*d[1])/den)) if den else 0
 return (a[0]+t*d[0],a[1]+t*d[1]),t
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def closest(a,b,c,d):
 u=(b[0]-a[0],b[1]-a[1]);v=(d[0]-c[0],d[1]-c[1]);w=(c[0]-a[0],c[1]-a[1]);den=cross(u,v)
 if den:
  t=cross(w,v)/den;s=cross(w,u)/den
  if 0<=t<=1 and 0<=s<=1:
   x=(a[0]+t*u[0],a[1]+t*u[1]);return 0.,x,x,t,s
 rows=[]
 for q,t in [(a,0.),(b,1.)]:
  r,s=project(q,c,d);rows.append((math.dist(q,r),q,r,t,s))
 for q,s in [(c,0.),(d,1.)]:
  r,t=project(q,a,b);rows.append((math.dist(q,r),r,q,t,s))
 return min(rows,key=lambda q:q[0])
def rectnear(bb,cx,cy,r):return bb.GetLeft()<=cx+r and bb.GetRight()>=cx-r and bb.GetTop()<=cy+r and bb.GetBottom()>=cy-r
def native_poly(obj,l,error=50):
 q=p.SHAPE_POLY_SET();obj.TransformShapeToPolygon(q,l,0,error,p.ERROR_OUTSIDE);return q
def lens_width(distance,r1,r2):
 if distance<=abs(r1-r2):return 2*min(r1,r2)
 along=(distance*distance+r1*r1-r2*r2)/(2*distance)
 return 2*math.sqrt(max(0,r1*r1-along*along))

def centerline_land_intersects(t,land,l):
 # One-nanometre centerline tube; exported results retain this explicit
 # numerical tolerance alongside the native polygon construction tolerance.
 q=p.PCB_TRACK(t.GetBoard());q.SetLayer(l);q.SetStart(t.GetStart());q.SetEnd(t.GetEnd());q.SetWidth(1)
 return q.GetEffectiveShape(l).GetClearance(land)<=0

def constructive_bridge(near,zones,l,target,first,last,poly):
 tracks=[q for q in near if isinstance(q,p.PCB_TRACK) and not isinstance(q,p.PCB_VIA) and q.GetWidth()>=target]
 adj={uid(q):set() for q in tracks}
 for i,t in enumerate(tracks):
  for u in tracks[:i]:
   distance,*rest=closest(pt(t.GetStart()),pt(t.GetEnd()),pt(u.GetStart()),pt(u.GetEnd()))
   if distance>t.GetWidth()/2+u.GetWidth()/2:continue
   if distance<.01 or lens_width(distance,t.GetWidth()/2,u.GetWidth()/2)>=target-1:
    adj[uid(t)].add(uid(u));adj[uid(u)].add(uid(t))
 lands=[]
 for q in near:
  if isinstance(q,(p.PAD,p.PCB_VIA)):lands.append((uid(q),p.SHAPE_POLY_SET(poly(q,l))))
 for i,q in enumerate(zones):lands.append(('zone:'+str(i),p.SHAPE_POLY_SET(q)))
 for name,land in lands:
  land.Inflate(-round(target/2+100),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,50)
  for oi in range(land.OutlineCount()):
   component=p.SHAPE_POLY_SET(land.COutline(oi))
   for hi in range(land.HoleCount(oi)):component.AddHole(land.CHole(oi,hi),0)
   key=name+':'+str(oi);links=[uid(t) for t in tracks if centerline_land_intersects(t,component,l)]
   if len(links)>1:
    adj[key]=set(links)
    for u in links:adj[u].add(key)
 seen={first};todo=[first]
 while todo:
  u=todo.pop()
  for v in adj.get(u,[]):
   if v not in seen:seen.add(v);todo.append(v)
 return last in seen
def contained_virtual_stroke(start,end,target,local,board,l):
 a=tuple(round(v) for v in start);z=tuple(round(v) for v in end);dx=z[0]-a[0];dy=z[1]-a[1];step=min(abs(dx),abs(dy));sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1
 paths=[[a,z],[a,(a[0],z[1]),z],[a,(z[0],a[1]),z],[a,(a[0]+sx*step,a[1]+sy*step),z],[a,(z[0]-sx*step,z[1]-sy*step),z]]
 for path in paths:
  poly=p.SHAPE_POLY_SET();keep=[]
  for x,y in zip(path,path[1:]):
   if x==y:continue
   t=p.PCB_TRACK(board);t.SetLayer(l);t.SetWidth(target);t.SetStart(p.VECTOR2I(*x));t.SetEnd(p.VECTOR2I(*y));keep.append(t);q=p.SHAPE_POLY_SET();t.TransformShapeToPolygon(q,l,0,50,p.ERROR_OUTSIDE);poly.BooleanAdd(q)
  if not poly.OutlineCount():continue
  outside=p.SHAPE_POLY_SET(poly);outside.BooleanSubtract(local)
  if outside.Area()==0:return {'path_mm':[mm(q) for q in path],'width_mm':target/1e6,'copper_outside_actual_native_union_mm2':0.0}
 return None

def precision_native_bridge(near,zones,l,target,anchors,center,radius):
 local=p.SHAPE_POLY_SET()
 for q in near:local.BooleanAdd(native_poly(q,l,1))
 for q in zones:local.BooleanAdd(q)
 region=p.SHAPE_POLY_SET();p.SHAPE_CIRCLE(p.VECTOR2I(round(center[0]),round(center[1])),radius).TransformToPolygon(region,100,p.ERROR_INSIDE);local.BooleanIntersection(region)
 local.Inflate(-round(target/2-2),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
 for oi in range(local.OutlineCount()):
  component=p.SHAPE_POLY_SET(local.COutline(oi))
  for hi in range(local.HoleCount(oi)):component.AddHole(local.CHole(oi,hi),0)
  if all(component.Contains(p.VECTOR2I(round(q[0]),round(q[1]))) for q in anchors):return True
 return False

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--baseline-report',type=Path);a=ap.parse_args();assert sha(a.candidate)==a.sha256;tool_hash=sha(Path(__file__));b=p.LoadBoard(str(a.candidate));start=time.time();groups=collections.defaultdict(list);objects=collections.defaultdict(list);alltracks=[]
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):continue
  assert not isinstance(t,p.PCB_ARC),'Arc copper requires separate exact handling'
  groups[(t.GetNetname(),t.GetLayer())].append(t);alltracks.append(t)
 for t in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]:
  for l in b.GetEnabledLayers().CuStack():
   if t.IsOnLayer(l):objects[(t.GetNetname(),l)].append((t,t.GetEffectiveShape(l).BBox()))
 zone_by=collections.defaultdict(list)
 for z in b.Zones():
  if z.GetIsRuleArea():continue
  for l in b.GetEnabledLayers().CuStack():
   if z.IsOnLayer(l) and z.HasFilledPolysForLayer(l):zone_by[(z.GetNetname(),l)].append(z.GetFilledPolysList(l))
 candidates=[];failures=[];counts=collections.Counter();pernet={};cache={}
 def poly(t,l):
  key=(uid(t),l)
  if key not in cache:cache[key]=native_poly(t,l)
  return cache[key]
 for (net,l),ts in sorted(groups.items()):
  local_counts=collections.Counter();ts.sort(key=lambda t:t.GetEffectiveShape(l).BBox().GetLeft());lbs=[t.GetEffectiveShape(l).BBox() for t in ts]
  for i,t in enumerate(ts):
   tb=lbs[i]
   for j in range(i+1,len(ts)):
    u=ts[j];ub=lbs[j]
    if ub.GetLeft()>tb.GetRight():break
    if ub.GetTop()>tb.GetBottom() or ub.GetBottom()<tb.GetTop():continue
    if t.GetEffectiveShape(l).GetClearance(u.GetEffectiveShape(l))>0:continue
    local_counts['actual_track_contacts']+=1
    dist,c1,c2,s1,s2=closest(pt(t.GetStart()),pt(t.GetEnd()),pt(u.GetStart()),pt(u.GetEnd()))
    if dist<.01:local_counts['centerlines_meet']+=1;continue
    local_counts['noncoincident_centerline_contacts']+=1;r1=t.GetWidth()/2;r2=u.GetWidth()/2;target=min(t.GetWidth(),u.GetWidth()) if net in RAILS else 130000
    if dist<=abs(r1-r2):neck=2*min(r1,r2)
    else:
     along=(dist*dist+r1*r1-r2*r2)/(2*dist);neck=2*math.sqrt(max(0,r1*r1-along*along))
    if neck>=target-1:local_counts['circle_lens_proves_width']+=1;continue
    center=((c1[0]+c2[0])/2,(c1[1]+c2[1])/2);radius=max(1000000,target*4);near=[q for q,bb in objects[(net,l)] if rectnear(bb,*center,radius)];local=p.SHAPE_POLY_SET()
    for q in near:local.BooleanAdd(poly(q,l))
    for zpoly in zone_by[(net,l)]:local.BooleanAdd(zpoly)
    region=p.SHAPE_POLY_SET();p.SHAPE_CIRCLE(p.VECTOR2I(round(center[0]),round(center[1])),radius).TransformToPolygon(region,100,p.ERROR_INSIDE);local.BooleanIntersection(region)
    def anchor(q,fraction,point):
     x,z=pt(q.GetStart()),pt(q.GetEnd());length=math.dist(x,z)
     if not length:return point
     # At endpoints step into the owning track, clear of the fragile end cap.
     if fraction<=1e-8:step=min(.4*length,200000);return (x[0]+(z[0]-x[0])*step/length,x[1]+(z[1]-x[1])*step/length)
     if fraction>=1-1e-8:step=min(.4*length,200000);return (z[0]+(x[0]-z[0])*step/length,z[1]+(x[1]-z[1])*step/length)
     return point
    anchors=[anchor(t,s1,c1),anchor(u,s2,c2)];erosion=target/2-100;eroded=p.SHAPE_POLY_SET(local);eroded.Inflate(-round(erosion),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,50)
    def components_at(point):
     matches=[]
     for oi in range(eroded.OutlineCount()):
      region=p.SHAPE_POLY_SET(eroded.COutline(oi))
      for hi in range(eroded.HoleCount(oi)):region.AddHole(eroded.CHole(oi,hi),0)
      if region.Contains(p.VECTOR2I(round(point[0]),round(point[1]))):matches.append(oi)
     return matches
    components=[components_at(q) for q in anchors];connected=bool(set(components[0])&set(components[1]));strict_connected=False;constructive=False;virtual_stroke=None;precision_pass=False
    if connected:
     strict=p.SHAPE_POLY_SET(local);strict.Inflate(-round(target/2+100),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,50)
     for oi in range(strict.OutlineCount()):
      region=p.SHAPE_POLY_SET(strict.COutline(oi))
      for hi in range(strict.HoleCount(oi)):region.AddHole(strict.CHole(oi,hi),0)
      if all(region.Contains(p.VECTOR2I(round(q[0]),round(q[1]))) for q in anchors):strict_connected=True;break
     if not strict_connected:
      virtual_stroke=contained_virtual_stroke(c1,c2,target,local,b,l)
      if not virtual_stroke:constructive=constructive_bridge(near,zone_by[(net,l)],l,target,uid(t),uid(u),poly)
    if connected and not (strict_connected or constructive or virtual_stroke):precision_pass=precision_native_bridge(near,zone_by[(net,l)],l,target,anchors,center,radius)
    proven=connected and (strict_connected or constructive or bool(virtual_stroke) or precision_pass);landcover=[]
    for q in near:
     if not isinstance(q,(p.PAD,p.PCB_VIA)):continue
     if q.GetEffectiveShape(l).Collide(p.VECTOR2I(round(center[0]),round(center[1])),0):landcover.append({'uuid':uid(q),'kind':q.GetClass(),'reference':q.GetParentFootprint().GetReference()+'.'+q.GetNumber() if isinstance(q,p.PAD) else None})
    def rec(q):return {'uuid':uid(q),'start_mm':mm(pt(q.GetStart())),'end_mm':mm(pt(q.GetEnd())),'width_mm':q.GetWidth()/1e6}
    row={'net':net,'layer':b.GetLayerName(l),'tracks':[rec(t),rec(u)],'closest_centerline_points_mm':[mm(c1),mm(c2)],'contact_center_mm':mm(center),'closest_centerline_gap_mm':dist/1e6,'pair_circle_lens_neck_mm':neck/1e6,'required_join_width_mm':target/1e6,'erosion_test_width_mm':2*erosion/1e6,'local_radius_mm':radius/1e6,'native_union_eroded_anchor_connected':connected,'strict_erosion_width_mm':(target+200)/1e6,'strict_erosion_connected':strict_connected,'constructive_full_width_path_connected':constructive,'actual_width_proven':proven,'one_nm_polygon_near_exact_nominal_width_connected':precision_pass,'near_exact_nominal_width_error_bound_nm':6 if precision_pass else None,'contained_target_width_virtual_stroke':virtual_stroke,'eroded_anchor_component_ids':components,'anchor_points_mm':[mm(q) for q in anchors],'terminal_lands_at_contact':landcover,'local_same_net_objects':len(near),'classification':'LOCAL NATIVE COPPER BRIDGES PAIR NECK' if proven else 'NARROW LOCAL COPPER JOIN; REPAIR OR EXPLICIT TERMINAL DISPOSITION REQUIRED'};candidates.append(row)
    if not proven:failures.append(row);local_counts['narrow_local_join_flags']+=1
    else:local_counts['native_union_proves_local_bridge']+=1
  pernet.setdefault(net,{})[b.GetLayerName(l)]=dict(local_counts);counts.update(local_counts)
  print(json.dumps({'net':net,'layer':b.GetLayerName(l),'counts':dict(local_counts),'elapsed_s':round(time.time()-start,1)}),flush=True)
 if a.baseline_report:
  prior=json.loads(a.baseline_report.read_text());prior_pairs={tuple(sorted(t['uuid'] for t in q['tracks'])) for q in prior['narrow_local_join_flags']}
  for q in failures:q['pair_flag_in_baseline']=tuple(sorted(t['uuid'] for t in q['tracks'])) in prior_pairs
 report={'status':'JOIN QUALITY REVIEW REQUIRED' if failures else 'NO NARROW LOCAL TRACK JOINS FOUND','source':str(a.candidate),'candidate_sha256':a.sha256,'audit_script_sha256':tool_hash,'summary':{'routed_nets':len(pernet),'track_count':len(alltracks),**counts,'flagged_nets':len({q['net'] for q in failures})},'per_net_layer':pernet,'narrow_local_join_flags':failures,'all_screened_low_lens_width_contacts':candidates,'method':__doc__,'tolerances':{'erosion_radius_screen_margin_nm':100,'strict_erosion_radius_extra_nm':100,'constructive_centerline_tube_nm':1,'native_polygon_error_nm':50,'fallback_native_polygon_error_nm':1,'fallback_maximum_width_uncertainty_nm':6,'nominal_signal_join_width_mm':.130,'rail_join_requirement':'Minimum of the two incident rail widths; separate branch/path-width preservation still required'},'limits':'Loose erosion screens at target minus200nm; acceptance requires target plus200nm erosion or a constructive target-width path, or a separate1nm-native-polygon check whose worst-case width uncertainty is6nm. Nominal-width trace arms cannot survive positive-margin erosion; the near-exact fallback distinguishes that numerical degeneracy from a real contact bottleneck. Land copper is included so legal pad/via-contained overlaps are not automatically failures. Via annulus penetration and trace-to-pad attachment depth require their separate audits. Non-local alternative paths do not waive a narrow local join.'}
 assert sha(a.candidate)==a.sha256 and sha(Path(__file__))==tool_hash;a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))
if __name__=='__main__':main()
