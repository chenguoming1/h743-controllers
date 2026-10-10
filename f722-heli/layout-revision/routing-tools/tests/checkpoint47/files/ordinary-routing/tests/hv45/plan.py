import json,math,pathlib,time,sys
import native_geometry as m
import shapely
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
HERE=pathlib.Path(__file__).resolve().parent
RMAP=json.load(open(m.ROOT/'candidate45/f722-heli.logical-route-map.json'))['logical_route_map']
OBJ={o['uuid']:o for o in m.N['objects']};KEY={o['key']:o for o in m.N['objects']if o['kind']=='pad'}

def trace_obs(net,layer,protected):
 t,v,skipped=m.obstacles(net,layer)
 for o,c,mask,d in m.OBJECTS:
  if d is not None and not o.get('npth') and o['net']!=net:
   t.append(dict(object=o.get('key',o['uuid']),uuid=o['uuid'],net=o['net'],kind=o['kind'],category='foreign_drill_to_track_copper',layers=o.get('barrel_layers',[]),required_physical_gap_mm=.20,moving_radius_mm=m.HALF,required_center_distance_mm=.20+m.HALF,geometry=d))
  if o['net']==net and o['kind']!='pad' and layer in c:
   pad=m.geom(KEY[protected]['copper'][layer]) if layer in KEY[protected]['copper']else m.Polygon()
   g=c[layer].difference(pad)
   if not g.is_empty:t.append(dict(object=o['uuid'],uuid=o['uuid'],net=net,kind=o['kind'],category='same_net_other_branch_outside_TVS_pad',layers=[layer],required_physical_gap_mm=.127,moving_radius_mm=m.HALF,required_center_distance_mm=.127+m.HALF,geometry=g))
 return t,v,skipped

def solid(obs,bounds=None):
 if bounds:
  region=box(*bounds).buffer(.6)
  obs=[o for o in obs if o['geometry'].intersects(region)]
 return unary_union([o['geometry'].buffer(o['required_center_distance_mm']+.0001,quad_segs=8) for o in obs])

def pathgood(pts,keepout):
 return not LineString(pts).intersects(keepout)

def run(net,keys):
 pads=[KEY[k]for k in keys];a,b=[o['xy']for o in pads]
 bounds=(min(a[0],b[0])-4,min(a[1],b[1])-4,max(a[0],b[0])+4,max(a[1],b[1])+4)
 obs={l:trace_obs(net,l,keys[1])[0]for l in ['F.Cu','B.Cu','In2.Cu','In3.Cu']}
 blocks={l:solid(obs[l],bounds)for l in obs};_,v,skipped=trace_obs(net,'F.Cu',keys[1]);vb=solid(v,bounds)
 portals=[]
 for xy in [a,b]:
  p=[]
  for ix in range(-20,21):
   for iy in range(-20,21):
    q=[round(xy[0]+ix*.1,6),round(xy[1]+iy*.1,6)]
    if Point(q).intersects(vb):continue
    paths=sorted(m.paths2(xy,q),key=lambda z:LineString(z).length)
    for pts in paths:
     if pathgood(pts,blocks['F.Cu']):
      p.append({'xy':q,'points':pts,'length':LineString(pts).length});break
  p.sort(key=lambda z:z['length']);portals.append(p[:60]);print(net,'portal',xy,len(p),'nearest',p[:3],flush=True)
 for direct in m.paths2(a,b):
  if pathgood(direct,blocks['F.Cu']):return {'net':net,'tracks':[{'layer':'F.Cu','points':direct}],'vias':[]}
 results=[]
 for pa in portals[0]:
  for pb in portals[1]:
   for l in ['In2.Cu','In3.Cu','B.Cu']:
    for pts in m.paths2(pa['xy'],pb['xy']):
     if pathgood(pts,blocks[l]):
      results.append({'net':net,'length':pa['length']+pb['length']+LineString(pts).length,'tracks':[{'layer':'F.Cu','points':pa['points']},{'layer':l,'points':pts},{'layer':'F.Cu','points':list(reversed(pb['points']))}],'vias':[pa['xy'],pb['xy']]});break
   if results:break
  if results:break
 out={'net':net,'source_board_sha256':m.EXPECTED,'portals':portals,'complete_proposals':sorted(results,key=lambda z:z['length'])}
 (HERE/(net+'-plan.json')).write_text(json.dumps(out,indent=2)+'\n')
 print(net,'proposals',out['complete_proposals'][:1],flush=True)
if __name__=='__main__':
 for net,keys in [('RPM_HV',['R25.2','U16.1']),('SBUS_HV',['Q2.3','U16.2'])]:run(net,keys)
