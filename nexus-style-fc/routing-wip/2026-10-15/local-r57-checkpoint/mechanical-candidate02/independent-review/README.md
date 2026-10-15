# Independent Nexus header candidate review

Reviewed 2026-10-15, current files through approximately 05:40 UTC. This is a text/Python-only review of an explicitly unfinished mechanical candidate. No native KiCad, solver, browser, user computer, publication, fabrication export or candidate-file edit was performed. All review artifacts and redirected checker outputs are confined to this directory.

## Verdict

The candidate faithfully implements the studied nominal mechanical/contact redesign and preserves the required electrical identities and protected source objects. It is suitable as the **unfinished input to local routing repair and native validation**, not as a connected or manufacturing-ready board. There are definite retained-copper conflicts and contact disconnections. Native DRC/ERC/parity, refill, inspected assembly-model export, fixture definition and physical qualification remain mandatory.

Three review findings in the transaction/checker were corrected by the implementation owner during review. The hardened revisions have been independently rechecked, including negative tests. The native board hashes did not change.

## Exact source and candidate binding

- r54 main source SHA256: `5677fb38db7d7e19cd3afa9dd5da61bbd9932ed0be7f6f2899f7bf4bf58e8fc9`
- Child source SHA256: `99d06c7ec685f776f357958c22f684f198f9ef5bf7e9bed437833c9d6aadfba0`
- Main candidate SHA256: `5d67813b166901f6fa08da706db36867cf5855512fdb86d47fd28cd1f45cf1e9`
- Child candidate SHA256: `f89abf8e21697fc401f16f48ee3877dd8c4d9f1360b10f79412bbd692a6da19c`
- Candidate child schematic SHA256: `946c4006e8e481bd5d39f61956ce1c61feed1c75d8359751fff5f8ea4ee31fe9`

The current pure transaction replay reproduces both candidate boards byte-for-byte. Both `transaction-r54-01` and `transaction-r54-02-hardened` contain these same board bytes, with exact original rollback files. Every source hash matches the bound source. The hardened transaction's 13 implementation/library hashes match the current files. `native-review.json` additionally records all inspected candidate file hashes, including the current checker and generator.

## Verified mechanical and identity properties

- Actual main J1 native edges, not merely generator constants, form two closed, unbranched eight-edge components. Their local bounds are x 0.6–10.6 and 11.8–21.8, y 1.35–3.45. Each has four R0.5 corner arcs. Radius reconstructed from serialized midpoint coordinates is approximately 0.500001334 mm; the roughly 1.3 nm difference is serialization rounding, not a changed design radius.
- The actual child external contour is one closed, unbranched 18-edge component. Four native root semicircles have centers at local x 0.9, 10.3, 12.1 and 21.5, y 0, radius 0.5, and remove material to y −0.5. These are exterior-open contour reliefs, not detached holes.
- Tabs are 8.4 mm wide, 11.2 mm center pitch, and 2.6 mm insertion length. Body width remains 22.4 mm. Both board thickness records remain exactly 1.6 mm. The main outside contour is exact versus r54; the child connector J1 is entirely exact versus the source. Child top/body geometry is unchanged outside the intended bottom redesign.
- All 22 mating contacts match their library pad geometry, sizes, shapes and copper/mask layers. Main native cutout geometry also equals the library. The five generated footprint files equal in-memory output from the current generator. All child placements agree with `design_header.py`, including the mirror mapping and strip side/net assignments.
- Every connected pad's UUID, number and net remains exact. No duplicate UUIDs were found. Main has the same 88 footprints, 1,506 segments and 230 vias. Child has the same 12 footprints, 70 segments and three vias.
- All tracks/vias and all non-target footprints are unchanged. All untouched top-level board categories compare equal; both projects' rules and project files are byte-identical. Main schematic is byte-identical. Child schematic differs only by the two intended strip footprint identifiers. These checks establish identity/parity preservation, not electrical continuity after moving pads.
- Zone definitions are unchanged except for removal of cached fill data. All cached fills are absent, so an apparent absence of zone-copper conflicts is not a passing zone test.
- Nominal contact edge clearances and the bounded fit arithmetic agree with the prior study and rechecked static report. These remain nominal analytic values. No tolerance stack, load capacity or process guarantee is inferred.

## Definite repair requirements

### Main retained routes violate the new slot clearance

Three DSM_DATA segments on In2.Cu are only 0.2115 mm from the new slot, below the retained 0.30 mm rule:

- `28881ec4-4a2c-4ddc-bd8a-469fc5af5692`
- `82b2f45c-a273-4745-a603-f3901db1c9fc`
- `e0c1e805-0cbd-414b-a762-9ee36f017b06`

DSM_DATA was outside the original mating-net-only inventory. The owner has added its complete existing track/via inventory. Repair scope must be driven by final native checks on all affected copper, not just mating nets.

