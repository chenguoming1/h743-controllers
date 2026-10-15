# r47 local routing checkpoint: unfinished, 24 clearance errors

This checkpoint follows externally merged PR36, on main `80a3f763d5031198b4622402bb73a532676b9be9`. **Do not fabricate or assemble.** Canonical source, schematic, generators, BOMs and all unrelated projects are unchanged by this checkpoint.

## Review the current experimental board

Open [r47 project](r47-u2-power/hardware/nexus-style-fc.kicad_pro). Its PCB SHA256 is `a1703af533e47f20ddc9830683b8239253c0d60be26b6eaeeb5c904fbb731cf9`. [Native receipt](r47-u2-power/native-receipt.json), [complete native findings](r47-u2-power/native-drc.json), [physical proof](r47-u2-power/geometry-verification.json), [gap audit](r47-u2-power/gap-audit.json), and [verification](r47-u2-power/verification.json) are bound to those exact saved bytes.

Native KiCad 10.0.7 refilled and saved each transaction, then checked all track errors, all configured severities and schematic parity. The final route has **24 clearance errors, zero opens, zero parity findings, and 54 unchanged silk warnings**. Minimum remaining measured gap is **0.0785 mm**. ERC remains zero for the byte-identical final schematic `49f9e0571424d0610e294bdcd6b120a42d04db284ecda9e660428fc587e62699`; its native ERC receipt is carried forward, while PCB parity was freshly checked. No new or worsened residual pair, exclusion or ignored-check change was accepted. Inherited ignored checks are not claimed passed.

## Three source-bound repairs

- r45: 29 to 26 errors. Complete R19 corridor transaction replaces twelve tracks with fifteen, relocates one existing IMU_CS via, and proves all full-width external contacts. Inherited widths and layers are retained.
- r46: 26 to 25 errors. One existing SCONF via moves 0.033716 mm with both complete donor entries. A previous incidental contact to retained B.Cu is explicitly preserved through the replacement segment.
- r47: 25 to 24 errors. One U2 sensor-power bend moves 0.0475 mm, keeping 0.250 mm copper and both external anchors. Full-width U2.5 entry remains through its unchanged anchor track.

Each immutable state includes exact source/result hashes, complete transaction and geometry/native receipts, gap comparison, rollback/pre-refill board, and audit scripts. [Lineage verification](lineage-verification.json) checks the 29→26→25→24 chain. Retained direct contacts and every replaced external port pass the transaction-specific physical proofs. The EN pin remains isolated; approved C19 remains 10uF/C19702; 18 inherited pasted-via locations remain unchanged. No new via or footprint movement is introduced in these three repairs.

## USB review and remaining electrical gates

[Source-bound USB/stack review](usb-review/USB-STACK-REVIEW.md) and [measured routing figure](usb-review/usb-geometry.png) describe the **published 29-error r43+C19 source**, SHA `10c4da72046f311a0ad61ac150091573966c8d9fae70fa93a57402a568d059c5`. Its exact saved fills are measured; the report does not validate later refill changes. It finds three USB clearance errors, asymmetric connector-orientation paths, remote protection branches, and nonuniform reference geometry. Both adjacent In2 and In4 fills are considered. In2 has uncovered mid-span projections away from USB vias; polygon membership alone does not establish finite return connectivity. The report proposes a complete-port routing study preserving both connector orientations and all external U7 bridge/pad contacts. No USB reroute is included here.

Impedance estimates are analytic seeds using the declared CAD stack, not a field-solver or manufacturer certificate. No arbitrary length/skew cap or exclusively signal-free plane is imposed. Actual production stack, mask/etch/coplanar effects, reference continuity, USB signal quality and system ESD qualification remain open.

The conditional r44 U10 loop experiment remains excluded because it improves the output loop while worsening input-reference coverage. C19's approved higher-capacitance part is retained but does not prove regulator stability or resolve loop geometry. A possible C18 relocation is only under read-only review and has not been applied.

## Unchanged canonical and manufacturing hold

Canonical still has **627 inherited errors: 428 clearance and 199 grouped width findings**, with zero opens/parity/ERC and 54 silk warnings. Header remains at **11 fixed copper-edge errors**, plus unresolved tab/slot fit. The preceding [circuit redraw/C19 checkpoint](../drafted-circuits-checkpoint/README.md) holds their exact source-bound receipts, [current schematic PDF](../../../docs/schematic-main.pdf), [15-page booklet](../../../docs/nexus-schematic-review.pdf) and source ZIP. No fresh canonical/header native run is claimed for this candidate-only publication.

Power/return/thermal/fault behavior, U10 loops, USB/ESD, header mechanics, pasted vias, connector mapping and U2 orientation/FSYNC remain qualification gates. The 7.4 V BEC / 10 A continuous / 25 A peak goal is not a verified PCB rating; never apply raw 6S to the FC. CAM/CPL remain historical/stale. Both BOMs retain the approved C19-only update, but the whole manufacturing package remains on hold. No fabrication or flight readiness is claimed.

Receipts preserve original execution paths; substitute equivalent local paths when reproducing with KiCad 10. The original sealed manifests are preserved, including their recorded session-preference files. Those files are evidence, not required project configuration. The root manifest seals all packaged bytes.
