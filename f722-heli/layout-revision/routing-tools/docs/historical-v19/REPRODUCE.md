# V19 bounded reproduction

## Immutable inputs

- V18 delta ZIP SHA256: `aa92e9f54083491d16d361f15ab0be522c1804b2959e9e1e1466c7f5f80b023b`
- Complete V18 FILES.sha256.json SHA256: `c92ec914f36f2bb31eb134f55f6c2cdd3d163d6ad89a1d078243207a7f619256`
- Paired source48 PCB SHA256: `dcdd0e5655d098ceaffa7f40b6a21f1ca101429ac8eb142c50fa96df86697e68`

Obtain the exact full V18 tree through its documented chain and recover candidate48 with V18 sessions/recovery-v18/rebuild_historical_source.py. V19 verifies all 61 paired base files, including the board and 60 unchanged project/schematic/library/parts inputs, before writing a recovered project.

## Portable application and checks

Use Python 3 standard library with assertions enabled. Run these commands from the complete V19 tree. Supply the independently distributed V19 ZIP SHA256; every output directory must be new.

```sh
python -B tools/apply_source_delta_v19.py --base /path/to/full-v18 --delta /path/to/routing-source-v19-delta.zip --zip-sha256 V19_ZIP_SHA256 --out /path/to/full-v19
python -B tests/verify_v19_evidence.py --base-project /path/to/candidate48 --out /tmp/v19-portable.json
python -B tests/verify_v19_delta.py --base /path/to/full-v18 --delta /path/to/routing-source-v19-delta.zip --zip-sha256 V19_ZIP_SHA256 --base-project /path/to/candidate48 --out /tmp/v19-clean-application.json
python -B sessions/recovery-v19/rebuild_historical_source.py project --base-project /path/to/candidate48 --source candidate49 --out /tmp/recovered49
python -B tests/checkpoint49/materialize.py --base-project /path/to/candidate48 --out /tmp/v19-native-inputs
```

The application script is available in changed/tools/ inside the hash-verified delta. It validates the complete immutable base, archive identity/member paths/digests, full result manifest and allowlist before output. V19 tests cover only the incremental 48→49 scope. Inherited historical verifiers require their own historical status files and inputs. The optional --historical-workspace flag additionally checks original source bytes; clean portability intentionally omits it.

Expected49 board SHA256: `15499b28bb63a8c2326c8c7e73dbac4198b8333b05325ab35653825848ae9069`. Materialization retains historical relative locations and source aliases for the frozen .used.py files. Eleven raw files remain explicitly omitted. Historical logs and absolute paths are evidence, not portable commands.

## Native construction replay, not executed for V19

Use a separately supplied, matching KiCad 10.0.6+dfsg-1 Python/pcbnew environment in a disposable materialization. Restore or regenerate ordinary-routing/candidate48/f722-heli.native.json with the supplied native exporter and verify its exact excluded digest before continuing. The selected source48 map, fixed IDs, project-preservation manifest, final proposal and frozen construct_mcu.py provide the construction inputs.

The constructor requires ordinary-routing/tests/port-a48/candidate01 to be absent. Materialization places historical classifier references in that directory, so move the receipt-only directory to a separate evidence archive before running the unchanged ordinary-routing/tests/port-a48/construct_mcu.py. It creates candidate01 and refills the board. Compare its output to the exact49 board digest above. Do not overwrite accepted paired projects or archived evidence.

Full finite geometry, reference classification and access-screen replay additionally need matching native exports and Shapely/GEOS plus wider documented source dependencies. Classifier receipts report Shapely 2.2.0 and GEOS 3.14.1. Planning helpers may refer to excluded peer-reservation hypotheses; the final accepted proposal is sufficient for constructor replay, but rerunning the earlier proposal search is not claimed to be self-contained. Full native validation/placement/power replay inputs and runtimes are not embedded.

Every restored dependency must match its recorded hash. Mismatches are replay blockers, not grounds for altering receipts or weakening predicates. Exact paired recovery is independent of native replay; byte-identical regenerated native output is not promised without matching runtime behavior.

The capture recipe tools/prepare_compact_v19.py is intentionally one-shot and refuses existing staging/freeze directories. Do not rerun it over a sealed package. The saved worker 138-file seal is separate from owner metadata extensions; changing one requires a new explicit receipt rather than editing the historical handoff.
