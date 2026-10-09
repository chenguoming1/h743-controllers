# Prototype static power validation

This bundle preserves 107 portable controls and the runtime used for the corrected candidate19 conditional screen. Its 62 required conditional voltage cases, five DC VCAP copper loops and numerical gates pass on 0.12/0.09 mm grids. The original overall runner boolean remains **false** because one of 11 separate high-load/lost-feed illustrations fails four servo floors. Those approximate DC endpoints exceed the stated continuous source envelope and have no assigned duration. This is not final-board, thermal, AC or flight qualification.

See [CANDIDATE19-COMBINED-REVIEW.md](CANDIDATE19-COMBINED-REVIEW.md), `candidate19-combined-summary.json` and `candidate19-runtime-identity.json` for results, conditions and hashes. `candidate22-power-result-applicability.json` proves exact modeled-input applicability to a later source while preserving candidate19 as the numerical source.

`MANIFEST.json` is the exact allowlist. No PCB, complete native export, expanded executable ledger, full 115 MB result, numeric arrays or environment is included. Tests and disabled compiler inputs are self-contained with pinned dependencies. Actual native-result reproduction additionally requires the external archived inputs listed by hash. Five runtime modules match the run byte for byte; the sixth corrects only a unit typo in a docstring, with executable AST equality verified.

## Reproduce the controls

Tested with Python 3.12.14 and the exact pins in `requirements.txt`: NumPy 2.2.6, SciPy 1.17.0, Shapely 2.2.0 / GEOS 3.14.1 and sexpdata 1.0.2.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -B -m unittest -v \
  test_static_validation test_case_compiler test_native_edge_noding \
  test_linear_backend test_mesh_cache test_result_evidence \
  test_loaded_pilot test_power_geometry_comparison test_refined_pilot \
  test_grid_edge_noding test_element_operator test_combined_summary \
  test_result_applicability
```

Expected: 107 passing controls. `synthetic-tests.json` records the actual bundled run and source hashes. No project PCB is loaded. Tests cover finite/grouped contacts and aliases, real drill/fill holes, narrow feeders, barrel spans, conserved source/return power, finite contacts, stale-source/compute gates, exact ancestry/seams, numeric-cache corruption/caps, mixed precision, physical condensation and scope classification.

The synthetic native-fill fixture can be regenerated with KiCad 10.0.6's `pcbnew` Python: `python generate_native_fill_fixture.py --out fresh-native-fill-fixture.json`. Export decodes fractured contours by exact reversed integer bridge cancellation; it never repairs, saves or refills a PCB.

## Bind and audit a new source

The case plan and terminal registry remain disabled/unbound. Generic freeze/ledger templates have false execution flags, no source paths and no load/material defaults. Measured four-conductor harness resistances remain unset and excluded. The plan distinguishes 0.32 A electronics, classic 20 mA DSM, capacity 0.50 A DSM and USB 0.30 A with external loads disconnected. Load allocations are adversarial vertices, not measured shares. Same-BEC 20/40/50/80 mΩ profiles are illustrative; capacity DSM does not inherit classic receiver accuracy.

The generator enumerates 310 primary definitions and 178 dependent selectors, not executed or historical cases. Dependent weakest-allocation slices stay disabled until validated rankings exist. The completed run executed only its selected 73 cases on two grids.

Finish and independently gate an immutable source copy. With KiCad 10.0.6, export saved geometry:

```sh
python export_native_copper.py --board board.kicad_pcb --out owner-native.json
```

The source directory must contain `f722-heli.kicad_pcb`, `owner-native.json`, current `parts.json`, `owner-parity.json`, `owner-process.json`, `owner-mechanical.json`, `owner-critical.json`, `power-audit.json`, `owner-drc.json`, `owner-drc-all.json`, `owner-protection.json` and `owner-supplemental.json`. Those independent board reports are external inputs. Set `SOURCE_FOR_REBIND` to the directory actually checked:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python compile_power_ledger.py \
  --source "$SOURCE_FOR_REBIND" --plan case-plan.disabled.json \
  --registry terminal-registry.disabled.json --settings compiler-settings.refined.json \
  --out compiled-preflight
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python prepare_loaded_pilot.py \
  --compiled compiled-preflight --out combined-prepared --refined-combined
```

Compilation verifies hashes, actual parts and pad/net/layer identities, finite contact unions and ideal-land aliases, without meshing. The refined selector requires 60 shared-ABC/classic-or-capacity cases at 5 V, two USB cases, 11 servo/feed illustrations and five VCAP loops: 13 networks / 99 contacts with 41 GND contacts. Repeated `--evidence receipt.json` arguments preserve additional passed source-bound reports.

