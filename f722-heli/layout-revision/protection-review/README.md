# Actual bonded TVS signal-I/O coverage review

## Result

The historical original and supplemental contracts cover **19 of 20 populated, bonded signal-clamp channels**. They omit **D7.1, DSM_RX_EXT**. The additive contract is `J12.3 → D7.1 → R38.1`, with the same **0.127 mm** outside-pad review gap used for the other actual I/O clamps. This new review criterion is separately labeled; it is not retroactively part of the published 18-case qualification.

Both sources pass **6/22 actual-I/O endpoint cases**, equivalent to **4/20 distinct actual-clamp channels**. The four complete channels are USB_P, USB_N, USB_CC1 and USB_CC2. USB_P and USB_N each have two connector contacts and therefore two cases. **Coverage completeness is not physical-route completeness.** Sixteen active signal-clamp channels remain unfinished on both sources.

The added D7 case is **0/1 on both sources**. J12.3, D7.1 and R38.1 are three separate native copper groups before the cut. Neither J12.3→D7.1 nor D7.1→R38.1 is complete; an already disconnected path cannot pass the cut proof. R38 is a series resistor: this check ends at R38.1 and does not infer resistor conduction or qualify R38.2→U1.43 downstream.

| Source | Native PCB SHA-256 | Original historical | Actual subset of original | NC routing-pad subset | Supplemental | Complete actual-I/O view | Distinct actual channels |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| source69 | `9cf04c88ebd31d7e2c12bdb8a9f80e01b615a7bdb94a73fc2234208a2e0a14c8` | 1/18 | 1/14 | 0/4 | 5/7 | 6/22 | 4/20 |
| source62 | `fd8fd21062c61992ec992481d394e19a6a99cfe8ec58405ed1e391c5e3836bfa` | 2/18 | 1/14 | 1/4 | 5/7 | 6/22 | 4/20 |

Source62's additional original-contract pass is **PORT_B_RX_EXT at U14.7**, a package NC routing pad. J10.1 reaches the actual U14.4 I/O pad, but **U14.4→R32.1 remains disconnected**, so the actual U14.4 cut contract still fails. It must not be counted as a completed protected port.

## Exact part and native-terminal inventory

Exact MPN fields were read directly from each PCB with KiCad 10.0.6. Every native terminal UUID, net and location was cross-checked against a freshly generated native copper snapshot. The pin roles were reviewed against these manufacturer datasheets on 2026-10-09:

