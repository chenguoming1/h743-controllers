# Connected schematic and approved EN correction: unfinished checkpoint 06

This checkpoint is based on latest main `866afe8f44523b0c8f3dc4360f83fdee599c77c9`, preserving its standalone power-module addition and shared generator compatibility changes. It follows merged PR34. **Do not fabricate or assemble these boards.**

## Open the correct files

- Main project: `nexus-style-fc/hardware/nexus-style-fc.kicad_pro`. Its canonical PCB receives only the approved U10 EN isolation and matching Description metadata; native refill/save is included. It retains **627 errors: 428 clearance and 199 grouped width findings**.
- Current review route: [experimental-en/hardware/nexus-style-fc.kicad_pro](experimental-en/hardware/nexus-style-fc.kicad_pro). This is the published batch35 route plus the same EN correction, with **32 clearance errors**. It is an experimental candidate, not the canonical PCB.
- [Readable single-sheet PDF](../../../docs/schematic-main.pdf) and [15-page functional-unit review PDF](../../../docs/nexus-schematic-review.pdf). The schematic source is identical in both main-board states.
- [Exact state summary](final-summary.json), and each state’s `integrated-verification.json`, `native-drc.json`, `native-erc.json`, physical contact proof, transaction and command receipts.

## Checks on the final integrated source

Native KiCad 10.0.7 refilled and saved both boards, then full-severity DRC checked all track errors and schematic parity. Both have **zero opens, zero parity findings, zero ERC findings, and the same 54 inherited silk warnings**. All remaining errors are visible; the DRC command correctly exits with violations. No new ignored check or exclusion was added. Minimum remaining clearance is 0.0898 mm canonical / 0.0751 mm experimental, below the 0.127 mm requirement.

The schematic now physically wires related components inside functional units. All 347 pin/reference mappings and 91 symbol identities are checked; the sole electrical change is U10.3 from VSYS to an explicit no-connect net. The six stock symbol definitions are pinned to their exact latest-main versions, including electrical and power attributes. Deterministic generation, ERC and visual panel checks pass. Main-only layout and pinned-symbol hooks leave other design modules on their previous loader path.

For each PCB, the EN correction removes exactly ten VSYS terminal tracks and isolates only U10.3. U10 IN and every other VSYS branch remain. All retained copper definitions, parts, pad geometry, placement, stack, outline and zone definitions remain exact. All 2,542 canonical / 2,626 experimental retained direct contacts survive. Full-width source-via entries are proven; EN has no contact to tracks, pads, vias or stored/independently refilled zones. The exact U10 Description field is synchronized for parity. No part or placement change is included.

## Unfinished qualification

The unchanged header has 11 contact-pad edge errors, zero opens/parity/ERC and no other findings. Its square tabs still interfere with capsule slots. The [read-only contact/mechanical remedy](../reviews/current-gates/header-contact-remedy-readonly.md) documents why copper recession alone cannot fix fit; no pad or mechanical redesign is applied.

The [source-bound board-level review](../reviews/current-gates/RECOVERY-QUALIFICATION.md) records U10 input/output capacitor-loop geometry, thinner inner-layer power cross-sections and USB/shield return risks. EN isolation addresses the confirmed enable-voltage error only. Regulator effective capacitance/stability, power/return paths, current/thermal/fault behavior, USB impedance against the actual stack, and ESD behavior remain unqualified. Planned 7.4 V BEC / 10 A continuous / 25 A peak is not a PCB rating. Never apply raw 6S to the FC.

Four previously added ordinary tented vias remain outside pasted pads; 18 inherited pasted-via locations still require disposition. Connector pin-order differences and U2 orientation/FSYNC remain unresolved. No manufacturing output was regenerated; existing CAM/BOM/CPL are historical and on hold.

## Provenance and recovery

The exact published batch35 route is the durable routing baseline. Unpublished later experiments were lost during a runtime replacement and are not claimed as recovered or validated here. The approved EN transaction and readable schematic were reconstructed from exact surviving source/evidence, then validated freshly. Archived batch35 and earlier snapshots remain unchanged. The checked header copy is evidence only; canonical header bytes are unchanged.

`evidence-manifest.json` seals every file in this checkpoint. Original baseline boards remain available in main `866afe8` and the immutable batch35 directory. Audit scripts preserve their original execution paths in receipts; use equivalent local paths when reproducing, and always use native KiCad 10. Native DRC is intentionally failing until the listed errors and qualification gates are closed.
