# V2 addendum: finished thickness and header-bore sensitivity

## Result

The optional 1.65 mm finished-thickness screen adds approximately **0.574 mV** of board-only drop and **5.134 mW** of board dissipation to the conservative uneven 10 A single-feed cases with the main load on T2/T1. Adding a **0.97 mm header-bore** resistance screen raises the combined change to approximately **1.149 mV and 10.250 mW**. The original qualification verdict is unchanged.

The original V2 report, seal, source PCB, geometry and sheet matrices remain unchanged. This addendum supplements the nominal 1.60 mm barrel calculation; it does not supersede the full review or establish an operating rating.

## Scope and source binding

- Child PCB SHA-256: `b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6`.
- Original report SHA-256: `9ad7fcc92386038b26c33c89b6461976769081c244c4c8ffbd28f441ac291fc2`.
- Sheet matrix SHA-256: `7ce62203e95796dcfdf6eae2e303052ef29257839f9ab54e343f592acf494dba`.
- Optional matched-fit manufacturing proposal: `/workspace/scratch/8a35c1f26232/nexus-child-power-redesign/candidate-continuous-vx-unfinished/verification/mechanical/PCB_ONLY_PROPOSAL.md`, SHA-256 `cf32a5c650c95eb303f9ddb3e7d8ae389ec754558036be9b56e859ba47fc72ee`. Its supplier-controlled box permits complete finished thickness 1.60–1.65 mm; it is a proposed acceptance condition, not an accepted supplier guarantee.
- The [exact Hanxia HX PZ2.54-3x7P ZZ drawing](https://www.lcsc.com/datasheet/lcsc_datasheet_2407231541_hanxia-HX-PZ2-54-3x7P-ZZ_C32713294.pdf), first PDF page, shows a recommended Ø1.02 mm PCB hole and PCB tolerance ±0.05 mm. This supports screening 0.97 mm as the recommendation’s lower endpoint. The current CAD remains 1.00 mm nominal. No fabrication-hole tolerance is assumed accepted. The locally inspected PDF SHA-256 is `b44606922b5eca64eafbe10a439688848635336dbf1bba66a53dd5ae916e88f8`.

Only the already-condensed **38-terminal networks** were solved. All header and power-via barrel lengths were changed from 1.60 to 1.65 mm, increasing their resistances by exactly 3.125%. Using the complete finished board thickness as barrel length is a conservative length screen, not a measurement of actual current-path length between copper layers. The optional bore case additionally changes only header barrel resistance from 1.00 to 0.97 mm bore; power-via bore remains 0.30 mm. All saved sheet geometry and ideal per-face land electrodes are retained, including the original 1.00 mm header holes. This isolates barrel sensitivity and does not reproduce changed annular geometry or evaluate pin fit.

## Conservative uneven 10 A benchmark

Servos are 4.5/1/1/2.4 A plus a fixed 1.1 A abstract main-board load. Conditions: 60 µm sheet copper, 80°C prescribed conductor temperature, 95% IACS, 18 µm barrel wall, 0.075 mm sheet grid, B.Cu feed/load injection. One complete feed pair is open; the surviving positive and return each retain the illustrative 40 mΩ lead/contact resistance. Main copper, tab-solder resistance, output harnesses and mating contacts are outside the board model.

### Length-only change, both main-load landing options

| Feed | Main load | Board drop, 1.60 → 1.65 mm (mV) | Change (mV) | Sheet loss at 1.65 mm (W) | Barrel loss at 1.65 mm (W) | Total loss at 1.65 mm (W) | Total change (mW) |
|---|---|---:|---:|---:|---:|---:|---:|
| SBUS only | T2/T1 | 37.734244 → 38.308230 | 0.573987 | 0.173575327 | 0.169377227 | 0.342952555 | 5.134140 |
| SBUS only | K2/K1 | 37.520086 → 38.094535 | 0.574449 | 0.165119355 | 0.166475351 | 0.331594706 | 5.046361 |
| ESC only | T2/T1 | 28.659832 → 29.233783 | 0.573951 | 0.083259900 | 0.169364492 | 0.252624391 | 5.133742 |
| ESC only | K2/K1 | 28.814347 → 29.388768 | 0.574421 | 0.082172566 | 0.166467584 | 0.248640150 | 5.046119 |

For T2/T1, the sheet/barrel loss increments are respectively **+0.098226/+5.035914 mW** with SBUS-only, and **+0.097475/+5.036268 mW** with ESC-only. Total dissipation is recalculated after current redistribution; it is not obtained by multiplying the old total by 1.03125.

### Combined 1.65 mm length and 0.97 mm header bore

| Feed | Main load | Board-only drop (mV) | Change from original (mV) | Sheet loss (W) | Barrel loss (W) | Total loss (W) | Total change from original (mW) |
|---|---|---:|---:|---:|---:|---:|---:|
| SBUS only | T2/T1 | 38.882997 | 1.148754 | 0.173670270 | 0.174398288 | 0.348068558 | 10.250143 |
| SBUS only | K2/K1 | 38.669755 | 1.149669 | 0.165224624 | 0.171423170 | 0.336647795 | 10.099450 |
| ESC only | T2/T1 | 29.808550 | 1.148718 | 0.083354842 | 0.174385552 | 0.257740394 | 10.249745 |
| ESC only | K2/K1 | 29.963988 | 1.149642 | 0.082277836 | 0.171415404 | 0.253693239 | 10.099208 |

For T2/T1, the combined sheet/barrel loss changes from the original are **+0.193169/+10.056974 mW** with SBUS-only and **+0.192417/+10.057328 mW** with ESC-only. The minimum servo-pad voltages with the illustrative 7.4 V source and 40+40 mΩ surviving leads are **6.561117 V** and **6.570191 V**, respectively. These are not servo-terminal voltages after real output wiring.

## Checks, secondary sensitivities and limitations

The length-only run contains 128 small network solves: both single-feed failures, both main-load ports, both saved grids, four material cases, 18/20 µm walls and the two lengths. The optional bore run adds 64 terminal solves. All 1.60 mm reruns reproduce the original terminal voltages and total board loss exactly in this environment. Maximum network residual is 1.001×10⁻¹⁰ A and maximum power-balance error is 1.737×10⁻⁷ W. No native KiCad job, copper mesh generation or large sheet solve was run.

At 1.65 mm length, T2/T1 and the fine grid:
- Nominal 70 µm / 20°C / 100% IACS / 18 µm walls: SBUS-only **27.318204 mV, 0.244551 W**; ESC-only **21.338817 mV, 0.185031 W**.
- Conservative 60 µm / 80°C / 95% IACS but 20 µm walls: SBUS-only **36.379145 mV, 0.325695 W**; ESC-only **27.304832 mV, 0.235368 W**.

The 80°C value is prescribed conductor temperature, distinct from the proposed 40°C ambient bench condition; no equilibrium temperature or temperature rise is solved. The sensitivity does not relax the retained header’s unsupported 10 A feed/contact demand, qualify the 4.5 A output contact, establish actual BEC-lead resistance, certify a 25 A pulse, resolve solder/pin current sharing or demonstrate flight safety. The 60 µm sheet, 18 µm local barrel wall, finished thickness and hole-size bounds still require explicit fabrication acceptance and inspection. The actual main electronics load must be established separately, especially for voltage-dependent conversion loads.

Full-precision results and verification records: `barrel-length-sensitivity.json`, `header-bore-sensitivity.json`, `ADDENDUM-SEAL.json`. Reproduction scripts in the parent audit directory: `solve_barrel_length_addendum.py` and `solve_header_bore_addendum.py`. Original sealed report: `../V2-POWER-REVIEW.md`.
