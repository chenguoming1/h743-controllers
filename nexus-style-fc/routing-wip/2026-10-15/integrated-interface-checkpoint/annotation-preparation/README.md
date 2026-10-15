# Guarded assembly-attribute and meaningful-silkscreen transaction

Prepared source-only; **no native KiCad, refill, DRC, CAM, GitHub or production-release action was run here**. The parent selected `filled-0.30` for the sole-lane trial. The move-only variant is rejected for printable-marker adoption and retained as conditional history because its 0.060 mm stroke is below JLCPCB's stated 0.150 mm legend line width.

## Adoption contract: replay on final mechanical source

**Do not adopt either illustrative PCB or apply its board diff over stage07.** The examples were prepared from mechanical `main-left-vias-06`; stage07 advances unrelated slots and signal copper. Replay the transaction against the exact final source SHA in a new sibling directory:

```sh
python assembly-annotation-cleanup/guarded_cleanup.py \
  --source-project <final-stage07-project> \
  --output-project <new-annotation-successor-project> \
  --expected-board-sha256 <exact-final-stage07-board-sha256> \
  --marker-style filled-0.30
```

The helper is pure source editing. It rejects existing output directories, rejects output nested in the source, checks the caller-specified input PCB SHA, full canonical fingerprints of all eight target footprints, exact C/`>` text nodes, and hashes of the relevant libraries, `pcbutil.py`, `design.py`, `export_fab.py` and schematic. Thus a changed target part, pad, pin/net, placement, footprint graphic or source module fails closed for review. It copies final source `hardware` and `tools` into the successor and changes only the allowlisted nodes. It never loads a stale illustrative PCB as the final source. All unaffected final copper, zones, slots, rules and metadata survive byte-exact.

Source/evidence files inherited within `hardware` remain historical; no copied evidence becomes a new validation claim. Root-level old seals, CAM and native reports are deliberately not copied.

## Bound examples and exact artifacts

- Baseline: `main-left-vias-06/hardware/nexus-style-fc.kicad_pcb`, SHA `ccb4bcac2adc3baffce2fcc5f2c891fe91b17384b1ba0064506ade2df7338d8f`
- Printable source illustration: `printable-candidate/hardware/nexus-style-fc.kicad_pcb`, SHA `ea9e5d6fb066c55cf0d4e0ffd4192c8451048de0941450aa4fa2aba657d15b6a`
- Move-only conditional history: `move-only-candidate/hardware/nexus-style-fc.kicad_pcb`, SHA `977b996d98f86e36a8662d493e6f8abbd3fc68f76a7bd51502fb9f6999c33e3a`
- `isolated-candidate` is the earlier move-only preparation; it is superseded by the explicit two-variant package.
- `input-bindings.json`: complete target footprint nodes, target source SHA guards, and r62/mechanical target continuity.
- `printable-candidate/annotation-transaction.json`: every exact before/after raw node, parsed node, new UUID, all copied source hashes, and protected-board canonical hash.
- `printable-candidate/annotation-source-checks.json`: exact unchanged identity/pad/pin/net/placement proof, source package/cathode mapping, package reuse, all actual front-mask aperture and front-silk conservative distances, and assembly selection.
- `printable-source-review.patch`: review only, **not** an adoption patch for a newer board.
- `unit-test-results.json`: nine passing pure-Python tests; mocks are explicitly control-flow checks, not native API or geometry qualification.
- `POLARITY-DRAWING-REVIEW.md` and `datasheet-evidence/source-manifest.json`: exact selected-part primary manufacturer drawings and the reviewed page-7 images.

## Exact board delta

1. U3, L2 and U14: `(attr through_hole)` becomes `(attr smd)`. Each package has exclusively SMD pads and no drilled pads (8/2/8).
2. J4: existing F.SilkS line `a3b8b0d3-051e-475c-9730-f77b531b60d9` at x=101.430 is retained in two pieces, y=119.220…121.475 and 123.325…124.430. Stroke stays 0.250 mm. First piece retains UUID; second gets deterministic UUID `f1c318a2-ce1c-5240-a5d2-6debed355f02`. Text C is unchanged.
3. J6: existing F.SilkS line `29c15410-5881-4b58-b707-0290eb542fd8` at x=112.900 is retained in two pieces, y=128.200…128.875 and 130.725…131.400. Stroke stays 0.250 mm. First piece retains UUID; second gets deterministic UUID `5b217e5a-f21c-54cb-8fe3-b7c966127674`. Text `>` is unchanged.
4. D1/D2/D3: original circle UUIDs remain. Printable centers are (107.200,126.250), (113.600,126.250), (110.400,126.250); local center (-0.800,1.150), endpoint (-0.725,1.150), stroke 0.150 mm, fill solid. Radius 0.075 mm plus half stroke gives a conservative 0.300 mm outer ink diameter. The actual plotted diameter must be checked in native Gerbers before adopting that size as a manufacturing fact.

