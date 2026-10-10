# C12 placement assessment

Status: proposed geometry only. No route, plane, AC or assembly qualification is asserted.

C12 remains Samsung CL05B104KO5NNNC, 100 nF / 16 V / X7R, 0402. The proposed move is F(26.0625, 12.0) to F(26.3125, 12.0), unchanged −90° orientation. Native7 board and export hashes remain unchanged; full bindings and every relevant contact UUID are in the companion JSON.

C12 is the local 100 nF VDD bypass connected to U2.8. Its supply pad joins three .20 mm branches: the U2.8 feed, C11.1 and the R3 pull-up. It also directly overlaps retained feed track d9731330-cda6-44f0-811a-9cdea7ea0676. Rebuilding the terminal branch must preserve that actual source contact group. Its .20 mm ground leaf reaches the shared capacitor barrel at (25.375, 12.9); contacts with C11/C13 return tracks occur only inside that barrel. U2.6 and grounded-reserved U2.7 have separate retained returns.

The old U2.8 supply plus C12-ground centerline sum is 2.706909 mm. With the retained feed endpoint and barrel fixed, the proposed pose requires at least 3.142921 mm: a minimum increase of .436011 mm before routing detours. This excludes capacitor and plane paths and is not an inductance or loop-area result.

## Acceptance evidence

1. Preserve C12 part/value/footprint and exact 0.25 mm translation at unchanged orientation. Verify all moved copper, solder-mask, paste, courtyard and pad identities in the candidate native export.

2. Rebuild all three supply branches plus the .20 mm ground branch with full-width positive-area pad/retained-copper contacts. Restore every actual source contact group, including retained d9731330; losing its direct pad overlap is permissible only when the same complete U2.8 branch is positively reconnected.

3. Keep FB2.2, C11.1, C12.1, C13.1, R3.1, U2.5 and U2.8 in the intended physical filtered-rail component. Keep the R3 pull-up exclusive; do not turn its low-current leaf into the sole series feed for C12 or U2.

4. Preserve the independent U2.6 primary and U2.7 grounded-reserved returns. Validate the C12 branch landing on the shared barrel with drill-subtracted full-width/annular witnesses; identify any new shared C11/C13 copper outside that barrel.

5. Recompute the actual U2.8-C12 supply/ground loop geometry and reference-plane return path after refill, including minimum necks, annulus-to-plane continuity, neighboring signal antipads, and new common return impedance. Rebind C11/common-rail paths affected by the C12-to-C11 replacement; retain C13 connection evidence.

6. Use final routed lengths and actual capacitor/stackup assumptions for the local PDN/noise comparison. The geometric lower bounds below do not qualify inductance, loop area, transient noise, or assembly. The previously pending whole-board power/reference acceptance remains pending.

7. Pass combined-candidate clearance, drill/mask, source-terminal restoration and C/SPI/B peer gates. A local capacitor move must not be accepted solely because the RX separator opens.

## Manufacturer evidence and limits

The verified [DS-000347 v1.6, §§3.3.2 and 4.1–4.3](https://product.tdk.com/system/files/dam/doc/product/sensor/mortion-inertial/imu/data_sheet/ds-000347-icm-42688-p-v1.6.pdf) identifies the bypass values, actual supply/ground pin roles and 10 mV peak-to-peak supply-noise specification. The verified official indexed [AN-000393 v2.0 §2.1](https://invensense.tdk.com/wp-content/uploads/documentation/AN-000393_TDK-InvenSense-IMU-PCB-Design-and-MEMS-Assembly-Guidelines.pdf) calls for close decoupler placement, separate VDD/VDDIO capacitors and supply fanout wider than 6 mil. No numerical allowable capacitor displacement was found in that section.

The [current product page](https://www.invensense.tdk.com/en-us/products/6-axis/icm-42688-p) lists datasheet v1.9 and application note v2.4. Those latest downloadable texts were not retrievable during this pass; their complete review is not claimed. The retained .20 mm drills remain below the reviewed guidance’s greater-than-8-mil recommendation. Existing under-body and AC limitations remain separate.

The .25 mm move is therefore an engineering candidate requiring the listed evidence, rather than a manufacturer-approved placement or an automatically prohibited displacement.
