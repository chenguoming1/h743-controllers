#!/usr/bin/env python3
"""Read-only exact-source I2C43 reference review. No refills, tolerances or numerical zeroing."""
import collections, hashlib, json, math, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'critical-reference-review/native'))
from check_signal_geometry import poly,centerline,copper_entries,sha,pieces,topology,validate_bindings
from check_critical_reference import REFERENCE,PLANES,ground_geometry,local_masks,partition_missing
from compare_reference_geometry import load,compare
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union,nearest_points
OUT=Path(__file__).resolve().parent
B=ROOT/'ordinary-routing/candidate41';A=ROOT/'ordinary-routing/candidate43';P=ROOT/'ordinary-routing/candidate42'
expected={B:'539d9547eb8c4d5984481293ae10cee34355ee838dff11ab43b00cca270ceae2',A:'1ee7174a578dffe4d5ef3ae8b39d8dc88f28b80395539263a65f23be234c21e6',P:'eac130eb32389c82b2bae274e2c50b73675c79d442cfc8441956369b4cdf3304'}
for p,h in expected.items():assert sha(p/'f722-heli.kicad_pcb')==h
before=load(B/'reference-snapshot',B/'f722-heli.kicad_pcb');after=load(A/'reference-snapshot',A/'f722-heli.kicad_pcb')
bg,bm,br=before;ag,am,ar=after
bs={o['uuid']:o for o in bg['objects']};ass={o['uuid']:o for o in ag['objects']}
comp=compare(before,after)
read=lambda p:json.loads(p.read_text())
gi=read(A/'i2c-geometry-review.json');critical=read(A/'owner-critical.json')
assert gi['board_sha256']==critical['board_sha256']==expected[A]
assert gi['sources']['native-geometry.json']==sha(A/'reference-snapshot/native-geometry.json')
assert gi['sources']['native-signals.json']==sha(A/'reference-snapshot/native-signals.json')
assert gi['sources']['check_signal_geometry.py']==sha(ROOT/'critical-reference-review/native/check_signal_geometry.py')
assert ar['sources']['check_critical_reference.py']==sha(ROOT/'critical-reference-review/native/check_critical_reference.py')
_,bz,bp,bcuts=ground_geometry(bg,copper_entries(bg));_,az,ap,acuts=ground_geometry(ag,copper_entries(ag))
masks,facts,holes=local_masks(ag,am,az)
critical_nets=[r['net'] for r in critical['fullnet_connectivity']]
existing={}
for n in critical_nets:
 bo={u:o for u,o in bs.items() if o['net']==n};ao={u:o for u,o in ass.items() if o['net']==n}
 r={'native_objects_identical':bo==ao,'changed_object_ids':[u for u in bo.keys()|ao.keys() if bo.get(u)!=ao.get(u)],'reference_projection':[]}
 for l in sorted({next(iter(o['copper'])) for o in ao.values() if o['kind'] in ['track','arc']}):
  ref=REFERENCE.get(l)
  if ref is None:r['reference_projection'].append({'signal_layer':l,'status':'no_designated_reference_mapping'});continue
  cu=unary_union([poly(o['copper'][l]) for o in ao.values() if o['kind']in['track','arc']and l in o['copper']])
  line=unary_union([centerline(o) for o in ao.values() if o['kind']in['track','arc']and l in o['copper']])
  lost=bp[ref].difference(ap[ref]);gained=ap[ref].difference(bp[ref])
  r['reference_projection'].append({'signal_layer':l,'reference_layer':ref,'before_missing_centerline_mm':line.difference(bp[ref]).length,'after_missing_centerline_mm':line.difference(ap[ref]).length,'before_missing_width_mm2':cu.difference(bp[ref]).area,'after_missing_width_mm2':cu.difference(ap[ref]).area,'lost_projection_area_mm2':cu.intersection(lost).area,'gained_projection_area_mm2':cu.intersection(gained).area,'distance_to_lost_GND_mm':cu.distance(lost)})
 existing[n]=r
