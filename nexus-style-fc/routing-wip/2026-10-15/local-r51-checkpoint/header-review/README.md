# Nexus header interface: bounded mechanical remedy review

Read-only review, 2026-10-15. No source changes, native KiCad/solver runs, GitHub writes, orders or fabrication contact were performed. Dimensions are millimetres. This is a proposal for a controlled redesign and validation, not manufacturing acceptance.

## Decision

Copper recession alone retains nominal solderable copper but does not make the existing joint assemble. The smallest defensible next approval is a **header-interface redesign**, covering the two slot profiles, tab widths, mating contact positions/shapes, local routing and an assembly-positioning method. Preserve the 22.4 mm board-body width, 11.2 mm slot/tab pitch, 1.6 mm nominal thickness, 2.6 mm insertion length, connector and net/pin assignments. Do not waive edge rules.

The preferred **root-aware design-study candidate** is two **10.0 × 2.1 mm rounded-rectangle cutouts with R0.5 internal corners**, two **8.4 mm tabs**, and four **R0.5 tab-root reliefs** on the child. Redistribute full-width 1.2 mm signal / 1.6 mm power contacts on both boards. Main nominal outer ligaments increase from 0.40 to 0.60 and the centre web from 0.80 to 1.20. The root reliefs leave 0.40 mm outer and 0.80 mm central flat seating lands. These figures do not establish strength. Manufacturing position/radius acceptance, fixture alignment and solder qualification remain explicit gates.

Suggested exact approval question:

> May I redesign the header interface around 10.0 × 2.1 mm R0.5 rounded-rectangle slots, 8.4 mm tabs and R0.5 tab-root reliefs, reposition the matching contacts and local routes while keeping the board body, connector and pinout unchanged, and specify an assembly-alignment fixture? This authorizes design and verification only; fabrication stays blocked until fit tolerances, remaining rails/seating lands and solder joints are qualified.

## Source and method

The original arithmetic and copper-proximity screen used a **retained original geometry source** under the local directory named `latest-main`. That directory name was not reliable provenance: its main-board SHA256 `b467854d…` is **not** canonical main at commit `80a3f763d5031198b4622402bb73a532676b9be9`. The original-source hashes below identify exactly what was screened.

- Retained original main PCB SHA256: `b467854d4e4a49959d61bdbaa088e78165129ce30ae8ab9dedf4d45c58999b5c`
- Header PCB SHA256: `99d06c7ec685f776f357958c22f684f198f9ef5bf7e9bed437833c9d6aadfba0`
- Main rule file SHA256: `3c261423d4fb5b02b61cf26ee73f62c417e487f71a5f28b5327213618212bd89`
- Header rule file SHA256: `752b0ed66c84a1a2d8ae770f8d1213192415054efef5f6c87d2a0b2318e6beaf`

`header-fit-options.json` records the retained source hashes, native mating-pad boxes, each proposed mating-pad box, per-pad slot/outline distances, lateral changes and numerical fit bounds. `review.py` uses the inspected pure S-expression parser and independent arithmetic only. `existing-copper-proximity.json` screens **only retained original main-board b467854d…** tracks, vias and filled zones. It is not a native DRC or a copper check of canonical main or r51.

### Current-source geometry comparison

The recorded binding in `current-main-binding-09.json` resolves canonical main at `80a3f763d5031198b4622402bb73a532676b9be9` to SHA256 `afd0f3225b8d9eca28487b62dfe92ed8feba742e9577b70fb08b03ff8411859f`. The local file bytes match that binding. The r51 experimental PCB inspected here is SHA256 `4e3b32282d184faef88e86e1d8f269065cfbf2acc79457953ee75bc610405d66`.

A separate read-only native-text comparison confirms that both have exactly the same main outline, board thickness, J1 position/layer and full pad/slot geometry/net assignments as the retained original. The header is byte-identical at `99d06c7e…`; its outline, thickness and all footprints/pads also compare identically. Thus the mechanical/contact dimensions and proposal remain applicable to canonical main and r51. **Track, via and zone-clearance results do not transfer with this geometry comparison.**

