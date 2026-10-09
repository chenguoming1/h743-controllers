#!/usr/bin/env python3
"""Bounded, read-only native pad-to-pad audit on frozen candidate15."""
import native_geometry as s
from shapely.geometry import Point,LineString
from shapely.ops import nearest_points
import collections,hashlib,itertools,json,pathlib,time
HERE=pathlib.Path(__file__).resolve().parent
MODEL=s.ROOT/'model-candidate15-ports/model.json'
M=json.loads(MODEL.read_text())
NETS=['BARO_SCL','BARO_SDA','ADC_BUS']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
IDENTITY={'board_path':str(s.BOARD),'board_sha256':sha(s.BOARD),'native_path':str(s.SOURCE),'native_sha256':sha(s.SOURCE),'model_path':str(MODEL),'model_sha256':sha(MODEL),'generator_sha256':sha(pathlib.Path(__file__)),'native_geometry_helper_sha256':sha(HERE/'native_geometry.py'),'native_polygon_max_error_mm':s.ERROR}
assert M['board_sha256']==IDENTITY['board_sha256'] and M['native_sha256']==IDENTITY['native_sha256']

def endpoint_sites(o,layer):
    p=s.geom(o['inside'][layer]);x,y=o['xy'];sites=[(x,y)]
    # Interior tip candidates on each axis, retaining at least a half width of pad.
    x0,y0,x1,y1=p.bounds
    for site in [(x0+.07,y),(x1-.07,y),(x,y0+.07),(x,y1-.07)]:
        q=Point(site)
        if p.covers(q) and q.distance(p.boundary)>s.HALF:sites.append(site)
    return sites

def path_choices(a,b):
    yield from s.paths2(a,b)
    # Four three-segment orthogonal doglegs through midpoint/exterior axes.
    for x in [(a[0]+b[0])/2,min(a[0],b[0])-.25,max(a[0],b[0])+.25]:yield [a,(x,a[1]),(x,b[1]),b]
    for y in [(a[1]+b[1])/2,min(a[1],b[1])-.25,max(a[1],b[1])+.25]:yield [a,(a[0],y),(b[0],y),b]

def minimum(g,obstacles):
    return min((g.distance(o['geometry'])-o['required_center_distance_mm'],i) for i,o in enumerate(obstacles))

def audit_pair(a,b,layer,t):
    sites_a=endpoint_sites(a,layer);sites_b=endpoint_sites(b,layer)
    roi=s.box(*LineString([a['xy'],b['xy']]).bounds).buffer(.26,join_style='mitre')
    # Search uses a bounded subset, final receipts always recheck all obstacles.
    local=[o for o in t if o['geometry'].distance(roi)<=o['required_center_distance_mm']]
    tested=[];seen=set()
    for pa,pb in itertools.product(sites_a,sites_b):
        for points in path_choices(pa,pb):
            pts=[]
            for p in points:
                p=tuple(round(v,6) for v in p)
                if not pts or p!=pts[-1]:pts.append(p)
            key=tuple(pts)
            if key in seen:continue
            seen.add(key);g=LineString(pts)
            margin,_=minimum(g,local)
            tested.append((margin,g.length,pts))
    passed=sorted((p for p in tested if p[0]>=0),key=lambda p:p[1])
    direct=list(s.paths2(tuple(a['xy']),tuple(b['xy'])))[0]
    representative=sorted(tested,key=lambda p:(-p[0],p[1]))[:3]
    failures=[]
    for margin,length,pts in representative:
        checks=s.check(LineString(pts),t,True)
        failures.append({'points_mm':pts,'length_mm':length,'minimum_extra_clearance_mm':checks[0]['extra_clearance_mm'],'nearest_constraints':checks[:5]})
    return {'start_pad':a['key'],'end_pad':b['key'],'start_pad_uuid':a['uuid'],'end_pad_uuid':b['uuid'],'layer':layer,'tested_path_count':len(tested),'passed_local_screen_path_count':len(passed),'bounded_search_description':'Pad centers and four full-width interior axis tips; direct, one-bend orthogonal/45-degree paths, and midpoint or 0.25 mm exterior orthogonal doglegs. No grid, full search or impossibility claim.','direct_centerline':{'points_mm':direct,'length_mm':LineString(direct).length,'nearest_constraints':s.check(LineString(direct),t,True)[:8]},'best_tested_paths':failures,'shortest_successful_tested_points_mm':passed[0][2] if passed else None}

started=time.monotonic();results=[]
for net in NETS:
    role=M['roles'][net];assert role['kind']=='ordinary'
    pads=[o for o,_,_,_ in s.OBJECTS if o['net']==net and o['kind']=='pad']
    assert set(o['uuid'] for o in pads)==set(role['terminals'])
    same=[];different=[]
    for a,b in itertools.combinations(pads,2):
        common=set(a['copper'])&set(b['copper'])
        if not common:
            different.append({'start_pad':a['key'],'start_pad_uuid':a['uuid'],'start_layers':list(a['copper']),'end_pad':b['key'],'end_pad_uuid':b['uuid'],'end_layers':list(b['copper']),'pad_center_distance_mm':Point(a['xy']).distance(Point(b['xy'])),'same_layer_connection_possible':False,'reason':'These native SMT pads share no copper layer. A complete connection requires at least one plated layer transition; no via proposal is in this audit.'})
        for layer in common:
            t,_,_=s.obstacles(net,layer)
            same.append(audit_pair(a,b,layer,t))
    results.append({'net':net,'logical_role':role,'existing_native_tracks_or_vias_on_net':sum(o['net']==net and o['kind']!='pad' for o,_,_,_ in s.OBJECTS),'same_layer_pairs':same,'cross_layer_pairs':different})
    print(net,[(p['start_pad'],p['end_pad'],p['passed_local_screen_path_count'],p['tested_path_count']) for p in same],flush=True)

