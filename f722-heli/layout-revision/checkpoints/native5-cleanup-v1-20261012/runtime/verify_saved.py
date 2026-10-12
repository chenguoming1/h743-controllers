#!/usr/bin/env python3
"""Replay saved exact geometry, identities and reports without native execution."""
import argparse, copy, gzip, hashlib, json, resource, sys
from pathlib import Path
import native_trial as n
import paired_source as paired

ROOT=Path(__file__).resolve().parent.parent
BOARD_SHA='01b115302e079c6c7a2b1370ef4a089c19c7c2b54fd13e73cf2341db2dffc133'
NATIVE_SHA='46d0b78c82003a3042e68ea2258fa40e5032499b3c3dc864594519c9178821ea'

def read_gzip(path):
    with gzip.open(ROOT/path,'rt') as stream:return json.load(stream)

def main():
    resource.setrlimit(resource.RLIMIT_AS,(1536*1024*1024,)*2)
    resource.setrlimit(resource.RLIMIT_CPU,(60,61))
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);p.add_argument('--repository-root',type=Path);args=p.parse_args()
    references=paired.read(ROOT/'INPUT-REFERENCES.json')
    board_ref=references['source_board']
    roots=[args.repository_root] if args.repository_root else [ROOT,*ROOT.parents]
    source_board=next((root/board_ref['repository_path'] for root in roots if root is not None and (root/board_ref['repository_path']).is_file()),None)
    n.require(source_board is not None,'Run from the checkpoint checkout or pass --repository-root')
    n.require(paired.sha(source_board)==board_ref['sha256'],'Referenced source board changed')
    paired.SOURCE=source_board.parent
    provenance=paired.read(ROOT/'SOURCE-PROVENANCE.json')
    exact_count=0
    for row in provenance['files']:
        file=ROOT/row['path']
        n.require(paired.sha(file)==row['publication']['sha256'],'Publication content changed: '+row['path'])
        if row['transformation']=='exact original bytes':
            raw=gzip.decompress(file.read_bytes()) if file.suffix=='.gz' else file.read_bytes()
            n.require(hashlib.sha256(raw).hexdigest()==row['original']['sha256'],'Exact reconstruction failed')
            exact_count+=1
    before=read_gzip('inputs/source.native.json.gz')
    after=read_gzip('evidence/candidate.native.json.gz')
    board=ROOT/'hardware/f722-heli.kicad_pcb'
    n.require(paired.sha(board)==BOARD_SHA,'Candidate board changed')
    n.require(hashlib.sha256(gzip.decompress((ROOT/'evidence/candidate.native.json.gz').read_bytes())).hexdigest()==NATIVE_SHA,'Candidate export changed')
    recipe=paired.read(ROOT/'recipe/compiled-cleanup-recipe-v1.json')
    poses={ref:row['proposed_pose'] for ref,row in recipe['pose_recipe'].items()}
    ledger=read_gzip('evidence/structural-edit-ledger.json.gz')
    rawproof=copy.deepcopy(ledger['raw_source'])
    rawproof['inverse_pose_check_copy']=str(ROOT/'inverse-pose-check-1.kicad_pcb')
    context=n.make_representation_context(before,after,rawproof,ledger['before_pad_settings'],ledger['after_pad_settings'],board)
    proof=n.verify_delta(before,after,poses,recipe,representation_context=context)
    pair=paired.verify_netlist_and_pads((ROOT/'inputs/source-paired.net').read_bytes(),(ROOT/'evidence/fresh-paired.net').read_bytes(),after)
    drc=paired.read(ROOT/'evidence/drc-all.json');erc=paired.read(ROOT/'evidence/erc-all.json')
    n.require(len(drc['unconnected_items'])==5 and len(drc['violations'])==3 and not drc['schematic_parity'],'Unexpected native DRC counts')
    n.require(all(x['severity']=='warning' for x in drc['violations']),'Geometric native DRC error')
    n.require(not any(s['violations'] for s in erc['sheets']),'ERC violations')
    audit=read_gzip('evidence/physical-audit-native5-cleanup-v1.json.gz')
    review=paired.read(ROOT/'evidence/cleanup-reviewed-disposition-v1.json')
    n.require(audit['candidate_sha256']==NATIVE_SHA and not audit['all_required_topology_and_support_checks_passed'],'Raw audit binding or false aggregate changed')
    n.require(review['all_permitted_cleanup_progress_requirements_passed'] and review['full_RX_status']=='INCOMPLETE_BEFORE_CUT' and not review['full_RX_protection_passed'],'Partial RX disposition changed')
    n.require(review['actual_IO_full_cut_passes']==21 and review['all_actual_IO_contracts']==22,'Full protection count changed')
    assert 'pcbnew' not in sys.modules and 'shapely' not in sys.modules
    result={'schema':'f722-publication-saved-replay/v1','passed':True,'native_execution_performed':False,
            'new_routing_or_physical_audit_performed':False,'candidate_board_sha256':BOARD_SHA,'candidate_native_sha256':NATIVE_SHA,
            'exact_original_artifacts_reconstructed':exact_count,'exact_added_records':proof['track_via_additions'],
            'exact_removed_records':proof['track_via_removals'],'fixed_records_verified':proof['fixed_objects_identical_after_bijective_net_code_normalization'],
            'all_558_pad_nets_unchanged':proof['all_558_pad_net_assignments_unchanged'],
            'full_netlist_pad_parity':pair,'all_U15_analytic_primitives_and_pad_settings_exact':True,
            'U15_representation_contours':sum(len(x['contours']) for x in proof['U15_representation_equivalence']['pad_checks']),
            'native_unconnected':5,'geometric_DRC_errors':0,'historical_warnings':3,'ERC_violations':0,
            'raw_physical_aggregate_preserved':False,'full_actual_IO_passes':21,'full_actual_IO_cases':22,
            'full_RX_status':'INCOMPLETE_BEFORE_CUT','current_DC_or_ESD_qualification_established':False,
            'publication_wrapper_native_reexecution_tested':False,
            'byte_identical_native_regeneration_claimed':False,
            'limit':'Saved native data and exact recipe geometry are verified. Refill or export serialization on another KiCad build is not promised byte-identical.',
            'peak_RSS_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
    out=json.dumps(result,sort_keys=True,indent=2)+'\n'
    if args.output:args.output.write_text(out)
    print(out)

if __name__=='__main__':main()
