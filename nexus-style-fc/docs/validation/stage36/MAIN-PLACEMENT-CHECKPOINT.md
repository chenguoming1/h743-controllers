# Stage36 independent ADC improvement

## Accepted changes
- C29 moves to F(111.0,119.2),270 degrees; R16 to F(111.4,121.15),90 degrees; C30 to F(114.39,114.16),0 degrees; R17 to F(111.4,123.2),270 degrees. Parts, values and MCU pin roles are unchanged.
- C30-to-MCU 5V ADC route improves from approximately 11.32 mm/two vias to 3.974 mm/one via. Its direct 0.25 mm ground return is 0.731 mm.
- C29-to-MCU VX ADC route is 3.052332 mm/one via; its filtered-node link to R16 is 2.583509 mm on F.Cu. C29 gains a direct 0.20 mm ground return of 0.779 mm to a nearby 0.45/0.20 mm through-via. R17 has a 2.394 mm local filtered-node feed and a 1.567 mm ground return.
- The nearby DSM_TX transition reuses an existing drill location, with the same signal-via count and approximately 0.500 mm added route length. The former ground connection is explicitly restored to the retained neighboring ground stitch; the original reset/crystal ground tree remains connected.
- The necessary 5V front branch is rerouted at its original 0.35 mm width. No power connection is dropped or narrowed.
- All NRST/OSC_IN/OSC_OUT track/via records and C10/C11/C12/Y1 poses remain unchanged from stage35. The original MCU ground branch now ends centrally on the new C29 ground via.

## Validation
Official KiCad 10.0.7 refill/DRC: zero errors, zero unconnected items, zero schematic parity violations; 61 warnings. Schematic unchanged from clean-ERC stage35. Generated source agrees on 89 footprints / 356 pads; exactly four placements change, BOM is unchanged and CPL changes only those references.

Saved fills connect C29/C30/R17 and retained C2/C21/C24/U5EP vias into the same GND polygon on both In1 and In4. The original clock/reset ground tree is explicitly retained. The limiting new C29-via-to-C12.1 copper/paste gap is 0.127367 mm, just above the 0.127 mm native copper rule; this is tightly packed and needs fabrication/assembly process review. Fresh mask/paste checks cover both full new via annuli against all 696 exported apertures: no center, drill or annulus opening; minimum gaps are 0.127367 mm for GND and 0.144711 mm for VX_SENSE. No filled/capped via process is assumed.

## Remaining NRST constraint
C10 remains remote. The attempted local C10/C12 placement required moving the nearby B_TX transition. A direct alternative B_TX escape crossed a necessary 5V rail branch; coordinated rail/via repairs then blocked either the MCU ground return or local NRST escape. Those partial trials were rejected. A proposed larger crystal shift also overlapped C25 and a load-capacitor courtyard. This establishes why the tested options were rejected, not proof that every local arrangement is impossible. A further coordinated crystal/load-capacitor/reset packing revision needs a new bounded plan; no MCU placement or pin-role change is proposed here.

## Other open gates
Retain stage35's documented U10 external-model/overlap mismatch, C19 lead-to-hole, edge/access, silk, tenting and process findings. Stage35's fresh JLC check cleared the two targeted mask-sliver/free-end findings; stage36 requires its own input-bound recheck. USB full-speed path/via asymmetry remains documented without an established numerical PCB mismatch failure. SI/PI, effective capacitance/ESR, thermal/current/transient/EMI, mechanical/vibration and assembly qualification remain open.

The 61 native warnings comprise 31 silk overlaps, 19 silk-over-copper, 7 track-not-centered-on-via, 3 silk-edge-clearance and 1 footprint-type mismatch. Five net additional warnings are silkscreen interactions near moved parts; no new electrical warning remains. Do not treat this checkpoint as fabrication-ready.
