# r54 routing checkpoint: unfinished, 14 clearance errors

This checkpoint extends PR37 from main `80a3f763d5031198b4622402bb73a532676b9be9`. **Do not fabricate or assemble.** Canonical PCB, schematic, generators, BOMs and all unrelated files remain unchanged.

## Exact current experimental board

Open [r54 project](r54-crx-ground/hardware/nexus-style-fc.kicad_pro). PCB SHA256: `5677fb38db7d7e19cd3afa9dd5da61bbd9932ed0be7f6f2899f7bf4bf58e8fc9`.
[Native findings](r54-crx-ground/native-drc.json), [verification](r54-crx-ground/verification.json), [geometry proof](r54-crx-ground/geometry-verification.json), and [gap audit](r54-crx-ground/gap-audit.json) bind the exact saved bytes.

Native KiCad 10.0.7 refill/save/all-track DRC gives **14 clearance errors, zero opens, zero schematic-parity findings, 54 inherited silk warnings**, with minimum residual gap **0.0893 mm**. No new or worsened native pair was accepted. The unchanged schematic `49f9e057…` retains its exact zero-ERC receipt; parity was checked freshly. No fresh ERC run is claimed for these copper-only changes. Inherited ignored checks remain visible and are not claimed passed.

## Three complete donor transactions

[Lineage verification](lineage-verification.json) binds the published 18-error metadata r51 source to these immutable states:

- **r52: 18 → 16.** Complete DSM_DATA bypass between existing vias, with all six original physical ports retained. No new or moved vias and no power edits. In1/In4 main fills are exactly unchanged. The new B.Cu path has continuous full-width In4 reference outside its two existing via antipads.
- **r53: 16 → 15.** CC2 remains 0.127 mm F.Cu with fixed endpoints and all three original ports. A new bend at (110.4,132.725) clears the J6 shield. Main In1/In4 fill geometry remains exact; actual shield/return contacts pass.
- **r54: 15 → 14.** C_RX's existing via moves 0.015 mm west and 0.010 mm south with its complete two-layer donors. The adjacent two-track B.Cu GND bend moves 0.080 mm west while retaining all original ports and 0.127 mm width. Its length changes 0.604395 → 0.687880 mm. The retained routed path, rather than an assumed nearby stitch, connects both external ports to the same actual local via and finite In1/In4 GND contacts. Antipad changes are local, with no main-plane split.

Each state retains exact transactions, rollback/pre-refill boards, native receipts, full-width contacts and gap comparisons. The final r54 check re-proves all **96 inherited J6 shield-spoke regions**, finite R20/U7/J6 plane contacts, and the unchanged full-width U10 output-reference projection. These are geometry/connectivity proofs, not high-frequency, thermal or transient certification. All original widths/layers are preserved in these accepted transactions.

USB signal copper is unchanged. A separate proposed 0.127 mm USB neck is **not included or adopted**. Complete paired routing with appropriate actual-stack reference, connector/protection topology and minimal stubs remains under review. No arbitrary length/skew cap or exclusively signal-free-plane requirement is imposed.

## Pasted-via process review

The accompanying [read-only manufacturing review](pasted-via-review/README.md) classifies all **18 inherited vias / 19 pasted-pad contacts** and their complete local donor paths. It is bound to its stated r53 source and carries a current-source applicability check. No via relocation, paste/mask edit, footprint change or new fabrication process is implemented here.

Only one listed via is on an exposed thermal pad: U5 TPS62130 GND. It also connects U5.6, opposite-side C15.2 and six tracks; it cannot be treated as disposable stitching. Connector/ESD vias can also carry opposite-side capacitor returns. The review distinguishes routing-only possibilities from thermal/return constraints and records bounded failed U5 alternatives without claiming global impossibility.

**Filled/capped processing is not universally required by TI.** TI permits appropriately filled, plugged or tented thermal vias. The current continuous U5 mask/paste opening plus a global tenting setting does not establish a component-side mask island over the drill. A concrete pad-specific mask/paste/process design and assembly qualification may be needed; no such change is silently assumed. Nominal geometric overlap is separate from actual paste loss, voiding, solder joint strength and process acceptance.

## Canonical and remaining release gates

Canonical remains the metadata-consistent PCB `925642c3…`, with **627 inherited errors**, zero opens/parity/ERC and 54 silk warnings. Header remains **11 fixed edge errors**, plus unresolved mechanical fit. [Prior r51 checkpoint](../local-r51-checkpoint/README.md) preserves the exact canonical receipts, U10 decision, export-equality proof and read-only header fit study. Header redesign is not included here.

The accepted U10 output improvement and approved C19/EN corrections remain. Input transient/ripple/PSRR, regulator effective capacitance, actual USB stack/SI/ESD, power/thermal/fault behavior, connector mapping and U2 orientation/FSYNC remain qualification gates. The 7.4 V BEC / 10 A continuous / 25 A peak goal is not a verified PCB rating; never apply raw 6S to the FC. CAM/CPL remain historical/stale and the manufacturing package remains on hold. No fabrication or flight readiness is claimed.

The [current schematic PDF](../../../docs/schematic-main.pdf), [15-page detail booklet](../../../docs/nexus-schematic-review.pdf) and source ZIP remain unchanged. Historical checkpoint observations do not supersede this status. Absolute execution paths in receipts may be mapped to equivalent local paths when reproducing with KiCad 10.
