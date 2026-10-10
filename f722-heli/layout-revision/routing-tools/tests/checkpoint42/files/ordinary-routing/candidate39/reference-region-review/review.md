# Candidate39: fresh exact-source critical reference-region receipt

Strict unchanged-own-window containment is verified for all changed critical missing-reference geometry on complete candidate39. Across all 72 critical/I2C reference tracks, the same three records change, and every changed piece is covered by its unchanged same-net own-via window with an empty outside-window difference. Exact missing-centerline equality remains false. Strict actual-hole-mask containment remains unresolved because four `covers` and empty-difference checks disagree; these disagreements remain cause-classification limitations rather than a stronger pass.

This fresh receipt is specific to candidate39. It does not reuse the partial-stage receipt, approve the enlarged merged hole, or establish overall board adoption or functional signoff.

## Exact sources

- Before: `ordinary-routing/candidate38/f722-heli.kicad_pcb`, SHA256 `95bb984bf046fef2d96c6e59d9e00696f504d35f89e3340fdf076cd7c9249c9f`
- Before snapshot: `checkpoint44-review/snapshot`
- After: `ordinary-routing/candidate39/f722-heli.kicad_pcb`, SHA256 `246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7`
- After snapshot: `ordinary-routing/candidate39/reference-snapshot`
- Supplied comparison: `ordinary-routing/candidate39/reference-comparison-to38.json`

The classifier verifies source bindings, recomputes the provided comparison exactly, checks all critical source objects for equality, reconstructs actual saved physical GND with native drill subtraction, and verifies unchanged own-via window definitions. It evaluates both source-track projection onto changed physical GND and direct subtraction of the separately clipped missing geometries. The exact predicates, coordinates, lengths, areas, native hole geometry, drill intersections, source hashes, and rejection controls are retained in `reference-classification.json`.

All five original partial-stage review artifacts are included in the source-preservation hash check and remain unchanged. Neither the older helper nor a public repository file was edited.

## Changed centerline and width geometry

All three changed records reference In1.Cu. No other critical reference projection changes.

### IMU_MOSI centerline

Track `6447ecc7-f06e-400b-9d6f-5f4db0815aa1`, F.Cu, source track `(22.709999, 10.6875)` to `(21.509999, 9.8)`, width 0.127 mm.

The physical-plane calculation adds this missing segment:

```
(21.795235630441734, 10.010956257930866)
to (21.795235244635585, 10.010955972595067)
length 4.798571699784025e-7 mm
```

There is no removed physical missing-centerline segment. The report's scalar subtraction remains `+4.798571699993204e-7` mm.

Direct subtraction of the independently clipped missing lines instead returns the full after interval, length `0.35477102207754796` mm, as added, and the full before interval, length `0.35477054222037796` mm, as removed. The after interval begins at the first coordinate above; the before interval begins at the second. Both end at `(21.509999, 9.8)`. Their exact 2D intersection is only that common via-center point. Both full intervals remain strictly inside the unchanged own-via window; no line equality is asserted or manufactured.

### IMU_MOSI width

Same track. Added physical missing-width area: `1.8575200425979192e-8` mm². Removed geometry is empty.

```
(21.827190083077813, 9.955609266984256)
(21.792069, 10.01644)
(21.794909, 10.011522)
(21.827190125129786, 9.9556092980852)
(21.827190083077813, 9.955609266984256)
```

Direct missing-polygon subtraction gives area `1.8575200423355488e-8` mm². The track-total scalar subtraction is `+1.8575200398662783e-8` mm²; the supplied net-total scalar subtraction is `+1.8575200405601677e-8` mm². All alternative values remain explicit.

### IMU_MISO width

Track `914fe3b1-3b8b-40ce-9188-3b1c713ceb65`, F.Cu. Removed physical missing-width area: `6.174417533380787e-9` mm². Added geometry is empty; centerline geometry is unchanged.

```
(21.425280532708168, 10.730833729261997)
(21.38606, 10.753478)
(21.398306, 10.746408)
(21.4179, 10.735095)
(21.42528054872994, 10.730833774656846)
(21.425280532708168, 10.730833729261997)
```

