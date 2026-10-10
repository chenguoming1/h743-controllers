# Joint native checkpoint: seven connections remain

This is the checked, paired KiCad candidate02 from accepted checkpoint11. It is an isolated, conditional routing WIP. Open `hardware/f722-heli.kicad_pro` in KiCad 10.0.6; the complete 61-file hardware folder includes the PCB, all 60 project inputs, local symbol and footprint libraries, and `parts.json`.

The accepted project at `../../hardware` remains checkpoint11. This checkpoint does not select or adopt candidate02 as canonical hardware. It is not fabrication, assembly, electrical, or flight qualification.

## Changes and checks

The exact transaction removes 146 source copper objects and adds 201 native segments plus 32 tented .45/.20 mm through-vias. It moves U15, C31, R42, R43 and R44, preserving every footprint and all 558 pad UUIDs. All declared changed native pad records, full footprint structure, retained source objects, and logical mapping were checked exactly. Part values, MPNs, footprint packages, bonded MCU/header connections, and design clearances are preserved.

Only U15 routing lands NC9 and NC10 gain net assignments, respectively PORT_C_TX_EXT and PORT_C_RX_EXT. The paired io-ports schematic uses a separately named symbol variant whose only pin-type changes make NC9/NC10 passive. Manufacturer NC names, pin UUIDs, bonded IO1 RX/IO2 TX, existing bonded wiring, and original library symbols are retained. Two wires and labels replace only the two NC marks.

Fresh native checks report zero geometric DRC errors, zero ERC violations and zero schematic-parity items, with exact 156-component / 506-node / 127-net parity. Seven missing connections and seven dangling-copper warnings remain. The open ledger is PORT_C_RX_EXT (three groups, two missing connections), PORT_C_RX_MCU, PORT_C_TX_MCU, FLASH_MISO, FLASH_MOSI and FLASH_SCK. All 16 original critical and 28 support nets are connected; mechanics, process and 29 firmware checks passed. Bonded protection checks pass 17/18 candidate and 21/22 actual-I/O cases; the unfinished C_RX case remains failed. These cut counts do not establish a complete functional UART path to the MCU.

## Scope and remaining work

The current scoped disposition is `evidence/geometric-review/owner-WIP-disposition.json`. The reviewed new/affected finite contacts have direct or named supplemental witnesses. The raw finite checker retains its false/unsupported predicates: two intentional C_RX open ends, the nonconvex U15.3 convex-entry limitation, and the two J11 full-track-width annular failures. The supplements preserve actual polygons and show finite contact; they do not claim .4/.8 mm through-annulus width or current capacity.

The 43-net reference review preserves raw centerline/width results. CORE and SBUS centerline features are inherited from checkpoint11; changed IMU projections, the SBUS width-only delta, and the new LED_RED detour/edge-window geometry remain conditional. Five changed ground recipes have scoped local and both-plane corridor witnesses. This is not coverage of every retained contact or global plane impedance: the inherited U2.9 ground leaf has a rounded-end-only pad entry and remains unchanged in this checkpoint. A separate unrun routing trial does not validate this board.

Seven ordinary opens, seven warnings, raw reference predicates, retained-return/tree questions, LED return/edge-antipad attribution and the inherited .20 mm drill vendor-guidance departure remain explicit. Historical numerical power/VCAP results are stale for this geometry. Current capacity, installed ADC acquisition/settling/noise, AC/ESD/transients, assembly and flight remain unqualified. Earlier stage receipts retain their original pending flags; this README and the final scoped disposition identify the latest review state. The historical review summary predates the narrow source11 reference comparison.

## Recovery and evidence

`MANIFEST.json` lists every payload file with byte count, SHA-256 and Git blob identity. `repro/DEPENDENCIES.json` pins the PR18-equivalent base tree, all required source inputs and official KiCad runtime. The 8,946,350-byte flattened transaction is included once as a 610,940-byte lossless gzip; `repro/restore.py` verifies its exact restoration. The source and candidate native JSON exports are reproducible and omitted to avoid duplicate geometry. See `RESTORE.md` for verification and reconstruction instructions.

Source PCB SHA-256: `454b7bb2454695b49c039f3d97e5edefb1946912363bab00ef5ced6ba2b0ea16`.
Candidate PCB SHA-256: `a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f`.
Transaction SHA-256: `b7ca08e59b4316c8a88c0ff9d3c0fe3cffac4d0f0ad2b407028cd1ef3050f497`.
