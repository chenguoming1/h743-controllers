# Continuous-VX child: source-bound copper and barrel review

## Decision summary

**V2 removes both identified PCB distribution bottlenecks:** the original four-servo0.50mm daisy-chain is paralleled by a broad front VX sheet, and the V1 split between ESC/RPM is removed. The actual saved V2 front VX fill is one connected region. This is a materially better copper topology for the selected compact board and standard servo plugs.

The10A pad-current benchmarks have modest calculated board voltage drop and dissipation under the stated fixed-temperature assumptions. **They do not qualify10A continuous operation through the retained header, factory BEC leads or standard servo contacts.** They also do not predict equilibrium temperature or establish any25A pulse duration. Connector, harness, solder-joint and thermal evidence remain release blockers.

For the uneven10A benchmark (servos4.5/1/1/2.4A plus a fixed1.1A main-board VX allowance), conservative60µm copper/80°C conductor/95%IACS/18µm barrels gives:
- SBUS-only input: **37.734mV board-only drop** to the lowest servo, **0.17348W sheet +0.16434W barrels**
- ESC-only input: **28.660mV board-only drop**, **0.08316W sheet +0.16433W barrels**

Those drops are measured in the model from the surviving input's actual positive/return PCB-pad pair to the servo PCB-pad pair, excluding the illustrative harness/contact drop. Actual servo terminal voltage includes additional unmodeled output wiring and contacts.

## 1. Exact scope and source identity

Final evaluated child:
`candidate-continuous-vx-unfinished/hardware/header-board/nexus-header-board.kicad_pcb`

SHA-256: **b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6**

This is the compact matched-fit V2. It is separate from:
- Original stage10 child: bfec2a120fbda6c97c1f8a36dfff6a35337e13ab1c3af63abb987f529d761403
- Copper-only prototype extracted but not accepted as final:31340ed282ebbbea055806e7202a78dc51ebfc305f4dc800054c1522ae7d7357
- Matched-fit V1 rollback, independently modeled:624e53e3de157331bd17a444e6f9c813a1ef21cab0b007a02c1a87fb11f8d869

The child worker reports native V2 DRC0errors/0opens, with inherited advisories. This reviewer independently reads the saved source and fills, but does not substitute that reported DRC result for a thermal or current rating. Main-board geometry was not included in this new sheet solve. The1.1A abstract main input is applied at child joint lands; main PCB voltage loss, actual component demand, joint solder and current sharing through the real main board remain outside the model.

All work was read-only. No PCB, schematic or manufacturing setting was changed by this audit. V1 outputs and their scripts are preserved by `V1-ROLLBACK-SEAL.json`; V2 has separate files.

## 2. Saved topology and actual conduction paths

The standard child J1 columns remain S1/S2/S3/TAIL/ESC/RPM/SBUS. VX pins are2/5/8/11/14/17/20 and GND pins3/6/9/12/15/18/21. Power holes are1.00mm bore with1.50mm circular lands and2.54mm pitch.

The evaluated feed mapping is ESC14/15 plus unused SBUS20/21, with verified polarity/fit still required. No second independent BEC is assumed. No Nano-Fit or XT30 parts are selected in this source.

- **VX:** one F.Cu sheet connects the seven VX header positions. The old0.50mm left-hand tracks remain inside that larger conductor; their widths no longer define the total path cross-section. ESC signal routing is now B.Cu, eliminating the V1 front-sheet split. The former0.50mm back ESC–RPM power V-bridge is absent.
- **GND:** one F.Cu lower return sheet and **five distinct B.Cu fills**. B.Cu is not treated as a continuous ideal ground plane. Actual header barrels and saved copper connections join the relevant regions. In particular, output and input return barrels can carry substantial current.
- **Main VX narrow-tab branch:** T2's B.Cu route joins the front sheet through three ordinary0.60/0.30mm VX vias at(114.5,104.35),(114.5,104.95),(115.1,104.95). Its lower retained0.50mm B.Cu branch carries the selected T2 main load, not aggregate servo current. K2 provides a broad F.Cu VX tab route.
- **Main return:** T1 is the B.Cu ground joint, K1 its front ground strip. Both have actual copper paths, modeled separately. No ideal short between T1/K1 or T2/K2 is credited.
- Matched-fit small joint lands are1.6×1.546mm; broad strips7.892×1.546mm. Their copper begins0.8mm below the seating root. The model makes each land face equipotential; it does **not** assign a solder-fillet resistance or mechanical qualification.
- Existing unrelated signal geometry and its saved clearances remain in the sheet boundaries. Standalone power vias are included by exact UUID and geometry; signal vias do not become power connections.

