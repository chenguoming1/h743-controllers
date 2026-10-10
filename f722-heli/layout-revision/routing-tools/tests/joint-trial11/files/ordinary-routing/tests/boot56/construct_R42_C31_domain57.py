"""Complete isolated R42 front supply and local ADC transition, with the full SERVO1 donor held."""
import copy, hashlib, json, math, signal, sys, time
from pathlib import Path
H=Path(__file__).resolve().parent; P=H.parent/'native13-access'; sys.path.insert(0,str(P)); START=time.monotonic(); END=START+58
import composite_native11_divider_joint as g
import route_native11 as r
import graph_native11 as gr
import shapely
import numpy as np
from shapely import unary_union
from shapely.affinity import rotate, translate, scale
from shapely.geometry import Point, LineString, box
from shapely.ops import polygonize, polylabel
s=g.s; OUT=H/'R42-C31-domain-cluster57.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
LEAF='8abfb231-06dd-424d-89f3-389986d23e6a'; SUPPLY='dfd384be-99d1-43a6-afd1-174fc1df74d9'
BASE=[a for a in g.BASE if a[0].get('ref')!='R42' and a[0]['uuid']!=LEAF]
servofile=P/'joint-divider-SERVO1-restore11.json'; SERVO=json.loads(servofile.read_text()); assert SERVO['complete']
sr=[dict(q,name='R42-held-SERVO1-route-'+str(i)) for i,q in enumerate(SERVO['routes'])]
sv=[dict(q,name='R42-held-SERVO1-via-'+str(i)) for i,q in enumerate(SERVO['vias'])]
BASE += [g.track(a['net'],a['layer'],a['points'],a['name'],a['width']) for a in sr]+[g.via(a['net'],a['xy'],a['name']) for a in sv]
bootvia=dict(name='R42-held-BOOT-via',net='BOOT0',xy=[18.983413,18.246418],diameter=.45,drill=.2)
bootroute=dict(name='R42-held-BOOT-entry',net='BOOT0',layer='F.Cu',width=.127,points=[g.one_pad('U1.60')['xy'],bootvia['xy']])
BASE += [g.track(bootroute['net'],bootroute['layer'],bootroute['points'],bootroute['name']),g.via(bootvia['net'],bootvia['xy'],bootvia['name'])]
F={f['ref']:f for f in g.N['footprints']}; PF=F['R42']; ORIGIN=tuple(PF['xy']); OLD=[o for o in g.N['objects'] if o.get('ref')=='R42']
assert PF['value']=='68.0k / 0.1%' and PF['side']=='F.Cu' and PF['angle']==0
out=dict(schema='f722-R42-C31-cluster57/v1',source=g.binding(),held_receipts={servofile.name:sha(servofile)},
    removed_native_records=[g.by[LEAF]],old_footprint=PF,old_pad_records=OLD,held_SERVO_routes=sr,held_SERVO_vias=sv,
    held_BOOT_route=bootroute,held_BOOT_via=bootvia,held_ADC_CAP=True,original_divider_feed_and_ground_held=True,
    routes=[],vias=[],rows=[],complete_R42_leaves=False,native_candidate=False,adoptable=False,
    pending=['Complete ADC divider join and MCU BOOT','Native pose reproduction and source transaction','Fresh power, ADC settling/noise, reference and finite native gates','Remaining C and flash capacity'])
def save():
    out.update(seconds=time.monotonic()-START,script_sha256=sha(__file__)); OUT.write_text(json.dumps(out,indent=2)+'\n')
def stop(sig,frame):
    out['terminal_reason']='Bounded60second constructive placement/supply/ADC search';save();raise SystemExit(0)
signal.signal(signal.SIGALRM,stop);signal.alarm(max(1,int(60-(time.monotonic()-START))))
def shape(f,layer):
    lines=[]; polys=[]
    for q in f['graphics']:
        if q['layer']!=layer:continue
        if q['shape']=='Line':lines.append(LineString([q['start'],q['end']]))
        elif q['shape']=='Rect':polys.append(box(min(q['start'][0],q['end'][0]),min(q['start'][1],q['end'][1]),max(q['start'][0],q['end'][0]),max(q['start'][1],q['end'][1])))
        elif q['shape']=='Polygon':polys.append(s.geom(q['polygons']))
        elif q['shape']=='Circle':polys.append(Point(q['center']).buffer(math.dist(q['center'],q['end']),quad_segs=96))
        else:raise ValueError(q['shape'])
    return unary_union(polys+list(polygonize(unary_union(lines))))
