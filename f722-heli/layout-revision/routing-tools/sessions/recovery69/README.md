# Exact replay source recovery from accepted69

This compact packet reconstructs the exact paired source projects for the two
v6 routing replays. It contains byte-copy deltas, hashes and a Python helper, not
complete PCB or schematic files. Use the accepted69 hardware project published
alongside v6, including its project, rules, schematics, library tables and local
libraries. The authoritative base PCB SHA-256 is:

`9cf04c88ebd31d7e2c12bdb8a9f80e01b615a7bdb94a73fc2234208a2e0a14c8`

The complete paired-file authority is `paired-files.json`. No Git commit or
remote access is needed. An older board or a later routing revision is not an
interchangeable base, even if it opens successfully in KiCad.

## Recover exact paired projects

Run with Python 3, using new output directories:

```sh
python3 sessions/recovery69/rebuild_historical_source.py project --base-project /path/to/accepted69/hardware --source candidate15 --out /path/to/new/replay70
python3 sessions/recovery69/rebuild_historical_source.py project --base-project /path/to/accepted69/hardware --source candidate13 --out /path/to/new/replay75
```

The first command recovers source70 / candidate15 for the explicit ADC_BUS
two-track replay. Its PCB SHA-256 is:

`23232e7bc1903c06c1809d569c91e4cb161281be9225f3776076386593e55674`

The second recovers source75 / candidate13 for the broad real-engine SES replay.
Its PCB SHA-256 is:

`008d0b11df400284d12750c7f5c877b43a7ea28ffddbf4a4b799c3ae7ec4917e`

Each command checks all 63 required input files, the selected delta and the
result before creating output. It writes the historical PCB and its 62 paired
files. All 62 paired files are byte-identical across accepted69, source70 and
source75, including the project, design rules, schematics, local libraries,
library tables, library README and licenses. The accepted69 source is read-only.
No KiCad installation, Java process, native solver or network is required.

For a PCB-only diagnostic reconstruction, use the lower-level mode:

```sh
python3 sessions/recovery69/rebuild_historical_source.py file --base-file /path/to/accepted69/hardware/f722-heli.kicad_pcb --delta sessions/recovery69/candidate15.f722-heli.kicad_pcb.delta.json --out /path/to/new/source70.kicad_pcb
```

That mode does not verify or copy the paired project. Use project mode for replay.

## Delta and verification details

Every JSON operation is either a literal UTF-8 string or `[offset, count]`, a byte
range copied from the hash-checked accepted69 file. The source70 delta removes
exactly the two ADC_BUS F.Cu track records. The source75 delta also preserves its
historical zone-fill bytes; it does not recalculate geometry. No preprocessing,
metadata transformation, code evaluation or executable payload is used.

Each delta checks the original base SHA-256, final byte count and final SHA-256.
Project mode additionally checks the selected delta's hash against the manifest.
Existing outputs are rejected rather than overwritten. `verification.json`
records full-project byte comparisons and fail-closed tests for wrong bases,
modified paired files, modified delta payloads and target hashes, invalid copy
ranges, and existing outputs. These checks establish source reconstruction only;
they are not a new electrical, DRC or routing validation.

`parts.json` and `f722-heli.kicad_prl` are present and byte-identical in all three
snapshots. Their hashes and sizes are recorded separately as optional omissions.
The helper omits parts metadata, which is not a KiCad project or SES import input,
and local editor preferences. If a later tool needs parts metadata, obtain the
hash-matching file separately; do not assume that the helper copied it.

These recovered projects are historical replay fixtures, not the adopted layout
or a manufacturing release. Original candidates and previous packets are unchanged.
