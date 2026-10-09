# Prototype static power validation

This bundle preserves completed analysis tooling and **35 passing synthetic/compiler controls**. Three bounded attempts on one provisional power-support board refused before the first native mesh completed. There is no native resistance, current, voltage, loop-compliance, thermal or flight result. The unfinished rational-intersection correction is excluded.

`MANIFEST.json` is the publication allowlist and SHA-256 inventory. Copy only its listed files and the manifest. No board, large WKB geometry, cache, environment, expanded case ledger or private path is included. `native-refusals.json` retains compact source/code/result hashes and the exact last triangle diagnostic; it is evidence of refusal, not electrical acceptance. Reproducing those board attempts additionally requires the exact board and independent reports identified by their hashes.

## Reproduce the controls

Tested with Python 3.12.14. Install the exact dependency versions in `requirements.txt`:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python -B -m unittest -v test_static_validation test_case_compiler
```

Expected: 35 passing tests. `synthetic-tests.json` binds the actual test result to this bundle's sources. KiCad is unnecessary for these small analytical fixtures. Coverage includes finite and grouped contacts, real drill voids, saved-fill holes, point-touch/disconnected rejection, barrel spans, narrow feeders, current/power conservation, real return voltage, converter power, same-source unequal feeds, three-grid conformity, reciprocity, convergence, stale/unfinished-source refusal, hash-bound cases, compute/thread gates, report-only headroom, exact empty-overlay handling, canonical decimal grid anchors and triangle conditioning refusal. Tiny well-shaped elements are retained; unresolved elements refuse.

`native-fill-fixture.json` is a synthetic KiCad 10.0.6 polygon set with holes and a disconnected outline. With that version's `pcbnew` Python runtime, regenerate independently using `python generate_native_fill_fixture.py --out fresh-native-fill-fixture.json`. The fill exporter decodes fractured storage using exact reversed integer bridge cancellation, preserving surviving edges, vertices and signed area. No contour repair is used.

## What is disabled

`case-plan.disabled.json` contains requirements, assumptions and sensitivity dimensions, with false execution and null freeze binding. `terminal-registry.disabled.json` contains terminal intent only, with no adopted board hash or pad UUIDs. The generic freeze/ledger templates are also disabled and have no source paths or material/load defaults. None is directly executable.

The explicit compiler settings are reviewable modeled inputs, not measured fabrication or harness values. They use 105 °C, 0.015 mm effective copper and plating, and 95% IACS. `compiler-settings.json` has smaller resource caps; `compiler-settings.pilot.json` has explicit 900k-node/1.8M-triangle limits. Select settings deliberately. Their power-only scope permits unrelated ordinary opens and never qualifies the completed board.

The plan separates 0.32 A electronics, classic 20 mA DSM, capacity 0.50 A DSM and USB 0.30 A configuration with external loads disconnected. It retains AB/AC/BC shared 2 A cases, real power/return ports, converter total-efficiency sensitivities, conditional voltage floors and explicit auxiliary-current accounting. Ten full-load allocation vertices are adversarial spatial samples, not historical current shares. Same-BEC measured four-conductor resistances remain null and are excluded. Published 20/40/50/80 mΩ examples are illustrative, including mismatches and feed loss. KST high-load DC endpoints retain their stated overload, unknown-duration and unqualified-envelope limitations.

## Bind a new frozen source

First use the board workflow to finish the intended scope, refill/save it, and independently check the exact immutable copy. This bundle never refills or saves a PCB. Export saved native geometry with KiCad 10.0.6:

```sh
python export_native_copper.py --board board.kicad_pcb --out owner-native.json
```

The project adapter `compile_power_ledger.py` requires a source directory containing these fresh reports:

- `f722-heli.kicad_pcb`, `owner-native.json`, current `parts.json`
- `owner-parity.json`, `owner-process.json`, `owner-mechanical.json`, `owner-critical.json`
- `power-audit.json`, `owner-drc.json`, `owner-drc-all.json`
- `owner-protection.json`, `owner-supplemental.json`

These are board-workflow inputs; this bundle does not manufacture their acceptance receipts. Set `SOURCE_FOR_REBIND` to their actual directory, then compile into a new output directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python compile_power_ledger.py \
  --source "$SOURCE_FOR_REBIND" --plan case-plan.disabled.json \
  --registry terminal-registry.disabled.json --settings compiler-settings.pilot.json \
  --out compiled-preflight
```

The compiler checks source hashes, actual selected part identities and finite native pad/net/layer bindings, copies evidence, stamps every resolved case, audits 106 contact intents and five loop definitions, and leaves numerical execution false. Power-only scope preserves failed unrelated protection rows as excluded evidence; a failure involving a tested power net refuses. No mesh or circuit runs during compilation.

It prepares 170 baseline definitions, 40 upper-receiver checks and 100 bounded same-BEC illustrations, combined in a 310-case primary ledger. These are new definitions, not executed cases or recovered historical results. The 178 weakest-allocation sensitivity selectors remain deferred until source-bound numerical rankings exist. `activate_ranked_slices.py` requires actual converged baseline evidence and chooses weakest sampled locations separately for each voltage constraint; it refuses guessed rankings.

For the final routed board, copy the selected settings to a new file, set `scope` to `final-board`, describe the actual final source stage, and rerun the same compiler command against fresh final reports. Final mode requires zero opens and passing protection checks. Any later track, drill, fill, part or solver change invalidates the binding. A provisional source result cannot stand in for the final board.

## Numerical execution and refusal

Allocate one heavy job before using the compiler's `--allow-numerical` flag in a new output directory. The locked output must not be edited in place. Bound a selected, reviewed numerical ledger with the supplied wrapper:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python run_bounded_pilot.py \
  --freeze compiled-released/freeze.json \
  --ledger compiled-released/ledger-primary.json \
  --out compiled-released/result.json
```

This is an execution recipe, not a recommendation to run the full case set as a short pilot. The wrapper enforces one process, one native numerical thread, a 4 GiB address-space cap and a 20-minute overall alarm. Mesh/resource/conditioning failures stop honestly. Exit 0 is preflight success or conditional enumerated-screen success; 1 means limits/convergence did not pass; 2 means refusal. The package's current native-board attempt remains refused because a near-collinear intersection requires further robust common-edge noding.

Grid coordinates come from exact decimal rationals with one binary64 conversion. Native vertices and generated intersections are not rounded to merge nodes. The 1e12 element Jacobian-condition bound is a numerical refusal threshold, not an error guarantee. Finite-contact membership uses a 2e-8 mm (0.02 nm) roundoff tolerance. KCL, energy, reciprocity, two-grid sensitivity and margin checks remain required. Different positive/return branches, intermediate narrow traces, actual drill antipads, overlapping copper unions and finite barrel resistance remain in the network; no equal feed split is assumed.

Fixed-temperature DC loss and density are not temperature rise, ampacity or a pulse rating. Ideal lands omit internal pin/solder/land heating. Efficiency, off-condition switch resistance and additional regulation allowances remain modeled sensitivities. U9's 4.3 V accuracy-condition comparison is separate from its 3 V operating minimum. Startup, handover/backfeed, converter dynamics, ripple, VCAP AC stability, EMI/ESD, production variation, assembly and flight qualification require separate evidence and measurements.
