# Nexus F722 USB: source-bound routing and stack review

## Decision

**Rework the complete connector-to-MCU pair, including both USB-C orientations and all four U7 I/O pads. A width-only or clearance-only repair cannot qualify this port.** Prefer a B.Cu trunk referenced to In4.GND, locally joined connector duplicates and equal transitions. Preserve the existing parts, placements, pin assignments, netlist, external U7 same-net bridges and manufacturing floors in the first candidate. This is a bounded routing target, not a demonstrated clearance-free route or an impedance certificate.

No PCB/schematic edits, native KiCad calls, refill, DRC, field solver, publication or external writes were performed by this review. All measurements use static text parsing and lightweight numerical geometry.

## Source and checks

- Candidate: `c19-integration/experimental-r43/hardware/nexus-style-fc.kicad_pcb`
- PCB SHA256: `10c4da72046f311a0ad61ac150091573966c8d9fae70fa93a57402a568d059c5`
- Schematic SHA256: `49f9e0571424d0610e294bdcd6b120a42d04db284ecda9e660428fc587e62699`
- Reported durable draft: chenguoming1/h743-controllers PR36, head `04fe0309a05348c28e82cdc72fda14bbf66eb557`. That remote head was supplied by the task owner, not independently fetched here.
- The existing native execution receipt binds this exact saved PCB hash to `--refill-zones --save-board`, completed 2026-10-15 03:47:03 UTC. Therefore the inspected polygons are the saved post-refill polygons of this candidate. They do not predict any later reroute/refill.
- Existing native report: 29 clearance errors, 54 silk warnings, zero opens and schematic-parity issues; existing ERC zero. Three clearance records involve USB: DP–DM 0.0987 mm twice, DP–GND-via 0.0893 mm once. These are below the required 0.127 mm. The review does not replace the owner’s active clearance-repair lane.

## Current endpoint mapping and geometry

The schematic/netlist and PCB agree:

