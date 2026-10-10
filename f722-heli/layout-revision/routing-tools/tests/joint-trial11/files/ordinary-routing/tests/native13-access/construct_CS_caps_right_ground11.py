"""Actual CS reconstruction with complete right-cap support and reserved SCK barrel."""
import hashlib,json,signal,time
from pathlib import Path
import composite_native11_caps_right as c
import graph_native11 as gg
import route_native11 as rr
from shapely.geometry import Point,LineString

START=time.monotonic();s=c.s;OUT=c.H/'CS-caps-right-IMU-ground-exchange11.json';assert not OUT.exists()
BP=c.H/'MCU-bank-native12-finite-rebind.json';B=json.loads(BP.read_text())
for o in B['removed_source_records']:assert c.physical(c.by[o['uuid']])==c.physical(o)
cuts={o['uuid'] for o in B['removed_source_records']};assert not cuts&c.REMOVED_NATIVE_IDS
SBUS_ID='ad46ffd3-a7c9-55fc-8989-1df897b6cd34'
SBUS_OLD=c.by[SBUS_ID]
assert SBUS_OLD['net']=='SBUS_HV' and SBUS_OLD['width']==.127
assert SBUS_OLD['start']==[22.77,14.1] and SBUS_OLD['end']==[22.69,16.26]
assert set(SBUS_OLD['copper'])=={'In3.Cu'} and SBUS_ID not in c.REMOVED_NATIVE_IDS|cuts
SBUS=dict(name='caps-right-SBUS-HV-complete-bend',net='SBUS_HV',layer='In3.Cu',width=.127,points=[[22.77,14.1],[22.6,14.55],[22.6,15.9],[22.69,16.26]])
SBUS['length_mm']=LineString(SBUS['points']).length
st=c.track(SBUS['net'],SBUS['layer'],SBUS['points'],SBUS['name'],SBUS['width'])
GND_CUTS={'09046fd8-1c6e-4da5-9bef-840de552ae28','33383260-eb77-4f88-a36d-46171e550cd7'}
assert not GND_CUTS & (cuts|c.REMOVED_NATIVE_IDS)
assert c.by['09046fd8-1c6e-4da5-9bef-840de552ae28']['xy']==[23.71,13.3625]
assert c.one_pad('U2.7')['net']=='GND'
GND=dict(name='caps-right-U2-7-shared-ground',net='GND',layer='F.Cu',width=.25,points=[c.one_pad('U2.7')['xy'],[23.21,13.3625]])
GND['length_mm']=LineString(GND['points']).length
gt=c.track(GND['net'],GND['layer'],GND['points'],GND['name'],GND['width'])
CSV=dict(name='caps-right-IMU-return-exchange-CS',net='FLASH_CS',xy=[23.8,13.35],diameter_mm=.45,drill_mm=.20)
cv=c.via(CSV['net'],CSV['xy'],CSV['name'])
base=[q for q in c.BASE if q[0]['uuid'] not in cuts|{SBUS_ID}|GND_CUTS]+[st,gt,cv]
bt=[c.track(r['net'],r['layer'],r['points'],r['name'],r['width']) for r in B['routes']]
bv=[c.via(v['net'],v['xy'],v['name']) for v in B['vias']]
MID=dict(name='caps-right-reserved-SCK-MID',net='FLASH_SCK',xy=[24.709459,15.296041],diameter_mm=.45,drill_mm=.20)
mv=c.via(MID['net'],MID['xy'],MID['name'])
out=dict(schema='f722-CS-caps-right-IMU-ground-exchange/v1',source=c.binding(),bank_binding=dict(file=str(BP.relative_to(c.ROOT)),sha256=hashlib.sha256(BP.read_bytes()).hexdigest()),
         bank_removed_records=B['removed_source_records'],bank_routes=B['routes'],bank_vias=B['vias'],reserved_SCK_barrel=MID,
         bank_checks=[],before={},after={},routes=[],vias=[],complete=False,selected=False,native_candidate=False,
         all_existing_INT_RPM_DSM_retained=True,full_remaining_functions_and_native_review_pending=True)
