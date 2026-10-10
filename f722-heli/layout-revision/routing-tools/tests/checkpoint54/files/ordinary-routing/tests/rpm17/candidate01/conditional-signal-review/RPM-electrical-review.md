# RPM input: source-bound conditional electrical review

The native RPM input is geometrically complete and the actual U13.6 clamp cut passes. Electrical, waveform, EMC and transient qualification remain **NOT_QUALIFIED**. This review supplies conditional loading and return context for the longer route; it does not establish compatibility with an unspecified ESC or encoder.

Board: `73dbae05954b8edec4143d91248bf38c40537f83e8f5f3fed51744105169d6c7`.
Source SERVO15: `755545e8198e9a3649c0e07533c23e67010d91ab6a8b09556d7463e064ac89eb`.
The change adds 19 tracks and five ordinary 0.45/0.20 mm tented through vias on RPM_MCU. All source copper, 156 full footprint records and 558 pad records are retained. Native normal/all-track/parity DRC reports 14 opens, zero errors and zero warnings. Remaining opens are elsewhere.

## Actual topology and route length

Current native pads, schematic parity and firmware binding give the following path:

J7.3 RPM_EXT → R25 (470 Ω, 1%) → RPM_HV → U16.1 protection → Q1.3 drain. Q1 is BSS138LT1G, with Q1.1 gate on +3V3_CORE and Q1.2 source on RPM_LV. R36 (4.7 kΩ, 1%) pulls RPM_LV to +3V3_CORE. RPM_LV reaches R39.1; R39 (220 Ω, 1%) feeds R39.2 RPM_MCU → U13.6 → U1.16 (PA2, FREQ input). U13.2 is GND and U13.5 is +3V3_CORE. The native pin assignments, rather than historical pin-reassignment prose, bind this review.

| Native endpoint graph walk | Planar track length | Vias |
|---|---:|---:|
| J7.3 → R25.1 | 2.091318 mm | 0 |
| R25.2 → U16.1 | 7.151030 mm | 0 |
| U16.1 → Q1.3 | 4.352278 mm | 0 |
| Q1.2 → R39.1 | 32.069220 mm | 1 |
| R36.2 → R39.1 | 25.930222 mm | 1 |
| R39.2 → U13.6 | 1.559848 mm | 0 |
| U13.6 → U1.16, all new | 57.886227 mm | 5 |

These are saved track-centerline endpoint-graph lengths, including entries into lands. Package internals, distances within pads and vertical via travel are excluded. They are not claimed as unique or shortest physical paths: an In2 track also contacts the bridge via land before its explicit endpoint, and the long final In3 approach contacts the MCU via land before the route doubles back into it. These same-net midsegment contacts are preserved and recorded separately, with overlap areas 0.0116564 and 0.0378429 mm². All associated copper is included in loading inventory; no extra contact bypasses U13.6. The native RPM_LV inventory is 32.336202 mm, including its pull-up branch; RPM_MCU is 59.446075 mm total. Q1.2 → R39.1 plus the entire RPM_MCU inventory is 91.515294 mm of planar signal copper on either side of R39, excluding its component body. The longest new B-side leg is 36.531550 mm around the west/top perimeter. Layer inventory and exact UUIDs are retained in `RPM-path-topology.json`.

Removing only actual U13.6 pad copper separates R39.2 from U1.16; both resulting branches reach the removed pad boundary. Minimum outside-pad gap is 0.155348 mm against the unchanged 0.127 mm rule. All 19 source passing protection cases survive and RPM raises the actual cases to 20/22. This proves clamp-first copper topology, not ESD waveform performance.

## Loading and timing sensitivity

The added path uses B.Cu, In2.Cu and In3.Cu on the unchanged six-layer 1.0324 mm stack. The five active via transitions span 1.9948 mm between the used copper center depths in total. All five complete through-barrels remain physically present; five full board depths total 5.162 mm. These geometric quantities do not establish via capacitance or unused-barrel resonance.

For the 57.886227 mm added planar inventory treated as one ideal line, an assumed effective permittivity of 2.8–4.4 gives a one-way delay sensitivity of 0.323–0.405 ns. The actual same-net overlaps mean this is not an extracted propagation delay. Assuming 40–100 Ω local characteristic impedance and the lossless relationship C = delay/Z gives 3.231–10.126 pF added trace capacitance. These are sensitivity assumptions, not extracted impedance or upper/lower manufacturing bounds. The relationship is the standard lossless line relation discussed in TI's [Design Considerations for Logic Products, section 6-7](https://www.ti.com/lit/an/sdya018/sdya018.pdf#page=449).

Separate assumed via allocations of 0.15, 0.30 and 0.60 pF per via add 0.75, 1.50 and 3.00 pF respectively. Combined new trace-plus-via allocation spans approximately 3.98–13.13 pF across these declared scenarios. A field solver or a validated via model is required to replace those assumed allocations. They omit the existing LV/HV branches, pads, device capacitance and any measurement probe.

The STM32F722 data sheet gives 5 pF typical I/O capacitance without a maximum; tested CMOS level bounds are 0.3×VDD low and 0.7×VDD high. Its output-drive OSPEEDR timings do not describe this input's externally produced edge. [ST DS11853 Rev 9, table 61](https://www.st.com/resource/en/datasheet/stm32f722re.pdf#page=143)

U13's USBLC6-4 I/O-to-GND capacitance is 3 pF typical, 4 pF maximum at 1.65 V; I/O-to-I/O capacitance is separately specified and neighboring activity can contribute coupling. The 4 pF figure is not an all-bias, assembled-node bound. [ST USBLC6-4, table 2](https://www.st.com/resource/en/datasheet/usblc6-4.pdf#page=2)

