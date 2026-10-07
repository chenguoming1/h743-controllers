# F722 R31: selected 0201 UART series resistor

Checked 2026-10-07 UTC. The selected 0201 part is applied **only to R31**, on F.Cu at **(20.700, 9.860) mm, rotation 180°**, in PCB `4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f`. R30 remains UNI-ROYAL 0402WGF220JTCE / C25092 on its 0402 footprint. This document records part/footprint evidence and qualification limits; it is not an order, stock reservation or assembly acceptance.

## Selected part

**R31 uses YAGEO AC0201FR-0722RL, JLC/LCSC C144830.** It preserves 22 Ω, ±1% initial tolerance and −55 to +155 °C component operating range. It is a suitable normal-operation UART damping candidate, conditional on layout/assembly review and the actual port's transient qualification. It is **not electrically identical in every rating** to the original 0402: rated power falls from 62.5 to 50 mW, maximum working-voltage ceiling from 50 to 25 V, and TCR widens from ±100 to ±200 ppm/°C. These changes should remain explicit in review. [JLC candidate](https://jlcpcb.com/partdetail/YAGEO-AC0201FR0722RL/C144830), [YAGEO exact-part specification](https://www.yageogroup.com/component-documentation/download/specsheet/AC0201FR-0722RL)

**Tolerance is preserved:** R30’s retained UNI-ROYAL 0402WGF220JTCE / C25092 and R31’s selected YAGEO part are both **±1%**, consistent with the accepted project BOM evidence. The original catalog rating is 62.5 mW, 50 V, −55 to +155 °C. [Original catalog](https://jlcpcb.com/partdetail/25835-0402WGF220JTCE/C25092)

## Verified candidate data

| Attribute | AC0201FR-0722RL |
|---|---|
| Manufacturer / procurement ID | YAGEO / C144830 |
| Resistance / initial tolerance | 22 Ω / ±1% |
| Package | EIA 0201 = metric 0603 |
| Body L × W × H | 0.60 ±0.03 × 0.30 ±0.03 × 0.23 ±0.03 mm |
| Top / bottom termination lengths | 0.12 ±0.05 / 0.15 ±0.05 mm |
| Rated power | 0.05 W at 70 °C ambient |
| Operating temperature | −55 to +155 °C, with power derating |
| TCR at 22 Ω | ±200 ppm/°C |
| Maximum working / overload voltage ceilings | 25 / 50 V; power-derived limit still applies |
| Qualification / moisture rating | AEC-Q200 / MSL1 |

Source: [YAGEO exact-part specification](https://www.yageogroup.com/component-documentation/download/specsheet/AC0201FR-0722RL) and [official AC-series datasheet](https://www.yageogroup.com/content/datasheet/asset/file/PYU-AC_51_ROHS_L). The downloaded series document identifies itself as V11, November 17, 2023; search indexing sometimes calls the same URL V12. This package uses the actual downloaded bytes and their hash, not an assumed revision.

## JLC availability and assembly impact

The live product page fetched at **2026-10-07 03:27:52 UTC** marked the part available. Its payload contained **57,220 displayed stock**, **53,756 maximum in-stock quantity**, 10,000/reel, and USD **$0.0029** in the 1–999 price tier. The public page's own JavaScript maps `overseasStockCount` to displayed `stockCount` and `canPresaleNumber` to `maxInStock`. This verifies the catalog snapshot; it does not reserve parts or establish their physical position on the SMT line. The sanitized fields and their provenance are saved in `jlc_availability_snapshot.json`. [JLC part](https://jlcpcb.com/partdetail/YAGEO-AC0201FR0722RL/C144830)

The part is **Extended, Standard Only**. JLC's capability table lists 0201 minimum for Standard and 0402 minimum for Economic. Standard needs rails and fiducials; its listed minimum single PCB/panel envelope is 70 ×70 mm, so small-board panelization/handling must be resolved at quotation. [Assembly capability](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)

The current price page, updated September 9, 2026, lists Standard setup at $25.56 single side / $51.12 double side and **$1.53 feeder loading per component type for Basic and Extended alike**. R30 and R31 require separate BOM lines because their exact MPNs and footprints differ. Other fixture, stencil, handling, board and component costs remain order dependent; this is not a total-cost quote. If the design otherwise qualified for Economic PCBA, R31’s 0201 selection changes the service class for the entire assembly. [Current fees](https://jlcpcb.com/help/article/pcb-assembly-price)

## Footprint inspection

Inspected the actual KiCad10 runtime `Resistor_SMD:R_0201_0603Metric` file, version 20260206; its hash is S10 in `sources.json`. It uses a Vishay body-size reference and IPC nominal geometry.

| Geometry, mm | Actual KiCad10 generic | YAGEO recommended reflow |
|---|---:|---:|
| Body outline | 0.60 ×0.30 | 0.60 ×0.30 nominal |
| Copper pad size | 0.46 ×0.40, rounded | 0.35 ×0.40, rectangular |
| Copper pad centres | x = ±0.320 | x = ±0.325 |
| Copper inner gap | 0.180 | 0.300 |
| Copper total outer span | 1.100 | 1.000 |
| Paste aperture size | 0.318 ×0.360, rounded | guide depicts solder land/paste together |
| Paste aperture centres | x = ±0.345 | x = ±0.325 |
| Courtyard | 1.40 ×0.70 | not specified in mounting table |

The generic footprint matches the body and geometrically overlaps both bottom terminations through the published body/termination tolerances at centred placement. It **does not reproduce YAGEO's recommended land pattern**. Its separate paste apertures must be retained if that footprint is used; do not blindly expand paste to match copper. This is a geometric check, not placement-yield or stencil-process validation. [YAGEO mounting guide, page 4, Figure 4/Table 1](https://yageogroup.com/content/Resource%20Library/Product%20Guide-Catalog/yageo_PYu-R_Mount_10_19050818_343.pdf)

The applied project-local footprint is **F722_YAGEO:R_0201_0603Metric_YAGEO_AC**, retained in the [hardware library](../../hardware/F722_YAGEO.pretty/R_0201_0603Metric_YAGEO_AC.kicad_mod). It uses rectangular copper pads **0.35 ×0.40 mm at x = ±0.325 mm**, with matching F.Paste apertures: the mounting guide's Figure 4 explicitly identifies the hatched pads as both the solder land and solder-paste pattern, and no aperture reduction is specified there. Final stencil thickness/process remains the assembler's responsibility. F.Mask follows the same pad shapes with project/global expansion; no local clearance, mask, or other manufacturing-rule relaxation is encoded.

Its **1.30 ×0.70 mm courtyard** encloses the copper envelope of 1.00 ×0.40 mm with 0.15 mm on each side. The verified maximum body is **0.63 ×0.33 ×0.26 mm**, also enclosed. F.Fab depicts the nominal 0.60 ×0.30 mm body. The exact AC-series applicability is explicit on page 9 of S2: the AC series uses the same recommended footprint/soldering profiles as RC, referring to the mounting guide; S3's page 4 table includes size 0201. This is a vendor-derived land pattern and a geometrically checked courtyard, not board-level DRC or assembly qualification.

## Normal UART loading and limits

These calculations use nominal 22 Ω and a 3.3 V logic swing. Actual UART bitrate, external capacitance, driving-pin mode and temperature were not measured. `calculations.json` contains the numerical results.

- **Logic swing is not continuous voltage across the resistor.** With a settled high-impedance receiver, only leakage/pull current flows. STM32F722's data sheet gives ±1 µA input leakage within the rails: 22 µV drop and 22 pW in 22 Ω. An 8 mA illustrative DC load dissipates 1.408 mW. Even 25 mA produces 13.75 mW, but 25 mA is the MCU's per-pin absolute maximum, not an operating target or fault-current guarantee. [STM32F722/723, tables 14 and 61](https://www.st.com/resource/en/datasheet/stm32f722re.pdf)
- A conservative lumped-capacitance estimate assigning all edge energy to this resistor is **E/edge = ½ C V²** and **P = ½ C V² × edges/s**. For an assumed 100 pF downstream load, an edge dissipates 0.5445 nJ; 3 million edges/s gives 1.6335 mW, and 10 million gives 5.445 mW. The 22 Ω RC time constant is 2.2 ns. For the MCU's typical 5 pF pin capacitance alone, 10 million edges/s is 0.2723 mW. Trace, cable, receiver and ESD-device capacitance must be added according to the actual side of R30/R31 on which they sit. This estimate does not validate signal integrity or a general repetitive-pulse rating.
- The continuous nominal limit at ≤70 °C is **sqrt(0.05/22) = 47.7 mA**, or **sqrt(0.05×22) = 1.049 V across the resistor**. The 25 V catalog ceiling does not mean 25 V can be continuously applied to 22 Ω. Applying the published linear ambient derating gives 29.4 mW / 36.6 mA at 105 °C and 17.6 mW / 28.3 mA at 125 °C. Leave design margin; account for resistor tolerance and actual board heat.
- A sustained 3.3 V fault across 22 Ω dissipates **0.495 W**, about **9.9×** the 0201 rating. A 5 V fault is **1.136 W**, about **22.7×**. The old 62.5 mW 0402 is also not a sustained fault solution (3.3 V is 7.92× its rating).

YAGEO's series qualification includes a room-temperature 5 s overload test at the smaller of 2.5× rated voltage and maximum overload voltage. At nominal 22 Ω/50 mW this is **2.622 V / 312.5 mW for the specified test**, not 50 V across 22 Ω. No applicable repetitive nanosecond pulse-energy curve was established, so do not extrapolate that test to arbitrary ESD/surge pulses. [AC-series datasheet, pages 9 and 11](https://www.yageogroup.com/content/datasheet/asset/file/PYU-AC_51_ROHS_L)

## External-port protection caveat

The provided topology places TPD4E05U06 first at the external port, with R30/R31 between its active protected node and the MCU. This is an appropriate direction for considering a downstream damping resistor, but it does not prove survival. TPD4E05U06 is a **passive TVS array**, not a regulated 3.3 V active clamp: its 5.5 V standoff, 6.5 V minimum breakdown and typical positive TLP clamp values of 10 V at 1 A / 14 V at 5 A permit substantial residual transients. [TI Rev O, section 5.4](https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf)

The relevant resistor stress is the actual difference between the TVS node and the MCU pin, including layout inductance and MCU pin behavior. A hypothetical 6.4 V difference would initially imply 291 mA and 1.86 W in 22 Ω; its duration determines energy. This is an illustration, not a modeled clamp waveform. MCU voltage/injection limits can be exceeded before resistor thermal limits. Preserve connector-to-TVS-to-resistor-to-MCU routing and short TVS grounds, then validate the intended ESD/fault class and UART waveforms on hardware. Do not describe this package change as an ESD/protection upgrade or a certified equivalent.

## Evidence contents

- `sources.json`: verified source URLs, retrieval date, byte counts and SHA-256 of fetched documents/pages and installed footprint
- `jlc_availability_snapshot.json`: minimal factual availability/price/class data, without signed download URLs
- `calculations.json`: reproducible arithmetic inputs and results
- [Project-local vendor-pattern footprint](../../hardware/F722_YAGEO.pretty/R_0201_0603Metric_YAGEO_AC.kicad_mod): canonical hardware asset applied to R31

Full copyrighted datasheets, source pages and screenshots are not copied into this shareable package. They were inspected locally, including visual confirmation of the derating plot and mounting drawing; use the linked originals for full conditions.
