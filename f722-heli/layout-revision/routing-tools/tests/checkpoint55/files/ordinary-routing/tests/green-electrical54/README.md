# GREEN source54 conditional electrical review

The 66.981610 mm GREEN recipe merits a conditional prototype screen; length alone supplies neither a rejection threshold nor acceptance. Its nominal trace resistance is negligible compared with R10. The unresolved checks are the restricted PC14 load/current conditions, actual switching edges, and the completed route's return geometry. This review constructs no board, refills no zones, and makes no accepted-route or hardware-qualification claim. Accepted candidate54 still has 14 opens; the isolated recipe is not that native board.

## Bound topology and stock firmware

Candidate54 native parity establishes +3V3_CORE → R10.1 → R10 (2.2 kΩ, ±1%, UNI-ROYAL 0402WGF2201TCE) → R10.2/D1.2 (D1_A) → D1 (KENTO KT-0603YG, C2289) → D1.1 (cathode, LED_GREEN_K) → U1.3/PC14. A low output lights GREEN by sinking current. R10 is at the LED/anode end; it is not series termination between the GPIO and this long cathode trace.

Restricted group: PC13/U1.2 is physically unconnected and has no C13 resource in the pinned configuration; PC14/U1.3 is GREEN/LED resource 1; PC15/U1.4 is RED/LED resource 2, with the analogous +3V3_CORE → R11 (2.2 kΩ, ±1%) → D2 → PC15 circuit. PI8 is absent from this LQFP64 package. PC13 runtime mode was not read.

