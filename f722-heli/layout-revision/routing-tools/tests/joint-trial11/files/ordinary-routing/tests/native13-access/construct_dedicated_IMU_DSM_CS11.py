"""Complete the single remaining CS In3 lead with dedicated IMU returns held."""
import hashlib,json,signal,time,sys
from pathlib import Path
import composite_native11_complete_BOOT as c
import route_native11 as rr
from shapely.geometry import Point,LineString,Polygon,box
START=time.monotonic();s=c.s
P=c.H/'dedicated-IMU-DSM-CS-finite11.json';D=json.loads(P.read_text());assert D['source']==c.binding()
OUT=c.H/'dedicated-IMU-DSM-CS-complete11.json';assert not OUT.exists()
assert len([q for q in D['route_checks']if not q['passed']])==1
assert all(q['passed']for q in D['via_checks'])and D['dedicated_U2_7_contact_pass']and D['actual_terminal_partitions_preserved']
cut={q['uuid']for q in D['exact_DSM_removed_records']};private=set(D['removed_private_names'])
base=[q for q in c.BASE if q[0]['uuid']not in cut|private]
routes=[r for r in D['routes']if r['name']!='dedicated-exchange-CS-In3'];vias=D['vias']
objects=base+[c.track(r['net'],r['layer'],r['points'],r['name'],r['width'])for r in routes]+[c.via(v['net'],v['xy'],v['name'])for v in vias]
a=[25.266112,10.724566];b=next(v['xy']for v in vias if v['net']=='FLASH_CS')
out=dict(schema='f722-dedicated-IMU-DSM-CS-complete/v1',source=c.binding(),finite_predecessor=dict(file=str(P.relative_to(c.ROOT)),sha256=hashlib.sha256(P.read_bytes()).hexdigest()),
 removed_native_records=D['exact_DSM_removed_records'],removed_private_names=D['removed_private_names'],routes=routes,vias=vias,complete=False,selected=False,native_candidate=False,
 actual_U2_6_return=D['retained_U2_6_exact_objects'],mounting_body_projection=D['mounting_body_projection'],inherited_drill_guidance_departure=D['inherited_drill_guidance_departure'],fresh_return_reference_AC_power_required=True)
out['imported_recipe_hashes']={str(Path(m.__file__).resolve().relative_to(c.ROOT)):hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in list(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).is_file() and Path(m.__file__).resolve().is_relative_to(c.ROOT) and Path(m.__file__).suffix=='.py'}
def save(reason=None):
 if reason:out['terminal_reason']=reason
 out['seconds']=time.monotonic()-START;out['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();OUT.write_text(json.dumps(out,indent=2)+'\n')
def stop(reason):
 save(reason);print('TERMINAL',out['complete'],reason,out['seconds'],flush=True);raise SystemExit(0)
signal.signal(signal.SIGALRM,lambda a,b:stop('25-second construction cap; incomplete stages retained'));signal.alarm(25)
s.OBJECTS=objects;s.HALF=.0635
pts=[a,[24.6,11.93],b];ch=s.check(LineString(pts),s.obstacles('FLASH_CS','In3.Cu')[0],True)
out['named_bend_check']=dict(points=pts,passed=all(q['pass_with_polygon_error']for q in ch),nearest=ch[:6],failures=[q for q in ch if not q['pass_with_polygon_error']]);save()
if not out['named_bend_check']['passed']:
 f,obs,_=rr.domain('FLASH_CS','In3.Cu',objects=objects);comp=rr.component(f,a)
 out['component']=dict(area_mm2=None if comp is None else comp.area,target_reachable=comp is not None and comp.covers(Point(b)));save()
 if not out['component']['target_reachable']:stop('Exact remaining CS In3 endpoints are disconnected')
 pts=rr.route(comp,a,b,START+20)
 if pts is None:stop('No complete CDT CS path saved inside deadline')
r=dict(name='dedicated-exchange-CS-In3',net='FLASH_CS',layer='In3.Cu',width=.127,points=pts,length_mm=LineString(pts).length)
routes.append(r);objects.append(c.track(r['net'],r['layer'],r['points'],r['name'],r['width']))
out['route_checks']=[];out['via_checks']=[]
for r in routes:
 s.OBJECTS=[q for q in objects if q[0]['uuid']!=r['name']];s.HALF=r['width']/2;ch=s.check(LineString(r['points']),s.obstacles(r['net'],r['layer'])[0],True)
 out['route_checks'].append(dict(name=r['name'],width_mm=r['width'],passed=all(q['pass_with_polygon_error']for q in ch),nearest=ch[:5],failures=[q for q in ch if not q['pass_with_polygon_error']]))
 save()
for v in vias:
 s.OBJECTS=[q for q in objects if q[0]['uuid']!=v['name']];s.HALF=.0635;ch=s.check(Point(v['xy']),s.obstacles(v['net'],'B.Cu')[1],True)
 out['via_checks'].append(dict(name=v['name'],passed=all(q['pass_with_polygon_error']for q in ch),nearest=ch[:5],failures=[q for q in ch if not q['pass_with_polygon_error']]))
 save()
def partitions(net,items):
 a=[q for q in items if q[0]['net']==net];parent=list(range(len(a)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 edges=[]
 for i,(o,co,_,_)in enumerate(a):
  for j in range(i):
   layers=[l for l in co if l in a[j][1]and co[l].intersects(a[j][1][l])]
   if layers:parent[find(i)]=find(j);edges.append(dict(a=o['uuid'],b=a[j][0]['uuid'],layers=layers))
 groups={}
 for i,(o,co,_,_)in enumerate(a):
  if o.get('key'):groups.setdefault(find(i),[]).append(o['key'])
 return sorted(sorted(q)for q in groups.values()),edges
out['terminal_partitions']={}
for net in ['DSM_RX_MCU','FLASH_CS','BOOT0','PORT_C_TX_EXT','FLASH_WP_N']:
 before,_=partitions(net,c.BASE);after,edges=partitions(net,objects)
 out['terminal_partitions'][net]=dict(before=before,after=after,contact_edges=edges)
out['all_terminal_partitions_preserved']=all(d['before']==d['after']for d in out['terminal_partitions'].values())
groute=next(r for r in routes if r['net']=='GND');gcu=c.track('GND','F.Cu',groute['points'],groute['name'],groute['width'])[1]['F.Cu']
contacts=[dict(uuid=o['uuid'],key=o.get('key'),area_mm2=gcu.intersection(co['F.Cu']).area)for o,co,ma,dr in objects if o['net']=='GND'and o['uuid']!=groute['name']and 'F.Cu'in co and gcu.intersects(co['F.Cu'])]
out['dedicated_return_contacts']=contacts
out['dedicated_return_contact_pass']={q['uuid']for q in contacts}<={c.one_pad('U2.7')['uuid'],'dedicated-U2-7-ground-via'}
out['full_CS_tree_complete']=any({'U1.33','U3.1','R4.2'}<=set(g)for g in out['terminal_partitions']['FLASH_CS']['after'])
out['complete']=all(q['passed']for k in ['route_checks','via_checks']for q in out[k])and out['all_terminal_partitions_preserved']and out['dedicated_return_contact_pass']and out['full_CS_tree_complete']
stop('Complete fixed support/DSM/CS exchange checked against every held actual peer; native and return qualification remain pending')
