# Integrated interface and routing checkpoint — qualification open

Open the [stable current project](../../current/hardware/nexus-style-fc.kicad_pro),
[main PCB](../../current/hardware/nexus-style-fc.kicad_pcb), and its matching
[child PCB](../../current/hardware/header-board/nexus-header-board.kicad_pcb).

Main PCB SHA256 `ccd8865f6785fd1cdec0214a08fe409faed4d47bb01e8474f09264ee36acab99`. Matching 349-pin schematic `7a133c241ba24a688d2d2490ae423ff74d26f57cf6578f871cc757093584de42`.
The final source-bound native check has zero errors, opens, electrical parity or dangling findings.
Its visible warning inventory is: 4 footprint_type_mismatch, 3 silk_edge_clearance, 19 silk_over_copper, 32 silk_overlap, 11 track_not_centered_on_via. Exact diagnostics, severity disclosure,
contact/return proofs and export checks are in [accepted](accepted/).
The redesigned child has zero geometric errors and opens with exact physical pin/net mapping;
its 11 bare-contact courtyard and 11 footprint-filter warnings remain explicitly disclosed.
No warning suppression or clearance relaxation is used.

## Integrated geometry

The approved tab/slot/contact redesign is now combined with the accepted capacitor/routing source.
Main board body, connector placement and pinout are preserved. Final slots are 10.10 × 2.20 mm,
with matching root-relieved child tabs, synchronized local footprints/generators and the exact
child model. Native and independent analytic checks retain the 0.300 mm copper-edge floor.
The [fit review](fit-review/README.md) binds the actual full-radius model and dimensions.

RPM returns to In2 rather than cutting a long trench through In4. Full-width In1 reference covers
the entire new span outside its two existing via-transition openings. The two measured TAIL
return witnesses improve from 10.95/9.50 mm to direct 0.814/0.922 mm paths. The old ESC probe
is inside its own retained via antipad. Complete ports, actual cap/LDO/buck/USB ground paths,
all 96 inherited shield regions and source-net identities are checked in the core and final evidence.
These measurements establish geometric continuity, not measured impedance or EMI performance.

The planned narrow assembly-attribute and meaningful-silkscreen cleanup has not been applied.
U3/L2/U14 retain the disclosed attribute warnings, and the current silk warnings remain visible.
J1 is a manual child-board solder joint omitted from placement exports; J6 has mixed SMT contacts
and PTH shell soldering. Source-only annotation preparation is preserved separately and is not
claimed as a native-validated change to this board. No centering-cosmetic copper edit is included.

## Fit and assembly limits

Nominal child-mesh clearance is 0.2875 mm. Under the stated adverse size/thickness assumptions,
plus assumed radius/pitch bounds, ±0.10 mm X and ±0.05 mm Y leaves only 0.013997 mm corner reserve.
This is a conditional tolerance study, not a guaranteed fabrication fit. The outer rail is only
0.55 mm nominal and 0.45 mm under the stated adverse size case. Rail strength, finished routing
datums, bow/twist, burrs, seating, solder joints/current/temperature and vibration need physical tests.

The tabs do not self-register contacts. Nominal longitudinal free play exceeds the 0.373 mm
offset where adjacent-net land projections first overlap. Deliberate per-net alignment, holding,
separated tacking and inspection must be demonstrated; a purchased fixture is not assumed necessary.
At ±0.10 mm offset, inner overlap is 1.10 mm for signal and 1.50 mm for power lands, not full overlap.
The actual populated connector/plug/cable/enclosure envelope is not fully qualified.

USB actual-stack impedance/electrical compliance, BEC/input-loop and power/current/thermal tests, ordinary tented via-in-paste process, and physical assembly/strength remain open. **Do not fabricate, assemble or fly.**

The root canonical hardware stays the older coherent reference. Historical experimental snapshots
remain historical. Current BOM/CPL are review-only and bound to this exact source; old canonical CAM
remains stale. The committed routed PCB is authoritative: historical floorplan/build scripts do not
reconstruct accepted copper. Use isolated copies for any new experiment.
