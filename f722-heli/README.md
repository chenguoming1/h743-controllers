# F722 controller: current native3 layout, work in progress

**Open [hardware/f722-heli.kicad_pro](hardware/f722-heli.kicad_pro) for the current paired project. Three connections remain unrouted. Do not manufacture or fly this revision.**

The normal `f722-heli/hardware/` project now contains the adopted native3 R35-cleanup layout and its exact paired schematics, parts metadata and libraries. All 61 design files match the [preserved native3 checkpoint](layout-revision/checkpoints/native3-r35-cleanup-v1-20261012/hardware/). This promotion changes their canonical location; it does not add routing or make the board complete.

Current PCB: [hardware/f722-heli.kicad_pcb](hardware/f722-heli.kicad_pcb). SHA-256: `c3183f7841bae96a59b29fd13ce9789cf47386a9db452a327ca797187d2ca8a8`. [Canonical source identities](hardware/CANONICAL-SOURCE.json) bind all paired files to the checkpoint.

## Verified state and remaining routing

- Three unfinished nets: **FLASH_MOSI, PORT_C_RX_EXT and PORT_C_RX_MCU**.
- Recorded KiCad 10.0.6 checks: zero geometric DRC errors, zero ERC violations, zero schematic-parity issues, and two unchanged historical RX dangling-via warnings.
- All 558 pad mappings and source-pair relationships are preserved. The scoped physical gates pass; actual-I/O protection remains 21/22, with RX incomplete.
- R35 is the adopted B.Cu 270-degree orientation. The current layout retains the repaired TX/CORE/SERVO2 transaction. See the [exact geometric evidence](layout-revision/checkpoints/native3-r35-cleanup-v1-20261012/README.md).

## Conditional evidence and qualification limits

The [current native3 DC and assembly evidence](layout-revision/checkpoints/native3-dc-assembly-v1-20261012/README.md) applies to this exact PCB. All 294 required conditional static DC cases pass on both grids; the 15 impedance-sensitivity checks and five VCAP margins also pass. **The overall static screen remains false:** the retained 18.560750 A single-feed illustration fails the four servo voltage floors. These modeled results depend on their stated material, temperature, contact, source and load assumptions; they are not bench measurements or an ampacity guarantee.

The bounded assembly review found no demonstrated land/paste collision requiring a PCB move or a change from ordinary both-sides-tented vias. It does not guarantee assembled seating height, tolerance or factory placement. Regenerate the final placement data from the eventual completed board, especially R35's bottom orientation, and inspect the factory preview.

Complete RX protection, final signal/reference and timing/SI review, shared-C75 ESD/transient behavior, thermal/AC and servo testing, factory orientation/process review, first-article and flight qualification remain open. The approved 400 kHz I2C operating choice retains its overshoot caveat; device timing, sink-current bounds and actual waveforms remain to be validated. This promotion applies no firmware or 385 kHz setting change.

## Historical files and manufacturing data

The previous [final95 project overview](README-final95-historical.md), `docs/` board images and prototype reports, `validation/` status and `manufacturing/` outputs describe the old fully routed prototype. They are preserved for history and **do not describe or qualify this current three-open PCB**. Do not use those old BOM/CPL/Gerber/stencil exports to manufacture the canonical native3 layout.

The [layout-revision history](layout-revision/README.md) retains its original checkpoint reports and recipes; its older eleven-open project is historical. The [native3 geometry checkpoint](layout-revision/checkpoints/native3-r35-cleanup-v1-20261012/) preserves exact design bytes and recorded checks; the [later DC/assembly packet](layout-revision/checkpoints/native3-dc-assembly-v1-20261012/) supplies the current conditional evidence. The older geometry README's pending-DC wording predates that later packet. All earlier checkpoints and B-RID records remain preserved.

This publication verifies file identities, paired completeness and repository scope. It does not rerun routing, KiCad checks or numerical models, and it is not a fabrication release.
