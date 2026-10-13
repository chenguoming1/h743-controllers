# Native1 MOSI/BARO prototype baseline, work in progress

This adopted prototype routing baseline closes FLASH_MOSI. **One connection remains: PORT_C_RX_EXT from J11.1 to R34.1. It is not fabrication-ready or flight-qualified.** Open the normal paired project at [../../../hardware/f722-heli.kicad_pro](../../../hardware/f722-heli.kicad_pro). Exact PCB SHA-256: `b31e6b9ca47e8e5a0b8967ec25f8390a66541b0c374ebedde77a39380e7d73ca`.

All 61 paired design files are bound in [PAIRED-HARDWARE.json](PAIRED-HARDWARE.json); only the PCB differs from native2. The edit adds 25 tracks and two through vias, removes one PORT_B_RX_MCU track for its repair, and moves no component or pad assignment. All 2,479 retained objects and the full native2 RX route remain exact. Recorded geometric DRC, warnings, ERC and schematic-parity findings are zero, with the declared unrouted item retained.

The raw inherited contact-applicability predicate and aggregate physical flag remain false. A fresh, narrow VX window disposition passes because actual VX copper, contacts and finite-width witnesses remain exact. It does not relax the general predicate. The [final disposition](evidence/ENGINEERING-BASELINE-DISPOSITION.json) binds this scoped evidence and the fresh DC result. Preliminary receipts retain their original issue-time status; [CURRENT-STATE.json](CURRENT-STATE.json) is the current adopted status.

## Current conditional DC

All **294 required cases on both 0.12 mm and 0.09 mm grids**, 15 numerical comparisons and five VCAP copper-loop checks pass. The overall static result stays false: the approximately **18.56 A lost-J6-feed illustration** produces J2-J5 fine-grid board-pad voltages 5.863718452, 5.865964789, 5.870752195 and 5.878528194 V, below 6 V. Servo harness/contact drop is unmeasured, so these board-pad windows do not establish servo terminal voltage. Exit code 1 and all failed flags remain in the [complete recorded result](dc/README.md).

The unchanged model covers 15 networks, 107 finite contacts and all 330 drilled objects. Across 9,500 matching source2/current probe rows, the largest fine-grid absolute voltage change is +0.435326 mV; the maximum VCAP loop increase is 0.106358 milliohm. These are conditional static calculations, not dynamic equivalence or ampacity guarantees. See the [technical report](evidence/dc/TECHNICAL-REPORT.md) and [independent disposition](evidence/dc/INDEPENDENT-DC-AND-REFERENCE-DISPOSITION.json).

## Reference, timing and unresolved limits

The complete 1,644-track inventory retains all 64 affected projections and unchanged FLASH_SCK/MISO reference loss. Actual SPI and BARO finite planar return itineraries are approximately 9.887 mm and 10.103 mm, with layer-transition surface distances reported separately. These finite metal witnesses do not establish nearest-reference equivalence, loop inductance, fast-edge settling or ESD behavior.

Timing supports a conditional **27 MHz prototype/bench envelope** with focused flash waveform/function, BARO and IMU noise tests. A proposed 2 ns extra settling/jitter test budget leaves approximately 2.719 ns modeled MISO setup margin; that budget is neither measured nor a datasheet requirement. 30 MHz is an out-of-datasheet stress case. Stock source blobs are pinned, but the installed binary and live registers are unverified. Actual GPIO edges, loading, settling, UART/SBUS protection and EMC/ESD remain bench work.

The approved 400 kHz I2C setup retains its overshoot and measurement caveat; 385 kHz remains pending. No firmware setting changes here. Ordinary-via process/stack, USB slots and StandardPCBA panel acceptance remain unresolved with JLCPCB. Thermal/AC, assembly/first-article, manufacturing and flight qualification are open. Later copper or pose edits need their own source-bound review. No later RX experimental work is included.

## Recovery and replay

[Saved-board reconstruction](recipe/README.md) was tested and reproduces the exact PCB bytes. The distinct KiCad construction recipe is present and syntax-checked, but was not executed during packaging. Four lossless raw DC chunks are verified through their full decompressed identity.

[Portable numerical source](dc/REPLAY.md) is included with explicit path normalization. Source/hash checks and model regeneration verified 305 cases, 107 contacts, 15 networks and five loops; portable native/geometry/mesh/finite-port/solver replay remains unrun. [Native1 reference measurement sources and inputs](reference-source/README.md) are preserved, including the required exact source projection cache. Their archival launcher still requires explicit path rebinding and runtime setup; heavy geometry replay is unrun, so fully portable reference replay is not claimed. Full-track inventory, finite-path results, timing evidence and stock source are retained. Prior native2 reference/source packages remain historical.

Hardware, native exports and raw result bytes are exact. Documentary normalization records the original identities and each change; raw originals remain preserved. [NORMALIZATION.json](NORMALIZATION.json) and the numerical package's normalization ledger make those changes explicit. No heavy workload was repeated for publication preparation.
