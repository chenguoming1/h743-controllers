# Native physical protection-path checks

This is a read-only, reusable reconstruction of the published F722 pad-cut proof. It does not route the board, alter the native input, certify ESD performance, or replace KiCad DRC.

## Verified outcome

- Published board `4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f`: the original **18/18** cases pass. Every published per-layer minimum gap, source/target object set, before-cut group and after-cut pad group is reproduced exactly (group ordering ignored).
- Partially routed checkpoint `0ab556b406d336cb94fe54060048bf3e78f8a14dfcc3086d83b7e0232ccb8c86`: **1/18** original-contract checks pass (USB_CC1). The remaining ordinary paths are disconnected before cutting; being disconnected afterward cannot establish protection.
- Four native controls behave as required: a broken source lead fails, a direct front-layer bypass fails, a rear-layer bypass through actual plated vias fails, and a single native track crossing the pad splits correctly despite both remaining pieces retaining the same object UUID.
- Seven additional checks are reported separately. The published board passes **2/7**, and the current candidate passes **5/7** (USB data in both connector orientations and USB_CC2). These results do not change the original 18-case scope or its 18/18 result.

## Method and interpretation

`export_native_copper.py` runs under KiCad 10.0.6 Python and exports the native copper polygons of pads, tracks, arcs and vias with `ERROR_OUTSIDE`, and pad-cut polygons with `ERROR_INSIDE`, at a maximum error of **0.00001 mm**. The exporter preserves polygon holes, every pad UUID including repeated pad numbers, physical copper layers, exact poses, mask openings, actual drill capsules, plated spans, track widths, zone ownership/rules/outlines/fills, native board outlines and exact Edge.Cuts drawing primitives. Board-outline tessellation retains its separately recorded native design error; the copper error bound must not be applied to that outline.

`check_protection_paths.py` removes the selected physical clamp object entirely, then subtracts its native `ERROR_INSIDE` copper from every other same-net copper object on the actual clamp layers. Removing the selected object, rather than retaining the difference of its two approximation envelopes, matches the source proof and avoids inventing thin round-corner copper remnants. Every resulting polygon piece becomes a separate graph node. Native geometric contact on the same layer and actual drilled, plated barrels establish edges. A common net name, pad number or component does not create an edge. In particular, U14 NC pads have **no assumed internal conductivity**.

Native drill voids are subtracted with `ERROR_INSIDE`, preserving the conservative overestimate of surviving copper. Barrel contact requires surviving copper at the actual drill boundary; plated interlayer edges apply only to the native barrel span. A cut involving a plated clamp or intersecting another plated barrel is explicitly rejected because it would require a three-dimensional barrel-cut model. No current contract has this ambiguity. A checked signal net containing a zone is explicitly rejected, even if unfilled, rather than silently ignoring it.

A pass requires all of the following:

1. Source and target are connected before the cut, and each reaches the clamp.
2. Removing the actual pad separates source and target.
3. Both separated groups contact the removed pad's boundary.
4. Every layer where both groups exist has at least the contract's required outside-pad gap: **0.127 mm** for the 14 actual I/O clamps, and the source's historical **0 mm** requirement for the four U14 NC routing-pad cuts.

The `1e-9 mm` contact epsilon handles floating-point arithmetic; it is 1000 times smaller than KiCad's 1 nm integer coordinate unit. It is not a clearance allowance.

The physical graph is scoped to the named signal net, as in the published proof. A clean native electrical-clearance/shorts check is an independent prerequisite: this script does not certify the absence of cross-net copper shorts. Component-internal impedance, diode conduction, resistor conduction, return-path inductance, transient clamp stress, thermal capacity and manufacturing acceptance are outside this cut proof.

## Contracts

`published-contracts.json` transcribes all 18 cases from `../../../evidence/clamp-first-proof.json`. It is source-bound and does not change thresholds.

`candidate-contracts.json` retains U12 and canonical U14 mappings and substitutes only the reviewed equivalent U13 channel cycle: ESC 1→3, RPM 3→6, SBUS 6→1. Wrong or missing native pad-net assignments fail closed.

`supplemental-contracts.json` separates the additional CC/HV review from the USB-data review by each check's `scope`. All use a stated **0.127 mm** review gap. None is retroactively part of the published 18-case claim:

| Review case | Published result | Evidence |
| --- | --- | --- |
| USB_CC2, D6.1, J1.B5→R15.1 | Fails topology | Source and target still connected after removing D6.1 |
| RPM_HV, U16.1, R25.2→Q1.3 | Fails topology | Source and target still connected after removing U16.1 |
| SBUS_HV, U16.2, R26.2→Q2.3 | Fails review gap | Cut separates, but gap is 0.1065667563 mm |
| USB_P, D3.1, each of J1.A6/J1.B6→U1.45 | Fails review gap | Cut separates, but gap is 0.1257304804 mm |
| USB_N, D4.1, each of J1.A7/J1.B7→U1.44 | Passes | Minimum gap 0.1878044083 mm |

## Reproduce

Use KiCad's Python for export/control construction, and Python with Shapely 2.x for analysis. These can be separate interpreters. From the layout-revision directory, with the scripts installed in `scripts/` and this evidence in `checks/protection/`:

```sh
kicad-python scripts/export_native_copper.py --board ../hardware/f722-heli.kicad_pcb --out /tmp/f722-published-native.json
kicad-python scripts/export_native_copper.py --board hardware/f722-heli.kicad_pcb --out /tmp/f722-candidate-native.json
python scripts/check_protection_paths.py --geometry /tmp/f722-published-native.json --contracts checks/protection/published-contracts.json --out /tmp/f722-published-recheck.json
python scripts/check_protection_paths.py --geometry /tmp/f722-candidate-native.json --contracts checks/protection/candidate-contracts.json --out /tmp/f722-candidate-recheck.json
python scripts/check_protection_paths.py --geometry /tmp/f722-candidate-native.json --contracts checks/protection/supplemental-contracts.json --out /tmp/f722-candidate-supplemental.json
kicad-python scripts/build_protection_controls.py --published-board ../hardware/f722-heli.kicad_pcb --out /tmp/f722-protection-controls
python scripts/verify_protection_controls.py --published-geometry /tmp/f722-published-native.json --published-proof ../evidence/clamp-first-proof.json --contracts checks/protection/published-contracts.json --controls /tmp/f722-protection-controls --out /tmp/f722-controls-result.json
```

`check_protection_paths.py` deliberately exits **1** when any selected case fails and still writes a full report. The current partially routed candidate and the published supplemental review are expected failures. The native exporter verifies the input board's hash before and after; it never saves that input. Controls save only disposable boards in the selected output folder. Control board UUIDs are freshly generated; their individual hashes are recorded in each run.

Full native geometry snapshots and disposable control boards are omitted from the public evidence because the scripts regenerate them directly from the hash-bound boards. `validation-controls.json`, `published-recheck.json`, `candidate-recheck.json`, and the two supplemental reports contain the reviewed results.
