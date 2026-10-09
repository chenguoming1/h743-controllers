# Native escape and engine via control

This source package retains compact historical reports and test sources. Referenced complete source boards/models/native exports, generated fixtures and compiled classes are external or regenerated inputs and are not included. Each report remains bound to its original source and binary hashes.

## Findings

On candidate05 (`08c2daf1df7db0a7c922632aa483cc13022b0c6a4066e87493e9dcee9fba7724`), the two ADC_DIV_MID targets occupy different full-board legal centerline components on F.Cu. The two FLASH_WP_N targets likewise occupy different components on B.Cu. All four half-width-inside pad targets retain their full area. Both optimistic inscribed and conservative outward-rounded native-polygon clearance calculations agree.

- R44.1 is in an enclosed approximately 2.8765 mm² F.Cu component bounded by fixed GND and +3V3_IMU copper.
- U3.3 is in an enclosed approximately 2.7755 mm² B.Cu component bounded by fixed GND, +3V3_CORE, ABC_VAUX, and ABC_FB copper.
- No mutable ordinary route is on either small component's boundary. A multilayer escape is necessary while those fixed boundaries remain.

All four components contain legal native through-via centers. The calculation was repeated on candidate06 (`221ee94c9a936be959dc89b7c7050a20b5f795af6a86921fb44c01a2e9dbecc3`), preserving the four original witnesses. The exact quantized points below were independently checked against native geometry again.

| Pad | Logical net | Via center, native mm | Minimum extra clearance, mm |
|---|---|---|---:|
| R43.2 | ADC_DIV_MID | (1.01394, 12.56278) | 0.534293842 |
| R44.1 | ADC_DIV_MID | (25.38059, 14.57554) | 0.056152010 |
| R5.2 | FLASH_WP_N | (38.65877, 19.35111) | 0.141951370 |
| U3.3 | FLASH_WP_N | (32.07791, 18.82408) | 0.040524295 |

These are existence witnesses, not preferred route locations. The native receipt also records nearer local witnesses and the small islands' usable via-region bounds. R44.1 has approximately 0.116075 mm² of conservative legal via-center area; U3.3 has approximately 0.013022 mm². A via witness does not establish engine acceptance, a complete multilayer route, or a legal imported board.

## Native rules included

- 0.127 mm trace width; foreign copper-to-centerline reserve 0.127 + 0.0635 = 0.1905 mm
- 0.45/0.20 mm through via; foreign copper-to-via-center reserve 0.127 + 0.225 = 0.352 mm on all six layers
- Both SMT mask faces, with no same-net exception: mask-to-center reserve 0.20 + 0.10 = 0.30 mm
- All existing drills, with no same-net exception: drill-polygon-to-center reserve 0.25 + 0.10 = 0.35 mm
- Board edge and NPTH copper clearance: 0.254 + 0.225 = 0.479 mm for via centers
- Actual rule keepouts; only the two regenerable In1.Cu/In4.Cu GND fills are excluded from via obstacles. Native pads, tracks and vias on those layers remain.

The export's native outside copper polygons have a stated maximum error of 0.00001 mm. No buffer(0), make_valid, geometry repair, source editing, route search, or board upload was performed. Native polygons must already be valid. Round buffer chords use 64 segments per quadrant; conservative buffers enlarge their radius by sec(pi/256) plus 0.000002 mm. Positive witnesses are also checked by direct distances to the original native polygons, independently of buffer classification.

## Artifacts

- `native_escape_audit.py` / `native_escape_audit.json`: candidate05 full-board and bounded-window same-layer component diagnostic, including small-island boundary source objects
- `native_via_escape_audit.py` / `native_via_escape_audit.json`: original candidate05 six-layer via-region diagnostic
- `native_via_escape_candidate06.json`: candidate06 six-layer via-region diagnostic; candidate05 receipt preserved
- `prepare_via_escape_fixture.py`: exact 10 nm quantization and native distance recheck, fixture generation and source/binary binding
- `via-escape-candidate06-fixture.json`: four source-bound cases; SHA-256 `a41e6e592a858e6e818fe9bd4e449aae5d68452e2dd8ccf1dfccd92e05c64519`
- `NativeViaEscapeControl.java` and `build/app/freerouting/board/NativeViaEscapeControl.class`: compiled tests-only stock-engine control; full-model execution is owned by the parent task

The fixture binds model, DSN, native export, board, adapter sources/classes, pinned Freerouting JAR, native receipt, test source/class and generator. The engine control checks all those hashes, requires the pinned stock ForcedViaAlgo class and bound NativeGuardFactory class, chooses each logical net's VIA_450_200 rule, resets stale failure diagnostics, and calls ForcedViaAlgo.check with zero shove recursion. It never inserts a via or runs routing. Each result contains failure class, engine item ID, label, nets, layers and native coordinates when available. Route and guard/contact/outline geometry fingerprints must remain unchanged after every case. Engine rejection is recorded as a diagnostic outcome, not converted into a native-geometry failure.

## Run after the full-model slot is granted

From `ordinary-routing`:

```sh
java -XX:-UsePerfData -Xmx3g -Djava.awt.headless=true -cp tests/clearance-audit/build:build:vendor/freerouting-2.1.0.jar app.freerouting.board.NativeViaEscapeControl model-candidate06-diagnostic tests/clearance-audit/via-escape-candidate06-fixture.json tests/clearance-audit/via-escape-candidate06-engine.json a41e6e592a858e6e818fe9bd4e449aae5d68452e2dd8ccf1dfccd92e05c64519
```

The historical full-model engine receipt `via-escape-candidate06-engine.json` records all four witnesses as allowed, with unchanged geometry. The control writes its result after each completed case and marks `completed` only after all cases and source rechecks finish.

To regenerate a native diagnostic for a different frozen input, pass explicit `--native` and `--output` paths to `native_via_escape_audit.py`, then create a new fixture. Do not silently reuse a fixture after any hash-bound source, binary or model change.
