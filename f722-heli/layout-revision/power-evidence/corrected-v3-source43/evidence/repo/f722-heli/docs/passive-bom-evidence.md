# F722-HELI passive BOM evidence

Research date: **2026-10-04 UTC**. This is an exact-part **prototype BOM proposal**, not a fabrication/flight release or a bench qualification. No CAD is changed by this report. The machine-readable companion is `validation/passive-bom-proposals.json`.

The proposal covers **107 current R/C/FB/L references in 49 groups**, with no missing or duplicate references in the manifest snapshot. The snapshot SHA-256 is `ca4e8e1dde8b436425350a8cf4bf510fa1547758955eb89801afe7069c58974c`. Circuit-owner edits may have incorporated the value/package recommendations while research was in progress; re-run the reference/package comparison before applying the BOM.

## 1. Recommended choices that affect the circuit or placement

- **C53/C54 plus the added C71:** 3 × Murata GRM21BR61E226ME44L, 22 µF / 25 V / X5R / ±20%, **0805**, C86816. All connect to `VX_PROTECTED` and GND. Keep the local low-ESL input bypass. The third 0805 is necessary for the conservative input-capacitance screen described below
- **C55–C57:** 3 × Murata GRM21BR61A476ME15L, 47 µF / 10 V / X5R / ±20%, **0805**, C124129, replacing the provisional 22 µF parts
- **C66:** use the same 22 µF / 25 V / 0805 C86816 as a stronger nominal input-bypass choice. Its qualification is separate from the TPS63070 bank
- **C67:** Murata GRM21BZ71A226ME15L, 22 µF / 10 V / X7R(Murata) / ±20%, **0805**, C907991. The special Z7 temperature specification and the actual biased capacitance are disclosed below
- **R54/R55:** 53.6 kΩ / 10.0 kΩ, both 0.1%, instead of 536 kΩ / 100 kΩ. YAGEO C852835 / C190095 preserves **5.088 V** nominal output while improving leakage/noise sensitivity
- **R16:** 0.15 Ω / 1% / 0.1 W UNI-ROYAL **0603WAF150LT5E**, C45879, using **0603** rather than the original 0402. This is a sourcing/thermal-margin improvement, not a new ESR value
- **C30/C31:** 220 nF / 16 V / X7R / ±10% Samsung CL05B224KO5NNNC, C16772, using **0402** instead of the original 270 nF / 0603. This preserves similarly slow ADC filtering and leaves the divider attenuation unchanged
- **R20–R26:** selected **Panasonic ERJPA2F4700X / C427238**, 470 Ω / 1% / **0.20 W ambient rating**, **0402**, footprint **F722_Heli:Panasonic_ERJPA2_0402**. The normal-duty screen passes through85°C; the previous0603 selection and its evidence are preserved below

No blanket substitution based only on nominal capacitance is approved. The X5R power-capacitor **body** must stay at or below 85°C, including ripple self-heating; an 85°C enclosure ambient does not by itself establish that condition.

## 2. What the capacitance evidence does and does not establish

Primary manufacturer DC-bias plots are typical design-reference characteristics at their stated temperature and AC test amplitude. They are not guaranteed combined-condition production minima. Initial tolerance, temperature dependence, DC bias, AC-amplitude dependence, aging and self-heating are separate effects. The calculations below deliberately expose the applied factors rather than silently calling the nominal value “effective capacitance.”

The factor **0.8 extra engineering allowance** is a design-screening budget for remaining effects, not a manufacturer aging specification or proof that every combined corner is bounded. Qualification still requires manufacturer approval data or measured biased small-signal capacitance and converter testing over the intended operating envelope. Do not multiply unrelated typical plots and label the result a guaranteed limit.

### 2.1 TPS63070 input bank: why a third 0805 is proposed

