# Corrected candidate43 power evidence

This packet preserves the completed corrected power run on candidate43, with 37 ordinary opens. It is a conditional prototype DC result. It is not a final-board, production, thermal, signal-integrity or flight qualification.

- Required conditional cases: 294 pass on both 0.12 mm and 0.09 mm grids.
- Actual device supply windows: ten per case; 6,100 rows across 305 cases and two grids; no window or two-grid guard failures.
- VCAP: five copper/barrel loops pass the 35 mΩ screen; numerical guards pass.
- Eleven same-BEC illustrations are separate. The lost-feed illustration draws 18.560272 A through J8 and fails all four 6.0 V servo pad floors. The original runner exit code 1 and overall false remain unchanged.

Read [REPORT.md](REPORT.md) and [compact-report.json](compact-report.json). The exact combined summary is compressed losslessly as `combined-summary.json.gz`. `runtime/` contains the actual copied solver/compiler/reporting sources plus the original launcher and environment identity. `frozen-inputs.tar.gz` preserves the full job stage, released inputs, and source receipts with their original relative layout, using exact-content hardlinks to avoid repeated native exports. The verifier restores ordinary files and verifies every member.

The current board has advanced to candidate44, 35 opens, SHA-256 `02d2090ad7220a64a8f4a1a259d522f7b0bca3e15214b73107491d17626bd51f`. Its BEC bend and five added vias require fresh assessment. This source43 numerical result does not qualify candidate44.

## Reproduce verification without solving

Run with Python 3.12, without `-O`:

```sh
python3 -B verify_package.py
```

This verifies all packet hashes, all 40 freeze dependencies, the full stage and original source inventories, all 305 case definitions, and exact regeneration of the compact report from the saved combined summary. It does not replay the raw result or run a field solver. Temporary extraction is removed after checking.

To retain the reconstructed job and source layout, use a new destination:

```sh
python3 -B verify_package.py --extract /tmp/f722-source43-evidence
```

For a mesh-free portability check, install the versions in `runtime/requirements.txt` in an appropriate isolated environment and run:

```sh
python3 -B verify_package.py --preflight
```

The local package was verified with the original runtime packages using an absolute PYTHONPATH to the existing `python-deps` directory. The preflight reads only restored freeze dependencies and copied solver sources; it does not require the original workspace source paths or current canonical board. It confirms 37 ordinary opens outside the power scope and performs no meshing or numerical solve.

## Exact raw-result recovery and optional summary replay

The 313,406,883-byte raw result is deliberately absent from this checkpoint packet. It and the original mesh cache remain intact in the completed job. A separate local `corrected-power-recovery-candidate43/result.json.gz` has verified decompression to the exact raw SHA recorded below. Its compressed identity and size are in `provenance/raw-recovery-identity.json`. The recovery file is not a compact summary.

If the original raw file or that exact recovery file is available, the verifier can rerun the preserved strict summarizer and require byte-identical combined-summary output:

```sh
python3 -B verify_package.py --raw-result /path/to/result.json.gz
```

This optional mode reads and decodes the large raw result and can use substantial memory; coordinate resources first. It does not mesh or solve. It was not rerun while packaging, because the completed independent review had already inspected the exact raw result. The default verification and compressed-summary projection do not establish raw-result replay.

## Reproduction boundaries

All 40 released freeze file dependencies, all stage inventory files, all original source inventory files, case templates, resolved ledgers and actual runtime source bytes are included. There are no missing relative file dependencies for frozen preflight or strict raw-result summary replay. The original numerical Python interpreter and binary dependencies are not bundled. `runtime/original-environment.json` records the actual interpreter path/version/hash and module versions/path/hash; `requirements.txt` pins the four imported numerical/parser packages. Package version installation alone cannot guarantee identical native libraries or bitwise numerical output.

The original launcher and plan intentionally retain their absolute source, canonical-board, interpreter and shared-heavy-lock bindings. They are provenance, not a relocation adapter. Since canonical has advanced to candidate44, replay of the original plan or independent canonical-equality review must refuse. A new heavy numerical run requires an explicit owner-reviewed source/release plan, current canonical/adoption rebind and the single shared heavy lane. Do not edit old hashes, redirect the canonical path, reuse historical caches, relax caps, or invoke a lower-level solver to bypass those gates. This packet does not authorize a run.

A whole KiCad reconstruction, historical regression-suite replay, original launcher restaging, and official datasheet download reproduction are outside this packet. Pinned model-review evidence is included as text/JSON, with its cited source URLs; the upstream PDFs and original numerical environment are not bundled. The independent review records its completed original run, while its exact verifier intentionally requires the then-current canonical source43 and cannot now pass that equality check.

## Preserved history and identities

The files in `provenance/README.md`, `MODEL-REVIEW.json` and `MANIFEST.json` are byte-identical pre-run implementation seals. Their “no numerical run” statements describe that earlier implementation checkpoint, not this completed job. `provenance/launch-receipt.json`, this packet, and the exact result identities document the later completion. The original files were not edited.

Historical U10/U11 power paths incorrectly used EN4 instead of IN6; historical barometer loads incorrectly used CSB2/SDO5 instead of VDDIO6/GND1 and VDD8/GND7. Those prior USB/DSM path-specific numerical claims remain invalid. No historical result, cache, pass count, 146 replay cases, 140 endpoints, or 5,532 sensitivities is promoted by this packet.

- Exact board: `1ee7174a578dffe4d5ef3ae8b39d8dc88f28b80395539263a65f23be234c21e6`
- Exact raw result: `1466a094fc40cfbed24fbda76d5445bad9c06d951389e2440ed6b0cd3b13bac9`
- Exact combined summary: `030fa2ae528c45d9f0207eac4fb9b93c74cc84cf3296035f995d869bf0409550`

`MANIFEST.json` binds this packet's files. Hash checking proves integrity/self-consistency against these declared identities, not an external cryptographic signature. No Git, canonical-board, Library, or external publication changes were made by packaging.
