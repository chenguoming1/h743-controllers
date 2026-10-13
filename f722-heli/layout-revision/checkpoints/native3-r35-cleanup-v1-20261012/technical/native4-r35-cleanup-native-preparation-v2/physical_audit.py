"""Non-executing source excerpts. See SOURCE-PROVENANCE.json for original identity.
Dependencies belong to the original implementation; use reproduction/replay_native.py
for the standalone verifier and exact sealed-recipe replay.
"""

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def surviving_fragments(old_graph,new_graph,old,removed,moved):
 by=defaultdict(list)
 for node in new_graph['nodes']:by[node['uuid']].append(node)
 checks=[]
 for root,nodes in old_graph['components'].items():
  retained=[x for x in nodes if x['uuid'] in old and x['uuid'] not in removed];mapped=set();missing=[]
  for node in retained:
   matches=(set(new_graph['memberships'].get(node['uuid'],set())) if node['uuid'] in moved else {x['root'] for x in by[node['uuid']] if x['layer']==node['layer'] and x['shape'].intersection(node['shape']).area>0})
   mapped.update(matches)
   if not matches:missing.append({'uuid':node['uuid'],'layer':node['layer'],'bounds_mm':list(node['shape'].bounds)})
  checks.append({'source_root':root,'retained_fragments':len(retained),'candidate_roots':sorted(mapped),'missing':missing,'passed':not retained or not missing and len(mapped)==1})
 return checks

