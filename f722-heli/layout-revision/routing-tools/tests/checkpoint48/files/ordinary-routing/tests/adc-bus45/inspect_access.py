import json,pathlib,sys
import native_geometry as m
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
HERE=pathlib.Path(__file__).resolve().parent
KEY={o['key']:o for o in m.N['objects']if o['kind']=='pad'}
def obs(net,layer):
 t,v,s=m.obstacles(net,layer)
 for o,c,mask,d in m.OBJECTS:
  if d is not None and not o.get('npth') and o['net']!=net:
   t.append(dict(object=o.get('key',o['uuid']),uuid=o['uuid'],net=o['net'],kind=o['kind'],category='foreign_drill_to_track_copper',layers=o.get('barrel_layers',[]),required_physical_gap_mm=.20,moving_radius_mm=m.HALF,required_center_distance_mm=.20+m.HALF,geometry=d))
 return t,v,s
def solid(obs,bounds=None):
 if bounds:
  region=box(*bounds).buffer(.6);obs=[o for o in obs if o['geometry'].intersects(region)]
 return unary_union([o['geometry'].buffer(o['required_center_distance_mm']+.0001,quad_segs=16) for o in obs])
def parts(g):return list(g.geoms)if hasattr(g,'geoms')else[g]
if __name__=='__main__':
 net='ADC_BUS';t,v,s=obs(net,'B.Cu');vb=solid(v);blocks={l:solid(obs(net,l)[0])for l in ['F.Cu','B.Cu','In2.Cu','In3.Cu']};out={}
 for key in ['U1.10','R42.2','C31.1']:
  o=KEY[key];p=Point(o['xy']);layer=list(o['copper'])[0];free=m.OUTLINE.difference(blocks[layer]);comp=next((g for g in parts(free)if g.covers(p)),None);choices=[]
  if comp is not None:
   for g in parts(comp.difference(vb)):
    if g.is_empty or g.area<1e-6:continue
    inside=g.buffer(-.003);q=nearest_points(p,inside if not inside.is_empty else g)[1];choices.append({'xy':list(q.coords[0]),'area':g.area,'bounds':g.bounds,'distance':p.distance(q)})
   choices.sort(key=lambda z:z['distance'])
  out[key]={'xy':o['xy'],'layer':layer,'free_component_area':comp.area if comp is not None else None,'bounds':comp.bounds if comp is not None else None,'legal_via_regions':choices[:30]};print(key,json.dumps(out[key]),flush=True)
 (HERE/'regions.json').write_text(json.dumps(out,indent=2)+'\n')
 for o in m.N['objects']:
  if o['net']==net:print({k:o[k]for k in ['uuid','kind','key','net','xy','start','end','layer','width']if k in o})
