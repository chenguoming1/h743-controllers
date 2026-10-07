# Prototype and fabrication gates

## Supplier and exact-part gates

**Battery/harness: unresolved.** Capacity was not fixed by the user. The former 500 mAh target is not an approved pack. Publicly documented compact leads are KBT-602035PL (380 mAh, 35×20×6 mm, 760 mA continuous) and KBT-602535PL (500 mAh, 35×25×6 mm, 1 A continuous). Their public information did not establish the needed charge-temperature, NTC and charger-voltage-tolerance limits. These are candidates, not approved substitutions.

The investigated LP412550 includes a correctly ordered 3-wire JST-SH harness and NTC, but its 500 mA continuous rating and 0–45°C charge window do not close the worst-case load/temperature requirements. A protection trip threshold is not a permitted pulse-current rating. The larger TinyCircuits ASR00012 1 Ah pack is a documented fallback only; its 40×30 mm size materially enlarges the device and requires timer/current/harness reconsideration.

BQ24074's illustrated TS resistor network can extend the direct-NTC window, not simply tighten it. A generic 10 kΩ/3950 NTC was not bounded to the desired maximum temperature at all charger/sensor corners. A proposed comparator interlock was rejected because its startup state did not guarantee charge inhibition. Firmware alone is not accepted as MCU-off charge-temperature protection.

Before selecting a pack, obtain:
- Exact protected-cell/PCM and harness drawing, dimensions, polarity and connector keying
- Manufacturer charge-temperature limits and the complete NTC R/T curve and tolerances
- Allowed charge current, maximum charge voltage including regulator tolerance, and continuous/pulse discharge ratings with duration/duty limits
- Charge safety-timer compatibility at minimum charge current, including USB input limiting and system load
- Genuine availability and applicable shipping/cell certification documentation

**GNSS receiver:** MIA-M10Q-00B public listings showed zero stock. Incoming dates are not supply commitments. Do not silently substitute a different module.

**Antenna:** exact INPAQ PA1575MQ4S-123-1Z stock was not verified. Its derived host footprint needs exact-part and assembly confirmation. No coax alternative is included.

See `component-qualification.md` and `battery-thermal-followup.md` for source links and calculations. No supplier messages or orders were sent.

## Bench qualification

- GNSS feed matching, antenna S11, acquisition/sensitivity, orientation, battery/enclosure influence and Wi-Fi/BLE coexistence
- USB differential signal quality, enumeration/recovery, programming, ESD, cable/orientation behavior and validated current-mode policy
- Power startup/load transients, minimum-cell operation, 3V3 droop, battery supplement mode, USB100 operation without a healthy cell, charger termination/timer/temperature behavior and converter/charger temperatures
- ADC calibration and power-off isolation, strap recovery and G/R/S behavior under actual firmware
- First-article mechanical fit, patch pin/adhesive/solder assembly, switch direction and LED visibility

## Release status

The native CAD checks are not a substitute for these gates. Manufacturing CAM, assembly BOM/CPL and purchase instructions are deliberately not released in this package. The schematic component fields document selected parts for engineering review. The next external step is exact supplier/pack qualification and fabricator/assembler review, under separate authorization; no automatic outreach or ordering is implied.
