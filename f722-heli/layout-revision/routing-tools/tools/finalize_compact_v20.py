#!/usr/bin/env python3
"""Finish V20 helper closure, explanatory documents and inherited delta tooling."""
import hashlib,json,lzma,shutil
from pathlib import Path
W=Path(__file__).resolve().parent.parent;B=W/'ordinary-routing/public-source-ready-v19';S=W/'ordinary-routing/public-source-ready-v20';P=S/'tests/checkpoint52'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
i=read(P/'raw-evidence.json');identity=read(S/'checks/v20-source-identity.json');frozen=identity['frozen_helpers'];bindings={}
def add(name,source=None):
 p=W/(source or name);data=p.read_bytes();row={'sha256':sha(p),'bytes':len(data)}
 if p.suffix=='.kicad_pcb' or p.name=='f722-heli.native.json':
  i['excluded_files'][name]=dict(row,reason='Hash-bound historical constructor preflight dependency only; raw geometry excluded. This historical48 reservation input is not a later flash trial or accepted copper. Native recipe replay requires exact regeneration/restoration.');return
 if name in i['files']:assert i['files'][name]['sha256']==row['sha256'];return
 if len(data)>100000:
  target='blobs/'+row['sha256']+'.xz';dest=P/target;dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():dest.write_bytes(lzma.compress(data,preset=1))
  row.update(compressed_file=target,compressed_sha256=sha(dest))
 else:
  target='files/'+name;dest=P/target;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);row['file']=target
 i['files'][name]=row
 if p.suffix=='.py':frozen[name]={'sha256':row['sha256'],'bytes':row['bytes']}
 if source:i['frozen_alias_sources'][name]=source
for name in ['verify_footprint_transforms.py','verify_footprint_translations.py','verify_intentional_i2c_review.py']:
 add('integrated-routing/'+name)
for name in ['rebuild_placement.py','patch_metadata.py','check_native_parity.py']:
 add('repo/f722-heli/layout-revision/scripts/'+name)
add('repo/f722-heli/layout-revision/source.json')
add('ordinary-routing/tests/port-b48/native-proposal50.json','ordinary-routing/tests/port-b48/candidate03/proposal.json')
screen='ordinary-routing/tests/port-b48/declared-transaction50-screen.json';assert read(W/screen)['proposal_sha256']==sha(W/'ordinary-routing/tests/port-b48/candidate03/proposal.json');add(screen)
for name,digest in read(W/'ordinary-routing/tests/port-b48/candidate03/proposal.json')['input_hashes'].items():
 assert sha(W/name)==digest;add(name);bindings[name]=digest
