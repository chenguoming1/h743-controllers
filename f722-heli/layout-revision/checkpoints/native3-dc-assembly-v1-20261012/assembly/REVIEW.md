# Adopted native3: bounded assembly review

Reviewed 2026-10-12. Disposition: no demonstrated assembly collision requires a PCB move or change from the existing ordinary 0.45/0.20 mm both-sides-tented process. Final factory orientation/process review remains required. This is local nominal-geometry review, not manufacturing or flight qualification.

Current board: `recovery-negotiated-routing-20261011/native4-r35-cleanup-native-preparation-v2/outputs/r35-cleanup-native-v1/diagnostic-board/f722-heli.kicad_pcb`.

- Board SHA-256: `c3183f7841bae96a59b29fd13ce9789cf47386a9db452a327ca797187d2ca8a8`
- Decompressed native SHA-256: `a4fddb679e9d73dd2a7b6300fa8888be47e30ab6f139bd5b78ab308d9192563c`
- Current authority: preparation `FINAL-HANDOFF.json` plus output `owner-geometric-adoption.json`; original reports preserved.

`review.py` reproduces the bounded comparison and local measurements in `evidence.json`, under a 512 MiB address-space cap. It does not load KiCad, geometry libraries or solvers, and writes only this review's evidence. `MANIFEST.json` binds the deliverable and source evidence.

## SERVO2 via beneath U1

Via `1953b731-93ac-592f-a736-2b74392740f0`, (17.047384, 12.463262), is 0.45/0.20 mm, tented on both sides, with no mask opening. Its disk is wholly beneath U1's nominal molded-body projection. U1 is STM32F722RET6, LQFP64, B.Cu at (20.959999, 13.8), 0 degrees. It has 64 perimeter lands and no central solder land.

Nominal circular-disk to native pad-polygon minimum separations are approximately:

- Back land, mask opening and paste: 0.762 mm to U1.11; drill to opening 0.887 mm.
- Front land, mask opening and paste: 0.388 mm to Q1.1; drill to opening 0.513 mm.

All relevant paste margins are zero and unchanged. These values identify nominal geometry, not production tolerances or exact native circular-contour approximation distances. No via-in-pad or via-in-paste collision is demonstrated.

ST's LQFP64 drawing specifies A1 = 0.05–0.15 mm relative to the package lead seating plane, and lead coplanarity ccc at most 0.08 mm. A1 is not a guaranteed assembled gap above PCB mask or a via tent. No assumed copper, solder or mask height was subtracted to claim clearance or collision. [ST DS11853 Rev 9, section 7.1, pages 197–199](https://www.st.com/resource/en/datasheet/stm32f722re.pdf).

JLC defines tenting as soldermask coverage and warns that incomplete plugging can leave tin beads. Filled/capped processing is a separate option. Tenting does not establish filling, capping or guaranteed flatness. [JLC via covering, updated September 9, 2026](https://jlcpcb.com/help/article/pcb-via-covering).

Keep ordinary tenting on current evidence. No blanket U1 body keepout or mandatory filling follows from the package drawing. Final factory process review and first-article inspection should include tent coverage/topography, U1 seating and joints. A demonstrated process interference would justify a specific remedy; none is established here. No process substitution, supplier contact, order or terms acceptance occurred.

## Exact predecessor applicability

The predecessor is `assembly-trimmed-native4-review-20261012/REVIEW.md`, bound to board `1b463dbb2115f5fa0d0ffada1f80fe674b1418a4ddbd661c83cb7516f334374a` and native logical hash `c4d5b66eeabdc7d9e7b87715ddcb811038ce9f8b2b67a722eec578cf807fe779`.

Every footprint record except R35 is exactly unchanged. Only R35's two pad records changed; all pad settings are exactly unchanged. RED via `2754fcb2-b9e9-5c3b-8023-61718c16e5e6` is exact. U1, U15, J11, U3 and Q1 footprint/land/mask/paste records carry over.

R35's current pad 1 occupies the former pad 2 position and shape, and current pad 2 the former pad 1 position and shape. Copper and mask polygon point sets match exactly across this swap; zero-margin paste therefore occupies the same regions. The body and physical land/paste union remain unchanged, while pad identities and nets at those locations change.

The predecessor RED-via/J11/U3 measurements and underside-information limitations remain applicable. U15's ten paste apertures and containment remain applicable. The same nearest foreign land is now R35.1, formerly R35.2, approximately 0.469 mm away. The prior nearest drill remains exactly retained; added drills are approximately 2.505, 12.473 and 1.505 mm from U15 paste and do not replace the prior approximately 0.310 mm minimum. No stronger supplier seating/tolerance claim transfers.

## Eventual CPL and orientation gate

The staged exporter preserves native bottom X and signed angles, and uses output Y = negative native Y. Its `native_export.py` reads `GetOrientationDegrees()` and compares the native position CSV angle numerically without a modulo correction. Thus current expected raw rows are:

- R35: X 29.2, Y -23.0, bottom, -90 degrees (geometrically equivalent to 270 degrees), replacing the old +90 degrees.
- U15: X 27.721926, Y -21.185113, bottom, 0 degrees.
- U1: X 20.959999, Y -13.8, bottom, 0 degrees.

Regenerate from the eventual exact final board. Do not reuse the old R35 row, mirror bottom X again or guess supplier angle corrections. Compare final CPL, bottom assembly view and actual factory part models against pin 1/polarity. R35's nonpolar symmetry does not make stale source data acceptable. U15's chosen C138714 model still requires the factory placement preview.

Counts remain 144 SMT: 65 front / 79 back. Preserve J2–J8 manual THT and TP1–TP5 bare-pad exclusions; matching totals do not prove matching poses. JLC requests both sides in one CPL with explicit side fields. [JLC BOM/CPL guidance, updated September 9, 2026](https://jlcpcb.com/help/article/advice-for-bom-and-cpl-files-preparation).

No final Gerber/stencil CAM, supplier placement preview, first-article or assembly-tolerance qualification was performed. Three electrical opens, two historical RX dangling-via warnings and stale power/reference evidence remain. This report does not mark the board ready for manufacture.
