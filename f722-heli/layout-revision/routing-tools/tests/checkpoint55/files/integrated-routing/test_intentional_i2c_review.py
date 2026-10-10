"""Source identity, critical preservation and qualification refusal controls."""
from pathlib import Path
import copy,json,tempfile,hashlib
from verify_intentional_i2c_review import verify
R=Path(__file__).resolve().parents[1];P=R/'ordinary-routing/candidate43/intentional-i2c-review/intentional-i2c-acceptance.json';C=R/'ordinary-routing/i2c43-reference-review/reference-comparison-41-to43.json'
r=json.loads(P.read_text());q=json.loads(C.read_text());before=r['source41_board_sha256'];after=r['board_sha256'];verify(P,before,after,C,R)
rows=[]
for name in ['stale_board','electrical_promotion','power_promotion','missing_guard','false_guard','stale_source_hash','non_I2C_numeric_delta','critical_GND_loss','non_I2C_object_difference']:
 a,b=copy.deepcopy(r),copy.deepcopy(q)
 if name=='stale_board':a['board_sha256']='0'*64
 elif name=='electrical_promotion':a['electrical_qualified']=True
 elif name=='power_promotion':a['fresh_power_VCAP_numerical_revalidation_required']=False
 elif name=='missing_guard':del a['guards']['both_pass_unchanged_strict_clean_tree_extractor']
 elif name=='false_guard':a['guards']['both_native_complete_three_terminal_nets']=False
 elif name=='stale_source_hash':a['sources'][next(iter(a['sources']))]='0'*64
 elif name=='non_I2C_numeric_delta':b['net_numeric_deltas_after_minus_before']['USB_P']['native_planar_length_mm']=.001
 elif name=='critical_GND_loss':b['ground_fill_changes']['In1.Cu']['critical_trace_proximity']['USB_P']['lost_GND_overlap_with_trace_width_mm2']=.001
 elif name=='non_I2C_object_difference':b['critical_object_differences'].append('unknown-uuid')
 with tempfile.TemporaryDirectory(prefix='f722-i2c-review-test-') as td:
  p,c=Path(td)/'receipt.json',Path(td)/'comparison.json';p.write_text(json.dumps(a));c.write_text(json.dumps(b))
  try:verify(p,before,after,c,R)
  except AssertionError:rows.append({'name':name,'rejected':True})
  else:raise RuntimeError('Accepted invalid review: '+name)
out={'passed':True,'positive_board_sha256':after,'controls':rows,'verifier_sha256':hashlib.sha256((R/'integrated-routing/verify_intentional_i2c_review.py').read_bytes()).hexdigest(),'scope':'Independent input defects refuse without changing any native board, source evidence, or electrical/DRC rules.'};(R/'integrated-routing/intentional-i2c-controls.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
