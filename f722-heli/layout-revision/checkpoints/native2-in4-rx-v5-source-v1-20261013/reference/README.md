# Native2 v5 finite reference and return replay

This source supplement reproduces the saved reference measurements for the ten-track In4 PORT_C_RX_MCU addition. It reads the exact public native3 predecessor and native2 v5 checkpoint exports. It does not modify or refill a board, construct a route, run a power solver, or change an engineering acceptance decision.

The package is source-only checked. Its portable geometry replay has **not** been run as part of packaging. Original local results and their hashes remain unchanged. `SOURCE-NORMALIZATION.json` records the exact source artifacts, pure-function selections, input selections and path changes. `MANIFEST.json` pins every shipped computational file and all four public inputs.

## Placement and inputs

This `reference/` directory is published under:

`f722-heli/layout-revision/checkpoints/native2-in4-rx-v5-source-v1-20261013/`

The default input checkpoint remains the sibling `native2-in4-rx-v5-20261013/`; no input files are copied into the source supplement.

The current board and native export are read from `hardware/f722-heli.kicad_pcb` and `native/after.native.json.gz`. The predecessor comes from sibling `native3-r35-cleanup-v1-20261012/hardware/f722-heli.kicad_pcb` and `current/after.native.json.gz`. No native export is duplicated here. Auxiliary exports, the KiCad installation, the numerical solver and broad historical routing diagnostics are not computational dependencies of these measurements.

Candidate PCB SHA-256: `7d9af57e9b22064fc6b2fd9cde4f2f5b72dc252cdbb1b104e706472bfdbbcdcb`.
Candidate native logical SHA-256: `ae89889c542bca2c96abbdd48e66e70215ab7da84ceb9bccf7d619f8739825a5`.
Predecessor PCB SHA-256: `c3183f7841bae96a59b29fd13ce9789cf47386a9db452a327ca797187d2ca8a8`.
Predecessor native logical SHA-256: `a4fddb679e9d73dd2a7b6300fa8888be47e30ab6f139bd5b78ab308d9192563c`.

## Dependencies and commands

Use Linux, Python 3.12, Shapely 2.2.0 and NumPy 2.2.6, matching the saved measurement environment. There is no installation step in this recipe. The default command checks syntax, package hashes, public input hashes and decompressed native hashes without importing geometry:

```sh
python -B f722-heli/layout-revision/checkpoints/native2-in4-rx-v5-source-v1-20261013/reference/run_review.py
```

When a geometry lane is available, request the isolated replay explicitly. The output directory must not exist and must be outside the immutable checkpoint:

```sh
python -B f722-heli/layout-revision/checkpoints/native2-in4-rx-v5-source-v1-20261013/reference/run_review.py --run-geometry --output "$PWD/native2-reference-replay-output"
```

For another checkout location, supply `--checkpoint-root` pointing to the exact native2 checkpoint directory. The recipe allows no source identity fallback. Each geometry stage uses one CPU, a 512 MiB address-space cap and a 120-second worker cap, with a 125-second subprocess timeout. The runner serializes its five stages, caps output at 64 MiB and retains 128 MiB free space. Coordinate the lane with other project jobs; its local replay lock does not control a separate solver process.

The five stages regenerate source and candidate projection inputs, actual TVS/ESD and RX-transition return attachments, the all-net projection inventory, and targeted finite-path measurements. The final comparison checks the generated metrics against `EXPECTED-METRICS.json`. Its 1e-12 absolute/relative floating comparison tolerance is a reporting comparison, not a geometry repair, clearance waiver or fabrication allowance.

## Retained measurement scope

- All 93 non-GND routed nets plus GND, including FLASH_SCK, and all 1,610 original track projections plus ten new In4 tracks.
- Actual own-drilled In1/In4 source and candidate fill; exact source In1 equality and In4 loss.
- TP2 pad margin, the true curved FLASH_CS collar and finite exit paths, the U15–J11 corridor and annular entries.
- The exact C3 direct supply/return loop, with a lateral-reference exception only for feed tracks `4d92c569-21f9-4a2f-a9fa-75ceb96db10b` and `d098696b-3e91-5200-8273-d992d7b658ef`. Their literal projections remain held.
- Actual protection-ground pads, retained branches and first return vias, their source/candidate plane attachment regions, and both RX barrel transitions.

The small input files hold exact measurement probes and immutable source records. They are selected from the saved source-bound reviews, not replaced by reconstructed approximations. The two U15/J11 annulus rows contain source3 overlap geometry only; unrelated candidate-v1 rows are omitted. Absolute historical provenance paths are represented by artifact names and original SHA-256 identities. Generated path, time and script-hash metadata will differ from the original local reports; numerical geometry and identity comparisons remain explicit.

## Engineering interpretation

The saved v5 geometry supports the practical prototype routing disposition: actual TP2 margin is approximately 0.099781 mm, the checked narrow collar exit supports approximately 0.130589 mm, and the functional U15–J11 approach retains a full 0.254 mm corridor. C3 feed-side margins are approximately 0.027806/0.027810 mm under the declared two-track exception. The J11 radial minimum is not a requirement for 360-degree plane extension when its finite functional return remains intact.

Fresh required conditional DC passed separately for the exact v5 source. This recipe does not reproduce that solve and does not turn DC connectivity into AC or ESD equivalence. The short ordinary-net reference gaps retain targeted fast-edge/ESD bench limits. The external RX edge is not inferred from baud or MCU output slew; R34 is 22 ohms. The two remaining ordinary opens and any future MOSI/SCK interaction belong to later source-bound work. No hypothetical MOSI crossing or unadopted route is included in this recipe.

Replay preserves the original measured limitations: finite observed paths are not global minimum-neck proofs, fabrication-tolerance qualification, extracted impedance/crosstalk bounds, transient ESD qualification, or thermal/flight qualification. A new native fill, added hole, route adjustment or component move requires a new source binding and engineering applicability review.

The two default-path expressions are adapted for this separate sibling source supplement. `../PLACEMENT-NORMALIZATION.json` records their exact upstream and published identities. All geometry measurement expressions and input probe content remain unchanged. The source-only check was run again after this placement adaptation; the portable geometry replay remains unexecuted.
