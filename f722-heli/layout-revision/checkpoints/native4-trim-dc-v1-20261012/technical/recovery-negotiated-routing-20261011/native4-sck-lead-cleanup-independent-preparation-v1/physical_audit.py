"""Only the two-track SCK physical delta is recomputed under an owner lease.
Unchanged-net findings retain exact source report and geometry-equivalence proofs.
"""
from collections import defaultdict
import copy,sys
import check_candidate as c

def run(paths,summary,prior,contracts,o):
 sys.path.insert(0,str(c.ROOT/'python-deps'))
 import shapely
 from shapely.ops import unary_union
 direct=c.load_module('trim_fixed_contact_kernels',paths['contact_adapter']);generic,k,f=direct.kernels()
 helper=c.load_module('frozen_source_physical_helpers',paths['source_physical_helper'])
 before,after=[c.read(paths[key]) for key in ['source_native','candidate_native']]
 old,new=[c.unique(native['objects']) for native in [before,after]]
 oldrows,newrows=[k.native_records_with_fills(native) for native in [before,after]]
 oldholes,newholes=[k.hole_map(rows,native['copper_layers']) for rows,native in [(oldrows,before),(newrows,after)]]
 error=max(before['maximum_polygon_error_mm'],after['maximum_polygon_error_mm'])
 added=set(summary['native4_delta']['added']);removed=set(summary['native4_delta']['removed'])
 c.require(len(added)==len(removed)==2 and all(new[u]['kind']=='track' and new[u]['net']=='FLASH_SCK' for u in added),'Only two SCK tracks permitted')
 source=c.read(paths['source_audit']);equivalence=summary['unchanged_geometry_equivalence']
 c.require(equivalence['carried_topology_predicates_have_identical_geometry_inputs'] is True,'Non-SCK reuse lacks exact geometry proof')
 rows=[r for r in newrows if r['net']=='FLASH_SCK'];previous=[r for r in oldrows if r['net']=='FLASH_SCK']
 oldg=f.rich_partition(previous,global_holes=oldholes);g=f.rich_partition(rows,global_holes=newholes)
 pads={r['uuid'] for r in rows if r['kind']=='pad'}
 def groups(graph):return [sorted({n['uuid'] for n in ns}&pads) for ns in graph['components'].values() if {n['uuid'] for n in ns}&pads]
 original=next(r for r in prior['all_physical_nets'] if r['net']=='FLASH_SCK')
 c.require(c.pair_set(groups(oldg))==c.pair_set(original['candidate_pad_partition']),'Source complete SCK topology not independently reproduced')
 comparison={'net':'FLASH_SCK',**c.compare_partitions(original,groups(g)),'pad_count':len(pads),'all_real_pads_connected':f.connected(g,sorted(pads)),'geometry_recomputed_from_actual_native':True}
 padroots=set().union(*(g['memberships'].get(u,set()) for u in pads));comparison['new_record_fragments']=[{'uuid':u,'candidate_roots':sorted(g['memberships'].get(u,set())),'every_fragment_reaches_real_pad':bool(g['memberships'].get(u,set())) and g['memberships'][u]<=padroots} for u in sorted(added)]
 comparison['route_only_components']=[{'root':root,'fragments':[{'uuid':n['uuid'],'layer':n['layer'],'bounds_mm':list(n['shape'].bounds),'area_mm2':n['shape'].area} for n in ns]} for root,ns in g['components'].items() if not {n['uuid'] for n in ns}&pads]
 lineage=[dict(net='FLASH_SCK',**r) for r in helper.surviving_fragments(oldg,g,old,removed,set())]
 endpoints=[]
 for uid in sorted(added):
  record=new[uid]
  for layer,shape in g['shapes'][uid].items():
   peers=unary_union([ls[layer] for other,ls in g['shapes'].items() if other!=uid and layer in ls and bool(g['memberships'][uid]&g['memberships'][other])])
   for point in [record['start'],record['end']]:
    centered=[r for r in rows if r['kind']=='via' and r['xy']==point and layer in g['shapes'].get(r['uuid'],{})]
    if centered:
     witnesses=[dict(via_uuid=v['uuid'],**k.full_width_witness(record,shape,g['shapes'][v['uuid']][layer],layer,error)) for v in centered]
     result={'track_uuid':uid,'endpoint':point,'layer':layer,'mode':'DRILL_SUBTRACTED_ANNULUS_INSTEAD_OF_DRILLED_CENTER','annular_witnesses':witnesses,'passed':any(w['passed'] for w in witnesses)}
    else:result=dict(track_uuid=uid,endpoint=point,mode='FULL_WIDTH_SUPPORTING_COPPER_UNION',**k.full_width_witness(record,shape,peers,layer,error,at_endpoint=point))
    endpoints.append(result)
 extra=clearance_and_reference(after,newholes,added,o,k,error,source)
 comparisons=[copy.deepcopy(r) for r in source['all_physical_nets'] if r['net']!='FLASH_SCK']+[comparison]
 for r in comparisons:
  if r['net']!='FLASH_SCK':r['reused_from_source_with_complete_identical_net_holes_fills_proof']=True
 gates=copy.deepcopy(source['diagnostic_gates'])
 for v in ['native4','native5','native6','native7']:gates['no_'+v+'_physical_pad_pair_losses']=all(not r[v+'_lost_pad_pairs'] for r in comparisons)
 gates.update(all_new_track_endpoints_union_or_annulus_supported=len(endpoints)==4 and all(r['passed'] for r in endpoints),all_surviving_native4_object_fragments_preserved=all(r['passed'] for r in lineage),every_new_copper_fragment_reaches_real_pad=all(r['every_fragment_reaches_real_pad'] for r in comparison['new_record_fragments']),all_new_copper_clearances_including_polygon_and_fills=extra['new_copper_clearance_passed'],complete_SCK_original_tree_and_all_terminals=len(pads)==2 and comparison['all_real_pads_connected'] and not comparison['route_only_components'],all_unchanged_net_predicates_have_exact_full_geometry_inputs=equivalence['carried_topology_predicates_have_identical_geometry_inputs'],saved_and_own_drilled_planes_unchanged=equivalence['symmetric_saved_and_own_drilled_plane_delta_is_zero_by_exact_input_equality'],native_geometric_DRC_errors_zero=summary['raw_native_DRC_error_count']==0,raw_native_open_count_held=summary['raw_native_DRC_counts']['unconnected_items']==4)
 result=copy.deepcopy(source);result.update(summary)
 result.update(status='NARROW_TWO_TRACK_SCK_PHYSICAL_DIAGNOSTIC_NOT_ACCEPTANCE',geometry_run=True,shapely_version=shapely.__version__,all_physical_nets=sorted(comparisons,key=lambda r:r['net']),new_track_endpoint_support=endpoints,new_via_annular_contacts=[],source_new_via_annular_contacts_preserved=source['new_via_annular_contacts'],surviving_native4_fragment_checks=[r for r in source['surviving_native4_fragment_checks'] if r['net']!='FLASH_SCK']+lineage,changed_via_plane_and_clearance_review=extra,diagnostic_gates=gates,all_required_topology_and_support_checks_passed=all(gates.values()),source_actual_IO_checks_reused_with_identical_complete_net_geometry=True,source_actual_IO_audit_sha256=c.sha(paths['source_audit']),current_source_checks_reused_explicitly=True,full_RX_protection_passed=False,hardware_current_AC_oscillator_ESD_reference_power_qualified=False)
 for v in ['native4','native5','native6','native7']:result[v+'_lost_pad_pair_count']=sum(len(r[v+'_lost_pad_pairs']) for r in comparisons)
 return result

