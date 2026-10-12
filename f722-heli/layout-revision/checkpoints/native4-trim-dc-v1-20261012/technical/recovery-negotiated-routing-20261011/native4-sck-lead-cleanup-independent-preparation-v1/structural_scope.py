"""Exact two-track SCK trim structural and inherited contact-window scope."""
import check_candidate as c

def bounds(polygons):
 points=[xy for p in polygons for xy in p['outer']]
 if not points:return None
 x,y=zip(*points);return [min(x),min(y),max(x),max(y)]

def structural_view(path):
 d=c.read(path);hashes={};copper_bounds={};drill_bounds={}
 nets=list(c.read(c.ANCHORS['power_scope']['path'])['pad_inventory']);c.require(len(nets)==15,'Exact15power net scope required')
 d['_power_networks']={net:{'objects':len([r for r in d['objects'] if r['net']==net]),'ordered_objects_sha256':c.digest([r for r in d['objects'] if r['net']==net]),'ordered_saved_zones_sha256':c.digest([z for z in d['zones'] if not z['rule'] and z['net']==net])} for net in nets}
 holes=[r for r in d['objects'] if r.get('drill')];c.require(len(holes)==326,'Exact326hole owners required');d['_holes_ordered_sha']=c.digest(holes);del holes
 d['_full_zones_sha']=c.digest(d['zones'])
 d['_per_net_full_records']={net:c.digest([r for r in d['objects'] if r['net']==net]) for net in {r['net'] for r in d['objects']}}
 for row in d['objects']:
  uid=row['uuid'];c.require(uid not in hashes,'Duplicate native UUID')
  hashes[uid]={'native':c.digest(row),'comparison':c.digest(dict(row,net_code=0))}
  copper_bounds[uid]={layer:bounds(p) for layer,p in row['copper'].items()}
  if row.get('drill'):drill_bounds[uid]=bounds(row['drill']['outside'])
  if row['kind']!='copper_polygon':
   row['copper']={l:[] for l in row['copper']}
   if 'inside' in row:row['inside']={l:[] for l in row['inside']}
   for mask in row.get('mask',{}).values():
    if isinstance(mask,dict) and 'polygons' in mask:mask['polygons']=[]
 for z in d['zones']:
  z['filled']={l:[] for l in z['filled']}
  if 'fill_representation' in z:z['fill_representation']=None
 d['_object_hashes']=hashes;d['_copper_bounds']=copper_bounds;d['_drill_bounds']=drill_bounds;return d

def verify_recipe(recipe,previous,delta):
 changed={'proposed_add_tracks','proposed_add_vias','handoff_path','handoff_sha256'}
 c.require({k:v for k,v in recipe.items() if k not in changed}=={k:v for k,v in previous.items() if k not in changed},'Unrelated cumulative source7 recipe change')
 cuts=set(delta['remove_native4_records']);c.require(len(cuts)==2,'Exactly two SCK track removals required')
 for name,added in [('proposed_add_tracks',delta['add_tracks']),('proposed_add_vias',delta['add_vias'])]:
  c.require(recipe[name]==[r for r in previous[name] if r['uuid'] not in cuts]+added,'Unexpected cumulative additions changed')
 c.require(len(delta['add_tracks'])==2 and delta['add_vias']==[] and {r['net'] for r in delta['add_tracks']}=={'FLASH_SCK'} and all(r['layer']=='In2.Cu' and r['width']==.127 for r in delta['add_tracks']),'Exact return stitch additions required')
 c.require(delta['all_other_native4_objects_held']==2450 and delta['both_via_sites_and_all_other_nets_poses_pads_planes_unchanged'] is True,'Retained scope declaration missing')
 return {'removed':sorted(cuts),'added':sorted(r['uuid'] for r in delta['add_tracks']+delta['add_vias']),'moved':[]}

