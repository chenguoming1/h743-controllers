# Conditional DC replay for In4 RX v5

The completed source-bound result passes all 294 required conditional cases on
both 0.12 mm and 0.09 mm grids, all 15 impedance checks and all five VCAP loop
resistance checks. The overall result is **false** because the single-feed,
all-cyclic 905X capacity illustration leaves four servo board-pad voltages below
6 V. This failure is preserved in the full raw result.

The current source is PCB `7d9af57e9b22064fc6b2fd9cde4f2f5b72dc252cdbb1b104e706472bfdbbcdcb`
and native logical `ae89889c542bca2c96abbdd48e66e70215ab7da84ceb9bccf7d619f8739825a5`.
The exact hardware and compressed native export remain in the sibling immutable evidence checkpoint, read from
`../../native2-in4-rx-v5-20261013/hardware/` and `../../native2-in4-rx-v5-20261013/native/`. They are required inputs, not downloaded by this
recipe. No mesh/cache from the completed run is included.

This package replays the numerical model against the supplied, saved native
geometry and its frozen physical/DRC evidence. It includes the complete numerical
source, corrected case plan, contact registry, settings, material assumptions,
resolved ledger and every file consumed by the numerical preflight. The separate
native hardware recipe regenerates native geometry and its checks. Documentary
producer snapshots here describe the original checks; they are not substitute
commands for that hardware recipe.

The numerical Python modules and three model inputs are byte-exact copies from
the completed run. `NORMALIZATION.json` records original/public stored hashes
and every changed JSON pointer or text line in documentary copies. Known paths
become relative paths; other historical locators become content identities or
opaque locator IDs. References to changed documentary copies are updated
explicitly. The portable freeze has new file paths/hashes, and the ledger changes
only its freeze-manifest link. The 305 case definitions, 107 finite contacts,
five loops, grids, limits and all material/numerical settings remain identical.
The model contract is
`285961cbf0d79d0ae28e2e2a84b256380da8c6a922b6977a2495b7554c922a95`.

Use Linux and CPython **3.12.14** with the exact versions in `requirements.txt`.
The original KiCad version is part of the hardware workflow, not a dependency
of this frozen numerical replay. Default verification needs only Python's
standard library and does not import the numerical or geometry stack:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B dc/replay.py verify
```

That command checks all published and external input hashes, rebuilds the model
from its plan/registry/settings, and compares every case/contact/loop and setting
with the resolved ledger. The source-only verification was tested during packaging. The following heavy commands are provided for a future
explicit replay; they were not run solely to create this package:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B dc/replay.py prepare --out /tmp/f722-v5-dc-replay
PYTHONDONTWRITEBYTECODE=1 python3 -B dc/replay.py run --out /tmp/f722-v5-dc-replay
```

Prepare repeats the unchanged numerical preflight and the 107-contact finite
port audit. Run requires that prepared receipt, repeats source checks and runs
the unchanged full two-grid solver. Both stages require fresh output destinations
and use a local exclusive lock. All generated output stays under `/tmp`.
The launcher enforces one CPU/thread, 4 GiB address space, 600 seconds for prepare,
1,800 seconds for run, 800 MiB launch admission, a 512 MiB combined package/output
cap and 128 MiB continuous filesystem reserves. It fails closed on changed
inputs, missing dependencies, resource stops or incomplete results. Logs,
watchdog receipts and failed output are retained. Exit 1 represents a complete
overall-false numerical result; inspect its receipt and failures. Exit 2 or a
resource stop is not a qualified result. New result hashes differ from the
historical result because they bind the portable manifest and new execution.

The full completed raw gzip is preserved in the accepted evidence checkpoint as
four ordered lossless chunks of at most 8 MiB. This source-only supplement avoids
duplicating those chunks. Its stored SHA is
`d9c6687a883e02bcb8af61733b938d374ba5e9d8c3199d5b63a2aab3e467f1ca`,
and its exact logical JSON SHA is
`37cccadce9ac8671ac0c2c1dff28127a183132878858505106737be6b67bc940`.
Documentary references to `evidence/result.json.gz` identify that reassembled
historical artifact; it is not needed to regenerate the numerical solution.

This is a conditional fixed-temperature DC screen. The copper assumptions are
105 °C, 0.015 mm thickness/plating and 95% IACS. It retains ideal terminal lands,
annuli and package assumptions. Global reported density/layer-loss/barrel-current
extrema do not establish local neck ampacity. AC return behavior, thermal
performance, startup, flight, manufacturing and final board qualification remain
outside this result. Historical source3 findings and the untested earlier v1
candidate are not substituted for this v5 result.

## Supplement placement

This directory is shipped under `f722-heli/layout-revision/checkpoints/native2-in4-rx-v5-source-v1-20261013/dc/`. Run the commands above from the source-supplement root. The eight external freeze locators and six package input locators are rebound to the existing evidence checkpoint; the ledger changes only its freeze-manifest hash. Documentary producer snapshots retain the preceding portable package's relative provenance strings. They are recorded evidence, not operational file locators for this launcher. `../PLACEMENT-NORMALIZATION.json` records this additional placement adaptation. Numerical sources and all three corrected model inputs remain byte-exact. The full historical raw result is restored with the evidence checkpoint's `dc/verify_dc_chunks.py`; it is not duplicated here.
