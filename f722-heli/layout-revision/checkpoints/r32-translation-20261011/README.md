# WIP: R32 translation source-only recovery checkpoint

This additive checkpoint preserves an incomplete routing candidate and its exact recovery inputs. It does not change the adopted board or schematic. The last checked native board still has seven opens; power qualification is stale. U15/R32 paired board/schematic parity, complete routing, final DRC/ERC, power checks and release exports remain pending.

## Preserved positive checkpoint

- Actual candidate R32 pose: (23.55, 19.5) mm, 270 degrees, F.Cu.
- 68 effective native cuts and 46 recipes (29 tracks and 17 vias).
- Three scarce terminal entries have actual contact. The corrected role-aware all-twelve guard and finite/contact/support checks pass at this intermediate checkpoint.
- The specifically named `R32-relief-held-TX-upstream-via` still awaits its actual TX source entry. Its narrow, declared intermediate contact exception is not a completed route; no other barrel receives that exception, and it must disappear before final completion.
- Positive v3 checkpoint SHA-256: `d4de200a581fc5c9af088abd23d3ba861adbbe3f160999616b9846161467b43d`.
- Physical snapshot SHA-256: `f4fccd1a1a6acbb63537b6831eaf9911a5c67abf26f6cad03a62398dfdc8259b`. The saved v7 replay refers to the same snapshot.

These are saved analytical receipts, not native-board acceptance. A passing intermediate reachability guard does not mean the twelve routes are physically complete.

## Current failed outcome and correction

The frozen v7 contract has 288 exact source bindings (SHA-256 `56652d4741e3ad408b63927a3f8a63dc538da49674e2bd0f22d57c457db5f8ac`). Its selected terminal result has SHA-256 `1b68abaad02aca6f3aafbc0ddf09222e97b472c766ac9b07ba87ea01529210dd`.

Both declared ABC crossover trials produced complete finite ABC trees with passing endpoint/annular contacts. Each failed the complete all-twelve guard by cutting ten peer demands. Both batches were rolled back in full. The terminal outcome is: “The two declared complete ABC crossover cells produced no guarded physical tree.” No complete planning witness or new native trial resulted. Exact per-trial cuts and receipt hashes are in `checkpoint-summary.json`; the original selected result is restored losslessly.

**Erratum:** The earlier v1 protected B_RX all-twelve claim is invalid. Inherited dispatch ignored `B_RX_EXT` and evaluated the whole true net instead of the actual protected downstream branch. That positive claim is not reused. Corrected v2+ dispatch checks U14.4 to R32.1 with the upstream/header copper retained as foreign obstacles. Final true-net and actual-TVS IO cut checks remain strict. The original v1 evidence is retained solely because the exact v7 contract binds it; retaining it does not endorse its invalid claim.

## Contents and storage

Only the frozen 288-file contract closure and six selected current evidence files are in scope. The six are the v7 contract, original v7 terminal result, v7 replay checkpoint, v7 preparation seal, the current ABC domain and its static controls. The v3 positive checkpoint and corrected role controls are already in the bound closure.

Of 294 scope paths, 210 reuse bytes from the already published recovery packages. The 84 new paths are losslessly stored in one 3,291,252-byte XZ chunk, below the 8 MB raw transport limit. The 80,004,948 raw new bytes include historical results and composition records that the contract explicitly requires for exact reproduction; no unrelated historical diagnostics are added. Nothing from work after this freeze is included.

Existing repository content and both predecessor packages remain byte-for-byte intact. This package adds only its own checkpoint directory. The cold restore reconstructs and verifies all 454 combined workspace paths, including the predecessors' full 370 paths. Every file is bound by path, byte count, SHA-256 and Git blob SHA. XZ CRC64, archive digest and contract/receipt bindings are also checked. The restore scripts use only the Python standard library and do not import restored engineering code.

## Cold restore from a repository checkout

Run these commands from the repository root, choosing a recovery output directory that does not already exist:

```sh
python3 f722-heli/layout-revision/checkpoints/routing-recovery-20261011/restore.py \
  --checkout . --output /tmp/f722-r32-recovery
python3 f722-heli/layout-revision/checkpoints/west-tx-bridge-20261011/restore.py \
  --workspace /tmp/f722-r32-recovery \
  --previous-package f722-heli/layout-revision/checkpoints/routing-recovery-20261011
python3 f722-heli/layout-revision/checkpoints/r32-translation-20261011/restore.py \
  --workspace /tmp/f722-r32-recovery \
  --routing-package f722-heli/layout-revision/checkpoints/routing-recovery-20261011 \
  --previous-package f722-heli/layout-revision/checkpoints/west-tx-bridge-20261011
```

`RESTORE-VERIFICATION.json` records the tested cold restore and refusal to overwrite an existing overlay. It verifies saved receipts and exact bytes; it does not rerun geometry, routing, KiCad or power qualification. Reconstructed engineering scripts remain available for an explicitly chosen continuation after review.
