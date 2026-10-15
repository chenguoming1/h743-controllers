# r51 routing and regulator-loop checkpoint: unfinished, 18 clearance errors

This checkpoint extends draft PR37 from main `80a3f763d5031198b4622402bb73a532676b9be9`. **Do not fabricate or assemble.** The current experimental board is separate from canonical copper.

## Open the exact current candidate

Open [experimental r51 project](metadata-integration/experimental-r51/hardware/nexus-style-fc.kicad_pro). PCB SHA256: `3e3869e15a819c3e8091fe5f73d13ffd5139af07f7fd2c4fe1eafcf0b3fb1b2b`. [Final native findings](metadata-integration/experimental-r51/native-drc.json), [source-bound verification](metadata-integration/experimental-r51/verification.json) and [native execution receipt](metadata-integration/experimental-r51/native-execution-receipt.json) refer to these exact saved bytes.

Final KiCad 10.0.7 checks report **18 clearance errors, zero opens, zero schematic-parity findings and 54 unchanged silk warnings**. Minimum remaining gap is **0.0878 mm**. Fresh native ERC is zero on the unchanged schematic `49f9e0571424d0610e294bdcd6b120a42d04db284ecda9e660428fc587e62699`; its identical receipt/netlist is shared by the canonical and experimental metadata checks. All 347 physical pin/net pairs agree. No fresh violation was suppressed and no new or worsened residual pair was accepted. Inherited ignored checks remain visible and are not claimed passed.

## Complete-contact routing progress

[Lineage verification](lineage-verification.json) binds the published r47 source through these immutable transactions:

- r48: 24 → 21 errors. Full-width, same-layer TP3 GND, J3 sensor power and J1 S3 repairs. Both existing GND vias have finite annular contacts to actual In1/In4 fills; those main-plane geometries were unchanged by r48.
- r50: 21 → 18 errors. Complete CC1/VBUS/VBUS_C donor transaction routes around the fixed-pad choke. VBUS stays 0.250 mm B.Cu. Two compliant ordinary tented vias are added outside paste-bearing pads. The initially tested r49 was rejected for losing shield-spoke copper; r50 corrects that and preserves all 96 inherited J6 shield-spoke regions. R20's local ground via, U7's retained via and all four J6 EPs have finite contacts to the same actual In1/In4 GND components. Each main plane loses 0.799548 mm² and gains 0.403700 mm² locally; this is measured geometry, not an impedance certificate.
- r51: 18 → 18 errors, with a regulator-output improvement. The U10-to-C19 output path becomes **4.400335 mm, entirely F.Cu at 0.250 mm**, removing both previous output vias. Full-width projection lies over the same actual In1 GND component. All eight replacement ports, C18 upstream paths and direct C19 ground are preserved.

Exact transactions, rollback/pre-refill boards, native receipts, physical contact proofs, gap comparisons and actual saved-fill checks are included in each directory. A fresh post-r51 check also preserves all 96 r50 shield-spoke regions and finite R20/U7/J6 contacts. The final metadata pass proves every copper primitive and all filled copper areas unchanged from sealed r51. EN remains isolated; the approved C19 10uF/C19702 selection remains. The inherited 18 pasted-via locations are unchanged and remain a fabrication concern.

## U10 engineering decision and its limits

[Engineering decision](u10-review/DECISION.md) explains why the output-loop improvement is retained despite a measured input-route tradeoff. It was written before fresh r51 validation; the r51 receipts above are the subsequent implementation evidence. TI's non-Q1 TPS709 datasheet says input capacitance is not required for stability, while recommending input bypass for transients, reactive sources, ripple and PSRR. [Exact C18 review](u10-review/C18-input-capacitance-review.txt) finds no demonstrated capacitance-driven input stability violation and no basis for an unapproved substitution.

The new input donor adds **0.389325 mm planar travel and 1.4134 mm modeled barrel travel**. Full-width reference projection is **58.43% B.Cu/In4 and 65.97% F.Cu/In1**, versus 84.19% on the previous F.Cu leg. Projection percentage is not a transient-performance or stability pass/fail threshold. The actual C18/U10/C19 ground paths retain finite contacts to the same main GND components. Startup, BEC/load steps, ringing, ripple/PSRR, sensor-rail disturbance and actual temperature/voltage corners still require electrical validation. C18 is unchanged; no viable fully verified placement move was found in the bounded [placement review](u10-review/C18-placement-review.md).

C18's approximately 0.2501uF manufacturer typical estimate at 7.4V and 0.1913uF separate tolerance/temperature screening value are not guaranteed minima. C19's approved part likewise does not by itself certify the assembled regulator. Nominal 7.4V alone does not rule out line transients.

## Narrow metadata consistency repair

The inherited U10 footprint instance carried `LCSC Part=C82942` and a `ME6211C33M5G-N` library description, despite its actual selected fields being TPS70933DBVR / C89347. The stale donor field is removed and the library description becomes `SOT-23-5 footprint; selected part TPS70933DBVR, LCSC C89347` in canonical and experimental instances. No selected part, schematic, net, placement, pad, copper or shared library changes. [Generator hook and scope tests](generator-review/) enforce the exact main-Nexus/U10/value/LCSC guard. Before/after exports and strict native geometry checks are preserved under [metadata integration](metadata-integration/).

Canonical PCB SHA256 is now `925642c3a3b8e032701ded5587814b91a78f50b1b3819d07aee303a026a70d6c`, solely due to this metadata cleanup. Its native count remains **627 inherited errors: 428 clearance and 199 grouped width findings**, zero opens/parity/ERC and 54 silk warnings. The canonical route is not replaced with the experimental one.

## Header and other release gates

The unchanged header still has **11 fixed copper-edge errors**, zero opens/parity/ERC. The [read-only interface review](header-review/README.md) shows copper recession alone cannot resolve the inherited tab/slot interference. Its root-aware slot/tab/contact/fixture proposal is a design study requiring separate approval and fit/strength/solder qualification; **none of that geometry is implemented**. Source comparison explicitly distinguishes the original proximity screen from current candidate geometry.

The earlier [USB/stack review](../local-r47-checkpoint/usb-review/USB-STACK-REVIEW.md) remains bound to the 29-error source, not this later refill. USB pair routing, actual-stack impedance and return/ESD behavior remain open; r50 repairs CC/power geometry without closing those gates. No arbitrary length/skew cap or exclusively signal-free-plane requirement is imposed.

Power/thermal/fault behavior, ordinary pasted vias, header mechanics, connector mapping and U2 orientation/FSYNC remain unresolved. The 7.4 V BEC / 10 A continuous / 25 A peak goal is not a PCB current rating; raw 6S must never be applied to the FC. CAM/CPL remain historical/stale. BOM selections are unchanged by this metadata-only cleanup, and the full manufacturing package remains on hold. No fabrication or flight readiness is claimed.

The [current single-sheet PDF](../../../docs/schematic-main.pdf), [15-page detail booklet](../../../docs/nexus-schematic-review.pdf) and source ZIP remain unchanged from the approved C19 circuit redraw. Historical checkpoints retain their exact observations and do not override this current status. Absolute execution paths in receipts may be mapped to equivalent local paths when reproducing with KiCad 10.
