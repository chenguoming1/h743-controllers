# Order fixes — 17 October 2026

**Prepared for two assembled main-board prototypes plus matching child PCBs, subject to the explicit factory process requirements below. Native checks pass, and both current Gerber ZIPs plus the new main BOM/CPL were freshly checked in JLCDFM. This is a prototype build recommendation, not measured electrical, load, mechanical or flight qualification.**

The owner's saved 5V_BUCK widening is preserved. The complete USB route objects, layer definitions and both stackups are unchanged from that saved input. No source board generator was run. [Exact source/CAM/BOM/CPL hashes and delta](candidate-delta.json), [native geometry](native-geometry.json), and [saved-fill versus fresh-refill equality](refill-check.json) bind this review to the current files. Historical reviews retain their earlier hashes and findings; this review supersedes their current-file/order instructions.

## Applied fixes

### VCAP C9

U1 remains **STM32F722RET6, LQFP64**. [ST DS11853 Rev9 Table19, page105](https://www.st.com/resource/en/datasheet/stm32f722ie.pdf) and [AN4661 §1.2](https://www.st.com/resource/en/application_note/an4661-getting-started-with-stm32f7-series-mcu-hardware-development-stmicroelectronics.pdf) specify one 4.7 µF capacitor and 0.1–0.2 Ω ESR for this package. Neither cited passage supplies an ESR reference frequency.

C9 is now **Samsung CL05A475KP5NRNC / C368809**, 4.7 µF ±10%, 10 V X5R, 0402. Added **R23, Uniroyal 0402WGF150LTCE / C423234**, **0.15 Ω (150 mΩ), ±1%, 62.5 mW**, in series with C9's branch:

`U1.30 VCAP → R23.1 → R23.2 VCAP_C → C9.1 → C9.2 GND`

Both parts are on B.Cu with 0.20 mm local routing and no vias in VCAP/VCAP_C. Added one local GND via near U1.31. C5 remains the original 0603 C69335 on its separate rail. Schematic, actual pad nets, source part definitions and exported BOM/CPL agree. The compact footprint variants retain stock lands, bodies and models, with individually reviewed compact courtyards. Native DRC and the fresh assembly collision check report no conflict at the new pair.

The [exact Samsung product curves](https://product.samsungsem.com/mlcc/CL05A475KP5NRN.do) show typical ESR around 0.015 Ω at 100 kHz and around 0.004–0.005 Ω at 1 MHz. With the deliberate 0.15 Ω series resistance and short copper, the representative room-temperature branch ESR is approximately **0.16–0.18 Ω**. This improves the previous uncontrolled low-ESR branch. These are estimates from typical curves, not production limits or a regulator-loop certification. The 0402 part's typical DC-bias graph suggests roughly 15–25% capacitance loss near 1.2–1.32 V; tolerance, X5R temperature and aging also apply. Its 4.7 µF marking is nominal, not a guaranteed in-circuit minimum. Startup and VCAP stability must therefore be measured on the prototypes before relying on the board. Do not call this a formally validated ST application circuit.

The MCU's DC core load does not flow through R23: R23 is only in the capacitor branch. Nominal RC is 0.705 µs; nominal capacitor energy at 1.32 V is about 4.1 µJ. Ripple/pulse dissipation and regulator stability still require measurement. [Samsung curve capture](c9-samsung.png), [assembly preview](vcap-assembly-preview.png).

### BEC input protection

D4 changed from the 13 V standoff SMF13A to **Littelfuse SMF9.0A / C1973343**, retaining the existing SOD-123FL pad copper, location and pin mapping: cathode VX, anode GND. The main-only exact symbol/footprint identity avoids changing the shared legacy sibling selection.

The [manufacturer SMF datasheet](https://datasheet.lcsc.com/datasheet/pdf/f8c76908115d9cf3a4ee18f1a219bc4b.pdf?productCode=C1973343), Table p2, specifies **9 V standoff, 10–11.1 V breakdown, 15.4 V maximum clamp at 13 A, 10/1000 µs**, at its stated conditions. That is better aligned with the confirmed regulated **7.4 V BEC** and the downstream 18 V absolute-maximum regulator than the old 21.5 V rated clamp. The manufacturer drawing was compared with the unchanged lands, and the new JLC model's cathode band aligns with the native cathode side in the [bottom preview](d4-polarity-preview.png). This does not establish immunity to unlimited energy, high-temperature surges, layout overshoot or sustained overvoltage. **This revision is for regulated 7.4 V BEC input; no raw flight battery or rail above 9 V.**

JLC showed 5,485 pieces / 5,482 available and SMT assembly support for D4; R23 showed only eight pieces. Two boards require two R23 placements; the supplier's actual setup/attrition quantity must be accepted by the quote. No stock has been reserved and no purchase was made. [D4 stock](d4-stock.txt), [R23 stock](r23-stock.txt).

### Main/child mating fit

Main J1 slots are now **9.8 × 2.2 mm, R0.5**; the child tabs narrow from 9.3 to **8.4 mm**. Pitch stays **11.20 mm**. All mating contact pad geometry, positions and pinout are unchanged. Local child routes moved only enough to preserve edge clearance. All 32 child vias and its four-layer power stack are retained. The child 3D model was regenerated from the changed child PCB.

The [source-bound geometry/tolerance screen](mating-fit.json) verifies actual outlines against the dimensions. A combined example with slot 9.6 × 2.0 mm, tab 8.6 mm, thickness 1.76 mm, radius 0.6 mm and total pitch mismatch 0.4 mm leaves about **0.034 mm radial corner reserve** when the pair shares half the mismatch. Doubling that pitch mismatch fails the screen. Thus the improvement does not guarantee fit across arbitrary independent full position tolerances. Agree matched dimensions/pitch/finished thickness and require physical insertion inspection. No mechanical strength, solder fatigue or vibration rating is established.

Child header lands increase from 1.50 to **1.52 mm**, retaining 1.00 mm holes: **0.26 mm nominal annulus**, above the previously noted 0.254 mm 2 oz PTH guidance. Dedicated VX/GND planes and power-via topology remain.

### USB shell mounting holes

J6's four short 0.85 × 0.60 mm plated slots became **0.85 mm round PTH holes at the exact original centers**. The round opening encloses the previous nominal capsule. The original oval land is retained and unioned with a 1.15 mm central circle for 0.15 mm nominal ring around the round drill. Exported Excellon contains exactly four 0.85 mm round holes and 228 0.20 mm vias; the four short plated slots are gone. C31 moved only −0.03 mm X / −0.06 mm Y, with its four local route endpoints, to preserve clearance.

The [connector manufacturer drawing](sources/J6.pdf) recommends **0.8 ±0.1 mm PCB** and shows **0.95 mm shell legs**. On the main board's nominal 1.6 mm thickness those legs do not protrude. **Factory must approve and inspect the actual shell/barrel soldering method and retention.** Enlarging the holes does not solve leg length. JLC's fresh SMT analysis raises four J6 pin-to-hole alignment flags with value 5.25 (units unspecified in that table), while PCB short-slot/slot-width categories are green. Nominal opening containment and unchanged centers support fit relative to the original recommended holes, but do not dispose of the short-leg assembly issue or actual part/tolerance stack. Factory review is required. [SMT detail](j6-smt-details.txt).

## Current verification

- KiCad 10 native main **ERC 0, DRC 0, opens 0, schematic parity 0**.
- Child **ERC 0, DRC 0 errors, opens 0, parity 0**; 11 inherited missing-courtyard warnings on bare contact footprints.
- Local model/library dependencies resolve. Both saved zone fills exactly match fresh native refills performed on separate copies. Rule settings and inherited ignored ERC checks were retained; no DRC exclusions added.
- Source definitions, actual PCB footprint/value/LCSC/pad-net data agree; exported schematic netlist independently confirms U1/C9/R23/D4. Main: **90 footprints, 84 assembled parts, 53 BOM groups, 84 CPL placements**. Child: **one optional header BOM/CPL placement**.
- ZIP integrity and each archived file's equality to the loose CAM export checked: **main 16 members, child 14**.
- USB route/via objects are unchanged. Fresh [saved-fill reference coverage](usb-reference.json) confirms both matched In3 trunks have continuous projected In4 ground across their center and edges. The earlier about-90 Ω field estimate remains applicable to the unchanged modeled cross-section; launches, transitions and the full assembled port remain electrically unqualified. Factory impedance control/coupon is required.

Native reports: [main ERC](native/nexus-style-fc-erc.json), [main DRC](native/nexus-style-fc-drc.json), [child ERC](native/nexus-header-board-erc.json), [child DRC](native/nexus-header-board-drc.json).

## Fresh JLCDFM results

Uploaded the exact current ZIPs and, for main SMT, the exact new BOM/CPL. All **53 groups confirmed** in the [matching screen evidence](bom-matched.txt), including exact C9, R23 and D4 identities.

| Result | Displayed danger | Displayed warning | Interpretation |
| --- | ---: | ---: | --- |
| [Main PCB](https://jlcdfm.com/viewer?pcbUploadFileId=634370103513927681) | 257 | 188 | Counts include capped silk and via-classification categories; not a clean pass |
| Main SMT, same viewer | 29 | 13 | 25 earlier danger flags plus four J6 pin/hole flags; factory disposition required |
| [Child PCB](https://jlcdfm.com/viewer?pcbUploadFileId=634370268063682561) | 0 | 78 | 12 via-ring flags, 26 through-hole-to-SMD and 40 equal-size mask warnings |

Counts are category occurrences, not unique physical defects, and several categories cap at 100. Default web rules were retained. [Main PCB category data](main-pcb-dfm.json), [SMT data](main-smt-dfm.json), [child data](child-pcb-dfm.json) include exact triples.

Main width, trace spacing, pad spacing, sharp corners, soldermask bridge and mask-to-trace categories remain **zero danger/warning**. Both slot categories are now zero. The new round USB holes are recognized by additional generic PTH-to-SMD clearance checks; that classification does not establish new shorts. Native pad-to-hole/track clearances pass, and the USB assembly concerns are explicitly retained above. Main retains three via-to-pad flags, three negative-mask warnings, via-ring flags, silk flags and dense-layout assembly flags. Use POFV for **all 228 main vias**, rather than ordinary tenting, to address the many pasted-via sites.

Child's 12 annular flags report **0.15 mm** on 0.30/0.60 mm vias, not its now-0.26 mm header rings. Its 40 new negative-mask warnings report **0 mm difference** on equal-size 1.52 mm circular lands/openings (20 per face); CAM/native mask equals copper diameter, so they are zero-expansion boundary/rounding results, not deliberately undersized openings. Copper/mask identity was checked; factory registration is still a process matter. Do not enlarge openings merely to turn this numerical boundary green.

Main SMT reports **no collisions, missing pads, clipped components or lead-area overlaps**. Retained left/right pin-edge flags on D1–D3/F1/F2 have prior drawing-based dispositions in the [pin-edge review](../pin-edges-2026-10-17/REVIEW.md). The 11 lead-to-hole flags and 4/7 component-edge flags still need factory stencil, tooling/panel and solder-joint review. They were not silently waived or relabelled green. The new VCAP pair and TVS were visually inspected in the imported assembly view.

## Updated child power calculation

Fresh extraction and three-grid solves use this exact child hash. [Calculation output](power/four-layer-full-load.json) uses 5/5/5/3.5 A servo stress loads plus 1.1 A main load (19.6 A total), prescribed 80°C copper resistivity, ≥60 µm outer / ≥55 µm inner copper and ≥18 µm local barrel wall with 1.65 mm length. At 0.05 mm grid, matched dual-feed board copper/barrel loss is **0.275 W** (0.281 W at 0.075 mm, 0.285 W at 0.10 mm). The tested single-feed cases reach about **0.485 W / 27 mV board-only drop**. Those are electrical losses at an imposed temperature, not a predicted temperature rise or measured rating. Contact/wire/source loss is additional and can dominate; model outputs retain it separately.

The retained header is specified **3 A/contact**. The Hobbywing V4 BEC is not a 19.6 A continuous source. Two BEC plugs share current imperfectly. The board changes do not make the connectors, wires, BEC or complete servo system a 20 A continuous system. Do not rely on a thermal estimate that omits those limits.

## Order and bring-up

Use [manufacturing/README.md](../../../../manufacturing/README.md) and [ORDER-INSTRUCTIONS.txt](../../../../manufacturing/ORDER-INSTRUCTIONS.txt). Confirm the exact six-layer main stack/90 Ω process, POFV, four-layer **2 oz outer AND inner** child stack, matched fit and J6 assembly method with the factory before release. The prepared notes have **not** been sent to a supplier and do not represent acceptance. Quantity confirmed by owner: **two main assembled boards**.

After arrival, inspect and check for shorts, power with current limiting and no servo/motor load, measure supply rails and VCAP startup/ripple, and verify reset/SWD/BOOT programming. Test USB in both cable orientations and both power configurations, then add peripherals and servo loads incrementally with blades removed. Firmware target resources, sensor orientation, transient immunity, thermals and flight behavior require physical commissioning.
