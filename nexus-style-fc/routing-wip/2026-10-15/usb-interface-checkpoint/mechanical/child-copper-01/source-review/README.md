# Child copper transaction: statically reviewed, unfinished

The proposed complete replacement of six B.Cu donor tracks with nine same-width segments corrects the six known edge-conflicting routes and reconnects S1/P1 and SBUS/P7 in static geometry. Independent review agrees. No PCB file has been edited or emitted by this proposal, and no native job has been run here.

## Results and limits

- All 22 physical pads of VX, GND, S1 and SBUS form one connected component per net without relying on zone fills.
- All six original external non-zone contacts survive: four retained upstream tracks and the existing T1/T2 land overlaps. No donor-to-via contacts existed. All three existing board vias remain untouched.
- Four terminal endpoints reach their pad centres with the entire original-width round end cap inside the land. Residual cap-to-pad-boundary margin is 0.55 mm for VX/GND and 0.50 mm for S1/SBUS.
- Minimum new-route clearances: Edge.Cuts 0.565218613 mm, foreign non-zone copper 0.258600000 mm, foreign plated drill 0.726000000 mm.
- Independent complete post-edit non-zone board screen: edge 0.254000000 mm, foreign copper 0.158240908 mm, foreign drill 0.318300000 mm. All 73 segment edges independently clear by at least 0.565218613 mm; the board-wide edge minimum belongs to retained pads at the 0.254 mm floor.
- These are nominal mathematical distances, not fabrication-tolerance, assembly-fit, solder-strength or material ratings.

**Native refill is mandatory.** Stored pre-edit B.Cu GND fill overlaps both proposed S1 segments and leaves only 0.058246 mm clearance to both proposed VX segments. Those are actual failures if the stored fills are retained. They are not accepted or waived by this static result. The old GND donor's same-net stored fill-island contact is retained, but connectivity proof does not depend on any fill.

## Exact binding

Source: `/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/mechanical-integration/initial-native/hardware/header-board/nexus-header-board.kicad_pcb`

Source SHA-256: `de56d5e4a066ff03a8c16d7e0501f45ca651ebf177c45ba12667488162010f38`

Initial native report: `nexus-recovery-20261015/mechanical-integration/initial-native/child-native-drc.json`

Report SHA-256: `d259df78652821cb7d43849c634d9bb6d03abeeb87208d104d93b0088c6fa290`

Transaction: `complete-transaction.json`, SHA-256 `0b130c0700b6adcbead837aaded342dc6d73d6f7301f4b9bbeeb1928c40dc6d9`.

Full four-net physical pad, segment and via inventory: `complete-net-inventory.json`, SHA-256 `05fd29db6b47d7479f47cee272744ad00f90dfff5bf36c324b458de6f20c11ff`.

The transaction contains each exact original native segment record and all nine replacement records. Six original UUIDs are retained; three deterministic UUIDs are added. Board segment count becomes 73 from 70. No pad, footprint, mask, outline, rule, schematic, via, net assignment, body or connector change is proposed. Candidate02 remains immutable. This proposal must not be overlaid onto an unverified newer child source by assuming its donors are unchanged.

## Complete replacement routes

Coordinates in mm, native board coordinates. Each arrow is one complete replacement segment. All are on B.Cu.

| Net | Original width | Complete polyline | Terminal |
|---|---:|---|---|
| VX | 0.50 | (113.5022,107.9983) → (113.654,108.1501) → (113.654,109.573) | T2.1 |
| S1 | 0.20 | (101.3,104.3017) → (102.254,105.2557) → (102.254,109.573) | P1.1 |
| SBUS | 0.20 | (121.1,103.3) → (120.3,104.1) → (120.3,109.573) → (120.146,109.573) | P7.1 |
| GND | 0.50 | (109.7,107.14) → (108.746,108.094) → (108.746,109.573) | T1.1 |

SBUS deliberately descends at x=120.3, then turns within P7. Descending at the relocated pad centre x=120.146 would violate clearance to the retained RPM vertical route; the proposed corridor leaves 0.2586 mm copper clearance.

| Net | Exact removed/replaced donor UUIDs | Retained upstream contact UUID |
|---|---|---|
| VX | `231b7cbd-70f5-429b-b94b-faef2b63c3af`, `ca788c04-a07c-422b-824f-dbeafc220a25` | `9b297fa4-a862-45ed-91d0-fb202dd3ab9b` |
| S1 | `1311c86b-1e8c-4833-8518-864755ff334c`, `a189ef97-eaa6-4497-8a33-d897ace91f54` | `ae55c203-0407-40db-b99e-b8b03ba44007` |
| SBUS | `66d19cc4-5711-4d71-8657-ceebbea5c7b9` | `dc40e5af-cf50-4658-b8e2-9cb48de8a057` |
| GND | `cbf85f81-7873-4ccf-8b3d-ddc0f3494041` | `b46a978f-a7c6-41f7-a829-bb2695caf596` |

