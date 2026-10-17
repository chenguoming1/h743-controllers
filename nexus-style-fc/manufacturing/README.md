# Matching review-only manufacturing files

**Do not order, fabricate or assemble: existing engineering qualification gates remain open.** Main CAM is regenerated for the USB 90 ohm correction; child CAM retains the latest owner cleanup.

- Main PCB SHA-256: `9b65ab90e9dfeecf8a440e4f1b522658419ee2d56a4e27513e03e35bf77e16ac`
- Main ZIP SHA-256: `bb8fd82bbd7b350da7e54eec824241b7af8f125061c9c5e2e6cc442fd68b9331`
- Child PCB SHA-256: `6d9314f769088949b64ade2e3b34fc67641186d3c02edc409738440645df874f`
- Child ZIP SHA-256: `220a5538215ab0a829b9129b38530612ca728193e13607ce38c0b8052dd3a36c`

The [USB correction review](../docs/validation/reviews/usb-compliance-2026-10-17/REVIEW.md) and its input/applied bindings describe current main source and the 16-member CAM ZIP. Native main DRC has zero violations/opens and ten inherited parity findings. All footprints, non-USB routed copper and 227 vias are preserved. Main BOM/CPL remain 51 groups / 83 parts / 83 placements and byte-identical; SMT was not rerun.

**Main: use [JLC06161H-2116A fabrication requirements](nexus-style-fc/FABRICATION-NOTES.md)**, six layers, nominal 1.6 mm order category (vendor special finished thickness 1.56 mm ±10%), 1 oz outer / 0.5 oz inner. Request **90 Ω differential ±10%** for USB on In3, width 0.143 mm / gap 0.154 mm, referenced to In4 ground across 0.130 mm core. Local calculated impedance is about 90 Ω; supplier process/coupon and prototype USB electrical qualification remain pending. The job's impedance-controlled flag is an order requirement, not a measured result.

Fresh [main PCB DFM](https://jlcdfm.com/viewer?pcbUploadFileId=634351113752236033) exactly matches all 29 predecessor category triples, including green width, spacing, pad spacing, corners and mask-to-trace. Existing annular, mask, slot, via-to-pad and silk findings remain.

The [latest child cleanup check](../docs/validation/reviews/child-dfm-20261017-200904/REVIEW.md) binds the current 14-member child ZIP. It has zero native errors/opens/parity issues, 11 inherited courtyard warnings and fresh JLCDFM zero danger / 38 warnings. **Child: use its separate [four-layer settings](nexus-header-board/FABRICATION-NOTES.md): nominal 1.6 mm, 2 oz outer AND inner, JLC041622-3313.** Child source/CAM/BOM/CPL are unchanged by the USB correction. Earlier power-loss calculations retain their earlier PCB binding; thermal/contact/BEC/system current qualification remains open.

**C8 pad 2 contains a 0.20 mm drill via. Specify epoxy-filled and copper-capped via-in-pad (POFV) and confirm production files. Ordinary tenting is insufficient inside the solder-pad aperture.**

Each folder contains matching Gerber/drill ZIP, BOM and CPL. Earlier [CPL](../docs/validation/reviews/cpl-2026-10-17/REVIEW.md), [PCB/SMT](../docs/validation/reviews/jlcdfm-current-2026-10-17/REVIEW.md) and other historical reports retain their original source bindings. Remaining release gates are listed in [validation](../docs/validation/README.md).

Run `tools/export_fab.py` only when intentionally replacing matching exports; do not mix exports with reports for other revisions.
