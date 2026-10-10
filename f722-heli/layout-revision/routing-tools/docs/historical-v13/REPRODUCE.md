# V13 bounded verification and recovery

Use Python 3 with `-B`. These checks need the complete immutable V12 source tree and the separately published V13 ZIP SHA-256. They also need accepted39's exact 61-file contract: PCB plus 60 preserved non-board inputs, including parts.json. The pair manifest pins every input hash and length.

V12's recovery42 produces 62 files, including two license copies absent from40/41, but does not by itself add parts.json. Obtain parts.json from V12's included `tests/checkpoint42/files/ordinary-routing/candidate39/parts.json` (SHA-256 `99e1589baf2033bc696613ad52c5deab3403397d7caafff6d8aa011296846858`). Alternatively V12's materializer with its required candidate37 base supplies both recovered39 and this included parts file. The V13 recovery ignores extra base files. It does not remove them or alter any source.

```sh
python -B apply_source_delta_v13.py --base V12 --delta routing-source-v13-delta.zip --zip-sha256 PUBLISHED_ZIP_SHA --out V13
python -B V13/tests/verify_v13_evidence.py --base-project EXACT39 --out evidence-verification.json
python -B V13/tests/verify_v13_delta.py --base V12 --delta routing-source-v13-delta.zip --zip-sha256 PUBLISHED_ZIP_SHA --base-project EXACT39 --out portable-verification.json
python -B V13/sessions/recovery41/rebuild_historical_source.py project --base-project EXACT39 --source candidate41 --out EXACT41
python -B V13/tests/checkpoint41/materialize.py --base-project EXACT39 --out EVIDENCE41
```

Extract the apply script from `changed/tools/apply_source_delta_v13.py` in the ZIP before the first command, if needed. Destinations must be new; keep verification outputs outside sealed trees. The apply tool checks the ZIP, complete base, every changed file and the complete resulting manifest/allowlist before writing. The clean delta test invokes only the V13 verifier, not historical test suites.

The materializer restores included evidence at its original relative paths and 61-file paired projects for 39/40/41. Excluded raw inputs fail explicitly. Exact recovery does not execute KiCad, constructors, geometry or electrical solvers. Standalone project recovery omits route maps/receipts; the materializer supplies them.

Recover the historical placement-only board, whose copper and non-rule zones were removed in an isolated copy:

```sh
python -B V13/sessions/recovery41/rebuild_historical_source.py file --base-file EXACT41/f722-heli.kicad_pcb --delta V13/sessions/recovery41/placement-preview.pcb.delta.json --out placement-preview.kicad_pcb
```

## Optional fresh placement reproduction, outside portable verification

The exact `integrated-routing/render_placement_previews.py` source and bound 41 poses are materialized in EVIDENCE41. With KiCad 10.0.6 Python available and the matching CLI at the helper's documented sibling `kicad10-runtime/kicad-cli` location, run from that recovered workspace:

```sh
KICAD_PY -B integrated-routing/render_placement_previews.py ordinary-routing/candidate41/f722-heli.kicad_pcb ordinary-routing/candidate41/poses-native.json --out fresh-placement41
```

`KICAD_PY` is the locally verified KiCad interpreter/wrapper, not a bundled executable. The helper validates all 156 poses, uses a disposable board, removes copper/non-rule zones, hides values and exports front plus mirrored-back SVG. It writes the source/poses/preview/output hashes. Rasterize each SVG using an installed SVG renderer such as Inkscape; raster/font versions may alter PNG bytes. Compare the new bindings; do not relabel different output bytes as the preserved preview. Packaging itself only verifies the original SVG/PNG hashes and exact placement-board recovery. Existing visual-review.json records the owner's earlier pixel review and its stated clipping/qualification limits.

## Construction and geometric audit replay boundary

Constructor source paths are `ordinary-routing/construct_dsm_complete40.py` and `ordinary-routing/construct_dsm_clear41.py`; their copied used sources and exact proposal inputs are retained. Both constructors have fixed output directories and require them absent. Run only in a new disposable workspace containing the relevant source stage, maps, preserved project inputs and all externally restored bound exports. Never run them over recovered evidence directories or use their output as adoption without new gates.

The full entry/return audit is `ordinary-routing/dsm41-audits/audit_dsm41_entries_return.py`, depending on the retained DSM40 and servo23 geometry helpers. Its included input manifest is authoritative. Full replay requires the excluded exports and matching polygon library/runtime; see EXCLUDED_INPUTS.md. No full native construction or geometric replay is claimed by the commands above.
