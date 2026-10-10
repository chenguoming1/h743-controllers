import json, math, pathlib, sys
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union, polygonize
from shapely.affinity import translate
from shapely.strtree import STRtree

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=ROOT/'ordinary-routing/candidate44'
n=json.loads((SOURCE/'f722-heli.native.json').read_text())
m=json.loads((SOURCE/'owner-mechanical-geometry.json').read_text())['current']['footprints']
def poly(q):return unary_union([Polygon(v['outer'],v['holes']) for v in q]) if q else Polygon()
def fab(f,side):
 lines=[]; shapes=[]
 for g in f['graphics']:
  if g['layer']!=side[0]+'.Fab':continue
  s=g['shape']; a=g['start']; b=g['end']
  if s=='Line':lines.append(LineString([a,b]))
  elif s=='Rect':shapes.append(box(min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])))
  elif s=='Circle':shapes.append(Point(g['center']).buffer(math.dist(g['center'],b),quad_segs=128))
  elif s=='Polygon':shapes.append(poly(g['polygons']))
  else:raise ValueError(s)
 shapes.extend(polygonize(unary_union(lines)));return unary_union(shapes)
objects={o['uuid']:o for o in n['objects']}
holes=[]
for o in n['objects']:
 if o.get('drill'):holes.append((o,poly(o['drill']['outside'])))
def init(ref,side_override=None):
 global tp,net,side,xy,copper,land_template,ct,mask,ctree,mech,mtree,htree
 tp=next(o for o in n['objects'] if o.get('ref')==ref and o['kind']=='pad');net=tp['net'];side=next(iter(tp['copper']));xy=tp['xy'];land_template=poly(tp['copper'][side]);ct=poly(m[ref]['courtyards'][side]);mask=poly(tp['mask'][side[0]+'.Mask']['polygons'])
 if side_override:side=side_override
 copper=[]
 for o in n['objects']:
  if o['net']!=net and side in o['copper']:copper.append((o,poly(o['copper'][side])))
 ctree=STRtree([v for o,v in copper]);mech=[]
 for r,f in m.items():
  if r==ref:continue
  body=fab(f,side);lands=unary_union([poly(p['polygons'].get(side,[])) for p in f['pads']]);court=poly(f['courtyards'].get(side,[]));reserve=unary_union([body.buffer(.25 if r in ['J'+str(i) for i in range(2,9)] else .15),lands.buffer(.15 if r in ['J'+str(i) for i in range(2,9)] else .1)])
  mech.append((r,body,lands,court,reserve))
 mtree=STRtree([unary_union([row[1],row[2],row[3],row[4]]).envelope for row in mech])
 htree=STRtree([g for o,g in holes])
def pose(q,explain=False):
 delta=[q[i]-xy[i] for i in range(2)];land=translate(land_template,*delta);court=translate(ct,*delta);ms=translate(mask,*delta);probe=Point(q).buffer(.7,quad_segs=128);viol=[]
 for idx in mtree.query(probe.buffer(.15)):
  r,body,lands,c,rs=mech[int(idx)]
  if court.intersection(c).area>1e-8:viol.append(('court',r))
  if land.buffer(.1).intersection(rs).area>1e-8:viol.append(('reserve',r))
  if not body.is_empty and probe.intersection(body).area>1e-8:viol.append(('probe',r))
  if viol and not explain:return False
 for i in ctree.query(land.buffer(.127)):
  o,g=copper[int(i)];d=land.distance(g)
  if d<.127-1e-8:viol.append(('copper',o.get('key',o['uuid']),d))
  if viol and not explain:return False
 for idx in htree.query(ms.buffer(.2)):
  o,h=holes[int(idx)]
  d=h.distance(ms)
  if d<.20-1e-8:viol.append(('drill_mask',o.get('key',o['uuid']),d))
  if viol and not explain:return False
 if explain:return viol
 return not viol
def route(points,explain=False):
 wire=LineString(points).buffer(.0635,quad_segs=128);viol=[]
 for i in ctree.query(wire.buffer(.127)):
  o,g=copper[int(i)];d=wire.distance(g)
  if d<.127-1e-8:viol.append((o.get('key',o['uuid']),d))
 return viol if explain else not viol
def routes(a,z):
 dx=z[0]-a[0];dy=z[1]-a[1];d=min(abs(dx),abs(dy));sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1
 for pts in [[a,z],[a,[a[0],z[1]],z],[a,[z[0],a[1]],z],[a,[a[0]+sx*d,a[1]+sy*d],z],[a,[z[0]-sx*d,z[1]-sy*d],z]]:
  pts=[p for i,p in enumerate(pts) if i==0 or p!=pts[i-1]]
  if len(pts)>1 and route(pts):yield pts
if __name__=='__main__':
 out={}
 for ref,region,targets in [('TP1',(28.3,30.0,15.7,17.1),[[26.634999,16.55]]),('TP5',(13,19,10,18),[[16.07081,14.32167],[16.47327,14.32167],[15.01263,13.26349],[16.66876,8.74761],[17.12882,8.28755],[17.12882,6.83933]])]:
  init(ref);found=[];clear=[]
  xmin,xmax,ymin,ymax=region
  for ix in range(round(xmin*20),round(xmax*20)+1):
   for iy in range(round(ymin*20),round(ymax*20)+1):
    q=[ix/20,iy/20]
    if not pose(q):continue
    clear.append(q)
    for z in targets:
     for path in routes(q,z):found.append({'xy':q,'points':path,'length':LineString(path).length})
  found.sort(key=lambda x:x['length']);out[ref]={'valid_pose_count':len(clear),'clear_poses':clear,'routes':found[:30]};print(ref,'valid poses',len(clear),'valid routes',len(found),'best',found[:3],flush=True)
 (HERE/'screen.json').write_text(json.dumps(out,indent=2)+'\n')
