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
SOURCE=ROOT/'candidate48/f722-heli.native.json'
BOARD=ROOT/'candidate48/f722-heli.kicad_pcb'
EXPECTED='dcdd0e5655d098ceaffa7f40b6a21f1ca101429ac8eb142c50fa96df86697e68'
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

