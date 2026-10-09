#!/usr/bin/env python3
"""Read-only bounded native pad/via stub proposals, never routing or board mutation."""
import collections, hashlib, heapq, itertools, json, math, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / 'python-deps'))
import shapely
from shapely import unary_union
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import nearest_points
ROOT=pathlib.Path(__file__).resolve().parents[2]
HERE=pathlib.Path(__file__).resolve().parent
SOURCE=ROOT/'candidate08/f722-heli.native.json'
BOARD=ROOT/'candidate08/f722-heli.kicad_pcb'
EXPECTED='1ff8ee645bd5fea7bbbc30cd4e5269aab76a2032efe3e2c4e77a0becd85e9edf'
N=json.loads(SOURCE.read_text())
assert hashlib.sha256(BOARD.read_bytes()).hexdigest()==N['board_sha256']==EXPECTED
HALF=.0635; VR=.225; DR=.1; ERROR=N['maximum_polygon_error_mm']

def geom(ps):
    pp=[Polygon(p['outer'],p.get('holes',[])) for p in ps]
    assert all(p.is_valid for p in pp)
    r=unary_union(pp);assert r.is_valid
    return r
OUTLINE=geom(N['outline_with_npth']['polygons'])
OBJECTS=[]
for o in N['objects']:
    OBJECTS.append((o,{l:geom(ps) for l,ps in o['copper'].items()}, {l:geom(m['polygons']) for l,m in o.get('mask',{}).items()} if o.get('smd') else {},geom(o['drill']['outside']) if o.get('drill') else None))

def obstacles(net,layer):
    trace=[];via=[];skipped=[]
    def add(out,o,category,gap,reserve,g,layers):
        out.append(dict(object=o.get('key',o['uuid']),uuid=o['uuid'],net=o.get('net'),kind=o.get('kind','zone'),category=category,layers=layers,required_physical_gap_mm=gap,moving_radius_mm=reserve,required_center_distance_mm=gap+reserve,geometry=g))
    for o,copper,masks,drill in OBJECTS:
        if o['net']!=net:
            for l,g in copper.items():
                if l==layer:add(trace,o,'foreign_copper',.127,HALF,g,[l])
                add(via,o,'foreign_copper',.127,VR,g,[l])
        for l,g in masks.items():add(via,o,'all_smt_masks_no_net_exception',.20,DR,g,[l])
        if drill is not None:
            add(via,o,'all_drills_no_net_exception',.25,DR,drill,o.get('barrel_layers',[]))
            if o.get('npth'):
                add(trace,o,'npth_copper',.254,HALF,drill,[])
                add(via,o,'npth_copper',.254,VR,drill,[])
    for z in N['zones']:
        if z['rule']:
            g=geom(z['outline'])
            if layer in z['layers'] and(z['forbid']['tracks'] or z['forbid']['copper']):add(trace,z,'rule_keepout',0,HALF,g,z['layers'])
            if z['layers'] and(z['forbid']['vias'] or z['forbid']['copper']):add(via,z,'rule_keepout',0,VR,g,z['layers'])
        elif z['net']=='GND' and set(z['layers'])<={'In1.Cu','In4.Cu'}:skipped.append(z['uuid'])
        elif z['net']!=net:
            for l,ps in z['filled'].items():
                g=geom(ps)
                if l==layer:add(trace,z,'foreign_zone_copper',.127,HALF,g,[l])
                add(via,z,'foreign_zone_copper',.127,VR,g,[l])
    for out,radius in [(trace,HALF),(via,VR)]:
        out.append(dict(object='board-outline-including-npth',uuid=None,net=None,kind='outline',category='edge_npth_copper',layers=[],required_physical_gap_mm=.254,moving_radius_mm=radius,required_center_distance_mm=.254+radius,geometry=OUTLINE.boundary))
    return trace,via,skipped

def check(g,obstacles,full=False):
    rr=[]
    for o in obstacles:
        dist=g.distance(o['geometry']);margin=dist-o['required_center_distance_mm']
        if full:
            a,b=nearest_points(g,o['geometry'])
            r={k:v for k,v in o.items() if k!='geometry'}
            r.update(center_distance_mm=dist,physical_gap_mm=dist-o['moving_radius_mm'],extra_clearance_mm=margin,pass_nominal=margin>=-1e-9,pass_with_polygon_error=margin>=ERROR,witness_on_moving_centerline_mm=list(a.coords[0]),witness_on_native_obstacle_mm=list(b.coords[0]))
        else:r=dict(object=o['object'],category=o['category'],layers=o['layers'],extra_clearance_mm=margin)
        rr.append(r)
    return sorted(rr,key=lambda r:r['extra_clearance_mm'])

