# Prototype handoff and acceptance scope

## Exact design

PCB SHA-256: `4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f`. The PCB outline centerline is nominally 41.66 × 25.40 mm. The unchanged 5.84 mm contact projection gives the 47.50 mm nominal controller length. This is not a zero-tolerance case-fit maximum: contact projection alone can raise the known length subtotal to about 47.63 mm, before PCB-edge, seating and other assembly tolerances. Mated cable bodies and bend space are additional installation envelopes.

Six layers retain two GND references. Minimum copper width/clearance remains 0.127 mm. Ordinary vias are at least 0.45/0.20 mm, loaded vias use the reviewed 0.60/0.30 mm scheme, and both faces are tented. No manufacturing rule or drill was reduced to finish routing. All schematic values, numbered pin/net assignments, selected footprints, firmware files and project rules remain consistent with the paired source.

## Completed CAD checks

- Both native DRC modes: 0 opens, 0 geometric errors and 9 visible warnings
- Nine-sheet ERC: 0 violations
- Source parity: 156 parts, 506 numbered netted pad keys and 511 physical assigned pads; no value, footprint or pin/net mismatch
- All 323 via drills pass the actual expanded-mask spacing check
- All 18 scoped signal-clamp and feed-through polygon checks pass, including Port C and relocated CC1
- No newly unreferenced route copper or unchanged-route reference regression; independent cold refill is byte-identical
- Component/body, independent header-tail, USB-stake and fixed-fillet screens retain positive clearances under their documented assumptions

Port C now enters the actual active U15 clamp pads. R14 remains 5.1 kΩ/1%; its shorter CC1 route retires five obsolete tracks and two vias. USB data, CC2, HSE and VCAP geometry are preserved. Four short via-center connections make existing wide-copper junctions explicit without changing their conductive union, clearing all six off-center warnings. A front-layer raw-bus pour adds current/heat-spreading copper around the original 1.8 mm trunk while preserving all pre-existing tracks, holes and zone fills.

The nine remaining warnings are eight free-ended power/ground tracks and one CORE via. Eight of these nine items have operating-current or local copper-spreading fields in the reviewed cases. The PERIPH track `874efe98` is an unloaded retained obsolete tail, and is not claimed as useful current-carrying copper. These warnings do not identify unconnected signal nets. Individual geometry/electrical dispositions remain in the review evidence; none is suppressed. The final exact-board electrical analysis is complete; physical qualification remains separate.

## Completed electrical and export verification

The [exact-board electrical assessment](final-electrical-review.md) binds all three modeled scopes to the saved 4da0708a board. Classic DSM 20 mA retains 51.884243 mV RP3-H reserve, 8.269704 mV DSM reserve and 33.813007 mΩ worst VCAP copper against 35 mΩ under the stated assumptions. The separate nominal DSM 0.5 A screen reaches 3.009775088 V at the DSM pad and is not a 3.3 V ±5% guarantee.

The specified same-BEC J6/J8 installation was solved with unequal positive/return paths, missing-feed cases and stated KST profiles. The selected factory Hobbywing plugs do not inherit a Harwin rating. Pulse/stall duration, hot contacts and copper, source sag and KST command-level compatibility remain physical qualification requirements. Neither the SBEC's 30 A peak label nor this analysis creates a 30 A board rating.

Manufacturing export verification is complete: 13 Gerbers plus job, separate plated/nonplated drill data and maps, 151 populated BOM references, 144 SMT placements, seven manual/THT headers and five excluded bare test pads. Native coordinate/rotation data were preserved. Factory CAM, supply/assembly acceptance, placement preview and first-article tests remain required. The status is **verified prototype files for CAM/assembly review**, not production or flight qualification.

## Specified installation

Use the documented Hobbywing Platinum HV 200A **SBEC V4.1** arrangement with three KST BLS815 cyclic servos and one BLS805X **or** BLS905X tail servo. The nominal engineering setting is 7.4 V; 8 V is also within the selected servos' published range. Do not apply the controller's broader 5–12.6 V boundary directly to these 6–8.4 V servos. Sustained 15 V is outside the selected input-protection part's recommended operating range.

