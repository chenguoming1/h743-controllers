# Matching review-only manufacturing files

**Do not order, fabricate or assemble.** Main CAM was regenerated from the current fabrication-cleanup PCB; child CAM remains byte-identical.

The [17 October CPL review](../docs/validation/reviews/cpl-2026-10-17/REVIEW.md) corrects the main bottom-side angle convention and U10's library offset. The restored correction changes 25 rotation fields only, preserving all 83 coordinates/sides and the child CPL. The exporter retains these corrections. Its website check used the predecessor PCB/CAM and 48-group BOM; current regenerated CAM and the 51-group artwork BOM require their own screening.

- Main PCB SHA-256: `7a5abe70f1c7f0ac5693cfa4a3156432f6321f5907bbcb0e0892687da51a5d60`
- Child PCB SHA-256: `b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6`

Each folder has a Gerber/drill ZIP, JLC BOM and CPL. Main BOM has 51 groups/83 parts; the group increase reflects artwork-only footprint names, with no selected-part change. Main CPL has the 25 reviewed rotation corrections; all other placement fields are unchanged.

[Fabrication-cleanup input hashes](../docs/validation/fabrication-fixes/INPUT-BINDING.json) and [verification/open gates](../docs/validation/fabrication-fixes/REPORT.md) record the newer PCB/CAM/BOM checkpoint before the CPL correction. Their CPL hash is historical. The corrected main CPL SHA-256 is `a10c80abb5c3d631555b580210867ee7d5d8c59c95325255dc70e814855deb21`, as recorded in the CPL review. Stage36 website results and the CPL preview check are predecessor-input evidence; no website check or supplier acceptance of these current CAM bytes is claimed. Remaining assembly clearance/model and process findings stay open.

Run `tools/export_fab.py` only when intentionally replacing matching exports; do not mix exports with reports for other Git revisions.
