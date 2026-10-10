"""Seal and simultaneously screen the complete small GREEN native transaction."""
import json,time,signal,math
import composite54_small_GREEN_actual as g
from shapely.geometry import Point,LineString
START=time.monotonic();signal.alarm(65);s=g.s
MID=g.load('tests/joint-flash-group/GREEN-small-MID-R44-flip54.json');assert MID['complete']
WP=g.load('tests/joint-flash-group/GREEN-small-actual-MID-WP54.json')['actual_pairs'][1];assert WP['complete']
M=MID['actual_pairs'][0];assert M['complete']
R44=g.load('tests/joint-flash-group/GREEN-small-R44-local-transaction54-v1.json')
remove=set(g.remove)|{o['uuid']for o in MID['R44_additional_removed_records']}
routes=[]
for i,r in enumerate(g.SMALL_ROUTES+WP['routes']+M['routes']+[MID['R44_ground_route']]):
 routes.append(dict(name='small-complete-route-'+str(i),net=r['net'],layer=r['layer'],width=r.get('width',r.get('width_mm')),points=r['points']))
vias=[]
for i,v in enumerate(g.SMALL_VIAS+WP['vias']+M['vias']+[MID['R44_ground_via']]):
 vias.append(dict(name='small-complete-via-'+str(i),net=v['net'],xy=v['xy'],diameter_mm=.45,drill_mm=.20,tented_both_faces=True))
for o in g.DSM_SMALL['added_native_shaped_records']:
 if o['kind']=='track':routes.append(dict(name='small-DSM-native-'+o['uuid'],net=o['net'],layer=next(iter(o['copper'])),width=o['width'],points=[o['start'],o['end']]))
 elif o['kind']=='via':vias.append(dict(name='small-DSM-native-'+o['uuid'],net=o['net'],xy=o['xy'],diameter_mm=o['width'],drill_mm=.20,tented_both_faces=True))
assert len({(v['net'],tuple(v['xy']))for v in vias})==len(vias)
pads=MID['R44_transformed_pads'];base=[g.entry(o)for o in g.N['objects']if o['uuid']not in remove and o.get('ref')!='R44']+[g.entry(o)for o in pads]
for r in routes:base.append(g.track(r['net'],r['layer'],r['points'],r['name'],r['width']))
for v in vias:base.append(g.via(v['net'],v['xy'],v['name']))
s.OBJECTS=base
out=dict(schema='f722-small-complete-GREEN-native-proposal54/v1',source_board_sha256=g.N['board_sha256'],source_native_sha256=g.sha(g.R/'candidate54/f722-heli.native.json'),removed_source_records=[g.by[u]for u in sorted(remove)],routes=routes,vias=vias,footprint_transforms=[MID['R44_footprint_transform']],transformed_pad_records=pads,checks=[],complete_all_donor_geometry=False,native_candidate=False)
files=['composite54_small_GREEN_actual.py','GREEN-native-four-support-branches54.json','GREEN-small-actual-MID-WP54.json','GREEN-small-MID-R44-flip54.json','GREEN-small-R44-local-transaction54-v1.json','GREEN-D1-native-flash-approach54.json','GREEN-mixed-south54.json']
out['bindings']={str('tests/joint-flash-group/'+p):g.sha(g.H/p)for p in files}
out['bindings'].update({p:g.sha(g.R/p)for p in ['tests/boot-red52/DSM-complete-current-context-witness54-v3.json','tests/portc51/A-RX-transition-south-centered54.json']})
def save():out['seconds']=time.monotonic()-START;(g.H/'small-GREEN-complete-proposal54.json').write_text(json.dumps(out,indent=2)+'\n')
cache={}
for r in routes:
 s.HALF=r['width']/2;key=(r['net'],r['layer'],r['width'])
 if key not in cache:cache[key]=s.obstacles(r['net'],r['layer'])[0]
 ch=s.check(LineString(r['points']),cache[key],True);out['checks'].append(dict(kind='route',name=r['name'],net=r['net'],passed=ch[0]['pass_with_polygon_error'],nearest=ch[:4],failures=[c for c in ch if not c['pass_with_polygon_error']]));r['length_mm']=LineString(r['points']).length;save()
for v in vias:
 s.HALF=.0635;s.OBJECTS=[r for r in base if r[0]['uuid']!=v['name']]
 ch=s.check(Point(v['xy']),s.obstacles(v['net'],'F.Cu')[1],True);out['checks'].append(dict(kind='via',name=v['name'],net=v['net'],passed=ch[0]['pass_with_polygon_error'],nearest=ch[:4],failures=[c for c in ch if not c['pass_with_polygon_error']]));save()
s.OBJECTS=base
out['complete_all_donor_geometry']=all(c['passed']for c in out['checks']);out['route_lengths_by_net_mm']={net:sum(r['length_mm']for r in routes if r['net']==net)for net in sorted({r['net']for r in routes})}
out['unchanged_scope']='All source54 objects and footprints remain exact except the75 named copper removals, complete added routes/vias and R44 same-envelope180-degree rotation. Existing C and ordinary MCU/servo/RPM/clock/IMU/USB paths retained. No new plane signal.'
out['pending']='Native construction, fresh refill/DRC/source comparisons, all changed actual pad groups/entries/cuts, all retained signal return changes, analog/filter/flash-support/PC14 loading review and numerical power before electrical acceptance.';save();print('TERMINAL',out['complete_all_donor_geometry'],len(remove),len(routes),len(vias),out['seconds'],flush=True)
if not out['complete_all_donor_geometry']:
 for c in out['checks']:
  if not c['passed']:print('FAIL',c['name'],[(x['object'],x['net'],x['extra_clearance_mm'])for x in c['failures']],flush=True)
