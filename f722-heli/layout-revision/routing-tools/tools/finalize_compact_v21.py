#!/usr/bin/env python3
"""Write bounded V21 documentation and reuse the validated compact delta tooling."""
import json,shutil
from pathlib import Path
W=Path(__file__).resolve().parent.parent;B=W/'ordinary-routing/public-source-ready-v20';S=W/'ordinary-routing/public-source-ready-v21'
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
i=json.loads((S/'checks/v21-source-identity.json').read_text())
status={'schema':'f722-source-package-status/v21','status':'unfinished_accepted_geometric_checkpoint','candidate':'candidate54','board_sha256':i['expected_boards']['candidate54'],'native_open_connections':14,'native_errors':0,'native_warnings':0,'actual_io_cases':[20,22],'support_groups':28,'critical_connected_nets':16,'latest_included_candidate':54,'historical_SERVO15_RPM14_separately_adopted':False,'newer_flash_GREEN_BOOT_PORT_C_trials_included':False,'native_replay_inputs_complete':False,'numerical_power_and_VCAP_applicability':False,'hardware_fabrication_flight_qualification':False,'source43_power_scope':'Historical source43/37 only','I2C_electrical_status':'NOT_QUALIFIED','RPM_electrical_status':'NOT_QUALIFIED','SERVO1_signal_quality_qualified':False,'ILM_ADC_noise_qualified':False,'cumulative_USB_N_width_delta_retained_mm2':2.6376462125554667e-10,'RPM_width_residue_retained_mm2':2.725130554532544e-05,'canonical_copy_performed_by_packet_worker':False}
write(S/'status.json',status)
(S/'README.md').write_text('''# F722 routing source packet V21: accepted14 geometric work in progress

V21 adds accepted candidate54, SHA24121b0e46d9a71207cd21e7cf599412c00796d48eb9af5f63ffcf92e5f2ca42:14 opens, zero native geometric errors/warnings,20/22 actual clamp-first protection cases,28 support groups and16 critical nets. Routing and electrical/hardware qualification remain unfinished. Current power/VCAP requires new source-bound analysis; conditional source43/37 results remain historical only.

The recovery sequence is accepted52→historicalSERVO15→historicalRPM14→accepted54. SERVO15 (also locally copied as candidate53) and RPM14 were held construction lineage, not independently adopted checkpoints. Their original166- and148-file seals remain intact. Accepted54 preserves its original146-file seal and separate owner additions/adoption.

SERVO15 reconstructs SERVO1 and supporting paths with R50 shifted0.25 mm inward. RPM14 adds19 tracks and five vias while retaining every source object. The final54 ground change removes nine GND tracks and adds seven GND tracks and one via; every footprint, non-GND object and all24 RPM additions remain exact versus RPM14. The cumulative52→54 transaction removes38 and adds97 track/via objects, with only the declared R50 footprint translation and its two pad positions changed.

U12 has a dedicated local discharge conductor to its original plane via. R51 uses its separate new plane via. R52 instead runs1.150391 mm at0.20 mm width to C30.2, then shares C30's existing1.249987 mm/0.25 mm return to its via. Both original Y1 returns and the existing analog/crystal signal geometry remain preserved. The discarded candidate05 R52 translation has two real RPM_HV clearance errors; its raw summary and failure receipts are retained and it is not adopted.

R52/C30 local shared copper is approximately8.069747 mΩ under explicit15 µm copper,105°C and95%IACS assumptions. The3.227899 µV figure assumes total eFuse current2 A and IMON400 µA; external ABC load2 A alone is not total eFuse current. The5.5 A/IMON1.1 mA illustration is a datasheet sensitivity case, not a supported board rating. Via/plane impedance, ADC charge/sampling/noise, inductive/transient/ESD coupling and actual U5.8 ground potential remain unqualified. C30 is not directly on ILM. TI's quiet-return and<50 pF ILM parasitic guidance remains explicit. The bounded fixed-signal quiet-return search documents a local blocker, not global infeasibility.

All1,259 saved signal-track projections are unchanged for the directRPM14→54 ground change, with117 accepted plane ties. Cumulative52→54 retains the nonzero USB_N missing-width delta2.6376462125554667e-10 mm²; its exact changed region2.6376491257347183e-10 mm² is reviewed inside the unchanged own-via window. RPM's real outside-window width residue2.725130554532544e-5 mm² remains false/unresolved as a full-width predicate. No tolerance, contour repair, zeroing or inherited power qualification is introduced.

Final14 placement reproduction and front/mirrored-back previews bind exact accepted54. Compact paired-file recovery and portable checks are documented in REPRODUCE.md. Native pose/geometry/DRC/reference/finite/placement/router/JVM/FEM results are stored evidence, not package-time reruns. V20 is preserved byte-for-byte; no canonical, Git-index, remote or Library write is part of packet preparation.
''')
(S/'REPRODUCE.md').write_text('''# Recover and verify V21

Use Python3 with assertions enabled and -B. The immutableV20 full-tree manifest is96187ae69afc1f7136982eb16a63673cef8f639a4ee67cfadef8a56d61f6f7fe; its delta ZIP is7c5fda16f2f1dc4cddd15212879e5a0205f4d9e0e036844261c17272e88da88f. V20's recovery supplies the required exact61-file candidate52 paired project.

1. Apply tools/apply_source_delta_v21.py --base V20 --delta routing-source-v21-delta.zip --zip-sha256 PUBLISHED_DIGEST --out NEW_V21. Output must not exist; full base/archive/final-manifest/allowlist verification precedes output.
2. Run python -B NEW_V21/tests/verify_v21_evidence.py --base-project CANDIDATE52 --out verification.json. This needs no historical workspace, KiCad, Shapely, JVM or FEM. It recovers four complete paired projects, checks original seals and syntax-tree transactions, invokes original support/adoption adapters and independently recalculates only the conditional shared-track arithmetic.
3. Recover one exact61-file project with python -B NEW_V21/sessions/recovery-v21/rebuild_historical_source.py project --base-project CANDIDATE52 --source candidate54 --out NEW_PROJECT. Choices: candidate52, SERVO15, RPM14, candidate54. The two named historical sources are construction lineage, not separately accepted boards.
4. Materialize evidence and all four paired sources at their recorded paths with python -B NEW_V21/tests/checkpoint54/materialize.py --base-project CANDIDATE52 --out NEW_EVIDENCE. Accepted54 is canonical candidate54; its originalworker alias is tests/servo48/candidate06. SERVO15 materializes at tests/servo48/candidate04 and is byte-identical to historical candidate53. Use a new output directory.

Exact paired-source recovery is portable and complete. Constructor replay separately requires pinned KiCad10.0.6 and exact restored/regenerated native exports listed under excluded_files; native_replay_inputs_complete remains false. Fixed proposals and frozen original helper sources are provided. Do not substitute current live experiments or refill outputs for hash-pinned input bytes.

SERVO15 uses construct_servo1_complete17.py with servo1-complete17-proposal.json on exact52. RPM14 uses construct_native.py with complete-layer-proposal.json/preconstruction-screen.json on exactSERVO15, followed by its original refill_native.py/seal_native.py helpers. Accepted54 uses construct_separated_returns14.py and dedicated-u12-ground15/separated-returns14-proposal.json on exactRPM14. Each constructor requires a fresh isolated output directory; recovered accepted/historical outputs serve as comparison targets. Native export/refill/receipt replay was not performed during packaging.

Placement reproduction retains the pinned-original source identity, builder and pose recipe. Before native placement replay, obtain the pinned original hardware identified by source.json rather than using a later promoted hardware directory. Final14 receipts reproduce156 poses/558 full native pad records; they do not reconstruct or qualify routing electrically.

After owner review, independently copy public-source-ready-v21 to canonical routing-tools and verify every manifest/allowlist member. Keep Git HEAD and frozen41 index untouched. Inherited staging files may share immutable inodes; unlink/copy before changing any path. Publication stays paused while the existing unknown42 approval remains unresolved.
''')
(S/'SOURCE_EVIDENCE.md').write_text('''# V21 evidence map

- tests/checkpoint54/raw-evidence.json: original path/digest/byte count, lossless blobs, explicit exclusions and recovered paired sources.
- sessions/recovery-v21/paired-files.json: four exact61-file native projects using candidate52 as hash-pinned base.
- checks/v21-source-identity.json: original166/148/146-file seals, frozen helpers, aliases and immutability baseline.
- HistoricalSERVO15: original construction, finite support, signal/return conditional evidence, ST IBIS model with license/Readme and original firmware headers.
- HistoricalRPM14: additive source proof,38 finite endpoints, original loading/return reviews and real width wedge. No separate acceptance is claimed.
- Accepted54: source-bound local-ground reconstruction,14 finite new endpoints,21 completed signal groups,28 support groups,117 plane ties and unchanged1,259 signal projections versusRPM14. Cumulative52 integration is separately explicit.
- Failed candidate05: raw native two-error clearance summary and rejected R52 move; no adoption.
- checkpoint14-ground-owner-review: final independent cumulative review and conditional acceptance. Earlier15/RPM14 reviews retain their historical held scope.
- checkpoint14-ground-placement-reproduction and placement-preview: final source54 identity, full pose/pad equality and front/back images.

Stored finite/refill/reference/native findings are not new executions. Portable checks verify provenance, exact recovery, syntax-tree changes, support/adoption adapters and explicitly assumed track arithmetic only. Local quiet-return/ADC/ILM/ESD limitations, source43 power staleness and all nonzero reference residuals remain visible.
''')
(S/'EXCLUDED_INPUTS.md').write_text('''# Explicit omissions and limits

Raw native exports, duplicate native boards, local KiCad preferences and vendor PDF copies are excluded with exact original hashes/byte sizes. Existing TI text and original source links remain available for the conditional R52/C30 review. No broad model containers, mesh caches, new flash/GREEN/BOOT/PORT_C trials, credentials, private notes or diagnostic-tree duplicates are included.

All61 paired project files recover exactly for52,SERVO15,RPM14,54. Native constructor/check replay needs exact excluded exports restored or regenerated under the pinned environment; every dependency hash must match. Ordinary byte recovery and portable checks do not need those omitted exports.

The shared-track calculation excludes vias, plane/device-ground potential, production tolerances, ADC charge/sampling/noise currents and transient coupling. The5.5 A illustration does not qualify this board's continuous load or chosen750-ohm current-limit setting. Stored clearance/refill/reference and physical-continuity passes are not ampacity, quiet-return, waveform, ESD, manufacturing or flight qualification.
''')
write(S/'EVIDENCE_INDEX.json',{'version':21,'current':status,'selected_evidence':'tests/checkpoint54/raw-evidence.json','source_identity':'checks/v21-source-identity.json','paired_recovery':'sessions/recovery-v21/paired-files.json','portable_verification':'checks/v21-incremental-verification.json','prior_index':'docs/historical-v20/EVIDENCE_INDEX.json'})
old='30ef631b771d66f4b46979237b7e9a603bfbe23ca3feda5ac29050411d4ba22a';new=i['base_v20_manifest_sha256']
p=(B/'tools/apply_source_delta_v20.py').read_text().replace('V20','V21').replace('V19','V20').replace(old,new);(S/'tools/apply_source_delta_v21.py').write_text(p)
p=(B/'tools/build_source_delta_v20.py').read_text().replace(old,new).replace('v20','v21').replace('V19','V20').replace('candidate52/17','candidate54/14').replace("'native_open_connections': 17","'native_open_connections': 14")
start=p.index("        'base_delta_zip_sha256':");end=p.index('\n    }',start)
p=p[:start]+"        'base_delta_zip_sha256': '"+i['base_v20_zip_sha256']+"',\n        'candidate_board_sha256': '"+i['expected_boards']['candidate54']+"',\n        'latest_included_candidate': 54, 'actual_io_cases': [20,22],\n        'historical_SERVO15_RPM14_separately_adopted': False,\n        'native_replay_inputs_complete': False, 'heavy_or_native_execution_performed': False,\n        'numerical_power_and_VCAP_applicability': False, 'source43_power_result_scope': 'Historical source43/37 only',\n        'cumulative_USB_N_width_delta_retained_mm2': 2.6376462125554667e-10,\n        'RPM_width_residue_retained_mm2': 2.725130554532544e-05,\n"+p[end:]
(S/'tools/build_source_delta_v21.py').write_text(p)
p=(B/'tests/verify_v20_delta.py').read_text().replace('V20','V21').replace('V19','V20').replace('v20','v21').replace('immutable_v19','immutable_v20').replace('candidate49/V20 recovered49','candidate52/V20 recovered52');(S/'tests/verify_v21_delta.py').write_text(p)
shutil.copy2(W/'ordinary-routing/verify_v21_evidence.py',S/'tests/verify_v21_evidence.py');shutil.copy2(Path(__file__),S/'tools/finalize_compact_v21.py')
print(json.dumps({'status_written':status,'source_files':i['selected_files'],'frozen_helpers':len(i['frozen_helpers'])}))
