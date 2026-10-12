# Native6 conditional DC screen

The accepted native6 geometry passes every enumerated required DC case: 294 cases on each of two grids (588 static evaluations), with all 4,536 required voltage-margin checks passing. The overall result remains **false** because one deliberately out-of-envelope, 18.56074 A single-feed illustration fails four servo-pad voltage floors on both grids. This is a completed conditional DC diagnostic, not final board qualification.

The run completed on 2026-10-12 from 09:34:58.713058 to 09:57:42.125041 UTC in 1,363.411 seconds. Exit code 1 records the retained illustrative failures. The source remained unchanged. Six ordinary connections remain open outside the tested power/return networks; native DRC reports zero geometric errors, six inherited dangling warnings, zero parity errors and no ignored checks.

## Required envelope and model boundaries

- **Classic, 126 cases:** 5.0 V at the ideal J6 board-pad source; 0.32 A aggregate electronics plus 0.020 A DSM demand (0.34 A CORE total). Each of the three receiver-port pairs J9/J10, J9/J11 and J10/J11 carries exactly 1 A per port. No single GH contact is assigned 2 A.
- **Capacity, 126 cases:** the same 5.0 V entry and 2 × 1 A receiver loading, with 0.32 A electronics plus 0.50 A DSM demand (0.82 A CORE total).
- **USB configuration, 42 cases:** 4.33 V at the ideal common USB contacts and 0.30 A aggregate electronics. External receiver, DSM and servo loads are disconnected. This does not establish USB compliance or pre-enumeration behavior.
- Each required condition covers 42 declared allocations among real MCU, flash and filtered sensor supply/return pins, including 0/20 mA analog branch endpoints and the combined 20 mA IMU branch budget. These allocations are enumerated conditional cases, not a proof of global interior extrema of the nonlinear converter equations.
- Converter total efficiency is assumed to be 85%; effective U8 resistance is 90 mΩ. Prescribed mux selection, conservative initial regulator setpoints and conditional quiescent/bias allowances are retained exactly. Package current distribution and behavior beyond specified component characterization are not fully resolved.
- Receiver board-pad floor 4.8 V assumes a remote 4.5 V floor at 1 A with 0.200 Ω contact resistance and at most 0.100 Ω cable resistance. Classic DSM board-pad floor 3.1394 V includes its 20 mA load, 0.120 Ω contacts and at most 0.100 Ω cable resistance. These are declared harness conditions, not measured harness limits. The capacity DSM case uses its separate ledger floor.
- Copper is modeled at 105 °C, 0.015 mm thickness, 95% IACS conductivity and 0.015 mm barrel plating. This temperature is a material assumption, not a thermal prediction, ambient rating, capacitor-body rating or manufacturing acceptance.

The complete model and every per-case floor, current, source, resistor and assumption are in the reconstructed reproduction/ledger.disabled.json. The model contract identifies all 305 case definitions. No current, voltage or convergence threshold was relaxed.

## Terminal and geometry fidelity

The model uses 15 actual copper networks, 107 finite contact windows, five VCAP DC loops, 268 scoped physical pads, 44 real return pads and all 321 drilled openings (294 vias and 27 drilled pads). Actual saved copper fills, antipads, contact overlap and barrel geometry are retained. No zero-resistance ground plane or nominal trace-width shortcut replaces those paths.

The PCB/native source owns pad coordinates and layers. Parts metadata supplies identities and ratings; its stale pose fields are not used to relocate terminals. This matters for moved R6 and D1. Corrected power terminals include TPS2553 IN6/OUT1/GND5 (EN4 is logic), DPS368 VDDIO6/GND1 and VDD8/GND7, and flash U3.8 referenced to its actual U3.4 ground. Flash exposed pad U3.9 is physical ground without invented ideal package current sharing. CORE entry is L2.2 with U9.1 power return; U9.6/U9.4 form the actual sense pair.

## Results

| Check | Result |
|---|---:|
| Required static evaluations | 588/588 pass |
| Required voltage margins | 4,536/4,536 pass |
| Illustrations, each grid | 10 pass, 1 fail |
| Tightest required board-pad voltage | Classic DSM 3.158208168 V versus 3.1394 V floor |
| Tightest required guarded headroom | 17.808168 mV after 1 mV guard |
| Lowest loaded BEC flash voltage | 3.097739340 V at U3.8 − U3.4, 0.32 A |
| Lowest loaded USB flash voltage | 3.126895343 V at U3.8 − U3.4, 0.30 A |
| Lowest receiver voltages J9/J10/J11 | 4.861386 / 4.887188 / 4.876652 V versus 4.8 V |
| Largest two-grid voltage change | 0.575847 mV versus 1 mV limit |
| Impedance sensitivity checks | All 15 pass |
| VCAP loop and resistance convergence checks | All five pass |
| Largest whole-circuit power imbalance | 1.883 × 10⁻¹⁰ W |
| Largest direct-field/port copper-energy difference | 2.261 × 10⁻¹¹ W |
| Largest loaded-field KCL residual | 3.815 × 10⁻⁹ A |

