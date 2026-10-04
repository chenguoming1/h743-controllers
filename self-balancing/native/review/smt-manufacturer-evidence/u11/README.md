# U11 P3 SMT overlap disposition

**Result: the reported 0.16 is not reproduced by correctly centered Winbond ZE terminals against the actual copper. It is reproduced, to the displayed precision, by comparing one of the four exposed-pad paste windows with the full package exposed pad. This is a specific recognition hypothesis, not proof of the supplier's internal object mapping. Do not change U11 copper or supplier rotation from this flag alone.**

The eight native signal lands provide 100% nominal lead-area overlap. The lowest value in the centered manufacturer-dimension grid is 93.6118%, still above the captured supplier 90% warning boundary. Nominal EP copper coverage is 100%; even maximum EP dimensions leave more than 97.4% coverage. The generic footprint does, however, differ substantially from Winbond's suggested PCB land pattern. Physical terminal coverage and reproduction of that suggested pattern are separate findings; this audit does not qualify solder-joint reliability or clear assembly.

## Evidence and scope

- Audited source: `controller-r3s-green/controller.kicad_pcb`, SHA256 `0850991d8aacd22138487804c24eefbae634a21ba218c18196f13fad795c3696`. Rechecked unchanged after the audit. No native board, supplier pose, BOM or CPL edits.
- Part: U11, Winbond W25N01GVZEIG, C88868, verified in the release BOM. Generic footprint: `Package_SON:WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm`.
- Native bottom-side placement: `(20.550,20.375) mm`, 180°. Gerber/CPL origin is `(20.550,17.625) mm`, because manufacturing y is `38 - native_y`. The user-corrected release CPL is Bottom/0° at that same manufacturing origin; the native audit CPL is Bottom/180°. These are separate representations, not a demonstrated supplier rotation error.
- [Captured P3 detail](p3-bottom-overlap-u11.txt) identifies U11, `i274x.RoundRect.d13`, value 0.16. Its help defines overlap as lead/pad intersection divided by lead area, with 0.75 and 0.90 thresholds. It does not identify the pin number, polygon, source layer or registration transform. The viewer remained at component loading.
- [Geometry audit](geometry-audit.json), [dimension cases](dimension-cases.csv), [reproducible audit script](audit_u11.py), [SVG overlay](u11-overlap-overlay.svg), [PNG overlay](u11-overlap-overlay.png). These are analyses of actual source geometry, not screenshots of the unavailable supplier model.

## Manufacturer sources

