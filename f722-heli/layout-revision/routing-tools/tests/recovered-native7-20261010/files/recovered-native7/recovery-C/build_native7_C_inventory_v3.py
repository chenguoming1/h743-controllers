"""Read-only exact native7 C copper/contact inventory; no routing or board edits."""
import hashlib,json,math,struct,time,uuid
from pathlib import Path
from shapely.geometry import Polygon,Point,LineString
from shapely import unary_union
START=time.monotonic();HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
IMP=ROOT/'ordinary-routing/tests/native13-access/joint-native-import11-v1'
NATIVE=IMP/'candidates/published-reference02/f722-heli.native.json';TX=IMP/'selected-transaction.json';SRC=ROOT/'ordinary-routing/tests/boot56/candidate01/f722-heli.native.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(NATIVE)=='53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505'
assert sha(TX)=='b7ca08e59b4316c8a88c0ff9d3c0fe3cffac4d0f0ad2b407028cd1ef3050f497'
assert sha(SRC)=='98f7d08c700cbc6e31cdd7f522be86091521ee4f2b7c760a9080541ade08cebd'
N=json.loads(NATIVE.read_text());T=json.loads(TX.read_text());by={o['uuid']:o for o in N['objects']};pads={o['key']:o for o in N['objects'] if o['kind']=='pad'}
th=sha(TX);source_hash=T['source_board_sha256'];recipes={r['recipe']['name']:r['recipe'] for r in T['added_copper']};mapping={};provenance={}
def rounded(p):return [round(x,6) for x in p]
for name,r in recipes.items():
 mapping[name]=[]
 for i in range(len(r['points'])-1) if r['kind']=='track' else [None]:
  suffix=name+('/via' if i is None else '/segment/'+str(i));uid=str(uuid.uuid5(uuid.NAMESPACE_URL,source_hash+'/'+th+'/'+suffix));assert uid in by,(name,i,uid)
  o=by[uid];assert o['kind']==r['kind'] and o['net']==r['net']
  if i is None:assert o['xy']==rounded(r['xy']) and o['width']==.45 and o['drill']['width']==.20 and set(o['barrel_layers'])==set(N['copper_layers'])
  else:assert o['start']==rounded(r['points'][i]) and o['end']==rounded(r['points'][i+1]) and o['width']==r['width'] and o['width_by_layer']=={r['layer']:r['width']},(name,i)
  mapping[name].append(uid);provenance[uid]=dict(recipe_name=name,segment_index=i)
assert len(provenance)==sum(len(x) for x in mapping.values())
def geom(pp):
 polygons=[Polygon(p['outer'],p.get('holes',[])) for p in pp]
 assert polygons and all(not p.is_empty and p.is_valid for p in polygons),'Invalid or empty actual native polygon'
 result=unary_union(polygons)
 assert not result.is_empty and result.is_valid,'Invalid native copper union'
 return result
needed_nets={'PORT_C_RX_EXT','PORT_C_TX_EXT','PORT_C_RX_MCU','PORT_C_TX_MCU','VX_PROTECTED'}
shapes={o['uuid']:{l:geom(p) for l,p in o['copper'].items()} for o in N['objects'] if o['net'] in needed_nets}
def source_contact_rows(ids):
 ids=set(ids);net=by[next(iter(ids))]['net'];out=[]
 for uid in sorted(ids):
  o=by[uid]
  for other in N['objects']:
   if other['uuid'] in ids or other['net']!=net:continue
   oc=shapes[other['uuid']]
   for layer in shapes[uid].keys()&oc.keys():
    z=shapes[uid][layer].intersection(oc[layer])
    if z.is_empty:continue
    witnesses=[]
    if o['kind']=='track':
     for p,q in [(o['start'],o['end']),(o['end'],o['start'])]:
      if not oc[layer].covers(Point(p)):continue
      dx,dy=q[0]-p[0],q[1]-p[1];d=math.hypot(dx,dy);nx,ny=-dy/d,dx/d
      cross=z.intersection(LineString([[p[0]-nx,p[1]-ny],[p[0]+nx,p[1]+ny]]))
      witnesses.append(dict(center=p,cross_section_mm=cross.length,nominal_width_mm=o['width'],full_width_with_native_polygon_error=cross.length>=o['width']-2*N['maximum_polygon_error_mm'],wkb_hex=cross.wkb_hex))
    out.append(dict(removed_uuid=uid,retained_uuid=other['uuid'],retained_key=other.get('key'),retained_record=other,layer=layer,
      intersection_area_mm2=z.area,intersection_length_mm=z.length,intersection_wkb_hex=z.wkb_hex,finite_positive_area=z.area>0,full_width_endpoint_witnesses=witnesses))
 return out
