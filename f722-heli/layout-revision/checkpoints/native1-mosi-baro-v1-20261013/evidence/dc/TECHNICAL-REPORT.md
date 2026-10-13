# Native1 MOSI/BARO conditional DC result

The exact current native1 candidate passes all **294 required conditional cases on both grids**, all **15 impedance/convergence checks**, and all **five VCAP loop checks**. The full raw overall result remains **false**, because the separately labeled single-feed illustration fails four servo board-pad voltage floors.

## Exact source and unchanged model

- PCB SHA256: `b31e6b9ca47e8e5a0b8967ec25f8390a66541b0c374ebedde77a39380e7d73ca`
- Native logical SHA256: `6c0485bf7e1098d0f51d8d63ca7e7a5ee6a26c21656192c0c967cd6e32917261`
- Model contract: `285961cbf0d79d0ae28e2e2a84b256380da8c6a922b6977a2495b7554c922a95`
- 15 networks, 107 finite contacts, 268 modeled physical pads and 44 current return-to-plane witnesses
- All 330 actual drilled objects, including both added MOSI vias, remove copper on their spanned layers irrespective of net
- 294 required plus 11 illustrative cases on each of the 0.12 mm and 0.09 mm grids: 610 complete case rows
- Actual USB/DSM supply input pin 6 and downstream floor mappings preserved; enable pin 4 remains a separate probe
- Copper/plating 0.015 mm, 95% IACS at 105 C; unchanged ideal land/package and component-current assumptions

The complete current ledger matches accepted source2 in every field except its bound source freeze. The fresh metadata, support, finite contacts, paired DRC and current saved fill were recomputed for this candidate. Both DRC modes retain one ordinary C_RX_EXT open outside the power scope, zero warnings and no ignored checks. Historical DC evidence was not transferred.

## Required checks and retained illustrative failure

The largest fine-grid VCAP loop is **26.324988 milliohms**, below the 35 milliohm limit. Worst loaded flash voltage is **3.083711651 V** against 2.7 V, with 0.32 A flash loading. Required-case voltage margins and all numerical sensitivity/resistance guards pass.

The failed illustration is `same_BEC_all_cyclic_905X_J6_feed_lost_capacity__sample_mcu_vdd19`. Its source current is **18.560994254 A**. Fine-grid board-pad voltages are:

| Pad | Voltage | Required floor |
|---|---:|---:|
| J2 | 5.863718452 V | 6 V |
| J3 | 5.865964789 V | 6 V |
| J4 | 5.870752195 V | 6 V |
| J5 | 5.878528194 V | 6 V |

The same illustration fails on both grids. These are board-pad windows; unmeasured servo harness/contact drops remain outside the model. All raw failed flags and the process exit code 1 are retained.

## Change relative to accepted source2

The comparison covers **9,500 matching probe rows** under exactly identical case, contact, material and numerical definitions. The largest fine-grid absolute probe change is +0.435326 mV at `actual_rail_mcu_vdd64` in the illustrative case. The maximum VCAP loop increase across both grids is 0.106358 milliohms. These changes do not transfer qualification between sources.

## Execution and verification

The numerical stage took 1479.04 seconds under the 1,800-second limit. It used one CPU/thread and the 4 GiB address-space cap. Combined output peaked at 390.52 MiB under 512 MiB. Minimum free space was 3537.25 MiB in the execution temporary filesystem and 224.73 MiB in the workspace, above the 128 MiB reserves. No watchdog stop occurred.

The bounded verifier checked all 610 raw cases, all 150 native geometry certificates, circuit/field energy and KCL checks, source identities and reduction equality. A separate reviewer recomputed the compact case, VCAP and numerical disposition and bound the exact raw-verification receipt without repeating the solve. The raw native inherited contact-applicability flag remains false, with the exact current VX-window supplement bound separately.

A read-only source comparison initially failed because its historical source2 directory label was changed incorrectly. The failed script/log/receipt remain preserved. The corrected version changes only that locator; no numerical or result data changed.

Raw gzip SHA256: `79774d3af8c62c3e8a3b06dd89de85a78c6f3abcdf43015e3dc8c53ba5b184ba`.
Logical JSON SHA256: `adc0b6e38cfe09bc2d65fc7288e4d949c69981ffef1ed02eaaddde7f6ab14761`.
See `FINAL-HANDOFF.json` for the full evidence identities.

## Scope

This is an intermediate, source-bound conditional DC/VCAP screen. It does not establish local neck ampacity, fast-edge AC behavior, startup, thermal performance, flight, manufacturing or final board acceptance. The unfinished ordinary RX route and independent engineering limits remain. No board adoption is claimed by this diagnostic.
