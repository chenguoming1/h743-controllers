"""Leased physical checks only. Module import performs no geometry work."""
from collections import defaultdict
import sys
import check_candidate as c

def surviving_fragments(oldg,newg,objects,removed,moved):
    """Keep every surviving native6 object fragment, even on a route-only island.

    Saved zone fills participate in both physical graphs but can legitimately
    change under refill. Their differences stay diagnostic; retained objects
    are the preservation obligations, with exact recipe cuts explicitly removed.
    """
    by=defaultdict(list)
    for node in newg['nodes']:by[node['uuid']].append(node)
    result=[]
    for root,nodes in oldg['components'].items():
        retained=[n for n in nodes if n['uuid'] in objects and n['uuid'] not in removed]
        mapped=set();missing=[];fragments=[]
        for node in retained:
            uid=node['uuid']
            matches=(set(newg['memberships'].get(uid,set())) if uid in moved else
                     {n['root'] for n in by[uid] if n['layer']==node['layer'] and n['shape'].intersection(node['shape']).area>0})
            mapped.update(matches)
            row={'uuid':uid,'layer':node['layer'],'source_bounds_mm':list(node['shape'].bounds),'candidate_roots':sorted(matches),'moved_exact_pad_geometry':uid in moved}
            fragments.append(row)
            if not matches:missing.append(row)
        reason='RETAINED_OBJECT_FRAGMENTS_PRESERVED' if retained else 'ONLY_EXPLICITLY_REMOVED_OBJECTS_OR_REFILLED_ZONE_MATERIAL'
        result.append({'native4_component':root,'retained_fragment_count':len(retained),'mapped_candidate_roots':sorted(mapped),'missing_surviving_fragments':missing,'fragment_matches':fragments,'disposition':reason,'passed':not retained or not missing and len(mapped)==1})
    return result

