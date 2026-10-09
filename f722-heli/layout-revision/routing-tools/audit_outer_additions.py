"""Audit add-only outer-layer branches and exact applicability of a power baseline."""
import argparse,hashlib,json,sys
from pathlib import Path
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'native-tools'))
from check_protection_paths import make_graph
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
poly=lambda ps:unary_union([Polygon(p['outer'],p.get('holes',[]))for p in ps])
ap=argparse.ArgumentParser()
for key in ['source','candidate','power-baseline','construction']:ap.add_argument('--'+key,type=Path,required=True)
a=ap.parse_args();A=a.source;B=a.candidate;P=a.power_baseline
before=json.loads((A/'f722-heli.native.json').read_text());after=json.loads((B/'f722-heli.native.json').read_text());base=json.loads((P/'f722-heli.native.json').read_text());power=json.loads((P/'power-audit.json').read_text());q=json.loads(a.construction.read_text());lm=json.loads((B/'f722-heli.logical-route-map.json').read_text())
assert sha(A/'f722-heli.kicad_pcb')==before['board_sha256']==q['source_board_sha256'];assert sha(B/'f722-heli.kicad_pcb')==after['board_sha256']==lm['board_sha256'];assert sha(P/'f722-heli.kicad_pcb')==base['board_sha256']==power['board_sha256']
old={o['uuid']:o for o in before['objects']};now={o['uuid']:o for o in after['objects']};assert all(now.get(u)==o for u,o in old.items());new=[o for u,o in now.items()if u not in old]
assert len(new)==q['new_tracks'] and all(o['kind']=='track'and len(o['copper'])==1 and set(o['copper'])<={'F.Cu','B.Cu'}and o['width']==.127 for o in new)
assert all(before[k]==after[k]==base[k]for k in ['zones','edge_cuts','footprints','copper_layers'])
groups=lambda n,net:sorted([sorted({v['object']['key']for v in g if v['object']['kind']=='pad'})for g in make_graph([o for o in n['objects']if o['net']==net])if any(v['object']['kind']=='pad'for v in g)])
pads={o['key']:o for o in after['objects']if o['kind']=='pad'};rows=[]
for branch in q['branches']:
 net=branch['net'];logical=branch['logical_net'];layer=branch['layer'];points=branch.get('points_mm',branch.get('points'));tracks=[o for o in new if o['net']==net]
 assert len(tracks)==len(points)-1
 expected={tuple(sorted((tuple(x),tuple(y))))for x,y in zip(points,points[1:])}
 assert {tuple(sorted((tuple(t['start']),tuple(t['end']))))for t in tracks}==expected
 assert all(lm['logical_route_map'][t['uuid']]==logical for t in tracks)
 entries=[]
 for key,xy in zip(branch['terminals'],[points[0],points[-1]]):
  metal=poly(pads[key]['inside'][layer]);point=Point(xy);depth=point.distance(metal.boundary);assert metal.covers(point)and depth>=.0685
  entries.append(dict(key=key,point=xy,centerline_inside_depth_mm=depth,full_width_cap_reserve_mm=depth-.0635))
 g0=groups(before,net);g1=groups(after,net);assert len(g1)==len(g0)-1
 assert any(set(branch['terminals'])<=set(g)for g in g1)
 rows.append(dict(net=net,logical_net=logical,track_uuids=[t['uuid']for t in tracks],source_groups=g0,result_groups=g1,endpoints=entries))
domains={}
for net in power['nets']:
 x=[o for o in base['objects']if o['net']==net];y=[o for o in after['objects']if o['net']==net];assert x==y
 zones=[z for z in base['zones']if z['net']==net]
 domains[net]=dict(object_count=len(x),zone_count=len(zones),identical_native_domain_sha256=hashlib.sha256(json.dumps(dict(objects=x,zones=zones),sort_keys=True,separators=(',',':')).encode()).hexdigest())
assert [o for o in base['objects']if o.get('drill')]==[o for o in after['objects']if o.get('drill')]
paired={}
for p in sorted(P.rglob('*')):
 if not p.is_file()or not(p.suffix in ['.kicad_sch','.kicad_pro','.kicad_dru','.kicad_mod','.kicad_sym']or p.name in ['parts.json','fp-lib-table','sym-lib-table']):continue
 dest=B/p.relative_to(P);assert dest.is_file()and sha(dest)==sha(p);paired[str(p.relative_to(P))]=sha(p)
r=dict(passed=True,source_board_sha256=before['board_sha256'],board_sha256=after['board_sha256'],power_baseline_board_sha256=base['board_sha256'],source_native_sha256=sha(A/'f722-heli.native.json'),native_sha256=sha(B/'f722-heli.native.json'),power_baseline_native_sha256=sha(P/'f722-heli.native.json'),construction_sha256=sha(a.construction),audit_source_sha256=sha(Path(__file__)),source_objects_retained_exact=len(old),new_tracks=len(new),new_vias=0,all_footprints_poses_saved_zones_drills_and_power_domains_exact=True,power_domains=domains,paired_circuit_hashes=paired,branch_results=rows,power_applicability='Exact power-baseline conductive domains, pads, drills, saved fills, component poses and paired circuits retained. Baseline numerical applicability is conditional on complete job/contact/material binding and its actual numerical result. This receipt is neither a new solve nor a power pass.')
(B/'unchanged-power-reference.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in ['power_domains','paired_circuit_hashes','branch_results']}))
