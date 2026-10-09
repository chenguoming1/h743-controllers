"""Retain actual native pad/annulus contact witnesses for changed power copper."""
import argparse, hashlib, json, math
from pathlib import Path
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);a=ap.parse_args()
p=a.candidate/'f722-heli.native.json';n=json.loads(p.read_text());r=json.loads((a.candidate/'power-construction.json').read_text());added={o['uuid'] for o in r['added_objects']};by_id={o['uuid']:o for o in n['objects']}
poly=lambda ps:unary_union([Polygon(x['outer'],x.get('holes',[]))for x in ps])
rows=[]
via_landings=[[33.7,14.666],[36.57,10.1],[39.5,7.875],[32.725,6.4],[18.025,4.7],[30.275,19.3]]
for target in n['objects']:
 if not(target.get('key')in ['U6.8','U7.3','U7.2','U7.7'] or target['kind']=='via' and(target['uuid']in added or target['xy']in via_landings)):continue
 for layer in target['copper']:
  metal=poly(target['inside'][layer]) if target['kind']=='pad' else Point(target['xy']).buffer(target['width_by_layer'][layer]/2-.000001,quad_segs=256)
  if target.get('drill'):metal=metal.difference(poly(target['drill']['outside']))
  matches=[]
  for t in n['objects']:
   if t['uuid']not in added or t['kind']!='track'or t['net']!=target['net']or layer not in t['copper']:continue
   copper=LineString([t['start'],t['end']]).buffer(t['width']/2-.000001,quad_segs=256);overlap=metal.intersection(copper)
   if overlap.area<1e-8:continue
   start,end=t['start'],t['end'];length=math.dist(start,end);dx=(end[0]-start[0])/length;dy=(end[1]-start[1])/length
   line=LineString([start,end]);proj=line.project(Point(target['xy']));lo=max(0,proj-.4);hi=min(length,proj+.4)
   widths=[]
   for w in [.127,.2,.3,.4]:
    longest=0;run=None;best=None
    for k in range(801):
     s=lo+(hi-lo)*k/800;x=start[0]+s*dx;y=start[1]+s*dy;cross=LineString([(x-dy*w/2,y+dx*w/2),(x+dy*w/2,y-dx*w/2)])
     ok=metal.covers(cross)and copper.covers(cross)
     if ok:
      if run is None:run=s
      if s-run>longest:longest=s-run;best=[run,s]
     else:run=None
    widths.append(dict(width_mm=w,positive_entry_interval_mm=longest,track_distance_interval_mm=best))
   matches.append(dict(track_uuid=t['uuid'],track_width_mm=t['width'],overlap_actual_metal_mm2=overlap.area,transverse_witnesses=widths))
  if matches:
   assert any(m['transverse_witnesses'][0]['positive_entry_interval_mm']>.005 for m in matches),(target['uuid'],layer,matches)
   rows.append(dict(target=target.get('key',target['uuid']),uuid=target['uuid'],kind=target['kind'],net=target['net'],layer=layer,drill_subtracted=bool(target.get('drill')),contacts=matches))
assert all(any(row['target']==key for row in rows)for key in ['U6.8','U7.3','U7.2','U7.7'])
assert all(any(row['uuid']==o['uuid'] and row['layer']==layer for row in rows)for o in r['added_objects']if o['kind']=='via'for layer in ['In2.Cu','B.Cu'])
out=dict(passed=True,board_sha256=n['board_sha256'],native_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),method='Native ERROR_INSIDE pad copper; inscribed circular via/round-track polygons from exact native dimensions with a 1 nm inward reserve; subtract native ERROR_OUTSIDE drill void. Positive transverse cross-section along actual new track; no filled-pad-over-drill witness.',minimum_witness_width_mm=.127,minimum_interval_mm=.005,contacts=rows,limitation='Finite physical metal entry only. Wider power tracks may overfill the pad or annulus; transverse widths and overlap are reported rather than claiming the whole track width fits the target. Current crowding/resistance and thermal qualification require the loaded model.')
(a.candidate/'power-endpoints.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(passed=True,contact_count=len(rows),board_sha256=n['board_sha256'])))
