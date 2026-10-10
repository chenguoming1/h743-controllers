# Bounded V15 recovery and verification

V15 is a delta over the complete immutable V14 source tree. Retain its exact manifest and supply the published V15 ZIP digest separately.

```sh
python3 -B tools/apply_source_delta_v15.py --base /path/to/immutable-v14 --delta /path/to/routing-source-v15-delta.zip --zip-sha256 PUBLISHED_V15_ZIP_SHA256 --out /new/path/to/v15
```

The external recovery input is the 61-file candidate43/accepted43 paired project recovered by V14. All 61 hashes and lengths are checked before outputs are created. Only the routed board changes; its project, schematic hierarchy, libraries, rules and parts metadata remain paired and exact.

```sh
python3 -B sessions/recovery44/rebuild_historical_source.py project --base-project /path/to/exact-candidate43 --source candidate44 --out /new/path/to/candidate44
python3 -B tests/verify_v15_evidence.py --base-project /path/to/exact-candidate43 --out /new/path/to/evidence.json
python3 -B tests/verify_v15_delta.py --base /path/to/immutable-v14 --delta /path/to/routing-source-v15-delta.zip --base-project /path/to/exact-candidate43 --zip-sha256 PUBLISHED_V15_ZIP_SHA256 --out /new/path/to/portable.json
```

The other recovery label is candidate43. Selected evidence can be recovered with tests/checkpoint44/materialize.py; `--base-project` also recovers both projects. Omitted raw exports are deliberately unavailable through this tool. `tools/capture_v15_evidence.py --workspace ...` refreshes only selected exact files and refuses changed source hashes.

The standard-library verifier checks all selected bytes, the 47 sealed dependency digests, owner-adoption dependencies, paired project identity, all 32 constructed tracks/five vias against proposal geometry and deterministic UUIDs, the exact copper transaction and all 156 complete footprints/558 pads. It reruns the exact independent owner's parser-based coordination verifier and requires a byte-identical original receipt. It also reruns the unchanged support adapter, seven existing typed-support controls, and ten separate full-entry/native/wrapper/group binding mutation controls. Recovery/path and delta-integrity controls reject malformed inputs.

The 22 full finite-width geometric controls and seven exact reference controls are retained original results. No native DRC, native exporter, board constructor/refill, geometric/reference classifier, JVM route search or numerical solve is run. The native-support adapter's `typed_audit_binding_checked=false` remains truthful; the separate portable binding check does not turn it into a typed adapter.

For an independently provisioned native audit replay, recover the paired boards, materialize selected evidence and inherited helper inputs, provision matching KiCad 10.0.6+dfsg-1 and the recorded geometry toolchain, regenerate excluded exports at their recorded paths, and require the exact hashes in tests/checkpoint44/raw-evidence.json. The full DSM audit uses ordinary-routing/dsm44-audits/audit_dsm44_entries_support.py. It requires the omitted exact exports and cannot run from receipts alone. Upstream route-search grids and all transitive historical replay inputs are not bundled; complete-tree-proposal.json already contains the selected construction geometry. Regeneration and full native replay are neither performed nor guaranteed by this packet. Never replace a required exact export with a small projection or report receipt checks as a fresh geometry pass.
