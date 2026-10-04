# D4 P3 SMT footprint audit

Audited 2026-10-03. Read-only: no native PCB, library footprint, CPL, BOM, or release Gerber changes.

## Decision

**A genuine D4 SMT land-size or polarity defect has not been established. Retain the current native footprint pending exact supplier-model/process evidence; do not enlarge its pads solely to force the generic DFM rules green.** The native land bounding dimensions match ST's recommendation. Zero nominal heel and side extension are consequences of that recommendation, not independent evidence of a defect.

There is a real, measured difference in corner shape: the native copper/paste use R0.1375 rounded corners whereas ST draws rectangular lands. That reduces overlap, but does **not** explain 0.87 using nominal ST terminals: calculated nominal copper overlap is 0.9710. At maximum published terminal length/width and nominal pitch, even ST's unrounded rectangular recommendation gives only 0.8824, below the supplier's generic 0.90 green boundary. This shows why a yellow overlap result alone is not a valid reason to grow this manufacturer-based footprint.

Do not call the supplier's exact six red and two yellow D4 records conclusively false positives yet. Their pin polygons, geometric conventions, and assembly pose have not been obtained. A source-backed exception/process disposition is needed to close those records. Squaring the existing corners is a possible strictly manufacturer-shaped variant, but a required assembly correction is not established by the available evidence, and it would not necessarily eliminate the maximum-terminal overlap warning.

## Identity, release inputs, and primary evidence

