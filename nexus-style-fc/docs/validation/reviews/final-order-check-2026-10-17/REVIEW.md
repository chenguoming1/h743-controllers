# Final pre-order review — 17 October 2026

**Recommendation: HOLD the assembled main-board order.** Native geometry and export consistency checks pass, but C9 VCAP compliance and supplier-specific fabrication/assembly acceptance remain unresolved. The latest USB correction does not close those gates. No order, payment, component substitution, CAD edit or supplier message was made during this review.

Reviewed saved Git revision `555d5ee` (USB rerouted for 90ohm). This report covers the main assembled PCB plus child board requested by the owner.

## Exact order files checked

| Item | SHA-256 |
| --- | --- |
| Main PCB | `9b65ab90e9dfeecf8a440e4f1b522658419ee2d56a4e27513e03e35bf77e16ac` |
| Main Gerber ZIP | `bb8fd82bbd7b350da7e54eec824241b7af8f125061c9c5e2e6cc442fd68b9331` |
| Child PCB | `6d9314f769088949b64ade2e3b34fc67641186d3c02edc409738440645df874f` |
| Child Gerber ZIP | `220a5538215ab0a829b9129b38530612ca728193e13607ce38c0b8052dd3a36c` |

[Source/CAM binding](source-and-cam-binding.json) records both PCB/project/schematic/ZIP/BOM/CPL sets. Both ZIPs pass integrity and member comparison: 16 main / 14 child members exactly match loose CAM. Their source hashes match the source-bound USB and latest child-cleanup export reports. No regeneration was needed. Both native zone refills, saved only to disposable temporary copies, produce **byte-identical PCBs**; see [refill check](refill-check.json).

A fresh BOM/CPL export to temporary directories is byte-identical to all four existing assembly CSVs. Main has **51 groups / 83 parts / 83 placements**; child has one populated header. This includes the existing bottom-angle convention and U10's reviewed 270-degree correction. Native front/back poses and part identities are preserved. Actual order inventory, assembly preview acceptance and supplier production settings are not established by these exports.

## Fresh native checks

KiCad CLI 10.0.6, all severities, all track errors and schematic parity; source files were not saved or refilled in place.

| Check | Errors | Warnings | Opens | Schematic parity |
| --- | ---: | ---: | ---: | ---: |
| Main ERC | 0 | 2 | — | — |
| Main DRC | 0 | 10 | 0 | 10 included in warnings |
| Child ERC | 0 | 0 | — | — |
| Child DRC | 0 | 11 | 0 | 0 |

The two main ERC findings are L1/L2 `PowerInductor` library-copy mismatches. Main parity findings are the previously recorded footprint/filter identities; child warnings are the 11 bare-contact missing courtyards. Existing four ERC ignored-check settings remain; no rules/exclusions were altered.

The wrapper `validate_project.sh` stopped before ERC/DRC because its recursive dependency scan includes unrelated untracked `hardware/.history` snapshots with stale relative model paths. The four native checks were therefore run directly. The actual two canonical boards' local model paths pass, and BOM/CPL exports resolve both projects; this historical-snapshot path issue is not a missing dependency in the boards being ordered. [Native manufacturing screen](native-manufacturing-screen.json), [counts](native-counts.json), four raw ERC/DRC JSON reports.

## Current website screening

