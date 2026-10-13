"""Read-only, source-bound finite v5 geometry. No acceptance or native mutation."""
import sys,math
import measure_reference as x
from shapely import wkb
from shapely.geometry import LineString,Point
from shapely.ops import unary_union,nearest_points
old,new=x.planes[0]['In4.Cu'],x.planes[1]['In4.Cu']; loss=x.lost['In4.Cu']
paths={'collar_paths':x.portable.DATA/'collar-paths.json','collar_mask':x.portable.DATA/'collar-mask.json','U15_J11':x.portable.DATA/'U15-J11-corridor.json','C3':x.portable.DATA/'C3-loop-and-feed-exception.json','return_attachments':x.O/'actual-return-geometry.json','source_annuli':x.portable.DATA/'source-return-annuli.json'}
pins={'collar_paths': 'd8b5c4fbdd73203fde8056663cca36245d90d89a28499ea4f0290a9c4b3059e9', 'collar_mask': '656f91de351a1763b02694d393797f06278a9c4812110f45107f2411efba56c2', 'U15_J11': '6a8774447ccfa8721ef63dbc00cec226d072f429885f2f8f5423c710efd4e403', 'C3': '6b076afed650dffeff73b397cc238d661f7b3230cce14d44062bf97a08c01b0d', 'source_annuli': 'cf90e979e9a1dc0c1b2018f52f12fdda604ede739dfb87b7b955879fa32e1bf8'}
for name,expected in pins.items(): assert x.sha(paths[name])==expected, name
_returns=x.read(paths['return_attachments']); assert _returns['source']['board_sha256']==x.a['board_sha256'] and _returns['candidate']['board_sha256']==x.b['board_sha256']
cp,cm,u,c3,returns,ann=[x.read(paths[k]) for k in paths]
assert cp['source_board_sha256']==x.a['board_sha256']==u['source_board_sha256']==c3['source_board_sha256']
added=unary_union([wkb.loads(r['shapes']['In4.Cu'],hex=True) for r in x.b['records'].values() if r['kind']=='track' and 'In4.Cu' in r['shapes']])
parts=x.k.polygon_parts(loss);slot=unary_union([p for p in parts if p.distance(added)<=.127+2*x.b['native_polygon_error_mm']]);residual=loss.difference(slot)
def ev(s):return {'area_mm2':s.area,'length_mm':s.length,'WKB_hex':s.wkb_hex}
def path(s):
 uncovered=s.difference(new); prior=s.difference(old);a,b=nearest_points(s,new.boundary)
 return {'length_mm':s.length,'source_uncovered_mm':prior.length,'candidate_uncovered_mm':uncovered.length,'newly_lost_mm':s.intersection(loss).length,'source_minimum_boundary_distance_mm':s.distance(old.boundary),'candidate_minimum_boundary_distance_mm':s.distance(new.boundary),'twice_minimum_boundary_distance_mm':2*s.distance(new.boundary),'limiting_path_xy':list(a.coords[0]),'limiting_candidate_boundary_xy':list(b.coords[0]),'candidate_uncovered_WKB_hex':uncovered.wkb_hex,'WKB_hex':s.wkb_hex,'finite_path_only_not_global_neck':True}
def mask(s):return {'source_supported':ev(s.intersection(old)),'source_unsupported':ev(s.difference(old)),'candidate_supported':ev(s.intersection(new)),'candidate_unsupported':ev(s.difference(new)),'newly_lost':ev(s.intersection(loss))}
def projection(uid):
 a,b=x.a['records'][uid],x.b['records'][uid];s=wkb.loads(b['shapes']['B.Cu'],hex=True)
 return {'uuid':uid,'net':b['net'],'key':b.get('key'),'record_exact':a['record_sha256']==b['record_sha256'],'source_record_sha256':a['record_sha256'],'source_unsupported_mm2':s.difference(old).area,'candidate_unsupported_mm2':s.difference(new).area,'newly_lost_reference_mm2':s.intersection(loss).area,'route_slot_margin':x.gap(s,slot,old,new),'all_loss_margin':x.gap(s,loss,old,new)}
