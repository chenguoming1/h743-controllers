"""Saved-domain attribution and bounded local domain widths; no routing or graph search."""
import json,math,signal,time
from collections import defaultdict
from native7_C12_shift_model_v1 import build,adapter,HERE
from shapely import from_wkb
from shapely.geometry import Point
from shapely.ops import unary_union,nearest_points,polylabel

start=time.monotonic();signal.alarm(25)
src=HERE/'native7-C12-RX-domain-v1.json';assert adapter.digest(src)=='3592a39dc2b8a5c4b79826a10446ebc0c5501ca75cb6cc4c09f724de21908fb8'
saved=json.loads(src.read_text());g,base,C,view,initial,before,replaced,inventory=build()
out={'schema':'f722-native7-C12-support-domain-audit/v1','source':g.binding(),'source_receipt_sha256':adapter.digest(src),'script_sha256':adapter.digest(__file__),'routing_started':False,'graph_built':False,'selected':False,'support_separators':[]}
trial=saved['attempts'][0];work=list(initial)
for r in trial['routes']:
    q=g.track(r['net'],r['layer'],r['points'],r['name'],r['width']);work.append((dict(q[0],role=r['role']),*q[1:]))
for r in trial['vias']:
    q=g.via(r['net'],r['xy'],r['name']);work.append((dict(q[0],role=r['role']),*q[1:]))
by={q[0]['uuid']:q[0] for q in work}
def summary(p):return {'area_mm2':p.area,'bounds':None if p.is_empty else list(p.bounds)}
for item in trial['four_support_paths']:
    if item['plan']['connected']:continue
    job=item['job'];regions={}
    for side in ('source','target'):
        for layer in C.ORDINARY:
            rows=[r for r in item['plan']['actual_frontier'] if r['side']==side and r['layer']==layer]
            if rows:regions[side,layer]=unary_union([from_wkb(bytes.fromhex(r['domain_wkb_hex'])) for r in rows])
    a,b=nearest_points(regions['source','F.Cu'],regions['target','F.Cu']);points=[[a.x,a.y],[b.x,b.y]]
    finite=g.check_track(job['net'],'F.Cu',points,width=job['width'],objects=work)
    pocket=regions['target','F.Cu'];row={'job':job,'F_frontier_mm':a.distance(b),'F_frontier_points':points,'exact_frontier_checks':finite[:12],'target_F_domain':summary(pocket),'barrel_obstacles':[]}
    with C._width_state(g,job['width']):
        old=g.s.OBJECTS;g.s.OBJECTS=work
        try:_,obs,_=g.s.obstacles(job['net'],'F.Cu')
        finally:g.s.OBJECTS=old
    covers=defaultdict(list);rules=defaultdict(list)
    for o in obs:
        if o['category']=='edge_npth_copper':continue
        radius=(o['required_center_distance_mm']+g.s.ERROR+.0001)/math.cos(math.pi/128)
        if pocket.distance(o['geometry'])>radius:continue
        z=o['geometry'].buffer(radius,quad_segs=32).intersection(pocket)
        if z.is_empty:continue
        covers[o['uuid']].append(z);rules[o['uuid']].append({k:v for k,v in o.items() if k!='geometry'})
    covers={uid:unary_union(parts) for uid,parts in covers.items()};allc=unary_union(list(covers.values()));row['target_barrel_area_mm2']=pocket.difference(allc).area
    for uid in sorted(covers,key=lambda x:covers[x].area,reverse=True)[:8]:
        exposed=pocket.difference(unary_union([p for k,p in covers.items() if k!=uid]));o=by.get(uid,{})
        row['barrel_obstacles'].append({'uuid':uid,'key':o.get('key'),'net':o.get('net'),'kind':o.get('kind'),'width':o.get('width'),'xy':o.get('xy'),'start':o.get('start'),'end':o.get('end'),'coverage_mm2':covers[uid].area,'single_exclusion_exposes_mm2':exposed.area,'rules':rules[uid]})
    out['support_separators'].append(row)
# Evaluate the actual primary feed at explicitly distinct engineering widths.
out['primary_feed_width_domains']=[]
for width in (.20,.18,.16):
    with C._width_state(g,width):free,_,vobs=g.rt.domain('+3V3_IMU','F.Cu',objects=work)
    a=g.rt.component(free,g.one_pad('C11.1')['xy']);b=g.rt.component(free,g.one_pad('C12.1')['xy']);legal=g.s.OUTLINE.buffer(-.479-g.s.ERROR-.0001).difference(g.rt.expanded(vobs))
    out['primary_feed_width_domains'].append({'width_mm':width,'above_manufacturer_reviewed_6mil':width>.1524,'F_connected':bool(a is not None and a.covers(Point(g.one_pad('C12.1')['xy']))),'C12_source_region':None if b is None else summary(b),'C12_legal_barrel_domain':None if b is None else summary(b.intersection(legal)),'no_actual_load_or_loop_qualification':True})
# All source-connected barrel cells before the failed long northern F approach.
rx=next(j for j in C._jobs(g) if j['name']=='RX_down');alias,peers=C._view(view,rx,initial)
with C._width_state(g,.127):free,_,vobs=g.rt.domain(alias,'F.Cu',objects=peers)
source=g.rt.component(free,rx['a']);legal=g.s.OUTLINE.buffer(-.479-g.s.ERROR-.0001).difference(g.rt.expanded(vobs));eligible=source.intersection(legal)
out['unrestricted_RX_source_connected_barrel_domain']=summary(eligible)
cells=[]
for part in g.rt.parts(eligible):
    if part.area<1e-12:continue
    p=polylabel(part,tolerance=.00001);near=nearest_points(Point(rx['a']),part)[1]
    cells.append({'area_mm2':part.area,'bounds':list(part.bounds),'representative_xy':[p.x,p.y],'nearest_source_distance_mm':Point(rx['a']).distance(part),'nearest_source_xy':[near.x,near.y],'wkb_hex':part.wkb_hex})
out['nearest_unrestricted_RX_cells']=sorted(cells,key=lambda z:z['nearest_source_distance_mm'])[:8]
out['scope_limit']='All RX cells still assume six support leaves pending. Single obstacle exclusions are diagnostic and do not prove a complete replacement. No support width has been adopted.'
out['seconds']=time.monotonic()-start;path=HERE/'native7-C12-support-domain-audit-v1.json';path.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');signal.alarm(0)
print(json.dumps({'seconds':out['seconds'],'receipt_sha256':adapter.digest(path),'primary_feed_width_domains':out['primary_feed_width_domains'],'nearest_RX_cells':[{k:v for k,v in r.items() if k!='wkb_hex'} for r in out['nearest_unrestricted_RX_cells']]},indent=2))
