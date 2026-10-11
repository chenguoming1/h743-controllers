# Dependencies for the final corrected power run

The package contains the exact corrected source43 runtime, model templates,
reference ledger and review evidence. `exact-source-manifest.json` records each
recovered file's SHA-256 and its Git blob identity or archive-member provenance.
`DEPENDENCIES.json` gives the precise operational file list and numerical limits.

## Already present

- Seventeen exact historical runtime/launcher sources and the native-export
  helper, plus supporting provenance and pure-data preparation code.
- The exact corrected disabled case plan and terminal registry, the original
  settings and review, and the hash-identical historical reference ledger.
- A separate disabled proposal with only R42.1 and R44.2 changed from F.Cu to
  B.Cu in the registry; all 305 case-definition identities remain unchanged.
- The verified `analysis-environment-restored.json` supplement: Python 3.12.14;
  numpy 2.2.6, scipy 1.17.0, shapely 2.2.0 and sexpdata 1.0.2 resolve through
  explicit `PYTHONPATH=<rebuild-root>/python-deps`. No numerical solve ran.

Preparation and package verification need Python 3.12's standard library only.
The source-only archive does not bundle third-party binaries or a PCB copy.

## Required after final routing and refill

1. Final source-local PCB, native export, parts, parity, process, mechanical,
   critical-connectivity, support, both DRC reports, protection, supplemental,
   summary, adoption, power-revalidation, mechanical-geometry, firmware and pose
   inputs. All exact filenames are listed in `DEPENDENCIES.json`.
2. The full digest-bound dependency closure behind the final support/mechanical
   receipts, and equality with the accepted canonical board and adoption record.
3. A new source-bound implementation/model review for the two registry changes
   and the deliberate launcher/support adaptation. The historical launcher
   retains its original path and schema gates; historical approval does not
   transfer to this disabled proposal.
4. A fresh final plan, release, job and mesh cache after routing releases the
   single shared heavy lane. Record the actual executable/module identities;
   the environment version receipt alone is not a release.

Retain 294 required cases, 11 separate illustrations, ten actual supply windows,
five 35 mOhm copper-only VCAP loops, fixed loads and mode-specific floors, 0.12/
0.09 mm grids, convergence guards and resource caps. The historical runner's
overall false and its four servo-floor failures remain visible.

No old raw numerical result, mesh cache, large archive or active operational
lease is needed or included in this source publication.
