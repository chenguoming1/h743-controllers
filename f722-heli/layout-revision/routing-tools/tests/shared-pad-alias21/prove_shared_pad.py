#!/usr/bin/env python3
"""Read-only analytic bounds proof; no solver, JVM, sampling grid, or board edits."""
from pathlib import Path
from decimal import Decimal
import hashlib, json, math
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FROZEN = '868b957a5dad28110216e6a59b05497150c2bf0d3b2ae02db6a38cede79e8181'
paths = {'native':ROOT/'candidate21/f722-heli.native.json', 'capture':ROOT/'tests/local-closures20/port-b-located-path.json', 'model':ROOT/'model-candidate21-ready/model.json'}
raw = {k:p.read_bytes() for k,p in paths.items()}
d = {k:json.loads(v) for k,v in raw.items()}
assert all(d[k]['board_sha256'] == FROZEN for k in d)
pad = next(o for o in d['native']['objects'] if o.get('key') == 'U14.7')
trace = next(o for o in d['native']['objects'] if o['uuid'] == '80e6c8c0-48bb-46c8-8199-32bcc81b5699')
located, failed = d['capture']['records']
assert failed['failing_obstacle']['class'] == 'app.freerouting.board.PolylineTrace'
assert failed['failing_obstacle']['fixed'] == 'USER_FIXED'
assert trace['start'] == [24.0,7.4825] and trace['end'] == [24.0,8.3175]
assert d['model']['source_logical_nets'][trace['uuid']] == 'PORT_B_RX_EXT::P1'
contacts = [c for c in d['model']['contacts'] if c.get('key') == 'U14.7']
assert {c['net'] for c in contacts} == {'PORT_B_RX_EXT::P0','PORT_B_RX_EXT::P1'}
assert all(set(c['owners']) == {'PORT_B_RX_EXT::P0','PORT_B_RX_EXT::P1'} for c in contacts)
S = 1000000 # integer millionths of a millimeter, exact for native JSON coordinates
U = lambda x: int(Decimal(str(x))*S)
P = lambda p: tuple(map(U,p))
poly = list(map(P,pad['inside']['F.Cu'][0]['outer']))
assert not pad['inside']['F.Cu'][0]['holes']
def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
turns=[cross(poly[i],poly[(i+1)%len(poly)],poly[(i+2)%len(poly)]) for i in range(len(poly))]
assert all(t>=0 for t in turns) or all(t<=0 for t in turns), 'Native inside outline must be convex'
sign=1 if any(t>0 for t in turns) else -1
def contained_box(box):
 x0,y0,x1,y1=box
 return all(sign*cross(poly[i],poly[(i+1)%len(poly)],v)>=0 for i in range(len(poly)) for v in [(x0,y0),(x0,y1),(x1,y0),(x1,y1)])
def bounds(pts): return (min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts))
def mm(box): return [v/S for v in box]
a0,a1=map(P,failed['requested_corners_mm']); b0,b1=P(trace['start']),P(trace['end'])
r=U(located['half_width_mm']); c=U(d['model']['rules']['clearance']); e=U(d['native']['maximum_polygon_error_mm'])
assert r==63500 and c==127000 and e==10 and a0[0]==a1[0] and b0[0]==b1[0]
bb=bounds([P(q) for p in trace['copper']['F.Cu'] for q in p['outer']])
# A is exact candidate capsule enlarged conservatively by the native polygon error.
# B is the actual native ERROR_OUTSIDE polygon. If dist(a,b)<c then each point
# must lie within c of the other set's coordinate bounds. These are outer bounds
# on ALL participating copper points, not samples or a nearest-pair-only check.
ar=r+e
abox=(a1[0]-ar,bb[1]-c,a1[0]+ar,a1[1]+ar)
bbox=(bb[0],bb[1],bb[2],a1[1]+ar+c)
assert contained_box(abox) and contained_box(bbox)
central=tuple(map(U,[23.9,7.25,24.1,7.715])); assert contained_box(central)
# Every earlier located segment is excluded using a lower bound on centerline
# distance: the distance between its AABB and the fixed vertical centerline AABB.
prefix_bounds=[]
for s,t in zip(located['requested_corners_mm'][:-2],located['requested_corners_mm'][1:-1]):
 sb=bounds([P(s),P(t)]); tb=bounds([b0,b1])
 dx=max(sb[0]-tb[2],tb[0]-sb[2],0); dy=max(sb[1]-tb[3],tb[1]-sb[3],0)
 dist=math.hypot(dx,dy)/S
 assert dx*dx+dy*dy > (2*r+c+2*e)**2
 prefix_bounds.append(dist)
