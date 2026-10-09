# F722 ordinary-routing reconstruction

Local-only adapter for the new F722 placement. This is a planning/import pipeline, not a fabrication-ready PCB. The parent coordinates the single heavy-process slot and the fixed power/critical support handoff. Never run nonzero passes on the bare placement model.

## Current routing checkpoint

Adopted candidate16 has 69 open connections and zero native DRC errors/warnings, PCB SHA-256 `9cf04c88ebd31d7e2c12bdb8a9f80e01b615a7bdb94a73fc2234208a2e0a14c8`. Eleven of 51 ordinary physical nets are complete; all 28 support nets remain connected. Original protection remains 1/18 and supplemental protection 5/7. The loaded-power screen identifies an unresolved BEC copper deficit. Native geometric/connectivity checks do not clear that electrical problem. This is unfinished and not fabrication-ready; power experiments are excluded from this checkpoint.

Candidate15 is real engine routing from adopted75, stopped cooperatively at five successes with eleven queue items remaining. It adds nineteen tracks and two vias, reduces opens to 70, and completes ADC_BEC. NRST and BOOT0 have useful partial connections but remain incomplete. Final output equals the verified checkpoint and all fixed geometry is preserved. This run did not exercise final-empty-queue stopping.

Candidate16 explicitly constructs a same-face ADC_BUS connection from R42.2 to R43.1 using two F.Cu tracks and no vias. C31.1 and U1.10 remain separate, so ADC_BUS is not complete. All 1,580 source pad/copper objects, existing drill geometry, In1/In4 copper, zone designs and saved fills are exact. No reference refill was requested or needed. The minimum foreign-copper gap is 0.498956 mm, nominal geometry only. This is native construction, not engine insertion.

Both tiny final-queue controls pass on the unchanged production adapter: each routes one connection, naturally exhausts queue 2→1→0 below the five-success threshold, and observes the actual initial stop flag change in the production listener. One forces a final geometry write and the other reuses a saved snapshot. Fixed contacts/guards/track/via geometry and final SES equality pass, as do missing-guard and shifted-endpoint negative controls. These are synthetic lifecycle proofs; they are not a native full-board or loaded-power test.

The accepted69 portable packet has also been replayed through the actual KiCad native importer on an exact recovered70 paired project. Its geometry matches adopted69 except the two generated route UUIDs; prior 67 ordinary UUIDs/nets and all saved reference geometry remain exact. No refill, JVM, new DRC or loaded solve was run for that replay. The accepted70 refill replay was not rerun. Source69 model preparation/zero and future routing are not included as validated evidence.

The corrected contact adapter separates physical ownership from logical connectivity. Contact-only polygons do not obstruct duplicate aliases during stock insertion; every contact has a same-layer owner-aware copper guard proven to cover its complete native copper. Both logical branches can insert into the shared-pad control, a foreign signal is rejected, and outside-pad branch separation is retained. Static native peers use one shared immutable list per group; live trace contacts are still recomputed. Full-board serialization preserves every native contact partition and binds every copied peer to the copied board. Copy IDs and stale peer replacement/removal are checked.

## Source and ownership

- Official Freerouting 2.1.0 release JAR and tagged source are pinned in `vendor/provenance.json`; Eclipse ECJ is from Maven Central.
- The local driver calls the engine directly, never the upstream GUI/API scheduler. It sets documented `usage_and_diagnostic_data.disable_analytics=true`, API server disabled, and GUI disabled before loading any board. No analytics client is initialized, no remote route service is used.
- The shared native exporter lives in `native-tools/export_native_copper.py` (mirrored from the canonical revision scripts). It records native UUIDs, pad shapes and masks on all actual layers, drill capsules, plated spans, footprint poses/side, rule zones and filled polygons with holes.
- `prepare_model.py` derives ordinary nets from every native terminal, excludes explicit power ownership and critical support domains, and includes full flash SPI, barometer I2C and ordinary GPIO/ADC/UART nets. Explicit power ownership is in `config/power-owned-nets.json`.
- Ordinary routing scope: 51 physical ordinary nets, 70 logical branches. Canonical U14 connector → NC → actual IO → series-resistor paths remain intact. U13 uses current reviewed channels ESC3/RPM6/SBUS1. U16 HV paths receive actual-pad branch constraints as well.

## Physical and planning geometry

The exact 1 nm native physical export is independently hashed and retained. Freerouting's safe board scale is 10 nm; its polygon implementation does not accept fractional coordinates. Planning guards therefore conservatively cover source geometry using a 20 nm outward allowance and 10 nm grid. Pad contacts are inset by 20 nm before gridding and remain inside native ERROR_INSIDE pad copper. This is an explicitly checked containment contract, not a claim that rounded planning shapes are identical to native copper.

