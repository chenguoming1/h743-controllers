# Nexus-style FBL controller

A KiCad 10 F722 controller based on the RadioMaster Nexus form factor and Rotorflight RDMS-NEXUS_F7 resource map. Orientation, bring-up and physical qualification remain unverified.

**Unfinished engineering design. Do not fabricate, assemble or fly.**

## Open the current design

- [Main KiCad project](hardware/nexus-style-fc.kicad_pro), [main PCB](hardware/nexus-style-fc.kicad_pcb), [main schematic](hardware/nexus-style-fc.kicad_sch)
- [Servo-header child project](hardware/header-board/nexus-header-board.kicad_pro), [child PCB](hardware/header-board/nexus-header-board.kicad_pcb), [child schematic](hardware/header-board/nexus-header-board.kicad_sch)
- [Review-only Gerber, BOM and CPL files](manufacturing/README.md)
- [Validation, exact source provenance and open gates](docs/validation/README.md)

There is one working design in this project root. `hardware/`, `tools/` and `manufacturing/` hold the current trace-corrected main and matched b49ef410 child. Work directly here on a Git branch; use commits, branches and pull requests for revisions. Older project snapshots are available in Git history, rather than additional working version folders. The other repository projects are unchanged.

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

The latest [pad-spacing correction](docs/validation/reviews/pad-spacing-2026-10-17/REVIEW.md) and [input binding](docs/validation/reviews/pad-spacing-2026-10-17/input-binding.json) cover the current main PCB/CAM. JLCDFM pad spacing is green: zero danger and zero warnings, down from four danger and 69 warnings. Trace width, trace spacing and sharp corners remain green. Native copper DRC has zero violations and zero opens; the same 10 schematic parity warnings remain.

Main PCB SHA-256: `d559c9f926ca5481d2b7a4804515600edb6ee63832a2dd913d03a1fc9e044461`. Vias and routes were adjusted, including relocating the A_TX layer transition. C31, R20, R21 and U10 shift 0.025 mm; Y1 shifts 0.03 mm. Pad geometry, part identities, orientations, via dimensions, outline, stack, rules, schematic and project are preserved. All outer traces remain at least 0.14 mm. The child is unchanged at `b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6`.

The 51-group BOM remains byte-identical. The corrected 83-placement CPL was regenerated with only those five coordinate changes; all sides and rotations are unchanged. SMT analysis was not rerun for this revision. Historical reports retain their original input bindings.

Other PCB and prior assembly/model findings remain open. Real assembly fit, pasted-via process, NRST, factory stack/tolerance, current/contact, mechanical fit, firmware orientation and physical qualification remain unverified. Retained header rating is 3 A/contact; no 10 A system rating is established.

## Attribution and sibling project

The [Rotorflight target reference](firmware/RDMS-NEXUS_F7.config) is copied unchanged from [rotorflight-targets](https://github.com/rotorflight/rotorflight-targets/blob/b89676f/configs/RDMS-NEXUS_F7.config), recorded upstream revision `b89676f` (2026-03-02), and remains attributed to its authors. No firmware binary is included. RadioMaster branding is not used on the board.

The separate [power module](../nexus-style-fc-power-module/) uses the shared legacy `PARTS` interface; the current main-board selection is isolated in `get_main_parts()`.
