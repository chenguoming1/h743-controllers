# Nexus stage10 component placement and local-loop audit

15 October 2026. Read-only. **Do not release for fabrication/assembly or flight on the strength of zero DRC.** The most important newly identified concerns are the MCU VCAP connection, the 5 V buck's input/switch/sense routing, and dispersed IMU bypass capacitors. These are verified layout facts and engineering recommendations; this review does not claim measured instability, noise, overheating or a new electrical open.

## Source and method

Reviewed current hardware, not older root hardware: [immutable current project](https://github.com/chenguoming1/h743-controllers/tree/3b84f587f226267f5e8269aa5be3a8977103bf36/nexus-style-fc/routing-wip/current/hardware).

- Main SHA-256: `2099ceb9ff904859a68e288683ee68b2ad74d7741b8b670341baf67bf67e1ea3`
- Child SHA-256: `bfec2a120fbda6c97c1f8a36dfff6a35337e13ab1c3af63abb987f529d761403`
- Main schematic SHA-256: `7bfd6617e7d0285c738615fd2b6d7b6d6958675c095e50de87a8ed44111b972b`
- KiCad 10.0.7 read-only extraction, pad/net/track/via contact checks, and reuse of exact-source native/physical receipts. Stage10's saved comparison proves copper, fills, placement and geometry unchanged from stage08. No edits, saves, refill, new DRC run, upload or GitHub write.

Route numbers below are **full-segment sums along physically contacting track/pad/via witnesses**, excluding pad-internal travel and via barrel length. They are not trimmed pad-edge shortest-path lengths, resistance/inductance extraction, or worst-case measurements. Long complete segments can include pad overlap or overhang. All six conductive zones are GND, so no supply-plane shortcut is omitted for VCAP, 3V3_SENS, 3V3, VX or VSYS. The local GND plane does matter: relevant GND pad centers are inside saved fill, and existing complete native/return receipts support conductive returns. Ground center inclusion does not prove the shortest return, plane neck impedance, or loop inductance. A missing track-only ground witness is not an open.

`critical-paths.png` is an annotated projection of actual extracted copper, not a simulation or a proposed layout. Background layers are overlaid and ground fills are omitted for visibility.

## Priority 1: MCU core capacitor and local decoupling

**Confirmed geometry:** C9 is 4.7 µF on F.Cu while U1 is on B.Cu. C9.1→U1.30/VCAP traverses 13.90 mm of complete 0.127 mm segments and three vias across F/B/In2/In3. It loops away from the two parts. C9 GND and MCU GND have filled-plane attachment; the supply leg itself is nonlocal.

**Recommendation:** make C9 and its return a compact, direct VCAP loop at U1.30/U1.31, preferentially on the MCU side if assembly and neighboring copper permit. Preserve the correct capacitor value and qualify its exact part. This is a high-priority layout correction candidate, not proof the MCU fails.

For the exact STM32F722RET6 LQFP64, ST DS11853 Rev9 §6.3.2/Table19 (printed p105) specifies 4.7 µF and capacitor ESR between 0.1 and 0.2 Ω. The table does not state an ESR test frequency. C9's exact manufacturer frequency-dependent ESR/effective capacitance has not been qualified here. Do not infer compliance from “ceramic,” and do not insert a series resistor without a separate design review. [Exact MCU datasheet](https://www.st.com/resource/en/datasheet/stm32f722re.pdf)

C1 is physically near U1.19 but its actual supply witness is 33.13 mm/two vias. Testing all ten 3V3 capacitors found the smallest complete-segment witness to U1.19 through C7, 13.31 mm/two vias. Thus C1's near-looking center is misleading. Other observed VDD legs are much better: C4→U1.64 1.65 mm/no vias; C3→U1.48 3.75 mm/no vias; C6→VDDA/U1.13 1.43 mm/no vias. C2→U1.32 is 7.36 mm/one via. Review U1.19 and U1.32 first, without indiscriminately moving all bypass capacitors. ST recommends local, low-impedance bypass connections for each power pair. [STM32F7 AN4661 §§6.4/8.3](https://www.st.com/resource/en/application_note/an4661-getting-started-with-stm32f7-series-mcu-hardware-development-stmicroelectronics.pdf)

## Priority 1: 5 V buck U5, C21/C22, L1, C24 and feedback

**Confirmed geometry:**

| Connection | Full-segment witness | Transitions | Observation |
|---|---:|---:|---|
| C21 input→U5 PVIN11 | 10.69 mm | 2 vias | B/In2; includes 0.127 mm input copper |
| C22 input→U5 AVIN10 | 8.83 mm | 2 vias | B/In2; shares remote supply network |
| U5 SW1→L1.1 | 11.76 mm | 2 vias | 0.50 mm B/In3 switching route |
| U5 VOS14→C24.1 | 15.54 mm | 2 vias | B/In2; 0.127/0.50 mm segments |
| U5 FB5→R11.2 | 4.62 mm | none | B.Cu 0.127 mm |

**Recommendation:** regroup U5's input capacitor, inductor and output capacitor as one compact power cell, with a short quiet VOS takeoff at output capacitance and a compact feedback divider/AGND return. Existing topology puts high-di/dt and high-dv/dt paths across multiple layers. The 6.667 mm of 0.127 mm inner input-route copper is particularly undesirable as a local switching-capacitor connection. There is no universal published maximum route length, so these dimensions do not establish an absolute specification failure by themselves.

TI requires a common direct AGND/PGND/EP/system-ground connection, a separate short VOS sense route, and compact low-impedance current loops. Native evidence shows AGND/EP contact and PGND attachment through B.Cu copper/fill; do not call grounds disconnected. EP soldering and the existing paste-overlapped drill remain process gates. [TPS62130 §11](https://www.ti.com/lit/ds/symlink/tps62130.pdf)

## Priority 1: IMU local bypass and functional disposition

U2 pin8 is VDD and pin5 is VDDIO; both are 3V3_SENS. C13 100 nF→VDD has a 4.25 mm/no-via witness. **C13 also serves VDDIO** through the same rail: 6.74 mm/no vias; VDD→VDDIO is 2.49 mm/no vias. Therefore it would be wrong to say VDDIO has no bypass or that the only bypass path is 33 mm.

The intended additional capacitors are dispersed: C14 2.2 µF→VDD is 22.80 mm/three vias; C15 10 nF→VDDIO is 33.63 mm/four vias. These branches are not electrically absent, but should not be credited as equivalent to a compact local bypass cluster. All relevant capacitor/IMU ground pads have saved-fill attachment. No rail impedance or noise spectrum has been extracted.

**Recommendation:** place the C13/C14 VDD pair and C15 VDDIO bypass at their respective pins with short local ground returns, while preserving room for IMU assembly, avoiding regulator switching-current corridors, and checking exact capacitor technology/effective capacitance. TDK's operating circuit specifies 100 nF + 2.2 µF for VDD and 10 nF for VDDIO. [TDK official datasheet, §§4.1–4.3](https://invensense.tdk.com/wp-content/uploads/2020/04/ds-000347_icm-42688-p-datasheet.pdf)

**Unresolved functional gate:** pin9 INT2/FSYNC/CLKIN remains NC. Unused-FSYNC grounding guidance must be reconciled with the selected pin role and firmware; reset INT2 behavior means blindly grounding it is not a safe generic correction. Package→board→vehicle axes and firmware alignment also remain unverified. These are distinct from component placement.

## Priority 2: crystal, reset and analog filtering

Y1→MCU oscillator legs are 4.80 mm and 2.53 mm, both B.Cu/no vias. However C11→OSC_IN is 6.17 mm/no vias and C12→OSC_OUT is 10.36 mm/two vias. C12's ground leg to Y1 ground has a 1.38 mm B.Cu witness plus parallel fill. **Recommend putting the load capacitors on their matching oscillator-node sides and shortening the C12 detour**, rather than assuming both are local because their centers flank Y1. The two 30 pF values with a 20 pF crystal imply 15 pF series load plus parasitics; actual load, ESR, drive level and startup margin require the exact crystal data and validation. AN4661's typical capacitor range is not a blanket prohibition of 30 pF.

C10 reset capacitor→U1.7 is 11.28 mm/two vias through B/In3. Recommend a more direct reset bypass connection at NRST. C29 VX-sense filter→ADC pin9 is 5.99 mm/one via; C30 5V-sense filter→ADC pin10 is 11.32 mm/two vias. Recommend clustering dividers/filter capacitors at their ADC inputs with a quiet reference return, keeping the high-impedance filtered nodes away from SW and digital clocks. ADC sampling time, divider impedance and measured noise are not qualified. [ST clock/decoupling guidance](https://www.st.com/resource/en/application_note/an4661-getting-started-with-stm32f7-series-mcu-hardware-development-stmicroelectronics.pdf), [MCU NRST recommendation, Fig47](https://www.st.com/resource/en/datasheet/stm32f722re.pdf)

## Already improved, still unqualified

**U10 TPS70933:** EN is intentionally floating, C19 is the approved 10 µF, and output routing is now front-side with no vias. Current witnesses: output 3.74 mm (includes 0.1874/0.25 mm sections), C19-GND→U10-GND 1.92 mm/no vias plus fill. C18 input remains remote: 29.15 mm/three vias in this witness. TI does not require an input capacitor for stability; the remote input is a transient/PSRR/local-bypass concern, not an established stability violation. Preserve the corrected output and evaluate input waveforms/PSRR before an intrusive move. Exact effective C19 capacitance/ESR, startup and load-step tests remain needed. **Width correction:** historical descriptions of an entirely 0.250 mm output route do not describe current stage10. Two actual F.Cu output items are 0.1874 mm wide (approximately 1.609 mm and 0.229 mm long). This is a real copper-width observation, not a path-summing effect, and does not by itself establish a fault. [TPS709 §§8.1.1/10](https://www.ti.com/lit/ds/symlink/tps709.pdf)

**U14 TPS629210:** approved C27/C31 22 µF/25 V parts and capacitor-local EN star are retained. The established pad-center axis metric is 9.401 mm/two vias for C27→VIN; this audit's 8.999 mm full-segment contact metric excludes pad-internal portions and is not a contradiction. C31 shares this feed. C28→VOS is 4.43 mm/no vias, SW→L2 is 3.55 mm/no vias. Final saved plane-attachment receipts resolve the earlier proposal's missing return proof. They do not establish low HF impedance. Prioritize more local VIN/GND geometry if redesigning the power cell; retain the approved pair until a full effective-capacitance replacement is qualified. TI specifies ≥3 µF effective input capacitance and close VIN/GND connection. [TPS629210 §§7.3/11](https://www.ti.com/lit/ds/symlink/tps629210.pdf)

## USB/ESD

U7 is near J6 and on B.Cu; actual connector-side witnesses are asymmetric: J6.A7→U7.1 about 2.60 mm/one via; J6.A6→U7.3 about 6.45 mm/two vias. C25→U7 VBUS is 3.21 mm/no vias. U7 ground has direct saved B.Cu fill and a track/via witness to connector GND, so it is not an ungrounded clamp. Prefer compact connector→protection→MCU flow, with short VBUS and ground paths and continuous return through transitions. ST explicitly warns that lead/ground parasitics increase clamping voltage. [USBLC6-2 §2.3](https://www.st.com/resource/en/datasheet/usblc6-2.pdf)

The full MCU-side USB path was not independently reconstructed by this audit's simple contact graph; use the existing full native path/return receipts. No USB open is inferred. Actual-stack impedance, transition/reference discontinuities, both Type-C orientations and ESD performance remain unverified. This is the integrated 12 Mbit/s FS path, not a demonstrated HS implementation.

## Assembly/mechanics and published child

- The automated JLC U10 pin/pad/overlap findings are **unresolved model/rotation/land-pattern reconciliation**, not yet a verified physical placement fault. Do not rotate or resize U10 solely from the automated label.
- Sixteen ordinary drills overlap 17 pasted contacts. Tenting flags do not ensure a sealed barrel in an open component pad; source-bound assembler treatment is still needed, particularly U5 EP and two-sided J2/C24.
- D5 has zero guaranteed minimum standoff over an under-body via. C27 also has under-body vias. Qualify tent topography, solder balls, seating and coplanarity; moved D5 is not by itself proof of clearance.
- Child/main fit remains conditional on actual finished slot/tab/radius/pitch/copper registration. Nominal fit is not assembly registration or structural strength. Verify access for seating, tack soldering, inspection, mating cables and the underside C27/C31 envelope.
- Child J1 is through-hole; accepted BOM/CPL does not qualify SMT reflow or hand/selective-solder access. The 0.55 mm nominal outer rail needs handling/mating/vibration qualification.
- Published child still has the shared 0.50 mm VX daisy-chain to the four left servo outputs; dual right-side feeds do not bypass it. Header contact and lost-feed current limits remain open. The ongoing proposed child redesign is **not** included in this as-is result.

## Classification and next action

**Confirmed physical/layout facts:** the above nonlocal capacitor/switch/sense routes, actual values/nets/layers, retained paste/drill overlaps, NC multifunction pin, child common feeder and source-defined mechanical margins.

**Recommended corrections:** compact VCAP/VDD19 loops; compact U5 power cell; local IMU bypass cluster; shorten C12/NRST/ADC-filter loops. A bounded placement plan should be prepared first because moving one part can break another return, assembly envelope or signal corridor. No specific move has been proven routable here.

**Unverified gates:** exact C9 ESR/capacitor corners, waveform/noise/thermal tests, actual return impedance, crystal margin, IMU pin-role/axes/firmware, U10 DFM cause, final assembly process, current envelope and finished-parts fit. None is a pass just because native DRC is zero.

**No new proven numerical datasheet-limit violation or measured malfunction is asserted in this audit.** The routing departures are substantial enough that production release should stay blocked pending a focused power/decoupling placement review and the existing qualification gates.