NEIGH={}
for f in F.values():
    if f['side']!='F.Cu':continue
    lands=unary_union([c['F.Cu'] for o,c,m,d in BASE if o.get('ref')==f['ref'] and 'F.Cu' in c])
    NEIGH[f['ref']]=(shape(f,'F.Courtyard'),unary_union([shape(f,'F.Fab').buffer(.15),lands.buffer(.10)]))
def move(z,xy,angle):
    return translate(rotate(z,-angle,origin=ORIGIN),xy[0]-ORIGIN[0],xy[1]-ORIGIN[1])
def records(xy,angle):
    ca,sa=round(math.cos(math.radians(angle))),round(math.sin(math.radians(angle)))
    def pt(p):
        dx,dy=p[0]-ORIGIN[0],p[1]-ORIGIN[1];return [round(xy[0]+ca*dx+sa*dy,6),round(xy[1]-sa*dx+ca*dy,6)]
    def pp(polys):return [dict(outer=[pt(x) for x in q['outer']],holes=[[pt(x) for x in h] for h in q.get('holes',[])]) for q in polys]
    rows=[]
    for old in OLD:
        q=copy.deepcopy(old);q['xy']=pt(old['xy']);q['angle']=angle;q['angle']=angle
        q['all_layers']=[l for l in old['all_layers']]
        q['shape_by_layer']={l:v for l,v in old['shape_by_layer'].items()}
        for k in ('copper','inside'):q[k]={l:pp(v) for l,v in old[k].items()}
        q['mask']={l:dict(v,polygons=pp(v['polygons'])) for l,v in old['mask'].items()}; rows.append(q)
    return rows
def routecheck(a,objects):
    s.OBJECTS=objects;s.HALF=a['width']/2;obs,_,_=s.obstacles(a['net'],a['layer']);checks=s.check(LineString(a['points']),obs,True)
    return dict(passed=all(c['pass_with_polygon_error'] for c in checks),nearest=checks[:4],failures=[c for c in checks if not c['pass_with_polygon_error']])
# Establish exact native leaf contacts before replacing anything.
leaf=next(a for a in g.BASE if a[0]['uuid']==LEAF);lc=leaf[1]['F.Cu']
out['old_supply_leaf_contacts']=[dict(uuid=o['uuid'],key=o.get('key'),kind=o['kind']) for o,c,m,d in g.BASE if o['uuid']!=LEAF and o['net']=='+5V_PERIPH' and 'F.Cu' in c and lc.intersects(c['F.Cu'])]
assert {a['uuid'] for a in out['old_supply_leaf_contacts']}=={g.one_pad('R42.1')['uuid'],'9e6756f4-4622-4a5f-80e2-4c78e46894ce'}
save()
GND_VIA='39a56392-875d-4879-813e-fb2d9fe74901';GND_LEAF='d94712e6-c55c-5d2f-a271-f17e1825ac82'
CAPF=F['C31'];CAPOLD=[o for o in g.N['objects'] if o.get('ref')=='C31'];assert CAPF['side']=='B.Cu' and CAPF['angle']==180 and CAPF['value']=='220nF / 16V / X7R'
oldground=next(a for a in g.BASE if a[0]['uuid']==GND_LEAF);oldvia=next(a for a in g.BASE if a[0]['uuid']==GND_VIA)
def samecontacts(entry,objects,skip):
    return [dict(uuid=o['uuid'],key=o.get('key'),kind=o['kind']) for o,c,m,d in objects if o['uuid']not in skip and o['net']==entry[0]['net'] and any(l in c and cu.intersects(c[l]) for l,cu in entry[1].items())]
