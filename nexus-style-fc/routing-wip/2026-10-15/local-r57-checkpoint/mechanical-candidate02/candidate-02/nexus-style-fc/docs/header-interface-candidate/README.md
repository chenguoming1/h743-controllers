# Nexus root-aware header interface, candidate 02

**UNFINISHED. Do not fabricate or assemble from this candidate.** This is an isolated mechanical transaction and dimensioned study on the dot cloud computer. It is not the accepted copper branch or a manufacturing release. No native KiCad job, router, solver, fabrication export/order or physical test was performed by this implementation lane.

## Result and source binding

Two real 10.0 × 2.1 mm R0.5 routed main-board cutout contours replace the former oval NPTH drill pads. The child has two 8.4 mm × 2.6 mm tabs with four real upper R0.5 root-relief semicircles connected to the outer contour. The 22.4 mm body width, upper outline, 11.2 mm mating pitch, board thickness, connector position/orientation and every connected pin/net assignment are preserved.

All seven signal lands retain 1.2 mm width and both individual power lands retain 1.6 mm width. Main and child mating lands move together. Child outer strips are explicitly named W7.892 and are 7.892 × 2.346 mm. Main outer strips remain 9.8 mm long and become 0.65 mm deep. Main inner lands are 0.85 mm deep. Nothing is silently cropped to a fractional signal/power width.

- Source main: r54 `5677fb38db7d7e19cd3afa9dd5da61bbd9932ed0be7f6f2899f7bf4bf58e8fc9`
- Candidate main: `40c4cdf78e7cb15a6ee5ed8219284f19e3a58b10686b0688daadd5f3d00c0689`
- Source child: `99d06c7ec685f776f357958c22f684f198f9ef5bf7e9bed437833c9d6aadfba0`
- Candidate child: `f89abf8e21697fc401f16f48ee3877dd8c4d9f1360b10f79412bbd692a6da19c`
- Main schematic remains byte-exact: `49f9e0571424d0610e294bdcd6b120a42d04db284ecda9e660428fc587e62699`
- Header schematic changes only two footprint-identifier strings, K1/K2 `ChildBoard_TabStrip_W9.8` → `ChildBoard_TabStrip_W7.892`. Every other byte, pin, wire, symbol identity and net is unchanged. Exact native parity still must be run.

Source files were reconstructed from the verified current-main binding with the accepted r54 board and checkpoint10 pcbutil override. The original files and exact model sources are retained in the root package's rollback directories. Canonical main copper was not replaced.

## Exact changes and invariants

The transaction retains all connected pad UUIDs, footprints' UUIDs and all unchanged board-edge UUIDs. Existing tracks, vias, setup, board thickness and all non-interface footprints are unchanged. Main J1's footprint type becomes SMD because its eleven electrical contacts are SMD; the routed cutouts are mechanical Edge.Cuts. The actual 3×7 connector remains through-hole and is unchanged.

The two all-layer slot keepouts retain their original, stricter x intervals, 100.1–111.1 and 111.3–122.3 mm in native coordinates. Their y bounds expand from 101.2–103.6 to 101.05–103.75. Track/via prohibition and all other permissions are unchanged. This adds the missing 0.30 mm vertical envelope around the enlarged slots, with no rule waiver. The routing generator now uses routed-slot bounds rather than searching for removed oval drill pads.

Main 0.127 mm width/clearance and 0.30 mm edge floors, and header 0.15 mm width/clearance and 0.254 mm edge floors remain unchanged. All zone-fill caches are removed because old filled polygons are invalid after the geometry change. Zone source polygons, connections and settings are retained, except the two explicitly described keepout contours.

The main schematic's inherited generic J1 footprint filter still says `Connector*:*_1x??_*`, which does not match the custom joint. J1 is the sole instance of embedded `Connector_Generic:Conn_01x09`. A separately reviewed metadata-only correction could allow `NexusFC:HeaderBoard_Joint` in that symbol and the schematic-generation path. This package does not change the main schematic to suppress that advisory.

## Static checks actually performed

`static-validation.json` records source hashes, all 22 actual mating-pad boxes, pad-to-slot/outline/root distances, contact overlaps and the assumptions used below.

