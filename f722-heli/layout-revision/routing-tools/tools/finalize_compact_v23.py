#!/usr/bin/env python3
"""Write bounded V23 documentation and derive the validated incremental tooling."""
import argparse,json,shutil
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);a=ap.parse_args();W=a.workspace.resolve();B=W/'ordinary-routing/public-source-ready-v22';S=W/'ordinary-routing/public-source-ready-v23'
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
i=json.loads((S/'checks/v23-source-identity.json').read_text());h=i['expected_boards']['candidate56']
status={'schema':'f722-source-package-status/v23','status':'unfinished_accepted_geometric_checkpoint','candidate':'candidate56','board_sha256':h,'native_open_connections':12,'native_errors':0,'native_warnings':0,'actual_io_cases':[20,22],'support_groups':28,'critical_connected_nets':16,'latest_included_candidate':56,'only_footprint_change_from55':'R4 translates B(27.5,19.8) to B(40.55,19.0);180 degrees retained','source_track_via_arc_objects_retained':1723,'new_tracks':13,'new_vias':2,'all_other_footprints_exact':155,'strict_I2C_trees_passed':True,'FLASH_CS_MCU_connection_complete':False,'retained_track_reference_records':1445,'retained_track_nonempty_width_intersections':8,'historical_source55_actual_hole_predicate_disagreements':8,'native_replay_inputs_complete':False,'native_replay_performed':False,'numerical_power_and_VCAP_applicability':False,'source43_power_scope':'Historical only; current56 fresh power unrun','hardware_fabrication_flight_qualification':False,'canonical_copy_performed_by_packet_worker':False}
write(S/'status.json',status)
(S/'README.md').write_text('''# F722 routing source V23: accepted12 geometric work in progress

Accepted candidate56 PCB SHA256 is 9d9f2f39c2b200f2c928dd3123f098797eb86ba56cb943d7f6e3fe89bf264a7e. Stored native gates report12 opens, zero errors and warnings. R4's U3.1 pull-up branch closes; actual MCU U1.33 FLASH_CS remains disconnected. Remaining gaps: PORT_C5, BOOT2, RED1, flash4. Routing and electrical qualification remain unfinished.

R4 alone moves from B(27.5,19.8),180 degrees to B(40.55,19.0),180 degrees, retaining its10k/1% value and actual pad nets. All other155 full footprints and all1723 original track/via/arc objects remain exact. Thirteen tracks and two ordinary tented through-vias are added. The CS branch is13.999707308mm; the new4.335mm CORE spur deliberately contacts C15.1. A separate1.835755975mm full-width bridge to actual C3.1 replaces the old R4 pad's CORE junction. Its current cannot be bounded by the pull-up bias current.

The original tests/native13-access/candidate02 retains its133-file seal. Candidate56's explicit support adapter adds only pad_group_count=len(groups) for28 verified singleton partitions. power-audit-sealed-original.json and support-report-adapter.json preserve the original bytes and both hashes. The original and accepted paired native projects are byte-identical. Stored checks preserve26 finite new endpoints,16 critical groups,20/22 actual I/O cases, strict I2C trees and117 accepted ground ties. Placement reproduction binds156 poses and558 full pad records; front and mirrored-back previews are included.

Critical projection metrics are unchanged from55. The independent global review covers1445 retained track-reference records and preserves eight nonempty numerical width-edge intersections, including an RPM centerline delta of1.9678329196301878e-7mm. New CORE projections are complete; the nine CS tracks have no centerline gap outside their own via windows, but one retains a1.6570642014549053e-5mm² width wedge. Prior55's eight actual-hole predicate ambiguities remain historical unresolved limitations. No tolerance, snapping, contour repair or zero normalization is introduced.

The conditional electrical review distinguishes active VERY_HIGH GPIO CS edges from the static WP/HOLD straps. Full MCU-to-U3 tree topology, fastest-edge loading/timing, local supply ramp/startup and fresh whole-network power/decoupling remain unqualified. Current numerical power/VCAP has not run. Source43 power evidence remains historical only. This is not manufacturing, flight, AC, thermal or ESD qualification.

V23 preserves all V22 lineage and adds compact, deduplicated current construction/owner evidence. Portable checks reconstruct exact paired project bytes, verify source bindings and the complete board syntax-tree transaction, execute support/adoption adapters and recalculate CS/CORE centerline lengths. They do not rerun native DRC, reference/finite geometry, placement, electrical simulation, routing or FEM.
''')
(S/'REPRODUCE.md').write_text('''# Recover and verify V23

Use Python3 with assertions enabled and -B. Immutable V22 manifest: a5bad034de1e93f23d78b86bfac94ab9ce474d7dfa728940dccfe0f4cf430a4a. V22 delta ZIP: c86634257a5c5a6ffa6a09a3f6679b8a4406832c3bdcdce406880e3b3955defb. Recover the exact61-file candidate55 project through V22 first.

1. Apply tools/apply_source_delta_v23.py --base V22 --delta routing-source-v23-delta.zip --zip-sha256 PUBLISHED_DIGEST --out NEW_V23. Output must not exist. Complete base/archive/final manifest/allowlist checks precede writing.
2. Run python -B NEW_V23/tests/verify_v23_evidence.py --base-project CANDIDATE55 --out verification.json. This uses only Python's standard library and needs no old workspace, KiCad, Shapely, JVM or FEM. Original stored native findings are checked for source bindings, not recalculated.
3. Recover one exact61-file paired project using python -B NEW_V23/sessions/recovery-v23/rebuild_historical_source.py project --base-project CANDIDATE55 --source candidate56 --out NEW_PROJECT. Choices: candidate55, sealed56 and candidate56. The latter two have identical project bytes with distinct original seal/owner acceptance context.
4. Materialize compact evidence and paired projects with python -B NEW_V23/tests/checkpoint56/materialize.py --base-project CANDIDATE55 --out NEW_EVIDENCE. Use a fresh output directory. Omitted raw native exports remain external dependencies.

The exact constructor is ordinary-routing/tests/native13-access/construct_R4_pullup_native55_v2.py with R4-pullup-complete-proposal55-v2.json on candidate55. It creates candidate02 in a fresh isolated root and retains the complete old copper. Frozen audit, extra-gate, measurement, seal and validation helpers are supplied at their original paths; the four bound construction receipts are also restored at the paths used by the original sealer. Compare resulting bytes to the exact recovered sealed56 target. Native replay requires pinned KiCad10.0.6 and exact omitted native exports identified by raw-evidence.json. Restore or regenerate them and verify every hash. No native replay has been performed during packaging.

Run original sealed-manifest validation against sealed56. The later candidate56 adapted support report intentionally differs from the original seal, and its original copy is retained separately. checkpoint12-owner-review/review_serial.py is the owner's sequential review runner; serial-runner-provenance.json explains its derivation. Independent retained-track comparison, changed-net wrappers/targets, checkers and raw compressed reference outputs are included. Prior candidate55 critical snapshot is retained for exact comparison. Geometry replay requires the omitted exports; no current reference or power pass may be inferred from portable provenance checks.

Placement reproduction uses the pinned original project identified by its source.json and the current pose recipe. Its successful native owner receipts are stored evidence. All inherited V22 payloads remain byte-identical. Current root documentation/manifests supersede V22's copies, preserved under docs/historical-v22 and checks/v22-original-*. Canonical copy, Git freezing and publication are separate owner actions.
''')
(S/'SOURCE_EVIDENCE.md').write_text('''# V23 evidence map

- tests/checkpoint56/raw-evidence.json: every selected path, hash and byte count; lossless payloads, explicit omissions and recovered paired projects. Duplicate content is stored once.
- sessions/recovery-v23/paired-files.json: exact candidate55/sealed56/candidate56 projects,61 files each, with a single candidate56 board delta over source55.
- checks/v23-source-identity.json: original133-file seal, frozen helpers, adapter/original hashes and immutability baseline.
- Original construction proposal/provenance plus four bound receipts preserve the exact R4 move, C15 contact, full-width CORE bridge and complete pull-up branch.
- checkpoint12-owner-review: independent source-bound integration, owner assessment including strict I2C trees, all1445 retained-track reference records, changed CORE/CS reference and sequential review provenance.
- ordinary-routing/tests/native13-access/electrical-review02/README.md: exact source-bound conditional active-CS and CORE topology/startup review, with primary-source links and remaining limitations. Existing pinned SPI sources are included; predecessor V22 retains supporting component models and earlier signal evidence.
- checkpoint12-R4-placement-reproduction and checkpoint12-R4-placement-preview:156 poses,558 pads and front/back images bound to accepted56.
- checks/v23-incremental-verification.json: three exact recoveries, all current evidence/source hashes, complete syntax-tree transaction, adapters, two terminal paths, added-net lengths and refusal controls. Native results are not replayed.
''')
(S/'EXCLUDED_INPUTS.md').write_text('''# Explicit omissions and limits

Raw native geometry exports, duplicate placement/preview boards and local KiCad preferences are omitted with their hashes and lengths recorded. All61 paired project files recover exactly from candidate55. V23 adds no model container, mesh cache, unrelated trial or duplicated historical raw native diagnostics. Existing V22 lineage is inherited without changes; new large source receipts and reference outputs are losslessly compressed.

Native construction/reference/finite/placement replay needs pinned tools and exact omitted exports or original hardware. native_replay_inputs_complete and native_replay_performed remain false. Reference residuals, prior55 actual-hole predicate ambiguities and the open actual MCU CS connection remain explicit. Current56 power/VCAP is unrun. No waveform, return-impedance, current-capacity, manufacturing or flight qualification is claimed.
''')
write(S/'EVIDENCE_INDEX.json',{'version':23,'current':status,'selected_evidence':'tests/checkpoint56/raw-evidence.json','source_identity':'checks/v23-source-identity.json','paired_recovery':'sessions/recovery-v23/paired-files.json','portable_verification':'checks/v23-incremental-verification.json','prior_index':'docs/historical-v22/EVIDENCE_INDEX.json'})
old='0080c59b78db5cf77e87dc644771882d8aaa95be7b77a9ee53acceddfb39b865';new=i['base_v22_manifest_sha256']
p=(B/'tools/apply_source_delta_v22.py').read_text().replace('V22','V23').replace('V21','V22').replace(old,new);(S/'tools/apply_source_delta_v23.py').write_text(p)
p=(B/'tools/build_source_delta_v22.py').read_text().replace(old,new).replace('v22','v23').replace('V21','V22').replace('candidate55/13','candidate56/12').replace("'native_open_connections': 13","'native_open_connections': 12")
start=p.index("        'base_delta_zip_sha256':");end=p.index('\n    }',start)
p=p[:start]+"        'base_delta_zip_sha256': "+repr(i['base_v22_zip_sha256'])+",\n        'candidate_board_sha256': "+repr(h)+",\n        'latest_included_candidate': 56, 'actual_io_cases': [20,22],\n        'historical_source55_actual_hole_predicate_disagreements': 8,\n        'native_replay_inputs_complete': False, 'heavy_or_native_execution_performed': False,\n        'numerical_power_and_VCAP_applicability': False, 'source43_power_result_scope': 'Historical source43 only',\n"+p[end:]
(S/'tools/build_source_delta_v23.py').write_text(p)
p=(B/'tests/verify_v22_delta.py').read_text().replace('V22','V23').replace('V21','V22').replace('v22','v23').replace('immutable_v21','immutable_v22').replace('candidate54/V22 recovered54','candidate55/V22 recovered55')
(S/'tests/verify_v23_delta.py').write_text(p)
shutil.copy2(Path(__file__),S/'tools/finalize_compact_v23.py')
print(json.dumps({'status':status,'selected_files':i['selected_files']}))