Fine-grid VCAP loop resistances for U1.12, U1.18, U1.31, U1.47 and U1.63 are respectively 19.1169, 18.6843, 23.6942, 26.1042 and 25.1249 mΩ, each below the 35 mΩ DC loop limit. These values do not establish AC decoupling or transient stability.

For the worst loaded BEC flash case, L2.2-to-U3.8 supply drop is 84.616170 mV and U3.4-to-U9.1 return rise is 2.750791 mV. The analogous worst loaded USB case gives 55.997115 mV and 1.726515 mV. This distinguishes the actual local flash supply/return voltage from a remote regulator or ground reading.

The retained failed illustration is same_BEC_all_cyclic_905X_J6_feed_lost_capacity__sample_mcu_vdd19. Its modeled external BEC current is 18.5607395745 A, already outside the stated 10 A continuous BEC envelope. The illustrative source is 7.4 V with explicit feed/contact resistances; current sharing is solved. The J2/J3/J4/J5 servo board-pad voltages are 5.863817071, 5.866053464, 5.870827184 and 5.878587896 V against a 6.0 V floor. The worst shortfall is 136.182929 mV. Output harness drops, time duration, startup, reversal and stall are unbound; a peak-current rating does not qualify this case.

## All 11 servo illustrations

All use a 7.4 V ideal external source with the exact finite feed/contact resistances in results/illustration-summary.json, J10/J11 loads of 1 A each, and the stated classic/capacity CORE load. An absent feed leg is disconnected. A voltage pass is not source-current qualification. No case specifically targets a solved 10 A input. The five moderate examples draw below 10 A, while even the three 8.9 A servo-only examples exceed 11 A after electronics and conversion demand.

| Exact case name | Servo J2/J3/J4/J5 (A) | BEC input (A), fine grid | Voltage result, both grids | Input ≤10 A |
|---|---|---:|---|---|
| same_BEC_moderate_equal20m_classic__sample_mcu_vdd19 | 1 / 1 / 1 / 0.5 | 5.350077 | pass | yes |
| same_BEC_moderate_paired_J8_weak_classic__sample_mcu_vdd19 | 1 / 1 / 1 / 0.5 | 5.367330 | pass | yes |
| same_BEC_moderate_crossed_J6_positive_strong_classic__sample_mcu_vdd19 | 1 / 1 / 1 / 0.5 | 5.367554 | pass | yes |
| same_BEC_moderate_J6_feed_lost_classic__sample_mcu_vdd19 | 1 / 1 / 1 / 0.5 | 5.443532 | pass | yes |
| same_BEC_moderate_J8_feed_lost_classic__sample_mcu_vdd19 | 1 / 1 / 1 / 0.5 | 5.442049 | pass | yes |
| same_BEC_heavy_S1_905X_equal40m_capacity__sample_mcu_vdd19 | 4.5 / 1 / 1 / 2.4 | 11.123542 | pass | no |
| same_BEC_heavy_S2_905X_paired_J8_weak_capacity__sample_mcu_vdd19 | 1 / 4.5 / 1 / 2.4 | 11.092697 | pass | no |
| same_BEC_heavy_S3_905X_crossed_J6_positive_strong_capacity__sample_mcu_vdd19 | 1 / 1 / 4.5 / 2.4 | 11.093236 | pass | no |
| same_BEC_all_cyclic_805X_equal40m_capacity__sample_mcu_vdd19 | 4.5 / 4.5 / 4.5 / 2.3 | 18.125543 | pass | no |
| same_BEC_all_cyclic_905X_paired_J8_weak_capacity__sample_mcu_vdd19 | 4.5 / 4.5 / 4.5 / 2.4 | 18.172118 | pass | no |
| same_BEC_all_cyclic_905X_J6_feed_lost_capacity__sample_mcu_vdd19 | 4.5 / 4.5 / 4.5 / 2.4 | 18.560740 | FAIL, four servo floors | no |

All 11 remain illustrative; they provide no general servo-load guarantee. Each grid’s individual servo pad voltages/floors and failed probes are retained in the companion JSON.

## Numerical and source evidence

