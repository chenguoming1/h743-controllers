"""Refresh owner evidence after adopt_verified; requires fresh source-bound review files."""
from pathlib import Path
import argparse,json,hashlib,shutil,re,sys
if sys.flags.optimize:raise RuntimeError('Validation requires Python assertions enabled')
R=Path(__file__).resolve().parents[1];N=R/'repo/f722-heli/layout-revision';C=N/'checks'
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('previous',type=Path);p.add_argument('review',type=Path);p.add_argument('--coordinated',action='store_true');rg=p.add_mutually_exclusive_group();rg.add_argument('--reference-review',type=Path);rg.add_argument('--reference-window-classification',type=Path);rg.add_argument('--intentional-i2c-review',type=Path);pg=p.add_mutually_exclusive_group();pg.add_argument('--footprint-translations',type=Path);pg.add_argument('--footprint-transforms',type=Path);p.add_argument('--placement-previews',type=Path);a=p.parse_args();D=a.candidate.resolve();O=a.previous.resolve();S=a.review.resolve()
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
h=sha(D/'f722-heli.kicad_pcb');old=sha(O/'f722-heli.kicad_pcb');assert sha(N/'hardware/f722-heli.kicad_pcb')==h
n=read(D/'owner-summary.json')['drc']['unconnected'];before=read(O/'owner-summary.json')['drc']['unconnected'];comp=S/f'comparison-{before}-to-{n}.json';q=read(comp)
assert q['before_board_sha256']==old and q['after_board_sha256']==h
if not a.intentional_i2c_review:assert q['critical_object_geometry_identical']
if a.reference_review:
 rr=read(a.reference_review);assert rr['passed'] and rr['before_board_sha256']==old and rr['board_sha256']==h and rr['comparison_sha256']==sha(comp)
 assert rr['critical_copper_identical'] and rr['all_missing_centerline_geometries_equal'] and rr['all_missing_width_geometry_outside_existing_own_via_windows_equal']
elif a.intentional_i2c_review:
 from verify_intentional_i2c_review import verify
 i2c_review=verify(a.intentional_i2c_review,old,h,comp,R)
elif a.reference_window_classification:
 from verify_reference_window_classification import verify
 window_review=verify(a.reference_window_classification,old,h,comp,R)
else:
 assert all(v==0 for x in q['net_numeric_deltas_after_minus_before'].values() for v in x.values())
 assert all(v['lost_GND_overlap_with_trace_width_mm2']==0 for x in q['ground_fill_changes'].values() for v in x['critical_trace_proximity'].values())
integration_kind='coordinated' if a.coordinated else 'additive';integration_name=f'owner-{integration_kind}-integration.json';add=S/integration_name;assert read(add)['passed'] and read(add)['source_board_sha256']==old and read(add)['board_sha256']==h
actual=S/'actual-io22.json';io=read(actual);assert io['board_sha256']==h
prior=read(C/'current-actual-io22.json');assert {x['id'] for x in prior['checks'] if x['complete_clamp_first_path_passes']}<={x['id'] for x in io['checks'] if x['complete_clamp_first_path_passes']}
for file in [S/'stock-spi-binding.json',S/'current-review.json',S/'snapshot/critical-reference.json',D/'power-revalidation-required.json']:assert h in json.dumps(read(file)),str(file)
sys.path.insert(0,str(R/'ordinary-routing/tests/mpn-parity'));from apply_metadata_copy import parse,children,shape
if a.footprint_translations or a.footprint_transforms:
 assert a.coordinated and a.placement_previews,'Translated footprints require coordinated review and fresh previews'
 if a.footprint_transforms:
  from verify_footprint_transforms import verify as verify_pose
  declaration=a.footprint_transforms;kind='transform'
 else:
  from verify_footprint_translations import verify as verify_pose
  declaration=a.footprint_translations;kind='translation'
 proof=verify_pose(O/'f722-heli.kicad_pcb',D/'f722-heli.kicad_pcb',declaration)
 assert read(add)[f'footprint_{kind}_review']==proof
 assert read(N/'placement.json')==read(D/'poses-native.json')
 previews=a.placement_previews.resolve();pv=read(previews/'placement-preview-source.json')
 assert pv['routed_board_sha256']==h and pv['poses_sha256']==sha(D/'poses-native.json') and pv['source_unchanged'] is True
 assert set(pv['files_sha256'])=={'placement-front.svg','placement-back.svg'}
 for name,digest in pv['files_sha256'].items():
  assert sha(previews/name)==digest
  shutil.copy2(previews/name,C/name)
 pf=C/f'{kind}-placement{n}.json';proof['placement_json_sha256']=sha(N/'placement.json');write(pf,proof)
 shutil.copy2(declaration,C/f'declared-placement-{kind}s{n}.json')
 pv.update(prior_routed_board_sha256=old);pv[f'{kind}_evidence']={'receipt':pf.name,'sha256':sha(pf),'all_footprint_structure_matches_declared_pose_operation':True}
 write(C/'placement-preview-source.json',pv)
