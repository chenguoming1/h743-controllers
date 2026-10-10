#!/usr/bin/env python3
"""Finalize compact accepted57 source documentation and validated delta tools."""
import argparse,json,shutil
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);a=ap.parse_args();W=a.workspace.resolve();B=W/'ordinary-routing/public-source-ready-v23';S=W/'ordinary-routing/public-source-ready-v24'
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
i=json.loads((S/'checks/v24-source-identity.json').read_text());h=i['expected_boards']['candidate57']
status={'schema':'f722-source-package-status/v24','status':'unfinished_accepted_geometric_checkpoint','candidate':'candidate57','board_sha256':h,'native_open_connections':11,'native_errors':0,'native_warnings':0,'actual_io_cases':[20,22],'support_groups':28,'critical_connected_nets':16,'latest_included_candidate':57,'only_footprint_change_from56':'R2 moves F(16.0,7.7),0 to F(40.2,6.2),270','source_copper_objects_removed':1,'new_tracks':2,'new_vias':0,'all_other_footprints_exact':155,'BOOT_MCU_connection_complete':False,'retained_GND_fills_and_drill_polygons_exact':True,'source_C31_ground_via_and_B_lead_preserved':True,'historical_source55_actual_hole_predicate_disagreements':8,'historical_source56_CS_width_wedge_retained':True,'native_replay_inputs_complete':False,'native_replay_performed':False,'numerical_power_and_VCAP_applicability':False,'source43_power_scope':'Historical only; current57 fresh power unrun','hardware_fabrication_flight_qualification':False,'canonical_copy_performed_by_packet_worker':False}
write(S/'status.json',status)
(S/'README.md').write_text('''# F722 routing source V24: accepted11 geometric work in progress

Accepted candidate57 PCB SHA256 is454b7bb2454695b49c039f3d97e5edefb1946912363bab00ef5ced6ba2b0ea16. Stored native gates report11 opens, zero geometric errors and warnings. R2's switch branch closes; actual MCU U1.60 BOOT0 remains disconnected. Remaining gaps are PORT_C5, BOOT1, RED1 and flash4. Routing and electrical/physical qualification remain unfinished.

R2 alone moves from F(16.0,7.7),0 degrees to F(40.2,6.2),270 degrees (-90 native representation), retaining its2.2k/1% value and actual pad nets. All other155 full footprints remain exact. One old exclusive R2 ground leaf is removed and two tracks are added, with no new vias. The new BOOT0 link to SW1 is1.2701279463109219mm; the new0.25mm ground leaf is1.0636728820459835mm to an existing ground via. C31's original ground via and rear lead remain exact.

Original tests/boot56/candidate01 retains its129-file seal. Candidate57 began as a hardlinked copy; only power-audit.json was detached before adding explicit pad_group_count fields. power-audit-sealed-original.json and support-report-adapter.json preserve the original report and both source/output hashes. No original sealed report was overwritten. Original and accepted paired projects remain byte-identical. Stored checks retain four finite new endpoints,28 support groups,16 critical groups and20/22 actual I/O cases.

The owner proves exact saved GND fill arrays for both ground planes and all307 physical drill polygons, with2293 retained native objects exact modulo runtime net_code. Existing track projection domains therefore remain unchanged. A separate BOOT0 reference inspection reports zero missing physical centerline and width projection while explicitly retaining the open MCU terminal. Inherited source55 actual-hole boundary ambiguities and source56's CS width wedge remain unresolved limitations. Exact retained reference geometry does not establish AC/noise performance or current capacity.

Placement reproduction binds156 poses and558 complete native pad records; front and mirrored-back previews are retained. Current numerical power/VCAP remains unrun. Source43 power evidence remains historical only. BOOT startup, switching/noise, ESD, manufacturing and flight remain unqualified.

V24 inherits V23 unchanged and adds only current construction/owner/placement evidence. Portable verification recovers exact paired project bytes, checks every selected source hash and original seal, validates the complete board syntax-tree transaction and full saved GND-zone syntax, executes support/adoption adapters and recalculates both new track lengths. It does not rerun native DRC, finite/reference geometry, placement, routing, FEM or electrical simulation.
''')
(S/'REPRODUCE.md').write_text('''# Recover and verify V24

Use Python3 with assertions enabled and -B. Immutable V23 manifest is04b91a8a36a88b50997e03360dbe2de801acbe43f233fad96a0d2d0b0b01c649. Its delta ZIP isb4eaf5eadf28e7de397b6aadeac99014bba02e5eb66cc04e93d77759447919fc. Recover the exact61-file candidate56 project through V23 first.

1. Apply tools/apply_source_delta_v24.py --base V23 --delta routing-source-v24-delta.zip --zip-sha256 PUBLISHED_DIGEST --out NEW_V24. The output must not exist. Complete base/archive/final manifest/allowlist checks precede writing.
2. Run python -B NEW_V24/tests/verify_v24_evidence.py --base-project CANDIDATE56 --out verification.json. This uses Python's standard library only and needs no old workspace, KiCad, Shapely, JVM or FEM. Stored native results are source-bound evidence, not new native executions.
3. Recover one exact61-file project with python -B NEW_V24/sessions/recovery-v24/rebuild_historical_source.py project --base-project CANDIDATE56 --source candidate57 --out NEW_PROJECT. Choices: candidate56, sealed57, candidate57. The latter two have identical native project bytes and distinct seal/owner status.
4. Materialize evidence and paired projects with python -B NEW_V24/tests/checkpoint57/materialize.py --base-project CANDIDATE56 --out NEW_EVIDENCE. Use a new output directory. Omitted native geometry exports remain external inputs.

The exact constructor is ordinary-routing/tests/boot56/construct_R2_standalone56.py with R2-SW1-standalone-proposal56.json on exact candidate56. It writes candidate01 into a fresh isolated root. Frozen audit, extra-gate, validation and sealing helpers are restored at their original runtime paths. Compare resulting native project bytes to recovered sealed57. Native construction replay needs pinned KiCad10.0.6 and exact source native exports identified by raw-evidence.json; regenerate or restore those bytes and verify their hashes before use. No native replay was performed while packaging.

Original manifest validation belongs to sealed57. Candidate57's later support adapter intentionally differs and preserves its original copy. checkpoint11-owner-review/run_owner.sh and the included checkers describe independent coordinated integration, new BOOT reference, placement and preview execution. seal_owner_metadata.py and finish_canonical_evidence.py retain the actual owner adapter/adoption/canonical recipe. These owner scripts are historical construction sources and are not safe to rerun directly over an accepted or sealed directory; replay only in a fresh isolated tree. Before replaying metadata adaptation, restore the original sealed support report.

Placement replay separately uses pinned-original hardware identified by source.json and the current pose recipe. Owner native placement receipts are stored, not rerun here. All V23 payloads remain unchanged except superseded root documentation/manifests, whose originals are retained under docs/historical-v23 and checks/v23-original-*. Canonical copying, Git freezing and publication are separate owner actions.
''')
(S/'SOURCE_EVIDENCE.md').write_text('''# V24 evidence map

- tests/checkpoint57/raw-evidence.json: all selected paths, original hashes/lengths, lossless compressed payloads, recovered projects and omitted raw inputs. Duplicate content is stored once.
- sessions/recovery-v24/paired-files.json: source56, original sealed57 and accepted57,61 exact project files each, with a single57 board delta over56.
- checks/v24-source-identity.json: original129-file seal, frozen helper paths, original/adapted support hashes and initial immutability identity.
- Construction proposal/provenance, source-bound entry/support audit and coordinated transaction preserve the exact R2 move, replaced exclusive ground leaf, retained C31 return and completed switch branch.
- checkpoint11-owner-review: independent integration, exact saved-ground/drill/retained-object binding, current BOOT0 reference, owner assessment and original execution/adapter/refresh recipes.
- checkpoint11-placement-reproduction and checkpoint11-placement-preview:156 poses,558 pads and source-bound front/back images.
- checks/v24-incremental-verification.json: three exact recoveries; all selected source/evidence hashes; complete copper/footprint transaction; two exact complete ground-zone syntax trees; support/adoption adapters; both track lengths and refusal controls. No native or power replay.
''')
(S/'EXCLUDED_INPUTS.md').write_text('''# Explicit omissions and limits

Large raw native geometry exports, duplicate placement/preview boards and local KiCad preferences are omitted with exact original hashes and lengths. All61 paired project files recover from candidate56. No unrelated trials, model containers, mesh caches or new copies of historical raw diagnostics are added. V23 lineage remains intact; current large receipts/reference reports are compressed losslessly.

Native construction, finite/reference and placement replay requires pinned tools and omitted exact exports or original hardware. native_replay_inputs_complete and native_replay_performed remain false. The actual MCU BOOT connection remains open. Retained exact GND geometry does not resolve prior boundary predicates or qualify AC/current capacity. Current57 power/VCAP is unrun; prior source43 evidence is historical only. No startup, waveform, manufacturing or flight qualification is claimed.
''')
write(S/'EVIDENCE_INDEX.json',{'version':24,'current':status,'selected_evidence':'tests/checkpoint57/raw-evidence.json','source_identity':'checks/v24-source-identity.json','paired_recovery':'sessions/recovery-v24/paired-files.json','portable_verification':'checks/v24-incremental-verification.json','prior_index':'docs/historical-v23/EVIDENCE_INDEX.json'})
old='a5bad034de1e93f23d78b86bfac94ab9ce474d7dfa728940dccfe0f4cf430a4a';new=i['base_v23_manifest_sha256']
p=(B/'tools/apply_source_delta_v23.py').read_text().replace('V23','V24').replace('V22','V23').replace(old,new);(S/'tools/apply_source_delta_v24.py').write_text(p)
p=(B/'tools/build_source_delta_v23.py').read_text().replace(old,new).replace('v23','v24').replace('V22','V23').replace('candidate56/12','candidate57/11').replace("'native_open_connections': 12","'native_open_connections': 11")
start=p.index("        'base_delta_zip_sha256':");end=p.index('\n    }',start)
p=p[:start]+"        'base_delta_zip_sha256': "+repr(i['base_v23_zip_sha256'])+",\n        'candidate_board_sha256': "+repr(h)+",\n        'latest_included_candidate': 57, 'actual_io_cases': [20,22],\n        'historical_source55_actual_hole_predicate_disagreements': 8,\n        'native_replay_inputs_complete': False, 'heavy_or_native_execution_performed': False,\n        'numerical_power_and_VCAP_applicability': False, 'source43_power_result_scope': 'Historical source43 only',\n"+p[end:]
(S/'tools/build_source_delta_v24.py').write_text(p)
p=(B/'tests/verify_v23_delta.py').read_text().replace('V23','V24').replace('V22','V23').replace('v23','v24').replace('immutable_v22','immutable_v23').replace('candidate55/V23 recovered55','candidate56/V23 recovered56')
(S/'tests/verify_v24_delta.py').write_text(p)
shutil.copy2(Path(__file__),S/'tools/finalize_compact_v24.py')
print(json.dumps({'status':status,'selected_files':i['selected_files']}))
