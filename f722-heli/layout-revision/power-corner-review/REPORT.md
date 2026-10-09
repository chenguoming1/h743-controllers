# Source19 voltage corners and measured-budget targets

These are historical, conditional small-circuit results on the two verified source19 port matrices. No new mesh or loaded field was solved. They do not qualify candidate26 or any later board with changed copper, drills, antipads or fills. The original full-field result remains unchanged: 62 required cases, five VCAP DC loops and numerical gates pass; the overall result stays false because of the overloaded lost-feed illustration.

## Completed evidence

The recovered 140 endpoint cases reproduce exactly, and all 146 original circuit replays match exactly. The new 5,532-case sensitivity sweep evaluates both 5.0/12.6 V input endpoints, complete ten-vertex BEC allocation contexts, nine independent 75/85/95% converter-efficiency pairings, effective switch-resistance stresses, signed leakage scenarios, independent divider-temperature signs, and combined cases. USB remains the two original 4.33 V configuration cases with external loads disconnected.

All acceptance and report-only voltage grid checks pass. Maximum delta is 0.678143 mV against the retained 1 mV criterion. Maximum circuit power-balance residual is 2.92e-10 W. This verifies the small circuits, not fresh spatial KCL, field energy or current density.

Initial lower-endpoint reserves are 60.325 mV at J9 and 17.650 mV for classic DSM; both limiting cases occur at 12.6 V. With the interval divider/leakage/U8 combination and all nine efficiency pairings, the reserves are 41.172 mV and 17.607 mV. Higher efficiency is slightly worse for those two floors because of actual return/sense motion. The combined U7=60 mΩ stress produces 642 failed voltage cases; its weakest guarded reserve is −12.829 mV. These failures are retained. They do not establish 60 mΩ as a manufacturer-guaranteed or measured U7 condition.

## Allowances with other terms held

Initial means 25°C divider bodies, initial resistor tolerance/reference bound, zero U6 leakage, U7=33 mΩ, U8=90 mΩ and eta6=eta9=85%. Combined means independent divider departure of 65°C from 25°C (conditional −40…85°C interval), assumed −100 nA leakage for lower corners, U8=150 mΩ and all nine efficiency pairings. Upper corners use +100 nA and the high reference/divider/U9 setpoints. U7 remains 33 mΩ except when it is the variable being bounded.

| Variable | Initial | Combined |
|---|---:|---:|
| U7 effective RON | 63.162 mΩ | 53.586 mΩ |
| U8 effective RON, 4.3 V accuracy condition | 512.386 mΩ | 395.424 mΩ |
| U8 effective RON, 3 V operating-only screen | 1316.166 mΩ (grid-limited lower bound) | 989.184 mΩ (grid-limited lower bound) |
| Additional downward U6-only error | 1.199493% | 0.821791% |
| Additional downward U9-only error | 0.554237% | 0.552893% |
| Additional common downward U6/U9 error | 0.554189% | 0.552843% |
| Additional upward U9-only error | 1.152573% | 1.147957% |

Every passing lower bracket is checked against all 120 initial lower contexts or 1,080 combined lower contexts; upper checks cover 80/720 contexts. Brackets are narrower than 1e−7 in ohms or fractional setpoint. A grid-limited result is only a verified lower bound: it does not locate the physical 3 V boundary. The saved failed bracket identifies the exact numerical stop. In the initial U8 operating search the stop occurs while U9 input is still 3.477632 V.

These are alternative budgets, not simultaneously available maxima. In particular, the separate U6 and U9 percentages must not be added; the common fractional row is a separately solved path. The combined U7 budget leaves about 20.586 mΩ above the assumed 33 mΩ only when no additional source error is spent. Approximately 10 mΩ at the ~2 A U7 load consumes 20 mV of ABC reserve. No U6 upper-error allowance is assigned because unspecified ABC peripherals have no documented universal ceiling. Neither endpoint sampling nor bisection proves continuous-input or arbitrary-intermediate-allocation behavior.

## Device sources and actual conditions

