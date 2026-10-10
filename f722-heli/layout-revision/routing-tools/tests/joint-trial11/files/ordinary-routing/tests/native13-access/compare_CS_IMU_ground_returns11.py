"""Complete independent versus shared U2.7 ground return with the CS site held."""
import hashlib,json,math,signal,time
from pathlib import Path
import composite_native11_caps_right as c
import route_native11 as rr
from shapely.geometry import Point,LineString,box
from shapely.ops import polylabel

START=time.monotonic();s=c.s;OUT=c.H/'CS-IMU-ground-return-options11.json';assert not OUT.exists()
B=json.loads((c.H/'MCU-bank-native12-finite-rebind.json').read_text())
bankcuts={o['uuid'] for o in B['removed_source_records']}
for o in B['removed_source_records']:assert c.physical(c.by[o['uuid']])==c.physical(o)
GND_CUTS={'09046fd8-1c6e-4da5-9bef-840de552ae28','33383260-eb77-4f88-a36d-46171e550cd7'}
SBUS_ID='ad46ffd3-a7c9-55fc-8989-1df897b6cd34'
base=[q for q in c.BASE if q[0]['uuid'] not in bankcuts|GND_CUTS|{SBUS_ID}]
base += [c.track(r['net'],r['layer'],r['points'],r['name'],r['width']) for r in B['routes']]
base += [c.via(v['net'],v['xy'],v['name']) for v in B['vias']]
SBUS=dict(name='caps-right-SBUS-HV-complete-bend',net='SBUS_HV',layer='In3.Cu',width=.127,points=[[22.77,14.1],[22.6,14.55],[22.6,15.9],[22.69,16.26]])
base.append(c.track(SBUS['net'],SBUS['layer'],SBUS['points'],SBUS['name'],SBUS['width']))
MID=dict(name='caps-right-reserved-SCK-MID',net='FLASH_SCK',xy=[24.709459,15.296041])
CSV=dict(name='caps-right-IMU-return-exchange-CS',net='FLASH_CS',xy=[23.8,13.35])
base.append(c.via(MID['net'],MID['xy'],MID['name']))
out=dict(schema='f722-CS-IMU-ground-return-options/v1',source=c.binding(),exact_ground_removed_records=[c.by[u] for u in sorted(GND_CUTS)],
         SBUS_replacement=SBUS,bank_source='tests/native13-access/MCU-bank-native12-finite-rebind.json',reserved_MID=MID,reserved_CS=CSV,
         actual_ground_pin=c.one_pad('U2.7'),retained_ground_pin=c.one_pad('U2.6'),dedicated_options=[],selected=False,
         fresh_IMU_reference_return_AC_power_review_required=True,connectivity_does_not_establish_AC_equivalence=True)
def save():
    out.update(seconds=time.monotonic()-START,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());OUT.write_text(json.dumps(out,indent=2)+'\n')
def stop(reason):
    out['terminal_reason']=reason;save();print('TERMINAL',reason,out['seconds'],flush=True);raise SystemExit(0)
signal.signal(signal.SIGALRM,lambda a,b:stop('20-second cap; only completed return paths count'));signal.alarm(20)
s.OBJECTS=base;s.HALF=.0635
ch=s.check(Point(CSV['xy']),s.obstacles('FLASH_CS','B.Cu')[1],True)
out['CS_via_check']=dict(passed=all(q['pass_with_polygon_error'] for q in ch),nearest=ch[:6],failures=[q for q in ch if not q['pass_with_polygon_error']]);save()
if not out['CS_via_check']['passed']:stop('CS transition preflight fails before any ground allocation')
base.append(c.via(CSV['net'],CSV['xy'],CSV['name']))
pin=c.one_pad('U2.7');a=pin['xy'];free,obs,vo=rr.domain('GND','F.Cu',.25,objects=base);comp=rr.component(free,a)
out['pin_component_area_mm2']=None if comp is None else comp.area
if comp is None:stop('Actual U2.7 has no .25 F trace component')
roi=box(22.3,12.5,24.7,14.0)
legal=s.OUTLINE.buffer(-.479-s.ERROR-.0001).difference(rr.expanded(vo))
regions=rr.parts(comp.intersection(legal).intersection(roi))
out['dedicated_via_inventory']=dict(roi=list(roi.bounds),area_mm2=sum(p.area for p in regions),regions=[dict(area_mm2=p.area,bounds=list(p.bounds)) for p in regions]);save()
centers=[]
for p in regions:
    pt=polylabel(p,tolerance=.0001);xy=[round(pt.x,6),round(pt.y,6)];centers.append((math.dist(a,xy),xy,p))
for _,xy,region in sorted(centers,key=lambda q:q[0])[:8]:
    v=dict(name='CS-exchange-U2-7-dedicated-ground-'+str(len(out['dedicated_options'])),net='GND',xy=xy,diameter_mm=.45,drill_mm=.20)
    s.OBJECTS=base;s.HALF=.0635;vc=s.check(Point(xy),s.obstacles('GND','B.Cu')[1],True)
    row=dict(via=v,via_passed=all(q['pass_with_polygon_error'] for q in vc),via_nearest=vc[:4],via_failures=[q for q in vc if not q['pass_with_polygon_error']],complete=False)
    out['dedicated_options'].append(row);save()
    if not row['via_passed']:continue
    objects=base+[c.via('GND',xy,v['name'])]
    f,ob,_=rr.domain('GND','F.Cu',.25,objects=objects);p=rr.component(f,a);pts=rr.route(p,a,xy,START+17)
    if pts is None:row['reason']='No complete finite .25 F path';save();continue
    s.HALF=.125;ch=s.check(LineString(pts),ob,True)
    r=dict(name=v['name']+'-lead',net='GND',layer='F.Cu',width=.25,points=pts,length_mm=LineString(pts).length)
    row.update(route=r,route_passed=all(q['pass_with_polygon_error'] for q in ch),route_nearest=ch[:4],route_failures=[q for q in ch if not q['pass_with_polygon_error']])
    copper=c.track('GND','F.Cu',pts,r['name'],.25)[1]['F.Cu'];contacts=[]
    for o,co,ma,dr in objects:
        if o['net']=='GND' and 'F.Cu' in co and copper.intersects(co['F.Cu']):contacts.append(dict(uuid=o['uuid'],key=o.get('key'),kind=o['kind']))
    row['exact_same_net_contacts']=contacts
    row['dedicated_contact_pass']={q['uuid'] for q in contacts}<={pin['uuid'],v['name']}
    row['complete']=row['route_passed'] and row['dedicated_contact_pass'];save()
    if row['complete']:out['preferred_complete_dedicated_return']=row;break
# Always record the complete shared alternative; this is not an AC acceptance.
r=dict(name='caps-right-U2-7-shared-ground',net='GND',layer='F.Cu',width=.25,points=[a,[23.21,13.3625]])
r['length_mm']=LineString(r['points']).length;s.OBJECTS=base;s.HALF=.125
ch=s.check(LineString(r['points']),s.obstacles('GND','F.Cu')[0],True)
out['shared_option']=dict(route=r,passed=all(q['pass_with_polygon_error'] for q in ch),nearest=ch[:5],failures=[q for q in ch if not q['pass_with_polygon_error']],shared_existing_via='23f2b322-6468-4bbf-b0a8-6d4b51e76bbf',shared_existing_pin='U2.6')
stop('Bounded independent/shared ground alternatives recorded; full CS construction and fresh return qualification remain pending')
