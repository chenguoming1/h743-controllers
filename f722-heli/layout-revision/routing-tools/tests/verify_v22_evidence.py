#!/usr/bin/env python3
"""Portable exact-byte recovery, source bindings and board syntax-tree transaction checks.

Stored native/reference/placement/signal findings are not native replay.
"""
import argparse,ast,copy,hashlib,importlib.util,json,math,re,sys,tempfile,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if sys.flags.optimize:raise RuntimeError('Assertions must be enabled')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base-project',type=Path,required=True);ap.add_argument('--historical-workspace',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 e=module('raw22',ROOT/'tests/checkpoint55/materialize.py').Evidence();identity=read(ROOT/'checks/v22-source-identity.json');packet=ROOT/'sessions/recovery-v22';manifest=read(packet/'paired-files.json');recovery=module('recover22',packet/'rebuild_historical_source.py')
 rows={**e.index['files'],**e.index['excluded_files'],**e.index['recovered_files']};neg=[]
 def original(n):return rows[n]['sha256']
 def reject(label,fn):
  try:fn()
  except (AssertionError,ValueError,KeyError,FileNotFoundError):neg.append(label)
  else:raise AssertionError('Invalid input accepted: '+label)
 for n in e.index['files']:e.verify(n)
 for n in e.index['excluded_files']:reject('excluded raw input '+n,lambda n=n:e.bytes(n))
 for n,row in identity['frozen_helpers'].items():assert original(n)==row['sha256']
 if a.historical_workspace:
  for n,row in rows.items():assert sha(a.historical_workspace/e.index['frozen_alias_sources'].get(n,n))==row['sha256'],n
 projects=[]
 with tempfile.TemporaryDirectory(prefix='v22-evidence-')as t:
  temp=Path(t)
  for label,row in manifest['sources'].items():
   outputs=recovery.prepare_project(a.base_project,label,packet)
   for n,data in outputs.items():
    p=temp/row['workspace_path']/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
   projects.append({'source':label,'paired_files':len(outputs),'board_sha256':sha(temp/row['workspace_path']/'f722-heli.kicad_pcb')})
  for n in e.index['files']:e.put(n,temp)
  for n,row in e.index['recovered_files'].items():assert sha(temp/n)==row['sha256'],n
  j=lambda n:read(temp/n);folder=lambda label:manifest['sources'][label]['workspace_path']+'/'
  c=folder('candidate55');s=folder('sealed55');b=folder('candidate54');before=identity['expected_boards']['candidate54'];after=identity['expected_boards']['candidate55']
  hand=j(s+'route-handoff.json');assert len(hand['files'])==132 and original(c+'route-handoff.json')==original(s+'route-handoff.json')==identity['sealed_worker_manifest']['manifest']['sha256']
  for n,h in hand['files'].items():
   assert original(s+n)==h
   assert original(c+('power-audit-sealed-original.json'if n=='power-audit.json'else n))==h,n
  native=j(c+'owner-summary.json');assert native['board_sha256']==after and native['drc']==native['drc-all']=={'unconnected':13,'errors':0,'warnings':0}
  for k in ['process','mechanical','parity','firmware']:assert native[k]['passed'] and native[k]['board_sha256']==after
  assert native['critical']['connected_nets']==native['critical']['total_nets']==16 and not native['critical']['faults'] and not native['critical']['missing_ground_returns']
  assert not j(c+'owner-drc-parity.json')['schematic_parity'] and not any(r['violations']for r in j(c+'owner-erc.json')['sheets'])
  prov=j(c+'construction-provenance.json');assert prov['source_board_sha256']==before and prov['board_sha256']==after and prov['constructor_sha256']==original(c+'construct.used.py') and prov['proposal_sha256']==original(c+'proposal.json')
  assert prov['source_native_sha256']==original(b+'f722-heli.native.json') and prov['source_map_sha256']==original(b+'f722-heli.logical-route-map.json')
  wrapper=j(c+'power-audit.json');sealed=j(c+'power-audit-sealed-original.json');audit=j(c+'entry-support-audit.json');prior=j(b+'power-audit.json')
  def adapter_check(w):
   adapter=w['serialization_adapter'];assert adapter['original_sha256']==original(c+adapter['original_file'])==original(s+'power-audit.json')
   assert w['board_sha256']==audit['board_sha256']==after and w['source_board_sha256']==audit['source_board_sha256']==before and w['passed'] and audit['passed']
   assert w['audit_sha256']==original(c+'entry-support-audit.json') and w['native_sha256']==original(c+'f722-heli.native.json') and w['source_native_sha256']==original(b+'f722-heli.native.json')
   assert not w['numerical_power_qualified'] and len(w['nets'])==28
   stripped=copy.deepcopy(w);del stripped['serialization_adapter']
   for n,row in stripped['nets'].items():assert row.pop('pad_group_count')==len(row['groups'])==1 and row['complete'] and row['source_groups_exactly_preserved']
   assert stripped==sealed and audit['nets']==sealed['nets']
  adapter_check(wrapper)
  for key,value in [('board_sha256','0'*64),('audit_sha256','0'*64),('native_sha256','0'*64),('numerical_power_qualified',True)]:
   bad=copy.deepcopy(wrapper);bad[key]=value;reject('support '+key,lambda bad=bad:adapter_check(bad))
  bad=copy.deepcopy(wrapper);next(iter(bad['nets'].values()))['pad_group_count']=2;reject('support forged group count',lambda:adapter_check(bad))
  support=module('support22',temp/'integrated-routing/verify_support_adoption.py');assert support.verify(wrapper,prior,before,after,temp/c)=={'passed':True,'nets':28,'typed_audit_binding_checked':False}
  assert audit['new_tracks']==104 and audit['new_vias']==13 and audit['new_track_endpoints_checked']==208 and len(audit['signal_groups'])==7 and all(v['rejected']for v in audit['negative_controls'])
  assert audit['R44_dedicated_return']['pads']==['R44.2'] and all(v>0 for v in audit['R44_saved_GND_plane_annular_contacts_mm2'].values())
  # Parse the complete native board text without loading KiCad or geometry libraries.
  parserpath=temp/'ordinary-routing/tests/mpn-parity/apply_metadata_copy.py';tree=ast.parse(parserpath.read_text());wanted={'Atom','Node','parse','children','child','value','properties','shape'}
  nodes=[n for n in tree.body if (isinstance(n,(ast.ClassDef,ast.FunctionDef))and n.name in wanted)or(isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='TOKEN'for x in n.targets))]
  parser=types.ModuleType('parser22');parser.__dict__.update(re=re,json=json);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(parserpath),'exec'),parser.__dict__)
  parsed={label:parser.parse((temp/folder(label)/'f722-heli.kicad_pcb').read_text())for label in ['candidate54','candidate55']}
  keyed=lambda root,kind:{parser.value(n,'uuid'):n for n in parser.children(root,kind)}
  old,new=parsed['candidate54'],parsed['candidate55'];ob={u:n for k in ('segment','via','arc')for u,n in keyed(old,k).items()};nb={u:n for k in ('segment','via','arc')for u,n in keyed(new,k).items()}
  report=j('checkpoint13-owner-review/owner-coordinated-integration.json');assert report==j(c+'native-coordinated-integration.json')
  def transaction(r):
   assert {x['uuid']for x in r['removed_objects']}==ob.keys()-nb.keys() and {x['uuid']for x in r['added_objects']}==nb.keys()-ob.keys()
   assert not r['changed_objects'] and all(parser.shape(ob[u])==parser.shape(nb[u])for u in ob.keys()&nb.keys())
   for field,records,side in [('added_objects',nb,'after'),('removed_objects',ob,'before')]:
    for row in r[field]:
     if side in row:assert row[side]==parser.shape(records[row['uuid']])
     assert row['net']==parser.value(records[row['uuid']],'net') and row['net']in r['allowed_changed_nets']
  transaction(report)
  for field in ('added_objects','removed_objects'):
   bad=copy.deepcopy(report);bad[field]=bad[field][1:];reject('transaction omitted '+field,lambda bad=bad:transaction(bad))
  assert len(report['added_objects'])==117 and len(report['removed_objects'])==75
  of,nf=keyed(old,'footprint'),keyed(new,'footprint');assert set(of)==set(nf) and len(nf)==156 and sum(len(parser.children(f,'pad'))for f in nf.values())==558
  changed={parser.properties(of[u])['Reference'].items[2].value for u in of if parser.shape(of[u])!=parser.shape(nf[u])};assert changed=={'R44'}
  poses_before=j(b+'poses-native.json');poses_after=j(c+'poses-native.json');assert {n for n in poses_before if poses_before[n]!=poses_after[n]}=={'R44'} and poses_before['R44']==[25.8,16.0,90,'F.Cu'] and poses_after['R44']==[25.8,16.0,-90,'F.Cu']
  def config(z):return [parser.shape(x)if isinstance(x,parser.Node)else x.value for x in z.items if not(isinstance(x,parser.Node)and x.items[0].value in ('filled_polygon','fill_segments'))]
  oz,nz=keyed(old,'zone'),keyed(new,'zone');assert set(oz)==set(nz) and all(config(oz[u])==config(nz[u])for u in oz)
  skip={'footprint','segment','via','arc','zone'};rest=lambda r:[parser.shape(x)if isinstance(x,parser.Node)else x.value for x in r.items if not(isinstance(x,parser.Node)and x.items[0].value in skip)];assert rest(old)==rest(new)
  adopt_verify=module('adopt22',temp/'integrated-routing/verify_adoption_integration.py');assert adopt_verify.verify(report,before,after)
  for key,value in [('schema','bad'),('passed',False),('source_board_sha256','0'*64),('board_sha256','0'*64),('allowed_changed_nets',[])]:
   bad=copy.deepcopy(report);bad[key]=value;reject('adoption '+key,lambda bad=bad:adopt_verify.verify(bad,before,after))
  for n in ['checkpoint13-owner-review/reference-region/owner/reference-classification.json','checkpoint13-owner-review/all-net-reference-summary.json']:
   for path,h in j(n)['source_hashes'].items():assert original(path)==h,(n,path)
  ref=j('checkpoint13-owner-review/reference-region/owner/reference-classification.json');summary=j('checkpoint13-owner-review/all-net-reference-summary.json');assessment=j('checkpoint13-owner-review/owner-adoption-assessment.json')
  assert ref['before_board_sha256']==before and ref['after_board_sha256']==after and ref['source_binding_verified'] and ref['critical_copper_identical']
  assert ref['classification_status']=='UNRESOLVED_ACTUAL_HOLE_BOUNDARY_PREDICATES' and ref['exact_containment_predicate_disagreement_count']==8 and not ref['missing_centerline_geometries_exactly_equal'] and not ref['all_changed_critical_projection_geometry_inside_actual_hole_window_intersections']
  assert ref['all_changed_critical_projection_geometry_inside_unchanged_own_windows'] and ref['all_changed_critical_projection_residuals_outside_unchanged_own_windows_empty']
  assert summary['target_count']==86 and summary['unchanged_routed_net_count']==79 and summary['ground_ties']=={'accepted':117,'rejected':0} and not summary['qualification']
  assert assessment['geometric_wip_adoption_eligible'] and not assessment['qualification'] and assessment['reference_classification']['actual_hole_predicate_disagreements']==8
  for n,h in assessment['review_sha256'].items():assert original('checkpoint13-owner-review/'+n)==h
  sr='ordinary-routing/tests/small-signal-review54/';signal=j(sr+'review-receipt.json');assert signal['board_sha256']==after and signal['native_handoff_sha256']==original(s+'route-handoff.json') and not signal['electrical_qualification_claimed']
  for n,h in signal['files'].items():assert original(sr+n)==h
  assert assessment['signal_review_sha256']==original(sr+'review-receipt.json')
  for row in j(sr+'source-index.json')['files']:assert original(row['path'])==row['sha256']
  for row in j(sr+'source-index.json')['new_firmware_files_git_blob_verified']:
   data=(temp/row['path']).read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_blob_sha1']
  arithmetic=j(sr+'arithmetic.json');assert not arithmetic['qualified'] and arithmetic['board_sha256']==after
  tracks=keyed(new,'segment');point=lambda node,key:[float(x.value)for x in parser.child(node,key).items[1:]]
  for label,path in [('GREEN',arithmetic['GREEN']),('DSM',arithmetic['DSM']['main_path'])]:
   measured=sum(math.dist(point(tracks[u],'start'),point(tracks[u],'end'))for u in path['track_uuids']);assert math.isclose(measured,path['length_mm'],rel_tol=1e-14)
  assert math.isclose(arithmetic['ADC']['nominal_RC_s'],21760*220e-9,rel_tol=1e-15)
  cut=j(c+'protection-actual-io.json');priorcut=j(b+'protection-actual-io.json');passes=lambda r:{x['id']for x in r['checks']if x['complete_clamp_first_path_passes']};assert cut['passed']==20 and cut['total']==22 and passes(cut)==passes(priorcut)
  adoption=j(c+'owner-adoption.json');imp=j(c+'f722-heli.import.json');assert adoption['board_sha256']==imp['output_sha256']==after and adoption['native_unfinished_connections']==13 and not adoption['numerical_applicability']
  assert adoption['integration_receipt_sha256']==imp['owner_integration_sha256']==original('checkpoint13-owner-review/owner-coordinated-integration.json') and imp['native_gate_receipt_sha256']==original(c+'owner-summary.json')
  for k in ['direct_engine_output','engine_routing_succeeded','engine_partial_geometry_adopted','fresh_model_zero_control_performed','numerical_power_VCAP_applicable']:assert imp[k]is False
  place=j('checkpoint13-placement-reproduction-native/placement-reproduction.json');preview=j('checkpoint13-placement-preview/placement-preview-source.json');assert place['source_board_sha256']==preview['routed_board_sha256']==after and place['156_poses_exact'] and place['558_complete_native_pad_records_exact'] and place['paired_native_parity_passed']
  assert place['placement_json_sha256']==preview['poses_sha256']==original(c+'poses-native.json')
  for n,h in preview['files_sha256'].items():assert original('checkpoint13-placement-preview/'+n)==h
  d=read(packet/'candidate55.f722-heli.kicad_pcb.delta.json');basebytes=(a.base_project/'f722-heli.kicad_pcb').read_bytes()
  for key,value in [('base_sha256','0'*64),('target_sha256','0'*64),('target_bytes',-1),('operations',[[len(basebytes)+1,1]]),('base_transform','unsupported')]:
   bad=copy.deepcopy(d);bad[key]=value;reject('paired recovery '+key,lambda bad=bad:recovery.reconstruct(basebytes,bad))
  reject('unsafe recovery path',lambda:recovery.relative_path('../escape'))
 result={'passed':True,'verifier_source_sha256':sha(__file__),'recovered_projects':projects,'selected_evidence_paths_verified':len(e.index['files']),'unique_payloads':identity['selected_unique_payloads'],'excluded_raw_files':len(e.index['excluded_files']),'original_source_hash_checks_performed':bool(a.historical_workspace),'frozen_helpers':len(identity['frozen_helpers']),'original_seal_files':132,'source_transaction':{'removed':75,'added_tracks':104,'added_vias':13,'unchanged_footprints':155,'changed_footprint':'R44 rotates180 degrees in place','pads':558},'support_adapter_reexecuted':True,'actual_hole_predicate_disagreements_retained':8,'all_net_reference_targets':86,'source_bound_GREEN_DSM_centerline_lengths_recomputed':True,'negative_controls':neg,'negative_controls_passed':len(neg),'native_DRC_reference_finite_placement_or_signal_review_reexecuted':False,'native_replay_inputs_complete':False,'heavy_or_native_execution_performed':False,'current_numerical_power_VCAP_run':False,'source43_power_scope':'Historical source43 only; no qualification onto current55','electrical_physical_manufacturing_qualification':False}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
