# Fresh U10 and USB qualification review after runtime recovery

## Status and evidence boundary

These are **new measurements against recovered published batch35**, PCB SHA256 `55b8508480f5fb098d0188e66229a3ab448cef8f7d6b534599da3d6637f52477`, using KiCad 10.0.7 read-only board loading. The source hash was checked before and after analysis. No board was written, routed, refilled or subjected to DRC or a heavy solver.

The earlier complete LDO/USB proposal JSON and unpublished batch41 board are not recovered here. Exact waypoint and UUID subsets visible in the earlier authored conversation are explicitly labeled historical parameters in the new receipt. They are not accepted transactions. Neither a lost batch41 result nor its source binding is silently assigned to batch35.

One prior authored report, `ldo-en-source-clarification.md`, was restored byte-for-byte: its SHA256 `724411b3f4427ae817269ffe98b65ab65b25864cb31f4391bee6ff14a00c63f5` matches the pre-loss receipt. All other files in this recovery folder are newly generated review evidence.

## U10: bounded output-loop improvement remains plausible

Fresh part/net inspection identifies TPS70933DBVR U10.1 IN at (108.450,108.200), U10.2 GND at (109.400,108.200), U10.3 EN at (110.350,108.200), and U10.5 OUT at (108.450,105.900). In this recovered PCB, IN and EN are still VSYS. EN isolation is a separate pending repair; this review does not claim it has happened.

Existing OUT→C19.1 routing is 4.488414 mm planar at 0.250 mm width, including two 0.450/0.200 mm vias at (108.925,107.350) and (109.300,109.550), with the middle route on 15.2 µm In3 copper. Intended F↔In3 barrel travel totals 1.7502 mm. C19.2→U10.2 direct F.Cu ground is 1.921016 mm.

The historically proposed 0.250 mm all-F.Cu output polyline is:
(108.450,105.900) → (108.450,106.500) → (107.895,107.055) → (107.895,108.950) → C19.1 (108.625,109.800).

Fresh arithmetic gives 4.400335 mm and zero local output vias. Every one of 446 stored In1-GND projection samples is covered. A scoped native copper check, excluding the proposed original input/output removals and hypothetical EN cut, gives a minimum foreign-copper gap of about 0.180320 mm. Trace-only resistance under a 20 °C bulk-copper model falls from about 14.57 to 8.67 mΩ; this excludes vias, pads and temperature effects and is not a stability result.

The historically proposed input donor is U10.1 → (108.450,107.650) → new VSYS via (108.925,107.350) on F.Cu, then B.Cu to existing ce0 via (107.728574,105.820545). It adds 0.389325 mm planar and approximately 1.4134 mm intended barrel travel. Both outer layers are 35 µm. This is a real input-path regression.

C18 is 1 µF on B.Cu, VSYS pad at (106.410,116.940). Fresh native shape checks confirm each adjacent physical contact in its 15-track serial chain to IN. The complete segment-length sum is 25.543149 mm, becoming 25.932474 mm under the historical donor substitution. This includes the overlapping C18 pad-entry segment; it is not a pad-center-to-pad-center impedance length. C18 remains remote.

TI requires effective output capacitance of at least 1.5 µF at 3.3 V, with ESR 0–0.2 Ω; close capacitor placement and a direct output-capacitor ground connection matter. Input capacitance is not inherently required for stability, but supports transient/ripple behavior and is required for anticipated line transients above 10 V. Thus the output/input trade is not electrically symmetric. Effective C19 capacitance and actual supply/transient conditions remain unverified. TI also forbids EN→VIN and permits floating EN; its 300 nA pull-up is not a clamp-injection rating. [TI TPS709 Rev H, §§7.4, 8.1.1, 10.1](https://www.ti.com/lit/ds/symlink/tps709.pdf)

Recommendation: the all-F output remains a reasonable bounded experiment only with a newly complete input/output transaction, preserved direct C19 ground, native acceptance and later electrical qualification. No stability claim follows.

## EN removal does not clear the checked all-F input alternative

Fresh hypothetical removal of the ten historical EN-only tracks leaves the physical EN pad as an obstacle. The explicit 5.168707 mm input alternative around OUT again overlaps retained RPM via (109.089142,106.510858) and TAIL via (109.260798,105.901932), and has only 0.077410 mm gap to the retained top 3V3_SENS trace. These failures are remeasured on batch35, not borrowed from lost batch41.

The short corridors remain obstructed by fixed vias/pads. A feasible larger-area route is not ruled out, but EN removal alone does not demonstrate one. Do not narrow the 0.250 mm power path or sacrifice direct C19 ground to force the gap. Coordinated signal-transition relocation would require its own complete contact/reference review.

## USB: retained local plane returns, with a specific spoke risk

U7 is USBLC6-2SC6: pin 2 GND (108.550,125.300), pin 5 VBUS (110.850,125.300). C28 is 22 µF on **3V3**, with GND at (104.225,124.100).

Fresh native collision confirms U7's retained 0.127 mm B.Cu route directly overlaps existing GND via `c189d3e3…` at (106.775,125.975), diameter/drill 0.450/0.200 mm. The route reaches the via-center projection after 1.996190 mm; lateral offset is 0.141 mm. Adding the track half-width, 0.0635 mm, remains inside the via radius, 0.225 mm. U7, C28 and that via touch the same stored B.Cu GND polygon; the via contacts both main planes. The proposed longer shield bridge is not U7's sole plane-return path.

All four plated J6 shield EPs at x=106.000/110.800, y=127.650/131.950 physically contact both main planes. In1/In4 use 0.250 mm thermal spokes, not solid pad attachment. At the upper-left EP, N/S/W/E thermal-gap stations each retain approximately 0.249 mm filled span at 0.001 mm sampling. Lower EPs already lack the south station near the board edge; N/W/E remain.

The historical CC1 move to (107.020,127.320) implies a 0.425 mm zone antipad with the source's 0.200 mm zone clearance. The upper-left EP east-spoke midpoint (106.775,127.650) lies about 0.411 mm away, inside this antipad. That spoke can be trimmed or lost after refill. The other three contacts are clear of this moved via.

Historical shield-donor arithmetic changes 1.816 mm B.Cu to 0.787722 mm B.Cu + existing via + 1.845603 mm F.Cu. Both retain 0.127 mm width on 35 µm copper. These parallel-path changes are real even when DC connectivity survives. ST emphasizes short I/O, VBUS and ground-plane-to-GND-pin paths to limit parasitic overvoltage; these geometric checks provide no system ESD rating. [ST USBLC6-2 DS4260 Rev 7, §2.3](https://www.st.com/resource/en/datasheet/usblc6-2.pdf)

Recommendation: reconsider this only through a complete newly validated USB transaction. Require U7-to-existing-via contact, the upper C28 junction, full plated EP entry and finite upper-left EP N/W/S contacts on both main planes after refill; record whether the east spoke survives and check all four EPs. Reject any variant that relies solely on the new thin bridge after losing these local alternatives.

## Deliverables and unchanged limits

- `fresh-batch35-geometry.json`: exact source UUIDs, physical contacts, parts/nets, per-plane spokes, projection samples and rejected-candidate evidence
- `fresh-derived-measurements.json`: source-bound arithmetic, stack and resistance assumptions
- `recheck_batch35.py`: newly authored, read-only reproducible analysis
- `recovery-manifest.json`: hashes and exact-recovery/new-evidence classification

Stored fills cannot certify a future refill. Complete route acceptance, ESD behavior, power transients, effective capacitor values, USB actual-stack impedance and the previously identified assembly/connector/orientation gates remain open.
