# Source12 complete FLASH_WP_N construction proof

This is the historical pre-import proof narrative. The later accepted candidate13 native gates are retained separately in `checks/accepted75-*`; their success does not turn this construction into stock engine insertion. The large witness file named below is excluded from the source package, with its exact hash retained in the proof projection receipt.

Native polygon proof passes against frozen candidate12, including the accepted ADC route. This receipt remains pending native add-only import, refill, DRC, process and connectivity gates. No board or source was changed. Historical candidate09 proposal and proof files remain byte-identical.

Use `source12-construction.json` for the import: three trace paths (11 segments) and two new 0.45/0.20 mm through vias. Source12 contains only U3.3 and R5.2 pads on this net, so the U3 stub and first via must both be added.

Source board SHA256: `508b5a36ed12795c4a2486b699f321f0f9867e29717175455e8fd7fc6f1f525a`.

Full exact proof: `source12-native-exact-witnesses.json`, SHA256 `15ff95c79db49ca786755b3ebbf1890dc1427f50199c9d3a77d6fccc9f88f8c1`. Detailed proposal: `source12-proposal.json`. Reproduce with `python prepare_source12_flash_completion.py`.

All segments are horizontal, vertical or 45 degrees and 0.127 mm wide. Minimum excess over the applicable native copper/edge/keepout rule:
- U3.3-pad-to-seed-via: 0.213313209 mm, 3 corners, 0.707276890 mm long
- seed-via-to-return-via: 0.522540000 mm, 3 corners, 4.106381808 mm long
- return-via-to-R5.2: 0.036000000 mm, 8 corners, 4.228620433 mm long

Both new vias were checked against every native foreign copper layer, all SMT masks without net exemptions, all drill holes, edge/NPTH contours and keepouts:
- seed-via at [31.5, 20.9853]: minimum excess 0.007854480 mm against J11.2 (foreign_copper)
- return-via at [30.21631, 24.55996]: minimum excess 0.093419601 mm against c0330d95-8045-43a8-92e9-c3e57893cb82 (foreign_copper)

Full-width endpoint entry inside conservative native inside polygons passes:
- U3.3: 0.170300 mm entry length and 0.091200 mm containment excess
- R5.2: 0.200000 mm entry length and 0.056500 mm containment excess

All self-path nonadjacent segments remain disjoint. The separate B.Cu paths remain separated; distinct-layer paths have only the intended via joins. Both new via copper/drill pairs and every nonincident via/path pair pass. Four intended joins have a full 0.127 mm transverse section within the 0.45/0.20 mm annulus, with 0.070000 mm clearance from the drill and approximately 0.0435 mm inside the outer copper edge.

Only explicitly enumerated regenerable In1/In4 GND fills were omitted from geometric collision checks. Refill and saved-ground validation are required. The 0.127 mm hard copper clearance remains unchanged; the completed lower B.Cu path has 0.163000 mm minimum copper clearance and 0.290000 mm edge clearance.