`current-source-geometry-comparison.json` contains full source hashes, local provenance, normalized geometry and comparison results. It also records matching geometry in the subsequently inspected U10 metadata-integration snapshots (`925642c3…` canonical and `3e3869e1…` experimental); those statements apply only to the captured hashes. No native jobs or newer-source copper-proximity scans were run.


For a capsule, the usable rectangular width at child thickness t is L − W + sqrt(W² − t²). For a rounded rectangle with corner radius r, it is L − 2r + 2 sqrt(r² − q²), where q = max(0, t/2 − (W/2 − r)). These are centered, rigid, perpendicular cross-sections; bow, twist, burrs, solder finish and assembly tilt require separate limits.

## Why the inherited interface fails

- Native tabs: x = 0.5–10.7 and 11.7–21.9, width 10.2, insertion length 2.6, nominal thickness 1.6.
- Native slots: centres (5.6, 2.4) and (16.8, 2.4), full capsule size 10.4 × 1.8, end radius 0.9.
- Only 9.424621 rectangular width is available at the child faces. Interference is 0.387689 per end.
- Lengthening the 1.8-wide capsules to 11.175379 merely removes nominal interference. It leaves 0.024621 centre web and 0.012311 outer ligaments. Reject.
- All eleven child mating lands end 0.150 from the tab end. Keeping their top at the seating line and trimming 0.104 produces height 2.346 and edge gap 0.254. Exposed copper below a 1.6 main board remains 0.746, down from 0.850.
- Six contacts also violate lateral clearance: both strips and edge signals P1/P7 and powers T1/T2. Copper-only recession would leave edge signal width 1.146, power 1.546, and strip width 9.692. This does not alter the assembly interference.

## Published process limits used, and what is not known

