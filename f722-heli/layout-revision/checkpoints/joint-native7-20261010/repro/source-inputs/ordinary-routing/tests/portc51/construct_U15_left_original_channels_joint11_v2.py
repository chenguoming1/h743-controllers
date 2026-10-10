"""One complete translated U15 cell, dedicated ground and full RPM donor span."""
import copy,hashlib,json,math,sys,time
from pathlib import Path
from shapely import unary_union
from shapely.affinity import translate,rotate
from shapely.geometry import Point,LineString,box
from shapely.ops import polygonize,nearest_points
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'native13-access'))
import composite_native11_divider_green_mid as g
import route_native11 as rt
s=g.s;START=time.monotonic();DEADLINE=START+25
OUT=H/'U15-left-original-channels-joint11-v2.json'
mapping={'U15.10':'PORT_C_RX_EXT','U15.9':'PORT_C_TX_EXT'}
RPM={'92a0cad1-6948-4fd2-9a91-283ea01629b8','173f3c05-4fd2-4cd8-a550-8415c9d91d2b','26ed2907-d8d1-4e4d-b636-b22c8fb99e6c'}
GND={'0ecf399a-607b-493d-8db1-cd0fb923de8b'}
RETAINED_GROUND_VIA='97282ff5-d6b5-415f-a3c4-0390df70f0ea'
TX={o['uuid']for o in g.N['objects']if o['net']=='PORT_C_TX_EXT'and o['kind']!='pad'}
cuts=RPM|GND|TX;assert len(TX)==16
def moved(o):
    q=copy.deepcopy(o)
    def pt(v):return [round(v[0]-.5,6),v[1]]
    def pp(rows):return [dict(outer=[pt(v)for v in p['outer']],holes=[[pt(v)for v in h]for h in p.get('holes',[])])for p in rows]
    q['xy']=pt(q['xy']);q['net']=mapping.get(q['key'],q['net'])
    for k in ['copper','inside']:q[k]={l:pp(v)for l,v in o[k].items()}
    for l,m in q['mask'].items():m['polygons']=pp(o['mask'][l]['polygons'])
    return q
pads=[moved(o)for o in g.N['objects']if o.get('ref')=='U15'];pd={o['key']:o for o in pads}
BASE=[q for q in g.BASE if q[0]['uuid']not in cuts and q[0].get('ref')!='U15']+[g.entry(p)for p in pads]
CLAIM=dict(name='conditional-MID-flash-barrel',net='FLASH_MID_RESERVED',xy=[24.709459,15.296041],diameter_mm=.45,drill_mm=.20)
BASE.append(g.via(CLAIM['net'],CLAIM['xy'],CLAIM['name']))
rpm=dict(name='U15-left-restored-RPM-LV',net='RPM_LV',layer='F.Cu',width=.127,
         points=[[22.7493,17.08106],[22.5,17.33036],[22.5,18.6],[21.05711,20.3335]])
ground=dict(name='U15-left-original-ground-via-join',net='GND',layer='F.Cu',width=.25,points=[[24.5,18.4175],[24.6,18.95],[25.287,19.1104]])
branches=[dict(name='RX-NC10-up',net='PORT_C_RX_EXT',role='upstream',clamp='U15.1',layer='F.Cu',width=.127,points=[[23.5,18.22],[23.5,17.5825],[23.5,17.10]]),
          dict(name='RX-down',net='PORT_C_RX_EXT',role='downstream',clamp='U15.1',layer='F.Cu',width=.127,points=[[23.5,18.6],[23.35,18.95]]),
          dict(name='TX-NC9-up',net='PORT_C_TX_EXT',role='upstream',clamp='U15.2',layer='F.Cu',width=.127,points=[[24,18.22],[24,17.5825],[24,17.30]]),
          dict(name='TX-down',net='PORT_C_TX_EXT',role='downstream',clamp='U15.2',layer='F.Cu',width=.127,points=[[24,18.6],[23.85,18.95]])]
routes=[rpm,ground]+branches;entries=[g.track(r['net'],r['layer'],r['points'],r['name'],r['width'])for r in routes]

