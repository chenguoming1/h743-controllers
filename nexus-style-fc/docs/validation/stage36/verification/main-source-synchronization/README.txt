Stage36 ADC source/placement/assembly synchronization: PASS

Bound routed PCB SHA256: bed37199e8d62b8135a27b9e182f8e8f584f1a9fb722cb6efb5d4c87b2a320b8
Unchanged project SHA256: ac4eb6dea52f66417f12afe9a23ee7a8ff2ff9872cee20164a383bf3e61b2066
Bound tools/design.py SHA256: ea95b1c7edfe1ec5db765c5b3823a4f388d633cb98e46f93df7777893b8a56a0
Runtime: official KiCad 10.0.7.

- All 89 main footprints and 356 pads regenerate with zero differences against the accepted routed stage36 board. Comparison includes pad nets, dimensions, shape, roundrect radius, copper layers and mask/paste membership; coordinate tolerance is 0.000002 mm.
- Exactly four placements change from stage35, all on F.Cu: C29 (111.0,119.2),270 degrees; R16 (111.4,121.15),90 degrees; C30 (114.39,114.16),0 degrees; R17 (111.4,123.2),270 degrees. Coordinates here are absolute KiCad board coordinates in mm.
- Other 85 footprints/pads remain unchanged, including C10, C12 and Y1. All legacy parts and approved main selections, pin roles, component values, LCSC IDs, notes, and the USB_DN alias are preserved. The four moved parts retain their pad geometries and nets.
- BOM is byte-identical to stage35: 48 rows, 83 assembly parts. CPL changes exactly C29/C30/R16/R17 and matches all 83 board placements, sides and rotations using the unchanged auxiliary origin.
- The routed stage36 PCB, schematic and project were not changed. Frozen stages32/35 inputs stayed unchanged. Only four placements and provenance comments in stage36/tools/design.py were updated, after the comparisons passed.

main-regenerated-floorplan.kicad_pcb is an UNROUTED comparison artifact. Do not replace the routed hardware board or fabricate from it. This proof does not replace native electrical, mechanical or manufacturing-output review and is not manufacturing approval.

The old global courtyard normalizer without the required stock model files is not the verified path. Isolated main-floorplan generation is the demonstrated reproducibility result. No full build, refill or routing overwrite was run here.

verification-report.json contains the full pose/CPL deltas and protected-input hashes. prepared-design.py and prepared-source-comparison.json are retained PREPARATION INPUTS with intentionally old stage35 provenance; the final bound source is ../../tools/design.py relative to this verification directory. Use the stage36 root tools/design.py, not that preparation overlay. Helpers record the verification procedure; rerunning requires a fresh separate staging copy because existing outputs are refused.
