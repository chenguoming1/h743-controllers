# Fresh child-board DFM check — 2026-10-17 20:09 SGT

Saved child PCB SHA-256: `6d9314f769088949b64ade2e3b34fc67641186d3c02edc409738440645df874f`.
Gerber ZIP SHA-256: `220a5538215ab0a829b9129b38530612ca728193e13607ce38c0b8052dd3a36c`.

[Fresh JLCDFM result](https://jlcdfm.com/viewer?pcbUploadFileId=634336887604203522) — all 29 PCB categories analyzed: **0 danger, 38 warnings**. The 12 annular-ring and 26 through-hole-to-SMD warning counts are unchanged from the previous four-layer upload. Trace width, spacing, pad spacing, copper/pad edge clearance, solder mask, sharp corners and slot checks have no warnings. Trace-width good count changed 34 to 33. Warning counts alone do not establish that each individual location is identical.

Native DRC in the original project: **0 errors, 0 unconnected items, 0 schematic parity issues**, and 11 inherited missing-courtyard warnings on the joint pads. A temporary copied project initially reported 12 additional missing-library configuration warnings; the check in the canonical project resolves them. `drc-canonical.json` is the authoritative report.

Zones were refilled in a temporary snapshot; its final bytes match the saved source exactly. Regenerated only child-board Gerbers and drills with four copper layers. ZIP contains 14 files and each matches the loose CAM file. Saved source and main PCB unchanged during this check. BOM/CPL not regenerated; SMT DFM not rerun.

This is a manufacturability check, not a thermal/current or flight qualification. Earlier electrical calculation evidence remains bound to its own earlier source hash.
