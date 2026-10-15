# All-section circuit redraw, approved C19 upgrade and r43: unfinished checkpoint 07

Based on current main `cc1ec880aff2ab971f726c6d2e6656d07ddd9fb9`, after externally merged PR35. Unrelated files and concurrent standalone power-module work are preserved. **Do not fabricate or assemble.**

## Open and review

- Main project: `nexus-style-fc/hardware/nexus-style-fc.kicad_pro`. Canonical PCB changes only the approved C19 Value/LCSC/Description properties; copper and all physical geometry remain exact to main. It still has **627 inherited errors: 428 clearance and 199 grouped width findings**.
- [Current experimental project](experimental-r43/hardware/nexus-style-fc.kicad_pro): the sealed r43 route plus the same C19 metadata, with **29 clearance errors**, minimum residual gap **0.0785 mm**. This review candidate remains separate from canonical.
- [Conventional single-sheet PDF](../../../docs/schematic-main.pdf), [15-page circuit booklet](../../../docs/nexus-schematic-review.pdf), and [exact schematic source/validation ZIP](../../../docs/nexus-drafted-schematic-source-and-validation.zip).
- [Final native state summary](SEALED-HANDOFF.json), state-specific `verification.json` / native receipts, [C19 research](board-review/C19-capacitance-review.txt), and [independent review](board-review/independent-review.md).

## Exact source and checks

Final schematic SHA256: `49f9e0571424d0610e294bdcd6b120a42d04db284ecda9e660428fc587e62699`.
Canonical PCB SHA256: `afd0f3225b8d9eca28487b62dfe92ed8feba742e9577b70fb08b03ff8411859f`.
Experimental PCB SHA256: `10c4da72046f311a0ad61ac150091573966c8d9fae70fa93a57402a568d059c5`.

All 15 sections are manually drafted as circuits with left-to-right rails, explicit local wiring and ground branches. All 91 original component identities, all original embedded symbol definitions and all 347 physical pin/net pairs remain exact. The 79 standard ground symbols are virtual, excluded from BOM and PCB, and add no power driver. Consecutive generation is byte-identical. C19 alone changes value/LCSC/Description, with all other parsed schematic nodes unchanged from the reviewed visual revision.

Native KiCad 10.0.7 refilled/saved both boards and checked all track errors, all configured severities, ERC and schematic parity against the exact final schematic. Both have **zero opens, zero parity findings, zero ERC findings and 54 unchanged silk warnings**. Every remaining native violation and measured description is unchanged by the visual and C19 revisions. All 2,542 canonical / 2,627 experimental direct physical contacts survive. Every copper primitive, pad, part placement, footprint geometry, stack, outline and zone definition remains unchanged by the part update. EN stays physically isolated. No new exclusion or ignored check was added; inherited ignored checks remain listed in native receipts and are not claimed passed.

The separate r42 C_RX/5V and r43 SWCLK/SDA/5V transactions improve the preceding 32-error route to 29 errors. Original widths/layers and complete external ports are proved, with no new/worsened residual pair. Minimum gap improves 0.0751 to 0.0785 mm. Native connectivity alone does not qualify electrical behavior.

## Approved C19 substitution

C19 is now **10 uF, 10 V, X5R, +/-10%, Samsung CL10A106KP8NNNC, JLC/LCSC C19702**, on the unchanged 0603 footprint and unchanged placement. The per-call generator override leaves the global capacitor table and C21's C96446 selection intact. Both main BOM CSVs change only the C19 row; all 83 generic-BOM / 82 assembly-BOM references match the final design. These BOM corrections do not release the manufacturing package.

The manufacturer typical curve gives about 4.429 uF at 3.3 V; a separate-factor tolerance/temperature screening estimate is about 3.388 uF. Neither is a guaranteed simultaneous-corner minimum. This improves local capacitance margin, while actual capacitance/ESR, regulator stability and the unresolved input/output loop remain qualification gates. The research report predates approval; its proposed C19 change is applied here. No other part substitution is included.

## Remaining gates

Header source is unchanged, with 11 fixed contact-edge errors and square-tab/capsule-slot interference. Its [prior native receipt](../en-readable-checkpoint/header-check/verification.json) is carried forward against exact unchanged source. No pad or mechanical redesign was made.

The conditional r44 U10 route is excluded because its output improvement worsens the input reference path. Power/return continuity, regulator stability, USB actual-stack impedance and ESD behavior, current/thermal/fault performance, 18 inherited pasted-via locations, connector mapping and U2 orientation/FSYNC remain open. Four added routing vias remain outside pasted pads. The 7.4 V BEC / 10 A continuous / 25 A peak goal is not a PCB rating; never apply raw 6S to the FC.

CAM/CPL remain historical/stale and on hold. Only the approved C19 BOM rows were updated; no routing-dependent manufacturing outputs were regenerated. Earlier checkpoints remain immutable. Receipts retain original execution paths; reproduce using equivalent local paths and native KiCad 10. The root evidence manifest seals all packaged bytes. No fabrication or flight readiness is claimed.
