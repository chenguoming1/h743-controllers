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
