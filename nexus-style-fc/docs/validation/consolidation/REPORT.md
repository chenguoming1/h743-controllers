# Canonical-root consolidation verification

Source: `chenguoming1/h743-controllers`, commit `fad62076054229a1d3de79106984d8b71906379e` (2026-10-16). The latest coherent stage36 main and b49ef410 child move into the single `nexus-style-fc` project root. No electrical design changes, regeneration, zone refill or native save were performed.

## Results

- All eight PCB, schematic, project and rule files are byte-identical to the accepted source. [Hashes and exact findings](summary.json).
- Main generator remains exact SHA-256 `ea95b1c7edfe1ec5db765c5b3823a4f388d633cb98e46f93df7777893b8a56a0`.
- Main/child ERC: 0 violations. Four inherited ignored checks remain visible in each report: single-global-label, four-way-junction, simulation-model and footprint-filter.
- Main DRC: 0 errors, 0 opens, 0 schematic parity findings; 61 warnings.
- Child DRC: 0 errors and 0 opens; 11 courtyard warnings plus 11 schematic footprint-filter parity warnings. These warnings match the accepted child report.
- No DRC check is disabled. Native finding arrays are unchanged from the accepted reports. DRC commands with `--exit-code-violations` return 5 because warnings are present; this is not an all-green unconditional release.
- Main source, all 89 footprints/356 pads, pin nets and placements match the native board. Main BOM has 48 groups/83 parts; all 83 CPL placements match. Child source pin nets, BOM and CPL also match. [Detailed consistency result](source-consistency.json).
- All current manufacturing bytes are retained; no mixed or regenerated CAM was introduced.
- All 36 project-local dependency references resolve in the planned Git tree. Existing model blobs are retained by exact Git SHA. The cloud validation used sparse materialization; large retained models were not all downloaded or visually checked.
- Python syntax and shell syntax pass. The default legacy build entrypoint refuses to overwrite native sources; full generation is intentionally not a validation test.

## Native commands

With KiCad 10.0.7, run each command for both `hardware/nexus-style-fc` and `hardware/header-board/nexus-header-board`, with outputs outside the native project folders:

```sh
kicad-cli sch erc --format json --severity-all --exit-code-violations -o erc.json PROJECT.kicad_sch
kicad-cli pcb drc --format json --all-track-errors --schematic-parity --severity-all --exit-code-violations -o drc.json PROJECT.kicad_pcb
```

The current `tools/validate_project.sh` provides the read-only workflow and counts errors separately while retaining warnings. KiCad may create `.kicad_prl` UI-state files; these are excluded. No source-affecting refill/save flags are used.

## Scope and limits

This verifies consolidation and existing design consistency, not new design qualification. Stage36 JLCDFM remains PCB-only, with six pad-spacing danger counts; assembly has no result and CPL acceptance is uncertain. The retained header rating is 3 A, without a 10 A system rating. U10/model/assembly, NRST placement, supplier process/stack, contact/current, physical/mechanical fit, thermal/transient/SI/PI and flight gates remain open. See the [validation guide](../README.md).
