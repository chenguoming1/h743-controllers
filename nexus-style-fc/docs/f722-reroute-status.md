# Latest integrated candidate

[Current project](../routing-wip/current/README.md) and [exact evidence](../routing-wip/2026-10-15/integrated-interface-checkpoint/README.md). Main/child geometric errors and opens are zero. Advisory and electrical/physical/process qualification gates remain open. No fabrication release.

Historical status follows.

---

# Latest: r62, zero main-board native errors

[Stable current project](../routing-wip/current/README.md) and [full source-bound evidence](../routing-wip/2026-10-15/input-caps-checkpoint/README.md). Approved C27/C31/D5 changes are atomic with the matching schematic/library/tools/PCB. Zero opens/parity; all-visible PCB has 11 centering/five type/54 silk warnings. Enabled ERC has zero findings; all-visible ERC has 13 single-global-label warnings. Mechanical integration and electrical/assembly/production qualifications remain open. No fabrication release.

Historical status follows and does not override the current guide.

---

# Latest: r61, two clearance errors

[Open the stable current candidate](../routing-wip/current/README.md). The matching PCB/project/schema/rules are together there. [Exact native and mechanical evidence](../routing-wip/2026-10-15/r61-interface-checkpoint/README.md) records zero opens/parity/ERC binding, 13 centering/five type/54 silk warnings, and separate mechanical main 24 errors. The old canonical route remains at 627 errors. Approved C27/C31/D5 changes are still pending atomic native validation and excluded here. No fabrication release.

Historical status follows; it does not override the current guide or the newly recorded mechanical native-net rejection.

---

# Current experimental routing: 8 clearance errors, unfinished

[Exact source, native receipts, mechanical states and open gates](../routing-wip/2026-10-15/usb-interface-checkpoint/README.md).

Fresh native KiCad 10.0.7 experimental result: 8 clearance errors, minimum 0.0927 mm, zero opens/electrical and footprint-filter parity findings. Exact unchanged schematic/ERC binding remains valid. All-visible diagnostics retain 13 centering, five footprint-type and 54 silk warnings. Canonical remains 627 inherited errors. No new exclusion or suppression is introduced.

Complete USB routing removes all three USB clearance pairs with explicit .170 mm inner/.150 mm launch widths and exact tapers. Actual filled-return/CAM/finite-port checks pass; production-stack impedance and USB electrical qualification remain open. Four buck entries are now centered with finite annular proofs.

The separate child mechanical correction reaches zero errors/opens/ERC while retaining 11 filter and 11 courtyard warnings. Main mechanical copper remains 45 errors/zero opens. Physical fit/fixture/solder/strength tests remain pending. C27's effective input capacitance is inadequate in the manufacturer typical-bias screen; a supported remedy and input-loop qualification are required. Do not fabricate or assemble.

Historical entries follow and do not override this state.

---

# Current r57 checkpoint: unfinished, 13 clearance errors

[Exact experimental source, native receipts and open gates](../routing-wip/2026-10-15/local-r57-checkpoint/README.md).

Fresh native KiCad 10.0.7: experimental 13 clearance errors, minimum 0.0893 mm; canonical 627 inherited errors. Both have zero opens, exact 347 physical pin/net mapping, zero ERC and no footprint-filter parity warnings. All-visible diagnostics retain 17 experimental / 21 canonical off-center warnings, five footprint-type warnings and 54 silk warnings each. No new or worsened native clearance pair, exclusion or suppression is accepted.

New progress: same-layer thermal-via clearance repair; two holes moved outside pasted pads with unchanged mask/paste apertures; centered full-width RPM annular entry; exact Nexus-only filter-library binding with unchanged shared design imports and BOM/CPL bytes. Four 5V_BUCK annular/current entries remain under review. Sixteen pasted vias / seventeen contacts remain.

