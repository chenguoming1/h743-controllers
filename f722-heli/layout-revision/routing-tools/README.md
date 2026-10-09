# F722 ordinary routing: V9 checkpoint55

Owner-adopted candidate28 is an unfinished geometric checkpoint: 55 open connections, zero native DRC errors/warnings and strict schematic parity zero. PCB SHA-256: `3afc574bdd766292932323c54fd198cc2cb88ab93617a434fe5d104ab01838d2`. Power/VCAP numerical applicability remains false. Routing, numerical revalidation and final electrical/physical qualification are incomplete; this is not fabrication-ready.

Candidate27 is the validated intermediate from exact candidate26. The actual `model-candidate26-ready/filtered02.successes/final` SES/report pair adds six NRST tracks and one through-via, reducing 57 to 56 opens. R1.2 reaches the existing U1.7/C10.1 group; TP5.1 remains open. Full-width pad, new-annulus and preserved-existing-via entry receipts pass. Saved GND reference fills changed, so older numerical power/VCAP passes cannot be inherited.

Candidate28 explicitly constructs three F.Cu PORT_B_RX_EXT::P2 tracks after a real stock insertion refusal against USER_FIXED P1. The source26 proposal is retained along with its additive-current-native recheck on27 and exact prepared-on27 construction packet. This is not an engine insertion success. It adds no further via or refill and preserves 27's saved power/fill/drill geometry, whose numerical status was already stale.

PORT_B_RX_EXT is physically complete. The actual bonded U14.4 cut J10.1→R32.1 passes with 0.3275132250445282mm outside-pad gap and zero overlap. Actual bonded I/O coverage is 7/22; 14/51 ordinary physical nets are fully connected. Shared-pad departure is explicitly audited in addition to degree-one endpoint checks. The owner comparison preserves critical copper and reports zero lost-GND overlap beneath critical trace widths; this is geometry evidence, not signal-integrity or numerical power qualification.

Candidate28's owner adoption covers the cumulative26→28 change. Candidate27 has no separate owner-adoption receipt. Original handoffs keep their historical pending statuses; later owner receipts are bound separately. `checks/v9-historical-receipt-status.json` records any overwritten receipt identity without claiming unavailable bytes.

Fresh source28 zero import is byte-identical. Five immutable explicit IDs protect the two previous in-pad extensions and three new P2 segments. The unfinished source28 filtered03 routing run and all later candidates are excluded. The small shared-pad predicate risk review is a bounded negative finding: relaxing only two checks could expose a downstream mutation of a fixed trace. No live Java source changed, and no unsafe predicate implementation is included.

## Package and verification scope

V9 is a changed-files-only delta from immutable V8, manifest SHA-256 `13f0fa03eaf62d3ae16635109877499976843e7289f97372cb4e2143cdd180e6`; the V8 delta ZIP is `5566e05ad8e58e9bdaad815bcf066db6883a33f685066a6af4aed4eff298e96b`. All historical recovery controls remain present. Two compact new packets preserve the real 27 engine history and separate 28 native construction. Exact byte-copy deltas recover27 and28 from pinned 26, itself recovered with V8 from the 62-file candidate22 paired source.

Portable checks verify complete manifests, exact paired recovery, SES/report parser agreement, importer projection rebinding, historical receipt hashes, selected insertion/refusal provenance, immutable explicit IDs, and negative controls. Packaging executes no JVM, native import, DRC, endpoint geometry audit, refill, numerical solve or route search. No full PCB, full native export, full routing model, binary or unrelated failed-search dump is bundled. See `REPRODUCE.md`.

## Inherited V8 documentation (historical only)

Everything below describes earlier checkpoints and remains for compatibility. Current status is the V9 section above; older acceptance and numerical statements do not qualify28.

# F722 ordinary routing: V8 checkpoint57

Adopted candidate26 is the V8 geometric checkpoint: 57 open connections, zero native DRC errors/warnings and strict schematic parity zero. PCB SHA-256: `697555207280b8d67714a0011a51ec355321f21f551d6a1486a786c38a671949`. Routing and electrical/physical qualification remain incomplete; this is not fabrication-ready.

