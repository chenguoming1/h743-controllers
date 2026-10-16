# Nexus main stage36 JLCDFM check

Status: Fresh PCB DFM tables returned. CPL upload completion is unverified; no assembly DFM result. Not a manufacturing release.

## Revision binding

All 262 sealed files verified. Every Gerber/drill ZIP member matches the sealed manufacturing directory. Main PCB SHA-256: bed37199e8d62b8135a27b9e182f8e8f584f1a9fb722cb6efb5d4c87b2a320b8. Full exact upload hashes are in input-binding.json.

## Changes from stage35

- Pad-spacing dangers: 7 → 6; good: 16 → 17.
- Trace-width warnings: 92 → 86; good: 8 → 14.
- Mask-exposure warnings: 83 → 84. Mask-exposure dangers remain 0.
- Unconnected trace-end remains 0/0/0.
- Other 26 PCB categories unchanged.

These are the site's capped generic-rule counts, not exhaustive physical defect counts. Pad-spacing detail exposes 50 rows per side out of 201 bottom / 136 front. Six shown dangers consist of one front at 0.05 mm and five bottom at displayed 0.08, 0.08, 0.08, 0.09, 0.1 mm. Aperture descriptions do not identify nets or reference designators.

## Assembly blocker

The matching BOM is accepted. After renewed user approval, CPL file selection/upload executed at 2026-10-16 00:12:36 UTC. The immediate page showed uploading; a follow-up read-only verification was blocked. CPL acceptance remains uncertain. No duplicate upload or assembly processing was attempted. There are no stage36 assembly results; prior U10 findings remain historical until rerun. The retained BOM-only snapshot predates the CPL attempt.

## Evidence and limits

- pcb-summary.csv: all 29 returned PCB rows
- pcb-pad-spacing-details.csv: 100 displayed localized rows
- Sanitized website snapshots and screenshots preserve the returned values
- stage36-dfm-findings.json: exact binding, comparison and limitations

The rendering area remains behind a Retrieving DFM data overlay, so visual placement/model proof is unavailable. Detail images are explanatory examples. No stage36 PDF export was attempted. No factory-specific stack, tenting, fill/plug/cap, stencil or other process acceptance was obtained. No order, payment, outreach, design/rule/placement modification or publication occurred.
