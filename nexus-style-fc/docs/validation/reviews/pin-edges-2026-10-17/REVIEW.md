# SMT left/right pin-edge disposition

**Leave D1-D3 and F1/F2 unchanged for these specific flags.** The current JLCDFM viewer reports eight left-edge and two right-edge danger flags, all displayed as 0 mm. The manufacturer drawings and saved pad/placement geometry do not establish a defect requiring a footprint or CPL change. This disposition is limited to those pin-edge checks; it does not clear other assembly/fabrication findings or release the board.

| Parts | Current pads and gap | Drawing comparison | Disposition |
| --- | --- | --- | --- |
| F1, F2: RUILON SMD0805P050TF / C20978 | Two 1.0 x 1.5 mm rectangular pads, centres 2.2 mm apart, gap 1.2 mm | Exact nominal match to the manufacturer's recommended 1.0 +/- 0.1 x 1.5 +/- 0.1 mm pads and 1.2 +/- 0.1 mm gap, page 5 | Keep both footprints and CPL poses |
| D2, D3: XL-1608SURC-06 / XL-1608UBC-04 | Two 0.8 x 0.8 mm rectangular pads, gap 0.7 mm | Manufacturer recommends 0.7 x 0.8 mm pads with 0.7 mm gap. Existing pads keep the inner edges and width, and extend 0.1 mm farther outward | Keep |
| D1: XL-1608SYGC-04 | Two 0.8 x 0.8 mm rectangular pads, gap 0.8 mm | Manufacturer recommends 0.7 x 0.8 mm pads with 0.7 mm gap. Existing inner pad edge is 0.05 mm farther out; nominal bottom contact still fully overlaps | Keep; optional land-pattern standardization would not address the side-edge flags |

For all three LEDs, page 7 of the exact manufacturer datasheets shows a nominal 0.8 mm package width and 0.7 mm-wide bottom contacts, 0.35 mm long. The pads have the recommended 0.8 mm lateral width. On the nominal model, package/upper terminal edges may therefore coincide with pad edges while the narrower bottom contacts still have about 0.05 mm lateral copper on each side. The source's nominal 0.35 x 0.7 mm contact rectangles fit within all six LED pads; no pad reduction or polarity change is proposed. D1-D3 retain their native/CPL 0 degree top pose. F2 retains its 0 degree top pose and F1 its 90 degree bottom pose, aligned with their two-pad axes.

The fuses' specified maximum body width is 1.5 mm, equal to the recommended nominal pad width. Their four flags are therefore consistent with a model at the pad boundary; widening pads is not required by the published pattern. Both fuses are non-polar. The six LED flags are similarly consistent with boundary/model rounding. **The exact numeric cause inside JLCDFM is not exposed: 0 mm is a rounded display, so these are engineering dispositions based on the drawings, not proof that every internal overhang value is exactly zero.**

## Evidence

- [RUILON drawing, page 5](sources/SMD0805P050TF-RUILON.pdf), obtained from the exact C20978 LCSC datasheet link; version A5/2024-2-21
- Existing retained XINGLIGHT manufacturer PDFs for the three exact MPNs, page 7; paths and hashes are in [input-binding.json](input-binding.json). No duplicate LED PDFs were added.
- [Measured native pad geometry](geometry-comparison.json)
- Website [left top](left-top.txt), [left bottom](left-bottom.txt), [right top](right-top.txt), [right bottom](right-bottom.txt)

The 10 findings apply to five parts: D1/D2/D3 each have two left-edge flags, F1/F2 each have one left-edge and one right-edge flag. Existing source, Gerbers, BOM and CPL remain unchanged. No new DRC run was needed for this read-only review, and no supplier process approval or physical assembly trial occurred.
