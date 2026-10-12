# WIP: native6 routing checkpoint

The latest checked WIP routing source is **hardware/f722-heli.kicad_pcb in this
checkpoint**, with its complete 61-file paired project. The repository's top-level
f722-heli/hardware board is an older snapshot and does not represent this result.
This checkpoint is adopted for geometric routing continuation only. Six opens
remain; current power/DC/VCAP, timing, reference-return, assembly and physical
qualification are pending. It is not fabrication-ready or flight-qualified.
The stock-firmware I2C timing/sink guarantee gap remains unresolved.

## Actual result

KiCad 10.0.6 refill and DRC report six unconnected items, zero other DRC errors,
six inherited dangling-copper warnings, and zero schematic-parity issues.
Both GND island warnings from the preceding six-open trial are eliminated.

The physical audit checks all 128 nets. No pad pairs or retained fragments are
lost against accepted native7; FLASH_MISO U1.35–U3.2 is restored. No pad-pair
connectivity changes from the original native6 trial. All nine edited net trees
are complete, including all 47 CORE pads and 133 GND pads, with no pad-free
islands. All six cleanup junction witnesses, nine affected real-pad contact
checks and the U2 same-barrel repair pass. The 22 actual IO protection cases have
21 passes and the inherited PORT_C_RX_EXT incompleteness, with zero regressions;
all three external NC-land bridge checks pass. These are geometry/DC connectivity
findings, not proof of power integrity, timing, return paths or assembly quality.

Remaining physical endpoint roles (six opens across five nets):

- PORT_C_RX_EXT: two gaps among J11.1, clamp U15.1/U15.10, and R34.1. Those three
  pad groups remain separate; the two clamp pads are connected to one another.
- PORT_C_TX_MCU: U1.29 to R35.2.
- PORT_C_RX_MCU: U1.28 to R34.2.
- FLASH_MOSI: U1.36 to U3.5.
- FLASH_SCK: U1.34 to U3.6.

The six warnings comprise two dangling PORT_C_RX_EXT tracks, one dangling
PORT_C_RX_EXT via, one dangling PORT_C_TX_MCU via, and two dangling
PORT_C_RX_MCU vias. evidence/drc-all.json preserves exact UUIDs and locations.

## Construction and evidence

The compiled source7-to-native6 recipe removes 34 original route records and adds
67 tracks plus seven through vias; R6 and D1 have four exactly transformed pads.
All 60 non-board files are byte-identical to the accepted native7 paired source.
All 2,346 retained non-moved native objects preserve geometry/settings after a
proved bijective integer net-code normalization. Native KiCad renumbered 37 net
codes; this normalization is comparison-only. Five exact R6 text angles normalize
from 270 to 90 degrees in the inverse-pose control; all other text fields remain
exact. Pad/aperture settings, stackup, net names and zone definitions are retained.
The structural summary records these narrow qualifications explicitly.

provenance.json binds the delivered board, source7 hardware, compiled recipe,
original native export and executed checks by SHA-256 and Git blob hash.
The recipe is preserved byte-for-byte; its historical handoff_path is provenance
only and is not used by the portable replay wrapper. Bulky native JSON and
auxiliary geometry stay outside this compact checkpoint. The topology summary
includes exact witness details and binds the full original audit by SHA-256.

## Reproduction

Byte verification needs only standard Python:

    python scripts/verify_package.py

Native re-export uses KiCad 10.0.6 Python with pcbnew:

    python scripts/export_native_copper.py --board hardware/f722-heli.kicad_pcb --out /tmp/native6.json

For comparison with the saved native-export SHA, serialize the exported JSON
with sorted keys, compact separators, and one trailing newline. An export does
not refill or modify the input board.

Run the authoritative DRC against this paired project with:

    kicad-cli pcb drc --format json --all-track-errors --severity-all --schematic-parity --output /tmp/native6-drc.json hardware/f722-heli.kicad_pcb

Exact native reconstruction requires the published predecessor at
f722-heli/layout-revision/checkpoints/joint-native7-20261010/hardware. All 61
source-file identities are in provenance.json. Run with KiCad's Python:

    python scripts/rebuild_native6.py --source-hardware /path/to/joint-native7-20261010/hardware --output /tmp/new-native6-rebuild

The output folder must not exist. The wrapper runs the original construction
body with extracted structural checks, and fails unless the final board SHA
matches this checkpoint. Its syntax and extracted comparator were checked here;
the comparator exactly reproduces the executed structural ledger. The newly
portable wrapper itself was not executed during packaging. Original construction,
refill, DRC and full topology checks ran before packaging.

The full topology checker is source-bound to the preserved accepted7 export,
original native6 control audit, protection contracts and pinned contact kernels.
This compact package includes its result and provenance, not those larger replay
prerequisites. The commands above reproduce native geometry, structural checks
and DRC; they do not independently rerun the full topology/protection audit.

The publication is additive: all 7,341 existing repository paths are preserved.
No historical diagnostic backlog or raw auxiliary export is added here.