planes={}
for l in PLANES:
 old=list(pieces(bp[l],'Polygon'));new=list(pieces(ap[l],'Polygon'));main=max(new,key=lambda p:p.area)
 planes[l]={'before_physical_component_count':len(old),'after_physical_component_count':len(new),'before_component_areas_mm2':sorted([p.area for p in old],reverse=True),'after_component_areas_mm2':sorted([p.area for p in new],reverse=True),'accepted_ties_with_positive_main_component_contact':sum(poly(ass[t['uuid']]['copper'][l]).difference(acuts[l]).intersection(main).area>0 for t in ar['GND_ties']['accepted']), 'total_accepted_ties':len(ar['GND_ties']['accepted'])}
# Preserve every width component including arbitrarily small nonzero fragments.
gaps=[]
for t in ar['tracks']:
 if t['net'] not in ['BARO_SCL','BARO_SDA']:continue
 o=ass[t['track_uuid']];line=centerline(o);cu=poly(o['copper'][t['signal_layer']]);ref=t['reference_layer']
 own=[v for (u,l),v in masks.items() if l==ref and ass[u]['net']==t['net']]
 part=partition_missing(cu.difference(ap[ref]),own,acuts[ref])
 delta=(o['end'][0]-o['start'][0],o['end'][1]-o['start'][1]);length=math.hypot(*delta);unit=(delta[0]/length,delta[1]/length);normal=(-unit[1],unit[0])
 for cls,shape in part.items():
  for p in pieces(shape,'Polygon'):
   coords=list(p.exterior.coords);along=[(x-o['start'][0])*unit[0]+(y-o['start'][1])*unit[1] for x,y in coords];perp=[(x-o['start'][0])*normal[0]+(y-o['start'][1])*normal[1] for x,y in coords]
   hs=[i for i,h in enumerate(holes[ref]) if p.intersection(h).area>0]
   gaps.append({'net':t['net'],'track_uuid':t['track_uuid'],'signal_layer':t['signal_layer'],'reference_layer':ref,'classification':cls,'area_mm2':p.area,'bounds_mm':list(p.bounds),'projected_along_trace_extent_mm':max(along)-min(along),'projected_across_trace_extent_mm':max(perp)-min(perp),'signed_across_trace_range_mm':[min(perp),max(perp)],'minimum_centerline_distance_mm':p.distance(line),'maximum_trace_halfwidth_mm':o['width']/2,'saved_holes':[ar['saved_holes'][ref][i] for i in hs], 'outer_mm':[list(x) for x in coords]})
trans=[r for r in ar['transitions'] if r['net'] in ['BARO_SCL','BARO_SDA']]
# Recompute the unchanged strict topology function; do not inherit fast-check metadata.
strict={n:topology([o for o in ag['objects'] if o['net']==n],am['nets'][n]) for n in ['BARO_SCL','BARO_SDA']}
for n in strict:assert strict[n]==gi['nets'][n]['topology'] and strict[n]['clean_complete_tree']
pg,pm,pr=load(P/'reference-snapshot',P/'f722-heli.kicad_pcb');ps={o['uuid']:o for o in pg['objects']}
stage=read(A/'construction-provenance.json');cleanup=stage['topology_cleanup']
removed=sorted(ps.keys()-ass.keys());added=sorted(ass.keys()-ps.keys());retained_changes=sorted(u for u in ps.keys()&ass.keys() if ps[u]!=ass[u])
assert len(removed)==len(added)==5 and not retained_changes
assert {o['uuid']:o for o in cleanup['removed_stage_records']}=={u:ps[u] for u in removed}
assert {o['uuid']:o for o in cleanup['added_stage_records']}=={u:ass[u] for u in added}
assert all(o['net']=='BARO_SDA' and o['kind']=='track' and o['width']==.127 for o in cleanup['removed_stage_records']+cleanup['added_stage_records'])
assert pg['zones']==ag['zones'] and all(pg[k]==ag[k] for k in ['footprints','edge_cuts','outline_with_npth','copper_layers'])
assert stage['constructor_sha256']==sha(A/'construct_i2c_topology43.py')
assert stage['source42_construction_receipt_sha256']==sha(P/'construction-provenance.json')
assert cleanup['before_topology_refusal_sha256']==sha(P/'i2c-geometry-review.json')
# Also close the accepted41→43 declared object/footprint delta; no unrelated ordinary-net exception.
base_removed={u:bs[u] for u in bs.keys()-ass.keys()};base_added={u:ass[u] for u in ass.keys()-bs.keys()}
assert base_removed=={o['uuid']:o for o in stage['removed_source_records']}
assert base_added=={o['uuid']:o for o in stage['added_candidate_records']}
base_changed={u:{'before':bs[u],'after':ass[u]} for u in bs.keys()&ass.keys() if bs[u]!=ass[u]}
assert base_changed=={o['before']['uuid']:o for o in stage['changed_pad_records']}
bf={f['ref']:f for f in bg['footprints']};af={f['ref']:f for f in ag['footprints']}
assert bf.keys()==af.keys()
assert {u:{'before':bf[u],'after':af[u]} for u in bf if bf[u]!=af[u]}=={o['before']['ref']:o for o in stage['changed_footprint_records']}
entry=read(A/'i2c-entry-support-audit.json')
assert entry['board_sha256']==expected[A] and entry['source_board_sha256']==expected[B] and entry['passed']
assert entry['construction_sha256']==sha(A/'construction-provenance.json')
assert entry['source_native_sha256']==sha(B/'f722-heli.native.json') and entry['candidate_native_sha256']==sha(A/'f722-heli.native.json')