scopes={
 'RX_MCU_source_entry':dict(status='complete_existing_source_escape_but_full_MCU_function_open',recipes=['C-MCU-coordinated-0','C-MCU-coordinated-via-0'],actual_keys=['U1.28','R34.2'],remove_for_v24=True),
 'TX_MCU_source_entry':dict(status='complete_existing_source_escape_but_full_MCU_function_open',recipes=['C-MCU-coordinated-1','C-MCU-coordinated-via-1'],actual_keys=['U1.29','R35.2'],remove_for_v24=True),
 'RX_down_source_prefix':dict(status='open_branch_source_boundary_retained_initially',recipes=['rotated-RX-down'],actual_keys=['U15.1','R34.1'],remove_for_v24=False),
 'RX_down_target_stub':dict(status='open_branch_target_boundary_retained_initially',recipes=['R34-complete-B-R34.1','R34-pair-R34.1'],actual_keys=['R34.1'],remove_for_v24=False),
 'RX_MCU_target_stub':dict(status='open_MCU_target_boundary_retained_initially',recipes=['R34-complete-B-R34.2','R34-pair-R34.2'],actual_keys=['R34.2'],remove_for_v24=False),
 'TX_down_complete_tail':dict(status='complete_donor_must_fully_restore_if_removed',recipes=['C-TX-down-F','C-TX-down-In2','C-TX-down-B','fullBOOT-held-TX-via-0','fullBOOT-held-TX-via-1'],actual_keys=['U15.2','R35.1'],remove_for_v24=True),
 'TX_down_IO2_prefix':dict(status='complete_bonded_IO2_entry_retained_initially_optional_full_replacement',recipes=['rotated-TX-down'],actual_keys=['U15.2'],remove_for_v24=False),
 'TX_up_header_tail':dict(status='complete_donor_must_fully_restore_if_removed',recipes=['rotated-TX-complete-J11-tail'],actual_keys=['U15.2','U15.9','J11.2'],remove_for_v24=True),
 'TX_up_bonded_NC9_prefix':dict(status='complete_bonded_and_NC9_entry_retained',recipes=['rotated-TX-NC9-up'],actual_keys=['U15.2','U15.9'],remove_for_v24=False),
 'RX_up_bonded_NC10_prefix':dict(status='complete_local_prefix_but_header_branch_open',recipes=['rotated-RX-NC10-up'],actual_keys=['U15.1','U15.10','J11.1'],remove_for_v24=False),
 'private_VX_leaf':dict(status='complete_0_25mm_supply_donor_must_fully_restore',recipes=['R57-complete-VX-from-C72'],actual_keys=['R57.1','C72.1'],remove_for_v24=True),
}
for name,row in scopes.items():
 ids=[u for r in row['recipes'] for u in mapping[r]];row['native_ids']=ids;row['records']=[by[u] for u in ids];row['recipes']=[recipes[r] for r in row['recipes']];row['actual_pads']=[pads[k] for k in row['actual_keys']];row['retained_finite_contacts']=source_contact_rows(ids)
