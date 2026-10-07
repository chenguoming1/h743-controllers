# Current routing revision

2026-10-07. Based on the user’s tidy commit `0da807d0`, in main `80352d0`. All requested VSYS, USB-rule and remaining-route cleanup is included. The routing and rules are freshly verified; the hashes below identify this revision.

## Verified result

Native KiCad **10.0.6**, after zone refill: **0 DRC violations / 0 open connections / 0 schematic-parity issues / 0 ERC violations**. All eight negative-regression tests detect their intended errors.

- PCB SHA-256: `349fbe54c6d95591bcbd5b6ae21f348d2a8d77a581d6df7f8176709179ab2ae4`
- Schematic SHA-256: `05f4de7b7ed008e723326027f1ecba670f42c9393f092da6f227d43a34177346`
- 41 routed nets, 688 tracks, 104 vias, 311 pads, 60 footprints, 56 resolved model references
- Original user input had 703 tracks / 105 vias. One obsolete VSYS via was intentionally removed; no USB or ground-return via was moved or removed
- [Current evidence](evidence/routing-cleanup-20261007/verification-summary.json)

## VSYS

The four B.Cu VSYS regions and local capacitor connections remain. Their inner bridges are now deliberately sized and simpler:

| Connection | Previous | Current |
|---|---|---|
| Source OUT/C2 to central region | 5.411 mm at 0.40 mm | 6.155 mm at 0.60 mm |
| Central region to VIN/C4 | Parallel 16.977 mm at 0.40 mm and 10.548 mm at 0.40/0.30 mm | 7.789 mm at 0.80 mm |
| VINA branch | 3.416 mm at 0.40 mm | 3.416 mm at 0.60 mm |

Inner VSYS routing decreases from **32.936 to 17.360 mm**. The retired VSYS via at (112.5,109.0) was removed with its unused loop. Intentional 0.20 mm control branches, 0.23 mm pour-backed VIN escape, switching paths and local decoupling are preserved. The former loop was replaced by wider, lower-resistance copper, rather than simply deleted for appearance.

[Actual VSYS before/after copper](renders/vsys-before-after.png)

The prior comparative DC screen for these same route coordinates estimated approximately **41 → 28 mΩ** source-to-VIN resistance (~32% lower), or **26.4 → 18.1 mV** at a 0.65 A screen. That estimate used 35 µm outer / 15.2 µm inner copper and assumed 20 µm via plating. It is a prior estimate, not a newly rerun resistor mesh or a thermal/transient rating. Fresh verification here proves the route coordinates, widths, connections, native clearances and preservation.

`VSYS_POWER` defaults to 0.60 mm. Explicit minimum rules enforce 0.20 mm on outer/control tracks, 0.60 mm on In2/In3, and 0.80 mm on the `VSYS VIN bridge` group. Keep/reassess named group membership when editing its route. Test narrowing to 0.40/0.60 mm correctly raises source/VIN width errors.

## Remaining routes

All **41 routed nets** were checked against fresh schematic connectivity and filled copper. Four redundant fragments were removed: two exact collinear merges and two fully contained remnants, on 3V3 and LED_R_A. Integer-nanometre interval/capsule proofs establish unchanged copper coverage. Segment count decreases **692 → 688** in this pass; short segments below 0.20 mm decrease **76 → 73**. Remaining short segments preserve real corners, via/pad/branch anchors or width transitions.

Two F.Cu VBUS charger-input tracks totaling **2.211 mm** widen **0.15 → 0.30 mm**, with unchanged endpoints and centerlines. Only that feed gains track copper (~0.372 mm²); its nearby F.Cu ground-clearance shape changes (~0.111 mm²). The other filled-zone unions, including In1/In4 ground references and In2 3V3, remain unchanged. The 3V3 plane remains one island connected to all 20 supply vias.

[Actual VBUS before/after copper](renders/vbus-before-after.png)

The local VBUS trace-resistance screen improves approximately **7.26 → 3.63 mΩ**, about **1.82 mV** at 0.5 A. This is a modest consistency/margin improvement, not evidence that the original route failed. A targeted 0.30 mm minimum applies to `VBUS charger input bridge`; a deliberately narrowed test copy fails it. Low-current pull-up/indicator branches remain narrower.

[All-net width decisions](ALL_NET_WIDTH_REVIEW.md) document BAT+ divider routing, plane-backed 3V3 connections, GNSS supply traces, converter pad escapes, signal widths and ground-return exceptions. No blanket width normalization was applied.

## USB safeguards

The logical pairs use recognized suffixes: `/USB_D_CONN_P` / `/USB_D_CONN_N` and `/USB_D_P` / `/USB_D_N`. All 71 physical USB segments, four signal vias, pad positions and ground returns remain unchanged. RF geometry, footprints and models are also preserved.

Rules enforce 0.135 mm width, the nominal 0.145–0.155 mm coupled-gap band, an independent 0.145 mm pair-clearance floor, scoped skew and regional uncoupled budgets. Existing breakouts have finite local allowances. Five fresh negative tests detect undersized width, excessive gap, insufficient gap, excessive skew and excessive uncoupling, with zero open connections in those copies.

KiCad gates maximum-gap reports through applicable uncoupled budgets. The regional limits are regression safeguards, not point-by-point impedance certification. [Exact rule scopes and limits](USB_DIFFERENTIAL_RULES.md).

Fresh path measurements retain **0.030636 mm** ESD-output-to-MCU mismatch and complete orientation mismatches **2.079364 mm (A)** / **0.030636 mm (B)**. These are separately audited through-path quantities, not KiCad branched-net skew. They exclude component interiors and equal via-barrel contributions. USB reference-plane samples remain covered away from intentional local signal-via antipads.

## Scope and history

The inherited ignored native categories remain unchanged: missing courtyard, via endpoint centering, tuning-profile geometry, footprint-filter mismatch and footprint-type mismatch. Clearance, connectivity and schematic parity remain enabled. Exact geometry and eight intentional negative tests supplement native checks.

The schematic PDF is regenerated from current source. Older review PDFs, generic renders and earlier evidence remain historical at their recorded hashes; this file and `evidence/routing-cleanup-20261007/` identify the current result. Fabrication, battery/harness, supplier/assembly, startup/transient/thermal, USB/ESD, GNSS/RF and firmware qualifications remain open. This is not a manufacturing or battery-connection release.

Sources: [TI BQ24074](https://www.ti.com/lit/ds/symlink/bq24074.pdf), [TI TPS63031](https://www.ti.com/lit/ds/symlink/tps63031.pdf), [u-blox MIA-M10Q integration manual](https://content.u-blox.com/sites/default/files/documents/MIA-M10Q_IntegrationManual_UBX-21028173.pdf), [KiCad10 PCB manual](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html).
