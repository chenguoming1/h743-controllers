# Independent peripheral-power drop review

**Finding:** the large 5 V peripheral deficit is supported by the actual native copper topology and an independent analytic lower bound. No source-pin swap, duplicate contact loss, wrong U6 setting, or missing parallel feed was found that explains it away. This is a **design risk at the declared load/material corner**, not an accepted voltage, thermal, production, or flight qualification. No board or voltage-setting changes were made.

## Exact source and acceptance status

- Numerical source: candidate15, board SHA-256 `23232e7bc1903c06c1809d569c91e4cb161281be9225f3776076386593e55674`; native export `dc1aa86cd3969eb2f0444674adef7f948b46cb50ad07d4d56d1efa3ba083febd`.
- Released result: `../static-power-validation/pilot-candidate15-loaded73-released/result.json`, SHA-256 `0780cece1cf4194220a542f9d7f65cc6be3dc457b9bbfaf74bd5a07fa3a1d9ac`; ledger `61c27f88dceb64d27e0cc700a8306de07543d5e268d5a4e2419bb81a44f3a8be`. This review independently verified all 25 frozen input hashes and the result hash.
- Accepted routing candidate16 board identity: `9cf04c88ebd31d7e2c12bdb8a9f80e01b615a7bdb94a73fc2234208a2e0a14c8`. `../static-power-validation/candidate15-to-candidate16-loaded73-geometry.json` records identical modeled power objects, fills, physical drills, contacts, stackup, and material. That comparison supports applicability of this geometry diagnosis; it does not rebind or accept the candidate15 numerical result as final-board validation.
- Two grids, 0.20/0.15 mm, each completed 73 cases. All 11 impedance guards pass. Maximum voltage-grid change is 1.434151 mV versus the locked 1 mV criterion: **the conditional screen remains unaccepted**. A 0.5 V shortfall is hundreds of times that discrepancy, but the discrepancy is not a rigorous error bound.

## Terminal and control audit

The frozen parts are TPS63070RNMR at U6 and TPS2117DRLR at U7. TI confirms U6 pins 7/8 are VOUT, 12/13 VIN, 10 power ground, 4 control ground and 5 feedback; pin 1 low selects forced PWM. The native source maps these correctly, including U6.1 on GND. The low corner uses 0.792 V feedback with 53,546.4/10,010 Ω divider values, yielding 5.028638 V relative to divider ground before finite trace/ground effects. That agrees with the observed R54.1 = 5.031879 V and local ground ≈3.277 mV. U6 output exceeds R54.1 by only 9.343 mV, so the controller senses near its output, not U7's distant input. [TI TPS63070 Rev. B, pp. 3, 7, 17](https://www.ti.com/lit/ds/symlink/tps63070.pdf)

U7 pin 3 is VIN1, pins 2/7 are VOUT, and pin 5 is MODE. The native pin mapping and circuit use are correct: U7.5's same-net connection is mode bias, not an unmodeled second power input. The model uses a separate 33 mΩ U7 resistor. TI specifies that maximum at 200 mA, 3.3/5 V test points and through 105°C; its use here at about 2 A and 4.424 V local input is explicitly an extrapolation. It accounts for about 66 mV, not the preceding 614 mV copper loss. [TI TPS2117 Rev. A, pp. 3, 6](https://www.ti.com/lit/ds/symlink/tps2117.pdf)

Native U6 power pads are custom polygons. Their 0.01 mm anchor size is not their conductor/contact size: the connected 7/8 union is 0.539205 mm², with bounds x=31.8–32.5/y=15.55–16.4 mm. U7.3's finite contact is 0.198852 mm² on B.Cu. The frozen code uses these actual finite land unions, not point injection or a tiny anchor square. Pads/annuli are ideal equipotentials and barrels have explicit resistance. Pin, solder and within-land losses are omitted; those omissions cannot supply a fictitious 0.6 V series loss.

The source registry's original “disabled/unbound intent” labels and historical documentation containing TPS2116/536 kΩ recommendations are not the executable run identity. The released ready ledger, bound contacts, selected parts and later 53.6 kΩ/10 kΩ BOM control this result. Their hashes were checked.

## Actual path and independent resistance bound

There is no saved +5V_BEC plane. Native inventory contains 96.754779 mm of 0.6 mm In3 track and 16.791985 mm of 0.6 mm In2 track. Treating those whole centerlines as a single straight series conductor gives 0.305452 Ω at the frozen material, close to the saved finite-port resistance 0.306810 Ω. This inventory calculation alone is only a cross-check: bends, overlaps and local branches prevent treating a sum of every track as a rigorous resistance.

The independent script reconstructs actual copper/fills minus every drill and the board outline. It identifies mutually disjoint straight interior slabs, verifies each is no wider than 0.60004 mm, contains no barrel, and has no bypass: deleting that slab disconnects U6.OUT_7_8 from U7.3 in a freshly built finite-component/barrel graph. Fifteen accepted slabs total **61.299066 mm**. Current conservation and the sheet energy inequality give:

**R ≥ 0.164889634 Ω; at 2 A, drop ≥ 329.779267 mV and loss ≥ 0.659558534 W.**

