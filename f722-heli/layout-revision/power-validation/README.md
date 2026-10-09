# Scoped static copper validation

This is prototype analysis software. Its retained evidence is **synthetic tests only**. This source bundle contains no F722 board mesh, completed case ledger, real-board electrical acceptance, thermal rating or flight qualification. Both input templates are disabled and contain no board paths, load allocations or material defaults to adopt accidentally.

## Reproduce the synthetic tests

Tested with Python 3.12.14 and the exact dependency versions in `requirements.txt`. KiCad is not needed for these tests.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest -v test_static_validation.py
```

The expected result is 19 passing tests. `synthetic-tests.json` records the checked source hashes, actual versions and execution result. Tests create only small analytical fixtures in temporary directories. They do not load a project PCB.

Coverage includes finite-contact analytical resistance at four spacings; irregular/holed mesh conformity and convergence; disconnected islands and point-touch rejection; saved fills and all-net drill voids; exact fractured-bridge decoding and a KiCad-generated multiple-hole/disconnected-outline fixture; round/slotted barrel resistance and unflashed layers; finite positive and return voltages; converter and whole-circuit power conservation; unequal same-source positive/return feed sharing; a narrow feeder before a wider trunk; resource limits; stale and unfinished input refusal; invalid/duplicate ledgers; protected-output aliases; and numerical guards around marginal voltage floors.

## Source allowlist

`MANIFEST.json` is the complete publication allowlist and SHA-256 inventory. Copy only its listed files plus the manifest. Do not include caches, temporary fixtures, virtual environments or future board data merely because they are in the same directory. The manifest's own hash is provided separately by the packaging owner.

## What the programs do

- `export_native_copper.py` reads a KiCad PCB without refilling or saving it. It exports native pads, tracks, arcs, vias, saved zone fills, drilled capsules, layers and source hash. The supported exporter runtime is KiCad 10.0.6 with its `pcbnew` Python module; use that runtime separately from the analysis virtual environment.
- `exact_native_contours.py` decodes native fractured saved-fill rings by cancelling only exact reversed integer bridge edges. It preserves every surviving directed boundary edge, exact signed integer area and all surviving coordinates. Ambiguous topology refuses. There is no geometric repair, snapping, buffering or tolerance relaxation. Filled-zone exports include per-contour representation receipts; raw native zero-hole storage must not be interpreted as an absence of physical antipads.
- `copper_fem.py` builds bounded triangular sheet meshes, subtracts actual drills, keeps exact finite contact boundaries and explicit plated spans, and solves DC fields/finite-port impedances. It reports resistance, KCL, energy, barrel currents/losses, per-layer sheet loss and peak element density/location. Density is never an ampacity rating.
- `dc_circuit.py` couples those finite copper ports with explicit sources, fixed-current loads, device/contact/harness resistances and conserved-power converters. It retains actual local return potential and checks differential voltage probes.
- `validate_static.py` binds a new ledger to immutable source/check files, checks scoped completion, compares at least two grids, checks voltage/resistance margins and cross-checks coupled cases against direct fields. It retains one network mesh at a time; compact matrices couple the networks.

## Reproduce the native synthetic fill fixture

`native-fill-fixture.json` was produced with KiCad 10.0.6. It contains only a synthetic polygon set with two holes and another disconnected outline. The generator checks explicit-hole export, a cloned native Fracture() representation, exact area/edge preservation and unchanged input objects. The ordinary analysis suite independently checks valid exported polygons and equal copper geometry. It does not repair the output.

With KiCad 10.0.6's Python runtime, independently regenerate to a new file:

```sh
python generate_native_fill_fixture.py --out fresh-native-fill-fixture.json
```

No project PCB is loaded or saved. `test_exact_native_contours.py` additionally checks handcrafted exact bridges and rejection of ambiguous touching cycles without requiring KiCad. The fixture and generator do not establish any project-board electrical result.

## Prepare a real input separately

Real-board analysis is a later activity requiring a completed scope, reviewed assumptions and an allocated compute budget. No ready real-board inputs are supplied here.

1. Freeze an immutable PCB copy after its intended copper and return paths are complete. Refill, save and verify saved fills using the board workflow. The exporter itself never performs these operations.
2. Using KiCad's Python runtime, export that copy:

   ```sh
   python export_native_copper.py --board input/board.kicad_pcb --out input/geometry.json
   ```

3. Run native standard and all-track DRC, native physical pad-group connectivity, schematic/native parity, and the applicable drill/mask/clearance/layer/keepout checks on exactly that frozen copy. Preserve visible warnings. Keep current parts metadata with these inputs. This bundle does not generate or replace those project-specific check reports.
4. Copy `freeze.template.json`, fill relative paths and SHA-256 hashes for every required file, select `power-only` or `final-board`, identify all tested nets, and record the actual saved-fill/check evidence. Only then set its status to `frozen-for-scoped-static-screen`. The two evidence booleans are receipts for performed checks, not substitutes for them.
5. Copy `ledger.template.json`. Enter all four material assumptions, at least two strictly decreasing positive mesh spacings, convergence limits, real contact mappings, required unit/loop/loaded cases and their limits. Bind it to the SHA-256 of the completed freeze manifest. Set its status to `ready` only when all assumptions and endpoints are reviewed.

Source/check contracts:

- Geometry: the supplied exporter's `kicad-native-copper/v1` schema, unchanged source, millimetre units, valid native outline and matching board hash.
- Connectivity: `board_sha256`, and `nets[net]` containing `pad_group_count` and `groups[].pad_uuids`. Every tested net must have exactly one native connected pad group containing every assigned native pad UUID on that net.
- Parity and physical check receipts: matching `board_sha256` and `passed: true`. Preserve their underlying evidence and scope descriptions in the frozen input set.
- Both DRC files: complete native JSON with `violations` and `unconnected_items`. Geometric/parity errors or ignored checks refuse. `power-only` allows unrelated ordinary opens; opens touching a tested net refuse. `final-board` additionally requires zero ordinary opens.
- All listed files: exact SHA-256 entries in the manifest. Native DRC JSON lacks an intrinsic PCB hash, so the freeze owner is responsible for running and binding those reports to the correct copy. This catches accidental stale reuse; it does not prove that an external check was performed correctly.

Run preflight before allocating numerical work:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python validate_static.py \
  --freeze input/freeze.json --ledger input/ledger.json --out preflight.json
```

