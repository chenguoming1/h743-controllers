# Failed-search state lifecycle control

This synthetic fixture has two separate same-net pad contacts, their owner-aware copper guards, and no tracks or vias. It uses no native PCB and performs no route insertion. Each JVM is limited to 256 MiB.

The control makes a `TimeLimit` expire deterministically at the first `MazeSearchAlgo.occupy_next_element` call, after maze initialization creates expansion rooms. A separate case expires as soon as initialization has created a room, exercising the null-maze early return. Both cases have a two-second fallback deadline. This avoids a timing-sensitive sleep while testing the production early-return paths.

## Negative evidence

`unrepaired-result.json` is the original unchanged negative receipt, with source and loaded-engine hashes. On both slow and fast trees:

- Before search: 0 complete expansion rooms in the cached tree.
- After timeout: 3 rooms remain.
- `init_autoroute(retain=false)` creates a new engine but returns the same cached tree containing all 3 rooms.
- Reverse initialization fails.
- Calling `finish_autoroute` on the replacement engine leaves all 3 orphan rooms.
- Calling `clear()` on the original engine removes them, giving 0 rooms; reverse initialization then succeeds.
- Fresh-board reverse initialization and `finish_autoroute` before replacing the engine also succeed.

No pad/guard geometry, physical item object identity, logical contact membership, or contact group changes in any case. The negative receipt covers the null-search-result path. The second, null-maze-initialization case was added afterward and verified against the repaired build.

## Repaired evidence

`repaired-result.json` uses an explicit repaired expectation. Both early-failure stages on both tree types leave 0 complete rooms immediately after returning. Reverse initialization succeeds on the same cached tree. Physical state and item identities stay unchanged. Recorded `failure_cleanup_seconds` is approximately 8–33 microseconds in this run.

Production cleanup belongs before both early returns in `AutorouteEngine.autoroute_connection`: use `clear()` when `maintain_database` is false, otherwise the existing `reset_all_doors()` behavior. The owner made this production change; this control edits tests only. This fixture exercises `retain=false`; it does not independently verify retained-database routing.

## Commands

Run from `ordinary-routing`:

```sh
python tests/failed-search-state/prepare_fixture.py
java -XX:-UsePerfData -Xmx256m -jar vendor/ecj-3.41.0.jar -21 -nowarn -cp build:vendor/freerouting-2.1.0.jar -d tests/failed-search-state/build tests/failed-search-state/FailedSearchStateControl.java
java -XX:-UsePerfData -Xmx256m -Djava.awt.headless=true -cp tests/failed-search-state/build:build:vendor/freerouting-2.1.0.jar app.freerouting.autoroute.FailedSearchStateControl tests/failed-search-state/fixture repaired > tests/failed-search-state/repaired-result.json
```

The latest test also supports `unrepaired` as the final argument when intentionally exercising an unrepaired build. It asserts the selected expectation rather than silently treating either behavior as a passing repair. Do not overwrite the retained original negative receipt.

## Source mechanism

Before repair, the null-maze and null-search-result returns preceded the existing `clear`/`reset_all_doors` block. `RoutingBoard.init_autoroute` replaces the engine whenever retain is false without first clearing the prior engine. `SearchTreeManager.get_autoroute_tree` caches and reuses trees by key. `CompleteFreeSpaceExpansionRoom.is_trace_obstacle` returns true for every net. The stale rooms consequently become obstacles for the replacement engine, which does not own the list needed to remove them.

This establishes a concrete state-lifecycle defect and its bounded repair. It does not establish whether an otherwise fresh full-board search will find a physically valid route.
