# Guarded integration handoff to the sole native routing lane

Use `candidate-02/nexus-style-fc` as the implementation package. Do not install its r54-derived main board over later accepted copper. Read scripts before running them. Do not run `build_all.sh`, a full generator, or fabrication export.

1. Preserve the latest accepted main/header boards, both project/rule files and parent-frozen schematics in a new integration rollback directory with exact SHA256s. Keep the original source untouched.
2. Copy the implementation files listed in `overlay-manifest.json` into the integration project. The overlay deliberately excludes candidate native boards, main schematic, project/rule files, unrelated sources, and the old assembled model. Keep the parent's latest approved main schematic, including any separately frozen filter-only correction.
3. Run the guarded mechanical transaction from the integrated tools directory, using exact accepted input paths and hashes, into a fresh output directory. Inputs are a main PCB, original header PCB and header schematic. Example syntax:

```sh
python tools/apply_header_interface.py \
  --main /verified/latest/nexus-style-fc.kicad_pcb \
  --child /verified/original/nexus-header-board.kicad_pcb \
  --child-schematic /verified/original/nexus-header-board.kicad_sch \
  --expect-main EXACT_LATEST_MAIN_SHA256 \
  --expect-child 99d06c7ec685f776f357958c22f684f198f9ef5bf7e9bed437833c9d6aadfba0 \
  --expect-child-schematic 7514ce37f03803bdbce5a2f54f290ff78e6cf1f719f5d51fb3509116a4e1cb10 \
  --out /new/nonexistent/integration-transaction
```

This verifies exact input hashes and reviewed J1/body/header/slot-keepout anchors, creates rollback files and implementation bindings, preserves existing tracks/vias/connected pad identities, makes the approved mechanical changes, clears cached fills and writes an exact transaction report. The output directory must not already exist. Optimized Python is rejected so assertions cannot be disabled. A future source that changed J1, the header or slot keepouts is rejected even if its file hash is supplied; reconcile those changes explicitly rather than removing guards.

4. Install the transaction's main PCB, header PCB and header schematic into the new integration project only. The header schematic changes only two footprint strings. Do not overwrite the parent's latest frozen main schematic. Capture this pre-copper mechanical baseline and hash manifest.
5. Repair local copper and refill both boards. Review all native failures, including actual track-to-edge and moved-pad isolation/connection failures. The source-bound inventory includes complete mating-net and DSM_DATA records; it is not a deletion list. Preserve all complete power/service/return ports and widths. The independent review's exact track UUID witnesses identify a minimum repair scope, not a complete DRC list.
6. Validate the mechanical delta against the original source and copper changes against this new mechanical baseline. The existing reroute validator intentionally rejects footprint/outline changes against an old geometry baseline; do not disable it or present that expected difference as a clean unchanged-geometry run. The mechanical transaction/independent review supplies the bounded intentional delta; the native/copper validator should then prove no extra geometry drift during routing.
7. Run exact integrated native refill, all-visible DRC, ERC and schematic parity/opens checks with unchanged rule floors and suppression settings. Compare both schematics against their appropriate frozen inputs. Main schema SHA49f9… is only the r54 mechanical package baseline; the parent may supply a newer explicitly approved filter-only freeze. The static checker currently asserts the r54 schema hash and must be explicitly rebound to a parent-verified new freeze before using it on that integrated source.
8. Only after repaired native-valid child geometry, export the candidate-specific child model using the approved KiCad10 runtime and `build_header_board.py --vrml`. The connector WRL is provided unchanged at the correct shared-library path. Do not invoke that builder without `--vrml`, because that rebuilds the child and discards copper. The target file is `hardware/library/NexusFC.3dshapes/nexus-header-board-root-relief-candidate.wrl`, already referenced by the native joint and generator.
9. Inspect exact integrated 3D geometry, model units and transform, nominal seating, the full tab/root insertion depth, contact alignment, connector/body collision and specified tolerance extremes. The unmodified original assembled WRL is a rollback/reference only. Rebind rendered/exported results to exact native/model hashes.

Native geometry/electrical completion would still leave fixture, manufacturing-tolerance, remaining-ligament, current/solder and physical load/prototype tests unresolved. No manufacturing output or fabrication approval follows from this handoff.

## Separately frozen parent metadata update

After this mechanical candidate was produced, the parent supplied a new main schematic freeze at `nexus-footprint-filter-cleanup/work/hardware/nexus-style-fc.kicad_sch`, SHA256 `261570f128cc14e2c3e975b22aaf653da677c0fafac50a5459d2121a59db369b`, and SchematicStock SHA256 `a7548153edb9eeb6de73243ab493f5bc89c06b1f01e23cdf25240ae5fdfa447a`. These are separately owned metadata-only filter updates. The mechanical overlay excludes both, and the native integration must use the parent's verified paths/freeze rather than this package's older copies. No claim that the old schematic hash is the latest release is intended.
