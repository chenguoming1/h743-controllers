# Release blockers

**Do not fabricate, purchase as a qualified assembly, or fly this design.**

## Recorded native checks

The supplied primary checkpoint was checked with KiCad 10.0.6. Its saved unsuppressed DRC report contains 31 unconnected items and 70 warnings: 28 dangling tracks, 22 dangling vias, 7 tracks not centered on vias, 7 silkscreen edge-clearance warnings, 4 silkscreen-over-copper warnings and 2 silkscreen overlaps. There are zero geometric errors in that recorded run. This is not a clean DRC pass.

The canonical nine-sheet source has zero reported ERC violations. The physical-wire graph audit passes, and the pin-map audit records 29 matching stock Rotorflight target resources. These checks do not demonstrate board connectivity or actual firmware/hardware operation.

## Work remaining

1. Complete the 31 unfinished connections and inspect all dangling copper. Rerun native refill and unsuppressed DRC/ERC on the exact final source and PCB.
2. Independently verify PCB-to-schematic pin/net/part parity, circuit operation, package mapping and every changed signal/return path.
3. Recheck power voltage/drop/current, startup, USB isolation, simultaneous loads, ground returns and thermal margins on the final exact copper. Prior scoped calculations are not hardware qualification.
4. Verify maximum package/connector envelopes, connector mating access, all 21 header pins/tails/solder fillets, USB clearance and fabrication/assembly tolerances. Full connector maximum depth/height evidence remains incomplete.
5. Regenerate and reconcile Gerbers, drill, procurement BOM and CPL only after the design is fully checked. Proposed LCSC/manufacturer selections are not live stock guarantees or purchase authorization.
6. Perform first-article electrical, thermal, USB, sensor orientation, receiver, output and failsafe testing with motors disconnected before considering flight evaluation.

The Infineon DPS368XTSA1 substitution and TPS2117/C75 source updates are present in this primary snapshot. Source evidence is included; physical compatibility and behavior still require testing.

The unaccepted experimental layout is not part of this PR and must not be substituted for the primary PCB without separate review.
