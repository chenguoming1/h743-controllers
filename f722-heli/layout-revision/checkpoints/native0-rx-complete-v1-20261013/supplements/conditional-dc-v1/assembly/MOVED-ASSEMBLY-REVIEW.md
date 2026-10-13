This is an explicitly normalized copy of the issue-time local assembly report. Its closing DC-pending statement is historical; the current conditional DC result is recorded in the sibling supplement README.

# Clean native0: moved parts and relocated via assembly review

2026-10-13. Exact PCB `84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd`; native compressed SHA `83a6c87643977d21a1c3841bc26d4f28694ff721436e36ba20824b7b191174d1`; pad-settings SHA `ba62b0e6147c74b26bb81f872215a31fa1c41d850ee75ba5514663adba0cf673`.

## Disposition

No nominal assembly defect or necessary CAD move is demonstrated for the three moved parts or the relocated RX/GREEN vias. Current physical pad/mask/paste/drill and body/courtyard evidence closes the earlier generic “moved-part local review pending” item. Preserve the exact parts and existing ordinary 0.45/0.20 mm both-sides-tented process. This is a bounded local design review suitable for a conditional prototype; it does not assert factory acceptance, manufactured tolerances, underside clearance, reflow seating or flight qualification.

The necessary data action is to generate a fresh source-bound CPL from the current poses. Required factory acceptance remains specific: exact stack/tenting route, J1 hole/slot capability, panel/double-sided handling, stencil/reflow, actual part-model pin-1/pickup/orientation and inspection of underbody tent topography/seating. Those are not reasons to leave the inspectable local nominal geometry unchecked, nor authority to substitute filled/capped vias.

## Three moved bottom components

The current native copper, mask and custom paste polygons were measured. All effective pad paste margins are zero. U15 has ten paste apertures: eight lead apertures and two native custom GND polygons. R34 and R35 each have two. For all three, paste lies wholly within its own copper land and soldermask opening. No foreign land/paste/mask, drill, same-side body or component courtyard overlap is present.

| Component | Nearest foreign land/paste gap | Nearest drill-to-paste gap | Nearest same-side nominal body gap | Nearest courtyard-region gap |
|---|---:|---:|---:|---:|
| U15 | 0.620 mm to R5.2 | 0.266900 mm | 0.825 mm to C75 | 0.050 mm to R34 |
| R34 | 0.663486 mm to U3.4 | 0.275190 mm | 0.780 mm to U3 | 0.050 mm to U15 |
| R35 | 0.645 mm to U3.1 | 0.480059 mm | 0.975 mm to U3 | 0.240 mm to U3 |

U15 mask-to-nearest-foreign-mask gap is 0.570 mm. R34/R35 minima are 0.663486/0.645 mm. Courtyard figures use the enclosed native courtyard region; they are nominal separation between footprint courtyard boundaries, not a 50 µm placement-tolerance promise. The saved unsuppressed all-zero native DRC is consistent with this independent local check.

U15's local Fab body at its new B90 pose is x=26.45..28.95, y=21.40..22.40 mm (2.5×1.0 mm). The previously reviewed TI DQA0010B manufacturer maximum of 2.6×1.1 mm gives x=26.40..29.00, y=21.35..22.45 mm. It remains wholly inside the current courtyard x=26.15..29.25, y=20.95..22.85 mm and has 0.775 mm separation from the nearest other nominal Fab body (C75). That comparison uses the TI maximum for U15; other parts' Fab representations are not newly certified manufacturer maxima.

R34 and R35 retain the exact same C25092 / 0402WGF220JTCE identity and R_0402_1005Metric library. Their local Fab rectangles are 1.05×0.54 mm, with cardinal rotation applied. These are verified library outlines, not a newly verified UNI-ROYAL maximum-body tolerance. The unchanged library, package identity, positive nominal body/land gaps and clean current DRC demonstrate no new geometry defect; no additional speculative package-certification program is introduced.

Pin-map/CPL sanity remains source-specific: U15.1 is (28.7,22.3175), U15.10 is (28.7,21.4825), and both have the intended PORT_C_RX_EXT net. Current raw bottom CPL expectations are U15 (27.7,−21.9),90°; R34 (29.65,−19.97),90°; R35 (29.2,−23.9),180°. Do not reuse the former U15/R35 rows or mirror bottom X again. The official exporter numerically compares the native CLI angle with GetOrientationDegrees; supplier-model corrections are not guessed.

