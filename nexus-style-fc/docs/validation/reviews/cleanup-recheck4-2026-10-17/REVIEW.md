# Latest owner cleanup: regenerated Gerbers and fresh PCB DFM

Gerbers were regenerated from the owner's latest saved cleanup. No route geometry, placement, via, net, rules, project or schematic edits were made by this export. Native zone refill refreshed only filled polygons; all other source nodes and zone definitions were verified unchanged. The filled board was saved before CAM generation.

- Incoming PCB SHA-256: `92b01bb3753449f07f21dd46070abf9350fdda20a21e9023a198fa670d56b788`
- Refilled PCB SHA-256: `9cfa914edcbad621a8c919f35c63ad56197c91e9c339928b4c6609e8aaa7e7e5`
- Gerber ZIP SHA-256: `9b8f6b21fdc89275fd8ce41ab74fef3dc047063f1d5b98626f0602c68f55ee34`
- Native copper DRC: zero violations and zero unconnected items; the same 10 schematic parity warnings remain.
- Minimum outer track width: 0.14 mm, verified across the full native segment inventory.
- Regenerated ZIP integrity and all 16 loose Gerber/drill/job members verified.
- BOM (51 groups) and corrected CPL (83 placements) reproduce byte-for-byte. SMT was not rerun for this copper revision. Child source/CAM remain unchanged.
- [Exact input binding](input-binding.json), [native DRC](drc.json)

Fresh [JLCDFM PCB analysis](https://jlcdfm.com/viewer?pcbUploadFileId=634287341780295681) completed. Trace width is **0 danger, 0 warning, 100 Good**. Sharp corners retain zero danger/warning; trace spacing retains zero danger/warning and four Good results. Pad-spacing warnings decreased **70 → 69**, with Good results increasing **26 → 27**; its four danger results remain. All other category counts match the preceding cleanup check. Website tables can be capped; these are displayed counts.

[Full category capture](pcb-summary.json) and [comparison](dfm-comparison.json) are retained. Source/CAM hashes were verified again after analysis.

![Latest cleanup DFM](pcb-result.jpg)

Earlier reports remain bound to their original inputs. Release status remains **HOLD** for other PCB, prior assembly/model and engineering qualification gates.
