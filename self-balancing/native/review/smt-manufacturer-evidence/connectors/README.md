# P3 connector SMT closure audit

Read-only audit, 2026-10-03 UTC. Native board SHA-256: `0850991d8aacd22138487804c24eefbae634a21ba218c18196f13fad795c3696`. No CAD, supplier data, order, or assembly setting was changed. The dated six-layer audit was used as background; all poses, pads, holes, and source identities below were re-extracted from current P3.

## Result

- **J3/J4/J5 component-edge rows:** no native copper or nominal Fab body crosses the board edge. These are assembly handling/carrier acceptance items and unresolved supplier-model alignment, not demonstrated land failures. J3's exact physical body-to-land datum remains incompletely specified by its supplied drawing.
- **J3 through-hole row:** incompatible with the selected manufacturer's SMD-only land pattern and the native SMD-only footprint. Resolve the C7527621 model/lead classification; do not invent holes.
- **J2 outline clipping:** near-flush USB mouth is intentional geometry. The DFM value 8.94 mm equals the shell width and is **not an established overhang depth**. Native Fab overhang is 0.000 mm; HRO drawing aligned by locating pegs predicts 0.030 mm nominal mouth overhang. Assembly and mated-plug access still require acceptance.
- **Separate J2 land-pattern departure:** the two front plated slots are 0.60 × 1.20 mm, while the exact HRO drawing recommends 0.60 × 1.40 mm. This is a real recommendation departure, not proof that the tabs cannot fit. A robust correction, if authorized in a subsequent revision, is 0.60 × 1.40 drill plus 1.00 × 1.80 copper, retaining the existing 0.20 mm annular ring. It needs local rerouting; it cannot simply be enlarged in place with present clearances.

The four green J2 hole-alignment results and zero missing holes close the earlier supplier-position mismatch. They do not prove finished slot tolerance, plated-slot soldering, mated access, or process acceptance.

## Evidence files

- `native-connectors.json`: exact native pads, holes, net names, graphic envelopes, BOM/CPL rows, and source hashes
- `connector-edge-evidence.png`: current native coordinate views and HRO mouth/edge overlay; bottom views deliberately retain the native top-board coordinate frame rather than mirroring CPL
- `hro-typec-drawing.png`, `*-lands.png`, `*-tabs.png`, `*-body.png`, `*-tolerances.png`: rendered exact source and readable crops
- `audit_connectors.py`: repeatable, read-only extraction; optional new pad shapes are mathematical capsules only, never saved CAD
- `render_connectors.py`: figure generation
- `../usb-slot-screen/screen-result.json`: parent's canonical optional pad-enlargement/clearance screen

The native source remains byte-identical after extraction. The input-hash map covers the board, both CPLs, BOM, HRO PDF, JST PDF and Lian Xin PDF.

## Exact identities and coordinate frames

Native coordinates are in mm, X right and Y down. The fabrication/placement datum is (0,38): raw CPL X = native X, raw CPL Y = 38 − native Y; no bottom-X mirror. Supplier CPL corrections are model/pickup transformations, not physical component moves.

| Ref | Exact fitted manufacturer part / JLC code | Native anchor / angle / face | Final supplier CPL X,Y / angle |
|---|---|---|---|
| J2 | HRO TYPE-C-31-M-12 / C165948 | (34.350,20.000), 90°, top | (33.000,18.000), 90° |
| J3 | Lian Xin XDWF-0910-06P / C7527621 | (3.200,11.450), 90°, bottom | (3.200,26.550), 90° |
| J4 | JST SM08B-SRSS-TB(LF)(SN) / C160407 | (3.200,23.750), 90°, bottom | (3.200,14.250), 90° |
| J5 | JST SM04B-SRSS-TB(LF)(SN) / C160404 | (34.800,10.550), 270°, bottom | (34.800,27.450), 270° |

J2's −1.350 mm supplier X correction is preserved in the current release and matches the user-corrected input. Do not subtract it from the native physical mouth or holes. J3/J4 native Fab centers are X2.750, while J5 is X35.250: each lies 0.450 mm toward the mouth from its library anchor. This does not by itself establish a supplier pickup correction.

## Side sockets: actual lands, nominal bodies, and edges

| Ref | Native Fab X interval | Native Fab Y interval | Body depth × width | Mouth inset | Closest MP copper inset | Courtyard overhang |
|---|---|---|---|---:|---:|---:|
| J3 | 0.625…4.875 | 7.450…15.450 | 4.250 × 8.000 | 0.625 | 0.425 | 0.080 |
| J4 | 0.625…4.875 | 18.750…28.750 | 4.250 × 10.000 | 0.625 | 0.425 | 0.080 |
| J5 | 33.125…37.375 | 7.550…13.550 | 4.250 × 6.000 | 0.625 | 0.425 | 0.080 |

