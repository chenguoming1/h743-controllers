# GCT USB4145-03-0170-C vertical USB-C footprint review

Status: **drawing-verified footprint integrated in the final prototype; fabrication and assembly qualification remain open**. Manufacturer-drawing review was prepared 2026-10-06; the current implementation is bound to PCB `4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f`. J1 is the GCT USB4145-03-0170-C / C5181332 upward-facing, top-entry receptacle.

## Deliverable and independent check

The [project-local footprint](../hardware/library/F722_Heli.pretty/USB_C_Receptacle_GCT_USB4145-03-0170-C_16P_Vertical.kicad_mod) has library identifier `F722_Heli:USB_C_Receptacle_GCT_USB4145-03-0170-C_16P_Vertical`. It is applied to J1 in the current schematic, PCB and parts registry.

The retained manufacturer drawing was visually checked independently on sheet 1 (component top/bottom views, physical dimensions and variant ordering grid), sheet 2 (recommended land pattern and pin table), and sheet 3 (pickup cap and mating diagram). A 350-dpi render of sheet 2 was inspected to check hole types, pad endpoints and row spacing. In particular, the component **bottom view** on sheet 1 swaps the vertical row positions; it must not be copied as the component-side footprint. The recommended layout on sheet 2 and the top view on sheet 1 both put A1 at the upper left, A12 upper right, B12 lower left and B1 lower right. The right locator is oval, the left is circular.

