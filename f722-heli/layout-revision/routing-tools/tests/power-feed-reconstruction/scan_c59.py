"""Read-only orthogonal C59 pose screen against native copper and drill/mask rules."""
import json, math
from pathlib import Path
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely.affinity import rotate, translate
HERE=Path(__file__).resolve().parent; R=HERE.parents[1]
n=json.loads((R/'candidate16/f722-heli.native.json').read_text())
m=json.loads((R/'candidate16/owner-mechanical-geometry.json').read_text())['current']['footprints']
poly=lambda ps:unary_union([Polygon(p['outer'],p.get('holes',[]))for p in ps])
cap=[o for o in n['objects']if o.get('key','').startswith('C59.')]
other=[o for o in n['objects']if not o.get('key','').startswith('C59.')]
ct=poly(m['C59']['courtyards']['B.Cu'])
cts=[(ref,poly(f['courtyards']['B.Cu']))for ref,f in m.items()if ref!='C59'and f['courtyards'].get('B.Cu')]
outline=poly(n['outline_with_npth']['polygons']); options=[]; rejected={}
def bump(reason):rejected[reason]=rejected.get(reason,0)+1
for deg in [0,90,180,270]:
 for xi in range(345,400,2):
  for yi in range(28,92,2):
   x,y=xi/10,yi/10
   def move(g):return translate(rotate(g,-deg,origin=(37.7,3.4)),xoff=x-37.7,yoff=y-3.4)
   courtyard=move(ct)
   if not outline.covers(courtyard):bump('outline');continue
   if any(courtyard.intersection(g).area>1e-12 for ref,g in cts):bump('courtyard');continue
   pads=[];bad=False
   for o in cap:
    copper=move(poly(o['copper']['B.Cu']));mask=move(poly(o['mask']['B.Mask']['polygons']))
    for v in other:
     if v['net']!=o['net'] and 'B.Cu'in v['copper'] and copper.distance(poly(v['copper']['B.Cu']))<.127:bad=True;break
     if v.get('drill') and mask.distance(poly(v['drill']['outside']))<.20:bad=True;break
    if bad:break
    pads.append(dict(key=o['key'],net=o['net'],xy=list(move(Point(o['xy'])).coords)[0]))
   if bad:bump('copper_or_drill');continue
   bynet={p['net']:p for p in pads}
   pd=math.dist(bynet['+5V_BEC']['xy'],[37.45,6.54]);gd=math.dist(bynet['GND']['xy'],[38.45,6.54])
   options.append(dict(xy=[x,y],angle=deg,pads=pads,positive_distance_mm=pd,return_distance_mm=gd))
options.sort(key=lambda q:max(q['positive_distance_mm'],q['return_distance_mm']))
r=dict(status='read_only_pose_screen_only_no_track_restoration_or_native_acceptance',board_sha256=n['board_sha256'],rejections=rejected,options=options[:30])
(HERE/'c59-pose-screen.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
