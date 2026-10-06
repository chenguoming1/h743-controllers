# F722 helicopter controller development project

**Draft engineering snapshot. NOT fabrication-ready or flight-qualified.**

Open `hardware/f722-heli.kicad_pro` with KiCad 10. The project includes the primary accepted development PCB, all nine schematic sheets, and relative project-local symbol and footprint libraries. The primary PCB has **31 unfinished connections**; routing is stopped and incomplete.

## Included

- Editable PCB, project/rules, schematics and source libraries
- Nine-page development schematic in `docs/f722-schematic-development.pdf`
- Proposed parts in `hardware/parts.json` and `validation/active-bom-proposals.json`
- Stock Rotorflight `RDMS-NEXUS_F7` target reference and 29-resource pin-map audit
- Native ERC/DRC reports, physical-wire audit, design evidence and first-article plan
- `validation/snapshot-manifest.json` identifying the exact delivered files

## Scope and limitations

This is an original controller design intended to match the classic RadioMaster NEXUS F7 interfaces and stock firmware resources. Runtime compatibility has not been established on hardware.

The nominal overall envelope is 45.0 × 25.4 mm, comprising a 39.16 × 25.4 mm PCB plus 5.84 mm direct-header projection. The height target is 13.1 mm. The board uses six copper layers and a saved 1.0324 mm stack thickness. Dimensions are nominal and subject to component, PCB and assembly tolerances; original enclosure fit is not claimed.

The primary PCB SHA-256 is `4dcb9a7666aaa3f8667de732d5be133b33c90391391f39cf91153ed97d3db883`. The 32-to-31 airwire reduction removed two isolated padless tracks and did not complete any functional connection. The separate unaccepted placement/routing experiment is deliberately excluded.

See [release blockers](docs/release-blockers.md) before further engineering or procurement. No qualified Gerbers, drill, CPL or production BOM are included.

## Portability

Library tables use `${KIPRJMOD}`. Optional 3D models reference `KICAD9_3DMODEL_DIR`; set it to an appropriate installed model directory if desired. Missing models do not establish mechanical clearance. Files are an editable engineering snapshot, not a self-contained one-command manufacturing build. Native reports describe the exact checkpoint and are not a waiver of outstanding checks.

Project libraries retain upstream KiCad license notices in `hardware/library/licenses`. Firmware provenance is recorded in `docs/source-provenance.json`. The new `f722-heli/` directory is independent of `self-balancing/`.
