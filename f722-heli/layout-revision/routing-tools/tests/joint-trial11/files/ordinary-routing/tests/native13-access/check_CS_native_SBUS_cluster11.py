"""Finite simultaneous CS/native-SBUS/ADC-cluster rebind before B-divider search."""
import ast,hashlib,json,signal,time
from pathlib import Path
import composite_native11_CS_native_SBUS as g
from shapely.geometry import Point,LineString
START=time.monotonic();signal.alarm(12);s=g.s
P=g.ROOT/'tests/boot56/R42-C31-full-supply12757-corrected.json';D=json.loads(P.read_text())
assert D['complete_cluster'] and D['held_BOOT_route']['layer']=='B.Cu'
cuts={q['uuid'] for q in D['removed_native_records']}|{'9e6756f4-4622-4a5f-80e2-4c78e46894ce','d354ba09-c0ed-4352-9f87-8f6fa70ec378'}
for o in D['removed_native_records']:assert g.physical(g.by[o['uuid']])==g.physical(o)
private={'divider-route-0','divider-route-2','divider-via-0'}
objects=[q for q in g.BASE if q[0]['uuid'] not in cuts|private and q[0].get('ref') not in ('R42','C31','R43','R44')]
cp=D['selected']['transformed_pad_records'];cr=D['routes']+D['held_SERVO_routes']+[D['held_BOOT_route']];cv=D['vias']+D['held_SERVO_vias']+[D['held_BOOT_via']]
objects += [g.entry(p) for p in cp]+[g.track(r['net'],r['layer'],r['points'],r['name'],r['width']) for r in cr]+[g.via(v['net'],v['xy'],v['name']) for v in cv]
assert len({q[0]['uuid'] for q in objects})==len(objects)
ids={q[0]['uuid'] for q in objects}
pr=g.PACKET['selected_routes']+[dict(q,name='divider-route-'+str(i)) for i,q in enumerate(g.DIVIDER_ROUTES)]+[g.GREEN['route']]+g.CAP['routes']+g.CS_REQUIRED_ROUTES
pv=g.PACKET['selected_vias']+[dict(q,name='divider-via-'+str(i)) for i,q in enumerate(g.DIVIDER_VIAS)]+g.CS_REQUIRED_VIAS
native=g.by[g.NATIVE_SBUS_ID]
nr=dict(name=native['uuid'],net=native['net'],layer='In3.Cu',width=native['width'],points=[native['start'],native['end']])
routes=list({r['name']:r for r in pr+cr+[nr] if r['name'] in ids}.values());vias=list({v['name']:v for v in pv+cv if v['name'] in ids}.values())
OUT=g.H/'CS-native-SBUS-cluster-rebind11.json';assert not OUT.exists()
out=dict(schema='f722-CS-native-SBUS-cluster-rebind/v1',source=g.binding(),cluster_receipt=dict(file=str(P.relative_to(g.ROOT)),sha256=hashlib.sha256(P.read_bytes()).hexdigest()),
    exact_native_SBUS_record=native,removed_private_bend=g.CS['SBUS_complete_replacement'],route_checks=[],via_checks=[],
    complete_CS_preserved=True,complete_SERVO1_held_unchanged=True,complete_B_divider=False,
    scope='Simultaneous finite CS/support and complete corrected ADC/SERVO1/BOOT-entry cluster. Old F divider explicitly released for pending complete B replacement.',
    future_B_divider_scope=dict(removed_native_records=[g.by[u] for u in sorted(cuts)],removed_private_objects=sorted(private),released_footprints=['R43','R44']),
    native_candidate=False,full_return_reference_power_AC_review_pending=True)
for r in routes:
    s.OBJECTS=objects;s.HALF=r['width']/2;ch=s.check(LineString(r['points']),s.obstacles(r['net'],r['layer'])[0],True)
    out['route_checks'].append(dict(name=r['name'],width_mm=r['width'],passed=all(x['pass_with_polygon_error'] for x in ch),failures=[x for x in ch if not x['pass_with_polygon_error']]))
for v in vias:
    s.OBJECTS=[q for q in objects if q[0]['uuid']!=v['name']];s.HALF=.0635;ch=s.check(Point(v['xy']),s.obstacles(v['net'],'B.Cu')[1],True)
    out['via_checks'].append(dict(name=v['name'],passed=all(x['pass_with_polygon_error'] for x in ch),failures=[x for x in ch if not x['pass_with_polygon_error']]))
out['all_finite_pass']=all(x['passed'] for k in ['route_checks','via_checks'] for x in out[k]);out['seconds']=time.monotonic()-START
out['overlay_sha256']=hashlib.sha256(Path(g.__file__).read_bytes()).hexdigest();out['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
OUT.write_text(json.dumps(out,indent=2)+'\n');print('TERMINAL',out['all_finite_pass'],len(routes),len(vias),out['seconds'],flush=True)
