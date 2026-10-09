#!/usr/bin/env python3
"""Bounded source-bound no-via outer-layer pad closure screen. Does not edit boards."""
import hashlib,itertools,json,math,pathlib,time
import numpy as np
import shapely
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import nearest_points

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BOARD=ROOT/'candidate20/f722-heli.kicad_pcb'
NATIVE=ROOT/'candidate20/f722-heli.native.json'
MODEL=ROOT/'model-candidate19-ports/model.json'
MAP=ROOT/'candidate20/f722-heli.logical-route-map.json'
DRC=ROOT/'candidate20/drc-all.json'
EXPECTED='759dc5fae8d446057f9aa8e11292c02075d127e2268d0541349f7a8038ab07d5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
started=time.monotonic()
N=json.loads(NATIVE.read_text());M=json.loads(MODEL.read_text());L=json.loads(MAP.read_text());D=json.loads(DRC.read_text())
assert sha(BOARD)==N['board_sha256']==L['board_sha256']==EXPECTED
IDENTITY={p.stem:{'path':str(p),'sha256':sha(p)} for p in [BOARD,NATIVE,MODEL,MAP,DRC,pathlib.Path(__file__)]}
HALF=.0635;ERROR=N['maximum_polygon_error_mm']
def geom(ps):
    g=shapely.union_all([Polygon(p['outer'],p.get('holes',[])) for p in ps]);assert g.is_valid;return g
OUTLINE=geom(N['outline_with_npth']['polygons'])
O={o['uuid']:o for o in N['objects']};KEY={o['key']:o for o in O.values() if o['kind']=='pad'}
C={uid:{l:geom(ps) for l,ps in o['copper'].items()} for uid,o in O.items()}
INSIDE={uid:{l:geom(ps) for l,ps in o.get('inside',{}).items()} for uid,o in O.items()}
DRILLS={uid:geom(o['drill']['outside']) for uid,o in O.items() if o.get('drill')}
Z=[(z,{l:geom(ps) for l,ps in z.get('filled',{}).items()},geom(z['outline'])) for z in N['zones']]
logical_by_uid=dict(M['source_logical_nets']);logical_by_uid.update(L['logical_route_map'])
missing_nets={O[x['uuid']]['net'] for r in D['unconnected_items'] for x in r['items'] if x['uuid'] in O}

def allowed_ids(net,logical,terminals):
    if M['roles'][net]['kind']=='ordinary':return {uid for uid,o in O.items() if o['net']==net}
    return set(terminals)|{uid for uid,o in O.items() if o['kind']!='pad' and o['net']==net and logical_by_uid.get(uid)==logical}

def components(ids):
    parents={u:u for u in ids}
    def root(u):
        while parents[u]!=u:parents[u]=parents[parents[u]];u=parents[u]
        return u
    for a,b in itertools.combinations(ids,2):
        if any(C[a][l].distance(C[b][l])<=2e-6 for l in C[a].keys()&C[b].keys()):parents[root(b)]=root(a)
    return {u:root(u) for u in ids}

def obstacles(net,logical,terminals,layer):
    own=allowed_ids(net,logical,terminals);obs=[]
    def add(uid,key,kind,category,g,gap):
        obs.append({'uuid':uid,'object':key,'kind':kind,'category':category,'required_gap_mm':gap,'required_center_distance_mm':gap+HALF,'geometry':g})
    for uid,o in O.items():
        if uid not in own and layer in C[uid]:add(uid,o.get('key',uid),o['kind'],'other_branch_copper' if o['net']==net else 'foreign_copper',C[uid][layer],.127)
        if uid in DRILLS:
            if o.get('npth'):add(uid,o.get('key',uid),o['kind'],'npth',DRILLS[uid],.254)
            elif uid not in own:add(uid,o.get('key',uid),o['kind'],'foreign_drill',DRILLS[uid],.20)
    for z,filled,outline in Z:
        if z['rule']:
            if layer in z['layers'] and (z['forbid']['tracks'] or z['forbid']['copper']):add(z['uuid'],z.get('name',z['uuid']),'zone','keepout',outline,0)
        elif layer in filled and z['net']!=net:add(z['uuid'],z.get('name',z['uuid']),'zone','foreign_zone_copper',filled[layer],.127)
    add(None,'board_outline_and_npth','outline','edge_npth',OUTLINE.boundary,.254)
    return obs

