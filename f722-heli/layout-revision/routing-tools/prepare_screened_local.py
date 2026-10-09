"""Prepare an add-only native import for explicit ordinary/protected branch proposals.

This does not run a router or edit a board. It accepts source-bound geometry proof,
checks exact native pad entry and logical ownership, and leaves all native gates
mandatory on the eventual isolated import.
"""
import argparse,hashlib,json,math
from pathlib import Path
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
poly=lambda ps:unary_union([Polygon(p['outer'],p.get('holes',[]))for p in ps])
ap=argparse.ArgumentParser();ap.add_argument('--proposal',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();q=json.loads(a.proposal.read_text())
ids=q['source_identity']
for i in ids.values():assert sha(i['path'])==i['sha256']
B=Path(ids['f722-heli']['path']);N=Path(ids['f722-heli.native']['path']);M=Path(ids['model']['path']);L=Path(ids['f722-heli.logical-route-map']['path'])
n=json.loads(N.read_text());m=json.loads(M.read_text());lm=json.loads(L.read_text());assert n['board_sha256']==lm['board_sha256']==q['board_sha256']==sha(B)
by_id={o['uuid']:o for o in n['objects']};by_key={o['key']:o for o in n['objects']if o['kind']=='pad'}
# A topology template can predate added copper, but every native pad contact,
# physical net and inside copper shape must still match exactly.
for c in m['contacts']:
 o=by_id[c['uuid']];assert o['net']==c['physical_net'] and o['inside'][c['layer']]==c['polygons']
assert q['source_unchanged'] and not q['proposal_mutual_conflicts']
routes=[];networks=[]
for row in q['proposals']:
 net=row['net'];logical=row['logical_net'];role=m['roles'][net];terminals=row['terminals'];layer=row['layer'];points=row['points_mm']
 assert net in m['ordinary_nets'] and m['aliases'][logical]==net and row['width_mm']==.127 and not row['vias']
 assert row['different_native_components_before'] and row['minimum_extra_clearance_mm']>=0
 if role['kind']=='protected_chain':
  branch=next(b for b in role['branches']if b['logical_net']==logical);assert branch['terminals']==terminals
 else:assert role['kind']=='ordinary'and logical==net and all(by_key[k]['uuid']in role['terminals']for k in terminals)
 assert layer in ['F.Cu','B.Cu']and not any(not z['rule']and layer in z['layers']for z in n['zones'])
 for k,xy in zip(terminals,[points[0],points[-1]]):
  pad=by_key[k];inside=poly(pad['inside'][layer]);point=Point(xy)
  assert inside.covers(point)and point.distance(inside.boundary)>=.0635+.005
 assert len(points)>=2 and all(math.dist(x,y)>0 for x,y in zip(points,points[1:]))
 ints=[[round(x*100000),round(-y*100000)]for x,y in points];assert all(abs(x-xx/100000)<1e-9 and abs(y+yy/100000)<1e-9 for (x,y),(xx,yy)in zip(points,ints))
 routes.append(dict(kind='track',fixed='NOT_FIXED',nets=[logical],layer=layer,width=.127,points=points))
 networks.append('(net '+json.dumps(logical)+' (wire (path '+layer+' 12700 '+' '.join(f'{x} {y}'for x,y in ints)+') (type route)))')
assert routes;a.out.mkdir(parents=True,exist_ok=True)
contract=dict(schema='f722-native-add-only-import/v1',engine_planning_model=False,physical_board=str(B),physical_native=str(N),board_sha256=sha(B),native_sha256=sha(N),aliases=m['aliases'],ordinary_nets=m['ordinary_nets'],routable_layers=m['routable_layers'],mutable_source_ids=[],source_logical_nets=lm['logical_route_map'],regenerable_reference_zones=[],all_source_copper_fixed=True,reference_plane_policy='Only outside-layer tracks, no vias, no zones on changed layers; every saved fill must remain exact.')
model=a.out/'native-construction-model.json';model.write_text(json.dumps(contract,indent=2)+'\n')
session=a.out/'constructed.ses';session.write_text('(session "explicit-screened-native" (routes (resolution mm 100000) (network_out '+' '.join(networks)+')))\n')
(a.out/'constructed-report.json').write_text(json.dumps(dict(board_sha256=sha(B),model_sha256=sha(model),routes=routes,route_solver_used=False,native_validation_required=True),indent=2)+'\n')
receipt=dict(status='prepared_only_native_checks_required_after_import',source_board_sha256=sha(B),proposal_sha256=sha(a.proposal),preparer_sha256=sha(Path(__file__)),role_template_sha256=sha(M),role_template_pad_contacts_exact=True,model_sha256=sha(model),session_sha256=sha(session),branches=[{k:r[k]for k in ['net','logical_net','layer','terminals','points_mm','length_mm','pad_entry','minimum_extra_clearance_mm']}for r in q['proposals']],new_tracks=sum(len(r['points'])-1 for r in routes),new_vias=0,engine_routing_performed=False,source_objects_removal_allowed=False,refill_allowed=False)
(a.out/'construction.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k!='branches'}))
