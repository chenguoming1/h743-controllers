## 2026-10-05 approved prototype update

U7 is now **TPS2117DRLR (JLC C22399676)**, pin/footprint-compatible with the earlier TPS2116 choice. C61 remains populated; **C75 GRM21BR61A476ME15L (C124129), 47 µF / 10 V / X5R / 0805**, is added on the peripheral mux output. The exact-source schematic, BOM identity and circuit manifest have been updated; PCB integration is still in progress.

The user approved USB for **configuration with external loads disconnected**, with BEC power for receivers and servos. Retain the existing USB current limiter. This scope does not establish full peripheral current from USB, seamless handover, a flight-qualified board, or guaranteed cold-start timing. Cold USB boot/current-limit recovery, sensor supply ramp, source handover, absent-host backfeed and loaded BEC response remain first-article acceptance gates. Start bring-up unloaded; any optional receiver or controlled load tests are qualification exercises, not expanded operating ratings.

The lower mux resistance improves the prior 105 °C engineering DC screen by approximately 54 mV at 2 A, but this must be recomputed on final integrated copper. RON's published test current is 200 mA; the 2 A budget is an explicit engineering extrapolation. X5R capacitor bodies must remain within their 85 °C rating.

Evidence: `validation/routing-45-tps2117-review/REPORT.md`, `PROTOTYPE-DECISION.md`, `application-check/REPORT.md`, `usb-load-refinement/REPORT.md`, and `source-adoption.json` in that review directory. Earlier TPS2116 analyses below are historical and must not be mistaken for the selected component.

# F722-HELI power implementation evidence

Research date: **2026-10-04 UTC**. Status: **engineering prototype proposal, not a fabrication or flight release**. This records an original circuit selected for the classic Nexus electrical envelope. It is not a recovered Nexus schematic and does not establish original-board USB behavior.

## 1. Chosen architecture and interface contract

The servo/BEC bus is a direct, appropriately rated copper passthrough. Do not regulate it and do not place the electronics eFuse in series with the servo connectors.

```text
VX_RAW (BEC / servo bus, 5–12.6 V)
  -> TPS259472ARPWR electronics branch -> VX_PROTECTED
       -> TPS63070RNMR -> +5V_BEC
            -> TPS2116 VIN1 ------> +5V_PERIPH (A/B/C shared 2 A)
       -> TPS2121 IN1 ------------> CORE_BUCK_IN
                                    -> TPS62162 -> +3V3_CORE
                                          -> TPS2553 -> +3V3_DSM (0.5 A load)
USB_VBUS_RAW -> TPS2553 -> USB_LIMITED
                            -> TPS2116 VIN2
                            -> TPS2121 IN2
```

| Net | Required meaning |
|---|---|
| `VX_RAW` | Common raw servo/BEC bus, 5–12.6 V in normal service; sensed by stock BEC ADC divider |
| `VX_PROTECTED` | Electronics-only reverse-blocking / voltage-clamping eFuse output |
| `USB_VBUS_RAW` | Connector VBUS; existing USB-page 1 µF counts toward total direct USB capacitance |
| `USB_LIMITED` | Single current-limited USB output, shared by both muxes |
| `+5V_BEC` | Dedicated ABC buck-boost output, nominally 5.088 V before mux |
| `+5V_PERIPH` | ABC connector supply after mux; stock `ADC_BUS` measures this rail |
| `CORE_BUCK_IN` | Selected wide-range BEC/USB input to main 3.3 V buck |
| `+3V3_CORE` | Main regulated 3.3 V; MCU, flash, sensors; IMU via its own ferrite |
| `+3V3_DSM` | Current-limited nominal 3.3 V receiver rail |

The stock firmware attenuation factors are **0.16 for BEC** and **0.32 for SYS/5 V**. Keep those ratios and existing GPIO assignments. The power implementation does not authorize changing bidirectional DShot or inserting one-way output buffers.

### Power budget and reason for splitting rails

- ABC: 5 V × 2 A = 10 W shared across A/B/C, available on BEC power
- Main/flash/sensor allowance: provisional 0.30 A at 3.3 V; DSM load: 0.50 A; total main-buck output budget: 0.80 A / 2.64 W
- One common 5 V converter would need `2 A + 2.64 W / (5 V × 0.85) = 2.621 A`. A TPS63070 advertised for 2 A is not the defensible choice for that combined load
- The split design leaves TPS63070 dedicated to the 2 A ABC demand and a 1 A TPS62162 for core + DSM
- At 5 V BEC and 90% conversion efficiency, input power is approximately 14.0 W / 2.8 A before small path losses. Confirm simultaneous full-load operation at the low-input corner
- STM32F722 ST table for all peripherals at 216 MHz includes 155.3 mA typical / 175.8 mA maximum at 85°C. The 0.30 A allowance is a design allocation, not a measured board current
- USB-only operation cannot provide full 2 A ABC + 0.5 A DSM ratings. It is a limited configuration/receiver-power mode, and excessive loads can brown out or current-limit
- JST GH is rated 1 A/contact at the specified AWG26 wire condition. The ABC 2 A specification is an aggregate across ports, not permission to draw 2 A through one GH power contact

## 2. Implementation tables

Component designators are intentionally not assigned here so the schematic owner can allocate them without collisions. All local bypass capacitors go to the common ground plane with short return paths. Unless separately qualified, retain reference capacitor populations and use X7R/X5R parts with adequate effective capacitance after DC bias. Ceramic size/value alone is not a capacitance guarantee.

### 2.1 TPS259472ARPWR electronics BEC eFuse

