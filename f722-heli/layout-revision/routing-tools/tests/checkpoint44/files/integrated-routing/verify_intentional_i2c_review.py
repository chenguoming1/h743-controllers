"""Bind a narrowly scoped I2C geometric-WIP review without electrical promotion."""
import hashlib,json,sys
from pathlib import Path
if sys.flags.optimize:raise RuntimeError('Validation requires assertions enabled')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def verify(path,before,after,comparison,root):
 path,comparison,root=map(Path,(path,comparison,root));r=read(path);q=read(comparison)
 assert r['schema']=='f722-intentional-I2C-geometric-WIP-acceptance/v1'
 assert r['source41_board_sha256']==before and r['board_sha256']==after
 assert r['eligible_for_geometric_WIP_adoption'] is True and r['electrical_qualified'] is False
 assert r['fresh_power_VCAP_numerical_revalidation_required'] is True
 required={'41_to43_only_exact_declared_object_and_footprint_delta','current_source_bound_entry_support_audit_passed','source_bindings_current','all_16_existing_critical_native_objects_identical','all_16_existing_critical_projected_reference_deficits_identical','both_native_complete_three_terminal_nets','both_pass_unchanged_strict_clean_tree_extractor','both_reference_planes_one_component_all118_ties_contact','42_to43_only_exact_declared_five_SDA_tracks_replaced','42_to43_saved_zone_records_and_all_retained_native_objects_identical'}
 assert set(r['guards'])==required and all(v is True for v in r['guards'].values())
 assert q['before_board_sha256']==before and q['after_board_sha256']==after
 expected={'BARO_SCL','BARO_SDA'}
 assert expected<=set(q['net_numeric_deltas_after_minus_before'])
 for net,metrics in q['net_numeric_deltas_after_minus_before'].items():
  if net not in expected:assert all(v==0 for v in metrics.values()),('undeclared reference change',net)
 assert all(v['lost_GND_overlap_with_trace_width_mm2']==0 for layer in q['ground_fill_changes'].values() for v in layer['critical_trace_proximity'].values())
 sources=r['sources'];assert sources
 for name,digest in sources.items():
  p=(root/name).resolve();assert p.is_relative_to(root.resolve()) and sha(p)==digest,('stale review source',name)
 native=[]
 for stage in ['candidate41','candidate43']:
  matches=[root/name for name in sources if name.endswith('/'+stage+'/reference-snapshot/native-geometry.json')];assert len(matches)==1
  native.append({o['uuid']:o for o in read(matches[0])['objects']})
 old_objects,new_objects=native
 assert q['critical_object_differences']
 for uid in q['critical_object_differences']:
  rows=[x[uid] for x in native if uid in x]
  assert rows and all(o['net'] in expected for o in rows),('non-I2C object difference',uid)
 tracked=set(q['net_numeric_deltas_after_minus_before'])-expected
 assert {k:v for k,v in old_objects.items() if v['net'] in tracked}=={k:v for k,v in new_objects.items() if v['net'] in tracked},'Existing critical native geometry changed'
 comparisons=[root/name for name in sources if name.endswith('/reference-comparison-41-to43.json')];assert len(comparisons)==1
 reviewed=read(comparisons[0])
 for key in ['before_board_sha256','after_board_sha256','critical_object_geometry_identical','critical_object_differences','net_numeric_deltas_after_minus_before','ground_fill_changes']:
  assert q[key]==reviewed[key],('independent comparison differs',key)
 assert set(r['I2C_reference_totals'])==expected
 for net,row in r['I2C_reference_totals'].items():
  assert row['native_complete'] is True and row['all_terminals_connected'] is True
  assert row['physical_missing_centerline_mm_by_class']['drill_void_outside_own_window']==0
  assert row['physical_missing_centerline_mm_by_class']['saved_void_or_edge_outside_own_window']==0
 return {'schema':r['schema'],'receipt_sha256':sha(path),'source_board_sha256':before,'board_sha256':after,'comparison_sha256':sha(comparison),'verified_source_files':len(sources),'intentional_changed_nets':sorted(expected),'geometric_WIP_only':True,'electrical_qualified':False,'numerical_power_VCAP_pending':True,'scope':r['scope'],'I2C_reference_totals':r['I2C_reference_totals'],'explicit_nonzero_outside_own_window_width_components':r['explicit_nonzero_outside_own_window_width_components']}
