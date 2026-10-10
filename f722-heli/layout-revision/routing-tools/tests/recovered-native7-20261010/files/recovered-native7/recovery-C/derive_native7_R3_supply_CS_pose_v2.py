"""Source-derived orthogonal R3 poses; exact finite checks, no route search."""
import copy,json,math,signal,time
from native7_C12_shift_model_v1 import build,adapter,HERE
from shapely.geometry import Point,LineString,box
from shapely.affinity import translate
from shapely.ops import unary_union,polygonize,polylabel

start=time.monotonic();signal.alarm(55)
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
def reachable(graph,seeds,new_cell=None):
    seen=set(seeds);stack=list(seeds)
    while stack:
        for nxt,cost,edge in graph['adj'][stack.pop()]:
            allowed=cost==0 or (new_cell is not None and edge['kind']=='new_via_region' and edge['geometry'].intersection(new_cell).area>1e-9)
            if allowed and nxt not in seen:seen.add(nxt);stack.append(nxt)
    return seen
source_data={};graphs={};regions={}
for net,key in [('+3V3_IMU','C12.1'),('IMU_CS','U2.12')]:
    groups=C._physical_groups(g,work,net);group=next(q for q in groups if key in q['keys'])
    with C._width_state(g,.127):graph=g.gg.build(net,work,layers=C.ORDINARY)
    graphs[net]=graph;seeds=set();anchors=[]
    for o,cu,_,_ in work:
        if o['uuid'] not in group['ids']:continue
        for xy in ([o['xy']] if 'xy' in o else [o['start'],o['end']]):
            nodes=g.gg.terminals(graph,xy,tuple(cu));seeds.update(nodes)
            if nodes:anchors.append({'uuid':o['uuid'],'key':o.get('key'),'xy':xy,'layers':list(cu),'nodes':sorted(nodes)})
    reached=reachable(graph,seeds)
    source_data[net]={'actual_source_component':group,'anchors':anchors,'existing_transition_reached_nodes':sorted(reached),'all_existing_plated_contacts':[q[0] for q in work if q[0]['uuid'] in group['ids'] and (q[0]['kind']=='via' or q[0].get('plated'))]}
    regions[net]={layer:unary_union([graph['nodes'][i][1] for i in reached if graph['nodes'][i][0]==layer]) for layer in ('F.Cu','B.Cu')}
    if net=='+3V3_IMU':supply_seeds=seeds
# Explicit additional source-transition candidate only, not an existing copper tie.
with C._width_state(g,.18):free,_,vobs=g.rt.domain('+3V3_IMU','F.Cu',objects=work)
supply_F=g.rt.component(free,g.one_pad('C12.1')['xy']);legal=g.s.OUTLINE.buffer(-.479-g.s.ERROR-.0001).difference(g.rt.expanded(vobs))
new_cell=supply_F.intersection(legal).intersection(box(25.04,15.41,25.32,15.76))
source_data['explicit_new_supply_transition']={'area_mm2':new_cell.area,'bounds':None if new_cell.is_empty else list(new_cell.bounds),'wkb_hex':new_cell.wkb_hex,'planning_only':True,'source_leg_width_mm':.18,'primary_U2_C12_C11_paths_must_remain_complete_independently':True}
new_reached=reachable(graphs['+3V3_IMU'],supply_seeds,new_cell)
new_regions={layer:unary_union([graphs['+3V3_IMU']['nodes'][i][1] for i in new_reached if graphs['+3V3_IMU']['nodes'][i][0]==layer]) for layer in ('F.Cu','B.Cu')}
cases=[]
for mode,supply in [('existing_transitions_only',regions['+3V3_IMU']),('one_declared_new_supply_cell',new_regions)]:
    for face in ('F.Cu','B.Cu'):cases.append((mode,face,supply[face],regions['IMU_CS'][face]))
