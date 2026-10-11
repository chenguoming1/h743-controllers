# Fixed-pose U15 IO4 paired source plan

This package prepares the exact native7 RX channel reassignment from U15 IO1/pad1 plus NC10 to IO4/pad5 plus NC6. It contains a source plan and host-only validators. It does not contain a native constructor or a complete routed candidate. The current route is unselected and its feasibility remains unproved.

Source board SHA256 is `a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f`; native export SHA256 is `53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505`. All 61 paired hardware files are checked against the published native7 checkpoint manifest before a plan is derived. Native JSON is read as data; no polygon processing is performed.

## Exact electrical and schematic change

U15 stays at F(25.5,17.6), 0 degrees with footprint UUID `080c5130-0255-45f4-aa7a-ed717f456528`, the same TPD4E05U06DQAR part, all ten physical pad numbers/UUIDs and all geometry. Every footprint pose remains fixed, including original C12 and R3.

| Physical pad | Before | Proposed semantic net |
|---|---|---|
| U15.1, actual IO1 | PORT_C_RX_EXT | unconnected-(U15-IO1-Pad1) |
| U15.10, manufacturer NC | PORT_C_RX_EXT | unconnected-(U15-NC10-Pad10) |
| U15.5, actual IO4 | unconnected-(U15-IO4-Pad5) | PORT_C_RX_EXT |
| U15.6, manufacturer NC | unconnected-(U15-NC6-Pad6) | PORT_C_RX_EXT |

Pad5 is at (25.0825,18.6), pad6 at (25.9175,18.6). Pad1/10 retain their physical positions. TX IO2/NC9, custom GND pads3/8, connector pins, series resistors and MCU pins are fixed. The old IO4/NC6 unused nets each contain only their own pad. Their names are retired; their old numeric codes are not transplanted onto another pin as identity.

The exact in-memory schematic recipe moves existing RX wire/label objects from pin1 to pin5 and from pin10 to pin6, and moves the corresponding unused marks from pin5 to pin1 and pin6 to pin10. All six object UUIDs are retained. The plan contains their complete before/after expressions. A new `TPD4E05U06_RoutePads_NC6_NC9` symbol is appended to the local and embedded libraries. It clones the current NC9_NC10 variant, changing only symbol/nested names, pin6 `no_connect` to `passive` and pin10 `passive` to `no_connect`. IO1 remains a real passive I/O with an explicit no-connect mark. Only U15's instance lib_id changes. Existing variants, other symbols and all remaining syntax are checked independently by reversing the six moves and removing only the new variant, then comparing the full source syntax.

The source netlist is checkpoint `evidence/paired.net`, not the older canonical reconstructed.net. The predicted semantic export keeps 156 components, 127 named nets and 506 assigned nodes. Full ref/pin/net/pinfunction/pintype/class and component/libpart expectations are derived from the exact XML source and hashed. The plan embeds the affected net rows, while the source-derived validator compares every row. Numeric XML/PCB codes are not assumed equal between exports: a future constructor must publish its complete bijective net-name/code map. Duplicate XML codes and native name/code aliases fail.

## Physical cut and group obligations

Both current 18-case and 22-case contracts require exactly `published-06.clamp: U15.1 -> U15.5`; every other check field and row is preserved. TX `published-07` remains U15.2. Candidate board/native hashes in the new contract templates are explicitly unbound. They cannot be used as accepted results. The 18 cases still contain 14 actual-clamp cases and four U14 NC cases; the actual-I/O inventory remains 22 cases across 20 active channels. The unused bonded set changes from `{U13.4,U15.4,U15.5}` to `{U13.4,U15.1,U15.4}`.

RX's complete external group is J11.1/U15.6/U15.5/R34.1, with R34.2/U1.28 separately on the MCU side. Old RX group membership of U15.1/10 is retired through those two explicit terminal substitutions. A blind historical-group failure must be preserved as expected under the declared change; it must not force the newly unused pads back onto RX. Every unchanged original physical terminal and complete group still requires preservation/restoration.

NC6 is an upstream PCB land with no internal channel connection. Both RX branches need actual full-width positive-area copper contact at IO4. Removing actual IO4 copper from the final complete native graph must disconnect J11.1 from R34.1 with at least 0.127 mm outside-pad separation. NC6 must remain upstream; old1/10 must have no residual RX contact. Neither NC cuts, implicit internal bonds, pair-only reachability nor a same-net bypass can satisfy the actual-clamp requirement.

