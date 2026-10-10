# Stock Nexus I2C timing and final-route requirements

Review: 2026-10-09 UTC. Scope: read-only source/electrical review; no firmware, configuration, parts, schematic or PCB edits. Canonical board routing was unfinished at the inspected snapshot. This is not a complete board qualification or silicon-errata audit.

## Result

Retain the authorized stock 800 kHz setting and fitted R7/R8 = 2.2 kΩ ±1%. The examined stock source has a usable short-bus timing envelope, provided the actual transitions and load meet the limits below. Use **100 ns rise/fall targets and a provisional 50 pF total-per-line allocation** for final routing. The 50 pF is an engineering budget, not measured or extracted capacitance. A **3.3 V DPS368 output-low guarantee and ordinary 800 kHz Fm+ operation remain unproven by the reviewed DPS368 tables**. Those are inherited compatibility/qualification gaps; layout completion alone cannot close them.

## Source and native configuration established

- The copied target matches upstream blob `ca042b1f51a341a46980cb9aba78420beab48be7`, target commit `1d9cb4dc6f85c7895c2b089f4b8aa776ca3d3bd3`: I2C1 SCL=PB8, SDA=PB9, barometer on I2C1. Its header identifies Rotorflight 4.3.0-RC2, firmware `ba6c7e3`; that expands to `ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94`. This identifies the reviewed reference, not an unexamined installed binary.
- At that firmware commit, `common_defaults_post.h` defaults I2C1 to 800 kHz and its internal pull-up to false absent `USE_I2C_PULLUP`. The unified F7X2 target does not define that override. Existing saved CLI settings or build overrides must be read back before claiming they match.
- Default startup: HSE=8 MHz, PLL M=8/N=432/P=2, SYSCLK=216 MHz, APB1 divide-by-4, I2C1 kernel=PCLK1=54 MHz. The source also supports a persisted 240 MHz overclock; that is not assumed or authorized here. Physical HSE error/load pulling still affects the actual clock.
- `bus_i2c_hal_init.c` passes the requested rate to `i2cClockTIMINGR(PCLK1, rate, 0)` and enables the analog filter. The interpretation assumes the reset digital-filter setting DNF=0.
- KiCad10 native inventory in `native-bus-inventory.json`, board SHA-256 `0ab556b406d336cb94fe54060048bf3e78f8a14dfcc3086d83b7e0232ccb8c86`: SCL has U1.61, U4.4, R7.2; SDA has U1.62, U4.3, R8.2. Each line has exactly these three terminals. There is no fitted connector, TVS, series resistor, test pad or other bus device. Both nets had no tracks in this unfinished snapshot, so zero trace length is not a completed-route result.

Source URLs and blob hashes for every fetched firmware file are in `stock-source-index.json`; local copies are under `stock-ba6c7e3/`. The exact calculation was run in a small host harness with an empty platform header; no firmware was built or flashed.

## Programmed timing and bounded interpretation

The unchanged upstream C calculation at nominal54 MHz returns **TIMINGR=0x00800D26**: PRESC=0, SCLDEL=8, SDADEL=0, SCLH=13, SCLL=38. A 60 MHz check returns0x00910F2A and is diagnostic only.

With one clock=18.5185 ns, the high counter is259.259 ns, low counter722.222 ns and setup delay166.667 ns. These counters alone are not the pin-level SCL high/low times. Analog filtering, edge slopes, synchronization and clock stretching add time. The source's assumed100 ns rise,10 ns fall,50 ns analog delay and two synchronizer cycles per edge give1265.556 ns/790.167 kHz. Thus a requested800 kHz is not a promise of exactly800 kHz on an oscilloscope.

Using the ST reference-manual inequalities and the programmed fields gives these nominal-clock limits:

| Check | Calculated limit |
|---|---:|
| SDA setup with50 ns Fm+ minimum | rise ≤116.667 ns |
| Minimum SDA hold with50 ns filter minimum | fall ≤105.556 ns |
|450 ns data-valid bound with260 ns filter maximum, without relying on stretching | rise ≤115.926 ns |

These limits are tighter than simply allowing the generic120 ns Fm+ transitions. The algorithm truncates fractional register fields and does not prove the whole120 ns edge envelope. This is an inherited stock-timing limitation, not a reason to change the authorized firmware. At100 ns maximum rise/fall the evaluated inequalities have positive margin. ST allows some data-valid conditions to be relaxed through clock stretching; the proposed target does not depend on that relaxation.

