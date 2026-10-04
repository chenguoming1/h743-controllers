# P5 routing visual review

**Visual disposition: accepted for this bounded routing cleanup.** The final actual copper has visibly simpler long routes and perimeter escapes on every signal layer. No new visual routing defect was found in the final comparison. This is a visual review of prototype CAD, not hardware qualification.

Reviewed final PCB SHA256: `6e2031b040ce8f3a534c2f73abb0091e25b3e6adcab982463264ad8898d65cf8`. Baseline P4 SHA256: `b2532487feab1cfd68047b27999651e6c35cae959b0d115ef2762de5341bdb7a`. The native board was not edited by the visual review. The actual final F.Cu, In2.Cu and B.Cu exports were independently inspected as pixels, including critical local zooms and a zone-free In2 diagnostic. These are the three layers containing signal tracks.

## What improved visibly

- The front AUX_PD14 route around H4 and USB_PRESENT_n route around H1 use compact polygonal corners instead of many tiny staircase segments
- The rear +5V_STACK incline has a straight vertical/45-degree course; southeast power and AUX_PC8 traces were cleaned together so neither forces a scalloped companion
- The two long UART2 spans beside the MCU now use vertical and 45-degree sections; the upper pin/via escape remains locally shaped
- The GND loop near U1 and the outer SWCLK arch have fewer, clear corners
- In2 NRST around H3 changed from a 39-segment stepped arc to a three-segment polygon, at 0.150 mm width
- Safe neighboring width transitions were joined; routing was not narrowed merely to make the drawing look cleaner

Final native track count is 5,741: F.Cu 2,101, In2.Cu 1,776, B.Cu 1,864. P4 had 7,302. The reduction of 1,561 is supporting context; acceptance is based on the visible changes, specific obstacle review and the separate native validation.

`routing-before-after.png` compares five representative areas at equal coordinates and scale within each before/after pair. `inner-H3-before-after.png` provides the inner-layer result at a larger reading size. The P4 and P5 whole-board views provide the wider context. Rear copper is shown in native top-view orientation, not mirrored.

## Why some detours remain

**H4 / AUX_PD14:** the straight line between the route's endpoints (33.95,31) and (30.65,33.8) crosses AUX_PC8 and the +5V_STACK connection. The actual obstacles include the AUX_PC8 via at (33.5,31.55), the +5V_STACK via at (31.7,32.45), and the H4 track keepout of radius 2.5 mm around (34.25,34.25). `retained-H4.png` labels these objects. The large detour is now polygonal; it was not replaced with an electrically invalid shortcut.

**Q2 / USB_SOURCE_DISABLE:** a direct line from (19.4,27.375) to (19.35,29.4) crosses the GND return near (19.3,28.175). `retained-Q2.png` shows the actual crossing. The route around the return remains, with simplified corners.

**Southeast power/AUX pair:** the +5V_STACK hook must pass below the GND via at (30.75,32.0) and the return/pad near (31.275,31.4). An independent power-only replacement hit the old AUX_PC8 path. Both were therefore reviewed together. The final power path stays 0.450 mm; the AUX path stays 0.150 mm in the changed bulk, with the existing exact via-entry tail retained. Further straightening of that tail added a measurable reference-plane gap in the tested alternative.

## Remaining inner-layer details

The filled copper picture can exaggerate the appearance of a wavy trace because the GND-clearance contour follows nearby vias and trace widths. `inner-trace-diagnostic.png` removes zone fills only from the rendering and retains native track/pad polygons and via holes. It confirms that some small centerline steps remain as well; they are not all a fill-display effect.

Two representative remaining hooks were tested explicitly:

- MOTOR_OK_BUF around x12.7–16.9, y26.5–27.6: a simple uniform 0.150 mm polygon collided with the USB_PRESENT_n via at (13.15,26.7) and adjacent USB_PRESENT_n trace sections near y27.2; it also introduced about 0.00576 mm² of new reference-gap area. Green and red geometry in the diagnostic identifies these routes
- AUX_PD14 around x20.95–23.15, y31.05–31.95: the tested simplified polygon collided with the AUX_PC9 via at (22.65,31.45) and introduced about 0.00516 mm² of new reference-gap area. Purple and blue geometry identifies that constrained hook

Those are concrete reasons to reject the tested shortcuts. They do not prove that every remaining tiny bend is globally optimal. Further changes would need a separately validated coordinated reroute; this review leaves those local details in the checked geometry.

## Review evidence and limits

The final native DRC report contains zero physical violations, zero unconnected items and zero schematic-parity entries. The routing implementation has separate contact, reference-plane, physical pad/via partition and replay evidence. This visual review independently confirms the visible routes and obstacle locations, and does not replace those checks, manufacturer review or hardware testing.

`ranked-findings.json` preserves the original P4 coordinates and native segment UUIDs for the initial findings. `visual-review-manifest.json` identifies the exact reviewed source and image hashes. All diagrams are inspection views, not print-scale fabrication drawings.
