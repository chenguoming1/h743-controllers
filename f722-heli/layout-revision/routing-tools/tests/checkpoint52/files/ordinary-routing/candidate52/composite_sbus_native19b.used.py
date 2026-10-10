"""Full held native19 plus only explicit SBUS changes and future flash reservations."""
import composite_sbus50 as g
import json
s=g.s;H=g.H;R=g.R;bindings={}
def load(path):
 p=R/path;bindings[path]=g.sha(p);return json.loads(p.read_text())
native=load('tests/port-a48/candidate04/f722-heli.native.json')
assert native['board_sha256']=='ea169f907ea6e596f6026364513c15c79a36e21d1597c478232b06e9eaeca406'
lvdrops={o['uuid']for o in native['objects']if o['net']=='SBUS_LV'and o['kind']=='track'and o['uuid']!='187f794e-f820-4425-869b-0ca552a872a2'}
assert len(lvdrops)==5
obj={o['uuid']:g.entry(o)for o in native['objects']if o['uuid']not in lvdrops and o.get('ref')!='R45'}
for o in g.pose['objects']:
 if o.get('ref')=='R45':obj[o['uuid']]=g.entry(o)
s.N=native;s.OUTLINE=s.geom(native['outline_with_npth']['polygons']);s.OBJECTS=list(obj.values())
old48=load('candidate48/f722-heli.native.json');private=load('tests/joint-flash-group/native-stage48/f722-heli.native.json');ids48={o['uuid']for o in old48['objects']};shared=load('tests/port-b48/shared-path-summary.json');excluded=set(shared['removed_ids'])
for o in private['objects']:
 if o['uuid']not in ids48 and o['uuid']not in excluded and o['net']!='+3V3_CORE':s.OBJECTS.append(g.entry(o))
 if o.get('ref')=='R4':s.OBJECTS.append(g.entry(dict(o,uuid='reserved-private-R4-'+o['uuid'])))
mp=load('tests/port-b48/shared-mosi-b.json');g.track('FLASH_MOSI','B.Cu',mp['points'],'reserved-new-MOSI-B')
g.track('LED_RED_K','B.Cu',g.red['path_B_mm'],'reserved-RED-MCU');g.via('LED_RED_K',g.red['via_mm'],'reserved-RED-via')
BASE=list(s.OBJECTS)