stage_comparison=compare((pg,pm,pr),after)
# Exact source-bound geometry predicates are local to these reviewed boards. Electrical pass is never inferred.
def geometry_guard(board_hash,objects,netreports,critical_rows):
    if board_hash!=expected[A]:return False
    current={o['uuid']:o for o in objects}
    if any({u:o for u,o in bs.items() if o['net']==n}!={u:o for u,o in current.items() if o['net']==n} for n in critical_nets):return False
    if any(not all(netreports[n][k] for k in ['terminal_inventory_matches','all_native_copper_connected','all_terminals_connected']) or not netreports[n]['topology'].get('clean_complete_tree') or netreports[n]['topology'].get('cycle_rank')!=0 for n in ['BARO_SCL','BARO_SDA']):return False
    if any(v['before_missing_centerline_mm']!=v['after_missing_centerline_mm'] or v['before_missing_width_mm2']!=v['after_missing_width_mm2'] or v['lost_projection_area_mm2']!=0 for r in critical_rows.values() for v in r['reference_projection']):return False
    return True
import copy
controls={}
controls['actual43_accepted_for_geometry_only']=geometry_guard(expected[A],ag['objects'],gi['nets'],existing)
controls['wrong_board_hash_rejected']=not geometry_guard(expected[P],ag['objects'],gi['nets'],existing)
changed=copy.deepcopy(ag['objects']);victim=next(o for o in changed if o['net']=='IMU_INT' and o['kind']=='track');victim['width']+=.01
controls['unrelated_critical_object_change_rejected']=not geometry_guard(expected[A],changed,gi['nets'],existing)
wrong=copy.deepcopy(gi['nets']);wrong['BARO_SDA']['terminal_inventory_matches']=False
controls['wrong_I2C_terminal_inventory_rejected']=not geometry_guard(expected[A],ag['objects'],wrong,existing)
old_topology=topology([o for o in pg['objects'] if o['net']=='BARO_SDA'],pm['nets']['BARO_SDA'])
assert not old_topology.get('clean_complete_tree',False)
wrong=copy.deepcopy(gi['nets']);wrong['BARO_SDA']['topology']=old_topology
controls['original42_strict_topology_refusal_rejected']=not geometry_guard(expected[A],ag['objects'],wrong,existing)
wrong=copy.deepcopy(existing);next(iter(wrong.values()))['reference_projection'][0]['lost_projection_area_mm2']=.000001
controls['new_critical_reference_loss_rejected']=not geometry_guard(expected[A],ag['objects'],gi['nets'],wrong)
for label,bhash,gphash in [('wrong_board_snapshot_binding',expected[P],sha(A/'reference-snapshot/native-geometry.json')),('wrong_geometry_snapshot_binding',expected[A],sha(P/'reference-snapshot/native-geometry.json'))]:
    try:validate_bindings(ag,am,gphash,bhash)
    except ValueError:controls[label+'_rejected']=True
    else:controls[label+'_rejected']=False
