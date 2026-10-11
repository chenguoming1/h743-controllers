# Native7 incremental routing importer v1

This is a source-bound CAD constructor, not a router or an acceptance gate. It copies exactly the checkpoint manifest's 61 paired hardware inputs into a **new** directory, removes declared native route objects, adds complete recorded recipes, refills with official KiCad 10.0.6, and exports through the unchanged published native exporter and exact contour decoder. No source file is edited. Existing warnings and open connections are not cleared or reclassified.

The immutable source is `../ordinary-routing/tests/native13-access/joint-native-import11-v1/candidates/published-reference02/`. Source PCB SHA-256 is `a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f`; native export SHA-256 is `53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505`. `empty-plan-v1.json` supplies the complete four-hash source binding, including the checkpoint manifest and checkpoint logical-route map. Incidental source PRL files, fresh exports, and diagnostics are not hardware inputs and are never copied as inputs.

## Plan contract

See `native7-incremental-routing-plan-v1.schema.json`. The structural JSON Schema supplements the authoritative Python validator; it does not replace the source-record, logical-identity, or native-grid checks. Unknown fields and duplicate JSON keys fail closed.

- Top-level fields: `schema`, `source`, `removed_native_records`, `added_copper`.
- Each removal is `{"record": FULL_NATIVE_RECORD, "full_record_sha256": DIGEST}`. Copy the entire record from the exact source export, including native polygons and `net_code`. Digest is SHA-256 of UTF-8 `json.dumps(record, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)`. Both full record equality and digest must match. Only tracks, vias, and arcs may be removed; tracks/arcs on plane layers cannot be removed.
- Each addition is a recipe directly, without a `recipe` wrapper. All recipe names are unique. Physical `net` must exist in the exact source; empty or unconnected nets are rejected. `logical_net` must be an existing exact source-map value, or the same physical source-net name when that net has no split identities. Existing canonical map values remain legal even when that net also has split values. No new split identities are inferred; untouched logical-map entries remain identical.
- Track recipe: `kind: "track"`, `name`, `net`, `logical_net`, `layer`, `points`, `width`. Include every polyline bend. Coordinates and widths are millimetres on the exact 1 nm native grid; no rounding or snapping is permitted. Width is at least .127 mm. Layers are only F.Cu, In2.Cu, In3.Cu, B.Cu. Every adjacent pair creates one native segment; collapsed segments fail.
- Via recipe: `kind: "via"`, `name`, `net`, `logical_net`, `xy`, `diameter: 0.45`, `drill: 0.20`, `layers: ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]`, `tented_front: true`, `tented_back: true`. These are ordinary fully tented through-vias; there is no process variation.
- Footprint poses, pin maps, pad/net edits, stack changes, zone changes, blind/buried vias, and added arcs are outside this schema. Through-via barrels necessarily pass through the stack; signal tracks cannot occupy the plane layers.

For example, an addition (coordinates illustrative, not an approved route) is:

```json
{"kind":"track","name":"example-polyline","net":"FLASH_HOLD_N","logical_net":"FLASH_HOLD_N","layer":"F.Cu","points":[[1,2],[3,4],[5,4]],"width":0.127}
```

UUIDs are `uuid5(NAMESPACE_URL, source_board_sha256 + "/" + exact_plan_file_sha256 + "/" + recipe_name + suffix)`, with `/segment/N` or `/via` suffixes. The exact plan file bytes are part of identity, so formatting changes alter UUIDs. Collisions are checked against every source-board UUID, including footprint graphics.

## Host-only validation

Run from `/workspace/scratch/8a35c1f26232/f722-layout-rebuild`:

```sh
python recovered-native7/recovery-importer/import_native7_incremental_v1.py --plan recovered-native7/recovery-importer/empty-plan-v1.json --check-inputs
python -m unittest discover -s recovered-native7/recovery-importer -p 'test_*.py' -v
```

Pure validation checks the source and all 61 file hashes, full removals, recipes, logical identities, and UUID collisions. It imports no `pcbnew`, creates no candidate, and needs no job lease. The tests include source/record tampering, forbidden pads/poses/layers/process changes, unknown and flattened logical identities, duplicate IDs/keys, nonfinite/off-grid/native-overflow coordinates, altered native contours, undeclared retained-object changes, zone-metadata changes, and absent/expired/misbound native-job permission.

