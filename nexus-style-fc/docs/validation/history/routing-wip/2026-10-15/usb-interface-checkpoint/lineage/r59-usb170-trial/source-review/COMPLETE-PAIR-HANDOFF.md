# r57 USB complete-topology proposal: geometry closed, electrical acceptance conditional

## Decision

Parent selected the separate .170 mm main-trunk/.150 mm terminal overlay for a bounded native trial after the current mechanical batch seals. `NATIVE-170-OVERLAY.json` is the authoritative overlay and acceptance-gate handoff. The .150 mm baseline remains immutable; selection for a trial is not electrical or fabrication approval. The helper must compare r57 local records against accepted r58 before replay.

A distinct full-width routing topology closes in the bounded static geometry model. It uses a paired In3 trunk, complete U7 external ports, a compact J6 orientation join, and a B.Cu MCU escape. It avoids the rejected C29 corridor and moves no component. **Do not adopt this as a qualified 90 Ω USB route merely because its copper clearance screen closes.** Nearer In2 reference changes and the compact connector launch remain material electrical acceptance items.

Authoritative transaction: `complete-transaction.json`. It contains 67 exact source removals, expected source records, 112 additions with deterministic UUIDs, exact arc start/mid/end coordinates, four preserved bridge UUIDs and four reused via UUIDs. No PCB or schematic was edited; no native KiCad, refill, DRC, routing solver or field solver was run.

Source: accepted `routing-continuation/r57-rpm-center/hardware/nexus-style-fc.kicad_pcb`, SHA-256 `583e73ba08c80e70d42bfd726ef1b440ab0ddf4d7309cef266de486fd03f461f`, verified unchanged. Applicability to a later board requires source/local-context comparison and re-screening. The final selected compact branch is **In1**, superseding only the earlier conditional In4 branch choice; the secondary artifact remains unchanged.

## Complete ports and transaction

All USB tracks are 0.150 mm. Every added/moved via is an ordinary 0.450/0.200 mm through via. The paired trunk has 0.127 mm edge gap, 0.427 mm total envelope and tangent circular bends. Both lane lengths are 13.533168 mm after trimming the north handoff to y110.85.

- J6 DP: A6 (108.15,128.95), B6 (108.65,130.65). DM: A7 (108.65,128.95), B7 (108.15,130.65).
- DP enters U7.3 (108.55,124.35), follows the existing external 2.300 mm bridge to U7.4 (110.85,124.35), then exits to the trunk. DM analogously enters U7.1 (108.55,126.25), follows all three existing bridge segments to U7.6 (110.85,126.25), then exits. Neither bridge-center launches nor protection bypasses survive. Cutting either external bridge disconnects both corresponding connector orientations from the output.
- South In3 handoff: DP (109.5115,124.0), DM (109.7885,124.0). North: DP (110.7615,110.85), DM (111.0385,110.85). Do not restore the obsolete y110.60 extension.
- MCU: U1.45 DP (115.85,106.15), U1.44 DM (115.35,106.15). New terminal vias: DP (110.972,110.34), DM (110.98,109.68).
- Compact connector joins: DP B6 via (108.66,129.82) to A6 via (108.075,127.375) on In1; DM B7 via (108.08,129.77) to A7 via (108.65,127.846) on In3. The duplicate connector contacts are the only branch topology. These local branches are not a continuously coupled pair.

Four complete foreign donor transactions: LED1_K In2 detour at 0.127 mm; VBUS_C via and its three incident routes at unchanged 0.250 mm; SWDIO B escape/ordinary via/In3 tie at 0.127 mm; IMU_CS In2 segment detour at 0.127 mm. Contact comparison preserves every retained same-net contact, adds none, and leaves each replacement connected. LED1_K preserves 2 contacts among 27 retained objects; VBUS_C preserves 4 among 12. SWDIO preserves U1.46 and the exact retained In3 tie; IMU_CS preserves its two exact adjoining segments. Full endpoint/UUID details are in the transaction and subreports.

