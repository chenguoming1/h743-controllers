# Exact historical source recovery from accepted75

This compact packet reconstructs the exact historical inputs for retained routing
sessions. It contains no complete PCB or schematic. Use the accepted75 hardware
project published alongside the v5 routing tools, including its project, rules,
schematics, library tables and local libraries. The authoritative base PCB is:

`008d0b11df400284d12750c7f5c877b43a7ea28ffddbf4a4b799c3ae7ec4917e`

No Git commit is claimed. Any source location with these exact board bytes and
the matching paired-file hashes in `paired-files.json` is suitable. A board from
a later routing revision is not an interchangeable base.

## Reconstruct complete paired projects

Run with Python 3 (standard library only). Each output directory must be new:

```sh
python3 rebuild_historical_source.py project --base-project /path/to/accepted75/hardware --source candidate09 --out /path/to/new/replay09
python3 rebuild_historical_source.py project --base-project /path/to/accepted75/hardware --source candidate12 --out /path/to/new/replay12
```

Each command verifies all 63 required source files before creating any output,
then writes the historical PCB and its 62 paired files. The accepted75 source is
read-only. No solver, KiCad installation, Java process or network is required.
Use the reconstructed directory as the corresponding historical source project
in the routing packet's session replay instructions.

- candidate09 PCB: `544491a48469d418ed47cf5da12b6b9406db282d60a3cda77b154f6ed11a869d`
- candidate12 PCB: `508b5a36ed12795c4a2486b699f321f0f9867e29717175455e8fd7fc6f1f525a`

candidate09 also needs the four included schematic deltas for `f722-heli`,
`io-ports`, `power-bec` and `usb-clock`. Its other 58 paired files are byte-identical
to accepted75. All 62 candidate12 paired files are byte-identical to accepted75.
The project, rules, footprint and symbol libraries are unchanged in both cases.
The helper applies these requirements automatically; copying only the historical
PCB into the latest schematic project would not recover candidate09's exact pair.

For a single file, use the lower-level mode:

```sh
python3 rebuild_historical_source.py file --base-file /path/to/accepted75/hardware/f722-heli.kicad_pcb --delta candidate09.f722-heli.kicad_pcb.delta.json --out /path/to/new/source09.kicad_pcb
```

## Delta format and verification

Each JSON operation is either a literal UTF-8 string or `[offset, count]`, a byte
range copied from the hash-checked base. Candidate12 first applies the explicitly
named, deterministic `compact-footprint-metadata/v1` transformation: it places
the MPN, Manufacturer, LCSC and Supplier footprint properties on one line without
altering token or quoted-string contents. Its intermediate SHA-256 is checked
before any byte-copy operation. This preserves the exact historical formatting
while keeping the delta small. Historical zone-fill differences are recovered
from copy ranges and short text literals, without recalculating geometry.

Every delta verifies the original base hash, final byte count and final hash.
Project mode also checks every delta file's hash from `paired-files.json`.
`verification.json` records successful full-project byte comparisons against both
historical snapshots and rejection of wrong bases, altered target hashes, altered
payloads, out-of-range copy instructions and existing output directories. These
are source-reconstruction controls, not new electrical or routing validation.

`parts.json` is absent in candidate09; candidate12 and accepted75 have identical
copies. It is not a KiCad project or SES import input, so the helper omits it and
does not invent a historical candidate09 copy. `f722-heli.kicad_prl` is identical
in all three snapshots but contains local editor preferences; it is also omitted.
Their observed presence and hashes are recorded separately from required files.
Tools that specifically require parts metadata must obtain it separately from
the appropriate source; this helper does not claim to recover absent metadata.

The recovered projects are historical replay fixtures, not an adopted layout or
manufacturing release. Original candidates and prior routing packets are unchanged.