Manufacturer source: [GCT USB4145 drawing, A2, 2023-01-31](https://gct.co/download?name=USB4145.pdf&type=PDFDrawing), [product page](https://gct.co/connector/usb4145). Procurement research selected [JLC/LCSC C5181332](https://jlcpcb.com/partdetail/5839804-USB4145_03_0170C/C5181332). Live stock and assembly acceptance must be rechecked at procurement.

## Exact land pattern

Millimetres, component-side view, origin at the midpoint of the locator holes; +X right and +Y down.

| Row | Y | Pad identifiers left to right | X positions left to right |
|---|---:|---|---|
| A | -1.485 | A1 A4 A5 A6 A7 A8 A9 A12 | -2.75 -1.25 -0.75 -0.25 +0.25 +0.75 +1.25 +2.75 |
| B | +1.485 | B12 B9 B8 B7 B6 B5 B4 B1 | -2.75 -1.25 -0.75 -0.25 +0.25 +0.75 +1.25 +2.75 |

- All 16 SMT lands are exactly 0.30 × 1.15, rectangular, on F.Cu/F.Paste/F.Mask. The 1.82 gap between row inner edges plus 1.15 land length gives 2.97 centre separation, hence Y = ±1.485. The six middle lands are at 0.50 pitch; outer contact centres span 5.50
- Four `S1` plated oval pads centred at (±4.00, ±1.43), copper 1.60 × 1.10, horizontal finished drill 1.10 × 0.60. The nominal copper ring is 0.25. Pads span all copper/mask layers and do not have an invented F.Paste aperture
- Left locator: (-4, 0), NPTH circular 0.71 diameter
- Right locator: (+4, 0), NPTH horizontal oval 1.01 × 0.71
- Native pad count is 22: 16 SMT contacts, four repeated S1 shell pads, two unnamed NPTHs. The 17 distinct electrical pad identifiers exactly match the existing USB2 symbol
- Manufacturer land-pattern dimensional tolerance is ±0.05. Treat drill dimensions as finished hole dimensions and obtain fabricator plating compensation
- Copper envelope is 9.60 × 4.12 before courtyard margin

The selected connector has 16 independent SMT tails. Pad names remain distinct, and every tail retains its assigned electrical net.

## Symbol/net preservation

The applied `F722_Heli:USB_C_Receptacle_USB2.0_16P` symbol preserves the selected connector’s pin functions.

| Pad identifiers | Existing board net |
|---|---|
| A1 A12 B1 B12 S1 | GND |
| A4 A9 B4 B9 | USB_VBUS_RAW |
| A5 | USB_CC1 |
| B5 | USB_CC2 |
| A6 B6 | USB_P |
| A7 B7 | USB_N |
| A8 | unconnected-(J1-SBU1-PadA8) |
| B8 | unconnected-(J1-SBU2-PadB8) |

A8/B8 remain explicit no-connects; CC1/CC2 have separate pull-downs, with the existing ESD and VBUS circuitry retained. The duplicate D+/D− contacts are routed in the current board. This implementation does not add USB PD or establish a higher power/current allowance.

On the frozen board, J1 is on **F.Cu at (39.000, 13.000) mm, rotation 90°**. Its local +X points toward board −Y. Use this saved placement and numbered-pad mapping for factory pin-1/pickup review; the native placement angle does not itself certify a supplier-library rotation.

## Mechanical layers and limits

- F.Fab has the nominal manufacturer body rectangle, 8.94 × 3.16 centred on the origin. Nominal shell height is 7.46 above the PCB
- Dwgs.User shows a dashed 8.94 × 3.69 overall termination envelope and the temporary 10.00 × 4.00 pickup-cap envelope. The cap top is 8.46 above the PCB and must be removed after assembly
- F.CrtYd is a closed 11.00 × 5.20 rectangle, the cap/copper envelope plus 0.50 nominal margin per side, rounded outward to the 0.05 grid
- One F.Cu footprint-only rule area covers X = ±5.00 and Y = ±2.06. This preserves front component/pickup space. It intentionally allows tracks, vias, pads and copper pours
- Four B.Cu footprint-only rule areas and matching B.CrtYd rectangles are each 2.60 × 2.10, centred on the shell slots. They reserve the shell-pad size plus 0.50 per side from other bottom components. B.Fab shows nominal 0.70 × 0.30 metal-stake plan rectangles
- The front/back keepouts are **provisional engineering mechanical reserves**, not claimed manufacturer-mandated keepout coordinates. Sheet 2 supplies a keepout legend but does not dimension an additional crosshatched copper keepout region. Native plated/NPTH drills and normal board clearances protect holes on all copper layers; do not treat the footprint-only rule areas as copper keepouts
- 1.70 nominal shell stakes have +0.10/-0.20 tolerance. At the saved 1.0324 nominal board thickness, bare-metal projection below PCB is 0.4676 minimum / 0.6676 nominal / 0.7676 maximum. Worst-case projection uses 1.80 minus the minimum finished PCB thickness, plus assembly-specific solder fillet height
- The provisional underside reserve is 1.20 vertically below PCB at the four stakes. That is not enforced by a 2D KiCad keepout. It uses the earlier ±10% board-thickness assumption plus roughly 0.3 solder/mechanical allowance; confirm actual tolerance before release. The plastic pegs extend 0.64 from seating plane and nominally do not project through this board
- A cable overmold shoulder is about 2 mm above the receptacle mouth in GCT's mating diagram, about 9.46 above PCB. Cable-specific overmold/bend space and the full top/bottom board assembly must be checked separately against the 13.1 target

No STEP model is attached. The manufacturer's default preview is the 0070 stake variant, not the selected 0170. A correct future model must be verified for origin, rotation, seating plane and 1.70 stake length. No approximate solid is presented as an exact part.

## Assembly and procurement gates

The source-backed research snapshot for C5181332 reported 993 in stock, 922 available to order, Extended, Economic/Standard SMT Assembly eligibility, and **High assembly difficulty**. These are observations, not a reservation or quote. The catalog's 24P label does not replace the manufacturer's 16-active-contact USB2 definition.

All four shell stakes must be soldered for retention. The standalone footprint intentionally has no shell paste openings because paste-in-hole/stencil details have not been qualified. Obtain assembler review of plated-slot filling, solder process, pickup cap, bottom-side access, CPL orientation, reflow/assembly order and any difficulty-related fee. SMT-only soldering of the signal pads is insufficient mechanical retention. Do not claim JLC approval, waived fees or qualified production assembly.

## Verification scope

The original isolated footprint review checked native parsing, all 22 pad objects, pad identifiers, dimensions, plating and drills, the five footprint-only rule areas, and the absence of an incorrect 3D model. A native drawing export was compared visually with the manufacturer layout. Its zero-violation standalone DRC was a geometry check with unassigned nets, not routed-board qualification.

The footprint and selected part are now applied. The frozen project’s exact-board source-parity report records no value, footprint or numbered pin/net mismatch; both native board DRC modes report zero opens and zero geometric errors, with nine visible power/ground warnings retained. These checks do not establish USB electrical compliance, supplier-library placement rotation, solder-process acceptance or the full connector/cable envelope.

Use the current project’s native source and manufacturing notes for fabrication and assembly review. The earlier isolated test boards, temporary plots, metadata-update scripts and historical source-change plan are not required public project files. The four plated shell slots still require a qualified soldering operation; the final exports contain 16 USB contact paste apertures and no shell paste.
