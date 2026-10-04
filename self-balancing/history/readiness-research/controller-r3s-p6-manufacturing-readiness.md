# P6 manufacturing readiness and bounded release gates

Audit date: 2026-10-03 UTC. Audited native PCB SHA-256: `fafa9c3f0efc570ab70c69d45ffb7bfc7e548dae520a391ed167540ffccf6c6a`.

## Recommendation

**The audited P6 source has no remaining demonstrated bare-PCB geometry blocker. It is suitable for a prototype fabrication submission once the owner's final export, package-parity and final supplier-rerun gates pass for this exact source.** Those deliverables were still pending when this focused audit began; this report does not substitute inherited P4/P5 results for a P6 release. P5 remains on fabrication hold and is not a fallback.

The 24 red / 6 yellow SMT records inherited from the unchanged P4/P5 component geometry are not 30 independent native design defects. Their dispositions below support retaining the present copper, holes and real paste windows. **They also do not prove that a particular assembled production lot is approved.** Four concrete production deliverables remain: a verified placement/polarity drawing, the double-sided carrier and actual connector-support arrangement, a defined production stencil, and a solder operation covering J2's four shell anchors. These can be prepared by the assembler during normal order engineering; no blanket geometry waiver is justified.

No probability of success is assigned. CAD checks, manufacturer land guidance and a prototype build cannot establish flight, thermal, EMI or firmware performance.

## Exact source and evidence inheritance

The [complete source qualification](controller-r3s-p6-independent-validation/final-fafa9c3f/complete-source-qualification.json) reports ERC/DRC/open/parity counts of zero, 85 live routed nets, 5,345 actual copper contacts, 839 pad/track contacts, 412 vias and 303 reference-plane attachment checks. Its negative control rejects the P5 narrow HOST_TX_RAW joints. All 151 footprint instances are unchanged from the P5 baseline; the manufacturing lands, paste and corrected supplier poses can therefore retain their established P4/P5 dispositions.

This audit independently re-extracted D4, J2–J5, U2, U11 and U13 directly from P6 in [native geometry evidence](controller-r3s-p6-manufacturing-readiness-native.json). D4 has two exact 0.55 × 0.80 mm rectangles. J2 has the corrected two front 0.60 × 1.40 mm slots, two rear 0.60 × 1.70 mm slots, and no shell paste. J3 has eight SMT lands and no drilled lead. Source bytes were unchanged.

Current full-board [mask/hole census](controller-r3s-p6-independent-validation/final-fafa9c3f/advisories/advisory-clearance-census.json) finds foreign mask clearance at least 0.100 mm on each face and foreign via-hole-to-copper clearance at least 0.225499 mm. These are exact-P6 measurements, not an extrapolation from capped supplier result lists.

## Fabrication selections that close the generic PCB concerns