The separate mechanical candidate is an unfinished r54-based implementation with known shorts/gaps. Its dimensions/tolerance/strength calculations do not prove physical fit or load capacity. Accepted header remains eleven edge errors until successful replay/reroute. USB pair, power/reference/transient and fabrication/assembly qualifications remain open. Do not fabricate or assemble.

Historical entries follow and do not override this state.

---

# Current r54 checkpoint: unfinished, 14 clearance errors

[Exact current experimental project and evidence](../routing-wip/2026-10-15/local-r54-checkpoint/README.md) continues from the published 18-error r51 state through complete DSM_DATA, CC2 and C_RX/GND repairs. Native KiCad10 refill/save/all-track DRC: 14 clearance errors, zero opens/parity, 54 unchanged silk warnings; minimum remaining gap 0.0893 mm. No new/worsened pair is accepted. The exact unchanged 49f9 schematic retains its zero-ERC receipt; no new ERC run is claimed for these copper-only transactions.

All accepted widths/layers and external ports are preserved. The final saved board rechecks all 96 inherited shield-spoke regions, actual R20/U7/J6 finite ground contacts, and U10 full-width output-reference projection. USB copper is unchanged; the conditional neck proposal is excluded while complete paired topology/reference work continues.

A source-bound read-only pasted-via review records all 18 inherited locations and shared capacitor/thermal/ESD donors. Filled/capped processing is not universally mandatory; TI also allows properly plugged or tented thermal vias. The actual current pad mask/paste opening, rather than global tenting alone, needs a verified process remedy. No paste/mask/footprint/process change is made.

Canonical is unchanged at 627 inherited errors; header at 11 edge errors and unresolved tab/slot fit. Power/thermal/fault, USB/SI/ESD, manufacturing and mechanical qualification remain open. CAM/CPL are stale; do not fabricate or assemble.

Historical entries follow and do not override this state.

---

# Current r51 checkpoint: unfinished, 18 clearance errors

[Exact candidate and evidence](../routing-wip/2026-10-15/local-r51-checkpoint/README.md) continues PR37 from main 80a3f763. Complete-contact r48/r50 repairs improve 24 to 18 errors; fresh r51 restores a 4.400335 mm all-F.Cu, 0.250 mm U10 output leg while retaining an explicitly documented input transient/PSRR tradeoff. Native refill/save/all-track DRC: 18 clearance errors, zero opens/parity, 54 unchanged silk warnings, minimum gap 0.0878 mm. Fresh ERC is zero for the exact unchanged 49f9 schematic. No new/worsened residual pair is accepted.

The final metadata-only pass removes U10's stale donor LCSC field and corrects its library description, with unchanged selected TPS70933DBVR/C89347 fields, geometry, fills, BOM/CPL exports and 347-pin map. The scoped generator hook does not edit shared libraries or other projects. Canonical copper remains unchanged at 627 inherited errors, with zero opens/parity/ERC and 54 silk warnings.

All 96 inherited shield-spoke regions are preserved by the corrected CC1 transaction. The U10 decision uses actual device guidance: input capacitance is not a stability prerequisite; the measured input reference/travel change remains an electrical qualification issue. No C18 substitution or placement change is made. Historical r44 hold statements below are superseded by the fresh r51 decision and validation, not by reusing an old receipt.

Header remains at 11 edge errors; a read-only fit review identifies a concrete but unapproved slot/tab/contact/fixture redesign. USB pair/actual-stack/ESD work and power/thermal/fault qualification remain open. CAM/CPL are stale; manufacturing stays on hold. No fabrication or flight readiness.

Historical entries follow and do not override this state.

---

# Current r47 checkpoint: unfinished, 24 clearance errors

[Exact candidate and evidence](../routing-wip/2026-10-15/local-r47-checkpoint/README.md) follows main 80a3f763. Three bounded complete-contact repairs improve the published 29-error experimental route to 24. Native KiCad 10.0.7 refill/save/all-track DRC gives 24 clearance errors, zero opens/parity and 54 unchanged silk warnings. Minimum remaining gap 0.0785 mm; no new/worsened residual pairs. The final 49f9 schematic/ERC is unchanged. Canonical, header, schematic/generators/BOMs and all unrelated files are untouched.

