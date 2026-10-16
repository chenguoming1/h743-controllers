# Nexus batch31: independent power and return-geometry review

## Result

The contact audit is useful but is not power/return qualification. Two changes deserve explicit electrical review before manufacture: the new two-via U10-to-C19 LDO output-capacitor path, and the new cross-board L2 output/distribution bridge. The B_TX inner-layer bridge introduces different reference/coupling geometry, but no mid-route break in either main GND plane was found beneath it.

This is read-only analysis of the published batch31 snapshot. No source, routing, refill, DRC, solver, publication, or user-computer action was performed. No oscillation, overheating, signal failure, impedance value, current rating, or EMC outcome is predicted here.

## Scope and evidence

- PCB: batch31/hardware/nexus-style-fc.kicad_pcb, SHA256 `47b6cf94fb2213c0ae46ab692fd9b8f71e90c2c278944827f9156daa25e8e23b`.
- Published association provided in the review scope: PR #33, commit `8d7fdeb5c5b73123b70e972923f1386c262d018b`. This review independently hashed the local PCB; it did not re-query GitHub.
- Compared candidate16, SHA256 `cbfdeacbcf474faac0f572f4b40db80de827ca498cab40ff3c76966f619d8388`, and original main, SHA256 `b467854d4e4a49959d61bdbaa088e78165129ce30ae8ab9dedf4d45c58999b5c`.
- Read cumulative-audit.json, batch31 verification.json, and accepted transaction evidence, especially batches 17, 19, 24, 25, 30 and 31. The stored native result remains 37 clearance errors, zero opens/parity and 54 inherited silk warnings. This review did not rerun it.
- Geometry was extracted with KiCad 10.0.7 LoadBoard. Stored filled GND polygons were queried with native Contains at centerline midpoints no more than 0.02 mm apart. Quoted coverage percentages describe projected filled-copper presence, not return-current allocation or field-solver results. Boundary intervals are approximate to the sampling step.
- Width-binned length totals count every segment once; they are not series path length, resistance of a complete rail, or current-sharing analysis. Via barrel length is excluded from those totals.

## 1. U10 output capacitor: new 3D loop geometry

U10 is TPS70933DBVR. U10.5 OUT is at (108.450,105.900), F.Cu. C19.1 is at (108.625,109.800), F.Cu; C19 is the 2.2 µF LDO output capacitor. The schematic explicitly says “LDO out, >=2 uF effective” and specifies LCSC C23630.

The accepted batch24 transaction replaces the direct, 0.25 mm F.Cu route with:

- F.Cu: U10.5 → (108.650,106.800) → new via (108.925,107.350)
- In3.Cu: (108.925,107.350) → new via (109.300,109.550), length 2.231731 mm
- F.Cu: (109.300,109.550) → C19.1

The four replaced planar segments total 4.210246 mm. The replacement totals 4.488414 mm, all 0.25 mm wide, but adds two F-to-In3 traversals. The retained 0.007 mm segment terminating inside C19 is excluded from these path totals.

Using the stored stack, F-to-In3 copper-center spacing is 0.8751 mm: the two intended traversals add about 1.7502 mm of vertical conductor. These are through vias, not blind vias; their unused In3-to-B portions remain. The stored copper thickness changes from 35 µm on F.Cu to 15.2 µm on In3.Cu. Thus equal trace width does not preserve conductor cross-section on the moved segment. A simple 20 °C bulk-copper trace-only calculation gives approximately 8.30 mΩ before versus 14.57 mΩ after, excluding pads, vias, current spreading, temperature and manufacturing variation. This is a geometric resistance comparison, not a predicted supply drop or stability result.

Return observations:

- The direct C19.2 GND (110.175,109.800) → (109.400,109.025) → U10.2 GND (109.400,108.200) F.Cu track remains, 1.921016 mm long and 0.127 mm wide. There is also filled GND copper. No open capacitor-ground path was found.
- In3's adjacent In4 GND plane is separated by 0.5500 mm dielectric. Its other neighbor is signal layer In2, only 0.1532 mm away.
- In2 GND pour covers about 17% of the new inner segment's projected centerline. The uncovered portion is about 1.853 mm. This nearby layer cannot be treated as a continuous GND reference.
- Both main GND planes, In1 and In4, cover the middle of this segment; their only sampled projection gaps are its own end-via antipads, approximately 0.359 mm at each end. No mid-span main-plane split was observed.
- The closest GND through-via to the upper new power via is (109.875,109.425), 2.282 mm away. The same GND via is 0.588 mm from the lower new power via and is connected to the stored GND fill on all six copper layers.
- The new In3 power segment crosses S3 on In2 in projection at (109.13819,108.60069). This is an interlayer coupling location, not a copper short.

