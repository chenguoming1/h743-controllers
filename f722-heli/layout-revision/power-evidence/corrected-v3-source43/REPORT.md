# Candidate43 corrected conditional power result

The corrected source43 run completed in 1,377.690855 seconds with a recorded peak RSS of 2,002,223,104 bytes. All 294 required conditional cases, five VCAP DC copper loops and declared numerical guards pass. The overall runner result remains false, with exit code 1, because one separate lost-feed illustration fails four servo pad floors.

This applies only to board SHA-256 `1ee7174a578dffe4d5ef3ae8b39d8dc88f28b80395539263a65f23be234c21e6`, candidate43 with 37 ordinary opens. The newer accepted candidate44/35 has changed BEC copper and vias and is not qualified by this run.

## Actual supply windows

Voltages are physical p−n pad differences, with local returns, across both grids. BEC minima below combine the 252 required classic/capacity cases; USB minima cover 42 required configuration cases. Four MCU VDD pads use the pinned 216 MHz, scale 1, overdrive, 7 wait-state mode with a 2.7 V floor for BEC. USB uses 3.0 V for full FS electrical specifications. VDDA uses a conservative 2.7/3.0 V screen only. All upper bounds are 3.6 V. These are scalar DC screens, not guarantees of analog tracking or full device operation.

| Supply | Physical p−n | BEC floor / observed min V | USB floor / observed min V |
|---|---|---:|---:|
| analog | U1.13 − U1.12 | 2.70 / 3.113687 | 3.00 / 3.128744 |
| barometer_vdd | U4.8 − U4.7 | 1.70 / 3.131300 | 1.70 / 3.161392 |
| barometer_vddio | U4.6 − U4.1 | 1.20 / 3.131863 | 1.20 / 3.160642 |
| flash | U3.8 − U3.4 | 2.70 / 3.098176 | 2.70 / 3.127311 |
| imu_vdd | U2.8 − U2.6 | 1.71 / 3.120157 | 1.71 / 3.146014 |
| imu_vddio | U2.5 − U2.6 | 1.71 / 3.121323 | 1.71 / 3.147179 |
| mcu_vdd19 | U1.19 − U1.18 | 2.70 / 3.133788 | 3.00 / 3.149178 |
| mcu_vdd32 | U1.32 − U1.31 | 2.70 / 3.150813 | 3.00 / 3.165600 |
| mcu_vdd48 | U1.48 − U1.47 | 2.70 / 3.138742 | 3.00 / 3.165257 |
| mcu_vdd64 | U1.64 − U1.63 | 2.70 / 3.109895 | 3.00 / 3.146495 |

The strict actual-sink report contains 6,100 rows (ten supplies × 305 cases × two grids), with zero window failures and zero two-grid failures. The compact JSON retains each scope/sink minimum and maximum, their exact case and grid, operating mode, pad pair and worst window margin. VBAT and CSB remain separate role observations, not supply-current injection terminals. U10/U11 power current enters IN6; EN4 is a separate control probe.

## Preserved failed illustration

`same_BEC_all_cyclic_905X_J6_feed_lost_capacity__sample_mcu_vdd19` draws 18.560272018 A through the remaining J8 feed at the fine grid. The 7.4 V same-BEC illustrations include loads beyond stated continuous capability without assigning a duration. They are not required operating envelopes. Fine-grid servo board-pad values are:

| Pad | Voltage V | Floor V | Result |
|---|---:|---:|---|
| J2_servo_board_pad | 5.864616350 | 6.0 | FAIL |
| J3_servo_board_pad | 5.866825367 | 6.0 | FAIL |
| J4_servo_board_pad | 5.871552140 | 6.0 | FAIL |
| J5_servo_board_pad | 5.879248902 | 6.0 | FAIL |

These are four distinct failed floor checks, observed on both grids. Unmeasured downstream servo harness/contact loss means passing a board-pad window would still not establish voltage at the servo. All eleven illustrative results remain available in the compact JSON and exact combined summary.

## Material, electrical and numerical bounds

The fixed DC model uses 105 °C copper, 15 µm copper thickness and via plating, and 95% IACS conductivity. This is a copper-temperature assumption, not ambient or allowed component body temperature. The two grids are 0.12/0.09 mm; impedance tolerance is max(2.5%, 0.1 mΩ), and voltage sensitivity is limited to 1 mV with locked margin guards. Two-grid sensitivity is not a rigorous discretization or manufacturing bound.