tp2=next(r for r in x.b['records'].values() if r.get('key')=='TP2.1');tp2s=wkb.loads(tp2['shapes']['B.Cu'],hex=True);tp2mask=tp2s.buffer(.10/math.cos(math.pi/128),quad_segs=32).intersection(old)
collarmask=wkb.loads(cm['source_GND_keep_WKB_hex'],hex=True);umask=wkb.loads(u['corridor_WKB_hex'],hex=True)
curves={name:path(wkb.loads(cp[name]['WKB_hex'],hex=True)) for name in ['local_offset_midcurve','left_half_offset_path','right_half_offset_path','complete_offset_loop']}
exits=[]
for r in cp['source_to_existing_ground_via_paths']:
 exits.append({k:r[k] for k in ['via_uuid','via_xy','via_source_record_sha256','collar_exit_xy']}|{'actual_v5_path':path(wkb.loads(r['straight_path_to_actual_annulus']['WKB_hex'],hex=True))})
contacts=[]
for r in c3['actual_source_positive_contacts']:
 shapes=[wkb.loads(x.b['records'][uid]['shapes']['B.Cu'],hex=True) for uid in [r['a'],r['b']]];area=shapes[0].intersection(shapes[1]).area
 contacts.append({'a':r['a'],'b':r['b'],'source_overlap_mm2':r['area_mm2'],'candidate_overlap_mm2':area,'source_candidate_input_shapes_exact':all(x.a['records'][uid]['shapes']['B.Cu']==x.b['records'][uid]['shapes']['B.Cu'] for uid in [r['a'],r['b']]),'overlap_area_delta_from_prior_source_receipt_mm2':area-r['area_mm2'],'both_records_exact':all(x.a['records'][uid]['record_sha256']==x.b['records'][uid]['record_sha256'] for uid in [r['a'],r['b']])})
for r in c3['records']:assert x.a['records'][r['uuid']]['record_sha256']==r['source_full_record_sha256']
axis=LineString(u['endpoint_xy']);sourceaxis=axis.intersection(old);entries=[]
for uid in [u['from_via_UUID'],u['to_via_UUID']]:
 ar=next(r for r in ann['rows'] if r['uuid']==uid);sourceann=wkb.loads(ar['In4_plane_overlap_WKB_hex'],hex=True);current=sourceann.intersection(new);rt=returns['selected_return_via_attachments'][uid]
 assert rt['source_full_record_sha256']==ar['source_record_sha256'] and rt['layers']['In4.Cu']['annular_attachment_loss_mm2']==0
 overlap=umask.intersection(current);edge=umask.boundary.intersection(current);entries.append({'uuid':uid,'xy':ar['xy'],'source_annulus_WKB_hex':sourceann.wkb_hex,'actual_retained_source_annulus_mm2':current.area,'new_annular_loss_mm2':sourceann.difference(new).area,'corridor_annular_overlap':ev(overlap),'corridor_boundary_through_actual_annulus':ev(edge),'source_supported_axis_inside_annulus':path(sourceaxis.intersection(sourceann)),'all_direction_collar_receipt':rt['In4_finite_attachment_collar']})
# Measure the actual approach between the two existing land lips, excluding the preexisting bores.
anns=[wkb.loads(e['source_annulus_WKB_hex'],hex=True) for e in entries]
lip1,lip2=nearest_points(*anns);approach=LineString([lip1,lip2]);dx=(lip2.x-lip1.x)/approach.length;dy=(lip2.y-lip1.y)/approach.length;approach_sections=[]
for e,lip in zip(entries,[lip1,lip2]):
 section=LineString([(lip.x-.127*dy,lip.y+.127*dx),(lip.x+.127*dy,lip.y-.127*dx)])
 approach_sections.append({'via_uuid':e['uuid'],'lip_xy':list(lip.coords[0]),'width_mm':section.length,'source_supported_mm':section.intersection(old).length,'candidate_supported_mm':section.intersection(new).length,'newly_lost_mm':section.intersection(loss).length,'section_WKB_hex':section.wkb_hex})
