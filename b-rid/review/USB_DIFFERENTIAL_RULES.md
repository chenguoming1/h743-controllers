# USB differential-pair rules

## Scope and naming

USB copper is unchanged. Schematic labels and PCB nets use KiCad-recognized polarity suffixes:

| Previous net | Current net |
|---|---|
| `/USB_DP_CONN` | `/USB_D_CONN_P` |
| `/USB_DM_CONN` | `/USB_D_CONN_N` |
| `/USB_DP` | `/USB_D_P` |
| `/USB_DM` | `/USB_D_N` |

The existing `USB90` project pattern `/USB_D*`, 0.135 mm width, 0.150 mm differential gap, and 0.250 mm via-gap routing defaults are retained. The project settings are unchanged. R3/R4 split the connector-side and MCU-side net pairs. Pair-specific skew rules use `within_diff_pairs`, so the short MCU nets are not compared with the much longer connector nets.

## Enforced CAD limits

- USB90 track width: minimum, preferred, and maximum **0.135 mm**
- Nominal coupled gap: **0.145–0.155 mm**, preferred **0.150 mm**
- Connector pair net-total skew: maximum **1.500 mm**
- MCU pair net-total skew: maximum **0.250 mm**
- Remaining connector-region uncoupled length: maximum **7.500 mm**
- Remaining MCU-region uncoupled length: maximum **1.100 mm**
- Each breakout below has a separate uncoupled budget
- Independent opposite-polarity track-to-track clearance: minimum **0.145 mm**

The gap band is a CAD check tolerance, not a fabrication tolerance. These are regression guardrails for the existing compact full-speed USB layout. They do not independently prove manufactured impedance, USB timing compliance, or signal integrity.

### Finite breakout allowances

KiCad also checks short parallel fanout sections which intentionally cannot remain at a 0.150 mm gap. Later rules provide finite upper bounds in these local regions while retaining the 0.145 mm minimum and 0.150 mm routing preference:

| Region | Selection | Maximum gap | Uncoupled maximum |
|---|---|---:|---:|
| USB-C duplicated contacts and connector transition | Connector pair, F.Cu, both track endpoints in x115.6–117.9 / y114.4–117.0 mm | 1.775 mm | 3.600 mm |
| R3/R4 upper escape | Connector pair, B.Cu, both endpoints in x120.5–121.7 / y109.15–110.0 mm | 0.675 mm | 0.500 mm |
| MCU-side termination/via fanout | MCU pair, both endpoints in x120.3–121.7 / y110.3–111.8 mm | 0.575 mm | 1.100 mm |

Measured parallel breakout gaps reach 1.765, 0.665, and 0.565 mm respectively. The local 0.010 mm allowances preserve the existing full-speed escapes without adding unnecessary meanders. Remaining connector and MCU regions retain the narrow gap band and their own uncoupled budgets. Both endpoint coordinates are tested, so reversing a segment's drawing direction does not change membership. Reassess the boxes if the connector, resistors, vias, or MCU move. No new DRC exclusions or severity downgrades are introduced.

## Native measurement and gap-check behavior

Recorded KiCad 10.0.6 zero-budget diagnostic runs on copies reported:

| Native quantity | Connector pair | MCU pair |
|---|---:|---:|
| Net-total skew magnitude | 1.2648 mm | 0.1428 mm |
| Remaining-region uncoupled length | 7.2858 mm | 0.9428 mm |

The three breakout regions have uncoupled baselines of **3.3928 mm** (connector), **0.3642 mm** (upper termination escape), and **0.9697 mm** (MCU-side termination/via fanout). Separate budgets preserve roughly 0.13–0.22 mm headroom per region. These regional quantities are not additive through-path measurements or lengths of single continuous uncoupled runs.

KiCad 10.0.6 emits a differential-gap violation when the corresponding uncoupled budget is exceeded, or when no uncoupled constraint applies. An overly broad shared budget can therefore hide a bad gap. Each final breakout rule owns its uncoupled constraint; the remaining tight-gap regions have separate, closely bounded budgets. A real 0.200 mm trunk-gap mutation fails the final 0.155 mm rule. The independent 0.145 mm trace-clearance floor does not depend on uncoupled-budget exhaustion.

Maximum-gap checking still follows this native budget behavior: small local uncoupled deviations within the explicitly allowed regional headroom are tolerated. It is not a point-by-point impedance checker. [Official KiCad 10.0 differential-pair DRC implementation](https://gitlab.com/kicad/code/kicad/-/raw/10.0/pcbnew/drc/drc_test_provider_diff_pair_coupling.cpp)

## Full-path audit remains required

The connector nets include duplicated-contact branches and ESD interconnects. Their native net-total skew is not J1-to-U1 through-path skew. Ordinary net-based rules also do not sum through R3/R4. Retain the separate orientation-specific audit of the unchanged geometry:

- ESD-output-to-MCU copper centerlines: D+ **26.491449 mm**, D− **26.522086 mm**, mismatch **0.030636 mm**
- Complete A-contact orientation mismatch: **2.079364 mm**
- Complete B-contact orientation mismatch: **0.030636 mm**

These measurements exclude component interiors and equal via-barrel contributions. Historical evidence retains its original net names and revision hashes. The earlier engineering review explains why these full-speed timing differences do not justify added meanders. Both cable orientations still require hardware verification.

## Fresh final validation

The exact final rule file was freshly parsed and exercised by native KiCad **10.0.6**. The final integrated routing candidate produced **0 PCB DRC violations, 0 unconnected items, 0 schematic-parity issues, and 0 schematic ERC violations**. Existing project-level ignored check categories were retained.

Five isolated track mutations were detected with the final rules unchanged:

| Mutation | Required native error | Fresh result |
|---|---|---|
| Change one trunk track from 0.135 to 0.120 mm | `track_width` | 0.120 < 0.135 mm |
| Offset a 3.458 mm trunk segment outward by 0.050 mm, adding endpoint joins | `diff_pair_gap_out_of_range` | 0.200 > 0.155 mm |
| Offset that trunk segment inward by 0.010 mm, adding endpoint joins | `clearance` from the independent floor | 0.140 < 0.145 mm |
| Add an endpoint-preserving MCU detour of 0.400 mm | `skew_out_of_range` | 0.2572 > 0.250 mm |
| Offset the trunk outward by 0.600 mm, adding endpoint joins | `diff_pair_uncoupled_length_too_long` | 11.8081 > 7.500 mm |

All five mutation copies retained zero open connections. Some intentional mutations also produced other expected errors. They are not deliverable boards. A prior broad-budget trial did not detect the gap mutation; this led to the final separately scoped budgets.

The final USB rule file was restored byte-for-byte (SHA-256 d779e853f441fd6e3f428f87fb999d49a4067fc04477563ea17a8b18a2b7a7a8), then integrated with the power rules. All five negative cases above were rerun on copies of the final integrated board after fresh native validation. See `evidence/routing-cleanup-20261007/usb-negative-tests.json` and `CURRENT_REVISION.md`.

The rename modifies only the four quoted net/label names. USB track geometry, pads, vias and return paths are preserved. The test copies are not deliverable boards.

[Official KiCad 10 PCB Editor manual](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html): differential-pair naming and routing; custom `track_width`, `diff_pair_gap`, `diff_pair_uncoupled`, and `skew` constraints; `within_diff_pairs`; series-component path boundaries. Net-class values are routing defaults; explicit custom constraints provide bounds.
