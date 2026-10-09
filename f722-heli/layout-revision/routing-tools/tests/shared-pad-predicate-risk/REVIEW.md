# Shared-pad predicate review: do not promote a two-predicate-only exception

The existing two rejections cannot safely be relaxed in isolation. The shove transaction retains the original obstacle collection and can later cut every foreign trace in it. That downstream operation does not check `USER_FIXED`. A small synthetic control confirms that it removes the fixed source object, shortens its copper, and reinserts the remaining part as `NOT_FIXED`.

This is a latent hazard of an incomplete future exception, not a claim that current routing damaged a source. Stock rejection still protects the fixed trace. No adapter change or routing candidate was produced, and no live source, build, model, board, public repository, GitHub, or Library object was modified. All new files are under this isolated staging directory.

## Exact call path

Paths below are relative to `ordinary-routing/vendor/source/src/main/java/app/freerouting/board/` and hashed in `source-manifest.json`.

1. `RoutingBoard.java:664-669` calls `ShoveTraceAlgo.spring_over_obstacles` before insertion. `ShoveTraceAlgo.java:471-504` classifies each foreign fixed `PolylineTrace` as an obstacle unless a normal contact advertises the requested logical net. The native shared-pad contacts intentionally do not merge logical nets.
2. `ShoveTraceAlgo.java:202-209` checks, and `:329-343` inserts, through `ShapeTraceEntries.store_items`. `ShapeTraceEntries.java:155-164` rejects a fixed item that lacks a shared logical net. Merely disabling that condition also exposes ordinary `store_trace` processing at `:172-179`; a proper pad exception would need to avoid treating the permitted fixed trace as movable.
3. In insertion, the same original `obstacles` collection survives `store_items`. If there are substitute trace pieces and recursion remains, `ShoveTraceAlgo.java:345-356` calls `shape_entries.cutout_traces(obstacles)`. A pad-local fixed trace skipped during storage can therefore still be present when another movable trace produces substitute pieces.
4. `ShapeTraceEntries.java:297-305` calls `cutout_trace` for every foreign `PolylineTrace` in that collection, with no fixed-state guard and no pad-containment test. `:81-85` removes the source and inserts residual pieces as `NOT_FIXED`; the two-piece fast path likewise creates `NOT_FIXED` pieces at `:97-105`.

Changing two booleans does not establish a safe check/insert transaction. The zero-substitute early return at `ShoveTraceAlgo.java:346-348` explains why a single-obstacle positive insertion control could pass while missing the mixed-obstacle hazard.

## Small control and result

Run `sh run-control.sh` from this directory. It compiles only the three copied contact/trace adapter classes and one synthetic control against the pinned release JAR. Compiler and control each have `-Xmx256m`; the control has a five-second process timeout. There is no solver, route replay, native PCB input, or full-board JVM.

The synthetic pad is the exact box `[-1000,-1000]..[1000,1000]`. Two separate logical contacts have the same native identity and the two physical owners. The fixed P1 track runs from `(0,-4000)` to `(0,0)`, half-width 50. The P2 query runs from `(-300,0)` to `(300,0)`, half-width 50. Full clearance is 100 plus the stock 16-unit safety allowance. Both participating-copper conflict sets have conservative rectangular bounds inside the exact pad. The unrelated owner remains rejected and the P1/P2 contact graph remains separate.

`control.json` records a passing expected-risk control:

- Unmodified `store_items` rejects P1 as the fixed foreign obstacle.
- A deliberate direct call to stock `cutout_traces` removes original ID 4, `USER_FIXED`, with corners `(0,-4000)..(0,0)`.
- It leaves replacement ID 5, `NOT_FIXED`, with corners `(0,-4000)..(0,-217)`.

The direct downstream invocation isolates the operation's precondition. It does not claim to execute a modified whole transaction, simulate a second movable obstacle, or prove a future exception routes successfully. No new outside-common-pad acceptance predicate was implemented, so no candidate-predicate outside-pad negative or actual-I/O cut gate was run. Those remain mandatory before any promotion.

## Existing evidence and scope

The source26 refusal is already preserved in `../tests/located-portb-rx26/{captured-engine.log,located-receipt.json,proposal.json}`. It identifies P2 at U14.4 against USER_FIXED P1 and binds board SHA-256 `697555207280b8d67714a0011a51ec355321f21f551d6a1486a786c38a671949`. It was read and hashed, not replayed. The source21 analytic shared-pad proof and the existing `PhysicalOwnerInsertionControl`/`SharedPadSeamControl` were reviewed. The former resets inserted tracks between aliases, and the latter explicitly preserves inside-pad track-to-track rejection; neither tests this downstream mutation contract.

## Recommendation

Keep the proven native alternative primary. A future bounded transaction-level exception is worth considering after a candidate is sealed, but it needs more than these two predicate edits. For each query, it must prove that all participating copper on both sides of every clearance conflict lies inside the same exact native pad identity and layer, with both legitimate physical owners. An inset native contact tile can serve as a conservative subset; a pad bounding box alone cannot.

The permitted collision must stay consistently classified through both checking and insertion, and must never place the immutable source trace in cutout, replacement, or tail-cleanup mutation work. A first prototype could conservatively reject any mixed case requiring shove/substitute work. It must preserve source IDs/fingerprints/fixed states and logical contact partitions. Required controls include the positive shared-pad case, wrong owner, another pad UUID/layer, outside-pad copper/clearance conflict on either side, a later foreign-trace section outside the pad, and mixed movable/fixed obstacles, followed by native actual-I/O pad-cut gates. Compensated and uncompensated search-tree geometry need separate treatment or an explicit fail-closed restriction. No physical alias broadening, clearance reduction, or mask/drill relaxation is justified.
