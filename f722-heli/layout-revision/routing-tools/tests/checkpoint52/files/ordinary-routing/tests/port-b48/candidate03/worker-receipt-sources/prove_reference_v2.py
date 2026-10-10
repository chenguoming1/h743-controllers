"""Create a strict v2 runtime-index receipt and execute ten rebound tamper controls."""
from pathlib import Path
import argparse,ast,copy,hashlib,json,sys,tempfile,shutil
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'integrated-routing'))
from verify_reference_runtime_indices import verify
ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path,required=True);ap.add_argument('--after',type=Path,required=True);ap.add_argument('--comparison',type=Path,required=True);ap.add_argument('--out',type=Path);args=ap.parse_args();S=args.before.resolve();D=args.after.resolve();C=args.comparison.resolve();OUT=(args.out or D/'reference-runtime-index-proof-v2.json').resolve()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());write=lambda p,x:Path(p).write_text(json.dumps(x,separators=(',',':'))+'\n')
BG=S/'reference-snapshot';AG=D/'reference-snapshot';bg,bm,br=[read(BG/n)for n in ['native-geometry.json','native-signals.json','critical-reference.json']];ag,am,ar=[read(AG/n)for n in ['native-geometry.json','native-signals.json','critical-reference.json']];raw=read(C)
constants={}
for node in ast.parse((ROOT/'repo/f722-heli/layout-revision/signal-review/native/check_signal_geometry.py').read_text()).body:
 if isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)and node.targets[0].id in {'CRITICAL','I2C'}:constants[node.targets[0].id]=ast.literal_eval(node.value)
wanted=set(constants['CRITICAL'])|set(constants['I2C']);old={o['uuid']:o for o in bg['objects']if o['net']in wanted};new={o['uuid']:o for o in ag['objects']if o['net']in wanted};assert old.keys()==new.keys()
diff=[]
for uid in old:
 fields=sorted(k for k in old[uid].keys()|new[uid].keys()if old[uid].get(k)!=new[uid].get(k));assert set(fields)<={'net_code'}
 if fields:diff.append(dict(uuid=uid,net=new[uid]['net'],kind=new[uid]['kind'],changed_fields=fields,before_net_code=old[uid]['net_code'],after_net_code=new[uid]['net_code']))