Official TI TPS709 Rev H guidance: §8.1.1 specifies 1.5–47 µF effective output capacitance for the 3.3 V version and 0–0.2 Ω capacitor ESR; effective capacitance includes tolerance, temperature and DC-bias effects. §10.1 calls for capacitors close to the pins and direct output-capacitor grounding. This supports reviewing the changed LDO output-loop impedance and AC response; it does not establish oscillation. This is an LDO output-capacitor loop, not a switching-converter hot loop. Source: [TI TPS709 datasheet, pages 14–16](https://www.ti.com/lit/ds/symlink/tps709.pdf).

C19 effective capacitance over operating conditions remains unverified. The source part selection and nominal 2.2 µF label alone do not close that check. The [LCSC listing](https://www.lcsc.com/product-detail/C23630.html) and [JLCPCB listing](https://jlcpcb.com/partdetail/CL10A225KO8NNNC/C23630) identify C23630 as Samsung CL10A225KO8NNNC, 16 V X5R ±10% 0603; do not substitute the different C1607 / CL10A225KP8NNNC part.

Bounded mitigation to investigate: first test whether a full-width F.Cu output-capacitor path can be recovered without moving footprints/pins. If it cannot, compare a shallower-layer alternative and a nearby GND stitch at the upper transition while preserving the direct U10/C19 ground path. Each candidate still needs native clearances/contact checks and an actual-stack return/AC check; feasibility is not established by this review. Validate output noise/transient response and the selected capacitor's effective C/ESR before qualification.

## 2. Added 3V3 via: post-inductor distribution bridge

The transaction called the “R15 bridge” is electrically a route from L2.2, the 3V3 buck's post-inductor output at (105.830,121.800), to the existing distribution via (108.622,121.748). R15 itself is on SCONF/GND; it is an obstruction landmark, not the load of this 3V3 route.

Old leg: 2.813250 mm of 0.25 mm B.Cu. New leg: 1.369452 mm B.Cu to the new via (105.600,123.150), then F.Cu through (105.950,122.700) to (108.622,121.748); planar total 4.776068 mm, still 0.25 mm. The new via introduces a B-to-F crossing. A path continuing onto B.Cu at the old distribution via crosses back there. The net also has other connections, so this is not established as the sole current bottleneck.

The closest GND through-via to the new power via is (106.775,125.975), 3.060 mm away. The nearest to the existing distribution via is (110.375,122.525), 1.918 mm away. B.Cu and F.Cu have nearby In4 and In1 GND planes respectively, each 0.1164 mm dielectric away, so this bridge changes the nearest plane and must transfer return between them. Both planes remain connected; no DC return break is asserted. No GND stitch was added: all three snapshots contain 75 GND vias.

The preserved width does not preserve length or via/return inductance. This is the buck's output distribution, not SW_3V3. Its impact on load-step delivery/current sharing remains to be checked. A bounded improvement would investigate a same-side full-width bridge or a nearby GND through-via for the existing cross-board bridge, without changing footprints/pins. Do not infer sufficient via ampacity from diameter/drill alone; plating, finished barrel, current and allowable temperature rise remain unknown.

## 3. B_TX bridge: reference and neighboring signal geometry

The new B_TX via (113.950,118.650) connects F.Cu to a 3.842853 mm, 0.127 mm In2.Cu segment terminating at the existing via now at (111.739894,115.506284). That existing via connects In2 and In3. Its position differs slightly from the proposal coordinates, so final PCB geometry, not proposal JSON, is used here. B_TX is U1.38 UART6 TX through the U13.6 protection connection to J5.4.

- In1 GND is 0.5500 mm dielectric from In2; the neighboring signal layer In3 is 0.1532 mm away.
- The In1 and In4 main planes cover the middle of the complete new bridge. The only sampled centerline projection voids on either are the bridge's end antipads, about 0.358 mm each. This is positive evidence against a new mid-span plane split.
- In3 GND pour covers about 36% of the projected bridge; ~2.449 mm lacks In3 GND underneath. The bridge crosses NRST on In3 in projection at (112.943665,117.218561).
- Closest GND through connection to the new via: (110.590858,121.956), 4.713 mm away. Closest to the existing In2/In3 transition: (112.875,112.075), 3.614 mm away.
- F-to-In2 can retain In1 as the same reference plane; the 4.713 mm GND-via distance alone is not proof of a broken return. The In2/In3 transition and partially available nearby pours still require return-transfer/coupling review. No edge rate, loading, parasitic extraction or crosstalk amplitude was evaluated.
- Total B_TX planar copper grows from 16.394791 mm in candidate16 to 18.450184 mm in batch31. This total includes all branches; it is not a driver-to-receiver flight-time result.

Bounded mitigation: investigate relocating the new inner segment away from the NRST crossing, maintaining a continuous selected reference, and placing a local ground return connection where planes change. These are feasibility targets, not approved route solutions. UART baud rate alone is insufficient to qualify an unknown output edge rate.

## 4. Width-binned power geometry and residual adequacy

See power-width-layer-lengths.csv for complete main/candidate16/batch31 bins, and plane-power-analysis.json for exact segment IDs and coordinates.

Notable candidate16 → batch31 totals:

- 3V3: 126.187895 → 133.282131 mm; vias 8 → 9. F.Cu at 0.25 mm: 31.129544 → 37.008391 mm. B.Cu at 0.25 mm: 48.669053 → 49.818459 mm.
- 3V3_SENS: 64.995169 → 65.587042 mm; vias 6 → 8. In3 at 0.25 mm: 4.586877 → 6.818608 mm. F.Cu at 0.25 mm: 37.465018 → 35.761127 mm.
- 3V3_DSM: unchanged total 11.850608 mm, but 1.202 mm migrates from In3 to F.Cu around the relocated via. Width is 0.25 mm. Equal total length does not mean identical loop/return geometry.
- VBUS_C: 12.656553 → 10.934289 mm, vias unchanged at 2; existing three-layer junction was relocated. Shorter total alone is not current/USB-port qualification.
- 3V3 still includes a continuous 13.789161 mm, 0.127 mm In3 branch between (117.746,116.188) and (118.016284,129.454450). It was 13.744922 mm at 0.127 mm in candidate16 and 13.692916 mm at 0.100 mm in original main. It has been widened relative to original main, not narrowed. It joins a multi-branch supply network around MCU distribution and boot/reset/LED circuitry; no load current or whole-rail rating is inferred.
- 3V3_SENS retains 4.096846 mm of 0.127 mm and 4.470336 mm of 0.1874 mm F.Cu traces. These inherited narrow branches require load-specific review if used to claim rail capacity.
- SW_3V3 planar copper remains 3.549872 mm and has no vias in all snapshots. This review found no basis to label the new 3V3 bridge as a switch-node reroute.

All four added vias are 0.45 mm copper / 0.20 mm drill, tented on both sides and outside paste-bearing pads per the cumulative audit. Tenting does not remove full-stack barrels/stubs or provide a return connection. With the stored stack, the unused B_TX In2-to-B barrel is about 0.8751 mm and each sensor via's In3-to-B remainder about 0.7067 mm (copper-center estimates). No resonance prediction is made.

The stored nominal board thickness is 1.6 mm, while its listed six copper layers plus five dielectrics sum to 1.6168 mm before solder mask. These values are inherited, and this is a model-consistency/fabricator-stack confirmation issue, not a newly measured fabricated thickness. The review uses listed dielectric/copper values only; actual fabrication impedance, via inductance and ampacity remain unqualified.

## Remaining limits and acceptance gate

This does not resolve the 18 inherited pasted vias, the 11 fixed header contact-edge errors, square-tab/capsule interference, USB actual-stack impedance, U2 FSYNC/orientation, or the differing Nexus/F722 connector pinout. It does not supersede remaining native clearance errors. Final electrical acceptance needs a confirmed manufactured stack, selected-capacitor effective value, bounded load/current assumptions, a local return/decoupling review and appropriate circuit/bench validation. Local continuity and full-width pad entry are necessary but do not establish these results.
