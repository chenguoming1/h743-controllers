# Sharp-corner and trace-spacing correction — 17 October 2026

Scope: clear the two outer-layer sharp-corner warnings and two trace-spacing warnings reported in the [pre-fix PCB/SMT check](../jlcdfm-current-2026-10-17/REVIEW.md). This report supersedes that check for PCB copper only. The previous SMT result remains historical; SMT analysis was not repeated for this copper revision.

## Routing change

- F.Cu 3V3_DSM: bevel the 88.11-degree bend at (105.000, 124.002) mm. Keep its two remote endpoints, via and 0.25 mm width. The adjacent 3V3 routing remains exactly unchanged.
- B.Cu IMU_CS: bevel the two acute tips of the existing detour around the GND via. Keep its connectivity and 0.127 mm width.
- F.Cu 5V / C_RX: shift the two 5V bend vertices from y117.930 to y117.911 mm; clearance increases from 0.1415 to 0.1605 mm. Keep both widths.
- B.Cu USB_DP / USB_DN: move three D+ vertices by +0.030 mm on each axis to increase the local pair gap. Keep the 0.15 mm conductors and all USB vias. Maintain adjacent clearances by moving the existing SWDIO via +0.075 mm in y and the existing GND via +0.045 mm on each axis, with their attached tracks; shift one IMU_INT bend +0.100 mm in y.

Exact old/new native coordinates are in [route-changes.json](route-changes.json). The source comparison finds 18 existing segments and two vias modified, three segments added and no original routing item removed. All footprints/pads, selected parts, placements, arcs, board outline, stack/setup, zone/keepout definitions and rule settings remain unchanged. [Source invariants](source-invariants.json) record this comparison.

USB D+ straight-track length decreases by 0.027190 mm; D− and all arcs are unchanged. This geometry correction does not qualify USB impedance or end-to-end signal integrity.

## Native verification

KiCad 10.0.7; final fills saved with `kicad-cli pcb drc --refill-zones --save-board` using matching project/rule files. The final canonical board was then checked with `pcb drc --all-track-errors --schematic-parity --severity-all`.

| Check | Result |
| --- | --- |
| Main native DRC | 0 errors, 0 warnings, 0 unconnected items, 0 parity findings |
| Main and child ERC | 0 findings |
| Child native DRC | 0 errors, 11 existing courtyard warnings, 0 unconnected/parity findings |
| Power width / routing geometry | Pass; no tracks narrowed and no nonconforming vias |
| Drill/pasted-SMD contacts | 14 inherited contacts before and after; zero new contacts |
| BOM/CPL reproduction | Byte-identical: 51 groups / 83 placements; reviewed rotations retained |

Reports are in [native/](native/). A no-edit CLI refill comparison distinguishes fill regeneration from the routing changes; [fill-comparison.json](fill-comparison.json) records polygon XOR areas by copper layer. The read-only validation wrapper's path scan also inspected unrelated untracked `hardware/.history` backups and stopped on their relative model paths; the four canonical ERC/DRC commands above were run directly. No backup files or validation rules were changed.

## JLCDFM verification

Fresh JLCDFM PCB analysis completed using the exact final [input binding](input-binding.json). [Open the result](https://jlcdfm.com/viewer?pcbUploadFileId=634211420904001537).

| Category | Before danger/warning/good | After danger/warning/good |
| --- | --- | --- |
| Sharp trace corner | 0 / 2 / 0 | **0 / 0 / 0** |
| Trace spacing | 0 / 2 / 3 | **0 / 0 / 4** |

Both requested categories are green. Top spacing displays 0.16 mm; the repaired bottom USB spacing displays 0.17 mm. The other PCB category counts are unchanged. Raw/normalized category rows, spacing detail text and the single result screenshot are retained here. Input hashes were rechecked after the website analysis and remained unchanged. The new PCB and matched main CAM replace the earlier fabrication-cleanup copper revision; previous input bindings retain their original hashes.

## Remaining gates

This is a scoped copper/DFM correction. Other PCB findings and the previous assembly/model/process findings remain unresolved. Supplier stack/tolerances, pasted-via process, electrical/power/thermal qualification, physical fit and orientation/bring-up remain open. Release status remains **HOLD**.
