# Clean native0 conditional DC / VCAP result

The exact clean native0 source passes **all 294 required accessory, logic and USB cases on both grids**, all **15 network convergence comparisons**, and all **five VCAP loop checks**. The raw aggregate remains **false**, with exit code **1**, because one of the 11 separately labeled servo illustrations fails four board-pad voltage floors. All six heavier servo illustrations exceed the version-qualified 10 A continuous BEC specification even where board-pad voltage passes.

## Current source and result

PCB SHA256: `84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd`. Native logical SHA256: `04d8ecd80edf004f3226f204f23adba51692a498ae38edc183debeffb704603d`. Unchanged model contract: `285961cbf0d79d0ae28e2e2a84b256380da8c6a922b6977a2495b7554c922a95`.

The fresh extraction and solve bind 15 networks, 107 finite contacts, 268 physical power pads, 44 saved-plane return witnesses, and all **331 actual drilled objects**. All-net drilled voids remove copper on their actual spanned layers. Both current DRC modes have zero opens, errors, warnings and parity discrepancies. The separate native diagnostic has zero ERC errors and all 22 physical gates pass. Both moved U15 GND pads and their new branch have fresh static support; U15 is not an injected-load or transient-ESD test.

The 0.12 mm and 0.09 mm grids contain 305 cases each, totaling 610 complete rows. Copper and plating remain 0.015 mm, 95% IACS at 105 °C; finite-contact, component, case, floor and numerical definitions are unchanged. USB and DSM devices use actual supply IN pin 6 and downstream output floors; EN pin 4 remains a distinct probe.

The worst fine-grid VCAP loop is **26.324493 mΩ**, below 35 mΩ. The smallest required voltage margin is **19.068952 mV**, at the classic DSM pad, against a 1 mV numerical guard. Worst loaded flash voltage is **3.083714276 V**, above 2.7 V. These are fixed-temperature DC results, including the stated unit-leg VCAP sums.

## Actual required-case envelope

- **126 classic BEC cases:** ideal 5.0 V at J6 board pads; exactly 1 A on each of two selected ports among J9/J10/J11; 0.32 A aggregate electronics plus 0.02 A classic DSM.
- **126 capacity BEC cases:** the same ideal 5.0 V and two 1 A accessory loads; 0.32 A electronics plus 0.50 A DSM capacity loading. The capacity cases do not inherit a classic-DSM remote-voltage guarantee.
- **42 USB configuration cases:** ideal 4.33 V at the common USB input contacts; 0.30 A electronics; accessory, DSM and servo loads disconnected.

For each configuration, 42 prescribed allocation vertices move the fixed electronics budget among actual MCU, flash, barometer, analog and IMU terminals. These are enumerated load cases; they do not establish arbitrary continuous ranges or all nonlinear interior extrema. **None of the 294 required cases loads the servo outputs.** Required BEC cases use one ideal J6 board-pad feed and exclude its upstream harness loss. Dual-feed and feed-loss scenarios appear only among the servo illustrations below. This run does not numerically sweep the full stated 5–12.6 V electronics-input capability.

The receiver board-pad floor is 4.8 V: the 4.5 V remote requirement plus a conditional 1 A allowance for 0.200 Ω contacts and at most 0.100 Ω measured cable. Classic DSM uses the preserved 3.1394 V floor and 3.465 V ceiling with its stated contact/cable allowance. These assumptions do not measure an installed harness. Actual local supply-minus-return probes, component operating windows and all case-specific limits remain in REQUIRED-CASE-ENVELOPE.json.

U6 and U9 use the preserved 85% total-efficiency model, with their stated initial low-regulation values. Effective switch resistances and their datasheet test-condition extrapolations are retained: U5 45 mΩ, U7 33 mΩ, U8 90 mΩ and U10/U11 150 mΩ. Detailed conditions and auxiliary currents are recorded verbatim in the case envelope. Ideal source regulation and these engineering component assumptions remain conditional inputs.

## All 11 servo illustrations

