# Proposed drill precision fix

The pinned KiCad 10.0.6 exporter generated correct 0.001 mm Excellon coordinates but its `round(...,3)` dictionary comparison rejected five exact half-grid ties. Keep that original failed run and tool version intact.

This separately versioned patch changes only `verify_fabrication`'s drill predicate, adds `match_drill_features`, imports Decimal, and records the comparison diagnostics. All existing source/runtime/native/ten-receipt gates, plotting commands, parts/placement policy and other verification code retain identical ASTs.

The matcher requires an unchanged full feature census and a unique one-to-one assignment; plating, round/slot kind and drill diameter are exact. Slot endpoint reversal represents the same physical slot. Each coordinate must be within half of the known 0.001 mm emitted grid, plus only 16 binary64 ulps for native unit conversion and rotated-slot arithmetic. The maximum added arithmetic bound for this board is 1.14e-13 mm. This is an output-quantization check, not a fabrication tolerance.

Host-only controls passed for the actual 329 PTH/2 NPTH census and all five ties. Missing features, same-count duplicates, wrong tool, wrong plating, 0.000501 mm shift, a shift just beyond the roundoff bound, altered slot endpoints and non-finite coordinates are rejected. Endpoint reversal and a one-ulp calculated-coordinate case behave correctly. No KiCad/native/export command or final release was run with the patched tool.

Original exporter SHA: d571a9763c3134d1995bf8a192cfdddcb4991dc637f9a20bfd7119877a6ecdfa

Proposed exporter SHA: 5383b93e8a6c04313c917341c64ddee9bf2b74770189a8bb3d7d6bcdb263dc86

Patch SHA: 43abd0a7ffab9236968195bf85521df6a6352f4810f0d605bf7363ebb6547bf9

Review `native_export.py.patch` and its control evidence before adopting the new tool version. If adopted, update repository exporter inventories/provenance transparently; do not overwrite the old recovered tool identity or relabel the stopped old run as passed. A later legitimate final export still requires all ten genuine current-source review receipts and unchanged-source/native checks.

`prepare_patch.py` reproduces this proposal from the unchanged original exporter. `check_patch.py` executes only the added matcher through AST extraction and consumes the source-bound `DRILL-CSV-DIAGNOSTIC.json` in the sibling CAM diagnostic directory. Preserve that fixture with the patch controls if publishing a reproducible review package. Canonical CAD/parts and repository files were not edited by this preparation.
