# Matching review-only manufacturing files

**Do not order, fabricate or assemble.** Main CAM was regenerated from the current fabrication-cleanup PCB; child CAM remains byte-identical.

- Main PCB SHA-256: `7a5abe70f1c7f0ac5693cfa4a3156432f6321f5907bbcb0e0892687da51a5d60`
- Child PCB SHA-256: `b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6`

Each folder has a Gerber/drill ZIP, JLC BOM and CPL. Main BOM has 51 groups/83 parts; the group increase reflects artwork-only footprint names, with no selected-part change. Main CPL remains byte-identical.

[Exact hashes](../docs/validation/fabrication-fixes/INPUT-BINDING.json) and [verification/open gates](../docs/validation/fabrication-fixes/REPORT.md) bind this checkpoint. Stage36 website results are predecessor evidence. No new website check or supplier acceptance of these exact CAM bytes is claimed.

Run `tools/export_fab.py` only when intentionally replacing matching exports; do not mix exports with reports for other Git revisions.
