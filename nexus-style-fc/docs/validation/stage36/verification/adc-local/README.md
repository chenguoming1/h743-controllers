# Stage36 saved-board ADC / DSM proof

**PASS for the read-only checks below.** Source SHA-256 before and after:
`bed37199e8d62b8135a27b9e182f8e8f584f1a9fb722cb6efb5d4c87b2a320b8`.

## Actual saved routes

Centerline lengths measured between saved pad centers through exact trace endpoints and via layer transitions:

- C29.1 → U1.9: **3.052332 mm, one via**
- C30.1 → U1.10: **3.974130 mm, one via**
- C29.1 → R16.2: **2.583509 mm, F-only**
- R16.2 → R17.1: **2.393714 mm, F-only**
- Complete C29.1 → R17.1 filtered-node branch: **4.977224 mm, F-only**

All four filter/divider signal pads have saved same-net tracks ending exactly at their centers. JSON contains every measured segment UUID, layer, coordinate and length.

## DSM repair

- Repaired branch from the existing (108.775,123.675) B-side via node to the In2 junction (116.715,117.985): **10.796515 mm**.
- The repurposed via at (110.590858,121.956) is DSM_TX, with exact-center B.Cu and In2.Cu contacts. Former DSM via at (111.025,123.675) is absent. Total DSM via count remains **6 → 6**.
- No foreign-net track/pad contact within 0.127002 mm on any of six copper layers; no either-surface pad contact within 0.100002 mm. These checks use the saved via's effective shapes.

## Preserved clock/reset tree

C10, C12 and Y1 have exactly the stage33 positions, rotations, sides, UUIDs, pin nets and pin coordinates. Explicit copper from retained GND stitch (110.375,122.525) reaches C10.2, C12.2, Y1.2 and C25.2. The original clock-tree segments remain unchanged except the already documented replaced stitch link.

The MCU ground branch `b3bcbf59-1c89-5cf2-b4dc-6f5eb5687b30` was extended from endpoint (111.77,119.4) to the new C29 GND stitch **(111.775,119.6)**. Its saved endpoint is exactly at that via center. C29.2→stitch is **0.779118 mm F**; U1.12→stitch is **2.065564 mm B**. This is an explicit retained MCU connection, not a discarded return.

## Evidence and limits

- `prove_saved_adc.py`: reproducible read-only check
- `saved-board-proof.json`: complete machine-readable route/contact/pose evidence
- `saved-board-proof.log`: execution result

No source edits, PCB saves, refill or DRC occurred. The parent's accepted native 0 errors / 0 opens / 0 parity was not rerun. Ground-fill/reference-plane and Y1.4 zone-grounding proof remain the separate auditor's scope.
