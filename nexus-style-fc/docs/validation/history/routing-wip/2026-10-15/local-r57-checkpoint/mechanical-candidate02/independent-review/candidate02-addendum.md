# Independent addendum: candidate02

2026-10-15, approximately 05:46 UTC. The candidate01 review remains historical and unchanged. This addendum covers only the bounded candidate02 changes and their integration with the previously reviewed mechanical candidate. All work was lightweight text/Python on the dot cloud filesystem. No candidate files were edited and no native KiCad or solver was run.

## Verdict

**The bounded candidate02 delta passes independent static review. No new defect was identified in the inspected changes.** It preserves the studied geometry, pads, connector, copper identities and rule permissions while correcting J1's footprint attribute and restoring a consistent routed-slot keepout definition. It remains an unfinished routing/verification input: all candidate01 electrical conflicts and physical/native-validation gates still apply.

## Binding

- Main candidate02 SHA256: `40c4cdf78e7cb15a6ee5ed8219284f19e3a58b10686b0688daadd5f3d00c0689`
- Child SHA256, unchanged from candidate01: `f89abf8e21697fc401f16f48ee3877dd8c4d9f1360b10f79412bbd692a6da19c`
- Transaction: `transaction-r54-03-candidate02`
- All three source-manifest source hashes match the original source files.
- All **14** implementation/library bindings match candidate02, including `route_board.py`.
- Independent in-memory replay matches both candidate02 native boards exactly. The saved transaction also matches the main PCB, child PCB and child schematic byte-for-byte.
- Full inspected file hashes, source checks and the report/diagnostic hashes are in `candidate02-review.json` and `candidate02/native-review.json`.

## Exact allowed native delta

A normalized comparison proves that candidate02 differs from candidate01 only in:

1. Main J1's footprint attribute changes from `through_hole` to `smd`.
2. The polygons of the same two main slot keepouts expand vertically.

The child PCB is byte-identical. No copper track, via, pad, contact net/number/UUID, cutout/outline shape, model transform, non-J1 footprint, rule or other main-board object changed. Thus the geometric and electrical findings from candidate01 transfer to candidate02 without needing another copper sampling pass.

The native J1, library J1 and generated library output consistently use `smd`. All five generated footprints still equal their current generator output. Both boards' mating-pad/library and actual-contour checks pass. Shared dimensions in `make_footprints.py` resolve to the same prior nominal values, and all child generator placements still match the native board.

## Actual keepouts and permissions

The preserved UUIDs are:

- `c67f2612-ad61-4083-8c9a-72e3a887c688`, left keepout
- `79e1149d-aeb4-4aaf-8cd7-cf3a7ca09f8a`, right keepout

Measured native polygon bounds:

| Keepout | Source x | Candidate02 x | Source y | Candidate02 y |
| --- | --- | --- | --- | --- |
| Left | 100.1–111.1 | 100.1–111.1 | 101.2–103.6 | 101.05–103.75 |
| Right | 111.3–122.3 | 111.3–122.3 | 101.2–103.6 | 101.05–103.75 |

Each new polygon encloses the old polygon. Lateral bounds remain exact. Everything in each zone except its polygon is identical, including UUID, layer set, net metadata, settings and permissions. Both continue to cover F.Cu, B.Cu and In1–In4.Cu; tracks and vias remain prohibited, while pads, copper pours and footprints remain allowed. No permission was relaxed.

The strengthened source guard binds exactly both keepout UUIDs and their complete original native records. Independent in-memory negative tests reject an altered source boundary and a relaxed source track permission, even when testing the modified native records directly. The earlier optimized-Python refusal remains in place.

The general candidate02 native comparison's `zones_only_cached_fill_removed: false` is expected: that older diagnostic intentionally does not whitelist the newly authorized keepout polygon expansion. `candidate02/delta-review.json` separately proves the exact two permitted polygon changes and unchanged remaining zone fields.

## Routing-generator update

Static inspection confirms that `joint_copper` no longer depends on discovering NPTH pads for slot extents. It constructs the two routed-slot bounding boxes from the J1 origin and the shared slot centers/length/width. It rejects a rotated or back-side J1 before creating any items. The intended current main J1 satisfies those assumptions.

For an independent arithmetic check, I extracted only `joint_copper` and executed it with small Python data stubs using the actual candidate02 pad rectangles. This did not import or execute KiCad. The calculation produces:

- Two keepout polygons exactly equal to the candidate02 native polygons
- The same intended all-copper track/via prohibition and unchanged other permissions
- Eight fixed vias and twelve fixed VX/GND link segments under the existing helper's topology
- Rejection of rotated and back-side J1 inputs before adding any item

This establishes the current coordinate/permission calculation and catches the removed-NPTH dependency. It does **not** establish SWIG/native constructor behavior, native bounding-box conventions, actual route legality, connectivity, process suitability of vias in these contacts, or autorouter behavior. The native API and route results remain unexecuted and must be validated in the controlled native lane. The helper is a board-generation path, not a safe general reroute operation on an existing routed candidate.

## Unchanged blocking findings

Candidate02 has identical copper and contact/cutout geometry to candidate01, so these known repair needs remain:

- Three retained DSM_DATA segments at 0.2115 mm nominal slot clearance, below 0.30 mm
- Five cross-net overlaps between moved main pads and retained routes
- Six child retained-route/root-or-tab conflicts
- Child P1/S1 and P7/SBUS contacts separated from their retained same-net copper by 0.254 mm

The deliberately absent new assembled WRL, all zone refills, native DRC/ERC/parity/zero-opens checks, finished-fit tolerance stack, fixture alignment, solder/current and mechanical qualification also remain unresolved. This addendum provides no fabrication approval.

## Evidence

- `candidate02/delta-review.json`: exact native delta, keepout bounds/permissions, negative guard tests and all transaction bindings
- `candidate02/native-review.json`: full candidate02 source/native/library/generator/replay comparisons and file hashes
- `candidate02/route-math-review.json`: arithmetic-only routing-helper execution and orientation/side negative tests
- Associated Python scripts in `candidate02/` reproduce those read-only checks