def run(root,c):
 sys.path.insert(0,str(n.ROOT/'python-deps'))
 import shapely
 from shapely.geometry import Point,LineString,box
 from shapely.ops import unary_union
 from shapely.strtree import STRtree
 plan=g.check_sources();p=plan['paths'];profile=n.read(c['profile']['path']);delta=n.read(c['delta']['path']);source=n.read(p['source_audit']);o=n.read(p['source_obligations']);contracts=n.read(p['protected_contracts'])
 adapter=load('next_candidate_frozen_kernels',p['contact_adapter']);generic,k,f=adapter.kernels()
 before=g.read_source('native');manifest=n.read(root/'compressed-artifacts.json');after=g.compact_json.read(root/'after.native.json.gz',manifest['native'])
 old,new=[{x['uuid']:x for x in d['objects']} for d in [before,after]]
 oldrows,newrows=[k.native_records_with_fills(d) for d in [before,after]]
 oldholes,newholes=[k.hole_map(rows,d['copper_layers']) for rows,d in [(oldrows,before),(newrows,after)]]
 oldby,newby=defaultdict(list),defaultdict(list)
 for row in oldrows:oldby[row['net']].append(row)
 for row in newrows:newby[row['net']].append(row)
 history={r['net']:r for r in source['all_physical_nets']};n.require(set(oldby)==set(newby)==set(history),'Physical net inventory changed')
 moved={x['uuid'] for x in before['objects'] if x.get('ref') in profile.get('pose_changes',{})}
 added={x['uuid'] for x in delta['add_tracks']+delta['add_vias']};removed=set(g.normalize_cuts(delta));error=max(before['maximum_polygon_error_mm'],after['maximum_polygon_error_mm'])
 pairs=g.pair_set;comparisons=[];lineage=[];endpoints=[];vias=[];contacts=[];actual=[];branches=[];guards=[]
 def grouped(graph,pads):return sorted([sorted({x['uuid'] for x in nodes}&pads) for nodes in graph['components'].values() if {x['uuid'] for x in nodes}&pads])
 def same(graph,a,b):return bool(graph['memberships'].get(a,set())&graph['memberships'].get(b,set()))
 for net,rows in sorted(newby.items()):
  old_graph=f.rich_partition(oldby[net],global_holes=oldholes);graph=f.rich_partition(rows,global_holes=newholes);pads={r['uuid'] for r in rows if r['kind']=='pad'};oldgroups=grouped(old_graph,pads);groups=grouped(graph,pads)
  n.require(pairs(oldgroups)==pairs(history[net]['candidate_raw_pad_partition']),'Current adopted physical partition not reproduced: '+net)
  row={'net':net,'pad_count':len(pads),'source_raw_pad_partition':oldgroups,'candidate_raw_pad_partition':groups,'source_lost_pad_pairs':sorted(pairs(oldgroups)-pairs(groups)),'all_real_pads_connected':f.connected(graph,sorted(pads)) if pads else None}
  for version in ['native4','native5','native6','native7']:row[version+'_lost_pad_pairs']=sorted(pairs(history[net][version+'_raw_pad_partition'])-pairs(groups))
  roots=set().union(*(graph['memberships'].get(u,set()) for u in pads)) if pads else set()
  row['new_record_fragments']=[{'uuid':u,'candidate_roots':sorted(graph['memberships'].get(u,set())),'every_fragment_reaches_real_pad':bool(graph['memberships'].get(u,set())) and graph['memberships'][u]<=roots} for u in sorted(added) if new[u]['net']==net]
  row['route_only_components']=[{'root':r,'UUIDs':sorted({x['uuid'] for x in nodes})} for r,nodes in graph['components'].items() if not {x['uuid'] for x in nodes}&pads];comparisons.append(row)
  lineage.extend(dict(net=net,**x) for x in surviving_fragments(old_graph,graph,old,removed,moved))
  for pad in [r for r in rows if r['kind']=='pad']:
   u=pad['uuid'];incident={a for a,b,l in graph['contacts'] if b==u}|{b for a,b,l in graph['contacts'] if a==u}
   changed_drill_shape=any(old_graph['shapes'].get(u,{}).get(l,unary_union([])).symmetric_difference(shape).area>0 for l,shape in graph['shapes'].get(u,{}).items())
   if not incident&added and not changed_drill_shape:continue
   witnesses=[]
   for layer,contour in pad['inside'].items():
    inner=k.native_polygons(contour).difference(newholes.get(layer,unary_union([])))
    route=[r for r in rows if r['kind'] in ['track','via','arc'] and layer in graph['shapes'].get(r['uuid'],{}) and same(graph,u,r['uuid'])];support=unary_union([graph['shapes'][r['uuid']][layer] for r in route])
    for t in route:
     if t['kind']=='track' and graph['shapes'][t['uuid']][layer].intersection(inner).area>0:witnesses.append(dict(track_uuid=t['uuid'],**k.full_width_witness(t,support,inner,layer,error)))
   required=bool(net) and not net.startswith('unconnected-');contacts.append({'pad_uuid':u,'key':pad['key'],'net':net,'required':required,'witnesses':witnesses,'passed':any(x['passed'] for x in witnesses) if required else None})
  for u in sorted(added):
   r=new[u]
   if r['net']!=net:continue
   if r['kind']=='track':
    for layer,shape in graph['shapes'][u].items():
     peers=unary_union([layers[layer] for peer,layers in graph['shapes'].items() if peer!=u and layer in layers and same(graph,u,peer)])
     for point in [r['start'],r['end']]:
      centered=[v for v in rows if v['kind']=='via' and v['xy']==point and layer in graph['shapes'].get(v['uuid'],{})]
      if centered:
       witnesses=[dict(via_uuid=v['uuid'],**k.full_width_witness(r,shape,graph['shapes'][v['uuid']][layer],layer,error)) for v in centered]
       result={'track_uuid':u,'layer':layer,'endpoint':point,'mode':'DRILL_SUBTRACTED_ANNULAR_CONTACT','witnesses':witnesses,'passed':any(x['passed'] for x in witnesses)}
      else:result=dict(track_uuid=u,endpoint=point,mode='FULL_WIDTH_SAME_NET_SUPPORT_UNION',**k.full_width_witness(r,shape,peers,layer,error,at_endpoint=point))
      endpoints.append(result)
   elif r['kind']=='via':
    witnesses=[]
    for layer,annulus in graph['shapes'][u].items():
     for t in [x for x in rows if x['kind']=='track' and layer in graph['shapes'].get(x['uuid'],{})]:
      if graph['shapes'][t['uuid']][layer].intersection(annulus).area>0:witnesses.append(dict(track_uuid=t['uuid'],intended_endpoint=r['xy'] in [t['start'],t['end']],**k.full_width_witness(t,graph['shapes'][t['uuid']][layer],annulus,layer,error)))
    required=[w for w in witnesses if w['intended_endpoint']];vias.append({'via_uuid':u,'net':net,'witnesses':witnesses,'passed':bool(required) and all(x['passed'] for x in required)})
  for case in [x for x in contracts['actual22_cases'] if x['contract']['net']==net]:
   result=generic.actual_protection_case(rows,case['contract'],newholes,error,f);prior=next(x['candidate'] for x in source['all22_actual_IO_cuts'] if x['original_raw_contract']['contract']['id']==case['contract']['id']);ids=case['pad_UUIDs'];result['source_to_actual_IO_connected']=f.connected(graph,[ids['source'],ids['clamp']]);result['target_to_actual_IO_connected']=f.connected(graph,[ids['target'],ids['clamp']])
   if case['contract']['clamp'] in ['U15.1','U15.2']:
    clamp=new[ids['clamp']];cut,_=k.conductive_shapes(dict(clamp,copper=clamp['inside']));outside=f.rich_partition(rows,subtract_region=cut,omit_ids={clamp['uuid']},global_holes=newholes);widths=[]
    for role in ['source','target']:
     connected=result[role+'_to_actual_IO_connected'];rr=outside['memberships'].get(ids[role],set());ww=[]
     for layer,contour in clamp['inside'].items():
      inner=k.native_polygons(contour).difference(newholes.get(layer,unary_union([])));route=[r for r in rows if r['kind'] in ['track','via','arc'] and layer in graph['shapes'].get(r['uuid'],{}) and outside['memberships'].get(r['uuid'],set())&rr];support=unary_union([graph['shapes'][r['uuid']][layer] for r in route])
      for t in route:
       if t['kind']=='track' and graph['shapes'][t['uuid']][layer].intersection(inner).area>0:ww.append(dict(track_uuid=t['uuid'],**k.full_width_witness(t,support,inner,layer,error)))
     widths.append({'role':role,'connected':connected,'witnesses':ww,'passed_when_connected':not connected or bool(rr) and any(w['passed'] for w in ww)})
    spec=next(x for x in o['branches'] if x['net']==net);bykey={r['key']:r for r in rows if r['kind']=='pad'};nc=bykey[spec['NC_land']]['uuid'];side=bykey[spec['endpoint_on_NC_side']]['uuid'];other=bykey[spec['other_endpoint']]['uuid'];ncside=f.connected(outside,[nc,side]);ncother=f.connected(outside,[nc,other]);survive=all(outside['memberships'].get(u,set()) for u in [nc,side,other])
    branches.append({'contract':spec,'widths':widths,'NC_side_connected':ncside,'NC_other_connected':ncother,'NC_internal_continuity_assumed':False,'passed':ncside and not ncother and survive and f.connected(graph,[nc,ids['clamp']]) and all(w['passed_when_connected'] for w in widths)})
    result['connected_branch_full_width']=widths
   actual.append({'original_raw_contract':case,'source':prior,'candidate':result,'regressed_from_source':prior['passed'] and not result['passed']})
  for guard in [x for x in contracts['external_NC_land_guards'] if x['physical_net']==net]:guards.append({'original_raw_expected_guard':guard,'candidate':generic.shortest_external_bridge(rows,guard['nc_land_UUID'],guard['actual_io_UUID'],newholes,k,f),'NC_internal_continuity_assumed':False})
  del graph,old_graph
 geometry=geometry_ledger(before,after,oldrows,newrows,oldholes,newholes,added,removed,o,k,error,moved)
 bynet={x['net']:x for x in comparisons};byclamp={x['original_raw_contract']['contract']['clamp']:x['candidate'] for x in actual};pairproof=n.read(root/'paired-native-proof.json')
 gates={'no_current_or_historical_pad_pair_loss':all(not row[key] for row in comparisons for key in ['source_lost_pad_pairs','native4_lost_pad_pairs','native5_lost_pad_pairs','native6_lost_pad_pairs','native7_lost_pad_pairs']), 'every_retained_fragment_preserved':all(x['passed'] for x in lineage),'every_new_fragment_reaches_real_pad':all(x['every_fragment_reaches_real_pad'] for r in comparisons for x in r['new_record_fragments']),'all_complete_net_obligations':all(bynet[net]['all_real_pads_connected'] and bynet[net]['pad_count']==count and not bynet[net]['route_only_components'] for net,count in profile['required_complete_nets'].items()),'all_22_actual_IO_contracts_checked':len(actual)==22,'all_previously_passed_IO_cuts_preserved':not any(x['regressed_from_source'] for x in actual),'required_actual_IO_full_protection':all(byclamp[clamp]['passed'] for clamp in profile['required_complete_actual_IO_clamps']),'connected_IO_branches_full_width':len(branches)==2 and all(x['passed'] for x in branches),'all_NC_external_guards_passed':all(x['candidate']['passed'] for x in guards),'all_changed_pad_contacts_full_width':all(x['passed'] for x in contacts if x['required']),'all_new_track_endpoints_full_width_union_or_annulus':len(endpoints)==2*len(delta['add_tracks']) and all(x['passed'] for x in endpoints),'all_new_via_annular_contacts_full_width':len(vias)==len(delta['add_vias']) and all(x['passed'] for x in vias),'all_new_copper_and_process_clearance_passed':geometry['all_new_clearance_and_process_passed'],'native_DRC_errors_zero':pairproof['raw_DRC_error_count']==0,'no_new_warning_signatures':pairproof['warning_ledger']['all_remaining_warnings_exactly_source_bound'],'required_open_count_progress':pairproof['raw_DRC_counts']['unconnected_items']<=profile['maximum_native_unconnected'],'inherited_scoped_contact_disposition_still_exact':geometry['contact_disposition_scope']['passed']}
 return {'schema':'f722-native4-next-complete-physical-audit/v1','status':'COMPLETE_NATIVE_PHYSICAL_DIAGNOSTIC_NOT_ADOPTION','accepted_or_adopted':False,'source_native_sha256':plan['source_native_logical_sha256'],'candidate_native_sha256':manifest['native']['uncompressed']['sha256'],'source_board_sha256':plan['source_board_sha256'],'candidate_board_sha256':after['board_sha256'],'profile':profile['name'],'geometry_run':True,'shapely_version':shapely.__version__,'all_physical_nets':comparisons,'surviving_source_fragment_checks':lineage,'new_track_endpoint_support':endpoints,'new_via_annular_contacts':vias,'affected_pad_full_width_contacts':contacts,'all22_actual_IO_cuts':actual,'NC_external_guards':guards,'updated_branch_cut_checks':branches,'critical_geometry_plane_drill_ledger':geometry,'raw_source_gates_unchanged':source['diagnostic_gates'],'raw_source_aggregate_unchanged':source['all_required_topology_and_support_checks_passed'],'source_scoped_disposition':n.read(p['source_contact_disposition']),'source_disposition_is_not_general_waiver':True,'full_RX_protection_passed':byclamp['U15.1']['passed'],'all_22_full_protection_passed':all(x['candidate']['passed'] for x in actual),'final_release_ready':False,'new_candidate_gates':gates,'all_required_new_checks_passed':all(gates.values()),'paired_proof_sha256':n.sha(root/'paired-native-proof.json'),'fresh_DC_required':profile['allowed_power_object_changes']!=[],'current_capacity_reference_timing_SI_ESD_assembly_qualified':False}

