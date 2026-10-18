# R23 assembly replacement — 18 October 2026

R23 is now **Uniroyal 0402WGJ012KTCE / C2766886, 0.12 Ω ±5%, 62.5 mW, 0402**. This is an engineering value substitution for the two-board prototype, preserving the existing C9-only damping topology and all PCB geometry. It is not an exact 0.15 Ω replacement or a regulator-loop qualification.

## Procurement and order observation

The live JLC catalogue showed 6,075 in stock / 6,057 available for C2766886. The original C423234 had eight pieces, while the actual assembly BOM requested 20 including setup allowance and showed a 12-piece shortfall. Other 150 mΩ 0402 options examined did not provide sufficient readily orderable stock.

During this work, the user updated the active JLC order: the observed BOM subsequently showed **53 of 53 groups confirmed**, R23 **C2766886**, 20 pieces, $0.1100, and the exact U1 STM32F722RET6 selected from My Parts. The original uploaded Comment still read 0.15; the selected catalogue component read 120 mΩ. The corrected local BOM supplied with this revision reads 0.12 and C2766886. The user then advanced to Quote & Order. The agent did not re-upload the complete BOM or reset these user selections, submit the order, reserve stock or pay. The agent corrected the open Quote & Order assembly remark to C2766886 / 0.12 ohm / +/-5%, explicitly superseding the original 0.15 BOM Comment. All other assembly instructions were preserved. This was an edit to the open quote, without clicking Save to Cart or submitting/payment. The user then confirmed saving the order. A fresh read of cart item SMT026101761917-3213566A independently verified R23 = C2766886 / 0402WGJ012KTCE, 20 pieces, customer-selected, $0.1100; see [saved cart proof](jlc-saved-r23.png). The agent did not independently re-read the saved assembly remark, so its persistence is not claimed. The selected R23 SKU in the saved BOM is confirmed.

The earlier LCSC quote/workbook is a separate, older loose-parts quote and was not changed after the user clarified that JLC assembly comes first.

## Electrical and physical check

[ST DS11853 Rev 9, Table 19](https://www.st.com/resource/en/datasheet/stm32f722ie.pdf) specifies one nominal 4.7 µF capacitor and 0.1–0.2 Ω ESR for the STM32F722 LQFP64 VCAP pin. C9 remains C368809, Samsung CL05A475KP5NRNC, and the connection remains:

`U1.30 VCAP → R23.1 → R23.2 VCAP_C → C9.1 → C9.2 GND`

The [Uniroyal series datasheet](https://datasheet.lcsc.com/datasheet/pdf/f42da6c80a0747bae77c2f98f4e46d1d.pdf?productCode=C2766886) confirms WG = 1/16 W, J = ±5%, and 012K = 0.12 Ω. Its 0402 body dimensions are 1.00 ±0.10 by 0.50 ±0.05 by 0.35 ±0.05 mm, the same series/body as the original. The existing pads, courtyard, orientation and placement are retained. JLC lists SMT assembly support. No new feeder part footprint is needed.

At 25 °C, R23 is 0.114–0.126 Ω before solder/process drift. Using the existing exact-C9 manufacturer's typical ESR estimate of about 0.004–0.015 Ω at representative 100 kHz–1 MHz frequencies, the branch is about **0.118–0.141 Ω plus short copper**. This is within the intended 0.1–0.2 Ω range at those representative conditions. Nominal RC changes from 0.705 to **0.564 µs**; stored capacitor energy at 1.32 V remains about **4.1 µJ**. The MCU DC core current does not flow through this capacitor branch.

Using ±800 ppm/°C and ±5% additively over -40 to +85 °C gives 0.10776–0.13224 Ω for the resistor alone. This tolerance/TCR calculation does **not** bound total branch ESR across all frequency, bias, process and life conditions. In particular, the generic Uniroyal datasheet permits absolute 0.05 Ω terms in soldering/endurance resistance changes, so the nominal/TCR result cannot be presented as a guaranteed post-reflow or lifetime compliance proof. C9's curves are typical, its effective capacitance has bias/temperature/aging dependence, and ST does not specify the ESR reference frequency here. Inspect and measure the populated VCAP branch, startup and ripple under MCU load on the prototypes. No physical regulator stability or pulse-dissipation test has been performed.

## Files and validation

Only R23 Value/LCSC/Description and C9's descriptive series-resistor note changed in schematic/PCB; source definitions and the R23 BOM row are synchronized. An independent parsed comparison confirms every other board object, and all geometry/net/setup data, unchanged. CPL, both main CAM archives, impedance sheet and child sources/outputs are byte-identical to the prior standard-stack revision. Gerber regeneration and a fresh geometry-only DFM upload are unnecessary for this metadata/BOM substitution.

Native KiCad 10 checks: main **ERC 0, DRC 0, opens 0, schematic parity 0**. Child ERC/errors/opens/parity remain zero with its 11 inherited courtyard warnings. The main BOM remains 53 groups / 84 placements, with exactly one changed row; CPL bytes are unchanged. Current order instructions and the complete prototype order ZIP now contain the updated R23 BOM. Previous review records retain their historical bindings.

See [binding.json](binding.json), [transaction.json](transaction.json), [calculation.json](calculation.json), [manufacturer text](uniroyal-chip-series.txt), and [native reports](native/).
