# Nexus main stage36 JLCDFM results

Fresh PCB and SMT numerical checks are complete. Unresolved manufacturing and model-alignment findings remain. This is not a manufacturing release.

## Exact revision

All 262 sealed files were verified. The 16 Gerber/drill ZIP members match the sealed manufacturing directory. PCB SHA-256: bed37199e8d62b8135a27b9e182f8e8f584f1a9fb722cb6efb5d4c87b2a320b8. Upload and seal hashes are in input-binding.json. These results apply only to main-adc-stage36, not later revisions.

The resumed website explicitly reported no bound BOM/CPL before the exact sealed files were restored. JLC then confirmed 48 BOM groups, reconciled to all 83 designators, and returned fresh SMT calculation results on 2026-10-16 at 08:00 UTC. The earlier uncertain upload is resolved.

## Comparison with stage35

- PCB pad-spacing dangers decreased from 7 to 6; good count 16 to 17.
- Trace-width warnings decreased from 92 to 86; good count 8 to 14.
- Mask-exposure warnings increased from 83 to 84. Mask-exposure dangers and unconnected trace ends remain zero.
- Other 26 PCB categories are unchanged.
- All 18 SMT category danger/warning counts are unchanged. Only collision-good count increased from 2 to 3.

## U10 remains unresolved

Matched part: C89347, TPS70933DBVR, footprint TPS70933DBVR_TI_DBV0005A. Top CPL placement is x=9.45 mm, y=26.1 mm, rotation=0 degrees.

- One pin-without-pad danger
- Four lead-overlap dangers, each ratio 0.66 (danger threshold 0.75)
- Two outer-edge dangers, each 0.15 mm
- One misalignment warning, 0.96 mm

The combined report labels lead overlap as 0.02 mm, inconsistent with its detailed table, which explicitly defines the value as a ratio. The 0.66 detail values are preserved.

The cloud browser cannot render the 3D models. Its fallback SVG represents U10 as a label rectangle without pins, so it cannot establish pin-1 orientation or justify changing the CPL. No placement or rotation was changed.

## Other retained findings

PCB: 6 displayed pad-spacing dangers, 3 via-to-pad dangers, 4 slot-width dangers, plus annular-ring, mask and silkscreen results. Pad-spacing tables are capped at 50 rows per side and refer only to aperture shapes, not nets.

SMT: 4 component-edge dangers (J2, R11, R12, U4), 10 lead-to-hole dangers, 9 left-edge dangers, 3 right-edge dangers, plus the U10 findings and 7 misalignment warnings. These generic checks require interpretation against real component geometry and fabrication/assembly processes. Localized tables are retained where obtained.

## Evidence and limitations

- stage36-dfm-findings.json: all 29 PCB and 18 SMT rows, comparison, exact binding and localized details
- matched-parts.json: 48 confirmed groups, covering 83 designators
- pcb-summary.csv and pcb-pad-spacing-details.csv: existing PCB tables
- smt-summary.json, smt-localized-details.json, pcb-via-pad-details.json: new extracted tables
- Sanitized UI snapshots and screenshots: returned values, including the stalled rendering limitation

One PDF export attempt stalled and its 10-second download wait timed out. Combined-report text is retained instead. An additional read-only Pin left edge detail action was denied after the main results had been captured; further browser actions stopped.

No factory-specific stack-up, tenting, via fill/plug/cap, stencil, panel handling or model orientation approval was obtained. No order, payment, outreach, design/rule/placement modification or publication occurred in this check.
