# Compact A/B/C UART ESD selection

**2026-10-04, 18:15–18:27 UTC. Original engineering design choice, not a claim about the proprietary Nexus circuit.** Intended UART logic is 3.3 V. The separate RPM/SBUS high-voltage interface is unchanged. This work adds a footprint and evidence only; it does not modify the schematic or PCB.

## Selected option

Use **two Texas Instruments TPD4E05U06DQAR** ground-only four-channel arrays in place of U14/U15. Locate them near their respective ports rather than collecting all six lines at a distant protection point. Preserve the existing connector-side protection / 22-ohm MCU-side series-resistor order. The arrays have no VBUS-bias connection, so the former explicit UART-to-+5V_PERIPH steering path is removed.

Primary source: [TI SLVSBO7O, TPDxE05U06 datasheet](https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf), Rev O, August 2024. Pin table is PDF page 4, electrical tables pages 6–8, DQA0010A drawings pages 28–30, and DQA0010B drawings pages 31–33. The current source includes both package constructions under DQA; the new footprint follows the newer B drawing explicitly.

### Exact pin map

| Pin | Function | Proposed U14 | Proposed U15 |
|---:|---|---|---|
| 1 | Protected I/O | PORT_A_RX_EXT | PORT_C_RX_EXT |
| 2 | Protected I/O | PORT_A_TX_EXT | PORT_C_TX_EXT |
| 3 | GND | GND | GND |
| 4 | Protected I/O | PORT_B_RX_EXT | Explicit NC, unused channel |
| 5 | Protected I/O | PORT_B_TX_EXT | Explicit NC, unused channel |
| 6 | NC | Explicit NC | Explicit NC |
| 7 | NC | Explicit NC | Explicit NC |
| 8 | GND | GND | GND |
| 9 | NC | Explicit NC | Explicit NC |
| 10 | NC | Explicit NC | Explicit NC |

Channels are interchangeable; the proposed allocation preserves the present logical grouping. Both ground pins must be grounded. Pins 6/7/9/10 are not internally connected signal mates. TI permits them to float or ground and describes optional straight-through routing; this project proposal leaves them explicitly unconnected to avoid misleading netlist continuity. Do not mistakenly ground unused **signal** pins through a label intended only for package NC pins, and do not connect either ground pin to +5V_PERIPH.

## Local footprint

Use **`F722_Heli:Texas_DQA0010B_TPD4E05U06_2.5x1mm`**.

Source geometry: TI **DQA0010B, drawing 4230307/A, December 2023**, PDF pages 31–33. Coordinates below are PCB top view, body centre origin, +x right, +y down. Body is oriented 1.0 mm across x and 2.5 mm along y, with pin 1 upper left. The package's maximum body dimensions are 1.1 × 2.6 mm and maximum height 0.55 mm.

| Pins | Centre x | Centre y | Copper / paste geometry |
|---|---:|---|---|
| 1, 2, 4, 5 | −0.4175 | −1.0, −0.5, +0.5, +1.0 | 0.565 × 0.200 mm, R0.050 rounded rectangles |
| 10, 9, 7, 6 | +0.4175 | −1.0, −0.5, +0.5, +1.0 | Same |
| 3, 8 | Ground-land end references at −0.4175 / +0.4175 | 0 | Joined source-derived ground shape, described below |

Ground copper spans x = −0.700…+0.700 mm. Its central section is 0.800 mm wide and 0.400 mm high; outer end sections are 0.300 mm high. The source R0.050 transitions/corners are retained. Custom numbered pads 3 and 8 divide the common shape into overlapping halves; **both must have the same GND net**. The 0.020 mm overlap is purely a KiCad connectivity representation and does not add a copper feature to the combined outline.

Ground paste uses two source-shaped windows, each 0.600 mm wide, with a 0.200 mm central gap. Their outer/inner heights are 0.300/0.400 mm. Ordinary signal/NC pads retain full-size paste. The drawing's **0.100 mm stencil** is consistent with the proposed board stencil. A drawn central 0.200 mm via is **not drilled by this footprint**; any via-in-pad would require a qualified filled/capped process. No hidden centre pad 11 is added.

Mask is NSMD with +0.050 mm expansion, within the drawing's +0.070 mm maximum guidance. The local courtyard is **1.900 × 3.100 mm**, including 0.25 mm around maximum body/copper extents. There is no external 3D-model dependency.

### Why the installed standard footprint was not copied unchanged

Installed `Package_SON:USON-10_2.5x1.0mm_P0.5mm` has uniform 0.550 × 0.300 mm lands at x = ±0.385 mm. It differs from both reviewed TI land drawings and lacks B's common-ground copper/split-paste pattern. Matching package name and pitch alone does not make it drawing-exact.

DQA0010A uses the same eight small-pin centres and 0.565 × 0.200 mm lands but two separate 0.565 × 0.400 mm ground lands. The B package changes the ground contact to a joined centre bar. Signal positions and ground net identity are compatible, but the two reference paste/ground shapes are not identical. The supplied file is explicitly B-derived; confirm the actual procured construction/marking with the assembler if an A lot is supplied. No blanket reflow equivalence for either lot is claimed.

### Validation performed

- KiCad 9.0.2 loads the footprint; exactly ten numbered copper pads, `{1…10}`
- A standalone audit board gives every non-ground pad a distinct net and grounds 3/8 together
- Native DRC: **0 violations, 0 unconnected items** under ordinary default rules
- Native F.Cu, F.Mask and F.Paste SVG plots were rendered and inspected against the source land/stencil drawings; joined ground copper, split ground paste and top-view numbering match
- Footprint SHA-256: `a875ee944a0f9d93879514bd5e3127cc7377795c1f380c487b5121c2d071daa7`

