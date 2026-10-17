# Nexus validation and provenance

This is the single evidence location. **The working design is `../../hardware/`, not any historical report or illustration here. Nothing here grants fabrication, assembly or flight approval.**

## Current checks

- [Final outer-layer 0.14 mm routing](reviews/width-final-2026-10-17/REVIEW.md): current PCB/CAM, all outer tracks at least 0.14 mm, local route adjustments and 0.016 mm IMU_CS via shift; native/website checks
- [Partial-segment 0.14 mm width improvement](reviews/width-profile-2026-10-17/REVIEW.md): earlier PCB/CAM, 57.8 mm widened across 25 nets with short narrow necks retained; fresh native/website checks
- [Gerber regeneration and JLCDFM reupload](reviews/gerber-reupload-2026-10-17/REVIEW.md): earlier saved PCB/CAM, unchanged assembly files and native/website PCB check
- [0.14 mm outer trace widths](reviews/width-014-2026-10-17/REVIEW.md): earlier copper/CAM, 456 clearance-safe width changes, 70 constrained sections retained, native checks and website comparison
- [TAIL loop cleanup](reviews/tail-route-2026-10-17/REVIEW.md): earlier copper/CAM, preserved protection and exact connectivity; incoming schematic/library warnings retained
- [Trace DFM correction](reviews/trace-dfm-2026-10-17/REVIEW.md): earlier corner/spacing correction and its exact PCB screening
- [Fabrication cleanup](fabrication-fixes/REPORT.md): predecessor copper checks, artwork changes and open gates
- [Pre-fix JLCDFM PCB/SMT recheck](reviews/jlcdfm-current-2026-10-17/REVIEW.md): earlier Gerbers, unchanged 51-group BOM and corrected 83-placement CPL screened; remaining assembly flags recorded

- [Consolidation report](consolidation/REPORT.md): fresh read-only KiCad 10.0.7 ERC/DRC, native/source/BOM/CPL checks and path inventory
- [Main stage36 engineering report](stage36/MAIN-PLACEMENT-CHECKPOINT.md) and [original source seal](stage36/ENGINEERING-CHECKPOINT-SEAL.json)
- [17 October CPL correction and assembly check](reviews/cpl-2026-10-17/REVIEW.md): verified bottom angles and U10 offset for the unchanged pad placements; 83 placements checked on predecessor CAM with its 48-group BOM
- [Stage36 predecessor PCB/SMT JLCDFM](reviews/jlcdfm-main-stage36/REVIEW-STATUS.md): completed numerical screening; historical findings and process limits, not current CAM approval
- [Child b49ef410 JLCDFM](reviews/jlcdfm-child-b49ef410/REVIEW-STATUS.md), [child engineering review](child-b49ef410/ENGINEERING-REVIEW.md) and [mechanical proposal](child-b49ef410/verification/mechanical/PCB_ONLY_PROPOSAL.md)
- [Stage35 DFM](reviews/jlcdfm-main-stage35/REVIEW-STATUS.md) and [stage10 DFM](reviews/jlcdfm-stage10/REVIEW-STATUS.md) are historical main-board evidence

The consolidation preserved the owner-restored source. The current fabrication cleanup adds main-only artwork identities and reviewed symbol filters while retaining parts, pad geometry and placement. The restored CPL correction changes 25 rotation fields only; coordinates, sides and reference coverage are preserved. The current BOM has 51 groups/83 parts. The CPL review's website result remains bound to its recorded predecessor PCB/CAM and 48-group BOM. The subsequent PCB/SMT recheck screens the fabrication-cleanup CAM and 51-group BOM with the corrected CPL. The latest width pass brings all outer-layer tracks to at least 0.14 mm using local routing adjustments and one small via shift; assembly files are unchanged and its own report binds the new PCB analysis. SMT was not rerun for this export. Historical seals and input bindings retain their original hashes, including the pre-correction CPL entry in the fabrication-cleanup binding. Excluded historical generators have not been restored.

## How evidence is bound to a revision

[Source map](SOURCE-MAP.json) maps retained files to their original paths and Git blob IDs at source commit [fad6207](https://github.com/chenguoming1/h743-controllers/tree/fad62076054229a1d3de79106984d8b71906379e/nexus-style-fc). Main and child source files were promoted from its `routing-wip/2026-10-15/stage36-main-child-checkpoint/candidate/`. Existing root 3D model dependencies and the firmware reference were retained.

Reports, seals, hashes and historical reproduction scripts retain their original bytes. Their embedded paths and relative links describe the original sealed layout and are not instructions to regenerate the canonical design. Use `source_path` in the source map with the pinned commit above to inspect a report in its original context. Historical scripts may require historical inputs that now exist only in Git; they are evidence, not supported current build entrypoints. Unrouted comparison boards, duplicate CAD project copies, old CAM exports and source ZIPs were intentionally removed from the working tree and remain recoverable from that commit.

`history/` holds unique earlier review evidence, deduplicated by Git blob identity. Revision folders here are evidence only; they contain no `.kicad_pcb`, `.kicad_sch`, `.kicad_pro` or generator copies. Older claims apply only to the revision named by each report. Exact project states and redundant copies belong in Git history.

## Open release gates

The inherited detailed reviews do not supersede these current limits:

- Current PCB DFM retains four pad-spacing, three via-to-pad and four slot-width danger flags, plus capped silkscreen findings; the prior assembly DFM recorded 24 danger flags and 13 warnings
- U10's CPL orientation and model overlap were clear in the prior assembly preview; real assembly fit remains unqualified
- C10/NRST local placement remains unresolved; no electrical redesign was attempted here
- Matched main/child fit, edge access and mechanical/vibration tests remain open
- Supplier stackup, board thickness, copper weight, tenting/stencil and other process approval remain open
- Header/contact current and physical joints need qualification; retained header rating is 3 A, not a 10 A system rating
- Effective capacitance, thermal/transient, SI/PI/EMI, firmware orientation/bring-up and flight tests remain open

The fresh ERC reports each retain four inherited ignored checks: `single_global_label`, `four_way_junction`, `simulation_model_issue`, `footprint_filter`. DRC disables no checks. Read the reports rather than interpreting zero errors as unconditional sign-off.
