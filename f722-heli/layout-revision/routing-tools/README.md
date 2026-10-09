# F722 ordinary-routing reconstruction

Local-only adapter for the new F722 placement. This is a planning/import pipeline, not a fabrication-ready PCB. The project owner coordinates the single heavy-process slot and the fixed power/critical support handoff. Never run nonzero passes on the bare placement model.

## Source and ownership

- Official Freerouting 2.1.0 release JAR and tagged source are pinned in `vendor/provenance.json`; Eclipse ECJ is from Maven Central.
- The local driver calls the engine directly, never the upstream GUI/API scheduler. It sets documented `usage_and_diagnostic_data.disable_analytics=true`, API server disabled, and GUI disabled before loading any board. No analytics client is initialized, no remote route service is used.
- The shared native exporter lives in `native-tools/export_native_copper.py` (and the canonical revision scripts). It records native UUIDs, pad shapes and masks on all actual layers, drill capsules, plated spans, footprint poses/side, rule zones and filled polygons with holes.
- `prepare_model.py` derives ordinary nets from every native terminal, excludes explicit power ownership and critical support domains, and includes full flash SPI, barometer I2C and ordinary GPIO/ADC/UART nets. Explicit power ownership is in `config/power-owned-nets.json`.
- Current bare-placement scope: 51 physical ordinary nets, 70 logical branches. Canonical U14 connector → NC → actual IO → series-resistor paths remain intact. U13 uses current reviewed channels ESC3/RPM6/SBUS1. U16 HV paths receive actual-pad branch constraints as well.

## Physical and planning geometry

The exact 1 nm native physical export is independently hashed and retained. Freerouting's safe board scale is 10 nm; its polygon implementation does not accept fractional coordinates. Planning guards therefore conservatively cover source geometry using a 20 nm outward allowance and 10 nm grid. Pad contacts are inset by 20 nm before gridding and remain inside native ERROR_INSIDE pad copper. This is an explicitly checked containment contract, not a claim that rounded planning shapes are identical to native copper.

The separate import gate requires exact native geometry and identity, including all UUID-distinct repeated pad numbers, complete layer sets, side and poses. The corrected zero control at `checks/baseline-zero-parity.json` passes all 526 native contact partitions and all 1,984 model area keys. Its zero SES was independently parsed and imported through native objects; the resulting PCB reproduced the source SHA exactly. A byte copy is not used.

Native pad-only static contact groups are established from physical native copper, including real plated barrels. Mutable routing is never used to manufacture virtual connectivity. The Java contact class recomputes intersections using the actual current trace capsules; the regression test checks off-centre contact, symmetric adjacency, logical isolation and stale-contact removal.

Logical branches share only proven physical pad contact windows. Distinct branch traces retain full mutual clearance. No broad physical-net alias merging or arbitrary four-via/length limit is permitted. `checks/shared-pad-seam-control.json` explicitly records that overlapping logical trace copper entirely within U14.4 is conservatively rejected, while outside-pad overlap is correctly forbidden. This is a known limitation, not evidence of physical impossibility. Conservative branch clearance may make an escape unroutable; it does not authorize a shunt bypass. The independent physical pad-cut checker is the completion gate.

## Manufacturing constraints

Six layers maximum; only F.Cu, In2.Cu, In3.Cu and B.Cu carry ordinary routes. In1/In4 are GND reference layers. Ordinary width/clearance is 0.127 mm; through vias are 0.45/0.20 mm and explicitly tented on both faces. Every SMT mask opening on both faces excludes via drills by 0.20 mm, regardless of net. Drill-to-drill gap is 0.25 mm and board-edge/NPTH clearance is 0.254 mm. No new filled/capped signal-via process is introduced.

Mask via guards include 0.075 mm beyond mask copper because the engine measures against 0.225 mm via copper radius: 0.075 + 0.225 − 0.100 = 0.200 mm drill gap. Existing hole guards add 0.125 mm for the analogous 0.25 mm hole gap. Guard clearance class 0 adds no hidden default clearance; ordinary foreign-copper guards use class 1.

## Commands

Use Python 3 with the pinned requirements installed for model building and independent geometry checks. Use the verified KiCad 10 Python wrapper specified by `KICAD_PY` for native export/import.