out['old_C31_ground_leaf_contacts']=samecontacts(oldground,g.BASE,{GND_LEAF})
out['old_C31_ground_via_contacts']=samecontacts(oldvia,g.BASE,{GND_VIA})
out['old_C31_GND_plane_contacts']=[dict(zone_uuid=z['uuid'],layer=l,source_intersection_area_mm2=oldvia[1][l].intersection(s.geom(pp)).area) for z in g.N['zones'] if not z['rule'] and z['net']=='GND' for l,pp in z['filled'].items() if l in oldvia[1]]
out['native_refill_required_because_GND_barrel_changes_to_ADC']=True
out['plane_behavior_qualified']=False
out['plane_behavior_gate']='Refill both retained GND planes after old ground via removal/new ADC barrel insertion; verify no ADC-to-GND contact and actual dedicated C31 return connectivity/reference continuity.'

assert {q['uuid'] for q in out['old_C31_ground_leaf_contacts']}=={g.one_pad('C31.2')['uuid'],GND_VIA}
assert {q['uuid'] for q in out['old_C31_ground_via_contacts']}=={GND_LEAF}
BASE=[a for a in BASE if a[0].get('ref')!='C31' and a[0]['uuid']not in (GND_VIA,GND_LEAF)]
out['removed_native_records'] += [g.by[GND_LEAF],g.by[GND_VIA]]
out['old_C31_footprint']=CAPF;out['old_C31_pad_records']=CAPOLD;out['complete_cluster']=False
out['held_ADC_CAP']=False;out['retained_actual_MCU_ADC_B_witness']=next(q for q in g.PACKET['selected_routes'] if q['net']=='ADC_BUS')
out['pending'] += ['Dedicated C31 ground replacement and ADC filter geometry require fresh noise/settling review']
anchor=g.one_pad('C31.1')['xy'];ADCVIA=dict(name='cluster-ADC-transition',net='ADC_BUS',xy=g.by[GND_VIA]['xy'],diameter=.45,drill=.2)
def caprecords(xy,angle):
    ca,sa=round(math.cos(math.radians(angle-CAPF['angle']))),round(math.sin(math.radians(angle-CAPF['angle'])))
    def pt(p):
        dx,dy=p[0]-CAPF['xy'][0],p[1]-CAPF['xy'][1];return [round(xy[0]+ca*dx+sa*dy,6),round(xy[1]-sa*dx+ca*dy,6)]
    def pp(polys):return [dict(outer=[pt(x) for x in q['outer']],holes=[[pt(x) for x in h] for h in q.get('holes',[])]) for q in polys]
    result=[]
    for old in CAPOLD:
        q=copy.deepcopy(old);q['xy']=pt(old['xy']);q['angle']=angle
        for k in ('copper','inside'):q[k]={l:pp(v) for l,v in old[k].items()}
        q['mask']={l:dict(v,polygons=pp(v['polygons'])) for l,v in old['mask'].items()};result.append(q)
    return result
NEIGHB={}
for f in F.values():
    if f['side']!='B.Cu' or f['ref']=='C31':continue
    lands=unary_union([c['B.Cu'] for o,c,m,d in BASE if o.get('ref')==f['ref'] and 'B.Cu' in c])
    NEIGHB[f['ref']]=(shape(f,'B.Courtyard'),unary_union([shape(f,'B.Fab').buffer(.15),lands.buffer(.10)]))
def padcheck(p,entry,objects):
    layer=next(iter(p['copper']));cu=entry[1][layer];ma=entry[2][layer.replace('Cu','Mask')];bad=[];minimum=math.inf
    for o,c,m,d in objects:
        if o['uuid']==p['uuid']:continue
        mm=[]
        if o['net']!=p['net'] and layer in c:mm.append(('foreign_copper',cu.distance(c[layer])-.127))
        if d is not None:
            mm.append(('all_drill_mask',ma.distance(d)-.20))
            if o['net']!=p['net']:mm.append(('foreign_drill_pad',cu.distance(d)-(.254 if o.get('npth') else .20)))
        for kind,margin in mm:
            minimum=min(minimum,margin)
            if margin<s.ERROR:bad.append(dict(uuid=o['uuid'],key=o.get('key'),net=o['net'],kind=kind,margin_mm=margin))
    if not s.OUTLINE.covers(cu) or cu.distance(s.OUTLINE.boundary)<.254+s.ERROR:bad.append(dict(kind='outline'))
    return dict(key=p['key'],passed=not bad,minimum_margin_mm=minimum,failures=bad[:8])
