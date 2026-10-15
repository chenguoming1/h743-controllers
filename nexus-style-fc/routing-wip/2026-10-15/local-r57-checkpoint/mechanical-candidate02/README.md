# Isolated Nexus header redesign

Latest implementation: **candidate-02/nexus-style-fc**. Unfinished and unvalidated natively; no fabrication/assembly acceptance.

Read `candidate-02/nexus-style-fc/docs/header-interface-candidate/README.md` for the complete dimensions, source binding, fit/overlap/strength screens, copper conflicts and qualification gates. Dimensioned preview files are alongside it.

- Exact initial rollback: `rollback-r54-source/` (69 verified source files plus untouched model sources)
- Preserved first candidate: `candidate-01/`
- Latest replay: `transaction-r54-03-candidate02/`
- Guarded replay tool: `candidate-02/nexus-style-fc/tools/apply_header_interface.py`
- Source/implementation binding: `transaction-r54-03-candidate02/source-manifest.json`
- Native changes and old/new per-pad records: `transaction-r54-03-candidate02/transaction-report.json`
- Actual-native static checks: `candidate-02/nexus-style-fc/docs/header-interface-candidate/static-validation.json`
- Complete mating-net/DSM_DATA copper inventory: `candidate-02/nexus-style-fc/docs/header-interface-candidate/routing-preservation-inventory.json`
- Guard/replay tests: `candidate02-replay-tests.json`
- Independent review: `independent-review/`

Native main candidate SHA256: `40c4cdf78e7cb15a6ee5ed8219284f19e3a58b10686b0688daadd5f3d00c0689`.
Native child candidate SHA256: `f89abf8e21697fc401f16f48ee3877dd8c4d9f1360b10f79412bbd692a6da19c`.

The parent remains the sole GitHub writer. The routing owner remains the sole native/heavy KiCad lane. This package does not replace either canonical or accepted experimental copper.
