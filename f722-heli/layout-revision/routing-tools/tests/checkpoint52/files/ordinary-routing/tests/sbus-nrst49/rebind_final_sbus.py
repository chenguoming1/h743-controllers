"""Read-only full exact rebind; emit a source-hash locked construction proposal."""
import argparse,json,hashlib,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out-prefix',required=True);a=p.parse_args()
import route_complete_sbus50 as r
import composite_sbus_native19b as g
from shapely.geometry import Point,LineString
S=Path(a.source).resolve();prefix=Path(a.out_prefix).resolve();read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();n=read(S/'f722-heli.native.json');assert sha(S/'f722-heli.kicad_pcb')==n['board_sha256'];oldnative=g.native;oldids={o['uuid']for o in oldnative['objects']};res=[row for row in g.BASE if row[0]['uuid']not in oldids and row[0].get('ref')!='R45'];lvdrops={o['uuid']for o in n['objects']if o['kind']=='track'and o['net']=='SBUS_LV'and o['uuid']!='187f794e-f820-4425-869b-0ca552a872a2'};assert len(lvdrops)==5
r.BASE=[g.g.entry(o)for o in n['objects']if o['uuid']not in lvdrops and o.get('ref')!='R45']+[g.g.entry(o)for o in g.g.pose['objects']if o.get('ref')=='R45']+res;r.s.N=n;r.s.OUTLINE=r.s.geom(n['outline_with_npth']['polygons'])
proposal=read(r.H/'reference-corrected-sbus19-proposal.json');assert proposal['all_corrections_found'];r.ROUTES[:]=proposal['selected_routes'];r.VIA[:]=proposal['vias'];paths=[];vias=[]
for q in r.ROUTES:
 rr=r.s.check(LineString(q['points']),r.obstacles(q['logical'],q['layer']),True);paths.append(dict(name=q['name'],passed=rr[0]['pass_with_polygon_error'],nearest=rr[:3],violations=[z for z in rr if z['extra_clearance_mm']<r.s.ERROR]))
for v in list(r.VIA):
 r.VIA.remove(v);r.install(v['logical']);obs=r.s.obstacles(v['logical'],'In2.Cu')[1];rr=r.s.check(Point(v['xy']),obs,True);r.VIA.append(v);vias.append(dict(**v,passed=rr[0]['pass_with_polygon_error'],nearest=rr[:3],violations=[z for z in rr if z['extra_clearance_mm']<r.s.ERROR]))
q=dict(source_board_sha256=n['board_sha256'],allowed_changed_nets=['SBUS_LV','SBUS_MCU'],removed_source_ids=sorted(lvdrops),footprint_transforms={'R45':[11.65,21.8,0,'F.Cu']},routes=[dict(x,logical_net=x['logical'])for x in r.ROUTES],vias=[dict(x,logical_net=x['logical'])for x in r.VIA],all_surface_branches_found=True,all_trunks_found=True,input_proposal_sha256=sha(r.H/'reference-corrected-sbus19-proposal.json'))
pp=prefix.with_name(prefix.name+'-proposal.json');sp=prefix.with_name(prefix.name+'-screen.json');pp.write_text(json.dumps(q,indent=2)+'\n');screen=dict(source_board_sha256=n['board_sha256'],source_native_sha256=sha(S/'f722-heli.native.json'),proposal_sha256=sha(pp),passed=all(x['passed']for x in paths+vias),paths=paths,vias=vias,source_object_count=len(n['objects']),explicit_removals=sorted(lvdrops),declared_pose=q['footprint_transforms'],future_reservation_objects=len(res));sp.write_text(json.dumps(screen,indent=2)+'\n');print(json.dumps({k:screen[k]for k in ['source_board_sha256','passed','source_object_count','future_reservation_objects']}));assert screen['passed']