def sites(o,layer):
    g=INSIDE[o['uuid']].get(layer,C[o['uuid']][layer]);x,y=o['xy'];x0,y0,x1,y1=g.bounds
    raw=[(x,y),(x0+.075,y),(x1-.075,y),(x,y0+.075),(x,y1-.075)]
    # For plated annuli, center is a hole. Cardinal outer-edge sites remain actual copper.
    result=[]
    for p in raw:
        q=Point(p)
        if g.covers(q) and q.distance(g.boundary)>=HALF+ERROR:result.append(tuple(round(v,6) for v in p))
    return list(dict.fromkeys(result))

def paths(a,b):
    yield [a,b]
    dx=b[0]-a[0];dy=b[1]-a[1];sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1
    for c in [(a[0],b[1]),(b[0],a[1]),(a[0]+sx*abs(dy),b[1]),(b[0],a[1]+sy*abs(dx)),(b[0]-sx*abs(dy),a[1]),(a[0],b[1]-sy*abs(dx))]:yield [a,c,b]
    for x in [(a[0]+b[0])/2,min(a[0],b[0])-.25,max(a[0],b[0])+.25]:yield [a,(x,a[1]),(x,b[1]),b]
    for y in [(a[1]+b[1])/2,min(a[1],b[1])-.25,max(a[1],b[1])+.25]:yield [a,(a[0],y),(b[0],y),b]

def witnesses(g,obs,count=5):
    rows=[]
    for ob in obs:
        d=g.distance(ob['geometry']);p,q=nearest_points(g,ob['geometry'])
        rows.append({k:v for k,v in ob.items() if k!='geometry'}|{'physical_gap_mm':d-HALF,'extra_clearance_mm':d-ob['required_center_distance_mm'],'centerline_witness_mm':list(p.coords[0]),'obstacle_witness_mm':list(q.coords[0])})
    return sorted(rows,key=lambda r:r['extra_clearance_mm'])[:count]

branches=[];skipped=[]
for net,role in M['roles'].items():
    if net not in missing_nets:continue
    if role['kind']=='ordinary':branches.append((net,net,role['terminals']))
    elif role['kind']=='protected_chain':
        for b in role['branches']:branches.append((net,b['logical_net'],[KEY[k]['uuid'] for k in b['terminals']]))

tasks=[]
for net,logical,terminals in branches:
    groups=components(allowed_ids(net,logical,terminals))
    for a,b in itertools.combinations(terminals,2):
        if groups[a]==groups[b]:continue
        layers=sorted(C[a].keys()&C[b].keys()&{'F.Cu','B.Cu'})
        if not layers:skipped.append({'logical_net':logical,'terminals':[O[a]['key'],O[b]['key']],'reason':'Native pads share no outer copper layer; no new vias allowed.'})
        for layer in layers:tasks.append((Point(O[a]['xy']).distance(Point(O[b]['xy'])),net,logical,terminals,a,b,layer))

