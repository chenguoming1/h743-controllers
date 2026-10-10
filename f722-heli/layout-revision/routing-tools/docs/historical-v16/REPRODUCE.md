# Reproduce the V16 portable incremental checks

Required external inputs are the complete immutable public-source-ready-v15 tree and exact candidate44 paired project already recovered by V15. V15 ZIP SHA-256: 8fca33afdf93c3dd0df5c21a87e18c40d54406b70e82398cdb5abbd94a100285. V15 FILES.sha256.json SHA-256: f3a51c6ba4ed04a51a48b77c1789a8de5d693f72b97cb40b5c65869732a09b93. The candidate44 board SHA-256 is 02d2090ad7220a64a8f4a1a259d522f7b0bca3e15214b73107491d17626bd51f; recovery-v16/paired-files.json pins all 61 files. Earlier recovery/native checks are not repeated for this increment.

Apply the delta with its separately published exact ZIP digest:

```sh
python -B tools/apply_source_delta_v16.py --base /path/public-source-ready-v15 --delta /path/routing-source-v16-delta.zip --zip-sha256 PUBLISHED_DIGEST --out /new/public-source-ready-v16
python -B /new/public-source-ready-v16/tests/verify_v16_delta.py --base /path/public-source-ready-v15 --delta /path/routing-source-v16-delta.zip --zip-sha256 PUBLISHED_DIGEST --base-project /path/exact-candidate44 --out /new/portable-verification.json
```

For only the incremental checks, run tests/verify_v16_evidence.py with --base-project /path/exact-candidate44 and --out /new/evidence.json. This succeeds without the historical workspace. The optional --historical-workspace verifies original bytes as well, including hashes of the omitted large exports; it still does not execute native checks.

Recover either complete paired project using sessions/recovery-v16/rebuild_historical_source.py project --base-project /path/exact-candidate44 --source candidate44 (or candidate45) --out /new/project. Materialize selected evidence with tests/checkpoint45/materialize.py --base-project /path/exact-candidate44 --out /new/evidence-workspace.

For original full native proof replay, restore every omitted input to the indexed original workspace-relative path, using the exact paired board, matching KiCad 10.0.6+dfsg-1, source-bound exporters, and required native/geometry dependencies; each export must match its pinned SHA-256 before replay. Reproduction of those hashes is not promised by the portable packet. Original debug scripts target tests/debug-testpoint44/candidate01 and assume the original workspace layout. The native runtime proof verifier reads the large exact source and target snapshots. The repro34 placement builder additionally needs the original published source project pinned in repro-34-placement/source.json, not the routed recovery project. Placement previews omit route copper and fills and do not establish 3D fixture/harness access. All those native checks and the five/six original control sets are preserved, not reexecuted by portable verification.
