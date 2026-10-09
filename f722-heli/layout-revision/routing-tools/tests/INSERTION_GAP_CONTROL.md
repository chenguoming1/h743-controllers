# D2.1 insertion-gap control

This tiny fixture extracts only the exact F.Cu copper Guard for D2.1 / LED_RED_K from candidate06 diagnostic model `7b560e734499d0a01fb5614781dac0a9bbe1ec2e5b0b5535ba7d2a796342aa81`, bound to native board `221ee94c9a936be959dc89b7c7050a20b5f795af6a86921fb44c01a2e9dbecc3`. The failed D2_A segment is `(41.16554, 20.84683)` to `(41.16554, 21.88273)` mm, width 0.127 mm.

Run from `ordinary-routing`:

```sh
python tests/prepare_insertion_gap_fixture.py
java -XX:-UsePerfData -Xmx256m -jar vendor/ecj-3.41.0.jar -21 -nowarn -cp build:vendor/freerouting-2.1.0.jar -d tests/insertion-gap-build tests/app/freerouting/board/NativeInsertionGapControl.java
java -XX:-UsePerfData -Xmx256m -Djava.awt.headless=true -cp tests/insertion-gap-build:build:vendor/freerouting-2.1.0.jar app.freerouting.board.NativeInsertionGapControl tests/insertion-gap-fixture > tests/insertion-gap-result.json
```

Each shift uses a fresh tiny in-memory board with the unmodified guard, unmodified 0.127 mm clearance, and stock insertion settings (trace/via/spring recursion 20/5/5). No maze search or native PCB read/write is performed in Java. Successful probes insert a temporary trace only into that disposable fixture board. Guard geometry and ownership are fingerprinted before and after each insertion.

## Observed result

- The original segment reproduces the rejection: `spring_over_obstacles` returns null, `ShoveTraceAlgo.check` rejects the guard, and `insert_forced_trace_polyline` returns the segment start.
- Outward x shifts of 0 through 14 engine units still fail.
- The first passing shift is 15 engine units (0.00015 mm), producing x = 41.16569 mm. Spring-over then returns the unchanged path, shove check succeeds, and full insertion reaches the endpoint. Native edge gap becomes 0.12719 mm.
- All guard fingerprints remain unchanged. Every tested shift keeps the nominal clearance matrix at 12700 units.

The default tree is `ShapeSearchTree_FortyfiveDegree_cc0`, with no compensation. The raw guard maximum x is 4097502 engine units, including the model's two-unit outward reserve. The original capsule's gap to that guard is 12702 units. `ClearanceMatrix.get_value(..., true)` adds its stock 16-unit safety margin, requiring 12716. At shift 14 the expanded shapes still touch, which the overlap predicate rejects. Shift 15 separates them by one unit.

The obstacle occupies four default-tree sections. `ShoveTraceAlgo` lines 581–598 refuses to spring over a multi-section `ObstacleArea`, so spring-over cannot correct this boundary mismatch automatically.

## Planning-stage source path

`AutorouteControl.java:207` supplies compensated half-width 12700. The fast tree's guard maximum x is 4103852. `LocateFoundConnectionAlgo45Degree.java:125–138` shrinks a free-space room by that compensated width plus `AutorouteEngine.TRACE_WIDTH_TOLERANCE`, currently 2, giving the observed x = 4116554.

Keeping all physical geometry and nominal clearances unchanged, a planning-only tolerance of 18 units (stock insertion safety margin 16 plus the existing 2-unit planning tolerance) would place this axis-aligned example at x = 4116570. That is within the measured passing range. This isolated result does not establish that changing the tolerance completes a full route or fixes every angled/multi-obstacle case.

`TRACE_WIDTH_TOLERANCE` is a static final primitive and is inlined into compiled consumers. Changing only `AutorouteEngine` does not alter locator bytecode loaded from the stock jar. Any intended policy change must recompile the relevant consumers, including the 45-degree locator, and review `LocateFoundConnectionAlgoAnyAngle`, `ExpansionDoor`, and `MazeSearchAlgo`. No source or routing policy was changed by this control.

## Compiled 18-unit planning margin verification

After the adapter owner compiled the planning-margin change and all intended consumers, the unchanged physical insertion fixture was rerun:

```sh
java -XX:-UsePerfData -Xmx256m -Djava.awt.headless=true -cp tests/insertion-gap-build:build:vendor/freerouting-2.1.0.jar app.freerouting.board.NativeInsertionGapControl tests/insertion-gap-fixture > tests/insertion-gap-result-margin18.json
python tests/audit_compiled_planning_margin.py
```

`compiled-planning-margin18-proof.json` records class/source hashes and direct class-file evidence, mapped through each method's `LineNumberTable`, for all five source references to the planning constant across the four intended consumer classes. It also verifies the compiled `AutorouteEngine` constant is 18. This catches both missing local class overrides and stale inlined numeric values without requiring `javap` or running a maze search.

The independently captured insertion report verifies the calculated planned x = 4116570 engine units (+16 units outward) succeeds: spring-over leaves the path unchanged, all shove checks pass, and insertion reaches the endpoint. The original x = 4116554 remains rejected, and the nominal 12700-unit matrix, stock 12716-unit safety-added insertion clearance, and exact guard geometry remain unchanged. This proves this straight-segment fixture and the intended compiled constants; full-board routing is outside this control's scope.
