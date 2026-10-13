# Static IMU orientation for the A/B-edge-forward mounting reference

**The current U2 orientation is statically consistent with the pinned Nexus CW90 transform when F.Cu faces up and the A/B connector edge is forward.** KiCad's 0-degree footprint pose does not conflict with a firmware CW90 sensor transform. No PCB, silkscreen, firmware or setting change is indicated by this check.

The exact PCB is `84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd`. U2 is ICM-42688-P at `(23.209999, 11.6)`, F.Cu, 0 degrees. This addendum explicitly documents forward as PCB negative Y, toward J9/J10 (A/B), with F.Cu upward. The original [RadioMaster Nexus manual](https://cdn.shopify.com/s/files/1/0609/8324/7079/files/NEXUS_User_Manual.pdf?v=1718329689), page 1, shows its case arrow toward the A/B side, while DSM/C are on the opposite side. The current connector arrangement preserves that reference. No explicit current PCB direction arrow was found. An installation using another heading is outside this zero-board-alignment reference.

## Actual package and footprint basis

The [TDK ICM-42688-P datasheet, revision 1.6](https://product.tdk.com/system/files/dam/doc/product/sensor/mortion-inertial/imu/data_sheet/ds-000347-icm-42688-p-v1.6.pdf), pages 20 and 54–56, was visually inspected. Its top-view numbering has pad 1 at the upper-left; 1–4 descend the left edge, 5–7 cross the bottom, 8–11 ascend the right, and 12–14 cross the top toward the left. The current PCB and library agree on all 14 nominal pad centers, including pad 1 `(-1.1625,-0.75)`, pad 4 `(-1.1625,+0.75)`, pad 5 `(-0.5,+0.9125)` and pad 14 `(-0.5,-0.9125)` mm relative to U2. These match the TDK package numbering and nominal pattern. The library's ST-derived description is stale metadata; it is not evidence of a different actual numbering. This does not constitute complete solder-process qualification.

Using PCB X right, PCB Y down, and physical Z out of F.Cu, the datasheet's pin-1-marked axis diagram gives raw sensor +X right, +Y toward PCB negative Y, and +Z upward. The receipt records this explicit physical basis so a drawing rotation cannot be confused with a firmware rotation.

## Pinned source path and single transform

All source links below use firmware commit `ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94`; the companion resource receipt pins the exact Nexus target.

1. [ICM driver](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/accgyro/accgyro_spi_icm426xx.c) selects the accelerometer X register at 0x1F and gyro X register at 0x25, and uses the shared SPI read functions.
2. [MPU SPI read functions](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/accgyro/accgyro_mpu.c) place consecutive X/Y/Z register pairs into X/Y/Z raw array entries, with byte-order conversion and no intervening axis permutation or sign negation in either interrupt or DMA path.
3. [Gyro initialization](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/sensors/gyro_init.c) loads the configured standard alignment and constructs a separate custom matrix. [Accelerometer initialization](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/sensors/acceleration_init.c) copies alignment from the active gyro.
4. [Gyro processing](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/sensors/gyro.c) and [accelerometer processing](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/sensors/acceleration.c) select the custom matrix only for ALIGN_CUSTOM; otherwise they select the standard rotation. These are mutually exclusive branches, not two successive rotations.
5. [CW90 implementation](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/sensors/boardalignment.c) gives `(outX,outY,outZ) = (rawY,-rawX,rawZ)`. The target's yaw=900 is 90 degrees in decidegrees; the [matrix construction/application](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/common/maths.c) gives the same mathematical rotation when selected as the custom alternative. No 180-degree double rotation occurs. This mathematical equivalence does not claim bit-identical floating arithmetic.

Consequently aligned +X points toward the A/B edge, aligned +Y toward PCB negative X, and aligned +Z out of F.Cu. A nonzero board-level installation alignment would add a separate intentional correction; its source default is zero and its live value was not inspected.

## Scope of closure

The static package-basis, raw register order, source branch selection and intended mounting reference are now explicit. No source-bound orientation mismatch was found. U2 was not moved by the current cleanup; this checks the inherited pose rather than attributing any hypothetical issue to the latest routing.

The first assembly must still verify actual component orientation, installed binary/settings, calibration, and matching physical/3D-model pitch, roll and yaw directions before any powered motor test. [Rotorflight's orientation guidance](https://doc.rotorflight.org/configurator/tabs/configuration/#board-and-sensor-alignment) requires the model to follow real movement. These checks detect assembly, installation and runtime errors that static arithmetic cannot exclude. No flight or runtime qualification is claimed.

`receipt.json` binds the PCB, complete U2 record, library, all 14 pad centers and source blobs. `verify.py --checkpoint-root PATH` repeats only text, source-hash and simple matrix checks using the existing checkpoint hardware. The primary PDF bytes were inspected locally but are not distributed here; their verified URLs and hashes are retained. No native engine, geometry solve or firmware build is required.
