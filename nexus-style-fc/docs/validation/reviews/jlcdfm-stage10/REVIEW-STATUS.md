# Nexus stage10: JLC automated DFM receipt

Observed 2026-10-15 in dot's cloud browser at https://jlcdfm.com/.

## Outcome

The sealed main and child Gerber/drill ZIPs and their matching BOM/CPL CSVs were accepted. The main BOM produced 48 confirmed rows; the child produced one confirmed row. Automatic PCB and SMT checks returned findings for both projects. This is not a fabrication or assembly release.

The main was detected as six copper layers, 22.4 × 33.1 mm; the child as two layers, 22.4 × 11.0 mm. Observed main routing-detail layer lists expose front/back copper only. Application of the same checks to inner layers is unverified. No factory stack was selected or accepted. Source nominal thickness remains 1.600 mm; the main saved copper/dielectric sum is 1.6168 mm.

## Priority findings

- Main U10, matched to TPS70933DBVR / C89347, top, uploaded rotation 0°: one pin-without-pad danger; two pin-outer-edge dangers at 0.21 mm; four lead/pad overlap dangers at ratio 0.54 against displayed 0.75/0.90 thresholds; a 0.96 mm warning in the site's through-hole-misalignment category. Pad geometry, placement convention and the library model must be reconciled before choosing a correction. No cause was established.
- Main lead-to-hole dangers: top J4, J2, U3, U2 twice, C19, U11 and J5 at displayed 0 mm; J3 at 0.05 mm. Displayed legend 0.20/0.25 mm; the site describes solder-wicking risk. Three further bottom-side entries have no recovered component localization.
- Main top J2 component-to-board-edge distance is 0.33 mm versus displayed 0.51/0.81 mm legend. J3 0.58 mm, R22 0.70 mm and C17 0.80 mm are warnings. One bottom danger and three bottom warnings remain unlocalized.
- Main PCB pad-spacing minimum displayed 0.05 mm is between approximately 0.600 × 1.700 mm rectangular copper and a 0.450 mm round primitive. Native comparison supplied separately suggests a same-net via/pad candidate; site XY/net identity was unavailable. This is not established as an electrical clearance violation.
- Four main PTH-slot width entries display 0.600 mm and fall below the built-in 24 mil / 0.6096 mm danger cutoff. These align with the source's four USB shell slots; the built-in rule is not itself the factory's plated-slot capability. No rule was relaxed.
- Child J1 matched C32713294 explicitly as Through Hole. Its SMT table contains seven board-edge warnings at 0.56 mm, displayed legend 0.51/0.81 mm. Acceptance of its CPL does not qualify through-hole insertion or soldering as ordinary SMT.

## Evidence and limitations

- `stage10-dfm-findings.json`: consolidated technical findings, all six upload hashes, source/manifest binding, source CPL values for localized components, and detailed limitations.
- `main-combined-report-visible-text.txt` and `child-combined-report-visible-text.txt`: exact report content recovered from the rendered page. These are page-text receipts, not downloaded PDFs.
- `private-originals/`: unmodified browser receipts and loading-preview screenshot. Keep private; some records include private project/session URLs. The screenshot shows only component placeholders under a loading overlay, not a validated PCB overlay.
- Actual PDF downloads did not complete. The child download waiter timed out after 60 seconds; main export also stalled. Both website report screenshot columns say “No.”
- The site reported unsupported 3D rendering. Geometry and 2D placement rendering stayed in loading state after supported reload/runtime recovery. This blocks visual orientation and location verification.
- Bottom SMT layer clicks were intercepted by the loading overlay. `main-smt-bottom-details.json` therefore repeats top rows and is retained only as failed-attempt evidence.
- Displayed values are rounded. Ordinary native via annulus 0.125 mm and track width 0.127 mm can appear as 0.12/0.13 mm. Detail retention is capped at 50 per layer/check, so displayed counts are not exhaustive.
- The overlap report summary misformats the result as 0.01 mm; the detail explicitly states dimensionless ratio 0.54. Preserve both and use the detailed ratio for interpretation.
- No geometry, part selection, rotation, coordinates, rules, source files, process parameters, orders or quotes were changed. No factory outreach occurred.

Official result-view guidance: https://jlcpcb.com/help/article/dfm-analysis-result-view-help
