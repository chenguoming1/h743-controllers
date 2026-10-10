"""Derive and construct a complete B divider on the exact completed ADC cluster."""
import ast,copy,hashlib,json,math,signal,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent/'native13-access';sys.path.insert(0,str(P));START=time.monotonic();END=START+58
sys.path.insert(0,str(H.parent/'portc51'))
import composite_native11_C_TX_WP as g
import route_native11 as r
import numpy as np
import shapely
from shapely import unary_union
from shapely.strtree import STRtree
from shapely.affinity import rotate,translate,scale
from shapely.geometry import Point,LineString,box
from shapely.ops import polygonize,polylabel
s=g.s;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();OUT=H/'B-divider-independent-C-TX-WP-exact57.json'
SOURCE=H/(sys.argv[1]if len(sys.argv)>1 else'R42-C31-B-supply12757.json');D=json.loads(SOURCE.read_text());assert D['held_BOOT_route']['layer']=='B.Cu';assert D['complete_cluster'],'A complete source-bound R42/C31 cluster is required'
F={f['ref']:f for f in g.N['footprints']}
model=H/'construct_R42_C31_domain57.py';tree=ast.parse(model.read_text());names={'shape','routecheck','viacheck','samecontacts','addroute','padcheck'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names],type_ignores=[]),str(model),'exec'),globals())
obsolete={'9e6756f4-4622-4a5f-80e2-4c78e46894ce','d354ba09-c0ed-4352-9f87-8f6fa70ec378'}
cuts={q['uuid']for q in D['removed_native_records']}|obsolete;private={'divider-route-0','divider-route-2','divider-via-0'}
BASE=[q for q in g.BASE if q[0]['uuid']not in cuts|private and q[0].get('ref')not in ('R42','C31','R43','R44')]
clusterpads=D['selected']['transformed_pad_records'];BASE += [g.entry(q)for q in clusterpads]
sr=D['held_SERVO_routes'];sv=D['held_SERVO_vias'];br=D['held_BOOT_route'];bv=D['held_BOOT_via']
heldroutes=D['routes']+sr+[br];heldvias=D['vias']+sv+[bv]
incoming_names={q['name']for q in heldroutes+heldvias};BASE=[q for q in BASE if q[0]['uuid']not in incoming_names]
BASE += [g.track(q['net'],q['layer'],q['points'],q['name'],q['width'])for q in heldroutes]+[g.via(v['net'],v['xy'],v['name'])for v in heldvias]
assert len({q[0]['uuid']for q in BASE})==len(BASE)
anchor=next(q['xy']for q in clusterpads if q['key']=='C31.1')
assert D['source']['board_sha256']==g.binding()['board_sha256']
allids={q[0]['uuid']for q in BASE}
peer_routes=g.PACKET['selected_routes']+[dict(q,name='divider-route-'+str(i))for i,q in enumerate(g.DIVIDER_ROUTES)]+[g.GREEN['route']]+g.CAP['routes']+g.CS_REQUIRED_ROUTES+g.C['selected_routes']+g.TXWP['routes']+g.TXWP['reserved_peer_routes']
peer_vias=g.PACKET['selected_vias']+[dict(q,name='divider-via-'+str(i))for i,q in enumerate(g.DIVIDER_VIAS)]+g.CS_REQUIRED_VIAS+g.TXWP['vias']+g.TXWP['reserved_peer_vias']
peer_routes=list({q['name']:q for q in peer_routes if q['name']in allids}.values());peer_vias=list({q['name']:q for q in peer_vias if q['name']in allids}.values())
audit_routes=heldroutes+peer_routes;audit_vias=heldvias+peer_vias

out=dict(schema='f722-complete-B-divider-cluster57/v1',source=g.binding(),input_receipts={SOURCE.name:sha(SOURCE)},removed_private_objects=sorted(private),removed_native_records=D['removed_native_records']+[g.by[x]for x in sorted(obsolete)],obsolete_R42_supply_contact_receipt_sha256=sha(P/'obsolete_R42_supply_contacts11.json'),cluster_poses=D['selected']['poses'],old_divider_footprints={ref:F[ref]for ref in ('R43','R44')},scope='Actual ADC B component, cardinal aligned resistor pair at 2 mm center separation on 0.1 mm grid; nearest 800 physical candidates and up to 12 exact legal constructions; bounded constructive set, not impossibility proof',rows=[],complete_B_divider=False,complete_ADC_tree=False,complete_BOOT_tree=False,native_candidate=False,adoptable=False,
 held_cluster_routes=D['routes'],held_cluster_vias=D['vias'],held_cluster_pads=D['selected']['transformed_pad_records'],held_SERVO_routes=sr,held_SERVO_vias=sv,held_BOOT_route=br,held_BOOT_via=bv,
 pending=['Full MCU-to-switch BOOT','Complete actual peer C/flash/U15 routes','Fresh native/source/placement/refill and numerical power/reference/ADC settling/noise review'],ordinary_R44_ground_width_mm=.127,divider_series_nominal_current_uA=50)
