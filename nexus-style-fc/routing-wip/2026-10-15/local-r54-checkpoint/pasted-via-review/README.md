# Nexus inherited pasted-via review

## Result and limits

The exact r53 board has **18 through vias contacting 19 pasted SMD pads**, all on the same net: **1 exposed-thermal-pad via, 6 capacitor/supply vias, 3 signal vias, and 8 other ground-return vias**. The double contact is one via shared by F.Cu J2.5 and B.Cu C24.2. These are inherited assembly risks, not 19 electrical shorts. **No manufacturing remedy is qualified or applied.**

Source: `r53-cc2-bend/hardware/nexus-style-fc.kicad_pcb`, SHA256 `3e0795a336cb3fd461b4c5a80025cc676028986f0b467ef331c10f505da8f842`. Source hashes, exact UUIDs, native-text pad geometry, all directly touching same-net tracks/pads, fixed track endpoints, plane-fill memberships and per-via next investigations are in `per-via-review.json`. All vias retain 0.45 mm lands / 0.20 mm drills. Static analytic shapes reproduce the sealed native contact totals; all 356 pad positions and orientations match archived native measurements. No KiCad process, route solver, PCB edit or publication was performed by this review.

The contact metric is the drill circle against the copper shape of an SMD pad with a paste layer, including partial overlap. It is not a final Gerber/CAM assembly test. The affected pads also expose their mask layers without local paste/mask reductions. Native refill, mask/paste export and manufacturing qualification remain separate gates.

## Exact affected locations

Coordinates are board-global millimetres. Complete identifiers and source-node hashes are in the JSON.

| Via centre X,Y | Net | Pasted pad(s) | Function and additional direct donors |
|---|---|---|---|
| 121.075,106.925 | 3V3 | C3.1 | MCU pin48 decoupling feed; B/In3 0.25 mm branches |
| 119.975,116.375 | GND | J3.6 | Connector mounting ground; F.Cu return track |
| 101.825,123.725 | GND | J4.6 | Also touches B.Cu C27.2 buck-input return |
| 119.975,122.375 | GND | J5.5 | Also touches B.Cu C20.2 flash decoupling return |
| 105.575,130.925 | GND | J6.B12 | USB connector ground; F.Cu return track |
| 109.875,109.425 | GND | C19.2 | Approved LDO output-capacitor return |
| 101.975,116.375 | GND | J2.5 + C24.2 | Connector ground and 5V buck-output return; F/B tracks |
| 101.975,117.575 | GND | J2.5 | Separate connector-ground via |
| 112.875,112.075 | GND | U2.10 | IMU ground, three F.Cu track contacts |
| 113.225,126.975 | GND | R14.2 | Power-mux PR1 divider reference |
| 105.725,106.625 | GND | U11.2 | ESD/clamp ground; also B.Cu C21.2 buck-input return |
| 117.575,124.775 | GND | C26.2 | 5V bus bulk-capacitor return |
| 112.825,109.975 | GND | C9.2 | MCU VCAP_1 return |
| 102.675,108.225 | GND | U5.17 | Buck thermal pad; also U5.6, C15.2 and six tracks |
| 109.775,118.025 | RPM | U1.16 | MCU signal; two In3.Cu donors |
| 112.825,107.275 | 3V3_SENS | U3.6 | Barometer VDDIO; F/In2 0.25 mm branches |
| 109.975,111.575 | SPI1_MISO | U2.1 | IMU signal; two In2.Cu donors |
| 120.125,114.075 | I2C1_SCL | U1.61 | MCU signal; B/In2 0.127 mm branches |

## Bounded routing-only candidates

Two modest candidates pass the static checks described below:

- **J6.B12:** move `3cfc0b66-fb89-4bcd-8fd4-b8f8542b90a3` to **105.175,130.925**; retain existing tracks and add a **0.45 mm F.Cu segment** from the old centre to the new centre.
- **J2.5, separate lower via:** move `7f89653b-c07a-4bb7-8d55-49a1f1873aa3` to **101.975,117.825**; add the same full-land-width F.Cu connection from its old centre. Keep the other J2/C24 via separate and unchanged.

The rounded old endpoint of each 0.45 mm segment replaces the original via’s full F.Cu land area, preserving every original direct pad/track contact without narrowing. Proposed lands and segments have no fixed unrelated-copper obstruction below 0.127002 mm; lands clear pasted drill contacts, 0.25 mm hole-to-hole spacing and 0.3 mm copper-to-edge spacing. The proposed centres remain in source GND fill on all six layers. This is **not** a finite-width plane-path, EMI or fabrication certificate. Native refill/DRC, full donor validation, USB/connector return checks, and mask/paste inspection are still required. See `simple-routing-only-options.json`.