# A bounded representation control, ONLY for the captured endpoint.
seam=U(7.65)
removed_box=(b0[0]-r,b0[1]-r,b0[0]+r,seam+r)
assert contained_box(removed_box)
trimmed_gap=math.hypot(a1[0]-b0[0],a1[1]-seam)/S-2*r/S
assert trimmed_gap > c/S+2*e/S
# Optional monotone completion to the pad center remains physically localized;
# it DOES NOT pass the preceding simple-trim insertion control.
ext_a_box=(min(a1[0],b0[0])-ar,bb[1]-c,max(a1[0],b0[0])+ar,b0[1]+ar)
ext_b_box=(bb[0],bb[1],bb[2],b0[1]+ar+c)
assert contained_box(ext_a_box) and contained_box(ext_b_box)
distance=math.dist(a1,b0)/S
result={
 'passed':True, 'method':'Exact integer convex-polygon containment plus analytic capsule and coordinate-distance bounds; no sampled grid, JVM, or route solver.',
 'scope':'Captured F.Cu P0 path versus identified P1 fixed trace only. Not a board-wide DRC or insertion-success claim.',
 'board_sha256':FROZEN,
 'input_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in raw.items()},
 'pad':{k:pad[k] for k in ['uuid','key','net','xy','angle','size']},
 'pad_certified_inside_rectangle_mm':mm(central),
 'fixed_trace_uuid':trace['uuid'], 'fixed_engine_id':failed['failing_obstacle']['engine_id'],
 'native_fixed_copper_outer_bounds_mm':mm(bb),
 'candidate_polygon_error_allowance_mm':e/S,
 'nearest_centerline_distance_mm':distance,'exact_nominal_copper_gap_mm':distance-2*r/S,
 'required_outside_pad_clearance_mm':c/S,'nominal_clearance_deficit_mm':(2*r+c)/S-distance,
 'all_candidate_copper_participating_in_clearance_conflict_contained_in_mm':mm(abox),
 'all_existing_copper_participating_in_clearance_conflict_contained_in_mm':mm(bbox),
 'both_conflict_bounds_inside_native_inside_pad':True,
 'earlier_segment_count':len(prefix_bounds),'earlier_centerline_aabb_distance_lower_bound_mm':min(prefix_bounds),
 'captured_path_outside_pad_crossing_with_this_trace':False,
 'planning_only_trim_control':{'start_mm':[24,7.65], 'omitted_prefix_capsule_bounds_mm':mm(removed_box),'omitted_prefix_fully_inside_native_pad':True,'retained_stub_nominal_gap_to_captured_path_mm':trimmed_gap,'native_source_must_remain_unchanged':True,'valid_for_deeper_endpoint_without_reproof':False},
 'monotone_completion_to_pad_center':{'candidate_x_range_mm':[24,24.03646],'candidate_y_range_mm':[7.26354,7.4825],'conflict_still_pad_local':True,'candidate_conflict_bound_mm':mm(ext_a_box),'existing_conflict_bound_mm':mm(ext_b_box),'simple_trim_control_still_sufficient':False}
}
(OUT/'proof.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['passed','exact_nominal_copper_gap_mm','both_conflict_bounds_inside_native_inside_pad','earlier_centerline_aabb_distance_lower_bound_mm']}))