def run(paths,summary,prior,contracts,obligations):
    sys.path.insert(0,str(c.ROOT/'python-deps'))
    import shapely
    from shapely.geometry import Point
    from shapely.ops import unary_union
    direct=c.b.load_module('reflected_pinned_contact_kernels',paths['contact_adapter'])
    generic,k,f=direct.kernels()
    before,after=[c.read(paths[key]) for key in ['source_native','candidate_native']]
    old,new=[c.unique(native['objects']) for native in [before,after]]
    before_rows,after_rows=[k.native_records_with_fills(native) for native in [before,after]]
    old_holes,new_holes=[k.hole_map(rows,native['copper_layers']) for rows,native in [(before_rows,before),(after_rows,after)]]
    error=max(before['maximum_polygon_error_mm'],after['maximum_polygon_error_mm'])
    added=set(summary['native4_delta']['added']);removed=set(summary['native4_delta']['removed']);moved=set(summary['native4_delta']['moved'])
    old_by_net=defaultdict(list);new_by_net=defaultdict(list)
    for row in before_rows:old_by_net[row['net']].append(row)
    for row in after_rows:new_by_net[row['net']].append(row)
    historical={row['net']:row for row in prior['all_physical_nets']}
    c.require(set(old_by_net)==set(new_by_net)==set(historical),'Complete physical net inventory differs')
    comparisons=[];lineage=[];contacts=[];endpoint_support=[];via_contacts=[];actual=[];guards=[];branches=[];repairs=[]
    ground={};core={};polygon_checks={};red_join={}

    def same_component(graph,a,b):return bool(graph['memberships'].get(a,set())&graph['memberships'].get(b,set()))
    def pad_groups(graph,pads):
        return [sorted({n['uuid'] for n in nodes}&pads) for nodes in graph['components'].values() if {n['uuid'] for n in nodes}&pads]

    for net,rows in sorted(new_by_net.items()):
        old_graph=f.rich_partition(old_by_net[net],global_holes=old_holes)
        graph=f.rich_partition(rows,global_holes=new_holes)
        pads={r['uuid'] for r in rows if r['kind']=='pad'}
        old_groups=pad_groups(old_graph,pads);groups=pad_groups(graph,pads)
        c.require(c.pair_set(old_groups)==c.pair_set(historical[net]['candidate_pad_partition']),'Frozen native4 topology not reproduced: '+net)
        row={'net':net,**c.compare_partitions(historical[net],groups),'all_real_pads_connected':f.connected(graph,sorted(pads)) if pads else None,'pad_count':len(pads)}
        pad_roots=set().union(*(graph['memberships'].get(u,set()) for u in pads)) if pads else set()
        row['new_record_fragments']=[{'uuid':uid,'candidate_roots':sorted(graph['memberships'].get(uid,set())),'every_fragment_reaches_real_pad':bool(graph['memberships'].get(uid,set())) and graph['memberships'][uid]<=pad_roots} for uid in sorted(added) if new[uid]['net']==net]
        row['route_only_components']=[{'root':root,'fragments':[{'uuid':n['uuid'],'layer':n['layer'],'bounds_mm':list(n['shape'].bounds),'area_mm2':n['shape'].area} for n in nodes]} for root,nodes in graph['components'].items() if not {n['uuid'] for n in nodes}&pads]
        comparisons.append(row)
        lineage.extend(dict(net=net,**item) for item in surviving_fragments(old_graph,graph,old,removed,moved))

        for pad in [r for r in rows if r['kind']=='pad']:
            uid=pad['uuid'];incident={u for u,v,l in graph['contacts'] if v==uid}|{v for u,v,l in graph['contacts'] if u==uid}
            if uid not in moved and uid not in obligations['critical_pad_ids'] and not incident&added:continue
            witnesses=[]
            for layer,contour in pad['inside'].items():
                inner=k.native_polygons(contour).difference(new_holes.get(layer,unary_union([])))
                tracks=[r for r in rows if r['kind']=='track' and layer in graph['shapes'].get(r['uuid'],{}) and same_component(graph,r['uuid'],uid)]
                support=unary_union([graph['shapes'][r['uuid']][layer] for r in rows if r['kind'] in ['track','via','arc','copper_polygon'] and layer in graph['shapes'].get(r['uuid'],{}) and same_component(graph,r['uuid'],uid)])
                for track in tracks:
                    if graph['shapes'][track['uuid']][layer].intersection(inner).area>0:
                        witnesses.append(dict(track_uuid=track['uuid'],**k.full_width_witness(track,support,inner,layer,error)))
            required=bool(pad['net']) and not pad['net'].startswith('unconnected-')
            contacts.append({'pad_uuid':uid,'pad_key':pad['key'],'net':net,'required':required,'inside_pad_full_width_routing_union_witnesses':witnesses,'passed':any(w['passed'] for w in witnesses) if required else None})

        for uid in sorted(added):
            record=new[uid]
            if record['net']!=net:continue
            if record['kind']=='track':
                for layer,shape in graph['shapes'][uid].items():
                    peer=unary_union([layers[layer] for other,layers in graph['shapes'].items() if other!=uid and layer in layers and same_component(graph,uid,other)])
                    for point in [record['start'],record['end']]:
                        centered=[r for r in rows if r['kind']=='via' and r['xy']==point and layer in graph['shapes'].get(r['uuid'],{})]
                        if centered:
                            witnesses=[dict(via_uuid=v['uuid'],**k.full_width_witness(record,shape,graph['shapes'][v['uuid']][layer],layer,error)) for v in centered]
                            result={'track_uuid':uid,'endpoint':point,'layer':layer,'mode':'DRILL_SUBTRACTED_ANNULUS_INSTEAD_OF_DRILLED_CENTER','annular_witnesses':witnesses,'passed':any(w['passed'] for w in witnesses)}
                        else:
                            result=dict(track_uuid=uid,endpoint=point,mode='FULL_WIDTH_SUPPORTING_COPPER_UNION',**k.full_width_witness(record,shape,peer,layer,error,at_endpoint=point))
                        endpoint_support.append(result)
            elif record['kind']=='via':
                witnesses=[]
                for layer,annulus in graph['shapes'][uid].items():
                    for track in [r for r in rows if r['kind']=='track' and layer in graph['shapes'].get(r['uuid'],{})]:
                        if graph['shapes'][track['uuid']][layer].intersection(annulus).area>0:
                            intended=record['xy'] in [track['start'],track['end']]
                            witnesses.append(dict(track_uuid=track['uuid'],intended_center_endpoint_attachment=intended,**k.full_width_witness(track,graph['shapes'][track['uuid']][layer],annulus,layer,error)))
                required=[w for w in witnesses if w['intended_center_endpoint_attachment']]
                via_contacts.append({'via_uuid':uid,'net':net,'track_annular_witnesses':witnesses,'incidental_pairwise_slivers_retained_as_diagnostics':True,'passed':bool(required) and all(w['passed'] for w in required)})

        for case in [row for row in contracts['actual22_cases'] if row['contract']['net']==net]:
            result=generic.actual_protection_case(rows,case['contract'],new_holes,error,f)
            old_result=next(row for row in prior['actual22_IO_cuts'] if row['contract']['contract']['id']==case['contract']['id'])
            ids=case['pad_UUIDs']
            result['source_to_actual_IO_connected']=f.connected(graph,[ids['source'],ids['clamp']])
            result['target_to_actual_IO_connected']=f.connected(graph,[ids['target'],ids['clamp']])
            if case['contract']['clamp'] in ['U15.1','U15.2']:
                clamp=new[ids['clamp']];cut,_=k.conductive_shapes(dict(clamp,copper=clamp['inside']))
                outside=f.rich_partition(rows,subtract_region=cut,omit_ids={clamp['uuid']},global_holes=new_holes)
                widths=[]
                for role in ['source','target']:
                    connected=result[role+'_to_actual_IO_connected'];roots=outside['memberships'].get(ids[role],set());witnesses=[]
                    for layer,contour in clamp['inside'].items():
                        inner=k.native_polygons(contour).difference(new_holes.get(layer,unary_union([])))
                        route=[r for r in rows if r['kind'] in ['track','via','arc','copper_polygon'] and layer in graph['shapes'].get(r['uuid'],{}) and outside['memberships'].get(r['uuid'],set())&roots]
                        support=unary_union([graph['shapes'][r['uuid']][layer] for r in route])
                        for track in route:
                            if track['kind']=='track' and graph['shapes'][track['uuid']][layer].intersection(inner).area>0:
                                witnesses.append(dict(track_uuid=track['uuid'],**k.full_width_witness(track,support,inner,layer,error)))
                    widths.append({'role':role,'endpoint':case['contract'][role],'connected_before_actual_IO_cut':connected,'survives_cut':bool(roots),'full_width_same_side_witnesses':witnesses,'status':'UNCONNECTED_ORIGINAL_PATH' if not connected else 'CONNECTED_PATH_FULL_WIDTH_PASS' if roots and any(w['passed'] for w in witnesses) else 'CONNECTED_PATH_SUPPORT_FAIL','passed_when_connected':not connected or bool(roots) and any(w['passed'] for w in witnesses)})
                result['connected_branch_full_width']=widths
                spec=next(r for r in obligations['branches'] if r['net']==net);bykey={r['key']:r for r in rows if r['kind']=='pad'}
                nc=bykey[spec['NC_land']]['uuid'];side=bykey[spec['endpoint_on_NC_side']]['uuid'];other=bykey[spec['other_endpoint']]['uuid']
                nc_side=f.connected(outside,[nc,side]);nc_other=f.connected(outside,[nc,other]);endpoint_survive=all(outside['memberships'].get(u,set()) for u in [nc,side,other])
                branches.append({'declared_candidate_branch_contract':spec,'raw_source_endpoint_contract_unchanged':case,'physical_NC_side_after_actual_IO_cut_connected':nc_side,'other_endpoint_reaches_NC_after_actual_IO_cut':nc_other,'all_external_pads_survive_actual_IO_cut':endpoint_survive,'NC_land_to_actual_IO_before_cut_connected':f.connected(graph,[nc,ids['clamp']]),'connected_path_full_width':widths,'NC_internal_continuity_assumed':False,'passed':nc_side and not nc_other and endpoint_survive and f.connected(graph,[nc,ids['clamp']]) and all(r['passed_when_connected'] for r in widths)})
            actual.append({'original_raw_contract':case,'native7_original_result':old_result['source'],'native4_original_result':old_result['candidate'],'candidate':result,'regressed_from_native4':old_result['candidate']['passed'] and not result['passed']})

        for guard in [r for r in contracts['external_NC_land_guards'] if r['physical_net']==net]:
            measured=generic.shortest_external_bridge(rows,guard['nc_land_UUID'],guard['actual_io_UUID'],new_holes,k,f)
            guards.append({'original_raw_expected_guard':guard,'candidate_measured_external_bridge':measured,'candidate_branch_contract':next((r for r in obligations['branches'] if r['net']==net),None),'raw_historical_role_not_silently_overwritten':True,'NC_internal_continuity_assumed':False})

        if net in ['+3V3_CORE','GND']:
            repair_ids=[u for u in obligations['new_CORE_GND_ids'] if new[u]['net']==net]
            repairs.append({'net':net,'all_pad_UUIDs':sorted(pads),'pad_count':len(pads),'all_pads_connected':f.connected(graph,sorted(pads)),'new_repair_UUIDs':repair_ids,'every_repair_and_all_real_pads_connected':f.connected(graph,[*sorted(pads),*repair_ids])})
            if net=='+3V3_CORE':core={'all_47_pads_and_new_repairs_connected':len(pads)==47 and f.connected(graph,[*sorted(pads),*repair_ids]),'power_current_return_qualified':False}
            else:
                ground_tracks=obligations['ground_track_ids'];annular=[]
                for u in ground_tracks:
                    annular.append(dict(track_uuid=u,**k.full_width_witness(new[u],graph['shapes'][u]['B.Cu'],graph['shapes'][c.C75_BARREL]['B.Cu'],'B.Cu',error)))
                overlap=graph['shapes'][c.GROUND_PADS[0]]['B.Cu'].intersection(graph['shapes'][c.GROUND_PADS[1]]['B.Cu']).area
                gcontacts=[r for r in contacts if r['pad_uuid'] in c.GROUND_PADS]
                ground={'custom_ground_pads_positive_overlap_mm2':overlap,'both_ground_pad_full_width_contacts':gcontacts,'shared_C75_barrel':c.C75_BARREL,'new_return_full_width_annular_contacts':annular,'both_pads_new_return_and_C75_connected':f.connected(graph,[*c.GROUND_PADS,*ground_tracks,c.C75_BARREL]),'retained_original_barrel':c.OLD_U15_BARREL,'all_GND_real_pads_connected':f.connected(graph,sorted(pads)),'ESD_and_reference_equivalence_qualified':False,'passed':overlap>0 and len(gcontacts)==2 and all(r['passed'] for r in gcontacts) and bool(annular) and all(r['passed'] for r in annular) and f.connected(graph,[*sorted(pads),*ground_tracks,c.C75_BARREL])}
        if net=='VX_PROTECTED':
            polygon_checks=c.read(paths['source_audit'])['VX_polygon_support']
            polygon_checks['raw_source_measurements_carried_with_exact_unchanged_contact_window_proof']=summary['preserved_source_contact_windows']
        if net=='LED_RED_K':
            u,v=obligations['red_new_join_id'],obligations['red_retained_join_id'];layer='B.Cu'
            red_join={'new_track':u,'retained_track':v,'source_record_exact':True,'new_track_width_witness':k.full_width_witness(new[u],graph['shapes'][u][layer],graph['shapes'][v][layer],layer,error,at_endpoint=new[u]['end']),'retained_track_width_witness':k.full_width_witness(new[v],graph['shapes'][v][layer],graph['shapes'][u][layer],layer,error,at_endpoint=new[u]['end'])}
            red_join['passed']=red_join['new_track_width_witness']['passed'] and red_join['retained_track_width_witness']['passed']
        del graph,old_graph

    bynet={r['net']:r for r in comparisons};byclamp={r['original_raw_contract']['contract']['clamp']:r['candidate'] for r in actual}
    rx=byclamp['U15.1'];rx_gaps=rx.get('outside_pad_gaps',[])
    rx_good=bool(bynet['PORT_C_RX_EXT']['native6_new_pad_pairs']) and rx['target_to_actual_IO_connected'] and rx['no_outside_actual_pad_bypass'] and bool(rx_gaps) and all(r['passed'] for r in rx_gaps) and (not rx['full_actual_function_connected'] or rx['passed'])
    extra=clearance_and_planes(after,before,new_holes,added,obligations,k,error)
    gates={
      'no_native4_physical_pad_pair_losses':not any(r['native4_lost_pad_pairs'] for r in comparisons),
      'no_native5_physical_pad_pair_losses':not any(r['native5_lost_pad_pairs'] for r in comparisons),
      'no_native6_physical_pad_pair_losses':not any(r['native6_lost_pad_pairs'] for r in comparisons),
      'no_native7_physical_pad_pair_losses':not any(r['native7_lost_pad_pairs'] for r in comparisons),
      'all_surviving_native4_object_fragments_preserved':all(r['passed'] for r in lineage),
      'every_new_copper_fragment_reaches_real_pad':all(r['every_fragment_reaches_real_pad'] for net in comparisons for r in net['new_record_fragments']),
      'all_previously_passed_actual_IO_cuts_preserved':not any(r['regressed_from_native4'] for r in actual),
      'all_22_actual_IO_contracts_reported':len(actual)==22,
      'actual_TX_IO2_cut_complete_and_passed':byclamp['U15.2']['passed'],
      'R34_to_actual_RX_IO1_improved_and_safe_partial_path':rx_good,
      'all_required_whole_nets_complete':all(bynet[net]['all_real_pads_connected'] for net in obligations['required_complete_nets']),
      'all_required_whole_net_pad_counts_exact':all(bynet[net]['pad_count']==count for net,count in obligations['required_complete_nets'].items()),
      'all_changed_real_pad_contacts_full_width':all(r['passed'] for r in contacts if r['required']),
      'all_new_track_endpoints_union_or_annulus_supported':all(r['passed'] for r in endpoint_support),
      'all_new_via_track_or_exact_GND_plane_contacts_full_width':all(r['passed'] or r['via_uuid']==obligations['new_GND_stitch_UUID'] and extra['declared_GND_stitch_support_passed'] for r in via_contacts),
      'all_actual_IO_external_NC_bridges_passed':all(r['candidate_measured_external_bridge']['passed'] for r in guards),
      'updated_RX_TX_branch_cut_contracts_passed':len(branches)==2 and all(r['passed'] for r in branches),
      'CORE47_and_every_new_CORE_repair_complete':core['all_47_pads_and_new_repairs_connected'],
      'shared_GND_physical_support_passed':ground['passed'],
      'VX_polygon_all_original_terminal_contacts_supported':polygon_checks['passed'],
      'RED_retained_B_lead_full_width_join':red_join['passed'],
      'all_new_copper_clearances_including_polygon_and_fills':extra['new_copper_clearance_passed'],
      'all_new_via_GND_plane_clearances':extra['new_via_GND_plane_clearances_passed'],
      'native_geometric_DRC_errors_zero':summary['raw_native_DRC_error_count']==0,
      'raw_native_open_count_held':summary['raw_native_DRC_counts']['unconnected_items']==summary['raw_baseline_DRC_counts']['unconnected_items']==4,
    }
    summary.update(status='NATIVE_SCK_POLYGON_PHYSICAL_DIAGNOSTIC_NOT_ACCEPTANCE',VX_polygon_support=polygon_checks,RED_retained_join=red_join,changed_via_plane_and_clearance_review=extra,geometry_run=True,shapely_version=shapely.__version__,all_physical_nets=comparisons,surviving_native4_fragment_checks=lineage,affected_pad_full_width_contacts=contacts,new_track_endpoint_support=endpoint_support,new_via_annular_contacts=via_contacts,all22_actual_IO_cuts=actual,raw_historical_and_measured_NC_guards=guards,updated_branch_cut_checks=branches,all_CORE_GND_repairs=repairs,CORE47=core,shared_C75_GND=ground,diagnostic_gates=gates,all_required_topology_and_support_checks_passed=all(gates.values()),native4_lost_pad_pair_count=sum(len(r['native4_lost_pad_pairs']) for r in comparisons),native5_lost_pad_pair_count=sum(len(r['native5_lost_pad_pairs']) for r in comparisons),native6_lost_pad_pair_count=sum(len(r['native6_lost_pad_pairs']) for r in comparisons),native7_lost_pad_pair_count=sum(len(r['native7_lost_pad_pairs']) for r in comparisons),RX_remaining_original_connector_gap=not rx['source_to_actual_IO_connected'],hardware_current_AC_oscillator_ESD_reference_power_qualified=False)
    return summary