J3/J4 mouths face X0; J5 faces X38. Every connector pad is inside the board. All three use 0.60 × 1.55 signal lands on 1.00 pitch, and two 1.20 × 1.80 SMT hold-down lands. The pattern depth is 5.55 mm. Hold-downs are on bottom copper/mask/paste, grounded, and have no drill. No locator or shell hole is missing from these selected SMD parts.

Signal centers: J3 at X5.200 and Y13.950 down to 8.950; J4 at X5.200 and Y27.250 down to 20.250; J5 at X32.800 and Y9.050 up to 12.050. Hold-down centers are J3 (1.325,7.650)/(1.325,15.250), J4 (1.325,18.950)/(1.325,28.550), J5 (36.675,7.750)/(36.675,13.350).

[JST's manufacturer SH catalog](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf) gives mounting-surface land-pattern orientation, circuit 1, side-entry dimensions, and exact 4-/8-circuit selections. These substantiate J4/J5's native orientation and nominal body registration. Its dimensions are reference values. The catalog's 6.25 mm mated assembly depth exceeds the 4.25 mm header depth by 2.00 mm; a nominal axial interpretation gives about 1.375 mm assembly protrusion beyond this board. That inference excludes wires, bends, and insertion/removal clearance and is not an accepted fixture envelope.

[Lian Xin's exact C7527621 listing and supplied drawing](https://jlcpcb.com/partdetail/Lian_XinTechnology-XDWF_091006P/C7527621) establish the selected 6-pin SMD part and nominal 8.00 × 4.25 × 2.90 body. Its land dimensions match the native pattern. The drawing does **not** fully datum body-to-land registration or label cavity 1; J3's 0.625 inset is therefore a native Fab result, not an exact production-body certification. It names ZYA1001H mating housing; JST cross-mating is unqualified.

The C7527621 web result retrieved on 2026-10-03 13:09 UTC says SMT Assembly and that a support/protection fixture is needed. The web tool labels that page crawl five months old. This is exact-SKU supporting catalog evidence, **not live factory acceptance**. J4/J5's returned exact-code listings identify SMT parts; they do not qualify this carrier layout.

## Disposition of supplied DFM rows

The supplied UI records were read from `/workspace/scratch/8a35c1f26232/jlcdfm-p3-review/corrected-cpl-smt-{edge,through-hole-warning,outline-clip}.txt`. Their title still names a corrected-CPL P2 test; the task owner separately reports that current P3 project 629271171624820737 repeats the same rows. This audit does not claim an independent live P3 viewer inspection.

| Row | Reported result | What the evidence establishes | What closes it |
|---|---|---|---|
| J3 component edge | 0.28, danger | Native pad gap 0.425; Fab body gap 0.625; exact physical/model datum unresolved | C7527621 model origin/body/lead outline and accepted carrier/nozzle clearance |
| J4 component edge | 0.51, warning | Actual nominal body is inset 0.625; no land crossing | Exact model-to-native alignment plus double-sided handling acceptance |
| J5 component edge | 0.73, warning | Same nominal inset 0.625; opposite facing placement is correct | Exact model-to-native alignment plus double-sided handling acceptance |
| J3 through-hole | 5.88, warning; second object null | No connector holes exist or are recommended; no evidence of a missing native hole | Supplier explains/removes erroneous model/lead class or provides a contradictory exact-SKU drawing |
| J2 outline clipping | 8.94, warning | Width equals physical shell width; mouth is near flush | Accepted USB special-design exception, carrier clearance and mated access |

The edge rule's own text concerns collision with assembly equipment. The clipping rule explicitly allows special designs such as USB connectors. None of those descriptions establishes that an electrical or land-pattern failure occurred. Conversely, deliberate edge placement does not establish the assembly equipment can handle it. Values 0.28/0.51/0.73 differ from the native common 0.625 body inset; without the supplier model, do not invent corrections from those differences.

## J2: manufacturer-aligned mouth and mounting details

The source is the exact HRO TYPE-C-31-M-12 sheet, title block date 2020-12-08, local PDF SHA `6ae33d50ac47820114661138dc4e4659f40fdc5d4f485b46685dfec338da1a9e`. The [current C165948 listing](https://jlcpcb.com/partdetail/C165948) links the same source object [8550723676065714176-C165948.pdf](https://jlc-prod-smt.oss-eu-central-1.aliyuncs.com/smtDataManualFile/8550723676065714176-C165948.pdf). The signed live PDF download failed in the web tool; the previously retained identical named source was visually inspected at high resolution.

The two native NPTH locator centers are (31.750,17.110)/(31.750,22.890), spacing 5.780, diameter 0.650. The drawing specifies 0.500 locator pegs and a recommended 0.600 PCB hole. Aligning its peg datum to native holes:

- HRO locator-to-mouth dimension 6.280 gives mouth X38.030; width 8.940 gives Y15.530…24.470
- HRO shell depth 7.350 gives rear shell edge X30.680; native Fab is X30.700…38.000, only a nominal simplified envelope
- HRO recommended PCB edge is 5.790 beyond the locator: X37.540. Actual X38.000 extends 0.460 farther under the mouth
- HRO nominal mouth overhang relative its recommended edge is 0.490; relative the actual board it is about 0.030
- Drawing dimensions include general component tolerances, and fabrication/placement add more. The 0.030 result is nominal, not a guaranteed positive projection. Near-flush shell geometry needs actual mating-plug/enclosure acceptance

All 12 physical SMT signal locations (16 named A/B pad records) are at X30.305 and remain on-board. Their native copper extents are X29.580…31.030. The four paired power/GND lands are 0.60 wide; the other eight are 0.30 wide. Native length is 1.45. The drawing's signal-land length inferred from 1.64−0.50 is 1.14; the installed lands are longer. Small lateral center differences at outer paired pads are 0.05 mm. This is not a literal copy of every 2020 reference-land dimension; this audit found no clipped or missing contact land. Native coordinates and nets are retained for supplier overlay, rather than declaring blanket exact-pattern equivalence.

| Feature | Native current P3 | Exact HRO recommendation |
|---|---|---|
| Rear shell slot centers | (31.220,15.680)/(31.220,24.320) | approximately X31.250 from PCB-land datum, X31.260 from rounded body dimensions |
| Front shell slot centers | (35.400,15.680)/(35.400,24.320) | X35.430 from locator/mouth/tab dimensions |
| Shell row separation | 4.180 | 4.180 |
| Transverse slot-center separation | 8.640 | 8.650 in PCB pattern; component drawing 8.640 |
| Rear slot drill / copper | 0.60×1.70 / 1.00×2.10 | 0.60×1.70 / 0.90×2.00 |
| Front slot drill / copper | 0.60×1.20 / 1.00×1.60 | 0.60×1.40 / 0.90×1.70 |
| Locator hole | 0.650 NPTH | 0.600 NPTH for 0.500 peg |

Dimensions are local footprint width × length; at native 90°, slot length runs in global X. All four plated S1 lands are grounded and have no paste apertures. Require an accepted shell-joint solder process covering all four; ordinary signal-contact reflow alone is not evidence that the shell anchors are soldered.

### Front-slot fit and correction choice

The drawing's two front tabs are 0.80 long with general ±0.10 tolerance, hence 0.90 maximum. Rear tabs are 1.10±0.10. Native front slot length 1.20 gives 0.30 total room against the maximum front tab before position, corner and thickness effects. [JLC's current published capability](https://jlcpcb.com/capabilities/pcb-capabilities) permits plated-slot size +0.13/−0.08 and hole position ±0.075. Applying −0.08 to slot length leaves 1.12−0.90 = 0.22 total, or 0.11 at each end when centered; the approximately 0.03 nominal center offset reduces one end to about 0.08. Component datum tolerances, hole position, peg float and curved slot ends remain. This does not prove interference, but it does not establish guaranteed worst-case fit.

For six-layer, 1 oz outer copper, JLC recommends a PTH ring of at least 0.20; its absolute minimum is 0.15. The HRO 0.90×1.70 copper around 0.60×1.40 slot has a 0.15 ring. **Prefer 1.00×1.80 copper with the recommended 0.60×1.40 slot**, keeping a 0.20 ring and existing centers, if a bounded correction is authorized. No guessed model translation is required. Slot center differences are within the drawing's ±0.05 PCB-layout tolerance.

The optional larger copper would reduce clearances to approximately 0.050 USB_VBUS on B.Cu, 0.067 UART3_RX on In2.Cu and 0.064 AUX_PC8 on F.Cu; it therefore requires local routing repair and fresh DRC/export verification. It retains 1.70 mm copper-to-board-edge clearance. The parent independently screened the same issue in `../usb-slot-screen/screen-result.json`. A smaller manufacturer copper envelope may reduce rerouting but trades away the preferred 0.20 annular ring; do not use it merely to hide clearance failures.

## Smallest remaining evidence

1. One supplier response or verified production model overlay for exact C7527621 identifying body/land origin, cavity 1 and all lead types, and explaining the through-hole warning. A generic JST model does not qualify the Lian Xin part
2. Acceptance of edge-connector clearances on the actual Standard double-sided carrier/fixture, including nozzle, rail, tab and depaneling access; show mouths and both faces
3. For J2, either exact-lot finished-slot-fit acceptance of P3 or a validated subsequent revision adopting 0.60×1.40 front slots with local clearance repair; independently confirm shell-joint solder coverage
4. A mated USB plug/enclosure check of the near-flush mouth, and exact mating-harness/cavity convention for J3. JST SH evidence qualifies J4/J5, not an assumed interchangeable J3 harness

These are scoped model, process and physical-acceptance items. No manufacturer inquiry was sent, and no supplier approval is implied.