[USB/stack review](../routing-wip/2026-10-15/local-r47-checkpoint/usb-review/USB-STACK-REVIEW.md) measures the exact earlier 29-error source and identifies full-port/return/impedance/ESD work; it is not validation of a later refill. No arbitrary length/skew caps are added. U10 input/output-loop qualification is still open; the conditional r44 route is excluded. No C18 relocation is applied.

Canonical remains 627 inherited errors; header 11 fixed edge errors and unresolved tab/slot fit. Prior exact receipts remain below. CAM/CPL remain stale and the entire manufacturing package remains on hold. No fabrication or flight readiness.

Historical entries follow and do not override this state.

---

# Current checkpoint 07: circuit redraw, approved C19 upgrade and r43, unfinished

[Exact checkpoint and native evidence](../routing-wip/2026-10-15/drafted-circuits-checkpoint/README.md) is based on main cc1ec880. All 15 functional sections are conventionally drafted. Only approved C19 metadata changes electrically selected parts: 10uF/10V Samsung CL10A106KP8NNNC, JLC C19702, unchanged footprint/placement. All 347 physical pin nets and original identities remain exact.

Native KiCad 10.0.7 against final schematic 49f9e057 gives 627 canonical errors (428 clearance,199 width), 29 experimental clearance errors, zero opens/parity/ERC and 54 unchanged silk warnings in both main states. No new/worsened native pair is hidden. All copper and physical geometry are unchanged by the C19 update. Header retains 11 fixed edge errors, with exact prior source-bound checks.

[Single-sheet PDF](schematic-main.pdf), [15-page circuit booklet](nexus-schematic-review.pdf), [exact source/validation ZIP](nexus-drafted-schematic-source-and-validation.zip). Earlier Library previews may still show the prior version; these files are current.

Both BOMs update C19 only and pass full part/reference parity. CAM/CPL remain stale and on hold. C19's stronger typical capacitance margin does not qualify stability, input/output loops, power/return paths, USB/ESD, current/thermal/fault behavior or assembly. The conditional U10 reroute is excluded because of its input-reference tradeoff. No fabrication release.

Historical entries follow and do not override this state.

---

# Current checkpoint 06: connected schematic and EN isolation, unfinished

[Checkpoint 06](../routing-wip/2026-10-15/en-readable-checkpoint/README.md) includes the approved U10 EN correction and a physically connected functional-unit schematic, rebuilt on latest main 866afe8. Native KiCad 10.0.7 revalidation gives:

- Canonical minimal-fix board: 627 inherited errors (428 clearance, 199 width).
- Separate experimental batch35-derived board: 32 clearance errors, minimum remaining gap 0.0751 mm.
- Both: zero opens, zero schematic-PCB parity findings, zero ERC findings, 54 unchanged silk warnings; no new/worsened native pairs or new suppressions.
- Unchanged header: 11 fixed contact-edge errors, zero opens/parity/ERC.

[Single-sheet schematic](schematic-main.pdf) · [Functional-unit detail booklet](nexus-schematic-review.pdf) · [Source-bound board-level risks](../routing-wip/2026-10-15/reviews/current-gates/RECOVERY-QUALIFICATION.md)

Only the approved EN terminal branch is removed in the canonical PCB; the experimental reroute remains separate. All other parts, pin mappings and placement are retained. EN has no conductive contact after refill. This does not qualify 7.4 V power operation, regulator stability, current capacity, USB/ESD behavior or assembly. Header mechanics and pasted vias remain open. Historical CAM/BOM/CPL remain on hold. No fabrication release.

The following entries are historical records and do not override this current state.

---

# Current published experimental checkpoint: batch35, unfinished

