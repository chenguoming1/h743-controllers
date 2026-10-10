# Exact candidate 43 I2C review

**Recommendation: accept this exact source as geometric WIP, with electrical qualification and numerical power/VCAP revalidation still pending.** The receipt is `intentional-i2c-acceptance.json`. It is specific to candidate 43 and is not a waiver for future I2C edits or other critical-net changes.

Candidate 43 SHA-256: `1ee7174a578dffe4d5ef3ae8b39d8dc88f28b80395539263a65f23be234c21e6`.

Accepted source 41: `539d9547eb8c4d5984481293ae10cee34355ee838dff11ab43b00cca270ceae2`. Intermediate source 42: `eac130eb32389c82b2bae274e2c50b73675c79d442cfc8441956369b4cdf3304`. Candidate 42 reports and their topology refusals remain untouched.

## Verified scope and guards

- Exactly five SDA tracks were replaced between 42 and 43. Every retained object, every footprint, all vias, all power objects, all zone definitions **and saved fills**, outline and layers are exactly equal. The declared old/new records match the actual exports. The In2 dogleg is now 0.20 mm; the In3 horizontal is 0.15 mm followed by an explicitly non-octilinear straight segment into the existing via.
- Both I2C nets are native-complete with their exact three terminals. Recomputing the unchanged strict topology function gives one clean tree, cycle rank 0 and no dangling nonterminal endpoints for each. The former 42 copper-only junction refusal is retained as a negative control and is rejected by this acceptance path.
- All 16 previously complete critical nets retain exact native object equality against41. Their union-of-track centerline and trace-width reference deficits are exactly preserved, with zero overlap between these traces and lost GND reference copper. This includes USB/CC, HSE, IMU, VCAP and the analog/IMU supply nets.
- Both physical reference planes remain one connected polygon after drill subtraction. All 118 accepted plated GND ties contact the main component on both planes. Compared with 41, each plane loses 1.9906491978695413 mm² and gains 0.08114063904254071 mm². Compared with 42, those planes are unchanged. Changed fill is as close as 0.237115187 mm to +3V3_IMU and 0.285417269 mm to IMU_INT trace copper, so there is no broad claim of unchanged electromagnetic surroundings.

The controls exercise actual 43 acceptance and rejection of: wrong board identity; altered unrelated critical copper; wrong I2C terminal inventory; original 42 strict topology refusal; added critical reference loss; wrong board/snapshot binding; and wrong geometry/snapshot binding. These use exact comparisons, not an area epsilon.

## Actual I2C geometry and remaining reference deficits

| Net | F.Cu mm | B.Cu mm | In2.Cu mm | In3.Cu mm | Total mm | Pull-up branch outside lands mm |
|---|---:|---:|---:|---:|---:|---:|
| SCL |5.565973691|2.360894919|6.870045421|4.799239578|19.596153609|2.127846424|
| SDA |1.421812409|1.508505425|10.576366517|9.093784306|22.600468657|0.155|

Every track is 0.127 mm wide. Each line has three 0.45 mm land / 0.20 mm drill vias spanning all six copper layers. Native length includes all branches and in-land lengths; it is not the shortest device-to-device path.

Relative to 42, SDA grows 0.08600584059955452 mm. Its missing reference centerline grows 0.0020720262303877135 mm, while summed missing trace-width area decreases 0.00097957113440178 mm². SCL is unchanged. Those deltas are explicitly reported, not labeled “unchanged I2C.”

The current report totals are:

- SCL: 2.526403558104753 mm missing centerline and 0.3896450564992601 mm² missing width projection.
- SDA: 2.4695734090251333 mm missing centerline and 0.35719604034707164 mm² missing width projection.

All reported missing centerline lies inside the own-via spatial windows. This class is not an electrical exemption. SCL still has a real outside-window width deficit of**0.000010190091226732164 mm²** in the merged SCL/PORT_C_TX_EXT hole by the sensor via at (21.4815,21.33). Its extents are 0.007018421103605732 mm along and 0.026974000000002718 mm across the trace, 0.036525999999998504 mm from the centerline. It remains accepted only as specifically reviewed geometric WIP.

The changed SDA approach no longer produces42’s 0.00062416369074 mm² physical outside-window region. The standard component report has zero SDA outside-window area; our independent no-threshold decomposition additionally preserves 7.621748690956714e-18 and 1.3611079810052984e-17 mm² floating fragments verbatim. Nothing is rounded to zero or used to establish an electrical pass. Full polygons, component dimensions, merged-hole membership and source hashes are in `scoped-review.json`.

Both merged holes remain internal holes of connected planes. Nearest proven GND-tie distances remain 0.597791268–2.043077398 mm. The farthest is the SCL In3↔In2 transition. These are contact/continuity facts; return inductance and coupled waveforms are unqualified.

## Capacitance and RC remain unqualified

Both current capacitance reports refuse an estimate because material and manufacturing bounds, etch/registration, external-copper distance, probe loading and model allowance/evidence are absent. The former topology refusal is now absent. No missing value was filled with an invented bound, and the checker’s exit 2 remains appropriate.

The existing 25 pF device/pad/assembly allocation is unverified engineering allowance. It leaves 25 pF for routed copper, vias, uncertainty and any probe within the provisional 50 pF target. With external-only Rmax=2244.22 Ω, the first-order rise screen is 1.901527606 ns/pF: 50 pF gives 95.0763803 ns; 100 ns corresponds to 52.5892969865198 pF. These are budget calculations, not an extracted or measured candidate 43 capacitance or rise time. No internal-pull-up credit is taken.

Still required: reviewed load-model inputs and a source-bound per-net capacitance ledger; DPS368 ordinary 800 kHz/Fm+ and 3.3 V VOL/IOL evidence; pin-capacitance bounds; rail/ripple/transient checks; installed firmware/settings/clock/TIMINGR readback; and first-article MCU- and DPS-driven edges, timing, levels and error-rate tests. Rise-time RC arithmetic does not qualify fall edges or return/coupling behavior.

No numerical power/VCAP pass is inherited. Apply this receipt only after the owner’s other required native, process, entry, support, mechanical and parity guards pass on this exact board.

## Reproduction and artifacts

```sh
PYTHONPATH=python-deps python ordinary-routing/i2c43-reference-review/review_exact43.py > ordinary-routing/i2c43-reference-review/review.log
```

The script binds the boards, snapshots, unchanged checkers, constructor and requirements; writes exact 41→43 and 42→43 comparisons; recomputes local geometry and strict topology; runs positive/negative controls; and produces the narrow acceptance receipt. `verification.json` checks every bound input and output hash. No board write/refill, router, JVM, FEM, canonical edit or Git mutation is performed by this review.
