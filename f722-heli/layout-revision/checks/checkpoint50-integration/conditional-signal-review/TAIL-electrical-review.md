# TAIL complete routing checkpoint: conditional electrical assessment

Candidate03 is suitable for owner review as a **geometric prototype checkpoint**, with electrical, protection-transient and loaded-power qualification still open. It closes the actual R23.2–U12.6–U1.55 tree using ordinary copper and five new tented vias, while retaining all 156 source49 footprint poses. No evidence presently establishes that structural shortening is mandatory, and no result here guarantees the 81 mm branch's waveform. The source-bound board SHA256 is `cbb9a1f0b43dc612718baf1277302c9ac0767474cc7fa13f5d8c0a2428f2b787`.

## Actual topology and historical comparison

The output order is U1.55/PB3 → TAIL_MCU → U12.6 bonded I/O pad → TAIL_MCU → R23.2 → 470 Ω R23 → R23.1/TAIL_EXT → J5.3 → unspecified cable and servo input. U12 is USBLC6-4SC6; its pin5 is +3V3_CORE and pin2 is GND. Both branches enter the actual pin6 copper. Removing that copper separates R23 from U1, with a 0.371503028 mm remaining branch gap. This is a physical path test, not an ESD-transient test.

| Saved board | MCU to clamp | Clamp to R23 | R23 to J5.3 | Total TAIL_MCU copper |
|---|---:|---:|---:|---:|
| Historical hardware `4da0708a…` | 8.565645 mm; 1 via | 93.071223 mm; 6 vias | 10.571589 mm; no via | 101.636867 mm |
| Candidate03 | 81.063747 mm; 4 vias | 4.612500 mm; no via | 12.911903 mm; 1 via | 85.676247 mm |

The protected net shortens overall, while the clamp moves much farther from the driver electrically. Both facts matter: the original board is a historical layout baseline, not proof of either layout's adequacy. The endpoint graph and independent actual-pad-cut object inventories agree; neither MCU-side branch contains an extra track stub. Four new through-vias still have unused barrel sections, which were not modeled as transmission-line stubs.

Candidate03's MCU-to-clamp path comprises 4.747906 mm B.Cu, 64.928038 mm In2.Cu, 9.461116 mm In3.Cu and 1.926687 mm F.Cu. The two complete inner paths to the clamp-side via require the far portals at (20.469046,24.065218) and (29.758523,22.999941). The earlier “29.8” referred to a portal x coordinate, not a demonstrated 29.8 mm complete route. No shorter complete alternative has been demonstrated. The attempted smaller SERVO2/RPM reconstruction remains a separate incomplete diagnostic.

R23 is 470 Ω, 1%, 0.20 W and lies beyond the clamp, approximately 85.68 mm of track from the MCU. It can isolate external load current and cable capacitance, but it is **not a driver-end source termination** for the long MCU-to-clamp branch. A PWM repetition rate alone does not assess reflections from a GPIO edge.

## Pinned firmware and manufacturer evidence

