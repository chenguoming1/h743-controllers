# One minimum-offset C29 placement option: rejected as a sufficient remedy

## Decision

A 0.211 mm westward C29 move opens exactly the requested C29/J5.6 pad gap, but violates clearance to a retained GND via and puts C29's GND pad across existing VX_SENSE copper. It also leaves the illustrated USB pair crossing C29's GND return. **Do not request or grant this move as a sufficient USB-launch remedy.** This is a read-only decision proposal; component movement is not authorized and was not applied.

The clear stopping test is the fixed C29.1-to-GND-via clearance: **0.053142 mm available, 0.127000 mm required**, a 0.073858 mm deficit. No trace reroute alone removes this pad-to-fixed-via violation.

## Source and exact placement

Baseline PCB: `/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/routing-continuation/r55-vsys-thermal/hardware/nexus-style-fc.kicad_pcb`

SHA256 `26c63920e944baaada474e49c8e7c08ab0260176047f6b452d4232746c91fe7b`.

| Item | Original | Proposed |
|---|---|---|
| C29 footprint center | (111.390,121.550) | (111.179,121.550) |
| Translation | | (−0.211,0.000) mm, west |
| Rotation | 90° | 90°, unchanged |
| Part/value | 0402, 100 nF ADC filter | unchanged |
| C29.1, VX_SENSE | (111.390,122.030) | (111.179,122.030) |
| C29.2, GND | (111.390,121.070) | (111.179,121.070) |
| Courtyard x interval | 110.930–111.850 | 110.719–111.639 |
| Courtyard y interval | 120.640–122.460 | unchanged |

Each pad retains its 0.56 × 0.62 mm local size, 90° pad orientation and actual 0.140 mm rounded-corner radius. The new C29.1 copper bounds are x110.869–111.489, y121.750–122.310. C29.2 bounds are x110.869–111.489, y120.790–121.350.

J5.6 is unchanged, with its west copper edge at x112.180. The new horizontal copper gap is exactly 0.691 mm = 0.155 + 0.127 + 0.155 + 2×0.127 mm. Thus −0.211 mm is the theoretical minimum west offset for this particular straight slot, with **zero nominal clearance margin**. It is not asserted to be the minimum displacement across all cardinal directions or a production placement recommendation.

## Courtyards, power and fixed-copper checks

The exact stored same-side courtyard contours do not overlap. Nearest contour gaps after the move are J4 0.349 mm, R16 0.370 mm and J5 0.391 mm. These are placement-courtyard distances, not copper-routing keepout requirements. No courtyard waiver or altered 3D body is assumed.

Static screening covered 153 fixed front/through pads, 498 F.Cu tracks, 230 through-vias, eight stored front GND-fill polygons and 43 front-side courtyard footprints. No new pad conflict with 3V3/5V/VX power copper was found. The unchanged C29.2-to-R16.1 copper gap remains 0.670 mm, and the nearby 0.500 mm VX feed gap remains 0.690 mm. Neither dimension establishes a complete USB launch.

The actual new electrical obstructions are:

1. **Fixed upper GND via** `143f6a86-dfad-4a4b-8c52-59e7a5c3ed89`, center (110.590858,121.956), diameter 0.450 mm. Its east edge is x110.815858; moved C29.1's west edge is x110.869. Exact gap: 0.053142 mm. The via lies alongside the pad's straight edge, so corner rounding does not help. Preserving 0.127 mm allows at most 0.137142 mm west movement, leaving only a 0.617142 mm C29/J5 gap, 0.073858 mm short of the pair corridor.
2. **Actual cross-net overlap:** moved C29.2 GND crosses fixed VX_SENSE segment `a4eae8e6-eaf8-44a3-ba6e-de8237538fcb`, (110.890716,120.723858) → (110.877719,121.544858), width 0.127 mm. The exact rounded-core screen reports a signed overlap indicator of −0.081968 mm; its negative magnitude is not a polygon penetration metric. The source pad/track gap was +0.129006 mm.
3. C29.2 also leaves only 0.034167 mm to VX_SENSE segment `2ca6e6af-31cf-4d8e-96c4-1c43f2fa72b3`.
4. The proposed VX_SENSE pad overlaps baseline saved F.Cu GND fill. A hypothetical move would require refill; this saved-fill observation is not proof of what a fresh fill would do and is not used as the decisive fixed obstruction.

## Complete existing ADC and ground ports

The source sense net joins R16.2, R17.1, C29.1 and MCU U1.9. R16 remains 52.3 kΩ, R17 10 kΩ and C29 100 nF. The VX terminal feed supplies that divider, approximately 0.118780 mA at an illustrative 7.4 V. The prior inner-layer feed area tradeoff remains a low-current ADC dependency, not a high-current power-equivalence requirement.

To terminate on the moved pad centers while retaining every other route object, the two incident 0.127 mm F.Cu segments would become:

- VX_SENSE `0a13d11c-c17a-4c7f-add1-b8eb553c3895`: fixed port (110.877719,121.544858) → new C29.1 (111.179,122.030). Length 0.705546 → 0.571081 mm.
- GND `2364fc18-712a-4a3d-bd33-5ddd77aba84b`: new C29.2 (111.179,121.070) → fixed port (112.680,122.360), then the unchanged connection to J5.6. Length 1.824335 → 1.979167 mm.

The explicit same-net copper graph retains all 23 VX_SENSE objects and all four ADC ports. It also retains all 37 objects and all nine pad ports of C29's original explicit GND component: J6.A12, J6.EP shield, J5.6, D3.1, C29.2, J4.1, J4.5, R21.2 and C25.2. Other source ground components and every connector stay untouched. This proves only same-net finite contacts under the static model; it does **not** excuse the added cross-net short, prove post-refill return integrity, or qualify analog noise/ESD performance.

## Exact illustrative pair primitives and unfinished launch

The narrow slot's centerline would be x111.834500. Two explicit 0.155 mm F.Cu rails, each 2.300 mm long, illustrate the local passage:

- USB_DP: (111.693500,120.700) → (111.693500,123.000)
- USB_DM: (111.975500,120.700) → (111.975500,123.000)

They have a 0.127 mm edge gap and 0.437 mm total copper envelope. At C29.1 and J5.6 the side clearances are exactly 0.127 mm. These are local reservation ports; they are not connected to the connector/U7/MCU or approved as net assignments for a final launch.

Both rails cross the re-terminated C29.2 GND segment `2364fc18…`. The DP rail also has only 0.113528 mm at its north end to existing VX_SENSE segments `3c128473…` and `994272a8…`. Consequently a single C29 move plus its two endpoint reconnections does not close even this local pair, let alone the full south launch. Removing the ground return or an ADC branch would violate the required topology.

## Outcome and scope boundary

Reject this minimum-west option as a sufficient remedy. A useful future placement decision would need a different complete component/ground-via/ADC-routing transaction or another USB corridor, established before asking approval. This pass intentionally does not broaden into those alternatives.

No source PCB, schematic, part assignment or frozen donor/refinement report was changed. No native KiCad, refill, DRC, heavy solver, fabrication or signal-integrity acceptance was run. Later source revisions require an applicability check.

Machine-readable evidence: `c29-option.json`, `placement-screen.json`.
Reproducible read-only calculations: `build_c29_option.py`, `placement_screen.py`.
Hashes: `manifest.json`, `SHA256SUMS.txt`.
