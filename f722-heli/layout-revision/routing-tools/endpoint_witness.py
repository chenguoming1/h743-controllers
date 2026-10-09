#!/usr/bin/env python3
import json,math,hashlib,argparse
from pathlib import Path
from collections import Counter
from shapely import unary_union
from shapely.geometry import Polygon,LineString,Point,box
ap=argparse.ArgumentParser();ap.add_argument('--native',type=Path,required=True);ap.add_argument('--net',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();n=json.loads(a.native.read_text());obs=[o for o in n['objects']if o['net']==a.net];tracks=[o for o in obs if o['kind']=='track'];pads=[o for o in obs if o['kind']=='pad'];geom=lambda ps:unary_union([Polygon(p['outer'],p.get('holes',[]))for p in ps]);degree=Counter(tuple(o[k])for o in tracks for k in ['start','end']);results=[]
for t in tracks:
 for k,k2 in [('start','end'),('end','start')]:
  xy=t[k]
  if degree[tuple(xy)]!=1:continue
  layer=next(iter(t['copper']));q=t[k2];d=math.dist(xy,q);nx=-(q[1]-xy[1])/d;ny=(q[0]-xy[0])/d;r=t['width']/2;section=LineString([(xy[0]-nx*r,xy[1]-ny*r),(xy[0]+nx*r,xy[1]+ny*r)])
  candidates=[p for p in pads if layer in p['copper']]
  nearest=min(candidates,key=lambda p:geom(p['copper'][layer]).distance(Point(xy))) if candidates else None
  for p in ([] if nearest is None else [nearest]):
   g=geom(p['copper'][layer]);inside=geom(p['inside'][layer]);pt=Point(xy)
   drilled=bool((p.get('drill') or {}).get('outside'));actual=inside.difference(geom(p['drill']['outside'])) if drilled else inside
   entry=LineString([xy,q]).intersection(actual.buffer(-(r+0.000001)))
   full_section=section.difference(actual).length<=1e-8
   entry_pass=entry.length>0 if drilled else inside.contains(pt) and full_section
   results.append({'track_uuid':t['uuid'],'endpoint':xy,'pad_uuid':p['uuid'],'pad':p['key'],'layer':layer,'trace_width_mm':t['width'],'centerline_to_native_pad_gap_mm':inside.distance(pt),'centerline_inside_native_pad':inside.contains(pt),'centerline_depth_inside_native_pad_mm':pt.distance(inside.boundary) if inside.contains(pt) else 0,'cross_section_inside_native_pad_mm':section.intersection(inside).length,'full_width_termination':section.difference(inside).length<=1e-8,'copper_overlap_mm2':geom(t['copper'][layer]).intersection(actual).area,'drill_void_subtracted':drilled,'actual_copper_cross_section_mm':section.intersection(actual).length,'full_width_actual_copper_termination':full_section,'full_width_annular_entry_length_mm':entry.length if drilled else None,'full_width_entry_wkt':entry.wkt,'physical_entry_passed':entry_pass})
report={'board_sha256':n['board_sha256'],'native_sha256':hashlib.sha256(a.native.read_bytes()).hexdigest(),'net':a.net,'passed':len(results)>=2 and all(x['physical_entry_passed']for x in results),'method':'Native ERROR_INSIDE pad copper minus conservative ERROR_OUTSIDE drill void; positive centerline interval in actual copper eroded by half trace width plus 1 nm proves full-width THT entry. SMD termination requires native interior and full transverse section. Nominal geometry only.','audit_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'endpoints':results};a.out.write_text(json.dumps(report,indent=2)+'\n')
draw_layer=next(iter(tracks[0]['copper'])) if tracks else next(iter(pads[0]['copper']));allg=unary_union([geom(o['copper'][draw_layer])for o in obs if draw_layer in o['copper']]);bb=allg.bounds;view=box(bb[0]-.25,bb[1]-.25,bb[2]+.25,bb[3]+.25);xmin,ymin,xmax,ymax=view.bounds
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="800" viewBox="{xmin} {ymin} {xmax-xmin} {ymax-ymin}"><rect x="{xmin}" y="{ymin}" width="{xmax-xmin}" height="{ymax-ymin}" fill="#101722"/>']
for o in n['objects']:
 if draw_layer not in o['copper']:continue
 g=geom(o['copper'][draw_layer]);g=g.difference(geom(o['drill']['outside'])) if (o.get('drill') or {}).get('outside') else g
 if not g.intersects(view):continue
 col='#ffcc5a' if o['net']==a.net and o['kind']=='pad' else '#42c9f4' if o['net']==a.net else '#444d61'
 svg.append(g.intersection(view).svg(scale_factor=.003,fill_color=col).replace('opacity="0.6"','opacity="0.95"'))
for t in tracks:
 svg.append(f'<path d="M{t["start"][0]} {t["start"][1]} L{t["end"][0]} {t["end"][1]}" stroke="#ffffff" stroke-width=".006"/>')
for e in results:
 x,y=e['endpoint'];svg.append(f'<circle cx="{x}" cy="{y}" r=".016" fill="#ffffff"/>');svg.append(f'<text x="{x-.10}" y="{y-.16}" fill="white" font-size=".065">{e["pad"]}: {"PASS" if e["physical_entry_passed"] else "FAIL"} {e["trace_width_mm"]:.3f} mm</text>')
svg.append('</svg>');a.out.with_suffix('.svg').write_text(''.join(svg));print(json.dumps(report))
