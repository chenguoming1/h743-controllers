# First-article verification plan

Engineering test plan, not completed test evidence. Do not connect a motor, spinning rotor, servo linkage or valuable receiver during initial testing. Use a protected bench supply, electronic/dummy loads, oscilloscope and suitable USB breakout/test equipment. Retain the actual assembled board revision, firmware binary hash, target configuration, supply/harness details and instrument captures with each result.

## 1. Assembly and unpowered checks

- Inspect orientation, solder bridges, QFN/WSON exposed-pad joints, header hole fill and both board faces. Check the explicitly documented tented-via/mask exceptions for exposed holes or solder wicking
- Verify physical header order using continuity, not silkscreen inference: lower exposed row GND, center VX_RAW, upper signal. Check GH A/B/C and DSM cable pin numbers against the assembly pinout before inserting a cable
- Confirm all regulated rails have no unexplained short to ground. Verify raw servo bus continuity among all seven center contacts and confirm it is not accidentally shorted to regulated 5 V
- Verify boot-button operation, SWD access, USB retention and complete mating/withdrawal of actual intended JR/GH/DSM plugs. Inspect the 1.10 mm header-hole adaptation, fixture alignment and solder fill

## 2. Controller-only power

- Start with all external ports empty and a current-limited bench supply. Choose a low inspection limit and increase only after observing expected startup rather than treating current-limit-induced brownout as a circuit failure. Do not exceed the documented controller-only budget without investigating the load
- Exercise nominal 5 V, intermediate BEC voltage and 12.6 V input. Measure VX_PROTECTED, +5V_BEC (nominal 5.088 V), +5V_PERIPH and +3V3_CORE at device pins; compare measured values against each component's datasheet tolerance, load and dropout conditions
- Capture cold startup, slow ramps, abrupt removal/reapplication and brownout. Measure ICM42688P supply rise at its actual power pin: verify its 10–90% rise interval against the 0.010–3.000 ms datasheet requirement. A typical simulation is not acceptance evidence
- Check converter switching nodes, input/output ringing, mux selection and reference/priority nodes. Inspect regulator/inductor/capacitor temperatures before increasing load. Establish measurement bandwidth and probe return technique

## 3. USB and source switching

- Initially use protected test equipment rather than a valuable host. Verify no bulk reverse power enters USB VBUS, the BEC input or another inactive source in all source-present/absent combinations
- Measure signal-pin leakage separately from bulk VBUS backfeed. Stock firmware disables application VBUS sensing; do not infer USB-IF-compliant self-powered detach behavior. Use a powered host for BEC-powered USB service unless a separately verified operating procedure establishes otherwise
- Test USB-only startup and enumeration, then BEC/USB insertion and removal in both orders. Capture +3V3_CORE and IMU supply transients, resets and device communication errors. Do not load USB as though it supplied the 2 A BEC-mode peripheral budget
- Verify BOOT/ROM DFU and SWD recovery with receivers disconnected or quiet. Read and record relevant option bytes; do not change protection settings blindly

## 4. Firmware and interfaces

- Load an official supported Rotorflight binary and the stock NEXUS_F7 target; record the exact binary/version. Recheck every resource and UART swap after configuration
- Verify accelerometer/gyro axes against the board's −Y forward arrow through deliberate hand rotation. Check gyro noise/vibration sensitivity, interrupt operation, I2C barometer detection and plausible pressure readings, and NAND identify/read/write/erase
- Record `gyro_1_sensor_align=CW90`, the stored alternative `gyro_1_align_yaw=900`, and actual `align_board_roll/pitch/yaw` values. The reference mounting convention uses all three board offsets0°. Sensor CW90 and custom yaw900 are alternative representations, not two successive90° rotations; retained nonzero board offsets must be reconciled with the actual installation before interpreting motion
- Calibrate/check displayed BEC and bus voltages against measured values; retain the stock divider ratios/scales unless a measured manufacturing deviation justifies investigation
- Test A/B/C, DSM and SBUS with current-limited dummy peripherals first. Verify receiver frame integrity, loss recovery and failsafe behavior. Inject representative RPM signals within documented electrical limits
- Observe all four servo outputs and ESC output on a scope/dummy load before connecting actuators. Verify startup, shutdown and receiver-loss behavior; do not rely only on successful firmware enumeration

## 5. Load, thermal and protection characterization

- Increase regulated loads in steps. ABC is 2 A aggregate on BEC power, not 2 A through each JST-GH contact; obey the chosen contact/wire rating. DSM nominal load allowance is 0.5 A. Account for core consumption in USB/source budgets
- Measure rail drop, ripple, mux/limiter behavior and temperatures at the lowest input voltage and worst intended ambient. Test repeated source switching at load. Evaluate regulator startup stability with actual capacitance and component tolerances
- Qualify the complete raw servo harness, mating contacts, input contact and return conductor with realistic simultaneous servo transients. This design currently asserts no qualified continuous or peak current for an unspecified JR-style harness
- ESD/surge, abnormal input and short-circuit tests require controlled fixtures and a defined test plan. Listed TVS parts and simulated thresholds do not establish an IEC compliance rating or arbitrary miswiring immunity

## Release boundary

Keep motors mechanically disconnected until power, interfaces, sensor direction and failsafes pass documented bench tests. Subsequent restrained-system and flight evaluation requires a separate risk-controlled validation program. Native ERC/DRC, a successful assembly, or stock-target matching alone does not establish flight readiness.