These are footprint checks, not whole-controller routing, ESD or assembly qualification. Temporary validation sources/plots are in `/tmp/f722-uart-review`; the library file is self-contained. Final integration still needs symbol/PCB parity and CPL orientation review.

## Normal operation and explicit limitations

All six MCU UART pins are FT/FTf: PA0/PA1, PC6/PC7, PB10/PB11. At a powered 3.3 V core, ordinary 3.3 V signaling is appropriate. The selected TI part has a 0–5.5 V operating range and does not perform voltage translation. [STM32F722 DS11853 Rev 9, Tables 10/13/14/16](https://www.st.com/resource/en/datasheet/stm32f722re.pdf)

The MCU's FT absolute upper input limit is **VDD + 4.0 V**. Thus a persistent external **5 V signal while VDD = 0 V exceeds the 4 V absolute bound**. Neither these arrays nor 22-ohm series resistors make external-first 5 V safe. A larger resistor is not a substitute for a specified FT-input voltage bound. Ground-only protection eliminates one intentional rail-steering path; it does not prove zero parasitic powering through the entire board.

For powered FT reception above VDD + 0.3 V, internal pulls must be disabled. The pinned [STM32F7 UART driver](https://raw.githubusercontent.com/rotorflight/rotorflight-firmware/ba6c7e3/src/main/drivers/serial_uart_stm32f7xx.c) uses IOCFG_AF_PP for ordinary two-wire UART; [io.h](https://raw.githubusercontent.com/rotorflight/rotorflight-firmware/ba6c7e3/src/main/drivers/io.h) defines this with GPIO_NOPULL. Half-duplex SERIAL_BIDIR instead explicitly chooses a pull-up or pull-down, so do not extrapolate ordinary powered 5 V reception to every serial mode. The intended 3.3 V signal contract avoids that particular over-VDD issue.

TI's 10 nA maximum leakage specification is at **2.5 V**, not a 10 nA guarantee at 5.5 V. Its 5.5 V standoff is specified at less than 10 µA. Clamp values are **typical TLP** results: approximately +10 V at 1 A / +14 V at 5 A, and negative magnitudes 3/7 V at those currents. These are not DC GPIO safety limits, and they are not directly interchangeable with a different manufacturer's 8/20 µs test. The device has ±12 kV contact / ±15 kV air ratings. Keep short shunt/ground paths, preferably local ground vias, and validate the residual waveform at the MCU after the series resistor.

## Compared with the six-discrete proposal

Six onsemi [ESD9M5.0ST5G](https://www.onsemi.com/download/data-sheet/pdf/esd9m5.0s-d.pdf) are a plausible ground-only **3.3 V** alternative with an already checked SOD-923 footprint: cathode pin 1 to each signal and anode pin 2 to ground. Their 2.5 pF maximum capacitance is benign for UART edges. However, standoff/leakage is specified at 5.0 V; a true nominal 5 V signal with positive tolerance is not fully covered merely because breakdown starts above 5.8 V. Their contact/air ratings are ±10/±15 kV and their published 1 A 8/20 µs maximum clamp is 9.8 V.

The original [USBLC6-4SC6](https://www.st.com/resource/en/datasheet/usblc6-4.pdf) lists 15 kV contact/air in its absolute-rating table and 12/17 V maximum clamps at 1/5 A, 8/20 µs. Therefore neither new option is an identical protection rating. Removing the bias pin sacrifices rail-steering behavior while avoiding its direct +5V_PERIPH backfeed path. Final-layout system immunity cannot be inferred from these component ratings alone.

Calculated courtyard bounding rectangles, excluding routing/ground vias:

- Existing two SOT-23-6 positions: `2 × 4.1 × 3.4 = 27.88 mm²`
- Six existing SOD-923 footprints: `6 × 1.5 × 0.9 = 8.10 mm²`
- Two new conservative TI footprints: `2 × 1.9 × 3.1 = 11.78 mm²`, approximately **58% less** than the original two positions

The singles offer greater distribution flexibility; the two TI arrays offer 5.5 V part-level headroom and fewer placements while fitting the owner's preferred split placement. These are packing estimates, not a guarantee of routability.

## Verified procurement snapshot

Read-only checks at approximately **18:18 UTC on 2026-10-04**. Stock is not reserved or a final assembly guarantee.

| Exact manufacturer / MPN | JLC code | Stock / orderable | Observation |
|---|---|---:|---|
| Texas Instruments TPD4E05U06DQAR | [C138714](https://jlcpcb.com/partdetail/C138714) | **143,564 / 139,399** | Public page data and visible cloud-browser stock panel; selected |
| Texas Instruments TPD6E05U06RVZR | [C962978](https://jlcpcb.com/partdetail/TexasInstruments-TPD6E05U06RVZR/C962978) | 6,766 / 6,261 | Public data and visible stock panel; researched alternate, not selected |
| onsemi ESD9M5.0ST5G | [C242267](https://jlcpcb.com/partdetail/C242267) | 16,097 / 15,976 | Public page's exact-part inventory object; discrete alternate |

The selected TI item lists SMT support for Economic/Standard assembly and MSL 1. Identically named parts from TECH PUBLIC, GOODWORK or other vendors are **not** substantiated by TI's data and are not authorized substitutes. Recheck manufacturer, suffix, package construction, inventory and traceability at future procurement. No parts were purchased.