Saved child stack:70µm F.Cu,1.44mm dielectric,70µm B.Cu,10µm masks each side, nominal total1.6mm including masks. The60µm screen is a proposed minimum finished-copper acceptance condition, not a fabrication guarantee. Manufacturing tolerance, etch undercut and actual plated-wall quality still require acceptance/measurement.

## 3. Electrical model and its limits

Two saved-copper grids,0.10 and0.075mm, were solved separately for VX and GND. Exact stored polygon boundaries, holes, tracks and lands form the mesh. Copper islands without any relevant terminal are excluded; separate connected regions are never silently shorted.

Each annular land **face** is an ideal electrode. Opposite faces are connected through explicit barrel resistors, rather than the ideal F/B shorts used in the original quick audit. This still omits within-land crowding, pin resistance, mating contacts, solder resistance and real current entry along a soldered barrel.

Header barrels use1.00mm finished bore and nominal1.6mm length. New VX via barrels use0.30mm bore and the same nominal length. Wall thickness is screened at18 and20µm:

R = ρL / {π[(d/2 + wall)² − (d/2)²]}.

Copper resistivity usesρ20=1.724×10⁻⁸Ωm and coefficient0.00393/°C. Material cases are70µm/20°C and70µm/80°C at100%IACS, plus60µm/20°C and60µm/80°C at95%IACS. Temperature is prescribed conductor temperature, not a solved temperature rise.

A1mm/18µm wall barrel is0.479mΩ at20°C/100%IACS and0.623mΩ at80°C/95%IACS. A20µm wall reduces the latter to0.560mΩ. Actual finished thickness tolerance and local plating defects are not resolved. Barrel length scales resistance linearly; the nominal1.6mm calculation is not a maximum-thickness fabrication bound.

