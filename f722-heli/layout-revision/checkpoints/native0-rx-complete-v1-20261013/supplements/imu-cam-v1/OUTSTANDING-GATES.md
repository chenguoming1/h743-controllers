# Remaining decisions and acceptance gates

Applies to native0 PCB `84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd`. The paired design is fully routed, with zero recorded native opens/DRC warnings/errors/ERC/parity. The fresh conditional DC screen, nominal moved-part geometry and static firmware/IMU mappings are recorded separately. Internal CAM output is a review artifact, not manufacturing or flight release.

## System decisions

- Identify the intended ESC/BEC SKU, battery cell count and servo set. The 200 A V4.1 page contains both SBEC and OPTO variants; the 120 A V4 is a different 3–6S unit. An external BEC needs its own exact model and operating limits. Confirm mating contacts, wire/harness construction and expected current/duty profile. Two feeds from one BEC do not double its capacity.
- Keep the intended KST servo rail within 6.0–8.4 V; raw 12.6 V servo operation is excluded. All 11 numerical servo examples are illustrative, and six exceed the version-qualified 10 A continuous reference. The 294 required DC cases cover accessory/logic/USB only.
- Confirm installation orientation and selected port/protocol functions. The static IMU result uses F.Cu up and the A/B edge (PCB −Y) forward. Ordinary DSM receive/bind is supported by the pinned source path; TX1/PA9-dependent configurations are not established by this design.
- The requested 400 kHz I2C setup with internal pull-ups off is approved in documentation but has not been applied. The requested 400 kHz setting can produce an actual bus clock above 400 kHz under the reviewed timing assumptions. The 385 kHz refinement is unapproved and unapplied; no hardware or firmware setting was changed by these checks.

## Factory acceptance

- Confirm the exact six-layer production stack and finished thickness, ordinary 0.45/0.20 mm through-via capability, both-side tenting, and applicability of the current filled/capped quote option. No process substitution is adopted. RX/GREEN lie beneath actual component-body projections; nominal land/mask/paste gaps pass, while manufactured tent topography and component seating require acceptance.
- Confirm J1's 1.01 × 0.71 mm NPTH oval and 1.10 × 0.60 mm plated shell slots, removable panel/rails and final drill/CAM interpretation.
- Confirm double-sided/0201 assembly handling, stencil/reflow, actual supplier pin-1/pickup/orientation, J1 secondary shell soldering and inspection criteria. Use the current U15/R34/R35 poses; no bottom-X remirroring or guessed angle correction.
- Confirm the chosen soldermask/copper process accepts the measured 0.100 mm U15 web to distinct openings. The reviewed JLC table's 0.10 mm allowance is specific to the listed 1 oz mask colors; its 0.13 mm black/white and 0.20 mm 2 oz values are not covered by that nominal web. U15's common GND mask and two separate paste apertures remain the actual reviewed geometry.
- Review the internal CAM/precision-patch disposition and its original failure evidence before accepting files for manufacture. A successful bounded comparison does not create missing final scope receipts or factory approval.

## Physical prototype checks

- Bind the installed binary and saved settings to their actual hashes, target/resources, clocks and selected functions. Verify cold boot/reset, BOOT0 ROM entry, USB DFU/enumeration, oscillator startup and supply sequencing.
- Verify real IMU component/board orientation and calibrated pitch, roll and yaw against the configurator model, using the documented mounting reference, before powered motor tests. Static CW90 and yaw=900 alternatives do not prove live settings or calibration.
- Verify full-rate flash operation and waveforms in the reviewed nominal 27 MHz envelope; check UART/protection paths, BARO/IMU noise and the recorded RX/MISO reference concerns. Confirm I2C physical frequency, edge times and separate MCU/sensor VOL under actual loading. ESD/EMC and fast-edge behavior remain unqualified.
- Measure BEC regulation/current limiting and actual harness/contact voltage drop and temperature for the intended continuous and transient loads, including servo startup/reversal/stall. Verify servo-terminal voltage and failsafe behavior. Copper-only VCAP resistance and enumerated fixed-temperature DC do not establish regulator stability, thermal/ampacity, dynamic protection or flight acceptance.

Any copper or component/process change needs fresh applicability review of the affected source-bound evidence. No manufacture, ordering or flight release is established by this checklist.
