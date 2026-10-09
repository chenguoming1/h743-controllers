# Native target shape regression

This control extracts the original J4.3 and R22.1 F.Cu contact polygons and their owner-aware copper guards from `model-candidate01/model.json`. It creates a tiny DSN with no tracks or vias. It performs no route search, route insertion, native-board change, or full-model load in Java.

Run from `ordinary-routing`, after the adapter owner has compiled the intended `src` into `build`:

```sh
python tests/prepare_target_shape_fixture.py model-candidate01/model.json tests/target-shape-fixture
java -Xmx256m -jar vendor/ecj-3.41.0.jar -21 -nowarn -cp build:vendor/freerouting-2.1.0.jar -d tests/target-shape-build tests/NativeTargetShapeControl.java
java -XX:-UsePerfData -Xmx256m -Djava.awt.headless=true -cp tests/target-shape-build:build:vendor/freerouting-2.1.0.jar NativeTargetShapeControl tests/target-shape-fixture
```

The legacy witness is the disconnected endpoint `(9.66816, 8.51561)` mm. The control establishes that at least one old clearance-expanded 45-degree tree section accepts it, although its trace capsule misses J4.3. It then requires the new target API to reject it, to remain within the requested search subdivision, and to retain full trace-half-width containment in the conservative contact, including after integer-grid endpoint rounding. J4.3 has multiple search sections despite having one native convex tile, so the control exercises indices above zero. Actual guard polygons and ownership must be unchanged by all target queries.

The expected target contract is the conservative native convex tile eroded by the configured trace half-width, two engine units of rounding margin, and 10000 additional engine units (0.10 mm) for plated contacts only, intersected with the requested tree section. SMT R22.1 retains only half-width plus two units. Empty sections are valid only when that intersection is empty. `Line.translate` rounds each offset axis displacement, so the geometric check allows at most 0.51 engine unit of offset rounding while separately requiring full half-width plus the per-contact extra depth after endpoint rounding. A minimum-depth upper check also detects an unintended deeper SMT inset.

The report separates the nominal extra depth from measured unrounded and rounded boundary distances for J4.3 and R22.1. It requires every rounded J4.3 target corner to retain at least 0.10 mm beyond the trace half-width from this fixture's conservative outer pad boundary. This is useful overlap depth in the geometry model, not a manufacturing-tolerance claim or a guarantee about clearance to all possible plated-hole annuli. It does not establish the depth of any separately routed candidate unless that route's endpoints are checked independently.

Both selected pads are convex. For a nonconvex pad decomposed into convex pieces, eroding pieces separately can discard otherwise legal target positions across internal decomposition seams. This control does not prove reachability across those seams. The factory's exact static group membership and the native connectivity audit must remain unchanged.

## Empty-target negative control

The separate `NativeEmptyTargetShapeControl` temporarily raises the configured trace half-width above both real pads' full bounding-box extent. This independently proves a full trace disk cannot fit, without deriving the expectation by repeating the target implementation. It requires an explicit empty shape for every existing search subdivision, including indices above the native tile count. A `finally` block restores every layer's original width; all original target geometry and copper guards must then match their initial fingerprints.

```sh
java -Xmx256m -jar vendor/ecj-3.41.0.jar -21 -nowarn -cp build:vendor/freerouting-2.1.0.jar -d tests/target-shape-build tests/NativeTargetShapeControl.java tests/NativeEmptyTargetShapeControl.java
java -XX:-UsePerfData -Xmx256m -Djava.awt.headless=true -cp tests/target-shape-build:build:vendor/freerouting-2.1.0.jar NativeEmptyTargetShapeControl tests/target-shape-fixture > tests/target-shape-empty-result.json
```

The report records source board/model identity, exact fixture hashes, relevant source-file hashes, and hashes of the actually loaded contact and maze-search bytecode. It calls the contact target API directly; it does not claim to execute the maze-search empty-start skip or any route search.

For integer-line convex contacts, the two-unit inset margin is sufficient for the current rounding steps: `Line.translate` loses at most 0.5 engine unit of normal clearance, and independent nearest-integer x/y endpoint rounding displaces a point by at most `sqrt(0.5)` units. At least approximately 0.793 unit of margin therefore remains beyond the configured half-width plus any nominal per-contact extra depth. This argument depends on a positive configured width, the existing integer-coordinate range, and no later endpoint movement outside the accepted target. Native geometry/contact validation remains necessary after routing and cleanup.