Both 0.12 mm and 0.09 mm grids completed all 305 cases, with the same case-definition hashes. Impedance convergence retains 2.5% relative or 0.1 mΩ absolute tolerance, and voltage comparison retains 1 mV. Independent bounded review checked all 610 case records, all margin classifications, all five loops, conservation checks, source/model/runtime identities, 36,432 certificate references, 150 certificate digests and 6,934 ring guards. All 30 mesh payload digests and 56 cache receipts (30 fresh builds, 26 matching reloads) were verified. All 1,737 recorded source/dependency hashes were unchanged before and after the run.

The exact raw result is preserved locally, 317,826,675 bytes, SHA256 c9afa4edd1037f716dd32687a3f528a9cbae27893df243c02f77be5f9bff04b7. It and the mesh payloads are intentionally absent from this compact package. The exported case records retain every scalar circuit result, probe voltage/floor, current, converter result and port injection. Loaded-field records retain conservation metrics and certificate references; the certificate index retains guards and digests. Large field arrays and full certificate payloads remain available through the raw-result identity. The actual failing BEC/In3 certificate is included with the serializer proof.

PCB SHA256: 76ae77d04a615762e96fbdac85c8190e52ace9125b68ce6c3176dccf776413e0.
Native export SHA256: dba3668fe6f3f0620952bf11bdaa18f342047a7cba63f98e20f5459002ee7f88.
Model contract canonical SHA256: 285961cbf0d79d0ae28e2e2a84b256380da8c6a922b6977a2495b7554c922a95.
SOURCE-PROVENANCE.json binds the exact numerical runtime, adapter identity and every technical export transformation.

## Bounded certificate serialization repair

The original numerical attempt refused while serializing an exact BEC/In3 ring-area Fraction, before any loaded result. Its numerator/denominator had 4,511/4,497 decimal digits; baseline native_edge_noding.py line 296 called str(exact_before), exceeding Python's unchanged 4,300-digit global guard. The isolated successor replaces only that certificate conversion with bounded 600-digit chunk conversion, capped at 32,768 digits per integer. It retains the existing canonical decimal-string schema and an exact bounded reader. It does not change geometry arithmetic, tolerances, repair decisions or acceptance semantics.

The actual failing source reproduction now passes all 18 ring certificates with exact roundtrips. The original failure/control is retained. Generated 4,999/5,999-digit controls, eight existing controls, 58 independent roundtrips and 24 independent refusal controls passed; 525 legacy-size ring fields and their canonical JSON were byte-identical. Existing consumers store/hash the same JSON string. Consumers that parse an oversized value with ordinary int/Fraction must use the supplied bounded reader. Python's global guard stays at 4,300 digits; over-cap values refuse. proofs/serializer-only.patch and the original/successor sources make this narrow delta reviewable.

## Reconstruction and replay

COMPRESSION-MANIFEST.json records every compressed member's digest plus its decompressed size and SHA256. The deterministic gzip streams use an empty filename and mtime zero. restore_inputs.py verifies compressed and restored bytes and reconstructs logical paths into a separate directory. The unchanged PCB is supplied from the exact repository path and Git blob recorded in inputs/board-reference.json; it is not duplicated here. Run restore_inputs.py with --repository pointing to a checkout containing that board and --output pointing to a new directory. It performs no numerical execution. model/job.json is reconstructible by selecting cases, networks, loops, material, mesh_spacings_mm, convergence and limits from the ledger; its canonical digest is recorded in provenance.

The replay freeze is disabled by default. Its only changes from the actual compiled input are portable relative paths and removal of administrative metadata, plus the corresponding ledger freeze hash; all numerical model values remain equal. A separately prepared enabled copy must set numerical_execution_authorized true and update that copy's ledger freeze_manifest_sha256. From the reconstructed directory, the numerical command is:

    python runtime/validate_static.py --freeze reproduction/freeze.enabled.json --ledger reproduction/ledger.enabled.json --out replay-result.json --mesh-cache replay-cache --run

Use Python 3.12.14, NumPy 2.2.6, SciPy 1.17.0, Shapely 2.2.0 (GEOS 3.14.1) and sexpdata 1.0.2. The original execution used one CPU/thread, 4 GiB memory and a 1,500-second overall bound, with unchanged solver-stage limits in the ledger. A replay is separate work; this package has not silently rerun or replaced the completed result.

The result does not qualify startup, switching ripple, AC impedance, transient stability, EMI, thermal rise, copper/current-density endurance, connector/harness ratings, manufacturability, assembled-unit behavior or flight use. Required-case success applies only to this exact source and these declared DC conditions.
