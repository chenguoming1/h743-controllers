# WIP: native3 conditional DC and bounded assembly evidence

This is an additions-only evidence successor to `../native3-r35-cleanup-v1-20261012/`. It preserves the adopted three-open board without editing hardware. It is not a fabrication release, standalone solver environment or final qualification.

## Current result

All 294 required conditional DC cases pass on both 0.12 mm and 0.09 mm grids; all 15 impedance-sensitivity checks and five VCAP margins pass. **Overall conditional static screen remains false.** The retained 18.560750 A single-feed illustration gives J2–J5 5.863814, 5.866050, 5.870825 and 5.878586 V, below the unchanged 6 V floor. No servo fault-case acceptance is inferred.

The worst required loaded-flash rail is 3.083971 V against 2.7 V. Its source-to-flash drop increases by 8.078179 mV versus the identical historical case. The 0.32 A flash allocation is an adversarial aggregate-model vertex, not nominal device consumption or additional load. Current GND and VCAP geometry were rebuilt and solved, with 15 modeled networks, 268 pad identities, 328 physical holes, 44 saved-plane return witnesses and 107 finite contacts checked. Independent review reconciled 610 grid/case records, 6,542 loaded fields, 150 geometry certificates and 36,432 references. Packaging does not rerun those computations.

The exact board SHA-256 is `c3183f7841bae96a59b29fd13ce9789cf47386a9db452a327ca797187d2ca8a8`; native logical SHA-256 is `a4fddb679e9d73dd2a7b6300fa8888be47e30ab6f139bd5b78ab308d9192563c`. Full original-to-public identities appear in `SOURCE-PROVENANCE.json`. Embedded hashes in normalized receipts refer to original bytes; `CONTENT-MANIFEST.json` binds public bytes.

## Assumptions and limits

- Static conditional copper model: 105°C, 15 μm copper and barrel plating, 95% IACS; source stackup layer centers; saved fills and all physical holes; finite contact windows; idealized within-layer lands/annuli. These are computational assumptions, not manufactured thickness, temperature, ampacity, package current-sharing or solder-contact guarantees.
- CORE source L2.2, sense-only U9.6, return U9.1; U10/U11 IN6→OUT1 with EN4 separate. Worst fine VCAP loop is 26.110304 mΩ against 35 mΩ.
- Seven other downstream pads (C14.1/C15.1, R4.1/R6.1, R71.1, R10.1/R11.1) are not separately enumerated physical injection locations. The 3.6 V, −1% resistor, zero LED-drop local passive screen totals 4.069422 mA and 0.380741 mV across the new strip inside the aggregate budget. It does not bound retained-path drop, hot tolerance, capacitor leakage, transients or AC behavior. Zero explicit injection does not mean zero physical current.
- The 11.593319 mm by 0.20 mm In3 strip's isolated 93.5616 mΩ / 29.9397 mV arithmetic and 25.2447 mV length-difference estimate are not full-network bounds. Retained copper and barrel redistribution matter; historical source4 receipts remain historical.
- FLASH_MOSI, PORT_C_RX_EXT and PORT_C_RX_MCU remain open. The two historical RX via warnings, incomplete RX protection, signal reference/timing/SI/ESD and stock I2C timing/sink-guarantee gap remain. No AC, thermal/ampacity, servo, manufacturing or flight qualification is established.

## Bounded assembly findings

No demonstrated land/paste collision or process interference requires a PCB move or change from ordinary 0.45/0.20 mm both-sides-tented vias. The SERVO2 via beneath U1 is nominally 0.762 mm from the nearest back land/mask/paste and 0.388 mm from the nearest front land/mask/paste. U1 has perimeter lands and no central solder land. Package A1 is measured from the lead seating plane, not a guaranteed assembled PCB gap; tenting does not establish filling, capping or flatness.

Only R35 footprint/two pad records changed from the reviewed predecessor; pad identity/net swap preserves the physical land/mask/paste union. Other reviewed U1/U15/J11/U3/Q1 footprints and the RED via carry over exactly. The current raw bottom CPL expectation is R35 X 29.2, Y −23.0, −90°; U15 X 27.721926, Y −21.185113, 0°; U1 X 20.959999, Y −13.8, 0°. Regenerate from the eventual final board and inspect the factory's actual part models, pin 1 and polarity. Do not reuse R35's old +90° row or mirror bottom X again. Counts are 144 SMT, 65 front / 79 back, with J2–J8 manual THT and TP1–TP5 bare pads excluded.

The included assembly predecessor is historical and only its explicitly verified unchanged geometry carries forward. Its four-open count is not current. The native3 assembly report predates DC completion, so its stale-power sentence is historical; reference/AC limitations remain. Earlier DC preparation/compile receipts retain historical pending/no-solve wording; `dc/FINAL-HANDOFF.json` and `CURRENT-STATE.json` record completion. Final Gerber/stencil CAM, factory placement preview, seating/tolerance review and first-article inspection remain required.

## Evidence scope

`dc/TECHNICAL-REPORT.md`, the independent result/storage reviews and current assembly evidence contain the detailed findings and official-source references. Full raw/reduced results and caches are not copied. `RAW-RESULT-REFERENCE.json` records the original stored/logical identities. This packet does not provide a standalone reproduction environment. The local publication envelope must still bind the actual verified native3 base commit before remote ancestry or publication is claimed.
