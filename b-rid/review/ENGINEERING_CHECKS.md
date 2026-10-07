# B-RID engineering checks

Latest revision-specific checks and hashes: [CURRENT_REVISION.md](CURRENT_REVISION.md). Earlier evidence remains historical; current evidence is in `evidence/routing-cleanup-20261007/`.

## Result and scope

The final editable KiCad 10.0.6 project passes native schematic ERC, PCB DRC, open-connection and schematic-parity checks: **0 / 0 / 0 / 0**. The project contains 60 footprint references,688 trace segments and 104 vias. Four references are test pads;56 have resolved 3D model associations. C13/C14 are native DNP tuning positions, leaving54 nominal populated component references.

These checks establish the reviewed CAD state, not a manufactured or electrically tested product. Battery/harness, procurement, assembly, USB power-policy and physical qualification gates remain. There is no fabrication, flight or compliance release.

## Design checks passed

### USB

- Correct mapping: J1 A6/B6 → U5 I/O1 pins1/6 → R3 → ESP pad27/IO19/D+. J1 A7/B7 → U5 I/O2 pins3/4 → R4 → ESP pad26/IO18/D−
- All USB data traces are 0.135 mm wide. The coordinated main B-side pair has a nominal 0.150 mm edge gap; actual tight-coupling measurements are approximately 19.11 mm D+ and 19.17 mm D−
- F-side data references In 1 GND and B-side data references In 4 GND. Independent full-width samples show continuous reference away from each signal's intentional via antipad
- ESD-output-to-MCU copper lengths are 26.491449 mm /26.522086 mm, giving0.030636 mm mismatch. This figure excludes component interiors and equal via barrels and is **not** connector-to-MCU skew
- Two MCU-transition ground returns are present, preserving the converter's original thermal return. A new filled/capped-process GND via is 0.2625 mm from U5 pin2 center

### Impedance basis

JLC06161H-3313 is selected from the nominal 1.6 mm category. Copper/dielectric sum in CAD is 1.5384 mm, consistent with the calculator's approximately 1.54 mm finished designation. Outer/inner nominal copper is 35 µm/15.2 µm; adjacent outer reference spacing is 0.0994 mm.

| Official uniform calculation | USB 90Ω width/gap | RF 50Ω width |
|---|---|---|
| Coplanar,0.300 mm flanking-ground gap |0.1349/0.1501 mm|0.1494 mm|
| Non-coplanar microstrip |0.1356/0.1501 mm|0.1509 mm|
| Actual CAD |0.135/0.150 mm|0.150 mm|