identity.update(frozen_helpers=frozen,frozen_alias_sources=i['frozen_alias_sources'],selected_files=len(i['files']),excluded_raw_files=len(i['excluded_files']),B03_constructor_input_hashes=bindings)
write(P/'raw-evidence.json',i);write(S/'checks/v20-source-identity.json',identity);write(S/'checks/v20-frozen-helpers.json',frozen)
status={'schema':'f722-source-package-status/v20','status':'unfinished_accepted_geometric_checkpoint','candidate':'candidate52','board_sha256':identity['expected_boards']['candidate52'],'native_open_connections':17,'native_errors':0,'native_warnings':0,'actual_io_cases':[18,22],'actual_io_channels':[16,20],'support_groups':28,'critical_connected_nets':16,'latest_included_candidate':52,'later_isolated15_RPM_flash_PORT_C_trials_included':False,'native_replay_inputs_complete':False,'numerical_power_and_VCAP_applicability':False,'hardware_fabrication_flight_qualification':False,'source43_power_scope':'Historical source43/37 only','source48_power_scope':'Historical mesh-free preparation only','I2C_electrical_status':'NOT_QUALIFIED','SBUS_electrical_status':'NOT_QUALIFIED','TAIL_signal_quality_qualified':False,'critical_BARO_SDA_width_delta_retained_mm2':-2.3792756653762126e-10,'canonical_copy_performed_by_packet_worker':False}
write(S/'status.json',status)
(S/'README.md').write_text('''# F722 routing source packet V20: accepted 17-open geometric work in progress

This compact source/evidence supplement adds accepted candidate50 (27 opens), candidate51 (19 opens) and candidate52 (17 opens), each with stored native zero-error/zero-warning receipts, over immutable V19. It is unfinished routing, not numerical-power, waveform, EMC, transient-protection, manufacturing or flight qualification. Source43 conditional DC results remain historical source43/37-only after these geometry changes.

The package retains exact original 148-, 193- and 162-file worker seals plus the original 62-file B03 seal. Owner extensions and adoption receipts remain separate. Historical pending-owner wording is superseded only by the source-bound owner acceptance. B03 and A04 are required construction lineage, not extra accepted milestones.

Candidate50 replaces 14 tracks with 58 tracks and five vias. Candidate51 is a cumulative 50-to51 transaction with three declared footprint transformations (R33, TP1, U14), 120 added, 26 removed and five changed track/via objects. Its A-on-B03 increment is 54 additions, 12 removals and two B RX track corrections. Candidate52 replaces five SBUS_LV tracks with 41 tracks and five vias, relocating R45. All other full footprints remain exact in each declared transaction.

All 16 critical nets and 28 support groups have bound passing geometric receipts. Actual clamp-first protection is 18/22 cases and 16/20 channels at52, so protection remains incomplete. TAIL has three nonzero outside-own-window width residuals; original ADC gaps and functional limitations remain in inherited evidence. Final all-eight-interface/NRST and new SBUS route projection receipts show no gaps outside their own windows. C74's 0.001 mm annular witness and 0.000491 mm reserve prove connectivity only. They do not establish ampacity or manufacturing margin.

The raw50-to51 critical identity comparison remains false for 147 runtime net-code differences. Explicit v2 proof retains exact critical physical fields/UUIDs after bijective net mapping and zero numeric deltas; changed saved planes are retained. Strict historical v1 behavior and its five refusal controls are preserved. At51-to52 the nonzero BARO_SDA missing-width delta -2.3792756653762126e-10 mm² remains visible, with the separate source-bound own-via-window review. No epsilon, normalization or zeroing was applied.

The first checkpoint19-review failure is an intentionally preserved wrong-incremental-declaration refusal, not a geometry failure. Independent checkpoint19-owner-review uses the cumulative50-to51 declaration and explicit owner integration option. Final19 and17 placement reproduction/previews bind their exact final sources; obsolete earlier19 placement is not used as current proof.

See REPRODUCE.md, SOURCE_EVIDENCE.md, EXCLUDED_INPUTS.md and checks/v20-incremental-verification.json. Packaging uses only hash checks, exact paired-file recovery, syntax-tree copper/footprint/zone comparisons and pure support/adoption adapters. Native geometry, pose operations, DRC, reference classification, finite-entry audits, router/refill and FEM were not rerun. No canonical board, Git index, GitHub or Library change is part of this packet.
''')
(S/'REPRODUCE.md').write_text('''# Recover and verify V20

Use Python 3 with assertions enabled and -B to avoid cache files. V20 extends the exact immutable V19 tree whose FILES.sha256.json digest is 30ef631b771d66f4b46979237b7e9a603bfbe23ca3feda5ac29050411d4ba22a. The V19 delta ZIP digest is 1826d411c57ca1e891c0d8f5c9da0e052ecf92b2a20d191892f170cff0192015. Existing V19 recovery instructions supply the hash-pinned candidate49 paired project.

1. Apply the V20 ZIP using tools/apply_source_delta_v20.py --base V19 --delta routing-source-v20-delta.zip --zip-sha256 PUBLISHED_DIGEST --out NEW_V20. The output must not already exist. The tool verifies the full immutable base, archive paths and hashes, complete final manifest and allowlist before writing.
2. Run python -B NEW_V20/tests/verify_v20_evidence.py --base-project CANDIDATE49 --out verification.json. This performs exact six-project recovery in temporary files, sealed evidence/hash checks, syntax-tree transaction checks and original support/cumulative-adoption adapter controls. It needs no original workspace, KiCad, Shapely, JVM or FEM.
3. To recover one exact 61-file paired project: python -B NEW_V20/sessions/recovery-v20/rebuild_historical_source.py project --base-project CANDIDATE49 --source candidate52 --out NEW_PROJECT. Source choices are candidate49, candidate50, B03, A04, candidate51 and candidate52.
4. To materialize selected evidence and all six exact projects at their original relative paths: python -B NEW_V20/tests/checkpoint52/materialize.py --base-project CANDIDATE49 --out NEW_EVIDENCE. Excluded raw native exports are never silently generated or substituted.

Exact paired-file recovery is fully portable. Re-executing native constructors is a separate procedure requiring the pinned KiCad10.0.6 environment and regenerated/restored native exports matching every recorded hash; this compact package deliberately reports native_replay_inputs_complete=false. Fixed proposals and exact original constructor helpers are included. The construction sequence is candidate49→TAIL candidate50→B03→A04→composedA05/candidate51→SBUS candidate52. Hash-pinned historical reservation inputs required by B03's preflight are identified separately; these are not adopted flash copper. Proposals are consumed as sealed data; historical live route searches are not needed for exact byte recovery and should not be rerun as if they were current routing instructions.

TAIL uses the frozen construct_complete49_v3.py and complete-proposal49-v3.json. B03 uses construct_native50_repaired.py, native-proposal50.json and declared-transaction50-screen.json, followed by its frozen refill/audit helpers. A04 uses construct_ext.py with its recovered proposal/preconstruction screen, then refill_ext.py; compose_shared_return_patch.py uses the recovered A04 board and the exact shared B RX patch to build A05. finalize_composed05.py preserves cumulative provenance. SBUS uses construct_sbus_native19.py with final19-proposal.json/final19-screen.json on exact51, then native refill and its frozen audit/seal helpers. Use an isolated workspace with new constructor output directories; materialized accepted outputs are reference targets, not scratch destinations.

Placement receipts preserve the pinned-original builder and final pose/pad equality. Their orchestrator's historical ../hardware source assumption is not a general license to use a later promoted board: obtain the pinned original hardware from its source.json Git identity before an independent placement reproduction.

After owner review, copy the sealed V20 staging tree into canonical routing-tools and verify every byte against its manifest and allowlist, preserving the frozen41 Git index and HEAD. The packet worker has not done this copy. Publication remains paused pending the existing unknown42 approval outcome.
''')
(S/'SOURCE_EVIDENCE.md').write_text('''# V20 source/evidence map

- tests/checkpoint52/raw-evidence.json maps original paths to exact bytes or lossless XZ blobs, exclusions and six recovered paired projects.
- sessions/recovery-v20/paired-files.json binds all61 paired files per project to exact candidate49. Literal/copy PCB deltas reproduce exact saved boards, not newly refilled equivalents.
- checks/v20-source-identity.json binds worker seals, all frozen helpers and constructor preflight dependencies. Aliases use .used.py or worker-receipt-sources snapshots when available, not later live experiments.
- Candidate50 retains TAIL conditional review, exact ST IBIS model/excerpt and its redistribution Readme, firmware evidence and three width residuals.
- Candidate51 retains B03 lineage, A04 correction context, final all-eight-interface/NRST reference, 96 A-stage endpoints and the separate B138 endpoint scope. Earlier raw failures remain intact.
- Candidate52 retains final SBUS review, complete NRST/support retention and the nonzero critical-width delta plus own-window review.
- checkpoint27-review, checkpoint19-owner-review and checkpoint17-owner-review are the independent accepted-source reviews. checkpoint19-review is the earlier declaration-binding refusal.
- Final19 and17 placement reproduction and front/mirrored-back previews are exact source-bound historical receipts, not package-time renderings.
- Earlier V19 and older packet files are retained byte-exact. Their historical claims apply only to their named sources.

No source43/37 numerical result is inherited as current52 power evidence. Current power/VCAP, waveform/transient protection, USB impedance, AC return and hardware qualification remain open.
''')
(S/'EXCLUDED_INPUTS.md').write_text('''# Deliberate exclusions and limits

This is a compact source recovery/evidence package. The raw-evidence index explicitly records omitted large native exports and duplicate native boards, plus local KiCad preferences. Vendor PDF copies are omitted. It does not include a raw model container, mesh/cache copies, JVM artifacts, speculative newer15/RPM/flash/PORT_C trials, credentials or private notes. Historical48 flash reservation input hashes required by B03 remain explicit constructor dependencies only.

Paired61-file project recovery is complete for candidate49/50/B03/A04/51/52. Raw native exports require exact regeneration/restoration before native recipe replay; failure to match any input digest must stop replay. Stored native/refill/DRC/reference/entry/placement results are preserved and hash-bound but were not rerun during packaging. Original failed predicates, numerical deltas, limitations and refusal receipts are not rewritten.

See tests/checkpoint52/raw-evidence.json excluded_files for each excluded original digest and byte count. Retained vendor model license/conditions and original source headers are preserved alongside their selected evidence.
''')
write(S/'EVIDENCE_INDEX.json',{'version':20,'current':status,'selected_evidence':'tests/checkpoint52/raw-evidence.json','source_identity':'checks/v20-source-identity.json','exact_paired_recovery':'sessions/recovery-v20/paired-files.json','portable_verification':'checks/v20-incremental-verification.json','prior_index':'docs/historical-v19/EVIDENCE_INDEX.json'})
old='c92ec914f36f2bb31eb134f55f6c2cdd3d163d6ad89a1d078243207a7f619256';new=identity['base_v19_manifest_sha256']
p=(B/'tools/apply_source_delta_v19.py').read_text().replace('V19','V20').replace('V18','V19').replace(old,new)
(S/'tools/apply_source_delta_v20.py').write_text(p)
p=(B/'tools/build_source_delta_v19.py').read_text().replace(old,new).replace('v19','v20').replace('V18','V19').replace('candidate49/29','candidate52/17').replace("'native_open_connections': 29","'native_open_connections': 17")
start=p.index("        'base_delta_zip_sha256':");end=p.index('\n    }',start)
p=p[:start]+"        'base_delta_zip_sha256': '"+identity['base_v19_zip_sha256']+"',\n        'candidate_board_sha256': '"+identity['expected_boards']['candidate52']+"',\n        'latest_included_candidate': 52, 'actual_io_cases': [18,22], 'actual_io_channels': [16,20],\n        'native_replay_inputs_complete': False, 'heavy_or_native_execution_performed': False,\n        'numerical_power_and_VCAP_applicability': False, 'source43_power_result_scope': 'Historical source43/37 only',\n        'critical_BARO_SDA_width_delta_retained_mm2': -2.3792756653762126e-10,\n"+p[end:]
start=p.index('    with tempfile.TemporaryDirectory');end=p.index("    assert sha(base / 'FILES.sha256.json')",start)
p=p[:start]+'''    # Verify complete delta application in memory; no broad second source-tree copy.
    rebuilt = {name:(base/name).read_bytes() for name in base_files}
    with zipfile.ZipFile(zip_path) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(changed) + 1
        for name, digest in changed.items():
            data=archive.read('changed/'+name)
            assert hashlib.sha256(data).hexdigest()==digest
            rebuilt[name]=data
    for name in deleted: del rebuilt[name]
    assert {name:hashlib.sha256(data).hexdigest() for name,data in rebuilt.items()}==current
''' +p[end:]
(S/'tools/build_source_delta_v20.py').write_text(p)
shutil.copy2(Path(__file__),S/'tools/finalize_compact_v20.py')
print(json.dumps({'selected':len(i['files']),'excluded':len(i['excluded_files']),'helpers':len(frozen)}))
