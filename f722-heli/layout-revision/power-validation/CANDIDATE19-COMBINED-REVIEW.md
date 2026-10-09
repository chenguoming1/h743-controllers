# Candidate19 conditional power and VCAP screen

The corrected candidate19 passes the 62 required conditional voltage cases, all five DC VCAP copper-loop checks, and every numerical/convergence gate. The unchanged overall runner result is **false** because one of the 11 separate high-load/lost-feed illustrations fails its four servo voltage floors. That illustration exceeds the stated continuous source capability and is not a qualified operating envelope.

This result is bound to PCB SHA-256 `e26da349b5585db16d2586ed05e3d649e2f1f8df4932c09d78aca8ce880469c4`, native export `3694b37bbe4f9b71b88472e8b3f075365cf6319bd26f28d06f0d254dc0d45868`, released freeze `1e0296e48e779f1a3531a7f0fa901c25ab978da97687e20826a395e58bb727b5`, and ledger `f811c4d93dd074e5d74fb000db2d1218d10199ceb7c0562173be437fda572951`. The full result hash is `28dfe7bcff16f08e3919be7063cf06727ab25678e3585e86f6acfda26e0742f1`. Later drills, fills, contacts or board changes require fresh binding and review.

## Scope and decisions

| Scope | Outcome |
|---|---|
| 60 shared AB/AC/BC cases at 5.0 V, with 0.32 A electronics allocated adversarially to ten actual load/return locations and separate classic 20 mA or capacity 0.50 A DSM | Pass under the frozen inputs; incompatible servo loads disconnected |
| Two USB configuration cases, 4.33 V source and 0.30 A electronics | Pass the defined operating checks; external DSM/ABC/servo loads disconnected |
| Five VCAP DC copper/barrel loops | Pass their 35 mΩ budgets with grid sensitivity guards |
| Numerical gates | Pass on 0.12/0.09 mm grids: residual, KCL, energy, reciprocity, impedance and voltage sensitivity |
| Eleven same-BEC lead/servo illustrations at 7.4 V | Ten pass; one high-load single-feed case fails four servo floors |
| Original all-selected-cases runner boolean | False, preserved without reinterpretation |

The fresh model has 13 networks, 99 finite contacts and 41 GND contacts. C7.2 is an additional ideal finite contact compared with the older 40-contact loaded model. No incompatible old GND operator was reused. Actual fills and every physical drill, including foreign-net antipads, were retained. Source-to-load currents include narrow intermediate sections and finite barrels; parallel sharing is solved from the network.

## Voltage and loop findings

| Quantity | Fine-grid result | Locked comparison |
|---|---:|---:|
| Lowest loaded ABC receiver pad | 4.862249 V at J9 | 4.8 V floor; 61.249 mV margin after the 1 mV numerical guard |
| Lowest classic 20 mA DSM pad | 3.158702 V | 3.1394 V floor; 18.302 mV guarded margin |
| Capacity 0.50 A DSM pad | 3.048114–3.061706 V | Report only; does not inherit classic receiver accuracy |
| Lowest loaded BEC U9 input | 4.615312 V | 315.312 mV above the separate 4.3 V accuracy-condition screen |
| Lowest USB U9 input | 4.234249 V | Above 3 V operating minimum; below the 4.3 V accuracy-condition screen |
| Maximum voltage grid change | 0.575190 mV | Below the unchanged 1 mV criterion |

The worst voltage-grid change is the U9 input in `capacity_BEC5_BC_mcu_vdd48_baseline`. All 294 voltage-grid comparisons meet the numerical criterion. The four negative threshold margins all belong to the same illustrative lost-feed servo case.

The five VCAP loops are 18.984229, 18.499300, 23.538322, 26.025318 and 24.990207 mΩ, respectively to U1.12, .18, .31, .47 and .63. The maximum loop change is 0.109247 mΩ; the worst remaining guarded margin is 8.865435 mΩ. These are sums of the specified DC copper/barrel legs. They exclude the physical 0.12 Ω R16 resistor, capacitor ESR, inductance and AC regulator stability.

For the representative classic AB case, U6 output is 5.037251 V absolute. BEC copper drops 38.370 mV to U7 VIN1; the explicitly modeled switch drops 66.002 mV; PERIPH positive copper to J9 drops 64.742 mV; J9 return is 5.889 mV above source return. J9 therefore receives 4.862249 V differentially. BEC copper loss is 76.746 mW. The former failed source had about 614 mV BEC drop and 1.227 W loss in its unconverged diagnostic. The route correction removes that dominant deficit; the old result is retained separately.

The failed illustration applies approximate 4.5/4.5/4.5 A cyclic plus 2.4 A tail loads with J6 feed lost. The remaining modeled J8 positive and return conductors each carry 18.560225 A; servo pads receive 5.864748–5.879330 V against the illustrative 6 V floor. The approximate DC endpoints have no assigned duration, exceed the stated 10 A continuous source envelope, and do not establish a usable pulse allowance.

## Numerical and source evidence

The final direct-field stage completed at 873.09 seconds. Peak recorded RSS was 1,879,621,632 bytes (1.75 GiB); the process enforced 4 GiB address space, 1,500 seconds and one numerical thread. Fine GND has 745,509 raw nodes, 285,290 reduced equations and 1,100,034 triangles. Maximum factor storage was 146.8 MB with 11.85 million nonzeros.

Maximum loaded-field KCL residual is 9.39e-10 A, energy discrepancy 6.68e-12 W, reciprocity error 1.57e-11 Ω and linear residual/required-target ratio 0.985. At most one refinement step was needed. The compact summary verifies 28 frozen file hashes, six runtime hashes, all 146 executed case-definition hashes, 7,972 loaded/port geometry references and 80 VCAP geometry references.

No native vertex or positive-area material was discarded. Maximum represented correction of a proved derived intersection is 5.854e-11 mm; maximum rounding of inserted exact grid intersections is 3.915e-15 mm. Exact rational ring areas, holes, finite contacts and seam constraints remain certified. These are numerical representation bounds, not fabrication tolerances.

Two earlier candidate19 attempts remain immutable. The first refused a one-ULP artificial sheet-partition triangle. Exact native-edge/grid subdivisions before clipping resolved it. The second refused KCL because double stiffness accumulation left spurious row sums after ideal-land condensation. The corrected solver retains every triangle, gives identically one-potential elements exactly zero energy, treats partial condensation algebraically, and uses the accurate wide physical operator for refinement/KCL with matching voltage-difference fields. Cached double matrices are only factorization preconditioners. No acceptance gate was weakened.

## Limits of the conditional result

The frozen material assumption is uniform 105 °C copper, 15 µm effective copper/plating and 95% IACS. This is a resistance model, not a thermal or manufacturing guarantee. Source/contact values, total converter efficiency and switch resistance outside their specified test conditions are explicit modeled inputs. Measured four-lead harness values remain unset. The 0.32 A electronics allocation is an adversarial sweep, not an assertion about actual equal or measured load shares.

This subset does not complete the 12.6 V/upper-output, total-efficiency, leakage, effective-switch-resistance, resistor-temperature, line/load or broader same-BEC corner review. Extra regulation sensitivities are engineering scenarios; they must not be relabeled as a manufacturer-required duplicate IC temperature error. The board still has unrelated ordinary opens. Final routed geometry, startup/handover, local bypass effectiveness, VCAP AC behavior, production and flight qualification require their own evidence.
