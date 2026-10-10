"""Bounded full-outline single-layer witnesses with exact full current reservations."""
import sys,json,pathlib,time,math,hashlib,heapq
H=pathlib.Path(__file__).resolve().parent
import native_geometry_sbus17 as m
sys.modules['native_geometry']=m
import inspect_access as q
import shapely
from shapely.geometry import Point,LineString
from shapely import affinity
R=H.parents[1];bindings={}
def load(p):
 p=R/p;bindings[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return json.load(open(p))
def entry(o):return(o,{l:m.geom(p)for l,p in o['copper'].items()},{l:m.geom(v['polygons'])for l,v in o.get('mask',{}).items()}if o.get('smd')else{},m.geom(o['drill']['outside'])if o.get('drill')else None)
n=load('tests/sbus-nrst49/candidate02/f722-heli.native.json');m.N=n;m.EXPECTED=n['board_sha256'];assert m.EXPECTED=='71d33748909bb960c5829973642272460607d8521831a6212975f7de6790d660';m.OUTLINE=m.geom(n['outline_with_npth']['polygons']);m.OBJECTS=[entry(o)for o in n['objects']]
plan=load('tests/servo48/servo1-complete17-proposal.json');removed=set(plan['removed_ids']);byid={o['uuid']:o for o in n['objects']}
assert all(byid[o['uuid']]==o for o in plan['removed_records'])
m.OBJECTS=[r for r in m.OBJECTS if r[0]['uuid']not in removed]
new=[]
for o,c,mask,d in m.OBJECTS:
 if o.get('ref')=='R50':o=dict(o,xy=[o['xy'][0]+.25,o['xy'][1]]);c={l:affinity.translate(g,.25,0)for l,g in c.items()};mask={l:affinity.translate(g,.25,0)for l,g in mask.items()}
 if o.get('key')=='R20.2':o=dict(o,net='SERVO1_SOURCE')
 new.append((o,c,mask,d))
m.OBJECTS=new
ROUTES=[];VIAS=[]
def addroute(r,name='new'):
 r=dict(r);net='SERVO1_SOURCE'if r['net']=='SERVO1_MCU'and r.get('branch')==0 else r['net'];w=r.get('width',.127);g=LineString(r['points']).buffer(w/2/math.cos(math.pi/512),quad_segs=128)
 if net=='SERVO1_SOURCE'and r['layer']=='F.Cu':g=g.difference(m.geom(q.KEY['U12.1']['inside']['F.Cu']))
 m.OBJECTS.append((dict(uuid=f'{name}:track:{len(m.OBJECTS)}',kind='track',net=net,width=w),{r['layer']:g},{},None));ROUTES.append(r)
def addvia(v,name='new'):
 net='SERVO1_SOURCE'if v['net']=='SERVO1_MCU'and v.get('branch')==0 else v['net'];g=Point(v['xy']).buffer(.225/math.cos(math.pi/512),quad_segs=128);d=Point(v['xy']).buffer(.1/math.cos(math.pi/512),quad_segs=128)
 m.OBJECTS.append((dict(uuid=f'{name}:via:{len(m.OBJECTS)}',kind='via',net=net,barrel_layers=m.N['copper_layers']),{l:g for l in m.N['copper_layers']},{},d));VIAS.append(dict(v))
old48=load('candidate48/f722-heli.native.json');private=load('tests/joint-flash-group/native-stage48/f722-heli.native.json');ids48={o['uuid']for o in old48['objects']};shared=load('tests/port-b48/shared-path-summary.json');excluded=set(shared['removed_ids'])
for o in private['objects']:
 if o['uuid']not in ids48 and o['uuid']not in excluded and o['net']!='+3V3_CORE':m.OBJECTS.append(entry(o))
 if o.get('ref')=='R4':m.OBJECTS.append(entry(dict(o,uuid='reserved-private-R4-'+o['uuid'])))
mp=load('tests/port-b48/shared-mosi-b.json');red=load('tests/boot-led48/red-surface-escape49.json');addroute(dict(net='FLASH_MOSI',layer='B.Cu',points=mp['points']),'reserved');addroute(dict(net='LED_RED_K',layer='B.Cu',points=red['path_B_mm']),'reserved');addvia(dict(net='LED_RED_K',xy=red['via_mm']),'reserved')
addvia(dict(net='RPM_MCU',xy=[15.079367,9.594711]),'reserved-RPM')
addvia(dict(net='RPM_MCU',xy=[13.170688,23.010102]),'reserved-RPM')
addroute(dict(net='RPM_MCU',layer='B.Cu',points=[[15.284999,10.05],[15.079367,9.594711]]),'reserved-RPM')
ROUTES=[];VIAS=[]
for r in plan['routes']:addroute(r)
for v in plan['vias']:addvia(v)
