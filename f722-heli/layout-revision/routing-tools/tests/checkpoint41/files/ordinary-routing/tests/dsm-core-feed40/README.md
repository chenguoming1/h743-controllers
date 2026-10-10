# Bounded courtyard-clear DSM correction, source40

The selected Case A correction passes the combined nominal geometry screen. It is a constructor-facing proposal, not an adopted board or a power qualification. Native construction, complete refill/DRC, reference/support review and fresh source-bound numerical power validation remain with the routing owner.

Source40 board SHA256: `ea6c41fef86c1f66dbf6e2ce24b58858313c5c83f2a518e53385d48aad734ed5`.

- `proposal40.json`: complete source-bound operations and required acceptance checks.
- `result.json`: exact geometry, entries, pad partitions, actual D7 cut, local load cut, power estimate and preserved failed alternatives.
- `check_feed.py`: read-only reproducible check. Uses the existing native polygon helper and exact source40 native/mechanical exports; does not construct or mutate a board.
- `check.log`: concise last execution output.

## Complete operations

All three footprint orientations/sides remain unchanged:

| Reference | Source40 pose (mm, degrees) | Proposed pose |
|---|---|---|
| R38 | 17.69, 23.59, 0, B.Cu | 17.60, 23.46, 0, B.Cu |
| R70 | 17.30, 22.72, 180, B.Cu | 17.30, 22.52, 180, B.Cu |
| C70 | 18.45, 24.60, 180, B.Cu | 18.45, 24.66, 180, B.Cu |

Five source tracks are removed; nine segments replace them, with no new via:

- CORE tracks `564d43f4-fb99-4ccd-80b4-4580af7617f8` and `b6cf7bc9-8a4c-4cb5-b764-038d677651c3`: new **0.25 mm B.Cu** polyline `(16.375525,21.252534) → (16.85,21.841) → (17.298,22.064) → (17.78,21.8588) → (18.36917,21.505923)`. Every other CORE track retains its source width.
- DSM track `021879e2-963d-5f8c-9894-8e9bd725f061`: new **0.127 mm B.Cu** polyline `(16.26,23.59) → (16.7,23.59) → (16.83,23.46) → (17.09,23.46)`. The complete preceding source40 D7 exit remains.
- R70 GND track `260176e7-2d4d-4020-850f-398625eda69c`: new **0.20 mm B.Cu** segment `(16.79,22.52) → (16.19,23.1)`.
- R70 ILIM track `30154a77-e29e-465a-aa6f-a2ea55289eb9`: new **0.20 mm B.Cu** segment `(19.025,22.5) → (17.81,22.52)`.

R70.1 remains DSM_ILIM at `(17.81,22.52)`; R70.2 remains GND at `(16.79,22.52)`. Both new 0.20 mm round-cap entries have 0.17 mm native inside-pad reserve. R38.1 entry reserve is 0.2065 mm. R38.2 is still bare and its MCU continuation remains open.

C70 retains both existing tracks: supply `475d63bb-6fc3-4bd9-8d5d-5012ed082346` at 0.30 mm and ground `fc56f459-cc2f-4bdb-86dc-69e20d3ab646` at 0.40 mm. Their existing endpoints remain fully inside the translated pads, with 0.265/0.215 mm cap reserves. C70 local supply/return topology and widths are preserved; the capacitor moves 0.06 mm only. C4 and its local MCU/ground support do not move.

The dedicated D7 ground via `(16.2,24.64)` and its 0.25 mm, 0.448284 mm return are unchanged from source40. D7 does not join the C70 ground neck. Source40 SBUS/RPM repairs and every accepted J12-to-D7 branch object remain.

## Exact nominal margins

