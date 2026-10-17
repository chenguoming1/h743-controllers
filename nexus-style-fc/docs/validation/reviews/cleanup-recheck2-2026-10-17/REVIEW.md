# Latest owner cleanup: regenerated Gerbers and fresh PCB DFM

Gerbers were regenerated from the owner's latest saved cleanup. No source geometry, placement, via, net, rules, project or schematic edits were made by this export. Native zone refill reproduced the incoming PCB bytes exactly.

- PCB SHA-256: `9f336260cb2f4fe6d2f12909121a6c1ba38d13a411f395b185c95ba06c104a24`
- Gerber ZIP SHA-256: `f0ce99b8ed7a4ad014bdbf4c2664a67e63bf02705fd6d772aa41aef7193623a4`
- Native copper DRC: zero violations and zero unconnected items; the same 10 schematic parity warnings remain.
- Minimum outer track width: 0.14 mm, verified across the full native segment inventory.
- Regenerated ZIP integrity and all 16 loose Gerber/drill/job members verified.
- BOM (51 groups) and corrected CPL (83 placements) reproduce byte-for-byte. SMT was not rerun for this copper revision. Child source/CAM remain unchanged.
- [Exact input binding](input-binding.json), [native DRC](drc.json)

Fresh [JLCDFM PCB analysis](https://jlcdfm.com/viewer?pcbUploadFileId=634285312339251202) completed. Trace width is **0 danger, 0 warning, 100 Good**. Sharp corners retain zero danger/warning; trace spacing retains zero danger/warning and four Good results. Pad-spacing warnings decreased **74 → 72**, with Good results increasing **22 → 24**; its four danger results remain. All other category counts match the preceding cleanup check. Website tables can be capped; these are displayed counts.

[Full category capture](pcb-summary.json) and [comparison](dfm-comparison.json) are retained. Source/CAM hashes were verified again after analysis.

![Latest cleanup DFM](pcb-result.jpg)

Earlier reports remain bound to their original inputs. Release status remains **HOLD** for other PCB, prior assembly/model and engineering qualification gates.
