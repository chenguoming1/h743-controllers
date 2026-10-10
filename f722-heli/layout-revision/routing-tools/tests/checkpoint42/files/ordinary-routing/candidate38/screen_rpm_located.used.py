#!/usr/bin/env python3
"""Read-only exact-native screen of the complete refused candidate37 RPM_LV path."""
import collections, hashlib, importlib.util, json, math, pathlib, sys
import numpy as np
import shapely
from shapely.geometry import LineString, Point
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
HELPER=ROOT/'tests/i2c-candidate35/native_geometry37.py'
spec=importlib.util.spec_from_file_location('rpm_native_source37',HELPER);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
MODEL=ROOT/'model-candidate37-ready/model.json';MAP=ROOT/'candidate37/f722-heli.logical-route-map.json';LOG=ROOT/'model-candidate37-ready/filtered10.log';BOUNDED=ROOT/'model-candidate37-ready/filtered10.bounded-run.json'
M=json.loads(MODEL.read_text());L=json.loads(MAP.read_text());DONE=json.loads(BOUNDED.read_text());NET='RPM_LV'
FILES={'board':s.BOARD,'native':s.SOURCE,'model':MODEL,'logical_map':MAP,'engine_log':LOG,'bounded_run':BOUNDED,'geometry_helper':HELPER,'screen_helper':pathlib.Path(__file__)}
ID={k:{'path':str(p),'sha256':sha(p)} for k,p in FILES.items()}
assert M['board_sha256']==L['board_sha256']==s.EXPECTED and M['native_sha256']==sha(s.SOURCE) and DONE['model_sha256']==sha(MODEL)
assert M['roles'][NET]['kind']=='ordinary' and M['aliases'][NET]==NET
ROWS=[]
for num,line in enumerate(LOG.read_text().splitlines(),1):
 if line.startswith('INSERT_DIAGNOSTIC '):
  r=json.loads(line[len('INSERT_DIAGNOSTIC '):]);
  if r.get('net')==NET:ROWS.append({'line':num,'record':r})
raw=next(r['record'] for r in ROWS if r['record']['stage']=='located_connection')
assert raw['status']=='located_only' and len(raw['traces'])==2 and len(raw['via_transitions'])==1
assert raw['traces'][0]['requested_corners_mm'][-1]==raw['traces'][1]['requested_corners_mm'][0]==raw['via_transitions'][0]['point_mm']
assert raw['target_endpoint']['contact_label']=='R39.1' and raw['start_endpoint']['contact_label']=='R36.2'
(HERE/'captured-rpm-records.json').write_text(json.dumps({'source_identity':ID,'engine_insertion_succeeded':False,'records':ROWS},indent=2)+'\n')
O={o['uuid']:o for o in s.N['objects']};K={o['key']:o for o in O.values() if o['kind']=='pad'}
OBS={};VOBS=None;EXCLUDED=None
for t in raw['traces']:
 layer=t['layer'];trace,via,skipped=s.obstacles(NET,layer)
 # Track copper must additionally avoid every foreign plated drill by 0.20 mm.
 for o,c,m,d in s.OBJECTS:
  if d is not None and not o.get('npth') and o['net']!=NET:
   trace.append(dict(object=o.get('key',o['uuid']),uuid=o['uuid'],net=o['net'],kind=o['kind'],category='foreign_drill_to_track_copper',layers=o.get('barrel_layers',[]),required_physical_gap_mm=.20,moving_radius_mm=s.HALF,required_center_distance_mm=.20+s.HALF,geometry=d))
 OBS[layer]=trace;VOBS=via;EXCLUDED=skipped
assert sorted(EXCLUDED)==sorted(M['regenerable_reference_zones'])

def screen_trace(points,layer):
 g=LineString(points);checks=s.check(g,OBS[layer],True)
 return dict(layer=layer,width_mm=.127,points_mm=points,length_mm=g.length,obstacle_count=len(checks),inside_board=s.OUTLINE.covers(g),minimum_extra_clearance_mm=checks[0]['extra_clearance_mm'],all_checks_pass_nominal=checks[0]['extra_clearance_mm']>=-1e-9,all_checks_pass_with_polygon_error_reserve=checks[0]['extra_clearance_mm']>=s.ERROR,nearest_constraints=checks[:15],violations=[r for r in checks if r['extra_clearance_mm']<s.ERROR])

def screen_via(xy):
 checks=s.check(Point(xy),VOBS,True)
 return dict(net=NET,xy_mm=xy,diameter_mm=.45,drill_mm=.20,span=s.N['copper_layers'],tented_both_faces=True,inside_board=s.OUTLINE.covers(Point(xy)),obstacle_count=len(checks),category_counts=dict(collections.Counter(r['category'] for r in checks)),minimum_extra_clearance_mm=checks[0]['extra_clearance_mm'],all_checks_pass_nominal=checks[0]['extra_clearance_mm']>=-1e-9,all_checks_pass_with_polygon_error_reserve=checks[0]['extra_clearance_mm']>=s.ERROR,nearest_constraints=checks[:20],violations=[r for r in checks if r['extra_clearance_mm']<s.ERROR],mask_minimum_by_face_mm={l:min(r['extra_clearance_mm'] for r in checks if r['category']=='all_smt_masks_no_net_exception' and l in r['layers']) for l in ['F.Mask','B.Mask']},all_drill_minimum_extra_mm=min(r['extra_clearance_mm'] for r in checks if r['category']=='all_drills_no_net_exception'))

TRACES=[screen_trace(t['requested_corners_mm'],t['layer']) for t in raw['traces']];VIA=screen_via(raw['via_transitions'][0]['point_mm'])
segment_fails=[]
for t in raw['traces']:
 for i,(a,b) in enumerate(zip(t['requested_corners_mm'],t['requested_corners_mm'][1:])):
  r=screen_trace([a,b],t['layer'])
  if r['violations']:segment_fails.append(dict(trace_index=t['trace_index'],segment_index=i,points_mm=[a,b],violations=r['violations']))
entries=[]
for ep in [raw['target_endpoint'],raw['start_endpoint']]:
 o=O[ep['native_uuid']];g=s.geom(o['inside'][ep['layer']]);p=Point(ep['point_mm'])
 entries.append({'pad':o['key'],'uuid':o['uuid'],'point_mm':ep['point_mm'],'pad_xy_mm':o['xy'],'center_inside_native_pad':g.covers(p),'full_width_inside_extra_mm':p.distance(g.boundary)-s.HALF})
report=dict(schema='f722-rpm-located-native-screen/v1',source_identity=ID,source_board_sha256=s.EXPECTED,engine_insertion_succeeded=False,engine_result='FAILED',raw_engine_record=raw,raw_trace_checks=TRACES,raw_via_checks=VIA,raw_endpoint_entries=entries,raw_segment_violations=segment_fails,regenerable_reference_zones=EXCLUDED,reference_plane_policy=M['reference_plane_policy'],source_object_removal_allowed=False,native_drc_performed=False,native_refill_performed=False,routing_acceptance_claimed=False)
(HERE/'raw-screen.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'raw_traces':[{k:r[k] for k in ['layer','minimum_extra_clearance_mm','violations']} for r in TRACES],'via':VIA,'entries':entries,'segment_fail_count':len(segment_fails)},indent=2),flush=True)
assert all(sha(p)==ID[k]['sha256'] for k,p in FILES.items())
