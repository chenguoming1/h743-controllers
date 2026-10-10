"""Preserve refill differences; verify they are confined to pre-existing own-via windows."""
from pathlib import Path
import json,hashlib,sys,argparse
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
p=argparse.ArgumentParser(description=__doc__)
for name in ['before-snapshot','after-snapshot','before-board','after-board','comparison','out']:p.add_argument('--'+name,type=Path,required=True)
p.add_argument('--tools',type=Path,default=Path(__file__).resolve().parent);args=p.parse_args();sys.path.insert(0,str(args.tools))
if sys.flags.optimize:raise RuntimeError('Assertions must be enabled')
from compare_reference_geometry import load,compare
from check_signal_geometry import copper_entries
from check_critical_reference import ground_geometry,local_masks,REFERENCE
old=args.before_board;new=args.after_board;B=load(args.before_snapshot,old);A=load(args.after_snapshot,new);c=compare(B,A);assert c['critical_object_geometry_identical'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
provided=json.loads(args.comparison.read_text());assert provided['before_board_sha256']==sha(old) and provided['after_board_sha256']==sha(new) and provided['critical_object_geometry_identical']
bg,bm,br=B;ag,am,ar=A
_,bz,bground,_=ground_geometry(bg,copper_entries(bg));_,az,aground,_=ground_geometry(ag,copper_entries(ag));bmask,bfacts,_=local_masks(bg,bm,bz);amask,afacts,_=local_masks(ag,am,az)
assert set(bmask)==set(amask)
# Same signal-via source objects were already established by exact critical object comparison.
for k in bfacts:
 for f in ['via_uuid','via_xy_mm','local_window_radius_mm','nominal_land_radius_mm','via_own_clearance_mm','maximum_ground_zone_clearance_mm','classification_allowance_mm']:
  assert bfacts[k][f]==afacts[k][f],(k,f)
by_old={x['track_uuid']:x for x in br['tracks']};by_new={x['track_uuid']:x for x in ar['tracks']};assert set(by_old)==set(by_new);rows=[]
for uid,b in by_old.items():
 a=by_new[uid]
 for field in ['net','signal_layer','reference_layer','start_mm','end_mm','width_mm']:assert a[field]==b[field]
 def geom(x,field,classes):
  return unary_union([Polygon(r['outer_mm'],r.get('holes_mm',[])) if field.startswith('trace_width') else LineString(r['coordinates_mm']) for cls in classes for r in x[field][cls]])
 classes=['local_own_via_window_in_saved_hole','drill_void_outside_own_window','saved_void_or_edge_outside_own_window'];outside=classes[1:]
 assert geom(a,'trace_width_missing_by_class',outside).equals(geom(b,'trace_width_missing_by_class',outside)),uid
 assert geom(a,'centerline_missing_by_class',classes).equals(geom(b,'centerline_missing_by_class',classes)),uid
 delta=geom(a,'trace_width_missing_by_class',classes).symmetric_difference(geom(b,'trace_width_missing_by_class',classes))
 if not delta.is_empty:
  # Use unchanged local windows with actual saved holes in either state. Do not enlarge a window or exempt merged holes wholesale.
  keys=[k for k,f in bfacts.items() if f['via_uuid'] in {v['via_uuid'] for v in b['local_own_windows_intersecting_missing']} and k[1]==b['reference_layer']]
  original_windows=unary_union([m[k] for k in keys for m in [bmask,amask]]);left=delta.difference(original_windows);assert left.is_empty,(uid,left.area)
  rows.append({'track_uuid':uid,'net':a['net'],'reference_layer':a['reference_layer'],'changed_width_region_mm2':delta.area,'bounds_mm':list(delta.bounds),'entirely_inside_unchanged_own_via_windows_and_before_or_after_actual_holes':True,'original_window_via_uuids':[bfacts[k]['via_uuid'] for k in keys]})
r={'schema':'f722-owner-existing-via-window-refill-review/v1','before_board_sha256':sha(old),'board_sha256':sha(new),'comparison_sha256':sha(args.comparison),'passed':True,'critical_copper_identical':True,'all_missing_centerline_geometries_equal':True,'all_missing_width_geometry_outside_existing_own_via_windows_equal':True,'changed_regions':rows,'numeric_differences_retained':c['net_numeric_deltas_after_minus_before'],'method':'Exact source-bound saved geometry, no snapping, epsilon, contour repair or value zeroing. Entire changed trace-width regions are confined to unchanged local same-net via windows intersected with actual saved holes from the before/after states.','limits':'Scoped reference classification only. Real fill changes remain and require new source-bound power/VCAP validation; no impedance, fabrication, timing or flight qualification.','script_sha256':sha(Path(__file__))};args.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
