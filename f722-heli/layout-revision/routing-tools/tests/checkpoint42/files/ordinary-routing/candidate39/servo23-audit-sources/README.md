# Sealed SERVO2/3 construction audits

These helpers are separate from every general validator. They only read board,
native, map, plan and construction inputs. They write the explicitly named JSON
audit output. No KiCad, router, JVM or electrical solver is used.

The original source is accepted37 (`2a73d9b7…0c2115`). Stage37 is pinned to
`f2bfe89b…a6deff`. A second explicit basis pins accepted38
(`95bb984b…249c9f`) and stage38 (`e93f1a18…6c8aa5`). Stage38 independently proves
that accepted38 contains all 1,803 accepted37 records unchanged, plus exactly
the 21 hash-bound RPM_LV records and their logical owners. All 21 remain exact
through the SERVO construction. Its additional clearance recheck and helper
are also pinned. There is no generic source-rebase or net-exemption option.

## Current receipts

- `../servo23-native-stage37/servo23-source-change-controls.json`: PASS,
  exactly 10 ordinary SERVO2 and 3 dedicated U12.2 GND records removed;
  38 constructed records match the sealed plan; eight negative controls reject.
- `../servo23-native-stage37/servo23-support-return-audit.json`: PASS, all 28
  support nets connected; separate GND return and both saved planes verified.
- `../servo23-native-stage37/servo23-rewritten-entry-audit.json`: FAIL solely
  for the unfinished P1 via at `(14.85, 9.06)`.
- Stage38 has the same three receipt filenames in `../servo23-native-stage38/`.
  Its endpoint audit compares to accepted37 and covers RPM as well as SERVO.
- Stable stage38 support receipt SHA256:
  `65abfe16c3de637768de8a9e50caf8a99600599ebaa7f8b0293c98ff688a70cb`.

The original stage receipts are preserved. Each stage directory contains
`servo23-<helper>.used.py` copies whose hashes match those receipts. The active
helpers additionally support an explicit exact additive successor and return a
nonzero exit status for endpoint failure. Archival `.used.py` files preserve
the used source; active commands should use the modules in this directory.

Stage38 endpoint results: 51 newly added ordinary tracks, seven reviewed vias
(five new and two retained vias newly contacted), seven full-width pad entries,
zero unresolved contacts. The sole layer-transfer failure is the P1 via, with
F.Cu only. Two buried spurs are recorded as non-evidence; two incidental side
contacts continue to separately verified full-width annular entries. No
threshold was relaxed. Shared endpoints inside real pads are also checked,
including both branches entering U12.4.

## Dedicated ground return

The return has two dedicated F.Cu tracks at 0.25 mm before and after, and one
0.45/0.20 mm plated via. Centerline length changes from 2.192 to 2.2275 mm
(+0.0355 mm). The via moves from `(11.404, 10.7915)` to `(11.27, 10.89)`.

Both source and replacement pass the actual 0.25 mm pad section and finite
full-width actual-annulus strip checks. The restricted pad + two tracks + via
graph is connected without relying on additional shared serial copper.
In1.Cu and In4.Cu each cover the entire conservative actual annulus. On each
plane an explicit 0.25 mm-wide, 0.6 mm-long strip from `(11.42, 10.89)` to
`(12.02, 10.89)` reaches the dominant plane component after 0.125 mm erosion.
The plane proof subtracts every exported drill void and applies an inward
polygon reserve; stage38 uses conservative mitered plane erosion. Thus no new
narrow shared neck is required between this dedicated return and bulk plane
copper. This is nominal geometry and continuity evidence only. Surge,
transient, impedance, inductance, temperature and loaded electrical quality
are not claimed.

All four new signal vias retain the original 0.127 mm saved-plane clearance
check. The observed minimum in both stages is approximately 0.12749913 mm.
The GND via is required to connect to the planes; it is never passed through
the signal antipad-gap test.

## Reproduce stage checks

Run from the `f722-layout-rebuild` directory, with Shapely provided by the
existing `python-deps` directory. Choose a new output filename to preserve the
stable receipts already used by a routing model.