1. [Winbond W25N01GV, Rev L, April 17, 2024, manufacturer PDF hosted by Mouser](https://www.mouser.com/catalog/specsheets/Winbond%20Electronics%20Corporation_08-25-2025_W25N01GV.pdf), printed pp 7 and 64; [local copy](sources/Winbond-W25N01GV-RevL.pdf), [package drawing](sources/winbond-ZE-page64.png). The live PDF was checked on 2026-10-03 and matches the locally audited revision. The [official Winbond download entry](https://www.winbond.com/hq/support/documentation/downloadV2022.jsp?__locale=en&xmlPath=/support/resources/.content/item/DA00-W25N01GV_2.html&level=1) redirected to a 403 response; no claim of a newer unavailable revision is made.
2. [Winbond AN0000009, Serial Flash PCB Layout Guidelines, Rev2, September 25, 2017, pp 20–21](https://robu-prod-media.s3.ap-south-1.amazonaws.com/uploads/2025/02/Winbond-W25Q64JVSSIQ-technical_drawing.pdf), [local manufacturer-authored copy](sources/Winbond-AN0000009-Rev2.pdf), [package page](sources/winbond-land-20.png), [suggested lands page](sources/winbond-land-21.png). This general SpiFlash application note is introduced for NOR packages; its WSON8 8×6 package drawing has the same dimensions as the NAND ZE drawing. It is useful package guidance, not a NAND-specific mandatory assembly specification. The [official Winbond AN entry](https://www.winbond.com/hq/support/documentation/downloadV2022.jsp?__locale=en&xmlPath=/support/resources/.content/item/DA01-AN0000009.html&level=1) confirms the document identity; current revision beyond the retrieved Rev2 is not established.

The ZE drawing specifies body D=7.90/8.00/8.10 and E=5.90/6.00/6.10 mm; terminal L=0.45/0.50/0.55, b=0.35/0.40/0.48, pitch 1.27; exposed metal D2=3.35/3.40/3.45 and E2=4.25/4.30/4.35. EP has a C0.4 pin-1 chamfer, no internal signal connection, and may be grounded. The drawing advises against exposed PCB vias beneath it.

## Actual copper, mask and paste

| Feature | Native / verified Gerber geometry |
|---|---|
| Signal pads 1–8 | 0.65×0.50 mm roundrect, R0.125, rows at x=±3.75 from origin, y=±1.905/±0.635 |
| Signal copper flashes | B.Cu D16, all eight coordinates and aperture parameters verified |
| Signal paste | Same 0.65×0.50/R0.125; B.Paste D14, eight matching flashes |
| EP copper 9 | Solid rectangular 3.40×4.30, GND; B.Cu D17 |
| EP paste | Four 1.37×1.73/R0.25 windows, centers x=±0.85/y=±1.075; B.Paste D13 |
| EP paste webs | 0.33 mm across x; 0.42 mm across y |
| Bottom mask | Polygon regions, same opening bounds as each copper pad; zero expansion; all nine openings independently located |
| Holes under EP | None even within max 3.45×4.35 package envelope; nearest via hole is 0.205 mm outside it |

Native B.Cu D13 is an unrelated 0.80×0.95/R0.20 macro. D numbers are file-local. The supplier may create its own names. Accordingly, neither the matching name of B.Paste D13 nor the different number of B.Cu D16 establishes what the supplier actually selected.

## Lead overlap calculation

The comparison places the package center and signal rows exactly on the native footprint, using Winbond's dimensions and the true rounded copper geometry. For a right-side terminal, its radial range is `[D/2-L,D/2]`, and transverse width is b. Its intersection with the 0.65×0.50/R0.125 land at x=3.75 is integrated analytically in transverse slices.

| Constructed centered case | Intersection/terminal area |
|---|---:|
| Nominal rectangular 0.50×0.40; D=8.00 | 100.0000% |
| Max rectangular 0.55×0.48; D=7.90 | 93.6118% |
| Max rectangular 0.55×0.48; D=8.00 | 99.3674% |
| Max rectangular 0.55×0.48; D=8.10 | 99.3674% |
| Nominal inward-rounded terminal | 100.0000% |
| Max inward-rounded terminal; D=7.90 | 98.4980% |

The inward-round case assumes a semicircular tip of radius b/2, consistent with the illustration but not a separately dimensioned radius. The rectangular envelope is a conservative comparison. All 54 min/nom/max combinations for D,L,b and the two shapes are saved. Package y is coplanarity, not an in-plane positional tolerance; it was not misapplied as x/y error. Fabrication, placement and unquantified terminal positional errors are outside this calculation.

Nominal signal margins are toe +0.075, heel +0.075 and sides +0.050 mm. Dimension-only envelope ranges are toe +0.025…+0.125, heel −0.025…+0.175 and each side +0.010…+0.075 mm. The small maximum-lead/minimum-body heel overhang explains the 93.61% conservative minimum, not a 16% overlap.

## Why one paste window produces 0.16

Each rounded window area is:

`1.37×1.73 − (4−π)×0.25² = 2.31644954 mm²`

Nominal package exposed-metal area, with the dimensioned chamfer, is:

`3.40×4.30 − 0.40×0.40/2 = 14.54 mm²`

Therefore one window / nominal EP is `0.15931565`, displayed as 0.16. Omitting the chamfer gives `2.31644954/14.62 = 0.15844388`, also displayed as 0.16. The four-window total is 9.26579816 mm², 63.3776% of EP copper or 63.7263% of the chamfered nominal package EP. Each window fits inside the nominal exposed metal, including at the chamfer.

By contrast, solid nominal EP copper covers 100% of nominal exposed metal. At maximum rectangular EP dimensions coverage is 97.41796%; with the 0.4 chamfer it is 97.52973%. Thus the reported 0.16 can be reproduced at a valid pose by a **single-paste-window denominator comparison**, but not by the intended full copper land. Model/layer/land recognition needs inspection before assigning cause. No supplier model dimensions, internal merging rule or transform are inferred.

## Suggested land-pattern comparison

AN0000009's drawing, rotated to native axes, uses 1.50×0.80 signal copper with 6.80 inner gap (row centers±4.15), 1.40×0.70 stencil openings with 7.00 inner gap, and 3.25×4.05 EP copper. The EP stencil has five 0.65-diameter openings; stated stencil thickness is 0.10 mm. Native signal copper is smaller and 0.40 mm inward; native EP copper and stencil strategy also differ. The current footprint is therefore **not a reproduction of this Winbond suggestion**. Suggested signal lands contain the centered terminal dimensional envelopes; native lands give the overlap figures above. The suggestion is shown as a comparison, not applied to the board.

## Pin 1 and disposition

Native pin 1 /CS is `(24.300,18.470)`, equivalent Gerber `(24.300,19.530)`. Pin 8 VCC is `(16.800,18.470)` native. Looking through the board in native top coordinates, pin 1 is upper-right; viewed from the bottom component face, it is upper-left. All pins 1–8 map correctly to the Winbond functions in the extracted audit; EP 9 is GND.

A 180° rotation preserves this symmetric eight-land arrangement while swapping electrical pin assignments. Consequently, a good overlap score cannot independently validate pin 1, and a 0.16 score cannot justify changing the user-corrected CPL 0°. Keep both native placement and corrected supplier pose unchanged pending actual supplier pin 1/model evidence.

**Disposition:** retain U11 unchanged for this read-only closure review. Ask the assembler to identify the source layer and terminal for `i274x.RoundRect.d13`, confirm whether it is one EP paste window, and compare the complete copper and stencil geometry with the exact ZE package at the approved pin 1 orientation. Obtain its explicit acceptance of the generic land/stencil pattern if retaining it. The numeric evidence strongly supports a recognition/EP-window explanation; the supplier canvas/polygon gap prevents declaring that explanation proven or marking SMT assembly cleared.
