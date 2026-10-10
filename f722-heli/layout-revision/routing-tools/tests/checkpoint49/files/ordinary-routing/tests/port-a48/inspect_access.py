import json,pathlib,sys
import native_geometry as m
# Exact candidate48 source; no peer route mutations are adopted.
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
