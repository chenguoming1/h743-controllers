# V18 bounded reproduction

## Required immutable inputs

- V17 delta ZIP SHA256: `d87f7e9a0e9ab14de4668fe09031d01e272073b4a827c755a465866ae3d002c8`
- Complete V17 FILES.sha256.json SHA256: `cad265201d7fa7e4260bb66d83e5027cce81ea0ee8e4d2c04d4b0204e503ca6e`
- Candidate47 PCB SHA256: `f7d5731bb0bf1ad314aca6d507da004993671bce413fbdeba545083168e28161`

Reconstruct the exact full V17 tree through its documented immutable chain. Recover candidate47 with V17's sessions/recovery-v17/rebuild_historical_source.py and the required candidate45 base. V18 requires all 61 candidate47 paired files, not just its board, and verifies each before writing outputs.

## Portable application and verification

Use Python 3 standard library, with assertions enabled; run commands from the complete V18 tree. Supply the separately distributed V18 ZIP SHA256. Every output directory must be new.

```sh
python -B tools/apply_source_delta_v18.py --base /path/to/full-v17 --delta /path/to/routing-source-v18-delta.zip --zip-sha256 V18_ZIP_SHA256 --out /path/to/full-v18
python -B tests/verify_v18_evidence.py --base-project /path/to/candidate47 --out /tmp/v18-portable.json
python -B tests/verify_v18_delta.py --base /path/to/full-v17 --delta /path/to/routing-source-v18-delta.zip --zip-sha256 V18_ZIP_SHA256 --base-project /path/to/candidate47 --out /tmp/v18-clean-application.json
```

The application script is also present under changed/tools/ in the delta, so it may be inspected/extracted after independently verifying the ZIP identity. It validates the complete V17 manifest/allowlist, archive names/digests, and complete resulting V18 tree before writing. The portable evidence test verifies only V18's incremental47→48 scope. Inherited historical verifiers require their historical status files and inputs; they are not one combined live-status test suite. Optional --historical-workspace additionally verifies the excluded/recovered/selected original source hashes; clean portability intentionally omits it.

```sh
python -B sessions/recovery-v18/rebuild_historical_source.py project --base-project /path/to/candidate47 --source candidate48 --out /tmp/recovered48
python -B tests/checkpoint48/materialize.py --base-project /path/to/candidate47 --out /tmp/v18-native-inputs
```

Expected candidate48 board SHA256: `dcdd0e5655d098ceaffa7f40b6a21f1ca101429ac8eb142c50fa96df86697e68`. Each project includes its board plus 60 unchanged schematic/project/library/parts inputs. Materialization preserves original relative evidence and source locations. It does not supply the 13 excluded files. Original logs contain historical workspace paths and are evidence, not portable commands.

## Optional native construction replay: not run for V18

A native replay requires separately supplied KiCad 10.0.6+dfsg-1 Python/pcbnew behavior and any matching source geometry dependencies. Restore or regenerate candidate47/f722-heli.native.json with the included exporter and verify its exact excluded hash first. Run native work only in a disposable materialization, outside accepted projects. The original ADC constructor uses ordinary-routing/tests/adc-bus45/candidate01 as a new output directory. Materialization places historical reference receipts there, so move that receipt-only directory aside to a separate evidence archive before invoking the constructor; do not overwrite or delete its evidence. Then the unmodified ordinary-routing/tests/adc-bus45/construct.py can build candidate01 from the paired47 source, map, IDs and proposal. It performs a refill. Compare the output to the exact candidate48 board hash.

The finite audits and fresh classifier also require matching Shapely/GEOS and source/candidate native exports. Stored classification reports specify Shapely2.2.0 and GEOS3.14.1. Full owner validation and placement reproduction require their wider repository, pinned original project and runtime inputs; those are not claimed to be fully embedded here. Restore every excluded dependency at its exact path and verify its digest before attempting the corresponding historical command. A mismatch is a replay blocker, never permission to change a receipt or weaken a predicate.

Exact project recovery is independent of native replay. Regenerated native byte identity is not promised without matching all runtime and input behavior. Portable checks do not execute KiCad, Shapely/GEOS geometry, JVM routing, fills or power solves.

The original tools/prepare_compact_v18.py is the historical one-shot capture recipe and refuses existing staging. This recovered packet continues the already completed capture; do not rerun that recipe over a sealed package.