else:
 assert not a.placement_previews,'Fresh preview option belongs to explicit placement revision'
 of=children(parse((O/'f722-heli.kicad_pcb').read_text()),'footprint');nf=children(parse((D/'f722-heli.kicad_pcb').read_text()),'footprint');assert len(of)==len(nf)==156 and [shape(x) for x in of]==[shape(x) for x in nf]
 proof={'source_board_sha256':old,'board_sha256':h,'all_156_footprints_exact':True,'placement_json_sha256':sha(N/'placement.json'),'scope':'Complete native footprints identical; placement-only previews apply, routing omitted.'};pf=C/f'unchanged-placement{n}.json';write(pf,proof)
 pv=read(C/'placement-preview-source.json');pv.update(routed_board_sha256=h,prior_routed_board_sha256=old,unchanged_placement_evidence={'receipt':pf.name,'sha256':sha(pf),'all_156_physical_footprint_structures_identical':True});write(C/'placement-preview-source.json',pv)
for src,name in [(D/'f722-heli.import.json','ordinary-import.json'),(D/'f722-heli.logical-route-map.json','ordinary-logical-route-map.json'),(D/'route-handoff.json','ordinary-route-handoff.json'),(add,integration_name),(actual,'current-actual-io22.json'),(D/'power-revalidation-required.json','power-revalidation-required.json'),(S/'stock-spi-binding.json','stock-spi-binding.json')]:shutil.copy2(src,C/name)
folder=C/f'checkpoint{D.name.removeprefix("candidate")}-integration';folder.mkdir(exist_ok=True)
for name in ['endpoint-audit.json','route-handoff.json','power-revalidation-required.json','native-construction.json','construction-provenance.json','tail-repair.json','engine-lineage.json','raw-engine-import.json']:
 if (D/name).is_file():shutil.copy2(D/name,folder/name)
shutil.copy2(add,folder/integration_name)
if a.coordinated:write(C/'owner-additive-integration.json',{'board_sha256':h,'status':'Additive-only proof is not applicable to this coordinated checkpoint. Prior proofs remain in versioned checkpoint directories.','current_report':integration_name})
receipt={'board_sha256':h,'native_unfinished_connections':n,'native_errors':0,'native_warnings':0,'native_gate_receipt_sha256':sha(D/'owner-summary.json'),'integration_kind':integration_kind,'integration_receipt_sha256':sha(add),'reference_comparison_sha256':sha(comp),'actual_io_receipt_sha256':sha(actual),'actual_io_complete_cases':io['passed'],'actual_io_total_cases':io['total'],'numerical_applicability':False,'reason':'Changed geometry since the separately screened source; current numerical power/VCAP requires source-bound revalidation.','status':'Adopted partial geometric routing checkpoint; electrical and physical qualification incomplete.'};
if a.reference_review:
 receipt['reference_change_review_sha256']=sha(a.reference_review);shutil.copy2(a.reference_review,folder/'reference-change-review.json')
if a.intentional_i2c_review:
 receipt['intentional_i2c_geometric_review']=i2c_review;shutil.copy2(a.intentional_i2c_review,folder/'intentional-i2c-geometric-review.json')
if a.reference_window_classification:
 receipt['reference_window_classification']=window_review;shutil.copy2(a.reference_window_classification,folder/'reference-window-classification.json')
write(D/'owner-adoption.json',receipt);write(C/f'checkpoint{n}-owner-review.json',receipt);write(folder/'owner-adoption.json',receipt)
s=read(C/'current-status.json');s['warning_scope']=f'Native normal/all-track DRC: zero geometric warnings,{n} unfinished connections.';s['loaded_power_diagnostic']=re.sub(r'current\d+ geometry',f'current{n} geometry',s['loaded_power_diagnostic']);channels={(x['net'],x['clamp']) for x in io['checks'] if x['complete_clamp_first_path_passes']};s['actual_signal_clamp_channels'].update(complete=len(channels),endpoint_cases_complete=io['passed']);legacy=read(D/'owner-protection.json')['checks']
for scope,key in [('actual_clamp','legacy_original_actual'),('nc_routing_pad','legacy_original_nc')]:s['actual_signal_clamp_channels'][key]={'passed':sum(x['complete_clamp_first_path_passes'] for x in legacy if x['scope']==scope),'total':sum(x['scope']==scope for x in legacy)}
write(C/'current-status.json',s)
for p in [N/'README.md',R/'repo/f722-heli/README.md']:
 t=p.read_text().replace(f'{before} unfinished',f'{n} unfinished').replace(f'{before}-open',f'{n}-open').replace(f'current{before}',f'current{n}');p.write_text(t)
NR=N/'signal-review/native'
for src,dst in [(S/'current-review.json',NR/'current-review.json'),(S/'snapshot/critical-reference.json',NR/'critical-reference.json'),(comp,NR/comp.name)]:shutil.copy2(src,dst)
p=NR/'README.md';p.write_text(p.read_text().replace(f'{before}-open',f'{n}-open').replace(old,h));m=read(NR/'FILES.sha256.json');m['source_board_sha256']=h
for row in m['files']:row['sha256']=sha(NR/row['source'])
if not any(row['source']==comp.name for row in m['files']):m['files'].append({'source':comp.name,'sha256':sha(NR/comp.name)})
write(NR/'FILES.sha256.json',m)
p=R/'ACTIVE-STATE.json';d=read(p);d.update(unfinished_connections=n,candidate_sha256=h,candidate_stage=f'Adopted{n} geometric WIP; numerical power/VCAP pending.');d['work']['ordinary']=f'Adopted {D.name}/{n}; next distinct groups underway.';d['work']['owner']=f'Current{n} owner acceptance and reference/identity refresh complete.';write(p,d)
print(json.dumps({'refreshed_count':n,'sha256':h,'actual_io_cases':io['passed'],'distinct_channels':len(channels),'numerical_applicability':False}))