The two added SBUS UUIDs are `6663f657-e200-5715-9735-24cf272a6353` and `cead2d63-fe15-51dc-8401-547242c1a0d8`; the added GND UUID is `6a072bfd-24cb-570a-9b36-3790ae596065`.

## Native integration handoff

1. Preserve an exact rollback and hash manifest of the child source and corresponding project/rule/schematic files in a new experimental directory. Verify the source SHA above and every donor's complete native record. If the source differs, stop and rebind/review; do not silently apply a stale proposal.
2. Replace exactly those six segment records with the nine exact replacement records from the transaction. Preserve all other native objects, including complete service/power/return paths and their external contacts. Verify 73 segments and three unchanged vias, no duplicate UUID, unchanged net/pad mapping, and unchanged body/connectors/rules.
3. Invalidate cached zone fills and refill with the approved KiCad runtime in the sole native lane. Do not evaluate retained stale fill as an accepted state. Preserve zone definitions, assignments, priorities and clearances; review the actual newly filled geometry and return continuity.
4. Run all-visible native child DRC and exact schematic parity/ERC with the unchanged header rules: 0.15 mm routing/clearance, 0.254 mm copper edge, and existing other manufacturing floors. The separately preserved main-board floors also remain unchanged. Require zero opens, shorts, edge violations and newly introduced manufacturing failures. Record precise remaining warning classifications.
5. Record the exact post-refill native source and report hashes. This proposal is eligible only for that native trial; it is not a fabrication-ready or strength-qualified release.

Do not regenerate/rebuild the child board during this transaction; doing so would discard its routed source. No generated model update is part of this copper proposal. Later exact integrated geometry and model checks still apply to the unfinished mechanical candidate.

## Warning transparency

Initial report has 12 track-edge errors, two opens, two dangling-track warnings, 11 missing-courtyard warnings and 11 footprint-filter warnings. The 12 edge errors bind exactly to the six donor UUIDs above. The two opens are S1/P1 and SBUS/P7.

The 11 entries under native `schematic_parity` are `footprint_filters_mismatch` warnings: embedded generic `Connector_Generic:Conn_01x01` filter `Connector*:*_1x??_*` does not match the custom tab-pad/strip names. They are not evidence of a changed pin/net mapping. These and the 11 bare-contact missing-courtyard warnings remain visible. No arbitrary courtyards, assembly-attribute flips, mask edits or filter waiver are included. A project-bound filter correction is deferred until the routed interface is stable.

## Evidence and reproduction

- `static-verification.json`: exact analytic line/arc/rectangle/circle clearance, component and external-port receipts.
- `supplemental-verification.json`: all 73 segment edge clearances, full-width terminal-cap margins, exact correspondence to the 12 initial native errors.
- `independent-child-review/REVIEW.txt` and `independent-review.json`: independent complete non-zone copper/edge/drill and original-contact checks, including stale-fill failure witnesses.
- `independent-child-review/arc-distance-crosscheck.json`: separate numerical bound check of all 54 new-segment/arc pairs.
- `child-routing-preview.png` and `.svg`: B.Cu-only nominal geometry, old donors and replacements; zone fills omitted. PNG visually inspected. The display's arc sampling is not used for acceptance distances.
- `PROPOSAL-SEAL.json`: every proposal artifact plus source/report/parser dependency hashes.

Read each Python script before execution. `build_proposal.py`, `verify_geometry.py` and `supplemental_checks.py` only read the source board and write JSON artifacts beside themselves. `draw_proposal.py` also writes the SVG/PNG preview. The independent verifier writes its report in its own directory. These scripts require normal Python with assertions enabled; never use `-O` or `-OO`. They do not apply the native transaction or run KiCad. All use the frozen candidate02 `tools/sexpr.py` parser. Native edits, refill and final checks belong to the routing owner.

For reproducible plotting, use writable cache paths such as `MPLCONFIGDIR=/tmp/nexus-child-mpl-cache XDG_CACHE_HOME=/tmp/nexus-child-font-cache`. No software installation was made. The SVG rasterizer was unavailable; the inspected PNG is drawn directly from the same native geometry with the existing Matplotlib runtime.
