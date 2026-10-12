#!/usr/bin/env python3
"""Replay exact saved-contact negative controls; no geometry execution."""
import argparse,ast,copy,json,resource,sys
from pathlib import Path
import paired_source as c
from review_disposition import evaluate
ROOT=Path(__file__).resolve().parent.parent
resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,)*2)
resource.setrlimit(resource.RLIMIT_CPU,(60,61))
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
local=c.read(ROOT/'evidence/local-support-review.json.gz')
raw=c.read(ROOT/'evidence/raw-physical-audit.json.gz')
partial=c.read(ROOT/'evidence/partial-RX-review.json.gz')
controls=[]
c.require(all(evaluate(local,raw,partial).values()),'Saved contact evidence failed')
controls.append({'name':'exact_saved_contact_evidence_positive','passed':True})
def reject(name,edit_local=None,edit_raw=None):
 a,b=copy.deepcopy(local),copy.deepcopy(raw)
 if edit_local:edit_local(a)
 if edit_raw:edit_raw(b)
 c.require(not all(evaluate(a,b,partial).values()),'Negative control accepted: '+name);controls.append({'name':name,'passed':True})
reject('CORE_missing_full_width_entry',lambda a:a['CORE']['continuous_annulus_sections']['best'].update(contiguous_width_mm=.31))
reject('CORE_clip_boundary_section',lambda a:a['CORE']['continuous_annulus_sections']['best'].update(clip_boundary_margin_mm=0))
reject('CORE_unplated_connection',lambda a:a['CORE']['actual_plated_barrel'].update(plated=False))
reject('RED_pairwise_only_support',lambda a:a['RED']['via_plus_new_join_frozen_witness'].update(passed=False))
reject('VX_lost_original_contact',lambda a:a['VX_peers'][0].update(lost_source_contact_mm2=.000001))
reject('VX_lost_barrel_contact',lambda a:next(r for r in a['VX_peers'] if r['peer_uuid'].startswith('bff99')).update(candidate_barrel_contact_boundary_length_mm=0))
reject('VX_branch_union_neck',lambda a:next(r for r in a['VX_peers'] if r['peer_uuid'].startswith('ca49'))['all_VX_support_continuous_sections']['best'].update(contiguous_width_mm=.7))
reject('VX_terminal_is_not_existing_drill',lambda a:a['VX_source_ports'][1].update(inside_actual_drill=False))
reject('unrelated_new_endpoint_failure',edit_raw=lambda a:a['new_track_endpoint_support'].append({'track_uuid':'unreviewed','passed':False}))
reject('unrelated_pad_pair_loss',edit_raw=lambda a:a.update(native5_lost_pad_pair_count=1))
reject('unrelated_raw_clearance_failure',edit_raw=lambda a:a['diagnostic_gates'].update(all_new_copper_clearances_including_polygon_and_fills=False))
shape=c.read(ROOT/'evidence/negative-geometry-controls.json')
c.require(len(shape['controls'])==6 and all(r['passed'] for r in shape['controls']),'Original six actual-native-shape controls failed')
for path in (ROOT/'runtime').glob('*.py'):ast.parse(path.read_text())
assert 'pcbnew' not in sys.modules and 'shapely' not in sys.modules
result={'schema':'f722-native4-publication-controls/v1','passed':True,'saved_contact_controls_replayed':controls,'actual_native_shape_controls_previously_passed':6,'actual_native_shape_controls_reexecuted':False,'new_geometry_or_native_execution':False,'all_runtime_files_parse':True}
text=json.dumps(result,sort_keys=True,indent=2)+'\n'
if args.output:args.output.write_text(text)
print(text)
