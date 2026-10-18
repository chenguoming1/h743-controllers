# Two-board prototype order package

Prepared for **two assembled main boards plus matching child PCBs**. The justified source fixes and fresh native/JLCDFM results are in the [current order review](../docs/validation/reviews/order-fixes-2026-10-17/REVIEW.md). Factory process acceptance and physical bring-up remain required; these files do not certify flight readiness.

[Download the complete order package](nexus-prototype-order-2026-10-17.zip). Extract it and upload the two inner Gerber ZIPs separately; the outer package is not a Gerber upload.

Latest component update: [R23 replacement](../docs/validation/reviews/r23-replacement-2026-10-18/REVIEW.md), C2766886 / 0.12 Ω ±5% in the same 0402 footprint. BOM and source metadata updated; CAM and CPL are unchanged.

Previous source/CAM check: [standard-stack adaptation](../docs/validation/reviews/standard-stack-2026-10-17/REVIEW.md). The main inner-layer mapping and USB width are adapted for standard JLC06161H-3313. Components, power widths and child board are unchanged.

## Upload these files

| Board | PCB upload | Assembly uploads |
| --- | --- | --- |
| Main | [Main quote ZIP with impedance sheet](nexus-style-fc/nexus-style-fc-jlc-quote.zip) | [53-group BOM](nexus-style-fc/nexus-style-fc-bom-jlc.csv), [84-placement CPL](nexus-style-fc/nexus-style-fc-cpl-jlc.csv); assemble both sides, quantity 2 |
| Child | [Child Gerber ZIP](nexus-header-board/nexus-header-board-gerbers.zip) | Bare PCB intended; optional header BOM/CPL in its folder |

Read [ORDER-INSTRUCTIONS.txt](ORDER-INSTRUCTIONS.txt) before releasing production. Main requires **JLC06161H-3313, six layers, nominal 1.6 mm, 1 oz outer / 0.5 oz inner, ENIG, nominal 90 Ω USB routing, no paid impedance test, POFV for all 228 main vias**. Child requires **JLC041622-3313, four layers, nominal 1.6 mm, 2 oz outer AND inner, ENIG**. Generic/default stack substitutions do not reproduce the analysis.

**Factory must accept the USB short-shell-leg soldering method on the 1.6 mm main board, inspect the new round mounting holes, and review paired board fit, dense-placement tooling/stencil and remaining assembly flags.** R23 is now C2766886 / 120 mΩ ±5%; JLC matching accepts the setup quantity. Confirm availability before payment. No order/payment or factory acceptance has been performed.

The source/CAM sets pass native ERC and have no DRC errors, opens or parity findings; child retains 11 courtyard warnings. Fresh main SMT matches all 53 groups and shows no collisions or missing pads. Main and child PCB DFM retain warnings and main assembly flags; they are documented, not treated as a clean web pass.

The [current quote-form record](../docs/validation/reviews/standard-stack-2026-10-17/REVIEW.md) documents the unsubmitted main-board settings. The quote ZIP adds only a nominal-impedance design note JPG to the original 16-member [DFM Gerber ZIP](nexus-style-fc/nexus-style-fc-gerbers.zip); CAM bytes are identical.

## Source binding

- `hardware/nexus-style-fc.kicad_pcb`: `1ca0c53eb9e53a8ea58d84373d03fe5b55b5f60efd88a95f7cfb788d803a1009`
- `hardware/nexus-style-fc.kicad_sch`: `7cee2893e46c6e786dc051b39f4127e1c518c88213d3f1aac33d65e239dda61f`
- `hardware/header-board/nexus-header-board.kicad_pcb`: `b732bdd0bcc64e7c7636ac6e33fbf65c48241514f945b195aebb30aff5362e4d`
- `hardware/header-board/nexus-header-board.kicad_sch`: `b11404bc82c8dc7581ae7c5acc6fc62b621bc302d896d04a8940717d07fd5b8b`
- `manufacturing/nexus-header-board/nexus-header-board-gerbers.zip`: `69adbcf9ab2d7a832687a4ab8561dbf4e3d147a409c3b336da01ee741575c3e2`
- `manufacturing/nexus-style-fc/nexus-style-fc-gerbers.zip`: `9b4565b40bd41888ee8cdb64ad9f499bd96400ce96b10e046cd4471bfe1cde4b`
- `manufacturing/nexus-header-board/nexus-header-board-bom-jlc.csv`: `6a2b3bbf1d27e84750eeaf034740681aaec0cd7413f736f5d7a42f3fed85e706`
- `manufacturing/nexus-header-board/nexus-header-board-cpl-jlc.csv`: `bf4bcb800239e4bae3c8b60adf1c5857b3636ae2fb359dbaedc06789f03488cf`
- `manufacturing/nexus-style-fc/nexus-style-fc-bom-jlc.csv`: `53d429bd0c2cc74c3ae2f1af0c82acacf8e4841b8909159ae96d1f448439dcf2`
- `manufacturing/nexus-style-fc/nexus-style-fc-cpl-jlc.csv`: `3724f663551500d272fab8cb12da777bc2b91015ba59e079c16ec6a283093464`

ZIP contents match the loose CAM files (16 main / 14 child members). Main fabrication details: [main requirements](nexus-style-fc/FABRICATION-NOTES.md); child: [child requirements](nexus-header-board/FABRICATION-NOTES.md). Historical reports apply only to their named revisions. Re-export with `tools/export_fab.py` after any further PCB change and rerun checks; do not mix files between revisions.