Eight finite conservative land probes per via were checked using a 0.100 mm pad-to-land copper separation study target. This target is a review choice, not a JLC rule. For the remaining 16 vias, no complete function-preserving routing option was proved. A clear land alone is insufficient: for example J5’s 2.03 mm distant candidate has no proven C20 decoupling-return path. Exact obstacles and smallest next investigations are retained in the JSON. This finite probe set does not prove routing impossible.

## U5 thermal via: ordinary tenting is not automatically disqualified

U5’s via is the only GND via within **2 mm copper-edge distance** of its exposed pad. It also supports U5.6 AGND, opposite-side C15 IMU decoupling, and six track contacts. Removing it, substituting a thin remote trace, or preserving only net connectivity cannot establish equivalent thermal/return function.

The source enables front/back tenting and disables covering, plugging, filling and capping. U5.17 has one continuous B.Cu/B.Mask/B.Paste custom shape. Its opening reaches **Y=108.200011**; the via drill spans **108.125–108.325**, overlapping the opening by **0.075011 mm**. A global tenting flag alone therefore does not demonstrate a component-side mask barrier over this partially overlapping hole. This is a source-geometry inference; exported mask/paste and CAM review must establish the actual result. [KiCad 10 mask/paste semantics](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html)

**Smaller hole-only relocation was also tested**, separately from the conservative annulus-outside-pad criterion. With an exploratory **0.05 mm hole-to-opening allowance** (not a fabrication tolerance commitment):

- At **102.675,108.350011**, EP17 clears by 0.05 mm, but the drill overlaps U5.6’s opening by 0.073128 mm and VSYS copper clearance is only 0.095744 mm.
- At **102.900,108.350011**, all source openings clear the drill by at least 0.05 mm and the via land still overlaps EP copper by 0.075 mm. However, the land intersects VSYS track `79c2d0d0…` by 0.129242 mm and FB_5V/U5.5 by 0.065465 mm.
- At **102.400,108.350011**, C15.2’s opposite-side opening and SW_5V copper block the move.

All nine bounded probes were rejected; no complete donor/thermal route is claimed. See `u5-bounded-small-shift.json`. The next routing-only step would be a coordinated local copper transaction preserving the thermal barrel and every listed donor, followed by thermal/return assessment. Do not broaden that work silently.

## Process choices requiring separate approval and qualification

**Filled/capped vias are not a universal requirement.** TI’s device guidance requires the exposed pad’s soldered ground/thermal connection; its package drawing offers filled, plugged **or tented** vias under paste. The current RGT0016C stencil example uses 85% exposed-pad coverage with a 0.125 mm stencil. That is package-specific guidance, not a ready-made stencil for this custom footprint. [TPS62130 datasheet, §§6,11 and package drawings](https://www.ti.com/lit/ds/symlink/tps62130.pdf)

TI also describes small ordinary thermal vias, component-side tenting, a mask diameter 0.1 mm larger than the drill, and segmented/reduced paste. Generic 50–70% coverage guidance must be reconciled with the device/package drawing and assembly process. Backside tenting can increase trapped-gas voiding. [TI SLUA271C, §§3.4.1,4.4](https://www.ti.com/lit/an/slua271/slua271.pdf)

Possible separately approved alternatives:

1. Keep U5/C15 copper and the thermal via unchanged; design an actual component-side mask notch/island and qualified reduced/segmented paste apertures that avoid the hole. Verify solderable EP area, thermal contact, mask registration and assembly voiding. Paste reduction alone does not prove a mask barrier or prevent reflow wicking.
2. Keep geometry and select a separately qualified manufacturing treatment. Filling/capping is one option, not presumed permission or necessity.
3. Retain ordinary small vias with an explicitly qualified stencil/reflow process and verified thermal/assembly outcome. No such qualification is present in the reviewed evidence.

JLC describes tenting as ordinary processing, prefers holes no larger than 0.4 mm, and distinguishes it from filling/capping. It also warns that tented/untented holes can retain solder and limits solder-mask-ink plugging near/in pads. The present 0.2 mm drill satisfies the size preference; that does **not** resolve the overlapping pad opening. [JLC via-covering guidance](https://jlcpcb.com/help/article/pcb-via-covering)

For U11/C21, retain both surge-ground and buck-input-cap return paths. A routing move must carry both F/B donors and prove local ground connectivity. An aperture/treatment proposal must also preserve U11’s solder joint and the opposite-side C21 joint; ordinary tenting is not evidence that those requirements are already met.

## r54 applicability and handoff

r54 board SHA256: `5677fb38db7d7e19cd3afa9dd5da61bbd9932ed0be7f6f2899f7bf4bf58e8fc9`.

The r54 changed C_RX via and four changed tracks intersect **none** of this inventory’s vias or direct donors. All listed vias, pads and direct donor tracks are textually unchanged. Classification and direct-donor facts carry over; detailed fill/candidate calculations remain explicitly r53-bound. See `r54-applicability.json`.

`PUBLICATION-HANDOFF.json` seals the intended review files. No component, placement, footprint, process, or aperture change is authorized by this report.
