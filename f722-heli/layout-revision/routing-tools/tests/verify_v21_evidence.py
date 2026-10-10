#!/usr/bin/env python3
"""Portable V21 source recovery, receipt binding and conditional arithmetic.

No native geometry, pose, DRC, reference, finite-entry, router or FEM replay.
"""
import argparse,ast,copy,hashlib,importlib.util,json,math,re,sys,tempfile,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if sys.flags.optimize:raise RuntimeError('Assertions must be enabled')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base-project',type=Path,required=True);ap.add_argument('--historical-workspace',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 e=module('v21_raw',ROOT/'tests/checkpoint54/materialize.py').Evidence();identity=read(ROOT/'checks/v21-source-identity.json');packet=ROOT/'sessions/recovery-v21';manifest=read(packet/'paired-files.json');recovery=module('v21_recovery',packet/'rebuild_historical_source.py')
 index=e.index['files'];excluded=e.index['excluded_files'];recovered=e.index['recovered_files'];allrows={**index,**excluded,**recovered};neg=[]
 def reject(label,f):
  try:f()
  except (AssertionError,ValueError,KeyError,FileNotFoundError):neg.append(label)
  else:raise AssertionError('Invalid input accepted: '+label)
 def original(name):return allrows[name]['sha256']
 for n in index:e.verify(n)
 for n in excluded:reject('excluded raw input: '+n,lambda n=n:e.bytes(n))
 for n,row in identity['frozen_helpers'].items():assert original(n)==row['sha256']
 if a.historical_workspace:
  for n,row in allrows.items():assert sha(a.historical_workspace/e.index['frozen_alias_sources'].get(n,n))==row['sha256'],n
 projects=[];stages=[];transactions=[]
 with tempfile.TemporaryDirectory(prefix='v21-evidence-')as t:
  tmp=Path(t)
  for label,row in manifest['sources'].items():
   outputs=recovery.prepare_project(a.base_project,label,packet)
   for n,data in outputs.items():
    p=tmp/row['workspace_path']/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
   projects.append({'source':label,'paired_files':len(outputs),'board_sha256':sha(tmp/row['workspace_path']/'f722-heli.kicad_pcb'),'status':row['status']})
  for n in index:e.put(n,tmp)
  for n,row in recovered.items():assert sha(tmp/n)==row['sha256'],n
  j=lambda n:read(tmp/n);folder=lambda label:manifest['sources'][label]['workspace_path']+'/'
  parserpath=tmp/'ordinary-routing/tests/mpn-parity/apply_metadata_copy.py';tree=ast.parse(parserpath.read_text());wanted={'Atom','Node','parse','children','child','value','properties','shape'}
  nodes=[n for n in tree.body if (isinstance(n,(ast.ClassDef,ast.FunctionDef))and n.name in wanted)or(isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='TOKEN'for x in n.targets))]
  parser=types.ModuleType('v21_parser');parser.__dict__.update(re=re,json=json);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(parserpath),'exec'),parser.__dict__)
  keyed=lambda root,kind:{parser.value(n,'uuid'):n for n in parser.children(root,kind)}
  point=lambda node,key:[float(x.value)for x in parser.child(node,key).items[1:]]
  parsed={label:parser.parse((tmp/folder(label)/'f722-heli.kicad_pcb').read_text())for label in manifest['sources']}
  def transaction(old,new,receipt,changed_refs):
   before,after=parsed[old],parsed[new];oldob={u:n for k in ('segment','via','arc')for u,n in keyed(before,k).items()};newob={u:n for k in ('segment','via','arc')for u,n in keyed(after,k).items()}
   added=set(newob)-set(oldob);removed=set(oldob)-set(newob);changed={u for u in set(oldob)&set(newob)if parser.shape(oldob[u])!=parser.shape(newob[u])}
   assert added=={r['uuid']for r in receipt['added_objects']} and removed=={r['uuid']for r in receipt.get('removed_objects',[])} and changed=={r['uuid']for r in receipt.get('changed_objects',[])}
   allowed=receipt.get('allowed_changed_nets',receipt.get('allowed_added_nets'))
   for field,records,side in [('added_objects',newob,'after'),('removed_objects',oldob,'before')]:
    for r in receipt.get(field,[]):
     if side in r:assert r[side]==parser.shape(records[r['uuid']])
     assert r['net']==parser.value(records[r['uuid']],'net') and r['net']in allowed
   for r in receipt.get('changed_objects',[]):assert r['before']==parser.shape(oldob[r['uuid']]) and r['after']==parser.shape(newob[r['uuid']]) and r['net']in allowed
   of,nf=keyed(before,'footprint'),keyed(after,'footprint');assert set(of)==set(nf) and len(nf)==156;assert sum(len(parser.children(f,'pad'))for f in nf.values())==558
   actual={parser.properties(of[u])['Reference'].items[2].value for u in of if parser.shape(of[u])!=parser.shape(nf[u])};assert actual==set(changed_refs)
   def config(z):return [parser.shape(x)if isinstance(x,parser.Node)else x.value for x in z.items if not(isinstance(x,parser.Node)and x.items[0].value in ('filled_polygon','fill_segments'))]
   oz,nz=keyed(before,'zone'),keyed(after,'zone');assert set(oz)==set(nz) and all(config(oz[u])==config(nz[u])for u in oz)
   skip={'footprint','segment','via','arc','zone'};rest=lambda r:[parser.shape(x)if isinstance(x,parser.Node)else x.value for x in r.items if not(isinstance(x,parser.Node)and x.items[0].value in skip)]
   assert rest(before)==rest(after)
   transactions.append({'source':old,'target':new,'added':len(added),'removed':len(removed),'changed':len(changed),'unchanged_full_footprints':156-len(actual),'changed_references':sorted(actual),'total_pads':558})
  support=module('v21_support',tmp/'integrated-routing/verify_support_adoption.py');adopt_verify=module('v21_adopt',tmp/'integrated-routing/verify_adoption_integration.py')
  for label,old,count,cases,expected_seal,kind in [('SERVO15','candidate52',15,19,166,'coordinated'),('RPM14','SERVO15',14,20,148,'additive'),('candidate54','RPM14',14,20,146,'coordinated')]:
   c=folder(label);source_folder=folder(old);board=identity['expected_boards'][label];source=identity['expected_boards'][old];hand=j(c+'route-handoff.json');seal=identity['sealed_worker_manifests'][label]
   assert original(c+'route-handoff.json')==seal['manifest']['sha256'] and len(hand['files'])==seal['files']==expected_seal
   for n,h in hand['files'].items():assert original(c+n)==h,(label,n)
   native=j(c+'owner-summary.json');prov=j(c+'construction-provenance.json');audit=j(c+'entry-support-audit.json');wrapper=j(c+'power-audit.json');prior=j(source_folder+'power-audit.json')
   assert hand['board_sha256']==native['board_sha256']==prov['board_sha256']==board and hand['integration_source_sha256']==prov['source_board_sha256']==source
   assert native['drc']==native['drc-all']=={'unconnected':count,'errors':0,'warnings':0}
   for s in ('process','mechanical','parity','firmware'):assert native[s]['passed'] and native[s]['board_sha256']==board
   assert native['critical']['connected_nets']==native['critical']['total_nets']==16 and not native['critical']['faults'] and not native['critical']['missing_ground_returns']
   assert not j(c+'owner-drc-parity.json')['schematic_parity'] and not j(c+'owner-drc-parity.json')['violations'];assert not any(x['violations']for x in j(c+'owner-erc.json')['sheets'])
   assert prov['proposal_sha256']==original(c+'proposal.json') and prov['source_native_sha256']==original(source_folder+'f722-heli.native.json') and prov['constructor_sha256']in {v['sha256']for v in identity['frozen_helpers'].values()}
   def bind(w):
    assert w['passed']is audit['passed']is True and w['board_sha256']==audit['board_sha256']==board and w['source_board_sha256']==audit['source_board_sha256']==source
    assert w['audit_sha256']==original(c+'entry-support-audit.json') and w['source_audit_sha256']==original(source_folder+'power-audit.json')
    assert w['native_sha256']==audit['native_sha256']==original(c+'f722-heli.native.json') and w['source_native_sha256']==audit['source_native_sha256']==original(source_folder+'f722-heli.native.json')
    assert w['nets']==audit['nets'] and len(w['nets'])==28 and all(audit.get('gates',{}).values()) and not w['numerical_power_VCAP_applicable']
    for n,r in w['nets'].items():assert r['complete'] and r['pad_group_count']==1 and r['groups']==prior['nets'][n]['groups'] and r['source_groups_exactly_preserved']
   bind(wrapper)
   for key,value in [('board_sha256','0'*64),('audit_sha256','0'*64),('native_sha256','0'*64),('numerical_power_VCAP_applicable',True)]:
    bad=copy.deepcopy(wrapper);bad[key]=value;reject(label+' support '+key,lambda bad=bad:bind(bad))
   assert support.verify(wrapper,prior,source,board,tmp/c)=={'passed':True,'nets':28,'typed_audit_binding_checked':False}
   assert all(r['rejected']for r in audit['negative_controls'])
   cut=j(c+'protection-actual-io.json');assert cut['passed']==cases and cut['total']==22
   previous=j(source_folder+'protection-actual-io.json');passes=lambda x:{r['id']for r in x['checks']if r['complete_clamp_first_path_passes']};assert passes(previous)<=passes(cut)
   transaction(old,label,j(c+'native-'+kind+'-integration.json'),['R50']if label=='SERVO15'else [])
   stages.append({'source':label,'opens':count,'native_errors':0,'native_warnings':0,'seal_files':expected_seal,'actual_cases':[cases,22],'stored_finite_controls':len(audit['negative_controls']),'support_adapter_reexecuted':True,'adopted_in_its_own_right':label=='candidate54'})
  c=folder('candidate54');board=identity['expected_boards']['candidate54'];base=identity['expected_boards']['candidate52'];review='checkpoint14-ground-owner-review/'
  report=j(review+'owner-coordinated-integration.json');worker_cumulative=j(c+'cumulative-source52-native-coordinated.json')
  assert {k:v for k,v in report.items()if k!='allowed_changed_nets'}=={k:v for k,v in worker_cumulative.items()if k!='allowed_changed_nets'} and set(report['allowed_changed_nets'])==set(worker_cumulative['allowed_changed_nets'])
  transaction('candidate52','candidate54',report,['R50']);assert adopt_verify.verify(report,base,board)
  for key,value in [('schema','bad'),('passed',False),('source_board_sha256','0'*64),('board_sha256','0'*64),('allowed_changed_nets',[])]:
   bad=copy.deepcopy(report);bad[key]=value;reject('cumulative adoption '+key,lambda bad=bad:adopt_verify.verify(bad,base,board))
  for field in ('added_objects','removed_objects'):
   bad=copy.deepcopy(report);bad[field]=bad[field][1:];reject('parsed cumulative transaction omitted '+field,lambda bad=bad:transaction('candidate52','candidate54',bad,['R50']))
  declaration=j(c+'cumulative-source52-footprint-transforms.json');assert declaration['source_board_sha256']==base and declaration['board_sha256']==board and set(declaration['changes'])=={'R50'}
  assert declaration['changes']['R50']['before']==[11.7,13.6,0,'F.Cu'] and declaration['changes']['R50']['after']==[11.95,13.6,0,'F.Cu']
  adopt=j(c+'owner-adoption.json');imp=j(c+'f722-heli.import.json');owner=j(review+'owner-review-run.json')
  assert adopt['board_sha256']==imp['output_sha256']==owner['board_sha256']==board and adopt['native_unfinished_connections']==owner['native_count']==14
  assert not adopt['numerical_applicability'] and adopt['actual_io_complete_cases']==20 and adopt['actual_io_total_cases']==22 and adopt['integration_receipt_sha256']==imp['owner_cumulative_integration_sha256']==original(review+'owner-coordinated-integration.json')
  assert adopt['native_gate_receipt_sha256']==imp['native_gate_receipt_sha256']==original(c+'owner-summary.json') and owner['previous_board_sha256']==base and owner['sealed_native_receipts_verified']
  assert imp['source_sha256']==identity['expected_boards']['RPM14'] and imp['owner_cumulative_source_sha256']==base
  for k in ('direct_engine_output','engine_routing_succeeded','fresh_model_zero_control_performed','numerical_power_VCAP_applicable'):assert imp[k]is False
  assert {r['command']:r['exit_code']for r in owner['commands']}=={'coordinated':0,'reference':0,'i2c':2,'actual-io22':1,'spi':0}
  comp=j(review+'comparison-17-to-14.json');ref=j(review+'reference-change-review.json');delta=comp['net_numeric_deltas_after_minus_before']['USB_N']['physical_GND_trace_width_missing_mm2'];assert delta==2.6376462125554667e-10
  assert comp['critical_object_geometry_identical'] and ref['passed'] and ref['comparison_sha256']==original(review+'comparison-17-to-14.json') and ref['numeric_differences_retained']==comp['net_numeric_deltas_after_minus_before']
  assert ref['all_missing_centerline_geometries_equal'] and ref['all_missing_width_geometry_outside_existing_own_via_windows_equal'] and ref['changed_regions'][0]['changed_width_region_mm2']==2.6376491257347183e-10
  assert adopt['reference_change_review_sha256']==original(review+'reference-change-review.json')
  direct=j(c+'reference-comparison14.json');alltracks=j(c+'all-signal-reference-ground-delta.json');audit=j(c+'entry-support-audit.json');nativebinding=j(c+'conditional-support-review/native-binding.json')
  assert all(v==0 for row in direct['net_numeric_deltas_after_minus_before'].values()for v in row.values()) and direct['critical_object_geometry_identical']
  assert alltracks['passed'] and alltracks['track_projection_count']==1259 and alltracks['all_changed_projection_intersections_exactly_empty'] and alltracks['all_non_GND_native_objects_exact']
  assert audit['new_track_endpoints_checked']==14 and audit['new_tracks']==7 and audit['new_vias']==1 and audit['all24_RPM_additive_objects_exact'] and len(audit['signal_groups'])==21
  assert nativebinding['passed'] and nativebinding['audit_sha256']==original(c+'entry-support-audit.json')
  contacts=nativebinding['outer_layer_contacts_to_first_vias'];assert contacts['U12.2']['pads']==['U12.2'] and contacts['R51.2']['pads']==['R51.2'] and set(contacts['R52.2']['pads'])=={'R52.2','C30.2'}
  ties=j(c+'reference-snapshot/critical-reference.json')['GND_ties'];assert len(ties['accepted'])==117 and not ties['rejected']
  rpm=j(folder('RPM14')+'route-handoff.json');assert rpm['new_width_projection_complete']is False and rpm['new_width_gap_outside_own_windows_mm2']==2.725130554532544e-05
  failed=j(c+'failed-dedicated-R52-tie-evidence.json');badsummary='ordinary-routing/tests/servo48/candidate05/owner-summary.json';assert failed['native_summary_sha256']==original(badsummary) and failed['result']==j(badsummary)['drc']=={'unconnected':14,'errors':2,'warnings':0}
  # Recompute only the explicitly assumed shared-track resistance/IMON sensitivity.
  ev=j(c+'conditional-support-review/evidence.json');dc=ev['conditional_shared_copper_DC'];assert ev['board_sha256']==board and ev['source14_board_sha256']==identity['expected_boards']['RPM14'] and ev['source14_proposal_byte_identical']
  tracks=keyed(parsed['candidate54'],'segment');shared=tracks[ev['paths']['shared_C30_to_via']['uuid']];length=math.dist(point(shared,'start'),point(shared,'end'));assert length==dc['length_mm'] and float(parser.value(shared,'width'))==dc['width_mm']==.25
  resistance=dc['rho20_assumed_ohm_m']*(1+dc['alpha_assumed_per_C']*(dc['copper_temperature_assumed_C']-20))*length*1e-3/(dc['width_mm']*1e-3*dc['thickness_assumed_um']*1e-6)
  assert math.isclose(resistance,dc['resistance_ohm'],rel_tol=1e-15)
  assert dc['ILM_max_current_A']==.0004 and dc['rail_normal_current_assumed_A']==2 and dc['TI_GIMON_min_max_uA_per_A']==[165,200]
  assert math.isclose(resistance/.95,dc['95_percent_IACS_sensitivity']['resistance_ohm'],rel_tol=1e-15) and math.isclose(resistance/.95*.0011*1e6,dc['95_percent_IACS_sensitivity']['at_datasheet_5p5A_illustration_drop_uV'],rel_tol=1e-15)
  assert len(dc['excluded'])==6 and 'not this board continuous-current rating' in ev['load_scope_correction']
  assessment=j(review+'owner-adoption-assessment.json');assert assessment['eligible_for_geometric_prototype_checkpoint'] and not assessment['electrical_qualified'] and not assessment['physical_qualified'] and not assessment['numerical_power_VCAP_current']
  r=j('checkpoint14-ground-placement-reproduction/placement-reproduction.json');preview=j('checkpoint14-ground-placement-preview/placement-preview-source.json');assert r['source_board_sha256']==preview['routed_board_sha256']==board and r['156_poses_exact'] and r['558_complete_native_pad_records_exact'] and r['paired_native_parity_passed']
  assert r['placement_json_sha256']==preview['poses_sha256']==original(c+'poses-native.json')
  for name,h in preview['files_sha256'].items():assert original('checkpoint14-ground-placement-preview/'+name)==h
  d=read(packet/'candidate54.f722-heli.kicad_pcb.delta.json');basebytes=(a.base_project/'f722-heli.kicad_pcb').read_bytes()
  for key,value in [('base_sha256','0'*64),('target_sha256','0'*64),('target_bytes',-1),('operations',[[len(basebytes)+1,1]]),('base_transform','unsupported')]:
   bad=copy.deepcopy(d);bad[key]=value;reject('paired recovery '+key,lambda bad=bad:recovery.reconstruct(basebytes,bad))
  reject('unsafe recovery path',lambda:recovery.relative_path('../escape'))
 result={'passed':True,'verifier_source_sha256':sha(__file__),'recovered_projects':projects,'raw_files_verified':len(index),'excluded_raw_files':len(excluded),'frozen_helpers':len(identity['frozen_helpers']),'original_source_hash_checks_performed':bool(a.historical_workspace),'negative_controls_passed':len(neg),'negative_controls':neg,'stages':stages,'pure_parser_transactions':transactions,'conditional_track_arithmetic_reexecuted':True,'conditional_shared_track_resistance_95_percent_IACS_ohm':resistance/.95,'cumulative_USB_N_width_delta_preserved_mm2':delta,'RPM_width_residue_preserved_mm2':rpm['new_width_gap_outside_own_windows_mm2'],'historical_SERVO15_RPM14_not_adopted_separately':True,'native_pose_transform_or_placement_reproduction_reexecuted':False,'native_DRC_reference_finite_classifier_or_access_reexecuted':False,'native_replay_inputs_complete':False,'heavy_or_native_execution_performed':False,'numerical_power_and_VCAP_applicability':False,'hardware_or_fabrication_qualification':False,'source43_power_scope':'Historical source43/37 only','scope':'Exact four-project paired recovery; original seals; syntax-tree transactions; support/cumulative-adoption adapters and conditional local DC arithmetic. Stored native findings are preserved, not replayed.'}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