The [Nexus target](https://github.com/rotorflight/rotorflight-targets/blob/1d9cb4dc6f85c7895c2b089f4b8aa776ca3d3bd3/configs/RDMS-NEXUS_F7.config#L33) is pinned to commit 1d9cb4dc6f85c7895c2b089f4b8aa776ca3d3bd3. At firmware ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94, [light_led.c](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/light_led.c#L65) uses IOCFG_OUT_PP for each status LED. The retained io.h/io.c and HAL/LL definitions resolve it to GPIO output push-pull, no pull, GPIO_SPEED_FREQ_LOW / OSPEEDR00. Default inversion is zero absent LED*_INVERTED build macros, and the target makes no inversion override; ledSet then writes LOW for ON. Source behavior does not verify the installed binary, build flags, inversion setting, resource map, or registers. This initialization path does not establish a maximum LED toggle frequency.

## DC current and the special-pin restriction

[ST DS11853 Rev 9](https://www.st.com/resource/en/datasheet/stm32f722re.pdf#page=80), Table 10 note 2, describes a common power switch limited to 3 mA, requires output operation at no more than 2 MHz/30 pF, and disallows LED current sourcing. Page 145 states ±3 mA capability for these special GPIOs. [RM0431 Rev 4](https://www.st.com/resource/en/reference_manual/rm0431-stm32f72xxx-and-stm32f73xxx-advanced-armbased-32bit-mcus-stmicroelectronics.pdf#page=99) repeats the switch restriction. Neither cited passage supplies a separate, unambiguous combined-sink table. Screening the group's simultaneous current against 3 mA is a conservative interpretation, not a newly asserted manufacturer per-group specification. The existing LEDs sink DC current, consistent with the direction restriction.

For GREEN, I = (VCORE − Vf − VOL)/(R10 + Rtrace). At 3.6 V, R10 minimum 2178 Ω, and nonnegative LED/GPIO drops, the resistor-only DC bound is 1.653 mA. At an illustrative 3.3 V, Vf=2.0 V and VOL=0, current is 0.591 mA. The [BOM-linked KENTO sheet](https://datasheet.lcsc.com/datasheet/pdf/26e5131f4b051119ebc8b24acf5eb4fa.pdf?productCode=C2289), Rev A.0, 2018-12-06, p3, gives Vf=1.8–2.4 V at 10 mA, not the sub-mA operating point; p4 voltage bins use 20 mA. Neither is a guaranteed low-current Vf curve. Brightness and exact operating current remain unmeasured.

Both existing LEDs, simultaneously ON, have a deliberately loose 3.306 mA combined bound if Vf and VOL are discarded. This is not an observed overcurrent. At minimum resistance, a combined sum of the two Vf+VOL drops of at least 0.666 V would put static current at or below 3 mA; actual low-current/temperature evidence and switching loads must close the conservative group screen.

Unadopted resistor-pair options, both at ±1% and 3.6 V with zero LED/GPIO drop:

| Each of R10/R11 | Combined DC bound | Margin to 3 mA | Current versus 2.2 kΩ, same Vf/VOL |
|---|---:|---:|---:|
| 2.49 kΩ | 2.921 mA | 0.079 mA | 88.4% |
| 2.7 kΩ | 2.694 mA | 0.306 mA | 81.5% |

These cap that static resistor-only sum, with reduced LED current and likely brightness. They change BOM values and need a brightness check; neither was adopted. They do not bound capacitive edge current, establish the manufacturer's intended combined-current interpretation, or solve the 30 pF/return question.

## Actual layers and conditional loading scale

All four route legs are 0.127 mm wide. The replay script checks their real pad endpoints, shared via coordinates and geometric lengths against the source54 native parity. Three vias connect the legs. The source-board/recipe hashes are in arithmetic.json and source-index.json.

| Layer | Track length | Copper thickness | Intended adjacent reference |
|---|---:|---:|---|
| B.Cu | 9.429480 mm | 0.035 mm | In4, 0.0994 mm dielectric, εr=4.1 |
| In3.Cu | 29.927193 mm | 0.0152 mm | In4 near, In1 farther |
| In2.Cu | 20.690158 mm | 0.0152 mm | In1 near, In4 farther |
| F.Cu | 6.934778 mm | 0.035 mm | In1, 0.0994 mm dielectric, εr=4.1 |

The inner near-plane gap is 0.25 mm/εr=4.23. The farther gap is 0.468 mm, traversing 0.2028 mm/εr=4.4, the opposite signal-layer level (0.0152 mm), and 0.25 mm/εr=4.23. The actual inner geometry is asymmetric and has neighboring signals.

Using [ADI MT-094](https://www.analog.com/media/en/training-seminars/tutorials/mt-094.pdf), equations 4/8, outer microstrip gives 0.099 pF/mm. Replacing the actual inner geometry with two symmetric sensitivity cases (both planes 0.468 mm away, εr=4.23; both 0.25 mm away, εr=4.4) gives about 6.0–7.5 pF for the complete trace alone. These ideal continuous-plane cases give a scale, not a measured or rigorous total-load interval. They omit native plane gaps, neighboring copper, mask, vias, pads, package, LED charge/capacitance and probe load. The LED sheet supplies no capacitance value. Therefore this estimate does not prove compliance with 30 pF. Treat 30 pF as an external-load budget, and include die/package terms consistently in any simulation rather than double-counting them.

At nominal copper thickness and assumed bulk-copper resistivity at 20°C, track resistance is 0.516 Ω, or 0.85 mV at the 1.653 mA bound, excluding vias/temperature/tolerance. Conditional uniform-line flight time is about 0.44 ns one-way, excluding transitions and return detours. These calculations are not native extraction.

## Edge, return and bench checks

The correct saved [ST IBIS](https://www.st.com/resource/en/ibis_model/stm32f7_ibis.zip) pin-3 selector is io8p_arwsudq_ft_v33; LOW/no-pull selects io8p00_arwsudq_ft_v33. The selected-model excerpt records C_comp≈2.83–2.98 pF and pin-package R/L/C. Its fast-corner ramp denominators are 10.37 ns rising and 11.30 ns falling, for specified voltage increments and a 50 Ω fixture. They are simulation-only ramp data, not guaranteed fastest installed-board 10–90% transitions. A 2 MHz repetition limit and the generic LOW-speed maximum rise/fall time do not prove slow edges.

Before adoption, construct the exact coordinated native candidate and refill; verify DRC, connectivity and undisturbed neighboring routes. Check the whole trace width against actual connected In1/In4 ground, including every aperture and via antipad. B→In3 and In2→F retain the nearest reference family; the middle In3→In2 transition changes nearest planes, so inspect the local ground stitching/return-transfer path. Confirm MCU ground and CORE decoupling close the LED supply/current loop. A DC-connected plane or visual overlap alone does not establish the high-frequency return impedance. Review coupling along nearby UART/servo/flash/analog runs and regulator areas in the final composition.

On a current-limited prototype with motors disconnected, record PC14/PC15 mode/speed/inversion and supply, measure both LED currents together over intended supply/temperature, then probe PC14 and the LED cathode using characterized low-capacitance probes. Check fastest startup/normal/fault transitions, overshoot/undershoot, ringing, unwanted LED activity and coupled disturbance while flash/UART/servo/regulator activity runs. Include probe capacitance in the load budget. No load, edge, EMI or return pass is claimed here.

Reproduce arithmetic with `python ordinary-routing/tests/green-electrical54/calculate_review.py` from the workspace root. Only this review directory was written.
