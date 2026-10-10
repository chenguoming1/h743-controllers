from pathlib import Path
import sys,json,hashlib
from shapely.geometry import Point,mapping
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'repo/f722-heli/layout-revision/signal-review/native'))
from check_signal_geometry import copper_entries,poly,centerline
from check_critical_reference import ground_geometry,REFERENCE
S=R/'ordinary-routing/candidate53/f722-heli.native.json';D=R/'ordinary-routing/tests/rpm17/candidate01/f722-heli.native.json'
a=json.loads(S.read_text());b=json.loads(D.read_text());old={o['uuid']:o for o in a['objects']};_,_,pa,_=ground_geometry(a,copper_entries(a));_,_,pb,_=ground_geometry(b,copper_entries(b));lost={l:pa[l].difference(pb[l]) for l in pa};nets={o['net'] for o in b['objects']};windows={n:unary_union([Point(v['xy']).buffer(v['width']/2+.127+.01,quad_segs=96) for v in b['objects'] if v['kind']=='via' and v['net']==n]) for n in nets};rows=[]
for o in b['objects']:
 if o['kind'] not in ['track','arc'] or o['uuid'] not in old:continue
 before=old[o['uuid']]
 assert o['copper']==before['copper'] and o['net']==before['net'],o['uuid']
 layer=next(iter(o['copper']));ref=REFERENCE.get(layer)
 if ref not in lost:continue
 width=poly(o['copper'][layer]).intersection(lost[ref]);line=centerline(o).intersection(lost[ref]);outside=width.difference(windows[o['net']]);outside_line=line.difference(windows[o['net']])
 if width.is_empty and line.is_empty:continue
 rows.append({'uuid':o['uuid'],'net':o['net'],'signal_layer':layer,'reference_layer':ref,'newly_missing_width_mm2':width.area,'newly_missing_centerline_mm':line.length,'newly_missing_width_outside_own_windows_mm2':outside.area,'newly_missing_centerline_outside_own_windows_mm':outside_line.length,'width_geometry':mapping(width),'outside_width_geometry':mapping(outside)})
r={'source_board_sha256':a['board_sha256'],'board_sha256':b['board_sha256'],'scope':'Exact saved-plane loss projection against all retained signal/power tracks. No geometric normalization or epsilon. Diagnostic only; does not prove AC return or electrical qualification.','tracks':rows};out=Path(__file__).with_suffix('.json');out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'affected_tracks':len(rows),'outside_window_affected':[{k:v for k,v in x.items() if not k.endswith('geometry')} for x in rows if x['newly_missing_width_outside_own_windows_mm2'] or x['newly_missing_centerline_outside_own_windows_mm']]}))
