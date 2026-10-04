# U2 TPS62162DSGR: P3 SMT land/model disposition

**Disposition: native land and stencil geometry are supported quantitatively by TI's exact package example; no native geometry change is justified by these reports. New evidence strongly suggests the JLC 0.44 is one exposed-pad paste window measured against the whole exposed pad. Its internal object-to-layer mapping remains unverified, so supplier approval is still open.**

Audited 2026-10-03, read only. P3 native SHA256: `0850991d8aacd22138487804c24eefbae634a21ba218c18196f13fad795c3696`. No native or release file was edited.

## Sources and evidence scope

- [TI TPS62162 datasheet](https://www.ti.com/lit/ds/symlink/tps62162.pdf), SLVSAM2E; physical PDF pages 4 and 39–41; DSG0008A drawing **4218900/E, 08/2022**. The [downloaded PDF](tps62162-current-ti.pdf) is SHA256 `abc824ca04ee985ede3a513172ccdd2a42c8e1fdcfc3af5acdbe2c1af31aaa72`, byte-identical to the earlier local `ti-tps62160.pdf` used in the stencil work. [TI's exact orderable part](https://www.ti.com/product/TPS62162/part-details/TPS62162DSGR) identifies DSG/WSON-8.
- Native U2 and release F.Cu/F.Paste were measured directly. [Reproducible geometry audit](geometry-audit.json), [per-pin metrics](per-pin-metrics.csv), [dimensioned overlay](u2-copper-ti-terminal-overlay.png), and [read-only script](audit_u2_geometry.py) accompany this report.
- [P3 supplier project](https://jlcdfm.com/viewer?pcbUploadFileId=629271171624820737) has the same displayed SMT category counts as [corrected-CPL P2](https://jlcdfm.com/viewer?pcbUploadFileId=629258777493983233). Detailed U2 captures available here are explicitly **P2 detail captures**, preserved as `corrected-cpl-smt-{pin-inner,pin-left,pin-right,lead-pad-overlap}.txt`; P3 category equality and unchanged U2 geometry/pose support carrying the issue forward, but do not establish P3's hidden selected pin or model polygon.

## Measured lands and manufacturer comparison

TI body limits are 1.90–2.10 mm square. Terminals are 0.20–0.40 mm longitudinally and 0.18–0.32 mm across, on 0.50 mm pitch. A rectangular terminal and an alternative rounded inner termination are shown. Here “nominal terminal” means the midpoint construction 0.30 × 0.25 mm, not a separately specified typical dimension.

| Feature | Actual P3 | TI example |
|---|---:|---:|
| Lead copper, length × width | 0.60 × 0.25 | 0.50 × 0.25 |
| Lead copper corner radius | 0.0625 | 0.05 |
| Two lead-row x centers | ±0.95 | ±0.95 |
| Four pin y offsets | −0.75, −0.25, +0.25, +0.75 | same |
| Thermal copper | 0.90 × 1.60, R0.05 | same |
| Eight lead paste openings | 0.50 × 0.25, R0.05 | same |
| Two thermal paste openings | 0.90 × 0.70, R0.05, y = ±0.45 | same |

All dimensions are mm. **Every point of the TI example lead land is inside P3 copper.** Increasing the corner radius does not create a missing corner: native copper extends 0.0375–0.0500 mm farther at each longitudinal edge at every transverse slice; the top/bottom edges coincide. The full native land area is 0.1466468463 mm² versus TI's 0.1228539816 mm². This is a geometric containment proof, not a generic IPC-alternative argument.

The existing stage-20 audit checks paste containment and drill avoidance; it does **not** compare package terminals or validate the supplier model. It has been rerun on the current P3 SHA in [current-stencil-audit.json](current-stencil-audit.json): 9 copper pads, 10 separate paste openings, no automatic paste on numbered pads, no paste outside copper, no drilled holes intersecting apertures, and **87.332%** actual rounded-shape thermal paste coverage. TI's example uses a **0.125 mm stencil**. The release manufacturing profile does not establish the ordered stencil thickness or process qualification, so that remains an assembly-process confirmation.

## Per-pin pose and margins

Native origin is (5.05, 10.80); the manufacturing transform is X = native X, Y = 38 − native Y. Native CPL, corrected CPL and released CPL all give **U2 (5.05, 27.20), Top, 0°**. The user made no U2 pose override.

Pin 1 is native upper left. Pins 1–4 run down the left side; 5–8 run up the right. This agrees with TI's **top view**. The package-outline bottom view must not be copied without mirroring. Native pad functions/nets agree with the datasheet: PGND/AGND/FB/EP connect to GND, VIN/EN to VLOGIC_IN, VOS to 3V3_CORE, SW to BUCK_SW, PG is intentionally unconnected. Native 0° alone does not establish JLC's model-zero orientation.

The following margins are longitudinal toe/heel at the terminal centerline and signed transverse margins; positive means land extends beyond the terminal. Overlap uses true rounded copper area divided by rectangular terminal area. All eight pins have the same geometry.

| Pin | Function | Native x,y | Nominal toe / heel / side each | Nominal overlap | Max terminal, min body overlap |
|---|---|---|---|---:|---:|
| 1 | PGND | 4.10, 10.05 | +0.25 / +0.05 / 0 | 0.999860266 | 0.572839243 |
| 2 | VIN | 4.10, 10.55 | +0.25 / +0.05 / 0 | 0.999860266 | 0.572839243 |
| 3 | EN | 4.10, 11.05 | +0.25 / +0.05 / 0 | 0.999860266 | 0.572839243 |
| 4 | AGND | 4.10, 11.55 | +0.25 / +0.05 / 0 | 0.999860266 | 0.572839243 |
| 5 | FB | 6.00, 11.55 | +0.25 / +0.05 / 0 | 0.999860266 | 0.572839243 |
| 6 | VOS | 6.00, 11.05 | +0.25 / +0.05 / 0 | 0.999860266 | 0.572839243 |
| 7 | SW | 6.00, 10.55 | +0.25 / +0.05 / 0 | 0.999860266 | 0.572839243 |
| 8 | PG | 6.00, 10.05 | +0.25 / +0.05 / 0 | 0.999860266 | 0.572839243 |

Nominal intersection per pin is 0.0749895199 mm² / 0.075 mm². The very small deficit is the intersection of square terminal corners with rounded copper. With TI's alternate rounded inner terminal, both P3 and TI nominal patterns give 100% coverage.

## Same terminal cases on native and TI lands

| Centered rectangular terminal case | P3 toe / heel / side each | P3 overlap/lead area | TI toe / heel / side each | TI overlap/lead area |
|---|---|---:|---|---:|
| 2.00 body; 0.30 × 0.25 terminal | +0.25 / +0.05 / 0 | 99.9860% | +0.20 / 0 / 0 | 98.5693% |
| 2.00 body; 0.40 × 0.32 terminal | +0.25 / −0.05 / −0.035 | 67.0495% | +0.20 / −0.10 / −0.035 | 57.7555% |
| 1.90 body; 0.40 × 0.32 terminal | +0.30 / −0.10 / −0.035 | 57.2839% | +0.25 / −0.15 / −0.035 | 47.9898% |
| 2.10 body; 0.40 × 0.32 terminal | +0.20 / 0 / −0.035 | 76.8152% | +0.15 / −0.05 / −0.035 | 67.5211% |
| 2.00 body; 0.20 × 0.18 terminal | +0.25 / +0.15 / +0.035 | 100% | +0.20 / +0.10 / +0.035 | 100% |

Over the centered dimensional envelope, native centerline toe is +0.20…+0.30, heel −0.10…+0.20, and each side −0.035…+0.035 mm. The JSON includes 54 combinations covering all endpoint/midpoint dimensions and both terminal shapes. These are **dimension-only comparisons**: they do not include the drawing's composite positional control, PCB etch variation, package placement error or rotation error. Do not promote 57.2839% to a guaranteed assembled minimum.

## What the red rows establish

1. **Eight inner-edge, four left-edge and four right-edge U2 reports show 0 mm.** The UI describes pin edges exceeding pad edges and allows special-design exceptions, but provides no numeric edge threshold in the capture. Native nominal heel is +0.05 mm, whereas TI's exact example heel is zero; both have zero nominal side extension. Maximum-dimension terminals overhang the inner/side land boundaries in both patterns. A generic no-overhang rule can therefore flag the manufacturer's own example. The displayed 0 mm does not establish the signed physical overhang or its pin mapping; it could be a displayed or clamped result, but that behavior is unverified.
2. **The single overlap red is 0.44 on `i274x.RoundRect.d11`.** Aperture numbers are **file-local**: front copper ADD11 is the 0.60 × 0.25 R0.0625 signal land, while front paste ADD11 is a 0.90 × 0.70 R0.05 thermal paste window. The earlier inference that this object must be a copper signal lead was not justified. JLC's captured help explicitly divides intersection by **lead area**, with boundaries 0.75 and 0.90. The signal-terminal computations would call multiple TI example cases above red, but do not reproduce 0.44. The split thermal-paste calculation below does reproduce the displayed ratio. It is the stronger current explanation, pending actual source-layer mapping.
3. **Reducing copper to the exact TI example would reduce or preserve every lead intersection.** It cannot remedy these overlap/heel/side reports. Enlarging or relocating copper merely to force green would be speculative without the actual model and process criteria. The present lands also retain 0.20 mm centerline clearance to the 0.90 mm EP and 0.25 mm between adjacent lead lands.

## Added evidence: exact 0.44 split-stencil signature

The actual P3 [front-paste Gerber](../../../controller-r3s-green/release/single-board-gerbers/controller-F_Paste.gtp) declares `FileFunction,Paste,Top`. Its line 33 defines ADD11 as a rounded rectangle with radius 0.05 and corner-center spans 0.80 × 0.60, giving outer dimensions **0.90 × 0.70 mm**. Line 60 assigns `%TO.C,U2*%`; no attribute reset intervenes before the ADD11 flashes on lines 66–67. Those flashes are at manufacturing **(5.05,27.65)** and **(5.05,26.75)**, exactly the two native EP stencil windows at y offsets ±0.45. [Full excerpts, line numbers, areas and hashes](split-stencil-evidence.json) and a [diagram](u2-split-stencil-recognition.png) are included.

Using rounded-rectangle area A = width × height − (4 − π) × radius²:

| Calculation | Result |
|---|---:|
| One paste-window area: 0.90 × 0.70 − (4 − π) × 0.05² | 0.627853981634 mm² |
| Full P3 EP copper area: 0.90 × 1.60 − (4 − π) × 0.05² | 1.437853981634 mm² |
| One window / full rounded EP | **0.436660460418 → 0.44** |
| Both windows / full rounded EP | **0.873320920836 = 87.3321%** |
| One window / full rectangular 0.90 × 1.60 EP | **0.436009709468 → 0.44** |
| Both windows / full rectangular EP | 0.872019418936 = 87.2019% |

This reproduces the displayed JLC value with either of two plausible nominal EP denominators while the combined windows reproduce TI's intended approximately 87% stencil coverage. It suggests that the analyzer may evaluate a single paste window against a full exposed-pad lead, rather than unioning the intentionally split windows. It would also explain why there is one reported 0.44 object rather than eight symmetric signal-pin overlap reports.

**Limits:** these denominators are explicit nominal hypotheses, including the measured PCB copper shape; they are not measurements of the JLC package lead. TI's package outline also contains a pin-1 EP chamfer and dimensional tolerances. The JLC EP shape, selected lead and `i274x` layer identity remain unknown. Aperture-name reuse and a rounded numerical match support the hypothesis but do not prove the engine's mapping or deduplication behavior. The inner/side-edge reports still require separate manufacturer-pattern disposition; this EP explanation does not automatically explain those rows.

## Evidence required to close U2

Obtain the following for P3 project 629271171624820737, matched part TPS62162DSGR/C40256:

- A selected 0.44 row showing its **source file/layer, pin number and target pad coordinate**; first test whether `i274x` points to F.Paste and whether the selected pin is the exposed pad. The shared aperture label is insufficient
- The model's lead polygon/dimensions, row spacing, body dimensions, pin-1 marker and model reference origin, plus the applied translation/rotation; or a calibrated, unobscured 2D overlay with enough dimensions to recover those quantities
- If it is the EP paste window, confirm that the supplier accepts both windows as one intended stencil pattern and the combined approximately 87% coverage. If it is a signal copper land, recompute its intersection using the actual selected model lead. Document any positional/placement tolerance and clipping/rounding convention
- A pin-1 comparison against native pin 1 at manufacturing (4.10, 27.95), and confirmation of supplier model-zero orientation at CPL 0°
- Supplier disposition of the DSG0008A manufacturer-example exception and actual stencil/process choice. If the model is correct and the supplier rejects this land/process, obtain its dimensional requirement before changing copper

**Close the native land/stencil investigation as manufacturer-supported, with an explicit supplier-model/process hold. Keep the U2 SMT row open until that evidence arrives.** No undocumented rotation, land resize, threshold relaxation or silent waiver is warranted.

## Exact provenance

The input SHA256 values, native and exported per-pin coordinates, aperture assignments and full computations are in [geometry-audit.json](geometry-audit.json). [SHA256SUMS.json](SHA256SUMS.json) binds every file in this audit bundle; it excludes itself.

- Native P3: `0850991d8aacd22138487804c24eefbae634a21ba218c18196f13fad795c3696`
- Corrected/released CPL: `ed23023d67402462e10042c7a7e8467062def891a487c25afa7da5a2af2c00a2`
- Native-audit CPL: `2af8d2593d96204987af71be3eab6e706ae00062e5cbddac4527c2818a179a8a`
- TI PDF: `abc824ca04ee985ede3a513172ccdd2a42c8e1fdcfc3af5acdbe2c1af31aaa72`
- Historical stage-20 board: `eb5d45c35b9e6971e4154cebe562ab7b3f81429d71bf8fbee91dfc7ebaac05a1`; this is historical, not the audited P3 source
