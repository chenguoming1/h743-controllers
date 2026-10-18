# Main-board fabrication requirements — two assembled prototypes

Current source/CAM hashes and checks: [standard-stack adaptation](../../docs/validation/reviews/standard-stack-2026-10-17/REVIEW.md), [binding](../../docs/validation/reviews/standard-stack-2026-10-17/binding.json). Main assembly: 84 placements, 53 BOM groups, both sides.

## Required standard stack

Specify **JLC06161H-3313**, six layers, nominal **1.6 mm**, **1 oz outer / 0.5 oz inner**, ENIG. JLC's calculator labels it standard, finished **1.54 mm ±10%**. In1 and In2 copper content were exchanged to give the USB pair a close, continuous L3 ground reference. Files from the earlier 2116A revision are incompatible with these instructions.

| Top to bottom | Material/function | Thickness mm | Model Er |
| --- | --- | ---: | ---: |
| F.Cu / L1 | Outer copper | 0.0350 | — |
| Dielectric 1 | 3313 PP | 0.0994 | 4.05 assumed |
| In1.Cu / L2 | Mixed signals / GND pour | 0.0152 | — |
| Dielectric 2 | FR4 core | 0.5500 | 4.6 |
| In2.Cu / L3 | GND | 0.0152 | — |
| Dielectric 3 | 2116 PP | 0.1088 | 4.16 |
| In3.Cu / L4 | USB pair / mixed signals | 0.0152 | — |
| Dielectric 4 | FR4 core | 0.5500 | 4.6 |
| In4.Cu / L5 | GND | 0.0152 | — |
| Dielectric 5 | 3313 PP | 0.0994 | 4.05 assumed |
| B.Cu / L6 | Outer copper | 0.0350 | — |

Copper plus dielectric sums to 1.5384 mm. Manufacturing thickness and dielectric tolerances require supplier confirmation. The 4.05 outer PP Er is a modelling assumption; the screened internal pair is dominated by the 2116/core materials. See [JLC calculator](https://jlcpcb.com/pcb-impedance-calculator).

## Controlled impedance

Nominal design target **90 Ω differential**, USB_DP/USB_DN matched trunks on **L4 / In3.Cu**, **0.132 mm drawn width / 0.165 mm edge gap**. Near reference **L3 / In2 GND**, 0.1088 mm PP; far reference **L5 / In4 GND**, 0.550 mm core. Retain the L4 pour-only keepout and both reference planes under the matched trunks.

The source-bound local six-layer model estimates 90.3–90.6 Ω at five sections under the documented etch/material assumptions. JLC's live synthesis gives approximately 0.1313 mm width with 0.1651 mm requested gap. These are nominal calculations, not measured qualification. Paid impedance testing was explicitly declined by the owner. The quote states no impedance test/report is provided; do not infer a free coupon from the general JLC help page. Review any proposed factory geometry adjustment.

L2 is now mixed routing. Top-side signals have a less direct return reference than the former custom stack; the changed top SPI/I2C pieces are short (about 0.7–3.2 mm). Bottom-side crystal, VCAP and MCU routing retain the adjacent L5 ground. Full-port USB launches, vias, ESD parts, EMI, sensor and power behaviour still require prototype tests.

## Assembly and drilling

Require **epoxy-filled, copper-capped (POFV) treatment for ALL 228 main-board 0.20 mm vias**. Several lie in pasted lands, including C8. Ordinary tenting or ink plugging is insufficient. Do not fill the four **0.85 mm USB component mounting holes** or NPTH holes.

J6 now uses four 0.85 mm round plated holes at its original centers; the custom copper lands preserve the original oval and add a 1.15 mm diameter center to maintain 0.15 mm nominal annulus. The holes enclose the original 0.85 × 0.60 mm nominal slots. The connector drawing recommends 0.8 ±0.1 mm PCB and shows 0.95 mm shell legs. On this 1.6 mm board the legs do not protrude. **Factory must accept and inspect the shell-joint soldering method and mechanical retention**; do not assume normal bottom-side protruding-pin soldering.

C9 is C368809 (4.7 µF 0402), with R23 C2766886 (0.12 Ω ±5%, 0402WGJ012KTCE) in series with its VCAP branch. C5 remains C69335 (4.7 µF 0603). D4 is C1973343 / Littelfuse SMF9.0A for the specified regulated 7.4 V BEC. **Do not connect raw flight battery or a rail above 9 V.** Keep exact parts, sides, centers and CPL rotations; U10 is already corrected to 270°. Verify D4 cathode on VX / anode GND and all pin-1/polarity marks in production preview. No automatic substitutions without electrical and footprint review.

Read [ORDER-INSTRUCTIONS.txt](../ORDER-INSTRUCTIONS.txt) and the [current engineering review](../../docs/validation/reviews/order-fixes-2026-10-17/REVIEW.md). The child board uses a separate four-layer 2 oz stack; do not apply the main stack to it.

## Quote upload

Use `nexus-style-fc-jlc-quote.zip`: the 16 current CAM members plus `IMPEDANCE-CONTROL.jpg`. The previous custom-stack quote record is historical. The standard quote remains on the first page with manual production/placement approval; no order or payment has been submitted.

R23 purchasing update (18 October 2026): C2766886 replaces the low-stock C423234. Same 0402 footprint and placement; copper, Gerbers and CPL are unchanged. See [replacement review](../../docs/validation/reviews/r23-replacement-2026-10-18/REVIEW.md). VCAP startup/stability remains a prototype bench check.
