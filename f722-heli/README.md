# F722 controller: native2 In4 RX layout, work in progress

**Open [hardware/f722-heli.kicad_pro](hardware/f722-heli.kicad_pro). Two connections remain: FLASH_MOSI and PORT_C_RX_EXT. This is an adopted prototype routing baseline; do not manufacture or fly this unfinished revision.**

The normal paired project contains the exact native2 In4 RX v5 board and all 60 unchanged schematic, project, rule, parts and library files. The [immutable checkpoint](layout-revision/checkpoints/native2-in4-rx-v5-20261013/README.md) binds all 61 files. Current PCB SHA-256: `7d9af57e9b22064fc6b2fd9cde4f2f5b72dc252cdbb1b104e706472bfdbbcdcb`. [Canonical provenance](hardware/CANONICAL-SOURCE.json) records every file identity.

Ten added In4.Cu tracks, totaling 21.453741692 mm, connect PORT_C_RX_MCU between the held MCU and R34 approaches. No source track, via, footprint pose or pad assignment changes. Recorded KiCad 10.0.6 checks show zero geometric DRC errors, zero warnings, zero ERC findings and zero schematic-parity findings; the two declared unrouted items remain. The incomplete connector-side RX route still prevents full RX protection completion.

Fresh current DC evidence passes all 294 required cases on both grids, all 15 grid sensitivity comparisons and five VCAP copper-loop limits. **The overall static screen remains false:** the retained approximately 18.56 A lost-J6-feed illustration gives J2–J5 fine-grid board pads 5.86378–5.87856 V against 6.0 V floors. These conditional modeled results depend on their material, temperature, source, load and contact assumptions. They are not measurements, an ampacity guarantee or permission to operate that failed illustration.

The [checkpoint review](layout-revision/checkpoints/native2-in4-rx-v5-20261013/README.md) retains exact finite TP2, FLASH_CS, C3 and U15–J11 return margins. Practical fast-edge UART/SBUS, SPI, ESD/EMC, thermal/AC, servo, assembly/process, first-article and flight checks remain open. Later MOSI/RX_EXT additions require their own exact-source review. The approved 400 kHz I2C choice retains its overshoot caveat; a possible 385 kHz change remains pending, and no firmware setting changes here.

## Historical project and manufacturing files

The [final95 overview](README-final95-historical.md), older `docs/` images, `validation/` status and `manufacturing/` exports describe earlier geometry. They do not qualify this two-open PCB. Do not use their BOM/CPL/Gerber/stencil outputs to manufacture it. Regenerate final assembly data from the eventual completed project and verify factory orientation, including R35's retained B.Cu 270-degree pose.

The [native3 geometry checkpoint](layout-revision/checkpoints/native3-r35-cleanup-v1-20261012/README.md) and [source3 DC/assembly evidence](layout-revision/checkpoints/native3-dc-assembly-v1-20261012/README.md) remain available as historical records. Their status and numerical results belong to their own exact source; the new native2 checkpoint supplies the current source-bound result. The [layout history](layout-revision/README.md) preserves older work. All B-RID files remain unchanged.

The publication packet includes tested exact saved-board reconstruction, a separate native construction recipe and complete current raw DC evidence. Portable numerical/reference replay source is pending a separate immutable supplement; this packet does not claim that source closure is complete. Packaging checks identities, paired completeness and repository scope; it does not rerun routing or numerical models and is not a fabrication release.
