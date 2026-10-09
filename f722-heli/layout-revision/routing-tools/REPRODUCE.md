# Reproduce V9 checkpoint55 provenance

This source-only delta requires the complete, unchanged V8 source tree, not the V8 delta ZIP alone. Verify the separately supplied V9 ZIP SHA-256. The base manifest is `13f0fa03eaf62d3ae16635109877499976843e7289f97372cb4e2143cdd180e6`. `tools/apply_source_delta_v9.py` validates every base file, safe archive paths, changed bytes and complete result before creating a new output tree:

```sh
python -B tools/apply_source_delta_v9.py --base /path/to/immutable-v8 --delta /path/to/routing-source-v9-delta.zip --zip-sha256 VERIFIED_V9_ZIP_SHA256 --out /path/to/new-v9
```

The apply helper is in the delta's changed/tools directory; it can be read there before applying. Use the SHA supplied alongside the archive, not an untrusted checksum from its contents.

From the reconstructed V9 root, portable verification uses Python's standard library only:

```sh
python -B tests/verify_v9_evidence.py --base-project /path/to/pinned-candidate22 --out /tmp/v9-verified.json
```

The required external project is the same 62 functional paired files pinned by V8 `sessions/recovery57/paired-files.json`. A different PCB or modified schematic/project/library file is rejected. The optional `--historical-workspace /path/to/ordinary-routing` verifies full original receipt/model/source hashes; absence of that workspace does not block portable verification. The output path should be outside the sealed source tree.

For exact paired recovery in two steps:

```sh
python -B sessions/recovery57/rebuild_historical_source.py project --base-project /path/to/pinned-candidate22 --source candidate26 --out /tmp/recovered26
python -B sessions/recovery55/rebuild_historical_source.py project --base-project /tmp/recovered26 --source candidate27 --out /tmp/recovered27
python -B sessions/recovery55/rebuild_historical_source.py project --base-project /tmp/recovered26 --source candidate28 --out /tmp/recovered28
```

All output directories must be new. Recovery preserves exact historical PCB UUIDs/serialization and all paired functional files. It does not reexecute native import or renew any qualification.

The real 27 packet is `sessions/engine56`; the explicit 28 packet is `sessions/accepted55`. `prepare_session_replay.py` can bind each packet to its exact recovered source board using `--packet`, `--source-board` and `--out`. It verifies SES/report/contract hashes and only prepares an importer projection. Native replay, if separately run, must use frozen `import_session_v8.py`;27 requires its original reference-refill behavior and28 requires `--preserve-unaffected-fills`. A new import can generate new UUIDs and is separate from exact byte recovery. It requires the native environment and coordinated resources; none was run by V9 packaging.

The exact source26 PORT_B_RX_EXT::P2 refusal and proposals are under `tests/located-portb-rx26`; `sessions/accepted55/native-construction.json` and `original-import-contract.json` preserve the prepared-on27 packet. Historical source paths are relative provenance locators, not promises that every full model/native export is bundled. Original dependency hashes are preserved beside portable projection hashes. The source script `prepare_located_branch_continuation.py` adds only additive-current-native rechecking; all Java sources remain identical to V8.

The shared-pad risk review/control is retained as a historical bounded finding. Its original README run command describes the isolated historical workspace; full copied baselines, compiler/JARs and generated classes are intentionally excluded from V9. The risk control was not rerun here.

## Inherited V8 reproduction instructions (historical only)

# Reproduce V8 portable controls

The V8 delta base is the complete, immutable V7 source package, manifest SHA-256 `c1c30c9e18658abef883d0b201b8233f135d7643574536637523cb633e1052d0`. Verify every V7 file against its manifest before applying `changed/`; remove only `DELTA.json`'s explicit deleted paths. Then verify the complete new allowlist and manifest. The delta is not a standalone full package.

## Exact paired source recovery and pure controls

An external hash-pinned candidate22/accepted62 paired project is required. Its PCB SHA-256 is `fd8fd21062c61992ec992481d394e19a6a99cfe8ec58405ed1e391c5e3836bfa`; all 62 functional file hashes are enumerated in `sessions/recovery57/paired-files.json`. The optional `library/README.md` is not needed. Recovery retains exact historical UUIDs and serialized bytes.

```sh
python3 -B tests/verify_v8_evidence.py --base-project /path/to/accepted62
```

The recorded verification also compared compact projections to their full historical originals:

```sh
python3 -B tests/verify_v8_evidence.py --base-project /path/to/accepted62 --historical-workspace /path/to/ordinary-routing
```

The second command needs the declared original files, including full original models/reports, owner receipts, integrated trial27 pose receipt, static power applicability receipt, and checkpoint57 comparison. These large inputs and surrounding historical workspace are not bundled. The first command verifies portable identity/recovery and controls without those extra originals. Running the verifier writes new `checks/*-v8-packet-verified.json` and `checks/v8-evidence-verified.json`; rebuild the source manifest afterward if those recorded receipts differ.

Recover a particular exact source without routing or KiCad:

```sh
python3 -B sessions/recovery57/rebuild_historical_source.py project --base-project /path/to/accepted62 --source candidate24 --out /tmp/exact24
python3 -B sessions/recovery57/rebuild_historical_source.py project --base-project /path/to/accepted62 --source candidate25 --out /tmp/exact25
```

Candidates22,23,24,25,26 are supported. Output directories must not already exist; all inputs are checked before outputs are written. Recovery contains compact copy/literal deltas, not full boards.

## Optional native replay, not executed during V8 packaging

Use the appropriate KiCad Python and the dependency/bootstrap guidance inherited below. The root `import_session.py` remains byte-identical to V7 for old receipts. Candidate23's frozen importer is `import_session_candidate23.py`; candidates25/26 use `import_session_v8.py`. `route_geometry.py` and native exporter sources remain identical.

Candidate25 uses only the second-success pair, against exact recovered24:

```sh
python3 -B prepare_session_replay.py --packet sessions/accepted58 --source-board /tmp/exact24/f722-heli.kicad_pcb --out /tmp/replay25-contract
/path/to/kicad-python -B import_session_v8.py --model /tmp/replay25-contract/model.json --session sessions/accepted58/session.ses --engine-report /tmp/replay25-contract/engine-report.json --preserve-unaffected-fills --out /tmp/replay25/f722-heli.kicad_pcb
```

Candidate26's final third-success session is rebound to exact25; its packet already retains the historical additive rebind. It requires native reference refill, so no preserve-fills option is passed:

```sh
python3 -B prepare_session_replay.py --packet sessions/accepted57 --source-board /tmp/exact25/f722-heli.kicad_pcb --out /tmp/replay26-contract
/path/to/kicad-python -B import_session_v8.py --model /tmp/replay26-contract/model.json --session sessions/accepted57/session.ses --engine-report /tmp/replay26-contract/engine-report.json --out /tmp/replay26/f722-heli.kicad_pcb
```

The importer copies the paired `.kicad_pro` and `.kicad_dru` for refill. A fresh output generates new route UUIDs, and native serialization/refill can differ across KiCad versions; do not expect its board byte hash to equal the historical board. Independently compare geometry and reexecute the required native endpoint, DRC, parity, process, mechanical and reference gates before any new adoption. Candidate26 power/VCAP results require new numerical validation regardless of this replay.

Candidate23's packet is replayable by the analogous source22/importer-candidate23 path with `--preserve-unaffected-fills`, but its failed endpoint disposition must remain. `complete_native_pad_entries.py` retains the explicit candidate24 constructor; it expects the exact candidate23 board/native/map/audit inputs. V8 does not claim a new constructor or confinement audit execution. The historical `audit_pad_completion.historical.py` is preserved for source identity and uses its original workspace layout; it is not a portable command without adapting that layout.

`prepare_engine_continuation_import.py` is the exact candidate26 rebind generator. It requires full original source24 model/native/board and candidate25 native/import/map inputs, whose original hashes remain in `sessions/accepted57/session-rebind.json`. The already projected packet avoids needing those full planning inputs for importer replay. Rebinding is not a new engine run.

## Rebuild the bounded V8 delta

```sh
python3 -B tools/build_source_delta.py --base /path/to/immutable-public-source-ready-v7 --staging . --out-prefix /path/to/routing-source-v8-delta
```

The builder checks source exclusions, syntax, the full immutable base, every changed ZIP entry, and exact reconstruction of complete staging. It performs no native work. Prior published versions stay untouched.

## Inherited reproduction instructions (historical V7 and earlier)

The following applies to earlier packets and checkpoints. It does not expand the V8 verification or numerical claim.

# Reproduce the ordinary-routing checkpoint

