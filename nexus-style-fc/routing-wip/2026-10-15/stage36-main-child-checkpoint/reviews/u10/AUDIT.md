# U10 stage10 read-only footprint, pinout and CPL audit

## Decision
No exact DFM correction is established. Do not rotate or move U10 from this evidence. Native pinout and placement-origin export are consistent. A real, separately actionable deviation from TI's example land pattern exists, but it does not explain a missing lead pad on its own and is not proof that the existing alternate footprint cannot be assembled.

## Source binding
Authoritative board: main-assembly-annotation-10/hardware/nexus-style-fc.kicad_pcb, SHA256 2099ceb9ff904859a68e288683ee68b2ad74d7741b8b670341baf67bf67e1ea3. Confirmed independently by reading bytes and by the active placement worker. No board, library, schematic or export was changed/saved/refilled.

## Native facts
- U10: TPS70933DBVR / C89347, front, origin (109.4,107.05) mm, angle 0 degrees.
- Pads relative to body origin, KiCad positive Y downward: 1 (-.95,+1.15) VSYS; 2 (0,+1.15) GND; 3 (+.95,+1.15) floating EN; 4 (+.95,-1.15) NC; 5 (-.95,-1.15) 3V3_SENS.
- Pads 1–3 .49 x 1.157 mm; 4–5 .49 x 1.175 mm; rectangular, copper/mask/paste. Pin 1 is lower-left in top view. Numbering is physically consistent with the TI top view rotated counterclockwise by 90 degrees. Rotating a drawing to fit the board is valid and does not establish a CPL error.
- Auxiliary origin (99.95,133.15) gives CPL x=109.4−99.95=9.45 and y=133.15−107.05=26.10. Actual exported row is U10,9.4500mm,26.1000mm,Top,0.
- export_fab.py exports native positions using --use-drill-file-origin, changes Side names, and normalizes Rot modulo 360. It does not apply component-specific offsets. Gerbers use the same auxiliary-origin option. U10 is top side; a bottom-side mirror rule cannot explain its result.

## Manufacturer comparison
TI TPS709 datasheet SBVS186H, pin table p3: non-A/non-B TPS709 DBV pins 1 IN, 2 GND, 3 EN, 4 NC, 5 OUT. Native assignment matches. TPS709A and TPS709B are different pinouts and must not be substituted.

DBV0005A package drawing 4214839/K (08/2024), PDF p33: .95 mm lead pitch, .3–.5 mm lead width, 2.6–3.0 mm overall lead span. TI example board layout PDF p34: five .6 x 1.1 mm lands, 2.6 mm opposite row-center distance, .95 mm pitch, .05 mm typical corner radius. The existing land width is .11 mm narrower, rows .15 mm inboard on each side, and lengths .057/.075 mm longer. Its .49 mm width is even .01 mm below maximum lead width, so it has no positive side-fillet allowance at maximum-width centered lead; this is a manufacturing-margin concern, not a proven open circuit. Existing outer pad edges extend to 1.7285/1.7375 mm from body center, beyond the maximum nominal half lead span of 1.5 mm. Five centered correctly oriented leads are therefore not absent merely because these pads are inboard. Full tolerance/reflow qualification was not performed.

TI explicitly notes alternative IPC-7351 land designs may exist. Deviation from its example is not automatically a mandatory-rule violation.

Exact candidate to adopt TI example without changing physical package pose: pads 1(-.95,+1.30), 2(0,+1.30), 3(+.95,+1.30), 4(+.95,-1.30), 5(-.95,-1.30), all .60 x 1.10 mm with .05 mm corner radius. Preserve center, angle, numbered nets and component selection. This requires route-contact, full-width entry, clearance, paste/mask, silk/courtyard and post-refill native checks; geometry changes can sever current pad entries. It is a separate best-practice candidate, not a verified DFM repair.

## Orientation and library uncertainty
JLC's official FAQ says design zero orientation can differ from its zero orientation, and that its nominal zero follows tape/reel packaging. TI's exact TPS70933DBVR tape table lists pin 1 quadrant Q3; the quadrant drawing puts Q3 lower-left with sprocket holes at the top. Native pin 1 is also lower-left. This is consistent at the quadrant level but does not identify the actual JLCDFM C89347 model's detailed pose. It does not justify adding 90/180/270 degrees.

