# F722 paired metadata parity audit and copy-only proof

**Verified:** the metadata correction eliminates all native KiCad 10.0.6 schematic-parity findings on disposable copies of candidate08 and candidate09. Source candidates and the repository remain unchanged. This is not a routing-completion or manufacturing acceptance result.

## Findings

- `repo/f722-heli/layout-revision/hardware/parts.json` is the authority for this pair. Its SHA256 is `99e1589baf2033bc696613ad52c5deab3403397d7caafff6d8aa011296846858`. All nine candidate08/09 schematic files are byte-identical to that paired project.
- All 151 purchasable-part MPNs match exactly. TP1–TP5 intentionally have empty MPNs and no parts records. Six `#FLG` symbols are schematic-only. All 156 footprint UUIDs, full symbol paths, symbol UUIDs, values and library IDs map correctly; there are no missing or conflicting reference mappings.
- Historical `repo/f722-heli/hardware/parts.json` differs at R7/R8, retaining the previous 4.7 kΩ part. Do not copy that historical identity into this revision.
- Each board actually has 153 missing MPN, Manufacturer and LCSC fields, plus 150 missing Supplier fields. J1, C75 and R53 already have correct MPNs. There are also 58 Datasheet differences and two Description differences.
- The 156 existing native warnings consist of 153 missing MPNs, missing Supplier on C75/R53, and the J1 Description mismatch. [KiCad 10.0.6's checker](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.6/pcbnew/drc/drc_test_provider_schematic_parity.cpp) reports only the first field discrepancy per footprint. Adding MPN alone exposes subsequent discrepancies.

## Applied only to disposable copies

The complete proposal is `expected-updates.json`, bound to footprint UUIDs and full symbol paths. It makes 609 PCB property additions and 57 existing PCB Datasheet value updates. Five paired schematic completions preserve useful source data:

1. R16, R31 and R53 receive Datasheet values from their authoritative parts records. R16/R53's existing matching board URLs are retained.
2. J1 and R16 receive their existing board Description text in the schematic. Those descriptions are retained on the board.

PCB-only fields such as J1's mechanical/assembly notes, C75's `Supplier URL`, and R53's TCR/power-review notes are retained. Empty MPN/Manufacturer/LCSC fields remain explicit on all five testpoints. No part identities, values, footprints, flags, pad assignments, geometry, copper, saved zone fill, or settings change. `parts.json` remains unchanged. Its empty L1 datasheet differs from the populated schematic URL; this informational gap is preserved and does not affect MPN or native parity.

## Evidence

`verification-summary.json` summarizes both full native proofs. Each copy has `metadata-verification.json`, a fresh baseline/output native netlist, and `metadata-drc-parity.json`.

- candidate08: 0 parity issues, 0 other DRC violations, unchanged 77 unconnected items. Original SHA256 `1ff8ee645bd5fea7bbbc30cd4e5269aab76a2032efe3e2c4e77a0becd85e9edf`; copy SHA256 `27809aabe52f74b0a6d0a10f73f2684bab263c458681e960751ec6c15c59e0c9`.
- candidate09: 0 parity issues, its same two dangling-via warnings, unchanged 77 unconnected items. Original SHA256 `544491a48469d418ed47cf5da12b6b9406db282d60a3cda77b154f6ed11a869d`; copy SHA256 `d60f257bed4d0a7efc2d7ce1df2d7daf3bd71e0d0a52ae446028a3b73dfd3299`.
- Exact parsed board/schematic structure outside the named metadata fields is identical before/after. Independent native footprint/pad/track/via/net fingerprints and exported schematic/pin/net identities also match. Every selected source/library file is rehashed after execution.
- Two independent candidate08 copy runs produce identical corrected board bytes.

`audit.json` contains all per-reference field states, source hashes and mapping checks. `reference-mapping.tsv` provides a compact 156-row review.

## Reuse on the next route candidate

Run `apply_metadata_copy.py` with KiCad 10's Python wrapper. Required arguments are `--source`, a **new** `--out` directory, `--authority`, `--manifest`, `--expected-board-sha256`, and `--cli`. Use the current route candidate's exact board hash. The script accepts new copper while requiring the audited schematic hashes, authoritative parts hash, 156 reference/UUID/path bindings, and exact prior values of every changed field.

For example, from the rebuild workspace:

```sh
"$KICAD_PY" \
  ordinary-routing/tests/mpn-parity/apply_metadata_copy.py \
  --source ordinary-routing/candidate08 \
  --out ordinary-routing/tests/mpn-parity/new-verification-copy \
  --authority repo/f722-heli/layout-revision/hardware \
  --manifest ordinary-routing/tests/mpn-parity/expected-updates.json \
  --expected-board-sha256 1ff8ee645bd5fea7bbbc30cd4e5269aab76a2032efe3e2c4e77a0becd85e9edf \
  --cli "$KICAD_CLI"
```

The script edits exact text spans in the new copy, uses deterministic UUIDs for new hidden fields, reloads it natively, exports both netlists, and runs strict `--schematic-parity --severity-all` DRC without suppression, board saving, or zone refill. It refuses source/output overlap and output reuse. It never overwrites canonical source or the supplied candidate.