Adopted candidate22 is unfinished at 62 opens and zero native DRC errors/warnings, PCB `fd8fd21062c61992ec992481d394e19a6a99cfe8ec58405ed1e391c5e3836bfa`. The separate power v6 supplies 62 passing required conditional cases, five passing VCAP DC loops and passing numerical gates. Its overall boolean stays false for the outside-envelope 18.56 A single-feed illustration. It is not fabrication-ready. `checks/current62-adoption.json` and the exact power applicability receipt bind this status; inherited pending handoffs remain historical.

## Current v7 replay from the accepted62 paired project

Set `ACCEPTED62` to the full paired hardware directory and use new empty destinations. Run from the package root. Recover each exact source with `sessions/recovery62/rebuild_historical_source.py`; no complete historical board is bundled.

```sh
python3 -B sessions/recovery62/rebuild_historical_source.py project --base-project "$ACCEPTED62" --source candidate21 --out "$RECOVERED63"
python3 -B tests/verify_session_packet.py --packet sessions/accepted62 --out "$PACKET_CHECK"
python3 -B prepare_session_replay.py --packet sessions/accepted62 --source-board "$RECOVERED63/f722-heli.kicad_pcb" --out "$REPLAY_INPUTS"
"$KICAD_PY" -B import_session.py --model "$REPLAY_INPUTS/model.json" --session sessions/accepted62/session.ses --engine-report "$REPLAY_INPUTS/engine-report.json" --out "$REPLAY_PROJECT/f722-heli.kicad_pcb"
```

Prepare `REPLAY_PROJECT` as a separate complete copy of the recovered paired project before native import. For accepted65 use source candidate19; for accepted63 use source candidate20. All three actual imports were rerun during packaging; geometry equals the historical candidate except newly generated route UUIDs, with exact saved fills/fixed objects and no refill. Historical owner/native acceptance remains separate from replay geometry equivalence.

For the complete recorded controls, `tests/verify_v7_replay.py --base-project "$ACCEPTED62" --historical-workspace "$HISTORICAL_INPUTS" --kicad-python "$KICAD_PY"` also compares against independent candidate20/21/22 native exports. Those exports are external large verification inputs, not bundled. Omit `--kicad-python` for packet/projection/negative controls only; the historical workspace then is not read. Temporary products are discarded. Recovery rejects altered source, paired files and delta data. See recovery62/README for the exact file contract and the chain back through old69.

## Reconstruct the coordinated power transaction

Recover candidate16 from accepted62, then copy `checks/accepted69-logical-route-map.json` to `f722-heli.logical-route-map.json` beside its recovered board. The map is board-bound. The constructor uses the included compact proposal with every operational transaction argument preserved:

```sh
"$KICAD_PY" -B tests/power-feed-reconstruction/construct_power_candidate.py --source "$OLD69/f722-heli.kicad_pcb" --proposal sessions/power19/input-proposal.json --out "$NEW_POWER_PROJECT"
```

This creates new native UUIDs and performs reference refill. It was not rerun during v7 packaging; original constructor/audit/endpoint/owner receipts remain source-bound evidence. Recreated geometry needs its own native/refill and numerical applicability checks. Do not expect the historical PCB byte hash or silently reuse loaded results. The retained exact power constructor consumes only the transaction fields preserved in the compact input. Diagnostic provenance hashes identify omitted large witnesses.

## Located-path preparation and bounded execution

`prepare_located_branch.py` accepts explicit board/native/map/model/captured-log inputs and preserves foreign/other-branch clearance outside the legitimate shared pad. See `tests/shared-pad-alias21/REPRODUCE.md`; the exact full historical source21 model is an external input if reexecuting its historical controls. Compact replay does not require it. The generic preparation is separately tested; actual candidate22 was produced by the source-bound specialized preparer and screened importer, both retained.

`run_bounded_local.py --model "$MODEL" --prefix "$PREFIX" --seconds 100 --successes 2 --nets "$NETS"` requests the runner's existing cooperative stop and never kills the JVM. Complete the fresh zero gate and obtain the normal heavy-process allocation first. Source21's tested request took 129.086 seconds including in-flight work. Source22 and all later live trials are outside this packet.

## Historical v1–v6 reproduction instructions

The following sections describe inherited controls and packets under their original hashes and statuses. References to current77/current75/source69 identify those historical epochs, not the adopted62 checkpoint above.

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