The existing source-matched [main PCB result](https://jlcdfm.com/viewer?pcbUploadFileId=634351113752236033) was reopened; all 29 category triples still match the USB correction report. Width, trace spacing, pad spacing, sharp corners and mask-to-trace have no danger/warning counts. Existing via-to-pad, annular, mask, short-slot and silk flags remain. The 207 displayed danger / 161 warning totals include capped 100-result silk/annular categories and are not unique defect counts or a clean DFM pass.

For a **fresh SMT run**, the exact current BOM and CPL were uploaded to that same main Gerber project. JLCDFM confirmed **51 detected / 51 confirmed groups**, saved the import and rendered component models. Assembly analysis completed: **25 danger / 13 warnings**, across 18 categories. No models, parts, placements, rotations or DFM rules were manually changed.

| Current assembly category | Danger | Warning |
| --- | ---: | ---: |
| Component to board edge | 4 | 7 |
| Lead to hole | 11 | 0 |
| Pin left edge | 8 | 0 |
| Pin right edge | 2 | 0 |
| Through-hole misalignment classification | 0 | 6 |

Missing-pad, pin-outer-edge, lead-overlap, missing component holes and collision dangers are zero. The old assembly check had 24 danger / 13 warnings; it must not be presented as the current result. The current lead-hole top rows identify U3, J4, C19, J5, U2 twice, U11 and J3; bottom rows U5, R14 and C8. These are geometric/model flags, not proved electrical shorts. All four edge-danger references remain J2 (0.33 mm), R11/R12 (0.45 mm) and U4 (0.50 mm); request factory panel/assembly handling acceptance. The six through-hole warnings remain SW1, F2, U1 twice, F1 and D4 with **null measurements**; no evidence supports inventing a CPL offset for them. The earlier [LED/fuse pin-edge disposition](../pin-edges-2026-10-17/REVIEW.md) remains limited to those specific unchanged footprints.

The existing source-matched [child PCB result](https://jlcdfm.com/viewer?pcbUploadFileId=634336887604203522) remains **0 danger / 38 warnings** (12 annular, 26 through-hole-to-SMD). It was reopened and captured, not reuploaded or claimed to be a new analysis. Exact PCB/CAM hashes are unchanged. Main SMT results, PCB category tables and inspected detail tables are retained in this directory.

## Items to resolve before releasing production

1. **C9 / VCAP component compliance.** Current native C9 connects VCAP directly to GND and the BOM specifies Samsung **CL10A475KA8NQNC / C69335**, shared with C5. ST's current **DS11853 Rev 9, page 105, Table 19** specifies **4.7 µF and ESR between 0.1 and 0.2 Ω** for the LQFP64 VCAP1 capacitor. No verified ESR acceptance across the relevant conditions is available for the selected part. This is an unresolved MCU regulator-stability specification, not proof that a fabricated unit will fail. Resolve with a documented compatible capacitor/network or ST-supported implementation; do not silently replace the shared C5/C9 group or add an arbitrary resistor. [ST datasheet](https://www.st.com/resource/en/datasheet/stm32f722ie.pdf), [exact Samsung product page](https://product.samsungsem.com/mlcc/CL10A475KA8NQN.do).
2. **Main via filling and assembly process.** Fresh native hole/pad screening finds **16 nominal pasted-pad intersections involving 15 unique 0.20 mm via holes**, all with zero effective paste margins. They include C8, C19, C26, U2, U3, U5, U11, U1, J3–J5, R14 and C3; one hole intersects pads on both faces. This screen uses the effective native pad polygons and circular drill disks, not a factory-approved stencil. Specify **epoxy-filled AND copper-capped POFV for all 227 main 0.20 mm vias**, which covers these holes; do not fill component holes. C8 alone is not the complete process requirement. JLC distinguishes this from tenting/ink plugging and recommends production-file confirmation. [Current via-covering guide](https://jlcpcb.com/help/article/pcb-via-covering).
3. **Factory stack and copper acceptance.** Main requires **JLC06161H-2116A, six layers, nominal 1.6 mm category, 1 oz outer / 0.5 oz inner**, and the stated USB **90 Ω differential ±10%** requirement. Child requires **JLC041622-3313, four layers, nominal 1.6 mm, 2 oz outer AND inner**. Do not use default stacks/copper. USB calculation is about 90 Ω on the named main stack, not full-port electrical certification. Child electrical calculations assumed at least 60 µm outer, 55 µm inner and 18 µm **local** barrel wall; JLC's public 18 µm **average** plating does not guarantee that local minimum. Factory acceptance/inspection is pending. Child 1.00 mm header holes / 1.50 mm lands have 0.250 mm radial annulus, just below JLC's published 0.254 mm 2 oz PTH guidance; obtain acceptance or review land changes. [JLC capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [stack reference](https://jlcpcb.com/impedance).
4. **Slots and matched fit.** Current native J6 has four approximately **0.85 × 0.60 mm plated slots**. Width is above JLC's multilayer minimum but length/width is 1.42, below its generic **2×** length guidance; request explicit finished-slot and shell-pin assembly acceptance. Child tabs are **9.30 mm wide**, with two **9.80 × 2.10 mm R0.50** main slots. A centred perpendicular section fits nominally with 0.146 mm corner radial reserve. An illustrative independent default routing/thickness tolerance combination (slot 9.60 × 1.90, tab 9.50, child thickness 1.76 mm) gives **0.122 mm corner interference**, even without pitch, bow, burr or insertion-angle errors. This does not predict every board failing; it demonstrates default nominal selections do not guarantee fit. Agree matched finished dimensions/tolerances or review geometry before production. [Actual outlines](critical-parts-and-outlines.json), [bounded fit screen](mechanical-tolerance-screen.json).
5. **Retained electrical qualification.** D4 SMF13A is still on VX; its catalog 21.5 V rated-pulse clamp is above U14 TPS629210's **18 V VIN/EN absolute maximum**. This does not predict 21.5 V at the actual 7.4 V BEC; protection coordination against the real transient remains unqualified. The [TI datasheet](https://www.ti.com/lit/ds/symlink/tps629210.pdf) confirms the 18 V limit. Header contacts remain rated 3 A/contact; the child copper upgrade is not a 20 A complete-system rating. Reset, firmware, full-port USB, thermal/load and mechanical/flight tests still require hardware validation.

## Prepared supplier instructions and scope

[Supplier requirements](supplier-requirements.txt) provide the exact process/stack/fit/assembly requests for review. They have **not** been sent or accepted. No JLC quote/cart/order was visible in the selected Chrome profile; selected order settings, part stock, price and final production preview were therefore not checked. The fresh DFM upload is not an assembly order.

Board, schematic, project, BOM/CPL and CAM bytes remain unchanged. Only this final-check evidence directory was created. Unrelated owner `.history` and `routing-wip` content was preserved.