approach_rectangle=approach.buffer(.127,cap_style=2)
result={'schema':'f722-source3-v5-targeted-actual-reference/v1','source':{k:x.a[k] for k in ['board_sha256','native_logical_sha256']},'candidate':{k:x.b[k] for k in ['board_sha256','native_logical_sha256']},'input_sha256':{str(p):x.sha(p) for p in paths.values()},'source_In1_exact':x.planes[0]['In1.Cu'].equals(x.planes[1]['In1.Cu']),'actual_In4_loss_mm2':loss.area,'route_associated_slot_mm2':slot.area,'remote_residual_mm2':residual.area,'TP2':{'projection':projection(tp2['uuid']),'source_pad_to_plane_boundary_mm':tp2s.distance(old.boundary),'candidate_pad_to_plane_boundary_mm':tp2s.distance(new.boundary),'source_0p10mm_collar':mask(tp2mask)},'FLASH_CS_collar':{'target_width_mm':.15,'exact_source_collar':mask(collarmask),'curves':curves,'full_exit_paths':exits,'existing_FLASH_CS_references':[{'uuid':r['uuid'],'layer':r['layer'],'source_unsupported_mm2':wkb.loads(x.b['records'][r['uuid']]['shapes'][r['layer']],hex=True).difference(old).area,'newly_lost_mm2':wkb.loads(x.b['records'][r['uuid']]['shapes'][r['layer']],hex=True).intersection(loss).area} for r in cp['nearby_FLASH_CS_reference_tracks']]},'C3':{'records':[projection(r['uuid']) for r in c3['records'] if 'B.Cu' in x.b['records'][r['uuid']]['shapes']],'direct_contacts':contacts,'feed_exception_UUIDs':c3['conditional_guard_exception']['only_track_UUIDs'],'v5_planning_feed_margins_mm':[.02824094074691537,.02824499740164932],'obsolete_0p068207_margin_used':False},'U15_J11':{'corridor_width_mm':.254,'corridor':mask(umask),'source_supported_center_axis':path(sourceaxis),'axis_baseline_bores_or_unsupported_mm':axis.difference(old).length,'annular_entries':entries,'between_annular_lips_axis':path(approach),'at_annular_lips_transverse_sections':approach_sections,'between_lips_0p254mm_rectangle':mask(approach_rectangle)},'limits':['Exact saved paths and actual own-drilled polygons; no snapping, repair or native edits.','Finite observed paths and collars do not bound loop inductance, global current capacity or ESD transient response.','0.127mm is an engineering reference from signal track width, not an enforced native plane-neck rule.','Native refill geometry is not fabrication tolerance qualification.'],'electrical_current_ESD_acceptance':'PENDING_ENGINEERING_DISPOSITION','accepted_or_adopted':False}
x.write(x.O/'targeted-actual-reference.json',result)
print(x.canon({'TP2_actual_margin_mm':result['TP2']['candidate_pad_to_plane_boundary_mm'],'TP2_collar_newloss_mm2':result['TP2']['source_0p10mm_collar']['newly_lost']['area_mm2'],'collar_newloss_mm2':result['FLASH_CS_collar']['exact_source_collar']['newly_lost']['area_mm2'],'collar_curves':{k:{q:v[q] for q in ['candidate_uncovered_mm','candidate_minimum_boundary_distance_mm']} for k,v in curves.items()},'exit_paths':[{k:r[k] for k in ['via_uuid','collar_exit_xy']}|{'path':{k:r['actual_v5_path'][k] for k in ['candidate_uncovered_mm','candidate_minimum_boundary_distance_mm']}} for r in exits],'C3_margins':[{k:r[k] for k in ['uuid','net','newly_lost_reference_mm2']}|{'slot_margin_mm':r['route_slot_margin']['distance_mm']} for r in result['C3']['records']],'U15_J11_newloss_mm2':result['U15_J11']['corridor']['newly_lost']['area_mm2']}))
