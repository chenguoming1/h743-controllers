# Reproduce the ordinary-routing checkpoint

This is unfinished work. The retained real sessions reduced the accepted native board from 85 to 80 open connections with zero native DRC errors/warnings. Historical placement and trial03 checks remain labelled by their source hashes. Every new source requires fresh zero controls and native validation.

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

## Compact actual-session replay

The two `sessions/` packets contain the actual SWCLK and accepted80 sessions, import-only ownership contracts, report geometry, exact original model/native/adapter/runtime identities, and explicit postprocessing provenance. These are not complete routing models. Verify `FILES.sha256.json` before use. Supply the exact frozen source board named by the packet identity and its full paired project, schematic and local libraries. Then:

```sh
python3 prepare_session_replay.py --packet sessions/accepted80 --source-board "$SOURCE_BOARD" --out "$REPLAY_INPUTS"
"$KICAD_PY" import_session.py --model "$REPLAY_INPUTS/model.json" --session sessions/accepted80/session.ses --engine-report "$REPLAY_INPUTS/engine-report.json" --out "$REPLAY_PROJECT/f722-heli.kicad_pcb"
```

This helper verifies source/session/report/contract hashes, preserves the original model identity, and explicitly rebinds an importer-only projection. New native UUIDs are expected; `checks/accepted80-replay-verified.json` establishes exact copper geometry, zones and footprint equivalence, 80 opens, zero native DRC violations and passing process checks. The original SWCLK sources are identified by hash; replaying their retained SES does not require bundling another entire old adapter tree.

The accepted80 session explicitly excludes only newly added SERVO3_EXT and extends RPM_EXT collinearly inside J7.3. See `retention.json` and `endpoint-completion.json`. The unfiltered engine SES is retained to audit the optimistic ROUTED result. The Java target-shape defect remains present in this historical tested source and must be repaired and separately controlled before a broad new run. Native contact partitions and physical endpoint checks remain acceptance gates.

The reusable endpoint audit subtracts conservative native drill polygons from native inside pad copper. For through-hole pads it requires a positive centerline interval inside the annulus eroded by half trace width plus 1 nm. It never treats an endpoint over the drill as evidence of copper contact. Its four accepted entries exactly match the independent owner witness; the historical SERVO3 gap and RPM narrow entry both fail.
