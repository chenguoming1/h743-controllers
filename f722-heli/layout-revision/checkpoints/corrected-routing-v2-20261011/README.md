# WIP: corrected routing and terminal native diagnostic recovery

This is a local, unaccepted recovery checkpoint. It preserves exact fixed/contact
controls, five center-join proofs, terminal router-v2 and router-v4 checkpoints,
the failed v3 compile, importer-v4 source and its incomplete v2 native diagnostic.
No later router successor is included. The prior negotiated-v1 publication packet
is unchanged; this successor's remote publication is not enabled.

Router-v2 remained incomplete with five of 19 roles connected and 17 required
joins versus 13 initially. Router-v4 failed at its exact fixed-trace gate after
pass-1 cleanup, before pass 2. All six last-good v4 report/SES/exact-trace triplets
are preserved; no final v4 report or session was exported. Raw failure receipts
retain their original state.

Importer-v4 used the incomplete v2 terminal candidate, not the rejected v4 board.
Its native diagnostic completed refill/export, full-record and syntax checks,
ERC and schematic parity. DRC reports 17 opens, 28 warnings and no other errors.
The corrected conversion retains 21 mutable source records, removes 121, and
adds 56 tracks, three vias and six fixed tracks. Superseded all-142-removal evidence
is retained as superseded. Actual finite contact, TVS IO-cut/no-bypass, reference
and fresh power/VCAP acceptance remain pending. Native7 remains accepted.

## Verified byte recovery

The 31,000,164-byte XZ archive contains 193 unique new objects and is split into
four parts listed in archive-index.json. Its SHA-256 is
2c13cd5ae402f638a5a04db074488162ad8db94d8792929de4f6304a602bebe0.
Packaging and cold restoration completed in 9.397 seconds under one CPU, a 1 GiB
address-space cap and a 60-second grant. All 571 paths and 349 unique objects
passed size, SHA-256 and Git blob checks. All archive members, deterministic
metadata/order and part reassembly were stream-verified. No engineering code
was run during packaging or restoration.

The unique 141,939,929-byte diagnostic native export is stored once. The 156
unchanged predecessor objects reuse the verified negotiated-v1 cold restore,
including original source-native bytes and unchanged paired hardware. Three
large exact JSONL witnesses preserve actual rejected/source engine states.
Large regenerable models and official binaries are separately represented by
their source recipes and expected hashes in regeneration-map.json.

Restore the unchanged negotiated-v1 checkpoint first. Then run:

    python restore.py --repository /path/to/repository --published-workspace /path/to/restored-negotiated-v1 --output /path/to/new-successor-workspace

The output must not exist. Source/evidence byte restoration is relocatable;
historical engineering replay still has the documented absolute-path, runtime
and receipt-hash requirements. SES/report pairs are not serialized router
processes and cannot establish an exact resumed queue/history state.

PREPARATION-SEAL.json and RECOVERY-PLAN.md preserve the source plan before
compression. RESTORE-VERIFICATION.json, VERIFY-ARCHIVE.json and
PACKAGE-EXECUTION.json establish the completed byte packaging result. Historical
issued lease bytes are provenance only and never grant another execution.

The predecessor manifest is
5db551817f51f75df2c66613c78c799c227634543a287278388c735535d67af5,
expected tree 7b2cb01a51d875e051482a3ec5406d6c9b263088. This does not assert
remote availability. Verify the predecessor's actual publication and obtain
owner instructions before any successor external write. No merge, deployment,
native adoption or manufacturing-readiness claim is made.
