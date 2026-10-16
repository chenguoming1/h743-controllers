# Nexus-style FBL controller

A KiCad 10 F722 controller based on the RadioMaster Nexus form factor and Rotorflight RDMS-NEXUS_F7 resource map. Orientation, bring-up and physical qualification remain unverified.

**Unfinished engineering design. Do not fabricate, assemble or fly.**

## Open the current design

- [Main KiCad project](hardware/nexus-style-fc.kicad_pro), [main PCB](hardware/nexus-style-fc.kicad_pcb), [main schematic](hardware/nexus-style-fc.kicad_sch)
- [Servo-header child project](hardware/header-board/nexus-header-board.kicad_pro), [child PCB](hardware/header-board/nexus-header-board.kicad_pcb), [child schematic](hardware/header-board/nexus-header-board.kicad_sch)
- [Review-only Gerber, BOM and CPL files](manufacturing/README.md)
- [Validation, exact source provenance and open gates](docs/validation/README.md)

There is one working design in this project root. `hardware/`, `tools/` and `manufacturing/` hold the matched stage36 main and b49ef410 child. Work directly here on a Git branch; use commits, branches and pull requests for revisions. Older project snapshots are available in Git history, rather than additional working version folders. The other repository projects are unchanged.

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

The consolidation changes paths, documentation and tooling safeguards only. Main PCB SHA-256 is `bed37199e8d62b8135a27b9e182f8e8f584f1a9fb722cb6efb5d4c87b2a320b8`; child PCB is `b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6`. Main `tools/design.py` is the exact file restored by the owner in commit `fad62076054229a1d3de79106984d8b71906379e`.

Fresh consolidation checks with KiCad 10.0.7: both ERC reports have zero violations; both DRC reports have zero errors/opens. Main has 61 warnings and zero parity findings. Child has 11 missing-courtyard plus 11 schematic footprint-filter warnings. All inherited rule settings are unchanged.

[Stage36 external DFM](docs/validation/reviews/jlcdfm-main-stage36/REVIEW-STATUS.md) is **PCB-only**: six pad-spacing danger counts remain. BOM acceptance was observed; CPL acceptance is uncertain, and there is no stage36 assembly result. Child-specific historical DFM remains bound to the unchanged child hash. These are screening results, not supplier process approval.

Open gates include U10 model/overlap and assembly fit, local NRST placement, matched main/child mechanical fit, PCB thickness/copper/process acceptance, header/contact current, thermal/transient/SI/PI/EMI, vibration and physical testing. The retained header is rated 3 A; no 10 A system rating is established. Stock-target orientation and flight qualification are also open.

## Attribution and sibling project

The [Rotorflight target reference](firmware/RDMS-NEXUS_F7.config) is copied unchanged from [rotorflight-targets](https://github.com/rotorflight/rotorflight-targets/blob/b89676f/configs/RDMS-NEXUS_F7.config), recorded upstream revision `b89676f` (2026-03-02), and remains attributed to its authors. No firmware binary is included. RadioMaster branding is not used on the board.

The separate [power module](../nexus-style-fc-power-module/) uses the shared legacy `PARTS` interface; the current main-board selection is isolated in `get_main_parts()`.