The separate import gate requires exact native geometry and identity, including all UUID-distinct repeated pad numbers, complete layer sets, side and poses. The historical bare-placement zero control at `checks/baseline-zero-parity.json` passes all 526 native contact partitions and all 1,984 model area keys. Its zero SES was independently parsed and imported through native objects; the resulting PCB reproduced the source SHA exactly. A byte copy is not used.

Native pad-only static contact groups are established from physical native copper, including real plated barrels. Mutable routing is never used to manufacture virtual connectivity. The Java contact class recomputes intersections using the actual current trace capsules; the regression test checks off-centre contact, symmetric adjacency, logical isolation and stale-contact removal.

Logical branches share only proven physical pad contact windows. Distinct branch traces retain full mutual clearance. No broad physical-net alias merging or arbitrary four-via/length limit is permitted. `checks/shared-pad-seam-control.json` explicitly records that overlapping logical trace copper entirely within U14.4 is conservatively rejected, while outside-pad overlap is correctly forbidden. This is a known limitation, not evidence of physical impossibility. Conservative branch clearance may make an escape unroutable; it does not authorize a shunt bypass. The independent physical pad-cut checker is the completion gate.

## Manufacturing constraints

Six layers maximum; only F.Cu, In2.Cu, In3.Cu and B.Cu carry ordinary routes. In1/In4 are GND reference layers. Ordinary width/clearance is 0.127 mm; through vias are 0.45/0.20 mm and explicitly tented on both faces. Every SMT mask opening on both faces excludes via drills by 0.20 mm, regardless of net. Drill-to-drill gap is 0.25 mm and board-edge/NPTH clearance is 0.254 mm. No new filled/capped signal-via process is introduced.

Mask via guards include 0.075 mm beyond mask copper because the engine measures against 0.225 mm via copper radius: 0.075 + 0.225 − 0.100 = 0.200 mm drill gap. Existing hole guards add 0.125 mm for the analogous 0.25 mm hole gap. Guard clearance class 0 adds no hidden default clearance; ordinary foreign-copper guards use class 1.

## Commands

Use Python 3 with `requirements.txt` installed for model building and independent geometry checks. Set `KICAD_PY` to a verified KiCad 10 Python interpreter for native export/import.

1. Export the agreed combined support board with `export_native_copper.py --board BOARD --out NATIVE.json`.
2. Build a fresh model with `prepare_model.py --native NATIVE.json --board BOARD --out MODEL_DIR`. Set `--support-ready` only after the fixed-support handoff and parent approval. The launcher rejects nonzero passes unless that exact model has a passing `zero-parity.json`. An existing protected ordinary route requires `--logical-route-map`; explicit immutable ordinary objects may be supplied with `--fixed-ids`.
3. Compile with `./compile.sh`.
4. With the heavy slot, run `./run_local.sh MODEL_DIR OUTPUT_PREFIX 0` for the finite zero-route control.
5. Import the actual session: `import_session.py --model MODEL_DIR/model.json --session OUTPUT_PREFIX.ses --engine-report OUTPUT_PREFIX.after.json --out ZERO.kicad_pcb`.
6. Verify: `verify_zero.py --model MODEL_DIR/model.json --engine OUTPUT_PREFIX.after.json --imported ZERO.import.json --out MODEL_DIR/zero-parity.json`. The final location is required by the nonzero-pass launch gate.
7. After support, zero controls and the parent launch gate pass, routing uses the same command with an approved pass budget. Route outputs remain isolated until native DRC, schematic parity, protection cuts, DFM and full-net timing/reference checks pass.

No routing result by itself establishes reference continuity, signal timing, power integrity, ESD immunity, or assembly qualification. Those are separate completion gates.

## Integrated-support controls and reference planes

The frozen trial03 support source passes a fresh, support-not-ready zero control: 51 physical ordinary nets, 70 logical branches, 4,185 engine area keys and 306 native contact partitions. Native zero import preserves all 1,109 source objects and 156 footprints and reproduces the original PCB SHA. These trial03 results are historical support controls; the later trial27 SWCLK route is documented above.

Saved KiCad GND fills can encode holes using exact zero-width bridge edges. `native-tools/exact_native_contours.py` removes only reversed integer edge pairs and reconstructs unambiguous cycles. It preserves every surviving boundary edge, coordinate and integer signed area, and rejects ambiguous touching topology. The trial03 planes each recover 53 holes with zero coordinate displacement. Raw native input and compact receipts are retained independently; no GEOS repair is used.

