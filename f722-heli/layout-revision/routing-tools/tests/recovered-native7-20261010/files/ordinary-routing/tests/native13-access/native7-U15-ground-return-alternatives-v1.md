# U15 ground return: bounded alternative inventory

The actual F copper of U15 GND3 and GND8 already overlaps in a 0.02002 by 0.40002 mm central strip. Board continuity does not depend on an assumed package-internal connection. Preserve these custom contours, whose copper is much larger than the nominal 0.1 mm pad-size metadata.

The complete existing 0.25 mm return is three tracks: ac132cca-ea4d-53a6-8376-a7cab37beb2b, a08299df-6002-52fd-8f9e-27b83956263e and c577b646-60c8-5101-b044-be71979ecce8. They run from GND3 through (24.5,17.83), (24.5,18.98), to GND barrel 97282ff5-d6b5-415f-a3c4-0390df70f0ea at (25.287,19.1104). Their trace length is 2.573994 mm. The latter two form the left/bottom wall beside IO4.

If actual IO4 access is blocked by that wall, first assess retaining the initial segment and replacing the two wall segments with a short 0.25 mm-or-wider branch to a legal dedicated external GND barrel. A planning seed near (24.0,18.25) would give a 1.279257 mm centerline; that point and path have not been process-validated. Exact six-layer copper, SMT mask, drill and plane checks must choose the real domain. Keep the old barrel as a plane stitch unless its removal is separately necessary and fully inventoried.

A right-side alternative can start from the already-connected GND8, but the immediate backside obstruction is U1.48 +3V3_CORE, whose B pad and mask span x25.859999–27.409999, y17.4–17.7. Restored TX-up/VX and retained ABC_EN also constrain F departure. A clear F line alone does not justify a new barrel.

Nearby existing GND barrels belong to the ADC_BEC divider, MCU decouplers, barometer and switching converter. Joining one is a separate transient-sharing assessment; it must not lengthen or narrow its original return or route TVS current through that component branch. The dedicated short-return option avoids assuming those shared paths are equivalent.

The [TI datasheet, SLVSBO7O](https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf?ts=1755070916604) identifies ground pins and shows GND-plane vias; it does not qualify this proposed return. Require full-width contacts, native clearances/refill/plane membership, affected power/VCAP and reference checks, and complete C/peer connectivity with the new return present. Shorter centerline alone does not establish lower loop inductance or ESD/AC equivalence.

All exact source hashes, pads, tracks, barrel identities, nearby owners and scope limits are in the JSON. No geometry library, router or native job was run.