- DM: J6.A7/B7 → U7.1/6 → U1.44, PA11.
- DP: J6.A6/B6 → U7.3/4 → U1.45, PA12.
- U7.2 GND, U7.5 VBUS. U1 is STM32F722RET6; this is its embedded full-speed USB interface. The ST pin table maps PA11/PA12 to OTG_FS_DM/DP; the device’s high-speed function instead requires ULPI. Do not judge this as a 480 Mb/s HS PHY route or add series resistors by analogy. ST documents integrated transceiver impedance matching. [STM32F722 datasheet, pin table and §6.3.29](https://www.st.com/resource/en/datasheet/stm32f722re.pdf), [AN4879, FAQ](https://www.st.com/resource/en/application_note/an4879-introduction-to-usb-hardware-and-pcb-guidelines-using-stm32-mcus-stmicroelectronics.pdf)
- ST’s USBLC6-2 top view confirms I/O1 pins 1/6 and I/O2 pins 3/4. No pin-swap error was found in these net assignments. Actual mounted orientation and connector vendor pinout are separate, unverified assembly gates. [USBLC6-2 DS4260 Rev7, p1](https://www.st.com/resource/en/datasheet/usblc6-2.pdf)

All data tracks are **0.150 mm** wide; all seven data vias are **0.450/0.200 mm** through vias. The netclass’s unused router defaults are 0.200 mm differential width / 0.250 mm gap; those defaults do not describe the actual route.

### All-net copper inventory, not end-to-end lengths

| Net | F.Cu traces | B.Cu traces | In3.Cu traces | Total trace centerline | Vias |
|---|---:|---:|---:|---:|---:|
| DP | 2.710 mm | 11.371 mm | 23.215 mm | 37.296 mm | 5 |
| DM | 3.011 mm | 10.341 mm | 19.838 mm | 33.190 mm | 2 |

These totals include branches, duplicate connector paths and U7 bridging. Their 4.106 mm difference is **not** the pair’s connector-to-MCU mismatch.

### Individual external-board paths

| Start → MCU | F.Cu | B.Cu | In3.Cu | Trace centerline | Traversed vias | Intended barrel travel | Synthetic contacts |
|---|---:|---:|---:|---:|---:|---:|---:|
| A6 → U1.45 DP | 1.606 | 10.096 | 18.635 | 30.337 mm | 4 | 2.995 mm | 0.102 mm |
| A7 → U1.44 DM | 1.104 | 6.185 | 19.838 | 27.127 mm | 2 | 1.582 mm | 0 |
| B6 → U1.45 DP | 1.104 | 10.096 | 23.215 | 34.415 mm | 4 | 2.995 mm | 0.025 mm |
| B7 → U1.44 DM | 3.011 | 6.185 | 19.838 | 29.034 mm | 2 | 1.582 mm | 0 |

Trace-only mismatch is **DP longer by 3.210 mm for the A contacts and 5.381 mm for the B contacts**. Adding the stated barrel and synthetic-contact lengths gives geometric differences 4.725 mm / 6.819 mm. None of these sums is electrically validated delay or skew; they exclude package/cable travel and propagation differences, and do not model current splitting through U7’s internal connections.

The graph splits straight track centerlines at contacts. The 0.077 mm DP contact is the offset from via (108.075,127.375) to the intersecting In3 line at x=108.152. The other 0.025 mm is an overlapping B.Cu endpoint at (109.575,124.375) touching the bridge at y=124.350. Synthetic lengths make this convention explicit rather than pretending all copper contacts share exact endpoints. Barrel distances use CAD copper midplanes: F↔In3 0.8751 mm and B↔In3 0.7067 mm; full through-via plating also leaves unused barrel portions.

DP layers: J6 F → In3 connector detour → B at (108.152,123.749) → U7 row/tee → In3 at (109.575,124.725) → B at (110.933502,110.275) → MCU. DM: J6 F → In3 at (108.65,127.846) → B at (111.237787,109.259787) → MCU. All exact waypoints and UUIDs are in `geometry-evidence.json`.

### Connector duplicate joins and U7 branches

- DP A6↔B6 uses **7.290 mm of trace + 1.750 mm intended barrel + 0.077 mm synthetic contact**. Its two legs to the In3 joining point differ by 4.001 mm including these conventions.
- DM A7↔B7 is **1.907 mm all-F.Cu**, joined at A7. Its corresponding orientation leg difference is 1.907 mm.
- A local DP duplicate join could eliminate much of the excursion to y=131.754 and back. It must preserve both orientations. The two connector rows reverse DP/DM x-order, so two straight same-layer joins would cross. A real local crossover or short outside fanout with balanced transitions is required; no feasible path is claimed here.
- DM’s main In3 path bypasses U7. Its B.Cu branch from via (108.65,127.846) runs to a tee at (109.253,126.25), then reaches U7.1 after **2.559 mm** or U7.6 after **3.453 mm** of planar copper. These are loaded protection branches, not literal open stubs.
- DP encounters the U7.3 row, but leaves toward the MCU from the midpoint (109.575,124.35) of the **2.300 mm U7.3→4 external bridge**. U7.4 remains on a **1.275 mm tail** beyond that tee. U7.1→6 also has a 2.300 mm external bridge.
- C25 is 1 µF on VBUS; C28 is 22 µF on **3V3**, so C28 must not be called U7 VBUS bypass. U7’s ground/rail loop is a separate ESD acceptance item. ST emphasizes short data-to-clamp, VBUS and ground-plane connections and connector proximity; device ESD ratings do not certify system immunity. [USBLC6-2, §2.3 and Fig17](https://www.st.com/resource/en/datasheet/usblc6-2.pdf)

### Pairedness and reference coverage

This is not a constant-gap differential pair. At 0.010 mm midpoint sampling, only 6.780 mm of DP’s 37.296 mm and 6.843 mm of DM’s 33.190 mm have a nearest opposite-net same-layer segment within 0.250 mm edge gap, aligned within 10°, with an interior projection. That is a descriptive test, not a USB requirement. Actual gaps vary from approximately 0.0987 mm to millimeters. For example, connector F escapes have 0.350 mm edge gap; the U7 external bridges are 1.750 mm apart; inner routes progressively separate. The long DM In3 line runs near x=110.918–110.960 while DP steps from x=110.575 to 110.225.

Saved filled-GND polygons were sampled under every track center and both edges. For the outer-layer references and **both layers immediately adjacent to In3**, the center-projection lengths outside saved GND fill are:

| Layer/reference | DP uncovered / examined | DM uncovered / examined |
|---|---:|---:|
| F/In1 | 0.724 / 2.710 mm | 0.348 / 3.011 mm |
| B/In4 | 1.067 / 11.371 mm | 0.711 / 10.341 mm |
| In3/In2 | 10.029 / 23.215 mm | 7.272 / 19.838 mm |
| In3/In4 | 2.111 / 23.215 mm | 0.738 / 19.838 mm |

For **In1/In4 only**, every uncovered center sample lies within 0.525 mm of a USB via; no unrelated mid-span fill gap was detected on those two references at this sampling resolution. Ordinary signal-via antipads are reference discontinuities, not evidence of a broad broken ground plane. The longest DP interval on those references is about 0.690 mm at x=108.152, y=127.028–127.718 around its off-center connector tee via.

**In2 also carries GND fill, interspersed with signal copper; it is not merely a signal-only layer.** Its closer fill covers 13.186 mm of DP and 12.566 mm of DM In3 centerline. It has uncovered center projections beyond the same USB-via neighborhoods: **7.190 mm DP and 5.816 mm DM**. Examples include DP x=110.575, y=113.105–114.595 (1.490 mm within one track) and DM near x=111.356–111.374, y=109.694–111.468 (1.774 mm within one track). Continuations across track endpoints can make a contiguous interval longer than an individual-record interval. At least one line-edge projection falls outside In2 GND for 10.759 mm DP / 7.792 mm DM. Thus a field model must account for changing adjacent copper and both In2/In4 references, rather than assign one uniform single-reference impedance. A mixed signal/GND layer is not automatically disqualified as a reference: assess its actual finite copper paths, coupling and GND interconnections.

Every segment/reference record enumerates the saved filled-polygon IDs touched by center and line-edge projections, expressed as zone UUID plus zero-based filled-polygon occurrence in the exact source:

- In1: `9f2a2d78-0e48-4414-9879-4fc68abc23e3:0`.
- In4: `88957e6f-e13e-4cbf-a8e2-1d52ff9863ab:0`.
- In2: zone `31ebd316-e294-41f0-8942-ba78a56019d4`, polygon indices **0, 2, 3 for DP** and **0, 1, 2, 3, 6 for DM**. Exact per-segment associations are in `geometry-evidence.json`. Multiple stored polygon memberships do not by themselves prove isolation; vias or other copper may connect them.

GND-via center distances range 0.710–2.538 mm from the seven signal vias; proximity alone does not prove a low-inductance return. Existing plated shield pads can provide additional returns and were not included in that nearest-via statistic. Finite return contact around each antipad/gap, via-to-plane copper contact and connections among these reference polygons/layers are **not proved** here and remain explicit native/geometric acceptance gates. These measurements are sampled projections, not a continuous return-current or EM analysis.

## Declared stack and bounded impedance estimate

Copper/dielectric sequence in the candidate, top to bottom, in mm:

`F 0.035 / 2116 0.1164 (Er 4.16) / In1 0.0152 / FR4 0.5500 (Er 4.6) / In2 0.0152 / 2116 0.1532 (Er 4.16) / In3 0.0152 / FR4 0.5500 (Er 4.6) / In4 0.0152 / 2116 0.1164 (Er 4.16) / B 0.035`

In1/In4 carry the principal GND pours. Outer traces have a 0.1164 mm dielectric to their neighboring GND layer. In3 has **0.5500 mm to In4** and only **0.1532 mm to In2**, which carries both GND fill and signal copper. Both adjacent layers are quantified above. The current In3 route cannot use an outer-layer microstrip estimate; a proper model includes the actual In2 and In4 copper, other significant conductors, layered dielectric and changing return geometry. An exclusively signal-free plane is not assumed necessary.

This is the **declared CAD stack**, not a verified manufacturer production stack. Its copper+dielectric sum is **1.6168 mm**, versus the nominal general board thickness setting 1.6 mm; the two 0.010 mm masks are additional declared layers. Confirm the intended production stack, finished copper/dielectric dimensions, nominal-thickness convention and tolerances with the fabricator before impedance release. This small nominal difference alone does **not** establish a fabrication defect.

Using TI’s empirical uncoated edge-coupled microstrip equations, with h=0.1164 mm, t=0.035 mm and Er=4.16:

| Width / edge gap | Estimated differential Z |
|---|---:|
| 0.150 / 0.127 mm | 92.09 Ω |
| 0.155 / 0.127 mm | 90.53 Ω |
| 0.160 / 0.127 mm | 89.00 Ω |
| 0.170 / 0.150 mm | 89.08 Ω |
| 0.200 / 0.250 mm | 88.08 Ω |

These are plausible starting geometries only. The existing 0.150/0.350 outer escape would estimate 107.77 Ω in this simplified model. [TI USB Layout Basics, impedance equations](https://www.ti.com/content/dam/videos/external-videos/en-us/4/3816841626001/6087491555001.mp4/subassets/usb_layout_basics.pdf)

The estimate ignores mask dielectric, nearby coplanar pours, etch trapezoid, roughness, frequency dependence and discontinuities. An illustrative parameter sensitivity sweep for nominal 0.155/0.127 produces **78.25–103.05 Ω**; those parameter bounds are not supplier tolerances and the low-gap scenario is not an allowed routing gap. Thus the nominal value cannot establish a qualified impedance window. USB nominal 90 Ω is supported by TI’s USB guidance; obtain fabricator-controlled dimensions/coupon verification and/or a suitable field solve before claiming 90 Ω. [TI USB layout guidance](https://www.ti.com/video/6087491555001)

## First full-port routing target and acceptance boundaries

1. **Scope:** J6.A6/B6/A7/B7, both complete U7 I/O bridges, MCU PA11/PA12, local signal transitions and their returns. Retain all parts, placements, nets and pin assignments. Repair all three existing USB clearances without lowering 0.127 mm track/clearance or changing 0.450/0.200 vias.
2. **Connector region:** seek the shortest practical local duplicate join for each polarity, then a paired exit; quantify the resulting A↔B path and branches without imposing an unsupported length cap. Resolve the reversed row order explicitly. Compare complete A and B paths; no long remote join masquerading as length matching. This target is subject to fixed-pad/CC/VBUS/shield obstacles, not a promise of feasibility.
3. **Layer plan:** connector F escapes referenced to In1, a compact equal transition arrangement, then B.Cu/In4 for U7 and the complete MCU trunk. Prefer one common F→B transition per signal after the local join; permit an equally treated local crossover only if necessary and fully evaluated. Avoid long In2/In3 excursions. 0.450 mm vias require at least **0.577 mm center spacing** for the 0.127 mm copper gap, so the pair must symmetrically fan out around vias.
4. **U7:** first target is connector→pin1→existing external copper bridge→pin6→MCU for DM, and connector→pin3→external bridge→pin4→MCU for DP. Put both pad contacts in the main external route, eliminate the current mid-bridge MCU tee and remote DM protection branch, preserve physical connectivity of all four pads. Retain the bridges instead of depending on an unrepresented package short. The fixed 1.9 mm channel separation creates a short unavoidable fanout; minimize it and re-pair on either side. Do not conceal it with a blanket uncoupled-length waiver.
5. **Pair trunk:** use one consistent width/gap after fabricator confirmation. For a compact initial study, 0.155/0.127 mm is a ~90.5 Ω analytic seed; 0.160/0.127 or 0.170/0.150 are nearby alternatives. Choose the actual geometry with coating and side-pour effects included. Preserve width through bends where possible. Keep same-layer ground pour spacing uniform or include it in the solver model.
6. **Geometry goals:** minimize complete-port asymmetry and unnecessary branching for **each connector orientation**, use equal signal-via counts and analogous transitions where feasible, and avoid unrelated branch/test pads or distant meanders added merely to match length. Quantify each complete path by layer, barrel convention, branch and U7/connector uncoupled section, then compare against the current candidate. Do not impose arbitrary total-length or mismatch caps. Apply a numerical acceptance limit only when its applicability to this STM32 full-speed interface is established from the manufacturer or USB requirements; no such board-length/skew limit is established by this review.
7. **Returns and completion:** inspect post-refill GND under both line edges and around transitions, place/reuse close GND returns where permitted, preserve U7 ground, C28 ground and all four shield EP connections/spokes. Then native all-track DRC, opens/parity, schematic ERC, exact path/branch extraction, A/B orientation review and impedance qualification. System USB signal-quality and ESD testing remain later gates.

If this fixed-parts plan cannot fit, stop with the exact blocking geometry. Moving/replacing/rotating U7 or J6, adding protection/bypass components, swapping channels, changing stack, removing the external pin bridges in favor of package-internal connectivity, or changing the schematic/footprint connectivity model needs separate review and approval. None was applied here. **This board is not fabrication-ready.**

## Reproducible artifacts

- `geometry-evidence.json`: exact parts, tracks/vias, UUID paths, per-layer lengths, stack, saved-fill coverage and pairedness.
- `supplement-evidence.json`: source-bound native report excerpts, nearest ground vias, uncovered-sample classification and analytic calculation assumptions/results.
- `analyze_usb_static.py`, `supplement_review.py`, `plot_usb.py`: complete read-only analysis and figure scripts. The supplement reruns the analyzer; none imports KiCad or writes a source board.
- `usb-geometry.png` / `.svg`: measured routing and stored-reference discontinuities, not a proposed routed candidate.
- `manifest.json`: final file/source hashes.
