# Nexus-style FBL controller

A KiCad 10 F722 controller based on the RadioMaster Nexus form factor and Rotorflight RDMS-NEXUS_F7 resource map. Orientation, bring-up and physical qualification remain unverified.

**Unfinished engineering design. Do not fabricate, assemble or fly.**

## Open the current design

- [Main KiCad project](hardware/nexus-style-fc.kicad_pro), [main PCB](hardware/nexus-style-fc.kicad_pcb), [main schematic](hardware/nexus-style-fc.kicad_sch)
- [Servo-header child project](hardware/header-board/nexus-header-board.kicad_pro), [child PCB](hardware/header-board/nexus-header-board.kicad_pcb), [child schematic](hardware/header-board/nexus-header-board.kicad_sch)
- [Review-only Gerber, BOM and CPL files](manufacturing/README.md)
- [Validation, exact source provenance and open gates](docs/validation/README.md)

There is one working design in this project root. `hardware/`, `tools/` and `manufacturing/` hold the current trace-corrected main and four-layer power-upgraded child. Work directly here on a Git branch; use commits, branches and pull requests for revisions. Older project snapshots are available in Git history, rather than additional working version folders. The other repository projects are unchanged.

## Source layout

| Path | Purpose |
| --- | --- |
| `hardware/` | Authoritative routed main board, schematic, project settings and rules |
| `hardware/header-board/` | Matching child board and its separate KiCad project |
| `hardware/library/` | Shared local symbols, footprints and 3D models |
| `tools/` | Part/placement definitions, legacy generators, routing helpers and read-only validation |
| `manufacturing/` | Exact matching review exports; not approved for ordering |
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

The latest [USB 90 ohm correction](docs/validation/reviews/usb-compliance-2026-10-17/REVIEW.md) binds the current main PCB/CAM. The In3 matched USB trunk uses **0.143 mm width / 0.154 mm gap**, a pour-only clearance corridor and continuous In4 ground 0.130 mm away. Local six-layer estimates are approximately **89.7–90.0 Ω**; factory controlled-impedance acceptance and assembled USB electrical tests remain pending. Main fabrication requires **JLC06161H-2116A**, six layers, nominal 1.6 mm category, 1 oz outer / 0.5 oz inner; read the [exact fabrication requirements](manufacturing/nexus-style-fc/FABRICATION-NOTES.md). Generic six-layer/default 3313 settings do not match this calculation.

Main PCB SHA-256: `9b65ab90e9dfeecf8a440e4f1b522658419ee2d56a4e27513e03e35bf77e16ac`. Native DRC has zero violations/opens and ten inherited parity findings. All 89 footprints, 2,093 non-USB copper route/via objects and 227 vias are preserved. The 51-group / 83-part main BOM and 83-placement CPL are unchanged. Fresh [PCB DFM](https://jlcdfm.com/viewer?pcbUploadFileId=634351113752236033) matches all 29 preceding category triples, including green width, spacing, pad spacing, corners and mask-to-trace. SMT was not rerun. **C8 still requires confirmed epoxy-filled and copper-capped via-in-pad (POFV).**

The [child power upgrade](docs/validation/reviews/child-full-load-2026-10-17/REVIEW.md) established a **four-layer, nominal 1.6 mm, 2 oz outer / 2 oz inner** design with dedicated VX/GND planes and 27 added power vias. The owner's subsequent cleanup is bound by the [latest child DFM check](docs/validation/reviews/child-dfm-20261017-200904/REVIEW.md), current child SHA-256 `6d9314f769088949b64ade2e3b34fc67641186d3c02edc409738440645df874f`. That check has zero native errors/opens/parity issues, 11 inherited courtyard warnings, and JLCDFM zero danger / 38 warnings. The earlier electrical-loss calculation remains bound to its earlier PCB hash; it is not a current thermal/system current rating. The child retains its separate [JLC041622-3313 / 2 oz fabrication settings](manufacturing/nexus-header-board/FABRICATION-NOTES.md) and is unchanged by the USB correction.

Other PCB and prior assembly/model findings remain open. Real assembly fit, pasted-via process, NRST, factory stack/tolerance, current/contact, mechanical fit, firmware orientation and physical qualification remain unverified. Retained header rating is 3 A/contact; no 10 A system rating is established.

## Attribution and sibling project

The [Rotorflight target reference](firmware/RDMS-NEXUS_F7.config) is copied unchanged from [rotorflight-targets](https://github.com/rotorflight/rotorflight-targets/blob/b89676f/configs/RDMS-NEXUS_F7.config), recorded upstream revision `b89676f` (2026-03-02), and remains attributed to its authors. No firmware binary is included. RadioMaster branding is not used on the board.

The separate [power module](../nexus-style-fc-power-module/) uses the shared legacy `PARTS` interface; the current main-board selection is isolated in `get_main_parts()`.
