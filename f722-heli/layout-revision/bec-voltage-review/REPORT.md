# TPS63070 BEC source-voltage scope

Source-only review, 2026-10-09. The fixed U6/R54/R55 BOM and acceptance thresholds are unchanged. No board, firmware, numerical plan or solver was changed or run. These calculations qualify the meaning of the source terms; they do not accept a completed-board rail.

## What the IC specification supports

[TI TPS63070 Rev. B, section 7.5, pp.6–7](https://www.ti.com/lit/ds/symlink/tps63070.pdf#page=7) gives:

- PWM feedback accuracy: MIN −1%, MAX +1%, PS/SYNC=GND. The table header spans VIN=2–16 V and TJ=−40…125°C; typical values use 25°C. No load-current test point is stated for the accuracy row.
- Line 0.07%/V and load 0.2%/A regulation are TYP only, with power-save disabled. Neither has a guaranteed maximum.
- Feedback leakage: MAX +100 nA at VFB=0.8 V; no negative limit is printed.

The 0.792–0.808 V feedback corner therefore already has the table's IC-temperature and input-voltage scope. It is not merely an initial 25°C IC tolerance. [TI's accuracy clarification](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1275607/tps63070-output-voltage-accuracy-of-tps63070) explicitly confirms the full-temperature guarantee. Adding another generic IC-temperature allowance would double count. The existing extra 0/1/2% rows remain engineering sensitivities; typical line/load slopes do not justify mandatory additional guaranteed percentages. Conversely, absent load-test detail and board qualification do not support a complete all-load board-rail guarantee.

## Resistor and component temperatures

The exact BOM specifies U6 TPS63070RNMR, R54 RT0402BRD0753K6L and R55 RT0402BRD0710KL. The fitted divider is 53.6 kΩ/10 kΩ. [YAGEO RT, pp.2 and 5–7](https://yageogroup.com/content/datasheet/asset/file/PYU-RT_1-TO-0-01_ROHS_L#page=5) confirms ±0.1%, ±25 ppm/°C, −55…155°C operation for RT0402, and power derating above 70°C. TCR tests use 25/−55°C and 25/+125°C. [The exact R55 sheet](https://www.yageogroup.com/component-documentation/download/specsheet/RT0402BRD0710KL) agrees. No matched-ratio tracking is specified. Nominal R54/R55 dissipation is 0.343/0.064 mW.

C55/C56/C57 are GRM21BR61A476ME15L. [Murata's selected-part record](https://ds.murata.com/simsurfing/mlcc.html?oripartnumbers=%5B%22GRM21BR61A476ME15L%22%5D&partnumbers=%5B%22GRM21BR61A476ME15%22%5D&rgear=jomoqke&rgearinfo=de&videoId=5970368750001) identifies X5R, −55…85°C. Modeled 105°C copper neither establishes component-body temperatures nor permits 105°C capacitor bodies. The resistor-temperature scenarios below impose no user ambient-temperature requirement.

## Reproducible conditional bounds

Use R=Rnom×(1±0.001)×(1±25×10⁻⁶×|Tbody−25|), independent adverse signs, and V=VFB×(1+R54/R55). This is a stated TCR magnitude model, not a measured temperature curve. Nominal setpoint is 5.088 V.

| Resistor-body assumption | Reference/divider only, V | Upper value with +100 nA endpoint, V |
|---|---:|---:|
| 25°C | 5.028638–5.147550 | 5.152916 |
| 85°C | 5.015947–5.160589 | 5.165962 |
| 105°C sensitivity | 5.011726–5.164943 | 5.170320 |
| Conditional interval −40…85°C | 5.014892–5.161677 | 5.167051 |

The interval row uses the cold endpoint's 65°C departure from 25°C. It is optional scope arithmetic, not an adopted operating envelope. IC feedback bounds are unchanged in all rows.

Positive leakage into FB raises the external-divider setpoint by IFB×R54. This effect is separate from feedback-node accuracy. The +100 nA column conditionally applies the printed endpoint, whose test condition is VFB=0.8 V. TI does not print a signed ±100 nA guarantee. The JSON also retains a clearly labeled −100/+100 nA engineering sensitivity; its lower endpoint must not be reported as manufacturer-guaranteed.

## Consequence for the 5–12.6 V review

These are conditional source/divider bounds, not voltages at U6 power pads or receiver pads. Local IC input voltage must remain in range, the regulator must remain in regulation, and actual feedback/ground copper must be solved. Do not add typical slopes as guaranteed maxima or count the same IC temperature effect twice.

Remaining evidence includes component temperatures, sustained near-2 A mild-boost operation at the low-input corner, effective capacitance and loop stability, ripple/transients/startup, mux behavior, and assembly/lifetime drift. YAGEO's endurance and soldering tests allow changes beyond initial tolerance; initial-plus-TCR arithmetic is not lifetime or post-assembly qualification. Numerical convergence and board-pad acceptance remain separate. No unconditional receiver-pad low/high guarantee over 5–12.6 V is established here.

## Packet identity and verification

`selected-bom.json` preserves exact selected entries from repository-relative `f722-heli/layout-revision/hardware/parts.json`, SHA-256 `99e1589baf2033bc696613ad52c5deab3403397d7caafff6d8aa011296846858`. Evidence-file strings inside those entries are preserved BOM metadata, not a claim that those files were independently revalidated here. `sources.json` records primary links, editions and access scope. No full PDF, private path or simulation result is included.

From this folder:

```sh
python3 calculate_bounds.py --check
```

To also check the original BOM, add `--bom PATH_TO_parts.json`. Without `--check`, the script regenerates `bounds.json` and `manifest.json` deterministically. It uses only Python's standard library, performs no network access, and cannot edit the BOM or board. The manifest hashes all five other packet files; its own hash is supplied at handoff.