| Fitted MPN and references | Signal pin roles | Applied native channels | Primary source |
| --- | --- | --- | --- |
| onsemi ESD9M5.0ST5G, D3–D7 | Pin 1 cathode/signal; pin 2 anode/GND | D3.1 USB_P; D4.1 USB_N; D5.1 USB_CC1; D6.1 USB_CC2; D7.1 DSM_RX_EXT | [ESD9M5.0S/D Rev 9](https://www.onsemi.com/download/data-sheet/pdf/esd9m5.0s-d.pdf), pp. 2 and 4, CASE 514AB STYLE 1 |
| ST USBLC6-4SC6, U12/U13 | I/O pins 1/3/4/6; GND 2; bias 5 | U12.1 SERVO1_MCU; .3 SERVO2_MCU; .4 SERVO3_MCU; .6 TAIL_MCU. U13.1 SBUS_MCU; .3 ESC_MCU; .6 RPM_MCU | [DocID11068 Rev 7](https://www.st.com/resource/en/datasheet/usblc6-4.pdf), p. 1 Figure 1 |
| TI TPD4E05U06DQAR, U14/U15 | I/O 1/2/4/5; GND 3/8; NC 6/7/9/10 | U14.1 PORT_A_RX_EXT; .2 PORT_A_TX_EXT; .4 PORT_B_RX_EXT; .5 PORT_B_TX_EXT. U15.1 PORT_C_RX_EXT; .2 PORT_C_TX_EXT | [SLVSBO7O Rev O](https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf), p. 4 Table 4-2 |
| Nexperia PESD15VS2UT,215, U16 | Cathodes 1/2; common anode 3 | U16.1 RPM_HV; .2 SBUS_HV | [13 April 2023 datasheet](https://assets.nexperia.com/documents/data-sheet/PESD15VS2UT.pdf), p. 2 Table 2 |

There are **23 bonded signal channels in the fitted packages, 20 used and three unused**. U13.4, U15.4 and U15.5 are explicitly unused native I/O nets. They are reported, not treated as missing external protection paths. U14 has four net-assigned NC copper pads; U15 has four unused NC pads. None is counted as a bonded I/O channel.

The exact BOM corroboration is `repo/f722-heli/docs/component-source-index.json` and the native PCB MPN fields; the latter bind the findings to these current sources. U13's current ESC3/RPM6/SBUS1 channel assignment is preserved.

## Coverage and endpoint dependencies

The `channels` inventory in each `coverage.json` includes every terminal on each protected signal net, its UUID, native coordinates and copper layers, the old contract IDs, and the separate actual-I/O contract IDs. Every signal-net terminal is covered as source, target or actual clamp, except explicitly classified package NC routing pads. The inventory fails closed if any active bonded channel is missing, its exact MPN differs, or a required endpoint has the wrong net.

Each `endpoint_dependencies` entry separately reports:

1. Source→actual-clamp native connectivity.
2. Actual-clamp→target native connectivity.
3. Source→target connectivity before cutting.
4. The full actual-pad cut result, with the corresponding report file.

All 14 historical actual-clamp cases, all seven supplemental cases, and the new D7 case are in `contracts/actual-io22.json`. The actual-I/O view adds provenance fields and classifies the supplemental entries as actual clamps. The original contract files, scopes, thresholds, IDs and results are untouched. The four NC cases remain in the historical 18-case rerun and are counted separately.

**NC-first is a retained engineering routing convention, not asserted user authority.** TI permits optional straight-through routing at these unbonded package pads. The user goal is preserved protection and pinout. This audit neither changes the existing NC contracts nor turns an NC pass into evidence that the actual protected path is complete.

## Scope boundaries

- D8 (`SMF5.0A`, USB_VBUS_RAW) and D9 (`SMF15CA`, VX_RAW) are explicitly inventoried as power-rail suppressors outside this **signal-I/O** cut review. They require the applicable power-path/return qualification. This is not an all-TVS or all-power protection claim.
- GND and bias pad **net assignments** were checked. Ground-return physical connectivity, ground inductance, rail steering, transient stress and MCU residual voltage were not qualified here.
- Downstream sides of series resistors, component-internal conduction and ESD survival are outside the same-net physical cut model.
- A clean cross-net clearance/shorts check remains an independent prerequisite. This packet does not replace DRC or manufacturing acceptance.

## Portable packet and preservation

- contracts/legacy-original18.json, legacy-published18.json and legacy-supplemental7.json are exact copies of the existing historical contracts. They remain separate from contracts/added-d7-1.json and contracts/actual-io22.json.
- receipts/source69/ and receipts/source62/ contain unchanged cut-check result files, portable coverage/dependency inventories, native terminal/MPN inventories, and source/hash receipts.
- sources/part-pin-map.json records exact fitted MPNs, manufacturer datasheet URLs, pin roles and the corroborating public BOM source.
- tools/ includes the unchanged generic physical checker and native exporter, its contour dependency, a read-only terminal exporter, and the portable receipt/replay verifier.
- provenance.json records which contract and tool bytes are unchanged. MANIFEST.sha256 binds every distributed payload file. MANIFEST.json gives file sizes and the same SHA-256 values.

No board was saved, routed or otherwise mutated. No historical contract, check implementation, test or owner result was changed. Every original and supplemental per-case result reproduced its corresponding owner result exactly on both sources. Fresh native exports independently confirmed unchanged input board hashes. Existing control tests were preserved; they were not rerun because the generic checker was unchanged.

The source boards and large native polygon snapshots are not included in this packet. Reproduction requires each retained source board matching its full SHA-256; a later board cannot substitute. Source69 was the accepted checkpoint at the time of review, and source62 was isolated review work. This packet does not promote or release either source.

## Reproduce

Use KiCad 10.0.6 Python for native export and a Python environment with Shapely 2.x for geometric analysis. These can be separate interpreters. Run commands from the portable packet root. The executable names below are local aliases for those installed interpreters; no private runtime location is required.

Verify the distributed files and stored receipts:

```sh
sha256sum -c MANIFEST.sha256
python -B tools/verify_review.py
```

For source69, place or select the exact matching retained board as source69.kicad_pcb, then run:

```sh
kicad-python tools/export_terminals.py --board source69.kicad_pcb --out replay69/terminals.json
kicad-python tools/export_native_copper.py --board source69.kicad_pcb --out replay69/native.json
python -B tools/verify_review.py --source source69 --board source69.kicad_pcb --geometry replay69/native.json --terminals replay69/terminals.json --out replay69/results
```

Repeat with source62, source62.kicad_pcb and replay62 for the other receipt. The wrapper checks source SHA, exact MPN fields, every native terminal, all contract coverage, preservation of historical endpoint/threshold fields, separate actual/NC counts and exact reproduction of all four report sets.

For an individual cut-check run, the unchanged generic checker also remains directly usable:

```sh
python tools/check_protection_paths.py --geometry replay69/native.json --contracts contracts/added-d7-1.json --out replay69/d7.json
python tools/check_protection_paths.py --geometry replay69/native.json --contracts contracts/actual-io22.json --out replay69/actual-io.json
```

All stored cut-check sets have all_pass=false and their generic checker exits 1. The portable verifier exits 0 when the evidence reproduces consistently, including those expected unfinished results. **A successful verifier exit is not a protection-completion or release approval.**

## Packet validation

The portable verifier was run on both stored receipt sets and replayed both native source snapshots. Every original18, supplemental7, actual-I/O22 and added-D7 result reproduced exactly. The saved replay receipts report source_unchanged=true and protection_complete=false. Distribution contains no absolute workspace paths, private routing-folder names or scratch logs.
