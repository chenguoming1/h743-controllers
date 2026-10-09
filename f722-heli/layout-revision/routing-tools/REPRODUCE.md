# Reproduce the ordinary-routing checkpoint

Adopted69 is unfinished: PCB SHA `9cf04c88ebd31d7e2c12bdb8a9f80e01b615a7bdb94a73fc2234208a2e0a14c8`, 69 native opens, zero native DRC errors/warnings, eleven complete ordinary nets. The loaded-power screen identifies an unresolved BEC copper deficit; this is not fabrication-ready. Candidate15’s real broad route stopped at five successes. Candidate16’s two-track ADC_BUS partial connection is explicit native construction. No later routing or power experiments are included. Historical receipts retain their actual source versions.

## Inputs

Use an owner-approved, immutable six-layer support PCB, paired `.kicad_pro` and `.kicad_dru` files, and a fresh empty model directory. Keep the 0.127 mm ordinary rules, 0.45/0.20 mm tented through vias, both-face 0.20 mm drill-to-SMT-mask exclusion, 0.25 mm hole gap, outline, external pinout, and ground-only In1/In4 contract. Resolve physical support conflicts before setting `--support-ready`.

Set `KICAD_PY` to a verified KiCad 10 Python wrapper, `BOARD` to the absolute final support-board path, and `MODEL` to an absolute fresh directory. Python 3 must have `requirements.txt` installed. Java 21 is required. Run all commands from this source directory. An alternative analysis interpreter may be supplied as `ANALYSIS_PY`.

## Fresh export and model

```sh
python3 bootstrap_dependencies.py
./compile.sh
./prepare_fresh.sh "$BOARD" "$MODEL" --support-ready
```

The bootstrap fetches only official, SHA-pinned engine/compiler artifacts. No PCB leaves the local environment. Source PCB hash, native snapshot hash, adapter-source hashes, and DSN hash are recorded in the model and rechecked at load.

## Zero control, with the owner-controlled heavy slot

```sh
./run_local.sh "$MODEL" "$MODEL/zero" 0
"$KICAD_PY" import_session.py --model "$MODEL/model.json" --session "$MODEL/zero.ses" --engine-report "$MODEL/zero.after.json" --out "$MODEL/imported-zero.kicad_pcb"
python3 verify_zero.py --model "$MODEL/model.json" --engine "$MODEL/zero.after.json" --imported "$MODEL/imported-zero.import.json" --out "$MODEL/zero-parity.json"
```

The output name `zero-parity.json` inside the current model directory is mandatory: the nonzero launcher requires its passing status and exact model/board hashes. Historical zero reports cannot satisfy a fresh model. Fixed source copper is preserved by native UUID and exact geometry. Existing protected ordinary copper additionally requires an explicit `--logical-route-map`; immutable ordinary objects can use `--fixed-ids`.

## Route candidate, after the fresh zero gate

The owner chooses `PASSES` as a computational budget and releases the heavy slot. It is not a via or electrical-length limit.

```sh
F722_CONNECTION_BUDGET_MS=10000 F722_CHECKPOINT_AFTER_ROUTED=5 F722_CHECKPOINT_EVERY_ROUTED=3 ./run_local.sh "$MODEL" "$MODEL/route" "$PASSES"
"$KICAD_PY" import_session.py --model "$MODEL/model.json" --session "$MODEL/route.ses" --engine-report "$MODEL/route.after.json" --out "$MODEL/routed-candidate.kicad_pcb"
python3 native-tools/check_protection_paths.py --geometry "$MODEL/routed-candidate.native.json" --contracts config/candidate-contracts.json --out "$MODEL/protection-original18.json"
python3 native-tools/check_protection_paths.py --geometry "$MODEL/routed-candidate.native.json" --contracts config/supplemental-contracts.json --out "$MODEL/protection-supplemental7.json"
```

Each physical checker returns nonzero when any case fails and still writes its full report. Candidate completion additionally requires native DRC, exact schematic connectivity, all-net connectivity, DFM, reference continuity, and timing checks. Preserve the logical route map returned by the native importer for any continuation. Do not publish a route as fabrication-ready based on engine connectivity alone.

## Small adapter controls

