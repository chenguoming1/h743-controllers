# Nexus header assembled geometry review

2026-10-15. Read-only native-text and exported-VRML analysis on the dot cloud filesystem. No source-board edits, native KiCad jobs, rendering, physical tests, publication or fabrication action.

## Verdict

**The exact nominal mechanical geometry, model transform and all 11 contact alignments pass this analytic screen. Manufacturing/assembly acceptance remains open.** No stale or inverted child-model transform was found. The documented size allowances do not define the complete positioning/radius/fixture tolerance stack, and no assembly/load/solder test has been performed.

The parent-selected integrated candidate is **10.10 × 2.20 mm**, with unchanged centres/R0.50/tabs/pads and a coordinated local signal repair. Its bounded adverse study accommodates ±0.10 X and ±0.05 Y with only **0.013997 mm radial corner reserve**. That is a conditional calculation, not a guaranteed physical fit. The wider geometry failed the unmodified stage07 source copper screen on three DSM_DATA segments. The integrated stage08 repair now passes this exact analytic edge screen and the sole lane reports zero native DRC errors/opens/parity/dangling findings. The smaller 10.00/10.04/10.10 × 2.10 calculations below are retained as study history, not competing final options.

## Exact source binding and preservation

Initially reviewed `mechanical-integration/main-dsm-slot-03`:

- Main PCB: `673f4e6fd86e3fb06eadcd1de49e48322a540080544d4bd51f51ec7df5b09782`
- Child PCB: `bfec2a120fbda6c97c1f8a36dfff6a35337e13ab1c3af63abb987f529d761403`
- New assembled child WRL: `e1f0da0372a9d95a13fcff612a7effc7f4033363e482d384f0d170019d3f5dbe`
- Unchanged connector WRL: `cd25aa172890bc506dc1254577b35eda18c9faff947c4a08dc74b8e0192f8294`

The approved design-study source is `nexus-header-redesign-20261015/candidate-02/nexus-style-fc`, its header-interface README and candidate02 independent addendum. Rejected original native geometries were not used as the proposed design.

Native comparison confirms unchanged candidate02 main outer body, both cutouts, all J1 contacts/model transform, child outline, all child footprint/pad/net/model records and J2–J6 connector geometry/pinout. The later main-left-vias-06 PCB `ccb4bcac2adc3baffce2fcc5f2c891fe91b17384b1ba0064506ade2df7338d8f` additionally has **all** main/child footprint records, board outlines, keepouts and general thickness fields equal to main-dsm-slot-03. Child and model bytes are identical. Thus this review transfers to that exact later main hash. The subsequent stage07 `main-terminal-cleanup-07` PCB `1d40a35cf373bef251f8032001766016f09500b007f22ff27ccb6578b0c4e263` has the same full footprint/outline/keepout/thickness geometry and unchanged child/model. The selected 10.10×2.20 proposal is bound to stage07 in `slot101x220-source-guarded-spec.json`; the integrated stage08 output has now been independently rebound below.

Electrical/native DRC acceptance is owned separately. The initial main-dsm-slot-03 still had 16 mechanical-stage errors and was not accepted; this report does not reclassify it.

## Final integrated output binding

Reviewed `mechanical-integration/main-signal-slot-08` main PCB **`ccd8865f6785fd1cdec0214a08fe409faed4d47bb01e8474f09264ee36acab99`**. All 16 slot-edge replacements and both expanded keepout records agree with the sealed proposal. All 11 J1 pads, model transform, main outer body, every other footprint/connector, thickness and setup rules remain unchanged. Child PCB/model and both schematics retain the hashes above. Native/library slot geometry and shared generator constants agree.

The two additional make_footprints.py comments were checked as exact text replacements and AST-equivalent. All five mechanical library footprint files match in-memory generator output **byte-for-byte**. Final make_footprints.py SHA is `b749b71dc49f8b5cf71d534f78ab3a1bf5c3b3342efc29342547acdb4992d17c`; joint-library SHA is `c1c8421437803c1f98a889af2acfdee6fa6cd3a654cbd182b2fd61f2c1641a4f`.

