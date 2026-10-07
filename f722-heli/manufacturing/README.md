# F722 prototype manufacturing files

**VERIFIED PROTOTYPE FILES — FACTORY CAM AND ASSEMBLY ACCEPTANCE REQUIRED.**

Native export verification and the final exact-board electrical analysis are complete. Physical production/flight qualification and actual ordering remain separate.

This public subset contains native KiCad 10.0.6 outputs for the paired `../hardware/f722-heli.kicad_pcb`, SHA-256 `4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f`. The complete 100-file recovery export package was verified separately; this compact public subset has its own inventory.

## Included files

- gerbers/: 13 Gerbers covering six copper layers, both mask/silkscreen/paste faces and Edge.Cuts, plus the native Gerber job
- drill/: separate PTH and NPTH metric Excellon files, two SVG drill maps and the drill report
- assembly/: complete 151-part procurement data, 144 SMT BOM/CPL placements, seven manual/THT headers, five excluded bare test pads and factory rotation-review checklist
- verification/: compact export/assembly results, exact native-check summary, visual-review scope and the native export contact sheet
- FABRICATION-NOTES.md and ASSEMBLY-NOTES.md: manufacturing constraints and supplier/assembly gates

`export-manifest.json` and `SHA256SUMS` bind this final public subset. [Final electrical assessment](../docs/final-electrical-review.md) gives the reviewed scopes and physical limits. The SMT CSV names containing HELD are retained historical filenames; their bytes are unchanged and the package status above is current. Detailed raw logs, scratch exports, duplicate source files, runtime data and vendor manuals are intentionally outside this compact public subset.

## Verified export scope

The 151 populated references are 144 SMT candidates and seven separate J2–J8 THT headers. SMT placements are 59 top and 85 bottom. TP1–TP5 are bare board features; no DNP parts are present. All values, identities, sides, coordinates and native rotations match the source. R16 supply and factory acceptance remain held; J1 is an SMT candidate whose four plated shell slots require separate soldering.

The closed Edge.Cuts centerline is 41.66 × 25.40 mm. Exported PTH features are 323 vias, 21 header holes and four USB shell slots; two nonplated USB locator features are separate. Drill tools and coordinates match source at 0.001 mm output precision. All 494 paste flashes match the native multiset, with 16 USB contact apertures and no USB shell paste.

Gerber, drill and placement origin is (0,0), mm. Output Y is negative native PCB Y. Native signed coordinates and rotations are preserved; no guessed bottom-side mirror or factory angle correction is applied. Factory pin-1/polarity/pickup and placement-preview verification remain required.

Representative native copper/mask/paste/drill exports were rendered and visually inspected. This is native-export geometry/metadata checking, not an independent full Gerber CAM raster comparison. Preserve the final electrical report's conditions and all stackup, sourcing, assembly, harness, mechanical and first-article gates in the companion notes.