Direct subtraction gives removed area `6.174417533367214e-9` mm². The supplied scalar subtraction remains `-6.17441728301138e-9` mm².

## Original windows and the fresh merged-hole evidence

- MOSI own via `743f60f6-99d7-40af-8adc-c8e9b0542c93`: center `(21.509999, 9.8)`, radius `0.362` mm
- MISO own via `7e8612c2-cc4c-4346-a00f-69e4734445fb`: center `(21.25, 10.425)`, radius `0.362` mm

These source via objects and window parameters are unchanged. Their pre-existing classification allowance is retained; no new tolerance or allowance was added.

Before-hole index 29 has area `0.7867610831950005` mm² and bounds `(20.8975, 9.4475, 21.862499, 10.7775)`. It contains the MOSI and MISO vias.

Candidate39 after-hole index 17 has area `1.5612640944305003` mm² and bounds `(20.8975, 9.0975, 23.1525, 10.7775)`. Its four contained vias are:

- `743f60f6-99d7-40af-8adc-c8e9b0542c93`, IMU_MOSI, `(21.509999, 9.8)`
- `7e8612c2-cc4c-4346-a00f-69e4734445fb`, IMU_MISO, `(21.25, 10.425)`
- `c045eadd-fdcc-46bf-92bd-ab580996c71b`, SERVO3_MCU, `(22.0, 9.45)`
- `eec68274-8fe5-464d-ad04-2d6f497f6461`, IMU_SCK, `(22.8, 9.5)`

This enlarged hole differs from the two-via partial-stage hole and was recomputed from candidate39. Hole extensions outside the original own-via windows receive no exemption. No actual drill intersects any of the three physical changed pieces.

The MOSI added width polygon is covered by the actual after-hole polygon. The MISO removed width polygon is covered by the before-hole polygon. For MOSI's added centerline, the after-hole subtraction is empty but its `covers` predicate is false. The before/after hole-intersected mask union also has empty subtraction residuals but false `covers` results for MOSI's added centerline and width, in both recorded computations. All four disagreements and their `relate` strings remain in the receipt. Thus strict actual-hole-mask containment is unresolved; strict containment inside the unchanged own-via windows is independently verified.

No snapping, rounding, endpoint projection, contour repair, numeric threshold, or value normalization is applied. Small discrepancies between polygon-overlay measures and subtraction of report totals remain nonzero.

## Whole-plane changes and assessment scope

Each physical reference plane, In1.Cu and In4.Cu, loses `1.632326549368308` mm² GND and gains `0.08155315009880729` mm².

Outside all unchanged critical own-via windows, each plane loses `1.6263956660071535` mm² and gains `0.08155308693141657` mm². These are positive whole-plane changes; the narrow critical-projection classification does not waive separate source-bound power/VCAP and functional assessment. Enlarged holes are not characterized as harmless by this receipt.

The older checkpoint49 review demands exact centerline equality, which is false here. It cannot be reused as-is. This new receipt establishes the stated own-window location result while retaining the actual-hole boundary limitation. It does not establish impedance, return-current performance, timing, fabrication, or flight qualification.

## Reproduction and controls

From the rebuild root, run:

```
bash ordinary-routing/candidate39/reference-region-review/reproduce.sh
```

The invocation pins both expected board hashes and the explicit source paths. The local classifier also accepts these paths and hashes as arguments for a later fresh F722 comparison; its geometric containment predicates and seven rejection controls remain unchanged.

All seven controls reject the intended invalid cases: mismatched source hash, cross-bound snapshot, enlarged own window, centerline outside its own window but inside a merged hole, width in that merged-hole extension, window area without an actual hole, and overriding a false `covers` result solely because the difference is empty. Twenty source/artifact hashes are checked before and after computation. `receipt.json` seals the final review files and the checked source bindings.

Any later board change requires another source-bound review. No native KiCad run, board rewrite, owner-evidence edit, JVM run, FEM run, or public repository mutation was performed for this classification.