def save():out.update(seconds=time.monotonic()-START,script_sha256=sha(__file__));OUT.write_text(json.dumps(out,indent=2)+'\n')
def stop(sig,frame):out['terminal_reason']='Bounded60second complete B-divider construction';save();raise SystemExit(0)
signal.signal(signal.SIGALRM,stop);signal.alarm(max(1,int(60-(time.monotonic()-START))))
def movedshape(f,z,xy,angle):
    orig=tuple(f['xy']);z=rotate(z,f['angle'],origin=orig)
    if f['side']=='F.Cu':z=scale(z,xfact=1,yfact=-1,origin=orig)
    return translate(rotate(z,-angle,origin=orig),xy[0]-orig[0],xy[1]-orig[1])
def records(ref,xy,angle):
    f=F[ref];a=math.radians(f['angle']);b=math.radians(angle);ca,sa,cb,sb=[round(v)for v in (math.cos(a),math.sin(a),math.cos(b),math.sin(b))]
    def pt(p):
        dx,dy=p[0]-f['xy'][0],p[1]-f['xy'][1];x,y=ca*dx-sa*dy,sa*dx+ca*dy
        if f['side']=='F.Cu':y=-y
        return [round(xy[0]+cb*x+sb*y,6),round(xy[1]-sb*x+cb*y,6)]
    def pp(polys):return [dict(outer=[pt(x)for x in q['outer']],holes=[[pt(x)for x in h]for h in q.get('holes',[])])for q in polys]
    rows=[]
    for old in g.N['objects']:
        if old.get('ref')!=ref:continue
        q=copy.deepcopy(old);q['xy']=pt(old['xy']);q['angle']=angle
        q['all_layers']=[l.replace('F.','B.')for l in old['all_layers']];q['shape_by_layer']={l.replace('F.','B.'):v for l,v in old['shape_by_layer'].items()}
        for k in ('copper','inside'):q[k]={l.replace('F.','B.'):pp(v)for l,v in old[k].items()}
        q['mask']={l.replace('F.','B.'):dict(v,polygons=pp(v['polygons']))for l,v in old['mask'].items()};rows.append(q)
    return rows
neighbors={}
for f in F.values():
    ref=f['ref']
    if ref in D['selected']['poses']:
        xy,angle,side=D['selected']['poses'][ref]
        if side!='B.Cu':continue
        co=movedshape(f,shape(f,f['side'].replace('Cu','Courtyard')),xy,angle);fa=movedshape(f,shape(f,f['side'].replace('Cu','Fab')),xy,angle)
    elif f['side']=='B.Cu':co=shape(f,'B.Courtyard');fa=shape(f,'B.Fab')
    else:continue
    lands=unary_union([c['B.Cu']for o,c,m,d in BASE if o.get('ref')==ref and 'B.Cu'in c]);neighbors[ref]=(co,unary_union([fa.buffer(.15),lands.buffer(.10)]))
out['scope']='Independent R43 and R44 placement from actual ADC then MID B components; cardinal 0.1 mm grid, nearest1000 physical candidates and up to8 copper-legal poses per derived domain; no global impossibility claim'
out['R43_domain_attempts']=[]
out['full_CS_support_cluster_rebind']=[dict(name=q['name'],**routecheck(q,BASE))for q in audit_routes]+[dict(name=q['name'],**viacheck(q,BASE))for q in audit_vias]+[dict(name=p['key'],**padcheck(p,g.entry(p),BASE))for p in clusterpads+g.CAP['transformed_pads']+g.C['changed_pad_records']]
out['full_CS_support_cluster_rebind_passed']=all(q['passed']for q in out['full_CS_support_cluster_rebind']);save()
if not out['full_CS_support_cluster_rebind_passed']:
    out['terminal_reason']='Complete cluster fails exact new CS/cap/bank/support rebind';save();signal.alarm(0);print('TERMINAL REBIND FAILED',out['seconds'],flush=True);raise SystemExit(0)

def bodyshape(ref,xy,angle,pads):
    co=movedshape(F[ref],shape(F[ref],'F.Courtyard'),xy,angle)
    re=unary_union([movedshape(F[ref],shape(F[ref],'F.Fab'),xy,angle).buffer(.15)]+[g.entry(q)[1]['B.Cu'].buffer(.10)for q in pads])
    return co,re

