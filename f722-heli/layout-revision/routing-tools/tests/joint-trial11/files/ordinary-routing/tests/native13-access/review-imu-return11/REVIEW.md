# U2.7 shared ground-return review

Bound to accepted candidate57 / 11 opens, PCB SHA-256 `454b7bb2454695b49c039f3d97e5edefb1946912363bab00ef5ced6ba2b0ea16`. `review.json` records exact local input hashes, geometry identifiers, predicates and qualifications. No board was adopted or edited.

**Decision:** the inspected sources do not prohibit a shared via or require preservation of these exact two vias. This exact diagonal remains unqualified: it introduces new under-body copper, and its final plane return has not been checked after refill. Geometry alone establishes neither failure nor AC/noise equivalence.

## Manufacturer provisions

[TDK DS-000347 v1.6](https://product.tdk.com/system/files/dam/doc/product/sensor/mortion-inertial/imu/data_sheet/ds-000347-icm-42688-p-v1.6.pdf), section 4.1 p20: pin 6 is power-supply GND; pin 7 is RESV requiring GND. Reserved does not establish zero internal current. The current [TDK DS-000347 v1.9](https://d17t6iyxenbwp1.cloudfront.net/s3fs-public/2026-06/DS-000347%20ICM-42688-P%20v1.9.pdf?VersionId=XL060vOv88u6zsKx9dkBVJEyV452m0eq), dated 2024-11-12, was also inspected directly from the official product-page PDF link. Its pin 6/7 descriptions and bypass BOM are unchanged. Section 19 p108 explicitly references AN-000393, replacing the old AN-IVS-0002A-00 reference. No new dedicated-via-per-pin requirement was found. `datasheet-v1.9-comparison.json` records this bounded comparison and download provenance; no whole-datasheet equivalence is claimed.

[TDK AN-000393 v2.4](https://d17t6iyxenbwp1.cloudfront.net/s3fs-public/2026-06/AN-000393%20TDK%20InvenSense%20IMU%20PCB%20Design%20and%20MEMS%20Assembly%20Guidelines%20v2.4.pdf?VersionId=0JJT_E0010fzx6pG58sIeAXICnPVAVgn), section 2.1 p6, recommends multiple nearby ground vias and specifies drill greater than 8 mil, copper diameter greater than 12 mil, and fanout wider than 6 mil. Section 2.4 pp8-9 specifies ground returns at least 10 mil wide for 0.5/1 oz copper, symmetric outward fanout, and under-chip copper avoidance. These are actual layout provisions, not electrical absolute-maximum limits.

Both old and proposed returns use 0.20 mm drills (7.874 mil) and 0.25 mm traces (9.843 mil), below the literal drill/return-width dimensions. The 0.45 mm copper diameter exceeds 12 mil. These inherited departures need explicit disposition; rounding them into compliance is inappropriate.

## Physical comparison

Before, each pin had its own 0.850000 mm, 0.25 mm F.Cu lead to a separate 0.45/0.20 mm through via. The vias are 0.5 mm apart. Both baseline vias have 0.127629877 mm² positive annular contact with saved ground fill on each of In1 and In4, after drill subtraction.

After, pin 6's lead/via remain; pin 7 uses a 0.986154 mm diagonal, 0.136154 mm longer (16.02%). The receipt reports 0.086079 mm² copper overlap and 0.246543 mm of retained lead centerline covered by new copper. The pins share copper and a barrel. These quantities do not establish shared impedance or noise equivalence.

The dedicated-via search was negative only within x=22.3-24.7, y=12.5-14.0 mm under this transaction; it does not establish global impossibility.

## Added under-body copper

Predicate: proposed pin-7 F.Cu minus old pin-7 and retained pin-6 lead copper, intersected with the nominal 3.0 × 2.5 mm body, minus all U2 pad copper.

The buffer formula matching the route helper yields **0.026938344106 mm²**, bounded by x=23.366444661-23.584999397, y=12.563457051-12.850000000 mm. The earlier nominal-width estimate was 0.026937561832 mm². Native polygon error is 1e-05 mm; this is an envelope screen, not a stress calculation.

The diagonal leaves the pad sideways before clearing the body. The mounting-face rule forbids vias only, so the finite-clearance pass does not screen this new trace departure. A straight outward escape before turning is worth testing. Maximum package and assembly-tolerance envelopes remain review items.

## Prototype review gates

1. Resolve or explicitly disposition new under-body copper, asymmetric escape, 0.25 mm return width and 0.20 mm drill against TDK guidance. Check maximum body and assembly tolerances; test straight outward escape before the turn if feasible.
2. Save/refill the complete isolated candidate. Prove both pins reach continuous GND; measure shared-via annular contacts and plane necks after new FLASH_CS antipads. Baseline contacts do not transfer automatically.
3. Repeat native connectivity, DRC, critical-reference and supply/return checks against the exact final board hash. The sealed receipt is expressly non-native.
4. Review shared return and decoupling loops with final stackup, copper/barrel geometry, capacitor parasitics and justified switching-current assumptions. Pin 7 internal current is undisclosed. Record bounded prototype risk; exhaustive FEM is not inherently required.
5. Predefine first-article acceptance for bias/noise spectra, communication reliability and local supply-to-sensor-ground behavior. Test SPI/flash activity, regulator/load changes, temperature and vibration with fixed firmware/filter settings.

Only source checks and small read-only polygon calculations were performed. No native job, routing, heavy solver, bench test or canonical edit was performed. Other capacitor moves and the complete simultaneous transaction remain separate review scope.