- Exact released BOM: D4 = **STMicroelectronics ESDA7P120-1U1M**, JLC/LCSC **C2969802**, quantity 1; footprint `Storm32_Review:ST_QFN-2L_1.6x1.0mm_DS14419`
- Native board SHA-256: `0850991d8aacd22138487804c24eefbae634a21ba218c18196f13fad795c3696`, checked before and after analysis
- [Manufacturer datasheet, DS14419 Rev 4, March 2025](https://www.st.com/resource/en/datasheet/esda7p120-1u1m.pdf): downloaded directly during this audit; [local PDF](sources/st-esda7p120-1u1m-DS14419-Rev4.pdf), SHA-256 `ea57a4d81bb8cf98a3eb3d0f08a345d23e0b749bc6281d482509daad4111016a`
- [ST product page](https://www.st.com/en/protections-and-emi-filters/esda7p120-1u1m.html)
- [P3 supplier project](https://jlcdfm.com/viewer?pcbUploadFileId=629271171624820737)
- Reproducible extraction/calculations: [audit_d4.py](audit_d4.py), [geometry-audit.json](geometry-audit.json), [tolerance cases](tolerance-cases.csv), [overlay PNG](d4-overlap-overlay.png), [overlay SVG](d4-overlap-overlay.svg)

The JSON records hashes for the board, project, exact released BOM/CPL, native audit CPL, user-corrected input CPL, and copper/mask/paste Gerbers. It records the actual D4 rows and pad nets, positions, and margins.

## Manufacturer geometry

DS14419 p9, Fig 13/Table 11: body D=1.55/1.60/1.65 mm and E=0.95/1.00/1.05 mm; terminal length L=0.30/0.35/0.40 mm, width b=0.75/0.80/0.85 mm, center pitch e=1.05 mm typical. Terminal pitch tolerance and pin-1 chamfer size are not given.

Page 10, Fig 14 recommends two **0.55 × 0.80 mm rectangular lands**, **0.70 mm inner gap**, **1.80 mm overall span**. Derived land center pitch is 1.25 mm. Page 1 identifies pin 1 as cathode and pin 2 as anode; p10 says to use the physical pin-1 marking for placement orientation.

## Actual native and fabrication geometry

Native center: (35.600, 26.450) mm, top, 0°. Manufacturing origin: (0,38) mm; Gerber/CPL transform is X=native X, Y=38−native Y.

| Feature | Pad 1 / cathode | Pad 2 / anode |
|---|---|---|
| Net | USB_VBUS | GND |
| Native center (mm) | (34.975,26.450) | (36.225,26.450) |
| Gerber center (mm) | (34.975,11.550) | (36.225,11.550) |
| Copper bounding box (mm) | X34.700–35.250, Y11.150–11.950 | X35.950–36.500, Y11.150–11.950 |
| Copper / paste shape | 0.55 × 0.80, R0.1375 | 0.55 × 0.80, R0.1375 |
| Mask expansion | 0 | 0 |
| Paste size margin / ratio | 0 / 0 | 0 / 0 |

The P3 copper flash is **D33**, with macro R0.137500 and corner-center extents ±0.137500/±0.262500 mm. P3 paste uses its own **D32** aperture for the same shape. Gerber D-codes are layer/file-local identifiers; the older supplier record `i274x.RoundRect.d32` is not evidence of P3 copper D33 being a different size.

The mask Gerber contains polygon regions, not flashes. The two openings have the same bounding boxes as copper, with four line segments per corner quadrant. Their area is 0.422255650 mm² each. Native ideal copper/paste area is 0.423770736 mm², versus 0.440000000 mm² for ST's rectangle. The mask's chord approximation is inside the ideal roundrect, with maximum arc/chord deviation about 0.002642 mm. Its entire opening lies on pad copper, so the region gives the actual exported solderable area; exposed adjoining traces do not enlarge it. Supplier CAM changes to these openings are not known.

## Toe, heel, side extension and overlap

Calculated at centered placement and ST's typical e=1.05 mm, treating terminals as rectangular b×L envelopes. Positive extension means the copper bounding box extends beyond the terminal. Negative means terminal overhang. Rounded-corner losses are included separately in areas.

For a right-hand terminal: toe = 0.90−(e+L)/2; heel = (e−L)/2−0.35; each side = (0.80−b)/2. Left terminal is the mirror.

| Terminal case | L × b (mm) | Toe (mm) | Heel (mm) | Each side (mm) | ST rectangle overlap | Actual copper/paste overlap | Exported mask/exposed overlap |
|---|---:|---:|---:|---:|---:|---:|---:|
| Published minimum sizes | 0.30 × 0.75 | +0.225 | +0.025 | +0.025 | 100.00% | 99.56% | 99.48% |
| Typical sizes | 0.35 × 0.80 | +0.200 | 0.000 | 0.000 | 100.00% | 97.10% | 96.83% |
| Published maximum sizes | 0.40 × 0.85 | +0.175 | −0.025 | −0.025 | 88.24% | 85.85% | 85.63% |

These ranges were also checked on a 21×21 grid over the independently published L/b intervals. Minimum overlap occurs at the maximum L/b dimensions. Native rounding costs **2.90 percentage points nominal**, or **2.39 points at maximum sizes**, relative to rectangular ST lands. Mask polygonization costs an additional **0.271 points nominal / 0.223 points maximum**. Neither effect by itself turns nominal ST terminals into the reported 0.87 result.

The rectangle-model ratios are not a guaranteed worst-case assembled result. ST does not provide terminal location tolerance for e or a dimensional definition of the pin-1 chamfer. Removing an unspecified chamfer can change both the overlap numerator and terminal-area denominator; no dimensions were invented. The nonchamfered terminal is represented directly by its published bounding dimensions. Copper etch, mask registration, stencil registration, solder volume and placement tolerances also remain unspecified.

For sensitivity only, at maximum L/b an inward shift of 0.025 mm reduces the right pad's mask-exposed overlap to 79.74%; an outward shift of 0.025 mm raises it to 91.51%. A whole-package shift improves one end and worsens the other. These offsets are illustrative, **not asserted supplier process tolerances**. The CSV includes both directions and selected combined X/Y offsets.

## Supplier flags and disposition

Requested current D4 flags: inner edge 0.00 mm twice; left and right edge 0.05 mm twice each; overlap 0.87 twice. The archived detail records are in `recovery-p2-20261003/dfm/evidence/smt-pin-{inner,left,right}.txt` and `smt-lead-pad-overlap.txt`. The P3 comparison records all displayed category counts identical to corrected-CPL P2; P3 summary has the remaining two overlap yellow records and overall 25 red/6 yellow. This audit did not independently capture fresh per-pin P3 UI rows.

The supplier help text explicitly allows special-design inner-edge exceptions. Its overlap criterion is lead area covered by pad, with 0.75 and 0.90 boundaries. Applying that generic 0.90 criterion to ST's maximum terminal envelope already yields yellow with the manufacturer's own rectangular recommendation.

- **Inner edge:** nominal zero is reproduced by the recommended geometry. This is strong evidence of a generic rule/land-style exception rather than insufficient heel design
- **Left/right edges:** at typical b the straight-edge extension is zero; at maximum b the overhang is only 0.025 mm each side. The displayed 0.05 mm is not uniquely reconciled. The supplier may measure another contour/distance or use a different pin model. Do not assert it uses an incorrect 0.90 mm terminal based on this scalar alone
- **Overlap:** 0.87 is not reproduced by ST's typical terminal and current native rounding. It lies in the range possible as dimensions vary, so it does not itself prove a model error or native defect. Exact model reconstruction is required
- **Native geometry action:** none. No manufacturer-backed reason was found to enlarge width, narrow the gap, move centers, or change CPL. A corner-only rectangular variant would add contact area while preserving ST dimensions, but is optional unless the supplier's process review requires it

## Polarity and pose

Native pad 1/cathode is west on USB_VBUS; pad 2/anode is east on GND. This is the correct electrical orientation for a unidirectional clamp across a positive USB supply. Existing cathode silk is on the west end. Both native audit and user-corrected/released CPL say `D4,35.600000,11.550000,Top,0.000000`; D4 was not among the user's CPL overrides.

This establishes native/BOM/CPL consistency. It does **not** prove JLC's part-model 0° pin-1 convention or actual machine-program polarity. Supplier zero degrees must be checked against the physical pin-1 dot, not text orientation or a guessed interpretation of a bottom-view package illustration.

## Exact residual evidence required to close D4

1. For **C2969802 / ESDA7P120-1U1M in the P3 project**, a dimensioned supplier model export or measured overlay showing both terminal polygons, b/L/e values, body centroid, corner/chamfer shapes, units, package revision, and whether those are nominal/max/tolerance-expanded geometry
2. The applied CPL transform and component model's pin-1/zero-degree convention; a top-side screenshot or assembly preview showing the physical pin-1 dot landing on the west USB_VBUS pad at the released 0° pose
3. For each D4 record, supplier contour/edge selection and distance-sign convention; whether the overlap numerator uses copper, paste, exposed mask, or a simplified pad envelope, and the exact denominator. Reconcile the 0.05/0.87 scalars with the uploaded P3 D33 copper geometry
4. A supplier assembly-process acceptance or specific requested change for these ST-recommended bounding dimensions and the native R0.1375 corners, including any mask/CAM or stencil aperture adjustment and the placement/registration tolerance used. A generic green threshold alone is insufficient

If the supplier accepts the current land and pose, record an explicit package-specific exception. If it requests a change, implement only the demonstrated pad/mask/paste/pose correction, preserve the native electrical polarity, regenerate the exact release and rerun the same-model checks. Nothing in this audit claims supplier approval or production readiness.
