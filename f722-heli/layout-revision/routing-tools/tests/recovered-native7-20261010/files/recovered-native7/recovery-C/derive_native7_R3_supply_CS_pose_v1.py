"""Source-derived orthogonal R3 poses; exact finite checks, no route search."""
import copy,json,math,signal,time
from native7_C12_shift_model_v1 import build,adapter,HERE
from shapely.geometry import Point,LineString,box
from shapely.affinity import translate
from shapely.ops import unary_union,polygonize,polylabel

start=time.monotonic();signal.alarm(40)
source=HERE/'native7-C12-RX-domain-v1.json';assert adapter.digest(source)=='3592a39dc2b8a5c4b79826a10446ebc0c5501ca75cb6cc4c09f724de21908fb8'
saved=json.loads(source.read_text());g,base,C,view,work,before,replaced,inventory=build();trial=saved['attempts'][0]
for r in trial['routes']:
    q=g.track(r['net'],r['layer'],r['points'],r['name'],r['width']);work.append((dict(q[0],role=r['role']),*q[1:]))
for r in trial['vias']:
    q=g.via(r['net'],r['xy'],r['name']);work.append((dict(q[0],role=r['role']),*q[1:]))
oldfp=next(f for f in g.N['footprints'] if f['ref']=='R3');oldpads=[q for q in work if q[0].get('ref')=='R3']
cs_leaves=[r for r in inventory['restored_original_CS_records']]
extra={r['uuid'] for r in cs_leaves}|{q[0]['uuid'] for q in oldpads}
work=[q for q in work if q[0]['uuid'] not in extra]
def graphic(fp,layer):return unary_union(list(polygonize([LineString([r['start'],r['end']]) for r in fp['graphics'] if r['layer']==layer and r['shape']=='Line'])))
oldcourt=graphic(oldfp,'F.Courtyard')
with C._width_state(g,.127):
    sf,_,_=g.rt.domain('+3V3_IMU','F.Cu',objects=work)
    cf,_,_=g.rt.domain('IMU_CS','F.Cu',objects=work)
s=g.rt.component(sf,g.one_pad('C12.1')['xy']);c=g.rt.component(cf,[24.259999,10.365]);assert s is not None and c is not None
out={'schema':'f722-native7-R3-source-derived-pose/v1','source':g.binding(),'source_receipt_sha256':adapter.digest(source),'script_sha256':adapter.digest(__file__),'selected':False,'routing_executed':False,'native_board_edited':False,'C12_pose':inventory['pose'],'R3_before':oldfp,'additional_original_CS_cuts':cs_leaves,'F_source_domains':{'supply':{'area_mm2':s.area,'bounds':list(s.bounds),'wkb_hex':s.wkb_hex},'CS':{'area_mm2':c.area,'bounds':list(c.bounds),'wkb_hex':c.wkb_hex}},'orientation_domains':[],'candidate_checks':[],'passed_candidates':[],'main_feed_candidate_width_mm':.18,'primary_feed_current_and_loop_qualification_pending':True}
def rotation(p,angle):
    t=math.radians(angle-90);x,y=p[0]-25.7,p[1]-9.5
    return [x*math.cos(t)+y*math.sin(t),-x*math.sin(t)+y*math.cos(t)]
def shifted(p,angle,center):
    x,y=rotation(p,angle);return [round(x+center[0],6),round(y+center[1],6)]
def transform_pad(o,angle,center):
    o=copy.deepcopy(o);o['xy']=shifted(o['xy'],angle,center);o['angle']=float(angle)
    def polys(items):return [dict(p,outer=[shifted(v,angle,center) for v in p['outer']],holes=[[shifted(v,angle,center) for v in h] for h in p.get('holes',[])]) for p in items]
    for key in ('copper','inside','mask'):
        if key in o:o[key]={layer:(dict(item,polygons=polys(item['polygons'])) if isinstance(item,dict) else polys(item)) for layer,item in o[key].items()}
    return g.entry(o)
def transform_fp(angle,center):
    fp=copy.deepcopy(oldfp);fp['xy']=center;fp['angle']=float(angle)
    for r in fp['graphics']:r['start']=shifted(r['start'],angle,center);r['end']=shifted(r['end'],angle,center)
    return fp