Only filled GND reference zones wholly on In1/In4 are regenerable. Their old fill areas are omitted from planning obstacles so ordinary through-vias can receive new antipads. Static pads/tracks/vias, every mask/drill guard, rule areas and all other filled zones remain obstacles under their existing rules. In1/In4 stay disabled for ordinary signal tracks.

Seven direct engine checks prove legal through-vias at three empty reference-plane points and rejection at a foreign pad, fixed track, existing drill and same-net SMT mask. A separate signal-via/stub importer fixture tests actual saved antipads: each plane gains one hole, the gap is 0.1274991308 mm, and the complete native GND pad partition stays connected and unchanged. A deliberately stale-fill fixture fails both reference-layer clearance checks. These are isolated controls, not routing candidates.

For route imports the destination PCB/project pair is saved and reopened before native refill. Every new ordinary object's physical net is checked before save, after reload, after refill and in the final export. Exact fixed native objects and zone identity/outlines/rules remain mandatory; regenerated GND fill is explicitly reported as changed. Final saved-fill clearance, full GND connectivity, reference/current checks and loaded native DRC remain required.

Every import now writes `OUTPUT.logical-route-map.json` with its exact output-board SHA and all surviving ordinary route UUIDs, including immutable ordinary objects. Use this artifact as `--logical-route-map` when preparing a later model from that imported PCB; a map for another board is rejected. Do not silently assume that later sources have no ordinary copper. The `.import.json` also retains the logical mapping and names the standalone artifact.

## Observable bounded routing

`F722_CONNECTION_BUDGET_MS` bounds engine initialization plus maze search (default 10,000 ms); the initial search-tree setup consumes that same budget. Statistics and verified serialization are outside the budget and timed separately. `F722_ONLY_NETS` optionally selects comma-separated physical ordinary nets for a focused search without removing any physical guards. `F722_CHECKPOINT_AFTER_ROUTED` requests a cooperative stop after a selected number of successful connections; it is a search budget, not an electrical constraint.

Progress includes net/contact identity, result, per-stage timing and actual counters on every attempt. Full geometry snapshots use two alternating atomic slots, normally every three successful connections or 60 seconds, and on cooperative stop. `F722_CHECKPOINT_EVERY_ROUTED` adjusts that cadence. A progress record with `pending_route_geometry=true` explicitly points to the last verified recoverable geometry while reporting newer live counters. Unchanged attempts reuse the previous session. Only geometry writes advance the slot selector, so deferred events cannot overwrite the current published pair. Create `OUTPUT_PREFIX.stop` for a graceful stop. The final `.after.json`/`.ses` is also written and checked; forced termination can recover only the last completed snapshot.

Checkpoint SES output does not remove contacts from the active model. Fixed objects, routes and contact partitions are fingerprinted around verified saves. Graceful stopping skips end-of-pass tail cleanup and rounded-score BoardHistory rollback, preserving the successful checkpoint. Native acceptance remains a separate gate.

## Continuation and signal review

Every accepted output includes a separate board-bound logical-route-map artifact. A new model of an actual partial route must consume it; an empty ordinary-copper assumption is not reusable. Source UUIDs whose geometry is retained survive import. Intended physical nets are asserted before save, after reload, after native refill and in the final native export. Reference-plane refill is followed by saved GND-clearance and full reference/connectivity checks.

The barometer I2C review target is at most 50 pF estimated loading and 100 ns edges, without firmware changes. `analyze_candidate.py` reports native lengths, layers and vias as inputs to that later electrical review; connectivity or geometric length alone does not prove the loading/edge targets.

## Source-only v6 package

This delta uses corrected immutable v5 manifest `02791deae14ce18c6d8b678cb63e3be43d4f383dbc2bc2b2f820e8468f49a0ac`, ZIP `9d6f368c740fa6ce4df36eb9636f155c79eb5937e13f5d622a749c1eae4e2832`. It includes changed files only, with a complete staging allowlist and hash manifest. Full boards, real models/native exports, large witness arrays, JVM binaries and Python caches are excluded. The four explicitly allowlisted tiny synthetic fixture files are test data only.

`sessions/accepted70` retains the real broad session/report; `sessions/accepted69` retains explicit ADC_BUS construction and importer projection. `sessions/recovery69` recovers exact source75/source70 paired projects from the proposed published69 hardware project. Authority is the full69 PCB hash and paired-file manifest, not an assumed remote commit. Both complete 63-file recovery controls and rejection controls pass.

All packaged paths are portable. Source-bound historical hashes remain distinct from path-projected copies; `checks/v6-portable-projections.json` records each mapping. The Java adapter is byte-identical to v5 and to the actual broad-run/tiny-control source. No active power-correction experiment or later route is included. See `SOURCE_EVIDENCE.md` and `REPRODUCE.md` for the exact evidence boundaries.