```sh
PYTHONPATH=python-deps python ordinary-routing/servo23-audits/audit_source_change_controls.py --basis stage38 --out ordinary-routing/servo23-audits/recheck-source38.json
PYTHONPATH=python-deps python ordinary-routing/servo23-audits/audit_support_and_return.py --basis stage38 --out ordinary-routing/servo23-audits/recheck-support38.json
PYTHONPATH=python-deps python ordinary-routing/servo23-audits/audit_rewritten_entries.py --basis stage38 --out ordinary-routing/servo23-audits/recheck-entries38.json
```

The last command must exit 1 until P1 is completed. Use `--basis stage37` for
the original source/stage. `--source`, `--stage`, `--origin`, `--plan-dir`,
`--constructor`, `--continuation-helper`, and `--source-audit` permit explicit
path relocation where applicable; they never change the allowed hashes.
The scripts locate the existing `native-tools` relative to `ordinary-routing`.
Keep that directory layout and this complete audit directory when relocating.

## Final additive successor

A stage support receipt can be a baseline for the existing ordinary additive
gates. It does not replace final full-candidate entry validation. A complete
candidate must keep every stage native record and owner exact, contain no
further GND additions, and use only ordinary logical owners from the pinned
model37 owner contract. The exact successor manifest is an explicit record
comparison contract, not proof of engine lineage, route intent, acceptance,
or fabrication readiness.

First prepare its exact manifest, replacing `candidateNN` with the actual
candidate directory:

```sh
PYTHONPATH=python-deps python ordinary-routing/servo23-audits/prepare_successor_manifest.py --basis stage38 --candidate ordinary-routing/candidateNN --out ordinary-routing/candidateNN/servo23-addition-manifest.json
```

Review and use the printed SHA256 as `MANIFEST_SHA` in both commands:

```sh
PYTHONPATH=python-deps python ordinary-routing/servo23-audits/audit_rewritten_entries.py --basis stage38 --candidate ordinary-routing/candidateNN --addition-manifest ordinary-routing/candidateNN/servo23-addition-manifest.json --addition-manifest-sha256 MANIFEST_SHA --out ordinary-routing/candidateNN/servo23-complete-rewritten-entries.json
PYTHONPATH=python-deps python ordinary-routing/servo23-audits/audit_support_and_return.py --basis stage38 --candidate ordinary-routing/candidateNN --addition-manifest ordinary-routing/candidateNN/servo23-addition-manifest.json --addition-manifest-sha256 MANIFEST_SHA --out ordinary-routing/candidateNN/servo23-complete-support-return.json
```

The entry audit always compares the complete candidate against accepted37,
including the stage construction and accepted38 RPM additions. It audits all
new ordinary tracks, their pad terminations (including shared pad endpoints),
and new or newly contacted retained vias. It keeps the same native pad,
transverse-entry, drill-void and finite annular-strip thresholds as the broad
endpoint audit. The final P1 via must have verified entries on at least two
layers. Saved fills are recomputed/read separately by the native owner flow;
this helper only checks the saved candidate export.

The support audit compares to the selected accepted source, rechecks all 28
support nets and the dedicated GND return, and evaluates all additional signal
vias against both saved planes. Candidate board/native/map/manifest hashes
are rechecked at the end. Full native DRC, process, protection cuts, actual IO,
critical-reference, parity, firmware and mechanical gates remain mandatory.

## Negative controls

`audit_source_change_controls.py` rejects wrong source, wrong removed or
constructed owner, undeclared GND removal, other-net addition, moved existing
object, changed constructed segment, and undeclared plan omission.

`audit_successor_controls.py` additionally checks exact additive manifests:
changed/deleted fixed GND, changed existing owner, wrong manifest owner,
undeclared addition, manifest geometry mismatch, even explicitly declared USB
or GND additions, stale manifest digest, and wrong stage source. Its positive
synthetic addition is an in-memory invariance test only; it does not claim
native routing qualification or write any board.