[Batch35](../routing-wip/2026-10-15/batch35/README.md) has 33 native clearance errors, zero opens/parity, and 54 inherited silk warnings. The worst RPM/J1 gap is repaired; minimum remaining clearance is 0.0751 mm, still below 0.127 mm. Both accepted steps since batch31 have no worsened residual gap. Exact candidate, native/contact/width/gap evidence and the independent [batch31 board-level review](../routing-wip/2026-10-15/reviews/batch31/README.md) are archived. Canonical hardware PCBs and manufacturing holds remain unchanged. U10/C19 output-loop, L2 distribution and B_TX return/coupling qualification remain provisional.

## Superseded published checkpoint31 and earlier history

# Historical published experimental checkpoint: batch31

Batch31 has 37 native clearance errors, 0 opens, 0 schematic-parity findings and 54 inherited silkscreen warnings. It is preserved under [routing-wip/2026-10-15/batch31](../routing-wip/2026-10-15/batch31/README.md), with exact source, native receipts and cumulative contact/width evidence. The canonical hardware PCBs are unchanged. Four new compliant ordinary tented vias are outside pasted pads; 18 inherited pasted-via locations and all header/mechanical, USB, power and fabrication gates remain open. No manufacturing outputs were regenerated.

The candidate08 material below is superseded historical evidence, not the current best published route.

## Historical rule-transfer and routing record

# F722-rule reroute: unfinished

## Source and scope

Based on remote main `dc1ea0c324b5f4a0bb3c8e250a31acdfe5793c4c`. Only `nexus-style-fc` is changed. The source main PCB at rule transfer is SHA-256 `b467854d4e4a49959d61bdbaa088e78165129ce30ae8ab9dedf4d45c58999b5c`; header SHA-256 is `99d06c7ec685f776f357958c22f684f198f9ef5bf7e9bed437833c9d6aadfba0`. No topology, parts, pin assignments, placements, mechanical architecture, or F722 project files are changed in this first checkpoint.

## Rule transfer

- Minimum trace and clearance: 0.127 mm; preferred signal trace: 0.15 mm. Existing 0.15 mm header minima remain.
- Copper-edge minimum: 0.254 mm; main retains 0.30 mm.
- Hole-to-copper: 0.20 mm; header retains 0.25 mm. Hole-to-hole: 0.25 mm.
- Via annulus: at least 0.125 mm; drill: at least 0.20 mm. Main via: 0.45/0.20 mm; existing larger header vias are retained.
- Project rules and regeneration/routing defaults are updated. Sub-minimum neckdown/fallback settings are removed. No DRC exclusion or general clearance waiver is added.
- Fresh via-in-pasted-SMD placement is disabled by default. Ordinary tenting is not approval for filled/capped assembly.

## Native check at initial rule transfer

KiCad 10.0.7, full severity, all track errors, schematic parity; new-rule boards also refilled in isolated check copies.

| Board/state | DRC errors | Warnings | Opens | Parity |
|---|---:|---:|---:|---:|
| Main, original rules | 0 | 54 | 0 | 0 |
| Main, F722 rules | 636 | 54 | 0 | 0 |
| Header, original rules | 0 | 0 | 0 | 0 |
| Header, F722 rules | 11 | 0 | 0 | 0 |

Main rule errors are 437 clearance and 199 grouped track-width findings. Static source inventory separately finds 937 of 1,450 segments below 0.127 mm; DRC grouping is not a segment count. With matching bundled KiCad 10 libraries, main ERC has zero errors and zero warnings. Main DRC retains 54 historical silkscreen warnings: 32 overlaps, 19 over exposed copper, and 3 clipped by board edges. The earlier portable-runtime missing-library warnings were resolved by configuring the bundled libraries; no project diagnostic was suppressed.

## Open gates

