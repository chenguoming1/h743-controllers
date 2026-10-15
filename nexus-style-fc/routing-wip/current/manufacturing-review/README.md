# Unreleased Nexus manufacturing review package

These are exact exports of the accepted stage10 experimental source, made with official KiCad 10.0.7. They are ready for the separately authorized DFM review, not a fabrication or assembly release. No order, quote or factory contact was performed by the export lane.

## Files

Each board directory contains its Gerber-and-drill ZIP plus actual JLC-format BOM/CPL. The main ZIP has six copper layers, both mask/paste/silk layers, complete outer/slot contours and separate plated/nonplated drill files. The child ZIP has two copper layers and the corresponding layers/outline/drills; its NPTH file is intentionally empty. Exact layer roles and saved stack/settings are recorded in source-and-settings.json and the native Gerber job files.

Main export: 238 plated round via holes, four plated routed USB shell slots, and two nonplated locating holes. Child export: three plated via holes and 21 plated header holes. Every native hole is accounted for. Excellon is decimal millimetres with three fractional digits: measured centre quantization is at most 0.0006253 mm main / 0.0004243 mm child. The largest tool-diameter rounding is 0.000002 mm. Main 24 and child 18 outline segments/arcs match the exact saved native contours within 0.000000553 mm. All three .300 mm cathode dots survive mask-subtracted silk export.

Main BOM has 83 selected parts in 48 rows. CPL is exact to the accepted source; five approved main-local footprint names are the sole BOM metadata changes from stage08. Child exports one item: J1 servo header, C32713294. It is through-hole; the generic CPL row does not mean SMT placement is qualified. The tab/contact joints are manual. J6 remains a mixed SMT/PTH process.

## Open gates

Main nominal thickness is 1.600 mm; saved copper/dielectric thicknesses total 1.6168 mm, or 1.6368 mm with the two mask entries. Child declares 1.600 mm without a detailed stack. These values are preserved, not reconciled to an approved factory stack. USB impedance/reference, power/HF/transient/current/thermal performance, 16 inherited main pasted-via locations, under-body tenting, stencil/reflow/assembly, mechanical tolerances/fixture registration/rail strength and solder-current tests remain unqualified. Main retains 49 silk, 11 centering and one mixed-technology advisory; child retains 11 filter and 11 courtyard advisories.

Checks here establish export integrity, exact source binding, outlines, hole inventory/origin/serialization and BOM/CPL selection. They do not replace independent copper-clearance Gerber analysis or remote factory DFM. A source-call argument error stopped before any native export; the drill check initially compared a legacy 0.599998 mm nominal hole against the correctly serialized 0.600 mm tool. Both failed receipts are retained; no board edit or rule relaxation occurred.
