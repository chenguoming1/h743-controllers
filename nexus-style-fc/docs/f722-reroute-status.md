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
