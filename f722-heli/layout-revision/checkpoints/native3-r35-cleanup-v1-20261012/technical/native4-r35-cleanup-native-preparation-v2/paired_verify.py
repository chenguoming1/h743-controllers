"""Non-executing source excerpts. See SOURCE-PROVENANCE.json for original identity.
Dependencies belong to the original implementation; use reproduction/replay_native.py
for the standalone verifier and exact sealed-recipe replay.
"""

def warning_ledger(source,candidate):
 old={n.digest(r):r for r in source['violations'] if r['severity']=='warning'};new={n.digest(r):r for r in candidate['violations'] if r['severity']=='warning'}
 return {'source_warning_signatures':old,'remaining_source_warning_signatures':{h:new[h] for h in new.keys()&old.keys()},'resolved_source_warning_signatures':{h:old[h] for h in old.keys()-new.keys()},'new_warning_signatures':{h:new[h] for h in new.keys()-old.keys()},'all_remaining_warnings_exactly_source_bound':not bool(new.keys()-old.keys()),'source_dangling_warnings_may_disappear_when_connected':True,'warning_count_forced_unchanged':False}

def verify(root,c):
 p=n.common.paired;plan=n.guard.check_sources()['paths'];candidate=root/'diagnostic-board';board=candidate/'f722-heli.kicad_pcb';profile=n.read(c['profile']['path']);delta=n.read(c['delta']['path'])
 source=p.verify_hardware(candidate,c['hardware']);p.write(root/'paired-source-proof.json',source)
 artifacts=p.read(root/'compressed-artifacts.json');binding=artifacts['native'];after=compact_json.read(root/binding['path'],binding);before=n.guard.read_source('native')
 p.require(after['board_sha256']==p.sha(board),'Compressed native board binding differs')
 padproof=p.verify_pad_nets(before,after);expected=n.guard.verify_delta(before,after,delta,profile);ledger=p.read(root/'structural-edit-ledger.json')
 for key,value in expected.items():p.require(ledger[key]==value,'Native structural proof differs: '+key)
 p.require(ledger['raw_source']==n.guard.raw_delta(plan['source_board'],board,delta,profile),'Raw source proof differs')
 p.require(ledger['ordinary_refill_reopen_exact'] is True and ledger['all_pad_settings_exact'] is True,'Fresh repeat/settings proof missing')
 p.require(ledger['pad_settings_sha256']==p.digest(p.read(root/'after-pad-settings.json')) and p.read(root/'after-pad-settings.json')==p.read(plan['source_pad_settings']),'Current all558 settings differ')
 p.require(ledger['native_electrical_connectivity_sha256']==p.sha(root/'native-electrical-connectivity.json'),'Native terminal proof differs')
 critical=n.guard.critical_ledger(before,after,profile);p.require(ledger['critical_geometry_ledger']==critical,'Exact allowed critical ledger differs')
 parity=p.verify_netlist_and_pads(p.SOURCE_XML.read_bytes(),(root/'fresh-paired.net').read_bytes(),after)
 erc=p.read(root/'erc-all.json');drc=p.read(root/'drc-all.json');violations=list(erc.get('violations',[]))+[v for s in erc.get('sheets',[]) for v in s.get('violations',[])]
 p.require(('sheets' in erc or 'violations' in erc) and not violations and not drc['schematic_parity'],'Fresh ERC or parity failed')
 counts={key:len(drc[key]) for key in ['violations','unconnected_items','schematic_parity']}
 result={'schema':'f722-native4-next-complete-paired-proof/v1','status':'PAIRED_DIAGNOSTIC_NOT_ACCEPTANCE','accepted_or_adopted':False,'board_sha256':p.sha(board),'candidate_native_sha256':binding['uncompressed']['sha256'],'compressed_native_sha256':binding['compressed']['sha256'],'compressed_exports':artifacts,'source_native_sha256':n.guard.source_binding('native')['sha256'],'source_netlist_sha256':p.SOURCE_XML_SHA,'fresh_netlist_sha256':p.sha(root/'fresh-paired.net'),'ERC_sha256':p.sha(root/'erc-all.json'),'DRC_sha256':p.sha(root/'drc-all.json'),'paired_source_proof_sha256':p.sha(root/'paired-source-proof.json'),'structural_ledger_sha256':p.sha(root/'structural-edit-ledger.json'),'all_60_non_board_hardware_files_byte_identical':True,'all_schematic_AST_and_bytes_unchanged':True,'fresh_ERC_performed':True,'ERC_violation_count':0,'full_DRC_schematic_parity_performed':True,'paired_ERC_and_schematic_parity_clean':True,'raw_DRC_counts':counts,'raw_DRC_violations':drc['violations'],'raw_DRC_error_count':sum(v['severity']=='error' for v in drc['violations']),'warning_ledger':warning_ledger(p.read(plan['source_drc']),drc),'critical_geometry_ledger':critical,'fresh_power_reference_physical_reviews_pending':True,**padproof,**parity}
 p.write(root/'paired-native-proof.json',result);return result

def arguments():
 parser=argparse.ArgumentParser()
 for key in ['contract','lease','output']:parser.add_argument('--'+key,type=Path,required=True)
 for key in ['contract-sha256','lease-sha256']:parser.add_argument('--'+key,required=True)
 parser.add_argument('--variant',default='local_v1');parser.add_argument('--lock-fd',type=int,required=True);return parser.parse_args()
