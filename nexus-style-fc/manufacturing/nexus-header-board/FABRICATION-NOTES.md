# Four-layer child: review-only fabrication settings

Source: `12d537492ebb7aa347e30c78c758efbdbd6e238425f0095282cbf7188e872e23`.

- **Four copper layers**, nominal **1.6 mm**, **2 oz outer and 2 oz inner**, ENIG.
- Stack reference: **JLC041622-3313**, as displayed by [JLC's stackup selector](https://jlcpcb.com/impedance) on 2026-10-17 with 1.6 mm / 2 oz outer / 2 oz inner selected. Do not substitute the default 0.5 oz inner copper.
- Layer assignment: F.Cu existing copper; **In1.Cu VX**; **In2.Cu GND**; B.Cu signals and power copper.
- CAD copper thicknesses: 0.070 / 0.061 / 0.061 / 0.070 mm. Dielectrics: 0.1835 / 0.960 / 0.1835 mm; outer prepregs are two 3313 sheets, 0.107 + 0.0765 mm each side. The numerical stack sum including two nominal 0.010 mm masks is 1.609 mm; the order thickness remains nominal 1.6 mm. Final complete thickness and matched-tab fit require supplier agreement and physical verification, including the earlier proposed 1.60-1.65 mm finished-thickness envelope.
- Copper analysis assumes **at least 60 um outer, 55 um inner and 18 um local plated-hole wall**, with a conservative 1.65 mm barrel-length screen. These are required calculation bounds, not claims that the public order selector guarantees those minima. Obtain acceptance and inspection/coupon evidence before relying on the calculated losses.
- Added vias: 27 power vias, **0.60 mm copper / 0.30 mm drill**, tented; original 5 vias and all header/joint geometry remain. No soldermask openings or stencil changes were added.
- ZIP contains **14 Gerber/job/drill files**, including both inner-plane Gerbers. BOM and CPL are unchanged.

The PCB has no controlled-impedance routing requirement. Selecting the named laminate is for the power/fit design; the Gerber job does not claim impedance control.

This improves PCB copper resistance for the approximately 20 A stress case. It does **not** make the retained 3 A header contacts, unspecified mating plugs, or the Hobbywing V4's 10 A continuous BEC into a 20 A continuous system. Current waveform, voltage sag, hotspot temperature and physical joint/fit qualification remain open. See the [engineering review](../../docs/validation/reviews/child-full-load-2026-10-17/REVIEW.md).
