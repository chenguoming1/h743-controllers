# r57 checkpoint: unfinished, 13 clearance errors

**Do not fabricate, assemble or fly.** The accepted experimental route and the separate mechanical candidate have different validation states.

## Open these exact files

- [Current experimental project](filter-integration/experimental-r57/hardware/nexus-style-fc.kicad_pro): PCB SHA256 `583e73ba08c80e70d42bfd726ef1b440ab0ddf4d7309cef266de486fd03f461f`.
- [Canonical validation](filter-integration/canonical/verification.json): unchanged PCB `925642c3…`, 627 inherited errors.
- [Current experimental native DRC](filter-integration/experimental-r57/native-drc.json), [ERC](filter-integration/experimental-r57/native-erc.json), [verification](filter-integration/experimental-r57/verification.json), and complete all-visible diagnostic in that directory.
- [Fresh schematic PDF](../../../docs/schematic-main.pdf) and [generator/library compatibility proof](filter-source/metadata-verification.json). Final schematic SHA256 `5e964b66b1bf4aa02caf87b678fc725b82ed688d0050609746a029eba928f101`.

Fresh KiCad 10.0.7 refill/save/all-track checks retain **13 clearance errors, zero opens, zero electrical/footprint-filter parity findings, ERC 0 and 54 inherited silk warnings**. The minimum residual gap is **0.0893 mm**. The all-visible copy additionally exposes **17 off-center track/via and 5 footprint-type warnings**. No new or worsened clearance pair is accepted. Accepted severity settings are unchanged; no DRC exclusion or fresh suppression was added.

## Changes since published r54

1. r55 repairs the VSYS/thermal-via gap through complete same-layer 0.250/0.350 mm VSYS/5V paths. It preserves all five ports and the thermal via. The small measured 5V reference tradeoff is explicit in [thermal-power-return-proof.json](lineage/r55-vsys-thermal/thermal-power-return-proof.json); projection percentages do not establish electrical qualification.
2. r56 moves two ordinary GND holes outside pasted pads while retaining the entire original F.Cu lands and donor contacts. Actual front/back mask and paste apertures are unchanged. Pasted-hole inventory falls from 18 vias/19 contacts to **16/17**. The [mask/paste proof](lineage/r56-offpad-ground/mask-paste-proof.json) establishes nominal separation, not fabrication tolerance or reflow qualification. Its Gerbers are diagnostic comparisons, not release CAM.
3. r57 centers the marginal RPM segment into its unchanged via. A finite 0.127 x 0.020 mm annular entry and both external ports are proved; the off-center count falls 18 to 17. The extra 0.163169 mm lies within the existing via transition. Every full-width route portion outside that transition retains GND reference, with no new plane cut.

All 96 inherited J6 shield-spoke regions, finite R20/U7/J6 plane contacts and U10/C18/C19 return checks remain proved. In1/In4 fill is unchanged by r57. These are measured geometry/connectivity results, not current/thermal/EMI/PSRR/transient certification.

## Transparent advisory review and narrow metadata repair

The [initial all-visible report](initial-all-visible-diagnostic/native-drc.json) exposes the five inherited ignored categories. Missing-courtyard and tuning-profile checks add no findings. The [complete 18-entry contact review](offcenter-contact-review/contact-review.json) distinguishes ten direct full-width entries, two donor-supported short stubs, one shorter full-width GND patch, the RPM defect now repaired, and **four unresolved 5V_BUCK entries**. Those 0.375/0.500 mm conductors enter 0.450 mm lands; current/contact adequacy remains under review. An off-center warning is not automatically a broken connection, and the absence of opens does not qualify its finite current path.

Exact selected-footprint filters for J1/L1/L2 are now bound to two Nexus-only reviewed symbols. Their pins, geometry, selected parts and all 347 physical pin/net pairs are unchanged. The generic stock libraries are not shadowed. The main-only generator override leaves design.py and imported standalone power-module parts byte-identical. BOM/CPL exports are byte-identical. Native ERC and all-visible filter parity both reach zero through consistent metadata, not suppression. The failed earlier stock-edit approach is not used.

The five footprint-type findings J1/J6/U3/L2/U14 remain visible. J6 mixes SMD contacts and plated shield features; no blind attribute flip is made. The main schematic's fresh PDF raster exactly matches the prior reviewed visual revision. The 15-page visual booklet remains that visually equivalent prior export; the source archive below is refreshed for the new library bindings.

## Mechanical implementation is a separate unfinished candidate

[Candidate02 source, dimensions and tolerance/strength screens](mechanical-candidate02/PUBLICATION-STATUS.md) are preserved for review and recovery. It is based on r54 and contains known moved-contact copper conflicts and gaps. It has not replaced canonical or accepted r57 copper. Native replay/reroute and physical fixture, fit, solder and strength tests remain open. Do not interpret a nominal fit calculation as a physical test.

## Remaining release gates

USB signal copper remains unchanged. The conditional 0.127 mm neck is excluded, and the [single C29 placement option](rejected-c29-placement-option/C29-PLACEMENT-OPTION.md) is rejected because it creates fixed-via/foreign-net/return conflicts. Complete paired routing, actual-stack impedance and protection/reference validation remain open.

Canonical remains 627 errors; the accepted unchanged header has 11 contact-edge errors. Power/current/transient/fault qualification, the remaining 16 pasted vias/17 contacts, assembly process, U2 orientation/FSYNC and connector mapping questions remain open. The 7.4 V BEC / 10 A continuous / 25 A peak goal is not a verified PCB rating. Never apply raw 6S to the FC. Manufacturing CAM/CPL remain historical/stale and manufacturing is on hold.

[Prior r54](../local-r54-checkpoint/README.md) and [prior r51](../local-r51-checkpoint/README.md) retain earlier exact evidence. Later experiments do not change this frozen snapshot.
