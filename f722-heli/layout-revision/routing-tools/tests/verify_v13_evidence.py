#!/usr/bin/env python3
"""Bounded V13 standard-library recovery, source, identity and receipt checks.

Full native polygon/finite-width/DRC replay is explicitly outside this verifier.
The original 28 geometric mutation controls are preserved as historical evidence.
"""
import argparse, ast, contextlib, copy, hashlib, importlib.util, io, json, re, runpy, sys, tempfile, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base-project',type=Path,required=True);ap.add_argument('--historical-workspace',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 identity=read(ROOT/'checks/v13-source-identity.json');expected=identity['expected_boards'];recovery=module('recovery41',ROOT/'sessions/recovery41/rebuild_historical_source.py');raw=module('evidence41',ROOT/'tests/checkpoint41/materialize.py');negatives=[];recovered=[]
 def reject(label,op):
  try:op()
  except (ValueError,KeyError,AssertionError,FileNotFoundError):negatives.append(label)
  else:raise AssertionError('Accepted invalid input: '+label)
 with raw.Evidence()as e,tempfile.TemporaryDirectory(prefix='v13-controls-')as td:
  tmp=Path(td);idx=e.index['files'];excluded=e.index['excluded_files'];j=e.json;c39='ordinary-routing/candidate39/';c40='ordinary-routing/candidate40/';c41='ordinary-routing/candidate41/'
  def original(n):
   for group in [idx,excluded,e.index['recovered_files']]:
    if n in group:return group[n]['sha256']
   raise KeyError(n)
  for n in idx:
   e.verify(n);e.put(n,tmp)
   if a.historical_workspace:assert sha(a.historical_workspace/n)==idx[n]['sha256'],n
  for n in excluded:
   reject('excluded raw input unavailable: '+n,lambda n=n:e.bytes(n))
   if a.historical_workspace:assert sha(a.historical_workspace/n)==excluded[n]['sha256'],n
  for label in expected:
   outputs=recovery.prepare_project(a.base_project.resolve(),label,ROOT/'sessions/recovery41');out=tmp/'ordinary-routing'/label
   for path,data in outputs.items():
    p=out/path;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==data
    p.write_bytes(data)
   assert len(outputs)==61 and sha(out/'f722-heli.kicad_pcb')==expected[label]
   recovered.append({'source':label,'board_sha256':expected[label],'paired_files':61})
  h=j(c41+'route-handoff.json');ad=j(c41+'owner-adoption.json');native=j(c41+'owner-summary.json');refusal=j(c40+'ISOLATED-REVIEW-STATUS.json')
  assert original(c41+'route-handoff.json')==identity['sealed_handoff_sha256'] and len(h['files'])==48
  for n,digest in h['files'].items():assert original(c41+n)==digest,n
  for n,digest in j(c41+'audit-sources/input-hashes.json').items():assert original('ordinary-routing/'+n)==digest,n
  assert native['drc']==native['drc-all']==dict(unconnected=41,errors=0,warnings=0)
  assert ad['board_sha256']==native['board_sha256']==expected['candidate41'] and ad['native_unfinished_connections']==41 and not ad['numerical_applicability']
  for field,path in [('native_gate_receipt_sha256',c41+'owner-summary.json'),('integration_receipt_sha256','checkpoint41-review/owner-coordinated-integration.json'),('reference_comparison_sha256',c41+'reference-comparison-to39.json'),('actual_io_receipt_sha256',c41+'protection-actual-io.json')]:assert ad[field]==original(path)
  assert refusal['adopted']is False and (refusal['native_opens'],refusal['native_errors'],refusal['native_warnings'])==(41,3,0)
  for n,digest in refusal['files'].items():assert original(c40+n)==digest,n
  assert j(c40+'owner-summary.json')['drc-all']==dict(unconnected=41,errors=3,warnings=0)
  assert all(x['severity']=='error' and x['type']=='courtyards_overlap' for x in j(c40+'owner-drc-all.json')['violations'])
  for pre,proposal,constructor,rem,add in [(c40,'coordinated-route-proposal.json','construct_dsm_complete40.used.py',4,13),(c41,'proposal40.json','construct_dsm_clear41.py',5,9)]:
   r=j(pre+'construction-provenance.json');assert r['proposal_sha256']==original(pre+proposal) and r['constructor_sha256']==original(pre+constructor)
   assert len(r['removed_source_records'])==rem and len(r['added_records'])==add
   assert r['direct_engine_output']is False and r['engine_routing_succeeded']is False and r['numerical_power_VCAP_applicable']is False
  rev=j(c41+'construction-provenance.json')['power_width_revision_explicit'];assert rev['before_width_mm']==.30 and rev['after_width_mm']==.25 and rev['fresh_DC_required']
  audit=j(c41+'candidate41-entry-return.json');transaction=j(c41+'coordinated-change-receipt.json')
  assert audit['passed']and all(v is True for v in audit['gates'].values())and len(audit['gates'])==14
  assert len(audit['strict_pad_entries'])==13 and sum(x['passed']for x in audit['strict_pad_entries'])==11
  assert len(audit['ordinary_support_CORE_track_joins'])==20 and all(x['passed']for x in audit['ordinary_support_CORE_track_joins'])
  assert len(audit['finite_actual_annular_entries'])==2 and all(x['passed']for x in audit['finite_actual_annular_entries'])
  fails=audit['direct_pad_entry_failures_preserved'];assert len(fails)==2 and {x['pad']for x in fails}=={'R26.2','R38.1'} and all(x['passed']is False for x in fails)
  for key in ['explicit_retained_R26_junction','explicit_new_R38_junction']:
   row=audit[key];corridor=row['full_width_actual_copper_corridor'];assert row['passed']and row['direct_incoming_transverse_entry_remains_false']
   assert corridor['width_mm']==.127 and corridor['length_mm']>0 and corridor['area_outside_actual_copper_mm2']==0 and corridor['minimum_boundary_reserve_mm']>0
  assert len(audit['new_endpoint_classification'])==40 and len(audit['negative_controls'])==28 and all(x['rejected']for x in audit['negative_controls'])
  assert audit['changed_CORE_feed']['new_width_mm']==.25 and audit['changed_CORE_feed']['removed_width_mm']==.30
  assert len(audit['support_nets'])==28 and all(x['passed']for x in audit['support_nets'].values())
  for key in ['dedicated_D7_ground_return','R70_ground_return']:
   row=audit[key];assert row['passed'] and len(row['saved_planes'])==2 and all(x['passed']for x in row['saved_planes'])
  assert len(transaction['removed_source_records'])==8 and len(transaction['added_candidate_records'])==21
  assert len(transaction['changed_pad_records'])==6 and len(transaction['changed_footprint_records'])==3 and transaction['all_other_source_objects_exact']==1843
  assert transaction['passed'] and not transaction['engine_success_claimed']and not transaction['numerical_power_VCAP_applicable']
  assert transaction['complete_rewritten_entry_receipt_sha256']==original(c41+'candidate41-entry-return.json')
  io_report=j(c41+'protection-actual-io.json');assert len(io_report['checks'])==22 and sum(x['complete_clamp_first_path_passes']for x in io_report['checks'])==11
  assert h['actual_bonded_io_channels']=={'passed':9,'total':20}
  for row in j(c41+'project-input-preservation.json')['files']:assert sha(tmp/c41/row['path'])==row['sha256']
  # Pure parser definitions are loaded from the unchanged owner source. pcbnew
  # is neither installed nor imported for these identity-only checks.
  src=tmp/'ordinary-routing/tests/mpn-parity/apply_metadata_copy.py';tree=ast.parse(src.read_text());wanted={'Atom','Node','parse','children','child','value','properties','shape'}
  nodes=[n for n in tree.body if (isinstance(n,(ast.ClassDef,ast.FunctionDef))and n.name in wanted)or(isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='TOKEN'for t in n.targets))]
  parser=types.ModuleType('apply_metadata_copy');parser.__dict__.update(re=re,json=json);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'),parser.__dict__);sys.modules['apply_metadata_copy']=parser
  sys.path.insert(0,str(tmp/'integrated-routing'));translation=module('verify_footprint_translations',tmp/'integrated-routing/verify_footprint_translations.py');sys.modules['verify_footprint_translations']=translation
  proof=translation.verify(tmp/c39/'f722-heli.kicad_pcb',tmp/c41/'f722-heli.kicad_pcb',tmp/'integrated-routing/declared-translations39-to41.json')
  assert proof==j('checkpoint41-placement-preview/translation-proof.json')and proof['exact_unchanged_footprints']==153
  for script,output,count,key in [('test_footprint_translations.py','footprint-translation-controls.json',10,'negative_controls'),('test_support_adoption.py','support-adoption-controls.json',7,'controls')]:
   with contextlib.redirect_stdout(io.StringIO()):runpy.run_path(str(tmp/'integrated-routing'/script),run_name='__main__')
   r=read(tmp/'integrated-routing'/output);assert r==j('integrated-routing/'+output);assert len(r[key])==count and all(x['rejected']for x in r[key]);negatives.extend('owner helper: '+x['name']for x in r[key])
  owner=j('checkpoint41-review/owner-coordinated-integration.json');script=tmp/'integrated-routing/check_coordinated_integration.py';owner_out=tmp/'verified-integration.json'
  args=[str(script),str(tmp/c39/'f722-heli.kicad_pcb'),str(tmp/c41/'f722-heli.kicad_pcb'),'--out',str(owner_out)]
  for net in owner['allowed_changed_nets']:args+=['--net',net]
  declaration=['--footprint-translations',str(tmp/'integrated-routing/declared-translations39-to41.json')]
  def run(args):
   old=sys.argv;sys.argv=args
   try:
    with contextlib.redirect_stdout(io.StringIO()):runpy.run_path(str(script),run_name='__main__')
   finally:sys.argv=old
  run(args+declaration);assert read(owner_out)==owner
  reject('candidate41 undeclared translations',lambda:run(args))
  shortened=list(args);pos=shortened.index('DSM_RX_EXT');del shortened[pos-1:pos+1]
  reject('candidate41 missing allowed net',lambda:run(shortened+declaration))
  # Both intermediate transactions are independently checked against parsed PCB
  # records, without trusting the full native-export receipts.
  def pcb(label):
   tree=parser.parse((tmp/'ordinary-routing'/label/'f722-heli.kicad_pcb').read_text())
   return {parser.value(x,'uuid'):parser.shape(x)for kind in ['segment','via','arc']for x in parser.children(tree,kind)}
  boards={label:pcb(label)for label in expected}
  for before,after,receipt,added_key in [('candidate39','candidate40',j(c40+'construction-provenance.json'),'added_records'),('candidate40','candidate41',j(c41+'construction-provenance.json'),'added_records'),('candidate39','candidate41',transaction,'added_candidate_records')]:
   b,n=boards[before],boards[after];rem={x['uuid']for x in receipt['removed_source_records']};add={x['uuid']for x in receipt[added_key]}
   assert set(b)-set(n)==rem and set(n)-set(b)==add and all(n[k]==v for k,v in b.items()if k not in rem)
  b=(a.base_project/'f722-heli.kicad_pcb').read_bytes();d=read(ROOT/'sessions/recovery41/candidate41.f722-heli.kicad_pcb.delta.json')
  for name,source,dd in [('wrong recovery source',b+b'\n',d),('wrong target hash',b,dict(d,target_sha256='0'*64)),('out-of-range copy',b,dict(d,operations=[[0,len(b)+1]])),('invalid operation',b,dict(d,operations=[{}]))]:reject(name,lambda source=source,dd=dd:recovery.reconstruct(source,dd))
  for path in ['../escape','/absolute','safe/../escape','windows\\escape']:reject('unsafe evidence path '+path,lambda path=path:raw.safe(path))
  preview=j('checkpoint41-placement-preview/placement-preview-source.json');visual=j('checkpoint41-placement-preview/visual-review.json');assert preview['routed_board_sha256']==visual['board_sha256']==expected['candidate41']
  assert preview['poses_sha256']==original(c41+'poses-native.json')and preview['source_unchanged']and preview['footprints']==156
  for n,digest in preview['files_sha256'].items():assert original('checkpoint41-placement-preview/'+n)==digest==visual['native_svg_hashes'][n]
  for n,digest in visual['raster_hashes'].items():assert original('checkpoint41-placement-preview/'+n)==digest
  pb=recovery.reconstruct((tmp/c41/'f722-heli.kicad_pcb').read_bytes(),read(ROOT/'sessions/recovery41/placement-preview.pcb.delta.json'))
  assert hashlib.sha256(pb).hexdigest()==preview['placement_only_board_sha256']==original('checkpoint41-placement-preview/preview.kicad_pcb')
  pt=parser.parse(pb.decode());assert not parser.children(pt,'segment') and not parser.children(pt,'via') and len(parser.children(pt,'footprint'))==156
  status=read(ROOT/'status.json');assert status['native_open_connections']==41 and not status['numerical_power_and_VCAP_applicability']and not status['fabrication_ready']
 result={'passed':True,'verifier_source_sha256':sha(__file__),'scope':'Incremental exact paired recovery, selected source and receipt bindings, parsed native copper transactions, unchanged owner translation/integration/support identity helpers, placement-source recovery and binding. Historical finite-width and saved-plane geometry receipts checked for identity and stated results only; raw polygon audits not rerun.','recovered_projects':recovered,'placement_only_board_recovered_exactly':True,'raw_files_verified':len(idx),'negative_controls_passed':len(negatives),'negative_controls':negatives,'original_source_hash_checks_performed':bool(a.historical_workspace),'sealed_handoff_byte_exact':True,'sealed_dependency_digests_preserved':True,'all_sealed_dependency_bytes_included':False,'actual_owner_translation_identity_reexecuted':True,'actual_owner_coordinated_integration_reexecuted':True,'actual_owner_support_adapter_reexecuted':True,'historical_geometric_negative_controls_preserved':28,'full_width_geometric_audit_reexecuted':False,'excluded_raw_files':len(excluded),'native_replay_inputs_complete':False,'real_reference_classifier_reexecuted':False,'native_DRC_reexecuted':False,'native_replay_reexecuted':False,'JVM_router_refill_or_power_solve_executed':False,'placement_render_reexecuted':False,'numerical_power_and_VCAP_applicability':False,'native_open_connections':41,'native_errors':0,'native_warnings':0}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