[JLCPCB rigid-board capabilities](https://jlcpcb.com/capabilities/pcb-capabilities/) lists ±0.20 mm non-plated slot size tolerance, ±0.20 mm regular routed-outline dimensions, and ±10% thickness for a 1.6 mm board (1.44–1.76). The existing slot can therefore be 1.60 wide while the child is 1.76 thick. It also lists 1.0 mm minimum NPTH slot width. Its ±0.10 mm high-precision outline option lists a 50 × 50 mm minimum and three tooling holes; this review does not assume that service applies to these individual boards.

[JLCPCB's outline guidance](https://jlcpcb.com/blog/pcb-board-outline) discusses internal corner radii of at least 0.5–1.0 mm and explicitly drawing internal cutouts. This makes an R0.5 rounded-rectangle a credible process candidate, rather than assuming every slot must have radius W/2. It is not a binding acceptance of an exact maximum R0.5, its positional tolerances, or this design's thin rails. Square internal corners are explicitly unsupported in the capabilities page.

No published source located here approves a 0.40 mm remaining outer ligament or 0.80 mm central web for this connector load. Those are inherited dimensions, not accepted manufacturing/strength minima. Neither their survival in a native DRC nor retention in a proposal establishes strength. Slot-to-outline registration, two-slot/two-tab pitch tolerances, maximum finished corner radius, child flatness and the acceptable joint load/current still need definitions.

## Bounded options

| Option | Slot profile | Tab width | Nominal total x / y play | Nominal side ligament / centre web / front ligament | Disposition |
|---|---|---:|---:|---:|---|
| Existing | 10.4 × 1.8 capsule R0.9 | 10.2 | −0.775379 / 0.20 | 0.40 / 0.80 / 1.50 | Cannot assemble |
| Modest coupled enlargement | 10.9 × 2.2 capsule R1.1 | 10.2 | 0.009967 / 0.60 | 0.15 / 0.30 / 1.30 | Reject: negligible nominal end play, thinner rails, fails tolerance check |
| Narrower tab, full capsule | 10.4 × 2.1 capsule R1.05 | 8.4 | 1.260147 / 0.50 | 0.40 / 0.80 / 1.35 | Conditional alternative; requires root reliefs and fixture |
| Preliminary rounded rectangle | 10.4 × 2.1, four R0.5 corners | 9.0 | 1.266025 / 0.50 | 0.40 / 0.80 / 1.35 | Incomplete: straight-tab fit alone omits root fillets |
| Root-aware rounded rectangle | 10.0 × 2.1, four R0.5 corners | 8.4 | 1.466025 / 0.50 | 0.60 / 1.20 / 1.35 | Preferred design-study candidate, with four R0.5 root reliefs and fixture |

The dimensions are full slot size, not cutter centreline length. Rounded-rectangle slots must be defined as actual routed cutout contours, not left as oval NPTH pads with a drawing suggesting different corners.

At +0.20 slot length, the two 10.4-long alternatives retain only 0.30 side ligaments and 0.60 centre web **before** slot/outline position error. The **preliminary 10.4 × 2.1 R0.5 rounded rectangle with 9.0 mm tabs** holds the thin end wall at its minimum width for 1.10 mm of height; the old capsule reaches its minimum at only the end tangent. Retaining the same minimum width does not retain the same mechanical strength. That preliminary cutout removes about 21.625 mm² per slot versus 18.025 originally. The final 10.0-long, 8.4-tab candidate has different ligaments/area, stated separately below.

### Size-only tolerance envelope

The following deliberately takes slot length and width each −0.20, tab width +0.20, child thickness 1.76. It holds the rounded-rectangle radius at exactly 0.5 and assumes the axes are centred. It is an adverse dimensional screen, not a complete manufacturing stack.

| Option | Usable slot width at faces | Remaining total x play | Remaining total y play |
|---|---:|---:|---:|
| Coupled 10.9 × 2.2 capsule, tab 10.2 | 9.649947 | −0.750053 | 0.24 |
| 10.4 × 2.1 capsule, tab 8.4 | 9.015821 | 0.415821 | 0.14 |
| 10.4 × 2.1 R0.5 rectangle, tab 9.0 | 9.710294 | 0.510294 | 0.14 |
| Root-aware 10.0 × 2.1 R0.5 rectangle, tab 8.4 | 9.310294 | 0.710294 | 0.14 |

For two equal fits, total available x play also bounds the difference between slot pitch and tab pitch. A hypothetical 0.40 pitch mismatch produces the following **separate cases**. The 0.40 is an illustrative allocation, not a vendor-guaranteed pitch tolerance.

- **Capsule alternative: 10.4 × 2.1 slot, 8.4 tab.** Remaining total x budget is 0.015821. At the loose size endpoints, total x play is 1.893432.
- **Preliminary straight-tab case: 10.4 × 2.1 R0.5 rounded rectangle, 9.0 tab.** Remaining total x budget is 0.110294 at R0.5, 0.037029 at R0.55, and −0.037506 at R0.60. Its loose-endpoint total x play is 1.790152. These figures do not describe the final 8.4-tab candidate, and omit root-fillet interference.
- **Final root-aware candidate: 10.0 × 2.1 R0.5 rounded rectangle, 8.4 tab with R0.5 root reliefs.** Remaining total x budget is 0.310294 at R0.5, 0.237029 at R0.55, and 0.162494 at R0.60. Its loose-endpoint total x play is 1.990152. Root-envelope and process-position errors still need specification.

All three can reach 0.86 total y play at the loose size endpoints. A snug fit cannot be inferred from the nominal drawing. A larger default corner radius must not be substituted without recalculation.

## Root-aware geometry and concrete contact redesign

The original child outline also has sharp concave tab-root corners. A real router leaves fillets there; they widen a tab close to the seating line and can prevent flush seating even when its straight-section cross-section fits. This is why the preliminary 9.0 mm tab case is not recommended as a complete remedy. Ordinary 2D insertion-tip rounding does not address these roots.

For the root-aware candidate, child tab ranges are x = 1.4–9.8 and 12.6–21.0, with seating at y = 0 and ends at y = 2.6. Add circular R0.5 reliefs centred at (0.9, 0), (10.3, 0), (12.1, 0), (21.5, 0), unioned with the existing outside/notch regions. Their upper semicircles remove material up to y = −0.5; their tangencies allow the full-width straight tab envelope to start at the intended seating line. Remaining flat seating lands are x = 0–0.4, 10.8–11.6 and 22.0–22.4. Define these as actual contour reliefs, not extra detached holes or a graphic. Acceptance of this small-feature process and seating land size is required.

A corresponding 10.0 × 2.1 R0.5 main cutout has bounds x = 0.6–10.6 and 11.8–21.8, y = 1.35–3.45. Its side/central/front minimum ligaments are 0.60 / 1.20 / 1.35. At +0.20 length/width, they become 0.50 / 1.00 / 1.25 before position errors. Its thin vertical end wall extends for 1.10 mm; no strength approval is inferred. Removed area is about 20.785 mm² per slot, versus 18.025 originally.

With the adverse size screen above, straight-envelope x play is 0.710294. A hypothetical 0.40 combined pitch mismatch leaves 0.310294. If the finished main-corner radius is 0.55 or 0.60, the remaining budget becomes 0.237029 or 0.162494. These are proposed tolerance budgets, not verified process guarantees. The finished tab-width limit must cover the **entire insertion envelope including the relieved roots**, and the root-radius/copper/seating tolerances require a separate stack.

At the loose size endpoints, total x play is 1.990152 and y play 0.86. A fixture is required. Do not silently accept sharp roots, a default larger radius, or an undefined fit.

All eleven child contacts start at y = 0 and end at y = 2.346, giving nominal 0.254 bottom clearance. Keep signals 1.2 wide and power contacts 1.6 wide by moving matching lands on both boards together. Child strips become 7.892 wide. The largest inner contact shift is 0.954. Adjacent inner-land gaps become 0.373 and 0.897333, still above the retained 0.15 rule.

All main inner lands below have y = 3.800–4.650, and minimum slot clearance 0.350. Mirror their x ranges to the child using x_child = 22.4 − x_main and y = 0–2.346. The JSON explicitly lists both sides, all eleven pad/slot distances and all child side/bottom clearances.

| Net / main pad | Main x range | Width | Main minimum outer-outline clearance |
|---|---:|---:|---:|
| SBUS / 3 | 1.654000–2.854000 | 1.2 | 1.654000 |
| RPM / 4 | 3.227000–4.427000 | 1.2 | 3.227000 |
| ESC / 5 | 4.800000–6.000000 | 1.2 | 3.800000 |
| TAIL / 6 | 6.373000–7.573000 | 1.2 | 3.800000 |
| VX / 1 | 7.946000–9.546000 | 1.6 | 3.800000 |
| GND / 2 | 12.854000–14.454000 | 1.6 | 3.800000 |
| S3 / 7 | 15.351333–16.551333 | 1.2 | 3.800000 |
| S2 / 8 | 17.448667–18.648667 | 1.2 | 3.751333 |
| S1 / 9 | 19.546000–20.746000 | 1.2 | 1.654000 |

Main outer strips retain their x ranges 0.700–10.500 (VX) and 11.900–21.700 (GND), but become y = 0.350–1.000. Each has 0.350 to both slot and external outline. Child outer strips become x = 1.654–9.546 (GND) and 12.854–20.746 (VX). Main inner depth changes 1.00→0.85; main strip depth 0.80→0.65. These retain the original 0.35 slot-copper distance.

All eleven proposed child contacts have minimum nominal clearance 0.254 to their tab outline; the nearest contact corners also remain 0.254 from the circular root-relief boundary. The unchanged 3×7 through-hole connector pads remain in the body: minimum top-outline clearance 0.270, and the bottom row lies 1.55 above the original seating line, leaving at least 1.05 vertically above the relief top. Existing traces or fills in the relief region still need rerouting/refill.

Merely cropping the old edge lands to an 8.4 tab would leave only 0.246 signal and 0.646 power width. Reject that approach; preserve full contact widths by moving both matching sets. The generator, library footprints, native boards and 3D assembly model must all represent the same revised geometry.

## Solder overlap and assembly are separate gates

All dimensions here concern nominal exposed lands, not verified solder strength or allowable current.

- All child signal/power contacts retain their full x width at perfect alignment. Vertical exposed copper is 0.746 rather than 0.850, a 12.24% reduction. With main thickness 1.76 it is 0.586 before copper/outline registration, seating error and bow.
- Outer-strip x overlap becomes 7.892 instead of 9.8; its exposed vertical area falls about 29.32%. This reduction needs current/fillet qualification even though all individual power lands retain their widths.
- The centred horizontal solder reach increases from 0.45 to 0.60 on either face. Nominal transverse float makes it range from 0.35 to 0.85, with the opposite fillet changing conversely. If the nearest main copper edge actually follows the finished slot with the assumed 0.35 clearance, the loose size endpoint permits reach up to 1.21; independent copper/slot registration can change this further.
- Nominal longitudinal float is ±0.733013 for the root-aware rounded rectangle. This exceeds the 0.373 inter-net land gap, so unconstrained assembly can overlap a neighbouring net's main land. The slots cannot serve as the only positioning fixture.
- For illustration only, holding *finished copper-to-copper* x alignment to ±0.10 would retain at least 1.10 signal and 1.50 power overlap, and full 7.892 strip overlap. No current source establishes that fixture tolerance or a required fillet minimum; those must be specified and verified.
- A fixture or another explicit retention/positioning feature, an inspected 3D seating model, and a fillet/current/connector-load qualification are part of the minimum scope.

## Other main-board copper must change too

The native-text proximity screen against **retained original main-board b467854d… only** found no old tracks/vias/filled zones below 0.30 from the original slots (screen minimum 0.300500). Against the proposed capsule it found 3 segments and 11 filled polygons below 0.30; against the preliminary 10.4-long R0.5 rounded rectangles, 5 segments and 11 filled polygons, with minimum estimated spacing 0.020427. Against the root-aware 10.0-long R0.5 candidate it found 3 segments and 11 filled polygons below 0.30, minimum 0.115616. It found no vias below 0.30 in these proposals. These are retained-original-source screening counts, not DRC counts or release evidence. **They do not report the copper clearance of canonical afd0f322… or experimental r51 4e3b3228…; neither newer board was scanned for these counts.**

Therefore neither option can be implemented by changing slot outlines and pad shapes alone. The main interface needs local trace clearance repair, zone refilling and new native DRC. The child needs routing adjusted to moved contacts and the narrower outline. Native checks must use the final working PCB version and must still establish zero opens, schematic parity, ERC and the existing rule floors.

## Bevel/relief alternative

For the original 10.4 × 1.8 capsule, a 45° cross-sectional bevel at all four longitudinal tab corners needs at least 0.387689 face setback merely for nominal contact-free passage. The bevel must run the entire insertion depth, not just round the insertion tip in the 2D child outline. Requiring 0.254 copper setback from the new face edge would leave approximately 0.758311 edge-signal width, 1.158311 edge-power width and 8.916621 strip width, and needs a special side-edge machining/copper process.

It still fails the ordinary slot-width/thickness tolerance case of a 1.60-wide slot and 1.76-thick child. An ordinary gold-finger bevel or a simple tip chamfer is not an established remedy. Reject as a release path unless a manufacturer explicitly accepts the full 3D process, thickness limits and revised copper faces. Local dog-bone/end-relief profiles could be analysed, but this review does not nominate an unmeasured relief that might eat rails or copper.

## Stopping gates

Do not claim assemblability or fabrication readiness until all of these are satisfied:

1. Explicit slot profile, finished maximum radius, tab/slot dimensions and relative positional tolerance stack, including finish, bow and perpendicular seating.
2. Acceptance of the actual remaining outer/central/front ligaments under connector load; nominal inherited widths are not a waiver.
3. A demonstrated assembly-positioning method and acceptable per-net overlap/fillet, plus current and mechanical-load limits.
4. Updated generator/footprint/native PCB agreement, final native DRC/refill, parity/ERC/opens checks and independently inspected mating 3D geometry.
5. Updated fabrication drawings and CAM only after the above and a separate fabrication authorization.
