# Prototype static power validation

This bundle preserves tested DC copper/circuit tooling and 67 small analytical, compiler, geometry, cache and solver controls. Native attempts on one provisional power-support source have not produced a converged two-grid VCAP loop result. The latest full attempt passed the three coarse-grid network solves and then refused a receipt serialization comparison before the fine mesh. A tested canonical-JSON correction is included; its native retry remains pending.

`MANIFEST.json` is the exact public allowlist and SHA-256 inventory. No PCB, full native export, matrix arrays, environment or expanded case ledger is bundled. The two small source-bound geometry regression fixtures total about 40 kB. `native-refusals.json`, `native-linear-diagnostic.json` and `native-receipt-roundtrip.json` preserve compact evidence with source/result hashes. They do not qualify this or any later board.

## Reproduce the controls

Tested with Python 3.12.14, the exact dependency pins in `requirements.txt`, and Shapely's GEOS 3.14.1 runtime. Use one native numerical thread:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -B -m unittest -v \
  test_static_validation test_case_compiler test_native_edge_noding \
  test_linear_backend test_mesh_cache
```

Expected: 67 passing tests. `synthetic-tests.json` binds the actual bundled test run to source hashes. No project PCB is loaded. Coverage includes finite/grouped native contacts; drill voids and saved-fill holes; point-touch and disconnected rejection; barrel spans; narrow feeders; coupled return voltage, finite contacts and converter input-power conservation; unequal same-source feeds; reciprocity/convergence; stale-source and compute/thread gates; exact ancestry, seam and area checks; numeric-cache corruption/caps; mixed-precision residuals; and receipt roundtrip/refusal controls.

`native-fill-fixture.json` is a synthetic KiCad 10.0.6 polygon set with holes and a disconnected outline. With that version's `pcbnew` Python, regenerate it using `python generate_native_fill_fixture.py --out fresh-native-fill-fixture.json`. The exporter decodes fractured fills by exact reverse integer bridge cancellation. It does not repair geometry or save/refill a PCB.

## Disabled requirements and cases

`case-plan.disabled.json` has false execution and null freeze binding. `terminal-registry.disabled.json` retains terminal intent without an adopted board hash or pad UUIDs. Generic freeze/ledger templates are disabled, without source paths or load/material defaults. Measured four-conductor harness resistances remain unset and are excluded by the compiler.

The project plan separates 0.32 A electronics, classic 20 mA DSM, capacity 0.50 A DSM, and USB 0.30 A configuration with external loads disconnected. It includes shared AB/AC/BC 2 A loading, actual positive/return pad intent, conserved converter power, auxiliary-current accounting and conditional voltage floors. Ten aggregate-load vertices are adversarial allocations rather than measured shares. Same-BEC 20/40/50/80 mΩ profiles are explicitly illustrative, with mismatch and feed-loss boundaries. KST high-load DC endpoints retain their approximate-current, unknown-duration and overload limitations. The capacity DSM case does not inherit the classic receiver guarantee.

Compiler outputs contain 170 baseline, 40 upper and 100 bounded servo definitions, combined into a 310-case primary ledger. These are newly enumerated definitions, not executed cases or historical results. Another 178 dependent selectors stay disabled until actual source-bound baseline rankings exist. `activate_ranked_slices.py` preserves separate weakest sampled locations for distinct voltage constraints and rejects invented rankings.

Settings are explicit modeled assumptions: 105 °C, 0.015 mm effective copper/plating, 95% IACS. They are not fabrication measurements. Select and review the resource/material settings deliberately. The larger pilot settings select sparse direct solving, two grids and 900k nodes/1.8M triangles; they do not authorize execution.

## Bind and audit the final source

Finish the intended board scope, refill/save it, and independently check one immutable copy. Export saved native geometry with KiCad 10.0.6:

```sh
python export_native_copper.py --board board.kicad_pcb --out owner-native.json
```

The project compiler requires a source directory containing `f722-heli.kicad_pcb`, `owner-native.json`, current `parts.json`, `owner-parity.json`, `owner-process.json`, `owner-mechanical.json`, `owner-critical.json`, `power-audit.json`, `owner-drc.json`, `owner-drc-all.json`, `owner-protection.json`, and `owner-supplemental.json`. Those acceptance reports come from the board workflow, not this bundle.

Set `SOURCE_FOR_REBIND` to that actual directory. For final validation, copy the selected settings to `settings.final.json`, set `scope` to `final-board`, and describe the actual source stage. Compile to a new directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python compile_power_ledger.py \
  --source "$SOURCE_FOR_REBIND" --plan case-plan.disabled.json \
  --registry terminal-registry.disabled.json --settings settings.final.json \
  --out compiled-preflight
```

