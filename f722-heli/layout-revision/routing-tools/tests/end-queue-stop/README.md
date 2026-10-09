# End-of-queue cooperative stop control

Both cases passed against the unmodified production `LocalRouter` build. Each makes one real successful connection, merges the two native contact partitions into one, and naturally exhausts the initial queue: `2 → 1 → 0`. The configured success threshold is five, the requested pass count is one, and no stop file exists.

- `positive-flush`: checkpoint frequency three leaves the one successful route pending until queue exhaustion forces a new geometry checkpoint. The first stop call comes from `LocalRouter.lambda$0`, line 86.
- `positive-reuse`: checkpoint frequency one saves the success immediately. Queue exhaustion reuses that snapshot. The first stop call comes from `LocalRouter.lambda$0`, line 78.

A read-only JDI debugger observes the actual stock `StoppableThread.request_stop_auto_router` assignment and return. In both cases the first call changes the flag from false to true, with published counters `pass_count=1`, `queued_to_be_routed_count=0`, `routed_count=1`. This establishes the final-queue trigger independently of exit status or an inferred log label. The batch loop subsequently requests stop again at line 444 with the flag already true; this is redundant and does not alter geometry.

Both child JVMs exit zero. The final snapshots retain the exact two contacts, two contact guards, one fixed trace, and one fixed via. Production fixed-geometry hashes include class, ID, nets and geometry and remain unchanged. Before/after JSON comparison independently verifies all fixed areas and copper. Each successful checkpoint has the same routes and native contact partitions as the final report. Its SES is byte-identical to the final SES, and independently parsed SES coordinates/width/net/layer match the final JSON route. Assertion controls reject a removed guard and a shifted route endpoint while leaving the successful counters intact.

The fixture derives its two exact synthetic contact rectangles and guards from `tests/failed-search-state/fixture/model.json`. It adds the six layers expected by `LocalRouter`, plus a fixed trace/via on an ignored net. Its physical-board and native-export identities are explicitly labeled synthetic text files; no real board is loaded, changed or claimed to pass native DRC. As in production, temporary contact adapters are removed after the final JSON snapshot for SES export.

`result.json` contains the checks and hashes for the fixture, all production sources/classes, test sources, and successful output artifacts. All receipt paths are relative to `ordinary-routing`, identified by its `path_base` field. The original run retained a `source-used/` tree. This package avoids duplicating it: all its recorded hashes match the packaged `src/` files. Each `*.debugger.json` contains the actual stop stacks and published progress observed at the stop calls; its runtime paths are projected relative to the package root, with original and portable hashes recorded in `checks/v6-portable-projections.json`. The fixture generator resolves the current checkout root when preparing a fresh run.

Source identities used:

- Final `result.json`: `2d9512408e1320244c101e68ded242493a79accb42b569da57b2d941cc667120`
- `LocalRouter.java`: `2e8fcec59f2e89b28be8670b71bdff61627874e57c08a6ffabd4949a99d182df`
- `BatchAutorouter.java`: `0fb10dd577de3843422dac66cc918102e0a65c4a2eaf975524140169e0201a54`
- Fixture model: `794913f2d1b2ea713b1895f5b035d601d7e3fdeef65f179769c4ccd5a3cc5258`

## Reproduce

Run from `ordinary-routing` after the intended production build has been compiled. All output is confined to this test directory. The observer uses a 64 MiB heap; its production child uses 256 MiB, a two-second connection budget and a twenty-second watchdog. Observed routing/checkpoint elapsed times were about half a second per case.

```sh
python tests/end-queue-stop/prepare_fixture.py
java -XX:-UsePerfData -Xmx256m -jar vendor/ecj-3.41.0.jar -21 -nowarn --add-modules jdk.jdi -cp build:vendor/freerouting-2.1.0.jar -d tests/end-queue-stop/build tests/end-queue-stop/ObserveStop.java
F722_CHECKPOINT_AFTER_ROUTED=5 F722_CHECKPOINT_EVERY_ROUTED=3 F722_CONNECTION_BUDGET_MS=2000 java -XX:-UsePerfData -Xmx64m --add-modules jdk.jdi -cp tests/end-queue-stop/build:vendor/freerouting-2.1.0.jar ObserveStop tests/end-queue-stop/fixture tests/end-queue-stop/positive-flush 1
F722_CHECKPOINT_AFTER_ROUTED=5 F722_CHECKPOINT_EVERY_ROUTED=1 F722_CONNECTION_BUDGET_MS=2000 java -XX:-UsePerfData -Xmx64m --add-modules jdk.jdi -cp tests/end-queue-stop/build:vendor/freerouting-2.1.0.jar ObserveStop tests/end-queue-stop/fixture tests/end-queue-stop/positive-reuse 1
python tests/end-queue-stop/verify.py
```

The route queue is shuffled, so either pad may initiate the connection and exact route points may differ between runs. The acceptance criteria do not depend on that order.

## Excluded exploratory evidence

The excluded `observer-startup-timeout.*` records the discarded broad method-event observer. Its debugger overhead exceeded the twenty-second bound before routing; this is not a routing failure. Precise breakpoints replaced those method events. The excluded `positive.*` records the first successful production run, after which the observer correctly rejected its own too-strict assertion that there must be only one stop call. The final observer allows the verified redundant batch-loop call and requires the initial false-to-true transition to originate in the production listener. Only `positive-flush.*` and `positive-reuse.*` are the final passing receipts.