def paths2(a,b):
    # One- or two-segment octilinear centerlines; degenerate bends removed.
    yield [a,b]
    dx=b[0]-a[0];dy=b[1]-a[1];sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1
    mids=[(a[0],b[1]),(b[0],a[1]),(a[0]+sx*abs(dy),b[1]),(b[0],a[1]+sy*abs(dx)),(b[0]-sx*abs(dy),a[1]),(a[0],b[1]-sy*abs(dx))]
    for m in mids:
        if m not in [a,b]:yield [a,m,b]

TARGETS=[('R44.1','ADC_DIV_MID','F.Cu',(25.38059,14.57554)),('U3.3','FLASH_WP_N','B.Cu',(31.5,20.98530))]
PATHS={
    'R44.1':[(25.8,16.51),(25.62,16.51),(24.65,15.54),(24.65,15.12),(24.88,14.89),(25.06613,14.89),(25.38059,14.57554)],
    'U3.3':[(30.95,21.365),(31.12030,21.365),(31.5,20.98530)],
}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def heading(a,b):
    dx=b[0]-a[0];dy=b[1]-a[1]
    assert abs(dx)<1e-9 or abs(dy)<1e-9 or abs(abs(dx)-abs(dy))<1e-9
    return round(math.degrees(math.atan2(dy,dx)),8)

