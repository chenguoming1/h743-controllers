# Portable project library

`F722_Heli.kicad_sym` and `F722_Heli.pretty` are project-local copies or adaptations of installed KiCad 9 library items, plus original project-specific symbols and manufacturer-drawing-derived footprints. Library names are intentionally local so a future system-library update cannot silently change the design.

The KiCad Community items retain the upstream CC-BY-SA 4.0 license with the electronic-design exception. Installed distribution copyright/license notices are preserved in `licenses/`. The exception applies to electronic designs and their generated files; the copied library material retains its original notices.

Project-specific footprint validation, departures from stock library geometry, manufacturer sources and selected part numbers are recorded in the project evidence documents and `hardware/parts.json`. Relevant changes include TI power-package lands, the Samtec right-angle triple-row header, exact Panasonic/Murata 0402 lands, and the USB outer-ground-pad corner treatment. Do not replace these footprints with similarly named generic packages without rechecking land dimensions, numbering, paste and courtyard geometry.

This library is a development artifact. Inclusion does not imply that a fabricated first article or assembler rotation/pickup mapping has been validated.