The [JLCPCB plating guide](https://jlcpcb.com/blog/mastering-pcb-plating) distinguishes20µm average from18µm thinnest-point Class2 copper. It is background for this sensitivity, not lot certification or an accepted fabrication order. [JLCPCB copper-weight guidance](https://jlcpcb.com/help/article/jlcpcb-copper-weight) also does not by itself certify the proposed60µm minimum for this design.

Primary results inject feed and output current at the B-side solder-land electrodes. F-side injection and an ideal-barrel limit are additional sensitivities. Real through-hole pin/solder current distribution lies outside this simplified electrode model; no pin or solder parallel shunt is credited in the finite-barrel runs.

The ideal source is7.4V. Leads and contacts are four independent illustrative resistors:
- Equal: ESC positive/return and SBUS positive/return20mΩ each
- Paired weak SBUS:20/20/80/80mΩ
- Crossed:20/80/80/20mΩ
- Whole-feed loss: surviving positive and return40mΩ each, failed pair open
- Individual degradation: ESC positive or return becomes200mΩ, other conductors20mΩ
- Individual conductor open: only that conductor is removed, other conductors20mΩ

These are test inputs, not measured factory harness resistances or guaranteed contact bounds. Positive and return sharing are solved independently.

## 4. Load allocations and results

Four allocations are retained:
1. Synthetic balanced PCB bench:2.5/2.5/2.5/2.5A servo outputs, total10A. **2.5A is not a chosen per-output limit or claimed operating rating.**
2. Uneven bench:4.5/1/1/2.4A servos plus1.1A main VX load, total10A. Endpoint servo currents are illustrative, not continuous servo ratings.
3. Moderate servos only:1/1/1/0.5A, total3.5A.
4. Moderate plus an illustrative1.1A main allowance: total4.6A.

For allocations2and4, the entire main allowance is tested separately at T2/T1 and K2/K1. These expose both joint paths without inventing an ideal main-board bridge. The main allowance is a **current bound at loaded VX voltage**, not nominal7.4V constant-power accounting. Real converter/receiver/FC demand must stay inside it as VX droops. At8.9A servos, there is only1.1A remaining within the10A BEC continuous budget; two1A,5V accessories already require at least1.351A from an ideal7.4V source, before FC demand, and do not fit.

### Uneven10A, conservative material, main load at T2/T1

The following uses60µm copper,80°C,95%IACS,18µm barrels,0.075mm mesh and B-face injection. Voltages include the stated illustrative upstream lead/contact loss; sheet/barrel columns exclude it. External servo output leads/contacts are not included.
| Feed case | Max feed conductor A | Min servo V | Main joint V | Sheet W | Barrels W | Lead/contact W |
|---|---:|---:|---:|---:|---:|---:|
| both_equal20m | 5.064 | 7.1754 | 7.1816 | 0.1049 | 0.1020 | 2.0002 |
| both_paired_weak_SBUS | 7.974 | 7.0550 | 7.0611 | 0.0866 | 0.1240 | 3.2002 |
| both_crossed_ESC_return_weak | 7.970 | 7.0518 | 7.0580 | 0.1182 | 0.1236 | 3.2007 |
| ESC_pair_open | 10.000 | 6.5623 | 6.5687 | 0.1735 | 0.1643 | 8.0000 |
| SBUS_pair_open | 10.000 | 6.5713 | 6.5774 | 0.0832 | 0.1643 | 8.0000 |
| ESC_positive_degraded_200m | 9.053 | 7.0893 | 7.0957 | 0.1260 | 0.1225 | 2.8187 |
| ESC_return_degraded_200m | 9.046 | 7.0884 | 7.0946 | 0.1358 | 0.1224 | 2.8187 |
| ESC_positive_open | 10.000 | 7.0694 | 7.0759 | 0.1327 | 0.1332 | 3.0002 |
| ESC_return_open | 10.000 | 7.0682 | 7.0744 | 0.1456 | 0.1332 | 3.0001 |
### Board-only single-feed voltage drop

Input reference here is the surviving input PCB positive/return pad pair, so the0.8V illustrative upstream drop at10A is excluded.

| Allocation | Input remaining |70µm20°C drop to worst servo |60µm80°C drop |60µm80°C sheet / barrel loss |
|---|---|---:|---:|---:|
| Balanced10A | SBUS |24.599mV |34.698mV |0.16886 /0.15751W |
| Balanced10A | ESC |18.592mV |25.582mV |0.07771 /0.15750W |
| Uneven10A incl.main | SBUS |26.878mV |37.734mV |0.17348 /0.16434W |
| Uneven10A incl.main | ESC |20.899mV |28.660mV |0.08316 /0.16433W |
| Moderate3.5A servos | SBUS |8.860mV |12.500mV |0.02158 /0.01939W |
| Moderate3.5A servos | ESC |6.758mV |9.309mV |0.01041 /0.01939W |
| Moderate+main4.6A | SBUS |10.864mV |15.310mV |0.03746 /0.03279W |
| Moderate+main4.6A | ESC |8.128mV |11.158mV |0.01856 /0.03279W |

All rows use18µm barrels and B-face current injection. Voltages at the main joint are included in the machine-readable results, but voltage at actual main-board ICs is not established.

In the same balanced10A conservative benchmark, V1 SBUS-only sheet+barrel loss was0.56611W. V2 reduces it to0.32638W. ESC-only remains about0.23521W. V1's main input and its original mandatory back bridge are preserved only as rollback/comparison evidence; no V1 rating is inherited.

### Local current/area metrics, not thermal ratings

No mesh-pixel peak current density is advertised. Such peaks depend on raster alignment and on the deliberately ideal land electrodes. Instead:
- A1.00mm bore with18µm uniform plated wall has0.05757mm² axial copper area. A surviving feed's modeled10A barrel current therefore averages **173.7A/mm² over that wall**;4.5A output current averages78.2A/mm². This does not resolve local thin spots or solder/pin sharing.
- Each0.30mm/18µm new VX via has0.01798mm² wall area. With the entire1.1A main load on T2, their largest modeled individual currents over the studied feed profiles are about0.428/0.360/0.364A. The largest area-average is **23.8A/mm²**. They are not assumed to split equally.
- The retained0.50mm B.Cu section below their junction carries1.1A in this allocation. At60µm its area is0.030mm², giving **36.7A/mm²** section-average. This branch does not carry the10A servo aggregate in V2.
- Saved F.Cu VX cross-sections sampled every0.002mm within the four inter-land gaps have minimum total filled widths2.804/3.443/3.443/3.444mm. Under the uneven servo allocation, their net currents are4.5/5.5/6.5/8.9A, giving area-average26.7/26.6/31.5/43.1A/mm² at60µm. These are averages over defined inter-land cuts, not worst edge/annular current crowding or thermal limits. `v2-copper-sections.json` records exact coordinates and intervals.

## 5. Numerical checks and remaining qualification

The saved run contains1080 records including repeated baseline/sensitivity combinations. Maximum two-grid load-voltage change is **0.405mV**, with up to0.00342W sheet+barrel loss change. Changing18to20µm wall gives up to1.875mV load-voltage change. F- versus B-face electrode injection changes up to18.233mV and0.16321W, demonstrating why actual solder/pin entry cannot be hidden in an ideal-pad claim. These sensitivities are not rigorous discretization or manufacturing error bounds.

For finite18/20µm barrel cases, maximum circuit residual is1.16×10⁻¹⁰A and maximum power-balance discrepancy1.92×10⁻⁷W. The ideal-barrel sensitivity is more ill-conditioned and is retained only as a limiting comparison. Small residuals verify circuit bookkeeping, not the omitted physics.

**Contact and harness limits remain decisive.** The exact selected [Hanxia C32713294 datasheet](https://www.lcsc.com/datasheet/lcsc_datasheet_2407231541_hanxia-HX-PZ2-54-3x7P-ZZ_C32713294.pdf) publishes3A AC/DC and≤20mΩ contact resistance without adequate mated-contact, simultaneous-contact, thermal or peak-duration qualification. The benchmark requires5A-scale contacts even with balanced dual feeds, around8–9A with unequal/degraded conductors and10A with one surviving path. Standard factory female contacts, crimps and BEC wire gauge/length are unbound. Output4.5A illustrations are likewise unqualified. Better PCB copper does not upgrade these parts.

At10A, the illustrative40mΩ positive plus40mΩ return dissipate8W outside the PCB. That result is intentionally shown separately; acceptable PCB millivolts cannot be mistaken for acceptable lead/contact heating. At moderate3.5A, a lost feed still carries3.5A through each remaining contact before any FC load, above the header's only published3A figure.

The [Hobbywing Platinum120A V4](https://www.hobbywing.com/en/products/platinum-120a-v471) BEC is10A continuous/25A peak; the reviewed manufacturer information does not bind the peak duration. No25A pulse qualification follows from this10A DC study. Motor/battery current does not traverse this FC.

**Proposed bench condition:**40°C ambient in the actual intended enclosure/airflow, with sensors on the input/output contacts, feed barrels, VX sheet restrictions, main branch and joints. The model's80°C conductor case is40K above that proposed ambient, but it is not a predicted rise, a permission to run every component at80°C, or an approved equilibrium criterion. Establish acceptable component/conductor limits and duty cycles before testing; use whichever limits are tighter. Measure both-feed, each whole-feed-open and asymmetric-conductor conditions only with a separately appropriate test fixture and qualified current-entry hardware. Do not infer that unqualified factory plugs should be stressed at10A.

Before release, bind actual factory harness/contact parts and allowable loads/durations, obtain accepted minimum copper/plating/thickness tolerances, inspect representative solder and barrel sections, measure four-wire path resistance and current sharing, and scope voltage at actual servo/FC terminals during startup, synchronized loading and feed interruption. Main-board DC power/conversion, thermal coupling, mechanical fatigue, EMI and flight reliability need separate evidence.

## Evidence files

- `v2-geometry.json`: exact pads, tracks, vias and stored fill polygons; source hash
- `v2-sheet-model.json`, `power_sheet_model.py`: per-face sheet matrices, no source edits
- `v2-bench-cases.json`, `solve_bench_cases.py`: current allocations, every feed and material/barrel sensitivity, per-barrel currents, separate losses and balances
- `v2-primary-table.md`, `v2-exact-key-results.txt`, `v2-result-sensitivities.json`: compact reproducible results
- `v2-copper-sections.json`, `measure_sections.py`: defined local section-average metrics
- `v2-VX-saved-copper-screen.png`, `v2-GND-saved-copper-screen.png`: reviewed model inspection plots, not fabrication exports
- `V1-ROLLBACK-SEAL.json`: preserved V1 source-bound model and scripts

The final source hash is checked again in the seal. Any later copper, fill, stack, pad or via change requires a new binding and re-evaluation.