For intuition only, independent0–100 ns edges,50–260 ns analog-delay terms and two-to-three synchronizer cycles yield an unstretched nominal-clock period screen of1155.556–1812.593 ns, or551.696–865.385 kHz. This is not a guaranteed operating-rate range; software stalls/stretching can make transfers longer. Measure actual SCL high/low time and duty cycle rather than using this range as a test result.

## Electrical evidence and gaps

STM32F722 DS11853 Rev9 supports Fm+ timing when configured correctly, requires at least22.5 MHz I2CCLK with analog filter on/DNF0, and explicitly does not support the20 mA Fm+ output-drive requirement. Its ordinary sink row is VOL≤0.4 V at8 mA for2.7–3.6 V, subject to aggregate-current limits. Pin capacitance5 pF is **typical, not maximum**. The54 MHz kernel and approximately1.7 mA pull-up screen are within those separate clock/sink conditions; they do not certify assembled timing.

DPS368 v1.1 supports VDDIO1.2–3.6 V and identifies standard, fast and high-speed operation, with3.4 MHz maximum in its broad timing table. Its detailed output-low rows cover1.8 V/2 mA and1.2 V/1.3 mA, not3.3 V. It does not explicitly qualify ordinary800 kHz/Fm+ transactions. A3.4 MHz HS headline cannot establish this: HS has a separate entry/protocol. The400 pF row is a total bus-load allowance, not input pin capacitance or an800 kHz RC allowance. Setup20 ns in S/F mode, hold0 ns and stated duty-cycle maxima are useful checks but do not fill these gaps.

The current official Infineon `DpsClass.cpp`, commit `6b90f368224cce170e336f280d9260dcf444cb83`, calls `TwoWire.begin()` without setting1 MHz in that path. The previously mentioned vendor1 MHz example has not been re-established; it is not used as qualification evidence.

## Pull-up and supply corners

Fitted R7/R8 are UNI-ROYAL0402WGF2201TCE/C25879. Official thick-film datasheet v10 decodes F=±1%, WG=1/16 W and gives±100 ppm/°C for0402 resistance>10 Ω. Calculations combine initial tolerance and TCR multiplicatively; they exclude cumulative soldering, humidity and aging shifts, which require an added service-life margin if such a qualification is claimed.

| Assumed resistor temperature | External Rmin/Rmax | Conditional effective Rmin/Rmax with60–180 kΩ DPS pull-up |
|---|---:|---:|
|25°C |2178/2222 Ω |2101.708/2194.905 Ω |
|−40…85°C |2163.843/2236.443 Ω |2088.522/2208.997 Ω |
|−55…125°C, broader resistor screen |2156.220/2244.220 Ω |2081.420/2216.584 Ω |

The DPS36860–180 kΩ row does not positively assign an enabled pull-up to SDA/SCL in the reviewed text; CSB is explicitly shown with a pull-up. Therefore the parallel values above are conditional. Use **external Rmax alone for slowest rise** and **external Rmin plus a conservative60 kΩ hypothetical pull-up for sink current**. Do not count CSB's pull-up as an SDA/SCL load.

TPS62162 initial accuracy gives nominal rail3.3 V, PWM upper3.399 V, PFM upper3.432 V at the stated conditions. The regulator footnote excludes line/load regulation, and the table does not give a guaranteed maximum for those typical terms. Ripple/transient overshoot is also not bounded by initial accuracy. Consequently **3.432 V is not a proven rail maximum**. Use3.6 V as an operating-ceiling design screen and verify that the actual rail stays below it with margin.

At3.6 V and the broader2156.22 Ω resistor minimum, the external pull-up supplies at most1.66959 mA atVOL=0. Add60 µA if a60 kΩ DPS bus pull-up is active:1.72959 mA. An unexpectedly enabled30 kΩ MCU pull-up would add another120 µA:1.84959 mA. AtVOL=0.4 V, the external-plus-conditional-DPS current is1.53741 mA. Add applicable leakage-current contributions. These currents are comfortably below the STM328 mA row; being below the DPS's2 mA row measured at1.8 V is **not a3.3 V DPS VOL guarantee**.

For slowest rise, with2244.22 Ω and no internal-pull-up credit: tr≈0.8473RC gives95.076 ns at50 pF;100 ns corresponds to52.589 pF. At25°C the corresponding capacity is53.115 pF. This calculation is a first-order RC screen with ideal supply and no leakage; leave margin for leakage, resistor drift, nonlinear pin capacitance and measurement loading.

## Requirements for the final native route