Source: [TI TPS25947 datasheet](https://www.ti.com/lit/ds/symlink/tps25947.pdf), Rev. C, May 2026; RPW0010A package drawing. Selected variant is **TPS259472A**, not a different clamp/shutdown option.

| Pin | Name | Connect to / implement |
|---:|---|---|
| 1 | EN/UVLO | `VX_RAW` through 1.5 MΩ; no divider in this proposal |
| 2 | OVCSEL | 390 kΩ to GND, selects nominal 13.8 V clamp |
| 3 | PG | NC when unused |
| 4 | PGTH | GND when PG monitoring is unused |
| 5 | IN | `VX_RAW` |
| 6 | OUT | `VX_PROTECTED` |
| 7 | DVDT | 3.3 nF, 50 V, to GND |
| 8 | GND | GND |
| 9 | ILM | 750 Ω to GND |
| 10 | ITIMER | Open for fastest fault response |

- Package: 2 × 2 mm RPW10 HotRod, no separate generic exposed-ground pad
- Local input: at least 0.1 µF; use 1 µF with an appropriate voltage rating. Downstream converter bypass supplies the output capacitance
- Current limit: nominal `3334/750 = 4.445 A`; table range approximately 3.96–4.84 A before resistor tolerance
- DVDT equation: `C(pF) = 2000 / slew(V/ms)`; 3.3 nF yields about 0.6 V/ms
- 390 kΩ clamp-select nominal 13.8 V; threshold spread approximately 13.2–14.5 V, actual clamp can reach about 14.6 V under specified conditions
- EN pull-up value is deliberate: 12.6 V reverse / 1.5 MΩ = 8.4 µA, limiting pin reverse current below 10 µA. Datasheet minimum series resistance guidance is not a substitute for this reverse-voltage calculation
- This hookup uses the IC's internal undervoltage behavior (roughly 2.65 V), not a separately calibrated 5 V BEC brownout threshold
- Add `VX_PROTECTED` to GND **4.7 kΩ, 0603** bleeder. 500 µA leakage yields 2.35 V, below the main-mux minimum UVLO threshold; at 12.6 V dissipation is 34 mW
- Hot reversal is not automatically covered: VIN absolute minimum is `max(-15 V, VOUT - 21 V)`. A still-charged +12.6 V output followed by −12.6 V input violates that differential bound. Cold reverse input and hot reversal are different tests
- Do not claim that the downstream converters are protected from all pulses until clamp overshoot and energy capability are measured

### 2.2 TPS63070RNMR dedicated ABC buck-boost

Source: [TI TPS63070 datasheet](https://www.ti.com/lit/ds/symlink/tps63070.pdf), RNM0015A drawing 4222000/B, 03/2020. The standard TPS63070 does not have the TPS630702 output-discharge behavior.

| Pin | Name | Connect to / implement |
|---:|---|---|
| 1 | PS/SYNC | GND for forced PWM |
| 2 | PG | `ABC_PG`; 100 kΩ pull-up to `+5V_BEC`; connects to TPS2116 PR1 |
| 3 | VAUX | 100 nF to GND |
| 4 | GND | Quiet ground tied to common ground |
| 5 | FB | `ABC_FB`, divider junction |
| 6 | FB2 | GND, unused second setting |
| 7, 8 | VOUT | `+5V_BEC`, both numbered pads are required |
| 9 | L2 | One end of 1.5 µH inductor |
| 10 | PGND | Power ground, common ground plane |
| 11 | L1 | Other end of 1.5 µH inductor |
| 12, 13 | VIN | `VX_PROTECTED`, both numbered pads are required |
| 14 | EN | `VX_PROTECTED` through 100 kΩ |
| 15 | VSEL | GND |

Recommended first-article values:

| Component | Value / reason |
|---|---|
| L | 1.5 µH; datasheet reference Coilcraft XFL4020-152ME, 4 × 4 × 2.1 mm, Isat 4.6 A, DCR 14.4 mΩ |
| CIN | 2 × 10 µF, 25 V, 0805, as reference population |
| COUT | 3 × 22 µF, 16 V, 0805, as reference population |
| VAUX | 100 nF ceramic |
| FB upper | 536 kΩ, 0.1%, `+5V_BEC` to `ABC_FB` |
| FB lower | 100 kΩ, 0.1%, `ABC_FB` to GND |
| PG pull-up | 100 kΩ to `+5V_BEC` |
| EN series | 100 kΩ from protected input |
| Bleeder | 47 kΩ, `+5V_BEC` to GND |

- Nominal pre-mux output: `0.8 × (1 + 536/100) = 5.088 V`. This offsets part of the mux's full-load drop, but total tolerance/line/load/drop still requires measurement
- With 1.5 µH, the stability table gives effective output capacitance minimum 15 µF, nominal 47 µF, maximum 470 µF. Do not silently turn nominal 3 × 22 µF into three tiny capacitors without DC-bias verification
- PG is low when disabled or output is not good, high impedance when good. Rising threshold 94.5–98.5%, falling 90–94.5%. This controls BEC preference of the ABC mux without MCU software
- EN supply drive series resistance recommended range is 1 kΩ–1 MΩ
- Reference θJA is 63°C/W. At 10 W output, 90–95% efficiency implies about 1.11–0.53 W loss before calculating board-dependent temperature rise; no enclosure thermal claim is established
- Input operating maximum 16 V is close enough to the protection clamp to require transient validation

### 2.3 TPS2116DRLR ABC mux

Source: [TI TPS2116 datasheet](https://www.ti.com/lit/ds/symlink/tps2116.pdf). Package DRL8 / SOT-583, 2.1 × 1.6 mm.

| Pin | Name | Net |
|---:|---|---|
| 1 | GND | GND |
| 2, 7 | OUT | `+5V_PERIPH` |
| 3 | VIN1 | `+5V_BEC` |
| 4 | PR1 | `ABC_PG` from converter PG |
| 5 | MODE | `+5V_BEC` |
| 6 | VIN2 | `USB_LIMITED` |
| 8 | ST | NC |

- Use local input bypass; 1 µF at each input is a layout starting point, subject to nearby converter capacitors. Initial output capacitor 4.7 µF
- 2.5 A rated path suits the dedicated 2 A ABC rail. At 5 V, RON can be 60 mΩ through 105°C, producing 120 mV at 2 A
- Inactive-input reverse leakage figures 0.001 µA at 25°C, 0.05 µA at 85°C, 0.15 µA at 105°C are **typical, not guaranteed hot maxima**
- Recommended ambient maximum 105°C. Recommended rail maximum 5.5 V, absolute maximum 6 V are important for USB surge protection

### 2.4 TPS2121RUXR main-input mux

Source: [TI TPS2121 datasheet](https://www.ti.com/lit/ds/symlink/tps2121.pdf), RUX0012A drawing 4224010/A, 11/2017; [TI XREF hysteresis guidance](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1280611/tps2121-xref-hysteresis).

| Pin | Name | Net / component |
|---:|---|---|
| 1, 8 | OUT | `CORE_BUCK_IN` |
| 2 | IN2 | `USB_LIMITED` |
| 3 | CP2 | `CORE_REF`; 12.7 kΩ to `+3V3_CORE`, 10.0 kΩ to GND |
| 4 | OV2 | GND, overvoltage input disabled |
| 5 | OV1 | GND, overvoltage input disabled |
| 6 | PR1 | `CORE_PRIORITY`; 18.0 kΩ to `VX_PROTECTED`, 10.0 kΩ to GND, 330 kΩ to ST |
| 7 | IN1 | `VX_PROTECTED` |
| 9 | ST | `CORE_MUX_ST`; 10 kΩ pull-up to `+3V3_CORE`; 330 kΩ to PR1 |
| 10 | ILIM | 80.6 kΩ to GND |
| 11 | SS | 100 nF to GND |
| 12 | GND | GND |

- Actual body is **2.0 × 2.5 mm**, not 2.5 × 2.5 mm. No added center EP
- Use 0.1% for four PR1/CP2 divider resistors; 1% for ST pull-up and feedback. Optional 1 nF from CP2 to GND filters noise; not a substitute for correct return placement
- Local input bypass 1 µF at each input; output can share the immediately adjacent 10 µF / 25 V buck input capacitor
- Current limit with 80.6 kΩ: `65.2 / 80.6^0.861 = 1.489 A` nominal. Datasheet table at 80 kΩ gives roughly 1 / 1.5 / 2 A minimum / typical / maximum
- SS 100 nF yields approximately 780 V/s at 5 V, 800 V/s at 12 V. The typical 5 µs switchover claim applies after input qualification/settling, not the complete cold-start event

#### Proposed priority and hysteresis network

This is an **engineering derivation**, not a copied TI application circuit. TI confirms there is no internal PR1/CP2 comparator hysteresis, so external feedback is necessary when the supplies hover around crossover.

- At a nominal 3.3 V reference, BEC return threshold is approximately **4.150 V**, and BEC-to-USB falling threshold approximately **3.973 V**
- Corner sweep including core −3.5/+4%, divider 0.1%, feedback/pull-up 1%, comparator ±40 mV, ST-low 0–0.4 V gives approximately 3.859–4.441 V return and 3.709–4.257 V falling thresholds
- The 18.0 kΩ PR1 upper resistor supersedes the initial 20.0 kΩ proposal. Datasheet eFuse RON maximum is 45 mΩ at 3 A over −40 to 125°C, so 5.0 V raw BEC gives at least 4.865 V protected before trace/wire drop. This leaves approximately 424 mV above worst-case return threshold; even a conservative protected voltage of 4.72 V leaves 279 mV. Low-BEC dropout remains a first-article corner check
- Minimum CP2 in that sweep is 1.401 V, above the internal-reference maximum 1.1 V
- Before core power exists, CP2 = 0 and the mux starts under its internal-reference / highest-valid-input behavior. At 5 V BEC PR1 already exceeds 1.06 V; with USB alone IN2 is the only valid source. Once core powers up, XREF behavior becomes active. This bootstrap must be bench checked, including partial ramps and repeated insertion
- Dividing USB instead of the stable core rail for CP2 was rejected: 4.33–5.25 V USB variation can move BEC dropout too close to approximately 3.1 V and risk core brownout

Inactive-input leakage can reach **±35 µA through 85°C / ±500 µA through 125°C** for the wider input differential (≤22 V), or ±5 µA / ±80 µA when differential is ≤5 V. Account for leakage in either direction; do not leave unpowered source rails floating.

### 2.5 TPS62162DSGR fixed 3.3 V main buck

Source: [TI TPS62160-family datasheet](https://www.ti.com/lit/ds/symlink/tps62160.pdf), fixed TPS62162 member. Package DSG8 WSON, 2 × 2 mm, exposed pad required.

| Pin | Name | Net |
|---:|---|---|
| 1 | PGND | GND |
| 2 | VIN | `CORE_BUCK_IN` |
| 3 | EN | `CORE_BUCK_IN` |
| 4 | AGND | GND, quiet return |
| 5 | FB | GND for the fixed-voltage part |
| 6 | VOS | `+3V3_CORE`, sensed directly at output capacitor |
| 7 | SW | `CORE_SW`, via inductor to `+3V3_CORE` |
| 8 | PG | NC if unused |
| EP | Exposed pad | AGND / GND as required by package drawing |

| Passive | Selection |
|---|---|
| L | 3.3 µH preferred for low-VIN full-load margin; reference XFL3012-332MEC (3 × 3 × 1.2 mm, reference current 1.6 A), alternatively LPS3015-332ML (3 × 3 × 1.4 mm, 1.4 A) |
| CIN | 10 µF / 25 V ceramic |
| COUT | 22 µF ceramic, reference population; qualify effective value at 3.3 V |

- Datasheet standard inductor is 2.2 µH; 3.3 µH is recommended at low input/full-current conditions
- 1 A output versus provisional 0.8 A combined load budget leaves limited margin; quantify real flash, MCU and sensor loads
- PWM accuracy ±3%; PFM approximately −3.5/+4%, plus applicable line/load terms. 3.3 × 1.04 = 3.432 V before ripple, below 3.6 V rail absolute maxima
- Nominal internal start: about 50 µs delay then 25 mV/µs output ramp. Thus 3.3 V 10–90% is about 0.106 ms **when the input is already adequate**
- A slow mux/eFuse input ramp may cause output tracking; do not infer final sensor ramp compliance from the internal soft-start number alone
- These exact reference inductors still need assembly sourcing, DC-bias/temperature current-curve review, and footprint verification

### 2.6 TPS2553DRVR USB and DSM current limiters

Source: [TI TPS2553 datasheet](https://www.ti.com/lit/ds/symlink/tps2553.pdf); [TI VIN=0 reverse-blocking clarification](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/860676/tps2553-about-reverse-voltage-protection). Use **TPS2553DRVR**, not the `-1` latch-off option. Package WSON DRV6, 2 × 2 mm, EP to GND.

| Pin | Name | USB instance | DSM instance |
|---:|---|---|---|
| 1 | OUT | `USB_LIMITED` | `+3V3_DSM` |
| 2 | ILIM | 66.5 kΩ, 1%, to GND | 45.3 kΩ, 1%, to GND |
| 3 | /FAULT | NC if unused | NC if unused |
| 4 | EN | `USB_VBUS_RAW` | `+3V3_CORE` |
| 5 | GND | GND | GND |
| 6 | IN | `USB_VBUS_RAW` | `+3V3_CORE` |
| EP | Thermal pad | GND | GND |

Datasheet fit, R in kΩ / I in mA, including 1% resistor limits:

```text
Imin = 25230 / (R × 1.01)^1.016
Inom = 23950 / R^0.977
Imax = 22980 / (R × 0.99)^0.94
```

| Instance | RILIM | Minimum / nominal / maximum steady limit |
|---|---:|---:|
| USB | 66.5 kΩ ±1% | 351.2 / 396.7 / 448.7 mA |
| DSM | 45.3 kΩ ±1% | 518.7 / 577.2 / 643.8 mA |

- USB selected maximum is below 450 mA, not a claimed exact 450 mA limit. Minimum can limit the board considerably earlier
- DSM resistor intentionally gives a minimum above the 0.5 A supported load. A nominal 550 mA choice would not necessarily guarantee 0.5 A through tolerance
- RON max 150 mΩ through 125°C creates up to 75 mV drop at DSM 0.5 A. Nominal 3.3 V receiver supply is not a precision 3.3 V ±5% assertion at every corner
- Input bypass at least 0.1 µF, 1 µF recommended. The USB module already has 1 µF at raw VBUS; avoid an unnecessary duplicate if physically adjacent
- Proposed initial outputs 4.7 µF each; this is a design starting point, not a mandatory fixed datasheet capacitor value
- Current response about 2 µs typical; reverse-detection threshold 95–190 mV and response about 3–7 ms. The TPS2553 alone is not fast reverse isolation; the downstream muxes provide the essential rail separation
- Reverse-current maximum 1 µA is specified only at TJ=25°C, VOUT=6.5 V, VIN=0. No corresponding 85/125°C guaranteed maximum was found
- Operating input maximum 6.5 V; absolute maximum **7 V**, correcting an earlier 6.5 V absolute-maximum interpretation

### 2.7 Required bleeders and direct USB capacitance

| Node | Bleeder | Purpose / bound |
|---|---:|---|
| `USB_LIMITED` | **1 kΩ ±1%** | 500 µA identified mux leakage contribution creates ≤0.505 V; about 5 mA load with USB present |
| `USB_VBUS_RAW` | **10 kΩ ±1%** | At the room-temperature 1 µA limiter bound, approximately 10.1 mV; hot absent-host leakage still needs testing |
| `VX_PROTECTED` | **4.7 kΩ, 0603** | 500 µA yields 2.35 V, below mux minimum UVLO; 34 mW at 12.6 V |
| `+5V_BEC` | **47 kΩ** | Prevents floating output / PG / ABC mux chatter during USB-only operation |

These are the final proposed values; earlier 10 kΩ or 2.2 kΩ suggestions for `USB_LIMITED` are superseded. USB overhead is roughly 5 mA downstream plus 0.5 mA upstream, before quiescent currents. Keep the aggregate directly connected `USB_VBUS_RAW` capacitance below 10 µF; downstream current-limited capacitance still needs inrush qualification.

## 3. Protection, startup and release gates

### USB source isolation and surge limits

The objective is safe operation from a compliant 5 V USB source with current limiting and no material rail backfeed into BEC/servo or absent host. This is not yet a claim of arbitrary wrong-voltage-source survival.

A common 5/5.5 V TVS can clamp well above 6–7 V at an ESD pulse current. The TPS2116 absolute maximum of 6 V is the tightest limit, and TPS2553 has 7 V absolute maximum. Therefore **no ordinary TVS can be declared adequate solely from its standoff label**. Select the VBUS TVS against its dynamic clamp curve and the actual pulse path; measure at the IC pins. Existing 1 µF input capacitance and very short ground routing help but do not constitute compliance evidence. A separate active USB OVP stage would need an explicit area/protection tradeoff if wrong-voltage survival is required.

The USB signal/CC page uses ground-only ESD diodes rather than supply-steering USBLC6 rails. The VBUS TVS is still a separate unresolved selection. The raw servo bus is not protected by the electronics eFuse. For example, a 13 V SMBJ device can clamp around 21.5 V; it does not by itself protect a 16 V converter.

### USB current and original-board behavior

- A fixed 400 mA-class current limiter is not proof of USB's pre-enumeration ≤100 mA behavior. Verify stock descriptors, startup consumption and enumeration behavior; the MCU's worst-case active current can exceed 100 mA by itself
- The official classic Nexus manual is a one-page poster containing specifications/wiring and **no statement of USB-only rail topology or permitted current**. Whether original Nexus powers each receiver port on USB alone remains a physical-reference test
- Full receiver loads on USB may brown out even when connectors receive voltage. Do not present USB bench mode as the full BEC-powered output rating
- Disconnect motors/servos during USB bench qualification. I/O-driven phantom power is a separate system-level consideration; do not add unidirectional buffers that break stock bidirectional DShot

### Startup and component power timing

The independently reported ICM-42688-P rail 10–90% ramp constraint is 0.01–3 ms; the DPS368-compatible barometer proposal has a 0.001–5 ms-to-90% constraint. Confirm against the exact assembled sensor MPN and sensor evidence file. TPS2121 SS=100 nF and TPS259472 DVDT=3.3 nF deliberately slow upstream ramps. TPS62162's approximately 0.106 ms intrinsic 10–90% rise is encouraging but **does not prove a cold start through two slowly ramping upstream stages**, especially with ferrite-filtered IMU capacitance and prebias.

Capture `VX_PROTECTED`, `CORE_BUCK_IN`, `+3V3_CORE` and IMU VDD under USB insertion, BEC insertion, both-source insertion in each order, low BEC ramp, current-limit recovery and hot plug. No added startup supervisor is assumed until the waveform establishes whether it is necessary.

W25N01GV power-up sequencing requires CS high and timing before command/write operations; reported gates are 200 µs after VCC minimum before selection and 1 ms before write. Exact driver delays and reset boot behavior remain a firmware-source review/first-article check.

### Required qualification before fabrication release / flight

1. ERC and full pin-to-pad audit, especially every nonstandard HotRod land and signal-ground versus power-ground return
2. Verify real minimum effective capacitance and inductor saturation/current/temperature curves; no arbitrary reference-cap reductions
3. Simultaneous 2 A ABC + 0.5 A DSM + worst core load at 5 V and 12.6 V BEC, including wiring drop and component tolerances
4. Thermal soak in the intended enclosed 41.3 × 25.4 × 13.1 mm overall envelope; converter and mux junction estimates, hot spots, and sensor drift
5. Cold/hot BEC insertion, USB insertion, BEC priority, brownout, both source orderings, reverse input within applicable absolute limits, and fault recovery
6. Leakage into absent USB/BEC at room and maximum intended operating temperature. Bleeders only bound identified leakage terms, not every possible parasitic path
7. BEC clamp overshoot, cable inductance and servo-induced transients; TVS pulse energy and converter pin voltage
8. USB steady/inrush current and enumerated-power behavior with stock firmware
9. Sensor rail ramp and NAND boot/write timing; IMU noise with 2 A peripheral load switching
10. Port-specific short circuits: a DSM short can hit approximately 644 mA limit; combined core demand during that fault approaches the 1 A buck rating and may still reset the MCU
11. Correct raw-bus copper/contact current handling and user pinout. Servo passthrough current is not established by a 4.4 A electronics eFuse
12. Actual first-article USB receiver behavior versus an original classic Nexus, because documentation does not resolve it

## 4. Alternatives researched and why they were not selected

### MP28167GQ-A-Z (programmable-reference version)

Sources: [MPS MP28167-A primary datasheet](https://www.monolithicpower.com/en/documentview/productdocument/index/version/2/document_type/Datasheet/lang/en/sku/MP28167GQ-A/document_id/9621/), [JLC C3188179](https://jlcpcb.com/partdetail/3750121-MP28167GQ_AZ/C3188179).

- Can operate without firmware: defaults include VREF=1 V, enable bit=1, 500 kHz FPWM, 3.5 A current limit, 3.5 ms soft-start, hiccup and output discharge. Pull SCL/SDA to its 3.65 V VCC if unused, do not silently substitute fixed-version connections
- 5 V setup: 430 kΩ top / 107 kΩ bottom divider, plus **806 kΩ in series between divider tap and FB**; OC 21.5 kΩ parallel 22 nF; VCC 1 µF; each bootstrap 100 nF; EN 499 kΩ from VIN plus 22 nF to GND
- Pins: 1 IN, 2 GND, 3 EN, 4 ALT, 5 SCL, 6 SDA, 7 OC, 8 FB, 9 VCC, 10 AGND, 11 GND, 12 OUT, 13 BST2, 14 SW2, 15 SW1, 16 BST1
- Nonstandard QFN16 with long inward power/signal lands; no invented pad 17
- Reference 4.7 µH inductor; CIN includes 100 µF bulk + 22 µF ceramic; COUT minimum 5 × 22 µF ceramic. Reference MPL-AL6050-4R7 is 6.6 × 6.4 × 4.8 mm, DCR 16.5 mΩ, rated current 7.5 A, Isat 11 A
- At 4.7 V input, 5 V × 2.62 A output implies about 3.10 A input at 90% / 3.28 A at 85% efficiency, below a 4 A recommended input envelope. At 12.6 V ideal buck peak approximately 3.26 A; L/f each −20% raises it to about 3.62 A. Mixed buck-boost operation near 5 V needs validation
- Feasible current capability does not solve the passive-area problem. The substantial reference L/C population is the reason this is not the chosen compact baseline

### MP28167GQ-Z (fixed 5 V version)

Sources: [MPS fixed-version primary datasheet](https://www.monolithicpower.com/en/documentview/productdocument/index/version/2/document_type/Datasheet/lang/en/sku/MP28167GQ/document_id/4000/), [JLC C2912962](https://jlcpcb.com/partdetail/Monolithic_PowerSystems-MP28167GQZ/C2912962).

Fixed 5 V removes the -A feedback configuration, not the big reference passives. Figure 10 still uses 5 × 22 µF output; Figure 9 alternative uses 100 µF output electrolytic + 2 × 10 µF. Input remains 100 µF bulk + 22 µF; L=4.7 µH. NC pins 4/8 connect to GND; RSV1/RSV2 cannot float and connect to GND or VCC. Do not interchange pin functions with -A.

### TPS552892 / TPS552872

[TPS552892 primary datasheet](https://www.ti.com/lit/ds/symlink/tps552892.pdf) supports higher current in a 3 × 5 mm package but its reference passives are not automatically compact: 4.7 µH / 400 kHz, 4 × 22 µF output and 20 µF effective input. Its reference inductor was 7.5 × 7.2 × 7 mm for the broader 8 A envelope. A 1 MHz / 2.2 µH redesign might be smaller within its supported frequency/inductance envelope, but would require fresh compensation, ripple and thermal validation. It is not a free validated compact drop-in. TPS552872 sourcing was also weak.

## 5. Sourcing observations and lifecycle

**Stock is a dated observation, not a reservation or assembly guarantee.** Recheck exact suffix and approved substitute before BOM purchase. Reference inductors and capacitance choices are electrically recommended but not yet a complete stock-locked BOM.

| MPN / library ID | Observed date/time UTC | Observed stock / orderable | Notes |
|---|---|---|---|
| MP28167GQ-A-Z / C3188179 | 2026-10-04 16:25 | 1,107 / 1,036 | Live JLC page; displayed unit price approximately US$3.3029 |
| MP28167GQ-Z / C2912962 | 2026-10-04 16:31 | 2,343 / 2,283 | Live JLC page; displayed unit price approximately US$2.4784 |
| TPS552892RYQR / C19272254 | 2026-10-04 earlier web snapshot | 79 / 29 | Approximately US$11; snapshot is not an order quote |
| TPS552872 / C22427496 | 2026-10-04 earlier LCSC snapshot | 0 | Not selected |
| TPS63070RNMR / C109322 | 2026-10-04 16:37–16:50 | 24,003 / 22,866 | Live JLC selected-part snapshot |
| TPS259472ARPWR / C3662789 | 2026-10-04 16:37–16:50 | 3,781 / 3,667 | Live JLC selected-part snapshot |
| TPS2121RUXR / C485916 | 2026-10-04 16:37–16:50 | 32,212 / 31,601 | Live JLC selected-part snapshot |
| TPS2116DRLR / C3235557 | 2026-10-04 16:37–16:50 | 79,070 / 78,596 | Live JLC selected-part snapshot |
| TPS62162DSGR / C40256 | 2026-10-04 16:37–16:50 | 6,621 / 6,574 | Live JLC selected-part snapshot |
| TPS2553DRVR / C138719 | 2026-10-04 16:37–16:50 | 28,919 / 28,794 | Live JLC selected-part snapshot; two instances |

Manufacturer lifecycle references: [STM32F722RET6 active](https://estore.st.com/en/stm32f722ret6-cpn.html); [ICM-42688-P production](https://product.tdk.com/en/search/sensor/mortion-inertial/imu/info?part_no=ICM-42688-P); [W25N01GVZEIG mass production](https://www.winbond.com/hq/product/code-storage-flash/qspi-nand/w25n-gv/?__locale=en&partNo=W25N01GVZEIG). W25N01GV is **1 Gbit = 128 MiB**, not 128 Mbit; SON8 8 × 6 mm, 2.7–3.6 V. SPL06-001 JLC C2684428 exists, but manufacturer lifecycle was not independently established; consult the sensor selection record for the actual selected barometer.

## 6. Footprint source / audit contract

Three nonstandard HotRod footprints must be traced from the package drawings, not inferred from pin count:

- TPS63070 RNM0015A: body 2.5 × 3 mm; datasheet PDF pages 39–41; drawing 4222000/B, March 2020. Split paste and solder-mask-defined power copper required. Pins 7/8 and 12/13 have joined power geometry; they remain separately numbered electrical pins
- TPS259472 RPW0010A: body 2 × 2 mm; datasheet PDF pages 72–74; central IN/OUT strips are pins 5/6, not ground EP
- TPS2121 RUX0012A: body 2 × 2.5 mm; PDF pages 38–40; drawing 4224010/A, November 2017. Power pads 1/2/7/8 are wide inward lands; there is no separate EP

The drawing-verified generator is `tools/power_footprints.py`; its exact dimension tables and verification results follow below. A parsed footprint and correct pad count are necessary but insufficient checks: visually compare copper, mask and paste with the source drawing and separately audit the schematic pin functions. Thermal vias in power lands require assembler-approved filled/capped via-in-pad or a qualified alternative; never automatically turn a drawn example via into an open drill that steals solder.

### 6.1 Generated files and coordinate convention

Run `python tools/power_footprints.py` from any working directory. It writes only these three files under `hardware/library/F722_Heli.pretty/`, never the schematic, PCB or library table:

1. `Texas_RNM0015A_TPS63070_2.5x3mm.kicad_mod`
2. `Texas_RPW0010A_TPS259472_2x2mm.kicad_mod`
3. `Texas_RUX0012A_TPS2121_2x2.5mm.kicad_mod`

Use `--out-dir /path/to/test.pretty` for a temporary reproducibility check. No third-party Python package is required by the generator. The files are original manufacturer-drawing-derived geometry. They contain no external 3D-model dependency.

All following dimensions are millimetres, PCB **top view**, origin at body centre, +x right / +y down. Do not mirror the package-bottom outline onto the board. The footprint follows the orientation of each datasheet's board-land drawing. Only the documented numbered copper pads are present; mask/paste-only apertures have empty numbers. Body outlines are nominal sizes, and courtyards add 0.25 mm to the maximum body/copper extent, rounded outward to 0.05 mm.

### 6.2 TPS63070 RNM0015A exact lands

| Pin(s) | Centre(s) x, y | Geometry |
|---|---|---|
| 1, 2, 3, 4 | x=−1.150; y=−0.750, −0.250, +0.250, +0.750 | Copper 0.600 × 0.250; NSMD +0.050 mask; equal-size paste |
| 5, 6 | x=−0.725, −0.225; y=+1.400 | Copper 0.250 × 0.600; NSMD +0.050 mask; equal-size paste |
| 15, 14 | x=−0.725, −0.225; y=−1.400 | Copper 0.250 × 0.600; NSMD +0.050 mask; equal-size paste |
| 9, 11 | x=+0.775; y=+0.500, −0.500 | Exposed mask 1.350 × 0.250; copper 1.450 × 0.350 |
| 10 | x=+0.600, y=0 | Exposed mask 1.700 × 0.250; copper 1.800 × 0.350 |
| 7, 8 | left/right stems centred x=0.275 / 0.775, y=+1.400 | Joined U-shaped power land; dimensions below |
| 13, 12 | left/right stems centred x=0.275 / 0.775, y=−1.400 | Vertical mirror of 7/8 |

The 7/8 exposed mask is the polygon with vertices `(0.150,1.100), (0.900,1.100), (0.900,1.700), (0.650,1.700), (0.650,1.350), (0.400,1.350), (0.400,1.700), (0.150,1.700)`. Thus the joined shape is 0.750 × 0.600, with 0.250-wide stems and 0.250-high bridge. The 12/13 mask is mirrored across y=0. Paste uses those same joined U outlines. Copper extends at least 0.050 beyond the mask; its two numbered halves overlap on the bridge, so both pins must have the same electrical net as specified. Do not separate the source's joined geometry into four isolated generic pads.

Explicit bar paste apertures:

| Copper pin | Paste centres x | y | Each aperture |
|---|---|---|---|
| 9 | 0.388 and 1.163 | +0.500 | 0.575 × 0.250 |
| 11 | 0.388 and 1.163 | −0.500 | 0.575 × 0.250 |
| 10 | 0.140 and 1.060 | 0 | 0.720 × 0.250 |

Drawing R=0.050 at exposed outer corners; the expanded bar copper uses R=0.100. Convex custom-polygon corners are rendered by eight segments per 90-degree arc, with less than 0.00025 mm chord error at 0.050 mm radius. Concave corners remain sharp, matching the land drawing. Datasheet 0.125 mm stencil example gives approximately 85% coverage for pads 9–11.

### 6.3 TPS259472 RPW0010A exact lands

| Pin(s) | Copper centre(s) x, y | Copper geometry |
|---|---|---|
| 2, 3 | x=−0.900; y=−0.225, +0.225 | 0.600 × 0.250 |
| 9, 8 | x=+0.900; y=−0.225, +0.225 | 0.600 × 0.250 |
| 5 IN | −0.250, 0 | 0.300 × 2.400 long central strip |
| 6 OUT | +0.250, 0 | 0.300 × 2.400 long central strip |
| 1 | Horizontal (−0.900,−0.700), vertical (−0.725,−0.875) | Union of 0.600 × 0.300 horizontal + 0.250 × 0.650 vertical |
| 4 | Horizontal (−0.900,+0.700), vertical (−0.725,+0.875) | Same L mirrored vertically |
| 7 | Horizontal (+0.900,+0.700), vertical (+0.725,+0.875) | Same L mirrored both axes |
| 10 | Horizontal (+0.900,−0.700), vertical (+0.725,−0.875) | Same L mirrored horizontally |

All copper uses the preferred NSMD mask with +0.050 mm opening expansion. There is **no pad 11 / ground EP**. Drawing 4225183/A, August 2019, specifies R=0.050 outer corners.

For the 0.100 mm reference stencil:

- Pins 2/3/8/9: paste equals copper outline
- Pins 5/6: two apertures per strip, 0.280 × 1.060, centred at their x=±0.250 and y=±0.630
- Corner paste: union of horizontal 0.600 × 0.275 centred x=±0.900, y=±0.6875 and vertical 0.225 × 0.650 centred x=±0.7125, y=±0.875, using the respective corner signs
- Explicit paste-only shapes are used, with automatic copper-pad paste disabled on those pads. TI describes 93% coverage for corners and 82% for central strips

### 6.4 TPS2121 RUX0012A exact lands

| Pin(s) | Centre(s) x, y | Copper / paste |
|---|---|---|
| 1, 2 | x=−0.675; y=−0.350, +0.350 | 1.050 × 0.400 |
| 8, 7 | x=+0.675; y=−0.350, +0.350 | 1.050 × 0.400 |
| 3, 4, 5, 6 | x=−0.750, −0.250, +0.250, +0.750; y=+1.150 | 0.200 × 0.600 |
| 12, 11, 10, 9 | x=−0.750, −0.250, +0.250, +0.750; y=−1.150 | 0.200 × 0.600 |

All use NSMD +0.050 mask expansion and R=0.050 outer corners. The 0.100 mm stencil example uses 100% paste coverage of the exposed lands. No generic central pad, and no open via-in-pad holes, are generated. The drawing shows example thermal/power vias in the four large pads, but these require a separately qualified filled/capped process and layout decision.

### 6.5 CAD validation performed

On 2026-10-04 approximately 17:20 UTC:

- Generator compiled successfully and generated exactly the three named footprints
- KiCad 9.0.2 `pcbnew.FootprintLoad` successfully loaded all three
- Numbered copper pad sets verified exactly `{1..15}`, `{1..10}`, `{1..12}`; empty-number paste/mask-only apertures are excluded from that count
- Actual KiCad SVG exports for F.Cu, F.Mask and F.Paste were rasterized and visually compared with the datasheet drawings. Joined power openings, split paste, L-shaped RPW corners and all rotations match
- A temporary standalone audit board with unique nets on distinct pins, shared nets only on RNM 7/8 and 12/13, passed KiCad DRC with **0 violations / 0 unconnected items**, using a documented 0.127 mm clearance rule. This is a **footprint-level check**, not whole-controller board validation
- At the generic 0.200 mm default netclass, two RNM power-pad gaps legitimately report 0.150 mm clearance. Do not misread that as an unknown defect; retain a fabrication-supported 0.127 mm rule for these fine-pitch lands, and do not arbitrarily shrink the manufacturer's pads
- Reference text is 0.8 mm / 0.12 mm stroke. Layout may relocate reference labels while preserving pin-1 indication

Temporary rendered drawing and audit files are under `/tmp/f722-power-research/`: `tps63070-land.png`, `tps63070-paste.png`, `tps25947-check-page-73.png`, `tps25947-check-page-74.png`, `tps2121-land.png`, `tps2121-paste.png`, and `plots/power-footprints-audit-F_{Cu,Mask,Paste}.png`. The repeatable source is the project generator plus linked manufacturer PDFs; `/tmp` artifacts are not a permanent library dependency.

**Assembly gate:** RNM reference stencil thickness is 0.125 mm, while RPW/RUX references are 0.100 mm. The board's proposed single 0.10 mm stencil must be reviewed with the assembler for RNM solder volume and every aperture's area/aspect ratio. Preserve the explicit paste geometry through CAM review. A successful footprint DRC does not qualify reflow, mask registration, copper capping, solder volume or thermal performance.

## 7. Additional fixed-buck and limiter footprint audit (2026-10-04)

These two additional footprint files were derived from the current primary drawings. They are stored directly in the project library; the earlier three-footprint generator remains intentionally limited to its three HotRod files. No schematic/PCB connection was edited by this footprint audit.

### TPS62162DSGR: DSG0008A, exposed pad 9

Source: [TI TPS62160 family datasheet](https://www.ti.com/lit/ds/symlink/tps62160.pdf), physical PDF pages 39–41; drawing **4218900/E, August 2022**. Added file: `Texas_DSG0008A_TPS62162_2x2mm_EP0.9x1.6mm.kicad_mod`.

Top-view dimensions, mm:

- Body 2 × 2; left pins 1/2/3/4 at x=−0.950 and y=−0.750/−0.250/+0.250/+0.750; right pins 8/7/6/5 at x=+0.950 with the same y sequence
- Each outer copper/paste land 0.500 × 0.250, radius 0.050
- Exposed copper pad **9** centred (0,0), **0.900 × 1.600**, externally connected to **AGND/pin 4**, soldered for thermal and mechanical reliability
- EP explicit paste: two 0.900 × 0.700 apertures at (0,±0.450); central gap 0.200. Drawing reports 87% coverage using a 0.125 mm stencil
- Preferred NSMD maximum mask expansion is 0.070 mm; generated footprint uses 0.050 mm
- Drawing's optional 0.200 mm vias at (0,±0.550) are not drilled by the footprint; apply the board's qualified filled/capped-via process if added

The installed generic `DFN-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm` has the correct EP size/number but **different lands** (0.725 × 0.250 at x=±1.0125) and a single 0.730 × 1.290 paste window. It is not an exact match to this source drawing. The new local footprint follows the current TI geometry instead of silently claiming the generic footprint was identical.

### TPS2553DRVR: DRV0006A, exposed pad 7

Source: [TI TPS2553 datasheet](https://www.ti.com/lit/ds/symlink/tps2553.pdf), physical PDF pages 38–40; drawing **4222173/C, November 2025**. Added file: `Texas_DRV0006A_TPS2553_2x2mm_EP1x1.6mm.kicad_mod`.

| Pin | Function | Top-view centre x, y (mm) |
|---:|---|---|
| 1 | OUT | −0.975, −0.650 |
| 2 | ILIM | −0.975, 0 |
| 3 | /FAULT | −0.975, +0.650 |
| 4 | EN | +0.975, +0.650 |
| 5 | GND | +0.975, 0 |
| 6 | IN | +0.975, −0.650 |
| 7 | Exposed thermal pad | 0, 0; connect externally to GND/pin 5 |

- Body 2 × 2; each perimeter copper/paste land **0.450 × 0.300**, radius 0.050
- Exposed copper pad 7 is **1.000 × 1.600**
- EP explicit paste: two **1.000 × 0.700** windows at (0,±0.450), 0.200 central gap. The 0.125 mm stencil reference reports 88% coverage
- Preferred NSMD maximum mask expansion 0.070; local footprint uses 0.050
- Optional 0.200 mm thermal vias at (0,±0.550) require separate board-level process approval, so no open holes are generated

The installed generic `DFN-6-1EP_2x2mm_P0.65mm_EP1x1.6mm` has correct body/EP/pin count but different 0.650 × 0.350 perimeter lands at x=±1.050 and reduced 0.820 × 0.630 paste windows at y=±0.400. Use the new local TI-specific geometry for this design. Both DSG and DRV add further 0.125 mm reference-stencil cases to the existing 0.10 mm board-stencil review gate.

Verification addendum at 17:38 UTC: the new DSG/DRV files both load in KiCad 9.0.2, have exactly 9/7 numbered copper pads respectively, and their exported copper/paste plots were inspected against the drawings. A standalone temporary board passed DRC with 0 violations and 0 unconnected items at the ordinary 0.200 mm default clearance. This verifies the footprint geometry, not the controller circuit or assembled thermal performance.

### Additional TPS63070 low-input rating caveat

The datasheet's 2 A recommended-output row conditions include `VOUT/VIN ≤ 1`. At the low 5.0 V raw-BEC corner, protection drop and the 5.088 V setpoint put the converter slightly into boost, so the complete 2 A connector rating there is an **engineering calculation and required first-article test**, not an unconditional reading of the 2 A row. The specified minimum average positive input-current limit is 3.05 A at VIN=5 V/VOUT=6.5 V and TJ=0–125°C. That supports useful current margin over calculated normal demand but does not establish cold operation, startup with an attached load, efficiency or thermal headroom at the final operating point.

Using TI's boost peak-current equation, VIN=4.7 V, VOUT=5.088 V, IOUT=2 A, conservative efficiency 85%, fSW minimum 2.1 MHz and effective L=1.05 µH (−30% from 1.5 µH) gives approximately **2.63 A peak** and **3.15 A** after TI's suggested 20% selection margin. The ideal buck ripple calculation at VIN=12.6 V using the same L/f corner gives about **2.69 A peak**. Actual mixed-mode ripple and magnetic losses near VIN≈VOUT remain measurement gates.

## 8. Final power inductors and assembly-stock observations

Selection updated **2026-10-04 17:42 UTC**: L1 is **Coilcraft XGL4020-152MEC**, 1.5 µH, and L2 is **Murata DFE322512F-3R3M=P2**, 3.3 µH. These supersede the provisional XFL4020/XFL3012 BOM choices in the earlier reference-value discussion. XFL3012 remains a documented alternate, not the current L2 BOM. Component substitution does not constitute validation of converter stability, EMI or thermal performance.

### Dated stock, not reservations

| Part | JLC ID | Live UTC observation on 2026-10-04 | In stock / orderable | Selection |
|---|---|---|---|---|
| XFL4020-152MEC | C3033018 | 17:35 | 0 / pre-order | Original TI reference unavailable from current assembly stock |
| XGL4020-152MEC | C7417180 | 17:37 | 2,316 / 2,309 | **Selected L1** |
| XFL3012-332MEC | C3911580 | 17:36 | 20 / 20 | Low-stock reference alternate |
| DFE322512F-3R3M=P2 | C3221010 | 17:39 | 4,209 / 4,198 | **Selected L2** |

All four observed JLC listings are Extended parts and list SMT support for Economic and Standard assembly. No stock was reserved or purchased. Recheck exact manufacturer suffix and assembly quantity including placement loss before procurement. Public sources: [XFL4020](https://jlcpcb.com/partdetail/XFL4020-152MEC/C3033018), [XGL4020](https://jlcpcb.com/partdetail/Coilcraft-XGL4020152MEC/C7417180), [XFL3012](https://jlcpcb.com/partdetail/Coilcraft-XFL3012332MEC/C3911580), [Murata](https://jlcpcb.com/partdetail/3784028-DFE322512F_3R3MP2/C3221010).

### L1: Coilcraft XGL4020-152MEC, 1.5 µH ±20%

Source: [Coilcraft XGL4020 primary datasheet](https://www.coilcraft.com/getmedia/76c9c081-4945-4c85-9129-9356e1ad6734/xgl4020.pdf), Document 1529, revision 2026-02-19. Project footprint: **`F722_Heli:Coilcraft_XGL4020`**.

- DCR: 13.0 mΩ typical / 14.3 mΩ maximum
- Saturation-current points at 25°C: 3.2 / 5.3 / 7.5 A for 10 / 20 / 30% inductance reduction
- Thermal current figures: 8.0 / 11.1 A for 20 / 40°C rise in the manufacturer's test conditions; these do not predict enclosed-board temperature by themselves
- Body 4.0±0.3 mm square; maximum mounted height 2.10 mm for this termination; courtyard **4.8 × 4.8 mm**, accounting for the 4.3 mm maximum body plus 0.25 mm placement clearance each side
- Manufacturer land pattern: two **0.980 × 3.400 mm** rectangular copper/paste lands, centres **x=±1.185 mm**, y=0 (2.370 mm centre spacing)
- Footprint **pad 1 is the right-hand marked short/start lead**, pad 2 left, matching the manufacturer's top-view terminal direction. Prefer the start lead toward the higher-dv/dt node for EMI. Both ends of the buck-boost inductor are switching nodes, so qualify the final orientation/layout
- NSMD mask expansion 0.050 mm and full-area paste are project starting choices; the manufacturer land diagram specifies copper land dimensions, not a qualified board-specific stencil reduction
- Same recommended land geometry as XFL4020. It has a different soft-saturation curve: the 20–30% current points improve, but its 10%-drop point is lower than the original XFL4020's 4.1 A. Check the actual peak-biased inductance, rather than comparing one headline Isat value

The approximately 2.63–2.69 A normal-peak calculations above are below its 3.2 A 10%-drop point at the stated test condition; temperature, inductance tolerance, core loss and the mixed-mode waveform must still be qualified. Do not interpret its high thermal-current number as permission to increase the converter's specified output.

### L2: Murata DFE322512F-3R3M=P2, 3.3 µH ±20%

Primary-authored reference specification **J(E)TE243A-0019C-01**, nine pages, downloaded from the [verified JLC part page's datasheet link](https://jlcpcb.com/partdetail/3784028-DFE322512F_3R3MP2/C3221010). Page 1 is the body drawing, page 2 electrical limits, page 5 land pattern/reflow, page 7 mounting precautions. The document is marked Reference Only; confirm procurement specifications before production. Project footprint: **`F722_Heli:Murata_DFE322512F`**.

- DCR maximum **108 mΩ**
- Saturation-current point **2.6 A at 30% inductance reduction**; thermal-current figure **2.0 A at 40°C rise** on Murata's six-layer test board. Rated DC current is the smaller limit, so do not call it a 2.6 A continuous-current part
- Inductance test condition 1 MHz, 0.5 V. Withstand voltage 20 V DC; check converter switch-node excursions
- Body **3.2±0.2 × 2.5±0.2 mm**, height **1.2 mm maximum**; unmarked/nonpolar package
- Recommended copper/paste lands: **0.900 × 2.800 mm** at **x=±1.400 mm**, y=0; inner gap 1.900 mm, total outer span 3.700 mm
- Footprint pad 1 left / pad 2 right; no manufacturer start-lead polarity is asserted. Courtyard **4.2 × 3.3 mm**, accounting for maximum body/land extents plus 0.25 mm clearance
- This is **not footprint-compatible with XFL3012**. Update both MPN and footprint together
- Mask expansion 0.050 mm and full-area paste are project starting choices. Manufacturer reflow recommendation allows two reflow cycles maximum and a 250–255°C peak region; confirm the complete assembly profile against every populated part

#### Required core keepout

The manufacturer identifies a low-insulation-resistance core and prohibits through holes and copper underneath except electrode-connected copper, and prohibits contact with other components. The source wording does not explicitly distinguish external and internal copper layers. The local footprint therefore implements a **conservative six-copper-layer central-core keepout**, x=−0.940…+0.940 and y=−1.350…+1.350 mm, on F.Cu, In1–In4.Cu and B.Cu. Tracks, vias, other pads and copper pours are prohibited there; its two electrode pads remain outside. The 0.010 mm inset from nominal electrode inner edges avoids numerical boundary overlap and is not permission to thread traces through the gap.

Respect the footprint courtyard to prevent component contact. Do not remove this keepout to simplify routing without re-evaluating the manufacturer precaution. Avoid unrelated vias even under the electrode-overlap body region; only electrode-connected copper is excepted by the source. If a different layer count or mounting side is used, re-audit transformed keepout layers and geometry. The keepout is an intentionally conservative engineering interpretation, not a claim that Murata explicitly required removal of every internal plane.

#### Load/current qualification gate

At VIN=12.6 V / VOUT=3.3 V, the typical 2.25 MHz buck frequency, and a conservative effective inductance `3.3 µH × 0.8 tolerance × 0.7 bias = 1.848 µH`, ideal buck ripple is approximately 0.586 A peak-to-peak. This gives:

| Output load | Calculated peak | Peak plus 20% selection margin | RMS copper-loss estimate at 108 mΩ |
|---:|---:|---:|---:|
| 0.8 A design budget | 1.093 A | 1.311 A | 72 mW |
| 1.0 A converter rating | 1.293 A | 1.551 A | 111 mW |

These are design estimates using typical frequency, not complete worst-case validation. They exclude core loss and board-dependent temperature rise. The 2.6 A saturation point provides substantially more ordinary-load margin than XFL3012, but must be checked over temperature and with the actual DCS-control switching waveform. The TPS62162 static high-side current limit can reach 2.45 A; TI's typical 30 ns propagation-delay term can raise an estimated fault peak to roughly 2.60–2.65 A at this conservative inductance. Thus short-circuit/current-limit recovery is an explicit magnetic/thermal scope test, not a guaranteed no-saturation condition. Measure minimum effective L, ripple, output transient response and restart behavior at low/high BEC and with a DSM short.

### Retained reference alternate: XFL3012-332MEC

Sources: [Coilcraft electrical datasheet](https://www.coilcraft.com/getmedia/f76a3c9b-4fff-4397-8028-ef8e043eb200/xfl3012.pdf), Document 747 revision 2025-03-10; [manufacturer land drawing](https://www.coilcraft.com/getattachment/02b6f684-78f7-41d5-8676-8d7ea7ead2c6/xfl3012d-%281%29.gif). Additional library footprint **`F722_Heli:Coilcraft_XFL3012`** is retained for a reviewed alternate only.

- 3.3 µH ±20%; DCR 106 mΩ typical / 127 mΩ maximum
- Isat at 10/20/30% drop: **0.87 / 1.2 / 1.4 A**; thermal figures at 20/40°C rise: **1.2 / 1.6 A**. The earlier 1.6 A reference-table number is not a 1.6 A saturation guarantee
- Body 3.0±0.2 mm square; actual maximum height **1.30 mm**, correcting the 1.2 mm nominal reference-table shorthand
- Two 1.000 × 2.900 mm lands at x=±1.015 (2.030 mm centres); pad 1 right-hand marked start lead, pad 2 left. Courtyard 3.7 × 3.7 mm accounts for maximum body
- Connect the marked start lead to SW for reduced EMI. Changing back to it requires footprint change, stock recheck, and saturation/ripple re-evaluation

### Additional footprint validation

At approximately **17:45 UTC**, the selected XGL/Murata and retained XFL footprints loaded in KiCad 9.0.2; source land drawings were visually inspected, and actual KiCad copper/fabrication/courtyard plots were checked. A standalone six-layer footprint-audit board passed **0 DRC violations / 0 unconnected items**. A separate intentional negative test placed a via and an In1.Cu track beneath the Murata core; both triggered the named keepout rule. This confirms that the keepout is active in the saved footprint, not merely a drawn warning. No whole-controller routing or assembled performance is certified by these tests.


## 9. Bounded startup-ramp analysis — retain C62 = 100 nF

Decision recorded **2026-10-04 20:36 UTC**: retain the selected **C62 = 100 nF, Samsung CL05B104KA5NNNC / C155422, 0402**. No capacitor change is justified solely by the earlier concern that the entire mux ramp would propagate to the IMU. The nominal cases below have useful margin; this section does **not** establish an all-corner startup guarantee. It supplements the startup gate in section 3 and does not change the CAD.

### Primary-data correction: U9 does not track from zero

The [TI TPS6216x datasheet](https://www.ti.com/lit/ds/symlink/tps62160.pdf), SLVSAM2E, sections 7.5, 8.3.4, 8.4.1 and 8.4.4, provides these relevant facts:

- U9 switches off under UVLO. The falling threshold is **2.60 / 2.70 / 2.82 V minimum / typical / maximum**. The rising hysteresis is **180 mV typical**, with no minimum or maximum specified. Thus **2.88 V is a typical rising-start estimate**, not a guaranteed threshold
- The internal soft start has an approximately **50 µs delay** followed by an approximately **25 mV/µs = 25 V/ms** output ramp. Both are descriptive typical values, not guaranteed timing limits
- At VIN = 3 V, high-side FET resistance is **430 mΩ typical**. The **600 mΩ maximum** is specified only for VIN ≥ 6 V; it cannot be silently applied as a guaranteed maximum during startup near 3 V
- In 100%-duty operation, the approximate dropout is `Iout × (RDS(on) + RL)`

Therefore the expression `0.8 × 3.3 V / 0.78 V/ms = 3.38 ms` is **not the modeled IMU 10–90% rise time**. U9 waits until its input is near UVLO release, rapidly raises its output through most of the interval, and may then track the slowly rising input for the last portion. Time spent with the sensor rail near zero is startup latency, not its 10–90% rise time.

### Conditional typical timing model

Assumptions: initially discharged rails; monotonic input; no prebias; constant output load; no current-limit, source-droop or thermal interruption; the buck follows its stated typical internal ramp until limited by input headroom. Use nominal final output 3.3 V, typical UVLO release 2.88 V, and `Rpath = 0.430 + 0.108 = 0.538 Ω`. The 108 mΩ term is L2's specified room-temperature maximum DCR; the FET term is typical, so this combination is still an estimate, not a worst-case bound. PCB resistance and hot winding resistance are excluded.

With time in milliseconds and the input slew `S` in V/ms, relative to U9 UVLO release:

```text
t10 = 0.050 + 0.330 / 25 = 0.0632 ms
t90 = max(0.050 + 2.970 / 25,
          (2.970 + Iload × 0.538 − 2.880) / S)
t10–90 = max(0.1056,
             (2.970 + Iload × 0.538 − 2.880) / S − 0.0632) ms
```

The **0.1056 ms** term is the intrinsic typical 10–90% ramp. A ferrite-filtered sensor waveform and actual startup load must still be evaluated separately.

| Conditional case | S at U9 input | Assumed constant 3.3 V load | Calculated 10–90% |
|---|---:|---:|---:|
| USB, mux tabulated slew | 0.78 V/ms | 0.10 A | 0.121 ms |
| USB, mux tabulated slew | 0.78 V/ms | 0.30 A | 0.259 ms |
| BEC, upstream slew-limited screen | 0.60 V/ms | 0.30 A | 0.356 ms |
| BEC, upstream slew-limited screen | 0.60 V/ms | 0.80 A | 0.804 ms |
| Slower upstream screen | 0.50 V/ms | 0.80 A | 0.978 ms |

For example, after the USB mux **output begins rising**, U9 reaches its typical UVLO at approximately `2.88 / 0.78 = 3.69 ms`; the calculated sensor-rail 10% crossing follows at approximately 3.76 ms. This preceding delay must not be added to the sensor's 10–90% measurement. Total connector-insertion-to-ready time also includes U10 startup, U8 input qualification/settling and firmware initialization, and cannot be bounded from the typical rise number alone.

Two cascaded slew-control stages do not imply addition of their full 10–90% times to the final sensor rail. U8 waits for a valid input and a settling interval, which gives U5 additional time to rise before the core is powered. The 0.60 V/ms BEC rows deliberately screen a case where the upstream ramp reaches the buck; they do not assert that this is the waveform in every insertion sequence.

### U8 timing limits and inconsistent figure

The [TI TPS2121 datasheet](https://www.ti.com/lit/ds/symlink/tps2121.pdf), SLVSEA3F, section 9.3.1/Table 9-1, gives **780 V/s at 5 V and 800 V/s at 12 V** for 100 nF. Section 10.2.4's worked inrush example also uses 780 V/s. Input UVLO release is **2.5–2.8 V**, typical 2.65 V. The input settling interval precedes output soft start; its absolute time and the output slew have no guaranteed minimum/maximum timing specification in the electrical table.

**Source inconsistency:** Figure 7-6 visually indicates roughly **3.5–4 V/ms near 100 nF**, inconsistent with Table 9-1 and the worked example's approximately 0.8 V/ms. The slower explicit table/example value is used for the timing screen above. Neither figure interpolation nor inverse-capacitance scaling is accepted as a guaranteed bound or as a sufficient basis for a smaller C62.

[TI's direct support explanation](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/931081/tps2121-how-to-detect-which-input-is-present-with-ic) says timing depends on voltage, temperature, SS capacitance and load, and supplies no specific timing formula. A numerical all-corner connector-to-start bound cannot be honestly derived from these primary data.

### U5 variation explains the remaining all-corner gap

The [TI TPS25947 datasheet](https://www.ti.com/lit/ds/symlink/tps25947.pdf), SLVSFC9C, sections 6.5, 6.7 and 7.3.5.1, gives **0.61 V/ms typical at VIN = 12 V with 3.3 nF**. Its dVdt charging current spans **0.81 / 2.21 / 3.82 µA minimum / typical / maximum**. C50 is the selected 3.3 nF ±5% C0G part. Proportional sensitivity scaling gives:

```text
slow illustration = 0.61 × (0.81 / 2.21) / 1.05 ≈ 0.213 V/ms
fast illustration = 0.61 × (3.82 / 2.21) / 0.95 ≈ 1.11 V/ms
```

These are **illustrative estimates**, not guaranteed output-slew limits: they scale a typical transfer characteristic, omit the internal circuit's variation and do not model an externally slow BEC. TI's switching-characteristic table also presumes a steady input and an initially discharged load. At 12 V, the listed 3.3 nF turn-on delay is 2.35 ms typical and full 10–90% output rise is 15.37 ms typical; those upstream latency/rise numbers are not the sensor-rail rise time.

An intentionally unfavorable **sensitivity case**, using an early 2.60 V start with no positive hysteresis credit, final output 3.432 V, an **assumed** 0.8 Ω buck/inductor path at 0.8 A and 0.213 V/ms input slope, gives:

```text
(0.9 × 3.432 + 0.8 × 0.8 − 2.60) / 0.213 − 0.0632 ≈ 5.2 ms
```

The 0.8 Ω path is an engineering assumption, not a TI low-VIN limit. This calculation does **not prove failure** and is not a claimed silicon corner; it demonstrates why the absent guarantees cannot be dismissed. Conversely, the favorable nominal table does not prove all-corner compliance. Decreasing C62 cannot force the core input to outrun U5 or the external BEC and shortens the input-settling head start; it is not a universal remedy.

### Inrush and USB operating envelope

The current manifest has C66 = 22 µF ±20% and C74 = 1 µF ±10% directly on `CORE_BUCK_IN`. Their summed positive nominal tolerance is **27.5 µF**, before any temperature allowance and excluding receiver-added capacitance. At the mux's tabulated 0.78 V/ms, this corresponds to approximately **21.5 mA** of capacitor-charging current. This is a useful sizing estimate, not a guaranteed maximum inrush, particularly given the figure/table discrepancy.

U8's RILIM = 80.6 kΩ programs about 1.5 A typical; the datasheet's adjacent 80 kΩ row specifies **1 / 1.5 / 2 A minimum / typical / maximum**. Do not treat the 1 A value as an exact guarantee for the different resistor and all dynamic conditions. U9's fast internal soft start charges tens of microfarads on its output and can encounter either its own or upstream current limiting. The timing model above excludes the resulting stretching.

USB is more restrictive: U10's selected resistor gives approximately **351 mA minimum** current limit shared between both mux branches. A 300 mA core load during the near-unity-conversion part of startup plus a 100 mA ABC load already exceeds that minimum before capacitor charging. This is why the 300 mA USB row is conditional on an adequate available source current and no competing receiver load. Full BEC-rated peripheral loads are not supported in USB-only mode. Startup qualification must establish the allowed USB receiver/load envelope; a C62 change cannot overcome insufficient available current.

### Explicit measured pass condition and release gate

**C62 remains 100 nF. No all-corner guarantee or bench pass is claimed.** Before design/flight release, qualify the assembled prototype as follows:

1. Capture `VX_PROTECTED`, `CORE_BUCK_IN`, `+3V3_CORE` and the actual ICM VDD/VDDIO supply at the sensor-side decoupling pads. Use suitable low-inductance probing and enough time resolution to distinguish the **10 µs lower limit**; record the measurement setup and populated component values
2. For each fully discharged cold start, measure the actual final sensor-rail voltage and its 10% and 90% crossings. **Pass requires 0.010 ms ≤ t10–90 ≤ 3.000 ms at the ICM supply**, with a monotonic rise through that interval, no intervening UVLO restart/current-limit plateau that makes the complete rise exceed the limit, and a valid settled voltage. Include measurement uncertainty; a trace too close to a limit to resolve is inconclusive. A compliant upstream mux trace alone is not a pass
3. Run USB-only insertion at low/high supported USB voltage and the declared maximum USB receiver load; BEC-only insertion at **5.0 V and 12.6 V** with the intended load envelope, including the **0.8 A core/DSM budget and 2 A ABC loading**; and both-source insertion/removal in each order. Exercise realistic slow BEC ramps, repeated insertion, brownout and current-limit recovery over the declared temperature range. Respect each component's temperature limits, including the selected X5R capacitor bodies' 85°C limit
4. Prebiased and partial-brownout recoveries are outside the initially discharged timing model. Record sensor-rail behavior and verify a valid recovery/initialization sequence with stock firmware; a successful USB enumeration by itself does not establish IMU startup compliance. Confirm the separate barometer ramp requirement against its exact assembled MPN
5. Record actual startup current, source droop, U9 input slew and any output plateau alongside the sensor waveform. The supported USB load envelope must leave enough current for startup, not merely permit steady operation after manual pre-powering

If any required case fails, revise sequencing or the current/load envelope from the captured cause. If guaranteed compliance is required **before** these measurements, use a defined input-good enable condition for U9 or equivalent sequencing with appropriately specified thresholds/timing. The typical-only data above cannot justify that guarantee, and a C62-only substitution does not close the gate.