results=[];proposals=[]
for _,net,logical,terminals,aid,bid,layer in sorted(tasks):
    a,b=O[aid],O[bid];obs=obstacles(net,logical,terminals,layer)
    # Bounded filtering: every tested route lies inside pad-center bounding box plus 1 mm.
    x0,y0,x1,y1=LineString([a['xy'],b['xy']]).bounds
    roi=box(x0-1.25,y0-1.25,x1+1.25,y1+1.25)
    local=[ob for ob in obs if ob['geometry'].distance(roi)<=ob['required_center_distance_mm']]
    ga=np.array([ob['geometry'] for ob in local],dtype=object);req=np.array([ob['required_center_distance_mm'] for ob in local])
    seen=set();tested=[]
    for pa,pb in itertools.product(sites(a,layer),sites(b,layer)):
        for pts0 in paths(pa,pb):
            pts=[]
            for p in pts0:
                p=tuple(round(v,6) for v in p)
                if not pts or pts[-1]!=p:pts.append(p)
            key=tuple(pts)
            if key in seen:continue
            seen.add(key);g=LineString(pts)
            # Some one-corner 45-degree candidates extend beyond the small local box.
            if not roi.covers(g):continue
            margin=float(np.min(shapely.distance(g,ga)-req));tested.append((margin,g.length,pts))
    passed=sorted([x for x in tested if x[0]>=ERROR],key=lambda x:x[1])
    best=passed[0] if passed else max(tested,key=lambda x:x[0]) if tested else None
    result={'net':net,'logical_net':logical,'layer':layer,'terminals':[a['key'],b['key']],'terminal_uuids':[aid,bid],'tested_paths':len(tested),'passed_paths':len(passed),'different_native_components_before':True}
    if best:
        margin,length,pts=best;g=LineString(pts);checks=witnesses(g,obs)
        result|={'best_points_mm':pts,'length_mm':length,'minimum_extra_clearance_mm':checks[0]['extra_clearance_mm'],'nearest_constraints':checks}
        if passed:
            assert checks[0]['extra_clearance_mm']>=ERROR and OUTLINE.covers(g)
            entry=[]
            for o,p in [(a,pts[0]),(b,pts[-1])]:
                pg=INSIDE[o['uuid']].get(layer,C[o['uuid']][layer]);q=Point(p)
                assert pg.covers(q) and q.distance(pg.boundary)>=HALF+ERROR
                entry.append({'pad':o['key'],'uuid':o['uuid'],'point_mm':p,'full_round_cap_inside_native_pad':True,'extra_containment_mm':q.distance(pg.boundary)-HALF})
            proposal=result|{'points_mm':pts,'width_mm':.127,'vias':[],'net_code':a['net_code'],'logical_role':M['roles'][net],'pad_entry':entry,'native_drc_performed':False,'acceptance_claimed':False}
            proposals.append(proposal)
            print('PASS',logical,a['key'],b['key'],layer,round(length,3),'clearance reserve',round(checks[0]['extra_clearance_mm'],6),pts,flush=True)
    results.append(result)
    print('screen',logical,a['key'],b['key'],layer,len(tested),len(passed),flush=True)

# Proposals are independent witnesses; disclose mutual conflicts for construction.
conflicts=[]
for ia,ib in itertools.combinations(range(len(proposals)),2):
    a,b=proposals[ia],proposals[ib]
    if a['layer']!=b['layer'] or a['logical_net']==b['logical_net']:continue
    gap=LineString(a['points_mm']).distance(LineString(b['points_mm']))-.127
    if gap<.127+ERROR:conflicts.append({'proposal_indices':[ia,ib],'physical_track_gap_mm':gap,'required_gap_mm':.127})
assert sha(BOARD)==EXPECTED and all(sha(pathlib.Path(v['path']))==v['sha256'] for v in IDENTITY.values())
receipt={'source_identity':IDENTITY,'board_sha256':EXPECTED,'scope':'Read-only bounded pad-to-pad simple closure screen of remaining ordinary and protected-chain nets. Direct, one-corner orthogonal/45-degree, and two-corner midpoint or 0.25mm exterior doglegs. No grid, solver, board mutation, or native DRC. Other branches on same physical net are foreign copper except this branch terminal pads. Each candidate independently checked against every native obstacle after bounded local screening.','rules_mm':{'width':.127,'foreign_copper':.127,'foreign_drill':.20,'edge_npth':.254,'native_polygon_error':ERROR},'candidate_count':len(results),'proposals':proposals,'proposal_mutual_conflicts':conflicts,'rejected_or_screened':results,'cross_layer_skipped':skipped,'source_unchanged':True,'elapsed_seconds':time.monotonic()-started}
(HERE/'candidate20-local-closures.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('COMPLETE',len(results),'candidates',len(proposals),'proposals',len(conflicts),'mutual conflicts','seconds',receipt['elapsed_seconds'],flush=True)