Every reference, value, supplier identifier, part, pad, pad number, pad net, component position/orientation/layer, model, copper item, mask/paste definition, hole, board text, outline and rule remains unchanged, except the three explicit assembly attributes and five explicit graphic targets. No centering-cosmetic copper change is included.

### Erratum to the earlier advisory C-gap calculation

The r62 advisory used a 0.075 mm stroke radius for the J4 line. Exact r62 and mechanical source both specify **0.250 mm stroke**, hence 0.125 mm radius. The original proposed centerline gap y=121.525…123.275 supplies only 0.100 mm conservative text clearance. Correct endpoints y=121.475/123.325 supply 0.150 mm around the unchanged 1.300 mm conservative C glyph box. No rule or clearance was weakened. J6's earlier calculation already used the correct stroke.

## Authoritative source and reuse

The three attribute changes are duplicated in their existing `hardware/library/NexusFC.pretty/*.kicad_mod` files; no other library bytes change. These imported package libraries are authoritative, loaded by `pcbutil.Board.footprint`, and are not regenerated by `make_footprints.py` (that generator owns mechanical footprints only). The current main/child pair has one consumer of each affected package. The correction is also intrinsically valid for any other consumer of those same all-SMD packages.

All imported artwork libraries remain byte-exact. In particular, J4's generic JST-GH library is shared by J3/J4/J5 and **must not be redrawn**. The new `tools/assembly_annotations.py`, called once from `pcbutil.Board.footprint` immediately after `FootprintLoad`/identity setup and before placement, applies graphics only for project `nexus-style-fc`, exact reference, footprint and LCSC identity. It checks the original shape/layer/width/local coordinates and fails if ambiguous or already changed. J3/J5, child and standalone projects receive no artwork change. It checks, rather than rewrites, the three correct SMD library attributes.

J1 is byte-exact and retains the mechanical source's `smd` attribute. This describes its pads, not an ordinary machine-placement process: it remains a manual child-board slot/fillet joint with empty LCSC selection. J6 remains `smd` with 16 SMT signal contacts, 4 PTH GND shell lugs and 2 NPTH locators. Shell soldering remains a distinct mixed-technology process to qualify; no PTH pad was removed or converted.

## Conservative screening

Printable markers clear every actual front-mask aperture bound by at least D1 0.600 / D2 0.280 / D3 0.230 mm, and every other front silk/text bound by at least 0.175 mm. Both retained-outline/text pairs clear their deliberately enlarged glyph boxes by 0.150 mm. The new outline pieces are strict subsets of the old lines, so add no ink beyond their original bounds. All three markers remain on the actual board pad-1/cathode side, including independent exact-part manufacturer pin/mark mapping detailed in the polarity review.

[JLCPCB capabilities](https://jlcpcb.com/capabilities/Capabilities), reviewed 2026-10-15, specify at least 0.150 mm legend line width and 0.150 mm pad-to-silk gap. This meets a nominal source screen only. It does not establish the final printed feature, body fit, stencil/reflow result or finished assembly orientation.

## Sole-native-lane checks still required

1. Replay onto final stage07; inspect transaction and all nonallowed source preservation. Re-run the final full native DRC/ERC/parity and other mechanical/return/contact checks using the sole lane's established process. No severity suppression.
2. `verify_source_checks.py <new-annotation-successor-project>` can repeat the pure source and aperture screen once the final source has its `mask-paste/after` export. It uses the actual source mask apertures; it does not create them.
3. Run `native_verify_generator.py --candidate-project <new> --expected-helper-sha256 <new/tools/assembly_annotations.py SHA> --out <fresh-output>` using the lane's KiCad Python wrapper. It exercises real `FootprintLoad` and helper behavior for 33 project/reference cases, serializing only tiny dedicated test boards; it does not rebuild the routed board.
4. Run `native_verify_assembly.py --source-project <stage07> --candidate-project <new> --expected-source-sha256 <stage07 SHA> --expected-candidate-sha256 <new SHA> --kicad-cli <approved-wrapper> --out <fresh-output>` using ordinary Python. It invokes the exact reviewed exporter and real native positions on both source/candidate. It requires byte-identical BOM and CPL, U3/L2/U14/J6/D1/D2/D3 inclusion, and J1 omission. These **new actual exports have not run here**. Static selection is 83 parts; historical real-native r62 output matches the same 83 references and omits J1 plus TP1–TP5, but is not a substitute for final export evidence.
5. Inspect native assembly and soldermask-subtracted front-silk Gerbers visually: C and `>` legibility/association, all three exposed filled markers with correct cathode-side relationship, native plotted diameter and no clipping; preserve package negative-mark/triangle-to-pin-1 orientation and review CPL's vendor placement convention. Package mark must face board west/pad 1 for all three. No current/thermal, body-fit, via-in-paste, assembly-process or production signoff is implied.

The old 0.060 mm move-only dots remain conditional history, not the selected printable trial.
