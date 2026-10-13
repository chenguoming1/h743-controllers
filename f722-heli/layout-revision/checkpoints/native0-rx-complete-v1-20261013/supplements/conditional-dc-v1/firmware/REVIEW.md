# Exact native0 stock-source mapping receipt

**Static mapping evidence is complete for the current candidate, with explicit unused-resource and runtime limits.** All 29 historical pinmap rows agree with the actual pinned target, MCU pin-function names, current schematic netlist and current PCB pads. Enumerating the full target reveals 31 assigned resources: PPM1 shares the existing PA3 SBUS path; TX1 on PA9 is assigned by the target but deliberately unconnected on this design. The original Nexus external pinout shows only RX/GND/3.3 V at DSM, so the unused TX1 resource is not an established external-pinout defect. No other assigned target resource is unconnected or mapped to a conflicting net.

This is a receipt candidate for internal export readiness, not a passed firmware binary, boot, sensor-axis, electrical or flight test. It does not certify all advertised protocols or all user-selected configurations.

## Exact identities and fresh checks

- Current PCB SHA-256: `84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd`.
- Current fresh-paired.net SHA-256: `a48480a34f27b7c534df0bfce78cac9ad0bc2742aa6e458672a3060b2b0e3542`.
- Current native logical SHA-256: `04d8ecd80edf004f3226f204f23adba51692a498ae38edc183debeffb704603d`.
- Historical contract SHA-256: `f09f99efa565075e1676e9be9d9d27f27c0b5b6e15275533b478a626d96b9826`.
- Firmware source: [rotorflight-firmware at ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94](https://github.com/rotorflight/rotorflight-firmware/tree/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94).
- Target: [RDMS-NEXUS_F7.config at 1d9cb4dc6f85c7895c2b089f4b8aa776ca3d3bd3](https://github.com/rotorflight/rotorflight-targets/blob/1d9cb4dc6f85c7895c2b089f4b8aa776ca3d3bd3/configs/RDMS-NEXUS_F7.config), Git blob `ca042b1f51a341a46980cb9aba78420beab48be7`, SHA-256 `063c35dc0ff54802eab4a18b6a202c45a773cd0d233fb8d90fa8e79ce1efca97`.

The target declares board NEXUS_F7, manufacturer RDMS, design F7A1. Its header identifies STM32F7X2/S7X2, 4.3.0-RC2, short source ba6c7e3 and MSP API 12.6. That is a source/config identity, not evidence of an installed release or downloaded binary. 

The text-only audit reads the exact PCB bytes directly, rather than treating prior pairing as firmware proof. It counts 558 physical pads, compares all 510 numbered PCB/native pad-map entries, and compares all 506 netlist nodes with the sole already-documented U13 `I/O3` versus `I{slash}O3` net-name alias. All pass. It explicitly verifies 14 connector signal chains and 11 sensor/flash endpoints. All six copper layers are present: F, In1, In2, In3, In4, B. The user's maximum-six-layer condition is met.

The audit rehashes the seven retained SPI/clock source files against their original SHA-256 and Git blob IDs; all match. It freshly retrieves the complete target, unified target header and DSM driver at the pinned refs, then verifies their Git blob IDs. No native engine, geometry operation, power solve, firmware build, flash, setting change or source mutation occurred. The local audit's first board-text pass was corrected to recognize KiCad 10's name-only net records; the successful output is the final receipt, not a waived mismatch.

## Resource and external function map

| Function | GPIO / U1 pad | Current endpoint/path |
|---|---|---|
| ESC MOTOR1 | PB6 / 58 | R24, 470 ohm, J6.3 |
| S1 / S2 / S3 | PB4 / 56; PB5 / 57; PB0 / 25 | R20/R21/R22, 470 ohm, J2/J3/J4.3 |
| TAIL SERVO4 | PB3 / 55 | R23, 470 ohm, J5.3 |
| RPM FREQ1 | PA2 / 16 | J7.3, R25, Q1, R39, RPM_MCU |
| SBUS RX2 / PPM1 | PA3 / 17 | J8.3, R26, Q2, R45, SBUS_MCU |
| DSM RX1 | PA10 / 43 | J12.3, R38, 22 ohm; R71 100 kohm idle pull-up |
| Port A UART4 RX/TX | PA0 / 14; PA1 / 15 | R30/R31, 22 ohm, J9.1/.2 |
| Port B USART6 RX/TX | PC6 / 37; PC7 / 38 | R32/R33, 22 ohm, J10.1/.2 |
| Port C USART3 RX/TX | PB10 / 28; PB11 / 29 | R34/R35, 22 ohm, J11.1/.2 |
| Gyro SPI1 | CS PA4/20; SCK PA5/21; MISO PA6/22; MOSI PA7/23; IRQ PA15/50 | U2 ICM-42688-P pins 12/13/1/14/4 |
| Flash SPI2 | CS PB12/33; SCK PB13/34; MISO PB14/35; MOSI PB15/36 | U3 W25N01GVZEIG pins 1/6/2/5 |
| Barometer I2C1 | SCL PB8/61; SDA PB9/62 | U4 DPS368 pins 4/3; 2.2 kohm R7/R8; CSB high, SDO low for 0x76 |
| BEC / bus sense | PC1/9; PC2/10 | ADC_BEC from VX_RAW, 105k:20k; ADC_BUS from +5V_PERIPH, 68k:(16k+16k) |
| Green / red LEDs | PC14/3; PC15/4 | LED_GREEN_K / LED_RED_K |

Servo-header pins 1/2/3 are GND/VX_RAW/signal. Each A/B/C connector's pins 1/2/3/4 are MCU RX/MCU TX/+5V_PERIPH/GND; the named directions are from the flight controller's viewpoint. DSM pins 1/2/3 are +3V3_DSM/GND/RX. The [original RadioMaster NEXUS manual](https://cdn.shopify.com/s/files/1/0609/8324/7079/files/NEXUS_User_Manual.pdf?v=1718329689), linked from its official manual index, was downloaded and visually inspected on page 1. It shows these external signal families and no TX1 connector. Manual SHA-256: `751ed115ffc409ca3047f16024030eb725eb5da00f49b6193587d5ffc3503df3`. This verifies the published interface interpretation; it does not prove unseen factory test pads or mechanical harness mating tolerances.

The retained UART review follows native AF detection, pinSwap, HAL initialization and CR2.SWAP. Its source chain supports the reversed native TX/RX assignments on UART3/4/6. Resource-name agreement alone is not the reason they are considered supported. A live selected serial function and correct protocol settings still matter.

For [ordinary DSM reception](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/rx/spektrum.c), the pinned driver opens MODE_RX when no shared-port/SRXL telemetry condition applies, and ordinary non-half-duplex binding uses the RX resource. No PA9 route is needed for that source path. Configurations that require UART1 TX, including relevant half-duplex/SRXL telemetry paths, are not supported by this unconnected PA9 path and must not be claimed tested. No required ordinary DSM mode was found to depend on PA9.

## Feature interpretation and retained limits

The pinned unified build header explicitly includes ICM42688P gyro/accelerometer, W25N01G flash, DPS310 barometer, I2C/SPI, VCP, ADC and frequency-sensor paths. The target chooses gyro SPI1 with CW90/yaw 900, barometer AUTO/I2C1 and blackbox SPI2. These source selections agree with the current populated device connections. The DPS368 substitution has its separately reviewed DPS310-compatible register/detection path; it is not the original product's advertised SPL06-001 and no blanket drop-in equivalence is inferred.

Stock target defaults select one MOTOR and four SERVO resources, PWM 250 Hz, and disabled DShot options. MOTOR2 on PB3 is commented out. Turning TAIL into a second motor or selecting another output protocol requires the corresponding approved configuration; its presence in product marketing does not make it active in this target. PPM1 and SERIAL_RX2 intentionally share PA3 and require an appropriate selected receiver mode.

Nominal divider fractions are 0.16 for BEC and 0.32 for bus, consistent with the target's divider values 160 and 320. Battery/current meters are NONE. This is mapping and nominal-ratio evidence; ADC gain, offset, supply-reference behavior and loaded readings remain unmeasured.

The sealed timing ledger and current cleanup reference review bind the normal source envelope to 8 MHz HSE, 216 MHz core, nominal 27 MHz flash SPI2 and VERY_HIGH GPIO speed. The actual binary/registers, first/last-bit waveforms, loading and threshold stability are unverified. 240 MHz/30 MHz is an overclock stress case, not the stock acceptance envelope. Slow flash identification does not prove successful final-rate logging.

The approved documentation requests I2C1 400 kHz with internal pull-ups OFF, without changing the firmware or pins. It has not been applied. At nominal 54 MHz the verified stock algorithm produces TIMINGR 0x1095102A: assumed-edge 398.995 kHz, conservative fastest model 417.311 kHz. Therefore requested 400 is not a guaranteed physical Fast-mode limit. The 385 kHz refinement remains unapproved and unapplied. The historical ordinary approximately 790 kHz case remains outside an established DPS368 ordinary-mode guarantee. Retain the existing loading, rise/fall and separate MCU/sensor VOL checks; lowering frequency does not reduce instantaneous pull-up current.

## Remaining gates

1. **Binary and saved configuration:** identify the actual intended/downloaded binary with its hash and build/target origin, then confirm installed version, target/resources, selected port functions, clocks and settings on the first assembly. No binary identity can be derived solely from these source commits.
2. **Boot/service:** verify normal cold boot/reset, BOOT0 ROM entry and USB DFU/enumeration with the actual supply conditions; confirm oscillator startup and clock state. Static connections exist for USB PA11/12, BOOT0/SW1/R2, NRST, SWD and 8 MHz HSE. Connectivity is not ROM/USB operation. The absent PA9 TX1 should not be turned into an invented new pin requirement.
3. **Sensor, I/O and calibration:** confirm IMU identity and reported axes/directions against the board's intended mounting orientation under stock CW90/yaw 900; barometer 0x76/0x10 detection and stable calibrated readings; full-speed flash readback/logging; actual servo/ESC/RPM/PPM/SBUS/DSM/UART behavior and failsafe behavior under the chosen configurations. GPIO matching cannot prove sensor axis signs or protocol electrical behavior.
4. **Existing physical gates:** close physical I2C Fast-mode timing or obtain approval for the documented refinement, and perform the focused SPI/UART/protection waveform and functional checks already recorded in the exact cleanup review. Fresh candidate-bound DC/thermal/prototype acceptance is outside this mapping audit. No bench result or production/flight release is claimed here.

`receipt.json` contains every target resource, all 29 comparison rows, connector pinmaps, component endpoints, service pins, source hashes, original review bindings and explicit non-pass flags. `audit.py` reproduces the text-only checks against the included source/netlist inputs and the checkpoint PCB/native export. The primary manual bytes and rendered intermediate were inspected locally but are not included; the official URL and verified hash are retained.


## Portable text-only replay

From this firmware directory run `python3 -B audit.py`. Its default checkpoint root is three directories above this folder. For an independently located package, pass `--checkpoint-root PATH_TO_NATIVE0_CHECKPOINT`. Only Python's standard library is needed. The audit reads the exact checkpoint `hardware/f722-heli.kicad_pcb` and `native/after.native.json.gz`, plus included `inputs/fresh-paired.net`, `inputs/firmware-pinmap.json` and hash-indexed source files. Default execution changes no files. An optional `--output NEW_PATH` saves a new result without overwriting an existing file.

`SOURCE-NORMALIZATION.json` records the original audit identity, exact computational-chunk preservation after one locator substitution, identical parser AST and identical endpoint checks. Source snapshots and the historical contract are byte-preserved. The netlist has only its documentary design/source locator normalized to the public schematic path; original and normalized byte hashes are retained and all component/net nodes are identical. `receipt.json` preserves technical findings and original hashes while replacing private paths with public or source-artifact locators. Its documentary proof entries distinguish original receipt bytes from existing public normalized wrappers. Historical review files and the original manual are not computational replay dependencies. No binary, geometry or power replay is implied.

Normalized portable netlist SHA-256: `2ca61314b02815a26f5d2bed0a60b09302448a2940f9c666665f422671e4cab8`; original source SHA-256 remains `a48480a34f27b7c534df0bfce78cac9ad0bc2742aa6e458672a3060b2b0e3542`.
