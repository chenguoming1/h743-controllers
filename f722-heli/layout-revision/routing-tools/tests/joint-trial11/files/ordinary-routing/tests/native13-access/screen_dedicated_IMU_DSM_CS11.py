"""One complete, source-bound dedicated IMU/DSM/CS transition exchange."""
import hashlib,json,signal,time
from pathlib import Path
import composite_native11_complete_BOOT as c
from shapely.geometry import LineString,Point,Polygon,box
from shapely.ops import unary_union
START=time.monotonic();s=c.s;OUT=c.H/'dedicated-IMU-DSM-CS-finite11.json';assert not OUT.exists()
DSM_IDS={'164b4bba-fddc-5419-9d77-77c787d6a0a3','9efd055c-8c4d-5a8c-b0c3-cbb67414ba8d','afb269fa-2b2c-5a59-bb68-c7240506828e'}
PRIVATE={'caps-right-U2-7-shared-ground','caps-right-IMU-return-exchange-CS','caps-right-CS-route-1','caps-right-CS-route-2'}
ids={q[0]['uuid']for q in c.BASE};assert DSM_IDS|PRIVATE <= ids
removed=[q[0]for q in c.BASE if q[0]['uuid']in DSM_IDS]
for o in removed:assert c.physical(o)==c.physical(c.by[o['uuid']])
base=[q for q in c.BASE if q[0]['uuid']not in DSM_IDS|PRIVATE]
GV=[23.70,13.36];CV=[24.29,13.36];DV=[24.88,13.30]
oldcs={r['layer']:r for r in c.CS_INNER}
routes=[
 dict(name='dedicated-U2-7-outward-return',net='GND',layer='F.Cu',width=.254,points=[c.one_pad('U2.7')['xy'],[23.709999,13.12],GV]),
 dict(name='dedicated-exchange-DSM-B',net='DSM_RX_MCU',layer='B.Cu',width=.127,points=[[24.9,14.89055],DV]),
 dict(name='dedicated-exchange-DSM-In2',net='DSM_RX_MCU',layer='In2.Cu',width=.127,points=[[25.567515,13.581606],DV]),
 dict(name='dedicated-exchange-CS-In3',net='FLASH_CS',layer='In3.Cu',width=.127,points=[oldcs['In3.Cu']['points'][0],CV]),
 dict(name='dedicated-exchange-CS-In2',net='FLASH_CS',layer='In2.Cu',width=.127,points=[CV]+oldcs['In2.Cu']['points'][1:])]
vias=[dict(name='dedicated-U2-7-ground-via',net='GND',xy=GV,diameter_mm=.45,drill_mm=.20),dict(name='dedicated-exchange-CS-via',net='FLASH_CS',xy=CV,diameter_mm=.45,drill_mm=.20),dict(name='dedicated-exchange-DSM-via',net='DSM_RX_MCU',xy=DV,diameter_mm=.45,drill_mm=.20)]
for r in routes:r['length_mm']=LineString(r['points']).length
objects=base+[c.track(r['net'],r['layer'],r['points'],r['name'],r['width'])for r in routes]+[c.via(v['net'],v['xy'],v['name'])for v in vias]
out=dict(schema='f722-dedicated-IMU-DSM-CS-finite/v1',source=c.binding(),exact_DSM_removed_records=removed,removed_private_names=sorted(PRIVATE),routes=routes,vias=vias,
   route_checks=[],via_checks=[],selected=False,native_candidate=False,full_width_peer_checks_pending=True,
   inherited_drill_guidance_departure='All proposed barrels preserve existing .45/.20 process; .20 mm is below literal >8 mil vendor guidance. No drill-rule relaxation or guidance equivalence is claimed.',
   complete_BOOT_C_TX_WP_held=True,fresh_IMU_ground_return_reference_AC_power_required=True)
