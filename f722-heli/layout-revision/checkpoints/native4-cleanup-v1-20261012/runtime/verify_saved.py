#!/usr/bin/env python3
"""Replay exact saved native4 geometry and report bindings without native work."""
import argparse,copy,gc,gzip,hashlib,json,lzma,resource,sys
from pathlib import Path
import native_trial as n
import paired_source as paired
import transaction_guard,island_guard,review_disposition
ROOT=Path(__file__).resolve().parent.parent
BOARD_SHA='293631bc83f880a11bf5d5da2cd2d21cc3e1ecb12e8e95731ef2547a10bcc862'
NATIVE_SHA='c98fd2e2f8c66b43c38897fecfc1263f855df0bcf8598f31b3a74a10a142f762'

def original_bytes(path):
    path=Path(path)
    if path.suffix=='.xz':return lzma.decompress(path.read_bytes())
    if path.suffix=='.gz':return gzip.decompress(path.read_bytes())
    return path.read_bytes()

def main():
    resource.setrlimit(resource.RLIMIT_AS,(1536*1024*1024,)*2)
    resource.setrlimit(resource.RLIMIT_CPU,(90,91))
    parser=argparse.ArgumentParser();parser.add_argument('--repository-root',type=Path);parser.add_argument('--output',type=Path);args=parser.parse_args()
    ref=paired.read(ROOT/'INPUT-REFERENCES.json')['source_board']
    roots=[args.repository_root] if args.repository_root else [ROOT,*ROOT.parents]
    source_board=next((r/ref['repository_path'] for r in roots if r and (r/ref['repository_path']).is_file()),None)
    n.require(source_board is not None and paired.sha(source_board)==ref['sha256'],'Exact unchanged source board required')
    paired.SOURCE=source_board.parent
    provenance=paired.read(ROOT/'SOURCE-PROVENANCE.json');exact=0
    for row in provenance['files']:
        path=ROOT/row['path'];n.require(paired.sha(path)==row['publication']['sha256'],'Publication bytes changed: '+row['path'])
        if row['transformation'].startswith('exact original bytes'):
            n.require(hashlib.sha256(original_bytes(path)).hexdigest()==row['original']['sha256'],'Lossless source reconstruction failed')
            exact+=1
    n.require(paired.sha(ROOT/'hardware/f722-heli.kicad_pcb')==BOARD_SHA,'Candidate board changed')
    n.require(hashlib.sha256(original_bytes(ROOT/'evidence/candidate.native.json.xz')).hexdigest()==NATIVE_SHA,'Candidate native changed')
    before=paired.read(ROOT/'inputs/source.native.json.gz');after=paired.read(ROOT/'evidence/candidate.native.json.xz')
    recipe=paired.read(ROOT/'recipe/compiled-additive-recipe-v1.json');poses={k:v['proposed_pose'] for k,v in recipe['pose_recipe'].items()}
    ledger=paired.read(ROOT/'evidence/structural-edit-ledger.json.gz');rawproof=copy.deepcopy(ledger['raw_source'])
    rawproof['inverse_pose_check_copy']=str(ROOT/'inverse-pose-check-1.kicad_pcb.xz')
    context=n.make_representation_context(before,after,rawproof,ledger['before_pad_settings'],ledger['after_pad_settings'],ROOT/'hardware/f722-heli.kicad_pcb')
    proof=n.verify_delta(before,after,poses,recipe,representation_context=context)
    n.require(proof['track_via_removals']==69 and proof['track_via_additions']==135,'Cumulative recipe count changed')
    pair=paired.verify_netlist_and_pads((ROOT/'inputs/source-paired.net').read_bytes(),(ROOT/'evidence/fresh-paired.net').read_bytes(),after)
    del before;gc.collect()
    delta=transaction_guard.verify_native5_delta(after,n.verify_added)
    polygon=transaction_guard.verify_raw_polygon(ROOT/'hardware/f722-heli.kicad_pcb')
    policy=island_guard.verify_saved_policy(ROOT/'hardware/f722-heli.kicad_pcb')
    patch=paired.read(ROOT/'inputs/precleanup-native-reconstruction.json')
    raw4=dict(after);raw4['zones']=copy.deepcopy(after['zones'])
    for operation in patch['operations']:
        node=raw4
        for key in operation['path'][:-1]:node=node[key]
        key=operation['path'][-1]
        n.require(paired.digest(node[key])==operation['cleanup_value_sha256'],'Cleanup reconstruction input changed')
        if operation.get('operation')=='append':node[key].extend(operation['precleanup_value'])
        else:node[key]=operation['precleanup_value']
    restored=(json.dumps(raw4,sort_keys=True,separators=(',',':'))+'\n').encode()
    n.require(len(restored)==patch['restored_native_bytes'] and hashlib.sha256(restored).hexdigest()==patch['restored_native_sha256'],'Exact raw4 reconstruction failed')
    n.require(len(after['objects'])==2450 and raw4['objects']==after['objects'] and raw4['footprints']==after['footprints'],'Island cleanup changed physical objects')
    plan=island_guard.check_sources();old={z['uuid']:z for z in raw4['zones']};new={z['uuid']:z for z in after['zones']}
    island_checks=[island_guard.verify_fill(old[u],new[u],u,plan) for u in plan['zones']]
    del raw4,restored;gc.collect()
    raw=paired.read(ROOT/'evidence/raw-physical-audit.json.gz');local=paired.read(ROOT/'evidence/local-support-review.json.gz');partial=paired.read(ROOT/'evidence/partial-RX-review.json.gz')
    disposition=paired.read(ROOT/'evidence/contact-disposition.json');gates=review_disposition.evaluate(local,raw,partial)
    n.require(all(gates.values()) and gates==disposition['reviewed_contact_gates'],'Reviewed contact disposition differs')
    n.require(not raw['all_required_topology_and_support_checks_passed'] and raw['diagnostic_gates']==disposition['raw_gates_preserved'],'Raw false findings changed')
    handoff=paired.read(ROOT/'evidence/final-handoff.json');n.require(handoff['actual_IO_full_cut_passes']==21 and handoff['actual_IO_contracts']==22 and handoff['full_RX_status']=='INCOMPLETE_BEFORE_CUT','Full RX status changed')
    drc=paired.read(ROOT/'evidence/drc-all.json');erc=paired.read(ROOT/'evidence/erc-all.json')
    n.require(len(drc['unconnected_items'])==4 and not drc['schematic_parity'] and len(drc['violations'])==3 and all(v['severity']=='warning' and v['type']=='via_dangling' for v in drc['violations']),'Native DRC changed')
    n.require(not any(s['violations'] for s in erc['sheets']),'ERC changed')
    assert 'pcbnew' not in sys.modules and 'shapely' not in sys.modules
    result={'schema':'f722-native4-saved-publication-replay/v1','passed':True,'board_sha256':BOARD_SHA,'native_sha256':NATIVE_SHA,
        'exact_original_artifacts_reconstructed':exact,'exact_source7_cuts':69,'exact_source7_additions':135,
        'exact_native5_cuts':len(delta['exact_five_cuts']),'exact_native5_additions':len(delta['exact_39_added_UUIDs']),
        'all_2411_retained_native5_records_exact':True,'all_2450_precleanup_objects_and_footprints_exact':True,
        'exact_raw4_native_reconstruction_sha256':patch['restored_native_sha256'],'two_exact_island_removals':island_checks,
        'saved_policy':policy,'raw_polygon':polygon,'all_558_pad_net_identities_unchanged':True,'full_netlist_pad_parity':pair,
        'U15_representation_contours':sum(len(r['contours']) for r in proof['U15_representation_equivalence']['pad_checks']),
        'raw_false_physical_aggregate_preserved':False,'reviewed_exact_contact_gates':gates,'full_IO_passes':21,'full_IO_cases':22,'full_RX_status':'INCOMPLETE_BEFORE_CUT',
        'native_unconnected':4,'geometric_errors':0,'historical_via_warnings':3,'ERC_violations':0,'parity_issues':0,
        'current_power_reference_ESD_assembly_qualification':False,'portable_native_wrapper_reexecuted':False,
        'new_native_or_physical_geometry_execution':False,'peak_RSS_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
    text=json.dumps(result,sort_keys=True,indent=2)+'\n'
    if args.output:args.output.write_text(text)
    print(text)

if __name__=='__main__':main()
