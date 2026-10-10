# Corrected power-validation implementation v3

This is the actual isolated compiler, preparation, preflight, reporting and launcher migration. The sealed v1 proposal, sealed v2 implementation and all historical source19 files/results remain unchanged. **No real-board compilation, staging, native mutation, heavy release or numerical run was performed.** The implementation is ready for owner review; source-specific stage/preflight remain untested runtime gates.

## V3 source integration correction

Independent review found that v2 could not enter a source job: it required legacy `native_sha256` and `pad_group_count` fields missing from the valid candidate41 DSM wrapper, and it selected stale trial27 poses. V3 fixes these actual blockers without changing the v2 physical model or numerical core.

`support_receipt.py` verifies explicit legacy, DSM and I2C schemas. `owner_support_contract.py` is a byte-identical pinned copy of the owner's current support verifier. The adapter binds the full predecessor chain, nested audit hashes, source/candidate native bytes, nonempty true gates, exact per-net UUID sets and single groups. Unknown schemas, incomplete receipts, split/duplicate/omitted pads, stale dependencies and optimized Python refuse. It emits a separate derived connectivity proof; original receipts retain their real fields and schemas. The compiler pins copied evidence for the entire verified chain in the freeze.

The planner selects the source's own `poses-native.json`, or an explicitly supplied `--poses` file, only when its SHA matches `owner-mechanical.json`. It never silently chooses trial27. Planning and later execution recheck every support-chain dependency. Any new source must pass a fresh canonical/adoption/native/pose rebind.

`source-check-candidate43.json` records read-only inspection of accepted candidate43 and a historical candidate41 DSM regression. Both source variants produce valid 15-net connectivity shapes and preserve exact part/contact/net/layer identities. Candidate43 uses the legacy39 → DSM41 → I2C43 chain, with 11 bound evidence files, and its approved pose SHA is `f234abbe2f8d458fb2e623499a6f79449f19d07448ba1a51d53141547b73ba41`. This receipt is not a staged job, approval, or numerical acceptance.

Review `implementation-v2-v3.diff` for the narrow runtime changes, then the retained physical model below. V2's earlier receipt remains sealed as historical implementation evidence; its first-stage integration defects are explicitly superseded here.

## Implemented scope

- Correct U10/U11 TPS2553 DRV supply paths from EN4 to IN6; correct U10 IQ and preserve EN as a separate control probe. Audit U5–U9 physical power/sense roles without changing their existing valid unions/ties.
- Replace CSB2/SDO5 barometer injection with actual U4.6/GND1 and U4.8/GND7 supplies. Include FB1/FB2 series resistance, downstream U1.13, U2.5 and U2.8 contacts and actual local returns.
- Generate42 bounded allocations per context, keeping total0.32A BEC/0.30A USB, each filtered branch≤20mA, and combined IMU VDD+VDDIO≤20mA. The1Ω hot-bead limit is a conditional project test bound, not a manufacturer guarantee.
- Verify that the historical two USB seeds and each ten-case BEC group differ only in explicitly removed allocation fields. Any source/mode/load/assumption difference refuses. The bound context hashes produce6 BEC groups×42 +1 USB group×42 =294 required cases, plus11 unchanged external load/feed illustrations.
- Remove the obsolete single-vertex `CORE_actual_adversarial_sink` report. Ten actual supply-pad probes own acceptance in every new case. BEC MCU VDD uses2.7V for the pinned216MHz/scale1/overdrive/7WS mode; USB uses3.0V for full FS electrical specifications. Other fitted devices use their individual supply limits. VDDA's conservative2.7/3.0V screen does not close tracking or analog-accuracy requirements. VBAT, CSB and VDDA-to-VDD differences remain separate role reports.
- Derive and bind the exact used-network/contact identity. Current templates derive15nets/107contacts/41GND contacts; those counts are outputs, not geometry assumptions. Preserve five35mΩ VCAP loops,0.12/0.09mm grids,105°C copper,15µm copper/plating,95% IACS, convergence rules and numerical/resource caps.

The convex-weight witness proves coverage of the stated **current polytope only**. Conserved-power converter equations are nonlinear; enumerating its vertices does not prove all interior voltage extrema. Actual package/exposed-pad current sharing remains unverified. Scalar DC windows do not establish component temperatures, VDDA tracking, signal levels, startup, USB coexistence, ripple, AC stability or flight qualification.105°C is copper temperature, not ambient or an allowed component body temperature.

U11 quiescent/enable demand and other CORE-powered bias were already included once in the inherited0.32A/0.30A electronics aggregate. No separate U11 load is added on top. **Its individual IQ/EN injection locations and current distribution are not separately resolved** by the seven unfiltered/three filtered supply allocation model; actual-pad voltage probes do not close that gap. TI's140µA on-state reference uses6.5V/open OUT/20kΩ ILIM, and the±0.5µA EN-current test uses0/6.5V. Those conditions do not establish a guaranteed actual3.3V bound. A future dedicated physical load must use an explicitly reviewed bound, be deducted from the aggregate and change the model identity. Pin5/exposed-pad sharing remains unverified. U10's explicit140µA IQ screen is retained at IN6/GND5, with its inherited condition caveat. No auxiliary2mA sensitivity slices are active. The dormant historical `added_auxiliary_U10.4` label has a correction rule to IN6; it must be renamed if regenerated for future publication and must never make EN4 a power-current entry.

## Identity and execution gates

`model_contract.py` binds every exact case hash/order/scope, all operational job categories and the dynamic contact set. Compiler, preparation, preflight, launcher and actual-sink reporting share that contract. Rehashing an altered case cannot hide a role, floor, branch-resistance or current-allocation change. Historical ledger/results cannot satisfy the corrected model identity.