```sh
python3 prepare_contact_control.py --model "$MODEL/model.json" --out "$MODEL/contact-fixture"
java -Xmx256m -cp build:vendor/freerouting-2.1.0.jar NativeContactRegression "$MODEL/contact-fixture"
java -Xmx256m -cp build:vendor/freerouting-2.1.0.jar SharedPadSeamControl "$MODEL/contact-fixture"
java -Xmx256m -cp build:vendor/freerouting-2.1.0.jar PhysicalOwnerInsertionControl "$MODEL/contact-fixture" "$MODEL/physical-owner-insertion.json"
python3 route_geometry.py
```

The native-contact control exercises off-centre trace capsule contact, symmetric adjacency, logical isolation, and stale-contact removal. The shared-pad control deliberately reports the conservative rejection of inside-pad branch overlap. It does not claim physical impossibility. Full native geometry is retained in the separate independent source export; 10 nm engine planning geometry uses checked containment.

## Reference-plane and native-import controls

Run these after the fresh zero gate, under the same serialized heavy-process allocation for the engine check. The native-import SES/report pair below is explicitly synthetic and tests the importer; it is not real router output.

```sh
python3 native-tools/test_exact_native_contours.py
python3 prepare_via_control.py --model "$MODEL/model.json" --out "$MODEL/reference-via-fixtures.json"
java -Xmx3g -Djava.awt.headless=true -cp build:vendor/freerouting-2.1.0.jar ReferencePlaneViaRegression "$MODEL" "$MODEL/reference-via-fixtures.json" "$MODEL/reference-via-control.json"
python3 prepare_import_control.py --model "$MODEL/model.json" --via-control "$MODEL/reference-via-control.json" --out-prefix "$MODEL/synthetic-import"
"$KICAD_PY" import_session.py --model "$MODEL/model.json" --session "$MODEL/synthetic-import.ses" --engine-report "$MODEL/synthetic-import.after.json" --out "$MODEL/native-import-control.kicad_pcb"
python3 verify_refill_control.py --source "$MODEL/native.json" --result "$MODEL/native-import-control.native.json" --out "$MODEL/native-import-control-verified.json"
python3 native-tools/check_via_process.py --geometry "$MODEL/native-import-control.native.json" --out "$MODEL/native-import-control-process.json"
```

The native signal-via/stub control must retain FLASH_CS before and after save/reload/refill. An isolated via without a signal anchor can be reassigned by native connectivity to the plane net; that is not a valid signal-antipad fixture. The archived negative process report deliberately uses stale saved ground fill with the intended FLASH_CS net intact and must fail the two reference-layer checks.

## Continuing an actual partial route

After importing real engine output, retain the PCB, its paired project/rules, the native export, import report and `routed-candidate.logical-route-map.json`. A later fresh model must bind that same board and consume its logical ownership artifact:

```sh
./prepare_fresh.sh "$PREVIOUS_PCB" "$NEXT_MODEL" --support-ready --logical-route-map "$PREVIOUS_LOGICAL_MAP"
```

Set these variables to the exact imported PCB and its standalone map. Repeat the zero control for this new model before routing. Preserve any intentionally immutable ordinary UUIDs through `--fixed-ids` as well. Never reuse an empty-map/no-existing-copper assumption from the first support board.

## Full-board serialization and copied contact identity

Compile the separate test programs with the pinned compiler, then run the copy check under the heavy-process allocation. This check is necessary because a zero route run does not exercise BoardHistory serialization. The peer-mutation check is a small synthetic in-memory control.

```sh
java -Xmx256m -jar vendor/ecj-3.41.0.jar -21 -nowarn -cp build:vendor/freerouting-2.1.0.jar -d build tests/FullNativeCopyControl.java tests/app/freerouting/board/NativePeerMutationControl.java
java -Xmx3g -Djava.awt.headless=true -cp build:vendor/freerouting-2.1.0.jar FullNativeCopyControl "$MODEL" "$MODEL/full-copy-control.json"
java -Xmx256m -Djava.awt.headless=true -cp build:vendor/freerouting-2.1.0.jar app.freerouting.board.NativePeerMutationControl "$MODEL/contact-fixture"
```

## Progress, graceful stop and recoverable snapshots

The runner emits a cheap per-attempt net/contact label, status, timings and counters. Full snapshots default to every three successful connections or 60 seconds. A pending-geometry flag distinguishes newer live counters from the last verified session. The latest two geometry slots remain bounded and are replaced atomically; the progress pointer is published after both report and session. A failed attempt with identical geometry reuses the previous files. Create `OUTPUT_PREFIX.stop` to request a cooperative stop; full checked output is retained at that stop and at final completion. A forced termination can recover only the last complete snapshot.

