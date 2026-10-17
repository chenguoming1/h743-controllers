# Matching review-only manufacturing files

**Do not order, fabricate or assemble.** Main CAM is regenerated from the current saved PCB; child CAM remains byte-identical.

- Main PCB SHA-256: `d559c9f926ca5481d2b7a4804515600edb6ee63832a2dd913d03a1fc9e044461`
- Child PCB SHA-256: `b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6`

The [Pad-spacing correction](../docs/validation/reviews/pad-spacing-2026-10-17/REVIEW.md) and [exact input binding](../docs/validation/reviews/pad-spacing-2026-10-17/input-binding.json) record the current PCB, regenerated Gerber ZIP, native connectivity/DRC and fresh PCB website check. Existing schematic/footprint/library warnings remain. The [earlier trace DFM correction](../docs/validation/reviews/trace-dfm-2026-10-17/REVIEW.md) is bound to its recorded earlier PCB/CAM. Other fabrication, assembly/model and process findings remain open.

Each folder has a Gerber/drill ZIP, JLC BOM and CPL. Main BOM has 51 groups/83 parts. The main CPL retains the 25 reviewed rotation corrections: bottom-side angle convention and U10 library offset. The BOM is byte-identical. The CPL updates only C31, R20, R21, U10 and Y1 coordinates for the small placement shifts; all sides, rotations and reference coverage remain unchanged.

The [CPL review](../docs/validation/reviews/cpl-2026-10-17/REVIEW.md) used predecessor CAM and a 48-group BOM. The later [pre-fix PCB/SMT recheck](../docs/validation/reviews/jlcdfm-current-2026-10-17/REVIEW.md) matched all 51 groups and screened the corrected placements on the fabrication-cleanup PCB. That recheck and the [fabrication-cleanup binding](../docs/validation/fabrication-fixes/INPUT-BINDING.json) retain their original hashes and apply to earlier copper. SMT was not rerun for this export. Supplier acceptance is not established.

Run `tools/export_fab.py` only when intentionally replacing matching exports; do not mix exports with reports for other Git revisions.
