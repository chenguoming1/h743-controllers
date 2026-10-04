# P6 Controller Fabrication Handoff

This R3-S6-P6 package is ready for prototype PCB fabrication submission using the fixed six-layer process below. This handoff separates the closed source and export checks from the manufacturer's CAM confirmation, four preassembly production outputs and first-article tests. Use only the final P6 files and their SHA-256 manifest. P6 supersedes earlier fabrication packages; P5 contained confirmed narrow copper joints and must not be fabricated.

Final native PCB SHA-256: cf16a6f5ceae65aad217e29eef23a60dbc8f15af743b363df03aa5a42c9c71dc.

Independent source qualification SHA-256: 90cf0c96961b5711d6827e7f5f33a8d46be328a1152fda17a68a2a9fa724d94f. Final release closure SHA-256: 45548ee43cda5247800758b04a00761f32e6879632329897ddc6c8406285790d.

## Complete routing review

Every one of the 85 live nets was reviewed across its routed layers, alongside all six actual filled-copper layers and 159 detailed regions. The included P6-all-net-coverage.csv gives each net's before/after segment counts, layer coverage, disposition and concrete explanation. The atlas preserves equal-coordinate comparisons and annotated obstacle/reference-plane context. After unzipping, open native/review/routing-visual-review/index.html for offline navigation.

| Review scope | Fixed | Already geometrically clean | Retained with constraints |
|---|---|---|---|
| All 85 live nets | 52 | 12 | 21 |
| All 159 detailed regions | 96 | 9 | 54 |

P6 has 3,178 trace segments versus P5's 5,741, and 2,832.738 mm of total track length versus 2,894.434 mm: 2,563 fewer segments and 61.696 mm less length. The changes replace repeated steps, width pulses, hooks and dead branches with coherent straight and 45-degree runs. AUX_PD14 falls from 151 to 47 segments, MOTOR_OK_BUF from 92 to 36, and 3V3_CORE from 779 to 356. The supply and local-return work preserves real branch feeds rather than deleting copper merely to lower a count.

HOST_TX_RAW deliberately increases from 24 to 26 segments: two old rounded-end overlaps formed approximately 0.050 mm copper throats despite nominal 0.150 mm tracks and a zero-open DRC result. They now have explicit full-width joins. Shallow via and pad attachments were repaired too. The last UART3_TX rear offset is a uniform 0.130 mm three-segment path with both via approaches retained. Visual acceptance is based on the rendered geometry and named constraints, not the segment total alone.

## Electrical and actual copper qualification

Fresh ERC, DRC, schematic parity and open-connection counts are all zero. All 405 logical pin assignments and the physical connectivity of all 85 live nets pass. The final audit checks 5,151 actual track contacts, 835 direct pad/track contacts, 709 routed via-layer profiles and 303 solid ground-reference-plane attachments. It finds no unresolved narrow joins, shallow attachments, meaningless vias or exposed pad-anchored dead trees. Its negative control still rejects the old HOST_TX_RAW throats.

Ordinary signal necks meet 0.130 mm; power paths have separate width-preservation and joined-copper checks. Native lands and plated annuli use their approved dimensions, including U2's 0.250 mm lands fed by 0.300 mm traces. All 27 USB data segments remain exact at 0.1392 mm width / 0.1600 mm gap. All 151 footprints, 79 fitted poses, 67 edge-pad mappings, source parts and corrected placement data are unchanged.

## Six redundant vias removed

Six 0.450/0.200 mm signal or power vias were proven unnecessary after dead-branch pruning or a real same-layer bridge. The final board has 406 vias. All 97 ground vias, all seven 0.350/0.200 mm vias and every surviving via record remain unchanged. No required pad destination was lost.

| Net | Native X Y mm | Via UUID prefix | Retained function |
|---|---|---|---|
| FDCAN1_RX | 26.750, 13.350 | 0339b82d | A real In2 bridge replaces the redundant via and hidden pad-only stub |
| UART3_TX | 29.400, 26.550 | 24ff4382 | Full-width front junction retains the functional signal path |
| IMU_CS | 7.050, 21.800 | 5a501fc3 | The unused pad-anchored branch is removed; chip-select terminals remain connected |
| +5V_STACK | 21.150, 7.750 | 9c197846 | The unused branch is removed; active supply feeds and widths are retained |
| USB_SOURCE_DISABLE | 18.500, 29.900 | b1deabfa | The In2 antenna branch is removed; functional front and rear paths remain |
| IMU_CS | 6.350, 25.000 | cc569dba | Pruning the same dead tree retires its second unnecessary via |

The qualification evidence records the full UUIDs and all six deletions. The three reference-plane definitions are unchanged, but their filled copper is not claimed byte-identical to P5: an independent native refill deleting only these six vias reproduces the final reference-plane copper exactly, including local merged-hole fillets. Supplemental In2 ground-fill changes are separately bounded and do not replace the solid reference planes.

## Reference geometry and necessary bends

