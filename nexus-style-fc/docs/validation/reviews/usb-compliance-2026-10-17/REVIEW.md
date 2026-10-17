# Applied USB nominal 90 ohm correction — 2026-10-17

The main USB matched trunk now targets nominal **90 Ω** on a specified six-layer **JLC06161H-2116A** stack. Actual-copper local cross-section estimates are **89.664–90.022 Ω** at 2.5 µm mesh; the additional 1.25 µm check is **90.028 Ω**. This is a layout calculation, not complete USB electrical certification or a fabricated measurement. Supplier controlled-impedance acceptance and prototype electrical checks remain pending.

## Exact source and exports

- Before main PCB: `6295c7ebda6c8a4035064f235072d56e1d6e0ff1b7e6b0402f908ce372ae901e`.
- Applied main PCB: `9b65ab90e9dfeecf8a440e4f1b522658419ee2d56a4e27513e03e35bf77e16ac`.
- Applied project: `71b2c7a155a0321d73224ae91497e90297accaf780ba946efc293dd13fbeb37a`.
- Main Gerber ZIP: `bb8fd82bbd7b350da7e54eec824241b7af8f125061c9c5e2e6cc442fd68b9331`.

[Input binding](input-binding.json), [applied binding](applied-binding.json) and [exact PCB transaction](pcb-transaction.json) record changes and protected files. All 89 footprints, 2,093 non-USB track/arc/via objects, Edge.Cuts and other graphics are exact. All 227 vias remain; no drill or component was added. Saved F.Cu, B.Cu and In4.Cu ground polygons are exact. Both BOM/CPL pairs, the schematic, rules, design definitions and child source/CAM remain byte-identical (29 protected files). Main BOM remains 51 groups / 83 parts, CPL 83 placements. SMT was not rerun.

## Changes

1. Bind the physical stack to JLC06161H-2116A, keeping six layers and the nominal 1.6 mm category. Outer copper is 35 µm, inner 15.2 µm. In3 USB is now 0.130 mm from continuous In4 ground. The central dielectric is explicitly three sublayers: 0.1164 mm PP / 0.7000 mm core / 0.1164 mm PP. The exact factory stack and impedance requirements are in [fabrication notes](../../../../manufacturing/nexus-style-fc/FABRICATION-NOTES.md).
2. Narrow 41 matched In3 track/arc objects from 0.170 to **0.143 mm**, retaining centerlines. Their 0.297 mm center separation produces **0.154 mm edge gap** on parallel runs. Four existing tapers change their wide end to 0.143 mm and retain their 0.150 mm launch end. Each trunk is approximately 13.133 mm; differential router defaults now match 0.143/0.154.
3. Add one **pour-only** In3 keepout around the trunk to avoid variable close coplanar ground. It permits tracks, vias, pads and footprints. The actual new trace-edge setback is about 0.4135 mm at the nominal corridor boundary; other routed nets are retained.
4. Move only the connector's USB_DP duplicate-pin join from In1 to In2, removing its old slot from the In1 ground reference. Reuse existing vias. Its centerline becomes 4.6995 mm instead of 2.5140 mm, avoiding VBUS_C on In2. Other USB launch routing stays as saved.

Changing the stack makes the nearby continuous In4 reference dominate over variable distant In2 copper; ideal In2 present/absent sensitivity is now about 0.02 Ω. It changes spacing for other signals too; no general signal-integrity qualification is implied. No non-USB power reroutes were applied.

## Electrical and numerical evidence

[Sections](sections.json) are extracted read-only from native KiCad saved copper at global Y=116.0, 118.1, 120.2, 113.4 and 123.4 mm. [Model inputs](field-input.json) and [results](field-results.json) bind all solves to the applied PCB hash. The solver includes all six finite copper cross sections, ground antipads, the explicit mixed dielectric stack, 0.010 mm masks modeled with Er=3.8 (CAD mask property is 3.3), outside air, and foreign metal as either floating with zero net charge or ideal AC ground. Signals use the documented JLC etched trapezoid assumption, top width = base width minus 0.7 mil. The 0.143 mm width is nominal base/drawn width. Material Er is 4.16 for PP2116 and 4.6 for core; production etch/material values are unmeasured.

