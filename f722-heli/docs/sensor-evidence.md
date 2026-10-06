# Sensor and NAND evidence

Evidence reviewed: 2026-10-04. JLC stock snapshots were read from the live purchasing panels at approximately 16:26–16:28 UTC. Stock and prices are observations, not a reservation or procurement guarantee.

## Decision and verification boundary

- **Approved selection:** ICM-42688-P, W25N01GVZEIG, and **DPS368XTSA1 / JLC C3232508**. The user approved DPS368 as the replacement for unavailable SPL06-001 on 2026-10-04. The native sensor schematic now uses DPS368XTSA1 at I2C address `0x76`, with local 4.7 kΩ SDA/SCL pull-ups.
- Datasheets, package drawings, selected KiCad footprint geometry, firmware source, lifecycle pages, and live sourcing panels were reviewed. The pin tables below also agree with the sensor schematic generator inspected on 2026-10-04.
- This is an original design targeting published classic NEXUS F7 electrical behavior. The evidence does **not** establish an exact original NEXUS schematic, PCB geometry, or physical component orientation.
- **Physical bring-up remains pending:** component placement/assembly polarity, supply integrity, chip identification, actual stock Rotorflight initialization, flash operation, sensor data, gyro axes, barometer behavior, and first-article reliability. Source-level compatibility and successful CAD checks are not flight qualification.

## 1. ICM-42688-P

