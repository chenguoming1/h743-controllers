# F722 native manufacturing export tools

This tooling generates source-bound prototype manufacturing files from a frozen, paired F722 KiCad project. It refuses incomplete native routing, missing reviews, stale source identities and mismatched assembly data. Export checks do not establish production or flight qualification. Factory CAM, assembly acceptance and physical testing remain separate.

## Installation and runtime

Place these files in `f722-heli/layout-revision/export-tools/`. Run with a Python interpreter that can import KiCad **10.0.6** `pcbnew`, and provide the **10.0.6** CLI explicitly through `--kicad-cli`. Both reported versions must match exactly. The commands below assume the working directory is `f722-heli/layout-revision/`; replace `python3` with the appropriate KiCad Python interpreter if needed.

The exporter records the reported Python/CLI versions, CLI executable SHA-256 and native Gerber build string. `--runtime-provenance /path/to/provenance.json` optionally binds an additional runtime/package provenance file by SHA-256. No local package manifest is required.

```sh
python3 export-tools/native_export.py \
  --hardware hardware \
  --output build/prototype-new \
  --expected-pcb-sha256 EXACT_FINAL_PCB_SHA256 \
  --receipts checks/export-receipts/receipt-index.json \
  --kicad-cli /path/to/kicad-cli
```

`--hardware` must identify the full paired project: PCB, project/rules, all nine schematic sheets, parts metadata, and local libraries. `--output` may be any new directory outside that hardware tree. Existing output directories are refused so stale files cannot mix with a new run. Native checks and plotting never refill or save the source board. The CAD/parts/library input set is hashed before checks, after gate validation and after export.

## Required checks and receipts

Every candidate run performs fresh native DRC with all track errors and all severities included. It requires zero opens, zero errors/exclusions, and no ignored checks. Fresh ERC must cover all nine sheets with zero violations. Warnings remain visible and require a receipt matching the exact fresh warning signature.

Ten additional source-bound review scopes are required:

- `native-schematic-parity`: full reference/pad/net/value/footprint agreement
- `firmware-pinmap`: intended external pin and firmware mappings
- `critical-signal-return-paths`: source-specific USB, clock, sensor, VCAP and signal/reference paths
- `protection-paths`: every required protection/series-path cut, including loaded paths
- `mechanical-process`: poses, body/courtyard, connector, board-edge and bounded process checks
- `via-mask-process`: via connections, drills, mask/tenting and process treatment
- `electrical-power-review`: final-source power/ground analysis and operating conditions, with physical limits explicit
- `warning-dispositions`: all fresh native warnings reviewed against their exact signature
- `parts-identity`: current values, exact manufacturer/MPN, footprint and supplier identities
- `zone-fill-replay`: independently checked/reproduced saved fills for the frozen source

Each scope uses schema `f722-validation-receipt-v1`, its scope name, `result: "pass"`, all three source hashes, nonempty method/limitations, and hashed underlying evidence. The index uses schema `f722-export-receipts-v1` and hashes each receipt. Relative receipt paths resolve from the index; evidence paths resolve from each receipt. Templates are deliberately nonpassing.

Receipts must be prepared from the actual completed scoped checks. The exporter verifies their source identity and bytes; it does not infer engineering review from native DRC or independently rerun the receipt producers. Never turn stale historical evidence into a passing current-board receipt.

To collect source identity and fresh native diagnostics before preparing receipts, use a new output directory and add `--gate-only`, omitting `--receipts`. An unfinished board is blocked by DRC; a clean board is blocked by the missing receipts. The diagnostic directory contains `verification/source-identity.json`; `verification/gate.json` includes the native warning signature once DRC runs. This does not bypass candidate gates.

## Payload and verification

The payload contains:

- Six copper Gerbers; front/back mask, paste and silk; Edge.Cuts and Gerber job file
- Separate PTH/NPTH Excellon drills with actual routed slots, SVG maps and drill report
- Unmodified native positions, JLC-format SMT BOM/CPL, complete per-reference/grouped procurement, manual/THT positions, bare-pad exclusions and factory rotation checklist
- Nine-sheet native schematic PDF and front/back native board SVG previews
- Fresh native diagnostics, command records, input identity, validation receipts, verification results, manifest and SHA256SUMS

Coordinates use absolute `(0,0)` in mm, with output Y equal to negative native PCB Y. Native rotations and bottom-side X are preserved. No supplier angle correction is guessed. J1 remains an SMT placement candidate with 16 contact paste apertures; all four plated shell slots need separate soldering and have no shell paste. J2–J8 remain exact Samtec manual/THT headers; TP1–TP5 remain bare unplaced board features. R16 supply/installed-circuit qualification and R31 0201/50 mW constraints remain explicit.

Checks compare native pad and attributed copper-flash centres, the full paste-centre multiset, outline segment equality and closure, all round-hole/routed-slot coordinates and sizes, native poses/values/footprints/sides, and parts/BOM/CPL coverage. Changed exclusion/DNP/manual sets, unsupported blind/buried drills and non-straight outlines are refused. These are scoped native/export checks, not an independent full CAM raster/aperture-shape comparison, supplier inventory check or factory placement-preview approval.

Every subsequent PCB, schematic, parts, rule, project or local-library edit invalidates prior source-bound receipts and requires entirely regenerated exports.

## Historical control replay

Historical mode is hard-pinned to PCB `4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f` and parts `3dc37171d45add434f693219ea37f9f9ff2c9bc58830d2215f0c34760b2409d9`. It is only an exporter regression control, never current-board release evidence. When the historical hardware and manufacturing package remain in their original sibling directories:

```sh
python3 export-tools/native_export.py \
  --hardware ../hardware \
  --output build/historical-control \
  --expected-pcb-sha256 4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f \
  --mode historical-control \
  --kicad-cli /path/to/kicad-cli

python3 export-tools/check_control.py \
  --published ../manufacturing \
  --rebuilt build/historical-control \
  --report build/historical-comparison.json

python3 export-tools/test_export_controls.py \
  --hardware ../hardware \
  --control build/historical-control
```

All 13 historical Gerber drawing/aperture/net-attribute command streams were reproduced after omitting timestamp metadata and normalizing only the exact Debian `10.0.6+dfsg-1` build suffix. All nine CSV files were byte-identical; drill tool sets and round/slot geometry matched. The compact historical receipt binds these results to source and tooling hashes.

Negative controls demonstrate that the earlier 158-open checkpoint and a clean board lacking review receipts are refused before manufacturing output. Those receipts do not describe later layout checkpoints. Sixteen focused tests cover receipt/evidence tampering, stale source, missing scopes, unreviewed warnings, changed part footprint, dropped THT header, altered placement rotation, wrong slot size, shifted paste flash preservation of existing output directories, rejection of hardware-tree output, and exact Python/CLI version gates. Synthetic fixtures are removed afterward.

`PUBLIC_SOURCE_ALLOWLIST.json` lists this compact bundle; `FILES.sha256.json` hashes every allowlisted file except itself. Historical/control receipts describe tooling behavior only. Large manufacturing payloads, preview files, native-source duplicates and raw logs are excluded; regenerate them with the commands above.
