# Current paired base and incomplete v12 routing recovery

This package preserves the verified current U15/R32 paired base, the sealed
source-only final-binding preparation, and the v12 routing checkpoint. It does
not contain a completed routing witness or a native route-import result.

Verified partial planning entry: actual ABC_PG U6.2 source entry through In3 to a new barrel at the retired
FLASH_CS site. All 13 repair demands remain reachable; FLASH_CS has three
separate groups awaiting physical reconstruction. Restricted ABC continuation
failed, and full joint routing remains incomplete. `complete_planning_witness` remains
false, and neither checkpoint is adopted or accepted.

## Delivery files

Send only the files named in `delivery-manifest.json`. Never recursively send
this directory: `verification-fixture/` contains expanded local test inputs and
outputs, including duplicate restored native files, and is not a deliverable.

`recovery-objects.tar.xz` is 9,469,996 bytes. Its SHA256 is
`94950084f9658c59c42bf378bdb235f05ec6453e5955c0658b9fcf294c742fe8`.
Base64 encoding uses 12,626,664 bytes; adding a 1 MiB metadata allowance stays
below the 16 MiB request cap. No split is necessary. The builder uses 8 MiB
binary parts only if the archive would exceed that calculated request budget.

The archive contains 73 unique new content objects totaling 188,688,515 raw
bytes. The reconstruction map references another 361 unchanged published
objects, for 434 unique objects and 622 restored paths. Identical bytes are
stored once per SHA256. The 143,980,766-byte native export appears exactly once
as an archive member; its hash remains
`ef924ac03c069313072650357ca094dc71c5919f218d3c8904d87cbe46ae3e83`.

The original `recovery-file-allowlist.json` is preserved byte-for-byte as
provenance. Sealed binder artifacts, the v12 checkpoint/contract/result/producer,
and all 319 exactly bound v12 source dependencies are added in the new
`reconstruction-map.json`. Historical diagnostics are present only when
explicitly pinned by that current contract. No incidental logs, caches, live
process state, duplicate native payloads, or runtime binaries are included.

## Restore exact bytes

Supply a repository checkout containing the referenced PR21 blobs and a
workspace restored from its published routing-recovery, west-TX-bridge and
R32-translation predecessor packages. `reconstruction-map.json` records every
repository path or predecessor member, size, SHA256 and Git object identity.
The local publication evidence records an expected tree; it is not a fresh
remote status check.

Run from this package directory, replacing the three paths:

```sh
python -S -B restore.py \
  --repository /path/to/PR21-checkout \
  --published-workspace /path/to/restored-predecessors \
  --output /path/to/new-absent-recovery-workspace
```

The output must not exist. The restorer verifies the map hash, archive/part
hashes, each exact archive member, each published input's SHA256 and Git blob,
then copies and rechecks every restored file. It does not execute restored
engineering code or run native, geometry, routing, or solver operations.

Byte restoration is portable. The unmodified historical engineering verifiers
still bind original absolute paths and may need a separately reviewed adapter
in a relocated workspace. The included allowlist records the old generic
importer closure and the unchanged canonical/runtime prerequisites. Do not
rewrite hashed receipts or treat preserved owner leases as execution permission.

## Verification and reproducibility

`VERIFY-ARCHIVE.json` records member hashes, deterministic tar metadata, exact
archive reassembly, one native member, and the routing dependency checks.
`RESTORE-VERIFICATION.json` records the fresh 622-file byte restore and independent
post-restore hashes, path traversal rejection and existing-output rejection.

The local restore test used verified predecessor bytes. Six repository references
used equivalent locally available published copies; one reference used its exact
bound local source matching the recorded published Git blob. The provenance is
explicit in `PREDECESSOR-FIXTURE.json`; no remote checkout or fresh engineering
verification is claimed.

`build_recovery_package.py` preserves the exact content bytes in SHA256-named,
lexicographically ordered USTAR regular-file members, with mode 0644, empty
owner names, and zero uid/gid/mtime. Compression is XZ with CRC64 and preset 6.
The source-only builder fails on changed bound inputs and existing outputs.
For rebuilding, place its source in a fresh package directory under the restored
final-binding directory and supply the same sealed file names shown in
`VERIFY-ARCHIVE.json`. Do not run it over this completed package.

No files were uploaded and no external service was changed during packaging.