- Actual native main contours: two closed components, eight elements each; four R0.5 corners per slot. Native contour coordinates agree with the generated footprint/shared definition.
- Actual native child: one closed 18-edge contour; four actual root-relief arcs match the shared definition. Existing upper body and connector remain exact.
- Actual native and generated mating pad geometry agrees, with six-decimal-mm placement precision. All connected pad UUID/net/number identities remain exact.
- All 11 main mating lands have at least 0.350 mm nominal slot spacing. All 11 child contacts have at least 0.254 mm nominal tab-edge/root-relief spacing.
- Independent read-only review found the same contour/body/contact invariants. Its separate electrical screens also identified the expected retained-copper problems listed below.
- Seven source-bound transaction tests pass: exact fresh replay, existing-output refusal, wrong-hash refusal before writing, changed-J1 anchor refusal, changed-keepout anchor refusal, explicit refusal of optimized Python, and matching implementation/source manifest.

These are native-text and analytic checks. They do not establish native DRC, absence of shorts/opens, electrical parity, accepted process tolerances, real mating fit or strength.

## Nominal and assumed tolerance-envelope collision screen

Coordinates below are local main-board coordinates. Slot bounds are x=0.6–10.6 and 11.8–21.8, y=1.35–3.45. Child tabs are x=1.4–9.8 and 12.6–21.0, y=0–2.6. Four relief centres are (0.9,0), (10.3,0), (12.1,0), (21.5,0), with R0.5. The tab-width specification must bound the entire finished insertion envelope, including its relieved root transitions.

The analytic cross-section uses a rigid, centred, perpendicular tab. It accounts for the slot's circular corners; simply comparing full slot length with tab width would be wrong.

- Nominal 10.0 × 2.1 slot, 8.4 tab, 1.6 thickness, R0.5: total x play 1.466025; y play 0.500.
- Adverse study sizes, slot 9.8 × 1.9, entire tab width 8.6, thickness 1.76, R0.5: x play 0.710294; y play 0.140.
- Add an illustrative 0.40 mm slot/tab-pair pitch mismatch: remaining total x budget 0.310294 at R0.5, 0.237029 at R0.55, 0.162494 at R0.60. These imply only ±0.155147, ±0.118514, ±0.081247 mm common translation respectively before any further errors.
- Loose endpoint, 10.2 × 2.3 slot, 8.2 tab, 1.44 thickness, R0.5: total x play 1.990152, y play 0.860.
- A separate straight-section tilt screen with both boards 1.76 mm and slot width 1.90 mm gives only 4.381° transverse tilt before contact, using `t/cos(theta) + main_thickness*tan(abs(theta)) <= slot_width`. This deliberately omits simultaneous radius/pitch/finish/bow errors and is not an allowable assembly angle.

The dimensional assumptions are carried from the prior design study. They are not a vendor acceptance of radius, position, pitch or this assembly. Burrs, finish thickness, bow, twist, perpendicularity, root radius/position, copper-to-outline registration and thermal effects have no allocated acceptance limits yet. A positive size-only budget is not a fit certification.

## Contact overlap and fixture requirements

All child lands end at y=2.346, giving 0.254 mm nominal tip clearance. Exposed height below a 1.6 main board is 0.746 mm, down from 0.850; at main thickness 1.76, only 0.586 remains before seating and registration error. The full strip's nominal exposed area is 7.892 × 0.746 = 5.887432 mm², approximately 29.32% below the inherited 9.8 × 0.850 = 8.330 mm². Full-width power contacts do not remove this current/fillet qualification need.

The centred transverse solder reach is 0.60 mm on each face. Nominal free float gives about 0.35–0.85 mm opposing reaches; the loose endpoint can reach 1.21 mm under the study's slot-to-copper assumption. Solder volume, wetting, bridging, fillet geometry, current capacity and fatigue are unqualified.

A positioning/retention fixture is required. The nominal ±0.733013 mm x float exceeds the smallest inter-net land gap, 0.373 mm, so the slot cannot align the solder pads by itself. Illustratively, verified finished copper-to-copper x alignment within ±0.10 mm would retain at least 1.10 mm signal and 1.50 mm individual power overlap; the shorter strip retains its full nominal 7.892 mm x overlap. This is a proposed inspection target, not a fixture capability claim. At the adverse R0.60/pitch screen, the mechanical common-position window is narrower than ±0.10, so that fixture number cannot substitute for a complete fit stack.

The fixture must establish finished per-net longitudinal registration, transverse centring, perpendicularity, flush seating and retention through soldering. It should not apply unqualified clamping load through the narrow seating lands. No fixture hardware has been designed or validated in this package. A reviewable fixture design, metrology/gauge plan, solder process limits and prototype inspection remain required before acceptance.

