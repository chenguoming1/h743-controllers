from geometry import *
options=[('3cfc0b66-fb89-4bcd-8fd4-b8f8542b90a3',[105.175,130.925],['F.Cu']),('7f89653b-c07a-4bb7-8d55-49a1f1873aa3',[101.975,117.825],['F.Cu'])]
result=[]
for uid,p,ls in options:
 v=items[uid]; q=dict(uuid=uid+'-dogbone',kind='segment',net=v['net'],layers=ls,start=v['at'],end=p,width_mm=.45)
 obs=[]
 for d in items.values():
  if d['net']==v['net'] or not set(d['layers'])&set(ls):continue
  dist=gap(q,d)
  if dist<.127002:obs.append(dict(uuid=d['uuid'],kind=d['kind'],net=d['net'],layers=d['layers'],gap_mm=dist,ref=d.get('ref'),pin=d.get('pin')))
 zs=[]
 for z in zones:
  if z['net']!='GND':continue
  ps=[x for x in z['fill_polygons'] if contains(p,x['points'])]
  zs.append(dict(layer=z['layer'],containing_fill_indices=[x['index'] for x in ps],minimum_candidate_centre_to_containing_polygon_edge_mm=min((min(point_seg(p,a,b) for a,b in edges(x['points'])) for x in ps),default=None)))
 donors=[d for d in items.values() if d['uuid']!=uid and d['net']==v['net'] and gap(v,d)<=1e-9]
 result.append(dict(via_uuid=uid,source_at=v['at'],candidate_at=p,unchanged_via_diameter_mm=.45,unchanged_drill_mm=.2,add_tracks=[q],original_all_direct_copper_donors=donors,all_donors_preserved_by_retaining_source_tracks_and_full_land_width_dogbone=all(gap(q,d)<=1e-9 for d in donors),fixed_different_net_route_obstructions=obs,all_ground_fill_source_memberships=zs,qualification='Static bounded candidate only; no PCB edit, native DRC, mask/paste export, or actual return-path/EMC qualification.'))
 print(uid,'routeobs',obs,'zones',zs)
OUT.joinpath('simple-routing-only-options.json').write_text(json.dumps(result,indent=2))