LCSC's primary product page verifies C89347 = TI TPS70933DBVR SOT-23-5. Its public footprint-image page's fetched SVG has an empty geometry group, so no exact selected-library pad or zero-angle data was available there. Do not equate an LCSC footprint graphic or generic SOT-23 example with the JLCDFM model.

The DFM receipt reports one lead without pad, four overlap ratios .54, two pin-edge .21 mm dangers, and .96 mm misalignment warning, but has no per-pin localization/model overlay. These aggregate numbers can fit an orientation/model/registration problem and cannot distinguish it from geometry/tolerance assumptions. In particular, four corner overlaps plus a missing middle lead is suggestive of an orientation issue, not proof of an angle or sign. The parent prompt's 'edge2.21mm' means two .21 mm findings, not a 2.21 mm gap.

Next decisive evidence: obtain the actual top-view U10 model/lead overlay with pin identity and centroid for C89347 in the existing DFM project, or an explicit factory/library placement convention. Compare all five lead centers to the native coordinates before any CPL override. No duplicate upload/project or browser action was performed by this audit.

## Primary sources
- https://www.ti.com/lit/ds/symlink/tps709.pdf (local PDF and rendered DBV land/outline/tape pages retained alongside this audit)
- https://www.lcsc.com/product-detail/C89347.html
- https://www.lcsc.com/product-image/C89347.html
- https://jlcpcb.com/help/article/pcb-assembly-faqs-part-2

## Isolated TI candidate and local native result (subsequent authorized trial)
Created `u10-ti-candidate.kicad_pcb` (SHA256 d0f2736fd1013a48b45ad125fde71058bebeb2ffcd636c6cfbbe96ded6c47158), `u10-ti.patch`, `pad-deltas.json`, and source-hash-guarded `make_candidate.py`. Only five U10 pad blocks differ from authoritative stage10; no saved zone polygon or route was edited. Candidate is unfinished and must not be adopted unchanged. KiCad 10.0.7 loaded it successfully; no save/refill/full DRC was run.

Native effective-shape comparisons (`native-contact-clearance.json`) found three newly sub-.127 mm local copper pairs:
- Pad1 versus 3V3_SENS track 9b50f9bd-dbb9-517f-903d-660848453e78: .221911 -> .121534 mm.
- Pad3 versus VCAP via 7dace066-4359-4c56-b914-53acaa4c96fd: .144957 -> .089957 mm.
- Pad3 versus SPI2_SCK via f740a49a-edce-4197-bea4-3de31d8f3eab: .137384 -> .100097 mm.

Connected pads 1/2/5 retain their .25/.127/.25 mm straight contact segments. Those segment endpoints are inside the new lands with enough transverse and endpoint depth for full-width entry. Pad1 and pad5 no longer directly touch an additional upstream diagonal segment, but that segment still joins the retained straight segment at the unchanged endpoint. No endpoint extension is needed to preserve these three path contacts. EN and NC remain without same-net routed contacts. This is local contact evidence, not complete connectivity certification.

The main worker reported stage11 has removed old VCAP copper and another worker is rerouting sensor feed. Against exact stage11 source (SHA recorded in `stage11-via-candidate.json`), I explored a SPI2_SCK via move with its two incident track endpoints held together. Incident tracks: cfae5b44-d100-40dc-be1b-8a3ca79f182d on B.Cu, and 00823769-0023-4607-a4b2-e22f63f890ce on In2.Cu. Original via center (110.957383,107.736094) mm.

No acceptable move was found within .15 mm radius on a 5 µm Cartesian grid. Checks used native effective copper shapes on all six layers, .127 mm copper spacing, .2 mm via-hole-to-foreign-copper spacing in both directions, fixed pad/track/via obstacles, unchanged net identities, and a bounded obstacle window extending beyond the entire moving-segment envelope. This is a discrete bounded search, not proof no continuous or wider solution exists. Rightward moves encounter SPI2_MOSI via 7ca855e7-08d6-44f8-a746-d65d7ec6e46a at (111.488508,108.00173); upward moves encounter IMU_CS In2 track 83bbca34-c30a-4072-b1fa-0c4271579a52. Therefore no via patch is supplied or claimed accepted. Existing filled-zone polygons are stale for the new geometry, and were not used as proof; coordinated refill and full DRC remain mandatory after any selected repair.