`MODEL-REVIEW.json` pins the implementation scripts, launcher, templates, historical seed identity and official pin/branch evidence. It is an implementation-review artifact, not an approval or source freeze. The planner requires its exact explicitly owner-reviewed SHA. The compiler emits disabled freezes only and refuses direct numerical release. Preparation requires an explicit board SHA to enable a release.

The launcher preserves complete source/adoption/native/DRC checks, canonical-board equality, actual interpreter/package identity, immutable stage inventories, source/freeze/ledger/result binding, fresh-output/cache requirements, exceptions/partial evidence and the shared advisory heavy lock at `static-power-validation/.f722-heavy-slot.lock`. Overriding the canonical board path to evade a changed source refuses. The lock covers cooperating launchers only. The routing owner must explicitly release the sole heavy lane.

`post` always refuses: the old146 circuit replays,140 endpoints and5532 sensitivities are disabled until their definitions are regenerated from the corrected model. No historical pass count, inverse allowance or cache is inherited.

`summarize_combined_pilot.py` includes the strict actual-sink report and preserves required/illustrative/VCAP/numerical scopes and the raw runner boolean. The report checks every case, probe, physical p−n voltage, threshold and two-grid guard. Refused/partial work cannot qualify a completed scope.

## Review and future owner-operated commands

Run from this directory. Do not run stage or launch until their respective owner gates are met. The source below is an example binding to the currently inspected accepted43; use the owner's intentionally frozen source and explicit SHA if routing advances.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=../python-deps python3 -B plan_power_revalidation.py plan --source ../ordinary-routing/candidate43 --expected-board-sha 1ee7174a578dffe4d5ef3ae8b39d8dc88f28b80395539263a65f23be234c21e6 --owner-reviewed-model-sha OWNER_REVIEWED_MODEL_REVIEW_SHA --job job-candidate43 --out plan-candidate43.json
```

Record the returned plan SHA. Planning does not compile, stage, mesh or solve. It checks the actual runtime and complete accepted-source receipts. Once the owner authorizes source staging:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=../python-deps python3 -B plan_power_revalidation.py stage --plan plan-candidate43.json --plan-sha RECORDED_PLAN_SHA
```

Stage compiles the actual305-case primary ledger, runs native finite-contact/connectivity and mesh-free preflight checks, and retains a disabled numerical freeze. It may refuse if the additional rail/return topology or source evidence is incomplete. These real-board runtime gates have not been exercised by this implementation task.

Only after successful staging and explicit release of the sole heavy lane for this source:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=../python-deps python3 -B plan_power_revalidation.py launch --plan plan-candidate43.json --plan-sha RECORDED_PLAN_SHA --owner-released-board-sha 1ee7174a578dffe4d5ef3ae8b39d8dc88f28b80395539263a65f23be234c21e6
```

The runner retains1500s/4096MiB/one numerical thread with the existing outer1530s watchdog. Corrected runtime is unmeasured.305/73 case growth does not imply4.18× factorization time: exact operators are reused within one source/contact/grid identity, while new networks/contacts and additional loaded-field recoveries have different costs. Never relax caps or grids silently; preserve refusals and partial output.

## Verification

`test_corrected_migration.py` checks context equivalence, constrained allocations, physical roles, source and model identities, immutable case/contact definitions, prepared metadata with mocked native I/O, mode floors, actual-pad reporting, failure preservation and release refusal. Retained public-v6 synthetic regressions cover geometry, element operators, conservation, conditioning, cache identity, partial-grid failure and scope classification. Native geometry and audit I/O are mocked in the serialization integration test; no project board is staged by tests.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=../python-deps python3 -B -m unittest -v test_corrected_migration test_revalidation_plan test_static_validation test_exact_native_contours test_native_edge_noding test_linear_backend test_mesh_cache test_result_evidence test_grid_edge_noding test_element_operator test_combined_summary
```

The final transcript is `test-run.txt`: 126 tests pass, comprising the prior 114 tests, ten adapter/source tests and two owner contract suites (seven refusal mutations each). All fixture mutations use temporary directories. Candidate41 and candidate43 board/receipt reads are read-only; no test stages a project board.

Reproduce the full final test run from the project directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=python-deps:power-terminal-correction-v3 python3 -B -m unittest discover -s power-terminal-correction-v3 -p 'test_*.py' -v
```

Reproduce source inspection from the project directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=python-deps:power-terminal-correction-v3 python3 -B power-terminal-correction-v3/inspect_source_readonly.py --source ordinary-routing/candidate43 --expected-board-sha 1ee7174a578dffe4d5ef3ae8b39d8dc88f28b80395539263a65f23be234c21e6
```

`implementation.diff` covers runtime changes against historical code; `implementation-v2-v3.diff` isolates this integration fix. `MODEL-REVIEW.json` lists unchanged numerical core files separately; `MANIFEST.json` inventories the deliverable. Original73-case selectors are intentionally superseded in this new directory rather than weakening their historical tests or editing old evidence.

`seal_implementation.py` creates the review, both diffs and manifest in a fresh implementation directory. It refuses an existing manifest, stale test transcript, changed inspected source, modified v1/v2 artifacts or changed historical runtime/results. This task recovered a review and both diffs sealed before an interruption, then completed the missing manifest using `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=../python-deps python3 -B seal_implementation.py --finish-manifest`. That explicit recovery mode verifies and preserves the prior review/diff bytes; it cannot replace their identity. Owner approval remains a separate action after review.
