"""Exact native4 return-stitch structural and inherited contact-window scope."""
import check_candidate as c

def bounds(polygons):
 points=[xy for p in polygons for xy in p['outer']]
 if not points:return None
 x,y=zip(*points);return [min(x),min(y),max(x),max(y)]

def structural_view(path):
 d=c.read(path);hashes={};copper_bounds={};drill_bounds={}
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
 cuts=set(delta['remove_native4_records']);c.require(len(cuts)==3,'Exactly three native4 SCK removals required')
 for name,added in [('proposed_add_tracks',delta['add_tracks']),('proposed_add_vias',delta['add_vias'])]:
  c.require(recipe[name]==[r for r in previous[name] if r['uuid'] not in cuts]+added,'Unexpected cumulative additions changed')
 c.require(len(delta['add_tracks'])==3 and len(delta['add_vias'])==2 and {r['net'] for r in delta['add_tracks']}=={'FLASH_SCK'} and sorted(r['net'] for r in delta['add_vias'])==['FLASH_SCK','GND'],'Exact return stitch additions required')
 c.require(delta['all_other_native4_objects_held']==2447 and delta['poses_pads_nets_source7cuts_rail_RED_unchanged'] is True,'Retained scope declaration missing')
 return {'removed':sorted(cuts),'added':sorted(r['uuid'] for r in delta['add_tracks']+delta['add_vias']),'moved':[]}

def compare(before,after,delta,poly):
 old,new=[c.unique(x['objects']) for x in [before,after]];cuts=set(old)-set(new);adds=set(new)-set(old)
 c.require(cuts==set(delta['remove_native4_records']) and adds=={r['uuid'] for r in delta['add_tracks']+delta['add_vias']},'Actual native4 transaction scope differs')
 for uid in cuts:c.require(before['_object_hashes'][uid]['native']==delta['remove_native4_records'][uid]['native_record_sha256'],'Raw native4 cut record changed')
 for uid in set(old)&set(new):c.require(before['_object_hashes'][uid]['comparison']==after['_object_hashes'][uid]['comparison'],'Retained complete native4 record changed: '+uid)
 c.require(len(set(old)&set(new))==2447,'All2447 retained records required')
 for row in delta['add_tracks']+delta['add_vias']:c.verify_added(row,new[row['uuid']],poly)
 for key in ['footprints','copper_layers','copper_layer_ids','edge_cuts','outline_with_npth','board_thickness_mm','maximum_polygon_error_mm','native_build']:c.require(before[key]==after[key],'Native4 board/footprint structure changed: '+key)
 oldz,newz=[c.unique(x['zones']) for x in [before,after]];c.require(set(oldz)==set(newz),'Zone inventory changed')
 for uid,z in oldz.items():c.require(z==dict(newz[uid],net_code=z['net_code']),'Zone rule/layer/outline changed')
 c.require(len([r for r in new.values() if r['kind']=='pad'])==558,'558 physical pads required')
 return {'removed':sorted(cuts),'added':sorted(adds),'moved':[],'all_2447_retained_records_exact_except_bijective_net_codes':True,'all_558_pad_identities_nets_contours_exact':True,'all_footprints_board_and_zone_settings_exact':True}

def intersects(a,b):return a is not None and not (a[2]<b[0] or a[0]>b[2] or a[3]<b[1] or a[1]>b[3])
def unchanged_contact_windows(before,after,delta,obligations,local,disposition):
 windows=obligations['old_native4_source_contact_windows'];layers={'VX_PROTECTED':'In2.Cu','LED_RED_K':'B.Cu','+3V3_CORE':'In3.Cu'}
 c.require(local['candidate_native_sha256']==disposition['candidate_native_sha256']==delta['source_native_sha256'],'Prior contact evidence not bound to adopted source')
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
