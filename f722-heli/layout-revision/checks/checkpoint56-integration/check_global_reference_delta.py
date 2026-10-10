"""Exact all-retained-track projection against changed physical GND; no repairs."""
from pathlib import Path
import json,hashlib,sys,time
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'repo/f722-heli/layout-revision/signal-review/native'))
from check_signal_geometry import copper_entries,poly,centerline,pieces
from check_critical_reference import ground_geometry,ground_ties,REFERENCE,PLANES
START=time.monotonic();O=R/'ordinary-routing/candidate55';D=R/'ordinary-routing/tests/native13-access/candidate02';S=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((O/'f722-heli.native.json').read_text());new=json.loads((D/'f722-heli.native.json').read_text())
assert old['board_sha256']==sha(O/'f722-heli.kicad_pcb') and new['board_sha256']==sha(D/'f722-heli.kicad_pcb')
a=ground_geometry(old,copper_entries(old));b=ground_geometry(new,copper_entries(new));lost={l:a[2][l].difference(b[2][l])for l in PLANES};gained={l:b[2][l].difference(a[2][l])for l in PLANES};newby={o['uuid']:o for o in new['objects']};rows=[]
for o in old['objects']:
 if o['kind']not in ('track','arc'):continue
 q=newby[o['uuid']];assert o['net']==q['net'] and o['copper']==q['copper']
 for k in ['kind','start','end','mid','width']:assert o.get(k)==q.get(k),(o['uuid'],k)
 l=next(iter(o['copper']));ref=REFERENCE.get(l)
 if ref is None:continue
 line=centerline(o);width=poly(o['copper'][l]);x=lost[ref].intersection(width);y=gained[ref].intersection(width);lc=lost[ref].intersection(line);gc=gained[ref].intersection(line)
 rows.append({'uuid':o['uuid'],'net':o['net'],'layer':l,'reference':ref,'lost_width_area_mm2':x.area,'gained_width_area_mm2':y.area,'lost_centerline_mm':lc.length,'gained_centerline_mm':gc.length,'lost_width_intersection_empty':x.is_empty,'gained_width_intersection_empty':y.is_empty})
oldt,oldr=ground_ties(old,a[1],a[3]);newt,newr=ground_ties(new,b[1],b[3]);assert {x['uuid']for x in oldt}=={x['uuid']for x in newt} and not newr
out={'schema':'f722-all-retained-track-ground-delta/v1','before_board_sha256':old['board_sha256'],'board_sha256':new['board_sha256'],'source_native_sha256':sha(O/'f722-heli.native.json'),'native_sha256':sha(D/'f722-heli.native.json'),'all_retained_track_copper_exact':True,'retained_tracks_inspected':len(rows),'rows':rows,'nonempty_width_intersections':[r for r in rows if not r['lost_width_intersection_empty']or not r['gained_width_intersection_empty']],'ground_ties_both_planes':len(newt),'rejected_ground_ties':len(newr),'planes':{l:{'before_components':len(pieces(a[2][l],'Polygon')),'after_components':len(pieces(b[2][l],'Polygon')),'before_area_mm2':a[2][l].area,'after_area_mm2':b[2][l].area,'lost_area_mm2':lost[l].area,'gained_area_mm2':gained[l].area,'lost_wkb_hex':lost[l].wkb_hex,'gained_wkb_hex':gained[l].wkb_hex}for l in PLANES},'limits':'Actual saved copper minus all physical drill voids. Exact nonzero intersections retained; no geometry repair, snapping or numerical tolerance normalization. This checks geometric change under retained traces, not absolute coverage, current capacity, AC return or physical qualification. New tracks require their separate reference review.','seconds':time.monotonic()-START}
(S/'global-retained-track-reference-delta.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['rows','planes','nonempty_width_intersections','limits']}));print('nonempty',out['nonempty_width_intersections'])
