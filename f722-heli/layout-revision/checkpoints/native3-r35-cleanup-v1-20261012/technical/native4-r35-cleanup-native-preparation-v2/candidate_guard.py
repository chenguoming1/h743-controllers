"""Non-executing source excerpts. See SOURCE-PROVENANCE.json for original identity.
Dependencies belong to the original implementation; use reproduction/replay_native.py
for the standalone verifier and exact sealed-recipe replay.
"""

def check_sources():
 require(sha(PLAN)==PLAN_SHA,'Exact adopted native4 source plan changed');p=read(PLAN)
 for rel,h in p['bindings'].items():require(sha(ROOT/rel)==h,'Frozen source/helper changed: '+rel)
 return p

def source_binding(kind):
 p=check_sources();m=p['source_manifest'][kind]
 return {'path':p['paths']['source_'+kind],'sha256':m['uncompressed']['sha256'],'compressed_sha256':m['compressed']['sha256']}

def read_source(kind):
 p=check_sources();return compact_json.read(p['paths']['source_'+kind],p['source_manifest'][kind])

def normalize_cuts(delta):
 rows=delta['remove_records'];require(isinstance(rows,list) and len({r['record']['uuid'] for r in rows})==len(rows),'Duplicate or invalid candidate cuts')
 return {r['record']['uuid']:{'native_record_sha256':r['source_record_sha256'],'declared_record':r['record']} for r in rows}

def validate_delta(delta,profile,index):
 require(delta['complete'] is True and delta['source_native_sha256']==index['native_logical_sha256'],'Complete exact-source candidate required')
 require(delta['source_native_file_sha256']==read(PLAN)['source_manifest']['native']['compressed']['sha256'],'Compressed source differs')
 cuts=normalize_cuts(delta);require(set(cuts)==set(profile['cuts']),'Candidate cuts differ from exact selected scope')
 for u,row in cuts.items():
  source=index['objects'][u];require(row['native_record_sha256']==source['sha256']==profile['cuts'][u],'Exact full native cut record differs: '+u)
  expected_kind=profile.get('cut_kinds_by_uuid',{}).get(u,'track');require(source['identity']['kind']==expected_kind and expected_kind in ['track','via'],'Cut kind differs from exact profile')
  if expected_kind=='via':require(u in profile.get('allowed_removed_drill_UUIDs',[]),'Undeclared physical hole removal')
  for k,v in row['declared_record'].items():
   if k in source['identity']:require(v==source['identity'][k],'Declared cut identity changed')
   if k in source['primitive']:require(v==source['primitive'][k],'Declared cut primitive changed')
 adds=delta['add_tracks']+delta['add_vias'];uids={r['uuid'] for r in adds}
 require(adds and len(uids)==len(adds) and not uids&set(index['objects']),'Duplicate or reused addition UUID')
 require(len(adds)<=512,'Bounded candidate record limit exceeded')
 if 'expected_added_geometry_sha256' in profile:require(digest({'tracks':delta['add_tracks'],'vias':delta['add_vias']})==profile['expected_added_geometry_sha256'],'Cleanup changed any planned addition geometry')
 for r in adds:require(str(uuid.UUID(r['uuid']))==r['uuid'],'Canonical UUID required')
 allowed=set(profile['required_complete_nets']);require(all(r['net'] in allowed for r in adds),'New net outside selected complete obligations')
 require({r['net'] for r in adds}==set(profile['new_route_nets']),'Every route obligation must have physical additions')
 for r in delta['add_tracks']:
  require(set(r)=={'uuid','kind','net','layer','width','start','end'} and r['kind']=='track','Exact explicit track geometry required')
  require(r['layer'] in profile['layers_by_net'][r['net']] and r['width']==profile['width_by_net'][r['net']],'Track layer/width outside selected scope')
  require(len(r['start'])==len(r['end'])==2 and r['start']!=r['end'],'Degenerate track')
  for q in r['start']+r['end']:nm(q)
 for r in delta['add_vias']:
  require(set(r)=={'uuid','kind','net','xy','diameter','drill','layers','type','tented'} and r['kind']=='via','Exact explicit via geometry required')
  require(r['diameter']==.45 and r['drill']==.2 and r['type']=='through' and r['layers']==index['copper_layers'] and r['tented']=={'F.Mask':True,'B.Mask':True},'Via geometry/process changed')
  require(len(r['xy'])==2,'Via needs two coordinates')
  for q in r['xy']:nm(q)
 import r35_pose
 poses=r35_pose.pose_map(profile,delta)
 if not poses:require(delta['poses_and_nets_unchanged'] is True and not delta.get('pose_changes'),'No pose or net edit allowed')
 return cuts