The reference audit finds no true new foreign-plane gap under its explicit 2 nm polygon-boundary allowance and individually bounded same-net via antipads. The documented east-edge regulated 3.3 V rail exception remains narrow in scope: 0.375 mm of its 0.450 mm width is plane-backed and the outward 0.075 mm strip lies beyond the plane contour. It is a DC rail exception, not a waiver for signal paths or foreign holes.

Some bends remain for physical reasons. The paired UART2 MCU shoulders pass between fixed GND/BOOT0 and 3V3/NRST copper and the neighboring route; their annotated views show the actual reference-plane apertures. The rear 3V3 fold near U11 is a through-feed plus capacitor branch, bounded by FLASH_MOSI, SWDIO and OUT1 copper; the lower shortcut meets the VDDA via. MOTOR_OK_BUF retains a bypass around USB_PRESENT_n. Each retained ledger row has specific evidence, and no visual-review row remains open.

## Manufacturer comparison and fabrication data

The [final P6 supplier analysis](https://jlcdfm.com/viewer?pcbUploadFileId=629361373570224129) reports trace width 0 / 0 / 100, trace spacing 0 / 0 / 32, hole-to-trace 0 / 0 / 100, and mask-opening-to-trace 0 / 58 / 39 (red / yellow / good). The three prior hole-to-trace yellows are cleared; mask warnings fall from 61 to 58. Other displayed PCB counts are unchanged. The 18 SMT categories remain 24 red / 6 yellow / 104 good. Final release closure binds these results to the exact submitted archive, BOM and CPL.

Whole-board native mask clearance is at least 0.100 mm, above the published 0.090 mm process minimum. Three new rounded tuples are consistent with EXT_SPI_CS beside J114/J115 at 0.100 mm and OUT5 beside J140 at 0.125 mm. The supplier exposes no unique location IDs, so this remains bounded tuple correlation. Full-board clearance is independently verified; the capped outer-layer lists are supported by the uncapped six-layer audit.

Manufacturer-pattern evidence supports U2/D4 lands and the U2/U11 split-paste geometry. Diagnostic full-exposed-pad paste is excluded from production. The selected J3 drawing and native lands are SMD-only; adding holes to satisfy that classification would be wrong. Preview colours do not establish polarity or assembly approval. All 13 Gerbers match independent native regeneration, and all 416 drill/slot features match the board. The fresh BOM has 35 groups; all 79 CPL placements are byte-identical to the corrected input.

## Required PCB order settings

Use the 38 x 38 mm six-layer board, JLC06161H-3313, nominal 1.6 mm with published finished thickness 1.54 mm +/-10%, 1 oz outer / 0.5 oz inner copper, ENIG, green mask and white silk. Preserve the 90-ohm USB differential requirement and its 0.1392/0.1600 mm width/gap; confirm the named stack and impedance requirement in the manufacturer's CAM production files. [JLC stack table](https://jlcpcb.com/impedance)

Select the documented 0.20 mm drill/small-via process. The seven 0.350/0.200 mm vias meet the published preferred diameter-minus-drill rule. Specify epoxy-filled, copper-capped, mask-covered vias; keep component slots and NPTH mounting/locating holes open. Preserve J2's two 0.60 x 1.40 mm and two 0.60 x 1.70 mm plated shell slots. These are supported process selections, with quote and CAM confirmation at order entry. [PCB capabilities](https://jlcpcb.com/capabilities/Capabilities), [via covering](https://jlcpcb.com/help/article/pcb-via-covering)

## Four production outputs before assembly

1. **Placement and polarity:** obtain the final supplier two-face 2D production placement drawing. Match physical pin-1/cathode marks to native numbered pads and the exact corrected CPL. Submit JLC_CPL.csv; the native audit CPL is reference data. A symmetric outline fit or generic 3D red dot is not a polarity proof.

2. **Carrier and connector support:** use Standard double-sided PCBA with approved carrier/rails, tooling and fiducials. Confirm actual connector support/fixture suitability during order engineering and preserve mouth, nozzle and depaneling access.

3. **Production stencil:** JLC regenerates stencil data, so put the retained U2/U11 split-window requirements in order remarks. The supplied production instructions propose evaluation of a top 0.12 mm stencil with a 0.10 mm U13 region and a 0.10 mm bottom stencil. The stencil engineer must approve step boundaries, neighboring apertures and deposited volumes, or identify a qualified alternative. This is a feasible proposal, not an already-approved stencil. [JLC stencil workflow](https://jlcpcb.com/help/article/smt-stencil-data-prepared-for-smt-orders)

4. **USB shell soldering:** include an accepted solder operation and inspection for all four J2 S1 plated shell anchors. Their paste openings are intentionally absent. Contacts-only SMT reflow does not establish those mechanical joints.

These are normal order-engineering deliverables before PCBA production, distinct from the local bare-PCB geometry closure. P6-Production-Instructions.txt and the six-page assembly drawing carry the exact process details and placement references.

## First article

Inspect shorts and polarity before current-limited initial power, plus hidden and shell solder joints. Test rails, source switching, HSE, USB attachment/current policy, IMU, NAND and external interfaces. Verify the J3 harness cavity-to-pad mapping before power, then check the 1 A combined input budget, temperature, USB mating and enclosure/stack access. Thermal, EMI, firmware and application performance require hardware tests.
