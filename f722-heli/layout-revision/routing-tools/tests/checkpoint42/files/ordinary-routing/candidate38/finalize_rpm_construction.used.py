#!/usr/bin/env python3
"""Create a source-bound constructed-native alternative, never an engine success."""
import copy,hashlib,importlib.util,json,math,pathlib
import numpy as np
import shapely
from shapely.geometry import LineString,Point,Polygon
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('rpm_screen',HERE/'screen.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
s=q.s;repair_path=HERE/'corner-repair.json';repair=json.loads(repair_path.read_text());assert all(r['passed'] for r in repair['repairs'])
assert repair['refine_helper_sha256']==q.sha(HERE/'refine.py') and repair['source_identity']==q.ID
NET=q.NET;threshold=.00015
arrays={l:(np.array([o['geometry'] for o in obs],dtype=object),np.array([o['required_center_distance_mm'] for o in obs])) for l,obs in q.OBS.items()}
def can_join(a,b,l):
 g=LineString([a,b]);ga,req=arrays[l]
 return s.OUTLINE.covers(g) and float(np.min(shapely.distance(g,ga)-req))>=threshold
# Complete each pad entry only along a segment wholly inside its actual native pad.
b=copy.deepcopy(q.raw['traces'][0]['requested_corners_mm']);f=copy.deepcopy(repair['repaired_f_points_mm']);extensions=[]
for layer,key,pts,at_start in [('B.Cu','R39.1',b,True),('F.Cu','R36.2',f,False)]:
 pad=q.K[key];old=pts[0 if at_start else -1];new=pad['xy'];g=s.geom(pad['inside'][layer]);line=LineString([old,new]);assert g.covers(line) and line.distance(g.boundary)>s.HALF+s.ERROR
 extensions.append({'pad':key,'uuid':pad['uuid'],'layer':layer,'old_endpoint_mm':old,'new_endpoint_mm':new,'extension_points_mm':[old,new],'extension_wholly_within_actual_native_pad':True,'minimum_full_width_interior_reserve_mm':line.distance(g.boundary)-s.HALF})
 if at_start:pts.insert(0,new)
 else:pts.append(new)

def simplify(points,layer):
 # Monotone indices, no new geometry search sites. Every new line passes all native obstacles.
 out=[points[0]];indices=[0];i=0
 while i<len(points)-1:
  for j in range(len(points)-1,i,-1):
   if points[j]!=points[i] and can_join(points[i],points[j],layer):break
  else:raise AssertionError('No clearing continuation')
  out.append(points[j]);indices.append(j);i=j
 return out,indices
paths=[]
for layer,pts in [('B.Cu',b),('F.Cu',f)]:
 pp,ii=simplify(pts,layer);check=q.screen_trace(pp,layer);assert check['all_checks_pass_with_polygon_error_reserve'] and check['inside_board']
 paths.append({'net':NET,'layer':layer,'width_mm':.127,'points_mm':pp,'length_mm':LineString(pp).length,'before_simplification_points_mm':pts,'kept_indices':ii,'native_polygon_check':check})
xy=q.raw['via_transitions'][0]['point_mm'];via=q.screen_via(xy);assert via['all_checks_pass_with_polygon_error_reserve']
# A prospective analytic full-width annular strip on each incident segment.
# This is not a substitute for the imported native-annulus audit.
annular=[]
for p in paths:
 pts=p['points_mm'];a,b=(pts[-1],pts[-2]) if p['layer']=='B.Cu' else (pts[0],pts[1]);assert a==xy
 length=math.dist(a,b);assert length>.175
 direction=[(b[k]-a[k])/length for k in range(2)];normal=[-direction[1],direction[0]];verts=[]
 for radius,sign in [(.155,-1),(.155,1),(.165,1),(.165,-1)]:verts.append([a[k]+direction[k]*radius+normal[k]*sign*s.HALF for k in range(2)])
 strip=Polygon(verts);d0=Point(xy).distance(strip);d1=max(math.dist(xy,v) for v in verts)
 assert d0>.10+s.ERROR and d1<.225-s.ERROR
 annular.append({'layer':p['layer'],'incident_points_mm':[a,b],'full_width_strip_polygon_mm':verts,'strip_width_mm':.127,'strip_length_mm':.010,'inner_drill_reserve_mm':d0-.10,'outer_copper_reserve_mm':.225-d1,'prospective_analytic_annular_passed':True,'native_actual_annulus_verification_pending':True})
entries=[]
for p,key,idx in [(paths[0],'R39.1',0),(paths[1],'R36.2',-1)]:
 o=q.K[key];g=s.geom(o['inside'][p['layer']]);pt=Point(p['points_mm'][idx]);assert g.covers(pt) and pt.distance(g.boundary)>s.HALF+s.ERROR
 entries.append({'pad':key,'uuid':o['uuid'],'layer':p['layer'],'point_mm':list(pt.coords[0]),'full_round_cap_in_actual_native_pad':True,'extra_containment_mm':pt.distance(g.boundary)-s.HALF})
# Preserve exact current fill checks separately. New through-via needs only authorized GND fill antipads.
fill_rows=[];reference=[]
for z in s.N['zones']:
 if z['uuid'] not in q.EXCLUDED:continue
 for l,ps in z['filled'].items():
  g=s.geom(ps);dist=Point(xy).distance(g);fill_rows.append({'uuid':z['uuid'],'layer':l,'net':z['net'],'saved_fill_distance_from_via_center_mm':dist,'saved_fill_copper_gap_mm':dist-.225,'saved_fill_violates_proposed_via_clearance':dist<.352,'native_antipad_refill_required':True})
  track=next(p for p in paths if p['layer']==('F.Cu' if l=='In1.Cu' else 'B.Cu'));line=LineString(track['points_mm']);drills=[d for o,c,m,d in s.OBJECTS if d is not None and l in o.get('barrel_layers',[])]
  actual=g.difference(shapely.union_all(drills));missing=line.difference(actual)
  reference.append({'track_layer':track['layer'],'reference_layer':l,'current_saved_plane_missing_centerline_mm':missing.length,'post_refill_reference_acceptance_pending':True,'scope':'Current saved-plane projection only; before new via antipads and native refill.'})
extra_files={'repair_receipt':repair_path,'refine_helper':HERE/'refine.py','finalize_helper':pathlib.Path(__file__),'failed_partial_receipt':q.ROOT/'model-candidate37-ready/filtered10.failed-partial-geometry.json','importer':q.ROOT/'import_session.py'}
identity=dict(q.ID);identity.update({k:{'path':str(p),'sha256':q.sha(p)} for k,p in extra_files.items()})
proposal={'schema':'f722-rpm-native-alternative/v1','status':'fully_polygon_screened_constructed_native_alternative_pending_native_gates','source_identity':identity,'source_board_sha256':s.EXPECTED,'source_native_sha256':q.sha(s.SOURCE),'engine_result':'FAILED','engine_insertion_succeeded':False,'failed_engine_partial_additions_adopted':False,'raw_engine_located_record':q.raw,'raw_refusal_record_path':str(HERE/'captured-rpm-records.json'),'raw_refusal_record_sha256':q.sha(HERE/'captured-rpm-records.json'),'raw_screen_path':str(HERE/'raw-screen.json'),'raw_screen_sha256':q.sha(HERE/'raw-screen.json'),'net':NET,'logical_net':NET,'paths':paths,'vias':[via],'local_repairs':repair['repairs'],'pad_entry_extensions':extensions,'endpoint_entries':entries,'prospective_annular_transit':annular,'saved_reference_fill_conflicts':fill_rows,'prospective_reference_projection':reference,'rules_mm':q.M['rules'],'existing_source_copper_allowed_only_for_this_ordinary_physical_net':True,'protected_alias_exemptions':False,'existing_geometry_changes':[],'remove_existing_objects':[],'all_source_native_objects_fixed':True,'regenerable_reference_zones':q.EXCLUDED,'reference_plane_policy':q.M['reference_plane_policy'],'engine_routing_performed_by_helper':False,'native_DRC_performed':False,'native_refill_performed':False,'routing_acceptance_claimed':False,'pending_gates':['native import / exact source preservation','native DRC and connectivity','native actual endpoint/annular process checks','protection and pin/net proof','GND-only In1/In4 refill and post-refill reference validation']}

def validate(p):
 assert p['source_board_sha256']==s.EXPECTED==q.sha(s.BOARD),'wrong source board'
 for i in p['source_identity'].values():assert q.sha(i['path'])==i['sha256'],'source content changed'
 assert p['source_native_sha256']==q.sha(s.SOURCE) and p['net']==p['logical_net']==NET
 assert not p['engine_insertion_succeeded'] and not p['failed_engine_partial_additions_adopted'] and not p['existing_geometry_changes'] and not p['remove_existing_objects']
 assert len(p['paths'])==2 and len(p['vias'])==1
 for r,key,idx in [(p['paths'][0],'R39.1',0),(p['paths'][1],'R36.2',-1)]:
  assert r['net']==NET and r['layer'] in ['F.Cu','B.Cu'] and r['width_mm']==.127,'invalid track process'
  pts=r['points_mm'];assert all([round(x*1e5)/1e5,round(y*1e5)/1e5]==[x,y] for x,y in pts),'off grid'
  assert all(a!=b for a,b in zip(pts,pts[1:]))
  pad=q.K[key];g=s.geom(pad['inside'][r['layer']]);point=Point(pts[idx]);assert g.contains(point) and point.distance(g.boundary)>=s.HALF+s.ERROR,'outside pad'
  assert q.screen_trace(pts,r['layer'])['all_checks_pass_with_polygon_error_reserve'],'native track collision'
 v=p['vias'][0];assert v['diameter_mm']==.45 and v['drill_mm']==.20 and v['tented_both_faces'],'invalid via process'
 assert v['xy_mm']==p['paths'][0]['points_mm'][-1]==p['paths'][1]['points_mm'][0]==xy,'transition mismatch'
 assert q.screen_via(v['xy_mm'])['all_checks_pass_with_polygon_error_reserve'],'native via collision'
validate(proposal)
controls=[]
for label,mutate in [('wrong_source',lambda p:p.update(source_board_sha256='0'*64)),('outside_pad',lambda p:p['paths'][0]['points_mm'].__setitem__(0,[0.,0.])),('invalid_via_process',lambda p:p['vias'][0].update(drill_mm=.25)),('invalid_track_process',lambda p:p['paths'][0].update(width_mm=.10))]:
 bad=copy.deepcopy(proposal);mutate(bad)
 try:validate(bad)
 except AssertionError as e:controls.append({'control':label,'rejected':True,'reason':str(e)})
 else:raise AssertionError('Negative control admitted')
proposal['negative_controls']=controls;proposal['source_recheck_unchanged']=all(q.sha(i['path'])==i['sha256'] for i in identity.values());assert proposal['source_recheck_unchanged']
PP=HERE/'proposal.json';PP.write_text(json.dumps(proposal,indent=2)+'\n')
# Source-preserving add-only packet: existing ordinary RPM_LV copper remains native.
contract={'schema':'f722-native-add-only-import/v1','engine_planning_model':False,'physical_board':str(s.BOARD),'physical_native':str(s.SOURCE),'board_sha256':s.EXPECTED,'native_sha256':q.sha(s.SOURCE),'aliases':q.M['aliases'],'ordinary_nets':q.M['ordinary_nets'],'routable_layers':q.M['routable_layers'],'mutable_source_ids':[],'source_logical_nets':q.L['logical_route_map'],'regenerable_reference_zones':q.EXCLUDED,'reference_plane_policy':q.M['reference_plane_policy'],'all_source_copper_fixed':True,'proposal_sha256':q.sha(PP)}
model=HERE/'native-construction-model.json';model.write_text(json.dumps(contract,indent=2)+'\n')
wires=[];routes=[]
for p in paths:
 ints=[[round(x*1e5),round(-y*1e5)] for x,y in p['points_mm']]
 wires.append('(wire (path '+p['layer']+' 12700 '+' '.join(f'{x} {y}' for x,y in ints)+') (type route))')
 routes.append({'kind':'track','fixed':'NOT_FIXED','nets':[NET],'layer':p['layer'],'width':.127,'points':p['points_mm']})
wires.append(f'(via VIA_450_200 {round(xy[0]*1e5)} {round(-xy[1]*1e5)})');routes.append({'kind':'via','fixed':'NOT_FIXED','nets':[NET],'xy':xy,'diameter':.45,'drill':.20})
ses=HERE/'constructed.ses';ses.write_text('(session "rpm-constructed-native-alternative-not-engine-success" (routes (resolution mm 100000) (network_out (net "RPM_LV" '+' '.join(wires)+'))))\n')
receipt={'status':proposal['status'],'engine_insertion_succeeded':False,'engine_result':'FAILED','constructed_native_alternative':True,'source_board_sha256':s.EXPECTED,'source_native_sha256':q.sha(s.SOURCE),'proposal_sha256':q.sha(PP),'helper_sha256':q.sha(__file__),'model_sha256':q.sha(model),'session_sha256':q.sha(ses),'new_track_segments':sum(len(p['points_mm'])-1 for p in paths),'new_vias':1,'source_objects_removal_allowed':False,'native_validation_required':True,'pending_gates':proposal['pending_gates'],'negative_controls':controls}
report=HERE/'constructed-report.json';report.write_text(json.dumps({'board_sha256':s.EXPECTED,'model_sha256':q.sha(model),'routes':routes,'route_construction':receipt,'route_solver_used':False,'engine_insertion_succeeded':False,'native_validation_required':True},indent=2)+'\n');receipt['report_sha256']=q.sha(report)
(HERE/'construction.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('CONSTRUCTION',json.dumps(receipt),flush=True)
print('SIMPLIFIED',json.dumps([{'layer':p['layer'],'points':p['points_mm'],'length_mm':p['length_mm'],'minimum_extra_mm':p['native_polygon_check']['minimum_extra_clearance_mm']} for p in paths]),flush=True)