The compiler checks every evidence hash, actual selected parts and pad/net/layer identities, finite contact unions and ideal-land aliases. It copies the inputs, stamps every case and audits five loop definitions without meshing. Final mode requires zero opens and passing protection checks. Power-only settings permit explicitly excluded unrelated ordinary opens and cannot qualify a completed board. Every later track, drill antipad, fill or part change requires fresh evidence and rebinding.

## Bounded numerical execution

After allocating the single heavy-job slot, compile again to a new directory with `--allow-numerical`. Review the selected ledger and use its matching freeze. The following shows the interface; the full primary ledger is not implied to fit a short pilot:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python run_bounded_pilot.py \
  --freeze compiled-released/freeze.json \
  --ledger compiled-released/ledger-primary.json \
  --out compiled-released/result.json --mesh-cache private-numerical-cache
```

The wrapper sets one BLAS/OpenMP thread before imports, enforces a 4 GiB address-space cap and 20-minute alarm, and requires external scheduling of one heavy job. No source is edited. Exit 0 means preflight or conditional enumerated-screen success, 1 means a completed screen did not pass, and 2 means refusal. Completed coarse-grid data on a later refusal is retained as explicitly unqualified partial data.

The optional cache stores numeric-only NPZ arrays and integrity-checked JSON. It binds board/native geometry, contact order, material, stackup, spacing, dependencies and geometry-builder source. Solver-only changes may reuse identical geometry, with original provenance retained. Corrupt, stale or resource-ineligible cache entries cannot silently qualify. Save matrices before solving and keep them out of published source bundles.

Sparse direct solving checks finite coefficients, symmetry, positive diagonal and anchored connectivity. It uses diagonal scaling, a bounded reusable double LU with `MMD_AT_PLUS_A` ordering, and longdouble solution/residual refinement. Platforms without wider-than-float64 arithmetic refuse this backend. The saved-matrix diagnostic reduced approximately 1e-9 A residuals below 7.1e-13 A with unchanged coefficients and acceptance thresholds. That one-grid diagnostic is separate from loop compliance. Linear, full KCL, energy, reciprocity, mesh sensitivity and margin gates remain mandatory; failed histories are preserved.

## Geometry and interpretation

Grid anchors use exact decimal rationals. Derived native-edge intersections require unique exact integer/rational ancestry, covered source intervals and shared seam nodes. Native vertices, holes, contacts and exact rational ring areas are preserved. Represented binary64 area deltas and every derived coordinate correction are recorded. A residual/angle-derived position bound plus a 1 pm absolute cap limits numerical representation correction; this is not a fabrication tolerance. Unknown/ambiguous ancestry, collapsed identities and invalid topology refuse. Canonical JSON comparison keeps cached/fresh certificates content-identical without confusing tuple/list representation.

No positive-area triangle is discarded. The 1e12 element condition guard is numerical rather than a physical error guarantee. Finite-contact membership has a 2e-8 mm roundoff allowance. True drills, intermediate narrow copper, actual copper unions and finite barrel resistance remain in the network. Feed sharing comes from the circuit, never an assumed split. Two-grid sensitivity is not a rigorous discretization/manufacturing bound.

Fixed-temperature DC loss/density is not temperature rise, ampacity or pulse capability. Ideal lands omit within-land, pin and solder heating. Efficiency, off-condition switch resistance and extra regulation allowances are modeled sensitivities; U9's 4.3 V accuracy screen is distinct from its 3 V operating minimum. Startup, handover/backfeed, converter dynamics, VCAP AC stability, ripple, EMI/ESD, assembly, production and flight qualification require separate evidence and measurement. A provisional result never substitutes for the later fully routed board.