Candidate26 adds six tracks and one through-via to candidate25, retaining all 1,688 source objects. The ESC_MCU::P0 branch reaches bonded clamp U13.3, while ESC_MCU::P1 to U1.58 remains open. Native refill changes the two inner GND fills. **Previous power/VCAP numerical acceptance is stale for candidate26.** Source24 is the last fully job-bound numerical checkpoint; source25 preserves its exact power domains/fills/drills/circuit but has no new complete numerical compilation. Candidate26 requires new power/VCAP validation.

The critical-reference comparison reports unchanged critical copper and projection metrics, with zero lost-GND overlap under critical trace widths. Nearest measured lost-GND distances are 5.629 mm for USB_P/In1.Cu and 3.570 mm for HSE_IN/In4.Cu. These geometric findings do not replace a loaded numerical or signal-integrity qualification.

## Separate route histories

- Candidate23 contains the stock engine's two successful connections from source22: 14 tracks, no vias. Its endpoint audit refuses two narrow entries, Q1.2/RPM_LV and R26.2/SBUS_HV. That raw refusal remains included.
- Candidate24 explicitly adds two in-pad entry tracks to candidate23, retains all engine copper, passes all four full-width entries, and reaches 60 opens. These completions are not engine insertions. Both are fixed in the subsequent source24 and source26 model controls.
- Candidate25 imports only `filtered01.successes/second`: ten outer tracks, no vias, all four endpoint entries pass, 58 opens. SBUS_LV and PORT_A_RX_MCU become fully connected, taking ordinary fully connected physical nets to 13.
- Candidate26 separately uses `filtered01.successes/final`, the third successful connection. The actual source24 session is rebound to exact additive candidate25 without a new engine run. It adds six tracks and one via, passes two full-width pad entries and two actual annular strips, and reaches 57 opens. One redundant via-centered spur is retained as original engine geometry and excluded from endpoint evidence.

`checks/candidate25-owner-adoption.json` and `checks/candidate26-owner-adoption.json` are later owner decisions. Historical handoffs retain their original pending statuses. `checks/v8-historical-receipt-status.json` identifies three candidate25 DRC receipts whose earlier bytes were overwritten by owner reruns; original hashes remain in the handoff and fresh owner receipts are separately bound. This package does not claim those overwritten bytes are available.

## Portable coverage

Three compact session packets preserve distinct selected histories: `sessions/engine60-refused23`, `sessions/accepted58` and `sessions/accepted57`. Their full original report/model hashes are retained beside compact importer projections. Real boards, full native exports, routing models, fixed guard arrays, binaries and every unsuccessful search are excluded. Unfinished filtered02 and later routing work are outside V8.

`tests/verify_v8_evidence.py` passes five exact recoveries (candidates22–26, 62 functional paired files each), three SES/report parser and importer-projection checks, and 15 wrong-source/tamper/recovery rejection controls. Historical projection values were compared with the original inputs. No JVM, native import replay, new endpoint geometry audit, refill, DRC or numerical solve was executed by V8 packaging. Historical native acceptance evidence is retained and source-bound; byte recovery is not a new native replay.

The mechanical target is the exact trial27 pose receipt, SHA-256 `9c84633da6de3d501d7ca258bcf4a8051b965af728929f8cd7587e20f73e2bae`. Candidate25's initial generic obsolete-pose failure remains recorded; its corrected worker result and fresh owner result both pass against this target. Fresh source26 zero import is byte-identical and zero parity reports no errors.

Historical protection counts remain 2/18 routing-pad cuts, 5/7 supplemental cuts and 6/22 actual bonded I/O cuts; these do not establish complete protected ports. Fifty-seven opens, full protected-path contracts, loaded power revalidation and final board review remain outstanding.

The changed-files-only archive applies to the complete immutable V7 source package with manifest SHA-256 `c1c30c9e18658abef883d0b201b8233f135d7643574536637523cb633e1052d0`. See `REPRODUCE.md` for exact recovery, controls and optional native replay commands.

## Inherited V7 documentation (historical only)

Everything below documents the earlier V7 checkpoint and compatibility workflows. Its numerical applicability does not qualify candidate26.

