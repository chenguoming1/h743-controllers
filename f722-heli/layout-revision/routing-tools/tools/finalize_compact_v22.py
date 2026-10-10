#!/usr/bin/env python3
"""Finalize compact V22 documentation and validated V21 delta tooling."""
import argparse,json,shutil
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);a=ap.parse_args();W=a.workspace.resolve();B=W/'ordinary-routing/public-source-ready-v21';S=W/'ordinary-routing/public-source-ready-v22'
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
i=json.loads((S/'checks/v22-source-identity.json').read_text());h=i['expected_boards']['candidate55']
status={'schema':'f722-source-package-status/v22','status':'unfinished_accepted_geometric_checkpoint','candidate':'candidate55','board_sha256':h,'native_open_connections':13,'native_errors':0,'native_warnings':0,'actual_io_cases':[20,22],'support_groups':28,'critical_connected_nets':16,'latest_included_candidate':55,'only_footprint_change_from54':'R44 rotates180 degrees in place','source_unchanged_footprints':155,'all_routed_net_reference_targets':86,'actual_hole_predicate_disagreements':8,'reference_classification':'UNRESOLVED_ACTUAL_HOLE_BOUNDARY_PREDICATES','native_replay_inputs_complete':False,'native_replay_performed':False,'numerical_power_and_VCAP_applicability':False,'source43_power_scope':'Historical only; current55 fresh power unrun','hardware_fabrication_flight_qualification':False,'canonical_copy_performed_by_packet_worker':False}
write(S/'status.json',status)
(S/'README.md').write_text('''# F722 routing source V22: accepted13 geometric work in progress

Accepted candidate55 is SHA256 14dea1df09ea9d800bf66a6d74eb5f0dac33a8705161e9ed1a02f2e11f3b58b8: 13 native opens, zero errors and warnings. It completes GREEN and restores all affected DSM, ADC, static flash pull-up and A RX routes. Remaining gaps are PORT_C5, BOOT2, RED1 and flash5. Source54 and all V21 historical evidence remain intact.

The exact source54 transaction removes75 copper objects and adds104 tracks plus13 tented through-vias. R44 alone rotates180 degrees in place, from90 to-90 degrees at F(25.8,16.0); its16.0k/0.1% value and pad net identities remain. All other155 full footprints remain unchanged. Stored native gates cover208 new finite endpoints,28 support groups, seven changed signal groups,16 critical connectivity groups and all20 previously passing actual I/O cases out of22. R44 has an exclusive local return to its new plane tie.

The original isolated small-candidate01 retains its132-file seal. Candidate55 retains those exact bytes except for an explicit owner serialization adapter in power-audit.json: pad_group_count=len(groups) is added after validating all28 singleton inventories. power-audit-sealed-original.json preserves the original report. Neither the original seal nor the old report has been silently rewritten. The accepted and sealed paired native projects are byte-identical.

The owner reviewed all86 routed-net reference projections. All79 unchanged routed nets retain exact objects; changed nets retain finite width wedges and nonzero raw deltas. Eight exact actual-hole containment predicate disagreements remain UNRESOLVED. Unchanged-own-via-window location evidence and empty geometric residuals do not override the conflicting actual-hole covers predicates. The strict earlier refusal remains in the packet. Two connected ground-plane polygons and117 ties establish geometric connectivity only.

The source-bound conditional signal review records a136.672265mm DSM main receive path and71.87564991794923mm GREEN route. External receiver edges/loading and bind behavior, total PC14 load below30pF, effective ADC filter capacitance/acquisition/noise, and static flash pull-up startup/coupling remain unqualified. All original values and the existing2.2k LED resistors remain. Current-board numerical power/VCAP has not run; source43 power results remain historical only.

Fresh owner placement evidence reproduces156 poses and558 complete native pad records; front and mirrored-back previews are included. Packet-time checks verify exact-byte source recovery, source bindings, complete board syntax-tree changes, the support adapter, pinned firmware blobs, path lengths and simple ADC RC arithmetic. They do not rerun native DRC, finite geometry, reference classification, placement, waveform simulation, routing or FEM. See REPRODUCE.md for exact scope and dependencies.
''')
(S/'REPRODUCE.md').write_text('''# Recover and verify V22

Use Python3 with assertions enabled and -B. Immutable V21 manifest: 0080c59b78db5cf77e87dc644771882d8aaa95be7b77a9ee53acceddfb39b865. Its delta ZIP: 6d2d242e6d82d8ed56d5b7c96e790622fa3aa6d24ab506e659921a06adf47f6b. V21 recovery supplies the exact61-file candidate54 paired project.

1. Apply tools/apply_source_delta_v22.py --base V21 --delta routing-source-v22-delta.zip --zip-sha256 PUBLISHED_DIGEST --out NEW_V22. Output must not exist. The complete base, archive, final manifest and allowlist are checked.
2. Run python -B NEW_V22/tests/verify_v22_evidence.py --base-project CANDIDATE54 --out verification.json. No historical workspace, KiCad, Shapely, JVM or FEM is needed. It recovers three exact61-file projects, verifies all selected source/evidence bytes and original seal bindings, independently checks the complete board syntax-tree transaction, executes the original support/adoption adapters and recalculates two route lengths and simple ADC RC arithmetic. The stored geometry reports are not recomputed.
3. Recover an exact paired native project with python -B NEW_V22/sessions/recovery-v22/rebuild_historical_source.py project --base-project CANDIDATE54 --source candidate55 --out NEW_PROJECT. Choices: candidate54, sealed55 and candidate55. The last two are byte-identical paired projects with separate review status.
4. Materialize current evidence at its original recorded paths with python -B NEW_V22/tests/checkpoint55/materialize.py --base-project CANDIDATE54 --out NEW_EVIDENCE. Every selected file and exact project is verified before writing. The output directory must be new. Omitted raw exports are not materialized.

The frozen constructor is ordinary-routing/tests/joint-flash-group/construct_small_GREEN_native54.py. It reads exact candidate54 and small-GREEN-complete-proposal54.json, then creates small-candidate01 in a fresh isolated root. Original audit, measurement, extra-gate, validation and sealing helpers are frozen at their recorded runtime paths. The target board and original receipts supply exact comparison identities. Native constructor replay requires pinned KiCad10.0.6 and exact source native exports identified by excluded_files; restore or regenerate them and verify every byte hash. Native replay inputs are explicitly incomplete and no replay was performed while packaging.

For independent native review, use the unmodified sealed55 original, not the later candidate55 adapter against its original manifest. Original review_ordinary_checkpoint.py verifies all132 sealed members before review. The owner classifier has historical defaults: pass explicit source54/source55 boards, snapshots, expected hashes and comparison using its --help interface and a fresh output path. The original owner receipt records all20 source dependencies. Never replace unresolved actual-hole predicates with a passing qualification claim. All-net wrappers, native checkers, current contracts, original strict refusal, classifier and reference reports are included; omitted raw geometry must be restored exactly before recomputing them.

Placement replay separately needs the pinned-original hardware from source.json, not a promoted routed board. The original non-native interpreter failure and successful native reproduction logs are retained. Native placement was run by the owner before packaging; the packet verifier only binds those stored results.

V21 content is unchanged except current root documentation/manifests, whose originals are preserved in docs/historical-v21 and checks/v21-original-*. Copying this isolated staging into canonical routing-tools is a separate owner-coordinated action. No Git index/HEAD, board or publication changes are made by the packet tools.
''')
(S/'SOURCE_EVIDENCE.md').write_text('''# V22 evidence map

- tests/checkpoint55/raw-evidence.json binds every selected source path, lossless payload, recovered project file and omitted raw input. Identical evidence is stored once by content identity.
- sessions/recovery-v22/paired-files.json binds candidate54, original sealed55 and owner-accepted55 to the exact V21-recovered61-file candidate54 project.
- checks/v22-source-identity.json binds the132-file original seal,97 helper paths, owner serialization adapter and preserved source54/55 identities.
- checkpoint13-owner-review holds independent integration, all86-net summaries and raw reports, source-bound reference classification with8 unresolved predicates, the strict previous refusal, adoption assessment and canonical refresh source.
- ordinary-routing/tests/small-signal-review54 retains the full current conditional signal review and pinned firmware/model/data dependencies. The earlier GREEN context and older66.98mm proposal are historical source context only; the current71.876mm path is checked from55 board text.
- checkpoint13-placement-reproduction-native and checkpoint13-placement-preview bind156 poses,558 pads and front/back images. Native results are stored owner evidence.
- checks/v22-incremental-verification.json records portable exact recovery, source checks, complete syntax-tree changes, support/adoption adapters, two route lengths, ADC RC arithmetic and refusal controls. It makes no native, reference, power, signal or physical qualification claim.
''')
(S/'EXCLUDED_INPUTS.md').write_text('''# Explicit omissions and limits

Raw native geometry exports, duplicate native boards, local KiCad preferences and vendor PDF copies are omitted with original hashes and lengths retained. Exact61-file paired projects recover from source54. Existing vendor text, pinned source links, model licenses and current review inputs remain available. The all-net reports are losslessly compressed and identical receipts deduplicated. No broad model container, mesh cache, unrelated trial branch or repeated raw native export is added.

Constructor/reference/finite/placement replay requires pinned tools plus exact omitted native exports or pinned-original hardware. A matching board is not sufficient evidence that a regenerated export matches the recorded byte hash. native_replay_inputs_complete and native_replay_performed remain false.

Eight actual-hole boundary predicate disagreements remain unresolved. Exact geometry, reference-window location and native connectivity do not qualify return impedance, current capacity, waveform behavior, EMI/ESD, manufacturing robustness or flight. Current55 power/VCAP is unrun; historical source43 evidence cannot qualify this source.
''')
write(S/'EVIDENCE_INDEX.json',{'version':22,'current':status,'selected_evidence':'tests/checkpoint55/raw-evidence.json','source_identity':'checks/v22-source-identity.json','paired_recovery':'sessions/recovery-v22/paired-files.json','portable_verification':'checks/v22-incremental-verification.json','prior_index':'docs/historical-v21/EVIDENCE_INDEX.json'})
old='96187ae69afc1f7136982eb16a63673cef8f639a4ee67cfadef8a56d61f6f7fe';new=i['base_v21_manifest_sha256']
p=(B/'tools/apply_source_delta_v21.py').read_text().replace('V21','V22').replace('V20','V21').replace(old,new);(S/'tools/apply_source_delta_v22.py').write_text(p)
p=(B/'tools/build_source_delta_v21.py').read_text().replace(old,new).replace('v21','v22').replace('V20','V21').replace('candidate54/14','candidate55/13').replace("'native_open_connections': 14","'native_open_connections': 13")
start=p.index("        'base_delta_zip_sha256':");end=p.index('\n    }',start)
p=p[:start]+"        'base_delta_zip_sha256': "+repr(i['base_v21_zip_sha256'])+",\n        'candidate_board_sha256': "+repr(h)+",\n        'latest_included_candidate': 55, 'actual_io_cases': [20,22],\n        'actual_hole_predicate_disagreements': 8,\n        'native_replay_inputs_complete': False, 'heavy_or_native_execution_performed': False,\n        'numerical_power_and_VCAP_applicability': False, 'source43_power_result_scope': 'Historical source43 only',\n"+p[end:]
(S/'tools/build_source_delta_v22.py').write_text(p)
p=(B/'tests/verify_v21_delta.py').read_text().replace('V21','V22').replace('V20','V21').replace('v21','v22').replace('immutable_v20','immutable_v21').replace('candidate52/V21 recovered52','candidate54/V21 recovered54').replace("portable['raw_files_verified']","portable['selected_evidence_paths_verified']")
(S/'tests/verify_v22_delta.py').write_text(p)
shutil.copy2(Path(__file__),S/'tools/finalize_compact_v22.py')
print(json.dumps({'status':status,'selected_files':i['selected_files']}))
