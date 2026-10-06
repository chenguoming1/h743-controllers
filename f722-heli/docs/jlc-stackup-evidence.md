# JLCPCB 6-layer stackup and USB fabrication evidence

Verified 2026-10-04 against JLCPCB's live public calculator and order selectors. No design was uploaded, order saved, or purchase made. These are design inputs and release conditions, not factory acceptance of this PCB.

## Selected candidate

**JLC06101H-3313**, standard/recommended, nominal **1.0 mm**, **1 oz outer / 0.5 oz inner**, **Nan Ya NP-155F**, ENIG, green soldermask. The live calculator labels its finished thickness **1.03 mm ±10%**. Allow **0.927–1.133 mm** in the mechanical tolerance budget; do not treat nominal 1.0 mm as an exact dimension.

The static [stackup overview](https://jlcpcb.com/impedance) omits 1.0 mm from its six-layer buttons, but the [live calculator](https://jlcpcb.com/pcb-impedance-calculator) and [live order selector](https://cart.jlcpcb.com/quote?stencilLayer=6) both explicitly offer JLC06101H-3313. Use the live stackup identifier, not a guessed scaled version of a 1.6 mm structure.

### Calculator stackup

Thicknesses below are the live calculator's displayed mm values.

| Layer | Proposed use | Material | Thickness mm | εr |
|---|---|---|---:|---:|
| F.Cu / L1 | Signals, USB | Outer copper, 1 oz | 0.0350 | — |
| Dielectric 1 | | 3313 PP, RC57% | 0.0994 | 4.1 |
| In1.Cu / L2 | Continuous GND | Inner copper, 0.5 oz | 0.0152 | — |
| Dielectric 2 | | NP-155F core | 0.2500 | 4.23 |
| In2.Cu / L3 | Signals | Inner copper, 0.5 oz | 0.0152 | — |
| Dielectric 3 | | 7628 PP, RC49% | 0.2028 | 4.4 |
| In3.Cu / L4 | Power | Inner copper, 0.5 oz | 0.0152 | — |
| Dielectric 4 | | NP-155F core | 0.2500 | 4.23 |
| In4.Cu / L5 | Continuous GND | Inner copper, 0.5 oz | 0.0152 | — |
| Dielectric 5 | | 3313 PP, RC57% | 0.0994 | 4.1 |
| B.Cu / L6 | Signals | Outer copper, 1 oz | 0.0350 | — |

Dielectric values: [JLCPCB's NP-155F material table](https://rs.jlcpcb.com/static/image/blog/pcb/nan-ya-plastics-np-155f.png), visually checked. For the 0.25 mm core, use 4.23 rather than the older overview's generic core value 4.6.

**Unresolved manufacturer documentation difference:** the order-page stackup drawing shows **0.21040 mm** for central 7628 PP, while the calculator shows **0.2028 mm**. Both agree on the outer PP (0.0994 mm), cores, and copper table. Do not silently combine the diagrams. Record JLC06101H-3313 and obtain the final production-stackup confirmation before fabrication release. This difference is between L3 and L4 and does not alter the calculator's L1/L2 USB geometry, but matters for the exact KiCad stack thickness and internal-layer models.

## Manufacturer-calculated 90 Ω differential geometry

Live calculator inputs: Rigid; six layers; PCB thickness 1; 0.5 oz inner; 1 oz outer; mm; impedance 90 Ω; L1 signal; no upper reference; L2 lower GND reference; soldermask-present model; pair spacing input 0.15 mm; numerical search tolerance displayed 0.5%; select standard JLC06101H-3313 result.

| Model | Output trace width | Output pair edge gap | Output trace-to-same-layer-ground gap |
|---|---:|---:|---:|
| Differential Pair (Non coplanar) | **0.1356 mm** | **0.1501 mm** | Not modeled |
| Coplanar Differential Pair | **0.1349 mm** | **0.1501 mm** | **0.4999 mm** (input 0.5 mm) |

These are actual calculator outputs, not impedance inferred from width alone. Both exceed a project 0.127 mm minimum trace width. For an intentionally grounded coplanar corridor, the second row provides an explicit same-layer copper boundary. Do not use that row while placing another trace, non-ground copper, or different ground setback inside the modeled corridor. For the first row, adding close coplanar copper changes the model and must be recalculated. Keep uninterrupted L2 GND below the entire USB run; do not cross plane gaps. Connector and ESD/series-resistor pad discontinuities and short uncoupled escapes remain separate layout review items.

[Calculator guide](https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator): 4–8-layer calculations assume NP-155F. Its solver parameters list outer copper 1.6 mil (40.64 µm), inner 0.6 mil (15.24 µm), mask εr 3.8, mask 1.2 mil on substrate/between traces and 0.6 mil above copper, and trapezoid top width 0.7 mil narrower than base. The table's outer copper is 35 µm, so do not recreate the solver using the table alone. The displayed 0.5% calculator tolerance is **not** a fabrication tolerance or test certificate. Numeric values may be updated by JLCPCB.

## Fabrication limits and project rules

Manufacturer limits from [Rigid PCB capabilities](https://jlcpcb.com/capabilities/Capab), for this multilayer/1 oz class:

| Feature | Manufacturer limit / recommendation |
|---|---|
| Trace/space | 0.09/0.09 mm; use ≥0.127/0.127 mm project default |
| Via drill/pad | 0.15/0.25 mm minimum; 0.20 mm preferred drill |
| Via annulus | Pad diameter ≥ drill +0.10 mm; +0.15 preferred |
| Economical via | 0.20/0.45 mm avoids small-via surcharge; 0.30/0.45 mm also suitable |
| Component PTH annulus | 0.15 mm absolute; ≥0.20 recommended; distinct from via rule |
| Drill-to-unrelated-copper | Via: 0.20 mm; inner component PTH: 0.30 mm |
| Hole-to-hole | Vias 0.20 mm; component holes 0.45 mm |
| NPTH hole / routed slot | ≥0.50 / ≥1.00 mm |
| Pad-to-track / SMD pad-to-pad | ≥0.10 / ≥0.15 mm |
| Copper to routed outline | ≥0.20 mm; project target ≥0.30 mm |
| Routed outline tolerance | ±0.20 mm regular |
| Mask | 1:1 opening supported; ≥0.09 mm opening-to-neighbor trace |
| Mask bridge | 0.10 mm green; 0.13 mm black/white |
| Legend | ≥0.15 mm stroke; ≥1.0 mm height; ≥0.15 mm from pads |
| Surface finish | Six-layer HASL unsupported; select ENIG |

Do not confuse copper-to-copper clearance with drill-edge-to-copper clearance. A 0.20/0.45 via has only 0.125 mm radial annulus, so a 0.127 mm copper clearance alone does not prove every applicable drill constraint. Enforce both rules in DRC.

## Via-in-pad and thermal pads

[JLCPCB via-covering instructions](https://jlcpcb.com/help/article/pcb-via-covering) support epoxy filling and copper capping, with resin filling free for six-layer and above boards. Select **Epoxy Filled & Capped** for solderable thermal-pad vias. Specify the drill sizes to fill and preserve component through-holes as solderable PTHs. The help page recommends ≤0.5 mm holes for reliable filling. Mask tenting and ink plugging are not substitutes for a flat capped via-in-pad surface. The order page offers copper-paste-filled/capped as another process; its thermal benefit and cost require a separate decision.

For a small exposed pad, follow its component package drawing first. A grounded thermal pad should have the requested local copper and via array, not an arbitrary via count. Use segmented paste where the package/assembly guidance requires it, and check every paste pane's release ratio. Do not assume that a CAD copper thermal relief is a paste-mask design.

## Stencil and assembly preparation

Provide F.Paste and B.Paste Gerbers and review the actual stencil apertures. [Stencil ordering instructions](https://jlcpcb.com/help/article/instructions-for-stencil-order) list 0.10, 0.12, 0.15, 0.18, and 0.20 mm as standard thicknesses; special thinner options cost extra. A **0.10 mm starting candidate** is appropriate for review of this small fine-pitch board, but final choice depends on its finest apertures and larger solder-volume needs.

[JLCPCB stencil guidance](https://jlcpcb.com/blog/stencil-aperture-design-geometry-area-ratio-tips) gives area ratio ≥0.66 and aspect ratio ≥1.5, and describes 60–75% segmented thermal-pad paste coverage. These are general assembly starting points; the component's recommended land/paste pattern takes precedence. Area ratio = opening area / (opening perimeter × stencil thickness).

[JLCPCB's stencil-processing standard](https://jlcpcb.com/help/article/opening-process-standard-of-stencil) changes apertures by default. For 0.5 mm pitch ICs it lists 0.24 mm width and outward extension where applicable; larger heat pads are divided by bridges. Explicitly review CAM changes rather than assuming the exported paste Gerber is cut literally. Through-hole apertures are omitted unless paste data or instructions request them.

Engineering recommendation: panelize this small outline for double-sided assembly with accessible rails/fiducials, ensure no component overhang is damaged during depanelization, and account for routed-edge tolerance in the enclosure. Final panelization must be agreed with the assembler.

## Impedance service, quantity, and cost caveats

The live order page, with six layers / 1.0 mm / 1 oz outer / 0.5 oz inner / NP-155F / JLC06101H-3313 selected, offers **±10% impedance control** (±5 Ω only for targets ≤50 Ω). Selecting this also enables production-file confirmation. The generic 100×100 mm / five-piece example showed an **impedance-control line item of US$33.08**, plus US$1.05 production-file confirmation; this is a dated option-cost observation, **not a quote for this controller**. No freight, tax, assembly, or final-board total is asserted.

Five boards is the smallest offered preset quantity; a custom quantity of one was rejected by the UI's multiples-of-50 validation. PCB assembly minimums are separate. Do not rely on promotional PCB prices as an assembled prototype budget.

The [current laminated-structures article](https://jlcpcb.com/help/article/multi-layer-pcb-standard-laminated-structures) distinguishes free ±20% testing from chargeable precision testing, while the capabilities page advertises ±10%. Therefore, explicitly select and confirm **90 Ω differential ±10%** in the actual order; do not assume that selecting a named stackup alone purchases that guarantee.

## Release gates

1. Obtain/approve the exact JLC06101H-3313 production stackup, especially central PP discrepancy and finished thickness.
2. Verify the USB routing against the selected calculator model, planes, mask, copper boundaries, and geometry; obtain CAM impedance confirmation/coupon testing for 90 Ω ±10%.
3. Run copper, drill, mask, paste, courtyard, and enclosure-tolerance checks on actual exported files.
4. Review filled/capped via treatment and stencil CAM output; do not permit thermal-pad solder loss into open vias.
5. Recheck current options and charges before ordering. No factory engineering review has been performed in this research.
