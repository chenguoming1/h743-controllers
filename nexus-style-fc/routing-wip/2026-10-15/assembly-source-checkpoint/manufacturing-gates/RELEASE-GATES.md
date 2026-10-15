# Nexus manufacturing release gates

15 October 2026. **Experimental source checkpoint accepted; fabrication/assembly release and flight-use qualification remain on hold.** This is a bounded engineering closeout, not a request to keep rerouting indefinitely. No project, factory account or order was changed by this review.

## Exact review baseline

- Main: `ccd8865f6785fd1cdec0214a08fe409faed4d47bb01e8474f09264ee36acab99`
- Matching child: `bfec2a120fbda6c97c1f8a36dfff6a35337e13ab1c3af63abb987f529d761403`
- [Draft PR 41](https://github.com/chenguoming1/h743-controllers/pull/41), published head `758108b6a4b6b9698174e195cc5146dee373ff07`, verified by publication17 receipt.
- Existing native receipts: main zero errors, opens, electrical parity and dangling tracks; fresh matching child zero errors/opens. Main retains 11 centering, 4 type and 54 silk advisories; child retains 11 courtyard and 11 footprint-filter advisories. Annotation cleanup is separate. Subsequent source changes require an updated hash binding and relevant checks; these results do not automatically transfer.

The [source receipt](source-receipt.json) independently rebinds all 16 inherited via definitions, all 17 contacted pasted-pad definitions and their positions to this main. It also records the actual U5 exported aperture. No native KiCad, refill, solver or routing was run here.

## What can close where

| Gate | Cloud/source work | Exact outside evidence needed | Release condition |
|---|---|---|---|
| Pasted drills and under-body vias | Per-location process drawing; optional qualified aperture/routing remedies; coherent final exports | Fabricator **and assembler** disposition of exact geometry, registration and reflow process; sample joint evidence | Every location has an accepted treatment, with no undocumented CAM substitution |
| USB FS | Firmware/mode record; exact-stack extraction and any justified source correction | Actual production stack/tolerances and coupon method; assembled FS tests | Model and manufactured electrical results satisfy applicable FS requirements |
| Header assembly | Datum/registration drawing and assembly/inspection instructions | Finished slot/tab/copper tolerance agreement; assembly, joint/current and structural tests | Fits and retains correct contacts under agreed dimensional and service limits |
| BEC/power | Load-path budget, component-corner analysis and bounded test plan | Actual BEC configuration/envelope, exact-part data and bench measurements | All rails, joints and components meet documented operating limits at intended loads |
| IMU function | Resolve pin9 hardware/firmware disposition; derive package-to-vehicle axis transform | Firmware evidence plus physical axis/rotation checks | No unresolved unused-input treatment or orientation assumption |
| Final package | Source/library/generator agreement, warnings disposition, hashes and complete main/child DFM exports | Order-specific DFM acceptance and controlled production files | Source and approved production files match; manufacturing acceptance is recorded |

A DFM website pass can help close fabrication checks. It cannot establish firmware correctness, USB waveform quality, regulator stability, current rating, solder fatigue or physical assembly fit.

## 1. Pasted vias: concrete choices and required process answer

### Current construction

All 16 are ordinary through vias, 0.450 mm land / 0.200 mm drill. They intersect 17 same-net pasted pads, with no different-net contacts. The board requests front/back tenting; covering, plugging, capping and filling are off. Those flags do **not** create soldermask inside an overlapping pad opening or make a planar filled/capped via.

The [17-contact inventory](pasted-contact-inventory.csv) identifies coordinates, sides and actual pad shapes. Grouped by joint:

- C3.1, C19.2, C26.2, C9.2: decoupling/bulk-capacitor contacts
- J3.6, J4.6, J5.5: connector mounting/ground contacts
- J2.5 **and opposite-side C24.2**: one shared drill, requiring a two-sided disposition
- U2.10, U11.2, R14.2: ground/reference or clamp-return contacts
- U1.16, U1.61, U2.1, U3.6: signal/supply land contacts
- U5.17: exposed thermal pad, requiring the device-specific review below

Some grounds also serve circuitry on the opposite face; preserve those donor paths. In particular, do not remove a buck, LDO, IMU or clamp return merely to reduce the inventory count.

### Three optional source remedies, not applied

| Joint | Proposed moved centre (mm) | Nominal drill-to-opening gap | Required preserved connection |
|---|---:|---:|---|
| J3.6 | 119.975, 116.150 | 0.170000 mm | 0.450 mm F.Cu bridge and finite plane return |
| C26.2 | 117.575, 124.700 | 0.060000 mm | 0.450 mm F.Cu bridge and bulk-cap return |
| U1.61 SCL | 120.220, 114.075 | 0.070975 mm | 0.450 mm B.Cu/In2 bridges and both donors |

These r61-bound proposals would reduce the inventory to 13 vias/14 contacts if revalidated and accepted on the final source. C26/SCL still have partial annulus overlap with the opening; their drill centres being outside does not prove tolerance-safe separation. The small nominal margins need actual drill, mask and stencil registration limits. Rebind complete donors and surrounding copper, then native refill/DRC, exact exported openings and return continuity before accepting any move. There is no requirement to apply these moves if the retained construction is qualified.

### U5 process decision

U5 is TPS62130RGTR. Its actual bottom-paste export flashes one continuous clipped-corner polygon approximately **1.800 × 1.800 mm**, not a 0.005 mm aperture; 0.005 is only the custom-pad anchor. The 0.200 mm drill at **(102.675,108.225)** overlaps this opening by approximately **0.075 mm**. The native pad has no local mask notch or separate paste exclusion. It is the only GND via in the inherited review within 2 mm copper-edge distance of EP17, and also participates in AGND/C15 return paths.

TI requires EP soldering and direct AGND/PGND/common-ground connection. Its RGT package guidance permits filled, plugged **or tented** vias under paste; its current stencil example uses a smaller aperture and a stated stencil thickness. This supports a package/process review, not a universal premium-via mandate or copying a percentage as a universal acceptance limit. [TPS62130 datasheet, §§6/11 and RGT package/stencil drawings](https://www.ti.com/lit/ds/symlink/tps62130.pdf)

Resolve each affected location through one of these explicit routes:

1. **Retain geometry with a qualified process.** Ask whether the exact final mask/paste/drill stack will leave the barrel exposed on either face, and how the intended reflow sequence controls solder loss, voids, balls, bridging and seating. Record the accepted material/process, inspection method and joint acceptance criteria by reference/coordinate. “Tented” alone is not an answer.
2. **Exclude the drill from solder deposition/exposure in source.** Revalidate an off-pad escape, or design a manufacturable local mask notch/island with matching paste exclusion/reduced or segmented stencil aperture. At edge-straddling U5 a notch may be more natural than an isolated island. Preserve enough solderable EP and all electrical/thermal donors; agree minimum mask feature, registration allowance and stencil release with the assembler. A paste-only hole does not itself seal a barrel that remains exposed in mask. Export and inspect the actual geometry afterward.
3. **Use a specified plugged/filled/capped construction where needed.** Select only a process that the fabricator explicitly supports at these pad-overlap geometries, with the necessary planarity and finish. JLC distinguishes mask tenting, ink plugging, and filled/capped processes, and places restrictions on ink plugging near/open in pads. Do not relabel ordinary tenting or assume any plugging checkbox covers these sites. [JLC via-covering definitions and restrictions](https://jlcpcb.com/help/article/pcb-via-covering)

For U5, compare the chosen mask/stencil/reflow arrangement with device guidance and verify EP wetting/void distribution and thermal operation on samples. Tenting can be valid; backside tenting can also trap gas, so finish, paste and reflow matter. [TI QFN/SON attachment, §3.4 and solder-printing guidance](https://www.ti.com/lit/an/slua271/slua271.pdf)

**Separate under-body gate:** r62's D5 body has A1 minimum 0.000 mm. The retained 0.200 mm VX hole at (101.800,125.650) lies beneath its maximum body. C27 also has under-body holes. Even where paste is clear, qualify tent topography/integrity, solder balls, seating and coplanarity. Do not use D5's maximum standoff as guaranteed clearance. Existing C27/C31 maximum height is 1.450 mm.

## 2. Actual-stack USB qualification

Source maps USB_DM/DP to STM32F722RET6 **PA11/pin44 and PA12/pin45**, the integrated **OTG_FS** PHY. J6 has Type-C UFP CC pull-downs; U7 is USBLC6-2SC6 protection. This is a **12 Mbit/s full-speed hardware path**. Firmware and observed enumeration are unverified. [ST STM32F722RE datasheet, §3.29/Table 10](https://www.st.com/resource/en/datasheet/stm32f722re.pdf)

Accepted routing uses 0.170 mm In3 trunk width with intended 0.127 mm paired edge gap; 0.150 mm launches/terminals and four tapers remain. **0.170 mm is not the pair clearance.** Actual ground connectivity is demonstrated, but In3 has mixed nearby reference coverage and the compact DP In1 join has interrupted nearby reference. Projection fractions and nearest-ground-via distances are diagnostics, not pass thresholds.

Required closure:

- Obtain the **order-specific six-layer stack**: pressed dielectric thickness/material assumptions, finished copper/etch profile, width/gap and layer-registration tolerances, outer-mask assumptions. Reconcile the source's nominal “JLC06161H-2116-like” declaration with the offered stack. Its nominal copper/dielectric sum is 1.6168 mm versus the 1.6 mm board declaration; confirm rather than silently substitute.
- Bind an actual-stack multiconductor extraction/model to final copper, including interrupted In2 reference, adjacent signals/power copper, DP In1 join, tapers, transitions/unused barrels/antipads, uncoupled launches, connector and ESD loading. Evaluate impedance, coupling/common-mode conversion, full-path delay/skew and FS waveform behavior. The earlier idealized width sweep is not final-board signoff.
- Agree impedance target/tolerance, structures, coupon and allowed CAM adjustments. Lot-linked coupon/TDR evidence checks the manufactured structure; a uniform coupon alone does not validate this board's discontinuities. [JLC stack parameters](https://jlcpcb.com/impedance), [JLC impedance-test explanation](https://jlcpcb.com/blog/pcb-impedance-testing)
- Verify intended firmware/clock/VBUS-attach behavior, enumeration and transfers in both Type-C orientations with relevant cables/hosts/power modes. Perform applicable FS signal-quality and, where applicable, UFP inrush/back-voltage tests, reset and suspend/resume. Use the applicable official requirements, not HS-only limits or invented geometric percentages. [USB-IF electrical compliance specification v1.08](https://www.usb.org/sites/default/files/USB2%20Electrical%20Compliance%20Specification%20v1.08.pdf)

## 3. Header tolerance, registration and strength

Stage08 uses **10.10 × 2.20 mm R0.50 slots**. The actual child mesh clears nominally by **0.287500 mm**. Under the explicitly assumed adverse size/radius/pitch model, **±0.10 X / ±0.05 Y leaves 0.013997 mm radial reserve**. This is conditional geometry, not a factory guarantee. The window is about the actual feasible midpoint, whose offset from copper alignment remains unallocated.

Require a finished-parts drawing/agreement for slot/tab/root dimensions, maximum corner radius, two-slot/two-tab pitch, copper-to-outline/common datum, thickness, finish/burrs, bow/tilt and seating. Public size tolerances alone do not close that stack. Nominal copper-edge gap is 0.300 mm; finished contour tolerance can reduce it.

Tabs are **not self-aligning electrical contacts**. Define how the child is positioned, held, tack-soldered and inspected. At ±0.10 X the nominal 1.20 mm signal projection retains 1.10 mm overlap, but overlap alone is not a qualified solder/current joint. Use finished-copper registration and qualified fillet/overlap criteria. Hand seating/tacking is acceptable only if demonstrated; a purchased precision fixture is not automatically required.

The outer rail is **0.55 mm nominal / 0.45 mm in the stated adverse length case**, before unallocated datum effects. Qualify handling/clamping, soldering, connector mating/cable pull and service vibration/shock/fatigue; inspect cracks and contact resistance. Test the actual header power/ground joints at the intended current profile. Confirm enclosure/mating-cable clearances: C27/C31 can extend below nominal tab tips. No rail strength, fixture or joint current rating has been established.

## 4. BEC and power transient qualification

Intended source is Hobbywing Platinum 120A V4 **SKU30203401**, on 6S, with user-planned **7.4 V BEC**. Manufacturer data lists a 5–8 V adjustable BEC and 10 A continuous/25 A peak; the cited BEC peak duration is unspecified. The ESC motor-current rating's duration must not be transferred to the BEC. Actual configuration, tolerance and transients remain unverified. **Raw 6S must never feed the FC. Neither BEC specification is a PCB current rating.** [Hobbywing exact product](https://www.hobbywingdirect.com/collections/clearance/products/platinum-120a-v4-esc)

The approved C27/C31 pair is Samsung CL21A226MAYNNNE, 22 µF/25 V X5R each. Exact manufacturer curves are typical reference data. The inherited combined tolerance/temperature/aging screens are assumptions, not a guaranteed combined-corner minimum. [Samsung exact part family](https://product.samsungsem.com/mlcc/CL21A226MAYNNN.do)

r62 improves C27→U14 VIN to 9.401 mm and approximately 18.52 mΩ **trace-only nominal** resistance, with two through transitions. Finite returns and EN branching are proven; this does not establish local HF impedance. C31 shares the feed. U14 TPS629210 requires at least 3 µF effective input capacitance and close VIN/GND decoupling; its recommended input range is 3–17 V. A 25 V capacitor does not extend IC limits. [TI TPS629210, §§7.3/9.2/11](https://www.ti.com/lit/ds/symlink/tps629210.pdf)

Close with:

- Exact BEC programming/readback, output tolerance/transient evidence, harness/wire lengths and the actual FC/peripheral/servo load paths. Specify continuous and pulse currents, pulse duration/duty cycle, ambient/cooling and service life. Separate bypassed loads from current that crosses the PCB/header.
- Worst-corner component/rail budget using actual effective capacitance, ESR/ESL, voltage/temperature/aging, regulator/diode/inductor limits and actual copper/plating. Do not claim a current rating from trace width, a nameplate BEC rating or summed nominal capacitance.
- Low-inductance measurements at U14 VIN/GND and EN/GND, U5 VIN, upstream BEC and downstream rails during startup/hot-plug, load steps, brownout and relevant power-source changes. Establish ripple/ringing, overshoot/undershoot, regulation and reset behavior against actual device/system limits. Verify current/temperature rise at traces, vias, D5, regulators, connectors and header joints over the intended envelope.
- If measurements fail, use a bounded diagnosed remedy: improve the affected loop/return or evaluate a local bypass/protection change with its own review. No extra part or indiscriminate reroute is justified solely by a nonzero route length.

## 5. Two inherited IMU functional gates

U2 is ICM-42688-P/C1850418. Pad9 is presently the NC `INT2/FSYNC/CLKIN` net; source sets pin9 to `None`. TDK's pin table calls for grounding unused FSYNC. Its register description also makes pin9 multifunctional, with reset selection INT2. Therefore resolve intended hardware and firmware together: for unused-FSYNC intent, prepare a coherent ground-connection/firmware disposition; if retaining an unused INT2 output, record firmware behavior and a device-supported rationale. Do not blindly ground an output or claim that an NC flag resolves the input guidance. [TDK pin table §4.1](https://invensense.tdk.com/wp-content/uploads/2022/12/DS-000347-ICM-42688-P-v1.7.pdf), [TDK §15.18](https://invensense.tdk.com/wp-content/uploads/2020/04/ds-000347_icm-42688-p-datasheet.pdf)

U2 is on F.Cu at 0°; the source comment asserts `gyro_1_sensor_align CW90`. Derive and record package pin1/axes → board face/forward → vehicle axes → firmware transform, then verify gravity directions and positive rotations physically before flight use. A placement angle or comment alone is insufficient. [TDK axes, §10.1](https://invensense.tdk.com/wp-content/uploads/2020/04/ds-000347_icm-42688-p-datasheet.pdf)

The approved A/B/C GH mapping remains **Nexus GND/5V/RX/TX**. Its intentional difference from F722 is not a redesign gate; document and inspect cable/pin1 orientation against that approved mapping.

## Bounded next handoff

### Cloud-completable now

1. Finish the separately owned annotation work and rebind final main/child, schematic, libraries, generators and receipts. Disposition the remaining centering/type/courtyard/filter advisories by actual function; do not hide severities or treat every advisory as a physical defect.
2. Prepare a **review-only DFM package** containing exact main/child copper, mask, paste, drills/outlines, stack declaration, assembly drawings, BOM/CPL, per-via process table and hash manifest. Mark unqualified gates; do not substitute old review exports for final source.
3. Record selected source-remedy choices and pin9/axis/firmware intent. Only implement authorized changes, with coherent source updates and native validation. Prepare the test/inspection record before ordering.

### Exact user/design decisions still needed

- Which fabricator/assembler and quoted stack/process will be used? If ordinary tenting is required, select source remedies where that process cannot qualify the retained geometry. If a different process is proposed, approve its exact scope/cost before ordering.
- Confirm the actual 7.4 V configuration and specify connected loads, routing through/bypassing the board, intended current/time/temperature envelope and enclosure.
- Confirm the physical board-forward/up orientation and intended firmware revision; resolve pin9's intended role with the designer.
- Choose controlled prototype evaluation versus production release. A prototype order still requires an explicit bounded acceptance of outstanding risks and normal purchase authorization; it does not close them.

### Manufacturer reply checklist

Request a written, source-version-bound disposition for: (a) all 17 pasted contacts and under-body vias, including two-sided reflow; (b) actual mask/stencil edits and registration; (c) U5 EP treatment/inspection; (d) the exact six-layer stack/impedance coupon; (e) finished slots, corner radii, datum/pitch and thin rails; (f) assembly holding, solder/inspection and selected-component envelopes. If the response is only an automated DFM result, the unanswered items stay open. No upload, outreach or purchase was performed in this review.

### Evidence index

All paths below are existing source evidence relative to `nexus-recovery-20261015/`; hashes are preserved in [source-receipt.json](source-receipt.json).

- `mechanical-integration/main-signal-slot-08/`: `verification.json`, `mask-paste-proof.json`, actual `mask-paste/after/`, `usb-reference-return-verification.json`, `FINAL-SEAL.json`
- `mechanical-integration/main-signal-slot-08-validation-supplement/verification.json`: fresh child and ERC receipt
- `r56-remaining-via-inventory/remaining-vias.json`: inherited per-via functions and donors, rebound here
- `/workspace/shared/nexus-pasted-via-r61/three-bounded-proposals.json`: unapplied optional moves
- `header-assembly-fit-review-readonly/README.md`, `electrical-registration-window.json`: fit, datum, rail and contact evidence
- `routing-continuation/r62-input-cap-star/independent-review/REVIEW.md`: electrical loop/derating distinctions; subsequent finite attachments are closed by stage08 receipts
- `routing-continuation/r62-input-cap-star/physical-assembly-evidence/FINAL-ASSEMBLY-SUPPLEMENT.md`: D5/C27/C31 body and via envelopes

External sources were checked on 15 October 2026. TDK's current landing page lists revision 1.9, but its download did not expose document contents in this read-only web session; the specific pin/axis/register statements above are from official indexed revisions 1.7/1.8. Obtain the supplied-part/current revision for the final pin9 disposition.