assert diff and sorted(x['uuid']for x in diff)==raw['critical_object_differences'];assert br['nets']==ar['nets']
names=['reject_net_change','reject_width_change','reject_uuid_change','reject_start_change','reject_copper_polygon_change','reject_omitted_UUID','reject_reference_report_change','reject_nonzero_numeric_delta','reject_lost_critical_width','reject_altered_ground_change_receipt']
r=dict(schema='f722-critical-reference-runtime-net-index-proof/v2',passed=True,scope_kind='critical_records_and_reference_only_with_changed_ground',before_board_sha256=sha(S/'f722-heli.kicad_pcb'),board_sha256=sha(D/'f722-heli.kicad_pcb'),raw_comparison_sha256=sha(C),before_native_sha256=sha(BG/'native-geometry.json'),after_native_sha256=sha(AG/'native-geometry.json'),before_report_sha256=sha(BG/'critical-reference.json'),after_report_sha256=sha(AG/'critical-reference.json'),script_sha256=sha(__file__),verifier_sha256=sha(ROOT/'integrated-routing/verify_reference_runtime_indices.py'),raw_critical_object_geometry_identical=False,critical_physical_records_exact_except_runtime_net_code=True,critical_record_count=len(old),raw_difference_count=len(diff),runtime_net_mapping_bijections_verified=True,each_raw_difference_is_only_net_code=True,raw_runtime_net_index_differences=diff,all_saved_zone_records_exact=bg['zones']==ag['zones'],all_critical_reference_net_reports_exact=True,all_numeric_projection_deltas_exactly_zero=True,ground_fill_changes=raw['ground_fill_changes'],negative_controls=[dict(name=n,rejected=True,temporary_fixture_expectation=True)for n in names],scope='Exact unchanged critical UUIDs, names and all physical fields/contours; only verified runtime net_code remapping differs. Exact critical reference report records and zero numeric/critical-width loss are required. Real saved-ground changes remain reported and require fresh power/return review. No native data normalization or electrical qualification.')
sample=next(o for o in ag['objects']if o['kind']=='track'and o['net']in wanted);controls=[]
with tempfile.TemporaryDirectory(prefix='f722-reference-v2-controls-')as td:
 T=Path(td);TP=T/'receipt.json';CP=T/'comparison.json';A=T/'after';A.mkdir();write(TP,r);shutil.copy2(C,CP)
 for n in ['native-geometry.json','native-signals.json','critical-reference.json']:shutil.copy2(AG/n,A/n)
 baseline=verify(TP,S/'f722-heli.kicad_pcb',D/'f722-heli.kicad_pcb',CP,BG,A);assert baseline['passed']
 for name in names:
  gg=copy.deepcopy(ag);mm=copy.deepcopy(am);rr=copy.deepcopy(ar);qq=copy.deepcopy(raw);proof=copy.deepcopy(r);target=next(o for o in gg['objects']if o['uuid']==sample['uuid']);description=name
  if name=='reject_net_change':target['net']='NRST';target['net_code']=next(o['net_code']for o in gg['objects']if o['net']=='NRST')
  elif name=='reject_width_change':target['width']+=.001
  elif name=='reject_uuid_change':target['uuid']='00000000-0000-4000-8000-000000000001'
  elif name=='reject_start_change':target['start'][0]+=.001
  elif name=='reject_copper_polygon_change':target['copper'][next(iter(target['copper']))][0]['outer'][0][0]+=.001
  elif name=='reject_omitted_UUID':gg['objects']=[o for o in gg['objects']if o['uuid']!=sample['uuid']]
  elif name=='reject_reference_report_change':rr['nets'][next(iter(rr['nets']))]['tampered_control_marker']=True
  elif name=='reject_nonzero_numeric_delta':qq['net_numeric_deltas_after_minus_before'][next(iter(qq['net_numeric_deltas_after_minus_before']))]['native_planar_length_mm']=.001
  elif name=='reject_lost_critical_width':
   plane=qq['ground_fill_changes']['In1.Cu'];plane['critical_trace_proximity'][next(iter(plane['critical_trace_proximity']))]['lost_GND_overlap_with_trace_width_mm2']=.001;proof['ground_fill_changes']=copy.deepcopy(qq['ground_fill_changes'])
  elif name=='reject_altered_ground_change_receipt':proof['ground_fill_changes']['In1.Cu']['physical_GND_lost_mm2']+=.001
  write(A/'native-geometry.json',gg);mm['geometry_sha256']=sha(A/'native-geometry.json');write(A/'native-signals.json',mm);rr['sources']['native-geometry.json']=sha(A/'native-geometry.json');rr['sources']['native-signals.json']=sha(A/'native-signals.json');write(A/'critical-reference.json',rr);write(CP,qq);proof['after_native_sha256']=sha(A/'native-geometry.json');proof['after_report_sha256']=sha(A/'critical-reference.json');proof['raw_comparison_sha256']=sha(CP);write(TP,proof)
  rejected=False;reason=''
  try:verify(TP,S/'f722-heli.kicad_pcb',D/'f722-heli.kicad_pcb',CP,BG,A)
  except(AssertionError,KeyError,ValueError)as exc:rejected=True;reason=type(exc).__name__+': '+str(exc)
  assert rejected,name;controls.append(dict(name=name,rejected=True,verifier_invoked=True,metadata_hashes_rebound_after_mutation=True,mutated_geometry_sha256=sha(A/'native-geometry.json'),mutated_comparison_sha256=sha(CP),rejection=reason));print(name,'rejected',flush=True)
r['negative_controls']=controls;write(OUT,r);result=verify(OUT,S/'f722-heli.kicad_pcb',D/'f722-heli.kicad_pcb',C,BG,AG);write(OUT.with_name(OUT.stem+'-verification.json'),result);print(json.dumps({'passed':result['passed'],'proof':str(OUT),'controls':len(controls),'differences':len(diff)}))
