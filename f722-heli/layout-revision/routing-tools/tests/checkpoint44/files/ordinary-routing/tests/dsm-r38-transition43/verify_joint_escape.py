#!/usr/bin/env python3
"""Read-only source43 DSM escape and exact two-track BEC reconstruction witness."""
import sys,pathlib,json,hashlib,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'dsm-mcu-candidate43'))
import native43_geometry as G
from shapely.geometry import Point,LineString
HERE=pathlib.Path(__file__).resolve().parent
REMOVED={'38e0887e-ae81-480f-82c7-f32e7ea12c27','cad1419a-e60e-4274-b9ad-78e419772ee4'}
VIA=(18.45,24.095)
STUB=[(18.11,23.46),(18.45,23.8),VIA]
BEC=[(15.021874,20.464544),(17.7,23.7),(17.7,24.8),(24.147805,24.648486)]
bec_line=LineString(BEC);stub_line=LineString(STUB)
T,V,skipped=G.obstacles('DSM_RX_MCU','B.Cu')
old=G.check(Point(VIA),V,True)
V=[o for o in V if o['object'] not in REMOVED]
V.append(dict(object='replacement-BEC-In3-centerline',uuid=None,net='+5V_BEC',kind='track',category='foreign_copper',layers=['In3.Cu'],required_physical_gap_mm=.127,moving_radius_mm=.225,required_center_distance_mm=.652,geometry=bec_line,obstacle_radius_mm=.3,geometry_basis='capsule centerline; exact radius included in required center distance'))
P,_,_=G.obstacles('+5V_BEC','In3.Cu')
for o in P:
 o['required_center_distance_mm']+=.3-G.HALF;o['moving_radius_mm']=.3
P.append(dict(object='new-DSM-via-center',uuid=None,net='DSM_RX_MCU',kind='via',category='foreign_copper',layers=['In3.Cu'],required_physical_gap_mm=.127,moving_radius_mm=.3,required_center_distance_mm=.652,geometry=Point(VIA),obstacle_radius_mm=.225,geometry_basis='circle center; exact radius included in required center distance'))
def check(g,obstacles):
 rows=G.check(g,obstacles,True)
 for r in rows:
  if 'obstacle_radius_mm' in r:
   r['physical_gap_mm']-=r['obstacle_radius_mm']
 return dict(constraints_evaluated=len(rows),pass_with_polygon_error=all(r['pass_with_polygon_error'] for r in rows),minimum_excess_mm=rows[0]['extra_clearance_mm'],failures=[r for r in rows if not r['pass_with_polygon_error']],nearest_witnesses=rows[:20])
r=dict(schema='f722-read-only-R38-DSM-via-with-BEC-two-track-reconstruction/v1',board_sha256=G.EXPECTED,native_sha256=hashlib.sha256(G.SOURCE.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),geometry_helper_sha256=hashlib.sha256(pathlib.Path(G.__file__).read_bytes()).hexdigest(),maximum_polygon_error_mm=G.ERROR,removed_track_uuids=sorted(REMOVED),preserved='All source pads, footprints, drills, other tracks, and zones retained. D7 DSM_RX_EXT protected cut unchanged. In1/In4 ground zones remain GND-only.',scope='Complete local pad-to-through-via transition and full width reconstruction of both displaced BEC segments. No inner DSM trunk, native board adoption, DRC, power/FEM, or global feasibility claim.',proposal=dict(dsm_stub=dict(net='DSM_RX_MCU',layer='B.Cu',width_mm=.127,points=STUB),dsm_via=dict(net='DSM_RX_MCU',center_mm=VIA,diameter_mm=.45,drill_mm=.20,tented_front=True,tented_back=True,through_layers=G.N['copper_layers']),bec_reconstruction=dict(net='+5V_BEC',layer='In3.Cu',width_mm=.6,points=BEC)),source_via_conflicts=[x for x in old if not x['pass_with_polygon_error']],stub_check=check(stub_line,T),via_check=check(Point(VIA),V),bec_check=check(bec_line,P))
r['reconstruction_endpoint_checks']=[dict(endpoint=pt,retained_connected_objects=[o.get('key',o['uuid']) for o,c,m,d in G.OBJECTS if o['net']=='+5V_BEC' and o['uuid'] not in REMOVED and 'In3.Cu' in c and Point(pt).distance(c['In3.Cu'])<1e-9]) for pt in [BEC[0],BEC[-1]]]
old_objects=[o for o,c,m,d in G.OBJECTS if o['uuid'] in REMOVED]
old_length=sum(math.dist(o['start'],o['end']) for o in old_objects)
r['bec_length_comparison_mm']=dict(before=old_length,after=bec_line.length,delta=bec_line.length-old_length)
r['power_status']='Fresh native power solve required on adopted joint candidate. This geometry-only read-only lane ran no JVM/FEM and does not claim electrical equivalence from equal width.'
r['new_copper_inside_source_outline']=dict(dsm_stub=G.OUTLINE.covers(stub_line.buffer(.0635,quad_segs=256)),dsm_via=G.OUTLINE.covers(Point(VIA).buffer(.225,quad_segs=256)),bec=G.OUTLINE.covers(bec_line.buffer(.3,quad_segs=256)))
r['full_width_endpoint_joins']=[]
for endpoint in [BEC[0],BEC[-1]]:
 for o,c,m,d in G.OBJECTS:
  if o['net']=='+5V_BEC' and o['uuid'] not in REMOVED and 'In3.Cu' in c and Point(endpoint).distance(c['In3.Cu'])<1e-9:
   r['full_width_endpoint_joins'].append(dict(endpoint_mm=endpoint,retained_track_uuid=o['uuid'],retained_track_width_mm=o['width'],replacement_width_mm=.6,center_matches_retained_native_endpoint=tuple(endpoint) in [tuple(o['start']),tuple(o['end'])],overlap_area_mm2=bec_line.buffer(.3,quad_segs=256).intersection(c['In3.Cu']).area))
r['all_geometry_checks_pass']=all(r[k]['pass_with_polygon_error'] for k in ['stub_check','via_check','bec_check']) and all(x['retained_connected_objects'] for x in r['reconstruction_endpoint_checks']) and all(r['new_copper_inside_source_outline'].values()) and all(j['center_matches_retained_native_endpoint'] and j['retained_track_width_mm']==.6 for j in r['full_width_endpoint_joins'])
(HERE/'joint-escape-proof.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:r[k] for k in ['all_geometry_checks_pass','reconstruction_endpoint_checks']},indent=2))
for k in ['stub_check','via_check','bec_check']:print(k, r[k]['minimum_excess_mm'],r[k]['failures'])