The inherited electronics aggregate is 0.32 A for BEC or 0.30 A for USB. Each filtered branch is limited to 20 mA, and IMU VDD plus VDDIO together are limited to 20 mA. FB1/FB2 series resistance uses a conditional 1 Ω hot-bead bound. These are project engineering test bounds; the hot DCR and branch-current bounds require bench evidence. The 42 allocations per context give six BEC contexts and one USB context, totaling 294 required vertices. Vertex coverage proves the declared current polytope, not all nonlinear interior voltage extrema of the conserved-power converter model.

The 15 networks have 107 finite contacts, including 41 ground contacts. The five VCAP loops screen the sum of copper and barrel leg resistance against 35 mΩ, excluding R16, capacitor ESR, inductance, startup and AC stability.

| VCAP loop | Fine-grid resistance mΩ | Limit mΩ |
|---|---:|---:|
| VCAP_copper_to_U1.12 | 19.001530 | 35 |
| VCAP_copper_to_U1.18 | 18.508345 | 35 |
| VCAP_copper_to_U1.31 | 23.558866 | 35 |
| VCAP_copper_to_U1.47 | 26.049067 | 35 |
| VCAP_copper_to_U1.63 | 25.042475 | 35 |

All 15 network impedance guards and all 4,750 declared voltage-grid guards are complete; the maximum voltage-grid change is 0.576051 mV. The four failed threshold margins remain failures. The largest condensed mesh has 286,396 equations and 1,099,202 triangles. Maximum field KCL residual is 2.851 nA; maximum linear residual/required ratio is 0.9912. Raw detail and exact values are preserved by identity, not repeated here. Caps stayed at 1,500 s, 4,096 MiB, one numerical thread, with the original outer 1,530 s watchdog. No grids, thresholds, resource limits or failed decisions were relaxed.

## What remains unqualified

- VDDA-to-VDD tracking and ADC accuracy remain separate. No 300 mV steady-state tracking allowance is asserted. Device supply-floor passes do not establish clock, GPIO or peripheral electrical requirements.
- Actual package/exposed-pad current sharing is unverified. Finite lands/annuli omit within-land, pin, solder and contact heating. Idealized internal package ground behavior and local return choices remain model limits.
- U11 quiescent/enable and other CORE bias are included once in the aggregate; their individual injection locations/current distribution are not separately resolved. The TI 140 µA reference at 6.5 V/open OUT/20 kΩ ILIM and EN-current test at 0/6.5 V do not establish a guaranteed 3.3 V bound. U10's explicit 140 µA IN6/GND5 screen retains its inherited condition caveat. No auxiliary 2 mA sensitivity slices were run.
- The DSM 0.50 A capacity case does not inherit classic 20 mA receiver accuracy. USB configuration disconnects external loads, and U9's 3 V operating input minimum does not establish its separate 4.3 V accuracy conditions. Real harnesses and contacts require measurement.
- I2C support-chain continuity evidence does not validate edge rate, rise/fall time, bus capacitance, pullups, logic levels, EMI or full I2C signal integrity.
- No startup, reverse blocking, handover, USB coexistence, ESD, switching ripple, VCAP AC stability, thermal/ampacity, KST signal-level, bench, production or flight qualification follows. Component temperature limits, including X5R and servo limits, remain separate.
- Thirty-seven ordinary opens remain outside this source's power scope. Candidate44's later BEC bend and via changes require fresh assessment and source binding; geometric equivalence is not a substituted numerical result.
- The historical EN4 and barometer CSB/SDO power-terminal results remain invalid for USB/DSM path-specific claims. Historical 146/140/5,532 postprocessing is disabled and was not regenerated.

## Review and reproducibility status

The independent completed review verified plan/source/stage/launch/freeze/ledger/runtime identities, verified 610 case identities against the hash-checked ledger definitions, 9,500 acceptance p−n/window checks, 6,448 report-only p−n checks, 4,750 voltage guards, 15 impedance guards and five VCAP guards. It checked 6,542 loaded fields and 36,432 geometry references; the reconstructed actual-sink report matched the exact saved summary. Its original execution records and verifier are in `independent-review/`. The review was performed while canonical equaled source43; its canonical-equality guard now intentionally refuses the advanced board.

Package verification checks the entire portable payload and regenerates compact evidence from the exact saved summary. The mesh-free preflight verifies portable input completeness. This packaging work did not rerun numerical analysis or repeat raw-result diagnostics. Lossless recovery was verified by streamed decompression SHA-256. Raw-result summary replay is an explicit optional verifier mode and is not implied by compact-report regeneration. See README for commands and gaps in the original launcher/binary environment portability.
