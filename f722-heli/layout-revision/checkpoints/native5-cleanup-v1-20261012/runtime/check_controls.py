#!/usr/bin/env python3
"""Check retained representation, recipe mutation, and partial-progress controls."""
import argparse, ast, copy, gzip, json, resource, sys
from pathlib import Path
import native_trial as n
import representation_equivalence as rep
import review_partial_rx_progress as rx
import review_cleanup_result as cleanup
ROOT=Path(__file__).resolve().parent.parent

def main():
    resource.setrlimit(resource.RLIMIT_AS,(768*1024*1024,)*2)
    resource.setrlimit(resource.RLIMIT_CPU,(60,61))
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    controls=[]
    report=json.loads(gzip.decompress((ROOT/'evidence/physical-audit-native5-cleanup-v1.json.gz').read_bytes()))
    native=json.loads(gzip.decompress((ROOT/'evidence/candidate.native.json.gz').read_bytes()))
    controls.extend(rx.controls(report,rx.inventory(native)))
    good=cleanup.trim_review(report);assert good['passed']
    controls.append({'name':'exact_four_trim_endpoints_and_pad_anchored_fragments','passed':True})
    bad=copy.deepcopy(report);next(r for r in bad['new_track_endpoint_support'] if r['track_uuid'] in cleanup.TRIMS)['passed']=False
    assert not cleanup.trim_review(bad)['passed'];controls.append({'name':'failed_trim_endpoint_rejected','passed':True})
    bad=copy.deepcopy(report);next(r for group in bad['all_physical_nets'] for r in group['new_record_fragments'] if r['uuid'] in cleanup.TRIMS)['every_fragment_reaches_real_pad']=False
    assert not cleanup.trim_review(bad)['passed'];controls.append({'name':'padless_trim_fragment_rejected','passed':True})
    comparison=n.read(ROOT/'representation/comparison.json')
    for row in comparison['rows']:
        rep.verify_contour(row['expected_polygons'],row['actual_polygons'])
    controls.append({'name':'ten_original_failed_mask_contours_fit_narrow_representation_bound','passed':True})
    row=next(r for r in comparison['rows'] if r['key']=='U15.1')
    bad=copy.deepcopy(row['actual_polygons'])
    for xy in bad[0]['outer']:xy[0]=(rep.nm(xy[0])+24)/1e6
    try:rep.verify_contour(row['expected_polygons'],bad)
    except ValueError:pass
    else:raise AssertionError('24 nm translated contour unexpectedly accepted')
    controls.append({'name':'over_bound_24_nm_contour_rejected','passed':True})
    bad=copy.deepcopy(row['actual_polygons']);bad[0]['holes']=[[[1,1],[2,1],[1,2]]]
    try:rep.verify_contour(row['expected_polygons'],bad)
    except ValueError:pass
    else:raise AssertionError('Changed topology unexpectedly accepted')
    controls.append({'name':'changed_contour_topology_rejected','passed':True})
    recipe=n.read(ROOT/'recipe/compiled-cleanup-recipe-v1.json');actual={r['uuid']:r for r in native['objects']}
    for row in recipe['proposed_add_tracks']+recipe['proposed_add_vias']:n.verify_added(row,actual[row['uuid']])
    controls.append({'name':'all_96_recipe_additions_exact_against_native_export','passed':True})
    for field in ['width','net','uuid']:
        row=copy.deepcopy(recipe['proposed_add_tracks'][0]);target=actual[row['uuid']]
        row[field]=row[field]+.000001 if field=='width' else 'invalid'
        try:n.verify_added(row,target)
        except ValueError:pass
        else:raise AssertionError('Changed added '+field+' unexpectedly accepted')
        controls.append({'name':'changed_added_'+field+'_rejected','passed':True})
    for path in (ROOT/'runtime').glob('*.py'):ast.parse(path.read_text())
    assert 'pcbnew' not in sys.modules and 'shapely' not in sys.modules
    result={'schema':'f722-publication-technical-controls/v1','passed':True,'controls':controls,
            'native_execution_performed':False,'new_physical_audit_performed':False,
            'all_runtime_files_parse':True,'peak_RSS_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
    data=json.dumps(result,sort_keys=True,indent=2)+'\n'
    if args.output:args.output.write_text(data)
    print(data)

if __name__=='__main__':main()
