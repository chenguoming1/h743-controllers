# RPM/SBUS high-voltage input clamp decision

Research: 2026-10-04, 18:05–18:10 UTC. Scope: U16 replacement, package compatibility, bounded circuit analysis and prototype acceptance gates. This research changes no CAD, generator, BOM or procurement state.

## Decision

Replace **U16 with Nexperia PESD15VS2UT,215, JLC/LCSC C282556**, retaining the existing `F722_Heli:SOT-23` footprint and all three nets. This is a **dual unidirectional, common-anode** part. It corrects the selected bidirectional protector's negative-avalanche mechanism without changing the normal positive signal range or PCB pad locations. Do not substitute `PESD15VS2UAT` or a similarly named part from another manufacturer.

### Exact stock evidence

[JLC C282556](https://jlcpcb.com/partdetail/C282556) was fetched directly on the research date. Its public, server-rendered product data identified:

| Field | Observed value |
|---|---|
| Manufacturer / model | Nexperia / PESD15VS2UT,215 |
| Package / library | SOT-23 / Extended (`expand`), SMT |
| `overseasStockCount` | 1,265 |
| `canPresaleNumber` | 1,239 |
| Purchasable / blocking reason | `isBuyComponent="1"` / `noBuyReason=null` |
| Initial unit price | USD 0.146 |

The two quantities are the stock and available-order quantities carried by the page; they are a snapshot, not a reservation. Recheck the exact MPN and assembled-order availability before release. An older indexed LCSC image page showed 850 and an NRND inventory notice, whereas [Nexperia's current product page](https://www.nexperia.com/product/PESD15VS2UT) identifies the family as **Production**. Do not convert the distributor notice into a manufacturer EOL claim. No alternate search is needed while this exact part remains orderable.

## Electrical identity and pads

The [Nexperia datasheet, 13 April 2023](https://assets.nexperia.com/documents/data-sheet/PESD15VS2UT.pdf), pp2–4, specifies:

- Pin 1 = K1, pin 2 = K2, pin 3 = common anode
- Reverse working voltage 15 V; breakdown 17.6–18.4 V at 5 mA
- Positive clamp maximum 23 V at 1 A, 40 V at 5 A, for the specified 8/20 µs pulse at 25°C
- Capacitance 70 pF maximum at 0 V/1 MHz; leakage 1 µA maximum at 15 V/25°C
- SOT23/TO-236AB, nominal 2.9 × 1.3 × 1.0 mm body, 1.9 mm outer-pin pitch

Thus normal 0–12.6 V signaling is below standoff by 2.4 V. Negative input excursions forward-bias the diode from GND to the signal rather than waiting for negative avalanche. The datasheet **does not specify a guaranteed maximum forward clamp voltage**. A fixed −0.7 V or −1 V worst-case claim would be unsupported.

The existing project footprint was read directly at `hardware/library/F722_Heli.pretty/SOT-23.kicad_mod`. In its unrotated, top/component-side coordinates:

| Pad | Centre x,y (mm) | Land x,y size (mm) | Required net |
|---|---|---|---|
| 1 | −0.9375, −0.950 | 1.475 × 0.600 | RPM_HV, K1 |
| 2 | −0.9375, +0.950 | 1.475 × 0.600 | SBUS_HV, K2 |
| 3 | +0.9375, 0 | 1.475 × 0.600 | GND, common anode |

All lands are roundrect SMT copper/mask/paste. Pads 1–2 have the required 1.900 mm pitch. This is the installed KiCad SOT-23 land pattern, not a claim that its land lengths reproduce Nexperia's recommended pattern exactly. Package family and numbering match; retain the physical footprint. Update the generator's custom symbol name/pin descriptions, value/MPN, and procurement identity together, then regenerate and verify all three pad nets. The old bidirectional symbol must not remain as misleading documentation.

## Circuit and negative-stress bounds

Reviewed topology in `tools/build_ports.py`:

- RPM: J7 signal → R25 470 Ω/1% → RPM_HV → Q1 drain
- SBUS: J8 signal → R26 470 Ω/1% → SBUS_HV → Q2 drain
- U16 shunts the two HV nodes to ground; Q1/Q2 gates connect to +3V3_CORE
- Each source has 4.7 kΩ to +3V3_CORE, then 220 Ω/1% to its MCU node and U13 USBLC6-4SC6

The current R20–R26 selection is Panasonic ERJPA2F4700X, with its ambient/terminal rating distinction and derating documented in `passive-bom-evidence.md`; the older 0.25 W ambient shorthand must not be used.

### Checked U13 channel reassignment, 2026-10-05

The accepted 32-open development board assigns SBUS_MCU to the previously unused equivalent U13 I/O pin 6 and leaves pin 4 unconnected. ESC, RPM, bias and GND pins are unchanged. This preserves the original USBLC6-4SC6 component and external/MCU pinout. The short local SBUS branch is 2.001857 mm; R45-to-R37 is 0.864089 mm. An exact-endpoint, same-width 0.15 mm ESC trace rethread adds 1.322601 mm with no new via.

The canonical generator, manifest and native schematic agree, with zero KiCad 10 ERC violations, nine independent physical-wire graphs passing and all 29 firmware resources matching. Package-channel equivalence does not establish identical package parasitics or board-level ESD immunity. System bench qualification remains required. Exact evidence is in `validation/routing-45-rpm-sbus-20261005/compact-r45-pin6-esc-bend/REPORT.md`. This local cell does not mean the remaining SBUS backbone is routed.

[onsemi BSS138LT1G, Rev 15](https://www.onsemi.com/pdf/datasheet/bss138lt1-d.pdf) limits VGS to ±20 V and VDS to 50 V. A sufficiently negative drain turns the FET on and can pull its source negative; a clamp after 220 Ω does not directly clamp that source. This explains the original review finding. A nominal 15 V bidirectional protector can reach negative voltages that violate the gate limit.

For a general negative transient, define B as the maximum negative source excursion relative to the **local gate-supply ground**, including return bounce and ringing. With the explicit rail ceiling Vgate ≤3.6 V:

`VGS(max) ≤ 3.6 V + B`

Absolute-limit compliance requires B <16.4 V; the proposed prototype acceptance target is B ≤5 V and measured |VGS| ≤10 V. The replacement's forward conduction makes that target plausible but does not make it a datasheet guarantee. Probe the source and gate directly. A short ground return and measurements on the assembled board are necessary to bound the fast peak.

There is also a limited numerical bound from the existing downstream clamp. [ST USBLC6-4 datasheet](https://www.st.com/resource/en/datasheet/usblc6-4.pdf), Table 2, gives VF ≤0.86 V at 10 mA and 25°C. For a quasi-static negative test with **total current through the 220 Ω branch ≤10 mA**, and negligible ground bounce:

`Vsource ≥ −0.86 − (0.010 × 222.2) = −3.082 V`

`VGS ≤ 3.6 + 3.082 = 6.682 V`

This is a bounded 25°C/current-limited circuit check, not a full-temperature or ESD result and not permission for sustained negative signaling. U16's local forward path should further reduce negative stress. Do not extrapolate U13's 10 mA forward specification to high-current pulses.

A −12.6 V fault with an approximately grounded clamp can draw up to 27.1 mA through a 1%-low 470 Ω resistor, dissipating up to 0.341 W. That exceeds the stated 0.25 W continuous rating. Define transient duration and verify the selected resistor's pulse curve before a stronger injection test; this substitution does not add sustained reversed-signal or wrong-header immunity. Positive 40 V TVS clamping is below the FET's 50 V rating only at its stated pulse conditions and before layout overshoot; it is not unrestricted surge immunity.

## 100 kbaud edge budget

A 100 kbaud bit is 10 µs. First-order estimates use `t10–90 = ln(9)RC`, and `t70% = −ln(0.3)RC`. These screen component loading; the nonlinear FET translator and real cable still need measurement.

| Assumed network | RC τ | 10–90% edge | Time to 70% |
|---|---:|---:|---:|
| 474.7 Ω series, U16 alone at 70 pF | 0.0332 µs | 0.0730 µs | 0.0400 µs |
| 474.7 Ω + 100 Ω driver, 150 pF total HV budget | 0.0862 µs | 0.189 µs | 0.104 µs |
| 474.7 Ω + 4.7 kΩ external pull-up, 150 pF HV budget | 0.776 µs | 1.71 µs | 0.935 µs |
| 4.747 kΩ + 222.2 Ω, 100 pF total LV budget | 0.497 µs | 1.09 µs | 0.598 µs |

The 150 pF and 100 pF totals are **design budgets, not verified worst-case capacitances**. BSS138 capacitance increases at low bias; do not treat its Coss maximum specified at 25 V as the all-bias value. Include U13, MCU, layout and probe loading. The 220 Ω was included conservatively in the LV estimate; the actual circuit has capacitance on both sides of it. Open-drain cable loading and an unknown external pull-up can dominate. For scale, 10 kΩ charging 1 nF alone takes about 22 µs for 10–90%, which is unsuitable for 10 µs bits.

The selected TVS adds only about 73 ns of 10–90% loading through the board's 470 Ω resistor. It is therefore a reasonable 100 kbaud selection; this does not certify an arbitrary receiver/cable combination or higher RPM frequency.

## Remaining release gates

1. Substitute the exact Nexperia MPN/C282556 in the generator, schematic and BOM; verify pad 3 is ground, pads 1/2 are their HV signals, and the TVS is after the 470 Ω resistors. This research did not perform that edit
2. Keep the connector → resistor → TVS → drain path short; connect U16 ground directly to the reference plane with short, low-inductance return. Review coupling and common-ground bounce when either channel is stressed
3. Begin with current-limited negative bench tests within the 10 mA/25°C bound above. Define the intended stronger transient amplitude, source impedance, duration and repetition rate; check resistor pulse capability first. For that declared envelope, verify both FET sources remain ≥−5 V and |VGS| ≤10 V, and separately check MCU pin voltage/injection current and rail disturbance. No arbitrary IEC/ESD certification follows from these calculations
4. Scope and decode 100 kbaud SBUS at actual rail extremes, temperatures, receiver output levels and longest intended cable. Check both transition directions, low-level margin, crossings and framing; target valid levels well before the bit centre. Test open-drain RPM with its real pull-up and maximum pulse rate separately
5. Test powered-off controller, receiver-first startup and hot connection for parasitic powering and unintended outputs. Inspect post-test leakage/function before motor-disconnected system/failsafe testing

**Disposition:** one verified, stocked, same-pad unidirectional candidate is selected. The negative-polarity component-selection flaw has a concrete correction. Fast-transient clamp magnitude, whole-input robustness and flight suitability remain prototype-validation gates.
