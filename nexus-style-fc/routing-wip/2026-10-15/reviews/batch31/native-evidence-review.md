# Independent native evidence review: batch31

Reviewed published draft PR33 head 8d7fdeb5c5b73123b70e972923f1386c262d018b. Experimental PCB SHA-256 47b6cf94fb2213c0ae46ab692fd9b8f71e90c2c278944827f9156daa25e8e23b.

## Native evidence

The sealed native KiCad 10.0.7 JSON includes error, warning and exclusion severities. It reports exactly 37 clearance errors, zero unconnected items, zero schematic-parity findings, 32 silk overlaps, 19 silk-over-copper warnings and three silk-edge warnings. No excluded violation is present. The five ignored check categories are inherited from the original project, not added for this candidate.

Remote candidate and receipt Git blob hashes match the package. The exact PR comparison lists 38 Nexus-only files; neither canonical PCB is changed. GitHub returned no status contexts and no PR workflow runs for the head; empty CI is not a native or engineering pass.

## Error counts conceal gap regressions

Comparison against the connected widened attempt01 seed shows that 11 of the 37 remaining error pairs became narrower during earlier aggregate coordinate repair. Nine present gaps are below the source project's old 0.09 mm clearance floor. These are fully exposed native errors, not suppressions, but count reduction alone must not be described as uniform geometric improvement.

The worst pair is RPM on B.Cu near (106.252159,104.728013) and J1 pad5 ESC at (105.4,104.15): 0.0920 mm with transferred rules, 0.0885 mm after widening, 0.0647 mm in attempt08 and 0.0261 mm by candidate16/batch31. This pair is a priority for subsequent bounded repair. Other notable regressions include USB_DP to a GND via (0.1162 to 0.0893 mm), SWCLK to U12 S3 (0.0950 to 0.0751 mm), and two CC1/VBUS pairs (0.0938 to 0.0785 mm). Full pair data is in native-gap-regression-review.json.

## What the contact evidence establishes and does not establish

The reviewed cumulative script checks same-layer physical shape overlap for retained track/pad contacts, immutable footprint/pad/net/outline/stack/zone definitions, retained copper width/layer/net/drill/lock properties, all ordinary via dimensions, and no added pasted-pad contact. Complete replacement transactions have separate external-port and finite full-width pad/annular entry evidence. The graph's changing pair count is expected when segments are removed and replaced; no retained original-object contact is lost.

Those checks do not measure frequency-dependent return currents, loop impedance, branch-specific ampacity, copper temperature rise, regulator transient/stability behavior, EMI/crosstalk or fabrication tolerances. Unchanged zone definitions do not mean unchanged filled return geometry. The aggregate minimum-width test is especially limited: some power-net branches already have 0.127 mm source widths, while trunk widths are separately preserved. No 10 A/25 A PCB rating is implied.

## C19 identity and unresolved effective-capacitance requirement

The unchanged schematic assigns C19 LCSC C23630, value 2.2 uF, with the description “LDO out, >=2 uF effective.” The supplier mapping is Samsung CL10A225KO8NNNC, 16 V, X5R, +/-10%, 0603. Effective capacitance at 3.3 V after tolerance, temperature, aging and DC bias has not been established. The same source requirement predates rerouting. No component substitution is made or authorized here.

Supplier mapping: https://www.lcsc.com/product-detail/C23630.html and https://jlcpcb.com/partdetail/CL10A225KO8NNNC/C23630 . TPS709 layout/output capacitance source: https://www.ti.com/lit/ds/symlink/tps709.pdf . The separate board-level return review provides measured new-layer coverage and route lengths.

## Disposition

Keep the exact candidate as unfinished review material. Continue repairs without weakening the 0.127 mm floor, and track residual gap magnitude as well as error counts. Before selecting a final route, complete native DRC/refill/ERC/parity checks and board-level USB, power and return qualification. The 11 header contact-edge errors, mechanical interference, 18 inherited pasted vias and all manufacturing holds remain unresolved.