Every illustration uses one common ideal **7.4 V BEC**, 1 A each on J10/J11, 0.32 A electronics, and classic 0.02 A or capacity 0.50 A DSM. Two leads from one BEC are not independent supplies. Servo current assignments are engineering comparisons derived from approximate manufacturer plotted load points; they are not guaranteed continuous or stall-current ratings. No duration is assigned. The moderate 1/1/1/0.5 A assignment has no demonstrated motion, torque, duty-cycle or temperature envelope.

| Case (same_BEC prefix and sample suffix omitted) | J2/J3/J4/J5 A | Source A, fine grid | Servo board-pad V span | Both-grid voltage check | Above 10 A |
|---|---|---:|---:|---|---|
| moderate_equal20m_classic | 1.0/1.0/1.0/0.5 | 5.350168 | 7.284456–7.288109 | Pass | No |
| moderate_paired_J8_weak_classic | 1.0/1.0/1.0/0.5 | 5.367422 | 7.220528–7.224261 | Pass | No |
| moderate_crossed_J6_positive_strong_classic | 1.0/1.0/1.0/0.5 | 5.367649 | 7.219399–7.223007 | Pass | No |
| moderate_J6_feed_lost_classic | 1.0/1.0/1.0/0.5 | 5.443639 | 6.950911–6.954450 | Pass | No |
| moderate_J8_feed_lost_classic | 1.0/1.0/1.0/0.5 | 5.442150 | 6.956565–6.960365 | Pass | No |
| heavy_S1_905X_equal40m_capacity | 4.5/1.0/1.0/2.4 | 11.123666 | 6.934168–6.943851 | Pass | Yes |
| heavy_S2_905X_paired_J8_weak_capacity | 1.0/4.5/1.0/2.4 | 11.092811 | 7.028432–7.035777 | Pass | Yes |
| heavy_S3_905X_crossed_J6_positive_strong_capacity | 1.0/1.0/4.5/2.4 | 11.093354 | 7.028151–7.032942 | Pass | Yes |
| all_cyclic_805X_equal40m_capacity | 4.5/4.5/4.5/2.3 | 18.125700 | 6.641134–6.656354 | Pass | Yes |
| all_cyclic_905X_paired_J8_weak_capacity | 4.5/4.5/4.5/2.4 | 18.172259 | 6.787604–6.803047 | Pass | Yes |
| all_cyclic_905X_J6_feed_lost_capacity | 4.5/4.5/4.5/2.4 | 18.560991 | 5.863719–5.878528 | Four floor failures | Yes |

The unmeasured feed/contact inputs are per positive leg and per return leg: equal20m = 20 mΩ each; equal40m = 40 mΩ each; paired J8 weak = J6 +/− 20 mΩ and J8 +/− 80 mΩ; crossed = J6 positive 20 mΩ, return 80 mΩ, J8 positive 80 mΩ, return 20 mΩ. A lost feed removes both its legs and uses 40 mΩ per surviving leg. Current sharing is solved, not forced equal. Exact individual feed currents, voltages and losses are in SERVO-ILLUSTRATIONS.json.

The failed single-J8-feed illustration draws **18.560991391 A**. Its J2/J3/J4/J5 voltages are **5.863718666 / 5.865965005 / 5.870752414 / 5.878528416 V**, below the unchanged 6.0 V floors. Raw failed flags remain. Output servo cable and contact losses are not included, so even a board-pad pass cannot establish voltage at the installed servo.

Different rail currents cannot be added as source amperes. In the moderate equal20m fine-grid case, 3.5 A raw servos plus 2 A at approximately 5 V and 0.34 A at approximately 3.3 V result in **5.350167835 A at the 7.4 V source**. U6 draws 1.667347450 A at 7.105423 V while supplying 2.000238954 A at 5.034462 V; U9 draws 0.179461503 A while supplying 0.34 A. Their 85% efficiency and the remaining modeled biases account for the difference. All 22 illustration source-current identities reconcile within 2.48e-11 A; CURRENT-ACCOUNTING.json records each term.

## Intended hardware and remaining operating decisions

