# Recover historical ordinary-session inputs

The published native 80-open board is sufficient to reconstruct the two exact historical source PCBs used by the retained real sessions. These small line deltas remove only the recorded differences; they do not approximate geometry. The helper verifies complete input/output byte hashes and refuses to overwrite an existing output.

Use the hardware directory from Git commit `71c5683d691f96189043ede9ea81c022bb41b90c`, path `f722-heli/layout-revision/hardware/`. Its PCB SHA-256 is `e38e71c1960fc52881ee699117aa48c7e43483562ea22ec276ec0dc1d2138883`. Extract that directory into a new disposable project folder and move its PCB to a separate `published80.kicad_pcb` path. Keep all matching KiCad project, rules, schematics and libraries; their exact historical equivalence is recorded in `verification.json`.

If that commit is absent after a squash merge or branch deletion, `git fetch origin refs/pull/11/head` retrieves the verified PR11 head. The reconstruction also accepts the identical base PCB from another commit, because its full byte hash is the authority.

From this folder, reconstruct one input into the disposable project's now-vacant `f722-heli.kicad_pcb` path:

```sh
python3 rebuild_historical_source.py --base-board /path/to/published80.kicad_pcb --delta support85.delta.json --out /path/to/disposable-project/f722-heli.kicad_pcb
```

`support85.delta.json` produces SHA `1069f4ce2d92088271a4ec3154ff0ed35e88adc4100705f75c4aaa4a884717bd`, the input for `sessions/swclk`. For `sessions/accepted80`, use a separate disposable folder and `swclk84.delta.json`, which produces SHA `fce917be01bb2071a8d415763ad375ec6a0b897f62a367148b5cca13b8889764`. Then follow the compact-session replay commands in `REPRODUCE.md`.

These are historical replay fixtures, not the current adopted layout or manufacturing files. Both byte-exact reconstruction controls pass; wrong-base and tampered-target checks fail as expected. No old PCB, compiled binary or private filesystem location is embedded in this packet.