To import a running checkpoint, read the exact `checkpoint`, `report_sha256` and `session_sha256` from the progress JSON, verify both referenced files still match, and use that paired `.after.json` and `.ses` with the exact originating model. Never pair a session with a report from another checkpoint or reconstruct logical ownership from physical net names alone. Use a complete disposable project copy, including all matching schematics and local footprint libraries, with a matching PCB/project basename for native DRC and refill.

`F722_ONLY_NETS=SWCLK` or another comma-separated physical ordinary-net list provides a focused search. It changes the search queue only; all native fixed geometry and physical clearance guards remain installed. The first accepted short route and the corrected adapter's identical session are retained as hash-bound receipts. Successful SWCLK endpoint overlap is nominal geometry, not manufacturing margin.

After native import, `analyze_candidate.py` reports physical/logical connectivity and I2C geometry. `endpoint_witness.py` can record the pad-interior and full-width endpoint intersection of a routed two-terminal net. Full I2C loading/edge, reference continuity and loaded power qualification remain separate completion requirements.

## Compact historical-session replay


The historical `sessions/swclk` and `sessions/accepted80` packets contain the actual SWCLK and accepted80 sessions, import-only ownership contracts, report geometry, exact original model/native/adapter/runtime identities, and explicit postprocessing provenance. These are not complete routing models. Verify `FILES.sha256.json` before use. Supply the exact frozen source board named by the packet identity and its full paired project, schematic and local libraries. Then:

```sh
python3 prepare_session_replay.py --packet sessions/accepted80 --source-board "$SOURCE_BOARD" --out "$REPLAY_INPUTS"
"$KICAD_PY" import_session.py --model "$REPLAY_INPUTS/model.json" --session sessions/accepted80/session.ses --engine-report "$REPLAY_INPUTS/engine-report.json" --out "$REPLAY_PROJECT/f722-heli.kicad_pcb"
```

This helper verifies source/session/report/contract hashes, preserves the original model identity, and explicitly rebinds an importer-only projection. New native UUIDs are expected; `checks/accepted80-replay-verified.json` establishes exact copper geometry, zones and footprint equivalence, 80 opens, zero native DRC violations and passing process checks. The original SWCLK sources are identified by hash; replaying their retained SES does not require bundling another entire old adapter tree.

The accepted80 session explicitly excludes only newly added SERVO3_EXT and extends RPM_EXT collinearly inside J7.3. See `retention.json` and `endpoint-completion.json`. The unfiltered engine SES is retained to audit the optimistic ROUTED result. The Java target-shape defect was present in the historical v3 source that produced these receipts. The current source contains the controlled target repair; these old routes must not be attributed to the current adapter. Native contact partitions and physical endpoint checks remain acceptance gates.

The reusable endpoint audit subtracts conservative native drill polygons from native inside pad copper. For through-hole pads it requires a positive centerline interval inside the annulus eroded by half trace width plus 1 nm. It never treats an endpoint over the drill as evidence of copper contact. Its four accepted entries exactly match the independent owner witness; the historical SERVO3 gap and RPM narrow entry both fail.

## Recover the exact historical inputs

See `sessions/recovery/README.md` and its manifest for byte-exact historical85/84 reconstruction from the pinned PR11 published80 board. The helper checks complete base and target hashes. Keep the paired project, rule, schematic and library files. No historical PCB is bundled here.

## Replay the accepted77 constructed session

`sessions/accepted77/source-identity.json` requires the exact candidate06 source board SHA-256 `221ee94c9a936be959dc89b7c7050a20b5f795af6a86921fb44c01a2e9dbecc3`, its paired project/rules and libraries. This source board is an external prerequisite; the historical85/84 recovery helpers do not reconstruct candidate06. The original full model SHA is `7b560e734499d0a01fb5614781dac0a9bbe1ec2e5b0b5535ba7d2a796342aa81`.

```sh
python3 -B tests/verify_session_packet.py --packet sessions/accepted77 --out /path/to/packet-check.json
python3 -B prepare_session_replay.py --packet sessions/accepted77 --source-board "$SOURCE_BOARD" --out "$REPLAY_INPUTS"
"$KICAD_PY" import_session.py --model "$REPLAY_INPUTS/model.json" --session sessions/accepted77/session.ses --engine-report "$REPLAY_INPUTS/engine-report.json" --out "$REPLAY_PROJECT/f722-heli.kicad_pcb"
```