`native7-U15-IO4-copper-scope-v1.json` records the exact current source inventory: 90 common cuts minus 26 add-backs (19 TX, 5 VX, 2 R3) plus four old RX-prefix cuts = 68 removals. Every selected full native record was compared to the exact native7 source before the compact hash inventory was created. The origin is C's `native7-RX-IO4-access-v2.json`, SHA256 `858be4d3e355637a7a1931b190578674b3f1dfa39998583f0f149c251c234120`; its bulky contours are unnecessary for revalidating this compact source-record set. That trial stopped before routing on a proposed U2.9 GND tail conflict with restored R3. A replacement proposed tail is separate routing work. This plan includes no new copper recipes and authorizes no removal. Later inventory changes require a newly reviewed exact scope, never count-only permission.

## Running the source checks

Run from the workspace root that contains `repo/`, `recovered-native7/` and `ordinary-routing/`:

```sh
python recovered-native7/recovery-importer/prepare_native7_u15_io4_pair_v1.py --root . --check recovered-native7/recovery-importer/native7-U15-IO4-paired-source-plan-v1.json
python -m unittest discover -s recovered-native7/recovery-importer -p test_prepare_native7_u15_io4_pair_v1.py -v
```

`--write-plan NEW.json` derives a new JSON declaration and refuses to overwrite an existing file. There is no CAD write option, native import, subprocess, geometry package or heavy job. `metadata_preview()` returns strings in memory only. `verify_netlist()` is a pure future XML parity check; `verify_pad_metadata()` is a pure future native-record comparison for all pad geometries and semantic assignments. Neither is a final board verifier. Their meaningful controls include partial schematic changes, unrelated TX/library/component edits, wrong NC type, stale net names, old-clamp/group claims, missing endpoints, pad contour/pose changes and numeric code aliases. Real native/export behavior has not been exercised for this proposal.

The manifest lists all runtime source dependencies and their hashes. Hardware/native/checkpoint inputs are reproducible from the earlier native7 checkpoint; the compact scope and Flash assessment must also be present. No missing input is silently substituted. The historical large U15 plan was read for selected paired-schematic, variant, contract and reproduction keys; it is context only and is not a runtime dependency. No prior placement or routing success is inferred from it.

## Minimum later native importer path

Implement a separately named successor only after the finite routing prerequisite succeeds. Keep the ordinary importer v1, C12 translation importer and final-contact v2 frozen.

1. Copy exact61 hardware to an isolated candidate; apply this exact schematic/library recipe, export a fresh paired netlist and bind its full semantic parity and explicit net allocation.
2. Extend the ordinary copper importer with one exact U15 electrical-delta declaration. Set these four pad nets through the official native API. No footprint transforms or generic channel selection are needed. Predict the four native records by changing net/name codes only; every pad polygon, mask, paste, UUID and physical number remains source-identical. Prove all 156 footprint records and 554 unaffected pad records, allowing only recorded numeric-code remapping.
3. Supply complete newly selected polyline/via recipes and exactly the reviewed full-record removals. Bind paired-plan hash, routing-plan hash, role-sidecar hash, netlist hash, code map and construction provenance. Use the existing official exporter/contour helper and refill; report changed fills independently.
4. Version `common_joint11`, paired validator, constructor, physical validator and full-support checker. The old constructor/physical validator demand whole check-array equality; replace it with exactly one clamp-field delta. Full-support RX terminals change from 10/1 to 6/5. Branch-view BONDED changes to U15.5; opposite TX IO2 remains foreign. No old U15 translation or U13 permutation is replayed.
5. Version coverage/review unused-set assertions and actual-IO inputs. `check_protection_paths.py` needs the new candidate contracts, not an algorithm waiver. Rebind final-contact scope to the four semantic changes, exact cut inventory, explicit terminal substitutions and actual IO4 roles while retaining inherited/source findings and raw old failures.
6. Only a separately granted bounded owner lease permits candidate native construction/refill/export. Fresh DRC/ERC/parity, native contact and actual IO4/IO2 cut gates remain mandatory. Manufacturer channel equivalence does not establish route feasibility or ESD/ground-return/transient acceptance. Existing power qualification remains stale.

TI's [SLVSBO7O datasheet, revised August 2024](https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf?ts=1755070916604), Table4-2 and §7.2.1.2.1, supports interchangeable protected channels at physical1/2/4/5 and identifies6/7/9/10 as unconnected routing lands. §7.3 describes operation without a power input. Those facts support this electrical choice only.