Q1 capacitance is nonlinear. BSS138LT1 specifies Ciss/Coss/Crss of 40/12/3.5 pF typical and 50/25/5 pF maximum at 25 V, zero gate bias and 1 MHz. Those test conditions do not bound the low-voltage translator trajectory. Its 10 Ω maximum on-resistance is specified at VGS = 2.75 V, ID < 200 mA and −40 to +85 °C; it cannot be applied throughout turn-on or release. [onsemi BSS138LT1, electrical characteristics](https://www.onsemi.com/pdf/datasheet/bss138lt1-d.pdf#page=2)

Once Q1 releases, a first-order sensitivity places an assumed total LV-plus-MCU capacitance behind R36(max) + R39(max) = 4969.2 Ω. This is a conservative placement of that declared capacitance for a passive lumped model; it does not bound unmodeled Q1 turn-off, coupling, leakage, internal pull configuration or a missing load allocation. Using t10–90 = ln(9)RC and t70% = −ln(0.3)RC gives:

| Assumed total load | 10–90% rise | Time to 0.7×VDD | Single-pole −3 dB frequency |
|---|---:|---:|---:|
| 25 pF | 0.273 µs | 0.150 µs | 1281 kHz |
| 50 pF | 0.546 µs | 0.299 µs | 641 kHz |
| 100 pF | 1.092 µs | 0.598 µs | 320 kHz |
| 200 pF | 2.184 µs | 1.197 µs | 160 kHz |

The 100 pF case is an engineering budget already used in the local HV input review, not a verified maximum. A valid budget must include existing LV trace and pads, Q1's source-side loading, U13, MCU, new trace/vias, coupling, assembly variation and probing. No RPM bandwidth is accepted from this table alone.

Falling edges depend on the unknown external output's low level and impedance, the harness, R25 (up to 474.7 Ω), Q1's bias-dependent conduction and R39 (up to 222.2 Ω). R36's pull-up also creates a low-state divider with the effective sink. Without the external source and cable model, neither falling time nor VIL margin is established. An open-drain external source with a weak pull-up and a capacitive cable can also determine release timing before Q1 disengages. The HV protection and translator ratings are not evidence of arbitrary cable or source compatibility.

Mechanical pulse repetition and edge rate are different quantities. Pulse frequency depends on events per revolution, RPM, gearing and encoding; if P is pulses per measured revolution, f = P×RPM/60. Minimum high/low duration and the firmware capture/filter configuration must be established separately. Even slow repetition can contain a fast edge. The calculated board flight time is much shorter than the illustrative RC rises, but this does not prove ringing, crosstalk or EMC behavior, especially for externally imposed falling edges and the cable.

## Exact saved return geometry

The current filled-plane projection covers every RPM_MCU centerline outside the explicitly reported own-via windows. Raw totals are 4.263894 mm centerline missing inside those windows and 0.614904153 mm² missing finite-width projection overall. The raw whole-width outside-window pass remains **false**.

One actual new In4 fill wedge lies under the edge of In3 track `d668f229-cdb8-5ebf-a199-7db95d300761`, from (15.336486, 7.938185) to (15.130631, 11.415217). Its area is 0.00002725130554532544 mm², bounds x15.195108–15.204501 / y9.245985–9.255039 mm. It has zero intersection with drills, lies at least 0.053928 mm from the centerline, and was wholly covered by source15's plane. It belongs to the merged saved hole containing the new RPM via (15.079367, 9.594711) and existing SERVO3 via (14.85, 9.06). This is a real local width-only loss from refill, not numerical zero. Its exact polygon and source/current comparison remain in `RPM-return-context.json`; no contour normalization, tolerance waiver or functional-failure claim is made from its size alone.

| RPM via | Signal transition | Reference change | Nearest GND tie bonded to both planes |
|---|---|---|---:|
| (13.21, 23.02) | B ↔ In2 | In4 ↔ In1 | 2.413229 mm |
| (9.013184, 20.66732) | In2 ↔ In3 | In1 ↔ In4 | 1.459780 mm |
| (4.844794, 17.894794) | In3 ↔ B | In4 on both | 1.480353 mm |
| (14.906568, 6.34672) | B ↔ In3 | In4 on both | 1.675934 mm |
| (15.079367, 9.594711) | In3 ↔ B | In4 on both | 0.633534 mm |

These GND ties have positive finite land contact to both saved planes after drill subtraction. Distances are Euclidean context, not actual return-path length or inductance. No dedicated GND transition via was added. The two reference-plane changes, five antipads and width wedge therefore remain explicit AC-return review items even though DC support continuity and geometric centerline coverage pass. All 28 support groups are preserved. Critical reference objects and every reported numeric delta are exact, with zero lost-GND overlap against critical trace width; the whole GND planes do change.

## Conditions before electrical release

Confirm the real ESC/encoder output topology, voltage, pull-up or source impedance, cable capacitance and ground connection; derive required pulse-high/low times and capture filtering from its encoding. Bound or extract the actual LV/MCU loading and via/return behavior. Check both logic margins and captured edges on the assembled board with representative harness and temperature, accounting for probe loading. Review ESD/clamp rail returns and transient behavior separately. Fresh current-source power/VCAP analysis is still required after the five new antipads. None of these electrical or manufacturing qualifications is asserted by the geometric closure.

Reproducible calculations, path UUIDs, pad identities, exact residual and return ties are in the three adjacent JSON receipts, generated by `review_rpm_context.py`. Raw native/reference reports are retained one directory above.