[TI TPS63070 datasheet](https://www.ti.com/lit/ds/symlink/tps63070.pdf) section 7.3 lists input capacitance minimum 4.7 µF and nominal 10 µF. The explicit effective-capacitance footnote is attached to the output-capacitance row, so the input interpretation is not equally explicit. This design conservatively treats **4.7 µF as an effective input floor** unless TI clarifies otherwise. Section 9.2.2.3 additionally requires enough local buffering to prevent input dips too brief for the UVLO circuitry to react.

The actual TI small-body reference input is GRM21BC71E106ME11, not an arbitrary 10 µF / 25 V part. The reference circuit also has a separate local 10 µF / 0603 input bypass in addition to its two 0805 capacitors. Therefore comparing only the two large capacitors is incomplete.

| Exact part / 0805 unless noted | C typical at 12.6 V | C typical at 14.6 V | Result |
|---|---:|---:|---|
| GRM21BR61E106KA73L, 10 µF / 25 V | 1.654 µF | 1.426 µF | Reject as an assumed 10 µF-effective input part |
| GRM21BC71E106ME11, exact TI 10 µF reference | 2.551 µF | 2.174 µF | Demonstrates that nominal reference values do not equal effective capacitance; observed supplier stock unavailable |
| GRM21BR6YA106KE43L, 10 µF / 35 V | 2.527 µF | 2.175 µF | Higher rating alone does not solve the input-bank screen |
| GRM21BR61H106KE43L, 10 µF / 50 V | 2.477 µF | 2.102 µF | Not better than the examined 35 V part |
| GRM21BR61H475KE51L, 4.7 µF / 50 V | 1.319 µF | 1.111 µF | Does not solve it |
| GRM21BZ71H475KE15L, 4.7 µF / 50 V | 1.945 µF | 1.677 µF | Does not solve it |
| **GRM21BR61E226ME44L, 22 µF / 25 V** | **3.745 µF** | **3.177 µF** | Selected three-part input bank |

Selected worst-voltage screen: `3 × 3.176965 × 0.8 tolerance × 0.85 temperature × 0.8 extra allowance = 5.185 µF`, about 10.3% above 4.7 µF. With only two parts, tolerance/temperature alone gives 4.321 µF before any additional allowance, so the two-pad bank does not pass this conservative screen.

Samsung cross-checks did not rescue the two-pad layout: CL21A226MAQNNNE and CL21A226MAYNNNE retain approximately 3.116 and 2.865 µF at 14.6 V; CL21A106KAYNNNE about 1.454 µF. Its current main LCSC C15850 page was out of stock despite older descriptive/search pages reporting large inventory.

A 1206 comparison was also checked. Current-production GRM31CC81E226ME11L X6S retains 5.869 µF at 14.6 V; one such 1206 plus one selected 0805 screens to only 4.658 µF when X6S uses a 0.78 temperature factor. Two 1206s screen to 5.859 µF, but enlarge both pads and had weak/stale stock evidence. Older GRM31CR61E226KE15L is marked **to be discontinued** and retained only 4.058 µF, so it is not recommended. Adding one 0805 is the smallest verified layout change among these candidates.

Primary selected curve: [GRM21BR61E226ME44](https://pim.murata.com/en-global/pim/details/?partNum=GRM21BR61E226ME44%23). The 14.6 V calculation covers the eFuse clamp corner used in the power evidence; normal BEC maximum is 12.6 V. Scope `VX_PROTECTED` at converter pins with actual cabling, eFuse ramp, peripheral load steps, both-source transitions and input current limiting.

### 2.2 TPS63070 output bank

TI gives a 15 µF effective output minimum for nominal 1.5 µH and also requires effective C in µF to be at least ten times effective L in µH. With +20% inductance tolerance, the conservative comparison floor is **18 µF**. The maximum output-capacitance value is 470 µF.

| Output candidate, three 0805 parts | Per part at 5.2 V | Bank typical | Screen before assembly qualification |
|---|---:|---:|---:|
| 22 µF / 16 V X5R GRM21BR61C226ME44L | 9.798 µF | 29.394 µF | Inadequate additional margin after tolerance, temperature and aging allowance |
| Exact TI X6S GRM21BC81C226ME44L | 9.798 µF | 29.394 µF | Wider temperature range, but ±22% temperature change consumes more capacitance margin |
| **47 µF / 10 V X5R GRM21BR61A476ME15L** | **13.926 µF** | **41.779 µF** | **22.728 µF** with 0.8 × 0.85 × 0.8 factors |

The selected bank is 141 µF nominal / 169.2 µF at +20%, below the 470 µF ceiling. At nominal 5.088 V it is approximately 42.792 µF typical. Increased capacitance changes startup/inrush and transient behavior; confirm that the converter reaches regulation with attached loads and that source mux handover does not create repeated restarts. [Selected manufacturer curve](https://pim.murata.com/en-global/pim/details/?partNum=GRM21BR61A476ME15%23)

### 2.3 C66 and C67 on TPS62162

[TI TPS62160-family datasheet](https://www.ti.com/lit/ds/symlink/tps62160.pdf) recommends 10 µF nominal input capacitance for most applications. It does **not** state a universal 10 µF-effective input floor. C66 = selected 22 µF / 25 V C86816 is a useful nominal upgrade in the same 0805; at 14.6 V it is only 3.177 µF typical, or 1.728 µF under the stated screening factors. This must be validated against real input droop, source impedance, current ripple and mux behavior rather than mislabeled a 10 µF-effective pass.

C67 GRM21BZ71A226ME15L has about **14.634 µF typical at 3.3 V** (25°C, 0.5 Vrms), rather than 22 µF effective. Murata Z7 is X7R(Murata), with its ±15% temperature-change specification defined at half rated voltage. It is not a promise that total bias loss stays within ±15%. TPS62162 Table 2 gives proven **nominal** LC combinations and assumes typical ±20% variation; this candidate’s full biased LC network therefore retains a loop/transient validation gate. Consult [TI SLVA463](https://www.ti.com/lit/an/slva463/slva463.pdf) before asserting a broader stability envelope. [C67 manufacturer curve](https://pim.murata.com/en-global/pim/details/?partNum=GRM21BZ71A226ME15%23)

### 2.4 Small MLCCs and C7 VCAP

Current Samsung manufacturer graph data provides the following useful typical values at 25°C / 1 Vrms / 1 kHz. Exact primary links appear in the component table and JSON.

| Family | Relevant bias | Typical effective estimate |
|---|---:|---:|
| CL05B104KO5NNN, 100 nF / 16 V / 0402 | 3.3 V | 96.1 nF |
| CL05B104KA5NNN, 100 nF / 25 V / 0402 | 3.3 V | 96.1 nF |
| CL05B103KO5NNN, 10 nF / 16 V / 0402 | 3.3 V | 10.14 nF |
| CL10A475KP8NNN, 4.7 µF / 10 V X5R / 0603 | 3.3 V | 2.10 µF |
| CL10B225KP8NNN, 2.2 µF / 10 V / 0603 | 3.3 V | 1.91 µF |
| CL10B105KP8NNN, 1 µF / 10 V / 0603 | 3.3 / 5.25 V | 0.919 / 0.823 µF |
| CL10B105KO8NNN, 1 µF / 16 V / 0603 | 5.25 V | 0.823 µF |
| CL10B105KA8NNN, 1 µF / 25 V / 0603 | 12.6 / 16 V | 0.459 / 0.352 µF |

The current Samsung CL10B105KA8NNN curve differs from an older 2013 distributor-hosted manufacturer characteristic sheet. The current data above is used here; do not mix old and new curve estimates as though they were identical production guarantees. For local 1 µF / 25 V bypasses, even a nominally large capacitor can retain well under 1 µF at high BEC voltage.

C7’s exact nominal candidate is **Murata GRM188Z71A475KE15D**, 4.7 µF / 10 V / X7R(Murata) / ±10% / 0603, C913474. Its characteristic plot suggests roughly 4.6 µF at 1.2 V before other effects, 3.4 µF at 3.3 V, and 2.4–2.6 µF near 5.1–5.25 V. It is also the nominal candidate for C61/C68/C70. [Manufacturer reference sheet](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM188Z71A475KE15-01A.pdf) · [Manufacturer-authored characteristic plot](https://static6.arrow.com/aropdfconversion/d900e8518e5901e628f4aafed74df816f12c8a36/grm188z71a475ke15.pdf)

[ST DS11853 Rev 9](https://www.st.com/resource/en/datasheet/stm32f722rc.pdf) Table 19 specifies 4.7 µF and 0.1–0.2 Ω ESR for the single-VCAP LQFP64 package, but gives no capacitance-tolerance band or ESR test frequency. This is a nominal matching proposal; it does not establish an ST-approved effective-capacitance range, and it cannot support a literal claim of **at least 4.7 µF retained**. Do not upsize the internal-regulator capacitor without checking permitted stability conditions.

The exact Murata plot suggests ESR around 0.02 Ω at 100 kHz and 0.005 Ω near 1 MHz. With R16 = 0.15 Ω, the nominal totals are approximately 0.17 and 0.155 Ω at those example frequencies. R16’s ±1% tolerance and ±800 ppm/°C from 25 to 85°C give approximately 0.1414–0.1588 Ω before capacitor ESR; cold extremes must also be checked. These estimates do not prove the required ESR band at all frequencies, bias, temperature or aging. Qualify MCU startup/load steps and the VCAP network instead of labeling the resistor alone sufficient.

C5 may optionally be consolidated to the same Murata 4.7 µF X7R(Murata) part for better observed DC-bias retention and wider temperature class, but the primary JSON preserves its requested X5R nominal-match candidate. All 1 µF / 0603 positions may likewise be explicitly uprated to the 25 V Samsung part to reduce line items; that does not eliminate high-voltage bias loss.

## 3. ADC filter area reduction

Use C30/C31 = **CL05B224KO5NNNC**, 220 nF / 16 V / X7R / ±10% / 0402, C16772. The [current Samsung model](https://product.samsungsem.com/mlcc/CL05B224KO5NNN.do) gives 218.15 nF at 2.0 V and 217.55 nF at 2.1 V (25°C, 1 Vrms, 1 kHz). This is a useful near-nominal bias result at the actual ADC voltage, not a guaranteed tolerance-inclusive minimum.

| Filter | Thevenin resistance | Original 270 nF nominal τ / pole | Proposed 220 nF nominal τ / pole |
|---|---:|---:|---:|
| BEC, 105 kΩ / 20 kΩ | 16.80 kΩ | 4.536 ms / 35.09 Hz | 3.696 ms / 43.06 Hz |
| BUS, 68 kΩ / (16 kΩ + 16 kΩ) | 21.76 kΩ | 5.875 ms / 27.09 Hz | 4.787 ms / 33.25 Hz |

The attenuation factors remain exactly 0.16 / 0.32 nominal. The capacitor is not firmware-visible calibration. Verify ADC sampling settling and ripple with stock firmware. If the original 270 nF / 0603 is retained instead, YAGEO CC0603KRX7R7BB274/C519443 was identified with 2,050 LCSC stock, but no exact manufacturer bias curve was retrieved for it; do not call that alternate bias-qualified.

## 4. Resistor electrical checks

### R20–R26: selected 0402 normal signal-duty envelope

**Selected 2026-10-04 19:52 UTC: Panasonic ERJPA2F4700X / C427238,470 Ω ±1%,0.20 W at70°C ambient,0402.** The separate0.25 W rating applies at100°C terminal temperature and is not an ambient rating. Panasonic’s ambient curve derates linearly to zero at155°C, giving **164.71 mW at85°C**. With−1% initial tolerance and−100 ppm/°C over25→85°C, Rmin=462.5082 Ω: dissipation is **25.47 mW at3.432 V** or **65.40 mW at5.5 V**. Both remain below the derated allowance. When the rating method is uncertain, Panasonic gives priority to terminal temperature; verify mounted-board thermal conditions and keep the case below155°C. The50 V limiting-element voltage does not override the lower continuous limit from√(P×R), approximately8.73 V at85°C using Rmin. [Panasonic datasheet,28-Mar-2026](https://industrial.panasonic.com/cdbs/www-data/pdf/RDO0000/AOA0000C331.pdf)

Use **F722_Heli:Panasonic_ERJPA2_0402**, two0.50×0.50 mm pads centered atx=±0.50 mm, giving0.50 mm inner gap and1.50 mm outer span; suggested courtyard2.00×1.10 mm. This follows Panasonic’s0.50–0.60 mm gap,1.40–1.60 mm span and0.40–0.60 mm pad-width recommendation. The installed generic R_0402_1005Metric has a slightly smaller0.48 mm gap and larger0.64 mm width, so it is not an exact recommendation match. The part is nonpolar. Compared with the existing2.96×1.46 mm0603 courtyard, seven new courtyards recover about **14.85 mm²**. [Manufacturer land pattern,24-Dec-2025](https://industrial.panasonic.com/cdbs/www-data/pdf/RDM0000/DMM0000COL17.pdf)

Pulse and ESD qualification limits remain explicit: the pulse plots are **reference data, not guaranteed ratings**, at room temperature for1 µs–1 s pulses, period≥10 s,≤1,000 cycles, with up to±5% resistance change. Both the applicable pulse-power curve andVpeak<100 V apply. The separate ESD reference comparison uses±1 kV,100 pF and1.5 kΩ; it does not qualify IEC61000-4-2 immunity for this board. No pulse-survival equivalence to the superseded0603, arbitrary surge survival or raw-BEC wrong-wire survival is claimed. Preserve the header protection and first-article transient/thermal tests. [Panasonic pulse reference](https://industrial.panasonic.com/cdbs/www-data/pdf/RDO0000/ast-ind-161285.pdf)

**Superseded 0603 selection, retained as evidence:**

The manufacturer UNI-ROYAL thick-film datasheet, February 12, 2019 V.3, rates 0603 WA parts at 0.1 W up to 70°C, then linearly derates to zero at 155°C. The 470 Ω 1% part is ±100 ppm/°C. [Exact part and manufacturer datasheet](https://jlcpcb.com/partdetail/0603WAF4700T5E/C23179)

- Allowable continuous power at 85°C: `0.1 × (155−85)/(155−70) = 82.35 mW`
- At the stated 25.3 mW ordinary DC worst case, margin is substantial
- Conservative 5.5 V continuously across the resistor, with resistance minimized for −1% and −100 ppm/°C across a 60°C rise: `Rmin = 470 × 0.99 × 0.994 = 462.51 Ω`; `P = 5.5²/Rmin = 65.40 mW`, below 82.35 mW
- This supports the specified normal signal-duty envelope. It is not a raw-12.6 V miswire, arbitrary surge, short-circuit or ESD survival claim. PCB heating and nearby regulator losses still affect local ambient

### Feedback divider and precision parts

TPS63070 section 9.2.2.1 requires at least 2 µA divider current, equivalent to Rbottom ≤400 kΩ, and explicitly recommends lower resistance for accuracy/robustness. Thus **53.6 kΩ / 10.0 kΩ** is allowed and preserves `0.8 × (1 + 53.6/10) = 5.088 V`. Divider current increases from 8 to 80 µA, only 72 µA extra. With the datasheet’s maximum 100 nA FB leakage, the upper-resistor-related voltage error falls from 53.6 mV to 5.36 mV.

All listed precision resistors remain 0.1% and ±25 ppm/°C in 0402. Primary YAGEO RT-series V.16 (May 6, 2025) and Viking ARG-series (January 2022) documents were inspected. They specify 50 V and 1/16 W for the selected 0402 values; normal divider dissipation is far below derated power. Temperature coefficients are individual limits, not ratio tracking guarantees. Do not substitute an ordinary 1% resistor merely because its nominal value matches.

### R16 availability choice

0402WGF150LTCE/C423234 was an exact 0402 / 0.15 Ω / 1% candidate but only **19** JLC pieces were orderable. YAGEO RL0402FR-070R15L/C728420 showed only 3 stock and a pre-order minimum of 1,347. The preferred **0603WAF150LT5E/C45879** had **17,095 stock / 17,051 orderable** at 18:34 UTC. It retains the same resistance/tolerance/TCR with 0.1 W rating; the explicit 0603 footprint change is justified by stock and thermal margin.

## 5. Exact grouped passive BOM proposals

Inventory counts below are observations, not reservations. **JLC assembly inventory and LCSC retail stock are separate.** A supplier code/catalogue entry alone does not prove assembly availability. “Search stock” is a live rendered, priced JLC catalog result; “orderable” is recorded separately where the detail page exposed it. The JSON preserves full inventory wording, supplier URLs, manufacturer URLs, existing footprint/net mapping and required footprint changes.

### Resistors

| References | Proposed value | Exact MPN / code | Package | Inventory observation |
|---|---|---|---|---|
| R1, R3, R4, R5, R6, R64, R69 | 10k / ±1% | [0402WGF1002TCE](https://jlcpcb.com/partdetail/26487-0402WGF1002TCE/C25744) / C25744 | 0402 | JLCPCB 21,682,859 |
| R2, R10, R11 | 2.2k / ±1% | [0402WGF2201TCE](https://jlcpcb.com/partdetail/26622-0402WGF2201TCE/C25879) / C25879 | 0402 | JLCPCB 2,218,028 |
| R7, R8, R36, R37 | 4.7k / ±1% | [0402WGF4701TCE](https://jlcpcb.com/partdetail/26643-0402WGF4701TCE/C25900) / C25900 | 0402 | JLCPCB 15,439,969 |
| R14, R15 | 5.1k / ±1% | [0402WGF5101TCE](https://jlcpcb.com/partdetail/26648-0402WGF5101TCE/C25905) / C25905 | 0402 | JLCPCB 5,950,001 |
| R9 | 0R / jumper; <50 mΩ max, per series datasheet | [0402WGF0000TCE](https://jlcpcb.com/partdetail/17853-0402WGF0000TCE/C17168) / C17168 | 0402 | JLCPCB 9,192,090 |
| R30, R31, R32, R33, R34, R35, R38 | 22R / ±1% | [0402WGF220JTCE](https://jlcpcb.com/partdetail/25835-0402WGF220JTCE/C25092) / C25092 | 0402 | JLCPCB 4,603,622 |
| R39, R45 | 220R / ±1% | [0402WGF2200TCE](https://jlcpcb.com/partdetail/25834-0402WGF2200TCE/C25091) / C25091 | 0402 | JLCPCB 1,418,208 |
| R50 | 1.5M / ±1% | [0402WGF1504TCE](https://jlcpcb.com/partdetail/23001-0402WGF1504TCE/C22276) / C22276 | 0402 | JLCPCB 56,324 |
| R51 | 390k / ±1% | [0402WGF3903TCE](https://jlcpcb.com/partdetail/26525-0402WGF3903TCE/C25782) / C25782 | 0402 | JLCPCB 4,731 |
| R52 | 750R / ±1% | [0402WGF7500TCE](https://jlcpcb.com/partdetail/25875-0402WGF7500TCE/C25132) / C25132 | 0402 | JLCPCB 964,211 |
| R53 | 4.7k / ±1% | [0603WAF4701T5E](https://jlcpcb.com/partdetail/23889-0603WAF4701T5E/C23162) / C23162 | 0603 | JLCPCB 22,394,157 |
| R56, R57 | 100k / ±1% | [0402WGF1003TCE](https://jlcpcb.com/partdetail/26484-0402WGF1003TCE/C25741) / C25741 | 0402 | JLCPCB 8,209,410 |
| R58 | 47k / ±1% | [0402WGF4702TCE](https://jlcpcb.com/partdetail/26535-0402WGF4702TCE/C25792) / C25792 | 0402 | JLCPCB 5,532,230 |
| R65 | 330k / ±1% | [0402WGF3303TCE](https://jlcpcb.com/partdetail/26521-0402WGF3303TCE/C25778) / C25778 | 0402 | JLCPCB 152,106 |
| R66 | 80.6k / ±1% | [0402WGF8062TCE](https://jlcpcb.com/partdetail/26664-0402WGF8062TCE/C25921) / C25921 | 0402 | JLCPCB 190,390 |
| R67 | 66.5k / ±1% | [0402WGF6652TCE](https://jlcpcb.com/partdetail/30135-0402WGF6652TCE/C29381) / C29381 | 0402 | JLCPCB 20,028 |
| R68 | 1k / ±1% | [0402WGF1001TCE](https://jlcpcb.com/partdetail/12256-0402WGF1001TCE/C11702) / C11702 | 0402 | JLCPCB 7,106,354 |
| R70 | 45.3k / ±1% | [0402WGF4532TCE](https://jlcpcb.com/partdetail/27729-0402WGF4532TCE/C26980) / C26980 | 0402 | JLCPCB 18,471 |
| R40 | 105k / 0.1% / 25ppm/C | [ARG02BTC1053](https://jlcpcb.com/partdetail/VikingTech-ARG02BTC1053/C2984407) / C2984407 | 0402 | JLCPCB 13,256 |
| R41 | 20.0k / 0.1% / 25ppm/C | [RT0402BRD0720KL](https://jlcpcb.com/partdetail/YAGEO-RT0402BRD0720KL/C705630) / C705630 | 0402 | JLCPCB 310,014 / 280,408 orderable |
| R42 | 68.0k / 0.1% / 25ppm/C | [ARG02BTC6802](https://jlcpcb.com/partdetail/VikingTech-ARG02BTC6802/C5266108) / C5266108 | 0402 | JLCPCB 10,239 / 10,208 orderable |
| R43, R44 | 16.0k / 0.1% / 25ppm/C | [RT0402BRD0716KL](https://jlcpcb.com/partdetail/YAGEO-RT0402BRD0716KL/C513647) / C513647 | 0402 | JLCPCB 2,071 |
| R54 | 53.6k / 0.1% / 25ppm/C | [RT0402BRD0753K6L](https://jlcpcb.com/partdetail/YAGEO-RT0402BRD0753K6L/C852835) / C852835 | 0402 | JLCPCB 3,152 / 2,674 orderable |
| R55, R61, R63 | 10.0k / 0.1% / 25ppm/C | [RT0402BRD0710KL](https://jlcpcb.com/partdetail/YAGEO-RT0402BRD0710KL/C190095) / C190095 | 0402 | JLCPCB 742,623 / 358,456 orderable |
| R60 | 18.0k / 0.1% / 25ppm/C | [RT0402BRD0718KL](https://jlcpcb.com/partdetail/YAGEO-RT0402BRD0718KL/C852579) / C852579 | 0402 | JLCPCB 96,132 |
| R62 | 12.7k / 0.1% / 25ppm/C | [RT0402BRD0712K7L](https://jlcpcb.com/partdetail/YAGEO-RT0402BRD0712K7L/C852509) / C852509 | 0402 | JLCPCB 10,852 / 10,826 orderable |
| R16 | 0.15R / 1% / 0.1W / 800ppm/C | [0603WAF150LT5E](https://jlcpcb.com/partdetail/46882-0603WAF150LT5E/C45879) / C45879 | 0603 | JLCPCB 17,095 / 17,051 orderable |
| R20, R21, R22, R23, R24, R25, R26 | 470R / 1% / 0.20W ambient / 100ppm/C | [ERJPA2F4700X](https://jlcpcb.com/partdetail/PANASONIC-ERJPA2F4700X/C427238) / C427238 | 0402, Panasonic_ERJPA2_0402 | JLCPCB31,550 /28,898 orderable,19:48 UTC |

Ordinary resistor observations: 18:30–18:35 UTC; precision groups: 18:24–18:41 UTC. R9 is a zero-ohm jumper with manufacturer limits <50 mΩ / 1 A, not a meaningful “0 Ω ±1%” accuracy promise. R16 and R53 are0603; R20–R26 now use the dedicated Panasonic0402 footprint, and the other ordinary groups remain0402. See JSON for exact reference lists rather than assuming numerical ranges contain no gaps.

### Capacitors

| References | Proposed value | Exact MPN / code | Package | Inventory observation |
|---|---|---|---|---|
| C1, C2, C3, C4, C6, C9, C10, C12, C14, C16, C17, C58 | 100nF / 16V / X7R | [CL05B104KO5NNNC](https://www.lcsc.com/product-detail/C1525.html) / C1525 | 0402 | LCSC 9,168,500; MOQ100; JLC Basic; official basic-parts listing showed 22,167,170; direct detail omits stock |
| C5 | 4.7uF / 10V / X5R | [CL10A475KP8NNNC](https://www.lcsc.com/product-detail/C1705.html) / C1705 | 0603 | LCSC 824,200; MOQ50; JLC Not independently stock-verified |
| C7, C61, C68, C70 | 4.7uF / 10V / X7R | [GRM188Z71A475KE15D](https://www.lcsc.com/product-detail/C913474.html) / C913474 | 0603 | LCSC 8,310; MOQ10; JLC Extended catalog verified; stock not exposed |
| C8, C15, C59, C60, C65, C69 | 1uF / 10V / X7R | [CL10B105KP8NNNC](https://www.lcsc.com/product-detail/C95843.html) / C95843 | 0603 | LCSC 604,500; MOQ50; JLC Not independently stock-verified |
| C20 | 1uF / 16V / X7R | [CL10B105KO8NNNC](https://www.lcsc.com/product-detail/C59782.html) / C59782 | 0603 | LCSC 189,300; MOQ50; JLC Not independently stock-verified |
| C51, C52, C64 | 1uF / 25V / X7R | [CL10B105KA8NNNC](https://www.lcsc.com/product-detail/C29936.html) / C29936 | 0603 | LCSC Direct main page out of stock; older search/image listings conflict; JLC Extended; retrieved official JLC page996,355 stock/856,497 available order qty |
| C11 | 10nF / 16V / X7R | [CL05B103KO5NNNC](https://www.lcsc.com/product-detail/C318577.html) / C318577 | 0402 | LCSC 69,100; MOQ100; JLC Not independently stock-verified |
| C13 | 2.2uF / 10V / X7R | [CL10B225KP8NNNC](https://www.lcsc.com/product-detail/C100082.html) / C100082 | 0603 | LCSC 317,840; MOQ20; JLC Extended; retrieved official JLC page363,362 stock/344,914 available |
| C18, C19 | 15pF / 50V / C0G | [CL05C150JB5NNNC](https://www.lcsc.com/product-detail/C86285.html) / C86285 | 0402 | LCSC 80,600; MOQ100; JLC Not independently stock-verified |
| C50 | 3.3nF / 50V / C0G | [GRM1555C1H332JE01D](https://www.lcsc.com/product-detail/C1518207.html) / C1518207 | 0402 | LCSC 4,480; MOQ20; JLC Not independently stock-verified |
| C62 | 100nF / 25V / X7R | [CL05B104KA5NNNC](https://www.lcsc.com/product-detail/C155422.html) / C155422 | 0402 | LCSC 236,350; MOQ50; JLC Extended catalog verified; stock not exposed |
| C63 | 1nF / 50V / C0G | [CL05C102JB5NNNC](https://www.lcsc.com/product-detail/C307441.html) / C307441 | 0402 | LCSC 304,200 on directly opened page; MOQ50; JLC Not independently stock-verified |
| C30, C31 | 220nF / 16V / X7R / 10% | [CL05B224KO5NNNC](https://jlcpcb.com/partdetail/17456-CL05B224KO5NNNC/C16772) / C16772 | 0402 | JLCPCB 2,347,039 / 2,223,775 orderable |
| C53, C54, C71 | 22uF / 25V / X5R / 20% | [GRM21BR61E226ME44L](https://www.lcsc.com/product-detail/C86816.html) / C86816 | 0805 | LCSC 286,715 |
| C66 | 22uF / 25V / X5R / 20% | [GRM21BR61E226ME44L](https://www.lcsc.com/product-detail/C86816.html) / C86816 | 0805 | LCSC 286,715 |
| C55, C56, C57 | 47uF / 10V / X5R / 20% | [GRM21BR61A476ME15L](https://www.lcsc.com/product-detail/C124129.html) / C124129 | 0805 | LCSC 32,355 |
| C67 | 22uF / 10V / X7R(Murata) / 20% | [GRM21BZ71A226ME15L](https://www.lcsc.com/product-detail/C907991.html) / C907991 | 0805 | LCSC 146,915 |
| C72, C73 | 10uF / 25V / X5R / 20% | [TMK107BBJ106MA-T](https://jlcpcb.com/partdetail/TaiyoYuden-TMK107BBJ106MAT/C386081) / C386081 | 0603 | JLCPCB 79,969 / 78,393 orderable |

C29936 is the notable inventory mismatch: the current LCSC main page showed out of stock, while a retrieved official JLC page reported stock/orderable inventory. Do not merge those channels into a single availability assertion. C7/C61/C68/C70 C913474 latest direct LCSC count was 8,310, superseding an older 9,510 snapshot.

### Ferrites and power inductors

| References | Exact MPN / code | Package / local footprint | Inventory |
|---|---|---|---|
| FB1, FB2 | [BLM15AG601SN1D](https://jlcpcb.com/partdetail/BLM15AG601SN1D/C76884) / C76884 | F722_Heli:Murata_BLM15AG_0402 | JLCPCB 1,447,835 / 1,430,240 orderable (19:27 UTC update) |
| L1 | [XGL4020-152MEC](https://jlcpcb.com/partdetail/Coilcraft-XGL4020152MEC/C7417180) / C7417180 | F722_Heli:Coilcraft_XGL4020 | JLCPCB 2,316 / 2,309 orderable |
| L2 | [DFE322512F-3R3M=P2](https://jlcpcb.com/partdetail/3784028-DFE322512F_3R3MP2/C3221010) / C3221010 | F722_Heli:Murata_DFE322512F | JLCPCB 4,209 / 4,198 orderable |

FB1/FB2 now select **BLM15AG601SN1D**, 600 Ω ±25% at **100 MHz**, 0.3 A, maximum initial DCR 0.52 Ω, 0402; see Section9 for the exact land and voltage-drop screen. The earlier0603 BLM18AG601SN1D had0.5 A rating and0.38 Ω maximum initial DCR. Neither part specifies600 Ω at the2.4 MHz converter frequency. Manufacturer ENFA0018 and ENFA0003 data were inspected. Validate ferrite/capacitor resonance, sensor supply ripple and the IMU power-up ramp. L1/L2 detailed primary sources, current curves, land patterns and the Murata core keepout are in `power-evidence.md`; earlier dated inventory is carried forward here.

## 6. First-article and release checklist

1. Reconcile every proposal with the current schematic manifest; preserve exact ratios, net names, package changes and the third input capacitor
2. Recheck supplier stock and production status before purchase; no parts have been purchased/reserved
3. Measure biased small-signal capacitance and ripple self-heating at actual rail voltage. Maintain X5R body≤85°C or revise the dielectric/package selection
4. Test low/high BEC voltage, input cable impedance, hot plug, simultaneous peripheral/core/DSM load, eFuse ramp and current-limit recovery. Scope converter VIN at the IC pins
5. Check output loop stability/load steps and input-source mux behavior after larger capacitor values. Confirm startup with attached loads
6. Qualify C7/R16 VCAP startup and dynamic behavior against an allowed ST capacitance/ESR band. Typical plots do not resolve the unspecified measurement band
7. Verify ADC settling/filtering and crystal startup/load capacitance with stock firmware; capacitor nominal matching alone does not validate those functions
8. Review actual stencil apertures and solder-joint process after any 0402/0603/0805 changes. No assembly-process or flight-readiness claim is made by this report

### Evidence sources and freshness

Primary evidence consists of the linked TI/ST datasheets, current Murata product curves, current Samsung product-page graph data, manufacturer-authored YAGEO/Viking/UNI-ROYAL series PDFs obtained through their verified supplier pages, and the Murata ferrite specification. Manufacturer plots were read as typical curves at displayed conditions; no hidden procurement API or guessed part-code inventory was used. The machine-readable proposal carries source URLs and numerical points for reproducibility.

## 7. U6 local high-frequency bypasses C72/C73

Added to the proposal after the bulk-capacitor audit: **C72/C73 = Taiyo Yuden TMK107BBJ106MA-T**, 10 µF / 25 V / X5R / ±20% / **0603**, JLC **C386081**. This is the exact capacitor that TI names for C1 (VIN) and C4 (VOUT) in TPS63070 Table 6 and its reference BOM. Section 11.1 calls for ceramics of 0603 or smaller directly at VIN/GND and VOUT/GND, with additional 0805 capacitance for bulk requirements. [TI source](https://www.ti.com/lit/ds/symlink/tps63070.pdf)

- C72: `VX_PROTECTED` to GND, directly at U6 VIN power pins
- C73: `+5V_BEC` to GND, directly at U6 VOUT power pins
- Use short, wide power/ground loops; a remote same-net bypass does not provide the same high-frequency path
- Preserve all three selected 0805 input and all three selected 0805 output capacitors. **No capacitance credit from C72/C73 is needed for the reported conservative bulk screens**, so their nominal 10 µF must not be added as 10 µF effective at high BEC voltage
- Live JLC on 2026-10-04 18:49 UTC: **79,969 stock / 78,393 orderable**. [Exact supplier page](https://jlcpcb.com/partdetail/TaiyoYuden-TMK107BBJ106MAT/C386081)
- Manufacturer now identifies TMK107BBJ106MA-T as a renamed legacy number; the preferred general-equipment successor is **MSAST168BB5106MTNA01**. The legacy exact TI part has current supplier inventory, but later production orders should confirm the successor and supplier mapping rather than silently substituting by name. [Manufacturer part-number transition](https://ds.yuden.co.jp/TYCOMPAS/eu/detail?pn=TMK107BBJ106MA-T&u=M)
- X5R body temperature remains limited to 85°C. The manufacturer's data is for general electronics; this BOM does not establish suitability for a safety-certified aviation system

A stocked same-nominal Samsung candidate also exists, CL10A106MA8NRNC/C96446 (live JLC 3,331,476 stock / 2,314,832 orderable at 18:49 UTC), but the proposal uses the exact TI reference instead. No Samsung substitution is needed merely for stock.

HF-bypass bias evidence was also inspected: the exact-family manufacturer-authored [TMK107BBJ106MA characteristic sheet](https://media.digikey.com/pdf/Data%20Sheets/Taiyo%20Yuden%20PDFs%20URL%20links/TMK107BBJ106MA-T_SS.pdf), page 2, shows approximately **4.5–5.0 µF around5.2 V** and **1.2–1.6 µF around14.6 V**, read visually from its curve. These are approximate reference readings, not production limits; they support excluding nominal10 µF from the bulk-floor arithmetic. Maximum part height is1.0 mm. Validate the final HF loop impedance and ripple temperature rise on the first article.

## 8. Header ESD array shrink considered, retained original — 2026-10-04

**Decision: retain U12/U13 USBLC6-4SC6 for this revision.** The current placement fits. Relocate the mux control capacitors locally instead of changing the header protection solely for area.

The verified smaller candidate was Texas Instruments **TPD4E001DRLR / C527516**, a four-channel external-VCC/GND steering array in DRL/SOT-563. Live JLC at 19:01 UTC: **7,268 stock / 7,250 orderable**. Its exact DRL0006A copper lands are six 0.67 × 0.30 mm pads at x=±0.74 mm, y=−0.50/0/+0.50 mm. Pins 1/2/4/5 are signals, 3 is GND, and 6 is VCC. A conservative 2.65 × 2.50 mm courtyard including mold-flash allowance would recover about 14.6 mm² across two arrays before bypass capacitors, relative to two 4.1 × 3.4 mm courtyards. [TI datasheet](https://www.ti.com/lit/ds/symlink/tpd4e001.pdf), [exact JLC identity](https://jlcpcb.com/partdetail/TexasInstruments-TPD4E001DRLR/C527516)

The tradeoff is significant: TI requires **100 nF adjacent to each VCC pin**, and its central TVS has **11 V minimum breakdown**, compared with the USBLC6 family's 6 V minimum. Externally biased operation preserves steering to the 3.3 V rail, but neither that topology nor the ESD rating guarantees a safe instantaneous MCU voltage. The TI part's normal I/O range is 0…VCC and absolute maximum is VCC+0.3 V; no continuous forward-clamp current rating is specified. It is not a substantiated sustained 5 V-to-3.3 V level converter. The added local bypasses and changed clamping behavior reduce the area benefit. The candidate is therefore **not selected**. No CAD change was made by this research.

## 9. Selected 0402 analog-rail ferrites — 2026-10-04 19:32 UTC

**Selected update: Murata BLM15AG601SN1D / C76884 for FB1 and FB2.** The parent accepted this change at19:31 UTC. The previous selected proposal is BLM18AG601SN1D / C19330 in **0603**, so this is a real footprint change. Limit these two branches to STM32 VDDA and ICM-42688-P supplies; do not move MCU digital VDD or DSM load onto them.

- 600 Ω ±25% at 100 MHz, **300 mA rated current at 125°C**, −55…125°C operating range, 1.00 × 0.50 × 0.50 mm body, each ±0.05 mm
- Maximum DCR: **0.52 Ω initial / 0.62 Ω after reliability tests**. These are standard-condition resistance specifications, not a guaranteed hot-resistance curve
- Live JLC, 2026-10-04 19:27 UTC: **1,447,835 stock / 1,430,240 orderable**, Extended, exact Murata MPN; snapshot only
- Murata's recommended BLM15AG land uses 0.50 mm width, 0.40 mm inner gap, and 1.20–1.40 mm overall copper span; equivalently pad lengths 0.40–0.50 mm. Use project-local **F722_Heli:Murata_BLM15AG_0402**, two0.50 ×0.50 mm pads atx=±0.45 mm, giving1.40 mm span and0.40 mm gap; suggested courtyard1.90 ×1.10 mm. The part is nonpolar. The installed KiCad L_0402_1005Metric uses0.59 ×0.64 mm pads atx=±0.485 mm,1.56 mm span and0.38 mm gap, so it is not an exact match to Murata’s public recommendation

Sources: [Murata current product information](https://pim.murata.com/en-global/pim/details/?partNum=BLM15AG601SN1%23), [manufacturer reference specification ENFA0018](https://www.murata.com/products/productdata/8796740059166/ENFA0018.pdf?1730777411000=), [JLC identity/stock](https://jlcpcb.com/partdetail/BLM15AG601SN1D/C76884). Manufacturer-authored JENF243A-0018AJ-01 obtained through JLC was inspected; the current Murata product page independently confirms the rating, DCR and in-production status.

**Voltage-drop screen:** 20 mA through 0.62 Ω loses 12.4 mV; 50 mA loses 31 mV. STM32F722 Table 67 gives maximum 1.8 mA ADC analog current plus 0.5 mA reference current; even budgeting that for all three ADCs and 0.85 mA each for all three PLL analog contributions gives 9.45 mA before other analog blocks. A **20 mA per-branch design budget** is conservative for the expected configuration but is a board validation limit, not a manufacturer total-current guarantee. ICM-42688-P's 0.88 mA six-axis figure is **typical**, with no maximum in that table. Verify actual branch current and rail voltage under all firmware modes.

TPS62162 permits −3.5% initial output accuracy in power-save mode, giving 3.1845 V before line/load/ripple effects. With a deliberately conservative **1 Ω hot-bead acceptance limit** and 20 mA branch load, the corresponding rail is 3.1645 V before those effects; that is comfortably above F722's 2.4 V high-rate-ADC requirement and ICM's 1.71 V minimum. The 1 Ω figure is an engineering test bound, not a Murata guarantee. Measure minimum voltage directly at both loads during valid USB/BEC operation. ST explicitly permits a ferrite between VDD and VDDA in [AN4661](https://www.st.com/resource/en/application_note/an4661-getting-started-with-stm32f7-series-mcu-hardware-development-stmicroelectronics.pdf). The datasheet's 300 mV VDD/VDDA difference allowance applies only during power-up/down; do not use it as a steady-state voltage-drop allowance.

**Bias/filter limitation:** 600 Ω is specified at 100 MHz under standard small-signal conditions. It is not the impedance at the converter's 2.4 MHz frequency, nor a guaranteed impedance at 300 mA DC. Murata explains that DC bias can reduce ferrite impedance as permeability falls. The available exact-part page shows zero-bias frequency data; an exact-part quantitative DC-bias curve was not obtained, and no minimum biased impedance is asserted. The expected ≤20 mA load is only 6.7% of the current rating, which gives strong thermal/DC-drop margin but does not itself prove attenuation. [Murata DC-bias explanation](https://corporate.murata.com/en-us/technology/techmag/metamorphosis18/productsmarket/ferritebead)

Preserve downstream local decoupling and test filter resonance/ripple, ADC calibration/noise, and the ICM 10–90% startup ramp of 0.01–3 ms on USB and BEC. The revised layout's shorter load loop is the reason to use 0402 here. No CAD edits were made by this research.

### R20–R26 sourcing update and coverage verification —2026-10-04 19:54 UTC

Live JLC confirmed **ERJPA2F4700X / C427238:31,550 stock /28,898 orderable**, Extended, at19:48 UTC. This is a dated inventory snapshot, not a reservation. The former UNI-ROYAL0603WAF4700T5E / C23179 observation remains available in the JSON `supersedes` record, including its original6,367,613 stock /5,822,377 orderable and82.35 mW at85°C screen.

The initially considered ERJ2RKF4700X is genuinely0.1 W/0402 but appears in Panasonic’s2025 discontinuation notice, with last-time buy2025-06-30 and last eligible shipment2025-11-30. It is not the selected part. [Manufacturer-authored discontinuation notice](https://www.tti.com/content/dam/ttiinc/products/PCN/Panasonic%20Automotive%20&%20Industrial%20Systems/Panasonic-PDN.PG13324.06.03.2025.pdf)

The updated JSON was parsed and compared with the current circuit manifest: **107 passive references in 49 groups; zero missing, additional or duplicate references**, and each quantity agrees with its reference list. Manifest snapshots and required package changes are explicit; CAD integration remains with the circuit owner.

## R53 header-clearance revision — 2026-10-05

R53 is now selected as Panasonic ERJPA2F4701X / C427244 / Panasonic_ERJPA2_0402, replacing the earlier0603 UNI-ROYAL selection. Resistance4.7kΩ, tolerance1% and TCR100ppm/K are preserved. The conservative ambient rating is0.20W at70°C, derated to164.7mW at85°C; the advertised0.25W is referenced to100°C terminal temperature. Defined14.6V clamp-corner dissipation is46.44mW under the reviewed tolerance/TCR screen. Exact qualification, live JLC sourcing, manufacturer PDFs, fault/bleed limitations and maximum body/land evidence are in `validation/routing-45-r53-small-package-review/qualification.md`.

The original PCB pose is retained. Real0402 lands clear the header lands by0.400mm; maximum body/placement allowance passes by0.025mm. Both source leads now extend to full pad centers at0.20mm width. The integrated header-correction candidate has zero native geometric errors, all186 predecessor source groups preserved, and all244 actual via-mask gaps≥0.20mm. This is a checked development substitution, not a completed routing/manufacturing release. SW1/power-topology work and all existing first-article/fault limits remain open.
