# Final manufacturer-body and assembly supplement

This supplement binds r61 source SHA256 `5a51610cc1569958442f97407e11533b646b1e0d8997d86356b8968dce50487e` and cap-star `candidate-6.json`, SHA256 `443dac4ddd6d5e3dd4e7fa31c5348b9ec1d9c0f37247df890be02b735133558a`. No PCB or source file was edited. The exact approved placements remain C27 (101.870,124.320) B180, C31 (105.820,126.300) B0 and D5 (102.280,126.180) B180.

## Exact D5 manufacturer package

The manufacturer-authored [JSCJ B5817WS–5819WS Rev. 1.0 datasheet](https://uploadcdn.oneyac.com/attachments/files/brand_pdf/jscj/65/1E/JSCJ-B5819WS.pdf), page 3, is saved as `D5-JSCJ-B5819WS.pdf` (SHA256 `d496fc5793dd7a09e8fdc421c62f939321a7b2f9082f3ad4763e8f9c1b9e6123`). The rendered `D5-package-page.png` was inspected directly. It is the exact non-AD JSCJ B5819WS package family, matching selected C22624.

- Body E maximum 1.800 mm along the pin axis; D maximum 1.400 mm transverse.
- Total lead span E1 maximum 2.750 mm; package height A maximum 1.000 mm.
- Body standoff A1 minimum 0.000 mm, maximum 0.100 mm.
- General ±0.05 mm tolerance applies to unspecified dimensions; explicit min/max bounds are not inflated a second time. This package table supplies no component-placement or soldermask-registration tolerance.

At the approved D5 position, the centered maximum body occupies x 101.380–103.180, y 125.480–126.880 mm. A conservative body-plus-leads rectangle occupies x 100.905–103.655, y 125.480–126.880 mm. The unchanged D5 courtyard centerline spans x 100.460–104.100, y 125.380–126.980 mm. Thus the full maximum package envelope fits with 0.445 mm pin-axis and 0.100 mm transverse margins to that centerline. It intersects no neighboring courtyard or fixed connector/NPTH drill; both maximum envelopes pass the 0.300002 mm board-edge screen. D5 maximum body to C27 maximum body has a 0.435 mm nominal XY gap. These are centered CAD envelopes, not placement-tolerance or assembly certification.

## Final two nearby vias

All dimensions below are mm. Both vias use 0.450 copper diameter and 0.200 drill.

| Via | Center | Drill bounds | Copper annulus bounds | D5 maximum-body relationship |
|---|---|---|---|---|
| Moved VX, original UUID `7cb6eb35-a8ab-4a2b-8f3a-c47d9f3fb630` | (101.800,125.650) | x 101.700–101.900; y 125.550–125.750 | x 101.575–102.025; y 125.425–125.875 | Entire drill is beneath the maximum body; copper also extends under body. |
| New VSYS cap-star | (102.350,125.300) | x 102.250–102.450; y 125.200–125.400 | x 102.125–102.575; y 125.075–125.525 | Drill is outside body by 0.080 mm; copper annulus overlaps body envelope by 0.045 mm. |

Neither annulus overlaps any actual front/back pad mask or paste opening. The source VX via has inherited front/back tenting and zero mask expansion; preserve those settings. The candidate JSON does not encode new-via mask settings, so the sole PCB lane must explicitly verify the new star via inherits the board’s front/back tenting and zero mask expansion. No filling, plugging, capping or covering process is implied.

The final star annulus is 0.080 mm from C27 positive paste and 0.030 mm from C27’s maximum body. This improves the earlier candidate-3 paste gap of 0.005 mm. Positive CAD separation is not a guarantee against fab or placement registration error.

A1 can be zero. Therefore the D5 package gives no guaranteed clearance over soldermask tents or copper topography. Bottom tent integrity, solder wicking/balls, seating/coplanarity and standoff must be qualified with the intended fabricator and assembly process. Do not rely on the 0.100 mm maximum standoff as available clearance. If this construction cannot be qualified, stop for a separately reviewed via relocation or approved fabrication treatment.

The two previously disclosed under-C27 GND holes remain at (101.825,123.725) and (101.925,124.775), each 0.200 drill/0.450 copper; `assembly-envelope.json` records their exact openings. Capacitor maximum height remains 1.450 mm independently of any generic 0805 3D model, and actual enclosure/child-board Z clearance remains open.

## Independent final screen and acceptance gates

`merged-star-review-candidate-6.json` records empty inter-net copper, courtyard, edge, via/paste and via/drill conflict arrays. Explicit copper, without relying on filled zones, connects C27 GND, U14 GND, J4.6, retained ground via 097c5d92, the new GND via and every external port of the two removed F.Cu GND donors. C31’s separate local GND component and the moved plane-only ground stitch still require finite post-refill plane attachments. The exact manufacturer D5 dimensions are now resolved; physical fabrication/assembly, native refill/DRC, current-loop review, Z clearance and actual capacitor voltage/transient/lifetime qualification remain open.

Implementation fields are in `physical-transaction-final.json`; this must be combined with the coordinator’s complete candidate-6 route transaction and frozen schematic overlay. Older shape-probe capacitor pad UUIDs are deliberately excluded from that implementation handoff.

Candidate 6 retains every candidate-5 position and widens only GND_inner on In1.Cu from 0.127 to 0.300 mm. Its geometric screen was independently rerun. This preserves the coordinator’s nominal copper cross-section comparison; it does not independently prove return impedance or post-refill attachment.
