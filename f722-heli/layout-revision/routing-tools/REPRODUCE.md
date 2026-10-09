# Reproduce the ordinary-routing checkpoint

This is unfinished work. No real ordinary route has run, and fixed-support integration is still incomplete. The historical checks establish the bare-placement adapter only. They are not approval to route another board.

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
./run_local.sh "$MODEL" "$MODEL/route" "$PASSES"
"$KICAD_PY" import_session.py --model "$MODEL/model.json" --session "$MODEL/route.ses" --engine-report "$MODEL/route.after.json" --out "$MODEL/routed-candidate.kicad_pcb"
python3 native-tools/check_protection_paths.py --geometry "$MODEL/routed-candidate.native.json" --contracts config/candidate-contracts.json --out "$MODEL/protection-original18.json"
python3 native-tools/check_protection_paths.py --geometry "$MODEL/routed-candidate.native.json" --contracts config/supplemental-contracts.json --out "$MODEL/protection-supplemental7.json"
```

Each physical checker returns nonzero when any case fails and still writes its full report. Candidate completion additionally requires native DRC, exact schematic connectivity, all-net connectivity, DFM, reference continuity, and timing checks. Preserve the logical route map returned by the native importer for any continuation. Do not publish a route as fabrication-ready based on engine connectivity alone.

## Small adapter controls

```sh
java -cp build:vendor/freerouting-2.1.0.jar NativeContactRegression "$MODEL"
java -cp build:vendor/freerouting-2.1.0.jar SharedPadSeamControl "$MODEL"
python3 route_geometry.py
```

The native-contact control exercises off-centre trace capsule contact, symmetric adjacency, logical isolation, and stale-contact removal. The shared-pad control deliberately reports the conservative rejection of inside-pad branch overlap. It does not claim physical impossibility. Full native geometry is retained in the separate independent source export; 10 nm engine planning geometry uses checked containment.
