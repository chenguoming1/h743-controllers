# WIP: closed 173-record routing and exact statistics recovery

This checkpoint preserves the closed negotiated-v6 and v7 routing trials, the
exact statistics baseline control and saved-output reconciliation, and three
sealed importer source packets. Canonical native7 remains unchanged with seven
native opens. No candidate is adopted, numerical power remains stale, and
engineering acceptance is unfinished. This work is not manufacturing-ready.

V6 stopped safely at its 512 MiB exact-key cap before routing, with no checkpoint.
The baseline control's five Java stages passed but its supervisor exited 1 after
a final source-rehash TypeError. Original source and failed receipt are preserved
alongside independent saved-output reconciliation. V7 stopped cooperatively with
6 of 19 roles connected. Full passes ended at 18, 17 and 17 required joins; its
terminal state has 16 versus the source's 13. All 16 complete checkpoint triplets
and the final report/session remain recoverable. Terminal analysis does not
claim that budget saturation proves geometric infeasibility.

The selected-checkpoint binder preserves both v5 regression selections and the
later heap failure. Its full-pass proof accepts checkpoint 0018 and rejects the
stale boundary interpretation of 0019. The 173-record adapter and concrete importer
profile preserve 173 original mutable records, 2,214 fixed records and six declared
fixed additions. The profile's synthetic initial conversion is a source-only test
fixture. Active triangle/tree simplification and later importer/native diagnostic
outputs are outside this checkpoint.

## Verified byte recovery

The 19,464,328-byte XZ archive contains 170 new objects in three parts, SHA-256
e3f9a59ff65901e2cf80a76068fed9c01ab210b82bfc6bfe8e8645cb4f7b8b99.
Another 270 objects reuse exact v5/corrected-v2 predecessor identities. All 687
restored paths and 440 unique objects passed size, SHA-256 and Git blob checks.
Member ordering/metadata and part reassembly were stream-verified. Packaging and
cold byte restoration took 6.366 seconds under one CPU, a 1 GiB address-space cap
and a 60-second bound. No geometry, native tool or routing code ran during these
checks. The shared heavy lane was released before publication metadata work.

The unique 54,004,404-byte exact source witness is stored once. Original reports,
control failures, source overlays and synthetic conversion evidence are lossless.
Two large v6/v7 model JSON files are omitted through pinned composition and
metadata-only derivation recipes; earlier generated/runtime dependencies retain
their exact inherited recipes. Byte restoration runs no regeneration.

Restore corrected-v2 and its predecessors, then v5. Assemble a fresh ancestor
workspace containing the exact aliases named in PREDECESSOR-FIXTURE.json from
the identified restored checkpoints. Check each alias's size, SHA-256 and Git
blob identity; duplicate aliases must agree. The verified fixture requires 270
unique objects. Do not use live source files as predecessor replacements.
Then run:

    python restore.py --repository /path/to/repository --published-workspace /path/to/verified-ancestor-union --output /path/to/new-173-cache-workspace

The output must not exist. Historical engineering replay requires the documented
original paths, runtimes, expected hashes and fresh model output directories.
Never overwrite preserved receipts. Saved report/SES pairs do not serialize the
router's queue or history. This checkpoint proves byte recovery; engineering
replay and any native acceptance need separate execution and evidence.