Primary electrical/package source: [TDK DS-000347, revision 1.6](https://product.tdk.com/system/files/dam/doc/product/sensor/mortion-inertial/imu/data_sheet/ds-000347-icm-42688-p-v1.6.pdf), pin table p.20, typical circuit p.21, capacitors p.22, axes p.54, package pp.55–56, SPI mode register p.64. The [TDK product page](https://www.invensense.tdk.com/en-us/products/6-axis/icm-42688-p) reports Production; its current listed datasheet revision was 1.9. The detailed checks here used the identified revision 1.6 PDF.

### Complete pin map and external circuit

| Pin | Datasheet function | Connection in this design | Requirement / interpretation |
|---:|---|---|---|
| 1 | AP_SDO / AP_AD0 | SPI1 MISO, PA6 | SPI output; I2C address function is unused |
| 2 | RESV | No connect | Datasheet permits NC or GND |
| 3 | RESV | No connect | Datasheet permits NC or GND |
| 4 | INT1 / INT | PA15 | Firmware configures pulsed, active-high, push-pull interrupt |
| 5 | VDDIO | Filtered 3.3 V IMU rail | **10 nF X7R, ±10%**, local to pin 5 |
| 6 | GND | GND | Short local return |
| 7 | RESV | **GND** | This reserved pin must be grounded |
| 8 | VDD | Filtered 3.3 V IMU rail | **100 nF + 2.2 µF X7R, ±10%**, local to pin 8 |
| 9 | INT2 / FSYNC / CLKIN | GND | Datasheet typical unused-pin circuit; no external clock used |
| 10 | RESV | No connect | Datasheet permits NC or GND |
| 11 | RESV | No connect | Datasheet permits NC or GND |
| 12 | AP_CS | SPI1 CS, PA4 | 10 kΩ pull-up is a design choice for deselection during reset |
| 13 | AP_SCLK | SPI1 SCK, PA5 | Keep SPI route short |
| 14 | AP_SDI | SPI1 MOSI, PA7 | SPI input |

VDD and VDDIO are each rated 1.71–3.6 V. Keep the three bypass capacitors close to their designated supply pins even when both pins use the same rail. The schematic's ferrite-filtered supply is an engineering choice; the selected ferrite, rail impedance, transient response, and capacitor effective capacitance still need board-level validation.

SPI supports modes 0/3 in its default setting and up to 24 MHz; the SPI_MODE setting also permits modes 1/2. Do not assume a generic 40 MHz or 50 MHz IMU bus is acceptable. No external INT1 pull resistor is required for the push-pull configuration selected by the reviewed Rotorflight driver. Grounding pin 9 assumes the unused INT2/FSYNC/CLKIN function remains consistent with that firmware configuration.

Firmware evidence: [Rotorflight ICM426xx driver at commit 21e8a8a0a5894cd889f8b118bbf6e54a1dab94e2](https://github.com/rotorflight/rotorflight-firmware/blob/21e8a8a0a5894cd889f8b118bbf6e54a1dab94e2/src/main/drivers/accgyro/accgyro_spi_icm426xx.c). The reviewed driver uses a 24 MHz maximum, programs the INT1 pulse/drive/polarity settings, and clears INT_ASYNC_RESET as required for the interrupt behavior.

### Footprint and physical-axis interpretation

The matched KiCad footprint is `Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y`, copied into the project's native library. With the datasheet top view upright and pin 1 at upper left:

- Body: 3.0 × 2.5 mm; nominal thickness 0.91 mm, range 0.85–0.97 mm
- Contact pitch: 0.50 mm; nominal device contact 0.25 mm wide × 0.475 mm long
- Footprint pads 1–4 run down the left at x = −1.1625 mm, y = −0.75, −0.25, +0.25, +0.75 mm
- Pads 5–7 run along the bottom at y = +0.9125 mm, x = −0.5, 0, +0.5 mm
- Pads 8–11 run up the right at x = +1.1625 mm, y = +0.75, +0.25, −0.25, −0.75 mm
- Pads 12–14 run along the top at y = −0.9125 mm, x = +0.5, 0, −0.5 mm
- Copper pad sizes are 0.625 × 0.35 mm for the side rows, with equivalent rotated pads on the top/bottom rows. These overlap the package contacts as expected

In the corresponding **top-of-package view**, the sensor axes are **+X right, +Y up, +Z out of the package top**. Do not use the underside package drawing as a top view.

The [Rotorflight board alignment implementation](https://github.com/rotorflight/rotorflight-firmware/blob/21e8a8a0a5894cd889f8b118bbf6e54a1dab94e2/src/main/sensors/boardalignment.c) explicitly implements CW90 as:

`corrected X = raw Y; corrected Y = −raw X; corrected Z = raw Z`

Consequently, **sensor +Y must point along intended corrected +X / board forward**. “CW90” is a firmware transform, not an instruction to type `+90` into KiCad. For this footprint's stated zero-degree view, a PCB-up forward arrow corresponds to footprint 0°. A PCB-right forward arrow requires a physical clockwise 90° rotation, conventionally KiCad −90° on the front side, putting pin 1 at upper right. Re-check actual CAD coordinates, board side, exported CPL convention, and assembler preview. Final pitch/roll/yaw direction must be tested using the exact production firmware before any flight.

#### Verified 45mm placement and separate board-mount settings — 2026-10-05

The accepted45mm assessment places U2 on **F.Cu,0°, at(23.209999,11.6)mm**. Native numbered-pad coordinates independently match the top-view orientation above: pin1 is upper-left, pins1–4 descend the left row, pins12–14 lie along the top. Therefore raw sensor+X points toward PCB+X/right, raw+Y toward PCB−Y/up, and raw+Z out of the front face. Under CW90, corrected+X/forward is PCB−Y, corrected+Y is PCB−X, and corrected+Z is out of the front face. No sensor rotation or firmware change is required for the stated forward convention.

**Do not add the target's two sensor settings together.** `gyro_1_sensor_align=CW90` selects the discrete sensor rotation. `gyro_1_align_yaw=900` stores90.0° for the alternative **custom sensor** matrix, in decidegrees. The [gyro processing branch](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3/src/main/sensors/gyro.c#L335-L338) selects that matrix only for ALIGN_CUSTOM; otherwise it applies the discrete enum once. The [initialization](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3/src/main/sensors/gyro_init.c#L200-L201) stores both representations without applying two rotations. Accelerometer processing uses the corresponding gyro alignment as well. This branch behavior was independently checked at both the target-header revision `ba6c7e3` and the previously reviewed `21e8a8a0a5894cd889f8b118bbf6e54a1dab94e2` snapshot.

The separate whole-board mounting fields are `align_board_roll`, `align_board_pitch` and `align_board_yaw`, in **degrees**, as shown by the [CLI mapping](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3/src/main/cli/settings.c#L827-L830). They are applied after sensor alignment when nonzero. The pinned NEXUS target does not set these fields. The physical arrow convention assumes all three are0; a reused flight controller configuration may retain mounting offsets, so record actual loaded values on the first article. This audit neither changed firmware/configuration nor asserted that an unexamined binary has reset settings.

**Final silkscreen acceptance:** retain U2 front-side0°/pin1 upper-left and place a clear front-side forward arrow toward decreasing PCB Y, the top edge in the front-view layout. The current assessment has no board-level forward arrow yet; the existing silk-generator arrow also points−Y but is historical placement evidence, not proof of the final artwork. Inspect the actual final F.SilkS Gerber and CPL/assembler pin1 preview. Verify deliberate roll, pitch and yaw hand motions in the configurator with motors disconnected before any flight.

## 2. W25N01GVZEIG NAND

Electrical and package source: [Winbond W25N01GV revision K PDF hosted by LCSC](https://datasheet.lcsc.com/datasheet/pdf/5bf0c9e548ad36f1d13cc4b6d89a1f6e.pdf?productCode=C88868). Exposed-pad permission is explicit in the newer [Winbond revision Q PDF hosted by Mouser](https://www.mouser.com/pdfDocs/W25N01GV_DS.pdf), p.65 package note. The older revision K drawing lacks that clarification.

### Complete pin map and external circuit

| Pin | Function | Connection in this design | Requirement / interpretation |
|---:|---|---|---|
| 1 | /CS | SPI2 CS, PB12 | 10 kΩ pull-up to 3.3 V, keeps CS tracking VCC through reset/power transitions |
| 2 | DO / IO1 | SPI2 MISO, PB14 | Single-SPI output |
| 3 | /WP / IO2 | 10 kΩ pull-up to 3.3 V | Remain high for the selected single-SPI use |
| 4 | GND | GND | Supply return |
| 5 | DI / IO0 | SPI2 MOSI, PB15 | Single-SPI input |
| 6 | CLK | SPI2 SCK, PB13 | SPI clock |
| 7 | /HOLD / IO3 | 10 kΩ pull-up to 3.3 V | Must not float in single-SPI operation |
| 8 | VCC | 3.3 V core rail | Local 100 nF + 1 µF decoupling |
| 9* | Exposed center pad | GND | Grounding is permitted; floating is also permitted |

*The center-pad number 9 is the footprint/schematic convention, in addition to the eight numbered package terminals. Winbond states that the metal center pad is not internally connected and may float or connect to device GND. It is **not mandatory** to ground it. This design elects GND. Avoid open/exposed PCB vias beneath the pad because of solder wicking; any filled/capped via-in-pad implementation would need a separately reviewed fabrication process.

VCC operating range is 2.7–3.6 V. The 10 kΩ values and 100 nF + 1 µF bypass arrangement are engineering selections, rather than fixed capacitor values mandated by the reviewed Winbond text. Place the bypass capacitors adjacent to pin 8 and its return.

This is **SPI NAND**, not interchangeable generic SPI NOR. Capacity is 1 Gbit / 8 = **128 MiB user data**, with 2048 data bytes + 64 spare bytes per page. SPI modes 0/3 are supported, up to 104 MHz under the appropriate datasheet timing conditions. The `IG` ordering suffix selects the documented buffer-read default, BUF = 1. Firmware must use the NAND command and bad-block/ECC behavior appropriate to this device.

### Footprint and lifecycle

Matched footprint: `Package_SON:WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm`, copied into the project library.

- Body: 8 × 6 mm; pitch 1.27 mm; exposed pad 3.4 × 4.3 mm
- Nominal device terminal size: 0.50 mm length × 0.40 mm width
- Footprint pad 1 center: (−3.75, −1.905) mm; side-row pitch 1.27 mm
- Footprint terminal copper: 0.65 × 0.50 mm; pad 9 matches the 3.4 × 4.3 mm exposed pad, with subdivided paste apertures

The [Winbond exact-part lifecycle page](https://www.winbond.com/hq/product/code-storage-flash/qspi-nand/w25n-gv/?__locale=en&partNo=W25N01GVZEIG) reports industrial status **P / mass production**, with longevity-program indication **Y** dating from 2016/11. This is manufacturer lifecycle evidence; it does not reserve distributor inventory.

## 3. DPS368XTSA1, approved SPL06-001 replacement

Primary source: [Infineon DPS368 datasheet, revision 1.1, 2019-07-03](https://www.infineon.com/assets/row/public/documents/24/49/infineon-dps368-datasheet-en.pdf), pin configuration, application circuit, interface selection, register descriptions, package p.40, recommended land/stencil p.41.

### Complete pin map and external circuit

| Pin | Function | Connection in this design | Requirement / interpretation |
|---:|---|---|---|
| 1 | GND | GND | Ground terminal |
| 2 | CSB | 3.3 V VDDIO | High selects I2C; direct connection avoids reliance on internal pull-up |
| 3 | SDA / SDI | I2C1 SDA, PB9 | Local 4.7 kΩ pull-up to 3.3 V |
| 4 | SCL / SCK | I2C1 SCL, PB8 | Local 4.7 kΩ pull-up to 3.3 V |
| 5 | SDO / address select | GND | Selects **7-bit address 0x76** |
| 6 | VDDIO | 3.3 V | Local 100 nF bypass |
| 7 | GND | GND | Ground terminal |
| 8 | VDD | 3.3 V | Local 100 nF bypass |

VDD operates at 1.7–3.6 V; VDDIO at 1.2–3.6 V. Tie both supply domains to the stated 3.3 V rail and bypass each pin locally. With SDO floating or high, the address is `0x77`; grounding it selects `0x76`, matching the reviewed Rotorflight default. CSB high selects I2C; do not leave it low for this connection.

The datasheet example uses 10 kΩ I2C pull-ups and allows an optional 100 kΩ SDO pull-down. The implemented **4.7 kΩ** pull-ups and direct SDO ground are deliberate selections. For a 400 kHz bus with a 300 ns rise-time limit, `tr ≈ 0.8473 × Rp × Cbus` gives approximately 75 pF maximum at 4.7 kΩ, compared with 35 pF at 10 kΩ or 161 pF at 2.2 kΩ. At 3.3 V, a 4.7 kΩ pull-up draws approximately 0.70 mA when held low. These are first-order limits; verify total parallel pull-ups, trace/input capacitance, actual rise time, and device sink-voltage limits. Calculation reference: [TI I2C Bus Pullup Resistor Calculation, SLVA689](https://www.ti.com/lit/an/slva689/slva689.pdf).

### Driver and detection evidence

The reviewed [Rotorflight DPS310 driver](https://github.com/rotorflight/rotorflight-firmware/blob/21e8a8a0a5894cd889f8b118bbf6e54a1dab94e2/src/main/drivers/barometer/barometer_dps310.c) defaults to I2C address `0x76` and requires product register `0x0D` to read `0x10`. DPS368 documents the same ID, coefficient block `0x10–0x21`, configuration/control registers `0x06–0x09`, reset register `0x0C`, reset value `0x09`, and coefficient-temperature-source bit 7 of `0x28` used by that driver.

[Infineon's accepted DPS310-versus-DPS368 support answer](https://community.infineon.com/t5/Pressure-sensors/DPS310-vs-DPS368/td-p/813752), 2024-07-28, explicitly confirms use of the same driver. This supports using the existing DPS310 firmware path for DPS368. It does not replace a test with the exact stock Rotorflight release/target binary, which remains pending.

The [DPS368 product page](https://www.infineon.com/part/DPS368) reports Active and preferred, identifies DPS368XTSA1 / VLGA-8-2, MSL 1, and planned availability to at least 2034 as observed. This is the preferred sourcing alternative to the obsolete SPL06 and DPS310.

### Footprint, numbering, and pressure port

DPS368 and SPL06-001 have the same functional eight-pin order and compatible nominal contact geometry: 2.5 × 2.0 mm body, 0.65 mm pitch, 0.35 mm square package contacts, and 1.45 mm opposing-row center separation. DPS368 is up to 1.1 mm high, compared with SPL06's 0.95 mm nominal height. Account for that difference in the mechanical envelope.

The project uses `Bosch_LGA-8_2x2.5mm_P0.65mm_ClockwisePinNumbering`, copied into the native library. The vendor label in the footprint name is not a substitute for dimensional verification. In its zero-degree landscape top view, pin 1 is at upper left; pins 1–4 go left to right on the top row, and 5–8 go right to left on the bottom row. In the rotated portrait datasheet top view, pin 1 is upper right, pins 1–4 go down the right side, and 5–8 go up the left side. These are the same clockwise numbering after rotation.

The inspected KiCad footprint has longitudinal pad centers at −0.975, −0.325, +0.325, +0.975 mm and transverse row centers at ±0.8 mm, with copper 0.35 × 0.50 mm. This overlaps the full nominal 0.35 mm square device contacts at row centers ±0.725 mm. **The copper land centers are not identical to the device-contact centers**, and dimensional overlap alone does not certify paste-volume or assembly yield. Review the final project's solder-mask/paste geometry against Infineon's p.41 recommended solder-mask-defined land/stencil drawing and the assembler's process before release.

Keep the pressure opening unobstructed. Adhesive, conformal coating, flux residue, cleaning, foam and enclosure venting require an explicit process/mechanical review; waterproof component packaging does not mean the pressure opening can be sealed.

### Why SPL06 and DPS310 were not retained

The [Goertek SPL06-001 datasheet hosted by LCSC](https://datasheet.lcsc.com/datasheet/pdf/7f52851b2beb8afe5cf68acd1d437ed6.pdf?productCode=C2684428) supports the original pin/function and capacitor mapping: address p.9, application circuit p.15, pins p.29, package p.30. Its detailed product-ID register description gives `0x10`, although the register-summary table contains an inconsistent reset entry. No SPL06-named driver was found in the reviewed Rotorflight tree; source-level compatibility should not be inferred from the package alone.

The live JLC SPL06 page had zero stock and offered consignment/quote, while [LCSC C2684428](https://www.lcsc.com/product-detail/C2684428.html) stated unavailable and [DigiKey's exact SPL06-001 page](https://www.digikey.com/en/products/detail/goertek-microelectronics-inc/SPL06-001/17005535) marked it obsolete/no longer manufactured. Older search-index inventory snippets do not override those live pages. The proposed DPS310 alternative also had zero JLC stock and a no-longer-manufactured notice. The user has now resolved this sourcing gate by approving **DPS368XTSA1**; it is no longer an outstanding substitution decision.

## 4. Live JLC sourcing snapshot

| Exact part / JLC identifier | Live inventory / available order quantity | Assembly / handling observation | Decision |
|---|---:|---|---|
| [ICM-42688-P / C1850418](https://jlcpcb.com/partdetail/ICM-42688-P/C1850418) | 4,642 / 4,201 | Economic + Standard, X-ray required, MSL 1; $19.4364 at quantity 1 | Selected |
| [W25N01GVZEIG / C88868](https://jlcpcb.com/partdetail/W25N01GVZEIG/C88868) | 3,826 / 3,721 | Economic + Standard, MSL 3; $10.7212 at quantity 1 | Selected |
| [SPL06-001 / C2684428](https://jlcpcb.com/partdetail/Goertek-SPL06001/C2684428) | 0 / unavailable | Standard only, consignment/quote, X-ray required, MSL 1 | Replaced with user approval |
| [DPS310 / C130156](https://jlcpcb.com/partdetail/InfineonTechnologies-DPS310/C130156) | 0 | No-longer-manufactured notice | Not selected |
| [Generic DPS368 / C535115](https://jlcpcb.com/partdetail/InfineonTechnologies-DPS368/C535115) | 0 | Different catalog entry | Do not use this identifier for the stocked orderable part |
| [DPS368XTSA1 / C3232508](https://jlcpcb.com/partdetail/InfineonTechnologies-DPS368XTSA1/C3232508) | **5,082 / 5,002** | Standard only, MSL 1; $4.1942 at quantity 1, $3.5814 at 10, $3.2172 at 30, $2.8482 at 100 | **Approved and selected** |

Prices are USD snapshots and exclude any unverified assembly, X-ray, handling, tax or shipping fees. JLC “assembly” or consignment-only SKUs do not demonstrate purchasable component stock. Live listings establish available catalog inventory, but do not independently prove an authorized-distributor chain for every lot. Confirm exact manufacturer MPN, procurement traceability, MSL handling, and current availability in the final assembly quote. No order or reservation was placed as part of this research.

## 5. STM32F722 HSE assumption

The reviewed [Rotorflight STM32F7 startup implementation](https://github.com/rotorflight/rotorflight-firmware/blob/21e8a8a0a5894cd889f8b118bbf6e54a1dab94e2/src/main/startup/system_stm32f7xx.c) uses an 8 MHz default HSE_VALUE with PLL_M = 8, PLL_N = 432, PLL_P = 2 and PLL_Q = 9. Thus `8 MHz / 8 × 432 / 2 = 216 MHz`. Its 48 MHz USB domain is produced using the configured PLLSAI path, with N = 384 and P = 8. HSE is enabled in crystal mode rather than bypass mode.

No measurement-based HSE-frequency auto-detection was found in that STM32F7 startup implementation. Software computing/checking SystemCoreClock from configured values is not evidence that an arbitrary external crystal frequency will be discovered. Use the intended **8 MHz crystal** and independently calculate its load capacitors from the chosen crystal and PCB parasitics. Pin the actual firmware release/build before relying on this source snapshot. This evidence does not identify the crystal component or exact oscillator circuit used inside an original NEXUS board.

## 6. Remaining release and bench checks

1. Reconcile final native schematic and PCB pad nets against the complete tables above, including every reserved pin, both barometer grounds, and the NAND exposed pad
2. Check top-view component pin-1 markers, front/back board side, CPL rotation, and assembler preview independently; do not equate firmware CW90 with a CAD angle
3. Review final barometer mask/paste lands, pressure-port clearance, capacitor placement, rail return loops, and NAND exposed-pad process
4. Confirm current stock and exact MPNs when ordering; retain traceability and moisture-handling records
5. Perform current-limited power-up, check all supply rails, then read device IDs before enabling high-rate operation
6. Run the exact intended stock Rotorflight binary: confirm IMU initialization/interrupt timing, flash identification and write/read behavior, and DPS368 detection at 0x76 with sane calibration, temperature and pressure values
7. Measure I2C rise times and verify sensor data under representative power/output activity
8. Check all three gyro/accelerometer axes and signs against the marked board forward direction, including actual configurator movement, before arming; motor-disconnected receiver, output and failsafe tests precede any flight

These are pending physical validation gates, not tests claimed to have passed.

## DPS368 footprint adaptation — 2026-10-05

The 45 mm routing revision replaces the generic Bosch footprint with project-local `Infineon_DPS368_VLGA-8_2.5x2mm_SMD`. Infineon DPS368 datasheet v1.1, pp40–41, Figures17–18, was visually reviewed. Pin numbering is unchanged: landscape top-view pin1 upper left; x positions −0.975/−0.325/+0.325/+0.975mm; opposing row centers ±0.725mm.

The implementation uses 0.45mm square copper and a −0.05mm per-side solder-mask margin, yielding a 0.35mm square exposed SMD opening. The 0.05mm copper overlap is an explicit engineering choice to implement solder-mask-defined pads; it is not claimed to be a separately dimensioned manufacturer requirement. Independent 0.35mm circular paste apertures match Figure18. Adjacent copper clearance is 0.20mm, with 0.30mm between mask openings. At a proposed 0.10mm stencil, circular aperture area ratio is0.875. Factory stencil/mask registration approval remains required.

The generic Bosch3D model reference is removed instead of asserting it models the DPS368's1.1mm maximum height/pressure port. The pressure port must remain unobstructed and free from coating, adhesive, foam or flux contamination. Pin-net parity and physical clearance will be rerun on the integrated board. Historical compact-board checkpoints retain their old embedded lands and are not the final design.