All existing GND traces/vias, shared capacitor/connector returns, J6 shield copper, U7.2 GND and U7.5 VBUS assignments remain untouched. This geometric preservation does **not** prove that newly refilled ground planes will retain every finite return contact. Ground regions are not disposable stitches.

## Static geometry result and margins

`integration-screen.json`: zero cross-subsection foreign-clearance failures; each USB net forms one finite-copper connected component containing all five required pads. Exact endpoint graph paths also close. Individual port and MCU screens show zero retained-object/new-mutual failures. Roundrect pads used conservative rectangular bounds. Circular arcs were screened with chord sagitta at most 0.000002 mm; transaction arcs remain true arcs.

The limiting MCU gate has only 0.127500147 mm retained-object clearance against 0.127 mm required. Its fixed B_TX/GND via-center opening is 1.133616985 mm; two traces, three clearances and two via radii need 1.131 mm. Other tight items: DP via/C19.2 0.128035 mm; VBUS_C via/J6.B5 0.130000 mm; connector join vias 0.132151 mm. This is a low-margin construction, not manufacturing tolerance approval. All new/moved annuli and drills separately clear nominal paste bounds; minimum reported annulus/paste spacing is 0.110 mm at a reused U7-side via. Final stencil, mask/tenting and fabrication tolerances remain unchecked.

## Length and via bookkeeping

| Connector orientation | DP planar centerline | DM planar centerline | DP excess | DP/DM used vias |
|---|---:|---:|---:|---:|
| A | 32.762451 mm | 30.191995 mm | 2.570457 mm | 4 / 3 |
| B | 34.500512 mm | 32.003648 mm | 2.496865 mm | 5 / 4 |

All-net copper totals, which include both connector branches, are DP 36.106578 mm and DM 33.107648 mm. Total USB vias are DP 5 and DM 4. These are different quantities from individual source-to-destination paths.

The In1 compact branch removes the old lower DP excursion and the secondary In4 option's additional 1.1304 mm barrel travel. Used barrel-centerline bookkeeping is 2.9952 mm on each of the four complete paths, despite differing via counts. Endpoint graph transitions are synthetic zero-length links; physical barrel bookkeeping is reported separately. Neither calculation models delay, unused barrel stubs, pads, ESD capacitance or mode conversion. No arbitrary total-length or skew gate is imposed. Further work should minimize complete-port asymmetry and branching and quantify its result.

## Actual stack and reference evidence

Declared stack, top to bottom: F 0.035 / dielectric 0.1164, Er4.16 / In1 0.0152 / dielectric 0.5500, Er4.6 / In2 0.0152 / dielectric 0.1532, Er4.16 / In3 0.0152 / dielectric 0.5500, Er4.6 / In4 0.0152 / dielectric 0.1164, Er4.16 / B 0.035 mm. The 1.6168 mm sum versus nominal 1.6 mm is a production-stack confirmation item; the small nominal difference alone proves no defect.

For the trimmed trunk, seven stored-fill projection rays sampled at no more than 0.001 mm show:
- Nearer In2: 5.370791 mm of pair-center projection absent; 7.423624 mm with at least one ray absent. Touched saved components are `31ebd316-e294-41f0-8942-ba78a56019d4:2` and `:3`.
- Remote In1 and In4: every sampled trunk ray covered. Component IDs are `9f2a2d78-0e48-4414-9879-4fc68abc23e3:0` and `88957e6f-e13e-4cbf-a8e2-1d52ff9863ab:0` respectively.
- In2 contains actual GND and signal/power copper. Six independent nets overlap the pair's projected envelope: 3V3, 5V, 5V_BUCK, 5V_SENSE, DSM_DATA and SPI1_MISO. Individual projected overlap sums are approximately 0.833, 0.922, 0.923, 0.608, 0.879 and 1.522 mm; overlaps between nets/intervals must not be summed as a unique route length. Exact UUIDs, intervals, full donor ports and adjacent via constraints are in `reference/`.