out=dict(schema='f722-U15-left-original-channels-joint11/v2',source=g.binding(),hypothesis_only=True,native_candidate=False,
         additional_removed_native_records=[g.by[u]for u in sorted(cuts-set(g.REMOVED_NATIVE_IDS))],
         footprint_transform=dict(ref='U15',before_xy=[25,18],after_xy=[24.5,18],angle=90,side='F.Cu'),
         changed_pad_records=pads,selected_routes=routes,selected_vias=[],pad_checks=[],checks=[],actual_IO_cut_checks=[],
         conditional_unselected_via_claims=[CLAIM],R57_all_native_feed_records_retained=True,ground_scope='Retain the exact original U15 GND via and replace its complete .25 F lead. Record all actual parallel contacts; no other narrow series lead is substituted.',
         old_RPM_span_length_mm=sum(math.dist(g.by[u]['start'],g.by[u]['end'])for u in RPM),
         old_U15_ground_length_mm=math.dist(g.by['0ecf399a-607b-493d-8db1-cd0fb923de8b']['start'],g.by['0ecf399a-607b-493d-8db1-cd0fb923de8b']['end']))
out['old_ground_physical_contacts']=[]
for uid in sorted(GND):
    old=g.by[uid]
    for o in g.N['objects']:
        if o['uuid'] in GND or o['net']!='GND':continue
        for layer in set(old['copper']) & set(o['copper']):
            a=s.geom(old['copper'][layer]);b=s.geom(o['copper'][layer])
            if a.intersects(b):out['old_ground_physical_contacts'].append(dict(removed_uuid=uid,retained_uuid=o['uuid'],key=o.get('key'),kind=o['kind'],layer=layer,overlap_mm2=a.intersection(b).area))
out['ground_leaf_exclusive_to_U15']=all(q['key'] in ['U15.3','U15.8'] or q['retained_uuid']==RETAINED_GROUND_VIA or q['kind']=='zone' for q in out['old_ground_physical_contacts'])
out['transformed_ground_pad_physical_overlap_mm2']=s.geom(pd['U15.3']['copper']['F.Cu']).intersection(s.geom(pd['U15.8']['copper']['F.Cu'])).area
out['new_RPM_span_length_mm']=LineString(rpm['points']).length
out['RPM_retained_physical_contacts']=[]
for o,c,m,d in BASE:
    if o['net']!='RPM_LV' or 'F.Cu'not in c:continue
    hits=[u for u in RPM if s.geom(g.by[u]['copper']['F.Cu']).intersects(c['F.Cu'])]
    if hits:out['RPM_retained_physical_contacts'].append(dict(retained_uuid=o['uuid'],key=o.get('key'),removed_contacts=hits,restored_overlap_mm2=entries[0][1]['F.Cu'].intersection(c['F.Cu']).area))
out['RPM_all_retained_contacts_restored']=all(q['restored_overlap_mm2']>0 for q in out['RPM_retained_physical_contacts'])
out['complete_protected_branches']=False
out['complete_local_cell']=False

