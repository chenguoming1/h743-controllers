# USB nominal 90 ohm check — 2026-10-17

**Disposition: the saved USB route is not demonstrated to be uniformly 90 Ω.** Under the saved CAD stack, local 2D estimates are reasonably close to 90 Ω but vary with reference copper. A different fabrication stack can shift them materially. Do not release this route as controlled 90 Ω solely from DRC or the nominal six-layer/1.6 mm selection. This finding does not demonstrate failed 12 Mbit/s USB operation or independently require a prototype reroute.

Main PCB SHA-256: `6295c7ebda6c8a4035064f235072d56e1d6e0ff1b7e6b0402f908ce372ae901e`. The board, project, schematic and manufacturing files were not changed. `sections.json`, `model-input.json`, `results.json`, `etch-sensitivity.json` and `validation-summary.json` bind this study to the saved source.

## Geometry and saved stack

The straight paired trunk is on In3.Cu (physical L4): **0.170 mm width, 0.127 mm edge gap, 0.0152 mm copper**. The nearer In2.Cu/L3 reference is separated by **0.1532 mm prepreg, Er 4.16**; In4.Cu/L5 lies **0.5500 mm away through core, Er 4.6**. Where In2 GND is absent, the farther In1.Cu/L2 plane becomes relevant; the intervening upper core is 0.55 mm, Er 4.6. Thus a single outer-layer microstrip formula is inappropriate.

## Numerical results

| Modeled section | Rectangular copper | Signal etch sensitivity |
|---|---:|---:|
| Saved CAD: solid In2 + In4 references | 81.9 Ω | **84.5 Ω** |
| Saved CAD: In2 absent, solid In1 + In4 references | 93.1 Ω | **96.0 Ω** |
| JLC current standard 3313: solid L3 + L5 references, present 0.170 mm width | 74.7 Ω | **77.2 Ω** |

The signal etch sensitivity uses JLC's published **top width = base width − 0.7 mil**, a 0.01778 mm reduction, while holding nominal base width and gap fixed. Ground and other conductors remain rectangular. Neither case is a fabricated tolerance bound; actual etch shape is unmeasured. [JLC calculator guide, Calculation Parameters Used](https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator).

Actual native copper intervals were extracted across five straight trunk positions, at global Y = 116.0, 118.1, 120.2, 113.4 and 123.4 mm. The models retain local In2/In3 GND and foreign-net cross sections; each foreign net is considered either isolated/floating or ideal AC ground. Solid remote In1/In4 planes are assumed. With the signal etch assumption, differential energy estimates range **83.0–91.8 Ω**; rectangular-copper estimates range **80.3–88.9 Ω**. These are representative local sensitivities, not the impedance range of the entire physical USB path. For asymmetric sections they are not a unique pure odd-mode impedance, and mode conversion is not quantified.

The important result is reference-dependent variation, not a claim that every section is outside a particular USB tolerance. No tolerance was selected in a fabrication order. Material/etch tolerances, actual layer dimensions and the 3D discontinuities remain unqualified.

## Independent manufacturer comparison

The live JLC calculator was configured for six layers, nominal 1.6 mm, 1 oz outer / 0.5 oz inner, **L4 signal with L3/L5 references**, non-coplanar differential pair and **0.127 mm gap**. Its currently recommended **JLC06161H-3313** stack gives **0.1171 mm width for a 90 Ω target**. The result is recorded in `jlc-calculator-visible.txt` and `jlc-calculator.png`.

This stack uses **0.1088 mm** of central prepreg, instead of the CAD's **0.1532 mm**. The screenshot's **4.28 mil** column denotes thickness, not dielectric constant. The calculation here uses Er **4.16** for 2116, from JLC's published material table, and Er **4.6** for core. The earlier interactive observations of 3313, 2116A/B/C and 2116 special stacks did not establish an exact match to the saved CAD stack. This study does not select an order stack. [JLC published material constants and stackups](https://jlcpcb.com/impedance), [live calculator](https://jlcpcb.com/pcb-impedance-calculator).

**Do not copy 0.1171 mm onto this board as a fix.** It is below the project's present 0.127 mm minimum track rule, assumes solid reference planes and omits the actual coplanar copper. It is evidence that the fabrication stack and reference choice must be settled before selecting width/gap.

## Method and numerical checks

`solve_sections.py` solves the two-dimensional electrostatic equation ∇·(ε∇V)=0 using a nonuniform finite-volume grid aligned to conductor and dielectric boundaries. D+ is +0.5 V and D− is −0.5 V. An identical vacuum solve supplies the magnetic normalization. With a 1 V differential excitation, the discrete field energy gives Cdiff = 2U, and the symmetric odd-mode impedance is Zdiff = 1/(c√(Cdiff·Cdiff,vac)). For asymmetric copper this is an energy-based differential estimate. Floating conductors are equipotential with zero net charge.

Independent analytic homogeneous and layered parallel-plate checks agree to floating-point precision. Ideal etched-case refinement from 2.5 to 1.25 µm changes results by at most 0.011 Ω; rectangular local slices refined from 5 to 2.5 µm change by about 0.3 Ω. Increasing the ideal-case domain halfwidth from 2.5 to 4 mm changes impedance by <0.001 Ω. Equation residuals are ~1e−24 C/m and floating charge residuals ~1e−23 C/m. These establish numerical consistency of the specified model, not accuracy against the finished board.

For the independent JLC synthesized width case, this solver gives **90.587 Ω** at 0.1171 mm width with the published 2116 Er=4.16 and the stated etch assumption, approximately **0.65%** above JLC's 90 Ω synthesis target. This agreement supports the scale of the calculation, not its applicability to every discontinuity on the PCB. The live calculator's displayed 90 is an input target, not a measurement of the present route. See `validation-summary.json`.

Crossing traces in a 2D slice are treated as longitudinally uniform conductors. The real crossings have finite length and require 3D analysis for their discontinuity/crosstalk. Also omitted: actual In1/In4 antipads outside the modeled pair corridor, bends, four tapers, uncoupled USB-C/ESD/MCU breakouts, via barrels/stubs, pads, solder mask, package/connector/protection capacitance, conductor loss, dispersion, glass weave and production tolerances. No eye diagram, TDR, field measurement or vendor coupon qualification was performed. [ATLC's primary tutorial on cross-section calculations and differential/odd modes](https://atlc.sourceforge.net/tutorial.html) describes the general numerical approach; this implementation is an independent Python solver, not ATLC output.

## Recommended next action

For predictable nominal 90 Ω, first select and bind the actual main-board manufacturing stack and material. Then establish a consistent ground-reference corridor for the complete USB route and choose the required width/gap for that geometry, including coplanar copper and transitions. Do not compensate for a changing reference by blanket narrowing or widening. A stack-specific calculation and fabrication impedance requirement/coupon, followed by full-speed electrical checks in both cable orientations, are needed for a stronger signoff.

## Reproduction

Run `extract_sections.py` using KiCad's bundled Python, then run `solve_sections.py`, `solve_sections.py --etch`, and `summarize_results.py` using a Python environment with NumPy and SciPy. `jlc-calculator-input.json` records the separately observed live calculator inputs/result. The calculator's 0.5% field is not a fabrication order or an ordered impedance guarantee.
