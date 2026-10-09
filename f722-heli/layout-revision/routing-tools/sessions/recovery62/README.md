# Exact historical source recovery from accepted62

This compact packet reconstructs four historical paired projects from the
accepted62 / candidate22 hardware project published alongside v7. It contains
byte-copy deltas and hashes, not duplicate complete PCB or schematic files.
The authoritative base PCB SHA-256 is:

`fd8fd21062c61992ec992481d394e19a6a99cfe8ec58405ed1e391c5e3836bfa`

`paired-files.json` identifies all 63 required base files and the exact target
boards. Use the published project, design rules, schematics, local libraries,
library tables, README and licenses together. No Git commit, remote connection,
KiCad installation, Java process or native solver is required for recovery.

## Recover paired projects

From the v7 packet root, run Python 3 with a new output directory per source:

```sh
python3 sessions/recovery62/rebuild_historical_source.py project --base-project /path/to/accepted62/hardware --source candidate16 --out /path/to/new/old69
python3 sessions/recovery62/rebuild_historical_source.py project --base-project /path/to/accepted62/hardware --source candidate19 --out /path/to/new/power69
python3 sessions/recovery62/rebuild_historical_source.py project --base-project /path/to/accepted62/hardware --source candidate20 --out /path/to/new/source65
python3 sessions/recovery62/rebuild_historical_source.py project --base-project /path/to/accepted62/hardware --source candidate21 --out /path/to/new/source63
```

Each command verifies every required base file, the selected delta, and the
reconstructed board before creating output. It writes the exact historical PCB
and its 62 paired files. All 62 paired files are byte-identical across these five
snapshots. The base project is read-only; existing outputs are rejected.

The source names are exact snapshot selectors, not approximate connection counts:

- candidate16 / old69, before power construction:
  `9cf04c88ebd31d7e2c12bdb8a9f80e01b615a7bdb94a73fc2234208a2e0a14c8`
- candidate19 / power69:
  `e26da349b5585db16d2586ed05e3d649e2f1f8df4932c09d78aca8ce880469c4`
- candidate20 / source65:
  `759dc5fae8d446057f9aa8e11292c02075d127e2268d0541349f7a8038ab07d5`
- candidate21 / source63:
  `868b957a5dad28110216e6a59b05497150c2bf0d3b2ae02db6a38cede79e8181`

candidate16 can also provide the exact accepted69 base for the retained
`sessions/recovery69` helper when older replay sources are needed. Recover its
complete paired project first, then use that directory as recovery69's
`--base-project`. Do not use candidate19 as a substitute: its board hash differs.

For a board-only diagnostic, use the lower-level mode:

```sh
python3 sessions/recovery62/rebuild_historical_source.py file --base-file /path/to/accepted62/hardware/f722-heli.kicad_pcb --delta sessions/recovery62/candidate21.f722-heli.kicad_pcb.delta.json --out /path/to/new/source63.kicad_pcb
```

File mode does not verify or copy the paired project. Use project mode for replay.

## Delta format and verification

Operations are either UTF-8 text literals or `[offset, count]` byte ranges copied
from the SHA-256-checked base. candidate19, candidate20 and candidate21 need only
copy ranges. candidate16 also uses historical text literals, including historical
fill bytes. The helper preserves exact bytes without recalculating geometry.
No transformation, executable payload or code evaluation is used.

Every delta verifies the original base hash, final length and final hash. Project
mode additionally verifies the delta against its manifest hash and checks the
selected target board hash. `verification.json` records complete output-byte
comparisons, omitted optional files, wrong-source rejection, altered paired-file
and delta rejection, malformed-copy checks and overwrite prevention. Temporary
test outputs are removed. These are source-reconstruction checks, not new DRC,
electrical, native-import or routing validation.

`parts.json` and `f722-heli.kicad_prl` are present and byte-identical in all five
snapshots. Their hashes and sizes are listed as optional omissions. The helper
does not copy parts metadata, which is not needed for KiCad project or SES import,
or local editor preferences. Obtain the matching parts metadata separately if a
later tool requires it.

Recovered projects are historical fixtures, not the adopted layout or a
manufacturing release. Original sources and earlier packets remain unchanged.