The fitted U7 is TPS2117DRLR. TI's [Rev. A table, p.6](https://www.ti.com/lit/ds/symlink/tps2117.pdf#page=6) uses VINx=5 V and IOUT=200 mA: 18.5 mΩ typical / 25 mΩ maximum at TA=25°C, 31 mΩ maximum through TA=85°C and 33 mΩ through TA=105°C. The board's ~2 A use is an extrapolation of that resistance row. Its actual temperature is unmeasured; modeled 105°C copper is neither ambient nor junction temperature. The 50/60 mΩ cases are stresses, and do not by themselves justify a component or copper change.

U8 is TPS2121RUXR. Its [Rev. F table, p.7](https://www.ti.com/lit/ds/symlink/tps2121.pdf#page=7) specifies resistance at VINx≥5 V, |IOUT|=200 mA and VPRI>VREF: 56 mΩ typical / 70 mΩ maximum at TJ=25°C, then 85/90/100 mΩ maxima through 85/105/125°C. The 120/150 mΩ cases are engineering stresses. Actual modeled BEC selected-input voltage spans 4.655701–12.514713 V and path current 0.091175–0.771806 A across loaded profiles. No table test-current equality is inferred.

The reviewed TPS63070 ±1% feedback term already covers its IC temperature/input table scope. Only divider-body TCR is varied here; no second generic IC-temperature error is added. Positive 100 nA is the printed endpoint tested at VFB=0.8 V. Negative 100 nA is an engineering assumption. Divider R54/R55 tolerances and TCR signs are independent; 105°C resistor-body rows remain sensitivities, and X5R capacitor bodies remain limited to 85°C.

## Where the modeled drop occurs

For the combined 95/95% limiting cases, terminal accounting gives:

- J9.3/J9.4: U6 output to U7 input copper: 38.370 mV; U7 effective device: 66.002 mV; U7 output to J9 positive copper: 64.742 mV; J9 return relative U6 power ground: 4.938 mV.
- J12.1/J12.2: L2 output to U11 input copper: 23.176 mV; U11 effective device: 3.000 mV; U11 output to J12 positive copper: 0.209 mV; J12 return relative U9 power ground: 0.968 mV.

These are signed terminal drops, not isolated resistances or spatial hotspots. They identify paths worth checking in a newly bound layout. No independent copper reduction is called achievable here: that requires an actual routed candidate and a new source-bound field solve. The changed GND antipad on the later board makes reuse of these exact values inappropriate.

## Physical checks still required

1. Measure U7 effective voltage drop at the actual ~2 A aggregate ABC load, regulated input and component temperatures. Reserve part of the 53.586 mΩ combined limit for measured source/load/assembly drift; the maximum is not a recommended production target.
2. Measure U6 and U9 static pad voltages under the ranked loads at both endpoints, in their configured operating modes. Compare measured additional error with the separate/common budgets, without counting typical-only line/load slopes as guaranteed maxima.
3. Demonstrate sustained U6 mild-boost operation at the 5 V entry corner. The sweep reaches 2.000246 A output including passive demand and 3.660380 A through U5. The latter exceeds U5's 3 A RON test point; its programmed current limit and temperature still require evidence. U9's modeled maximum is 0.820000 A against its 1 A model cap.
4. Bound ripple, startup, load steps, switchover, source/cable/contact losses and thermal steady state. The classic DSM static reserve is only about 17.6 mV after the numerical guard. Check actual resistor and capacitor-body temperatures and post-assembly/lifetime drift; 105°C modeled copper grants no ambient or X5R-body allowance.
5. Verify USB configuration behavior separately. Its worst static current headroom is 42.872 mA against the declared 351.2 mA reference; the 4.3 V U9 accuracy condition, enumeration/inrush and dynamics are not accepted by that current screen.

## Portable reproduction boundary

See README.md for the compact packet commands. The unchanged circuit solver and deterministic case definitions can reproduce the endpoint/sensitivity calculations from the included sealed port matrices. The omitted original raw results are identified by SHA-256 in source-identities.json. Native geometry, mesh construction, loaded-field evidence and thermal/dynamic behavior cannot be reconstructed from this packet. No changed board, including candidate26, is qualified here.