The exact final-board analytic segment/arc/via/pad-to-slot screen has **zero below 0.300 records**. Minimum segment/via/pad gaps are **0.300/0.300/0.300**; the north DSM straight run is 0.3115. The native lane separately reports zero full DRC errors, opens, electrical parity and dangling findings. This review neither reruns nor substitutes for those native checks. Manufacturing tolerance, datum/registration, narrow-rail strength, solder/current and demonstrated assembly/test gates remain open.

## Correct transform and seating

Units are millimetres unless stated otherwise. Main local coordinates use `(100,100)` as XY origin, board Y increases inward, and Z=0 is the main front-copper plane.

The exported child origin `(100,108.4)` is at its seating line. WRL units are tenths of an inch, **2.54 mm/unit**. The correct native J1 settings already present are:

- Offset `(22.4, -2.4, 0)` mm
- Rotation `(-90, 0, 180)` degrees
- Scale `(1,1,1)`

For a WRL point `(u,v,w)`, after its nested scene transforms, the assembled coordinates are `X=22.4−2.54u`, `Y=2.4−2.54w`, `Z=2.54v`. Equivalently for native child XY and centred physical thickness coordinate z: `X=122.4−x_child`, `Y=2.4−z`, `Z=108.4−y_child`.

KiCad applies negative model Euler angles and a front-layer placement height. Therefore zero model Z offset puts the seating shoulder at the front plane. Adding 0.8 mm or negating the existing X rotation would be incorrect. This convention was checked against [KiCad model-matrix source](https://docs.kicad.org/doxygen/3d__math_8cpp_source.html) and [VRML placement/layer source](https://docs.kicad.org/doxygen/exporter__vrml_8cpp_source.html).

At nominal seating:

- Child F.Cu faces outward at main Y=1.6; child B.Cu faces inward at Y=3.2
- Body rises to Z=8.4; tabs occupy Z=−2.6 to 0
- Main occupies Z=−1.6 to 0, so the tab ends protrude 1.0 below it
- Tab cross-sections stay 8.4 × 1.6 through the full insertion depth
- Four R0.5 reliefs remove material **above** the seating line; there is no widened root below Z=0
- Three flat seating lands are X=0–0.4, 10.8–11.6 and 22.0–22.4. Their nominal support is 2.56 mm², without a qualified load rating

The exported board artwork has FR4 at ±0.7875, copper at ±0.8 and mask at ±0.8125. These small layer separations are rendering conventions. They do not replace the 1.6 mm nominal finished-board specification or create an independent mask-thickness tolerance allocation.

## All eleven mating contacts

These are longitudinal solder-contact alignments; perpendicular boards do not have a planar copper-on-copper mating area. A solder fillet must bridge the transverse reach.

| Child | Net / main pad | Assembled child X interval | Nominal X overlap | Minimum overlap at ±0.10 finished-copper alignment |
|---|---|---|---:|---:|
| P7 | SBUS / 3 | 1.654–2.854 | 1.200 | 1.100 |
| P6 | RPM / 4 | 3.227–4.427 | 1.200 | 1.100 |
| P5 | ESC / 5 | 4.800–6.000 | 1.200 | 1.100 |
| P4 | TAIL / 6 | 6.373–7.573 | 1.200 | 1.100 |
| T2 | VX / 1 | 7.946–9.546 | 1.600 | 1.500 |
| T1 | GND / 2 | 12.854–14.454 | 1.600 | 1.500 |
| P3 | S3 / 7 | 15.351333–16.551333 | 1.200 | 1.100 |
| P2 | S2 / 8 | 17.448667–18.648667 | 1.200 | 1.100 |
| P1 | S1 / 9 | 19.546–20.746 | 1.200 | 1.100 |
| K2 | VX outer / 1 | 1.654–9.546 | 7.892 | 7.892 |
| K1 | GND outer / 2 | 12.854–20.746 | 7.892 | 7.892 |

Inner main lands are Y=3.8–4.65; outer strips Y=0.35–1.0. Nominal fillet reach is 0.60 on either face. All child copper runs from Z=0 down to −2.346, leaving 0.254 nominal tab-tip edge clearance. Exposed vertical copper below main B.Cu is 0.746 at 1.6 board thickness, or 0.586 at 1.76, **before** seating/copper registration errors. Strip exposed area is 5.887432 mm². Current, wetting and fillet strength are not established.

Nominal unfixtured x freedom is ±0.733013, exceeding the minimum inter-net gap 0.373. Slots alone cannot locate the solder contacts or ensure all three narrow seating lands bear correctly. An alignment, holding and inspection method is required. This does not establish a need for a purchased precision fixture; the hand-positioning/tacking option is discussed below.

## Electrical registration window and a simple assembly check

Let Δx be the assembled child displacement from perfect finished-copper alignment. Every individual inner signal/power overlap is `max(0, w−|Δx|)`, with w=1.2 or 1.6. Thus ±0.10 retains 1.10/1.50 overlap, **not full inner-contact overlap**, although physical pad widths are unchanged. Outer-strip overlap is 7.892 for |Δx|≤0.954, then `max(0,8.846−|Δx|)`.

The first foreign-net projected edge touch is at Δx=±0.373 in the SBUS/RPM/ESC/TAIL/VX group. GND/S3 and S2/S1 have 0.897333 gaps; S3/S2 has 0.897334. The VX/GND inner gap is 3.308. Opposite-net outer-strip projected touch first occurs at ±2.354. At ±0.10 the nearest foreign-net projection gap is 0.273.

These are **projected solder-land** limits. Edge touch at 0.373 is not itself a direct conductive short, because the boards are perpendicular with a transverse gap. Additional displacement creates foreign-net projected overlap and a clear solder-bridging hazard; solder spread could cause bridging before that projection threshold. No verified solder fillet/current specification presently sets the permissible minimum overlap or bridging allowance, so ±0.10 must not be turned into an arbitrary production requirement.

With the selected 10.10×2.20 slots, centred-Y nominal longitudinal travel is ±0.808258. At that displacement, a signal can retain only 0.391742 same-net overlap while reaching 0.435258 foreign-net projected overlap. The earlier 10.10×2.10 length-only study has ±0.783013 travel and 0.416987/0.410013 respective overlaps. The tabs therefore **do not self-jig** electrical registration. A feasible seating pose does not imply safe electrical alignment at every mechanically allowed pose.

A simple reviewable method could use a flat support and temporary square/holding guide: seat the three shoulders flush with the main front plane, align the visible body edges as an initial cue, then inspect each intended pair from the underside under magnification, confirming net pairing, overlap, lack of neighbouring-pad intrusion and perpendicularity. Hold that position while making separated tacks, then recheck alignment before completing fillets. Avoid loading the thin rails or narrow seating lands. This describes a method to trial, not a qualified assembly instruction or a claim that visual alignment reliably achieves 0.10 mm. Board-edge matching alone is insufficient because edge-to-copper registration is unqualified. If hand seating and tacking can demonstrate the required finished registration and retention, a separate precision fixture is unnecessary; otherwise a more controlled guide/gauge is needed.

`electrical-registration-window.json` records all eleven directional thresholds and overlap functions/results. The eventual acceptance window should follow a qualified minimum joint overlap/fillet and current/load requirement, combined with the mechanical passage limits.

## Manufacturing tolerances versus illustrative assumptions

[JLCPCB's current capability page](https://jlcpcb.com/capabilities/pcb-capabilities/) confirms ±0.20 regular routed dimensions, ±0.20 non-plated slot size, and ±10% board thickness at 1.6 mm, meaning 1.44–1.76. This supports the **size-only study endpoints**. It does not, by itself, specify the maximum finished corner radius, individual cutout-to-copper datum positions, relative two-slot/two-tab pitch, or minimum remaining seating lands for this design.

Applying ±0.20 to the **entire finished tab/root insertion width** is an explicit drawing/process interpretation that needs acceptance. It is not permission to let each contour edge move independently by ±0.20 and then still call the resulting width 8.4±0.20.

The 0.40 pair-pitch mismatch and R0.55/R0.60 finished-radius cases below are **illustrative contractual bounds**, not published guarantees. The ±0.10 finished-copper fixture target has not been demonstrated. Burrs, finish, bow/twist, seating/perpendicularity, absolute datum registration, connector tolerances and thermal effects remain unallocated.

Rounded-slot usable width at thickness t is `L−2r+2sqrt(r²−q²)`, `q=max(0,t/2−(W/2−r))`.

| Case | Centred-Y longitudinal play/budget | Centred-Y translation half-window | Straight-sided transverse budget, not simultaneous |
|---|---:|---:|---:|
| Nominal 10.0×2.1, tab 8.4, thickness 1.6, R0.5 | 1.466025 | ±0.733013 | 0.500 |
| Adverse sizes 9.8×1.9, tab 8.6, thickness 1.76, R0.5 | 0.710294 | ±0.355147 | 0.140 |
| Same plus 0.40 pair-pitch mismatch, R0.5 | 0.310294 | ±0.155147 | 0.140 |
| Same plus 0.40 pair-pitch mismatch, R0.55 | 0.237029 | ±0.118514 | 0.140 |
| Same plus 0.40 pair-pitch mismatch, R0.60 | 0.162494 | ±0.081247 | 0.140 |
| Loose sizes 10.2×2.3, tab 8.2, thickness 1.44, R0.5 | 1.990152 | ±0.995076 | 0.860 |

The half-window is around the **actual feasible midpoint**, which may shift relative to nominal copper alignment. A tolerance on pitch alone does not constrain that common datum shift. The current ±0.10 target cannot be guaranteed by the R0.60/0.40 case.

## Coupled corner envelope and selected 10.10×2.20 proposal

Independent longitudinal/transverse budgets cannot be spent simultaneously at a rounded corner. For rigid perpendicular tabs, symmetric pair-pitch mismatch P about the actual feasible midpoint, longitudinal displacement dx and transverse displacement dy:

`qx=max(0,T/2+P/2+|dx|−(L/2−r))`

`qy=max(0,t/2+|dy|−(W/2−r))`

The entire rectangular tab section fits iff `qx²+qy²≤r²`. This is an exact rounded-rectangle containment condition under the stated rigid geometry. The window is about the **actual feasible midpoint**, not automatically about the copper-alignment origin. It excludes absolute datum, tilt/bow/finish/burr effects.

For the **selected nominal 10.10×2.20** proposal, adverse finished L=9.90, W=2.00, T=8.60, t=1.76, assumed r≤0.60 and P≤0.40:

- Centred-Y longitudinal half-window is ±0.210000.
- The raw straight-side Y half-budget is 0.120000. After pitch/corner coupling at dx=0, the actual Y half-window is **0.100948**.
- At |dx|≤0.10, the exact maximum |dy| is **0.065436**.
- The illustrative rectangular window **±0.10 X and ±0.05 Y** leaves **0.013997 radial reserve** at its worst corner. It has 0.015436 further Y allowance at dx=0.10, which is not an independent reserve that can also be allocated in X.
- At dy=0.07 and dx=0.10, the radial interference is 0.004152. Full free play is not a safe assembly window.

All dimensions and contacts stay fixed except the two slots and corresponding keepout expansion. New local slot bounds are `[0.55,1.30,10.65,3.50]` and `[11.75,1.30,21.85,3.50]`, still drawn R0.50. Native keepouts become `[100.1,101.00,111.1,103.80]` and `[111.3,101.00,122.3,103.80]`, with original X bounds and all layer/rule permissions preserved. The generator X allowance changes 0.50→0.45 only to represent the same protected X area after the length increase; Y allowance stays 0.30 and the physical polygons expand 0.05 upward/downward for the width increase.

### Exact copper and rail consequences

The exact stage07 analytic screen covers 1,589 segments, 17 arcs and 238 vias, using real rounded-slot geometry. Its geometry and the donor records below are bound to the unchanged reviewed assembly. Native refill/full DRC is still required.

- All **11 main contact-to-slot gaps become 0.300 mm**, consuming the previous 0.050 nominal reserve. Pads are not moved or cropped. The global 0.300 edge floor is retained.
- Minimum existing via gap becomes 0.300 mm; some VX trace portions also reach exactly 0.300. Circular arcs are remote (minimum 7.982588).
- Three In2.Cu DSM_DATA segment edge gaps fall **0.3365→0.2865**, failing by 0.0135: `1820c4c2-7b40-522a-a5f4-bb1f05c3ea7b`, `23a76edb-07a7-56c4-ac2b-748fb6295bbe`, `527e82f5-aa9c-530c-848d-87b60ae4314f`. Their full native records are in the guarded specification. The approved integrated trial includes a coordinated DSM/RPM signal repair, with SW_5V fixed.
- Existing pre-expansion keepout Y allowance would shrink to 0.25. The specified expansion restores 0.30; X allowance is 0.45. No track/via prohibition is relaxed.
- Outer rails become **0.55 nominal / 0.45 at +0.20 slot length**; centre web **1.10 / 0.90**. Front rail becomes **1.30 nominal / 1.20 at +0.20 slot width**, before any unallocated absolute contour datum shift. This is gross geometry, not a load rating.
- Removed area per slot is **22.005398 mm²**, 1.22 above the original 10.00×2.10 and 1.01 above the length-only 10.10×2.10 study.
- Child 0.254 artwork edge/root clearances, all longitudinal solder-overlap functions and the centred nominal 0.60 fillet reach remain unchanged.

The 0.300 pad clearance is a **CAD rule quantity**. An independently adverse +0.20 slot width could reduce physical finished-copper spacing by another 0.10 per side before datum errors. Public size tolerance alone therefore does not guarantee a 0.300 finished physical copper-edge clearance. Procurement/assembly tolerance acceptance remains separate from a native design-rule pass.

### Actual exported full-radius model screen

The actual sealed WRL contains 24 meshes and 10,637 indexed faces. Clipping these to the open main-board interior slab Z=−1.6..−0.00001 gives 352 face polygons. Every complete polygon is contained in one convex rounded slot; checking the full polygon, rather than only a rectangular slot box, covers its edges/interior as well.

For nominal 10.10×2.20 slots there are **zero interfering clipped faces** and minimum radial/edge clearance **0.287500 mm**, including the exported mask visual layer. The earlier 10.00/10.10×2.10 screens also have zero intersections with 0.237500 minimum. Coplanar Z=0 shoulders are intentional seating contacts. This is a deterministic actual-mesh/analytic-cutout test, not a native renderer, manufactured-parts test, load test or model of all tolerances.

### Smaller studies retained as history

Length-only 10.10×2.10 with finished 9.90×1.90 and the same assumed r/P bounds has centred-Y x half-window 0.131247. However at |dx|=0.10 its permitted |dy| is only **0.015436**, rather than the independent 0.070 straight-side half-budget. At dx=0.10/dy=0.02 it interferes by 0.004152; at dx=0.10/dy=0.05 by 0.031585. The earlier statement that an independent ±0.070 transverse allocation could accompany ±0.10 X was incorrect and is superseded by this coupled calculation.

The length-only mathematical minimum 10.037506 applies only at dy=0. Rounding to 10.04 leaves a tiny 0.001247 x reserve and does not establish a practical 2D positioning window. Narrowing tabs to 8.30 would reduce fixed edge-contact clearance to 0.204, below 0.254, and was not selected. A tighter fixture/registration specification also remains unproven; merely naming ±0.05 accuracy cannot qualify a manufacturing or hand-assembly process.

## Body, connectors, C27/C31 and D5

Actual transformed child connector mesh bounds are:

- X=2.304920–20.095081
- Y=−6.900110–4.599994
- Z=1.089944–8.590056

The plastic body is above the main front plane by at least 1.089944; pins are above it by at least 1.979960. The connector is 0.190056 above the child-board top. At centred nominal seating, it does not intersect the main board or any other footprint courtyard: the closest are U11/U12, whose Y minimum is 5.100, leaving 0.500006 plan-view separation. Main connectors J2/J3 have ≥4.150006/4.230006 plan-view separation; J4/J5/J6 are farther away.

This nominal courtyard screen is not an all-tolerance solid collision certification. At the loose slot/thin-child endpoint, allowing full inward float and keeping the model's 2.999994 mm front-face-to-tail reach puts the pin-tail extreme at Y=5.109994. That enters the U11/U12 courtyard by about 0.010. Courtyard overlap is not a proven body collision, but it shows why actual connector/nearby component height envelopes and transverse fixture limits matter. Main models are available in the parent's durable PR40 source; many are not present in this isolated local snapshot and were not silently treated as absent physical components.

C27/C31 are on B.Cu and explicitly have maximum bodies 2.20×1.45×1.45:

| Part | Maximum/native XY envelope | Separation in Y from full header mesh |
|---|---|---:|
| C27 max body | X=0.770–2.970, Y=23.595–25.045 | 18.995006 |
| C31 max body | X=4.720–6.920, Y=25.575–27.025 | 20.975006 |
| D5 courtyard | X=0.460–4.100, Y=25.380–26.980 | 20.780006 |

These show no nominal header interference. C27's max body is 0.335 above D5's courtyard in Y; C31's max body is 0.620 to its right. Their courtyards retain nominal separations 0.085 and 0.145 respectively from D5's courtyard. D5's exact maximum package height was not established here; its courtyard is an envelope screen, not a 3D solid.

The 1.45-high capacitors can extend to Z=−3.05 on a nominal 1.6 main board (−3.21 at 1.76), before solder standoff. They therefore reach 0.45 below the nominal header-tab tips. A bottom enclosure cannot use the tab tip as its sole height datum. No enclosure, mating plugs/cables or assembly fixture has been supplied, so their clearances remain unverified.

## Remaining acceptance gates

1. Agree finished slot/tab/root dimensions, maximum radius, relative pitch and common copper/outline datum limits; specify finish/bow/tilt/seating allowances.
2. Demonstrate an alignment/holding and inspection method satisfying both mechanical passage and finished per-net copper registration. Hand seating and tacking may suffice if measured results support it; do not require a purchased fixture or assume visual accuracy. Avoid unqualified clamping through narrow rails/seating lands.
3. Review remaining rails/seating lands under connector insertion/extraction, cable pull and soldering loads; qualify laminate, solder/current/temperature-rise and mechanical/environmental tests.
4. If any dimension changes, source-bind generator/library/native agreement and rerun exact native refill, full DRC, parity/opens/ERC and populated 3D inspection.
5. Keep manufacturing and fabrication acceptance separate from a nominal geometry or electrical DRC pass.

## Reproducible evidence

- `review_assembly.py` and `assembly-review.json`: exact source hashes, candidate02 preservation, native contact records, all 24 actual mesh bounds and nearby courtyard envelopes
- `compare_followon.py` and `main-left-vias-06-geometry-binding.json`: full footprint/outline/keepout/thickness comparison and exact follow-on hashes
- `study_minimal_remedy.py` and `minimal-remedy-study.json`: bounded historical length cases and selected width case, exact source binding, analytic segment/arc/via and J1 contact clearance results
- `check_full_radius.py` and `full-radius-model-check.json`: actual exported face/slab containment and coupled rounded-corner adverse-envelope calculations
- `electrical-registration-window.json`: all eleven finished-contact overlap/foreign-projection thresholds
- `bounded-width-alternative.json`: selected width-case mechanical/copper/rail consequences
- `prepare_slot101x220_spec.py` and `slot101x220-source-guarded-spec.json`: stage07-bound exact incremental geometry/keepout/library/generator/checker handoff to the sole native lane
- `verify_integrated_geometry.py`, `main-signal-slot-08-integrated-geometry-binding.json`, `main-signal-slot-08-generator-binding.json`, and `main-signal-slot-08-copper-width-study.json`: exact final integrated geometry, source-comment/generator/library and copper-edge binding

Scripts use explicit source bindings and read-only comparisons; the arithmetic/checking scripts write only review artifacts in this directory. No full board/footprint generator, native job or source-board edit was performed by this review.
