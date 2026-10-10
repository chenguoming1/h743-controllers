# Portable project library

`F722_Heli.kicad_sym` and `F722_Heli.pretty` are project-local copies or adaptations of installed KiCad 9 library items, plus original project-specific symbols and manufacturer-drawing-derived footprints. Library names are intentionally local so a future system-library update cannot silently change the design.

The KiCad Community items retain the upstream CC-BY-SA 4.0 license with the electronic-design exception. Installed distribution copyright/license notices are preserved in `licenses/`. The exception applies to electronic designs and their generated files; the copied library material retains its original notices.

Project-specific footprint validation, departures from stock library geometry, manufacturer sources and selected part numbers are recorded in the project evidence documents and `hardware/parts.json`. Relevant changes include TI power-package lands, the Samtec right-angle triple-row header, exact Panasonic/Murata 0402 lands, and the USB outer-ground-pad corner treatment. Do not replace these footprints with similarly named generic packages without rechecking land dimensions, numbering, paste and courtyard geometry.

This library is a development artifact. Inclusion does not imply that a fabricated first article or assembler rotation/pickup mapping has been validated.

## Vertical USB replacement (2026-10-06)

`USB_C_Receptacle_GCT_USB4145-03-0170-C_16P_Vertical` is an original transcription of GCT USB4145 drawing A2 (2023-01-31), independently checked against the component-side recommended layout. It retains the generic USB2 symbol pin names and has no inherited horizontal STEP model. Front and underside component keepouts are explicitly provisional engineering reserves. See `../../docs/vertical-usb-evidence.md`; assembly/process and full-board release checks remain open.


## R16 Panasonic ERJ3R land candidate, 2026-10-06

`R_Panasonic_ERJ3R_0603.kicad_mod` is derived from the local KiCad `R_0603_1608Metric` asset, retaining body, conservative courtyard and 3D model reference. Its a=0.85 mm gap, b=2.20 mm outer span and c=0.95 mm width fit the ERJ*R 1608 example in Panasonic DMM0000COL17, page 1: https://industrial.panasonic.com/cdbs/www-data/pdf/RDM0000/DMM0000COL17.pdf. Pads are 0.675 × 0.95 mm at x=±0.7625 mm with 0.20 mm corner radii. Only R16 is assigned this asset. Source library licensing remains in `licenses/`; manufacturer drawing is dimensional evidence, not imported CAD. Actual assembly qualification remains pending.
