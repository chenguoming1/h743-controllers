"""Check and simplify a retained located P0 path using actual native geometry."""
import hashlib,json,math
from pathlib import Path
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;R=H.parents[1]
B=R/'candidate21/f722-heli.kicad_pcb';N=B.with_suffix('.native.json');L=B.with_suffix('.logical-route-map.json');M=R/'model-candidate21-ready/model.json';raw_path=H/'port-b-located-path.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();n=json.loads(N.read_text());lm=json.loads(L.read_text());model=json.loads(M.read_text());raw=json.loads(raw_path.read_text());assert n['board_sha256']==lm['board_sha256']==model['board_sha256']==raw['board_sha256']==sha(B)
net='PORT_B_RX_EXT';logical=net+'::P0';role=model['roles'][net];branch=role['branches'][0];assert branch['logical_net']==logical and branch['terminals']==['J10.1','U14.7']
poly=lambda ps:unary_union([Polygon(p['outer'],p.get('holes',[]))for p in ps])
pads={o['key']:o for o in n['objects']if o['kind']=='pad'};source=pads['J10.1'];target=pads['U14.7'];shared=poly(target['inside']['F.Cu']);outline=poly(n['outline_with_npth']['polygons']);objects=[];holes=[];rules=[];same_branch=[]
for o in n['objects']:
 if o.get('drill'):holes.append((o,poly(o['drill']['outside'])))
 if 'F.Cu'not in o['copper']or o['uuid']in [source['uuid'],target['uuid']]:continue
 shape=poly(o['copper']['F.Cu'])
 if o['net']==net and o['kind']!='pad':
  alias=lm['logical_route_map'][o['uuid']]
  assert alias!=logical,'Unexpected existing P0; review separately.'
  # Only the branch's shared U14.7 pad permits physical P0/P1 contact.
  if alias==net+'::P1':same_branch.append((o,shape.difference(shared)));continue
 objects.append((o,shape))
for z in n['zones']:
 if z['rule']and 'F.Cu'in z['layers']and(z['forbid']['tracks']or z['forbid']['copper']):rules.append((z,poly(z['outline'])))
 if not z['rule']:assert 'F.Cu'not in z['layers']
def check(points,extra=0):
 line=LineString(points);shape=line.buffer(.0635,quad_segs=128);rows=[]
 rows.append(dict(kind='outline_npth',uuid='outline',gap_mm=line.distance(outline.boundary)-.0635,required_mm=.254))
 if not outline.covers(shape):return False,[dict(kind='outside_outline')]
 for o,g in objects:rows.append(dict(kind='foreign_or_other_branch_copper',uuid=o['uuid'],key=o.get('key'),net=o['net'],gap_mm=line.distance(g)-.0635,required_mm=.127))
 for o,g in same_branch:
  outside=shape.difference(shared);rows.append(dict(kind='other_branch_outside_shared_pad',uuid=o['uuid'],gap_mm=outside.distance(g),required_mm=.127))
 for o,g in holes:
  if o['net']==net and not o.get('npth'):continue
  rows.append(dict(kind='drill',uuid=o['uuid'],gap_mm=line.distance(g)-.0635,required_mm=.254 if o.get('npth')else .20))
 for z,g in rules:rows.append(dict(kind='rule',uuid=z['uuid'],gap_mm=line.distance(g)-.0635,required_mm=0))
 for r in rows:r['extra_mm']=r['gap_mm']-r['required_mm']
 rows.sort(key=lambda r:r['extra_mm']);return rows[0]['extra_mm']>=extra,rows[:12]
located=next(r['requested_corners_mm']for r in raw['records']if r['stage']=='located_trace');points=[source['xy']]+located+[target['xy']]
ok,raw_checks=check(points);assert ok,raw_checks
# Coordinate-preserving line-of-sight simplification; no grid or maze search.
simplified=[points[0]];i=0
while i<len(points)-1:
 for j in range(len(points)-1,i,-1):
  if check([points[i],points[j]])[0]:break
 simplified.append(points[j]);i=j
ok,checks=check(simplified);assert ok
entries=[]
for o in [source,target]:
 p=Point(o['xy']);g=poly(o['inside']['F.Cu']);depth=p.distance(g.boundary);assert g.covers(p)and depth>.0685
 entries.append(dict(pad=o['key'],uuid=o['uuid'],point_mm=o['xy'],full_round_cap_inside_native_pad=True,extra_containment_mm=depth-.0635))
negative=[[24,6.95],[24,8.0]];bad,bad_checks=check(negative);assert not bad and any(r['kind']=='other_branch_outside_shared_pad'and r['extra_mm']<0 for r in bad_checks)
row=dict(net=net,logical_net=logical,layer='F.Cu',terminals=branch['terminals'],terminal_uuids=[source['uuid'],target['uuid']],different_native_components_before=True,points_mm=simplified,width_mm=.127,vias=[],length_mm=LineString(simplified).length,minimum_extra_clearance_mm=checks[0]['extra_mm'],pad_entry=entries,logical_role=role,native_drc_performed=False,acceptance_claimed=False)
receipt=dict(source_identity={'f722-heli':{'path':str(B),'sha256':sha(B)},'f722-heli.native':{'path':str(N),'sha256':sha(N)},'model':{'path':str(M),'sha256':sha(M)},'f722-heli.logical-route-map':{'path':str(L),'sha256':sha(L)},'screen':{'path':str(Path(__file__)),'sha256':sha(Path(__file__))}},board_sha256=sha(B),source_unchanged=True,proposal_mutual_conflicts=[],proposals=[row],engine_provenance={'status':'located by engine, rejected during insertion, no engine success claimed','raw_receipt_sha256':sha(raw_path),'raw_points':located,'pad_center_completion_points':[source['xy'],target['xy']]},raw_combined_checks=raw_checks,simplified_checks=checks,negative_outside_shared_pad_control={'points':negative,'accepted':bad,'checks':bad_checks},limitations=['Geometric path only; native DRC, intended branch connectivity/protection and exact-source power/fill/drill applicability must pass after isolated import.','Nominal minimum clearance reserve is reported exactly; no manufacturing margin claimed.'])
(H/'port-b-native-proposal.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(points=simplified,length=row['length_mm'],minimum_extra_clearance_mm=row['minimum_extra_clearance_mm'],nearest=checks[:3])))