def viacheck(v,objects):
    s.OBJECTS=[q for q in objects if q[0]['uuid']!=v['name']];s.HALF=.0635;_,vo,_=s.obstacles(v['net'],'F.Cu');ch=s.check(Point(v['xy']),vo,True)
    return dict(passed=all(q['pass_with_polygon_error'] for q in ch),nearest=ch[:5],failures=[q for q in ch if not q['pass_with_polygon_error']])
def addroute(net,layer,width,a,b,objects,name):
    free,obs,_=r.domain(net,layer,width=width,objects=objects);comp=r.component(free,a)
    if comp is None or not comp.covers(Point(b)):return None
    pts=r.route(comp,a,b,END)
    if pts is None:return None
    q=dict(name=name,net=net,layer=layer,width=width,points=pts);q.update(routecheck(q,objects));return q if q['passed'] else None
courtR=shape(PF,'F.Courtyard');fabR=shape(PF,'F.Fab');courtC=shape(CAPF,'B.Courtyard');fabC=shape(CAPF,'B.Fab')
# Derive a physical shortlist from the complete actual ADC B component, not
# another collection of neighboring cap guesses. Board-wide component bounds
# are searched at0.1mm for every orthogonal cap angle, ranked by ADC-pin distance.
fixed_rxy=[16,7.7];fixed_rp=records(fixed_rxy,0)
out['ADC_terminal_ledger']=[dict(key='R42.2',planned_xy=next(q['xy'] for q in fixed_rp if q['key']=='R42.2'),path_complete_to_MCU=False,status='Complete moved input branch pending'),dict(key='C31.1',planned_xy=None,path_complete_to_MCU=False,status='Cap legal domain and full branch pending'),dict(key='U1.10',xy=g.one_pad('U1.10')['xy'],path_complete_to_MCU=True,status='Actual MCU pad and retained B witness held; moved cap connection pending'),dict(key='R43.1',xy=g.one_pad('R43.1')['xy'],path_complete_to_MCU=False,status='Current original complete-divider endpoint; actual ADC join pending')]
out['complete_ADC_tree']=False;out['complete_BOOT_tree']=False
out['BOOT_ledger']=dict(MCU_entry_complete=True,accepted_SW1_R2_segment_complete=True,actual_MCU_to_SW1_path_complete=False)

physical=BASE+[g.entry(q) for q in fixed_rp]+[g.via(ADCVIA['net'],ADCVIA['xy'],ADCVIA['name'])]
cf,co,_=r.domain('ADC_BUS','B.Cu',objects=physical);component=r.component(cf,anchor)
assert component is not None
out['actual_B_component_bounds']=list(component.bounds);out['actual_B_component_area_mm2']=component.area
out['proven_transition_reaches_retained_ADC_witness']=component.covers(Point(ADCVIA['xy']));save()
if not out['proven_transition_reaches_retained_ADC_witness']:
    out['terminal_reason']='Repurposed barrel has no B path to the retained actual MCU ADC branch';save();raise SystemExit(0)
# Conservative obstacle inflation and exact translated pad polygons provide a
# cheap positive legality filter. The selected candidates still receive every
# individual copper, mask/drill, body and route audit below.
blocked={};s.OBJECTS=physical;s.HALF=0
for net in ('ADC_BUS','GND'):
    obs,_,_=s.obstacles(net,'B.Cu');blocked[net]=r.expanded(obs)