def generate():
    started=time.monotonic()
    source={'board_path':str(BOARD),'board_sha256':sha(BOARD),'native_path':str(SOURCE),'native_sha256':sha(SOURCE),'native_polygon_max_error_mm':ERROR,'generator_path':str(pathlib.Path(__file__).resolve()),'generator_sha256':sha(pathlib.Path(__file__)),'shapely_version':shapely.__version__}
    proof={'source_identity':source,'scope':'Exact Euclidean distance checks against source native polygons. Constructible pad-to-via proposals only; no native DRC, engine acceptance, full-net route or accepted-board claim. No source board/model mutation, JVM, full solver, global free-space construction, geometry repair or global clearance relaxation. Only named In1/In4 regenerable GND fills excluded; native fixed copper and non-GND fills retained.','proposals':[]}
    proposals=[]
    for label,net,layer,viaxy in TARGETS:
        o=next(o for o,_,_,_ in OBJECTS if o.get('key')==label)
        trace_obs,via_obs,excluded=obstacles(net,layer)
        points=PATHS[label];via=Point(viaxy);path=LineString(points)
        assert tuple(points[-1])==tuple(viaxy)
        assert OUTLINE.covers(path) and OUTLINE.covers(via)
        pad=geom(o['inside'][layer]);first=LineString(points[:2])
        entry_distance=first.distance(pad.boundary)
        assert pad.covers(first) and entry_distance>HALF+ERROR
        all_segments=[];segments=[]
        for i,(a,b) in enumerate(zip(points,points[1:])):
            line=LineString([a,b]);checks=check(line,trace_obs,True)
            assert all(r['pass_with_polygon_error'] for r in checks)
            segment={'index':i,'start_mm':a,'end_mm':b,'heading_degrees':heading(a,b),'length_mm':line.length,'checked_obstacle_count':len(checks),'minimum_extra_clearance_mm':checks[0]['extra_clearance_mm'],'nearest_constraints':checks[:5]}
            segments.append(segment)
            all_segments.append({**segment,'all_obstacle_checks':checks})
        via_checks=check(via,via_obs,True)
        assert all(r['pass_with_polygon_error'] for r in via_checks)
        pad_entry={'source_inside_geometry':'objects[key].inside[layer]','centerline_start_mm':points[0],'full_width_entry_segment_index':0,'full_width_entry_length_mm':first.length,'entry_segment_inside_native_pad':True,'entry_centerline_minimum_pad_boundary_distance_mm':entry_distance,'track_half_width_mm':HALF,'full_width_containment_extra_margin_mm':entry_distance-HALF,'native_inside_polygon_error_reserve_passed':entry_distance-HALF>ERROR}
        proposal={'net':net,'net_code':o['net_code'],'pad_uuid':o['uuid'],'pad_key':label,'layer':layer,'points_mm':points,'via_xy_mm':viaxy,'width_mm':.127,'diameter_mm':.45,'drill_mm':.20,'via_type':'through','via_layers':['F.Cu','B.Cu'],'total_track_length_mm':path.length,'all_segments_octilinear':True,'pad_entry':pad_entry,'trace_minimum_extra_clearance_mm':min(r['minimum_extra_clearance_mm'] for r in segments),'via_minimum_extra_clearance_mm':via_checks[0]['extra_clearance_mm'],'segments':segments,'via_nearest_constraints':via_checks[:10],'trace_obstacle_count_per_segment':len(trace_obs),'via_obstacle_count':len(via_obs),'via_obstacle_category_counts':dict(collections.Counter(r['category'] for r in via_obs)),'excluded_regenerable_gnd_zone_ids':excluded,'inside_board_outline_with_npth':True,'all_checks_pass_nominal':True,'all_checks_pass_with_native_polygon_error_reserve':True,'native_drc_performed':False,'engine_check_performed_on_this_candidate':False,'accepted_route':False}
        proposals.append(proposal)
        proof['proposals'].append({**proposal,'segments':all_segments,'all_via_obstacle_checks':via_checks})
    # Confirm the two new, different-net proposals do not collide with each other.
    cross=[]
    for a,b in itertools.combinations(proposals,2):
        checks=[]
        ca=Point(a['via_xy_mm']);cb=Point(b['via_xy_mm'])
        for name,distance,reserve,required in [('via_copper_to_via_copper',ca.distance(cb),2*VR,.127),('via_drill_to_via_drill',ca.distance(cb),2*DR,.25),('a_via_to_b_trace',ca.distance(LineString(b['points_mm'])),VR+HALF,.127),('b_via_to_a_trace',cb.distance(LineString(a['points_mm'])),VR+HALF,.127)]:
            gap=distance-reserve;assert gap>=required+ERROR
            checks.append({'category':name,'distance_between_center_geometries_mm':distance,'physical_gap_mm':gap,'required_gap_mm':required,'extra_clearance_mm':gap-required,'pass':True})
        if a['layer']==b['layer']:
            distance=LineString(a['points_mm']).distance(LineString(b['points_mm']));gap=distance-2*HALF;assert gap>=.127+ERROR
            checks.append({'category':'trace_to_trace','physical_gap_mm':gap,'required_gap_mm':.127,'pass':True})
        cross.append({'a':a['pad_key'],'b':b['pad_key'],'trace_layers_distinct':a['layer']!=b['layer'],'checks':checks})
    assert sha(BOARD)==source['board_sha256'] and sha(SOURCE)==source['native_sha256']
    proof.update(interproposal_checks=cross,source_recheck_unchanged=True,elapsed_seconds=time.monotonic()-started)
    proof_path=HERE/'native-escape-stubs-exact-witnesses.json'
    proof_path.write_text(json.dumps(proof,indent=2)+'\n')
    main={'status':'constructible_native_polygon_proposals_pending_native_drc','source_identity':source,'scope':proof['scope'],'rules_mm':{'trace_width':.127,'via_diameter':.45,'via_drill':.20,'foreign_copper_gap':.127,'drill_to_both_faces_smt_mask_gap_no_net_exception':.20,'drill_to_drill_gap_no_net_exception':.25,'edge_and_npth_copper_gap':.254},'proof_receipt':{'path':str(proof_path),'sha256':sha(proof_path)},'proposals':proposals,'interproposal_checks':cross,'source_recheck_unchanged':True}
    (HERE/'native-escape-stubs-proposals.json').write_text(json.dumps(main,indent=2)+'\n')
    print(json.dumps({'proposal_file':str(HERE/'native-escape-stubs-proposals.json'),'proof_file':str(proof_path),'proof_sha256':sha(proof_path),'proposals':[{'pad':p['pad_key'],'points_mm':p['points_mm'],'via_xy_mm':p['via_xy_mm'],'track_length_mm':p['total_track_length_mm'],'trace_excess_mm':p['trace_minimum_extra_clearance_mm'],'via_excess_mm':p['via_minimum_extra_clearance_mm'],'trace_obstacles_per_segment':p['trace_obstacle_count_per_segment'],'via_obstacles':p['via_obstacle_count']} for p in proposals],'seconds':proof['elapsed_seconds']},indent=2))

if __name__=='__main__':generate()
