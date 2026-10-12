#!/usr/bin/env python3
"""Bounded structural, reuse-gate and lossless-input controls; no geometry."""
import ast,copy,gzip,json,resource,sys,tempfile
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(536870912,)*2)
resource.setrlimit(resource.RLIMIT_CPU,(60,)*2)
import check_candidate as c
import structural_scope as scope
import review_result as review

def main():
 checks=[]
 def good(name,fn):c.require(fn() is not False,name);checks.append({'name':name,'passed':True})
 def bad(name,fn):
  try:fn()
  except (ValueError,AssertionError,KeyError):checks.append({'name':name,'passed':True});return
  raise ValueError('Negative control accepted: '+name)
 r=c.read(c.ANCHORS['recipe']['path']);old=c.read(c.ANCHORS['previous_recipe']['path']);d=c.read(c.ANCHORS['delta']['path'])
 good('exact_actual_two_track_recipe',lambda:scope.verify_recipe(r,old,d))
 for label,key in [('unrelated_via','proposed_add_vias'),('unrelated_polygon','proposed_add_copper_polygons')]:
  x=copy.deepcopy(r);x[key][0]['net']='WRONG';bad(label+'_rejected',lambda x=x:scope.verify_recipe(x,old,d))
 x=copy.deepcopy(r);x['proposed_add_tracks'].pop();bad('missing_track_rejected',lambda:scope.verify_recipe(x,old,d))
 fixture={'_holes_ordered_sha':'holes','_full_zones_sha':'fills','_power_networks':{'GND':'full'},'_per_net_full_records':{'GND':'g','OTHER':'o','FLASH_SCK':'old'}}
 after=copy.deepcopy(fixture);after['_per_net_full_records']['FLASH_SCK']='new'
 good('SCK_only_complete_geometry_reuse_allowed',lambda:scope.unchanged_geometry_proof(fixture,after))
 for label,key in [('hole_owner','_holes_ordered_sha'),('saved_fill','_full_zones_sha'),('power_net','_power_networks')]:
  x=copy.deepcopy(after);x[key]='changed';bad(label+'_change_rejected',lambda x=x:scope.unchanged_geometry_proof(fixture,x))
 x=copy.deepcopy(after);x['_per_net_full_records']['OTHER']='changed';bad('non_SCK_full_record_change_rejected',lambda:scope.unchanged_geometry_proof(fixture,x))
 source=c.read(c.ANCHORS['source_audit']['path']);source['unchanged_geometry_equivalence']={'carried_topology_predicates_have_identical_geometry_inputs':True};source['source_actual_IO_checks_reused_with_identical_complete_net_geometry']=True
 prior=c.read(c.ANCHORS['source_contact_disposition']['path']);partial={'partial_RX_progress_gate_passed':True}
 good('exact_source_dispositions_and_reuse_gate',lambda:all(review.gates(source,partial,prior).values()))
 for key in ['carried_topology_predicates_have_identical_geometry_inputs']:
  x=copy.deepcopy(source);x['unchanged_geometry_equivalence'][key]=False;good('missing_geometry_reuse_proof_rejected',lambda:not all(review.gates(x,partial,prior).values()))
 x=copy.deepcopy(source);x['diagnostic_gates']['all_new_track_endpoints_union_or_annulus_supported']=False;good('new_endpoint_failure_rejected',lambda:not all(review.gates(x,partial,prior).values()))
 x=copy.deepcopy(source);x['native4_lost_pad_pair_count']=1;good('physical_pad_pair_loss_rejected',lambda:not all(review.gates(x,partial,prior).values()))
 x=copy.deepcopy(source);x['diagnostic_gates']['all_new_copper_clearances_including_polygon_and_fills']=False;good('new_foreign_clearance_failure_rejected',lambda:not all(review.gates(x,partial,prior).values()))
 reader=c.load_module('bound_trim_compact_reader',c.ANCHORS['compact_reader']['path'])
 with tempfile.TemporaryDirectory() as directory:
  q=Path(directory)/'test.json.gz';payload=b'{"full":[1,2,3],"holes":[]}'
  with gzip.open(q,'wb') as f:f.write(payload)
  plain=reader.plaintext_binding(q);good('lossless_full_encoded_plain_fixture',lambda:plain=={'sha256':__import__('hashlib').sha256(payload).hexdigest(),'bytes':len(payload)})
  receipt={'path':q.name,'encoding':'gzip','compressed':{'sha256':c.sha(q),'bytes':q.stat().st_size},'uncompressed':plain,'decompression_verified':True}
  good('complete_json_reader_roundtrip',lambda:reader.read_native(q,receipt)==json.loads(payload))
  wrong=copy.deepcopy(receipt);wrong['uncompressed']['sha256']='0'*64;bad('wrong_decompressed_hash_rejected',lambda:reader.read_native(q,wrong))
  wrong=copy.deepcopy(receipt);wrong['compressed']['sha256']='0'*64;bad('wrong_encoded_hash_rejected',lambda:reader.read_native(q,wrong))
 for name in ['check_candidate.py','structural_scope.py','physical_audit.py','review_result.py']:
  ast.parse((c.HERE/name).read_text())
 c.require(not any(n.split('.')[0] in ['shapely','numpy','pcbnew'] for n in sys.modules),'Bounded controls imported geometry/native modules')
 result={'schema':'f722-two-track-trim-bounded-controls/v1','all_passed':True,'controls':checks,'candidate_geometry_run':False,'generic_kernel_certification':False,'peak_RSS_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'bindings':{k:v for k,v in c.ANCHORS.items() if k in ['recipe','delta','reuse_plan','route_binding']},'script':c.file_binding(__file__)}
 out=c.HERE/'bounded-controls-v1.json';c.write(out,result);print(json.dumps({'controls_passed':len(checks),'sha256':c.sha(out),'peak_RSS_MiB':result['peak_RSS_MiB']}))
if __name__=='__main__':main()
