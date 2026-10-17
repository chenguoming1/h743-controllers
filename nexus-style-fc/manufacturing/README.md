# Matching review-only manufacturing files

**Do not order, fabricate or assemble.** Main CAM is unchanged; child CAM is regenerated for the four-layer power upgrade.

- Main PCB SHA-256: `6295c7ebda6c8a4035064f235072d56e1d6e0ff1b7e6b0402f908ce372ae901e`
- Child PCB SHA-256: `12d537492ebb7aa347e30c78c758efbdbd6e238425f0095282cbf7188e872e23`

The [owner VX/3V3 cleanup recheck](../docs/validation/reviews/owner-vx-recheck-2026-10-17/REVIEW.md) and [exact input binding](../docs/validation/reviews/owner-vx-recheck-2026-10-17/input-binding.json) record the current main PCB and Gerber ZIP. Native main DRC has zero violations/opens and the same ten inherited parity findings. The owner's route geometry is preserved. Main project, rules, schematic, 51-group/83-part BOM and 83-placement CPL remain unchanged. There are 227 main vias. Earlier reports retain their predecessor bindings. Other fabrication, assembly/model and process findings remain open.

The [child power-upgrade review](../docs/validation/reviews/child-full-load-2026-10-17/REVIEW.md) binds the current child PCB and 14-member Gerber/drill/job ZIP, including both inner planes. **Use the [four-layer fabrication settings](nexus-header-board/FABRICATION-NOTES.md): nominal 1.6 mm, 2 oz outer and 2 oz inner, JLC041622-3313 stack reference.** The child BOM/CPL are unchanged. Native child DRC has zero errors/opens/parity issues and 11 inherited missing-courtyard warnings. Calculated electrical loss is reduced; temperature rise and complete-system current capacity remain unqualified.

Fresh [PCB DFM](https://jlcdfm.com/viewer?pcbUploadFileId=634325109695401986) matches all 29 preceding category counts, including green width, spacing, pad spacing, corners and mask-to-trace.

Each folder has a Gerber/drill ZIP, JLC BOM and CPL. Main BOM has 51 groups/83 parts. The main CPL retains the 25 reviewed rotation corrections: bottom-side angle convention and U10 library offset. The BOM is byte-identical. The BOM and CPL are byte-identical to the preceding C9/C11 placement revision. Mask-to-trace warnings are now zero; five unconfirmed negative-expansion flags remain. Spacing, width and corners remain green.

**C8 pad 2 contains a 0.20 mm drill via. Specify epoxy-filled and copper-capped via-in-pad (POFV) and confirm the production files. Ordinary tenting is insufficient because the pad mask opening exposes the hole. No factory process selection has been confirmed.**

The [CPL review](../docs/validation/reviews/cpl-2026-10-17/REVIEW.md) used predecessor CAM and a 48-group BOM. The later [pre-fix PCB/SMT recheck](../docs/validation/reviews/jlcdfm-current-2026-10-17/REVIEW.md) matched all 51 groups and screened the corrected placements on the fabrication-cleanup PCB. That recheck and the [fabrication-cleanup binding](../docs/validation/fabrication-fixes/INPUT-BINDING.json) retain their original hashes and apply to earlier copper. SMT was not rerun for this export. Supplier acceptance is not established.

Run `tools/export_fab.py` only when intentionally replacing matching exports; do not mix exports with reports for other Git revisions.