out={'schema':'f722-native7-R3-source-derived-pose/v2','source':g.binding(),'source_receipt_sha256':adapter.digest(source),'script_sha256':adapter.digest(__file__),'selected':False,'routing_executed':False,'native_board_edited':False,'C12_pose':inventory['pose'],'R3_before':oldfp,'additional_original_CS_cuts':cs_leaves,'ordinary_source_reachability':source_data,'orientation_domains':[],'candidate_checks':[],'passed_candidates':[],'main_feed_candidate_width_mm':.18,'primary_feed_current_and_loop_qualification_pending':True}
def rotation(p,angle,face='F.Cu'):
    t=math.radians(angle-90);x,y=p[0]-25.7,p[1]-9.5
    if face=='B.Cu':x=-x
    return [x*math.cos(t)+y*math.sin(t),-x*math.sin(t)+y*math.cos(t)]
def shifted(p,angle,center,face):
    x,y=rotation(p,angle,face);return [round(x+center[0],6),round(y+center[1],6)]
def transform_pad(o,angle,center,face):
    o=copy.deepcopy(o);o['xy']=shifted(o['xy'],angle,center,face);o['angle']=float(angle)
    def polys(items):return [dict(p,outer=[shifted(v,angle,center,face) for v in p['outer']],holes=[[shifted(v,angle,center,face) for v in h] for h in p.get('holes',[])]) for p in items]
    for key in ('copper','inside','mask'):
        if key in o:o[key]={layer:(dict(item,polygons=polys(item['polygons'])) if isinstance(item,dict) else polys(item)) for layer,item in o[key].items()}
    if face=='B.Cu':
        mapping=lambda layer:layer.replace('F.','B.')
        for key in ('copper','inside','mask','shape_by_layer'):o[key]={mapping(layer):value for layer,value in o[key].items()}
        o['all_layers']=[mapping(layer) for layer in o['all_layers']]
    return g.entry(o)
def transform_fp(angle,center,face):
    fp=copy.deepcopy(oldfp);fp['xy']=center;fp['angle']=float(angle);fp['side']=face
    for r in fp['graphics']:r['start']=shifted(r['start'],angle,center,face);r['end']=shifted(r['end'],angle,center,face)
    if face=='B.Cu':
        for r in fp['graphics']:r['layer']=r['layer'].replace('F.','B.')
    return fp
candidates=[]
for mode,face,s,c in cases:
    for angle in (0,90,180,270):
        offsets={q[0]['key']:rotation(q[0]['xy'],angle,face) for q in oldpads}
        a,b=offsets['R3.1'],offsets['R3.2']
        center_domain=translate(s,xoff=-a[0],yoff=-a[1]).intersection(translate(c,xoff=-b[0],yoff=-b[1]))
        # The exact center intersection is recorded before the finite body/courtyard filters.
        # Erosion is a conservative pad-envelope filter; final candidate checks use actual rounded pads.
        radii=[]
        for q in oldpads:
            p=q[0]['xy'];bounds=q[1]['F.Cu'].bounds
            radii.append(max(math.dist(p,z) for z in ((bounds[0],bounds[1]),(bounds[0],bounds[3]),(bounds[2],bounds[1]),(bounds[2],bounds[3])))-.0635)
        safe=translate(s.buffer(-radii[0]),xoff=-a[0],yoff=-a[1]).intersection(translate(c.buffer(-radii[1]),xoff=-b[0],yoff=-b[1]))
        proto=transform_fp(angle,[25.7,9.5],face);courtyard=graphic(proto,face.replace('.Cu','.Courtyard'));x0,y0,x1,y1=courtyard.bounds;hw=(x1-x0)/2;hh=(y1-y0)/2
        blocked=[]
        for fp in g.N['footprints']:
            if fp['ref']=='R3' or fp['side']!=face:continue
            shape=graphic(fp,face.replace('.Cu','.Courtyard'))
            if shape.is_empty:continue
            u0,v0,u1,v1=shape.bounds;blocked.append(box(u0-hw,v0-hh,u1+hw,v1+hh))
        allowed=safe.difference(unary_union(blocked)).intersection(box(20,6,32,18))
        row={'source_case':mode,'face':face,'angle':angle,'raw_two_pad_center_intersection_mm2':center_domain.area,'raw_bounds':None if center_domain.is_empty else list(center_domain.bounds),'conservative_actual_pad_envelope_filter_mm2':safe.area,'mechanical_interior_centers_mm2':allowed.area,'strategy_window':[20,6,32,18],'courtyard_bounds_filter_conservative_for_nonrectangular_shapes':True}
        out['orientation_domains'].append(row)
        for p in g.rt.parts(allowed):
            if p.area<1e-9:continue
            q=polylabel(p,tolerance=.00001);center=[round(q.x,6),round(q.y,6)]
            candidates.append((math.dist(center,[25.7,9.5]),angle,center,p.area,mode,face))