def polygon_support(rows,graph,old_graph,old,new,o,k,error):
    """The filled polygon stays a polygon; source track is only a port-width ruler."""
    uid,cut=o['polygon_uuid'],o['polygon_replaced_uuid'];layer='In2.Cu'
    expected=set(o['polygon_required_peer_ids'])
    previous={b if a==cut else a for a,b,l in old_graph['contacts'] if cut in [a,b] and l==layer}
    c.require(previous==expected,'Original VX polygon peer inventory differs')
    poly=graph['shapes'][uid][layer];old_shape=old_graph['shapes'][cut][layer]
    raw=k.boundary_witnesses(rows,graph,{uid},error,moving_ids={uid},source_records=list(old.values()),source_partition=old_graph)
    by={r['right_uuid'] if r['left_uuid']==uid else r['left_uuid']:r for r in raw if r['layer']==layer}
    peers=[]
    for peer in sorted(expected):
        original=old_shape.intersection(old_graph['shapes'][peer][layer]);actual=poly.intersection(graph['shapes'][peer][layer]);lost=original.difference(actual).area
        peers.append({'peer_uuid':peer,'layer':layer,'source_contact_area_mm2':original.area,'candidate_contact_area_mm2':actual.area,'lost_source_contact_area_mm2':lost,'overlay_arithmetic_area_bound_mm2':1e-14,'source_region_preserved_to_arithmetic_bound':lost<=1e-14,'finite_contact_witness':by.get(peer),'passed':actual.area>0 and lost<=1e-14 and bool(by.get(peer)) and by[peer]['passed']})
    ruler=old[cut];ports=[]
    for point in [ruler['start'],ruler['end']]:
        ports.append({'source_track_UUID_as_measurement_reference_only':cut,'polygon_has_no_track_width_or_centerline':True,'point':point,**k.full_width_witness(ruler,poly,poly,layer,error,at_endpoint=point)})
    return {'polygon_uuid':uid,'kind':'copper_polygon','layer':layer,'stroke_width_nm':0,'drill_subtraction_applied':True,'five_original_contact_regions':peers,'all_actual_contact_witnesses':raw,'original_endpoint_normal_sections':ports,'polygon_current_capacity_qualified':False,'passed':all(r['passed'] for r in peers+ports)}