1. Main copper rerouting and exact native refill/DRC/parity validation are in progress. A width-only rewrite is not acceptance. Preserve power path widths and revalidate changed return geometry.
2. All 11 header solder-contact pads have 0.150 mm edge gaps; rerouting cannot satisfy the 0.254 mm rule without a contact geometry change. Existing square 10.2 mm tabs in 10.4 by 1.8 mm capsule slots also have about 0.388 mm interference per end at the 1.6 mm board faces. Mechanical and assembly changes are not silently authorized by a routing request.
3. Existing via-in-paste requires removal or explicit manufacturing/assembly disposition. No filled/capped process has been approved.
4. USB differential geometry and return path must be validated against this board's actual stack, independently of F722. Its existing width/gap does not constitute an impedance certificate.
5. Power transitions, fault response, thermal/current capability, finite return paths and servo current are not qualified. Planned 7.4 V BEC operation at 10 A continuous/25 A peak is not an established PCB rating. Do not apply raw 6S to VX.
6. A/B/C GH pins remain Nexus GND/5V/RX/TX, different from F722 RX/TX/5V/GND. Do not interchange harnesses. U2 physical orientation and unused FSYNC pin disposition remain open.
7. Manufacturing ZIPs/BOMs are historical and on hold until stable source and all release gates pass.

This draft is a progress checkpoint, not a fabrication release or a stock-firmware/power qualification.

## Checkpoint 2: native gates and router safeguards

The first protected routing seeds were created from the exact current source,
with all 88 footprint definitions, pad/net assignments, placements, outline,
physical stack and setup preserved. Source-identified offending copper was
removed only on rollback-protected experimental copies. Exact native geometry
also identified 18 ordinary drilled vias intersecting pasted SMT lands (19 pairs);
those were removed in the experiments, not yet from the published main PCB.

A diagnostic route exposed two independent Freerouting 2.5.0 necking paths:
fixed-width retry could narrow power nets even with automatic pad neckdown off,
and the fanout stage could independently micro-neck traces. That candidate was
stopped before import/publication. Both mechanisms are now disabled in the
routing defaults; the finisher no longer falls back below 0.25 mm for new Power
class routes. Actual imported widths and power-net regressions remain gated.

The bounded four-routing-layer attempts remained congested. A separate bounded
experiment may use all six existing layers, omitting generated GND pours only
from the router exchange, with original zone definitions restored before native
refill. This is not a passed six-layer reroute, and restoring zone definitions
does not prove equivalent finite ground return paths. No experimental copper
has been accepted or published in this checkpoint.

Both original schematics now have native KiCad 10.0.7 ERC results with zero
errors and zero warnings using matching libraries. Fourteen focused regression
tests pass for the new read-only [native validator](reroute-validation.md).
Full regeneration now rejects an older native KiCad before overwriting source
and requires a failing exit status on DRC errors before export can continue.

The published PCB files retain their original hashes and remain noncompliant
with the transferred manufacturing rules. Main rerouting, header mechanics,
USB/reference-path review, power qualification and manufacturing release remain
open. Existing manufacturing files remain on hold.

## Checkpoint 3: connected local-clearance experiment

The [separate candidate 08](../routing-wip/2026-10-14/README.md) preserves the
connected original route while widening subminimum tracks and making bounded
local coordinate repairs. Native KiCad 10.0.7 refill, full-severity DRC and parity
report **361 clearance errors, 0 opens, 0 parity issues**, no new dangling copper,
and the original 54 silkscreen warnings. This reduces the widened seed's 458 clearance
errors by 97; it does not establish compliance. All 361 remaining findings are
published in the native report.

Exact footprint/pad/net, placement, outline, stack, setup and zone invariants
pass. All tracks meet 0.127 mm, all 225 vias retain 0.45/0.20 mm, and aggregate power
width floors pass. The original 18 pasted-via locations remain (19 contact pairs);
no new contact was added. Their assembly disposition is still unresolved.

A separate global-route branch reached zero geometry errors but retained 62 opens
and 51 dangling items after safe source-power restoration. It is not the selected
connected local-repair candidate and is not a completed route.

Neither experimental result is a fabrication release. The canonical PCB files
remain unchanged; header mechanics, USB/reference review, power qualification
and historical manufacturing-output holds remain open.