### Moved main pads overlap retained unrelated routes

The current candidate has five definite same-layer track/pad overlaps:

| Moved contact | Retained route net | Track UUID |
| --- | --- | --- |
| VX inner land | TAIL | `3c6b6b07-bc47-44c3-933e-dec9987cb0a7` |
| GND inner land | DSM_DATA | `d3b48651-8a36-4b7d-a8a5-e2cee42f9873` |
| TAIL | RPM | `ee61bafe-8cbe-43ca-a23d-07f5ea479c2d` |
| TAIL | ESC | `6bfcbf0d-0229-4f3c-8cc7-0dfebdd7b25d` |
| S2 | S3 | `62aa1890-1d51-5a51-a2ab-0a3e85e99c83` |

The same screen on the original source found none of these contact/track overlaps. Exact net identities were preserved, but retaining routes under shifted pads does not preserve electrical isolation.

### Child retained routes leave the revised outline and contacts

Six segments fail the nominal child outline screen across VX, GND, SBUS and S1, including copper extending outside the narrowed tab envelope. The detailed UUIDs and geometric witnesses are in `retained-copper-screen.json`.

Moved P1/S1 and P7/SBUS each have a 0.254 mm positive gap to the nearest same-net retained track or via in the candidate. The original-source contacts had no such gap. These contacts need reconnection. No zone fill currently exists to provide alternative copper connectivity.

### Screen limits

The copper screens are independent nominal geometric diagnostics, not native DRC. Track centerlines are sampled at intervals no larger than 0.002 mm. A sampled minimum is an upper bound on the true minimum, with at most approximately 0.001 mm sampling uncertainty for these continuous distance functions. The reported overlaps/clearance failures are well beyond that uncertainty. The child outline screen is limited to y ≥ 107.9 mm near the redesigned roots/tabs. No via conflicts were found in the bounded screen. Fills, full-board clearance, all footprint shapes, drilled-hole rules, annular rings, global connectivity, mask/process limits and thermal behavior are not certified by it.

## Review findings corrected and retested

1. **Assertions could be disabled by optimized Python.** The transaction now refuses `-O` and `-OO` before reading/writing task files. Independently compiled optimization levels 1 and 2 both terminate with the intended refusal. Modified main and child source anchors are also rejected in ordinary Python.
2. **Replay manifest did not bind implementation/library versions.** Fresh hardened replay now binds the transaction, geometry, anchors, parser, generators, pcbutil and five mating/connector footprint files. All 13 hashes match. Both replayed boards still equal the original mechanical candidate bytes.
3. **Static contour flags originally tested expected definitions only.** The checker now compares actual main native/library shapes and verifies two closed native components, plus the actual 18-edge child component and exact bottom shape/UUID mapping. Rerunning this checker with output redirected into this review directory passes. In-memory deletion of one actual main cutout edge and displacement of an actual child relief midpoint are each rejected.

The builder's new root arc method is now `SetArcGeometry`; the earlier `SetMid` use was corrected by the owner. This review did not execute that native API, so native generator loading remains a gate.

## Remaining gates and usage cautions

- The newly referenced assembled child WRL is intentionally absent. The old assembled model must not be relabeled as the new geometry. Export the new named model from the exact repaired/refilled/native-valid child and independently inspect seating, orientation, pad alignment, connector and root reliefs.
- Do not run `build_header_board.py` or `build_all.sh` over these routed source files as a validation shortcut. They regenerate boards; `build_all.sh` also includes fabrication exports. Use the source-bound transaction and explicitly controlled native repair/check/export steps.
- Refill and repair the complete affected copper while preserving unaffected routes, net/pin assignments and rule floors. Recheck zero opens, shorts/clearance, ERC and schematic parity on the exact final files.
- Define and verify the finished root/tab envelope, slot radius/dimensions, relative pitch/registration, board thickness/finish/bow and seating tolerances. The analytic positive fit margin does not establish practical assembly.
- A fixture/retention method, allowed copper-to-copper alignment, solder overlap/current qualification and connector-load/remaining-ligament acceptance remain unresolved. Native DRC cannot approve those physical requirements.
- Rebind final native/model artifacts and validation reports after any repair. No fabrication acceptance or authorization is provided by this report.

## Artifacts

- `native-review.json` and `review_native.py`: source/candidate hashes, actual contour/radius graphs, independent object comparisons, library and generator agreement, replay equality.
- `guard-review.json` and `recheck_hardening.py`: source/implementation binding, guarded negative tests, actual-native mutation rejection tests.
- `retained-copper-screen.json` and `screen_retained_copper.py`: nominal slot/root/tab clearance witnesses.
- `contact-routing-screen.json`, `original-contact-routing-screen.json` and `screen_contact_routing.py`: changed-pad route intersections and disconnection comparisons.
- `rechecked-static/`: current production analytic checker outputs, redirected away from the candidate during independent recheck.