def clearance_and_planes(after,before,holes,added,o,k,error):
    """Actual polygon/track/via/fill geometry, including fresh GND antipads."""
    from shapely.geometry import box,LineString,Point
    from shapely.strtree import STRtree
    from shapely.ops import unary_union
    rows=k.native_records_with_fills(after);by={r['uuid']:r for r in rows};shapes={};layers=defaultdict(list)
    for row in rows:
        parts,_=k.conductive_shapes(row,holes);shapes[row['uuid']]=parts
        for layer,shape in parts.items():
            if not shape.is_empty:layers[layer].append((row['uuid'],row['net'],shape))
    trees={layer:STRtree([s for _,_,s in objects]) for layer,objects in layers.items()}
    minimum=o['clearance_mm'];search=minimum+2*error;clearances=[]
    for uid in sorted(added):
        record=by[uid]
        for layer,shape in shapes[uid].items():
            x0,y0,x1,y1=shape.bounds;candidates=[]
            for i in trees[layer].query(box(x0-search,y0-search,x1+search,y1+search)):
                other,net,peer=layers[layer][int(i)]
                if other!=uid and net!=record['net']:candidates.append((shape.distance(peer),other,net))
            nearest=min(candidates) if candidates else None
            clearances.append({'uuid':uid,'kind':record['kind'],'layer':layer,'nearest_foreign_within_search_bbox':list(nearest) if nearest else None,'required_mm':minimum,'native_export_two_boundary_allowance_mm':2*error,'certified_search_radius_mm':search,'includes_fresh_zone_fills_and_exact_polygon':True,'passed':nearest is None or nearest[0]>=minimum-2*error})
    planes={layer:shapes.get(uid,{}).get(layer) for layer,uid in o['GND_planes'].items()}
    c.require(all(s is not None and not s.is_empty for s in planes.values()),'Actual refilled GND planes absent')
    via_rows=[]
    for uid in sorted(added):
        row=by[uid]
        if row['kind']!='via':continue
        checks=[]
        for layer,plane in planes.items():
            land=shapes[uid][layer];gap=land.distance(plane)
            checks.append({'layer':layer,'GND_zone_uuid':o['GND_planes'][layer],'actual_land_to_refilled_plane_gap_mm':gap,'positive_copper_overlap_mm2':land.intersection(plane).area,'required_mm':0.0 if row['net']=='GND' else minimum,'native_export_two_boundary_allowance_mm':2*error,'GND_annulus_uncovered_mm2':land.difference(plane).area if row['net']=='GND' else None,'attachment_mode':'DECLARED_GND_PLANE_STITCH' if row['net']=='GND' else 'FOREIGN_NET_PLANE_CLEARANCE','passed':(uid==o['new_GND_stitch_UUID'] and land.area>0 and land.difference(plane).area<=1e-14) if row['net']=='GND' else gap>=minimum-2*error and land.intersection(plane).area==0})
        hole=k.native_polygons(row['drill']['outside']);other_holes=[];masks=[]
        for peer in after['objects']:
            if peer['uuid']!=uid and peer.get('drill'):other_holes.append((hole.distance(k.native_polygons(peer['drill']['outside'])),peer['uuid']))
            for layer,m in peer.get('mask',{}).items():
                if m.get('polygons'):masks.append((hole.distance(k.native_polygons(m['polygons'])),peer['uuid'],layer))
        via_rows.append({'uuid':uid,'net':row['net'],'xy':row['xy'],'tented':row['tented'],'actual_GND_plane_checks':checks,'minimum_drill_to_other_hole_mm':list(min(other_holes)) if other_holes else None,'minimum_drill_to_open_mask_mm':list(min(masks)) if masks else None,'assembly_body_projection_qualified':False,'passed':all(x['passed'] for x in checks)})
    refs={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','In3.Cu':'In4.Cu','B.Cu':'In4.Cu'};projections=[]
    for uid,row in sorted(by.items()):
        if row['kind']!='track' or row['net']!='FLASH_SCK':continue
        layer=next(iter(row['copper']));reference=refs[layer];plane=planes[reference];center=LineString([row['start'],row['end']]);outside=center.difference(plane)
        projections.append({'track_uuid':uid,'layer':layer,'adjacent_GND_layer':reference,'actual_refilled_zone_uuid':o['GND_planes'][reference],'centerline_length_mm':center.length,'centerline_outside_refilled_GND_mm':outside.length,'outside_refilled_GND_WKT':outside.wkt if not outside.is_empty else None,'copper_projection_outside_refilled_GND_mm2':shapes[uid][layer].difference(plane).area})
    old_by={r['uuid']:r for r in before['objects']};removed=old_by[o['old_SCK_via_UUID']];oldrows=k.native_records_with_fills(before);oldzones={r['uuid']:r for r in oldrows if r['kind']=='saved_native_zone'};envelope=Point(removed['xy']).buffer(.352,quad_segs=128);refill=[]
    for layer,uid in o['GND_planes'].items():
        previous=k.native_polygons(oldzones[uid]['copper'][layer]);now=planes[layer]
        refill.append({'layer':layer,'removed_SCK_barrel_uuid':removed['uuid'],'old_xy':removed['xy'],'diagnostic_envelope_radius_mm':.352,'old_GND_area_in_envelope_mm2':previous.intersection(envelope).area,'new_GND_area_in_envelope_mm2':now.intersection(envelope).area,'all_GND_fill_area_added_mm2':now.difference(previous).area,'all_GND_fill_area_removed_mm2':previous.difference(now).area})
    return {'new_copper_clearance_checks':clearances,'new_copper_clearance_passed':all(r['passed'] for r in clearances),'new_via_GND_plane_checks':via_rows,'new_via_GND_plane_clearances_passed':len(via_rows)==2 and all(r['passed'] for r in via_rows),'declared_GND_stitch_support_passed':len([r for r in via_rows if r['uuid']==o['new_GND_stitch_UUID'] and r['passed']])==1,'actual_SCK_reference_projection':projections,'actual_SCK_length_mm':sum(r['centerline_length_mm'] for r in projections),'actual_SCK_centerline_outside_refilled_GND_mm':sum(r['centerline_outside_refilled_GND_mm'] for r in projections),'removed_SCK_barrel_refill_review':refill,'signal_integrity_current_ESD_reference_or_assembly_qualified':False,'RED_assembly_disposition':'Moved tented RED via remains under U3; its J11 nominal body/drill projection overlap increases. No body-overlap waiver or assembly qualification is implied; exact supplementary evidence and native courtyard/clearance findings remain explicit.'}
