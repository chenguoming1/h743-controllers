# Preferred local support proposal: quarter-shift R50

**Preferred over the shared-crystal-via and crystal-pad-bridge alternatives, subject to complete transaction and native gates.** It preserves both original Y1 ground leads/vias and all HSE/load-cap geometry. It does not establish oscillator, ESD, AC, transient or loaded-power qualification. `REPORT.md` and `ALTERNATIVE-V5.md` remain historical alternatives; neither describes this preferred geometry.

## Exact evidence and local screen

Reviewed `../u12-r50-quarter-shift17-screen.json`, SHA-256 **`23c445977b5fcc82ac488a3e1094bbb851e9654246eeaa1305cd8b3c4597792a`**, against `tests/sbus-nrst49/candidate02/f722-heli.native.json` and its board SHA-256 **`71d33748909bb960c5829973642272460607d8521831a6212975f7de6790d660`**. The saved file contains 11 paths, two SERVO1 vias and 69 mutual comparisons, all passing their recorded checks; no path/via violations. Minimum saved path extra clearance is 0.006000 mm, minimum via extra clearance 0.021810 mm, and minimum mutual physical gap 0.163000 mm. These are **local screen results**, not a native DRC/refill pass.

R50 remains **1.5 MΩ / 1%, F.Cu, 0°**, shifted only +0.25 mm to (11.95,13.6). Pad 1 VX_RAW is (11.44,13.6); pad 2 EFUSE_EN is (12.46,13.6). The two proposed SERVO1 vias are (10.307854,12.958635) and (10.8,13.29). Unlike the previous alternatives, the removal list retains Y1.4's original lead UUID `326bfc04-07f8-45fc-933b-6205a02da9ff` and via UUID `fb5a234c-5d52-4584-aadd-252a670e4869`.

## Original → preferred support geometry

Lengths are explicit trace centerlines, including copper under pads, in mm. Every GND pad below still reaches its first ground plane using one 0.45 mm / 0.20 mm through via. No new GND via is added; only U12's original via (11.27,10.89) is removed.

| Path | Original length | Preferred length | Width and layer | Preferred first via |
|---|---:|---:|---|---|
| U12.2 | 2.227500 | 2.513660 | 0.25 F.Cu | (13.5984,13.4847) |
| Y1.2 | 1.050018 | unchanged | 0.25 B.Cu | (10.2299,11.7982), original |
| Y1.4 | 1.049967 | unchanged | 0.25 B.Cu | (13.1048,13.3702), original |
| C18.2 | 1.455793 | unchanged | 0.20 B.Cu | (10.2,15.35), original |
| C19.2 | 1.250025 | unchanged | 0.25 B.Cu | (10.874,9.9139), original |
| R51.2 | 1.750005 | 3.838234 | 2.157074 at 0.20 + 1.681160 at 0.25, F.Cu | (13.5984,13.4847) |
| R52.2 | 3.860858 | 2.517386 | 0.20 F.Cu | (13.5984,13.4847) |
| C30.2 | 1.249987 | unchanged | 0.25 F.Cu | (16.4574,15.8435), original |

U12 and R51 join at (12.5,12.72), then share the **1.681160 mm / 0.25 mm** lead through (13.5984,12.92) to the retained eFuse GND via. R51's revised 2.157074 mm / 0.20 mm approach follows (12.21,14.55) → (11.95,14.15) → (11.95,13.2) → (12.5,12.72), through R50's shifted central gap. R52 approaches the same via separately. Thus **U12/R51/R52 still share a local return**; the crystal pads do not join that outer-layer trace or via.

Y1.2 and Y1.4 retain their separate original traces and vias. Y1.4's via is 0.506706 mm center-to-center from the eFuse via, so retaining a distinct via does not establish zero plane coupling. Saved native geometry confirms positive conductive annulus contact to the existing In1.Cu and In4.Cu GND fills for all six retained vias in the table: 12 checks, each 0.12762988 mm² after drill subtraction. All connect to system GND; no electrical isolation is claimed. Fresh fill remains pending.

