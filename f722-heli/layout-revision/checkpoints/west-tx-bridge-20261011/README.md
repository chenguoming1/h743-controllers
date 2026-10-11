# WIP: physical TX source-to-west bridge source checkpoint

This additive source checkpoint preserves a positive physical TX bridge and the failed continuation that followed it. It does not publish or adopt a new native board.

The accepted checkpoint contains the actual `PORT_C_TX_EXT` source-to-west track on `In3.Cu`, width 0.127 mm. Its recorded all-eleven-demand guard passes. All eleven demands remain graph-reachable at that checkpoint, but none of those eleven complete physical trees is claimed complete. The subsequent F.Cu header construction failed its guard because the actual RX and TX downstream branches became trapped. The terminal failure is preserved alongside the accepted bridge checkpoint; the failed continuation is not a completion result.

The checked native7 baseline still has seven opens, zero geometric errors and seven inherited warnings. No new native board was adopted. Power, reference, ESD and final manufacturing/export acceptance remain stale or pending. The short-ground-return review is conditional context for isolated continuation, not electrical qualification.

## Exact scope and reuse

- Current frozen contract: 206 SHA-256-bound dependencies.
- Exact predecessor reuse: 185 dependencies, 291,443,927 bytes, matched by both restore path and content hash.
- New objects: 21 dependencies, the current contract, accepted bridge checkpoint, failed terminal result, and two ground-review files: 26 files total.
- Current verification scope: 211 files. The predecessor's entire 344-file restore is retained; the combined workspace contains 370 files.
- One compressed overlay chunk, below the 8,000,000-byte raw transport limit. The predecessor's large input archive is not copied into this package.

`overlay-inventory.json` records exact sizes, SHA-256, Git blob hashes, roles, and reuse bindings. `archive-index.json` binds the inventory and compressed objects. `checkpoint-summary.json` identifies the positive result, terminal failure, fixed snapshot and limitations. `RESTORE-VERIFICATION.json` records the cold restore and safety checks.

This package is additive to PR #21 branch `f722/native7-importer-20261010` at commit `9898e8e18405e418a34a49a39ec3208317f3b1cb`, tree `cc830f8916ff0231b155446b3c6415219ebd5983`. Existing repository paths and modes are unchanged. Local sealing does not update GitHub.

## Restore without running engineering code

Use a checkout containing both published checkpoint directories and the predecessor's required repository blobs. Choose a new, nonexistent workspace. From the repository root:

```sh
python f722-heli/layout-revision/checkpoints/routing-recovery-20261011/restore.py \
  --checkout . --output /path/to/new-recovery-workspace
python f722-heli/layout-revision/checkpoints/west-tx-bridge-20261011/restore.py \
  --workspace /path/to/new-recovery-workspace \
  --previous-package f722-heli/layout-revision/checkpoints/routing-recovery-20261011
```

The predecessor first restores and verifies all 344 source paths. The overlay verifies the exact predecessor package and all 344 restored paths, rejects existing overlay destinations and symlinks, verifies all archive objects before any additions, and appends only the 26 new files. It then verifies all 344 predecessor files again, all 211 scoped files, the current contract's 206 dependencies, the accepted checkpoint/result contract bindings, and the ground-review bindings. A second overlay invocation deliberately refuses to overwrite existing files.

Both scripts use only the Python standard library. Restoration does not import recovered source, rerun routing or geometry, invoke KiCad, edit a board or schematic, or perform electrical qualification. A successful restore establishes byte identity and preserves recorded evidence; it is not a new engineering pass.

## Fixed evidence

- Current contract SHA-256: `e812ade61d87c6b02692d9c0621126706dba16a66d46a24ae8693105243a4d71`
- Accepted bridge checkpoint SHA-256: `1c67d4b9ebfe2ed54fdaf550f467b351cd035f83d249ffd08962757c54acdf33`
- Accepted physical snapshot SHA-256: `46e7740e81b3a03e7b2f7d9c230b9bb97abd45e4fd85742c25b45452a53a61b5`
- Failed terminal result SHA-256: `bcd2375c87437ee3e2b567760f1cb544a0d021108ae4672e2ced2cd9666c17cb`

Only the fixed allowlist was packaged. No later active trials, private notes or shared-status files are included.
