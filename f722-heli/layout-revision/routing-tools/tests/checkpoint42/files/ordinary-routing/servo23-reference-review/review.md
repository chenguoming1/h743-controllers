# Partial servo23 stage: exact reference-region classification

All changed critical missing-reference geometry is inside the unchanged same-net own-via windows. Both `covers` and empty-difference checks establish that narrow window result; no positive changed critical centerline or trace-width geometry was found outside those windows. Strict actual-hole boundary containment remains unresolved because the saved-hole-mask `covers` and difference predicates disagree for MOSI. No value has been rounded away or treated as zero.

This is isolated partial-stage evidence, not adoption or functional signoff. The older helper and checkpoint49 receipt require exact centerline equality and cannot be reused as-is. A completed successor must repeat this source-bound comparison.

## Sources and method

- Before board: `ordinary-routing/candidate38/f722-heli.kicad_pcb`, SHA256 `95bb984bf046fef2d96c6e59d9e00696f504d35f89e3340fdf076cd7c9249c9f`
- Before snapshot: `checkpoint44-review/snapshot`
- After board: `ordinary-routing/servo23-native-stage38/f722-heli.kicad_pcb`, SHA256 `e93f1a1814f8b2bfd6341be9522a053a71db2706d7d81ee2984f6bd82a6c8aa5`
- After snapshot: `ordinary-routing/servo23-native-stage38/reference-snapshot`
- Supplied comparison: `ordinary-routing/servo23-native-stage38/reference-comparison-to38.json`

The classifier verifies all board/snapshot/report/comparison bindings, re-runs the comparison, and confirms the complete critical native objects are equal. It examines all 72 critical/I2C reference tracks. Physical GND is reconstructed from actual saved polygons minus native outside-drill contours on their real layer spans. It uses the pre-existing own-via windows, including their original 0.01 mm classification allowance, unchanged; it adds no allowance.

Two computations are recorded independently:

1. Original track centerline/copper intersected with physical GND lost or gained. This isolates the missing-reference change due to the saved physical planes.
2. Direct subtraction of the before/after clipped missing geometries. This preserves floating-point representation effects instead of silently forcing the independently clipped lines to coincide.

The machine-readable `reference-classification.json` retains every changed piece, actual saved-hole coordinates, hole and window relationships, source hashes, alternative numerical results, drill intersections, and predicate results. No board, source helper, public repository file, KiCad state, or FEM model was modified.

## Added/removed critical geometry

All three changed records reference `In1.Cu`; no other critical reference projection changed.

### IMU_MOSI centerline

Track `6447ecc7-f06e-400b-9d6f-5f4db0815aa1`, F.Cu, source track `(22.709999, 10.6875)` to `(21.509999, 9.8)`, width 0.127 mm.

The physical-plane computation adds one missing segment:

- Start: `(21.795235630441734, 10.010956257930866)`
- End: `(21.795235244635585, 10.010955972595067)`
- Length: `4.798571699784025e-7` mm
- Removed physical missing-centerline geometry: empty

The report's total-length subtraction remains `+4.798571699993204e-7` mm. These are different floating-point computations, and their different nonzero values are retained.

Direct subtraction of the separately clipped missing lines returns the complete after interval, length `0.35477102207754796` mm, as added and the complete before interval, length `0.35477054222037796` mm, as removed. Their intersection is only the common via-center point in the exact 2D representation. The added interval runs from the new start above to `(21.509999, 9.8)`; the removed interval runs from the old end above to that same point. Both entire intervals remain strictly covered by the original own-via window. They are not represented as equal.

### IMU_MOSI trace width

Same track. Added physical missing-width polygon area: `1.8575200425979192e-8` mm². No removed polygon.

Polygon vertices, including closure:

```
(21.827190083077813, 9.955609266984256)
(21.792069, 10.01644)
(21.794909, 10.011522)
(21.827190125129786, 9.9556092980852)
(21.827190083077813, 9.955609266984256)
```

The direct missing-polygon subtraction has area `1.8575200423355488e-8` mm². The track-total subtraction is `+1.8575200398662783e-8` mm²; the supplied net-total subtraction is `+1.8575200405601677e-8` mm². All are retained separately.

### IMU_MISO trace width

Track `914fe3b1-3b8b-40ce-9188-3b1c713ceb65`, F.Cu. Removed physical missing-width polygon area: `6.174417533380787e-9` mm². No added polygon and no centerline change.

Polygon vertices, including closure:

```
(21.425280532708168, 10.730833729261997)
(21.38606, 10.753478)
(21.398306, 10.746408)
(21.4179, 10.735095)
(21.42528054872994, 10.730833774656846)
(21.425280532708168, 10.730833729261997)
```

Direct subtraction gives removed area `6.174417533367214e-9` mm². The supplied net-total subtraction remains `-6.17441728301138e-9` mm².

## Windows, actual holes, and the retained boundary limitation

- MOSI own via: `743f60f6-99d7-40af-8adc-c8e9b0542c93`, center `(21.509999, 9.8)`, unchanged radius `0.362` mm
- MISO own via: `7e8612c2-cc4c-4346-a00f-69e4734445fb`, center `(21.25, 10.425)`, unchanged radius `0.362` mm
- The corresponding merged saved-zone hole is index 29 before and index 28 after. Both contain these two vias. Bounds are unchanged: `(20.8975, 9.4475, 21.862499, 10.7775)` mm
- Hole area before: `0.7867610831950005` mm²; after: `0.7867610939510006` mm²
- The holes extend beyond both own-via windows, and those extensions receive no blanket exemption
- No actual drill intersects any of the three physical changed pieces. These physical changed pieces are on the saved-hole boundary, not a new drill opening

The added MOSI width polygon is covered by the actual after-hole polygon; the removed MISO width polygon is covered by the actual before-hole polygon. For the added MOSI centerline, the after-hole difference is empty but its exact `covers` predicate is false. The union of the before/after hole-intersected masks likewise has empty residual difference for MOSI's added centerline and width, but false `covers` predicates. The report preserves the `relate` strings and all differing predicate results. There are four such mask-predicate disagreements across the two recorded computations.

Therefore the reliable location conclusion is **inside unchanged own-via windows, with no computed outside-window residual**. Strict actual-hole-mask containment is **unresolved**, and this report does not reuse the stronger old assertion. There is no arbitrary epsilon, contour repair, endpoint adjustment, snapping, or normalization to zero.

## Whole-plane changes remain outside this narrow classification

Each of In1.Cu and In4.Cu loses `1.2504320071327655` mm² physical GND and gains `0.08155309495376467` mm².

Outside the union of all unchanged critical own-via windows, each plane still loses `1.2504319883544175` mm² and gains `0.08155308693141657` mm². Those are positive real plane changes. The absence of changed *critical projected missing geometry* outside own-via windows does not exempt whole-plane changes from separate source-bound power/VCAP and functional assessment.

## Reproduction and rejection checks

From the rebuild root:

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=python-deps python ordinary-routing/servo23-reference-review/classify_reference_delta.py
```

All seven rejection controls passed: mismatched expected board hash; cross-bound snapshot geometry; expanded own window; centerline in a merged-hole extension outside its own window; width in that extension; window area without an actual saved hole; and treating empty difference as sufficient despite a conflicting exact `covers` result. The script verifies unchanged source hashes again before emitting the report.

No impedance, timing, return-current, fabrication, or flight qualification is established. The final complete candidate requires a fresh exact-source review.
