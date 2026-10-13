# Reproduce the native2 v5 checkpoint

This directory separates exact saved-byte restoration from fresh native execution. No command promotes a design, releases manufacturing files or establishes qualification.

## Integrity and saved bytes

From a checkout containing this checkpoint, run:

```sh
python3 recipe/replay_native.py
python3 recipe/restore_exact.py --output /your/new/directory/f722-heli.kicad_pcb
```

The first command verifies all 61 paired files, the ten route primitives and the content manifest. The second consumes the sibling public native3 R35-cleanup board and the deterministic `source-to-candidate.patch.gz`; it requires the exact predecessor SHA-256 and refuses any changed patch context or existing output. Its output must equal the recorded native2 PCB SHA-256. This byte reconstruction was checked during publication preparation. It is not a new copper refill.

## Fresh KiCad replay

Run the following with the Python interpreter belonging to KiCad `10.0.6+dfsg-1` and its pcbnew module:

```sh
python3 recipe/replay_native.py --rebuild-native /your/new/replay-directory
```

The replay copies the paired project into a new directory, replaces the PCB with the exact public source3 board, adds only the ten UUID-bound tracks, synchronizes nets, rebuilds connectivity, refills copper and saves. It requires at least 128 MiB free disk space. It asserts exact output PCB bytes. Different KiCad builds are rejected. This portable replay follows the recorded construction operations but was not executed again during packaging; the recorded native run and independent refill/reopen proof are in `../evidence/native/`.

For fresh standard KiCad checks, use the same installed release in the rebuilt project directory:

```sh
kicad-cli pcb drc --severity-all --schematic-parity --format json --output drc.json f722-heli.kicad_pcb
kicad-cli sch erc --severity-all --format json --output erc.json f722-heli.kicad_sch
```

DRC must retain the two declared unrouted nets; do not reinterpret an unrouted-error category as a zero-error complete board. Do not overwrite the immutable recorded reports with a new run.

## Full engineering evidence

The sibling `dc/` folder preserves the complete raw numerical result as four ordered, lossless chunks and provides read-only verification/reassembly. Compact current receipts are in `../evidence/dc/`. Public portable numerical and reference replay source packages are still pending a separate immutable supplement; this checkpoint does not claim complete executable source closure for those workloads.

The existing public source3 checkpoint supplies historical source exports. Recorded current v5 native exports are preserved here without changes. Generated mesh/cache outputs and later routing trial data are outside this checkpoint. The forthcoming source-only adaptations will document their exact code, input closure, runtime requirements and explicit provenance normalization separately.