The pinned [NEXUS target configuration](https://github.com/rotorflight/rotorflight-targets/blob/1d9cb4dc6f85c7895c2b089f4b8aa776ca3d3bd3/configs/RDMS-NEXUS_F7.config) assigns SERVO4 to PB3 and AF1. At firmware commit `ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94`, [servoInit](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/flight/servos.c) configures IOCFG_AF_PP. The [F7 I/O definitions](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/io.h) and LL initialization resolve this to alternate-function push-pull, no pull, GPIO_SPEED_FREQ_LOW, OSPEEDR=00. The subsequent PWM setup changes timer output parameters without raising GPIO speed. This establishes pinned-source behavior; no installed binary or register readback was inspected.

[STM32F722 DS11853 Rev9](https://www.st.com/resource/en/datasheet/stm32f722re.pdf), table63, gives a 100 ns maximum rise/fall time for OSPEEDR=00, CL=50 pF and VDD=1.7–3.6 V, guaranteed by design. It specifies no minimum rise/fall time. The maximum cannot be used as a guaranteed minimum edge time for a reflection argument.

ST's official [STM32F7 IBIS archive](https://www.st.com/resource/en/ibis_model/stm32f7_ibis.zip), package3.0, contains `stm32f7x2_lqfp64.ibs`, revision1.1 dated2016-12-21. Pin55/PB3 selects `io8p_arsudq_ft`; SPEED00 with no pull selects `io8p00_arsudq_ft`. The model originates from ST ELDO simulation and explicitly is not guaranteed. Its 50 Ω ramp fixture entries are:

| Model corner | VDD / temperature | Rising dV / dt | Falling dV / dt |
|---|---|---|---|
| Typical | 3.3 V / 25 °C | 1.27740 V / 19.68906 ns | 1.30734 V / 18.58362 ns |
| Weak | 2.7 V / 125 °C | 0.81540 V / 50.98348 ns | 0.78450 V / 39.11759 ns |
| Strong | 3.6 V / −40 °C | 1.56732 V / 10.32996 ns | 1.58789 V / 11.43308 ns |

These fixture ramp times support a slow-edge working hypothesis. They are neither measured edges on this board nor a lower-bound timing guarantee. Package pin55 model values are 0.049692 Ω, 2.222 nH and 0.022041 pF; typical die C_comp is2.2921 pF. These are model parameters, not a replacement for a distributed board/cable analysis.

[USBLC6-4 DocID11068 Rev7](https://www.st.com/resource/en/datasheet/usblc6-4.pdf), table2, specifies I/O-to-GND capacitance3 pF typical/4 pF maximum, and I/O-to-I/O1.85 pF typical/2.7 pF maximum, at VR=1.65 V and25 °C. The complete load also depends on other protected-channel bias/activity, trace/via capacitance and external load. A constant4 pF shunt across the full signal swing would be an assumption. The actual servo receiver, its input thresholds/capacitance, cable length/impedance and installed settings are unknown. No receiver part or timing requirement is invented here.

## Propagation and reference sensitivity

Uniform effective-permittivity scenarios2.8,4.1 and4.4 give81.064 mm one-way delays0.4525,0.5475 and0.5672 ns; corresponding round trips are0.9049–1.1344 ns. These are sensitivity arithmetic, not a field solve. The saved stackup contains4.1/4.23/4.4 dielectric values and a1.0324 mm board thickness, but manufacturing confirmation and dielectric tolerances are absent. Package delay, vertical via delay, mutual coupling and via stubs are excluded from those numbers. The strong-corner IBIS ramp times are substantially longer than these nominal flight times, which supports retaining the route for prototype review; it does not prove overshoot, monotonicity, threshold-crossing or settling margins.

Saved-fill projection uses In1.GND for F/In2 and In4.GND for B/In3. TAIL_MCU has2.823918628 mm of missing centerline, all within explicitly bounded own-via windows. Its full trace-width projection has0.408604820 mm² missing, of which0.000224846616 mm² remains outside those windows:

| Exact residual area | Location | Classification |
|---:|---|---|
| 0.000066056367 mm² | near(9.44,2.16) | Edge of J2.3/SERVO1_EXT plated-pad antipad |
| 0.000002216026 mm² | near(18.405,24.447) | Merged DSM_RX_MCU and +3V3_DSM via void |
| 0.000156574223 mm² | near(22.20,15.53) | Merged TAIL/BARO_SCL via hole, beyond TAIL's local window |

Exact polygons, bounds and identities are retained in `signal-geometry-details.json`. They were not snapped, normalized, repaired or hidden by a small-area threshold. Local-window labels are explanations, not electrical waivers. All GND pad groups remain one connected native group. There are117 plated ties with positive saved-zone contact to both reference planes. The nearest such GND vias to the four TAIL transitions are2.2450 mm at the MCU B/In2 transition,0.5945 mm at the left In2/In3 transition,2.9206 mm at the right In3/In2 transition and1.4171 mm at the clamp-side F/In2 transition. Both planes have proven DC connectivity; these distances do not qualify AC return inductance.

USB/HSE/IMU/BARO copper objects and reference metrics remain exact source49. The separate exact reference classifier confirms equality of missing centerline geometries with no containment-predicate discrepancy. Total saved GND area changes are retained in the comparison; there is no claim that the plane fill itself is unchanged.

## Process, support and decision limits

Native DRC is27 opens/0 errors/0 warnings, including the strict run. Process, mechanical, schematic parity, firmware mapping and all16 critical connectivity checks pass. Actual I/O pad cuts pass14/22, preserving every previous pass and adding TAIL. All58 new tracks have116 finite pad, track-junction or annular endpoints; all5 vias have at least two finite layer entries. Every affected support partition and completed SERVO2/3, RPM_LV, ADC_DIV_MID, ADC_BUS and PORT_A MCU path is restored.

The clamp-side via has0.285690 mm drill-to-SMT-mask clearance and0.160696 mm limiting copper clearance, exceeding the relevant0.20/0.127 mm limits by0.085690/0.033696 mm. Other new vias are all rule-clean; the smallest new-via copper excess is0.002730 mm at the MCU portal beside RPM_LV. These are drawn geometry margins, not manufacturing yield predictions. All new vias are ordinary0.45/0.20 mm through-vias, tented both faces.

CORE's replacement branch is8.867409 mm at0.20 mm width with one additional via, replacing2.951931 mm. An additional2.99 mm unchanged rail is represented by two tracks to make the finite-width join explicit, so the transaction inventory reads11.857409 mm added versus5.941931 mm removed. The branch feeds retained FB1.1/+3V3_CORE support; FB1.2/+3V3_ANALOG feeds U1.13 and C8/C9. U12.5 remains on the retained CORE rail. All support and ground connectivity is preserved, but fresh source-bound loaded DC/VCAP analysis is required.

Accepting this as a geometric checkpoint should retain explicit NOT_QUALIFIED waveform/protection/power status. Functional release needs either a validated distributed model using the actual driver, receiver, cable and fabrication stackup, or appropriate measurements of ringing, overshoot, repeated threshold crossings and settling at the MCU/clamp/connector across relevant operating conditions. The distant clamp also requires protection-transient assessment; an actual-pad-cut pass cannot establish ESD residual stress. No stock firmware speed change, added component or resistor change is assumed.

Reproduction and provenance: `electrical-evidence.json`, `fetched-source-index.json`, `tail-path-comparison.json`, `measure_tail_paths.py`, the preserved full ST IBIS source and selected-model excerpt. Historical failed moved/rotated R23 candidates remain distinct27/1 diagnostics; candidate03 restores the original pose.
