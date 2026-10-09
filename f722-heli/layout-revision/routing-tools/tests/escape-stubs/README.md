# Candidate08 native escape-stub proposals

These are construction inputs for the next native import/refill/DRC gate. They are not accepted routes, full-net connections, or native DRC results. The frozen board and native export are read-only throughout.

- Base board: `../../candidate08/f722-heli.kicad_pcb`
- Board SHA-256: `1ff8ee645bd5fea7bbbc30cd4e5269aab76a2032efe3e2c4e77a0becd85e9edf`
- Native export SHA-256: `20404782e5d29f18d73e77955524109c6cb86961fc112b890857e54e06e0608a`
- Construction input: `native-escape-stubs-proposals.json`, field `proposals`
- Complete proof: `native-escape-stubs-exact-witnesses.json`, hash-bound by the construction input

| Pad | Layer | Track segments / length | Through-via center | Minimum track excess | Minimum via excess |
|---|---|---|---|---|---|
| R44.1 | F.Cu | 6 / 2.927899872 mm | (25.38059, 14.57554) | 0.037330512 mm | 0.056152010 mm |
| U3.3 | B.Cu | 2 / 0.707276890 mm | (31.5, 20.9853) | 0.213313209 mm | 0.007854480 mm |

Every segment is horizontal, vertical, or 45 degrees. Both first segments lie wholly inside the actual native pad's inside polygon with their full 0.127 mm width. R44.1 retains the prior candidate06 engine-tested via witness. U3.3 uses a much closer local witness, refined within the small native legal region; it has not received an engine check. Its limiting constraints are the two front-face J11 pads and its own back-face SMT mask, so retain the exact stated coordinates for the native check.

The complete proof records an exact Euclidean point-pair witness for every segment-to-obstacle distance and all via-to-obstacle distances, including layer, source UUID/net, required reserve, actual physical gap, excess gap, and result. There are 724 trace obstacle checks per R44.1 segment, 838 per U3.3 segment, and 3,366 individual layer/mask/drill/outline via checks per proposal. No net exception is used for SMT masks or drills. All distances exceed the rules by more than the native export's 0.00001 mm stated polygon error. Interproposal copper and drill separation also pass.

Rules: 0.127 mm trace width; 0.45/0.20 mm through via; 0.127 mm foreign copper clearance; 0.20 mm via drill-to-SMT-mask gap on both faces; 0.25 mm hole-to-hole gap; 0.254 mm copper-to-board-edge/NPTH gap. Only the two named regenerable GND zone fills on In1.Cu/In4.Cu are excluded. Fixed copper on every layer, non-GND fills, keepouts, masks, and holes are retained.

Discovery used bounded local obstacle geometry and a small elbow enumeration around R44.2, plus a bounded refinement inside U3.3's existing nearby legal-via region. The final script performs only source validation and exact distance checks; it does not run a solver, build global free space, change board/model data, or invoke a JVM. Exploratory SVG/WKT and candidate files are diagnostics, not construction inputs.

To regenerate the two construction proposals and receipts:

```sh
python tests/escape-stubs/prepare_escape_stubs.py
```

Run from `ordinary-routing`. The script verifies the frozen source hashes before and after work. Native import, refill and DRC remain required, including confirmation that these stubs add no clearance violations and actually connect to their intended pad and via.