candidates=[]
for angle in (0,90,180,270):
    offsets={q[0]['key']:rotation(q[0]['xy'],angle) for q in oldpads}
    a,b=offsets['R3.1'],offsets['R3.2']
    center_domain=translate(s,xoff=-a[0],yoff=-a[1]).intersection(translate(c,xoff=-b[0],yoff=-b[1]))
    # The exact center intersection is recorded before the finite body/courtyard filters.
    # Erosion is a conservative pad-envelope filter; final candidate checks use actual rounded pads.
    radii=[]
    for q in oldpads:
        p=q[0]['xy'];bounds=q[1]['F.Cu'].bounds
        radii.append(max(math.dist(p,z) for z in ((bounds[0],bounds[1]),(bounds[0],bounds[3]),(bounds[2],bounds[1]),(bounds[2],bounds[3])))-.0635)
    safe=translate(s.buffer(-radii[0]),xoff=-a[0],yoff=-a[1]).intersection(translate(c.buffer(-radii[1]),xoff=-b[0],yoff=-b[1]))
    proto=transform_fp(angle,[25.7,9.5]);courtyard=graphic(proto,'F.Courtyard');x0,y0,x1,y1=courtyard.bounds;hw=(x1-x0)/2;hh=(y1-y0)/2
    blocked=[]
    for fp in g.N['footprints']:
        if fp['ref']=='R3' or fp['side']!='F.Cu':continue
        shape=graphic(fp,'F.Courtyard')
        if shape.is_empty:continue
        u0,v0,u1,v1=shape.bounds;blocked.append(box(u0-hw,v0-hh,u1+hw,v1+hh))
    allowed=safe.difference(unary_union(blocked)).intersection(box(20,6,32,18))
    row={'angle':angle,'raw_two_pad_center_intersection_mm2':center_domain.area,'raw_bounds':None if center_domain.is_empty else list(center_domain.bounds),'conservative_actual_pad_envelope_filter_mm2':safe.area,'mechanical_interior_centers_mm2':allowed.area,'strategy_window':[20,6,32,18],'courtyard_bounds_filter_conservative_for_nonrectangular_shapes':True}
    out['orientation_domains'].append(row)
    for p in g.rt.parts(allowed):
        if p.area<1e-9:continue
        q=polylabel(p,tolerance=.00001);center=[round(q.x,6),round(q.y,6)]
        candidates.append((math.dist(center,[25.7,9.5]),angle,center,p.area))
for distance,angle,center,area in sorted(candidates)[:8]:
    fp=transform_fp(angle,center);pads=[transform_pad(q[0],angle,center) for q in oldpads];court=graphic(fp,'F.Courtyard');body=graphic(fp,'F.Fab');mechanics=[]
    for peer in g.N['footprints']:
        if peer['ref']=='R3' or peer['side']!='F.Cu':continue
        pc=graphic(peer,'F.Courtyard');pb=graphic(peer,'F.Fab')
        if not pc.is_empty:mechanics.append({'ref':peer['ref'],'gap_mm':court.distance(pc),'overlap_mm2':court.intersection(pc).area,'body_overlap_mm2':0 if pb.is_empty else body.intersection(pb).area})
    finite=[]
    for o,cu,masks,_ in pads:
        p=cu['F.Cu'];m=next(iter(masks.values()));others=work+[z for z in pads if z[0]['uuid']!=o['uuid']]
        copper=sorted([{'uuid':z['uuid'],'key':z.get('key'),'net':z['net'],'gap_mm':p.distance(cu['F.Cu'])} for z,cu,_,_ in others if z['net']!=o['net'] and 'F.Cu' in cu],key=lambda r:r['gap_mm'])[:4]
        drills=sorted([{'uuid':z['uuid'],'gap_mm':m.distance(d)} for z,_,_,d in others if d is not None],key=lambda r:r['gap_mm'])[:4]
        overlaps=[z['uuid'] for z,_,ma,_ in others for face,shape in ma.items() if face in ('F.Cu','F.Mask') and m.intersection(shape).area>0]
        passed=all(r['gap_mm']>=.127+g.s.ERROR for r in copper) and all(r['gap_mm']>=.2+g.s.ERROR for r in drills) and not overlaps
        finite.append({'key':o['key'],'xy':o['xy'],'passed':passed,'nearest_foreign_copper':copper,'nearest_drill_to_mask':drills,'mask_overlaps':overlaps})
    passed=all(z['passed'] for z in finite) and all(z['overlap_mm2']==z['body_overlap_mm2']==0 for z in mechanics)
    row={'pose':[*center,angle,'F.Cu'],'movement_mm':distance,'center_component_area_mm2':area,'passed':passed,'pad_finite':finite,'nearest_courtyards':sorted(mechanics,key=lambda x:x['gap_mm'])[:5]};out['candidate_checks'].append(row)
    if passed:out['passed_candidates'].append(dict(row,candidate_footprint=fp,candidate_pad_records=[z[0] for z in pads]))
    if len(out['passed_candidates'])==2:break
out['seconds']=time.monotonic()-start;out['complete_two_pad_routes_pending']=True
path=HERE/'native7-R3-source-derived-pose-v1.json';path.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');signal.alarm(0)
print(json.dumps({'seconds':out['seconds'],'receipt_sha256':adapter.digest(path),'orientation_domains':out['orientation_domains'],'passed_poses':[z['pose'] for z in out['passed_candidates']],'tested_centers':len(out['candidate_checks'])},indent=2))
