# Placement mechanical screen

The reconstructed six-layer placement passes the bounded 2D screen on board SHA `f400b279ac5d2c63251d2401c788c485400a5c8fecbb1d646e4104fd3c22c1f1`.

- All 156 component poses match `placement.json`; every orientation is orthogonal.
- The 41.66 × 25.4 mm copper-board outline is unchanged. The header geometry retains the approved nominal 47.5 × 25.4 mm assembly envelope.
- No nominal body/land overlap or courtyard overlap was found.
- No conflict was found with the stated component-body, solder-growth or header-access reserves.
- USB front-body and underside-stake keepouts are clear. The two native NPTH holes have no conflicting nearby component body/land and satisfy the explicit 0.254 mm pad-copper clearance screen.
- Body/land and bounded assembly reserves remain within the board edges, excluding the intentional overhanging headers.

`mechanical-report.json` records every gate, connector and LED/switch pose, the source hash and tight courtyard gaps. `placement-interior.png` shows both copper faces at the same board coordinates; the back face is not mirrored. The native front/back SVG exports show the complete board.

Courtyard gaps can be very small: the inherited U1–C4 gap is 0.001 mm; U8–R66 and R66–C54 are 0.005 mm. These are gaps between already-expanded footprint courtyards, not package-body gaps or a placement-tolerance guarantee. The separate bounded body/solder screen passes, but physical assembly and handling still require qualification.

## Method and limits

The read-only KiCad exporter uses native pad polygons, Fab body centerlines, courtyards, board edges and footprint keepouts. Maximum pad-polygon approximation error is 0.0001 mm. The analysis reconstructs closed Fab body polygons and checks both faces. It uses 0.15 mm SMT body reserve, 0.10 mm SMT land solder growth, 0.25 mm header-body reserve and 0.15 mm header-land solder growth. Header solder access additionally checks a 0.30 mm neighborhood around each through-hole copper land against neighboring bodies with 0.15 mm reserve and fixed neighboring lands. These are stated engineering assembly-control scenarios, not manufacturer tolerance or yield guarantees.

This is a placement screen. It does not establish completed routing, power/ground current capacity, valid protection paths, signal integrity, 3D height or cable-mating clearance, flight qualification, or readiness for fabrication. The recorded prior physical-qualification limits still apply. Native DRC and the electrical checks are separate evidence.

## Reproduction

Run `scripts/export_mechanical_geometry.py` with KiCad 10's Python and `scripts/audit_mechanical_geometry.py` with Python and Shapely 2. Matplotlib is needed only for the optional preview. From the `layout-revision` directory:

```
<kicad-python> scripts/export_mechanical_geometry.py --board hardware/f722-heli.kicad_pcb --source ../hardware/f722-heli.kicad_pcb --out checks/mechanical-geometry.json
python scripts/audit_mechanical_geometry.py --geometry checks/mechanical-geometry.json --poses placement.json --out checks/mechanical-report.json --preview checks/placement-interior.png
```

The scripts never save the board. Both board hashes were unchanged during export and after the complete screen.