def derive(ref,key,component,objects,neigh,target):
    blocked={};s.OBJECTS=objects;s.HALF=0
    nets={q['net']for q in g.N['objects']if q.get('ref')==ref}
    for net in nets:
        ob,_,_=s.obstacles(net,'B.Cu');blocked[net]=r.expanded(ob)
    maskblocked=unary_union([d.buffer(.20+s.ERROR+.0001)for o,c,m,d in objects if d is not None]);inside=s.OUTLINE.buffer(-.254-s.ERROR)
    courts=np.array([co for co,re in neigh.values()if not co.is_empty],dtype=object);ctree=STRtree(courts);pool=[];minx,miny,maxx,maxy=component.bounds;shapely.prepare(component)
    for angle in (0,90,180,270):
        proto=records(ref,[0,0],angle);offset=next(q['xy']for q in proto if q['key']==key);cb=movedshape(F[ref],shape(F[ref],'F.Courtyard'),[0,0],angle).bounds
        xv=np.arange(math.floor((minx-offset[0])*10),math.ceil((maxx-offset[0])*10)+1)/10;yv=np.arange(math.floor((miny-offset[1])*10),math.ceil((maxy-offset[1])*10)+1)/10
        xx,yy=np.meshgrid(xv,yv);xx=xx.ravel();yy=yy.ravel();okay=shapely.intersects_xy(component,xx+offset[0],yy+offset[1])
        xc,yc=xx[okay],yy[okay];rects=shapely.box(xc+cb[0],yc+cb[1],xc+cb[2],yc+cb[3]);keep=np.ones(len(xc),dtype=bool)
        pairs=ctree.query(rects,predicate='intersects')
        if pairs.shape[1]:
            areas=shapely.area(shapely.intersection(rects[pairs[0]],courts[pairs[1]]));keep[np.unique(pairs[0][areas>1e-10])]=False
        for x,y in zip(xc[keep],yc[keep]):pool.append((math.dist([x+offset[0],y+offset[1]],target),[float(x),float(y)],angle))
    if ref=='R43':
        for xy in (list(F['C31']['xy']),[15.87,8.0]):
            for angle in (180,0,90,270):
                pp=records(ref,xy,angle);contact=next(q['xy']for q in pp if q['key']==key)
                if component.covers(Point(contact)):pool.append((-1.0,xy,angle))
    pool.sort();legal=[]
    for score,xy,angle in pool[:1000]:
        pp=records(ref,xy,angle)
        if not all(not s.geom(q['copper']['B.Cu']).intersects(blocked[q['net']])and not s.geom(q['mask']['B.Mask']['polygons']).intersects(maskblocked)and inside.covers(s.geom(q['copper']['B.Cu']))for q in pp):continue
        co,re=bodyshape(ref,xy,angle,pp)
        if not s.OUTLINE.covers(re)or any(co.intersection(nc).area>1e-10 or re.intersection(nr).area>1e-10 for nc,nr in neigh.values()):continue
        legal.append((xy,angle,pp))
        if len(legal)>=8:break
    return dict(component_bounds=list(component.bounds),component_area_mm2=component.area,mechanical_shortlist_count=len(pool),legal_pose_count=len(legal),legal_poses=[dict(xy=xy,angle=ang,side='B.Cu')for xy,ang,p in legal]),legal
out['mechanical_prefilter']='Exact translated rectangular resistor courtyard against each actual neighbor courtyard polygon, including U1 corner recesses; no whole-neighbor bounding-box exclusions'
out['old_C31_site_R43_diagnostic']=[]
for xy in ([15.9,8.0],[15.87,8.0]):
    for angle in (0,90,180,270):
        pp=records('R43',xy,angle);co,re=bodyshape('R43',xy,angle,pp);bad=[dict(ref=ref,courtyard_overlap_mm2=co.intersection(nc).area,reserve_overlap_mm2=re.intersection(nr).area)for ref,(nc,nr)in neighbors.items()if co.intersection(nc).area>1e-10 or re.intersection(nr).area>1e-10]
        oo=BASE+[g.entry(p)for p in pp];pc=[padcheck(p,g.entry(p),oo)for p in pp];out['old_C31_site_R43_diagnostic'].append(dict(xy=xy,angle=angle,mechanical_failures=bad,pad_checks=pc))
