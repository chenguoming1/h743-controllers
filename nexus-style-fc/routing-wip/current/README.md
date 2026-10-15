# Current experimental Nexus project

Open [nexus-style-fc.kicad_pro](hardware/nexus-style-fc.kicad_pro), [PCB](hardware/nexus-style-fc.kicad_pcb), or [schematic](hardware/nexus-style-fc.kicad_sch). This stable folder will hold the latest source-bound candidate; historical snapshots remain dated separately.

Current candidate: **r61, two clearance errors**, zero opens and electrical/footprint-filter parity issues. Exact unchanged schematic/ERC binding passes. All-visible diagnostics retain 13 centering, five footprint-type and 54 silk warnings. PCB SHA256 `5a51610cc1569958442f97407e11533b646b1e0d8997d86356b8968dce50487e`.

[Exact native receipts, changes and open gates](../2026-10-15/r61-interface-checkpoint/README.md). USB impedance/electrical qualification, effective input capacitance, mechanical integration, via-in-paste process and power/current/thermal/assembly qualification remain open. The approved two-capacitor/D5 remedy is not yet in this freeze. Do not fabricate, assemble or fly.

The root `nexus-style-fc/hardware/` is the older canonical reference, not this improved route. Its PCB/schematic remain mutually consistent. This experimental current folder likewise contains its own matching PCB, schematic, project, rules and local libraries. The separate unfinished mechanical experiment is not selected here.