Use the specified six-layer JLC06161H-3313 stack, nominal 1.6 mm, 1 oz outer / 0.5 oz inner copper, ENIG, green mask and white silk. The [current JLC stack table](https://jlcpcb.com/impedance) confirms the 0.0994 mm outer dielectrics, 0.55 mm cores and 0.1088 mm middle dielectric. Preserve the 90-ohm USB pair specification, W=0.1392 mm / gap=0.1600 mm, L1/L2 and L6/L5. The recorded calculator result is design evidence; controlled-impedance CAM/coupon acceptance is an order output.

The [current rigid-PCB capabilities](https://jlcpcb.com/capabilities/Capabilities) support these specific selections:

- Seven 0.35/0.20 mm vias have a 0.075 mm radial annulus and meet the preferred via diameter-minus-drill difference of 0.15 mm. Choose the priced small-via option; the component-PTH annulus rule is inapplicable to these vias
- Four 0.60 mm plated slots exceed the multilayer minimum and their 1.40/1.70 mm lengths exceed twice their width. Their 0.20 mm copper rings meet the recommended multilayer component-hole ring
- The measured mask and via-hole gaps exceed the applicable 0.09 and 0.20 mm limits. Generic 6-mil mask and 9-mil hole-to-trace green boundaries are stricter than those process minima

Thus these are process selections and supported advisory dispositions, not exceptional capability requests. The legacy phrase “supplier acceptance pending” in the small-via allowlist should not be interpreted as an unresolved local design defect.

Specify epoxy-filled, copper-capped, mask-covered 0.20 mm vias; keep the four component shell slots and NPTH holes open. JLC explicitly permits silk over filled/capped vias with solder mask and allows identifying vias for filling by drill diameter. This supplies a concrete supported treatment for the silk-over-via reports. Confirm the treatment in the CAM production files. [Via-covering specification](https://jlcpcb.com/help/article/pcb-via-covering)

## Disposition of every inherited SMT record

Counts are from [P5's completed production-input comparison](../controller-r3s-p6/review/supplier-p5-evidence/smt-comparison.json), identical to P4. They must be reconciled with the final P6 rerun, not relabeled as its observed counts in advance.

| Finding | Count | Evidence-backed disposition | Remaining consequence |
|---|---:|---|---|
| U2 inner/side edges | 16 red | Native copper contains TI's entire DSG0008A example; lead paste and two EP windows match its example. TI's own nominal side/heel limits can trigger generic no-overhang checks. No land enlargement is justified | Use exact TPS62162DSGR and the intended package orientation; include its stencil requirements in production engineering |
| D4 inner/side edges | 5 red | P6 now implements ST's exact rectangular recommendation. A paste-only controlled test removed one prior edge report, while five remain | Generic package-edge exception supported by exact ST lands; no corrective copper move established |
| U2/U11 EP overlap | 2 red | Paste-only substitution to full EP apertures removed exactly these two reports, with all 17 other category counts unchanged. Values 0.44 and 0.16 reproduce one split window divided by the full EP | Recognition dependency is demonstrated. Retain production split windows; the full-EP diagnostics are not production files |
| D4 overlap | 2 yellow | Exact ST rectangles still produce 0.89. ST's maximum terminal envelope also falls below the generic 0.90 boundary on its recommended lands | Document manufacturer-pattern exception; do not enlarge to force green |
| J3 edge | 1 red | Native nominal body inset 0.625 mm and nearest copper inset 0.425 mm; no native clipped land. An older indexed C7527621 listing flags a fixture; the newer retained live capture has no such notice | Real assembly handling condition, closed by the actual carrier/fixture design, not by dismissing a row |
| J4/J5 edges | 2 yellow | JST pattern/body registration supports the intended side-entry placements; same nominal insets as J3 | Actual two-sided panel/rail/nozzle/depanel access must work with the sockets |
| J3 through-hole class | 1 yellow | Exact selected part and manufacturer drawing are SMD-only, as is native geometry | Model/classification exception; adding holes is wrong |
| J2 outline clip | 1 yellow | 8.94 mm is shell width, not overhang depth. Manufacturer-datum calculation gives about 0.03 mm nominal mouth projection; all mounting features remain on-board | Intentional near-flush connector. Carrier clearance is a production condition; mating plug/enclosure fit is a first-article check |

Detailed primary comparisons are preserved with [TI/U2](../controller-r3s-p6/review/smt-manufacturer-evidence/u2/U2-P3-SMT-disposition.md), [ST/D4](../controller-r3s-p6/review/smt-manufacturer-evidence/d4/README.md), [Winbond/U11](../controller-r3s-p6/review/smt-manufacturer-evidence/u11/README.md) and [connectors](../controller-r3s-p6/review/smt-manufacturer-evidence/connectors/README.md). Their historical P3 dimensions are explicitly superseded where P4 corrected D4 corners and J2 front slots. [Controlled diagnostic provenance](../controller-r3s-p6/review/smt-manufacturer-evidence/controlled-diagnostic-disposition.json) establishes which changes were test-only.

U11's copper provides full nominal terminal coverage and at least 93.61% over the examined centered dimensional cases. It differs from Winbond's suggested generic SpiFlash land/stencil pattern; those geometric calculations do not certify placement tolerance or solder-joint yield. This is a specific retained assembly-pattern choice to review with production engineering, not an unexplained 16% copper overlap.

### J3 exact-part hole classification closure

The manufacturer sheet linked to C7527621 was independently viewed: [XDWF-0910-**P drawing](controller-r3s-manufacturing-sources/lian-xin-c7527621.pdf), SHA-256 `1e1c610ad8dd8029201131fba4ac2afc3aed201575aeb5e34632bfc090f3269a`. Its title identifies a 1.0 mm SMT 90-degree wafer; the six-circuit row gives A=5.0 and B=8.0 mm. It depicts surface contacts and surface hold-downs, with no locating-peg or through-hole PCB requirement. The PCB pattern specifies 0.60 × 1.55 mm contacts on 1.00 mm pitch, 1.20 × 1.80 mm anchors, 5.55 mm total pattern depth and a 0.70 mm first-contact-center to anchor-inner-edge offset. Fresh P6 measurements match all those dimensions; all eight drills are zero. Native rounded corners are not a literal reproduction of the drawn rectangles, but that does not create missing holes. The older family-style footprint name is not the evidence. **The 5.88 mm through-hole record is closed as a false classification of this selected part.** Unspecified cavity numbering and fixture support remain separate concerns.

## Four production deliverables that remain outside local CAD closure

1. **Placement/polarity file.** Preserve the user's corrected 79-row CPL, including ten rotations and J2's pickup offset; use the native assembly drawing as the physical pad/pin reference. Before assembly, obtain the final supplier 2D production placement view for both faces and verify physical pin-1/cathode markings against it. Focus on U1/U4/U6/U8/U10/U11/U12/U13, Q1/Q2, J2 and the symmetric U2/D4 cases. Zero missing-pad or overlap errors do not prove electrical orientation. JLC requires this production-file check; 3D/WebGL is not necessary for these SMT parts. [Assembly terms, DFM §6](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-assembly-service)
2. **Carrier and fixture.** Use Standard double-sided PCBA with JLC-added tooling/rails/fiducials or its accepted carrier. A missing customer-designed array is not itself a blocker: JLC offers panel generation and adds required production features. The actual layout must preserve J2/J3/J4/J5 mouth, bottom-component, nozzle and depaneling access. The newer retained J3 live capture (2026-10-02 20:26:24 UTC) has no fixture notice; the older indexed listing cannot establish a current mandatory fixture. Confirm actual connector support/fixture suitability during order engineering. The sockets are inside the bare-board outline but below the general 2.5 mm body-to-edge guideline, so this particular production accommodation must exist. [Panel service](https://jlcpcb.com/help/article/panelizing-your-pcb-for-assembly), [rail guidance](https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order), [J3 exact listing](https://jlcpcb.com/partdetail/Lian_XinTechnology-XDWF_091006P/C7527621)
3. **Production stencil definition.** Explicitly require the real U2/U11 split-EP apertures, with no diagnostic full-EP replacement. TI's U2 example is 0.125 mm thick; U13's example is 0.10 mm. The assembler must choose and record a compatible global or step-stencil treatment and hidden-joint inspection. This cannot be inferred from matching aperture XY. Crucially, JLC regenerates the SMT stencil after single-board verification instead of copying the supplied paste Gerbers; custom aperture requirements belong in order remarks. Its stated workflow supports step-stencil evaluation. [Current SMT stencil workflow](https://jlcpcb.com/help/article/smt-stencil-data-prepared-for-smt-orders)
4. **USB shell solder operation.** Explicitly include soldering all four J2 S1 plated shell anchors. Native paste is absent there; contacts-only reflow would leave the mechanical joints unproven. Specify an accepted manual/selective or other qualified shell-joint operation and inspect it. C165948 is sold as SMT assembly, so automatic selection does not independently establish which secondary shell process will occur. [Exact USB SKU](https://jlcpcb.com/partdetail/C165948), [JLC manual through-hole service](https://jlcpcb.com/help/article/pcb-assembly-faqs)

### Concrete stencil instruction for the eventual order

Recommended request, not yet sent: “Review a top-side 0.12 mm base stencil with a 0.10 mm U13 region, and a 0.10 mm bottom stencil. Preserve U2's eight 0.50 × 0.25 mm R0.05 lead apertures and two 0.90 × 0.70 mm R0.05 EP windows; preserve U11's four 1.37 × 1.73 mm R0.25 EP windows. Do not replace split EP windows with full openings. Confirm the actual step boundary, surrounding-aperture clearance and deposited volumes before assembly; identify any aperture adjustment for approval.”

Both 0.10 and 0.12 mm are published standard foils, and [JLC offers step-stencil production](https://jlcpcb.com/resources/jlcpcb-stencil). This is a feasible manufacturing route to evaluate, not an assertion that a custom 0.125 mm foil is available or that a step is mandatory. At unchanged XY, U2's proposed 0.12 mm foil delivers 96% of the 0.125 mm example's theoretical volume, while the U13 region retains its example thickness. Calculated rounded U2 lead-aperture area ratio at 0.12 mm is about 0.724; it does not present an obvious paste-release contradiction. [Native calculations](controller-r3s-p6-manufacturing-readiness-native.json) record the values. Actual transfer, joint formation and a practicable step boundary require the stencil engineer's production definition. JLC may instead propose a qualified common-thickness solution; it must identify the thickness and any aperture changes rather than silently regenerate them.

The first three outputs are normally created or finalized inside an actual PCBA order. Read-only public research cannot prove their contents for an order that does not yet exist. No supplier contact, upload, order, CAD mutation or CPL edit was made in this audit.

## Can public EasyEDA/JLC geometry prove the exact supplier zero angles?

**No such binding was established.** JLC's official FAQ describes tape/reel orientation as the intended zero convention, while expressly warning that CAD and JLC zero definitions can differ. It says the preview red dot is a component marking, not a universal pin-1 identifier, and explains that its engineers resolve orientation against silk. [JLC orientation FAQ](https://jlcpcb.com/help/article/pcb-assembly-faqs-part-2)

JLC's current [polarity guide](https://jlcpcb.com/help/article/component-polarity-and-orientation-identification-guide) recommends its/EasyEDA's footprint libraries as references. It does not bind a public library revision, pad-number transform or tape/reel lot to the C-code model loaded in this project's analyzer. A community footprint, a symmetric geometric fit, or a general counterclockwise rotation rule is insufficient to certify these exact ten corrections. The smallest conclusive evidence is the final order's 2D placement drawing with visible package markings, exact selected MPN/C-codes and final corrected CPL. A supplier-provided model-to-pad mapping for those exact order items would also suffice.

## First-article work, distinct from permission to fabricate

After fabrication/assembly: inspect hidden and shell joints; check unpowered shorts and polarity; power initially with current limiting; confirm rails, mux switching, USB attachment/current policy, HSE startup and peripherals; verify J3's actual mating harness and cavity convention before applying power; measure input-path loading/temperature within its 1 A combined budget; check the near-flush USB plug and enclosure. Broader thermal, EMI, firmware and application testing remain hardware qualification. These checks do not require another speculative CAD revision before manufacturing a prototype.

Structured phase/status/closure requirements are in [the gate list](controller-r3s-p6-manufacturing-readiness-gates.json). Final package verification and the final P6 supplier rerun are owned separately and should replace their pending entries when evidence is available.


### Sourcing-evidence correction, 2026-10-03 18:07 UTC

The maintained sourcing record contains newer live catalog evidence than the indexed public pages used above. It records no J3 fixture notice; therefore a SKU-mandated fixture is not established. Actual carrier/support clearance remains a production-engineering check. See [bounded sourcing recheck](controller-r3s-p6-sourcing-recheck-20261003.md). This correction changes no copper, footprint or assembly pose.
