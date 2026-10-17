# Main-board fabrication requirements — USB 90 ohm revision

Engineering review export; existing assembly, process and physical qualification gates remain open. Applies only to main PCB SHA-256 `9b65ab90e9dfeecf8a440e4f1b522658419ee2d56a4e27513e03e35bf77e16ac` and Gerber ZIP SHA-256 `bb8fd82bbd7b350da7e54eec824241b7af8f125061c9c5e2e6cc442fd68b9331`.

## Required order stack

Specify **JLC06161H-2116A**, six layers, nominal 1.6 mm order category, **1 oz outer / 0.5 oz inner copper**, ENIG. JLC's current calculator labels this special stack **finished thickness 1.56 mm ±10%**. Obtain supplier confirmation of the actual materials, finished copper and pressed dielectric dimensions. Selecting generic six-layer 1.6 mm or the default 3313 stack does not reproduce this design.

| Top to bottom | Material/function | Thickness mm | Model Er |
| --- | --- | ---: | ---: |
| L1 / F.Cu | Outer copper | 0.0350 | — |
| Dielectric 1 | PP 2116 | 0.1164 | 4.16 |
| L2 / In1.Cu | Ground | 0.0152 | — |
| Dielectric 2 | FR4 core | 0.1300 | 4.6 |
| L3 / In2.Cu | Signals | 0.0152 | — |
| Dielectric 3a | PP 2116 | 0.1164 | 4.16 |
| Dielectric 3b | FR4 bare core | 0.7000 | 4.6 |
| Dielectric 3c | PP 2116 | 0.1164 | 4.16 |
| L4 / In3.Cu | USB differential trunk / signals | 0.0152 | — |
| Dielectric 4 | FR4 core | 0.1300 | 4.6 |
| L5 / In4.Cu | Ground | 0.0152 | — |
| Dielectric 5 | PP 2116 | 0.1164 | 4.16 |
| L6 / B.Cu | Outer copper | 0.0350 | — |

Copper plus dielectric sums to 1.5564 mm. The CAD also retains 0.010 mm mask on each face, making its stack sum 1.5764 mm; the general board thickness is the nominal 1.6 mm category. These are not assertions of a measured finished thickness. See [JLC stack/material data](https://jlcpcb.com/impedance) and [calculator](https://jlcpcb.com/pcb-impedance-calculator).

## Controlled impedance

Request **90 Ω differential, ±10%** for the USB_DP/USB_DN trunk on **L4 / In3.Cu**, **0.143 mm nominal drawn width / 0.154 mm edge gap**. It references continuous L5 / In4 ground across a **0.130 mm core**. Far reference is L2 / In1; intervening L3 is mixed routing. The L4 pour-only keepout deliberately removes close coplanar ground around this trunk and must be retained.

The local six-layer copper model predicts approximately 89.7–90.0 Ω under its stated etch/material assumptions. JLC synthesis at 90 Ω with L4 signal, L2/L5 references and 0.154 mm requested gap gives about 0.1455 mm width / 0.1539 mm gap. These small model differences require factory review of final etch geometry and stack tolerances. Confirm the production impedance process, coupon and measured report before claiming controlled impedance. Any proposed trace-width/stack substitution must be reviewed against the routed copper and clearances.

The short USB-C, ESD and MCU breakouts, layer transitions and mounted parts are discontinuities; the complete assembled USB port has not been electrically certified. Test full-speed USB in both cable orientations on the prototype.

## Retained assembly requirement

**C8 pad 2 contains a 0.20 mm drilled via. Require epoxy-filled, copper-capped via-in-pad (POFV).** Ordinary tenting leaves the hole inside the solder-pad opening. Confirm this process in the production files/order.

The child board is a separate four-layer power design with its own [fabrication requirements](../nexus-header-board/FABRICATION-NOTES.md); do not apply this main-board stack to it.