Refined settings explicitly model 105 °C copper, 15 µm effective copper/plating and 95% IACS. These are assumptions, not fabrication measurements or execution permission. Final-board mode additionally requires zero opens and passing protection checks. Power-only mode may exclude unrelated ordinary opens and cannot qualify a completed board. Every later drill, fill, contact, part or modeled copper change requires fresh binding.

## Execute after compute release

After source acceptance and allocation of the single heavy-process slot, prepare a separate released copy:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python prepare_loaded_pilot.py \
  --compiled compiled-preflight --out combined-released --refined-combined --release
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python combined-released/solver-source/run_bounded_pilot.py \
  --freeze combined-released/freeze.json --ledger combined-released/ledger.json \
  --wall-seconds 1500 --memory-mib 4096 \
  --out combined-released/result.json --mesh-cache private-numerical-cache
python summarize_combined_pilot.py --result combined-released/result.json \
  --freeze combined-released/freeze.json --ledger combined-released/ledger.json \
  --out combined-summary.json
```

The wrapper sets one native numerical thread before imports and enforces the exact frozen budget: 25 minutes / 4 GiB for this refined scope; the legacy default remains 20 minutes. Candidate19 reached its last field stage in 873.09 seconds and recorded 1.75 GiB peak RSS. Neither runtime nor convergence is guaranteed for another board. The full 310-case ledger is not implied to fit the pilot budget.

Exit 0 means preflight or success of the complete selected screen; 1 means a completed screen failed at least one selected case/loop/guard; 2 means refusal. Preserve the runner boolean. The summarizer reports required voltage, VCAP, numerical and illustrative scopes separately. Partial grids on a later refusal remain unqualified.

For a different source with exactly equal modeled inputs, compile/prepare that source first and use `bind_result_applicability.py --help`. The read-only comparison checks the complete electrical job, actual copper/fills/all drills/stackup/ports, parts and runtime/compiler identities. It preserves the original result, never transfers a cache and cannot convert a scoped result into final-board qualification.

## Geometry and numerical interpretation

Native integer-nm vertices, holes and contacts remain authoritative. Derived intersections require unique exact ancestry, finite source coverage and rational area/orientation certificates. Exact grid-edge crossings are inserted before clipping; distinct intersections remain separate or refuse if binary64 collapses them. Grid-specific certificates retain exact hashes. Represented area deltas and rounding are recorded. No geometry repair, blanket snapping, native-vertex removal or positive-area deletion is allowed.

The 1e12 element-condition limit is numerical. Contact-membership allowance is 2e-8 mm, or 0.02 nm. Actual drill voids, narrow intermediate paths and finite barrel resistances remain in the network. Feed sharing comes from the circuit.

The cache holds checked geometry/material arrays and a double matrix used only as the LU preconditioner. Its identity includes source, contacts, stackup, material, grid, dependencies and geometry-builder code. The accurate longdouble physical operator is rebuilt from unchanged elements. Identical ideal node IDs have exactly zero energy while retaining every triangle record; partial condensation uses the singleton gradient; three-node elements use stable gradient-vector Gram products. Wide refinement, KCL and matching voltage-difference field/loss recovery survive cache reload. No voltage basis is serialized. All residual, energy, reciprocity and grid-margin gates remain unchanged. Platforms without wider-than-float64 arithmetic refuse this backend.

## Evidence and limits

The two compact candidate19 refusal receipts preserve the earlier grid and double-assembly failures. A small native annulus fixture, independent local-review identities and separate saved-mesh diagnostic preserve their controlled corrections. Previous native negative controls remain. Files named `historical-v5-*` and the old prepared73-case plan describe the previous archive, not this successor's defaults or runtime. Its failed peripheral/grid screen remains historical evidence.

Two-grid sensitivity is not a rigorous discretization/manufacturing bound. Fixed-temperature loss/density is not temperature rise, ampacity or pulse capability. Ideal lands omit within-land/pin/solder heating. Efficiency, off-condition switch resistance and extra regulation allowances are explicit modeled inputs. U9's 4.3 V accuracy-condition screen is separate from its 3 V operating minimum. Remaining upper / 12.6 V, efficiency/leakage/resistor-temperature/line-load cases, measured harnesses, local bypass dynamics, startup/handover, VCAP AC stability, EMI/ESD, production and flight qualification need separate evidence.

The unchanged legacy names `historical-runtime-identity.json` and `public-v5-test-run.txt` are also retained for overlay compatibility. Like their explicitly named historical copies, they describe the previous v5 archive and do not identify the current runtime.
