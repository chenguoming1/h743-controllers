# Current trimmed native4: bounded assembly review

Source: `recovery-negotiated-routing-20261011/native4-sck-lead-trim-native-preparation-v1/outputs/native4-SCK-trim-v1/diagnostic-board/f722-heli.kicad_pcb`, SHA-256 `1b463dbb2115f5fa0d0ffada1f80fe674b1418a4ddbd661c83cb7516f334374a`. `geometry.json` and reproducible `review.py` bind measurements to that exact source and its native export. Peak RSS 342 MiB; 512 MiB address-space cap. No board edits, exports, uploads, orders, or process changes.

## Disposition

No new land/paste collision or necessary layout correction was demonstrated in the inspected RED-via/U15 scope. Keep the six-layer ordinary 0.45/0.20 mm both-sides-tented process. Nominal body projection overlap alone is not a demonstrated conductive collision and does not establish a universal body keepout. This is not an assembly-tolerance guarantee, a waiver, or a full-board qualification. The four open nets remain a release blocker; current native DRC also retains its three historical dangling-via warnings.

The necessary manufacturing-data correction is a fresh source-bound CPL and placement review after routing is complete. Current totals independently recount to 144 SMT, 65 front / 79 back: totals happen to match the old handoff because side changes cancel, but the old component poses remain stale. Preserve R31 AC0201FR-0722RL/C144830, J2–J8 manual THT, and TP1–TP5 bare-pad exclusions.

## RED via at (34.030343,24.590967)

UUID `2754fcb2-b9e9-5c3b-8023-61718c16e5e6`; 0.45 mm copper diameter, 0.20 mm drill, F.Mask and B.Mask tented. J11 is on F.Cu. Its nominal F.Fab body rectangle is x=27.375..35.625, y=20.3..24.55 mm, consistent with the catalog's 8.25 by 4.25 mm body dimensions. Center is 0.040967 mm outside that projection; nominal drill crosses it by 0.059033 mm. Current exported outer-contour disk overlap is 0.061191 mm² and drill overlap 0.007751 mm². The earlier 0.061187 mm² value is consistent at the native polygon approximation scale; this is not a new body change.

Measured via outer-copper-edge separation:

- Front J11 mounting-tab land, mask opening and paste: 0.469658 mm. No overlap.
- Back U3 exposed-pad 9 land and mask opening: 0.215967 mm. No overlap.
- Back U3 nearest paste: at least 0.425967 mm. No overlap even using a conservative bounding rectangle for paste-only pads.
- Drill-to-nearest mask opening: front 0.594658 mm; back 0.340967 mm.

J11's official GH catalog identifies heat-resistant PA header housing, copper-alloy/tin-plated contacts and reinforcement tabs. The body projection here is consequently not a blanket metal region. The open catalog does not establish guaranteed underside standoff at this exact point or permissible soldermask topography. The exact 2D drawing is gated behind an explicit license and a form requesting company, name, address, phone and email; no form was submitted or agreement accepted. No underside metal/flatness assurance is inferred from a footprint outline. U3's opposite-side molded-body projection already covers this via; separation from its exposed pad and paste is the meaningful measured fact.

JLC's current official via-covering guidance says tented vias are soldermask-covered, ideally use holes <=0.4 mm, and warns that incomplete plugging can leave tin beads. Tenting is not a guarantee of a filled, capped or flat hole. Its process table also warns about insufficient spacing to mask openings. These statements support checking actual pad/mask geometry; they do not prescribe a universal component-body keepout. We did not substitute epoxy filling, despite its separate availability.

If an assembler's actual seating/underside review rejects this location, the smallest nominal pure-Y move clearing J11's drill projection is +0.059033 mm to tangency, or +0.184033 mm to clear the whole 0.45 mm disk to tangency. Positive tolerance margin would be additional. These are geometric lower bounds, not validated routes or recommended immediate edits: any move must reconstruct both copper joins and rerun native DRC/connectivity/plane/reference checks. Merely returning to the old y=24.740967 still leaves nominal copper-disk body overlap.

## U15 on the back side

Exact native pose is (27.721926,21.185113), B.Cu, 0°. Pad 1 is at (27.304426,22.185113), pad 10 at (28.139426,22.185113). Pin-1 chamfer/silkscreen is at the corresponding lower-left corner in board coordinates. All 10 native paste apertures are on B.Paste: eight ordinary lead apertures plus two custom GND paste polygons. Their union is wholly inside U15's copper lands; no foreign land overlap. Nearest foreign land is R35.2, 0.469136 mm away. Nearest drill is 0.310115 mm from U15 paste, with no drill/paste overlap.

TI's DQA0010B drawing lists body 0.9..1.1 by 2.4..2.6 mm and shows separate stencil apertures across the central ground region, based on a 0.1 mm stencil. Current local geometry is consistent with the intended DQA0010B split-paste construction; this review does not certify stencil manufacture or reflow profile. Placement ±0.10 mm / rotation ±2° elsewhere in the design remain engineering assumptions, not JLC guarantees; the U2 package tolerance note is not a U15/J11 tolerance specification.

The staged native exporter preserves bottom-side X and native angle and outputs Y=-native Y. U15's raw exported placement therefore should be X=27.721926, Y=-21.185113, bottom, 0°. This is a native-coordinate identity, not a JLC library angle correction. Regenerated CPL and bottom assembly view must be checked together against pad 1 and the actual chosen C138714 placement model; do not guess a 180° correction or mirror X again. JLC officially requires both sides in one CPL with explicit T/B or Top/Bottom fields.

## Sources and limits

- [JST official GH catalog](https://www.jst-mfg.com/product/pdf/jpn/GH.pdf), pages 2–3: dimensions, recommended PCB pattern, header materials. Catalog pattern dimensions are references, not an assembly tolerance warranty.
- [JST exact BM04B-GHS-TBT drawing access](https://www.jst-mfg.com/product/index.php?doc=4&filename=BM04B-GHS-TBT.pdf&series=105&type=10): explicit license/data form; not submitted.
- [TI TPD4E05U06 datasheet revision O](https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf), pages 31–33: DQA0010B package, land and stencil examples.
- [JLCPCB via covering](https://jlcpcb.com/help/article/pcb-via-covering), updated September 9, 2026; read October 12, 2026.
- [JLCPCB BOM/CPL preparation](https://jlcpcb.com/help/article/advice-for-bom-and-cpl-files-preparation), updated September 9, 2026; read October 12, 2026.
- Local `assembly-package-source-20261012.json`, `final-export-preparation-20261010/HANDOFF.md`, staged exporter README/native_export.py, prior native4 local-support review and current native pad settings.

Geometry method: actual exported outer copper/drill/mask contours; zero effective paste margins verified for pad apertures, with native copper contours as pad-paste proxies. Paste-only pads use rotated rectangular bounds, deliberately conservative (no false overlap-clearance assurance from omitting U3's paste windows). Custom paste graphics use their actual polygons. Native polygons have finite approximation error; quoted micrometre-scale precision identifies source geometry, not manufacturing capability. No final Gerber/stencil CAM or supplier preview has been generated in this review.
