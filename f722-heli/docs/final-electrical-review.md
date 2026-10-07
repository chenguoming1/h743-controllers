> Source packet: F722-4da0708a-ELECTRICAL-EVIDENCE.tar.gz, SHA-256 6abbea13f1c71c861957e73b03ba16ef4a4c85f0a380b010d2483f9d6dab2481. Result paths and reproduction commands in this report refer to that complete paired packet, which extracts as package-final4da0.

# Final F722 electrical assessment

Exact frozen board: `4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f`. Comparison checkpoint: `d5fb5b64b0549616c1581b5cc41632f8e1f96e78a9d271fdd6c13ad27e949698`.

The rebuilt classic DSM 20 mA screen passes with **51.884243 mV RP3-H reserve**, **8.269704 mV DSM reserve**, and **33.813007 mΩ worst VCAP copper** against 35 mΩ. No numerical flags or new DC continuity failure were found. All final candidate conductors and actual GND returns were rebuilt.

The requested nominal DSM 0.5 A/shared ABC 2 A scope is a separate capacity screen: its minimum DSM pad voltage is **3.009775088 V**, so it does not demonstrate a 3.3 V ±5% guarantee at 0.5 A. The confirmed dual-feed KST installation has useful DC results below, but its thermal, pulse, contact and signal-level qualification remains open. This packet does not establish a flight rating or authorize fabrication/order.

## Exact geometry and model scope

Owner receipts report 0 opens, 0 DRC errors and 9 unsuppressed warnings in both native modes; ERC 0, all 323 via masks pass, and all 511 assigned pads/129 electrical groups are preserved. Physical inventory checks retain all component values and pad/net identities. R14, R23, R24, R38 and U15 move relative to d5fb; their actual final terminals are modeled. The source project is never written by these tools.

Every model uses saved native fills with every drilled void. Copper is screened at 105°C, 15 µm effective thickness, 95% IACS and 15 µm assumed plating. GND meshes are 25/35 µm, primary CORE 12.5 µm and PERIPH 10 µm, with coarser sensitivity checks. These mesh spacings are numerical sampling, not copper thickness. Finite pad lands and contact regions are equipotential; pin, solder and within-pad neck resistance/heating are excluded. Neither mesh is a rigorous manufacturing bound.

Source and resistor assumptions are explicit in each case. Efficiency is 85/90/95% in the inherited electronics screens; installation cases use 85%. This is a static conserved-power calculation, not measured efficiency, regulator dynamics or a heat-flow solution. USB remains configuration-only with external ABC/DSM loads disconnected.

## Classic DSM 20 mA and receiver scope

Each full main GND grid includes 83 cases with B=C=1 A, conserved CORE 0.32 A distributed among nine actual sinks, DSM 20 mA, ideal J6 entry at 5.0/12.6 V and separate source/resistance corners. There are 27 USB-only cases at CORE 0.30 A. The 245-case extended source sweep retains adverse 105°C divider error. CORE/PERIPH mesh sensitivities and source sweeps are separate; they are not a universal combined worst-case cross-product.

The extended minimum C pad voltage is 4.851884243 V. RP3-H retains a 0.200 Ω contact loop plus measured cable loop ≤0.100 Ω at 1 A against 4.5 V. Classic DSM retains a 0.120 Ω contact loop plus measured cable loop ≤0.100 Ω at 20 mA against 3.135 V. DSM upper pad margin is 49.888404 mV below 3.465 V. These are bounded harness assumptions, not arbitrary cable guarantees.

The VCAP copper margin is 1.186993 mΩ. R16 remains 0.120 Ω nominal; the inherited assembled 110–130 mΩ R16 range, C7 ESR ≤25 mΩ and 5 mΩ other allowance still need physical qualification.

The actual PERIPH shared cuts, parallel In2 link, USB_LIMITED jog, CORE branches, local decoupling/analogue loops and U14 return probes are recomputed. The added PERIPH link remains a parallel current-sharing path because the restored In3 plane connects both named via contacts. The true east/west PERIPH paths carry the combined B+C load. USB local capacitor charging is represented only by labeled unit transfers, not a startup waveform.

The relocated U15 DC return to its actual Port C ground J11.4 is now 12.688–13.506 mΩ, versus approximately 9.645–9.873 mΩ before. USB ground comparisons are retained only as auxiliary DC probes. The few-milliohm increase is recorded, not suppressed. It is not an ESD pulse/inductance/residual-clamp result.

