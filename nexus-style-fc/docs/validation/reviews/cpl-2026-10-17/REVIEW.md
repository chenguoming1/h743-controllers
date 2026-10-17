# CPL rotation correction — 17 October 2026

This website review is bound to the predecessor stage36 PCB/CAM and 48-group BOM recorded below. The newer fabrication-cleanup PCB/CAM and 51-group BOM preserve the component/pad placements, but require their own website screening. The corrected CPL is reproduced against the newer source in [current-export-verification.json](current-export-verification.json).

The main CPL now uses JLC's bottom-side rotation convention and a verified U10 library offset. All 83 placements were accepted with all 48 BOM groups confirmed in a fresh JLCDFM project. Native PCB geometry, coordinates, sides, part selection, BOMs, Gerbers/drills and the child CPL are unchanged. This is an assembly-data correction, not a manufacturing release.

## Verified corrections

- **U10 / C89347:** native angle 0° becomes CPL 270°. JLC's zero model has three leads on the right and pin 1 lower-right. The native footprint has three pads below and pin 1 lower-left. A clockwise trial and a fresh file import both show all five leads on the intended pads with pin 1 lower-left. See [before](u10-before.jpg) and [final imported pose](u10-final-top.jpg).
- **Bottom side:** CPL angle is `(180 - native_angle) % 360`. At native 180°, U1, U4, U9, U14, D4, D5 and Y1 previously appeared reversed in the component-side view. Importing 0° places their pin-1/cathode at the native position. Native 90° remains 90° for U5, U7 and D6, whose poses were also checked. See [original bottom view](bottom-before.jpg), [corrected MCU pin 1](u1-bottom-corrected.jpg), [diode polarity](d5-d6-bottom-corrected.jpg) and [final bottom view](final-bottom-all-components.jpg).
- The complete bottom convention also changes the numeric angle of 17 symmetric two-terminal passive parts by 180°. Their physical alignment is equivalent. In total, **25 rotation fields change: 24 bottom placements and U10**. Every other CSV field is identical.

The top IC pin-1 locations and LED cathodes were inspected against native pad numbering; no further top rotation correction was established. The full [top-side view](final-top-all-components.jpg) is retained; redundant individual connector/switch/fuse and other component crops were removed after inspection. Passive placement alignment was screened by the complete assembly check. This does not establish real component tolerances, firmware axes or physical assembly qualification.

`tools/export_fab.py` applies the bottom conversion at export and guards U10's special offset by its exact part, footprint and top side. A changed U10 identity/side requires review instead of silently reusing the correction. Neither the native PCB nor its footprint orientation is changed to satisfy a supplier's zero angle.

## Final JLCDFM assembly result

Observed in the user's personal Chrome profile with the existing JLC account. A separate final project received the unchanged Gerber ZIP and BOM plus the corrected CPL. All 48 BOM groups were confirmed. Screenshots were taken after the actual board and models rendered; illustrative rule graphics were not used as placement evidence.

| Check | Danger | Warning | Good |
| --- | ---: | ---: | ---: |
| Component collision | 0 | 0 | 3 |
| Component spacing | 0 | 0 | 100 |
| Component to board edge | 4 | 7 | 4 |
| Lead to hole | 10 | 0 | 0 |
| Through-hole misalignment category | 0 | 6 | 0 |
| Pin left edge | 8 | 0 | 0 |
| Pin right edge | 2 | 0 | 0 |

Pin without pad, pin outer edge, lead-area overlap, pin inner edge, clipped components and missing holes all returned zero findings. U10 appears in none of the remaining problem rows. Full returned categories are in [final-assembly-summary.json](final-assembly-summary.json); both sides of every nonzero problem category are in [final-assembly-details.json](final-assembly-details.json).

Remaining findings require separate land-pattern, clearance or library-model review; they do not justify shifting true PCB centroids in the CPL:

- Edge dangers: J2 0.33 mm, R11/R12 0.45 mm, U4 0.50 mm. Warnings: J3, R22, C17, L1, C23, C5 and D4.
- Lead-to-hole dangers: C19, U11, U2 (two), U3, J5, J4, J3, R14 and U5. Nine display 0 mm; J3 displays 0.05 mm.
- Left/right edge findings display 0 mm for D1/D2/D3 and F1/F2. Their models are centered on their native pads; polarity was checked for the LEDs. No numeric placement offset was established for these flags.
- The misalignment category supplies six `null` measurements for F2, SW1, F1, D4 and U1 (two). These are unresolved model/check results, not quantified physical offsets.

The site's counts and generic rules are screening evidence. Existing PCB/process, mechanical, power and flight gates remain open. No PCB DFM rerun or physical qualification is claimed by this CPL-only change. The child remains through-hole assembly and was not uploaded again.

## Local verification and provenance

[local-verification.json](local-verification.json) records exact hashes and all 25 angle deltas. Fresh KiCad position export through the corrected exporter reproduces both current BOM/CPL sets byte-for-byte. Coverage is 83 unique main references and one child reference. All main X/Y/layer/reference fields and every top angle except U10 are preserved. Both PCB files and both Gerber ZIPs remain byte-identical to HEAD. U10 identity/side guards and cardinal-angle conversion checks pass. No DRC rerun is needed to verify unchanged copper; prior native checks remain bound to their documented source/settings.

[native-pin1.json](native-pin1.json) records native pad-1 offsets, including the horizontal mirror used to inspect the bottom from its component side. The main PCB remains `bed37199e8d62b8135a27b9e182f8e8f584f1a9fb722cb6efb5d4c87b2a320b8`. The corrected CPL SHA-256 is `a10c80abb5c3d631555b580210867ee7d5d8c59c95325255dc70e814855deb21`.

The original stage36 seals and consolidation receipts describe the previous CPL bytes and remain historical evidence. This review supersedes their CPL/assembly status only. The `final-*` records are authoritative for the completed correction. Redundant trial screenshots and duplicate intermediate table dumps were removed; core before/after views and final returned findings are retained.

JLCDFM initially returned save throttling/opener errors. Reimporting into that existing project retained stale poses, so it was not accepted as proof of changed angles. The separate final project above showed the numeric corrected inputs independently, and its Save & Close and assembly analysis completed. No rule, board position or component identity was changed to clear a finding.
