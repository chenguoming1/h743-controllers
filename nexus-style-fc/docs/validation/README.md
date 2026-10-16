# Nexus validation and provenance

This is the single evidence location. **The working design is `../../hardware/`, not any historical report or illustration here. Nothing here grants fabrication, assembly or flight approval.**

## Current checks

- [Consolidation report](consolidation/REPORT.md): fresh read-only KiCad 10.0.7 ERC/DRC, native/source/BOM/CPL checks and path inventory
- [Main stage36 engineering report](stage36/MAIN-PLACEMENT-CHECKPOINT.md) and [original source seal](stage36/ENGINEERING-CHECKPOINT-SEAL.json)
- [Stage36 PCB-only JLCDFM](reviews/jlcdfm-main-stage36/REVIEW-STATUS.md): assembly result unavailable; CPL acceptance uncertain
- [Child b49ef410 JLCDFM](reviews/jlcdfm-child-b49ef410/REVIEW-STATUS.md), [child engineering review](child-b49ef410/ENGINEERING-REVIEW.md) and [mechanical proposal](child-b49ef410/verification/mechanical/PCB_ONLY_PROPOSAL.md)
- [Stage35 DFM](reviews/jlcdfm-main-stage35/REVIEW-STATUS.md) and [stage10 DFM](reviews/jlcdfm-stage10/REVIEW-STATUS.md) are historical main-board evidence, not fresh stage36 assembly validation

Both native designs, library definitions and matching manufacturing exports retain their exact published content. Latest `tools/design.py` has SHA-256 `ea95b1c7edfe1ec5db765c5b3823a4f388d633cb98e46f93df7777893b8a56a0`, restored by the owner before consolidation. Excluded historical `design.py` and `prepared-design.py` have not been reconstructed or added.

## How evidence is bound to a revision

[Source map](SOURCE-MAP.json) maps retained files to their original paths and Git blob IDs at source commit [fad6207](https://github.com/chenguoming1/h743-controllers/tree/fad62076054229a1d3de79106984d8b71906379e/nexus-style-fc). Main and child source files were promoted from its `routing-wip/2026-10-15/stage36-main-child-checkpoint/candidate/`. Existing root 3D model dependencies and the firmware reference were retained.

Reports, seals, hashes and historical reproduction scripts retain their original bytes. Their embedded paths and relative links describe the original sealed layout and are not instructions to regenerate the canonical design. Use `source_path` in the source map with the pinned commit above to inspect a report in its original context. Historical scripts may require historical inputs that now exist only in Git; they are evidence, not supported current build entrypoints. Unrouted comparison boards, duplicate CAD project copies, old CAM exports and source ZIPs were intentionally removed from the working tree and remain recoverable from that commit.

`history/` holds unique earlier review evidence, deduplicated by Git blob identity. Revision folders here are evidence only; they contain no `.kicad_pcb`, `.kicad_sch`, `.kicad_pro` or generator copies. Older claims apply only to the revision named by each report. Exact project states and redundant copies belong in Git history.

## Open release gates

The inherited detailed reviews do not supersede these current limits:

- Stage36 PCB-only DFM still shows six pad-spacing danger counts; no stage36 assembly result
- U10 external model/overlap and real assembly fit remain unqualified
- C10/NRST local placement remains unresolved; no electrical redesign was attempted here
- Matched main/child fit, edge access and mechanical/vibration tests remain open
- Supplier stackup, board thickness, copper weight, tenting/stencil and other process approval remain open
- Header/contact current and physical joints need qualification; retained header rating is 3 A, not a 10 A system rating
- Effective capacitance, thermal/transient, SI/PI/EMI, firmware orientation/bring-up and flight tests remain open

The fresh ERC reports each retain four inherited ignored checks: `single_global_label`, `four_way_junction`, `simulation_model_issue`, `footprint_filter`. DRC disables no checks. Read the reports rather than interpreting zero errors as unconditional sign-off.
