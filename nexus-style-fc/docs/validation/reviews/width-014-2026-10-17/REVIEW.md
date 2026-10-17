# Clearance-safe 0.14 mm outer traces — 17 October 2026

Widened **456 outer-layer routing segments from 0.127 to 0.14 mm**. Kept **70 constrained segments at 0.127 mm**, as explicitly selected by the user. Inner-layer traces and USB trace widths remain unchanged. No route centerlines/endpoints, vias, parts, pads, net assignments, outline, stack, rules or keepouts were moved or changed.

The initial trial widened all 526 eligible outer segments and produced 73 native clearance violations involving 70 segments. That trial was rejected. Those segments were restored to their incoming widths; the final candidate was re-poured using matching project/rule files and passes native copper DRC with **zero violations and zero opens**. The incoming schematic's **10 footprint-parity warnings remain exactly unchanged**. Its previously recorded two library-symbol ERC warnings are outside this width change; the schematic/project bytes are unchanged.

[Width receipts](width-changes.json) list all widened and retained UUIDs, nets, layers and lengths. [Rejected trial](rejected-all-widened-trial-drc.json) records the clearance blockers. This report does not claim every remaining segment could never be widened; doing so would require a separately scoped routing change. No clearance rules or exclusions were relaxed.

Main Gerber/drill files were regenerated. The 51-group BOM and 83-placement CPL reproduce byte-for-byte. The child board and its exports remain unchanged. [Input binding](input-binding.json) binds the current source and CAM; [native DRC](drc.json) includes schematic parity.

Fresh baseline/final JLCDFM comparison completed. The new **0.14 mm traces classify as Good**. Displayed trace-width warnings decreased **86 → 27**; sharp corners stay **0**, and displayed trace-spacing warnings remain **1**, matching the incoming board. Pad-spacing warnings decrease 78 → 77; other category counts are unchanged.

The width details cap at the first 50 results per layer. Website summary counts therefore differ from the native counts of 456 widened / 70 retained segments. Remaining website width warnings come from retained 0.127 mm copper.

[Final website result](https://jlcdfm.com/viewer?pcbUploadFileId=634253917743124482) · [Incoming-board comparison](https://jlcdfm.com/viewer?pcbUploadFileId=634253942373699585). [Screenshot](pcb-result.jpg), raw category rows and Good-filter width details are retained. Exact source/CAM hashes were verified again after the website checks. Earlier reports retain their recorded earlier input hashes. Other fabrication, assembly and engineering gates remain open; release status remains **HOLD**.