assert all(controls.values()),controls
cleanup_review={'removed_records':cleanup['removed_stage_records'],'added_records':cleanup['added_stage_records'],'retained_objects_identical':not retained_changes,'saved_zone_records_identical':pg['zones']==ag['zones'],'poses_vias_power_objects_unchanged':True,'strict_topology':strict,'comparison_42_to43':stage_comparison,'controls':controls}
route={n:{k:gi['nets'][n][k] for k in ['actual_terminals','all_native_copper_connected','all_terminals_connected','whole_net_planar_length_by_layer_mm','whole_net_planar_length_mm','widths_mm','pads','vias','capacitance']} for n in ['BARO_SCL','BARO_SDA']}
calc=read(ROOT/'signal-review/stock-i2c-calculations.json');rmax=calc['pullup_cases'][-1]['r_external_max_ohm'];coeff=.8473*rmax*.001
result={'schema':'f722-i2c43-scoped-review/v1','before_board_sha256':expected[B],'board_sha256':expected[A], 'existing_16_critical_nets':existing,'planes':planes,'reference_comparison':comp,'I2C_reference_totals':{n:ar['nets'][n] for n in route},'I2C_all_nonzero_missing_width_components':gaps,'I2C_transitions':trans,'route_inventory':route,'topology_cleanup_review':cleanup_review,'RC_screen':{'external_Rmax_ohm':rmax,'rise_ns_per_pF':coeff,'provisional_total_target_pF':50,'rise_ns_at_50pF':50*coeff,'capacitance_pF_at_100ns':100/coeff,'device_pad_assembly_engineering_allocation_pF':25,'route_model_probe_budget_to_50pF_pF':25,'internal_pullup_credit':False,'status':'NO_ACTUAL_CAPACITANCE_OR_RC_ESTIMATE: material/geometric bounds, external-copper distance and probe/assembly inputs remain absent. No invented tolerance or electrical pass.'},'recommendation':'ACCEPT_EXACT43_INTENTIONAL_I2C_GEOMETRIC_WIP_ONLY. Both complete nets pass the unchanged strict clean-tree extractor. All 16 prior critical copper/projection guards pass. Explicit I2C reference deficits remain counted. No actual capacitance/RC pass, electrical qualification, production release or numerical power/VCAP carry-forward.', 'acceptance_scope':{'exact_board_sha256':expected[A],'intentional_changed_signal_nets':['BARO_SCL','BARO_SDA'],'geometric_WIP_eligible':all(controls.values()),'electrical_qualified':False,'power_VCAP_numerical_revalidation_required':True,'future_board_changes_require_new_review':True}, 'remaining_qualification_gaps':gi['remaining_qualification_gaps']}
files=[Path(__file__),B/'f722-heli.kicad_pcb',A/'f722-heli.kicad_pcb',A/'i2c-geometry-review.json',A/'owner-critical.json',A/'i2c-entry-support-audit.json',ROOT/'signal-review/final-native-i2c-requirements.json',ROOT/'signal-review/stock-i2c-calculations.json',ROOT/'signal-review/stock-i2c-review.md',ROOT/'repo/f722-heli/layout-revision/signal-review/native/model-inputs.template.json']
files += [B/'f722-heli.native.json',A/'f722-heli.native.json',A/'construction-provenance.json',A/'construct_i2c_topology43.py',P/'construction-provenance.json',P/'i2c-geometry-review.json',P/'f722-heli.kicad_pcb']
for p in[B,P,A]:files += [p/'reference-snapshot'/f for f in['native-geometry.json','native-signals.json','critical-reference.json']]
for f in['check_signal_geometry.py','check_critical_reference.py','compare_reference_geometry.py']:files.append(ROOT/'critical-reference-review/native'/f)
result['sources']={str(p.relative_to(ROOT)):sha(p) for p in files}
for p,h in expected.items():assert sha(p/'f722-heli.kicad_pcb')==h
(OUT/'reference-comparison-41-to43.json').write_text(json.dumps(comp,indent=2)+'\n')
(OUT/'reference-comparison-42-to43.json').write_text(json.dumps(stage_comparison,indent=2)+'\n')
result['sources']['ordinary-routing/i2c43-reference-review/reference-comparison-41-to43.json']=sha(OUT/'reference-comparison-41-to43.json')
result['sources']['ordinary-routing/i2c43-reference-review/reference-comparison-42-to43.json']=sha(OUT/'reference-comparison-42-to43.json')
(OUT/'scoped-review.json').write_text(json.dumps(result,indent=2)+'\n')
receipt={'schema':'f722-intentional-I2C-geometric-WIP-acceptance/v1',
  'source41_board_sha256':expected[B], 'source42_board_sha256':expected[P], 'board_sha256':expected[A],
  'scope':'Only these exact source41→43 intentional BARO_SCL/BARO_SDA routing changes and associated declared support changes; exact42→43 correction is five SDA tracks. This is not a reusable exemption for other boards/nets or an electrical pass.',
  'eligible_for_geometric_WIP_adoption':True, 'electrical_qualified':False,
  'guards':{'source_bindings_current':True,'all_16_existing_critical_native_objects_identical':all(v['native_objects_identical'] for v in existing.values()),'all_16_existing_critical_projected_reference_deficits_identical':all(v['before_missing_centerline_mm']==v['after_missing_centerline_mm'] and v['before_missing_width_mm2']==v['after_missing_width_mm2'] and v['lost_projection_area_mm2']==0 for n in existing.values() for v in n['reference_projection']),'both_native_complete_three_terminal_nets':all(gi['nets'][n]['terminal_inventory_matches'] and gi['nets'][n]['all_native_copper_connected'] and gi['nets'][n]['all_terminals_connected'] for n in strict),'both_pass_unchanged_strict_clean_tree_extractor':all(v['clean_complete_tree'] and v['cycle_rank']==0 for v in strict.values()),'both_reference_planes_one_component_all118_ties_contact':all(v['after_physical_component_count']==1 and v['accepted_ties_with_positive_main_component_contact']==v['total_accepted_ties']==118 for v in planes.values()),'41_to43_only_exact_declared_object_and_footprint_delta':True,'current_source_bound_entry_support_audit_passed':True,'42_to43_only_exact_declared_five_SDA_tracks_replaced':True,'42_to43_saved_zone_records_and_all_retained_native_objects_identical':True},
  'I2C_reference_totals':result['I2C_reference_totals'],
  'explicit_nonzero_outside_own_window_width_components':[{k:v for k,v in g.items() if k not in ['outer_mm','saved_holes']} for g in gaps if g['classification']!='local_own_via_window_in_saved_hole'],
  'I2C_lengths_mm':{n:route[n]['whole_net_planar_length_mm'] for n in strict},
  'source42_to43_numeric_delta':stage_comparison['net_numeric_deltas_after_minus_before'],
  'controls':controls, 'RC_screen':result['RC_screen'],
  'remaining_electrical_qualification_gaps':gi['remaining_qualification_gaps'],
  'capacitance_model_status':{n:gi['nets'][n]['capacitance'] for n in strict},
  'fresh_power_VCAP_numerical_revalidation_required':True,
  'interpretation':'Localized missing I2C reference remains explicitly reviewed geometry; no broad unchanged-reference, zero-area, worst-case-capacitance or full electrical claim. Apply this receipt only after independently required native/process/entry/support/parity guards also pass on the exact hash.',
  'sources':dict(result['sources'])|{'ordinary-routing/i2c43-reference-review/scoped-review.json':sha(OUT/'scoped-review.json')}}
assert all(receipt['guards'].values()) and all(receipt['controls'].values())
(OUT/'intentional-i2c-acceptance.json').write_text(json.dumps(receipt,indent=2)+'\n')

print(json.dumps({'all_16_critical_native_objects_identical':all(v['native_objects_identical'] for v in existing.values()),'critical_net_projected_GND_loss_mm2':{n:sum(v['lost_projection_area_mm2'] for v in x['reference_projection']) for n,x in existing.items()},'planes':planes,'outside_own_window_gaps':[{k:v for k,v in g.items() if k not in ['saved_holes','outer_mm']} for g in gaps if g['classification']!='local_own_via_window_in_saved_hole'],'controls':controls,'RC_screen':result['RC_screen']},indent=2))
