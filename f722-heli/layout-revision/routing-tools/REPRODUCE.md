# Reproduce the ordinary-routing checkpoint

This is unfinished work. The accepted candidate08 checkpoint has 77 open connections and zero native DRC errors/warnings, board SHA-256 1ff8ee645bd5fea7bbbc30cd4e5269aab76a2032efe3e2c4e77a0becd85e9edf. Its last D2_A closure was explicit native construction from a path located during failed stock insertion, with a documented 0.025 mm outward detour; it was not successful engine insertion. Current-source zero parity passes. The current margin18/slow-tree focused trial failed all four attempts and added no geometry. Historical receipts are bound to their original sources; every new source still requires fresh zero controls and native validation.

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

## Current controls and experimental settings

`checks/current77-source-identity.json`, `current77-zero-parity.json` and `current77-zero-import.json` bind the fresh passing zero to the current packaged source and model `c21ddb61a4e940988f1dbe59733a6fcd15930099d7459e48bed290d1539151eb`. All 1,513 fixed objects and 20 ordinary segments are preserved; the imported board is byte-identical to accepted77. This proves this zero control, not successful routing.

The current `TRACE_WIDTH_TOLERANCE=18` is a planning reserve, with the four inlined consumers compiled. `tests/compiled-planning-margin18-proof.json` and `tests/insertion-gap-result-margin18.json` establish the compiled constants and isolated D2 straight-segment control. Physical track width and clearance remain 0.127 mm. `F722_FORCE_SLOW_TREE=1` selects the stock slow tree; the route angle constraint remains 45 degrees. `F722_INSERT_DIAGNOSTICS=1` logs actual located paths and insertion failures.

The completed focused slow-tree trial on ADC_DIV_MID and FLASH_WP_N routed zero of four attempts; its output SES is byte-identical to its zero SES. See `checks/current77-slow-search.json` and the attempt summary. These switches and the planning-margin change remain experimental for full-route qualification. A failed search does not prove physical unroutability. The four historical legal via sites in `tests/clearance-audit` are existence witnesses, not complete routes.

Run the target and insertion tests following `tests/TARGET_SHAPE_CONTROL.md` and `tests/INSERTION_GAP_CONTROL.md` only after preparing their named exact external inputs. Their small generated fixtures and compiled classes are excluded. Reports preserve original source/model/class hashes; they do not silently claim that current classes produced historical routes. In particular, the empty-target receipt's loaded maze class predates the recompiled margin18 bytecode.

## Verify or regenerate a source delta

The complete staging allowlist includes every delivered file. `FILES.sha256.json` hashes each file except itself; the external delta metadata binds the full manifest hash. Verify the v3 base before applying the ZIP's `changed/` contents relative to the routing source root, remove only any metadata-listed deletions, and then verify the complete v4 manifest and allowlist.

The packaging helper recompiles Python syntax in memory, parses JSON, runs shell syntax checks, rejects caches/boards/models/binaries, and applies the delta to a temporary v3 copy to prove exact reconstruction. It does not compile Java, run native KiCad, or start route search.

```sh
python3 -B tools/build_source_delta.py --base /path/to/immutable-public-source-ready-v3 --staging . --out-prefix /path/to/routing-source-v4-delta
```