Preflight does not mesh. It refuses disabled templates, stale files and incomplete tested scopes. When the scope and compute budget are approved, append `--run` and use a separate result filename. Exit code 0 means preflight passed or the enumerated conditional static screen passed; 1 means the enumerated static limits/sensitivity did not pass; 2 means input or numerical refusal. Outputs may not alias source files, including when writing a refusal.

Resource defaults are 160,000 nodes, 320,000 triangles, 300,000 tiles, 128 contacts and 120 seconds per network construction/solve stage. Caps refuse rather than silently coarsening. Run single-threaded. Mesh spacing is numerical sampling, not copper thickness. Choose it according to the actual geometry and resolve inadequate convergence within the allocated budget.

## Ledger fields

Each `networks` item has a native `net` and a `contacts` mapping from unique circuit-node names to `{ "pad": "REF.NUMBER", "layer": "B.Cu" }`. The indicated pad must belong to that net. Contacts use finite actual copper on that physical layer, not a pad anchor point. Distinct/equivalent ports cannot be silently shorted: overlapping contacts or a contact spanning disconnected copper refuse. Use one port and a reviewed circuit-node alias for an actually joined native land. Every loaded path retains its intervening narrow conductors and plated spans; a net label or nominal trunk width creates no shortcut.

All material fields are explicit: `temperature_C`, `thickness_mm`, `conductivity_IACS`, `plating_mm`. The actual native stackup sets layer-center distances; effective sheet thickness and plating are separate resistance assumptions. Barrel area is drilled-capsule perimeter times plating thickness. No fabrication tolerance is inferred from the nominal CAD stackup.

`unit_transfers` contain `name`, `net`, `source`, `sink`, optionally `maximum_ohm`. `loops` contain a unique `name`, a nonempty `legs` list of net/source/sink objects, optionally `maximum_ohm`. The sum describes the specifically named DC unit legs. A missing limit is descriptive, not an invented pass threshold.

Loaded `cases` contain a unique `name`, `reference_node`, explicit `assumptions`, optional `nets` subset, and these entries:

- `sources`: name, p, n, voltage_V; optional sense_p/sense_n. Source current is positive from p to n into the source; delivery generally has negative current.
- `resistors`: name, p, n, ohm. Model source leads, contacts, harnesses and device on-resistance explicitly. Zero resistance refuses; a deliberately ideal internal tie can use a named zero-volt source.
- `loads`: name, p, n, current_A. Use actual positive and local ground contacts; idealizing every return at the global reference would bypass real return loss.
- `converters`: name, in_p/in_n, out_p/out_n, voltage_V, efficiency; optional quiescent_A, sense_p/sense_n, minimum_input_V, maximum_input_V, maximum_output_A. Input demand is output power divided by efficiency and actual local input voltage, plus quiescent current.
- `probes`: name, p, n, minimum_V and/or maximum_V; optional purpose. Every loaded case needs bounded differential voltage probes.

Use one external source and separate positive/return lead/contact resistances when two feeds come from the same supply. Their current sharing is solved, never assumed equal. Include actual GND copper in loaded physical-board cases. Sense pins must not substitute for real power injection terminals. State component and harness assumptions in the ledger; copper resistance does not supply them automatically.

The final two grids must meet explicit impedance sensitivity limits. A voltage/resistance margin must clear the observed grid change and the selected absolute guard. A tiny positive scalar margin can therefore remain unresolved. These guards are sensitivity checks, not rigorous discretization or manufacturing error bounds.

## Interpretation limits

Only the cases explicitly enumerated in a future ledger are assessed. The supplied synthetic receipt does not assert native-board continuity, loaded voltage, current capacity or loop compliance. A `power-only` result does not qualify a subsequently completed board after signal routing/drilling changes.

Fixed-temperature DC loss and current density are not thermal rise, ampacity, a contact rating or a guaranteed pulse/fault envelope. Equipotential lands/annuli omit within-land, pin, solder and contact heating. Polygon approximation and grid convergence do not establish a strict manufacturing bound. Material temperature assumptions do not alter component body-temperature ratings.

This model does not establish startup/inrush, handover/backfeed, regulator dropout or switching dynamics, ripple, magnetic behavior, AC loop stability, ESD/EMC, sensor noise, signal-level compatibility, CAM/assembly acceptance or flight qualification. Native/project checks and first-article measurements remain separate.
