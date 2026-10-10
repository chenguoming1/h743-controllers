Status note: the following report records the historical staged-only review. After batch05 terminated and candidate32 was qualified, the single diagnostic source was promoted and compiled. See promotion-identity.json and subsequent zero/runtime receipts for current state. Baseline sources/classes remain preserved exactly under baseline/.

# Staged complete located-path diagnostic

Status: staged only, outside live source and build. No compilation, engine run, geometry analysis or native DRC was performed. No live file, routing predicate, geometry alias, scheduling rule or fixed-state behavior was changed.

## Why this location

The live `src/app/freerouting/autoroute/InsertFoundConnectionAlgo.java:97` constructs the inserter. Its line 100 logs only the next `located_trace`; line 101 may refuse a via, and line 107 may refuse a trace. Either refusal returns before later polylines are logged. The staged patch adds exactly one diagnostics call immediately after constructing the inserter, before that loop or any insertion.

`vendor/source/src/main/java/app/freerouting/autoroute/LocateFoundConnectionAlgo.java:25` holds the already-computed `connection_items`; its constructor begins on `target_layer`, appends traces in target-to-start order (line 167), and exposes start/target items and layers. `ResultItem` at line 503 contains final layer and corner-array references. The diagnostic iterates those references without changing them, their arrays or any board item.

## Added record

With the existing `F722_INSERT_DIAGNOSTICS=1` gate, one `INSERT_DIAGNOSTIC` JSON line has `stage=located_connection` and `status=located_only`. It includes net name/number; target-to-start traversal order; every polyline with trace index, layer name/index, requested half-width and all corners; start/target endpoint coordinates and layer; endpoint engine ID, class, fixed state and label; and native UUID/group/contact label where the endpoint is a native pad contact.

Via transitions are recorded only when the layer changes, at the same planned corner and in the same from/to-layer order as the existing insertion loop. A transition with `before_trace_index` equal to the trace count is the final transition to `start_layer`. These are intended transitions, not a selected/inserted via mask or a claim about actual copper. Coordinates retain the existing x / 100000, -y / 100000 millimetre conversion.

Existing `ROUTE_ATTEMPT_START` provenance, `located_trace`, and failure records are unchanged. Failure records already expose obstacle engine ID, class, fixed state, clearance class and nets, plus guard label/native UUID when present. Thus a USER_FIXED ordinary Trace can be distinguished from NativePadContactArea or an ObstacleArea guard without guessing from its net name. Endpoint IDs describe the actually located endpoints; correlate an attempt using the surrounding ROUTE_ATTEMPT_START record. No global attempt counter or scheduler changes are introduced.

## Bounded verification

`stage_and_verify.py` generated the staged source and unified patch. It verifies that deleting only the new helper block and its one call recovers the live source exactly, byte for byte; that the new call precedes both insertion methods and the original loop; that the helper has no route/board-field assignments; and that collection writes target only fresh local JSON maps/lists. The existing `diagnosticPoint` on these IntPoint corners calls `IntPoint.to_float()` (vendor line 150), which constructs a new FloatPoint. Endpoint ID/fixed getters are direct field reads (Item lines 107 and 965). This is source/static evidence, not a Java compile or runtime proof.

`baseline-identity.json` hashes all 15 current Java sources, all 22 current build classes, the runtime engine JAR and run_local.sh. The complete manifest matched before and after staging. `baseline/src/.../InsertFoundConnectionAlgo.java` preserves the exact pre-change file. `static-verification.json` records the passed checks and explicitly records all runtime validation as not run.

## Caveats and use

The staged source is not compiled. The owner must check the manifest still matches the chosen live baseline before applying/rebuilding after live05 finishes. Logging allocates fresh JSON containers and performs stdout I/O when enabled, so timing can change; it introduces no route-state writes. As with existing diagnostics, output is not guaranteed if the process terminates or serialization/output fails. The collection is assumed to have valid elements/layers, as the current inserter already assumes. Empty paths/corner arrays retain empty arrays or null endpoints and are not repaired.

A complete located record shows a planning candidate only. Later forced insertion can refuse, partially mutate then recover, or choose a via mask with a wider span. Native route alternatives derived from this log still require separate construction and independent native validation; no success or reduced-open-count claim follows from this diagnostic.