def save(reason=None):
 if reason:out['terminal_reason']=reason
 out['seconds']=time.monotonic()-START;out['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();OUT.write_text(json.dumps(out,indent=2)+'\n')
def stop(reason):
 save(reason);print('TERMINAL',out.get('complete_finite_pass',False),reason,out['seconds'],flush=True);raise SystemExit(0)
signal.signal(signal.SIGALRM,lambda a,b:stop('12-second cap, only saved complete checks count'));signal.alarm(12)
for r in routes:
 s.OBJECTS=[q for q in objects if q[0]['uuid']!=r['name']];s.HALF=r['width']/2
 ch=s.check(LineString(r['points']),s.obstacles(r['net'],r['layer'])[0],True)
 out['route_checks'].append(dict(name=r['name'],passed=all(q['pass_with_polygon_error']for q in ch),nearest=ch[:6],failures=[q for q in ch if not q['pass_with_polygon_error']]))
 save()
for v in vias:
 s.OBJECTS=[q for q in objects if q[0]['uuid']!=v['name']];s.HALF=.0635
 ch=s.check(Point(v['xy']),s.obstacles(v['net'],'B.Cu')[1],True)
 out['via_checks'].append(dict(name=v['name'],passed=all(q['pass_with_polygon_error']for q in ch),nearest=ch[:6],failures=[q for q in ch if not q['pass_with_polygon_error']]))
 save()
def contact_rows(items,others):
 rows=[]
 for o,co,_,_ in items:
  for x,xc,_,_ in others:
   if o['uuid']==x['uuid']or o['net']!=x['net']:continue
   common=[l for l in co if l in xc and co[l].intersects(xc[l])]
   if common:rows.append(dict(a=o['uuid'],b=x['uuid'],key=x.get('key'),layers=common,areas_mm2={l:co[l].intersection(xc[l]).area for l in common}))
 return rows
out['DSM_removed_external_contacts']=contact_rows([q for q in c.BASE if q[0]['uuid']in DSM_IDS],base)
newids={r['name']for r in routes}|{v['name']for v in vias}
out['new_same_net_contacts']=contact_rows([q for q in objects if q[0]['uuid']in newids],objects)
# Full actual pad partitions, with same-net contact and layer continuity, before and after.
def partitions(net,items):
 a=[q for q in items if q[0]['net']==net];parent=list(range(len(a)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for i,(o,co,_,_)in enumerate(a):
  for j in range(i):
   if any(l in a[j][1]and co[l].intersects(a[j][1][l])for l in co):parent[find(i)]=find(j)
 groups={}
 for i,(o,co,_,_)in enumerate(a):
  if o.get('key'):groups.setdefault(find(i),[]).append(o['key'])
 return sorted(sorted(q)for q in groups.values())
out['actual_terminal_partitions']={net:dict(before=partitions(net,c.BASE),after=partitions(net,objects))for net in ['DSM_RX_MCU','FLASH_CS','BOOT0','PORT_C_TX_EXT','FLASH_WP_N']}
out['actual_terminal_partitions_preserved']=all(d['before']==d['after']for d in out['actual_terminal_partitions'].values())
ground=next(q for q in objects if q[0]['uuid']==routes[0]['name'])[1]['F.Cu']
body=Polygon([(21.709999,10.975),(21.709999,12.85),(24.709999,12.85),(24.709999,10.35),(22.334999,10.35)])
pad=c.entry(c.one_pad('U2.7'))[1]['F.Cu'];inside=ground.intersection(body).difference(pad)
normal_strip=box(23.709999-.1271,12.5125,23.709999+.1271,12.85)
out['mounting_body_projection']=dict(body_copper_outside_actual_pad_area_mm2=inside.area,lateral_copper_outside_straight_outward_strip_mm2=inside.difference(normal_strip).area,straight_centerline_to_y=13.12,body_south_y=12.85)
gcontacts=[x for x in out['new_same_net_contacts']if x['a']==routes[0]['name']]
out['dedicated_U2_7_contact_pass']={q['b']for q in gcontacts}<={c.one_pad('U2.7')['uuid'],vias[0]['name']}
out['retained_U2_6_exact_objects']=[c.by[u]for u in ['23f2b322-6468-4bbf-b0a8-6d4b51e76bbf','a4901cd4-da0d-44c6-8240-3a96cda6c6a9']]
out['complete_finite_pass']=all(q['passed']for k in ['route_checks','via_checks']for q in out[k])and out['actual_terminal_partitions_preserved']and out['dedicated_U2_7_contact_pass']
stop('Single complete finite transition exchange tested; exact nominal margins and any blockers preserved')