All terminal/bridge primitive reference IDs and three-ray projection lengths are also recorded in `full-saved-reference-projection.json`. These are saved source fills, not post-refill results. No sampled mid-span gap is different from proving finite connected return paths, including transitions around new antipads.

The In1 connector branch projects under J6.A7's DM pad and comes within 0.042722 mm projected edge distance of its F.Cu DM trace across the 0.1164 mm dielectric. This is not a same-layer DRC short. It is a specific broadside-coupling/reference-slot qualification item, recorded in `in1-connector-neighbors.json`.

## Analytic impedance assessment and stopping choice

`impedance-sensitivity.json` uses an explicitly stated equivalent-wire image-charge approximation with the actual plane distances. It sweeps homogeneous Er4.16/4.6 and two equivalent-radius choices to expose sensitivity; it does not solve the real mixed-dielectric, finite-strip, multiconductor cross section.

| Idealized cross section | Analytic sensitivity values |
|---|---:|
| In3 pair with solid In2 and In4 references | 90.6–101.0 Ω |
| In2 absent, actual remote In1 and In4 references | 104.3–115.3 Ω |
| F/B parallel .150/.127 pair over adjacent GND, simple microstrip seed | about 92.1 Ω |

These ranges are **not accuracy bounds or fabricated tolerance ranges**. A representative same-model comparison rises approximately 93→107 Ω when the nearer plane is removed. Actual In2 power/signal crossings, coplanar GND after refill, dielectric interfaces, vias, plane edges and soldermask can change the result. Therefore the complete route cannot be called uniformly 90 Ω. The outer-layer estimate does not apply to In3 or the uncoupled launches.

A one/two-donor In2 correction cannot establish uniform nearer reference over this whole trunk while six independent crossings remain. No such incomplete repair is included. **Concrete next choice:** keep this exact transaction as a conditional geometry candidate, then qualify the post-refill multiconductor stack and transitions before adoption, focusing on a covered section, a 5V/5V_BUCK crossing, and the compact connector launch. If the actual-stack extraction/USB-FS electrical checks reject it, a coordinated reference corridor involving those six donor nets is the next routing scope; this bounded study does not claim global impossibility. No further placement proposal is made.

## Acceptance gates and primary sources

1. Apply only to a matching source in the exclusive native lane; refill and run DRC, unconnected/parity and the full shared-return/mask/paste audit. Do not waive the low-margin MCU gate or newly split GND components.
2. Prove finite return continuity at every new transition and preserve shield/ESD/main-plane contacts after refill. Existing source component IDs are evidence to track, not acceptance by themselves.
3. Confirm production copper/dielectric data and qualify actual odd/common-mode impedance, branch/via discontinuities and USB-FS behavior. Keep schematic/part/pin assignments fixed.

[ST AN4879 Rev12](https://www.st.com/resource/en/application_note/an4879-introduction-to-usb-hardware-and-pcb-guidelines-using-stm32-mcus-stmicroelectronics.pdf) identifies the embedded FS use and internally managed driver impedance; it does not justify adding unrequested series resistors or inventing length/skew gates. [USBLC6-2 datasheet](https://www.st.com/resource/en/datasheet/usblc6-2.pdf) emphasizes short data/protection/ground connections and connector proximity; the proposal places both external U7 ports in the actual copper path. [TI USB layout guidance](https://www.ti.com/video/6087491555001) provides the nominal differential-routing context. [TI differential-pair guidance](https://www.ti.com/document-viewer/lit/html/SSZTCR1) emphasizes fairly constant/equal odd-mode impedance. The analytic proxy is explicitly our approximation, based on electrostatic image-charge reasoning and the lossless capacitance/impedance relation described by the [NBS/NIST transmission-line paper](https://nvlpubs.nist.gov/nistpubs/jres/71C/jresv71Cn1p59_A1b.pdf); it is not a vendor-qualified equation for this board.

The bounded wider-inner-width follow-up is recorded separately in `WIDTH-SENSITIVITY.md` and three variant JSON files. None silently supersedes this .150 mm transaction.
