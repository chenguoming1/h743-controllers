# Final main/child joint binding: stage32

Result: the selected joint geometry and nominal mesh fit pass on the coherent final main-placement snapshot. This closes the hash/model-binding and assembly-courtyard integration checks, not manufacturing, strength, fatigue, or flight qualification.

## Bound sources

- Main PCB: `f214f8141e8f21a7e0983c8eb4f2be89634e3b69d0d2b168a1ac3153f28a83de`
- Child PCB: `b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6`
- Child VRML: `fae6c66ed62270d7096f0ce6272e00ce853ec379e43c03f58bf43e89370c61cc`

All three are from the stage32 hardware tree. The actual main-relative model reference resolves to that same checked VRML. Files were hashed before and after the independent read-only check; no board/model file was changed.

## Checks and measured nominal gaps

- Exact 16 main J1 edge geometries implement 9.8 × 2.10 mm R0.50 slots. Exact 17 child lower-contour segments implement the selected 9.3 mm tabs/root reliefs.
- J1 pose, pads, pin/net assignments, model transform, both assembly courtyards, main body/thickness and original track/via slot keepouts remain unchanged. The keepouts permit copper pour; they are not a universal copper setback proof.
- All 11 child contact rectangles match the selected contract. Their X positions, widths and pin/net/face identities are preserved. The standard servo-header placement/pinout and child body are preserved.
- Actual exported mesh: 24 meshes, 11,136 faces, 1,046 polygons intersecting the parent slab. Zero slot interference; minimum nominal true-rounded-slot clearance 0.13749995 mm.
- Front-side component courtyard bounding boxes have no projected overlap with the nominal child/header envelopes. Nearest is U10: 0.450006 mm to the header envelope. Its actual revised courtyard begins at main-local Y5.05, 0.05 mm beyond J1's unchanged courtyard. U11/U12 remain 0.500006 mm from the nominal header envelope.
- No backside component courtyard overlaps J1's unchanged assembly courtyard. Closest are C21 at 0.07 mm and C22/C23 at 0.09 mm. This preserves the project's existing soldering/rework reservation; no new universal tool-access standard is asserted.
- U10 remains at native (109.4,107.05), zero-degree front pose. Its revised lands are 0.60 × 1.10 mm centered at Y±1.30; the courtyard extent Y±2.00 gives 0.15 mm beyond those land ends. This check records the implemented dense-land margin faithfully; component land-pattern/process qualification belongs to the placement/manufacturer audit.
- Read the main owner's stage32 KiCad 10.0.7 report: 0 errors, 0 unconnected items, 0 schematic-parity items, 58 warnings. The active main CAD edge rule is 0.30 mm. These are the owner's native results, independently read here; no second heavy/native run was performed.

## Limits that remain open

The selected PCB-only joint still requires actual finished-profile matched-pair acceptance or qualified tighter process control. Ordinary published routing/thickness tolerances do not guarantee universal insertion or limited play. The nominal 0.254 mm child-tip CAD clearance does not establish a minimum finished copper setback; no lower finished clearance floor is adopted. Full finished thickness, copper/outline registration, burr/bow, mask/finish, insertion force, solder wetting/fillets, load/temperature, connector/cable strain, vibration/shock and thermal cycling require qualification.

Courtyard screening uses conservative planar nominal envelopes. It does not certify all component 3D shapes, mated servo plugs/harness access, enclosure tolerances or service clearances. Retain the source-bound proof and repeat it after any PCB, model, pose or footprint change.

Evidence: `pcb-only-candidate/final-stage32-joint-proof.json`; tolerance/geometry specification: `pcb-only-candidate/geometry-contract.json`; design and process comparison: `PCB_ONLY_PROPOSAL.md`.