def save():
    out['seconds']=time.monotonic()-START;out['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();OUT.write_text(json.dumps(out,indent=2)+'\n')
def check(r,objects):
    s.OBJECTS=objects;s.HALF=r['width']/2;cc=s.check(LineString(r['points']),s.obstacles(r['net'],r['layer'])[0],True)
    return dict(name=r['name'],passed=all(q['pass_with_polygon_error']for q in cc),nearest=cc[:5],failures=[q for q in cc if not q['pass_with_polygon_error']])
for p in pads:
    cu=s.geom(p['copper']['F.Cu']);ma=s.geom(p['mask']['F.Mask']['polygons']);cc=[]
    for o,c,m,d in BASE+entries:
        if o['uuid']==p['uuid']:continue
        if o['net']!=p['net']and'F.Cu'in c:cc.append(dict(uuid=o['uuid'],key=o.get('key'),net=o['net'],category='foreign_copper',extra_mm=cu.distance(c['F.Cu'])-.127))
        if d is not None:
            cc.append(dict(uuid=o['uuid'],net=o['net'],category='all_drill_mask',extra_mm=ma.distance(d)-.20))
            if o.get('npth'):cc.append(dict(uuid=o['uuid'],category='npth',extra_mm=cu.distance(d)-.254))
            elif o['net']!=p['net']:cc.append(dict(uuid=o['uuid'],net=o['net'],category='foreign_drill_to_copper',extra_mm=cu.distance(d)-.20))
    cc.sort(key=lambda q:q['extra_mm']);bad=[q for q in cc if q['extra_mm']<s.ERROR];out['pad_checks'].append(dict(key=p['key'],passed=not bad,nearest=cc[:4],failures=bad))
def shape(f,layer):
    lines=[];pp=[]
    for q in f['graphics']:
        if q['layer']!=layer:continue
        typ=q['shape']
        if typ=='Line':lines.append(LineString([q['start'],q['end']]))
        elif typ=='Rect':pp.append(box(min(q['start'][0],q['end'][0]),min(q['start'][1],q['end'][1]),max(q['start'][0],q['end'][0]),max(q['start'][1],q['end'][1])))
        elif typ=='Polygon':pp.append(s.geom(q['polygons']))
        elif typ=='Circle':pp.append(Point(q['center']).buffer(math.dist(q['center'],q['end']),quad_segs=96))
        else:raise ValueError(typ)
    return unary_union(pp+list(polygonize(unary_union(lines))))
F={f['ref']:f for f in g.N['footprints']};court=translate(shape(F['U15'],'F.Courtyard'),xoff=-.5)
reserve=unary_union([translate(shape(F['U15'],'F.Fab'),xoff=-.5).buffer(.15)]+[s.geom(p['copper']['F.Cu']).buffer(.10)for p in pads])
out['mechanical_failures']=[]
poses=g.binding().get('declared_poses',{})
for ref,f in F.items():
    if ref=='U15' or f['side']!='F.Cu':continue
    c=shape(f,'F.Courtyard');fab=shape(f,'F.Fab')
    if ref in poses:
        xy,ang=poses[ref];c=translate(rotate(c,-(ang-f['angle']),origin=f['xy']),xy[0]-f['xy'][0],xy[1]-f['xy'][1]);fab=translate(rotate(fab,-(ang-f['angle']),origin=f['xy']),xy[0]-f['xy'][0],xy[1]-f['xy'][1])
    lands=unary_union([cu['F.Cu']for o,cu,m,d in BASE if o.get('ref')==ref and'F.Cu'in cu]);rs=unary_union([fab.buffer(.15),lands.buffer(.10)])
    ca=court.intersection(c).area;ra=reserve.intersection(rs).area
    if max(ca,ra)>1e-10:out['mechanical_failures'].append(dict(ref=ref,courtyard_overlap_mm2=ca,reserve_overlap_mm2=ra))
out['outline_covers_reserve']=s.OUTLINE.covers(reserve)
for i,r in enumerate(routes):out['checks'].append(check(r,BASE+[q for j,q in enumerate(entries)if i!=j]))
for key,inds,nc in [('U15.1',[2,3],'U15.10'),('U15.2',[4,5],'U15.9')]:
    cut=s.geom(pd[key]['inside']['F.Cu']);up=unary_union([entries[inds[0]][1]['F.Cu'],s.geom(pd[nc]['copper']['F.Cu'])]).difference(cut);dn=entries[inds[1]][1]['F.Cu'].difference(cut);gap=up.distance(dn)
    out['actual_IO_cut_checks'].append(dict(actual_pad=key,gap_mm=gap,passed=gap>=.127+s.ERROR,finite_entries_mm2=[entries[i][1]['F.Cu'].intersection(cut).area for i in inds]))
out['finite_cell_preflight']=all(q['passed']for q in out['checks']+out['pad_checks']+out['actual_IO_cut_checks'])and not out['mechanical_failures']and out['outline_covers_reserve']and out['ground_leaf_exclusive_to_U15']and out['RPM_all_retained_contacts_restored']
save();print('CELL_PREFLIGHT',out['finite_cell_preflight'],flush=True)
for q in out['pad_checks']+out['checks']:
    if not q['passed']:print('FAIL',q.get('key',q.get('name')),q['failures'],flush=True)
print('MECHANICAL',out['mechanical_failures'],flush=True)
out['ground_return_geometry']=dict(before_start_pad='U15.3',after_start_pad='U15.3',before_width_mm=.25,after_width_mm=.25,before_via_count=1,after_via_count=1,retained_via_record=g.by[RETAINED_GROUND_VIA],after_trace_length_mm=LineString(ground['points']).length,source_loop_ESD_equivalence_claimed=False)
out['new_ground_physical_contacts']=[]
for o,c,m,d in BASE:
    if o['net']=='GND'and'F.Cu'in c and entries[1][1]['F.Cu'].intersects(c['F.Cu']):out['new_ground_physical_contacts'].append(dict(uuid=o['uuid'],key=o.get('key'),kind=o['kind'],area_mm2=entries[1][1]['F.Cu'].intersection(c['F.Cu']).area))
out['local_ground_complete']=out['checks'][1]['passed'] and all(q['passed']for q in out['pad_checks']if q['key']in ['U15.3','U15.8'])
ground_entries=[entries[1]]
if out['finite_cell_preflight']:
    ground_entries=[entries[1]]
    out['tail_domain_ground_context']='retained original ground via with complete replacement lead'if ground_entries else'dedicated ground still pending'
    out['tail_domains']=[]
    for r in branches:
        if time.monotonic()>DEADLINE:break
        alias=r['net']+'::'+r['role'];local=[]
        for o,c,m,d in BASE+[entries[0]]+ground_entries:
            net=o['net'];key=o.get('key')
            if net=='PORT_C_RX_EXT':
                role='upstream' if key in ['J11.1','U15.10'] else 'downstream'
                net=alias if key=='U15.1' else net+'::'+role
            elif net=='PORT_C_TX_EXT':
                role='upstream' if key in ['J11.2','U15.9'] else 'downstream'
                net=alias if key=='U15.2' else net+'::'+role
            local.append((dict(o,net=net),c,m,d))
        for rr in branches:local.append(g.track(rr['net']+'::'+rr['role'],rr['layer'],rr['points'],rr['name'],rr['width']))
        free,obs,vo=rt.domain(alias,'F.Cu',objects=local);comp=rt.component(free,r['points'][-1])
        legal=s.OUTLINE.buffer(-.479-s.ERROR-.0001).difference(rt.expanded(vo))
        regions=[] if comp is None else rt.parts(comp.intersection(legal))
        target=(g.one_pad('J11.1' if r['net']=='PORT_C_RX_EXT' else 'J11.2')['xy'] if r['role']=='upstream' else [28.963320819671004,20.840573190398317] if r['net']=='PORT_C_RX_EXT' else None)
        row=dict(name=r['name'],role=r['role'],tail=r['points'][-1],component_area_mm2=None if comp is None else comp.area,
                 component_bounds=None if comp is None else list(comp.bounds),component_wkb_hex=None if comp is None else comp.wkb_hex,
                 actual_or_existing_target=target,target_in_component=bool(comp is not None and target is not None and comp.covers(Point(target))),
                 via_regions=[dict(area_mm2=q.area,bounds=list(q.bounds),representative_mm=list(q.representative_point().coords[0]),wkb_hex=q.wkb_hex)for q in regions])
        if not regions and not row['target_in_component']and time.monotonic()<DEADLINE:
            ff,oo,vv=rt.domain(alias,'F.Cu',objects=[q for q in local if q[0]['uuid']!=CLAIM['name']]);cc=rt.component(ff,r['points'][-1])
            ll=s.OUTLINE.buffer(-.479-s.ERROR-.0001).difference(rt.expanded(vv));rr=[]if cc is None else rt.parts(cc.intersection(ll))
            row['control_without_conditional_MID_claim']=dict(component_area_mm2=None if cc is None else cc.area,target_in_component=bool(cc is not None and target is not None and cc.covers(Point(target))),via_regions=[dict(area_mm2=q.area,bounds=list(q.bounds),representative_mm=list(q.representative_point().coords[0]))for q in rr])
        out['tail_domains'].append(row);save();print('DOMAIN',r['name'],len(regions),row['target_in_component'],flush=True)
    out['all_four_tail_domains_tested']=len(out['tail_domains'])==4
    out['all_four_independent_tail_access_available']=len(out['tail_domains'])==4 and all(q['via_regions'] or q['target_in_component']for q in out['tail_domains'])
    out['four_mutually_allocated_complete_branch_paths']=False
    out['complete_local_cell']=False
    out['remaining_obligations']=['Allocate and construct all four protected branches jointly; independent region presence is not a complete route.','Fresh native courtyard, paste, drill, bonded-cut, support, reference and return qualification.']
save();print('GROUND_COMPLETE',out.get('local_ground_complete',False),flush=True);print('TERMINAL',out['seconds'],flush=True)
