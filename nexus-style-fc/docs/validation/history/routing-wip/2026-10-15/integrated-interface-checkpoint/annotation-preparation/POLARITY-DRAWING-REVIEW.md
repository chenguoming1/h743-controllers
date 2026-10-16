# Exact selected LED package polarity review

Reviewed 2026-10-15. This is an orientation-source review, separate from the schematic symbol mapping, native board/Gerber rendering, actual reel orientation and final placement-preview approval.

## Primary drawing evidence

Each downloaded document is from XINGLIGHT's own domain, names the exact selected MPN, and was visually inspected on **page 7, Outline Dimension**. PDFs and page-7 PNGs are hashed in `datasheet-evidence/source-manifest.json`.

- D1, LCSC C965806, **XL-1608SYGC-04**: [manufacturer product](https://www.xinglight.cn/index.php?c=show&id=1062), [primary datasheet](https://www.xinglight.cn/uploadfile/202509/8a6576ffcb20e87.pdf). The polarity figure explicitly places the negative terminal at numbered end 1 and positive at end 2. The colored end mark is at end 1; the triangular underside mark points toward end 1.
- D2, LCSC C965799, **XL-1608SURC-06**: [primary datasheet](https://www.xinglight.cn/uploadfile/202506/60f2a54fafd0ff3.pdf). The page explicitly identifies the end-1 negative mark; the diode polarity figure independently assigns 1 negative, 2 positive. Its underside triangle points to end 1.
- D3, LCSC C965807, **XL-1608UBC-04**: [manufacturer product](https://www.xinglight.cn/index.php?c=show&id=1063), [primary datasheet](https://www.xinglight.cn/uploadfile/202509/2cca13f4111c846.pdf). The end-1 colored mark and triangle-to-1 drawing agree with the independent polarity figure's 1 negative, 2 positive.

The manufacturer's illustrations put end 1 on the right on the page. That page orientation is not a requirement to face the part right on the PCB. End numbering and physical polarity marks are the binding information.

## Separate schematic / source-board proof

The selected schematic symbols name pin 1 `C` for D1 and `K` for D2/D3; pin 2 is `A` for all three. The exact primary drawings independently establish that the selected physical part's terminal 1 is negative. Thus the intended source mapping is verified from both ends; it is not inferred solely from a generic LED symbol or a nearby dot.

All three source footprints are front-side, at zero board rotation, with pad 1 west of pad 2:

- D1: body origin (108.000,125.100), pad 1 (107.200,125.100), net LED1_K; pad 2 (108.800,125.100), LED1_A
- D2: body origin (114.400,125.100), pad 1 (113.650,125.100), net LED2_K; pad 2 (115.150,125.100), LED2_A
- D3: body origin (111.200,125.100), pad 1 (110.450,125.100), net GND; pad 2 (111.950,125.100), LED3_A

Consequently the selected package's negative-marked end 1 must face **board west**, toward the preserved pad-1 nets. The printable markers are at x=107.200/113.600/110.400, y=126.250. They lie on that west/cathode side and are closer to pad 1 than pad 2. D2/D3 marker x is 0.050 mm west of pad-1 center; this is preserved source association, not an assertion of exact x alignment. Their original central polarity graphics, pad shapes/nets and footprints remain unchanged.

## Explicit limits

The new marker is a board assembly cue; it does not define a new package pad number or rotate the component. All source placements and CPL rotation inputs are preserved. We have not verified the final assembler's reel/nozzle zero-angle convention or physically inspected an assembled sample. The current manufacturer's drawings establish the exact MPN's terminal/mark convention; the procurement lot or reel revision is not established here. Compare the final native assembly image and actual placement preview against the end-1-west requirement before release.

No changes to electrical operation, LED current selection, thermal limits, solder lands, stencil process or package-body qualification are made or signed off by this review.