for distance,angle,center,area,mode,face in sorted(candidates)[:8]:
    fp=transform_fp(angle,center,face);pads=[transform_pad(q[0],angle,center,face) for q in oldpads];court=graphic(fp,face.replace('.Cu','.Courtyard'));body=graphic(fp,face.replace('.Cu','.Fab'));mechanics=[]
    for peer in g.N['footprints']:
        if peer['ref']=='R3' or peer['side']!=face:continue
        pc=graphic(peer,face.replace('.Cu','.Courtyard'));pb=graphic(peer,face.replace('.Cu','.Fab'))
        if not pc.is_empty:mechanics.append({'ref':peer['ref'],'gap_mm':court.distance(pc),'overlap_mm2':court.intersection(pc).area,'body_overlap_mm2':0 if pb.is_empty else body.intersection(pb).area})
    finite=[]
    for o,cu,masks,_ in pads:
        p=cu[face];m=next(iter(masks.values()));others=work+[z for z in pads if z[0]['uuid']!=o['uuid']]
        copper=sorted([{'uuid':z['uuid'],'key':z.get('key'),'net':z['net'],'gap_mm':p.distance(cu[face])} for z,cu,_,_ in others if z['net']!=o['net'] and face in cu],key=lambda r:r['gap_mm'])[:4]
        drills=sorted([{'uuid':z['uuid'],'gap_mm':m.distance(d)} for z,_,_,d in others if d is not None],key=lambda r:r['gap_mm'])[:4]
        overlaps=[z['uuid'] for z,_,ma,_ in others for mlayer,shape in ma.items() if mlayer in (face,face.replace('.Cu','.Mask')) and m.intersection(shape).area>0]
        passed=all(r['gap_mm']>=.127+g.s.ERROR for r in copper) and all(r['gap_mm']>=.2+g.s.ERROR for r in drills) and not overlaps
        finite.append({'key':o['key'],'xy':o['xy'],'passed':passed,'nearest_foreign_copper':copper,'nearest_drill_to_mask':drills,'mask_overlaps':overlaps})
    passed=all(z['passed'] for z in finite) and all(z['overlap_mm2']==z['body_overlap_mm2']==0 for z in mechanics)
    row={'pose':[*center,angle,face],'source_case':mode,'flip_left_right':False,'movement_mm':distance,'center_component_area_mm2':area,'passed':passed,'pad_finite':finite,'nearest_courtyards':sorted(mechanics,key=lambda x:x['gap_mm'])[:5]};out['candidate_checks'].append(row)
    if passed:out['passed_candidates'].append(dict(row,candidate_footprint=fp,candidate_pad_records=[z[0] for z in pads]))
    if len(out['passed_candidates'])==2:break
out['seconds']=time.monotonic()-start;out['complete_two_pad_routes_pending']=True
path=HERE/'native7-R3-source-derived-pose-v2.json';path.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');signal.alarm(0)
print(json.dumps({'seconds':out['seconds'],'receipt_sha256':adapter.digest(path),'orientation_domains':out['orientation_domains'],'passed_poses':[z['pose'] for z in out['passed_candidates']],'tested_centers':len(out['candidate_checks'])},indent=2))