This deliberately omits bends, track ends, all other sheet copper, barrels and contacts. It is a conservative lower bound for the frozen uniform-material geometry, independent of the FEM result and any mesh choice. It already exceeds the representative 241.223 mV total U6-output-to-4.8-V allowance before U7 or downstream losses. Native export precision and floating-point geometry remain limitations; this is not a measured manufacturing bound. The width includes a 40 nm allowance and the geometry containment checks use a 10⁻¹² mm² numerical area tolerance.

The reviewed separate proof in `../static-power-validation/candidate15-bec-mandatory-barrel-cuts.json` finds the In2↔In3 span of via `617e9ee9-299c-492c-8be7-e03b48679c67`, at (26.165650, 0.640417) mm, is mandatory. Its saved field current is 2.000142 A. Thus the historically named “BEC second physical load path” is a continuation through the long In3 path and In2 segment. It is not a complete independent parallel source-to-load feed. Local source/entry vias do share current, but they do not bypass this mandatory transport route.

## Representative drop accounting

Case: `classic_BEC5_AB_mcu_vdd19_baseline`, fine 0.15 mm grid. Voltages below are relative to SOURCE_GND unless specified.

| Term | Value |
|---|---:|
| U6 output / feedback-top / U7 input | 5.041223 / 5.031879 / 4.427559 V |
| U6 output → U7 input copper | 613.663 mV |
| U7 switch | 66.001 mV |
| U7 output → J9 positive / J10 positive | 100.241 / 67.750 mV |
| J9 return / J10 return | 5.867 / 5.305 mV |
| J9 / J10 local pad voltage | 4.255450 / 4.288503 V |
| +5V_BEC sheet+barrel loss | 1.227412 W |
| +5V_BEC In3 / In2 sheet loss | 1.006833 / 0.135480 W |
| +5V_BEC all barrel loss | 0.007803 W |
| U7 resistor loss | 0.132006 W |

The load is two distinct 1 A receiver ports, 2 A aggregate. The 4.8 V board-pad threshold is conditional: 4.5 V at the remote receiver plus 0.200 Ω contact loop and cable loop ≤0.100 Ω at 1 A. Those external losses are in the threshold, not duplicated as copper resistors. Even removing that full external allowance leaves these loaded board pads below 4.5 V. The frozen converter supplies 2.000222 A including small bias loads; U7 input demand is 2.000048 A.

## Smallest supported redesign target

Address the **+5V_BEC transport between the U6 output/via cluster around (33.7–34.3, 14.45–14.9) mm and the U7 entry cluster around (36.125, 3.4)/(36.825, 2.6) mm**, including the local landing to U7.3 at (37.45, 6.54). The dominant loss is the long 0.6 mm In3 excursion around the lower/left/top board edges, followed by the In2 continuation through the mandatory via. A real shorter/wider path or a genuinely complete parallel connection across these endpoints is the concrete copper scope to investigate. Adding another local via at one existing end alone cannot bypass it. No clearance-feasible replacement has been designed or qualified by this audit.

Holding the representative source/downstream terms fixed leaves only 69.113 mV for this transport, approximately 34.06 mΩ after a 1 mV numerical planning guard, versus about 306.82 mΩ observed. This is a planning budget, not a signoff target: source regulation, return current and feedback must be recomputed after geometry changes. It does not justify changing the voltage setting. The downstream +5V_PERIPH path also needs its retained budget, but it is not the main deficit in this case.

## Scope and remaining limits

- Material is modeled 105°C copper, 15 µm thickness, 95% IACS and 15 µm plating. Native outer layers are nominally 35 µm; the uniform 15 µm screen is conservative there. Dominant In3/In2 nominal thickness is 15.2 µm. No thermal equilibrium or ampacity is established; copper temperature does not establish component-body temperature.
- The 5 V case starts at ideal J6 pads without an invented upstream harness. U6 sees 4.721501 V local input and 5.037183 V local output: mild boost. Its ideal regulated 2 A solution and 85% efficiency are conditional, not proof of converter current/thermal capability. Initial divider tolerance is at 25°C; its separate 105°C body/TCR sensitivity and broader line/load/leakage/efficiency corners were not included in this subset.
- The one all-cyclic/905X, J6-feed-lost servo illustration gives 5.864779–5.879317 V at servo board pads. It prescribes 15.9 A servo current, about 18.562 A total source, and an unmeasured 40 mΩ positive plus 40 mΩ return J8 feed. This exceeds the documented 10 A continuous BEC capability; the 30 A peak has no supplied duration. It is not an approved mandatory operating envelope or measured single-feed tolerance. Keep its below-6-V illustration separate from the shared ABC 2 A requirement and the recommended two-feed installation.
- No dynamics, startup, mux selection/handover, real connector/harness qualification or flight qualification were performed. Ordinary routing is unfinished, and any later power-relevant geometry change requires new source/check binding and numerical acceptance.

## Reproduce this bounded review

From the workspace root:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=python-deps python independent-power-drop-review/independent_checks.py
python independent-power-drop-review/extract_evidence.py
```

Outputs are `independent-checks.json` and `source-bound-evidence.json`. Both scripts only read source data and write review receipts; neither builds an FEM mesh, runs an electrical solver, edits the board, or changes frozen evidence.
