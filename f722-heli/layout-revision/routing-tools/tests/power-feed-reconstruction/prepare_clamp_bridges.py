"""Prepare, but do not import, four exact protected-chain clamp bridges."""
import hashlib, json, math
from pathlib import Path
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;R=H.parents[1]
B=R/'candidate19/f722-heli.kicad_pcb';N=B.with_suffix('.native.json');M=R/'model-candidate19-ports/model.json';L=B.with_suffix('.logical-route-map.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
n=json.loads(N.read_text());m=json.loads(M.read_text());lm=json.loads(L.read_text());assert n['board_sha256']==m['board_sha256']==lm['board_sha256']==sha(B)
poly=lambda ps:unary_union([Polygon(p['outer'],p.get('holes',[]))for p in ps])
pads={o['key']:o for o in n['objects']if o['kind']=='pad'};region=poly(n['outline_with_npth']['polygons']);rows=[];routes=[];network=[]
for net in ['PORT_A_RX_EXT','PORT_A_TX_EXT','PORT_B_RX_EXT','PORT_B_TX_EXT']:
 role=m['roles'][net];assert role['kind']=='protected_chain';branch=role['branches'][1];logical=branch['logical_net'];a,b=[pads[k]for k in branch['terminals']]
 assert a['ref']==b['ref']=='U14' and m['aliases'][logical]==net
 assert not any(o['net']==net and o['kind']!='pad'for o in n['objects']), 'Review existing protected copper before continuation.'
 points=[a['xy'],b['xy']];line=LineString(points);shape=line.buffer(.0635,quad_segs=128);endpoints=[]
 for o in [a,b]:
  inside=poly(o['inside']['F.Cu']);depth=inside.boundary.distance(Point(o['xy']));assert inside.covers(Point(o['xy'])) and depth>.0635
  endpoints.append(dict(key=o['key'],uuid=o['uuid'],centerline_pad_interior_depth_mm=depth,full_width_round_cap_inside=True))
 gaps=[];holes=[]
 for o in n['objects']:
  # Other same-physical-net pads belong to different protection branches and
  # remain clearance obstacles outside the two explicit branch terminals.
  if o['uuid']not in [a['uuid'],b['uuid']] and 'F.Cu'in o['copper']:
   gaps.append(dict(uuid=o['uuid'],key=o.get('key'),net=o['net'],gap_mm=line.distance(poly(o['copper']['F.Cu']))-.0635))
  if o.get('drill'):
   gap=line.distance(poly(o['drill']['outside']))-.0635;need=.254 if o.get('npth',False) else .2
   holes.append(dict(uuid=o['uuid'],gap_mm=gap,required_mm=need));assert gap>=need
 gaps.sort(key=lambda q:q['gap_mm']);assert gaps[0]['gap_mm']>=.127
 assert region.covers(shape) and line.distance(region.boundary)-.0635>=.254
 for z in n['zones']:
  if not z['rule']:assert 'F.Cu'not in z['layers'];continue
  if 'F.Cu'in z['layers']and(z['forbid']['tracks']or z['forbid']['copper']):assert not shape.intersects(poly(z['outline']))
 rows.append(dict(net=net,logical_net=logical,sequence=role['sequence'],terminals=branch['terminals'],points=points,length_mm=line.length,width_mm=.127,layer='F.Cu',endpoints=endpoints,min_foreign_or_other_branch_gap_mm=gaps[0]['gap_mm'],nearest=gaps[0]))
 routes.append(dict(kind='track',fixed='NOT_FIXED',nets=[logical],layer='F.Cu',width=.127,points=points))
 ints=[[round(x*100000),round(-y*100000)]for x,y in points];network.append('(net '+json.dumps(logical)+' (wire (path F.Cu 12700 '+' '.join(f'{x} {y}'for x,y in ints)+') (type route)))')
out=H/'clamp-bridges-prepared';out.mkdir(exist_ok=True)
contract=dict(schema='f722-native-add-only-import/v1',engine_planning_model=False,physical_board=str(B),physical_native=str(N),board_sha256=sha(B),native_sha256=sha(N),aliases=m['aliases'],ordinary_nets=m['ordinary_nets'],routable_layers=m['routable_layers'],mutable_source_ids=[],source_logical_nets=lm['logical_route_map'],regenerable_reference_zones=[],all_source_copper_fixed=True,reference_plane_policy='Only four F.Cu bridges; no new vias, no zones on F.Cu, all saved fill remains exact.')
model=out/'native-construction-model.json';model.write_text(json.dumps(contract,indent=2)+'\n')
session=out/'constructed.ses';session.write_text('(session "explicit-U14-clamp-bridges" (routes (resolution mm 100000) (network_out '+' '.join(network)+')))\n')
(out/'constructed-report.json').write_text(json.dumps(dict(board_sha256=sha(B),model_sha256=sha(model),routes=routes,route_solver_used=False,native_validation_required=True),indent=2)+'\n')
receipt=dict(status='prepared_only_waiting_for_candidate19_power_acceptance_and_adoption_no_board_edit',source_board_sha256=sha(B),source_native_sha256=sha(N),source_model_sha256=sha(M),logical_map_sha256=sha(L),preparer_sha256=sha(Path(__file__)),native_model_sha256=sha(model),session_sha256=sha(session),branches=rows,new_tracks=4,new_vias=0,expected_open_reduction=4,native_reduction_unproved=True,logical_protection_contract='Each track is exactly P1 between the two published U14 clamp terminals; no connector-to-resistor bypass. Original/supplemental native protection-cut gates are mandatory after import.',remaining_checks=['Source19 loaded power acceptance and owner adoption','Native import on an isolated paired copy','DRC/process/strict parity/protection/native connectivity and exact saved-fill preservation'])
(out/'proposal.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(status=receipt['status'],branches=[(q['logical_net'],q['length_mm'],q['min_foreign_or_other_branch_gap_mm'])for q in rows])))
