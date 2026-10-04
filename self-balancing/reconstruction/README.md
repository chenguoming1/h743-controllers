# P6 complete-path routing packet

Canonical native PCB SHA-256:
`cf16a6f5ceae65aad217e29eef23a60dbc8f15af743b363df03aa5a42c9c71dc`

Immutable bundled P5 source SHA-256:
`6e2031b040ce8f3a534c2f73abb0091e25b3e6adcab982463264ad8898d65cf8`

## Result

- 5,741 → **3,178 tracks**, with geometry improved on 76 of 85 routed nets
- Total routed length reduced by **61.696 mm**
- **406 vias** remain after six explicitly approved redundant holes and their unused branch trees were retired; all **97 GND vias** remain unchanged
- All **151 footprints**, 431 pad geometries, net assignments, user placement semantics, 38 mm outline, mounting holes, and six-layer stack are preserved
- All 27 USB data tracks and their .1392 mm geometry preserved exactly
- The screenshot's STACK_5V_GOOD MCU-to-via run is a coherent, uniform .130 mm logic path
- 64 meaningful .10–.30 mm corner trims replace newly introduced right-angle elbows with 45-degree transitions where clearance, contacts, and reference coverage permit
- Four reviewed HSE approaches, 30 reviewed local GND returns, the J162 redundant power arrow, and the C33 supply junction were handled as explicit local operations

The final review went beyond nominal trace widths and Boolean connectivity. It corrected actual narrow copper necks at noncoincident track ends, shallow functional via attachments, and shallow pad entries. The final board has no unresolved functional attachment bottleneck in the independent native-copper tests. Source current-carrying widths are retained; .130 mm homogenization applies only to eligible low-current signal paths.

## Mandatory acceptance checks

Run the attachment gate before export or acceptance:

    /usr/bin/python3 validate_attachment_quality.py

This gate fails closed on a changed board hash, changed audit implementation, narrow actual copper join, pad passage below .130 mm, shallow via contact, unused single-layer via, exposed antenna tree, failed GND-plane attachment, unreproducible six-via reference fill, or missing/changed exact engineering disposition. It is additional to native DRC, netmap/CPL/pose/stack checks, source-width preservation, physical topology, reference coverage, and complete visual review. Nominal segment width or zero native opens alone cannot approve this design.

Current results on the canonical hash:

- Native all-severity/all-track-error DRC: **0 violations, 0 opens, 0 schematic-parity issues**
- All 85 routed nets: **0 narrow actual-copper track joins**
- All 835 direct pad contacts: .130 mm floor passes; every functional nominal-width entry is qualified
- All 406 remaining vias, including 97 GND vias: **0 new/worsened or inherited shallow attachment groups**
- All remaining vias have real multilayer functions; **zero exposed pad-anchored dead trees** remain
- All **303 GND land/reference-plane attachments** pass the actual-width screen
- Each In1.Cu, In3.Cu and In4.Cu reference plane gains **2.568861 mm²** through the retired antipads; no loss extends beyond the independently checked **2 nm native polygon-rounding envelope**
- Portable replay: every non-zone native record matches, and every filled-zone copper union has exactly zero symmetric difference

Two nominal pad prompts have exact, non-bottleneck dispositions: a redundant U1.20 VDDA graze with a separately proved full .200 mm path, and a J162.1 .450 mm endpoint flare fed by a fully qualified .300 mm conductor. No functional narrow route is waived.

The parent task owns final whole-board numerical closure and all-85-net/159-region visual disposition. Their exact-hash reports accompany the release evidence. Segment counts and turn counts are screening data, not aesthetic acceptance.

## Reference engineering dispositions

`reference-dispositions.json` and `retirement-dispositions.json` bind every declared exception to this PCB hash and the immutable P5 source. Own-via transitions use exact isolated native antipad contours matched for geometry, clearance, netclass, and reference layer; merged multi-net holes are never treated as a blanket allowance.

Removing only the six named vias from bundled P5 and refilling reproduces all three final reference-plane copper unions exactly. This proves the recovered concave fillets around previously merged apertures without using a whole merged hole as an exposure allowance. Raw native subtraction slivers are retained in the evidence; every loss lies within 2 nm of the resulting boundary.

The one DC-supply outer-edge exception is exactly the .450 mm B.Cu segment from (37.5,26.2) to (37.5,26.7). It repairs an inherited .335 mm cap-overlap neck. Its complete centerline remains referenced, .375 mm of width lies over the unchanged plane, and only the outer .075 mm lies beyond the plane's outer boundary. The independently measured added unsupported area is .005331198 mm², with no internal-slot or foreign-antipad exposure. The inward ground rectangle remains continuous; ground-via clearance is .150 mm and board-edge clearance .275 mm. This is not a general reference-gap exemption.

## Portable reconstruction

    /usr/bin/python3 replay.py --out reproduced

The replay needs KiCad's `pcbnew` module and only files in this packet: bundled `input-p5/` PCB/project/rules, `source-delta.json`, and the final `controller.kicad_pcb`. It does not execute historical searches or depend on sibling research paths. `--source` accepts another copy only if its SHA-256 matches the pinned P5.

KiCad may retain or omit redundant collinear vertices when serializing filled polygons. Whole-file replay hashes can therefore differ; exact native non-zone records and every filled-copper union must still match.

- `source-delta.json`: complete P5→P6 UUID delta and the sole board metadata change, P5→P6 revision label
- `reference-dispositions.json`: exact transition/outer-edge engineering scope and all30 adopted local GND return operations, including the two final U1.49/Q2.2 shoulders
- `retirement-dispositions.json`: the exact six retired vias, real planar joins, unused trees and antipad-closure scope
- `attachment-dispositions.json`: exact two non-bottleneck pad advisories and audit implementation hashes
- `attachment-validation/attachment-quality-gate.json`: mandatory actual-copper acceptance result, including the exact six-via refill oracle
- `validation/`: standalone native-geometry audit implementations
- `evidence/`: ordered accepted operation ledgers and independent local proofs
- `reproduced/replay-result.json`: portable reconstruction proof
- `by-net-changes.csv`: all changed-net counts and lengths
- `drc-all.json`: native DRC result for these bytes

The 338 retained-path records in `evidence/remaining-path-blockers.json` contain exact current obstacles and reference limitations for bounded simpler alternatives. The UART2 paired-shoulder probe tests both lanes together and is carried to this exact source by `evidence/final-coupled-uart2-equivalence.json`; these records do not claim global routing optimality.

The last approved R140 rear UART3_TX shoulder changed exactly five .130 mm tracks into three, preserving terminal approaches and reducing path length by .029289 mm. Every filled-zone copper union remains identical to the preceding qualified source.

Historical and intermediate candidates outside this folder are not canonical release inputs. Hardware qualification and supplier/process acceptance remain separate from this CAD result.