- New CORE minimum copper clearance is 0.137009762 mm, excess **0.010009762 mm** over the required 0.127 mm, at R70.1. Excess to C4 GND via `3bdf9d5b-0ff4-4ef3-96c4-515517c5f18b` is 0.010033175 mm.
- The entire finite 0.25 mm endpoint caps fit in the retained 0.30 mm CORE copper at both ends. Native radial reserves are 0.024999905 and 0.024999438 mm; each contact has 0.049087544 mm² positive area.
- R38 native courtyard gaps: R70 **0.010 mm**, C70 **0.010 mm**, U11 **0.030 mm**, D7 0.130 mm. No courtyard exception is proposed. Existing bounded body/solder-reserve gaps are respectively 0.100, 0.205, 0.220406 and 0.392165 mm.
- C70 copper-to-board-edge gap is **0.265 mm**, excess 0.011 mm over 0.254 mm. Its courtyard ends at y25.385, leaving 0.015 mm nominal board margin; bounded body/solder reserve has 0.165 mm edge margin. These are small nominal margins, not fabrication robustness.
- Moved pads were checked against all actual source and proposed foreign copper, native keepouts, outline and every existing drill. There is no same-net exception for drill-to-SMT-mask. The translated footprints have B-side SMT masks only; unchanged F-side masks and all drills retain their original geometry. No new hole is introduced. C70.2's minimum drill-to-mask gap is 0.250 mm, leaving 0.050 mm beyond the required 0.20 mm.
- After removal/subtraction of the actual native bonded D7.1 inside polygon, the DSM graph has exactly two components: J12.3 and R38.1. Outside-pad copper separation is **0.148136761 mm**, above 0.127 mm. No enlarged pad cut, chip internal path or geometry snapping is used.

## Power and connected pad groups

The two removed CORE segments form a copper bridge. Removing them separates exactly `{C4.1, C6.1, U1.1, U1.64, U13.5}` from the source group. U11.4 and the separate DSM supply branch remain in the source group; the narrowed bridge is not in series with the external DSM load. This is copper-only connectivity, without assumed MCU internal conduction. The reconstructed feed restores all 46 distinct CORE pad keys to one component. CORE, DSM supply, ILIM, DSM EXT/MCU and unfilled GND pad partitions match source40 exactly. Final ground-plane continuity requires refill.

| Changed path | Old width / length (mm) | New width / length (mm) |
|---|---|---|
| CORE pair, total | 0.30 / 2.558950463 | 0.25 / 2.466979964 |
| DSM replaced tail | 0.127 / 0.920000000 | 0.127 / 0.883847763 |
| R70 GND | 0.20 / 0.670820393 | 0.20 / 0.834505842 |
| R70 ILIM | 0.20 / 1.251489113 | 0.20 / 1.215164598 |

The narrowed length is 2.466979964 mm. Its nominal L/W rises from 8.529834876 to 9.867919857 squares, ratio **1.156871147**. Using the existing ledger's conservative fixed-temperature assumptions (105°C, 0.015 mm copper, 95% IACS), the rectangular-strip estimate changes from 13.767666 to 15.927415 mΩ: **+2.159750 mΩ**.

At the full declared 0.32 A electronics adversarial envelope, with no assumed branch fraction, the estimated added drop is **0.691120 mV** and total local strip drop 5.096773 mV. The extra deliberately loose 0.82 A total-CORE screen gives +1.770995 mV and 13.060481 mV respectively; that does not assert the separate DSM load traverses this bridge. No universal MCU/CORE sink voltage floor is defined in the current model, so these numbers do not establish a voltage-budget pass. The classic DSM floor must not be substituted for a CORE sink requirement.

The material ledger is `static-power-validation/pilot-candidate19-operator-refined-released/ledger.json`, SHA256 `f811c4d93dd074e5d74fb000db2d1218d10199ceb7c0562173be437fda572951`. Only its explicit material assumptions are reused. No historical numerical solution qualifies the new geometry. The L/W estimate excludes current crowding, contact/spreading and return resistance, thermal rise, manufacturing tolerance and decoupling/ESD transients. Fresh source-bound sheet/barrel and VCAP validation, plus explicit changed-power/support review, are mandatory before electrical acceptance.

## Preserved failures and scope

At the fixed Case A pose, the source C4 ground-via to R70.1 copper gap is 0.524042944 mm. A 0.30 mm feed plus both clearances needs 0.554 mm and misses by 0.029957056 mm. The final tangent path at 0.30 mm also fails. Two direct 0.25 mm bends fail respectively R70.2 and the C4 ground via; the selected two-corner tangent construction resolves both. All are recorded in `result.json`; older proposal/failure receipts remain byte-identical.

This packet is relative to isolated source40. The routing owner must bind a complete successor to accepted source39, including the already-reviewed source40 D7/SBUS/RPM changes, and run complete native/fill/reference/power gates. No source board, canonical file, project or Git state was changed here.
