# Native0 routed milestone, work in progress

Selected clean native source: zero opens, geometric DRC errors, DRC warnings, ERC findings and parity findings; all required new physical checks and all 22 actual IO protection checks pass.

Selected PCB SHA-256: 84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd. Open the normal paired project at [../../../hardware/f722-heli.kicad_pro](../../../hardware/f722-heli.kicad_pro). This records the selected fully routed geometric WIP milestone. Cleanup reference applicability is complete with residual RX/MISO limits; fresh DC, electrical acceptance, fabrication and flight qualification remain pending.

All 61 paired files are bound and the 60 non-PCB files match the public native1 source. The selected reports state each native check separately. The preliminary two-warning board is not the selected source.

The cumulative route includes three actual cardinal pose changes at U15, R34 and R35, associated pad transforms, route cuts/additions and the two GREEN remnant removals. The selected structural ledger and cumulative recipe bind each change and all unchanged pad-net assignments. Do not describe all retained objects or all poses as unchanged. Use selected R35 geometry for orientation; the historical native1 270-degree note is inapplicable.

## Fresh engineering review remains pending

Native geometry/connectivity and the stated physical gates do not establish reference equivalence, signal integrity, power capacity, thermal behavior or fabrication readiness. Native1 reference/DC evidence remains historical and is not transferred to this geometry. Current source-bound cleanup reference applicability is included with its residual limitations. Fresh selected-source DC and the final electrical disposition remain pending.

The preserved power model has 294 required accessory/logic/USB cases and 11 separate servo illustrations. The required-case count does not qualify the servo system. Six heavier source1 servo illustrations exceed the preserved 10 A continuous BEC reference, including cases whose ideal-source board-pad voltage screen passes. That voltage result does not model actual BEC current limiting or droop. Native0 DC results are pending; none of those historical numerical results is presented as a native0 result.

Keep the conditional 27 MHz flash prototype/bench envelope and focused settling, GPIO-edge, BARO/IMU noise and ESD/EMC validation limits. The approved 400 kHz I2C setup retains its overshoot/measurement caveat; 385 kHz remains pending and no firmware setting changes.

Both new signal vias must retain their exact selected native tenting/mask and actual pad/paste/metal-clearance evidence. The provisional GREEN via at (37.001558, 23.342039) lies in the flash package region. DRC does not prove that every via lies outside component bodies. JLC filled/capped-process applicability, ordinary-via process/stack, USB slots and StandardPCBA panel acceptance remain unresolved; no process change is adopted here.

## Recovery and evidence

The checkpoint preserves the exact paired source and native/auxiliary exports, compact selected native/physical receipts and the minimum cumulative construction inputs. Saved-byte patch reconstruction from the public native1 PCB was tested and reproduces the selected board exactly. It is independent of native replay. The cumulative transaction data records 19 typed removals, 38 additions and three cardinal pose changes. The original validation ran in two native stages; a full portable rerun of that proof requires broader helper/dependency binding and is not claimed by this compact checkpoint. Any unrun native/reference/numerical replay will be labeled unrun. Required unique replay inputs are retained; intermediate trial boards, meshes, unrelated caches and internal coordination are excluded.

Documentary public normalization must retain original/raw identities and scientific values. The previous checkpoints and B-RID files remain exact. No current fabrication output is implied; final assembly data and factory orientation require regeneration and review from the eventual released project.

The [power scope correction](evidence/power/POWER-SCOPE-CORRECTION.md) binds the intended KST 6.0-8.4 V range, excludes raw 12.6 V servo operation, qualifies the 10 A continuous/30 A peak BEC figures to Hobbywing V4.1, and retains unknown actual mate/harness limits.

The [cleanup reference disposition](evidence/reference/REVIEW.md) preserves the 0.609907 mm RX crossing and 0.003312 mm MISO edge overhang as explicit prototype residuals. The [host manufacturing identity receipt](evidence/manufacturing/README.md) verifies current counts and raw pose expectations while leaving process, CAM and assembly acceptance open.
