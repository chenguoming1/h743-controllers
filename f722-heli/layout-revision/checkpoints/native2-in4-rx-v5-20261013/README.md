# F722 native2 In4 RX v5: prototype routing checkpoint

**Two connections remain: FLASH_MOSI and PORT_C_RX_EXT. This is an adopted prototype routing baseline, not a complete functional board or manufacturing release.**

Open [hardware/f722-heli.kicad_pro](hardware/f722-heli.kicad_pro). The normal project at [../../../hardware/f722-heli.kicad_pro](../../../hardware/f722-heli.kicad_pro) has the same 61 paired files. The exact current PCB SHA-256 is `7d9af57e9b22064fc6b2fd9cde4f2f5b72dc252cdbb1b104e706472bfdbbcdcb`.

## What changed

Ten 0.127 mm tracks on In4.Cu, totaling 21.453741692 mm, connect the held PORT_C_RX_MCU approach between U1.28 and R34.2. No via, cut, footprint move, pad mapping or source primitive changed. All 60 other paired hardware files remain byte-identical to the public native3 R35-cleanup predecessor. [PAIRED-HARDWARE.json](PAIRED-HARDWARE.json) binds every file, source commit, mode, byte count, SHA-256 and Git blob identity.

The recorded KiCad 10.0.6 native import/refill/reopen checks have zero geometric DRC errors, zero warnings, zero ERC findings and zero schematic-parity findings. The two unconnected items remain explicit DRC errors in the unrouted category. All 156 footprint poses, 558 pad assignments and 2,470 original objects are retained. All 19 candidate physical gates pass; the current full RX protection obligation remains incomplete while PORT_C_RX_EXT is open.

## Current conditional DC result

Fresh source-bound results cover this exact PCB and native copper. All 294 required cases pass on each of the 0.12 mm and 0.09 mm grids; all 15 grid sensitivity comparisons and five VCAP copper-loop limits pass. The complete run contains 305 cases per grid, including 11 illustrative cases. The current independent [DC and reference disposition](evidence/dc/INDEPENDENT-DC-AND-REFERENCE-DISPOSITION.json) retains the full numerical checks and remaining limitations.

**The overall static screen is false.** The retained approximately 18.56 A lost-J6-feed illustration gives J2–J5 fine-grid board-pad voltages of 5.8637795, 5.8660192, 5.8707973 and 5.8785627 V against 6.0 V floors. This operating illustration is unsupported. These are modeled board-pad voltages, not measurements at servo terminals. Results depend on the enumerated source, load, copper, temperature and finite-contact assumptions; they do not establish ampacity, thermal limits or an allowable flight envelope.

## Finite return geometry and bench limits

The In1 own-drilled plane remains exact; In4 loses 7.760499768 mm² around the added RX route. The 93 routed non-GND nets and 1,610 retained track projections were reviewed. FLASH_SCK's 28 track projections remain unchanged, and RX_EXT and FLASH_WP_N gain no reference loss.

- TP2 has 0.099780947 mm actual full-pad margin against a 0.0994 mm dielectric scale.
- The FLASH_CS bypass is continuous, with a checked upper exit width of 0.13058888 mm. It is not a uniform 0.150 mm neck guarantee.
- The two explicitly scoped C3 feed margins are 0.027806420 and 0.027810477 mm; the direct capacitor-to-MCU supply and ground paths remain exact and fully supported.
- The U15–J11 inward return approach remains 0.254 mm wide between real annular contacts over 2.478705783 mm. Its small outward collar is recorded separately and does not prove ESD immunity.

The retained B_RX, B_TX, C_TX, SBUS_HV and LED crossings require the stated practical waveform and return-path checks. Baud rate is not an edge-rate bound. The 22 ohm R34 does not establish the external driver's source impedance or edge rate, and no explicit shunt filter is assumed. Probe actual receiver waveforms with conservative fast edges and simultaneous neighboring switching. DC does not certify connector ESD/EMC, overshoot, crosstalk, AC regulator stability, assembly tolerance, first-article behavior or flight performance. Later MOSI/RX_EXT routing needs its own exact-source native, reference and power applicability review.

The approved 400 kHz I2C choice retains its overshoot caveat. Device timing, sink-current bounds and real waveforms still need validation. A possible 385 kHz change remains pending; this checkpoint changes no firmware setting.

## Reproduction and evidence provenance

Use [recipe/README.md](recipe/README.md) for read-only integrity verification, exact saved-board reconstruction and separate KiCad replay. The source is the public [native3 R35-cleanup checkpoint](../native3-r35-cleanup-v1-20261012/README.md), pinned at commit `0f81207c2d6783bf60071767cacd9530051545a0`. The new route primitives are fully specified in [recipe/route-delta.json](recipe/route-delta.json).

Hardware and the two current native gzip exports are byte-exact. Public evidence JSON explicitly wraps each original artifact's hash and byte count with its normalized technical content and a transformation ledger. Local locators and execution coordination metadata are removed; numerical results and engineering claims are retained. [NORMALIZATION.json](NORMALIZATION.json) binds those views. Recorded preliminary artifacts keep their original pending/not-adopted statements; [CURRENT-STATE.json](CURRENT-STATE.json) records the later combined result and adopted prototype status. Portable replay adaptations are identified separately and are not represented as the original launch scripts.

The [four lossless DC chunks](dc/README.md) retain the complete current compressed numerical result and its exact decompressed identity. The portable numerical and reference replay source packages are pending a separate immutable supplement. This checkpoint supplies complete saved-design recovery, the ten-track native construction recipe and current recorded evidence; it does not claim that public numerical or reference solver source closure is complete. Generated meshes, caches, previous trial outputs and duplicate historical exports are omitted. Packaging does not rerun the native, geometry or numerical workloads.

Old `manufacturing/`, `validation/`, images and final95 reports do not describe this two-open PCB. Do not use their BOM/CPL/Gerber/stencil outputs to manufacture this revision. Earlier checkpoints and all B-RID files remain unchanged.
