"""Exact cleaned-native4 return-stitch delta; no native imports at module load."""
import copy,importlib.util,json,sys,gzip
import compact_json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OLD=HERE.parent/'source7-native5-sck-red-polygon-native-preparation-v3'
sys.path.insert(0,str(OLD))
spec=importlib.util.spec_from_file_location('frozen_native4_predecessor',OLD/'native_trial.py');common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common)
spec=importlib.util.spec_from_file_location('exact_stitch_raw',HERE.parent/'source7-native5-sck-red-polygon-native-preparation-v2/structural_base.py');raw=importlib.util.module_from_spec(spec);spec.loader.exec_module(raw)
PLAN=HERE/'source-plan.json';PLAN_SHA='13b1031e1a02d9e5722afcc56a2c351a46d30447eec8b271382a24cf6f0d5d4c'
require=common.require;sha=common.sha;read=common.read;digest=common.digest

def check_sources():
 require(sha(PLAN)==PLAN_SHA,'Return-stitch source plan changed');plan=read(PLAN)
 for rel,h in {**plan['bindings'],**plan['immutable_predecessor_helpers']}.items():require(sha(ROOT/rel)==h,'Return-stitch source changed: '+rel)
 return plan

def validate_recipe(delta,recipe):
 plan=check_sources();require(delta==read(plan['delta']) and recipe==read(plan['cumulative_recipe']),'Only exact sealed return-stitch recipes permitted')
 require(delta['complete'] is True and len(delta['remove_native4_records'])==2 and len(delta['add_tracks'])==2 and delta['add_vias']==[],'Incomplete exact return-stitch transaction')
 old=read(delta['previous_cumulative_recipe_path']);projected=copy.deepcopy(recipe)
 removed=set(delta['remove_native4_records']);added={r['uuid'] for r in delta['add_tracks']+delta['add_vias']}
 for key in ['proposed_add_tracks','proposed_add_vias']:
  projected[key]=[r for r in projected[key] if r['uuid'] not in added]+[r for r in old[key] if r['uuid'] in removed]
  projected[key].sort(key=lambda r:r['uuid']);old[key].sort(key=lambda r:r['uuid'])
 for key in ['handoff_path','handoff_sha256']:projected[key]=old[key]
 require(projected==old,'Cumulative source7 recipe changed outside five additions and three replaced additions')
 require(recipe['proposed_add_copper_polygons']==old['proposed_add_copper_polygons'],'VX polygon changed')
 return delta

def binding():return {'schema':'f722-native4-two-SCK-track-trim-only/v1','source_plan_sha256':PLAN_SHA,'exact_cuts':2,'exact_added_tracks':2,'exact_added_vias':0,'fixed_objects':2450,'poses_nets_hardware_zone_rules_unchanged':True,'fresh_reference_power_acceptance_pending':True}

def verify_delta(before,after,delta):
 old={o['uuid']:o for o in before['objects']};new={o['uuid']:o for o in after['objects']};cuts=delta['remove_native4_records'];adds={r['uuid']:r for r in delta['add_tracks']+delta['add_vias']}
 for key in ['schema','native_build','native_version','units','copper_error_location','pad_cut_error_location','maximum_polygon_error_mm','single_copper_polygon_export','source_unchanged']:require(before[key]==after[key],'Native schema/version/units/export semantics changed: '+key)
 require(set(old)-set(new)==set(cuts) and set(new)-set(old)==set(adds),'Return-stitch native inventory changed')
 for uid,row in cuts.items():require(digest(old[uid])==row['native_record_sha256'],'Source cut hash differs')
 for uid,row in old.items():
  if uid not in cuts:require(row==new[uid],'Retained native4 record changed: '+uid)
 for uid,row in adds.items():common.verify_added(row,new[uid])
 for key in ['footprints','edge_cuts','outline_with_npth','copper_layers','copper_layer_ids','board_thickness_mm']:require(before[key]==after[key],'Return-stitch changed '+key)
 a={z['uuid']:z for z in before['zones']};b={z['uuid']:z for z in after['zones']};require(set(a)==set(b),'Zone inventory changed');fills=[]
 require(before['zones']==after['zones'],'Two-track trim changed saved plane fills or zone rules')
 for uid,z in a.items():
  require({k:v for k,v in z.items() if k not in ['filled','fill_representation']}=={k:v for k,v in b[uid].items() if k not in ['filled','fill_representation']},'Zone definition changed')
  for layer,parts in z['filled'].items():fills.append({'zone_uuid':uid,'layer':layer,'source_fill_sha256':digest(parts),'candidate_fill_sha256':digest(b[uid]['filled'][layer]),'source_components':len(parts),'candidate_components':len(b[uid]['filled'][layer]),'source_holes':sum(len(p['holes']) for p in parts),'candidate_holes':sum(len(p['holes']) for p in b[uid]['filled'][layer])})
 common.paired.verify_pad_nets(before,after)
 return {'binding':binding(),'all_2450_retained_objects_exact':True,'all_footprints_pads_nets_and_polygon_exact':True,'exact_removed_UUIDs':sorted(cuts),'exact_added_UUIDs':sorted(adds),'added_records':{u:new[u] for u in adds},'zone_fill_ledger':fills,'all_saved_plane_fills_exact':True,'power_domain_equivalence':power_equivalence(before,after)}

