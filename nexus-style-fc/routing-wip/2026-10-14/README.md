# Connected local-clearance experiment: unfinished

`attempt-08.kicad_pcb` is a review-only experimental board, separate from canonical hardware. Native KiCad 10 reports **361 clearance errors, 0 opens and 0 schematic-parity issues**. It is not compliant and must not feed manufacturing exports.

The original connected board was used, all 937 subminimum segments were widened to at least 0.127 mm, and 66 bounded local patches adjusted route coordinates by at most 0.07977 mm. Each patch protected pad landings, existing copper contacts including off-center via contacts, original locks and wide power segments. Native refill/DRC is authoritative: the widened seed had 458 clearance errors; this candidate has 361, with no new dangling-copper warnings and the same 54 historical silkscreen warnings. All 361 remaining errors are visible in `attempt-08-drc.json`.

Source invariants pass for all 88 footprint definitions, pad/net assignments, placements, outline, physical stack, setup and zone/keepout definitions. All 1,450 segments meet the 0.127 mm minimum, and all 225 vias retain 0.45/0.20 mm geometry. Aggregate original power-net width floors pass. Those checks do not qualify branch ampacity, USB impedance, finite return paths, thermal behavior or flight operation.

The original 18 vias drilling pasted SMT lands remain at their original locations, producing 19 contact pairs. No new drill/paste contact was introduced. Ordinary tenting is not evidence of a filled/capped assembly process; removal or an approved manufacturing disposition remains necessary.

## Evidence and reproduction

- `attempt-08-manifest.json` binds candidate/report hashes, canonical companion hashes, native invocation and failure counts.
- `attempt-08-drc.json` is native KiCad 10.0.7 DRC after refill/save, all track errors, full severity and schematic parity.
- `attempt-08-validation.json` checks the exact source-bound invariants and geometry. Overall status is **fail** due to clearance errors.

To recheck, use an isolated copy of the complete Nexus project and its libraries. In that copy only, replace `hardware/nexus-style-fc.kicad_pcb` with this candidate. Keep the main project/rule/schematic files matching the manifest hashes, then run the recorded KiCad 10 command. Do not replace the canonical PCB or export CAM from this experiment.

A separate six-layer global reroute reached zero geometry errors but still had 62 opens and 51 dangling items after safe source-power restoration. That disconnected candidate is not the connected local-repair candidate published here. Neither result is full compliance.

Canonical main/header PCBs remain unchanged from source. The 11 fixed header-contact edge violations, tab/slot interference, USB/reference-path review, power qualification and manufacturing release remain open. Historical CAM/BOM outputs are on hold.