## Native execution and owner lane

Only the owner holding the serialized native-job lane may issue the lease. `owner-job-lease-v1.template.json` is deliberately inactive and unusable. The owner must bind the exact source object, exact plan file SHA-256, current importer SHA-256, unique lease ID, one selected output, one allowed stage (`incremental_construct_refill_export`), issue timestamp, and expiry no more than two hours later. It is an explicit job-permission record, not a way for a worker to authorize itself or acquire the owner's lane.

The selected output must be an absolute, new direct child of this directory's `candidates/`, without symlink traversal. Existing directories are never reused. All input/lease/runtime gates run before native import or copying. Lease and selected-input hashes are rechecked before successive native phases and completion. A lease does not authorize DRC, routing, FEM, or other jobs. The owner should bound the process with an external timeout when granting the lane.

```sh
timeout 180s kicad10-runtime/python recovered-native7/recovery-importer/import_native7_incremental_v1.py --plan ABSOLUTE_SELECTED_PLAN --output ABSOLUTE_NEW_CANDIDATE --lease ABSOLUTE_OWNER_ISSUED_LEASE
```

## Proof and limits

The final exact native export must preserve every undeclared full object record, including net codes. Every new record must exactly equal the recipe identity plus the independently captured official native API shapes before save/refill. Full retained route S-expressions and all other board/footprint S-expressions are preserved; only native zone-fill payloads are excluded from the latter comparison. All 156 footprints and 558 pads retain their identities, geometry, nets, and complete footprint metadata. All 60 non-board hardware files remain byte-identical.

Zone outlines and settings are checked both in native records and full board syntax. `changed_zone_fills` reports each changed fill or representation with before/after hashes; exact post-fill geometry is in `f722-heli.native.json`. The source inputs and helpers are rechecked after construction. The provenance receipt includes all 61 hardware hashes, declared cuts, complete added native records, deterministic UUID mapping, recipe counts, and job bindings.

`construction-start.json` records a started attempt. **Only** `construction-provenance.json` with `CONSTRUCTION_VERIFIED_NOT_ACCEPTED` means the structural construction proof passed. Failed attempts are retained for inspection. Neither receipt nor an empty-plan smoke run establishes DRC, ERC, schematic parity, connectivity, mechanics, process suitability, electrical performance, manufacturability, adoption, or completion of routing; those gates remain separate. A refill may legitimately change existing saved fill geometry and is always reported.

## Verification on 2026-10-10

Twenty host tests passed. Both `empty-plan-v1.json` and `identity-replacement-plan-v1.json` passed pure input validation. Under two separately issued owner leases and sequential 180-second external caps, both native smoke jobs passed:

- `candidates/smoke-empty-v1`: zero cuts/additions. PCB and native export reproduced the source bytes exactly, including SHA-256 `a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f` and `53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505`.
- `candidates/smoke-identity-replacement-v1`: removed one existing LED_GREEN_K .127 mm B.Cu track and one .45/.20 mm tented through-via, then restored identical complete geometry and net/logical roles under two declared new UUIDs. PCB SHA-256 `55e26a886741e206121f4d0707fe326c0c16ee5aa2cfca0eec9698cb647f0b52`; native SHA-256 `8bf00da9f81c9ea0f84be73612d9d0c2cc695911185c8b5367f7444d09dc86a3`.

Neither smoke changed a zone fill. The separate host-only `verify_native7_smoke_v1.py` proved the complete native copper-record multiset, ignoring only the declared UUID replacements, equals the source. Both candidate directories contain `construction-provenance.json` and `smoke-proof.json`. These controls exercised official load/save/refill/export, removal, track/via addition, tenting/drill/layer API behavior, full new-record comparison, retention checks, and paired-input preservation. They do not exercise a changed route topology or demonstrate routing/physical/electrical acceptance. The owner lane was released after both native jobs terminated.

Host smoke proof command (use a new `--out` path or omit it when rechecking):

```sh
python recovered-native7/recovery-importer/verify_native7_smoke_v1.py --candidate CANDIDATE --plan EXACT_SMOKE_PLAN
```
