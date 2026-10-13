# Clean native0 conditional DC replay and compact result review

Current PCB: `84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd`.
Current native logical identity: `04d8ecd80edf004f3226f204f23adba51692a498ae38edc183debeffb704603d`.
Model contract: `285961cbf0d79d0ae28e2e2a84b256380da8c6a922b6977a2495b7554c922a95`.

All 294 required accessory/logic/USB cases pass on both grids, as do all 15
network convergence checks and all five VCAP resistance loops. None of those 294
cases includes servo loading. All 11 servo scenarios remain illustrations. The
single-feed all-cyclic 905X illustration draws 18.560991391 A and fails four
6 V servo board-pad floors; the full raw aggregate remains false with exit 1.
All six heavier illustrations exceed the version-qualified 10 A continuous BEC
specification. See TECHNICAL-REPORT.md and the complete evidence/ case envelope,
servo examples and source-current accounting for the actual operating scope.

## Exact source and shared dependencies

Keep this dc/ directory beside the checkpoint's exact hardware/ and native/
directories. Native0 has 331 actual drilled objects, including every all-net
void on its spanned copper layers. Fresh current metadata/support inputs,
107 finite contacts, 268 physical power pads and 44 saved-plane return witnesses
are bound. The moved U15 ground pads have static support; this is not an injected
U15 load or transient ESD test.

The package uses hash-verified repository-relative files from
`../../native1-mosi-baro-v1-20261013/dc`: nine byte-exact numerical Python modules,
three byte-exact model inputs, and the full 6.8 MB ledger. The predecessor package
manifest is pinned to
`cbaf8190130046f2dc2bee0581863ebc9d520701d081f27f6c0a1391413b1cbc`.
REUSED-DEPENDENCIES.json and PACKAGE-MANIFEST.json list each exact file.
No network fetch or floating dependency is used.

The current lossless_native_input.py is included locally because its four
native gzip/logical identity constants changed with the PCB. Its functions and
all physics algorithms remain unchanged. ledger-binding.json applies exactly
one in-memory edit to the shared ledger: /freeze_manifest_sha256. The complete
resulting serialized ledger identity is pinned, and every model field is
regenerated and compared exactly during verification. No case, contact, grid,
floor, material, convergence or resource limit is reduced.

NORMALIZATION.json lists original/public stored identities and changed JSON
pointers or text lines. Private historical locators become relative references
or content identities; coordination-only metadata is removed. References to
changed documentary copies are updated explicitly. The documentary native DRC
producer is an original-producer identity record, not an executable DRC recipe.
Other provenance snapshots document the current extraction; numerical replay
consumes their frozen outputs. The checkpoint's native hardware replay owns
fresh source export and native checks. The full numerical source itself is
byte-exact to the completed run.

## Tested lightweight checks

Use Linux and nonoptimized Python with bytecode writes disabled. These commands
were tested during packaging and regenerate no geometry, mesh or solution:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B dc/replay.py verify
PYTHONDONTWRITEBYTECODE=1 python3 -B dc/review_reduced.py --out /tmp/native0-reduced-review.json
```

The first checks every local/shared/source hash, regenerates the complete model
and compares its 15-network, 107-contact, 294-required/11-illustration, five-loop
ledger. The second independently recomputes all 610 case rows and 9,500 actual
positive-minus-return-pad probes, min/max decisions, cross-grid voltage guards,
15 impedance comparisons, five loop sums and 30 VCAP leg convergence checks.
Its scientific arithmetic block is byte-identical to the completed independent
review; REDUCED-CHECKER-ADAPTATION.json records that identity and the changed
input-admission/output scope. It preserves every failed servo row and overall
false. The checker uses 512 MiB address space and a 90-second CPU bound.

## Heavy replay commands: supplied, not executed for packaging

Use CPython 3.12.14 and the pinned requirements.txt versions. Prepare repeats
preflight and the complete finite-port audit; run then solves the two-grid
model. Each source module is first materialized byte-exactly under the output
directory so the unchanged validator's sibling-module hash checks still apply.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B dc/replay.py prepare --out /tmp/native0-dc-replay
PYTHONDONTWRITEBYTECODE=1 python3 -B dc/replay.py run --out /tmp/native0-dc-replay
```

Fresh output stays under /tmp. Limits are one CPU/thread, 4 GiB address space,
600 seconds prepare and 1,800 seconds run, a local exclusive lock, 800 MiB launch
admission, 128 MiB reserves on source/output volumes and a 512 MiB combined
package/output cap. An incomplete result or resource stop is not accepted.
Exit 1 can mean a complete overall-false result; inspect the case failures.
Portable output hashes bind the new manifest and execution and are not expected
to reproduce historical provenance bytes.

## Full raw omission and review limits

This compact publication contains the complete reduced case/probe, port-matrix,
loop, convergence and balance data with current source and verifier receipts.
It omits the full 31,564,460-byte compressed field stream, meshes and caches.
The exact raw result is preserved locally:

- Stored gzip SHA256: `a56f50ed965b6aaec75a0d77f4be5af4a9d3fa3cf23bdb65ea1b8a4aaa9cb401`
- Logical JSON SHA256: `ff4671a226068efdf29def43ad26a434f0d88a4dea7dbd3541689531da641eb3`
- Logical bytes: 318,863,747

The historical full verifier receipt records the original reconciliation of all
610 cases and 150 full geometry certificates. Without the omitted raw archive,
that full-field reconciliation cannot be repeated from the compact publication.
The supplied reduced checker says this explicitly; it validates the published
scalar evidence rather than claiming fresh verification of absent raw fields.
A fresh bounded numerical replay regenerates full fields with new provenance.

The result is conditional fixed-temperature DC at 105 °C with 0.015 mm
copper/plating and 95% IACS. The largest fine VCAP loop is 26.324493 mΩ against
35 mΩ. Ideal terminals/package distribution and the stated component/source
assumptions remain. AC/ESD behavior, startup, thermal rise, local ampacity,
installed harness suitability, manufacturing, flight and final-board adoption
are outside this diagnostic.