C18 remains separately stitched. C19 already shares its retained return with C9.2; neither joins the crystal case leads on B.Cu. C30 remains the **ADC_BEC** 220 nF filter capacitor, not eFuse DVDT; C50 is the actual 3.3 nF DVDT capacitor. R51 remains 390 kΩ / 1% OVCSEL and R52 750 Ω / 1% ILM. Their common impedance with U12 is an outstanding transient issue, despite preserved values and pin identities.

## EN and VX_RAW reconstruction

EFUSE_EN remains R50.2 → U5.1 (TPS259472ARPWR), now **3.706286 mm / 0.127 mm F.Cu**, zero vias, versus 2.556360 mm / 0.20 mm originally. Route: (12.46,13.6) → (12.81,13.95) → (12.81,15.1) → (11.55,15.1) → (11.16,15.8).

The pinned [TI Rev. C limits](https://www.ti.com/lit/ds/symlink/tps25947.pdf), exact source and conditions documented in `REPORT.md`, remain applicable to the bounded comparison: EN leakage ±0.1 µA, rising UVLO at most 1.223 V, R50 at most 1.515 MΩ, producing 0.1515 V leakage sensitivity. With source-declared 35 µm F.Cu and nominal 20°C copper resistivity, the new trace is **14.375 mΩ**, giving **1.44 nV** at 0.1 µA or **0.223 µV** under the loose positive-current bound 23 V / 1.485 MΩ. This supports the negligible-DC-drop conclusion only. It does not qualify noise, contamination leakage, pin-clamp operation, startup transients or power handling. TI's ≥350 kΩ pullup recommendation for above-5 V/reverse-input exposure remains satisfied.

VX_RAW's junction shifts (10.59,13.65) → (10.4,13.65). The complete local reconstruction is:

- Feeder from (6.6,13.65): **3.990000 → 3.800000 mm**, 0.30 mm F.Cu.
- Junction to R50.1: **0.882456 → 1.341462 mm**, 0.30 mm F.Cu, via (10.55,13.93) and (11.1,13.93).
- Junction to (9.7,14.0): **0.956347 → 0.782624 mm**, 0.25 mm F.Cu.

All are zero-via branches. This verifies reconstruction geometry, not a fresh loaded-power/current-distribution result.

## HSE and decision boundary

All original HSE signal pads/tracks, Y1/R9/C18/C19 parts and poses, both case-ground paths and load-cap returns are retained. HSE traces remain 0.15 mm B.Cu with zero signal vias; their totals and exact identities are in the historical evidence. The exact **YJX TAXM8M4RDBCCT2T / C400090** sheet is retained as `YJX-TAXM8M4RDBCCT2T.pdf`, SHA-256 `4801ca5b00287fb05fa004a0148933f7ed330b98f7a87a8b326d31e63b1ef34d`. Its visually checked Connection drawing marks pads 2 and 4 GND, resonator between 1 and 3. It does not establish internal case-pad bonding or waive board-level verification; see the source links and limitations in `ALTERNATIVE-V5.md`.

This proposal removes the newly introduced crystal/TVS via-sharing and 3.830305 mm crystal daisy-chain concerns of the historical alternatives. It creates no direct change to the crystal return topology. Remaining neighboring-copper/plane changes and the U12/eFuse shared return still prevent a blanket electromagnetic or ESD-equivalence claim. Complete the final route transaction, fresh native fill and native DRC/pose/process/finite/support/cut/reference gates. Oscillator startup/immunity and system ESD/transient qualification remain separate release requirements where required.

Reproducible evidence: `preferred-quarter-shift-evidence.json`, `preferred-quarter-shift-run-summary.json`, and `review_preferred_quarter_shift.py`. All reviewed inputs and historical reports were verified unchanged; outputs stay within this review directory.