# Exact physical components on each relevant net; same-net identities never create virtual edges.
def components(net,cut_pad=None):
 cut={} if cut_pad is None else shapes[pads[cut_pad]['uuid']];nodes=[]
 for o in N['objects']:
  if o['net']!=net or (cut_pad is not None and o.get('key')==cut_pad):continue
  for layer,cu in shapes[o['uuid']].items():
   pp=cu.difference(cut[layer]) if layer in cut else cu
   pieces=list(pp.geoms) if pp.geom_type=='MultiPolygon' else [pp]
   for j,p in enumerate(pieces):
    if not p.is_empty:nodes.append((o,layer,j,p))
 parent=list(range(len(nodes)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for i,(a,la,_,pa) in enumerate(nodes):
  for j,(b,lb,_,pb) in enumerate(nodes[:i]):
   if la==lb and pa.intersects(pb):parent[find(i)]=find(j)
   elif a['uuid']==b['uuid'] and a.get('plated') and la in a.get('barrel_layers',[]) and lb in a.get('barrel_layers',[]):parent[find(i)]=find(j)
 groups={}
 for i,(o,l,j,p) in enumerate(nodes):
  g=groups.setdefault(find(i),dict(native_ids=set(),actual_keys=set(),layers=set(),fragments=[]));g['native_ids'].add(o['uuid']);g['layers'].add(l)
  if o.get('key'):g['actual_keys'].add(o['key'])
  g['fragments'].append(dict(uuid=o['uuid'],layer=l,index=j,area_mm2=p.area))
 return [dict(native_ids=sorted(v['native_ids']),actual_keys=sorted(v['actual_keys']),layers=sorted(v['layers']),fragments=v['fragments']) for v in groups.values()]
connectivity={net:components(net) for net in sorted(needed_nets)}
cut_connectivity={net:components(net,pad) for net,pad in [('PORT_C_RX_EXT','U15.1'),('PORT_C_TX_EXT','U15.2')]}
# Full scopes include prefix + tail, avoiding historical recipe-name-only donor cuts.
for name,parts in [('RX_down_complete_existing_copper',['RX_down_source_prefix','RX_down_target_stub']),('TX_down_complete_existing_copper',['TX_down_IO2_prefix','TX_down_complete_tail']),('TX_up_complete_existing_copper',['TX_up_bonded_NC9_prefix','TX_up_header_tail'])]:
 ids=[u for p in parts for u in scopes[p]['native_ids']];scopes[name]=dict(parts=parts,native_ids=ids,records=[by[u] for u in ids],retained_finite_contacts=source_contact_rows(ids),not_automatic_cut=True)
row=dict(schema='f722-native7-C-structural-inventory/v3',native_binding=dict(file=str(NATIVE.relative_to(ROOT)),sha256=sha(NATIVE),board_sha256=N['board_sha256'],native_version=N['native_version'],maximum_polygon_error_mm=N['maximum_polygon_error_mm']),
 source11_binding=dict(file=str(SRC.relative_to(ROOT)),sha256=sha(SRC),board_sha256=T['source_board_sha256']),transaction_binding=dict(file=str(TX.relative_to(ROOT)),sha256=th),
 recipe_native_mapping_verified=True,recipe_count=len(mapping),native_added_member_count=len(provenance),recipe_groups=mapping,recipe_provenance=provenance,
 scopes=scopes,physical_components=connectivity,after_actual_bonded_pad_cut_components=cut_connectivity,
 all_C_native_records=[o for o in N['objects'] if o['net'].startswith('PORT_C_')],actual_endpoints={k:pads[k] for k in ['U1.28','U1.29','U15.1','U15.2','U15.9','U15.10','R34.1','R34.2','R35.1','R35.2','J11.1','J11.2','R57.1','R57.2','C72.1','C72.2']},
 no_routing_performed=True,no_native_source_edits=True,conditional_later_source_and_flash_recipes_not_adopted=True,script_sha256=sha(__file__),seconds=time.monotonic()-START)
out=HERE/'native7-C-removal-restoration-inventory-v3.json';assert not out.exists();out.write_text(json.dumps(row,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(file=str(out),sha256=sha(out),seconds=row['seconds'],scopes={k:len(v['native_ids']) for k,v in scopes.items()},components={k:[g['actual_keys'] for g in v] for k,v in connectivity.items()}),indent=2))