def geometry_ledger(before,after,oldrows,newrows,oldholes,newholes,added,removed,o,k,error,moved):
 from shapely.geometry import box,LineString,Point
 from shapely.ops import unary_union
 from shapely.strtree import STRtree
 old={r['uuid']:r for r in before['objects']};new={r['uuid']:r for r in after['objects']};by={r['uuid']:r for r in newrows};shapes={};layers=defaultdict(list)
 for r in newrows:
  parts,_=k.conductive_shapes(r,newholes);shapes[r['uuid']]=parts
  for layer,s in parts.items():
   if not s.is_empty:layers[layer].append((r['uuid'],r['net'],s))
 trees={l:STRtree([s for u,net,s in rows]) for l,rows in layers.items()};clearances=[];edge=[];via_process=[];outline=k.native_polygons(after['outline_with_npth']['polygons']);minimum=.127;search=minimum+2*error
 for u in sorted(added|moved):
  r=by[u]
  for layer,s in shapes[u].items():
   if s.is_empty:clearances.append({'uuid':u,'layer':layer,'passed':False,'reason':'EMPTY_CONDUCTIVE_COPPER'});continue
   x0,y0,x1,y1=s.bounds;near=[]
   for i in trees[layer].query(box(x0-search,y0-search,x1+search,y1+search)):
    peer,net,other=layers[layer][int(i)]
    if peer!=u and net!=r['net']:near.append((s.distance(other),peer,net))
   closest=min(near) if near else None;clearances.append({'uuid':u,'layer':layer,'nearest_foreign_within_certified_search':list(closest) if closest else None,'required_mm':minimum,'native_two_boundary_allowance_mm':2*error,'passed':closest is None or closest[0]>=minimum-2*error})
   gap=s.distance(outline.boundary);edge.append({'uuid':u,'layer':layer,'edge_or_NPTH_gap_mm':gap,'required_mm':.254,'inside_board':outline.covers(s),'passed':outline.covers(s) and gap>=.254-2*error})
  if r['kind']=='via':
   hole=k.native_polygons(r['drill']['outside']);hg=[];mg=[]
   for peer in after['objects']:
    if peer['uuid']!=u and peer.get('drill'):hg.append((hole.distance(k.native_polygons(peer['drill']['outside'])),peer['uuid']))
    for l,mask in peer.get('mask',{}).items():
     if mask.get('polygons'):mg.append((hole.distance(k.native_polygons(mask['polygons'])),peer['uuid'],l))
   holes=min(hg) if hg else None;masks=min(mg) if mg else None
   via_process.append({'uuid':u,'net':r['net'],'minimum_hole_gap_mm':list(holes) if holes else None,'minimum_drill_to_open_mask_mm':list(masks) if masks else None,'required_hole_gap_mm':.25,'required_mask_gap_mm':.2,'tented':r['tented'],'passed':(holes is None or holes[0]>=.25-2*error) and (masks is None or masks[0]>=.2-2*error) and r['tented']=={'F.Mask':True,'B.Mask':True}})
 a={z['uuid']:z for z in before['zones']};b={z['uuid']:z for z in after['zones']};planes=[]
 for u,z in a.items():
  if z['rule']:continue
  for layer,ps in z['filled'].items():
   s=k.native_polygons(ps);t=k.native_polygons(b[u]['filled'][layer]);ds=s.difference(oldholes.get(layer,unary_union([])));dt=t.difference(newholes.get(layer,unary_union([])))
   planes.append({'zone_uuid':u,'net':z['net'],'layer':layer,'saved_source_mm2':s.area,'saved_candidate_mm2':t.area,'saved_added_mm2':t.difference(s).area,'saved_removed_mm2':s.difference(t).area,'own_drilled_source_mm2':ds.area,'own_drilled_candidate_mm2':dt.area,'own_drilled_added_mm2':dt.difference(ds).area,'own_drilled_removed_mm2':ds.difference(dt).area,'each_side_uses_its_own_all_physical_holes':True})
 drill_changes=[]
 for layer in before['copper_layers']:
  a0=oldholes.get(layer,unary_union([]));b0=newholes.get(layer,unary_union([]));drill_changes.append({'layer':layer,'hole_area_added_mm2':b0.difference(a0).area,'hole_area_removed_mm2':a0.difference(b0).area})
 affected=[]
 for u in sorted(set(old)&set(new)):
  previous,_=k.conductive_shapes(old[u],oldholes)
  for layer,shape in previous.items():
   current=shapes[u].get(layer,unary_union([]));loss=shape.difference(current).area;gain=current.difference(shape).area
   if loss or gain:affected.append({'uuid':u,'net':old[u]['net'],'kind':old[u]['kind'],'layer':layer,'retained_primitive_source_hash_held':old[u]==new[u],'conductive_area_removed_mm2':loss,'conductive_area_added_mm2':gain})
 refs={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','In3.Cu':'In4.Cu','B.Cu':'In4.Cu'};reference=[];affected_nets={new[u]['net'] for u in added}|{'FLASH_SCK'}
 for r in after['objects']:
  if r['kind']!='track' or r['net'] not in affected_nets:continue
  layer=next(iter(r['copper']));ref=refs[layer];plane=shapes[o['GND_planes'][ref]][ref];line=LineString([r['start'],r['end']]);outside=line.difference(plane)
  reference.append({'uuid':r['uuid'],'net':r['net'],'layer':layer,'reference_layer':ref,'length_mm':line.length,'centerline_outside_actual_GND_mm':outside.length,'copper_outside_actual_GND_mm2':shapes[r['uuid']][layer].difference(plane).area,'outside_WKT':outside.wkt if not outside.is_empty else None})
 plan=g.check_sources()['paths'];local=n.read(plan['source_local_support']);source_audit=n.read(plan['source_audit']);ids=set(local['local_native_UUID_inventory']['candidate']);record_check=all(u in old and u in new and old[u]==new[u] for u in ids);windows=o['old_native4_source_contact_windows'];window_layers={'VX_PROTECTED':'In2.Cu','LED_RED_K':'B.Cu','+3V3_CORE':'In3.Cu'};touches=[]
 for native,uids in [(old,removed|moved),(new,added|moved)]:
  for u in sorted(uids):
   r=native[u]
   for net,coords in windows.items():
    window=box(*coords);layer=window_layers[net];copper=k.native_polygons(r['copper'].get(layer,[]));drill=k.native_polygons(r['drill']['outside']) if r.get('drill') else unary_union([])
    if copper.intersects(window) or drill.intersects(window):touches.append({'uuid':u,'window_net':net,'layer':layer,'copper_overlap_mm2':copper.intersection(window).area,'drill_overlap_mm2':drill.intersection(window).area})
 no_fills=not any(ps for d in [before,after] for z in d['zones'] for layer,ps in z['filled'].items() if layer in window_layers.values());scope={'reviewed_record_UUIDs':sorted(ids),'all_reviewed_records_exact':record_check,'changed_copper_or_drills_touching_windows':touches,'no_plane_fill_on_window_layers':no_fills,'source_trim_scope_evidence_sha256':n.digest(source_audit['preserved_source_contact_windows']),'source_scoped_disposition_sha256':n.sha(plan['source_contact_disposition']),'passed':record_check and not touches and no_fills and source_audit['preserved_source_contact_windows']['passed'] is True,'raw_false_predicates_preserved':True,'general_waiver':False}
 return {'new_copper_clearances_including_actual_fills_and_polygon':clearances,'new_copper_edge_and_NPTH_clearances':edge,'new_via_process':via_process,'all_new_clearance_and_process_passed':all(x['passed'] for x in clearances+edge+via_process),'symmetric_saved_and_own_drilled_plane_differences':planes,'global_drill_footprint_differences':drill_changes,'retained_conductive_shapes_changed_by_new_holes':affected,'actual_adjacent_plane_projection':reference,'contact_disposition_scope':scope,'fresh_power_rebind_or_rerun_required':bool(via_process or any(x['saved_added_mm2'] or x['saved_removed_mm2'] for x in planes)),'source_DC_qualification_transferred':False,'assembly_body_projection_qualified':False}