The board has a 0.30 mm minimum outer GND-zone clearance rule, not a uniform coplanar cross-section. The separately checked non-coplanar result supports the same nominal widths. Neither calculation guarantees every pad/transition/asymmetric power-copper feature or the fabricated impedance. The exact finished stackup, conductor shape/mask and acceptance coupon remain fabricator-controlled requirements. [Official JLC calculator](https://jlcpcb.com/pcb-impedance-calculator)

### RF and power

- The direct INPAQ patch feed is 4.085341 mm of 0.150 mm trace, excluding R15's interior. In 4 GND is continuous below it except at the intentional antenna PTH antipad. RF shunts are native DNP; R15 starts at 0Ω
- C4-to-VIN is 2.50 mm, C5-to-VINA1.253 mm, and C6-to-VOUT1.360 mm. Inductor paths widen to 0.50/0.40 mm after short IC escapes, with explicit ground returns and the Würth central copper restriction
- Exact MLCCs replace generic voltage annotations. The two22 µF output capacitors have a combined conservative engineering screen of about 18.5 µF at 3.4V based on manufacturer typical bias data. This is margin evidence, not a guaranteed combined worst-case capacitance
- TMUX1119 selects GND at BAT_SENSE while3V3 is off, and the buffered-by-capacitance divider node while on. The reservoir remains on the divider side. A GPIO8 pull-up completes the manual-recovery strap bias
- Actual G/R/S labels and corner-switch placement are encoded in the board. G/R require future firmware; S-green denotes3V3 power and S-red charging

## Justified compact-layout deviations

The USB-C duplicated contacts create orientation-dependent paths. To the **first clamp** pads, A6/A7 paths are 5.900343/3.790343 mm; B6/B7 paths are both2.790343 mm. Complete A-orientation board mismatch is about 2.079364 mm, while B orientation retains about 0.030636 mm.

Using conservative propagation√4.6/c, the A-orientation mismatch is about 15 ps. A3.11 mm duplicated-contact branch has about 45 ps round-trip delay. These are small compared with full-speed USB's4–20 ns transitions. No trivial U5 reversal removes the physical detour, so extra meanders or wholesale rerouting are not justified solely to advertise tiny connector-level skew. These are engineering estimates, not eye/ESD measurements. [USB 2 primary specification](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/138/usb_5F00_20.pdf)

Nearest existing MCU return distances remain2.052 mm for D− and 1.524 mm for D+. The added second return is 2.145/1.636 mm away. Connector transitions share a close return0.955 mm from each signal. These distances are disclosed rather than called ideal paired-return placement; the extra MCU and direct ESD returns remove straightforward weaknesses without disturbing the validated power loop. [Espressif USB guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/pcb-layout-design.html#usb)

## Nominal and tolerance-aware mechanical checks

- Native outline: x100.2–135.2 / y100–124, nominal 35×24 mm. The recess removes host PCB beneath the ESP antenna's nominal region
- Vendor ESP STEP measures x118.3–134.9 / y100.7–113.9. A conservative±0.15 mm body allowance plus assumed±0.10 mm placement gives a right limit135.15, only 0.05 mm inside the nominal envelope
- SW1 is inset to y103.10. Its conservative2.96 mm actuator reach leaves0.14 mm before placement variation, or0.04 mm with an assumed0.10 mm placement allowance. The corrected approximate model now shows the actuator toward the edge
- Patch nominal body is x100.8–110.8 / y113.3–123.3. Hole/pin play, body offset, adhesive and placement still require inspection

**A hard35×24 mm finished maximum requires explicit PCB-profile and assembly acceptance tolerances.** Nominal CAD and approximate models cannot guarantee that maximum. Antenna/recess position and actual surrounding battery/enclosure clearances must be checked on the assembled host. No15 mm enclosure keepout or RF performance claim is implied by a visual fit.

U1 retains the vendor STEP and J1 a third-party STEP. U2/A1/SW1 and several new small parts use labelled dimensional approximations. The original transferred approximate model files are preserved; corrected MIA marker and switch-actuator versions are separate files.

## Remaining gates

- **Supplier/part:** exact protected cell/NTC/harness/current/timer/temperature pairing; MIA receiver and exact INPAQ antenna availability; footprint/adhesive/ground-contact and assembly confirmation
- **Process:** ENIG, explicit via fill/cap acceptance, controlled stackup/impedance and compatible B-side-first / F-module-side-last reflow process
- **Bench:** USB signal integrity/ESD and both orientations; GNSS matching/acquisition/coexistence; power startup/transients/thermal/charge behavior; ADC isolation; LED visibility; first-article mechanical fit
- **Functional limitation:** USB SOF is not a 500mA grant. MCU-off host-suspend detection is unresolved; supported operation must be restricted or the design/firmware extended before USB-compliance claims
- **Firmware/compliance:** no firmware implemented or flashed; no proof of actual RID broadcasting, RF compliance or flight suitability

Details and primary sources: `component-qualification.md`, `battery-thermal-followup.md`, `FIRMWARE_INTERFACE.md`, `ASSEMBLY_NOTES.md`, `PROTOTYPE_GATES.md`, and native check evidence in `evidence/`.

## Final face and process improvement

Both U1 and U2 are now on F. The directly mounted patch and all three G/R/S indicators are on B, which is explicitly marked SKY. B-side ordinary components are assembled first, both F-side modules in the final SMT pass, and the patch afterward. The Kingbright LED specification permits up to two reflow passes. Confirm the full selected-parts/profile compatibility with the assembler.

The new F RF route is 1.956812 mm from the receiver to R15 and 2.128528 mm from R15 to the antenna, excluding resistor interior. C13 and C14 tuning branches are 0.954558 mm and 1.330000 mm. Antenna ground returns are 1.500 / 1.503 mm from the feed; shunt return vias are approximately 0.710 / 0.700 mm away. All 6,040 sampled points within the B-side 8 × 8 mm adhesive area are GND outside the intentional 1.3 mm feed exclusion. No ordinary non-ground B copper or via enters that area. The feed antipad is intentional, not an unnoticed reference-plane break.

The final face reroute changes only local GNSS/indicator paths and one BAT+ measurement branch. USB copper, the outline, converter switching nets, charger VBUS/VSYS routing and critical power placements were verified unchanged.

## Check coverage

Native reports cover configured error and warning severities with zero excluded violations. Inherited ignored DRC categories are missing courtyard, off-center via endpoint, tuning-profile geometry, footprint filters and component-type mismatch. Inherited ignored ERC categories are singleton global labels, four-way junctions, SPICE models and footprint filters. These categories are disclosed rather than represented as passed tests; no exclusions were added to hide the reroute.