def compare(before,after,delta,poly):
 old,new=[c.unique(x['objects']) for x in [before,after]];cuts=set(old)-set(new);adds=set(new)-set(old)
 c.require(cuts==set(delta['remove_native4_records']) and adds=={r['uuid'] for r in delta['add_tracks']+delta['add_vias']},'Actual native4 transaction scope differs')
 for uid in cuts:c.require(before['_object_hashes'][uid]['native']==delta['remove_native4_records'][uid]['native_record_sha256'],'Raw native4 cut record changed')
 for uid in set(old)&set(new):c.require(before['_object_hashes'][uid]['native']==after['_object_hashes'][uid]['native'],'Retained complete native4 record changed: '+uid)
 c.require(len(set(old)&set(new))==2450,'All2450 retained records required')
 for row in delta['add_tracks']+delta['add_vias']:c.verify_added(row,new[row['uuid']],poly)
 for key in ['schema','native_version','units','copper_error_location','pad_cut_error_location','source_unchanged','footprints','copper_layers','copper_layer_ids','edge_cuts','outline_with_npth','board_thickness_mm','maximum_polygon_error_mm','native_build']:c.require(before[key]==after[key],'Native4 board/footprint structure changed: '+key)
 oldz,newz=[c.unique(x['zones']) for x in [before,after]];c.require(set(oldz)==set(newz),'Zone inventory changed')
 for uid,z in oldz.items():c.require(z==dict(newz[uid],net_code=z['net_code']),'Zone rule/layer/outline changed')
 c.require(len([r for r in new.values() if r['kind']=='pad'])==558,'558 physical pads required')
 return {'removed':sorted(cuts),'added':sorted(adds),'moved':[],'all_2450_retained_records_exact':True,'all_558_pad_identities_nets_contours_exact':True,'all_footprints_board_and_zone_settings_exact':True}

def intersects(a,b):return a is not None and not (a[2]<b[0] or a[0]>b[2] or a[3]<b[1] or a[1]>b[3])
def unchanged_contact_windows(before,after,delta,obligations,local,disposition):
 windows=obligations['old_native4_source_contact_windows'];layers={'VX_PROTECTED':'In2.Cu','LED_RED_K':'B.Cu','+3V3_CORE':'In3.Cu'}
 prior=c.read(c.ANCHORS['source_audit']['path']);prior_window=prior['preserved_source_contact_windows']
 c.require(local['candidate_native_sha256']==disposition['candidate_native_sha256']==prior_window['source_native4_sha256'] and prior['candidate_sha256']==delta['source_native_sha256'] and prior_window['passed'] is True,'Prior contact evidence chain not bound to exact source')
 c.require(disposition['all_exact_contact_scope_checks_satisfied'] is True and disposition['raw_kernel_or_report_changed'] is False,'Prior exact disposition required')
 ids=set(local['local_native_UUID_inventory']['candidate']);new_ids={r['uuid'] for r in after['objects']}
 c.require(ids<=new_ids and all(before['_object_hashes'][u]['comparison']==after['_object_hashes'][u]['comparison'] for u in ids),'A reviewed contact object changed')
 changed=[]
 for data,uids in [(before,delta['remove_native4_records']),(after,[r['uuid'] for r in delta['add_tracks']+delta['add_vias']])]:
  for uid in uids:
   for net,window in windows.items():
    region=data['_copper_bounds'][uid].get(layers[net]);drill=data['_drill_bounds'].get(uid)
    c.require(not intersects(region,window) and not intersects(drill,window),'Changed native copper/drill touches prior contact window')
   changed.append({'uuid':uid,'native_copper_bounds_mm':data['_copper_bounds'][uid],'drill_bounds_mm':data['_drill_bounds'].get(uid)})
 for data in [before,after]:
  c.require(all(layer not in set(layers.values()) for z in data['zones'] for layer,ps in z['filled'].items()),'A saved zone participates in a prior contact window layer')
 return {'passed':True,'source_native4_sha256':delta['source_native_sha256'],'exact_retained_local_object_UUIDs':sorted(ids),'contact_windows_mm':windows,'contact_layers':layers,'all_changed_copper_and_drills_disjoint_from_reviewed_windows':changed,'no_zone_fill_on_reviewed_contact_layers':True,'prior_raw_contact_predicates_and_separate_disposition_retained':True,'generic_kernel_certification':False}


def unchanged_geometry_proof(before,after):
 c.require(before['_holes_ordered_sha']==after['_holes_ordered_sha'],'Actual physical hole owners changed')
 c.require(before['_full_zones_sha']==after['_full_zones_sha'],'Saved filled planes or zone definitions changed')
 c.require(before['_power_networks']==after['_power_networks'],'Power-domain geometry changed')
 old=before['_per_net_full_records'];new=after['_per_net_full_records'];c.require(set(old)==set(new),'Net geometry inventory changed')
 held={n:h for n,h in old.items() if n!='FLASH_SCK'};c.require(all(new[n]==h for n,h in held.items()),'A non-SCK net complete record changed')
 return {'all_non_SCK_complete_net_inputs_exact':True,'non_SCK_ordered_full_record_sha256':held,'all_saved_fills_and_zone_rules_exact':True,'complete_zones_sha256':before['_full_zones_sha'],'all_326_hole_owners_exact':True,'ordered_hole_owner_sha256':before['_holes_ordered_sha'],'all_15_power_networks_exact':True,'symmetric_saved_and_own_drilled_plane_delta_is_zero_by_exact_input_equality':True,'carried_topology_predicates_have_identical_geometry_inputs':True,'generic_kernel_certification':False}