def clearance_and_reference(after,holes,added,o,k,error,source):
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
    c.require(not via_rows,'Two-track trim unexpectedly contains a new via')
    prior=source['changed_via_plane_and_clearance_review']
    return {'new_copper_clearance_checks':clearances,'new_copper_clearance_passed':len(clearances)==2 and all(r['passed'] for r in clearances),'new_via_GND_plane_checks':prior['new_via_GND_plane_checks'],'new_via_GND_plane_clearances_passed':prior['new_via_GND_plane_clearances_passed'],'declared_GND_stitch_support_passed':prior['declared_GND_stitch_support_passed'],'GND_via_checks_reused_only_after_exact_all_drills_fills_and_records_equality':True,'actual_SCK_reference_projection':projections,'actual_SCK_length_mm':sum(r['centerline_length_mm'] for r in projections),'actual_SCK_centerline_outside_refilled_GND_mm':sum(r['centerline_outside_refilled_GND_mm'] for r in projections),'symmetric_saved_and_own_drilled_plane_deltas':{'added_mm2':0.0,'removed_mm2':0.0,'proof':'Complete source/candidate filled contours and all physical drill owner records are exactly identical.'},'historical_native4_to_stitch_symmetric_plane_delta':c.ANCHORS['source_symmetric_planes'],'signal_integrity_current_ESD_reference_or_assembly_qualified':False,'RED_assembly_disposition':prior['RED_assembly_disposition']}