1. Export the agreed combined support board with `export_native_copper.py --board BOARD --out NATIVE.json`.
2. Build a fresh model with `prepare_model.py --native NATIVE.json --board BOARD --out MODEL_DIR`. Set `--support-ready` only after the fixed-support handoff and project-owner approval. The launcher rejects nonzero passes unless that exact model has a passing `zero-parity.json`. An existing protected ordinary route requires `--logical-route-map`; explicit immutable ordinary objects may be supplied with `--fixed-ids`.
3. Compile with `./compile.sh`.
4. With the heavy slot, run `./run_local.sh MODEL_DIR OUTPUT_PREFIX 0` for the finite zero-route control.
5. Import the actual session: `import_session.py --model MODEL_DIR/model.json --session OUTPUT_PREFIX.ses --engine-report OUTPUT_PREFIX.after.json --out ZERO.kicad_pcb`.
6. Verify: `verify_zero.py --model MODEL_DIR/model.json --engine OUTPUT_PREFIX.after.json --imported ZERO.import.json --out MODEL_DIR/zero-parity.json`.
7. After support, zero controls and the project-owner launch gate pass, routing uses the same command with an approved pass budget. Route outputs remain isolated until native DRC, schematic parity, protection cuts, DFM and full-net timing/reference checks pass.

No routing result by itself establishes reference continuity, signal timing, power integrity, ESD immunity, or assembly qualification. Those are separate completion gates.

## Restore this source-only checkpoint

Install `requirements.txt` through the normal official package workflow; Java 21 is required. Run `python bootstrap_dependencies.py` to materialize and SHA-verify the official engine/compiler, then `./compile.sh`. These are local tools; no board upload is authorized or required.

Set `KICAD_PY` to the known KiCad 10 wrapper. `./prepare_fresh.sh /absolute/path/to/final-support.kicad_pcb /absolute/path/to/fresh-model` exports and prepares only. It does not route. Add `--support-ready` only for the owner-approved integrated support source. Preserve paired project and design-rule files beside the source board. The heavy-slot zero run is `./run_local.sh /absolute/path/to/fresh-model /absolute/path/to/fresh-model/zero 0`.

The included checks are historical F400 controls. They are not a zero gate for a later pose/support source and cannot authorize routing that source. Recreate the native export, model, zero SES, native import and zero-parity report before every new-source route. The packaged source intentionally contains no native PCB, JAR, geometry dump, route snapshot, log stream, or generated routing candidate.

The complete copy/paste sequence is in `REPRODUCE.md`. `PUBLIC_SOURCE_ALLOWLIST.json` is the exact publication allowlist, and `FILES.sha256.json` binds every payload file. The launcher supports both the standalone `native-tools` package and the development checkout exporter location.

## Integrated-support controls and reference planes

The frozen trial03 support source passes a fresh, support-not-ready zero control: 51 physical ordinary nets, 70 logical branches, 4,185 engine area keys and 306 native contact partitions. Native zero import preserves all 1,109 source objects and 156 footprints and reproduces the original PCB SHA. No nonzero route search has run.

Saved KiCad GND fills can encode holes using exact zero-width bridge edges. `native-tools/exact_native_contours.py` removes only reversed integer edge pairs and reconstructs unambiguous cycles. It preserves every surviving boundary edge, coordinate and integer signed area, and rejects ambiguous touching topology. The trial03 planes each recover 53 holes with zero coordinate displacement. Raw native input and compact receipts are retained independently; no GEOS repair is used.

Only filled GND reference zones wholly on In1/In4 are regenerable. Their old fill areas are omitted from planning obstacles so ordinary through-vias can receive new antipads. Static pads/tracks/vias, every mask/drill guard, rule areas and all other filled zones remain obstacles under their existing rules. In1/In4 stay disabled for ordinary signal tracks.

Seven direct engine checks prove legal through-vias at three empty reference-plane points and rejection at a foreign pad, fixed track, existing drill and same-net SMT mask. A separate signal-via/stub importer fixture tests actual saved antipads: each plane gains one hole, the gap is 0.1274991308 mm, and the complete native GND pad partition stays connected and unchanged. A deliberately stale-fill fixture fails both reference-layer clearance checks. These are isolated controls, not routing candidates.

For route imports the destination PCB/project pair is saved and reopened before native refill. Every new ordinary object's physical net is checked before save, after reload, after refill and in the final export. Exact fixed native objects and zone identity/outlines/rules remain mandatory; regenerated GND fill is explicitly reported as changed. Final saved-fill clearance, full GND connectivity, reference/current checks and loaded native DRC remain required.

Every import now writes `OUTPUT.logical-route-map.json` with its exact output-board SHA and all surviving ordinary route UUIDs, including immutable ordinary objects. Use this artifact as `--logical-route-map` when preparing a later model from that imported PCB; a map for another board is rejected. Do not silently assume that later sources have no ordinary copper. The `.import.json` also retains the logical mapping and names the standalone artifact.
