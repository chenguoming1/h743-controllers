# Current-input JLCDFM recheck — 17 October 2026

**Completed on the current fabrication-cleanup Gerbers, 51-group BOM and corrected 83-placement CPL. No regeneration was needed or performed. The design remains on fabrication/assembly hold.**

## Exact inputs and completion

Source revision: `09c2d35cf2b5621cb815dc28b21e38f85f49da8d`. [input-binding.json](input-binding.json) records the SHA-256 of the native PCB and all three upload files, plus every Gerber ZIP member. The files matched the current export-verification receipt before upload and remained unchanged after analysis. The ZIP integrity check passed, and BOM/CPL references cover exactly the same 83 parts.

A new JLCDFM project in the user's personal Chrome profile received the current ZIP, BOM and CPL. The actual website confirmed **51 detected / 51 confirmed BOM groups**. Component models rendered, Save & Close completed, and both PCB and SMT analysis finished. U10's imported 270° pose and U1's corrected bottom pose were inspected against their native pin-1 locations. No placement, part identity or DFM rule was changed on the site.

This closes the previous gap in website screening of the newer CAM/51-group BOM. The unchanged child was not uploaded again. Factory process acceptance and physical qualification are separate outstanding items.

## PCB result

All 29 returned categories are retained in [pcb-summary-normalized.json](pcb-summary-normalized.json). The nonzero danger categories are:

| Check | Displayed danger count | Detail |
| --- | ---: | --- |
| Pad spacing | 6 | One top at 0.05 mm; five bottom at displayed 0.08, 0.08, 0.08, 0.09 and 0.10 mm |
| Via to pad | 3 | Two top and one bottom; displayed zero spacing to pad apertures |
| Slot width | 4 | Plated slots display 0.60 mm against the site's generic 0.61 mm danger boundary |
| Silkscreen to pad | 100 | First 50 findings per side; capped result |
| Silkscreen to hole | 100 | First 50 findings per side; capped result |

The focused tables are in [pcb-focused-details.json](pcb-focused-details.json). Pad-spacing details show only the first 50 of 201 bottom / 136 top results. Aperture labels do not establish reference designators or net identities. These counts must not be described as confirmed electrical shorts. Silkscreen counts are capped and are not an exhaustive defect total. PCB detail panels include generic example illustrations; actual board rendering and returned tables are the evidence.

The returned routing tables expose top/bottom copper. Equivalent inner-layer DFM coverage is not established despite the six-layer upload. Native KiCad checks and JLC's generic rules remain distinct; no rule relaxation or geometry change was made to reconcile their findings.

## Assembly result

All 18 categories are in [assembly-summary-normalized.json](assembly-summary-normalized.json); every nonzero problem category was read on both sides and saved in [assembly-focused-details.json](assembly-focused-details.json).

| Check | Danger | Warning |
| --- | ---: | ---: |
| Component to board edge | 4 | 7 |
| Lead to hole | 10 | 0 |
| Pin left edge | 8 | 0 |
| Pin right edge | 2 | 0 |
| Through-hole misalignment category | 0 | 6 |
| **Total returned flags** | **24** | **13** |

Missing-pad, pin-outer-edge, lead-overlap and collision findings remain zero. U10 is absent from the remaining problem rows. Every assembly category count matches the earlier corrected-CPL check; the current 51-group BOM is now independently checked.

Remaining edge dangers identify J2 (0.33 mm), R11/R12 (0.45 mm) and U4 (0.50 mm). Lead-to-hole dangers identify C19, U3, U11, J5, J4, U2 twice, J3, U5 and R14; nine display zero and J3 displays 0.05 mm. Left/right pin-edge findings identify LEDs D1–D3 and fuses F1/F2. The six misalignment-category warnings for F2, SW1, F1, U1 twice and D4 return `null` measurements. No justified CPL offset is established for these remaining flags.

## Disposition

The current-input DFM rerun is complete, and the CPL rotation corrections hold. The result is **not a clean DFM pass or fabrication release**. Remaining flags need physical correlation, correction or an explicit manufacturing disposition. The fabrication report's pasted-via/stencil process, slot tolerances, stackup, electrical protection/VCAP and main/child fit questions remain open. No order, supplier acceptance or physical qualification occurred.

Only three core screenshots are retained: [PCB result](pcb-result.jpg), [pad-spacing detail](pcb-pad-spacing.jpg) and [assembly result](assembly-result.jpg). The returned DOM/table records and input hashes provide the detailed audit trail.