# F722 ordinary-routing reconstruction

Local-only adapter for the new F722 placement. This is a planning/import pipeline, not a fabrication-ready PCB. The parent coordinates the single heavy-process slot and the fixed power/critical support handoff. Never run nonzero passes on the bare placement model.

## Current routing checkpoint

Adopted candidate22 has 62 open connections and zero native DRC errors/warnings, PCB SHA-256 `fd8fd21062c61992ec992481d394e19a6a99cfe8ec58405ed1e391c5e3836bfa`. It is unfinished and not fabrication-ready. The owner adopted candidate19–22 after the exact modeled power/contact/job applicability check passed. The 62 required conditional voltage cases, five VCAP DC copper-loop checks and numerical gates pass; the unchanged overall runner boolean remains false because an outside-envelope 18.56 A single-feed illustration fails four servo floors. This is conditional fixed-temperature DC evidence, not thermal, startup, switching, protection, production or flight qualification. Broader source/circuit corners and final routed-board review remain incomplete.

Candidate19 is the coordinated power correction from historical candidate16/old69. It removes 23 approved objects, adds 93 power tracks and one via, preserves 1,559 other source objects and all prior ordinary logical ownership, and regenerates reference fills. The original BEC parallel copper remains included in the separate numerical model. The loaded result applies exactly to candidate22 under `checks/candidate22-power-result-applicability.json`; numerical sources/results are maintained in the separate power-owned v6 package.

Candidate20 adds four explicit native P1 bridges and reaches 65 opens. Candidate21 adds two explicit local connections, SBUS_LV and RPM_MCU::P0, and reaches 63. Candidate22 builds three PORT_B_RX_EXT::P0 segments from the stock engine's located path after insertion failed at a shared logical pad. All these routes are explicit native construction; none is a successful engine insertion. Candidate20–22 add no vias and preserve every source object, saved fill and power/drill geometry without refill.

The historical original protection checker reports 2/18 routing-pad cuts, with supplemental 5/7. The new count is an NC U14.7 routing-pad dependency. It does not establish protection at the actual bonded U14.4 I/O or a complete protected port. U14.4→R32.1 remains unfinished. Native clearance outside the legitimate shared pad remains mandatory.

All three compact packets have been replayed through the actual KiCad importer on exact recovered source projects. Their geometry matches the accepted candidates except newly generated route UUIDs; prior logical ownership, fixed copper, footprints, outline, layers and saved fills remain exact. No JVM, refill, new DRC or numerical solve ran during packaging. Power construction/refill itself was not reexecuted; its original source-bound acceptance receipts and operational inputs are retained.

The bounded source21 run exits cooperatively with zero new geometry. A 100-second request completed in 129.086 seconds because the active connection and verified output may finish. This is not a hard wall-time guarantee. The generic located-path preparer has one passing reproduction and three rejection controls; historical receipts retain their original model/source hashes. Both tiny final-queue controls inherited from v6 remain synthetic lifecycle proofs only.

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

## Source-only v7 package

Base is immutable v6 manifest `522a25eb21b66a1155f147411e95af79a1727b9915877ebce3693483651efbff`, ZIP `88d6c4b73b68c28d87bbd7a5a491252fbf0bb7a160ceebabb6c8e387764d0f79`. The delta contains changed files only, a complete allowlist and full hash manifest. Boards, real full routing models/native exports, large polygon witnesses, classes/JARs and caches are excluded. The four inherited tiny synthetic fixture files are test data only.

`sessions/recovery62` recovers exact candidate16/19/20/21 paired projects from the adopted62 project. All 62 paired files are identical; compact PCB deltas bind full base and target hashes. No unpublished Git commit or remote availability is assumed. Recovery through candidate16 also feeds the inherited recovery69 chain.

`sessions/accepted65`, `accepted63` and `accepted62` retain exact sessions/reports, portable importer projections and compact proposal inputs. `checks/v7-portable-projections.json` distinguishes original bytes from path/field projections; historical dependency hashes are preserved, and replay identities bind the actual portable files. Java/importer bytes are unchanged from v6. Later trials are excluded. See `SOURCE_EVIDENCE.md` and `REPRODUCE.md`.
