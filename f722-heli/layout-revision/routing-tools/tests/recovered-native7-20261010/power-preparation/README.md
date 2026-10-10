# Corrected F722 power preparation: source publication

Status: preparation only. Current power is STALE. No meshing, numerical solve,
native execution, board edit, source adoption, release, or electrical acceptance
was performed here. Final routing and saved refill must finish first.

## Recovered source

The 42 files listed in `exact-source-manifest.json` are bound to repository
`chenguoming1/h743-controllers`, commit
`a15d07d7d314b40589c52d545cf8d0cde9aa9ec6`, tree
`5e8748de94eb6da6057cae5e116cf3339083a014`.
Standalone files were checked against their exact Git blob identities. Five
necessary JSON members were extracted from the verified published source43
archive, with each member checked against its published SHA-256. The historical
reference ledger was reconstructed from the embedded JSON and matched its exact
original file SHA-256. `archive-recovery-receipt.json` records the archive checks.
The binary archive, raw numerical results, raw meshes and vendor archives are
excluded from this package.

`published/` and `frozen-minimum/` preserve historical bytes unchanged. Their
historical reports and approvals apply only to their recorded historical source.
The later `prepared-native7-v4-disabled/` directory is a separate, disabled
proposal. It does not inherit the source43 implementation approval.

## What was checked

- Current board SHA-256: `a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f`
- Current native SHA-256: `53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505`
- All 107 model contacts / 109 actual pads were checked against PCB text and the
  source-bound native export: UUID, net, copper layers and global coordinates.
  All 93 additional power/control/sense contract entries also match.
- Exactly two historical contact layer assignments differ: R42.1 (`+5V_PERIPH`,
  UUID `ffcaa37f-4c24-41b4-9aba-10376242234e`, at 15.71, 4 mm) and R44.2 (`GND`,
  UUID `69dd15ed-318d-4e07-93df-53253587847d`, at 15.5, 4.89 mm) are on B.Cu.
  The disabled proposal changes only those two registry layer bindings and its
  derived model contract. It also refreshes observation metadata and clears the
  old implementation approval from proposed settings.
- All 305 case-definition hashes are unchanged: 294 required conditional cases
  and 11 separately scoped illustrations. The ten actual device supply windows,
  five 35 mOhm copper/barrel-only VCAP loops, 15 networks, material assumptions,
  fixed loads, mode-specific floors, both grids and convergence/resource guards
  are preserved. These are coverage checks, not numerical pass results.
- Five mesh-free guard tests pass, including rejection of EN4 substituted for
  TPS2553 IN6, a falsified pad layer or coordinate, and an incorrect board hash.

## Repeat the preparation

Python 3.12 standard library is sufficient. The script imports only the restored
pure-data model/contract modules. It has no solve or launch option. Use a fresh
output directory below this package; it refuses to overwrite an existing one.

```sh
python -B prepare_final_power.py \
  --source ../recovered-native7/ordinary-routing/tests/native13-access/joint-native-import11-v1/candidates/published-reference02 \
  --expected-board-sha a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f \
  --expected-native-sha 53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505 \
  --out repeat-native7-disabled
python -B -m unittest -v test_preparation
```

The board/native pair is deliberately not duplicated into this source package.
Provide the exact source directory as shown, or a final source with its explicit
new hashes. For a source-local `owner-native.json`, add
`--native-name owner-native.json`. The script rejects unexpected terminal/part
changes; such changes need a reviewed new preparation, not a widened allowlist.
The tests target the retained native7 reference source.

## Minimum dependencies and final release boundary

`DEPENDENCIES.json` lists exact recovered runtime files, hashes, model inputs,
review evidence and all 18 source/pose filenames required by the preserved
launcher. A fresh final run also needs the complete digest-bound support and
mechanical dependency closure, canonical/adoption equality, final native gates,
and a new source-bound implementation/model review.

The source43 launcher deliberately retains its original canonical-path and
support-schema gates. It cannot be replayed on this restored layout or the
disabled layer proposal. Its path/support adaptation must be reviewed separately;
no old approval, hash relabeling, or lower-level solver invocation may bypass it.
The final runtime must retain the single shared heavy lane, 1 numerical thread,
4 GiB address-space bound, 1500-second wall bound, and fresh job/cache identities.

The later solver needs Python 3.12 with numpy 2.2.6, scipy 1.17.0, shapely 2.2.0
and sexpdata 1.0.2, with executable/module identities recorded. The added exact
`analysis-environment-restored.json` receipt records all four required versions
available through explicit `PYTHONPATH=<rebuild-root>/python-deps`. This supersedes
the earlier default-interpreter package observation recorded in the original
preparation. No numerical solve was performed. These module-version checks do
not grant a numerical release; the final source-bound review must still bind
executable and module identities. Native export and final refill require the
separately restored KiCad 10.0.6 environment.

## Retained invalidity and scope

Pre-correction USB/DSM numerical claims used TPS2553 EN4 in place of IN6 and/or
DPS368 CSB2/SDO5 in place of VDDIO6/GND1 and VDD8/GND7. They remain invalid.
Correct TPS terminals are IN6, OUT1, EN4, GND5 and EP7. The exact embedded old
reference ledger is input to the preserved corrected transformations, not an
accepted electrical result. No historical 4008-solver claims, 146 replay cases,
140 endpoints or 5532 sensitivities are promoted.

The corrected source43 historical overall false and runner exit code 1 remain:
its 18.560272 A single-feed illustration failed all four 6.0 V servo-pad floors,
outside the 10 A continuous envelope. VCAP's 35 mOhm screen covers copper and
barrels only; R16 and capacitor ESR are outside that budget. These prototype DC
cases do not qualify thermal behavior, nonlinear interior extrema, signal
integrity, startup, production or flight readiness.

## Publication variant and verification

This publication adds the analysis-environment receipt and readable dependency
and validation summaries. The original sealed recovery package remains separate.
All historical published source bytes, disabled proposed inputs and their 305
case identities are unchanged. No preparation or numerical job was rerun to
make this variant. `PACKAGE-MANIFEST.json` seals the exact publication files.

- `DEPENDENCIES.md` summarizes what is present and what the final run needs.
- `VALIDATION.md` explains completed checks and their limits.
- `PUBLICATION-SUMMARY.json` links original and publication identities.

After extracting the source package, run `python -B seal_recovery.py --verify`
from its `power-recovery-prep` directory to check all included file identities.
This verification needs no PCB, native runtime or numerical packages.