1. Re-export both complete native nets after routing and hash the exact PCB. Confirm the three-terminal inventory, required pad-to-pad connectivity, no unconnected copper stubs, and no added component or connector loads.
2. Report total length by layer, branch length to each pull-up, width, via count/drill/span, pad geometry and reference-plane conditions. Include all branches, not just the shortest U1–U4 path.
3. Make a per-line load ledger: U1 input allocation, U4 input allocation, all trace/pad/via/nearby-copper coupling, resistor parasitics, assembly allowance and any probe. A workable provisional allocation is10 pF for U1,10 pF for U4,5 pF for pads/pull-up/assembly, and25 pF remaining for routed geometry plus model uncertainty. All allocated values are engineering allowances, not verified component maxima. Include probe C within the50 pF if comparing measured edge time directly to the calculation; a10 pF passive probe can materially change this small bus.
4. Estimate geometric capacitance using the actual approved stackup/layer/width/copper proximity; document formula or extraction method and uncertainty. Do not treat a nominal PCB capacitance-per-length shortcut as a hard upper bound. No heavy field solver is required for this screening stage. A final result must say “estimated under these allocations,” not “guaranteed worst-case50 pF,” while device maxima remain missing.
5. Keep the resulting engineering total≤50 pF on each line, and recompute RC with the final tolerance/TCR envelope. If above50 pF, first reduce authorized layout loading; report before proposing a part or firmware change.50 pF is a target, not proof of failure at50.1 pF or proof of success at49.9 pF.

## First-article checks to close bench requirements

Record firmware binary/version/hash, target identity, resource map, actual I2C clock setting/pull-up setting, system/APB/kernel clocks, TIMINGR, CR1 filter configuration and HSE behavior. A debugger/register read is preferable for the latter. Do not silently reset or modify settings to match this report.

With motors disconnected, appropriate current limiting and low-capacitance probing at U1/U4, exercise writes, sensor ACKs and reads. Capture transitions driven by the MCU and by the DPS separately. Check30–70% rise≤100 ns and70–30% fall≤100 ns as the conservative design targets; check actual SCL high≥260 ns, low≥500 ns, setup≥50 ns, nonnegative hold, START/STOP/bus-free timing and data/ACK validity. Check duty cycle and logic levels against the receiver thresholds over supply/temperature and representative converter/output activity. SeekVOL≤0.4 V for substantial low-level margin, explicitly measure DPS ACK/data low levels, and check ringing/undershoot and the3.3 V rail.

Confirm DPS detection at0x76, correct ID/calibration, repeatable pressure/temperature and no I2C error growth across repeated boot, load/source changes and sensor reads. Bench success establishes performance of tested samples/corners, not a missing manufacturer's guaranteed3.3 V/Fm+ specification. A formal all-corner guarantee requires manufacturer confirmation or additional qualification evidence. No such third-party outreach was sent.

## Primary sources and reproducibility

- [Pinned Nexus target](https://github.com/rotorflight/rotorflight-targets/blob/1d9cb4dc6f85c7895c2b089f4b8aa776ca3d3bd3/configs/RDMS-NEXUS_F7.config)
- [Rotorflight timing algorithm](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/bus_i2c_timing.c), plus pinned source index supplied beside this report.
- [STM32F722 DS11853 Rev9, July2022](https://www.st.com/resource/en/datasheet/stm32f722re.pdf), pp143–146 and159–160.
- [STM32 RM0431 Rev4, February2025](https://www.st.com/resource/en/reference_manual/rm0431-stm32f72xxx-and-stm32f73xxx-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), pp829–831 and843–844. Note that the detailed updated hold formula includes one clock beyond the SDADEL counter; use its inequalities, not only the shorter register-field description.
- [DPS368 v1.1, 2019-07-03](https://www.infineon.com/assets/row/public/documents/30/49/infineon-dps368-datasheet-en.pdf), pp6,11,21,23–24.
- [TI TPS6216x SLVSAM2E, May2017](https://www.ti.com/lit/ds/symlink/tps62160.pdf), p6.
- [UNI-ROYAL thick-film datasheet v10, 2025-07-28](https://www.uni-royal.cn/en/images/userfile/file/1753752986c56505e6d9ab55c7.pdf), pp2,5–6.
- [NXP UM10204 Rev7.0, 2021-10-01](https://www.nxp.com/docs/en/user-guide/UM10204.pdf), Tables10–11, pp43–44.

PDF SHA-256 hashes and all arithmetic are in `stock-i2c-calculations.json`. Regenerate with `python3 signal-review/calc_stock_i2c.py`; reproduce the unchanged algorithm with the supplied `timing_probe.c` and source. Rendered source pages were visually checked for min/typ/max columns and formula details. The report deliberately leaves final native geometric loading and first-article measurements pending.
