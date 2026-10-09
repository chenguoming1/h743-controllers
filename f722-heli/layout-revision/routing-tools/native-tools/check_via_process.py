"""Read-only drill, tenting and routing-layer screen from native copper geometry.
Requires Shapely 2. This supplements native DRC; it is not a process qualification.
"""
import argparse, hashlib, json, math
from pathlib import Path
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union, polygonize
from shapely.strtree import STRtree

ap=argparse.ArgumentParser();ap.add_argument('--geometry',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
g=json.loads(a.geometry.read_text());eps=1e-8

def poly(rows):
 return unary_union([Polygon(r['outer'],r.get('holes',[])) for r in rows]) if rows else Polygon()

def nearest(rows):
 return min(rows,key=lambda x:x['gap_mm']) if rows else None

objects=g['objects'];vias=[x for x in objects if x['kind']=='via'];pads=[x for x in objects if x['kind']=='pad'];violations=[];mask_rows=[];holes=[];hole_keys={}
for x in pads:
 if x.get('smd'):
  for layer,entry in x['mask'].items():
   shape=poly(entry['polygons'])
   if not shape.is_empty:mask_rows.append((x,layer,shape))
for x in objects:
 if not x.get('drill'):continue
 d=x['drill'];key=(tuple(sorted([tuple(d['start']),tuple(d['end'])])),d['width'])
 if key in hole_keys:
  holes[hole_keys[key]]['objects'].append(x);continue
 hole_keys[key]=len(holes);holes.append({'shape':poly(d['outside']),'objects':[x]})
mask_tree=STRtree([x[2]for x in mask_rows]) if mask_rows else None
hole_tree=STRtree([x['shape']for x in holes]) if holes else None
mask_min=[];hole_min=[];dimensions=[];closest_holes=None
for via in vias:
 h=poly(via['drill']['outside']);diam=via['drill']['width'];widths=via['width_by_layer'];valid=(via['top_layer']=='F.Cu' and via['bottom_layer']=='B.Cu' and diam>=.20-eps and all(w>=.45-eps and (w-diam)/2>=.125-eps for w in widths.values()))
 dimensions.append({'uuid':via['uuid'],'drill_mm':diam,'widths_mm':widths,'passed':valid})
 if not valid:violations.append({'type':'via_dimensions_or_span','uuid':via['uuid']})
 if not all(via.get('tented',{}).get(layer,False) for layer in ['F.Mask','B.Mask']):violations.append({'type':'via_not_tented_both_faces','uuid':via['uuid']})
 if mask_tree:
  i=int(mask_tree.nearest(h));m,layer,shape=mask_rows[i];gap=h.distance(shape);mask_min.append({'via':via['uuid'],'pad':m['key'],'pad_uuid':m['uuid'],'mask_layer':layer,'gap_mm':gap})
  for i in mask_tree.query(h.buffer(.20)):
   m,layer,shape=mask_rows[int(i)];gap=h.distance(shape)
   if gap<.20-eps:violations.append({'type':'drill_to_SMT_mask','via':via['uuid'],'pad':m['key'],'pad_uuid':m['uuid'],'mask_layer':layer,'gap_mm':gap,'required_mm':.20})
for i,row in enumerate(holes):
 for j in range(i+1,len(holes)):
  gap=row['shape'].distance(holes[j]['shape']);record={'first':[x['uuid']for x in row['objects']],'second':[x['uuid']for x in holes[j]['objects']],'gap_mm':gap};
  if closest_holes is None or gap<closest_holes['gap_mm']:closest_holes=record
  if gap<=.25:hole_min.append(record)
  if gap<.25-eps:violations.append(dict(type='drill_to_drill',required_mm=.25,**record))
# All internal traces and zones on the reference layers must be ground. Through
# barrels and through-hole pads are intentionally allowed to cross their antipads.
for x in objects:
 if x['kind'] in ['track','arc'] and x['net']!='GND':
  for layer in x['copper']:
   if layer in ['In1.Cu','In4.Cu']:violations.append({'type':'non_ground_reference_layer_trace','uuid':x['uuid'],'layer':layer,'net':x['net']})
for z in g['zones']:
 if not z['rule'] and z['net']!='GND' and set(z['layers']) & {'In1.Cu','In4.Cu'}:violations.append({'type':'non_ground_reference_layer_zone','uuid':z['uuid'],'net':z['net']})
# Inspect saved fills rather than trusting that a refill command ran.
reference_checks=[];reference_layers=[]
for layer in ['In1.Cu','In4.Cu']:
 fills=[poly(z['filled'].get(layer,[])) for z in g['zones'] if not z['rule'] and z['net']=='GND' and z['filled'].get(layer)]
 if not fills:continue
 reference_layers.append(layer);ground=unary_union(fills)
 if not ground.is_valid:raise ValueError('Invalid saved reference fill; use exact native contour export')
 for item in objects:
  if item['net'] in ['GND',''] or layer not in item['copper']:continue
  copper=poly(item['copper'][layer]);gap=ground.distance(copper);overlap=ground.intersection(copper).area
  row={'layer':layer,'uuid':item['uuid'],'kind':item['kind'],'net':item['net'],'gap_mm':gap,'overlap_mm2':overlap};reference_checks.append(row)
  if gap<.127-eps:violations.append(dict(type='saved_reference_fill_foreign_clearance',required_mm=.127,**row))
lines=[];unsupported=[]
for edge in g['edge_cuts']:
 if edge['shape']=='Line':lines.append(LineString([edge['start'],edge['end']]))
 else:unsupported.append(edge['shape'])
if unsupported:violations.append({'type':'unsupported_board_edge_geometry','shapes':unsupported})
else:
 outlines=list(polygonize(unary_union(lines)))
 if len(outlines)!=1:violations.append({'type':'ambiguous_board_outline','polygon_count':len(outlines)})
 else:
  board=outlines[0];inner=board.buffer(-.254);npth=[row for row in holes if any(x.get('npth')for x in row['objects'])]
  for v in vias:
   copper=unary_union([poly(x)for x in v['copper'].values()])
   if not inner.buffer(eps).covers(copper):violations.append({'type':'via_board_edge_reserve','uuid':v['uuid'],'required_mm':.254})
   for row in npth:
    gap=copper.distance(row['shape'])
    if gap<.254-eps:violations.append({'type':'via_copper_to_NPTH','uuid':v['uuid'],'hole_uuids':[x['uuid']for x in row['objects']],'gap_mm':gap,'required_mm':.254})
result={'board_sha256':g['board_sha256'],'geometry_sha256':hashlib.sha256(a.geometry.read_bytes()).hexdigest(),'native_version':g['native_version'],'via_count':len(vias),'SMT_mask_opening_count':len(mask_rows),'unique_drill_count':len(holes),'minimum_via_drill_to_SMT_mask':nearest(mask_min),'minimum_drill_to_drill':closest_holes,'drill_pairs_within_025_mm':hole_min,'via_dimensions':dimensions,'saved_reference_plane_layers':reference_layers,'saved_reference_foreign_comparisons':len(reference_checks),'minimum_saved_reference_foreign_gap':nearest(reference_checks),'saved_reference_note':'Only present In1/In4 GND fills are checked; absent planes remain untested. Intended net assignment must be independently verified by the importer.','violations':violations,'passed':not violations,'method':'Conservative native ERROR_OUTSIDE copper/mask/drill polygons; no same-net SMT-mask exemption. Coincident physical drill definitions are deduplicated. Floating-point epsilon is1e-8mm. Native DRC remains required for all copper shorts/clearances.','limits':'No fabrication capability, assembly yield, current capacity, reference continuity, plane completeness or physical qualification is established by this screen.'}
a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ['board_sha256','via_count','unique_drill_count','minimum_via_drill_to_SMT_mask','passed','violations']}));raise SystemExit(0 if result['passed'] else 1)