def verify_delta(before,after,delta,profile=None):
 import r35_pose
 profile=profile or {};poses=r35_pose.pose_map(profile,delta);moved={r['uuid'] for r in before['objects'] if r.get('ref') in poses}
 old={o['uuid']:o for o in before['objects']};new={o['uuid']:o for o in after['objects']};cuts=normalize_cuts(delta);adds={r['uuid']:r for r in delta['add_tracks']+delta['add_vias']}
 require(len(old)==len(before['objects']) and len(new)==len(after['objects']),'Duplicate native UUID')
 require(set(old)-set(new)==set(cuts) and set(new)-set(old)==set(adds),'Native exact cut/add inventory changed')
 for u,row in cuts.items():
  require(digest(old[u])==row['native_record_sha256'],'Source full record hash differs: '+u)
  require(all(old[u][k]==v for k,v in row['declared_record'].items()),'Declared source cut record differs: '+u)
 for u,row in old.items():
  if u not in cuts and u not in moved:require(row==new[u],'Retained native record changed: '+u)
 for u,row in adds.items():common.verify_added(row,new[u])
 require(len(before['footprints'])==len(after['footprints']) and {f['ref'] for f in before['footprints']}=={f['ref'] for f in after['footprints']},'Footprint inventory differs')
 pose_ledger=r35_pose.verify(before,after,profile) if poses else None
 for ref,fp in {x['ref']:x for x in before['footprints']}.items():
  if ref not in poses:require(fp==next(x for x in after['footprints'] if x['ref']==ref),'Undeclared footprint change: '+ref)
 for key in ['schema','native_build','native_version','units','copper_error_location','pad_cut_error_location','maximum_polygon_error_mm','single_copper_polygon_export','source_unchanged','edge_cuts','outline_with_npth','copper_layers','copper_layer_ids','board_thickness_mm']:require(before[key]==after[key],'Native source schema/pose/settings differs: '+key)
 a={z['uuid']:z for z in before['zones']};b={z['uuid']:z for z in after['zones']};require(set(a)==set(b),'Zone inventory differs');fills=[]
 for u,z in a.items():
  require({k:v for k,v in z.items() if k not in ['filled','fill_representation']}=={k:v for k,v in b[u].items() if k not in ['filled','fill_representation']},'Zone definition differs: '+u)
  require(set(z['filled'])==set(b[u]['filled']),'Zone fill layers differ')
  for layer,parts in z['filled'].items():fills.append({'zone_uuid':u,'layer':layer,'source_fill_sha256':digest(parts),'candidate_fill_sha256':digest(b[u]['filled'][layer]),'source_components':len(parts),'candidate_components':len(b[u]['filled'][layer])})
 padproof=common.paired.verify_pad_nets(before,after)
 return {'all_unmoved_retained_objects_exact':True,'retained_object_count':len(old)-len(cuts),'all_retained_objects_exact':not bool(poses),'all_declared_pad_and_footprint_transforms_exact':True,'exact_pose_ledger':pose_ledger,'moved_pad_UUIDs':sorted(moved),'all_pad_net_identities_and_polygon_exact':True,'exact_removed_UUIDs':sorted(cuts),'exact_added_UUIDs':sorted(adds),'added_records':{u:new[u] for u in sorted(adds)},'zone_fill_ledger':fills,'all_saved_plane_fills_exact':before['zones']==after['zones'],**padproof}

