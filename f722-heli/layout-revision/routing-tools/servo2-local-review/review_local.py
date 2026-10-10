import json,hashlib,math
from pathlib import Path
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
ROOT=Path('ordinary-routing')
n=json.loads((ROOT/'candidate32/f722-heli.native.json').read_text())
m=json.loads((ROOT/'model-candidate31-ready/model.json').read_text())
lm=json.loads((ROOT/'candidate32/f722-heli.logical-route-map.json').read_text())['logical_route_map']
mutable=set(m['mutable_source_ids']);explicit=set(json.loads((ROOT/'model-candidate31-ready/fixed-explicit-native-ids.json').read_text()));ordinary=set(m['ordinary_nets']);region=box(10,9,16,15)
def geom(polys):return unary_union([Polygon(p['outer'],p.get('holes',[])) for p in polys])
def nearby(polys):
 return any(max(x for x,y in p['outer'])>=9.5 and min(x for x,y in p['outer'])<=16.5 and max(y for x,y in p['outer'])>=8.5 and min(y for x,y in p['outer'])<=15.5 for p in polys)
local=[];masks=[];drills=[]
for o in n['objects']:
 for layer,polys in o.get('copper',{}).items():
  if nearby(polys):local.append((o,layer,geom(polys)))
 for layer,md in o.get('mask',{}).items():
  if o.get('smd') and nearby(md['polygons']):masks.append((o,layer,geom(md['polygons'])))
 if o.get('drill') and nearby(o['drill']['outside']):drills.append((o,geom(o['drill']['outside'])))
pad=next(o for o in n['objects'] if o.get('key')=='U12.3');cut=geom(pad['inside']['F.Cu']);
p0=unary_union([g for o,l,g in local if l=='F.Cu' and lm.get(o['uuid'])=='SERVO2_MCU::P0']);p0cut=p0.difference(cut)
def brief(o,l,gap):
 return {**{k:o[k] for k in ['uuid','kind','key','net','xy','start','end','width'] if k in o},'logical_net':lm.get(o['uuid']),'layer':l,'gap':round(gap,7),'mutable_source31':o['uuid'] in mutable,'explicit_fixed_source31':o['uuid'] in explicit,'ordinary_net':o['net'] in ordinary}
def via_check(xy):
 p=Point(xy);circle=p.buffer(.225,resolution=128);drill=p.buffer(.1,resolution=128)
 copper=[brief(o,l,circle.distance(g)) for o,l,g in local if l not in ['In1.Cu','In4.Cu'] and o['net']!='SERVO2_MCU' and circle.distance(g)<.12701]
 mask=[brief(o,l,drill.distance(g)) for o,l,g in masks if drill.distance(g)<.20001]
 dh=[brief(o,'drill',drill.distance(g)) for o,g in drills if drill.distance(g)<.25001]
 return dict(xy=xy,copper=copper,mask=mask,drill=dh)
def trace_check(points):
 g=LineString(points).buffer(.0635,resolution=128);return dict(points=points,foreign=[brief(o,l,g.distance(poly)) for o,l,poly in local if l=='F.Cu' and o['net']!='SERVO2_MCU' and g.distance(poly)<.12701],p0_outside_gap=g.difference(cut).distance(p0cut),start_depth=Point(points[0]).distance(cut.boundary),cut_overlap_area=g.intersection(cut).area)
for xy in [[13.45,10.75],[13.3,10.75],[13.1,10.75],[13.7,10.75],[13.7,12.95],[13.45,12.95],[13.95,12.9],[13.95,11.7]]:
 print('VIA',json.dumps(via_check(xy)))
for points in [[[13.45,11.8875],[13.45,10.75]],[[13.45,11.8875],[13.45,12.95]],[[13.65,12.2],[13.65,12.95]],[[13.45,11.45],[13.3,11.3],[13.3,10.75]],[[13.45,11.8875],[13.95,11.8875]]]:print('TRACE',json.dumps(trace_check(points)))
