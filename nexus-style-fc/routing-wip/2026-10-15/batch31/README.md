# Batch31: unfinished routing checkpoint

Native KiCad 10.0.7: **37 clearance errors, 0 opens, 0 schematic-parity findings, 54 inherited silkscreen warnings**. All 37 errors remain visible in native-drc.json. This is an experimental review candidate, not a canonical PCB selection or fabrication release.

The exact filled PCB is hardware/nexus-style-fc.kicad_pcb. Its SHA-256 is 47b6cf94fb2213c0ae46ab692fd9b8f71e90c2c278944827f9156daa25e8e23b. The copied project, rules and schematic are included. Original hardware/ PCBs elsewhere in the project remain unchanged.

## What changed

The 937 original undersized segments were raised to the 0.127 mm floor, followed by bounded coordinate repairs and complete width-preserving local replacements. This checkpoint reduces the connected widened seed's 458 clearance errors to 37. There are four added 0.450/0.200 mm ordinary tented vias, all wholly outside paste-bearing pads. Eighteen inherited pasted-via locations remain and are not qualified as filled/capped vias.

Cumulative comparison with candidate16 (122 errors) verifies unchanged footprints, pads, nets, placements, stack, outline and zone definitions; unchanged retained original track widths/layers/nets/locks and via drills; zero missing contacts between retained original objects. Of 2,565 baseline direct-contact pairs, 2,467 remain direct and 98 were replaced by documented complete paths. The final graph has 2,637 pairs. Every accepted transaction has native connectivity and independent pad/via/external-port checks. Exact records are in cumulative-audit.json, verification.json and lineage-evidence.json. Contact counts and preserved widths do not establish current capacity or equivalent ground-return performance.

## Reproducing native checks

Make a disposable full copy of nexus-style-fc/hardware from this PR, including its library and header-board directories. Overlay this checkpoint's four hardware files into that copy, retaining their exact filenames. Use KiCad 10.0.7 or a compatible newer native KiCad with matching global libraries. Refill zones, save, then run full native DRC with schematic parity, all track errors and all severities. The recorded native receipt describes the exact saved board above. Do not run project regeneration scripts on this candidate: they rebuild source and are not a routing replay.

The schematic is unchanged from the prior zero-error/zero-warning native ERC source. This checkpoint does not claim a fresh hardware current, thermal, signal-integrity or manufacturing validation. No CAM, BOM or CPL was regenerated; historical outputs remain stale/on hold.

## Remaining gates

- Resolve the 37 main clearance errors without relaxing rules or creating opens.
- Resolve the 11 fixed header contact-edge errors through an explicitly approved contact/mechanical design. Existing square tab/capsule-slot interference remains.
- Disposition the 18 inherited pasted-via locations; ordinary tenting does not provide a filled/capped assembly process.
- Validate USB differential impedance and return path against the actual stack; qualify changed signal/power/ground paths, thermal/current capability and protection/reference integrity.
- Preserve the documented Nexus versus F722 connector-pinout difference and unresolved U2 FSYNC/orientation issue. Raw 6S must never be connected to the FC input. The planned 7.4 V, 10 A continuous/25 A peak BEC is not a verified PCB rating.

The earlier attempt08 checkpoint is retained only as superseded historical evidence.