The first two pure-Python checks passed during packaging, including the wrong-source rejection. The native import command has not been rerun for this compact packet. Its historical native acceptance is recorded in `checks/accepted77-import.json`, `accepted77-handoff.json` and `accepted77-owner-summary.json`. Native UUIDs of newly created objects may differ; compare native geometry, logical ownership, preserved fixed objects, endpoint entry, native DRC, process and reference results independently. The packet is an importer projection, never a complete routing model.

`construction.json` binds the original failed-insertion diagnostic, base session/report, exact constructor source and waypoint adjustment. `construct_located_session.used.py` is the exact historical source hash; the top-level constructor is the current source and has a distinct hash. The original 122 MB base report and complete native/model geometry are deliberately excluded. Reexecuting construction itself requires those exact external inputs. The retained compact constructed report preserves the actual route geometry required by the importer.

## Historical v4 controls and experimental settings

`checks/current77-source-identity.json`, `current77-zero-parity.json` and `current77-zero-import.json` bind the fresh passing zero to the v4 packaged source and model `c21ddb61a4e940988f1dbe59733a6fcd15930099d7459e48bed290d1539151eb`. All 1,513 fixed objects and 20 ordinary segments are preserved; the imported board is byte-identical to accepted77. This proves this zero control, not successful routing.

The v4 `TRACE_WIDTH_TOLERANCE=18` is a planning reserve, with the four inlined consumers compiled. `tests/compiled-planning-margin18-proof.json` and `tests/insertion-gap-result-margin18.json` establish the compiled constants and isolated D2 straight-segment control. Physical track width and clearance remain 0.127 mm. `F722_FORCE_SLOW_TREE=1` selects the stock slow tree; the route angle constraint remains 45 degrees. `F722_INSERT_DIAGNOSTICS=1` logs actual located paths and insertion failures.

The completed focused slow-tree trial on ADC_DIV_MID and FLASH_WP_N routed zero of four attempts; its output SES is byte-identical to its zero SES. See `checks/current77-slow-search.json` and the attempt summary. These were experimental full-route controls at v4. The later accepted76 ADC route supplies separate source-bound success evidence; the current runner completion fix still needs its own full-route proof. A failed search does not prove physical unroutability. The four historical legal via sites in `tests/clearance-audit` are existence witnesses, not complete routes.

Run the target and insertion tests following `tests/TARGET_SHAPE_CONTROL.md` and `tests/INSERTION_GAP_CONTROL.md` only after preparing their named exact external inputs. Their small generated fixtures and compiled classes are excluded. Reports preserve original source/model/class hashes; they do not silently claim that current classes produced historical routes. In particular, the empty-target receipt's loaded maze class predates the recompiled margin18 bytecode.

## Historical v5 source and controls

`checks/current75-source-identity.json`, `current75-zero-parity.json` and `current75-zero-import.json` bind the packaged Java sources to fresh model `4f0ac12384c28bc6431186dde30b035139d9d4acb8d32d3862d1f2d15c0c3354`. The zero import preserves all 46 ordinary objects, 1,513 fixed objects and 223 native contact partitions, reproducing the adopted75 PCB byte hash. No broad-route result is included.

`tests/failed-search-state/README.md` gives the two-pad fixture commands. Repaired and unrepaired reports preserve actual source and loaded-class hashes; the four repaired cases cover two early failures on fast/slow trees with retain=false. Current `AutorouteEngine` matches the repaired source. The small fixture does not exercise retained-database mode or complete board routing.

The accepted ADC checkpoint used the previous `LocalRouter` before the bounded-queue completion fix. `sessions/accepted76/adapter-source-provenance.json` selects each exact historical source from current v5 or immutable v4 and records all hashes. Runtime binary hashes are retained, but binaries and duplicate historical trees are not. A failure during the old final cleanup did not authorize its altered geometry; only the verified earlier session was accepted.

## Recover source09 and source12 for the new packets

Use `sessions/recovery75/README.md`, its manifest and helper. Supply the exact adopted75 PCB and its complete paired hardware project. The authority is PCB SHA `008d0b11df400284d12750c7f5c877b43a7ea28ffddbf4a4b799c3ae7ec4917e`; no Git commit is assumed. Recovery must restore the exact source09 board and four historical schematic files for ADC replay, or the source12 board with unchanged accepted75 paired files for FLASH replay. Keep these projects separate. The older `sessions/recovery` mechanism remains only for historical85/84 inputs.

