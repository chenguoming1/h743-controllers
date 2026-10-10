# SERVO1 candidate04: conditional geometric checkpoint

Board SHA-256 `755545e8198e9a3649c0e07533c23e67010d91ab6a8b09556d7463e064ac89eb` reconstructs SERVO1 on source17 `71d33748909bb960c5829973642272460607d8521831a6212975f7de6790d660`. Native result is 15 opens, zero errors and zero warnings. This is a complete geometric routing checkpoint. Waveform, ESD transient, AC return and loaded-power qualification remain open.

## Actual topology and complete path accounting

The output order is U1.56/PB4 → SERVO1_MCU → bonded U12.1 → SERVO1_MCU → R20.2 → R20 → R20.1/SERVO1_EXT → J2.3 → unspecified cable and servo input. Native R20 is 470 Ω, 1%, 0.20 W; U12 is USBLC6-4SC6, with pin5 on CORE and pin2 on GND. The actual U12.1 pad cut separates source and target with 0.143294148 mm remaining gap. It adds the nineteenth passing actual I/O contract out of 22 and preserves every earlier pass. This geometric cut does not simulate ESD.

| Branch | Historical hardware `4da0708a…` | Candidate04 |
|---|---:|---:|
| MCU → clamp | 17.485112 mm, 2 vias | 18.058336 mm drawn branch inventory, 2 vias |
| Clamp → R20 | 83.016702 mm, 3 vias | 25.599422 mm, 3 vias |
| R20 → J2.3 | 10.188270 mm, 2 vias | 1.228270 mm, zero vias |

Candidate04 has 44.120258 mm total protected-net track. This consists of the two branch inventories above plus 0.462500 mm of copper entirely inside U12.1. The MCU branch endpoint graph reports 17.283336 mm because a redundant 0.775000 mm centerline lies entirely in U1.56. The latter's round endpoint extends beyond the land at the adjoining track; its exact copper difference from the other same-net copper is retained as 0.000000027166712 mm² in `pad-entry-topology.json`, without rounding it to zero. Neither pad-contained centerline is an extra remote stub. Through-via unused barrel sections remain and are not modeled electrically. `servo1-path-comparison.json` retains each branch's track and via inventory and the independent actual-pad-cut object partition.

The protected route is substantially shorter overall than the historical 100.501814 mm. The MCU-to-clamp branch inventory is 0.573225 mm longer, with the same two transitions. The historical layout is a comparison, not evidence of adequacy. R20 is beyond both routed branches, about 43.66 mm from the MCU by drawn branch inventory, so it is not driver-end source termination. PWM repetition rate alone cannot establish edge or reflection margin.

## Pinned output and loading evidence

The pinned [NEXUS target](https://github.com/rotorflight/rotorflight-targets/blob/1d9cb4dc6f85c7895c2b089f4b8aa776ca3d3bd3/configs/RDMS-NEXUS_F7.config) assigns SERVO1 to PB4. Saved [firmware source](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/flight/servos.c), its I/O definitions and PWM setup establish alternate-function push-pull, no pull, GPIO_SPEED_FREQ_LOW / OSPEEDR00. This binds source behavior, not installed binary or register readback.

[STM32F722 DS11853 Rev9](https://www.st.com/resource/en/datasheet/stm32f722re.pdf), table63, specifies a 100 ns maximum rise/fall time at LOW speed, 50 pF and VDD1.7–3.6 V, guaranteed by design. There is no guaranteed minimum edge time. The maximum is not a lower bound for reflection assessment.

The retained [ST IBIS](https://www.st.com/resource/en/ibis_model/stm32f7_ibis.zip) pin56/PB4 selects `io8p_arsudq_ft`; LOW/no-pull selects `io8p00_arsudq_ft`. The exact package pin parameters are 0.049290 Ω, 2.180 nH and 0.020000 pF. The model is based on ST ELDO simulation and is not guaranteed. Its strong-corner 50 Ω fixture ramps are 10.32996 ns rising and 11.43308 ns falling; these are neither measured board edges nor guaranteed minima. Model C_comp is 2.2921 pF typical. The full model, exact pin line, corner conditions and source hashes are retained in `electrical-evidence.json`.

[USBLC6-4 Rev7](https://www.st.com/resource/en/datasheet/usblc6-4.pdf) gives I/O-to-GND capacitance 3 pF typical / 4 pF maximum and mutual I/O capacitance 1.85 pF typical / 2.7 pF maximum at VR1.65 V and25°C. This is not a constant capacitance over all bias and swing. Trace/via loading, other protected-channel activity and the unknown receiver/cable must also be included for an actual waveform assessment.

For uniform assumed effective permittivity2.8–4.4, the 18.058336 mm MCU branch gives about0.101–0.126 ns one-way delay and0.202–0.253 ns round trip. The fixture ramps support a slow-edge working hypothesis relative to this sensitivity range, not a guaranteed threshold, overshoot, monotonicity or settling margin. No field solve, board/cable waveform simulation or ESD analysis has been performed; package and vertical-barrel delay are omitted.

## Saved reference and process evidence

In1.GND references F/In2; In4.GND references B/In3. SERVO1 has 3.533594769 mm missing centerline, all in own-via windows. Trace-width missing area is0.510238598208 mm²; exactly four fragments totaling0.000134787127 mm² remain outside those windows. They sit in saved merged TAIL/BARO via, connector/TAIL_EXT and connector/SERVO1 voids. Exact polygons, hole membership, bounds and nearby plated-pad inventory are retained in `../signal-geometry-details.json`. No snapping, normalization or small-area suppression was applied. Window labels are not electrical waivers.

All116 GND plated ties have positive contact to both saved planes. Nearest such ties to the five SERVO1 transitions are1.1631 mm at(10.307854,12.958635),1.5970 mm at(10.8,13.29),2.3299 mm at(9.873437,7.809795),1.2540 mm at(12.404558,2.505690), and2.0541 mm at(21.48,14.47). These distances and saved DC connectivity do not establish AC return inductance.

ADC_BUS, ADC_DIV_MID and TAIL copper and reference totals remain exact source17. Critical copper and centerline missing geometries remain exact; USB_N retains a raw +0.000000000263765 mm² trace-width difference wholly inside unchanged own-via windows and actual saved-hole/window intersections. The separate exact classifier retains the region and reports zero containment disagreements. Existing RPM_LV outside-window centerline gap0.706370466 mm is unchanged, not waived. All six new ordinary tented0.45/0.20 mm vias satisfy native mask/drill/copper/edge rules; the smallest measured surplus over any relevant minimum is0.012089922 mm.

The complete native transaction passes finite entries for136 endpoints and six vias, all28 support partitions, mechanical/pose/process/schematic/firmware gates and all16 critical nets. R50 is the only footprint move, +0.25 mm inward at unchanged orientation. See `../conditional-support-review/NATIVE-SUPPORT-REVIEW.md` for the explicit shared U12/eFuse-control return risk. No current numeric power or VCAP qualification is claimed.
