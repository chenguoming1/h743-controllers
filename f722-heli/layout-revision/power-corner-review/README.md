# Historical F722 source19 circuit corners

This compact packet contains circuit evidence on the sealed source19 two-grid port matrices, with the preserved candidate24 applicability receipt. It does **not** qualify candidate26 or any later board with changed copper, drills, antipads or fills. No new mesh or loaded field is included or claimed.

The original result remains unchanged: 62 required cases, five VCAP DC loops and numerical gates pass; its overall result is false because of the overloaded lost-feed illustration. The 5,532-case sensitivity sweep retains 642 failures in the extrapolated U7=60 mΩ combined stresses. See REPORT.md and results-summary.json for margins, conditional budgets and physical tests.

## What can be reproduced

- The original dc_circuit.py and power_case_model.py are byte-identical copies.
- portable_model.py contains selected reviewed functions; exact source identities and symbol names are listed in source-identities.json.
- Inputs include both full small port matrices, the deterministic case plan, the two archived USB definitions, and source-voltage bounds. Generating all 5,532 case definitions must reproduce the original case-list hash.
- Fourteen controls, fourteen representative numerical cases, all 140 endpoints, the full sensitivity sweep, and individual stored budget brackets can be replayed without native geometry or the old raw results.
- Inverse searches are optional and separately bounded. The U8 3 V searches stop on grid convergence, so their physical maximum remains unresolved.

The impedance export is a **trusted sealed input** here. This packet cannot independently re-extract contacts, rebuild native/FEM geometry, repeat mesh convergence, recover loaded fields, or verify the omitted original archive. Source-identities.json preserves the raw-result hashes and byte sizes. The candidate24 receipt is preserved evidence, not re-created in this packet. Two input endpoints and ten allocation vertices are not a continuous-input/all-distributions guarantee.

## Dependencies and commands

Use Python 3.12 on POSIX with NumPy 2.2.6. SciPy, Shapely, KiCad and a mesh cache are not required. The file named copper_fem.py is expressly only the original-compatible Refused exception, allowing the circuit solver to remain byte-identical; it is not a field solver. Installing requirements is a separate user/environment step. No command downloads anything.

Run from this folder, using one numerical thread:

```sh
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
python3 -m unittest test_port_corners test_port_sensitivities -v
python3 portable_runner.py verify
python3 portable_runner.py sample
python3 portable_runner.py endpoints
```

Optional complete circuit replay or one inverse boundary:

```sh
python3 portable_runner.py sweep --out ../replayed-sensitivity-summary.json
python3 portable_runner.py budget-check --environment combined --target u7
python3 portable_runner.py budget-check --environment combined --target joint_error
python3 portable_runner.py budget-search --environment combined --target u7 --out ../replayed-u7-search.json
```

Each runner call has a 300-second wall cap, 4 GiB address-space cap and one-thread requirement. A timeout aborts; it is not converted into a physical boundary. Existing output files are not overwritten. Full original case outputs are intentionally omitted. Optional searches may produce larger local output files outside this packet.

Numerical replay uses 1e−10 V comparison tolerance where saved scalar values are available, while the original 1 mV voltage-grid guard remains unchanged. Exact floating-point result hashes may depend on the recorded NumPy/BLAS environment; manifest and case-definition hashes are exact. No numerical comparison tolerance is added to physical margin.

## Integrity and scope

manifest.json binds every distributed source/input/result-summary file. verification.json separately binds the manifest and records checks actually run. Neither a SHA-256 match nor the original numerical gates establishes thermal, dynamic, manufacturing or flight qualification.

No component change is justified by the extrapolated 60 mΩ stress alone. Physical work still includes effective U7 resistance at ~2 A and actual temperature, static source-error budgets, sustained low-input U6 boost capability, current-limit behavior, real harness/contact losses, ripple/startup/switchover and component temperatures. Modeled 105°C copper is not ambient or junction temperature; fitted X5R capacitor bodies remain limited to 85°C.