```sh
python3 -B sessions/recovery75/rebuild_historical_source.py project --base-project "$ACCEPTED75_PROJECT" --source candidate09 --out "$SOURCE09_PROJECT"
python3 -B sessions/recovery75/rebuild_historical_source.py project --base-project "$ACCEPTED75_PROJECT" --source candidate12 --out "$SOURCE12_PROJECT"
```

Both destinations must be new directories. Each recovery verifies the PCB and all 62 required paired files. The six textual deltas total 23,174 bytes; exact rebuild and wrong-base, tampered-target/delta, missing/altered-pair, range and overwrite controls pass. `parts.json` is optional for native replay but required as authority when running the metadata patcher.


## Replay the actual ADC closure and metadata correction

With `SOURCE09_BOARD` pointing to the recovered source09 PCB in its exact paired project:

```sh
python3 -B tests/verify_session_packet.py --packet sessions/accepted76 --out /path/to/accepted76-packet-check.json
python3 -B prepare_session_replay.py --packet sessions/accepted76 --source-board "$SOURCE09_BOARD" --out "$ADC_REPLAY_INPUTS"
"$KICAD_PY" import_session.py --model "$ADC_REPLAY_INPUTS/model.json" --session sessions/accepted76/session.ses --engine-report "$ADC_REPLAY_INPUTS/engine-report.json" --out "$ADC_REPLAY_PROJECT/f722-heli.kicad_pcb"
```

`retention.json` explicitly discards the three unaccepted FLASH seed source UUIDs as well as new FLASH partial geometry. Its accepted77 proof establishes that no accepted route copper is removed. The retained SES is verified as the exact non-FLASH subset of the original session/report. The source contract is genuinely candidate09 (`544491a4…`), and the historical native import output before metadata is `f31522c2…`. It must not be renamed in provenance to accepted77 or adopted76.

The adopted candidate12 PCB (`508b5a36…`) additionally includes a paired informational metadata correction: 666 board-field edits and five schematic-field edits across four schematic files. `tests/mpn-parity/apply_metadata_copy.py` is the exact copy-only patcher, with `expected-updates.json` and compact independent native identity receipts. Supply the accepted75 project's unchanged authoritative `parts.json` (SHA `99e1589baf2033bc696613ad52c5deab3403397d7caafff6d8aa011296846858`) and a fresh output directory. Use the actual replayed output-board SHA for `--expected-board-sha256`; newly generated route UUIDs need not repeat, so the historical output byte hash is not promised for a new import. Native semantic/geometry and strict parity checks remain mandatory.

```sh
"$KICAD_PY" tests/mpn-parity/apply_metadata_copy.py --source "$ADC_REPLAY_PROJECT" --out "$ADC_METADATA_PROJECT" --authority "$ACCEPTED75_PROJECT" --manifest tests/mpn-parity/expected-updates.json --expected-board-sha256 "$ADC_REPLAY_BOARD_SHA256" --cli "$KICAD_CLI"
```

The patcher refuses source/output overlap, refuses output reuse and retains board geometry/net identities without a native save/refill. It changes only reviewed informational fields. `checks/accepted76-metadata-identity-summary.json` preserves the full historical proof hash and before/after native identity digests; its full 2.17 MB identity arrays are excluded.

## Replay explicit FLASH construction

With `SOURCE12_BOARD` pointing to the recovered exact candidate12 source PCB:

```sh
python3 -B tests/verify_session_packet.py --packet sessions/accepted75 --out /path/to/accepted75-packet-check.json
python3 -B prepare_session_replay.py --packet sessions/accepted75 --source-board "$SOURCE12_BOARD" --out "$FLASH_REPLAY_INPUTS"
"$KICAD_PY" import_session.py --model "$FLASH_REPLAY_INPUTS/model.json" --session sessions/accepted75/session.ses --engine-report "$FLASH_REPLAY_INPUTS/engine-report.json" --out "$FLASH_REPLAY_PROJECT/f722-heli.kicad_pcb"
```