The throttle lead uses J6: black to pin 1/GND, red to pin 2/raw BEC and white to pin 3/ESC signal. When SBUS is unused, the auxiliary BEC lead can use J8: brown to pin 1/GND, red to pin 2/raw BEC and its signal cavity empty. Verify colored conductors and actual mating orientation before connection. Both leads originate from the same SBEC; this is not permission to parallel unrelated supplies. J8 remains the original SBUS resource when used for signals.

The BEC's 10 A continuous/30 A peak specification is not a PCB, contact or harness rating and does not specify a peak duration. Actual dual-feed sharing is unequal and depends on both positive and return impedances. Use the exact-board electrical review and physical load/temperature testing for the installation boundary.

The preserved firmware configuration places cyclic outputs on TIM3, tail on TIM2, ESC on TIM4 and RPM input on TIM5. Configure cyclic pulses for the selected BLS815 version (1520 µs/333 Hz) and tail for 760 µs/560 Hz. No firmware was flashed. Published servo command-level limits must be checked against measured output levels at load/temperature extremes; nominal 3.3 V signaling alone is not a worst-corner input-threshold guarantee.

USB is for prototype configuration with external loads disconnected. BEC supplies receivers and servos.

## Factory and assembly acceptance

Specify JLC06101H-3313 or an explicitly reviewed equivalent production stackup: nominal 1.03 mm ±10%, 1 oz outer/0.5 oz inner, NP-155F. Resolve the documented central-prepreg calculator/drawing discrepancy with CAM; preserve the reviewed outer reference/USB geometry and rules. The CAD thickness is 1.0324 mm, not an exact finished-board promise.

Use the exact GCT USB4145-03-0170-C stake variant. Confirm plated shell slots, locating holes, solder retention and underside fillet clearance; remove the temporary pickup cap. Do not substitute the former horizontal USB footprint or another stake length.

Retain the present nominal servo-header spacing. The complete fixed-land audit records positive clearances after 0.15 mm reserves on both neighboring lands, including smaller residuals on densely placed components. These are explicit controlled-soldering/inspection conditions, not hidden collisions. Actual KST and Hobbywing plug housings, full seating, removal access, polarity and retention require first-article inspection where manufacturer dimensions are unpublished. The earlier ±2° Harwin sensitivity is not an assertion about the actual selected harness or a mandatory assembly tolerance.

R23/R24 fillet residuals are 0.110 mm; R38 is 0.120 mm. R14's guarded body separation from D5 is 0.085151 mm, its nearest actual drill-to-mask gap is 0.205149 mm, and R38 copper-to-edge is 0.270 mm. C57/C51 stay in their original valid poses because the proposed optional shifts would violate an existing courtyard or mask constraint. No such constraint was relaxed.

R31 uses the reviewed YAGEO AC0201FR-0722RL 0201 resistor: 22 Ω/1%, 50 mW. Confirm the stated small-package assembly process. R16 requires exact Panasonic ERJ3RSFR12V supply or a separately reviewed replacement; current assembly availability is not established. The seven Samtec headers require separate procurement/THT assembly handling. Verify factory placement-preview rotations and sides, especially the IMU, U15, USB and connectors; no unverified library rotation correction is implied by native CPL export.

## Physical qualification after assembly

Before any flight use, perform unloaded bring-up with motors disconnected, then controlled source/load tests. Confirm rail voltage/ripple, USB startup and current-limit recovery, source handover/backfeed, dual-BEC-feed voltage/current sharing and contact/PCB temperatures. Exercise the specified servo set with realistic synchronized movement and bounded fault/transient cases; the manufacturer curves are not guaranteed stall-current envelopes.

Verify the installed VCAP resistor/capacitor/copper impedance and regulator stability, sensor supply ramp, gyro orientation/noise, barometer/flash operation, receiver binding/failsafe, PWM timing/levels and motor/RPM functions. Existing buried copper under the IMU remains a documented layout-guidance qualification item. ESD, vibration, harness retention and final mechanical fit require assembled tests. These physical tests are distinct from fabrication-file correctness and are not claimed complete by DRC/ERC.
