# WIP: native7 routing recovery checkpoint

The checked native7 board still has **seven opens**. No complete new routed board has been adopted. This additive checkpoint preserves reproducible routing inputs, exact native controls, partial positive witnesses, terminal failures, and source-only final-export/reference preparation. It is not a final hardware review or manufacturing release.

## Source status

- The preferred positive planning source is the original-TX official prefix, `recovered-native7/recovery-flash/native7-official-paired-headers-checkpoint-00-v2.json`, SHA-256 `20bdbf6c4f23a8f5706c31389ee41f5fb6a595285cbfeedb5727cf8c94ba34f9`; its physical snapshot is `27e733cea4aea37765b2df59d7fdc0a003c48683e95ce9d25cc04571ed88e377`.
- The experimental RX-west finite checkpoint-01 is retained exactly, SHA-256 `02d3760e0b6c7f1ee39876bf39690300770637c8e2d590fb72090c8a3cb7bffa`, with its complete 188-file source contract, SHA-256 `8c5d720c3b06da18e2c816263f844bb16e21a972b7425dbda299e4a6d09a5636`. Its subsequent full continuation failed when the conditional local header pair consumed another whole demand, including TX downstream. Neither that partial checkpoint nor the failed continuation is a completed routing solution.
- The U15 east180 IO1/IO2-swap raw native control has 14 opens, 29 geometric DRC errors and seven warnings with retained old copper. ERC and schematic-parity violations are zero. Its strict historical host comparison exited 7. Exact official pad arrays, raw named-net code reconciliation and receipts are preserved; the discrepancy was not converted into a pass or hidden by a geometry tolerance. An earlier exit-139 native failure remains historical provenance.
- The shorter 0.25 mm GND-return assessment, SHA-256 `bbcdae4f0cdbe388ad4e8c5215f84e5ebdc93f955bafba654973faebc8b9ae1c`, is a bounded local finite/contact witness only. It is explicitly not adopted. New active trials and pending full-stack GND controls are outside this frozen package.
- R53, CORE, U15, VX and routing-prefix recipes/scripts retain their source contracts and raw failed receipts. Search limits and positive local contacts are not electrical acceptance. R53 native-width exception and coupling review, complete routes, fresh support/power/VCAP checks, native acceptance, return/reference/ESD review and final exports remain open.

## Source-only preparation

`final-export-preparation-20261010` preserves its sealed exporter sources and readiness handoff. It records the host identity preflight, current parts provenance and 61 paired hardware inputs. There is no final accepted routed source or regenerated manufacturing package.

`final-reference-preparation-20261011` preserves its sealed source tools, 16 passing source-only controls and current inventory. The inventory has 92 routed non-GND nets with every disposition still pending. Saved reference subsets and old power/return evidence are not a final-board review. The prepared all-net runner has not been executed as a final check.

## Base-aware recovery

The inventory is bound to PR21 base commit `ff27b580d8c988a5dc6a2f1eaa26e70b17ced3c6`, tree `e35203f8eac0da22524db57808b37963a7006234`, in `chenguoming1/h743-controllers`, branch `f722/native7-importer-20261010`.

`recovery-inventory.json` maps all 344 restore paths to exact lengths, SHA-256, Git blob SHA-1 and CRC32. 102 paths reuse identical blobs already in the verified base. The 242 missing content blobs are stored once in a lossless USTAR/XZ archive, split into raw chunks no larger than 8,000,000 bytes; `archive-index.json` binds the chunk order and exact assembled hash. Original bytes, including large historical diagnostics, are preserved.

The original official-control ZIP (`b5a49fb20b5baf400105b8784ed1b032cffbd21e4a129d9eceec1eb95a7f53bf`) is not redundantly stored. Its 42 members are preserved with exact source-path/hash/size/CRC mapping; members already required elsewhere share the same content object. Restoration reproduces member bytes, not the original ZIP container byte sequence.

From a checkout containing the base or resulting commit, run:

```
python path/to/routing-recovery-20261011/restore.py --checkout . --output /tmp/f722-routing-recovery
```

The destination must not exist. Restoration verifies every chunk, the assembled archive, XZ CRC64, every content blob and every restored path. Existing repository paths are checked by exact Git blob; the tool may read the matching local Git object when a checkout path has changed. It makes no network requests and runs no restored code, KiCad, router or solver. Runtime installations are external prerequisites and are not included.

All repository changes from this package are new checkpoint paths. No pre-existing path is changed or deleted. No canonical PCB, schematic or parts file is modified; restored historical hardware is diagnostic input. Full-tree inventory and hash verification accompany the local publisher handoff.
