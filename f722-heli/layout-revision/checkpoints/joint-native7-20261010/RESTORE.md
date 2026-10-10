# Verify and restore

The hardware folder is directly openable in KiCad 10.0.6. Reproduction uses Python 3, a fresh Linux workspace, an existing extracted official Debian KiCad runtime 10.0.6+dfsg-1, and the exact source checkpoint. Runtime binaries and raw vendor documents are not included. The wrappers, package manifest and historical runtime validation are preserved under `repro/runtime-provenance`; its README describes the original full runtime, not files bundled here.

From this checkpoint directory, verify every payload identity and decompress/hash-check the flattened transaction without writing files or invoking KiCad:

```sh
python3 repro/restore.py --verify-only
```

Use a repository checkout of tree `6dba61a4971d6a9f4e4efe343ba4a784ed17e87b`, local commit `9314ad62a15c519585dad223f85e07c83221e33a`, equivalent to verified PR18 head `abff3d0e97509f4af6c4eb2351916d037bd0db73`. No checkout/ref/index mutation is performed by the restore tool. It verifies the 73 required base files individually, including the source checkpoint11 project and exact parser/exporter dependencies, against SHA-256 and Git blob identity.

```sh
python3 repro/restore.py --repository /path/to/base-checkout --workspace /path/to/new-rebuild --runtime /path/to/kicad10-runtime
```

The output directory must not exist. Default restoration only copies hash-checked files, preserves original source paths and decompresses the selected transaction. It writes a RESTORE-RECEIPT.json and reports two native exports as pending. The complete published hardware is copied under `ordinary-routing/tests/native13-access/joint-native-import11-v1/candidates/published-reference02`. All original input/spec bytes remain exact; a separately named `joint-native11-import-spec-v1.local.json` changes only `runtime.directory`, with both spec hashes and the single configuration delta recorded in the receipt. Existing absolute paths in historical evidence are provenance, not live restore destinations.

Native geometry work must use the pinned official runtime. Once scheduled/authorized for the local environment, restore into another new directory with `--export-native` to regenerate the source and published-candidate native exports. The tool rejects either regenerated export unless its exact SHA-256 matches the dependency manifest. It does not infer or normalize changed pad shapes. A runtime mismatch requires investigation rather than changing the expected hash.

```sh
python3 repro/restore.py --repository /path/to/base-checkout --workspace /path/to/new-rebuild-with-native --runtime /path/to/kicad10-runtime --export-native
```

After source-native export, the exact constructor's host-only input validation can run from the restored rebuild root:

```sh
python3 ordinary-routing/tests/native13-access/joint-native-import11-v1/construct_joint_native11_v1.py --spec ordinary-routing/tests/native13-access/joint-native-import11-v1/joint-native11-import-spec-v1.local.json --transaction ordinary-routing/tests/native13-access/joint-native-import11-v1/selected-transaction.json --poses ordinary-routing/tests/native13-access/joint-native-import11-v1/selected-poses.json --check-inputs
```

For a fresh replay, run that same constructor using `/path/to/kicad10-runtime/python`, omit `--check-inputs`, and supply `--output` as a new named directory under the restored importer `candidates/`, plus `--lease /path/to/current-local-job-permission.json`. The constructor validates the current local permission against source/transaction hashes, output path, expiry and the `construct_refill_export` stage. The permission format is defined in `common_joint11.py:validate_lease`; historical operational permissions are intentionally absent. Request any new execution permission from the environment's owner; the package provides no authorization by itself.

The constructor copies the localized spec into its new candidate, preserves all source inputs, applies paired metadata and exact native poses/cuts/segments/vias, refills, exports, and validates strict pad/full-footprint/retained-object equality. Stop on any failure. Native gate entry points are `validate_paired_joint11_v1.py --candidate <new-candidate> --lease <permission>` for `paired_native_gates`, and `validate_physical_joint11_v1.py --candidate <new-candidate> --lease <permission> --stage mechanics --stage process --stage critical --stage bonded --stage support` for the corresponding `physical_*` stages. The physical wrappers use their pinned helper dependencies and require the same host Python geometry packages as the original checks. Reports retain false overall status for known opens; no existing result authorizes silencing a new failure.

Restoration/input validation does not rerun native, physical, finite/reference or electrical gates. The package includes compact source-bound finite/reference receipts, not the large raw native/reference exports or a claim of fresh verification on another machine. For future changes, regenerate source-bound evidence with the appropriate original check tools and exact geometry; preserve all raw failed predicates and current electrical limits. No restoration command selects canonical hardware, changes Git refs/index, or publishes files.
