# Nexus-style FBL controller

Latest assembly sourcing update: [R23 replacement, 18 October 2026](docs/validation/reviews/r23-replacement-2026-10-18/REVIEW.md). R23 is C2766886 / Uniroyal 0402WGJ012KTCE, 0.12 Ω ±5%. Only component metadata and BOM change; Gerbers, routing and CPL remain unchanged.

A KiCad 10 F722 controller based on the RadioMaster Nexus form factor and Rotorflight RDMS-NEXUS_F7 resource map. Orientation, bring-up and physical qualification remain unverified.

**Two-board prototype package prepared. Factory process review and physical bring-up remain required before relying on this design; flight qualification is unverified.**

## Open the current design

- [Main KiCad project](hardware/nexus-style-fc.kicad_pro), [main PCB](hardware/nexus-style-fc.kicad_pcb), [main schematic](hardware/nexus-style-fc.kicad_sch)
- [Servo-header child project](hardware/header-board/nexus-header-board.kicad_pro), [child PCB](hardware/header-board/nexus-header-board.kicad_pcb), [child schematic](hardware/header-board/nexus-header-board.kicad_sch)
- [Current prototype Gerber, BOM and CPL files](manufacturing/README.md)
- [Validation, exact source provenance and open gates](docs/validation/README.md)

There is one working design in this project root. `hardware/`, `tools/` and `manufacturing/` hold the current trace-corrected main and four-layer power-upgraded child. Work directly here on a Git branch; use commits, branches and pull requests for revisions. Older project snapshots are available in Git history, rather than additional working version folders. The other repository projects are unchanged.

## Source layout

| Path | Purpose |
| --- | --- |
| `hardware/` | Authoritative routed main board, schematic, project settings and rules |
| `hardware/header-board/` | Matching child board and its separate KiCad project |
| `hardware/library/` | Shared local symbols, footprints and 3D models |
| `tools/` | Part/placement definitions, legacy generators, routing helpers and read-only validation |
| `manufacturing/` | Matching prototype order exports and explicit factory requirements |
| `firmware/RDMS-NEXUS_F7.config` | Unchanged upstream resource-map reference |
| `docs/validation/` | Current validation plus revision-labelled historical evidence |

## Validate safely

Install KiCad 10 with its standard symbols, footprints and models. The project's relative local-library and model paths work from these canonical locations. Native Python helpers need the Python interpreter bundled with KiCad, or one with its matching `pcbnew` module. On Linux, the standard libraries are normally under `/usr/share/kicad`; `KICAD_SYMBOL_DIR`, `KICAD_FOOTPRINT_DIR` or `KICAD10_FOOTPRINT_DIR` can override the corresponding lookup.

From this directory:

```sh
KICAD_CLI=kicad-cli KICAD_PYTHON=python3 bash tools/validate_project.sh
```

This checks paths, Python syntax, ERC and DRC with schematic parity and writes reports to a temporary directory. It does not refill zones or save either board. Native KiCad may create ignored `.kicad_prl` UI-state files. Pass an output-directory argument to retain reports elsewhere. Review all warnings and inherited exclusions; a zero-error result is not physical or manufacturing approval.

**Do not run `build_all.sh` to validate or reproduce the routed boards.** The legacy generator overwrites footprints, schematics and boards with a new baseline; it does not reproduce the accepted manual routing or the complete child integration. Its default invocation now refuses to overwrite anything. The explicit `--regenerate-unrouted` option is only for intentional experiments in a disposable Git worktree. Direct generator/routing scripts can also overwrite files. `design.py` is the current part/placement definition, while the checked-in native boards remain authoritative for routed copper and fills.

## Current evidence and remaining gates

Latest source/CAM binding and checks: [standard-stack adaptation](docs/validation/reviews/standard-stack-2026-10-17/REVIEW.md). Main uses standard JLC06161H-3313 with In1/In2 copper content exchanged and a 0.132/0.165 mm L4 USB trunk. Components, vias, outline, VCAP and power-track widths are preserved.

The [order-fixes review](docs/validation/reviews/order-fixes-2026-10-17/REVIEW.md) documents the preceding electrical/mechanical fixes for **two assembled main prototypes plus matching child PCBs**. It includes C9/R23 VCAP damping, a 7.4 V BEC-appropriate TVS, improved mating clearance, 0.26 mm child header rings and round USB shell holes. Native main ERC/DRC/opens/parity are all zero. Child ERC/errors/opens/parity are zero with 11 bare-contact courtyard warnings. Fresh main BOM/CPL has 53 groups / 84 placements, all groups matched in JLCDFM; both current Gerber ZIPs were freshly analyzed.

The owner's 5V_BUCK widening and USB centerlines are preserved. Main requires the [six-layer standard JLC06161H-3313 stack and nominal 90 Ω USB routing](manufacturing/nexus-style-fc/FABRICATION-NOTES.md), and filled/capped POFV for **all 228 main vias**. Child requires its separate [four-layer JLC041622-3313, 2 oz outer AND inner settings](manufacturing/nexus-header-board/FABRICATION-NOTES.md). Current-source child copper-loss calculation is about 0.275 W at the imposed 19.6 A dual-feed stress condition; it is not a thermal or connector/BEC rating. Retained contacts are 3 A each.

Use [ORDER-INSTRUCTIONS.txt](manufacturing/ORDER-INSTRUCTIONS.txt) for the exact files/settings. Factory acceptance of stack/impedance, POFV, paired-board fit, short USB shell-leg soldering and dense placement remains necessary. The full VCAP/USB/electrical, transient, mechanical, firmware and flight behavior needs prototype testing. Historical reports remain evidence of their named revisions and do not bind the new exports.

## Attribution and sibling project

The [Rotorflight target reference](firmware/RDMS-NEXUS_F7.config) is copied unchanged from [rotorflight-targets](https://github.com/rotorflight/rotorflight-targets/blob/b89676f/configs/RDMS-NEXUS_F7.config), recorded upstream revision `b89676f` (2026-03-02), and remains attributed to its authors. No firmware binary is included. RadioMaster branding is not used on the board.

The separate [power module](../nexus-style-fc-power-module/) uses the shared legacy `PARTS` interface; the current main-board selection is isolated in `get_main_parts()`.