Differential energy impedance uses paired dielectric/vacuum capacitance solutions, Z=1/(c sqrt(C Cvac)), with opposite ±0.5 V signal excitation. Five slices and two foreign-metal assumptions give ten local cases, each at 5 and 2.5 µm mesh. Coarse-to-fine changes are at most about 0.11 Ω. [Domain checks](field-domain-check.json) change the halfspan from 1.5 to 2.5 mm with <0.003 Ω change. The [1.25 µm refinement](field-mesh-refinement.json) uses 1,275,052 nodes and differs from its 2.5 µm case by about 0.006 Ω. Independent analytic capacitor checks and an earlier JLC synthesis cross-check are documented in the [preceding impedance study](../usb-impedance-2026-10-17/REVIEW.md). Numerical convergence does not establish manufacturing accuracy.

The [live JLC calculator](https://jlcpcb.com/pcb-impedance-calculator) was set to non-coplanar differential, six layers, 1.6 mm category, 1 oz outer / 0.5 oz inner, L4 signal, L2/L5 reference, target 90 Ω, requested gap 0.154 mm, stack JLC06161H-2116A. It synthesized **0.1455 mm width / 0.1539 mm gap**. Its 90 Ω display is an input target, not a measurement of the applied route. This modest width difference from our 0.143 mm nominal is disclosed for supplier review. [Visible result](jlc-calculator.txt), [screenshot](jlc-calculator.png), [vendor model guide](https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator).

[Projected ground coverage](reference-projections.json) samples the center and both copper edges at <=0.010 mm steps. Both matched trunks have zero sampled In4 ground gaps. Launch/via regions still contain reference antipads and other discontinuities; the report lists these explicitly. This projection does not solve return-current paths.

[Native topology checks](current-usb.json) confirm connector pins A6/B6 and A7/B7 reach STM32F722RET6 PA12/PA11 through their respective U7 external ESD bridges; removing either bridge disconnects the corresponding path. Whole-route planar witness lengths are A: D+32.6935 / D−30.0405 mm and B: D+36.6164 / D−31.8918 mm. Differences are 2.6529 and 4.7246 mm. Via counts differ, but the used copper-center barrel path sums to 2.0948 mm on all four paths. These are geometric bookkeeping, not electrical delay. No arbitrary compensating meanders were added.

Crossings are treated as longitudinal conductors in a 2D slice; real finite crossings require 3D treatment. Bends, transitions, barrels/stubs, uncoupled breakouts, packages, connector/ESD capacitance, loss, dispersion, glass weave, production tolerances and full-port mode conversion are not qualified here. Require factory confirmation/coupon and full-speed prototype electrical testing in both USB-C orientations before asserting compliance.

## Native DRC and fresh JLCDFM

Canonical [DRC](current-drc.json): **zero violations, zero unconnected items**, ten inherited unrelated schematic-parity footprint-name/filter findings. No rules were relaxed and no new exclusions were added. The editor was reopened to load the saved project defaults; [native USB rules](native-usb-rules.png) show 0.143/0.154 mm (5.62992/6.06299 mil). The [native stack view](native-stack.png) recognizes all three central sublayers and impedance-controlled flag.

Regenerated six-copper-layer Gerbers, both drills and the job file. All **16 ZIP members** match loose CAM. Job metadata declares six layers, nominal 1.6 mm, ENIG and impedance-controlled, with all pressed dielectric sublayers present. This flag expresses an order requirement, not measured qualification.

Fresh [JLCDFM](https://jlcdfm.com/viewer?pcbUploadFileId=634351113752236033) screens this exact ZIP. **All 29 category triples exactly match the preceding upload**, including green trace width, spacing, pad spacing, corners and mask-to-trace. [Summary](dfm-summary.json), [visible page](dfm-ax.txt), [screenshot](dfm-result.png). Existing annular-ring, three via-to-pad, five negative-mask, four short-slot, four slot-width and silkscreen findings remain. DFM is not an impedance check.

C8 still requires POFV. Existing assembly, NRST, contact/current, mechanical, firmware, thermal and flight gates remain open. The child board is unchanged by this USB correction; its latest cleanup check is [separately source-bound](../child-dfm-20261017-200904/REVIEW.md).
