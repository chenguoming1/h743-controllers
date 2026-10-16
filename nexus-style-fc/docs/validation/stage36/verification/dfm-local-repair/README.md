# Stage36 local manufacturing and identity verification

**PASS** on saved PCB `bed37199e8d62b8135a27b9e182f8e8f584f1a9fb722cb6efb5d4c87b2a320b8` and the confirmed-complete fresh export. Both Gerber proof files bind identical hashes for all 16 manufacturing files.

## SW repair and sensor dead leaf

The exact 0.25 mm SW path is preserved, with a **0.235 mm** full-path gap to the identical U5.3 copper/mask/paste oval. The old direct diagonal is absent. All four front dead-leaf strokes, its bottom branch, six-layer via flashes and plated drill remain absent. Exact native SW_5V and 3V3_SENS track/via/pad identities match accepted stage35, preserving all four SW pad and 15 sensor-pad contacts and conductive graphs.

## New ADC vias

Both new through vias are 0.45 mm copper / 0.20 mm drill, giving a 0.125 mm nominal radial annulus. Native board-inherited tenting is enabled on both sides, and the actual four mask/paste files independently contain no opening over either via center, drill or annulus. Every one of their **696 plotted apertures** was checked against each full 0.45 mm disk, including exact rounded-corner geometry.

| Via | Board coordinate (mm) | Front mask/paste minimum outer-edge gap | Bottom mask/paste minimum outer-edge gap |
|---|---|---:|---:|
| VX_SENSE | (112.45,118.66) | 0.785000 mm | 0.144711458 mm to U1.11 |
| GND | (111.775,119.6) | 0.240000 mm to C29.2 | 0.127366733 mm to C12.1 |

C12.1 is the OSC_OUT pad at `(112.35,120.02)`. Its rounded mask/paste aperture has a 0.252366733 mm gap to the GND via's drill edge and a 0.127366733 mm gap to the outer copper annulus. There is no nominal overlap. Matching copper flashes on all six layers and actual PTH drill hits verify both via dimensions and locations. Tenting is not a filled/capped barrel or a guarantee of fabricated mask registration; this is the nominal export-geometry result.

## USB and native receipt

All 102 USB track/arc/via items, four tapers and ten pad identities/contacts exactly match stage35. Native partner recognition remains USB_DP ↔ USB_DN (codes 22/23). Stage36 saved reference-fill projections were not recomputed; the stage35 report retains its stated signal-integrity scope rather than being presented as a new stage36 field/return analysis.

The existing stage36 native receipt reads 0 errors, 0 opens, 0 parity issues and 61 warnings. No new DRC was run here. The export owner confirms exit 0 and 48 BOM groups/83 placements; source and all manufacturing hashes stayed unchanged through verification.

## Proofs

- `gerber-proof.json` and `verify_gerber_proof.py`: exact SW aperture/stroke/gap and old branch/via/drill absence.
- `via-aperture-proof.json` and `.py`: native via identities, full-aperture analytic distances, exact geometry/line evidence, copper/drill confirmation and every tested gap.
- `saved-identity-proof.json` and `verify_saved_identities.py`: native USB/SW/sensor copper and pad identity/contact preservation.
- `final-verification-summary.json` and `SHA256SUMS.txt`: bound final results and evidence hashes.

No board, rule, source or manufacturing file was edited; no native save, refill, DRC, export or external upload was performed. This does not assert new JLC/assembler acceptance or fabrication/flight release.