def raw_delta(source,candidate,delta):
 result=raw.verify_raw_board(source,candidate,{},delta['remove_native4_records'],delta['add_tracks']+delta['add_vias'])
 common.island_guard.verify_saved_policy(candidate);common.transaction_guard.verify_raw_polygon(candidate)
 return result

def verify_native_connections(board):
 proof=common.transaction_guard.verify_native_connections(board);proof['GND_pad_partitions']=common.island_guard.ground_partitions(board)
 require(list(map(len,proof['GND_pad_partitions']))==[133],'Native GND partition changed')
 via=next(t for t in board.GetTracks() if t.m_Uuid.AsString()=='d32c719a-f1a5-5703-9665-8a93f6486bde')
 peers={x.m_Uuid.AsString() for x in board.GetConnectivity().GetConnectedItems(via)}
 require({'c956a476-e320-4f09-9832-420df749bd95','ee652b71-6147-4d53-abc1-8530e0b19eaf'}<=peers,'New GND stitch lacks both native plane connections')
 proof['new_GND_stitch_direct_connections']=sorted(peers);return proof


def read_source(kind):
 plan=check_sources();manifest=read(plan['source_manifest']);key='native' if kind=='native' else 'auxiliary'
 return compact_json.read(plan['source_'+kind],manifest[key])

def source_binding(kind):
 plan=check_sources();manifest=read(plan['source_manifest']);key='native' if kind=='native' else 'auxiliary'
 return {'path':plan['source_'+kind],'sha256':manifest[key]['uncompressed']['sha256'],'compressed_sha256':manifest[key]['compressed']['sha256']}

def power_equivalence(before,after):
 plan=check_sources();scope=read(plan['power_scope']);nets=list(scope['pad_inventory']);require(len(nets)==15,'Exact fifteen-network scope required');rows={}
 for net in nets:
  a=[o for o in before['objects'] if o.get('net')==net];b=[o for o in after['objects'] if o.get('net')==net]
  za=[z for z in before['zones'] if not z['rule'] and z['net']==net];zb=[z for z in after['zones'] if not z['rule'] and z['net']==net]
  require(a==b and za==zb,'Power-domain primitive or fill changed: '+net);rows[net]={'objects':len(a),'ordered_objects_sha256':digest(a),'ordered_saved_zones_sha256':digest(za)}
 holes=[o for o in before['objects'] if o.get('drill')];require(holes==[o for o in after['objects'] if o.get('drill')] and len(holes)==326,'Physical hole owners changed')
 with gzip.open(plan['power_model'],'rt') as f:model=json.load(f)
 return {'all_15_power_networks_exact':True,'networks':rows,'all_326_full_hole_owner_records_exact':True,'all_ordered_physical_hole_owners_sha256':digest(holes),'scope_sha256':digest(scope),'electrical_model_sha256':digest(model),'footprint_inventory_sha256':digest(before['footprints']),'source_stackup_and_rules_exact_by_raw_AST':True,'power_solve_or_qualification_transferred':False}