## Nominal DSM 0.5 A and shared ABC 2 A

Both GND grids contain 789 cases: 762 BEC and 27 USB. The AB, AC and BC vertices each place 1 A on two GH ports, with DSM 0.5 A and CORE 0.32 A. Aggregate 2 A does not mean 2 A at one GH contact. Source/tolerance and U8 resistance corners are retained, with nominal-source U11 resistance comparisons. All 789 cases have complete ten-net barrel envelopes; exact finite-port superposition is cross-checked against direct loaded fields.

U9 output is 0.820000 A, leaving nominal 0.18 A below the TPS62162 1 A output rating. U11's 45.3 kΩ resistor gives a 518.718 mA minimum from the datasheet fit with initial 1% tolerance. Its 150 mΩ screen alone drops 75 mV at 0.5 A. At nominal source values, minimum DSM is 3.125355 V at 150 mΩ and 3.150355 V at 100 mΩ. External receiver cable/contact loss is additional. The Nexus manual states nominal 3.3 V/0.5 A; it does not supply an explicit ±5% terminal promise.

| Loaded port | Minimum across GND grids (V) | Maximum (V) |
|---|---:|---:|
| A | 4.900082843 | 5.072228378 |
| B | 4.880717220 | 5.064397279 |
| C | 4.852126510 | 5.036738337 |

Maximum electronics-only input is 3.300269 A at the 5 V corner; U6 input reaches 2.585610 A and U9 input 0.712708 A. U5's 750 Ω table limit is 3.96–4.84 A before resistor tolerance. Scaling the lower figure for +1% resistance gives about 3.92 A as an engineering sensitivity, with startup, temperature drift and fault response still separate. U8's nearby 80 kΩ current-limit row gives 1 A minimum; the selected 80.6 kΩ is not an exact match to that test row. These figures support static headroom, not a cold-start guarantee.

TPS63070’s 2 A output row is conditioned on VOUT/VIN≤1. At 5 V raw input the protected converter input is lower than its approximately 5.1 V output, so that full-load corner is mild boost and requires a hardware test. Its 3.05 A minimum average input-limit figure is specified at VIN=5 V/VOUT=6.5 V and TJ=0–125°C; it is not an unconditional limit at every modeled point. U7’s 33 mΩ use at 2 A extrapolates a 200 mA test condition; U5’s 45 mΩ use above 3 A likewise extends its stated current test.

At 85% assumed efficiency, aggregate conversion loss reaches about 1.827 W for U6 and 0.497 W for U9. Those are conversion losses, not all IC heat. U5 I²R reaches 0.490 W and U11 reaches 0.0375 W. Regulator thermal rise, hot DCR, capacitor bias and real efficiency remain required measurements.

For L2, assumed effective inductance 1.848 µH and typical 2.25 MHz produce approximately 0.601 A peak-to-peak ripple and 1.120 A peak at the 0.82 A load/12.6 V example. The selected Murata part is specified at 2.6 A for 30% inductance drop and 2 A for 40°C rise under its test conditions. Core loss, hot winding and fault/restart peaks remain separate. L1 XGL4020-152MEC likewise needs hot-bias and mixed-mode validation; its 3.2 A figure is a 10% inductance-drop point at 25°C, not a converter rating.

U11's fitted minimum stays at least 0.5 A only while total hot RILIM stays below approximately 47.438 kΩ. Startup capacitance and receiver transients can encounter current limiting. No copper correction is indicated solely by the nominal current request. A requirement for 3.3 V±5% after a harness at 0.5 A would require a revised DSM regulation/distribution solution; raising shared CORE alone is not justified.

## Confirmed Hobbywing and KST installation

Use the confirmed Platinum HV 200A SBEC V4.1 with three BLS815 cyclic servos and one BLS805X or BLS905X tail. The documented design setting is 7.4 V. Main feed is J6; auxiliary feed is J8 pin 1 GND/pin 2 VX_RAW with signal cavity empty, conditional on unused SBUS and a UART receiver. Verify actual colored-wire polarity and fit. Both leads come from the same BEC.

The SBEC assembly is specified at 10 A continuous/30 A peak, with no published peak duration. Actual factory Hobbywing plugs mating with the selected Samtec headers need contact, temperature, pulse and retention qualification. A historical Harwin dimensional reference is not the selected installation and supplies no current limit for this comparison.

