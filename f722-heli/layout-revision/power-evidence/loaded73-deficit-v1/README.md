# F722 independent power-drop evidence, public v1

The +5V_BEC route presents a real copper-loss risk at the declared 2 A stress corner. The independent no-FEM lower bound is 329.779267 mV across 15 mandatory straight sections. This is a geometry/material diagnosis, not an accepted system rating.

Read REPORT.md first. The modeled material is 105°C, 15 µm uniform copper, 95% IACS and 15 µm plating. The loaded run completed two grids and 73 cases per grid, but its maximum voltage-grid change, 1.434151 mV, exceeds the locked 1 mV criterion. All 11 impedance gates pass. No accepted voltage convergence or thermal/flight qualification is claimed.

## Included and omitted

- receipts/independent-checks.original.json: untouched original analytic bound, per-section identities and contact areas.
- receipts/independent-checks.portable.json: same numerical/geometrical check reproduced by the explicit-input portable script; new script/projection hashes.
- receipts/source-bound-evidence.original.json: compact voltages, currents, losses, device/terminal mappings and source hashes extracted from the released full result.
- receipts/run-status.compact.json: selected original summary fields, with its original hash and projection declaration.
- receipts/candidate15-to-candidate16-loaded73-geometry.json: exact modeled-power applicability from 70-open candidate15 to 69-open candidate16. It transfers geometry evidence only; it does not rebind or accept the numerical run.
- receipts/candidate15-bec-mandatory-barrel-cuts.json: original finite topology receipt proving the mandatory In2↔In3 continuation.
- originals/: byte-preserved original report and historical scripts, for provenance. Those scripts retain their original workspace paths. Use scripts/ below for reproduction.

The full result (~85 MB), full native geometry, native boards, complete ledger, 25 frozen dependencies, and FEM runtime are not bundled. They remain external archived owner inputs. The forthcoming compact owner power-evidence bundle also omits the full result and native export; obtain those exact source files separately to reproduce the analytic check or extraction. No unverified download link is claimed. This package is not a self-contained FEM reproduction kit.

## Reproduce the analytic bound

Requires Python 3.12, Shapely 2.2.0 / GEOS 3.14.1 and NumPy 2.2.6. This was verified with Python 3.12.14. Shapely/NumPy are external installed dependencies, not copied here. No SciPy, KiCad or FEM runtime is imported by the analytic script. Use an environment providing those versions; package installation is not performed by these scripts.

Supply these exact original files from the owner’s archived source inputs:

| Argument | Original file | Required SHA-256 |
|---|---|---|
| --native | owner-native.json | dc1aa86cd3969eb2f0444674adef7f948b46cb50ad07d4d56d1efa3ba083febd |
| --board | f722-heli.kicad_pcb | 23232e7bc1903c06c1809d569c91e4cb161281be9225f3776076386593e55674 |
| --ledger | ledger.json | 61c27f88dceb64d27e0cc700a8306de07543d5e268d5a4e2419bb81a44f3a8be |

From this folder, replace the example absolute paths with the files' actual locations:

```sh
python scripts/reproduce_analytic_bound.py \
  --native /path/to/power-input/owner-native.json \
  --board /path/to/power-input/f722-heli.kicad_pcb \
  --ledger /path/to/power-release/ledger.json \
  --out /path/to/new-audit-output.json
```

The script rejects a changed source hash and compares its bound, inventory, contact regions and accepted/excluded sections with the original receipt. Its output path must be writable and should be outside this sealed folder. It reconstructs native topology and an analytic energy lower bound; it performs no mesh construction or electrical solve.

## Re-extract the full-run scalars (optional)

scripts/extract_full_result.py uses Python's standard library. It requires the omitted original result, freeze manifest, ledger, input directory and frozen runtime directory. --input-dir holds the input files named by the freeze manifest; --runtime-dir holds the seven frozen pilot source files. The script resolves these supplied directories explicitly and verifies all 25 frozen hashes. It does not execute the runtime or reproduce an FEM solve.

```sh
python scripts/extract_full_result.py \
  --freeze /path/to/power-release/freeze.json \
  --ledger /path/to/power-release/ledger.json \
  --result /path/to/power-release/result.json \
  --input-dir /path/to/power-input \
  --runtime-dir /path/to/power-release/solver-source \
  --out /path/to/new-compact-evidence.json
```

Original full result hash: 0780cece1cf4194220a542f9d7f65cc6be3dc457b9bbfaf74bd5a07fa3a1d9ac. The original frozen runtime hashes remain in receipts/source-bound-evidence.original.json; see the owner's full power bundle for those source bytes and any actual numerical rerun procedure.

## Provenance and sealing

ORIGINAL-PROVENANCE.json separates original identities from portable projections. MANIFEST.json hashes every delivered file except itself; MANIFEST.sha256 hashes that manifest. Verify with scripts/verify_manifest.py. The version is sealed after reproduction and verification. The owner should copy this folder intact. Corrections must be a new version, with new hashes; do not edit a sealed receipt and retain the previous identity.