## Relocated RX and GREEN vias

Both actual native via records are through-vias with 0.45 mm copper diameter / 0.20 mm drill, F.Mask and B.Mask tented, and empty native mask-opening maps. Measurements use the exported via disk and drill contours against all front/back component land, mask and paste shapes.

RX via `ec1b3878-61fc-5aff-9602-9d5133c60039` is at (31.253518,21.976537).

- Its disk/drill are under J11's front nominal body projection and U3's back nominal body projection.
- Front disk-to-nearest land/mask/paste gap: 0.823510 mm to J11.3; drill gap: 0.948515 mm.
- Back disk-to-nearest land/mask/paste gap: 0.147415 mm to U3.3; drill gap: 0.272412 mm. U3.2 is next at 0.193409 mm disk separation.
- Thus no via-in-land, open-mask overlap or paste/drill overlap is demonstrated. The back-side value is the tighter local process dimension and belongs in the assembler's mask/tent review.

GREEN via `c45deb1f-b195-55f5-9d25-74073f667227` is at (37.001558,23.342039).

- It lies under U3's back nominal body, with no front component body/courtyard crossing.
- Front disk-to-nearest land/mask/paste gap: 0.795730 mm to R10.1; drill gap: 0.920732 mm.
- Back disk-to-U3 exposed-pad land/mask gap: 0.376558 mm; drill gap: 0.501558 mm.
- Back disk-to-paste gap is at least 0.541558 mm; drill-to-paste is at least 0.666558 mm, even using conservative rectangles for U3's paste-only windows.
- No aperture collision is demonstrated. The former redundant GREEN hole at (32.15746,21.80934) was removed in this exact clean source; it is not an additional surviving assembly hole.

A component-body projection does not identify all underside metal or guarantee a seating gap. J11's previously reviewed official GH catalog describes a heat-resistant PA housing with metal contacts/reinforcement tabs; the current modeled apertures are clear, but its precise underside at the RX location is not guaranteed by that catalog. U3's actual exposed pad and paste are specifically included in the measurement. Ordinary tenting is soldermask coverage, not a filled/capped/flat surface. Neither automatic rejection nor unconditional seating approval follows from the underbody projection alone. If the assembler demonstrates interference, review a specific remedy; no geometry or process change is justified by the current nominal collision evidence.

## Method, evidence and remaining factory limits

The original local review completed in 5.4 seconds with a 768 MiB address-space cap and 60-second CPU cap. It ran no KiCad/native diagnostic, refill or export. `MOVED-ASSEMBLY-GEOMETRY.json` contains measured owners, distances, poses and hashes.

Regions come from actual source-bound native land/mask polygons, native custom paste graphics, zero-margin pad-paste contours, enclosed courtyard/Fab graphics, and actual drill/via contours. Paste-only pads use conservative rectangular bounds. Small digits identify native geometry; they are not manufacturing capability claims. This review covers these three moved components and two relocated vias, not exhaustive whole-board CAM.

Manufacturer/library interpretation is reused from the already completed `assembly-trimmed-native4-review-20261012/REVIEW.md` and `assembly-native3-review-20261012/REVIEW.md`: [TI TPD4E05U06 datasheet, DQA0010B drawing and stencil examples](https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf), pages 31–33; [JST GH catalog](https://www.jst-mfg.com/product/pdf/jpn/GH.pdf), pages 2–3. The TI split-paste example is based on a 0.1 mm stencil; no unchanged-layout inference certifies the assembler's stencil or reflow profile.

Keep the genuine outstanding process gates unchanged: six-layer production stack/nominal finished thickness, ordinary tenting versus the current filled/capped quote option, exact J1 1.01×0.71 mm NPTH oval and 1.10×0.60 mm plated shell slots, removable panel/rails, double-sided/0201 handling, J1 secondary shell soldering and eventual first-board seating/joint inspection. Contact/upload/order permission is still pending. Current source-bound DC review is separate and remains ongoing.
