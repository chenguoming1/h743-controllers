# Assembly and manufacturing intent

This is a process specification for supplier review, not a released order. No board or assembly has been manufactured in this work.

## PCB

- Six copper layers; JLC06161H-3313 standard stackup from the nominal 1.6 mm product category. CAD copper/dielectric sum1.5384 mm, approximately 1.54 mm finished designation. Confirm the exact stackup and finished tolerance in the quote
- Outer copper nominal 35 µm; inner copper15.2 µm. Dielectrics:0.0994 /0.5500 /0.1088 /0.5500 /0.0994 mm
- Intended finish: ENIG. Review stencil and solder-mask registration for the MIA LGA,0201 parts, QFN/SON thermal lands and USB connector
- All 105 vias explicitly request filled and capped processing in KiCad10, with tenting as recorded. Use epoxy-resin fill and copper cap/planarization suitable for via-in-pad; ordinary tenting or ink plugging is not equivalent. Confirm the fabricator recognizes the via attributes and instructions
- Fill/cap only vias. Do not fill the antenna feed hole, connector plated holes/slots, or switch locating NPTHs
- The nominal overall plan outline is 35×24 mm with a recess below the ESP antenna. A hard maximum finished device envelope requires an agreed board-profile tolerance and assembly acceptance fixture
- Confirm90 Ω differential USB and 50 Ω single-ended RF impedance on the stated outer/nearest-ground layer pairs, including finished copper, mask and etch compensation. The calculator's numerical solve tolerance is not a production guarantee

The copper layout includes actual filled/capped-via-in-pad requirements at several power/ground locations and the U5 ground return. The renderer may display a drilled via even when fill/cap process attributes are requested; it is a CAD view, not a photograph of a built stack.

## Ceramic GNSS patch

A1 uses an engineering-derived footprint, not a manufacturer-approved host land pattern. Exact part: INPAQ PA1575MQ4S-123-1Z. Nominal body10×10×4 mm; one0.81 mm feed pin, offset0.50 mm, with a nominal 3 mm protrusion and 0.16 mm adhesive.

Host pad:1.70 mm copper diameter,1.00 mm plated finished hole, no paste. Conservative published hole/pin limits give0.08 mm minimum diametral insertion clearance and approximately 0.235 mm annular copper with the stated registration allowance. The underside RF isolation margin can become small after pin/hole play and alignment; inspect for solder bridging and confirm the exact manufacturer's intended ground/adhesive interface. Do not assume an arbitrary replacement adhesive is electrically or thermally equivalent.

Install after SMT reflow, using an agreed adhesive/fixture and controlled manual or selective pin soldering. Confirm that the part, tape and assembly sequence tolerate the actual process. Inspect body position against the plan envelope and ensure protruding pin/solder cannot contact the battery or enclosure.

Mount and handle the patch in an ESD-protected area with grounded tools and board ground established first. If the antenna will remain touch-accessible outside an ESD-protected environment, qualify additional protection/enclosure measures; this design is not certified for exposed-antenna ESD.

C13/C14 are native DNP positions and must remain unpopulated until host matching is measured. R15 starts at 0 Ω. Preserve the RF trace geometry and ground returns during tuning.

## Orientation and indicators

B is the sky-facing face, marked SKY. The ceramic patch and G/R/S indicators are on B so they remain visible from the intended mounting side. F carries both RF modules. The battery and enclosure have not been mechanically modeled. Keep the patch facing open sky and qualify the complete host.

G and R are green, firmware-driven GNSS/RID indicators. S-green shows enabled 3V3 and S-red shows charging from external power, including with SW1 off. This defined charging behavior is not copied from the OEM reference's external-power indication.

## Other assembly checks

- Both Espressif and u-blox recommend a single reflow. Both modules are on F in this revision: assemble B-side ordinary components first, install both F-side modules in the final reflow pass, then attach and solder the B-side ceramic patch. The selected Kingbright LEDs allow a maximum of two reflow passes. Confirm every selected part, adhesive and actual profile with the assembler; the layout resolves the avoidable opposite-face module reheating conflict, but does not itself qualify a factory process. Respect moisture, profile and cleaning limits; u-blox prohibits ultrasonic processes
- SW1's actuator faces the accessible top-left edge. PWR is the only direction-neutral legend. Verify actuator position versus contacts before assigning ON/OFF in an enclosure
- JST header J2 is keyed, but the exact battery harness is not qualified. Pin1 BAT+, pin2 NTC, pin3 GND must be checked against the actual mating harness, not wire colors alone
- Test pads: TP1 GND, TP2 ESP_EN, TP3 BOOT_IO9, TP4 3V3. USB test stubs were removed; probe the resistor lands with appropriate low-capacitance tools
- The custom antenna, MIA, switch and several small-part 3D models are labelled visual approximations. U1 is vendor STEP; J1 is a third-party STEP. No approximate model substitutes for a component drawing or first-article measurement

Sources: [JLC via covering](https://jlcpcb.com/help/article/pcb-via-covering), [JLC capabilities](https://jlcpcb.com/capabilities/Capabilities), [Espressif module datasheet](https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.pdf), [u-blox integration manual](https://content.u-blox.com/sites/default/files/documents/MIA-M10Q_IntegrationManual_UBX-21028173.pdf), and exact component sources in `component-qualification.md`.

SW1 electrical mapping: pin 2 is common VSYS; pin 1 drives BUCK_EN; pin 3 is unconnected. R10 pulls BUCK_EN to ground when the switch selects the unconnected throw. The switch does not place VSYS directly across ground.