# Select the short robust octilinear ADC closure. The direct line is a valid alternative.
net='ADC_BUS';layer='F.Cu';a=next(o for o,_,_,_ in s.OBJECTS if o.get('key')=='R42.2');b=next(o for o,_,_,_ in s.OBJECTS if o.get('key')=='R43.1')
points=[(21.01,17.5),(21.89,17.5),(21.99,17.6)]
t,_,excluded=s.obstacles(net,layer);segments=[]
for i,(p,q) in enumerate(zip(points,points[1:])):
    checks=s.check(LineString([p,q]),t,True);assert all(c['pass_nominal'] for c in checks)
    segments.append({'index':i,'start_mm':p,'end_mm':q,'length_mm':Point(p).distance(Point(q)),'minimum_extra_clearance_mm':checks[0]['extra_clearance_mm'],'all_obstacle_checks':checks})
endpoint_proofs=[]
for o,point in [(a,points[0]),(b,points[-1])]:
    pad=s.geom(o['inside'][layer]);q=Point(point);margin=q.distance(pad.boundary)-s.HALF
    assert pad.covers(q) and margin>0
    endpoint_proofs.append({'pad_key':o['key'],'pad_uuid':o['uuid'],'point_mm':point,'full_round_cap_inside_actual_native_pad':True,'center_to_pad_boundary_mm':q.distance(pad.boundary),'track_radius_mm':s.HALF,'extra_containment_mm':margin})
proposal={'net':net,'net_code':a['net_code'],'pad_key':a['key'],'pad_uuid':a['uuid'],'target_pad_key':b['key'],'target_pad_uuid':b['uuid'],'layer':layer,'points_mm':points,'width_mm':.127,'vias':[],'logical_role':M['roles'][net],'total_track_length_mm':LineString(points).length,'all_segments_octilinear':True,'minimum_extra_clearance_mm':min(p['minimum_extra_clearance_mm'] for p in segments),'endpoint_full_width_entry':endpoint_proofs,'all_nominal_native_polygon_checks_pass':True,'source_polygon_error_mm':s.ERROR,'minimum_clearance_reserve_exceeds_polygon_error':min(p['minimum_extra_clearance_mm'] for p in segments)>s.ERROR,'native_drc_performed':False,'routing_acceptance_claimed':False,'expected_connectivity_effect':'Join R42.2 to R43.1 only; C31.1 and U1.10 remain separate terminals.','excluded_regenerable_gnd_zone_ids':excluded,'segments':[{k:v for k,v in seg.items() if k!='all_obstacle_checks'}|{'nearest_constraints':seg['all_obstacle_checks'][:5]} for seg in segments]}
assert s.OUTLINE.covers(LineString(points))
assert sha(s.BOARD)==IDENTITY['board_sha256'] and sha(s.SOURCE)==IDENTITY['native_sha256'] and sha(MODEL)==IDENTITY['model_sha256']
proof={'source_identity':IDENTITY,'scope':'Read-only bounded native geometry audit on three ordinary nets. No board/model mutation, JVM, full search, global clearance relaxation, native DRC or routing acceptance. Fixed copper and support retained; model ordinary terminal membership explicitly checked.','rules_mm':{'width':.127,'foreign_copper_clearance':.127,'edge_and_npth_copper_clearance':.254},'audit_results':results,'selected_proposal':proposal,'selected_proposal_all_segment_checks':segments,'prior_attempt_context':{'source':'Parent task message received 2026-10-09 09:49 UTC','detail':'The prior broad ADC_BUS run attempted C31.1 and U1.10 before stopping after five overall successes. R42.2 and R43.1 were not attempted. This new local closure is therefore an unattempted opportunity, not an engine/native reachability contradiction.'},'source_recheck_unchanged':True,'elapsed_seconds':time.monotonic()-started}
proof_path=HERE/'candidate15-short-local-exact-witnesses.json';proof_path.write_text(json.dumps(proof,indent=2)+'\n')
main={'source_identity':IDENTITY,'status':'native_polygon_proposal_pending_native_drc','proposals':[proposal],'direct_alternative_points_mm':[[21.01,17.5],[21.99,17.6]],'direct_alternative_length_mm':Point(a['xy']).distance(Point(b['xy'])),'proof_receipt':{'path':str(proof_path),'sha256':sha(proof_path)},'source_recheck_unchanged':True}
(HERE/'candidate15-short-local-proposals.json').write_text(json.dumps(main,indent=2)+'\n')
print('PROPOSAL',HERE/'candidate15-short-local-proposals.json','seconds',proof['elapsed_seconds'],flush=True)
