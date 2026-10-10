# Bounded V14 recovery and verification

V14 is a delta over the fully verified immutable V13 source tree, not a standalone replacement for it. Recover V13 with its existing chain, retain its exact manifest, and supply the published V14 ZIP digest separately.

```sh
python3 -B tools/apply_source_delta_v14.py \
  --base /path/to/immutable-v13 \
  --delta /path/to/routing-source-v14-delta.zip \
  --zip-sha256 PUBLISHED_V14_ZIP_SHA256 \
  --out /new/path/to/v14
```

The required external recovery input is the 61-file candidate41/accepted41 project recovered by V13. All 61 hashes and lengths are checked before any output is created. The exact project file, schematic hierarchy, libraries, parts metadata and rules travel with the board.

```sh
python3 -B sessions/recovery43/rebuild_historical_source.py project \
  --base-project /path/to/exact-candidate41 \
  --source candidate43 --out /new/path/to/candidate43
python3 -B tests/verify_v14_evidence.py \
  --base-project /path/to/exact-candidate41 --out /new/path/to/evidence.json
python3 -B tests/verify_v14_delta.py \
  --base /path/to/immutable-v13 --delta /path/to/routing-source-v14-delta.zip \
  --base-project /path/to/exact-candidate41 \
  --zip-sha256 PUBLISHED_V14_ZIP_SHA256 --out /new/path/to/portable.json
```

Other recovery labels are candidate41, candidate42, i2c-native-stage39, i2c-native-stage39-master-sda and i2c-native-stage39-complete-trunks. The historical stage projects are selected constructor inputs only; their inclusion does not adopt them. The two placement deltas use exact candidate43 as their base. The preview removes copper for display; the recipe reconstruction proves poses/pads and is not a routed-board construction.

Selected evidence can be materialized with tests/checkpoint43/materialize.py. `--base-project` also recovers all six paired projects. Omitted raw exports are deliberately unavailable through this tool. `tools/capture_v14_evidence.py --workspace ...` refreshes only the already-selected exact files and refuses any changed source hash.

Portable checks use the Python standard library. They verify all selected bytes, sealed dependency digest declarations, all recovered files, parsed41→42→43 copper transactions, complete footprint identities and bound native predicted-footprint hash, typed support adoption, recipe 156 poses/558 complete pad records, preview bindings, and malformed recovery/archive refusals. The seven typed support mutation controls are executed. The ten native transformation, nine intentional-reference and eight finite-width geometric controls are preserved original results, not rerun by this command.

No native DRC, refill, exporter, constructor, preview renderer, topology/reference classifier, JVM route search or power/FEM solve is run. Do not report any of those as a new portable pass. The source-bound original intentional-reference helper needs the omitted exact native exports; its original receipt can be checked here only by hashes and stated results.

For an independently provisioned full native replay, first recover the exact paired boards, use matching KiCad 10.0.6+dfsg-1 and the pinned native exporters, regenerate the excluded exports at their historical paths, and require each resulting hash to match tests/checkpoint43/raw-evidence.json. Materialize selected constructors/proposals and inherited dependencies at their recorded paths in a disposable workspace. Candidate39 and earlier source dependencies come from the V13 recovery chain. Compare every source-bound input before running original audits. Regeneration and full native replay are neither included nor verified by this packet; never substitute a smaller projection for a required exact export.
