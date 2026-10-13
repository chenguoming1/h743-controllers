# Current native1 DC evidence

Four ordered chunks in raw/ retain the complete original compressed result without any byte change. RAW-RESULT-CHUNKS.json binds each chunk, order, full gzip and decompressed JSON. No mesh or cache is needed to inspect this recorded result.

Run `python3 verify_dc_chunks.py` to verify all stored and decompressed identities without writing a result file. To restore the original gzip, run `python3 verify_dc_chunks.py --output /your/new/result.json.gz`. An existing output path is refused. This verifies recorded bytes; it does not run a numerical solver.

The current exact native1 PCB has all 294 required cases passing on both 0.12 mm and 0.09 mm grids. Fifteen numerical comparisons and five VCAP copper-loop checks pass. The raw overall static screen remains false: the approximately 18.56 A lost-J6-feed illustration has J2-J5 board-pad voltages 5.863718452, 5.865964789, 5.870752195 and 5.878528194 V, below the 6 V floors. The model does not establish voltage at the servo after unmeasured output harness/contact drop. Exit code 1 and the illustrative failure remain in the evidence.

The identical-case source2 comparison checks 9,500 probe rows. The largest fine-grid absolute voltage change is +0.435326 mV and the largest VCAP copper-loop increase is 0.106358 milliohm. This does not assert dynamic equivalence or final source acceptance.

Compact normalized receipts are in ../evidence/dc/. Their ledgers identify removed local locators and execution metadata, with raw local originals unchanged. Scientific values and issue-time false acceptance/release claims are retained. The model is conditional static DC; thermal/AC, edge settling, EMC/ESD, manufacturing and flight qualification are outside its scope.

The final combined disposition adopts this exact PCB as a prototype routing baseline. Portable numerical source and its tested source-only model verification are documented in REPLAY.md. Heavy portable native/geometry/mesh/finite-port/solver replay remains unrun. Native1 reference sources and inputs are preserved with explicit launcher-rebinding/runtime requirements; packaging has not rerun a numerical or geometry calculation.
