"""Derive and construct a complete B divider on the exact completed ADC cluster."""
import ast,copy,hashlib,json,math,signal,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent/'native13-access';sys.path.insert(0,str(P));START=time.monotonic();END=START+58
sys.path.insert(0,str(H.parent/'portc51'))
import composite_native11_dedicated_IMU_CS as g
import route_native11 as r
import numpy as np
import shapely
from shapely import unary_union
from shapely.strtree import STRtree
from shapely.affinity import rotate,translate,scale
from shapely.geometry import Point,LineString,box
from shapely.ops import polygonize,polylabel
s=g.s;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();OUT=H/'R43-six-MID-domains57.json'
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
import graph_native11 as gr
PREVFILE=H/'B-divider-independent-C-TX-WP-exact57.json';PREV=json.loads(PREVFILE.read_text());assert PREV['full_CS_support_cluster_rebind_passed']and PREV['source']==g.BOOT['source']
out.update(scope='Exactly six proved R43/ADC B witnesses and their opposite polarity controls, with complete current C/TX/WP/BOOT and unchanged ADC capacitor return',R43_witness_receipt_sha256=sha(PREVFILE),rows=[],complete_divider=False,complete_BOOT_tree=True)
for old in PREV['R43_domain_attempts']:
    xy,angle,side=old['R43'];pads=old['R43_pads'];adc=old['ADC_route'];objects=BASE+[g.entry(q)for q in pads]+[g.track(adc['net'],adc['layer'],adc['points'],adc['name'],adc['width'])]
    pp={q['key']:q for q in pads};pc=[padcheck(q,g.entry(q),objects)for q in pads];ac=routecheck(adc,objects)
    row=dict(R43=old['R43'],pad_checks=pc,actual_ADC_route=adc,ADC_route_check=ac);out['rows'].append(row);save()
    if not all(q['passed']for q in pc)or not ac['passed']:row['terminal_reason']='Previously proved R43 fails complete BOOT source rebind';save();continue
    graph=gr.build('ADC_DIV_MID',objects);starts=gr.terminals(graph,pp['R43.2']['xy'],('B.Cu',));reach=set(starts);pending=list(starts)
    while pending:
        i=pending.pop()
        for j,w,e in graph['adj'][i]:
            if j not in reach:reach.add(j);pending.append(j)
    row['MID_reachable_components']=[dict(node=i,layer=graph['nodes'][i][0],area_mm2=graph['nodes'][i][1].area,bounds=list(graph['nodes'][i][1].bounds),via_area_mm2=graph['eligible'][i].area if i in graph['eligible']else 0)for i in sorted(reach)]
    row['has_ordinary_transition']=len(reach)>len(starts);row['legal_via_area_mm2']=sum(graph['eligible'][i].area for i in starts if i in graph['eligible']);save()
    opposite=(angle+180)%360;flip=records('R43',xy,opposite);oo=BASE+[g.entry(q)for q in flip];fp=[padcheck(q,g.entry(q),oo)for q in flip];row['opposite_polarity_control']=dict(angle=opposite,pads=flip,pad_checks=fp,ADC_route=None)
    if all(q['passed']for q in fp):
        endpoint=next(q['xy']for q in flip if q['key']=='R43.1');ar=addroute('ADC_BUS','B.Cu',.127,endpoint,anchor,oo,'opposite-R43-ADC-control');row['opposite_polarity_control']['ADC_route']=ar
    save()
out['all_six_original_MID_entries_isolated']=len(out['rows'])==6 and all(not q.get('has_ordinary_transition',True)and q.get('legal_via_area_mm2',1)==0 for q in out['rows'])
out['terminal_reason']='Exact six R43 MID-domain census complete; opposite polarity checked against retained complete ADC tree';save();signal.alarm(0);print('TERMINAL',out['all_six_original_MID_entries_isolated'],out['seconds'],flush=True)
