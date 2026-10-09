import native_geometry as s
from shapely.geometry import Point,LineString
import itertools,json

def short(o):return {k:o[k] for k in ['key','uuid','net','xy']}
for net in ['BARO_SCL','BARO_SDA','ADC_BUS']:
 pads=[o for o,_,_,_ in s.OBJECTS if o['net']==net and o['kind']=='pad']
 print('\nNET',net,flush=True)
 for a,b in itertools.combinations(pads,2):
  layers=set(a['copper'])&set(b['copper'])
  print('pair',a['key'],b['key'],'center gap',Point(a['xy']).distance(Point(b['xy'])),'layers',layers,flush=True)
  for layer in layers:
   t,_,_=s.obstacles(net,layer)
   paths=[]
   for p in s.paths2(tuple(a['xy']),tuple(b['xy'])):
    g=LineString(p);checks=s.check(g,t)
    paths.append({'points_mm':p,'length':g.length,'min':checks[0]['extra_clearance_mm'],'nearest':checks[:5]})
   paths.sort(key=lambda p:(-p['min'],p['length']))
   print(json.dumps(paths[:2]),flush=True)