Each GND grid has 209 cases: eleven servo profiles, nine feed profiles at low/high source corners, and eleven common-source sag illustrations. The profiles include moderate motion, one heavily loaded cyclic at each location, both tail alternatives, resistance mismatch, crossed positive/return mismatch and loss of either feed. The 20/40/50/80 mΩ per-conductor path resistances and 7.0 V sag are illustrative sensitivities, not measured factory bounds. KST currents are approximate 7.4 V graph readings held constant as voltage changes; startup/stall tolerance and actual servo current response to droop are unknown.

| Illustration, high source corner | Total source (A) | J6 positive / return (A) | J8 positive / return (A) | Weakest servo pad (V) |
|---|---:|---:|---:|---:|
| 1/1/1 A cyclic + 0.5 A tail | 5.689102 | 2.986981 / 2.869177 | 2.702122 / 2.819925 | 7.268070 |
| 1.1/1.1/1.1 A + 0.6 A | 6.091769 | 3.198391 / 3.072762 | 2.893378 / 3.019007 | 7.258295 |
| 4.5/1/1 A + 2.4 A | 11.125683 | 5.841326 / 5.617589 | 5.284356 / 5.508093 | 7.132491 |
| 805X endpoint example | 18.074361 | 9.489563 / 9.130059 | 8.584798 / 8.944302 | 6.964060 |
| 905X endpoint example | 18.175081 | 9.542443 / 9.181041 | 8.632638 / 8.994040 | 6.961812 |
| 905X, J8 path 4× resistance | 18.250774 | 14.675873 / 14.593427 | 3.574901 / 3.657347 | 6.749767 |
| 905X, 7.0 V source/50 mΩ paths | 18.566854 | 9.475075 / 9.321774 | 9.091779 / 9.245081 | 5.996269 |

The endpoint examples exceed the SBEC continuous specification. Its 30 A peak figure gives no defensible duration for these cases. The 7.0 V sag example falls below the servo’s 6 V minimum. Neither case is an approved continuous operating load or a guaranteed transient envelope. No total system ampacity is invented.

Both feeds land below the servo outlets, so the J6–TAIL trunk still carries 15.900056 A in the 905X endpoint example. The local widened slice dissipates 0.336931 W; total RAW copper is 0.860300 W and full GND is 0.239770 W in that case. These are fixed-temperature DC losses, not a temperature prediction. J6/J8 first GND spans carry approximately 9.181041/8.994040 A; loss of either feed can concentrate about 18.3 A in the remaining entry span in the sensitivity set.

The RAW pour lowers J6→S1 positive unit resistance from 5.948544 to 4.543320 mΩ (23.62%). Between-header sections are about 2.45–3.0 mm wide, but total metal across the J3/J8 drill centers is only 0.800860/0.817447 mm; J4/J5 reach 1.90 mm. The bus is not uniformly 3 mm wide. Finite pad idealization omits within-land neck heating; the section audit makes that limit explicit.

Separate classic 20 mA DSM installation sweeps retain positive sampled receiver margins: the minimum DSM reserve after the stated 0.22 Ω loop is 9.233844 mV. These 418 scalar cases use the stated two source/core-location corners and are not a full cross-product with every classic sink and source sweep.

All three selected KST models require 6.0–8.4 V and specify −10 to +65°C in the current sheets. BLS815 uses 1520 µs/333 Hz; 805X/905X use 760 µs/560 Hz. Their published HIGH interval begins at 3.3 V and ends at 5.0 V. A nominal 3.3 V GPIO rail does not prove that lower bound after tolerance, output drop and ground motion. This is an explicit nominal-interface/physical-qualification gap; no guaranteed KST signal compatibility is claimed. No driver topology is changed by this review.

## Remaining warnings and physical acceptance

All nine native warnings have exact contacts, operating fields and independent finite-pad unit-basis fields. Six GND tracks and the CORE track retain spreading fields. CORE via 44c2e77d has a useful F annulus while its other annuli and barrel spans are numerically negligible. PERIPH track 874efe98 is a true zero-transport obsolete tail in this final model; it is retained under the frozen-geometry scope and classified explicitly. It is not a new DC failure. Native warnings are not suppressed to obtain a clean count.