maskblocked=unary_union([d.buffer(.2+s.ERROR+.0001) for o,c,m,d in physical if d is not None])
nb=[c.bounds for c,re in NEIGHB.values() if not c.is_empty]
minx,miny,maxx,maxy=component.bounds;pool=[];mcu=g.one_pad('U1.10')['xy']
shapely.prepare(component)
for angle in (0,90,180,270):
    proto=caprecords([0,0],angle);offset=next(q['xy'] for q in proto if q['key']=='C31.1')
    sh=rotate(courtC,-(angle-CAPF['angle']),origin=tuple(CAPF['xy']));cb=translate(sh,-CAPF['xy'][0],-CAPF['xy'][1]).bounds
    xv=np.arange(math.floor((minx-offset[0])*10),math.ceil((maxx-offset[0])*10)+1)/10
    yv=np.arange(math.floor((miny-offset[1])*10),math.ceil((maxy-offset[1])*10)+1)/10
    xx,yy=np.meshgrid(xv,yv);xx=xx.ravel();yy=yy.ravel()
    okay=shapely.intersects_xy(component,xx+offset[0],yy+offset[1])
    for b in nb:
        okay &= (xx+cb[2]<=b[0]) | (xx+cb[0]>=b[2]) | (yy+cb[3]<=b[1]) | (yy+cb[1]>=b[3])
    for x,y in zip(xx[okay],yy[okay]):
        xy=[float(x),float(y)];adcxy=[xy[0]+offset[0],xy[1]+offset[1]];pool.append((math.dist(adcxy,mcu),xy,angle))
pool.sort();out['ADC_reachable_mechanical_shortlist']=len(pool);legal=[];innerboard=s.OUTLINE.buffer(-.254-s.ERROR)
for score,xy,angle in pool[:350]:
    candidates=caprecords(xy,angle);good=True
    for q in candidates:
        cu=s.geom(q['copper']['B.Cu']);ma=s.geom(q['mask']['B.Mask']['polygons'])
        if cu.intersects(blocked[q['net']]) or ma.intersects(maskblocked) or not innerboard.covers(cu):good=False;break
    if good:legal.append((fixed_rxy,xy,angle))
    if len(legal)>=16:break