The original import-only model has SHA `fd9d1bc80e65864982ffe51e70885d713d94a96a016b3fba7411fd2694c5ef6d`. It is not a complete routing model. The historical original contract identity remains that SHA; its packaged copy relocates machine-local paths and therefore has a distinct portable hash. `checks/portable-path-projections.json` binds both identities, and `source-identity.json` separates them. The historical engine report/model hash remains unchanged. The minimal importer projection contains the same ownership and geometry contract and binds the supplied exact source board at replay time. All existing source objects are fixed; only FLASH geometry is added. The SES has eleven proposed segments and two vias; the historical native importer yields ten track objects plus two vias after exact collinear union. Packet checks compare the original SES/report geometry before union.

Both new packet identity/projection checks, including wrong-board rejection, pass. Neither new compact native replay was rerun while packaging. Native import/refill, endpoint entry, DRC, process, saved GND connectivity and support gates must be rerun for a newly imported board. Historical acceptance is documented separately in `checks/accepted76-*` and `checks/accepted75-*`.

## Construction proof sources and limits

Current `construct_escape_session.py`, `construct_native_network.py`, `retain_session.py`, `endpoint_witness.py` and `audit_support_connectivity.py` are included. Packaged proposal/contract paths are relative to the routing source root. Linked hashes among the portable proposals are updated; the portability receipt separately retains their original historical byte hashes. Construction/native acceptance receipts remain unchanged and identify the original inputs, rather than falsely attributing native execution to the relocated copies. The exact historical generator sources and compact proposals are under `tests/escape-stubs`. The large exact-distance witness arrays (including the 15 MB source12 proof) are omitted; `checks/native-construction-proof-projections.json` binds their exact hashes, sizes, compact proposal facts and generator versions. These summaries do not substitute for rerunning the native proof if construction inputs change.

The historical generators expect the original relative candidate/model directory layout, named in their source. Recover the corresponding exact boards and regenerate their native exports before reuse. `sessions/accepted75/located-topology.json` is the original topology receipt; place an exact copy at the generator's `model-candidate09-cleanup/located-topology.json` input when reproducing it. Native witness files and path-bound construction proposals must be regenerated in a new working copy; machine-specific path changes produce new report hashes. Do not relabel regenerated evidence as the old hash-bound receipt. Replaying the already preserved import session does not need those omitted witness arrays.

## v6 adopted70 and adopted69 replay

`sessions/recovery69/README.md` defines exact source recovery from the proposed published69 paired hardware project. Keep the full paired project, rules, schematics and libraries. All 62 required paired files match across source75, source70 and adopted69; only the PCB requires a delta. Optional parts metadata and local editor preferences are recorded separately. The full69 board hash is authoritative; no remote commit availability is assumed.

```sh
python3 -B sessions/recovery69/rebuild_historical_source.py project --base-project "$ACCEPTED69_PROJECT" --source candidate13 --out "$SOURCE75_PROJECT"
python3 -B sessions/recovery69/rebuild_historical_source.py project --base-project "$ACCEPTED69_PROJECT" --source candidate15 --out "$SOURCE70_PROJECT"
```

Both destinations must be new. Positive file/project reconstruction and wrong-base, payload/target tampering, missing/altered paired inputs and overwrite controls pass. Source70's delta is 439 bytes with two copy ranges and no literal geometry. Source75's delta is 9,893 bytes and restores the historical saved-fill bytes exactly. No geometry is recalculated during source recovery.

To replay the real accepted70 session:

```sh
python3 -B tests/verify_session_packet.py --packet sessions/accepted70 --out /path/to/accepted70-packet-check.json
python3 -B prepare_session_replay.py --packet sessions/accepted70 --source-board "$SOURCE75_PROJECT/f722-heli.kicad_pcb" --out "$REPLAY70_INPUTS"
"$KICAD_PY" import_session.py --model "$REPLAY70_INPUTS/model.json" --session sessions/accepted70/session.ses --engine-report "$REPLAY70_INPUTS/engine-report.json" --out "$REPLAY70_PROJECT/f722-heli.kicad_pcb"
```

The source75 full model is historical model `4f0ac12384c28bc6431186dde30b035139d9d4acb8d32d3862d1f2d15c0c3354`. Packet geometry, identity, importer projection and wrong-source rejection pass; a new native replay/refill of this 70 session was not run while packaging. Its original native acceptance and final/checkpoint equality remain separately source-bound. The successful broad run stopped at five successes, not at final queue exhaustion.

For accepted69, use the exact source70 project:

```sh
python3 -B tests/verify_session_packet.py --packet sessions/accepted69 --out /path/to/accepted69-packet-check.json
python3 -B prepare_session_replay.py --packet sessions/accepted69 --source-board "$SOURCE70_PROJECT/f722-heli.kicad_pcb" --out "$REPLAY69_INPUTS"
"$KICAD_PY" import_session.py --model "$REPLAY69_INPUTS/model.json" --session sessions/accepted69/session.ses --engine-report "$REPLAY69_INPUTS/engine-report.json" --out "$REPLAY69_PROJECT/f722-heli.kicad_pcb"
```

The historical original import-contract SHA is `db348feea0bd2f8b45c47c89bc3c1663931020c077fe8ef9972592f968ba2778`. The packaged historical-contract copy has portable paths and a separately recorded digest; the report retains the true original model identity. No new via, inner-layer track or outside-layer copper zone is involved, so its contract requests no refill and requires exact saved zones. It adds two F.Cu tracks to partially join ADC_BUS, not to complete the whole net.

This actual native importer replay was run on a recovered70 paired copy. `checks/accepted69-native-replay-verified.json` confirms geometry equivalence with adopted69 while allowing only the two generated track UUIDs to differ. All 1,580 source objects, prior 67 ordinary UUIDs/nets, zones/fills, footprints, outline and layer setup are exact. No JVM, native DRC or loaded-power solve was rerun for this replay. Each replay output remains disposable until whatever native gates its intended use requires have passed.

## Tiny final-queue controls and portable historical receipts

The final passing cases in `tests/end-queue-stop` cover both the pending-geometry flush and snapshot-reuse branches. Original production/test source and class hashes remain in the result receipt; no duplicate source-used tree or compiled class is bundled. The exact production sources are the packaged `src/` files. Four small model/DSN fixture files are explicitly allowlisted as synthetic test data; they contain no native PCB.

Machine-local paths in the fixture and observed progress/debugger/log files are projected relative to the routing source root. `checks/v6-portable-projections.json` binds each original byte hash to the delivered copy. Artifact links in the projected result receipt use current hashes; its historical fixture/result identity remains separate. The production snapshots still describe the original runtime model. Pure-Python rechecks of both portable recorded cases, exact final/checkpoint SES/geometry, source hashes, missing-guard and shifted-endpoint negatives pass. No JVM was rerun during packaging.

To run a new synthetic control, first run `python3 -B tests/failed-search-state/prepare_fixture.py`, then follow the commands in `tests/end-queue-stop/README.md`. The generator writes fresh runtime paths/model hashes for the current checkout. New result hashes must not be relabelled as the old historical execution. The two synthetic cases prove the final queue trigger; the broad board run independently proves a five-success cooperative stop. Neither replaces full-net or electrical acceptance.

## Short construction and endpoint sources

`construct_short_local.py` is the exact ADC_BUS constructor source. The source-bound generator/helpers and compact proposal are under `tests/short-local-proposals`; the 1.38 MB all-distance witness file is excluded, with its hash/size retained in `checks/accepted69-local-proof-summary.json`. Recreating a proposal requires the named exact source70 native export and logical-role model; a new route input needs new native validation. Replaying the preserved SES does not require that omitted witness file.

`tests/broad-endpoints/audit_native_endpoints.py` is the exact reusable accepted70 endpoint audit source. Its final receipt proves nine pad terminations and five full-width annular strips. A redundant via spur and incidental side overlap are explicitly retained as non-evidence. Nominal entry/gap values are not manufacturing tolerance or loaded electrical qualification.

`checks/accepted69-unchanged-reference-geometry.json` establishes exact saved fills, In1/In4 copper and existing via/drill geometry for the local two-track addition. It is not a loaded-power result. The BEC copper deficit from the loaded screen remains unresolved in this 69 checkpoint; no power fix is included.

## Verify or regenerate the v6 delta

Use immutable corrected v5 manifest `02791deae14ce18c6d8b678cb63e3be43d4f383dbc2bc2b2f820e8468f49a0ac`. The ZIP contains changed paths only; apply `changed/` to that exact base, remove only listed deletions, then verify the complete new manifest and allowlist.

```sh
python3 -B tools/build_source_delta.py --base /path/to/immutable-public-source-ready-v5 --staging . --out-prefix /path/to/routing-source-v6-delta
```

The packager validates syntax, exclusions and exact delta reconstruction without native execution. Boards, real models/native exports, large witness arrays, binaries and caches remain excluded. The complete staged package remains unfinished at 69 opens with the unresolved BEC copper deficit.