## Honest strength screen

Nominal main minimum outer/central/front ligaments are 0.60 / 1.20 / 1.35 mm. At +0.20 mm slot size these fall to 0.50 / 1.00 / 1.25 before position errors. The 10.0 × 2.1 R0.5 cutout removes 20.785398 mm² per slot; its narrow end wall extends over 1.10 mm height. These dimensions do not rate the routed rails for connector load.

Child flat seating intervals are 0–0.4, 10.8–11.6 and 22.0–22.4: 0.40 / 0.80 / 0.40 mm, totalling 1.60 mm. Multiplying by nominal 1.6 mm thickness gives only 2.56 mm² gross nominal seating area. Independent outline/root position errors could consume a large fraction of these lands. No minimum finished land dimension has been accepted.

One 8.4 mm tab has 13.44 mm² gross root section and 3.584 mm³ nominal out-of-plane rectangular section modulus at 1.6 mm thickness. This is a geometric screen only, before root-notch stress concentration. It is about 17.65% less gross section than a 10.2 mm tab. No allowable load is calculated because laminate grade/stack/fibre orientation, elastic/strength allowables, force and lever arm, unequal load sharing, clamping/restraint, connector insertion/extraction and cable pull, solder alloy and fillet, creep/fatigue, shock, vibration, humidity and temperature are not established.

Required qualification includes a specified material/process, load cases and safety criteria; inspection of manufactured rails/roots/copper; fixture and solder-process trials; current/temperature-rise tests; connector insertion/extraction and pull/bend testing; and appropriate fatigue/vibration/thermal cycling on prototypes. Geometry alone cannot prove strength or assembly fit.

## Electrical repair and integration gates

The mechanical candidate intentionally retains old routing, which is no longer correct for the moved pads and edges. Existing zero-open/clearance counts do not transfer.

Independent bounded checks on candidate01, whose contact/cutout geometry is unchanged in candidate02, found:

- Three retained DSM_DATA In2.Cu segments approximately 0.2115 mm from the new slot, below the 0.30 floor. Full UUIDs are in the independent-review record.
- Six definite child segment/outline conflicts across VX, GND, SBUS and S1, including old copper beyond the narrowed tabs.
- Main cross-net overlap witnesses: moved VX versus TAIL; moved GND versus DSM_DATA; moved TAIL versus RPM and ESC; moved S2 versus S3.
- Child P1/S1 and P7/SBUS have 0.254 mm gaps to nearest retained same-net track/via in the unfilled candidate.

These are static witnesses, not full DRC counts. `routing-preservation-inventory.json` contains complete existing segment/via records for all mating nets and DSM_DATA so repairs can preserve complete power/service/return ports, rather than deleting only obstructing fragments. The independent review contains full contact/edge witness records.

The routing owner must apply the guarded transaction to its latest accepted copper in a new dedicated integration snapshot, repair local copper on both boards, refill all zones, and run native KiCad 10 DRC/ERC/parity with zero opens on that exact integrated source. Full current main/header rules and relevant advisory checks remain visible; no new ignore setting is introduced.

## Models and preview

`header-interface-dimensioned-preview.svg/.png/.pdf` is a dimensioned two-dimensional study, not a screenshot or a native 3D check. `docs/images/joint-section.svg` is an additional nominal illustrative section. The corresponding scripts use the shared dimensions and source-bound contact results.

The untouched original assembled-child WRL is retained only in the root package's source-model/rollback directories, SHA256 `64ae3281014cf1c5cccc852d9e4c57859de106a1e7980f92d572a246038aa1c3`. It must not be presented as the redesigned child model. The exact connector WRL is copied unchanged to the candidate library, SHA256 `cd25aa172890bc506dc1254577b35eda18c9faff947c4a08dc74b8e0192f8294`, so a later native export includes the connector.

The main native footprint and generator reference `nexus-header-board-root-relief-candidate.wrl`. This target is intentionally absent pending native-valid integrated geometry. `build_header_board.py --vrml` is updated to export that exact filename from the integrated child PCB; the native lane must inspect the resulting model, model units/transforms, full-depth tab passage, seating, connector/body collision and worst-case mating limits. Running that script without `--vrml` rebuilds the child and would discard routed copper; it is not the integration method.
