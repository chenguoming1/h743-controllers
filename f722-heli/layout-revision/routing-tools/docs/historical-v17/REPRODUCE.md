# V17 bounded reproduction

## Base identity

- Immutable V16 delta ZIP SHA256: 1f3cccf99ad6d3cb593954c68afa145a695a6256054ea511cf7228f4fda5e5aa
- Complete V16 FILES.sha256.json SHA256: 7f665e9a4871b578affd4e37e05d281c5818fe8d46367053f3f01c76c86e5b8a
- Required paired candidate45 PCB SHA256: 9881a992b12fed90f17131ed627f12af77680cc2ddf95030adf8c564aaa24eb2

V16 remains an incremental dependency; obtain/reconstruct its exact full tree through its documented chain. Recover candidate45 with V16 sessions/recovery-v16/rebuild_historical_source.py from its hash-pinned candidate44 project. V17 does not embed those historical packages again.

## Apply and verify, Python standard library only

Supply the independently distributed V17 ZIP hash. All output directories must be new.

```sh
python -B tools/apply_source_delta_v17.py --base /path/to/full-v16 --delta /path/to/routing-source-v17-delta.zip --zip-sha256 V17_ZIP_SHA256 --out /path/to/full-v17
python -B tests/verify_v17_evidence.py --base-project /path/to/candidate45 --out /tmp/v17-portable.json
python -B tests/verify_v17_delta.py --base /path/to/full-v16 --delta /path/to/routing-source-v17-delta.zip --zip-sha256 V17_ZIP_SHA256 --base-project /path/to/candidate45 --out /tmp/v17-clean-application.json
```

Run V17 tests from the full V17 tree. They check only the incremental45/46/47 scope; inherited historical verifiers are not a combined live-status test suite. The optional --historical-workspace flag checks all selected, omitted and recovered source hashes against an original workspace; the clean portability test intentionally omits it.

## Exact paired recovery and construction materialization

```sh
python -B sessions/recovery-v17/rebuild_historical_source.py project --base-project /path/to/candidate45 --source candidate46 --out /tmp/recovered46
python -B sessions/recovery-v17/rebuild_historical_source.py project --base-project /path/to/candidate45 --source candidate47 --out /tmp/recovered47
python -B tests/checkpoint47/materialize.py --base-project /path/to/candidate45 --out /tmp/v17-native-inputs
```

Each recovered paired project contains the board plus all60 unchanged schematic/project/library/parts inputs. Expected board hashes:

- candidate46: 87c5ced471edaf2e0ace382d4236bc1787efb869b7ae759c53d87ee76165c0cb
- candidate47: f7d5731bb0bf1ad314aca6d507da004993671bce413fbdeba545083168e28161

The materialized tree preserves relative locations for both source maps, fixed explicit IDs, support wrappers, native exporters, constructors, exact proposals, finite-audit helpers and owner source/receipts. Candidate01 output directories remain absent, so original constructors can run in a disposable materialization without touching accepted source projects. Original absolute logs and receipt paths are historical evidence, not portable instructions.

## Optional native construction replay, not executed for this release

Use a separately supplied KiCad10.0.6 Python runtime with pcbnew; pin its full build/export behavior to the historical native reports. Regenerate or restore ordinary-routing/candidate45/f722-heli.native.json and candidate46/f722-heli.native.json using the included ordinary-routing/native-tools/export_native_copper.py (--board and --out). Match both exact excluded-file hashes before proceeding. Failure to match is a replay blocker, not permission to edit receipts or weaken binding.

From the materialized tree, run the unmodified ordinary-routing/tests/hv45/construct.py and ordinary-routing/tests/hv46/construct.py in fresh candidate01 directories using that KiCad runtime. RPM uses the sealed rpm-F-final-proposal.json; SBUS uses complete-joint-refined.json and refined-local-repair-results.json. Both need only the corresponding paired source, map/IDs, exporter and proposals already materialized, plus the omitted source native export. SBUS performs a native refill. Compare output PCB hashes with the expected hashes above. Recovery is exact independent of native replay; byte-identical regenerated output is not promised without matching runtime behavior.

The finite geometric audits additionally require Shapely2.x and omitted source/candidate native exports, all hash-verified; original owner review entrypoints also need their wider repository/runtime inputs. The portable verifier does not claim complete native validation replay or supply binary runtimes. No JVM/maze/router/fill/field-solve is run by the portable commands.