out['derived_copper_legal_poses']=[dict(C31=[xy,angle,'B.Cu'],R42=[rp,0,'F.Cu']) for rp,xy,angle in legal]
out['scope']='Actual ADC B component bounds, all cardinal cap angles and0.1mm center grid; nearest350 mechanical/ADC-reachable candidates receive exact conservative pad/mask filters, then up to16 full constructive cluster attempts';save()
poses=legal
for rxy,cxy,cangle in poses:
    rp=records(rxy,0);cp=caprecords(cxy,cangle);pads=rp+cp;entries=[g.entry(q) for q in pads];objects=BASE+entries+[g.via(ADCVIA['net'],ADCVIA['xy'],ADCVIA['name'])]
    pcs=[padcheck(p,e,objects) for p,e in zip(pads,entries)];mech=[]
    rc=move(courtR,rxy,0);rr=unary_union([move(fabR,rxy,0).buffer(.15)]+[e[1]['F.Cu'].buffer(.1) for e in entries[:2]])
    cc=translate(rotate(courtC,-(cangle-CAPF['angle']),origin=tuple(CAPF['xy'])),cxy[0]-CAPF['xy'][0],cxy[1]-CAPF['xy'][1]);cr=unary_union([translate(rotate(fabC,-(cangle-CAPF['angle']),origin=tuple(CAPF['xy'])),cxy[0]-CAPF['xy'][0],cxy[1]-CAPF['xy'][1]).buffer(.15)]+[e[1]['B.Cu'].buffer(.1) for e in entries[2:]])
    for ref,(co,re) in NEIGH.items():
        if rc.intersection(co).area>1e-10 or rr.intersection(re).area>1e-10:mech.append(['R42',ref])
    for ref,(co,re) in NEIGHB.items():
        if cc.intersection(co).area>1e-10 or cr.intersection(re).area>1e-10:mech.append(['C31',ref])
    if not s.OUTLINE.covers(rr) or not s.OUTLINE.covers(cr):mech.append(['outline'])
    vc=viacheck(ADCVIA,objects);row=dict(poses={'R42':[rxy,0,'F.Cu'],'C31':[cxy,cangle,'B.Cu']},pad_checks=pcs,mechanical_failures=mech,ADC_via_check=vc,pose_passed=all(q['passed'] for q in pcs) and not mech and vc['passed']);out['rows'].append(row);save()
    if not row['pose_passed']:continue
    pp={p['key']:p for p in pads};routes=[];current=list(objects);complete=True
    for net,layer,width,a,b,name in [('ADC_BUS','F.Cu',.127,pp['R42.2']['xy'],ADCVIA['xy'],'cluster-R42-ADC-F'),('ADC_BUS','B.Cu',.127,ADCVIA['xy'],anchor,'cluster-ADC-via-MCU-branch'),('ADC_BUS','B.Cu',.127,pp['C31.1']['xy'],anchor,'cluster-C31-ADC-join')]:
        q=addroute(net,layer,width,a,b,current,name)
        if q is None:complete=False;row['failed_branch']=name;save();break
        routes.append(q);current.append(g.track(q['net'],q['layer'],q['points'],q['name'],q['width']))
    if not complete:continue
    row['ADC_routes']=routes;save()
    gf,go,gvo=r.domain('GND','B.Cu',width=.25,objects=current);gc=r.component(gf,pp['C31.2']['xy'])
    gx,gy=pp['C31.2']['xy'];region=gc.intersection(box(gx-3,gy-3,gx+3,gy+3)).difference(r.expanded(gvo)) if gc is not None else box(0,0,0,0)
    regions=sorted(r.parts(region),key=lambda q:(q.distance(Point(pp['C31.2']['xy'])),-q.area));row['ground_regions']=[dict(area=q.area,bounds=list(q.bounds)) for q in regions];row['ground_trials']=[];save()
    for reg in regions[:4]:
        near=reg.intersection(Point(pp['C31.2']['xy']).buffer(reg.distance(Point(pp['C31.2']['xy']))+.3));nearparts=r.parts(near);p=polylabel(max(nearparts,key=lambda q:q.area),tolerance=.00001);gv=dict(name='cluster-C31-dedicated-GND-via',net='GND',xy=[round(p.x,6),round(p.y,6)],diameter=.45,drill=.2)
        gcheck=viacheck(gv,current)
        if not gcheck['passed']:continue
        gt=addroute('GND','B.Cu',.25,pp['C31.2']['xy'],gv['xy'],current,'cluster-C31-dedicated-GND-lead')
        if gt is None:continue
        ge=g.track(gt['net'],gt['layer'],gt['points'],gt['name'],gt['width']);ve=g.via(gv['net'],gv['xy'],gv['name'])
        extra=samecontacts(ge,BASE,set())+samecontacts(ve,BASE,set());trial=dict(via=gv,via_check=gcheck,route=gt,unintended_source_GND_contacts=extra);row['ground_trials'].append(trial);save()
        if extra:continue
        held=current+[ge,ve];ff,fo,_=r.domain('+5V_PERIPH','F.Cu',width=.25,objects=held);fc=r.component(ff,pp['R42.1']['xy'])
        anchors=[g.by[SUPPLY],g.one_pad('J9.3'),g.by['9e6756f4-4622-4a5f-80e2-4c78e46894ce']];accessible=[a for a in anchors if fc is not None and fc.covers(Point(a['xy']))]
        trial['accessible_supply_anchors']=[a.get('key',a['uuid']) for a in accessible];save()
        if not accessible:continue
        chosen=min(accessible,key=lambda a:math.dist(a['xy'],pp['R42.1']['xy']));feed=addroute('+5V_PERIPH','F.Cu',.25,pp['R42.1']['xy'],chosen['xy'],held,'cluster-R42-supply-F')
        if feed is None:continue
        fe=g.track(feed['net'],feed['layer'],feed['points'],feed['name'],feed['width']);held.append(fe)
        out['selected']=dict(row,transformed_pad_records=pads);out['routes']=routes+[gt,feed];out['vias']=[ADCVIA,gv];out['new_supply_anchor_record']=chosen
        out['new_supply_contacts']=samecontacts(fe,held,{feed['name']});out['dedicated_ground_source_contacts']=extra
        out['simultaneous_route_checks']=[dict(name=a['name'],**routecheck(a,held)) for a in out['routes']+[bootroute]+sr]
        out['simultaneous_via_checks']=[dict(name=v['name'],**viacheck(v,held)) for v in out['vias']]
        out['complete_cluster']=all(q['passed'] for q in out['simultaneous_route_checks']+out['simultaneous_via_checks']);out['complete_R42_leaves']=out['complete_cluster']
        out['terminal_reason']='Complete two-part ADC cluster, dedicated C31 return and R42 supply with complete SERVO1 and BOOT entry held; divider ADC join and remaining BOOT still pending'
        out['total_new_length_mm']=sum(LineString(q['points']).length for q in out['routes'])
        out['ADC_terminal_ledger']=[dict(key=key,xy=pp[key]['xy'] if key in pp else g.one_pad(key)['xy'],net='ADC_BUS',path_complete_to_MCU=key!='R43.1',evidence='Constructed cluster plus retained exact MCU ADC B witness' if key!='R43.1' else 'Join not yet constructed') for key in ('R42.2','C31.1','U1.10','R43.1')]
        out['complete_ADC_tree']=False;out['complete_BOOT_tree']=False;out['BOOT_ledger']=dict(MCU_entry_complete=True,accepted_SW1_R2_segment_complete=True,actual_MCU_to_SW1_path_complete=False);save()
        graph=gr.build('ADC_BUS',held);rp43=g.one_pad('R43.1');join=gr.connect(graph,pp['C31.1']['xy'],rp43['xy'],('B.Cu',),tuple(rp43['copper']))
        join['actual_pair']=['C31.1','R43.1'];out['actual_divider_join']=join;save()
        if join['connected']:
            for i,v in enumerate(join['new_vias']):
                av=dict(name='cluster-divider-ADC-via-'+str(i),net='ADC_BUS',xy=v['xy'],diameter=.45,drill=.2);out['vias'].append(av);held.append(g.via(av['net'],av['xy'],av['name']))
            joined=True
            for i,leg in enumerate(join['legs']):
                if math.dist(leg['start'],leg['end'])<1e-8:continue
                pts=r.route(graph['nodes'][leg['node']][1],leg['start'],leg['end'],END)
                if pts is None:joined=False;break
                ar=dict(name='cluster-divider-ADC-route-'+str(i),net='ADC_BUS',layer=leg['layer'],width=.127,points=pts);ar.update(routecheck(ar,held))
                if not ar['passed']:joined=False;break
                out['routes'].append(ar);held.append(g.track(ar['net'],ar['layer'],ar['points'],ar['name'],ar['width']));save()
            out['ADC_join_constructed']=joined
            if joined:
                out['full_ADC_mutual_checks']=[dict(name=a['name'],**routecheck(a,held)) for a in out['routes']+[bootroute]+sr]+[dict(name=v['name'],**viacheck(v,held)) for v in out['vias']]
                out['complete_ADC_tree']=all(q['passed'] for q in out['full_ADC_mutual_checks'])
                if out['complete_ADC_tree']:out['ADC_terminal_ledger'][-1].update(path_complete_to_MCU=True,evidence='Full actual divider join constructed and mutually finite-checked')
        else:
            join['terminal_component_domains']=[dict(node=i,layer=graph['nodes'][i][0],bounds=list(graph['nodes'][i][1].bounds),via_area_mm2=graph['eligible'][i].area if i in graph['eligible'] else 0) for i in join['start_nodes']+join['end_nodes']]
        out['terminal_reason']='Complete local R42/C31 cluster; actual divider ADC join '+('complete' if out['complete_ADC_tree'] else 'still open')+'; MCU-to-switch BOOT and complete peer/native/reference gates remain pending'
        out['total_new_length_mm']=sum(LineString(q['points']).length for q in out['routes']);save();signal.alarm(0);print('TERMINAL',out['complete_cluster'],out['complete_ADC_tree'],rxy,cxy,gv['xy'],out['total_new_length_mm'],out['seconds'],flush=True);raise SystemExit(0)
out['terminal_reason']='No complete two-part cluster in the bounded constructive set';save();signal.alarm(0);print('TERMINAL',False,out['seconds'],flush=True)