The linked [Hobbywing 200 A page](https://www.hobbywing.com/en/products/platinum-hv-200a-v4167) includes SBEC SKU 30209101 (6–14S input, 5–8 V BEC, 10 A continuous / 30 A peak) and OPTO SKU 30209102 (no BEC). The linked [120 A V4](https://www.hobbywing.com/en/products/platinum-120a-v471), SKU 30203401, is 3–6S with a 5–8 V, 10 A continuous / 25 A peak BEC. The published BEC peak figures supply no pulse duration; the 120 A 10-second motor-current row is not a BEC rating. Actual installed SKU, battery and feed harness remain to be bound. An unspecified external BEC has no assumed rating here, and no variant change was made to this model.

Consequently, all six heavier illustrations are outside the 10 A **continuous** BEC capability of either identified SBEC variant. Five nevertheless pass the ideal-source voltage screen because real BEC limiting and droop are not simulated. A peak-current label cannot establish an allowed pulse envelope for the BEC, contacts, PCB and servos. The five moderate illustrations remain conditional assumed DC points, not a manufacturer-backed continuous-use envelope.

KST's [BLS815 V8.0](https://cdn.shopify.com/s/files/1/0570/1766/3541/files/BLS815_V8.0_Technical_Specification.pdf?v=1700473913), [BLS805X](https://cdn.shopify.com/s/files/1/0570/1766/3541/files/BLS805X_Technical_Specification.pdf?v=1713150470), and [BLS905X](https://cdn.shopify.com/s/files/1/0570/1766/3541/files/BLS905X_Technical_Specification.pdf?v=1709113577) specify **6.0–8.4 V** operation. The preserved power schematic routes raw servo power around U5; its nominal 13.8 V clamp and approximately 4.45 A electronics-branch current limit do not protect or rate the servo bus. Thus the electronics' 5–12.6 V input scope does not permit applying 12.6 V to these servos. Setting a supported BEC voltage is an operating instruction, not a change to board limits.

The selected HTSW headers require an identified mating connector, wire/crimp and thermal condition before assigning an installed per-contact rating. Samtec's [catalog](https://suddendocs.samtec.com/catalog_english/htsw_th.pdf) gives named-mate comparisons of 4.3–6.3 A per powered contact, not an unconditional rating for an unknown RC female contact. A 15.9 A raw servo subtotal on two positive feeds already requires at least 7.95 A through one contact before electronics. Actual mate and harness resistance/current limits, BEC SKU and motion/duty measurements remain engineering inputs and operating-limit decisions; the 294 logic/accessory cases cannot answer them.

## Verification, comparison and scope

The bounded raw verifier reconciled all 610 case rows, 150 geometry certificates, 36,432 certificate references, field/circuit balance and source identities. Independent review reproduced all 9,500 supply-minus-actual-return probes exactly, all numerical comparisons and the five loops. Minimum required margin is 19.068952 mV against its 1 mV guard. Comparing all 9,500 probe rows with accepted native1 shows a largest fine-grid absolute change of **-8.397380 µV**; no pass/fail changed. Current results were freshly solved, not inherited.

Numerical time was 1510.25 s under 1,800 s, one CPU and 4 GiB. Peak combined output was 390.78 MiB under 512 MiB; /tmp and workspace minima were 2848.09 and 212.84 MiB, above 128 MiB. No watchdog stop occurred; the heavy lane was released.

This diagnostic establishes scoped fixed-temperature DC and VCAP resistance checks. U15 static ground support and the separate source-bound reference review do not establish injected ESD performance, fast-edge return capacity, startup, thermal rise, flight or manufacturing qualification. It makes no final-board adoption decision.

Full raw field diagnostics are preserved locally, stored SHA256 `a56f50ed965b6aaec75a0d77f4be5af4a9d3fa3cf23bdb65ea1b8a4aaa9cb401`, logical SHA256 `ff4671a226068efdf29def43ad26a434f0d88a4dea7dbd3541689531da641eb3`. A compact publication may include complete reduced case/probe/loop/convergence rows and source/review identities while omitting this 31.56 MB raw field stream. That omission must be stated; raw-field reconciliation then relies on the bound verification receipt, and independent full-field reproduction requires the replay inputs or access to the local raw file. FINAL-HANDOFF.json binds the exact local evidence.
