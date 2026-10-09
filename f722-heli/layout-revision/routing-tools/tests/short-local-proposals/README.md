# Candidate15 short local routing audit

One useful local closure is ready for native construction and DRC: ADC_BUS R42.2 to R43.1 on F.Cu. Both terminals belong to the model's same ordinary logical role. The selected 0.127 mm path is:

`(21.01,17.5) → (21.89,17.5) → (21.99,17.6)`

It has two octilinear segments, length 1.021421356 mm, and minimum native foreign-copper clearance 0.498956078 mm, which exceeds the 0.127 mm rule by 0.371956078 mm. Both endpoint round caps are wholly inside the actual native pad interiors. No via is needed. A direct center-to-center alternative is also valid, with length 0.985088828 mm. This joins only the two resistor pads; C31.1 and U1.10 still need routing.

The parent verified that the prior broad ADC_BUS run attempted C31.1 and U1.10 before the run stopped after five overall successes. Neither R42.2 nor R43.1 was attempted. This is an unattempted local opportunity, not evidence of disagreement between engine reachability and native geometry.

## Source and deliverables

- Frozen board: `../../candidate15/f722-heli.kicad_pcb`
- Board SHA-256: `23232e7bc1903c06c1809d569c91e4cb161281be9225f3776076386593e55674`
- Native SHA-256: `dc1aa86cd3969eb2f0444674adef7f948b46cb50ad07d4d56d1efa3ba083febd`
- Construction input: `candidate15-short-local-proposals.json`, list `proposals`
- Audit and full selected-route segment witnesses: `candidate15-short-local-exact-witnesses.json`
- Generator: `prepare_short_local_proposals.py`; helper: `native_geometry.py`

The proposal binds the board, native export, logical model, scripts, and exact-witness receipt by SHA-256. Source hashes were checked again after generation. All actual native foreign copper, fixed support, keepouts, edge and NPTH constraints remain. The nominal rules are 0.127 mm trace width, 0.127 mm foreign copper clearance, and 0.254 mm edge/NPTH copper clearance. No additional arbitrary clearance rule was imposed. The result has ample positive margin relative to the native export's 0.00001 mm polygon error.

## BARO findings

The physically nearest BARO pairs are on opposite faces:

- BARO_SCL U4.4 on F.Cu to R7.2 on B.Cu: center distance 0.777721030 mm
- BARO_SDA U4.3 on F.Cu to R8.2 on B.Cu: center distance 1.613335055 mm

These pairs cannot be connected by a same-layer track; at least one plated transition is necessary. No via location is proposed by this audit.

For each BARO B.Cu pair, 325 bounded paths were examined using pad centers and full-width interior tips, direct segments, orthogonal/45-degree one-bend routes, and a few three-segment orthogonal doglegs. None passed even the local obstacle screen. This is a bounded negative result, not a proof that every same-layer route is impossible.

BARO_SCL's best tested dogleg from U1.61 to R7.2 has only 0.054 mm physical clearance to fixed GND via `c4b3b59e-6ae1-430e-a66c-dc5fa02e7fe9`, a 0.073 mm deficit. The receipt gives the exact closest point pair `(22.302104,20.3825)` and `(22.302104,20.5)`. It also passes too close to U1.53, UUID `0a79a4f4-260e-42e2-a7a8-13b21a0be2b9`.

All tested BARO_SDA paths intersect native foreign copper. One short representative crosses +3V3_CORE track `2f11d7ab-d65f-49a0-8782-5e7d29abe4e9` at `(21.1244647673,21.8627566866)`, giving zero centerline-to-obstacle distance; another intersecting support track is `30cbc353-b645-4ef8-92a6-9d6ddf01dcba`.

The longer B.Cu ADC_BUS C31.1-to-U1.10 pair likewise had no passing bounded candidate. A short representative intersects HSE_IN track `12ca6022-6988-4c51-b3b6-a28eb5df707c` and HSE_OUT track `23739b12-5b2e-48be-91af-6db26f414b70`. Exact distance witnesses are recorded.

No JVM, board write, model write, full routing search, native DRC, or routing acceptance occurred. Native construction/refill/DRC remains the next gate for the selected ADC_BUS closure.
