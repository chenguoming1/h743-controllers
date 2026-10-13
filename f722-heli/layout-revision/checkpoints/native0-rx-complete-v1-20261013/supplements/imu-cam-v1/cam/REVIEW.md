# Exact clean0 internal CAM review

**INTERNAL WIP CAM REVIEW; final release is false.** PCB SHA `84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd`. Source CAD/parts and every original generated artifact remain unchanged. No factory submission/order occurred; this review makes no power or production qualification claim.

No actionable aperture, population, placement or drill-geometry defect was demonstrated in the bounded checks. A real exporter verification bug was found and a separate narrow patch is prepared; the original failed result is preserved.

## Generation and actual-output findings

The first official KiCad 10.0.6 run generated all 13 Gerbers/job, PTH/NPTH drills/maps/report and nine CSV sets, then stopped at its original rounded-bin drill predicate. Its exact output remains `actual-cam/`; `INCOMPLETE-INTERNAL-REVIEW.json` records the failure and unchanged source. Preview-only continuation in `previews/` subsequently generated the four requested SVGs and a PDF verified as nine pages, without regenerating or overwriting the first outputs.

- All 151 raw native poses/values/packages/sides and procurement manufacturer/MPN/LCSC/package joins match. All 144 SMT BOM/CPL references match; 65 top/79 bottom, 86 procurement groups, 79 SMT BOM groups, seven manual headers and five bare exclusions are retained. Current bottom CPL: U15 (27.7,−21.9),90°; R34 (29.65,−19.97),90°; R35 (29.2,−23.9),180°. No supplier rotation correction was applied.
- Actual Gerber outline is exactly four closed segments, 41.660×25.400 mm, absolute origin, millimetres. Plots declare Gerber 4.6 coordinates; mask files declare negative file polarity and their dark drawn shapes are openings.
- Drill census uniquely matches: 329 PTH = 304 vias + 21 manual-header rounds + four J1 plated slots; two NPTH = one round + one oval. All tools/diameters and slot endpoints match at the actual 0.001 mm output precision. J1 slots remain 1.10×0.60 mm; NPTH oval remains 1.01×0.71 mm. This is correct plotting, not factory slot acceptance.
- Actual selected copper, mask and paste shapes were compared with source-bound native contours for J1/U15/R34/R35: 108 pad-aperture comparisons plus two custom paste regions. All except the two custom U15 GND mask contours match within a numerical 0.00003 mm contour comparison bound. The two GND paste polygons match exactly. All 39 checked plotted pin-1/A/K shapes match source orientation; this is not a supplier-library orientation approval.
- Actual plotted RX-via disk-to-back-mask/paste gap is 0.147428 mm, drill gap 0.272428 mm; GREEN back-mask gap is 0.376558 mm and paste gap 0.541558 mm. Both vias have actual native tenting/no-mask-opening records; neither intersects the selected actual mask/paste apertures. Underbody seating/topography remains a process matter.

## U15 common GND mask, separate paste

Both plotted GND mask openings fully contain actual copper and custom paste, with zero area outside and a minimum 0.046194 mm copper-to-mask boundary expansion. Pad 3 and pad 8 are both GND; their mask openings overlap by 0.057071 mm², forming a common GND opening. Their two actual paste regions remain separate with a 0.200 mm gap. This is not a missed paste bridge.

The closest distinct mask opening retains a 0.100 mm web. The nearest foreign B.Cu track is 0.1865 mm away; its actual plotted centerline and width were matched to the source. The custom plotted mask contours are inward of the high-resolution auxiliary contours, differing by at most 0.003815 mm and approximately 0.000764 mm² per opening. The raw exact-equality failure is retained. The paired project's stored maximum curve error is 0.005 mm, whereas the auxiliary native export uses 0.00001 mm; the difference is consistent with those different approximation budgets. No undocumented plotter-cause or exact-equality assertion is needed to establish the actual containment and spacing above.

Source settings are explicit: global pad-mask margin 0, U15 local margin +0.05 mm, solder-mask-to-copper rule 0, mask-bridge severity error. Thus a source DRC pass alone does not certify factory mask spacing. The current [JLC capability table](https://jlcpcb.com/capabilities/pcb-capabilities), read October 13, lists 0.10 mm bridge capability for 1 oz green/red/yellow/blue/purple and 0.09 mm opening-to-neighboring-trace spacing. These measured nominal dimensions meet those figures, with no extra web allowance claimed. Black/white's listed 0.13 mm and 2 oz's 0.20 mm are not covered by this 0.10 mm web. Actual color/process acceptance remains pending.

## Drill predicate defect and proposed fix

Five 0.20 mm via coordinates lie exactly on a half-micrometre boundary. KiCad's three-decimal Excellon chooses the opposite bin to Python's `round(value,3)` for these values. The actual coordinates are all within 0.0005 mm per axis of native, and all 331 drilled features have unique full-census matches. Maximum center-vector difference is 0.000668351 mm; all diameters match exactly. No geometry or process limit was relaxed.

`DRILL-CSV-DIAGNOSTIC.json` preserves every expected/actual feature and the five differing records. `PRECISION-MATCH-CONTROLS.json` verifies the actual ties and rejects missing, duplicate, wrong-tool, over-half-grid and wrong-slot-endpoint controls. The original rounded-bin failure remains true as a historical execution result.

A separate proposed repository-tool patch is at `proposed-exporter/native_export.py.patch`; see its `PATCH-PROVENANCE.json`, `PATCH-CONTROLS.json` and README. No final export or final receipt gate has been run with that patch.

## Visual and scope notes

`actual-Gerber-critical-apertures.png` is drawn directly from the generated Gerber aperture primitives, with copper gray, mask openings blue, paste orange and drills black. Panels show USB front, U15/R34/R35 back, and RX/GREEN back/front. **U3 is fitted on the back: its label in the front panel is an opposite-side location reference, not a front-placement assertion.** Coordinates use a common PCB top view. The raster omits track strokes and full silkscreen to keep aperture/drill relationships legible; numeric trace and polarity checks are recorded separately. It is a targeted review image, not a whole-board CAM render.

The bounded parser accepts only the actual observed KiCad circle/rectangle/oblong/RoundRect/FreePoly flashes and linear region syntax, rejecting unsupported primitives. It is not a general Gerber certification framework. Existing raw contour differences and all diagnostic scripts remain visible. Factory stack/tenting, J1 slot acceptance, stencil/reflow/underbody seating and full final review receipts are still separate gates.

## Arithmetic distinction and reproducibility

The independent decimal diagnostic matched every feature at exactly ±0.0005 mm with **zero added epsilon**. The proposed reusable tool uses half that grid plus 16 binary64 ULPs for native arithmetic. These are distinct implementations. Its actual-board maximum extra allowance is 1.1368683772161603e-13 mm. The adjacent-float boundary evidence in `evidence/EXPLICIT-BOUNDARY-PROOF.json` accepts delta 0.00050000000011 mm and rejects 0.000500000000116 mm, above the maximum total 0.00050000000011368683772161603 mm. This numerical bound does not waive any physical clearance or process limit.
