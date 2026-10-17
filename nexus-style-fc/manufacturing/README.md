# Matching review-only manufacturing files

**Do not order, fabricate or assemble.** Main CAM is regenerated from the current saved PCB; child CAM remains byte-identical.

- Main PCB SHA-256: `6295c7ebda6c8a4035064f235072d56e1d6e0ff1b7e6b0402f908ce372ae901e`
- Child PCB SHA-256: `b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6`

The [owner VX/3V3 cleanup recheck](../docs/validation/reviews/owner-vx-recheck-2026-10-17/REVIEW.md) and [exact input binding](../docs/validation/reviews/owner-vx-recheck-2026-10-17/input-binding.json) record the current PCB and regenerated Gerber ZIP. Native DRC has zero violations/opens and the same ten inherited parity findings. The owner's route geometry is preserved; cached ground pours were refreshed. Main project, rules, schematic, 51-group/83-part BOM, 83-placement CPL and child PCB/CAM remain unchanged. There are 227 vias. Earlier reports retain their predecessor bindings. Other fabrication, assembly/model and process findings remain open.

Fresh [PCB DFM](https://jlcdfm.com/viewer?pcbUploadFileId=634325109695401986) matches all 29 preceding category counts, including green width, spacing, pad spacing, corners and mask-to-trace.

Each folder has a Gerber/drill ZIP, JLC BOM and CPL. Main BOM has 51 groups/83 parts. The main CPL retains the 25 reviewed rotation corrections: bottom-side angle convention and U10 library offset. The BOM is byte-identical. The BOM and CPL are byte-identical to the preceding C9/C11 placement revision. Mask-to-trace warnings are now zero; five unconfirmed negative-expansion flags remain. Spacing, width and corners remain green.

**C8 pad 2 contains a 0.20 mm drill via. Specify epoxy-filled and copper-capped via-in-pad (POFV) and confirm the production files. Ordinary tenting is insufficient because the pad mask opening exposes the hole. No factory process selection has been confirmed.**

The [CPL review](../docs/validation/reviews/cpl-2026-10-17/REVIEW.md) used predecessor CAM and a 48-group BOM. The later [pre-fix PCB/SMT recheck](../docs/validation/reviews/jlcdfm-current-2026-10-17/REVIEW.md) matched all 51 groups and screened the corrected placements on the fabrication-cleanup PCB. That recheck and the [fabrication-cleanup binding](../docs/validation/fabrication-fixes/INPUT-BINDING.json) retain their original hashes and apply to earlier copper. SMT was not rerun for this export. Supplier acceptance is not established.

Run `tools/export_fab.py` only when intentionally replacing matching exports; do not mix exports with reports for other Git revisions.
