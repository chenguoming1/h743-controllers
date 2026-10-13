# Rotated-R35 source3 conditional DC recheck

The fresh run passes all 294 required conditional cases on both 0.12 mm and 0.09 mm grids. All 15 impedance-sensitivity checks and five VCAP resistance margins pass. The complete result remains **overall false**: the 18.560750 A single-feed illustration produces 5.863814, 5.866050, 5.870825 and 5.878586 V at J2–J5, below the 6 V floor. The other ten illustrations have no failed static probes. No acceptance limit was changed.

This result applies to the owner-adopted geometric native3 source only:

- Board SHA256: `c3183f7841bae96a59b29fd13ce9789cf47386a9db452a327ca797187d2ca8a8`
- Native logical SHA256: `a4fddb679e9d73dd2a7b6300fa8888be47e30ab6f139bd5b78ab308d9192563c`
- Model contract SHA256: `285961cbf0d79d0ae28e2e2a84b256380da8c6a922b6977a2495b7554c922a95`

The source still has three ordinary signal opens and two historical RX via warnings. Fresh paired normal/all-track DRC found no geometric errors or ERC/parity errors. Conservative support verified 15 complete modeled networks, 268 pad identities, all 328 physical holes and 44 return-to-saved-plane witnesses. The finite-contact audit passed all 107 contacts. Current GND and VCAP geometry were rebuilt and solved; prior-source numerical results were not transferred.

## CORE bridge and retained paths

The repair replaces a 1.817991 mm, 0.20 mm F.Cu segment with 11.593319 mm of 0.20 mm In3.Cu copper between the existing `fbbf08d3` and `bb91164d` barrels. Cleanup removes the unused original arm and its obsolete barrel. All 47 CORE pads remain connected.

At the worst required loaded-flash case, `corrected_capacity_BEC5.0_1011_flash__analog0m__none`, the existing aggregate model assigns 0.32 A to U3.8→U3.4. This is an adversarial allocation vertex, not nominal flash consumption or an additional load.

| Fine-grid quantity | Current source3 | Identical historical case |
|---|---:|---:|
| U3.8−U3.4 rail | 3.083971 V | 3.092049 V |
| L2.2→U3.8 supply drop | 98.382325 mV | 90.304146 mV |
| U3.4→U9.1 return difference | 2.754282 mV | 2.754447 mV |

The current flash rail is 383.971 mV above its 2.7 V floor. The complete network increases source-to-flash drop by 8.078179 mV in this identical case. At `fbbf08d3`, 0.280631 A arrives through the F-side barrel segments and 0.039369 A through the B-side segments, feeding In3. At `bb91164d`, 0.320000 A flows from In3 toward F. Every adjacent-layer segment of both anchors was checked against the raw field results.

The earlier isolated-strip screen used 105°C, 15 μm copper and 95% IACS: the new strip is 93.5616 mΩ, or 29.9397 mV at 0.32 A. Its 25.2447 mV length-difference estimate was local arithmetic, not a full-network bound. The fresh result accounts for the retained copper, barrel current redistribution and changed return geometry.

The comparison uses the previous diagnostic's actual source hashes, recorded in `CORE-PATH-RESULT.json`. The source4 evidence remains historical; none of its receipts were relabeled as source3.

## Conditional model limits

The seven other downstream pads are C14.1/C15.1 decoupling, R4.1/R6.1 flash bias, R71.1 DSM idle bias and R10.1/R11.1 LED feeds. Their individual physical DC demand locations are not separately enumerated by the existing aggregate allocation model. Zero explicit injection does not imply zero physical current.

The local passive screen, using a 3.6 V bound, −1% resistor tolerance and zero LED forward drop, totals 4.069422 mA. This corresponds to 0.380741 mV across the new strip under the stated material assumptions. These demands remain inside the aggregate budget. This arithmetic does not independently bound retained-path drop, hot resistor tolerance, capacitor leakage or transient behavior.

The corrected terminal model uses L2.2 as the CORE source, U9.6 as sense only, U9.1 as return, and U10/U11 IN6→OUT1 with EN4 as a separate enable condition. The maximum fine-grid VCAP loop is 26.110304 mΩ against 35 mΩ. DC copper checks do not establish AC reference quality, package current sharing, thermal/ampacity, manufacturing or flight qualification.

## Evidence and execution

The recorded full run completed in 1,418.65 seconds. All 94 bound source/code/input checks remained unchanged. Independent review reconciled 610 case records, 6,542 loaded fields, 150 geometry certificates and 36,432 certificate references under a 512 MiB cap.

The preserved complete raw gzip is 31,583,042 bytes, SHA256 `9e89305c6c1c5f7139070a5f7c35f3119931cc0cc8b9c40940f38afea21dab09`. Its exact logical JSON is 318,559,907 bytes, SHA256 `8d59346234f3e50203145156ba289909599735365dbba9d60cca4fa723ae41b1`. `FINAL-HANDOFF.json` and the compact publication evidence index bind the summaries, reviews and receipts. The full raw result and all prior results/caches remain preserved separately.