save()
free,obs,_=r.domain('ADC_BUS','B.Cu',objects=BASE);component=r.component(free,anchor);assert component is not None
out['R43_derived_domain'],r43poses=derive('R43','R43.1',component,BASE,neighbors,anchor);save()
for x43,a43,p43 in r43poses:
    objects=BASE+[g.entry(q)for q in p43];checks=[padcheck(q,g.entry(q),objects)for q in p43];row=dict(R43=[x43,a43,'B.Cu'],R43_pads=p43,R43_pad_checks=checks);out['R43_domain_attempts'].append(row);save()
    if not all(q['passed']for q in checks):continue
    q43={q['key']:q for q in p43};adc=addroute('ADC_BUS','B.Cu',.127,q43['R43.1']['xy'],anchor,objects,'B-divider-ADC')
    if adc is None:row['terminal_reason']='Actual R43 ADC branch construction failed';save();continue
    current=objects+[g.track(adc['net'],adc['layer'],adc['points'],adc['name'],adc['width'])];row['ADC_route']=adc
    mf,mo,_=r.domain('ADC_DIV_MID','B.Cu',objects=current);mc=r.component(mf,q43['R43.2']['xy'])
    if mc is None:row['terminal_reason']='R43 MID pad has no B component';save();continue
    nb=dict(neighbors);nb['R43']=bodyshape('R43',x43,a43,p43);row['R44_derived_domain'],r44poses=derive('R44','R44.1',mc,current,nb,q43['R43.2']['xy']);save()
    for x44,a44,p44 in r44poses:
        pp={q['key']:q for q in p43+p44};held=current+[g.entry(q)for q in p44];pc=[padcheck(q,g.entry(q),held)for q in p44];trial=dict(poses={'R43':[x43,a43,'B.Cu'],'R44':[x44,a44,'B.Cu']},pads=p43+p44,pad_checks=checks+pc,complete=False);out['rows'].append(trial);save()
        if not all(q['passed']for q in pc):continue
        mid=addroute('ADC_DIV_MID','B.Cu',.127,pp['R43.2']['xy'],pp['R44.1']['xy'],held,'B-divider-MID')
        if mid is None:trial['failed_branch']='MID';save();continue
        trial['MID_route']=mid;held += [g.track(mid['net'],mid['layer'],mid['points'],mid['name'],mid['width'])]
        gf,go,gvo=r.domain('GND','B.Cu',width=.127,objects=held);gc=r.component(gf,pp['R44.2']['xy']);region=gc.difference(r.expanded(gvo))if gc is not None else box(0,0,0,0);regions=sorted(r.parts(region),key=lambda q:q.distance(Point(pp['R44.2']['xy'])));trial['GND_regions']=[dict(area=q.area,bounds=list(q.bounds))for q in regions];save()
        for reg in regions[:3]:
            near=reg.intersection(Point(pp['R44.2']['xy']).buffer(reg.distance(Point(pp['R44.2']['xy']))+.2));parts=r.parts(near)
            if not parts:continue
            p=polylabel(max(parts,key=lambda q:q.area),tolerance=.00001);v=dict(name='B-divider-GND-via',net='GND',xy=[round(p.x,6),round(p.y,6)],diameter=.45,drill=.2);vc=viacheck(v,held)
            if not vc['passed']:continue
            q=addroute('GND','B.Cu',.127,pp['R44.2']['xy'],v['xy'],held,'B-divider-GND')
            if q is None:continue
            ge=g.track(q['net'],q['layer'],q['points'],q['name'],q['width']);ve=g.via(v['net'],v['xy'],v['name']);contacts=samecontacts(ge,BASE,set())+samecontacts(ve,BASE,set())
            if contacts:trial['rejected_GND_contacts']=contacts;save();continue
            allobjects=held+[ge,ve];routes=[adc,mid,q];audit=[dict(name=a['name'],**routecheck(a,allobjects))for a in routes+audit_routes]+[dict(name=a['name'],**viacheck(a,allobjects))for a in audit_vias+[v]]
            trial.update(mutual_checks=audit,complete=all(a['passed']for a in audit));save()
            if not trial['complete']:continue
            out.update(selected=trial,routes=routes,vias=[v],complete_B_divider=True,complete_ADC_tree=True,ADC_terminal_ledger=[dict(key=k,path_complete_to_MCU=True,xy=next(p['xy']for p in clusterpads+p43+p44+[g.one_pad('U1.10')]if p['key']==k))for k in ('R42.2','C31.1','U1.10','R43.1')],dedicated_R44_GND_contacts=contacts,terminal_reason='Complete four-terminal ADC and independently placed B divider; full BOOT/native/source/refill/reference still pending')
            save();signal.alarm(0);print('TERMINAL',True,trial['poses'],v['xy'],out['seconds'],flush=True);raise SystemExit(0)
out['terminal_reason']='No complete independently placed B-divider pair in the derived actual-domain set';save();signal.alarm(0);print('TERMINAL',False,out['seconds'],flush=True)
