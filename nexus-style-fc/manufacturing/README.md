# Matching review-only manufacturing files

**Do not order, fabricate or assemble.** Main CAM is regenerated from the current saved PCB; child CAM remains byte-identical.

- Main PCB SHA-256: `9f336260cb2f4fe6d2f12909121a6c1ba38d13a411f395b185c95ba06c104a24`
- Child PCB SHA-256: `b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6`

The [Owner cleanup DFM recheck](../docs/validation/reviews/cleanup-recheck2-2026-10-17/REVIEW.md) and [exact input binding](../docs/validation/reviews/cleanup-recheck2-2026-10-17/input-binding.json) record the current PCB, regenerated Gerber ZIP, native connectivity/DRC and fresh PCB website check. Existing schematic/footprint/library warnings remain. The [earlier trace DFM correction](../docs/validation/reviews/trace-dfm-2026-10-17/REVIEW.md) is bound to its recorded earlier PCB/CAM. Other fabrication, assembly/model and process findings remain open.

Each folder has a Gerber/drill ZIP, JLC BOM and CPL. Main BOM has 51 groups/83 parts. The main CPL retains the 25 reviewed rotation corrections: bottom-side angle convention and U10 library offset. All coordinates, sides and reference coverage remain unchanged, and the complete BOM/CPL reproduce byte-for-byte for this export.

The [CPL review](../docs/validation/reviews/cpl-2026-10-17/REVIEW.md) used predecessor CAM and a 48-group BOM. The later [pre-fix PCB/SMT recheck](../docs/validation/reviews/jlcdfm-current-2026-10-17/REVIEW.md) matched all 51 groups and screened the corrected placements on the fabrication-cleanup PCB. That recheck and the [fabrication-cleanup binding](../docs/validation/fabrication-fixes/INPUT-BINDING.json) retain their original hashes and apply to earlier copper. SMT was not rerun for this export. Supplier acceptance is not established.

Run `tools/export_fab.py` only when intentionally replacing matching exports; do not mix exports with reports for other Git revisions.