def save():
    out.update(seconds=time.monotonic()-START,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    OUT.write_text(json.dumps(out,indent=2)+'\n')
def stop(reason):
    out['terminal_reason']=reason;save();print('TERMINAL',reason,out['seconds'],flush=True);raise SystemExit(0)
signal.signal(signal.SIGALRM,lambda a,b:stop('55-second cap; only completed witnesses are evidence'));signal.alarm(55)
out.update(SBUS_removed_record=SBUS_OLD,SBUS_complete_replacement=SBUS,SBUS_function_restored=False)
out.update(ground_removed_native_records=[c.by[u] for u in sorted(GND_CUTS)],ground_complete_route=GND,ground_replacement_passed=False,
           shared_IMU_return_change='Actual U2.7 joins retained U2.6 ground via23f2b322 at23.21,13.3625. The old right via and its exclusive leaf are removed. Fresh critical reference/return/AC/power review required; no equivalence from connectivity alone.',
           fresh_IMU_return_review_required=True)
s.OBJECTS=[q for q in base if q[0]['uuid']!=GND['name']]+bt+bv+[mv];s.HALF=.125
ch=s.check(LineString(GND['points']),s.obstacles('GND','F.Cu')[0],True)
out['ground_finite_check']=dict(passed=all(x['pass_with_polygon_error'] for x in ch),nearest=ch[:5],failures=[x for x in ch if not x['pass_with_polygon_error']])
out['ground_new_same_net_contacts']=[]
for o,co,ma,dr in s.OBJECTS:
    if o['net']=='GND' and 'F.Cu' in co and gt[1]['F.Cu'].intersects(co['F.Cu']):
        out['ground_new_same_net_contacts'].append({k:o[k] for k in ['uuid','key','ref','kind','xy','start','end','width'] if k in o})
s.OBJECTS=[q for q in base if q[0]['uuid']!=CSV['name']]+bt+bv+[mv];s.HALF=.0635
ch=s.check(Point(CSV['xy']),s.obstacles('FLASH_CS','B.Cu')[1],True)
out['reassigned_CS_via_check']=dict(passed=all(x['pass_with_polygon_error'] for x in ch),nearest=ch[:6],failures=[x for x in ch if not x['pass_with_polygon_error']])
save()
if not out['ground_finite_check']['passed'] or not out['reassigned_CS_via_check']['passed']:
    stop('Complete IMU ground replacement or reassigned CS via fails; no graph run')
expected={'23f2b322-6468-4bbf-b0a8-6d4b51e76bbf','a4901cd4-da0d-44c6-8240-3a96cda6c6a9',c.one_pad('U2.7')['uuid']}
if {o['uuid'] for o in out['ground_new_same_net_contacts']}-expected:
    stop('New ground lead reaches an undeclared shared return; no graph run')
oldvia=c.entry(c.by['09046fd8-1c6e-4da5-9bef-840de552ae28'])
oldleaf=c.entry(c.by['33383260-eb77-4f88-a36d-46171e550cd7'])
out['removed_ground_external_contacts']=[]
for o,co,ma,dr in c.BASE:
    if o['net']!='GND' or o['uuid'] in GND_CUTS:continue
    layers=[l for l in co if any(l in z[1] and co[l].intersects(z[1][l]) for z in [oldvia,oldleaf])]
    if layers:out['removed_ground_external_contacts'].append(dict(uuid=o['uuid'],key=o.get('key'),layers=layers))
if {o['uuid'] for o in out['removed_ground_external_contacts']}!={c.one_pad('U2.7')['uuid']}:
    stop('Removed ground branch has additional native contacts; no graph run')
out['ground_replacement_passed']=True;out['vias'].append(CSV);save()

s.OBJECTS=[q for q in base if q[0]['uuid']!=SBUS['name']]+bt+bv+[mv];s.HALF=.0635
ch=s.check(LineString(SBUS['points']),s.obstacles('SBUS_HV','In3.Cu')[0],True)
out['SBUS_finite_check']=dict(passed=all(x['pass_with_polygon_error'] for x in ch),nearest=ch[:5],failures=[x for x in ch if not x['pass_with_polygon_error']])
old_geom=c.entry(SBUS_OLD)[1]['In3.Cu'];new_geom=st[1]['In3.Cu']
old_contacts=[];new_contacts=[]
for o,co,ma,dr in s.OBJECTS:
    if o['net']!='SBUS_HV' or 'In3.Cu' not in co:continue
    if old_geom.intersects(co['In3.Cu']):old_contacts.append(o['uuid'])
    if new_geom.intersects(co['In3.Cu']):new_contacts.append(o['uuid'])
out['SBUS_same_net_contact_audit']=dict(old_contacts=old_contacts,new_contacts=new_contacts,lost_contacts=sorted(set(old_contacts)-set(new_contacts)),added_contacts=sorted(set(new_contacts)-set(old_contacts)))
s.OBJECTS=base+bt+bv+[mv]
ch=s.check(Point([23.05,14.8]),s.obstacles('FLASH_CS','B.Cu')[1],True)
out['new_left_site_check']=dict(xy=[23.05,14.8],passed=all(x['pass_with_polygon_error'] for x in ch),nearest=ch[:5],failures=[x for x in ch if not x['pass_with_polygon_error']])
save()
if not out['SBUS_finite_check']['passed'] or out['SBUS_same_net_contact_audit']['lost_contacts']:
    stop('Complete named SBUS bend failed exact geometry or retained contacts; no graph run')
out['SBUS_function_restored']=True

for i,r in enumerate(B['routes']):
    s.OBJECTS=base+[q for j,q in enumerate(bt) if j!=i]+bv+[mv];s.HALF=r['width']/2
    ch=s.check(LineString(r['points']),s.obstacles(r['net'],r['layer'])[0],True)
    out['bank_checks'].append(dict(name=r['name'],passed=all(x['pass_with_polygon_error'] for x in ch),failures=[x for x in ch if not x['pass_with_polygon_error']]))
for i,v in enumerate(B['vias']):
    s.OBJECTS=base+bt+[q for j,q in enumerate(bv) if j!=i]+[mv];s.HALF=.0635
    ch=s.check(Point(v['xy']),s.obstacles(v['net'],'B.Cu')[1],True)
    out['bank_checks'].append(dict(name=v['name'],passed=all(x['pass_with_polygon_error'] for x in ch),failures=[x for x in ch if not x['pass_with_polygon_error']]))
s.OBJECTS=base+bt+bv;s.HALF=.0635
ch=s.check(Point(MID['xy']),s.obstacles(MID['net'],'B.Cu')[1],True)
out['reserved_barrel_check']=dict(passed=all(x['pass_with_polygon_error'] for x in ch),nearest=ch[:6],failures=[x for x in ch if not x['pass_with_polygon_error']]);save()
if not all(x['passed'] for x in out['bank_checks']) or not out['reserved_barrel_check']['passed']:stop('Exact bank or reserved barrel preflight fails; no graph run')
objects=base+bt+bv+[mv]
PAIRS=[('FLASH_CS','U1.33','U3.1'),('FLASH_SCK','U1.34','U3.6'),('FLASH_MISO','U1.35','U3.2'),('FLASH_MOSI','U1.36','U3.5'),('PORT_C_RX_MCU','U1.28','R34.2'),('PORT_C_TX_MCU','U1.29','R35.2')]
def connection(net,a,b):
    gr=gg.build(net,objects);pa=c.one_pad(a);pb=c.one_pad(b);assert pa['net']==pb['net']==net
    return gr,gg.connect(gr,pa['xy'],pb['xy'],tuple(pa['copper']),tuple(pb['copper']))
gr,plan=connection(*PAIRS[0]);out['before']['FLASH_CS']=plan;save();print('CS GRAPH',plan['connected'],flush=True)
if not plan['connected']:
    # Persist the actual terminal components and their legal transition domains.
    out['CS_terminal_domains']={side:[dict(node=i,layer=gr['nodes'][i][0],area_mm2=gr['nodes'][i][1].area,bounds=list(gr['nodes'][i][1].bounds),new_via_area_mm2=gr['eligible'].get(i,Point().buffer(0)).area) for i in plan[side+'_nodes']] for side in ['start','end']}
    def reach(seed):
        seen=set(seed);todo=list(seed)
        while todo:
            i=todo.pop()
            for j,_,_ in gr['adj'][i]:
                if j not in seen:seen.add(j);todo.append(j)
        return seen
    src=reach(plan['start_nodes']);dst=reach(plan['end_nodes'])
    out['CS_reachable_node_counts']=dict(source=len(src),target=len(dst))
    out['existing_GND_barrel_bridge_candidates']=[]
    for o,co,ma,dr in objects:
        if o['kind']!='via' or o['net']!='GND':continue
        x,y=o['xy']
        if not (19<=x<=29 and 10<=y<=19):continue
        near=[i for i,(l,p) in enumerate(gr['nodes']) if p.distance(Point(o['xy']))<=.418]
        left=sorted(set(near)&src);right=sorted(set(near)&dst)
        if not left:continue
        elsewhere=[i for i in near if i not in src and not gr['eligible'].get(i,Point().buffer(0)).is_empty]
        if not right and not elsewhere:continue
        contacts=[]
        for q,qc,qm,qd in objects:
            if q['uuid']==o['uuid'] or q['net']!='GND':continue
            layers=[l for l in co if l in qc and co[l].intersects(qc[l])]
            if layers:contacts.append({k:q[k] for k in ['uuid','key','ref','kind','start','end','xy','width'] if k in q}|dict(layers=layers))
        out['existing_GND_barrel_bridge_candidates'].append(dict(uuid=o['uuid'],xy=o['xy'],source_nodes=left,target_nodes=right,other_nodes_with_legal_transitions=elsewhere,exact_same_net_contacts=contacts))
    gp=c.H/'CS-caps-right-IMU-ground-reachable-components11.json'
    gp.write_text(json.dumps(dict(source_binding=c.binding(),nodes=[dict(id=i,layer=gr['nodes'][i][0],source_reachable=i in src,target_reachable=i in dst,polygon_wkb=gr['nodes'][i][1].wkb_hex) for i in sorted(src|dst)]),indent=2)+'\n')
    out['reachable_components_file']=str(gp.relative_to(c.ROOT));out['reachable_components_sha256']=hashlib.sha256(gp.read_bytes()).hexdigest()
    stop('Actual CS remains disconnected with complete cap support and held MID barrel; exact graph and GND ownership diagnostics retained')
for net,a,b in PAIRS[1:]:
    _,p=connection(net,a,b);out['before'][net]=p;save();print('BEFORE',net,p['connected'],flush=True)
for i,v in enumerate(plan['new_vias']):
    s.OBJECTS=objects;s.HALF=.0635;ch=s.check(Point(v['xy']),s.obstacles('FLASH_CS','B.Cu')[1],True)
    if not all(x['pass_with_polygon_error'] for x in ch):out['via_failure']=ch;stop('CS graph-selected vias are mutually incompatible')
    v.update(net='FLASH_CS',name='caps-right-CS-via-'+str(i),diameter_mm=.45,drill_mm=.20)
    out['vias'].append(v);objects.append(c.via(v['net'],v['xy'],v['name']));save()
for i,leg in enumerate(plan['legs']):
    free,obs,_=rr.domain('FLASH_CS',leg['layer'],objects=objects);comp=rr.component(free,leg['start']);pts=rr.route(comp,leg['start'],leg['end'],START+48)
    if pts is None:stop('CS graph leg did not yield a complete finite route within bound')
    ch=s.check(LineString(pts),obs,True)
    if not all(x['pass_with_polygon_error'] for x in ch):out['route_failure']=ch;stop('CS finite route failed exact peer clearance')
    r=dict(net='FLASH_CS',name='caps-right-CS-route-'+str(i),layer=leg['layer'],width=.127,points=pts,length_mm=LineString(pts).length,nearest=ch[:4])
    out['routes'].append(r);objects.append(c.track(r['net'],r['layer'],pts,r['name']));save();print('ROUTE',r['layer'],r['length_mm'],flush=True)
out['complete']=True;out['total_new_CS_length_mm']=sum(r['length_mm'] for r in out['routes']);save()
for net,a,b in PAIRS[1:]:
    _,p=connection(net,a,b);out['after'][net]=p;save();print('AFTER',net,p['connected'],flush=True)
out['previously_connected_pairs_preserved']=all(not out['before'][n]['connected'] or p['connected'] for n,p in out['after'].items())
stop('Complete actual CS witness and actual flash/C guards recorded; donor completion and native/electrical review remain pending')