The board input remains conditionally bounded to 5–12.6 V; selected TPS259472A does not support a 15 V operating-input claim because its recommended input is limited by the chosen clamp threshold. In the installed servo setup, the tighter 6–8.4 V servo range and configured 7.4 V BEC apply. Measure source regulation and both lead resistances, bound simultaneous current and pulse duration, and verify every load stays within its voltage/temperature conditions.

The 105°C copper calculation is a resistance stress condition, not an ambient rating. Selected X5R capacitor bodies remain limited to 85°C, and servo limits are lower. First-article work must establish thermal rise at contacts, drilled necks, ground-entry spans and regulators; cold startup/inrush, handover/backfeed, fault recovery, sensor ramp/noise, ESD, installed VCAP impedance, connector polarity/retention and accepted mechanical margins. These open checks prevent an unconditional system or flight qualification.

## Reproduction and evidence

See README.md for exact compact replay and full geometry rebuild. FINAL-SUMMARY.json covers the classic scope; CAPACITY-SUMMARY.json covers nominal current; INSTALLATION-SUMMARY.json gives all dual-feed identities, currents, losses and voltages. Scope verification checks all 418 raw-cut balances and actual first GND spans. Sparse factor caches and duplicate vendor files are excluded from the archive. Historical d5fb archives remain unchanged.

## Sources

- [RadioMaster Nexus official manual](https://cdn.shopify.com/s/files/1/0609/8324/7079/files/NEXUS_User_Manual.pdf?v=1718329689): Nominal5V2A ABC and3.3V0.5A DSM; no explicit±5% terminal guarantee found.
- [TI TPS2553 Rev F](https://www.ti.com/lit/ds/symlink/tps2553.pdf): Sections7.3–7.5 and9.5: selectedDRV current/voltage, RON, current-limit fit and thermal conditions.
- [TI TPS62160 family Rev E / TPS62162](https://www.ti.com/lit/ds/symlink/tps62160.pdf): 1A output; accuracy conditions; static peak-current limits and thermal/reference conditions.
- [TI TPS63070 Rev B](https://www.ti.com/lit/ds/symlink/tps63070.pdf): 2A output condition includes VOUT/VIN<=1; input-current-limit test conditions; thermal and magnetic requirements.
- [TI TPS2117 Rev A](https://www.ti.com/lit/ds/symlink/tps2117.pdf): 4A path;33mOhm tested at200mA through105C; full2A use remains engineering resistance extrapolation.
- [JST GH series](https://www.jst-mfg.com/product/pdf/eng/eGH.pdf): 1A/contact withAWG26; aggregate2A is split among ports.
- [JST ZH series](https://www.jst-mfg.com/product/pdf/eng/eZH.pdf): Connector conditions; actual receiver harness still separate.
- [Coilcraft XGL4020](https://www.coilcraft.com/getmedia/76c9c081-4945-4c85-9129-9356e1ad6734/xgl4020.pdf): SelectedL1 current/DCR and thermal test conditions.
- [Murata DFE322512F-3R3M=P2 manufacturer specification via verified part page](https://jlcpcb.com/partdetail/3784028-DFE322512F_3R3MP2/C3221010): SelectedL2 manufacturer specification J(E)TE243A-0019C-01, already source-qualified in project power-evidence.
- [TI TPS25947 Rev C](https://www.ti.com/lit/ds/symlink/tps25947.pdf): Selected TPS259472A operating/clamp, current-limit and on-resistance conditions.
- [Hobbywing Platinum HV 200A SBEC V4.1 manual](https://www.hobbywing.com/en/uploads/file/20221015/a728560821bb05490636413c693a115f.pdf): Same SBEC output and parallel auxiliary lead; 5–8 V/default 7.4 V, 10 A continuous/30 A peak without published peak duration.
- [KST BLS815 V8 manufacturer specification](https://cdn.shopify.com/s/files/1/0570/1766/3541/files/BLS815_V8.0_Technical_Specification.pdf?v=1700473913): Current product-linked cyclic model and approximate 7.4 V performance curve.
- [KST BLS805X manufacturer specification](https://cdn.shopify.com/s/files/1/0570/1766/3541/files/BLS805X_Technical_Specification.pdf?v=1713150470): Tail protocol, voltage/logic limits and approximate 7.4 V curve.
- [KST BLS905X manufacturer specification](https://cdn.shopify.com/s/files/1/0570/1766/3541/files/BLS905X_Technical_Specification.pdf?v=1709113577): Alternative tail protocol, voltage/logic limits and approximate 7.4 V curve.
