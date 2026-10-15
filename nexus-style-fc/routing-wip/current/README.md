# Current experimental Nexus project: r62

Open **[nexus-style-fc.kicad_pro](hardware/nexus-style-fc.kicad_pro)**, [PCB](hardware/nexus-style-fc.kicad_pcb), or [schematic](hardware/nexus-style-fc.kicad_sch).

This is the latest accepted experimental routing: **zero native errors, zero opens and zero schematic parity issues**. All-visible PCB diagnostics retain 11 centering, five footprint-type and 54 silk warnings. Enabled ERC has zero findings; all-visible ERC has 13 single-global-label advisories and no errors. [Exact receipts and remaining gates](../2026-10-15/input-caps-checkpoint/README.md).

The approved C27/C31 capacitor pair and D5 0.400 mm move are integrated with the readable schematic, generator, library and WIP BOM/CPL. All 347 original physical pins remain exact; C31 adds two. PCB SHA256 `ee1b9b1c814998b957b03777644b531f78b5301856c2a5eb823a6ef07c99059c`; schematic `7a133c241ba24a688d2d2490ae423ff74d26f57cf6578f871cc757093584de42`.

- [Full schematic PDF](docs/connected.pdf)
- [15-page functional-circuit review](docs/nexus-connected-circuits-review.pdf)
- [Source/validation archive](docs/nexus-c27-c31-source-and-validation.zip)
- [Actual WIP BOM and placement exports](manufacturing-wip/README.md)

The root `nexus-style-fc/hardware/` remains the older coherent canonical reference. This current folder is a complete matching project with its own rules and libraries. Its tools preserve the separate power-module selection; no unrelated project is updated. Existing 3D models are copied unchanged for relative-path usability, not fit certification; standard KiCad 10 models are still a system dependency and the new capacitors have no asserted 3D model.

The mechanical redesign remains separate and unfinished. USB impedance/electrical, actual capacitor/input-loop behavior, power/current/thermal/transient, via-in-paste process and physical assembly qualifications remain open. **Do not fabricate, assemble or fly.**

Generator reproduction from this folder uses `python3 tools/gen_schematic.py design hardware/nexus-style-fc.kicad_sch nexus-style-fc`. PCB routing was edited and validated natively; running historical floorplan/build scripts is not a replay of the accepted routed board. Preserve the committed PCB and use a separate work copy for any experiment.
