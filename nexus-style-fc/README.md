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

The latest [owner VX/3V3 cleanup recheck](docs/validation/reviews/owner-vx-recheck-2026-10-17/REVIEW.md) and [input binding](docs/validation/reviews/owner-vx-recheck-2026-10-17/input-binding.json) cover the current main PCB/CAM. The owner's In3 VX cross-feed/trunk-entry and 3V3 cleanup preserve the component placements, vias, physical slots, keepouts and DRC rules. Native DRC has zero violations and zero opens; exactly the same ten schematic-parity warnings remain. Cached ground pours were refreshed, with no route correction during the recheck.

Main PCB SHA-256: `6295c7ebda6c8a4035064f235072d56e1d6e0ff1b7e6b0402f908ce372ae901e`. There are 227 vias; the removed GND stitch is not restored. The [preceding corner-width revision](docs/validation/reviews/vx-corner-width-2026-10-17/REVIEW.md) retains its own source binding. Main project, schematic, rules and BOM/CPL are unchanged. **C8's via-in-pad still requires epoxy filling and copper capping (POFV), to be confirmed in the production order.** Ordinary tenting does not cover the hole inside the solder-pad aperture.

Fresh [PCB DFM](https://jlcdfm.com/viewer?pcbUploadFileId=634325109695401986) matches all 29 preceding category counts, including green width, spacing, pad spacing, corners and mask-to-trace.

The 51-group / 83-part main BOM and 83-placement CPL are byte-identical to the preceding revision. Matching main Gerbers were regenerated and screened; SMT was not rerun. Historical reports retain their original input bindings.

The [child power upgrade](docs/validation/reviews/child-full-load-2026-10-17/REVIEW.md) replaces b49ef410 with a **four-layer, nominal 1.6 mm, 2 oz outer / 2 oz inner** design: In1 VX, In2 GND, a rear VX pour and 27 added power vias. Child SHA-256: `12d537492ebb7aa347e30c78c758efbdbd6e238425f0095282cbf7188e872e23`. Outline, header/joint geometry, signal routes and BOM/CPL are preserved. Native child DRC has no errors, opens or parity issues; 11 inherited missing-courtyard warnings remain. Calculated loss at the 19.6 A imposed stress case falls from 0.767 to 0.282 W on the same grid; the finer-grid result is 0.275 W. This is a copper-resistance improvement, not a thermal or complete-system current rating. Matching four-layer Gerbers and [required fabrication settings](manufacturing/nexus-header-board/FABRICATION-NOTES.md) are included; default thin inner copper would not match the analysis.

Other PCB and prior assembly/model findings remain open. Real assembly fit, pasted-via process, NRST, factory stack/tolerance, current/contact, mechanical fit, firmware orientation and physical qualification remain unverified. Retained header rating is 3 A/contact; no 10 A system rating is established.

## Attribution and sibling project

The [Rotorflight target reference](firmware/RDMS-NEXUS_F7.config) is copied unchanged from [rotorflight-targets](https://github.com/rotorflight/rotorflight-targets/blob/b89676f/configs/RDMS-NEXUS_F7.config), recorded upstream revision `b89676f` (2026-03-02), and remains attributed to its authors. No firmware binary is included. RadioMaster branding is not used on the board.

The separate [power module](../nexus-style-fc-power-module/) uses the shared legacy `PARTS` interface; the current main-board selection is isolated in `get_main_parts()`.