def raw_delta(source,candidate,delta,profile=None):
 import r35_pose
 poses=r35_pose.pose_map(profile or {},delta)
 result=raw.verify_raw_board(source,candidate,poses,normalize_cuts(delta),delta['add_tracks']+delta['add_vias'])
 common.island_guard.verify_saved_policy(candidate);common.transaction_guard.verify_raw_polygon(candidate);return result

def all_native_pad_partitions(board):
 graph=board.GetConnectivity();nets={}
 for f in board.GetFootprints():
  for pad in f.Pads():nets.setdefault(pad.GetNetname(),{})[pad.m_Uuid.AsString()]=pad
 out={}
 for net,pads in sorted(nets.items()):
  remaining=set(pads);groups=[]
  while remaining:
   queue=[pads[min(remaining)]];seen=set()
   while queue:
    item=queue.pop();u=item.m_Uuid.AsString()
    if u in seen:continue
    require(item.GetNetname()==net,'Foreign net in native component');seen.add(u)
    queue.extend(x for x in graph.GetConnectedItems(item) if x.m_Uuid.AsString() not in seen)
   terminals=remaining&seen;require(terminals,'Empty native pad group');remaining-=terminals;groups.append(sorted(terminals))
  out[net]=sorted(groups)
 return out

def pair_set(groups):return {(a,b) for g in groups for i,a in enumerate(sorted(g)) for b in sorted(g)[i+1:]}

def verify_native_connections(board,source_partitions,profile):
 p=all_native_pad_partitions(board);require(set(p)==set(source_partitions),'Native net partition inventory differs')
 losses={n:sorted(pair_set(source_partitions[n])-pair_set(g)) for n,g in p.items()};require(not any(losses.values()),'Native baseline pad-pair loss')
 for n,count in profile['required_complete_nets'].items():require(len(p[n])==1 and len(p[n][0])==count,'Native whole-net obligation incomplete: '+n)
 return {'source_pad_partitions':source_partitions,'candidate_pad_partitions':p,'baseline_lost_pad_pairs':losses,'required_complete_nets':profile['required_complete_nets'],'all_required_native_nets_complete':True,'physical_full_width_contact_and_power_review_still_required':True}

def critical_ledger(before,after,profile):
 nets=list(read(read(PLAN)['paths']['power_scope'])['pad_inventory']);rows={};allowed=set(profile['allowed_power_object_changes'])
 for net in nets:
  a=[o for o in before['objects'] if o.get('net')==net];b=[o for o in after['objects'] if o.get('net')==net]
  if net not in allowed:require(a==b,'Undeclared power copper change: '+net)
  rows[net]={'source_objects_sha256':digest(a),'candidate_objects_sha256':digest(b),'primitive_records_exact':a==b,'permitted_object_change':net in allowed}
 old={o['uuid']:o for o in before['objects'] if o.get('drill')};new={o['uuid']:o for o in after['objects'] if o.get('drill')}
 permitted=set(profile.get('allowed_removed_drill_UUIDs',[]));require(set(old)-set(new)==permitted and all(old[u]==new[u] for u in set(old)&set(new)),'Existing physical hole owner changed outside exact removed CORE barrel')
 return {'profile':profile['name'],'power_object_changes_allowed_only_on':sorted(allowed),'all_15_power_networks':rows,'all_retained_drill_owner_records_exact':True,'exact_removed_drill_owner_UUIDs':sorted(set(old)-set(new)),'added_drill_owner_UUIDs':sorted(set(new)-set(old)),'all_holes_exact':old==new,'all_saved_fills_exact':before['zones']==after['zones'],'source_DC_or_reference_qualification_transferred':False,'fresh_DC_required':bool(allowed),'fresh_power_model_rebind_or_rerun_required':bool(allowed or old!=new or before['zones']!=after['zones']),'source_DC_provenance':read(PLAN)['paths']['source_power_handoff']}
