# Native I2C and critical-signal reference screen

This is a read-only conditional check for the final BARO_SCL/BARO_SDA route plus saved-reference geometry for USB, HSE and all five IMU nets. It does not change stock firmware, the PCB, the project or R7/R8. The current evidence is an **unfinished-board checkpoint**, not a final signal qualification.

## Current result

The inspected KiCad 10.0.6 unfinished 13-open board is SHA-256 `14dea1df09ea9d800bf66a6d74eb5f0dac33a8705161e9ed1a02f2e11f3b58b8`.

- SCL contains exactly U1.61, U4.4 and R7.2; SDA contains exactly U1.62, U4.3 and R8.2.
- Both three-terminal nets are complete and pass the unchanged strict clean-tree extractor. SCL has 13 tracks totaling 19.596154 mm; SDA has 20 tracks totaling 22.600469 mm. Capacitance and RC values remain null because required bounded material/manufacturing/device inputs are unresolved, rather than because routing is incomplete.
- The exact 41-to37 comparison intentionally reports generic critical-object equality false because it includes the newly routed I2C nets. Every changed selected-object UUID belongs to BARO_SCL/SDA; existing non-I2C critical objects and reference metrics remain exact. The scoped receipt is checks/checkpoint43-integration/intentional-i2c-geometric-review.json. SCL retains 0.0000101900912267 mm² outside-window width loss; no outside-window centerline gap is hidden.
- R7/R8 native values are both `2.2k / 1%`.
- The existing `checks/critical-net-connectivity.json` is bound to this same PCB and reports no faults in its stated scope. It has not been substituted for a global DRC.
- Fresh saved-plane projection shows HSE_IN/HSE_OUT/HSE_XTAL_OUT have no missing adjacent In4.Cu GND beneath their centerlines. Their complete native planar lengths are 6.428539 / 5.370822 / 3.279505 mm.
- USB_P/USB_N complete native planar lengths are 18.101786 / 18.712550 mm. Missing adjacent-GND centerline projection totals are 0.705014 / 2.478245 mm, including via antipads. All of these missing intervals lie in actual saved holes within the local own-via windows; the length outside those windows is zero. Nine exact track/layer/coordinate intervals are in `USB_reference_interval_review` in the JSON report. Local windows have radius 0.362 mm = 0.225 mm land radius + 0.127 mm native clearance + 0.010 mm polygon-classification allowance. Merged-hole extensions are not exempted. The nearest GND vias geometrically tying In1/In4 are 0.603515 mm from the P transition and 1.466640 / 1.429490 / 1.100000 mm from the N transitions at (34.27,12.65), (36.5,12.95), (39.35,13.35). These are geometry facts, not impedance or return-current passes. The intentionally narrow centerline-tree model refuses existing off-center USB contacts; native connectivity is independently complete. Do not infer a USB disconnection from that modeling limitation.

The historical `critical-verification-trial15/usb-reference-audit.json` uses board hash `e9a61776…` and cannot qualify this board. Its geometric findings are context only. The new report retains exact track IDs, lengths and layer projections rather than copying the historical pass.

## Expanded physical reference review

`critical-reference.json` is bound to the same 13-open board and adds finite-width and drill-aware inspection. It independently subtracts actual native drill polygons on their finite spans from the saved GND copper. All 118 accepted GND plated ties have positive annular area against both actual saved GND zone fills, excluding their drill holes, and native barrels spanning In1/In4. The USB helper now uses this same criterion: a GND land merely intersecting a union containing itself cannot qualify a tie. The previously reported nearest USB ties still qualify under the corrected criterion and retain their stated distances.

All HSE and IMU nets are natively connected. HSE has no missing In4 GND beneath either centerlines or full trace copper. Physical drill subtraction introduces no additional critical-track projection gap on this checkpoint.

| IMU net | Native planar length, mm | Missing centerline projection, mm | Missing trace-width projection, mm² | Nearest verified GND via at its F/B transition, mm |
|---|---:|---:|---:|---:|
| CS | 10.306701 | 0.705330 | 0.102067855 | 1.667707 |
| INT | 7.578768 | 0.706778 | 0.101985607 | 1.490072 |
| MISO | 3.961179 | 0.706091 | 0.112466735 | 2.748596 |
| MOSI | 3.804632 | 0.708366 | 0.101933689 | 2.309772 |
| SCK | 7.101470 | 0.708919 | 0.112403248 | 0.986266 |

Every IMU missing centerline interval remains within its bounded same-net via window. Strict saved-hole boundary containment is unresolved for the MOSI boundary pieces because exact polygon predicates disagree; the current extended comparison below retains that limitation. These are location classifications, not electrical passes. The full trace width reveals a **pre-existing IMU_CS sliver of 0.000039505315 mm² outside its own-via windows**. F.Cu track `2c8bdb06-a4fb-4246-a69b-3fe2bfb0bac5`, from (23.159999, 9.125) to (21.959999, 8.975), width 0.127 mm, overlaps the In1 saved hole containing IMU_SCK via `eec68274-8fe5-464d-ad04-2d6f497f6461` at (22.8, 9.5). The sliver bounds are x=22.828047–22.862468 and y=9.147500–9.151803 mm; its centerline remains fully backed by saved GND. This is neither its own antipad nor a new regression, and no arbitrary pass threshold is applied.

`comparison-76-to-75.json` shows that the added FLASH_WP_N through-vias at (30.216310, 24.559960) and (31.500000, 20.985300) remove about 0.785217153 mm² of GND per reference plane but do not change any USB/HSE/IMU projection metric. The nearest critical trace-width distance to newly missing GND is IMU_INT: 7.136058 mm on In1 and 5.194400 mm on In4. All critical copper objects remain byte-identical in the native exports. The earlier 77-to-76 ADC_DIV_MID vias likewise introduced no finite-width crossing; their nearest newly absent-GND distance to IMU_INT is 0.288993 mm on In1 and 0.104486 mm on In4. These distances carry no universal acceptance threshold.

`comparison-75-to-70.json` records the two further ADC_BEC/NRST vias and identical critical signal copper. Saved physical GND decreases by 0.785217154 mm² per reference plane. In1 has zero critical trace-width overlap with that difference; In4 records a 5.84393e-9 mm² overlap under IMU_INT. Its total missing centerline projection changes by 2.62606e-7 mm and missing-width area by 5.52335e-10 mm². All missing IMU_INT centerline/width regions remain in its bounded own-via windows; the separate pre-existing IMU_CS sliver is unchanged. These small represented differences are preserved without inventing an acceptance threshold.

`comparison-70-to-69.json` verifies that the two added outer ADC_BUS tracks preserve every existing copper object, drill, reference-plane object and saved zone fill exactly. That comparison is historical source69 evidence. Fresh native snapshots and both current signal/reference reports are bound to the 13-open board.

`comparison-69-to-power19.json` retains the coordinated BEC/PERIPH/USB_RAW reroute and actual refilled GND changes. All critical copper and projection metrics remain identical. `comparison-power19-to-62.json` independently confirms the seven subsequent outer signal closures leave all critical objects, saved GND geometry and projection metrics exactly unchanged. The existing IMU_CS sliver and all qualification limits remain visible.

`comparison-62-to-60.json` confirms the next two F.Cu SBUS_HV/RPM_LV connections preserve all critical objects, saved GND geometry and projection metrics exactly. Finite pad-entry restoration was checked independently of DRC.

`comparison-60-to-57.json` records one new ESC_MCU via and changed saved GND fills: each reference plane loses 0.392608639433 mm² and gains a represented 0.000000021989 mm². All critical copper/projection metrics remain identical. Newly absent GND has zero overlap with critical trace widths; nearest distances are 5.628648 mm from USB_P on In1 and 3.569891 mm from HSE_IN on In4. These geometry facts do not transfer the old numerical power/VCAP result to this changed board.

`comparison-57-to-55.json` records the subsequent NRST via: another 0.392608544409 mm² removed per GND reference plane, zero added fill, and zero critical trace-width overlap. All critical copper and projection metrics remain identical. Power/VCAP revalidation remains pending.

`comparison-50-to-49.json` records the coordinated SERVO2 rewrite and two added vias. Critical copper and missing-centerline geometries are unchanged. Saved refill differences change missing width by +6.1744e-9 mm² for IMU_MISO and -6.8386e-10 mm² for USB_N. `reference-change-50-to-49.json` verifies the entire changed regions lie within unchanged pre-existing same-net via windows intersected with actual before/after saved holes; all missing width outside those windows is geometrically identical. No contour was repaired, snapped or discarded, and no value was rounded to zero for acceptance. The current source still needs numerical power/VCAP revalidation. `review_reference_window_change.py` reproduces this classification from the two native snapshots and boards.

`comparison-44-to-42.json` records the completed coordinated SERVO2/SERVO3 revision. Critical copper is unchanged, while the native refill retains +4.798571699993204e-7 mm MOSI missing centerline, +1.8575200405601677e-8 mm² MOSI missing width and -6.17441728301138e-9 mm² MISO missing width. Independent source-bound classification examines all 72 critical reference tracks and places all changed centerline/width geometry inside unchanged own-via windows. It does not claim exact centerline equality or strict actual-hole containment: four boundary-predicate disagreements remain explicit in `reference-window-classification-44-to-42.json`. The MOSI/MISO hole now merges with two more via holes, totaling 1.5612640944305003 mm²; its extensions receive no exemption. Each plane loses 1.632326549368308 mm² and gains 0.08155315009880729 mm². Whole-plane changes still require fresh numerical power/VCAP and functional assessment. The older exact-centerline receipt remains unchanged; no contours or numerical differences were repaired, discarded or zeroed.

Twenty-seven controls pass: the original 18 remain unmodified and 9 focused controls cover false self-land ties, annular contact, finite barrel span, drill-only overlap, tangency, NPTH drilling, full-width defects, bounded merged-hole extension and sloped interval length conservation. No impedance, timing, signal integrity, oscillator, IMU performance or AC qualification follows from this geometry. The board and I2C qualification remain unfinished.

Run the additional screen against the same freshly exported snapshot:

```sh
python signal-review/native/check_critical_reference.py \
  --board hardware/f722-heli.kicad_pcb --snapshot /tmp/f722-signal-snapshot \
  --out /tmp/f722-critical-reference.json

python -m unittest discover -s signal-review/native -p 'test_*.py' -v
```

`compare_reference_geometry.py --help` gives the read-only snapshot/report comparison interface. Historical snapshots must be bound to their original board bytes, not a later canonical board. The large native snapshots stay disposable; compact report source hashes identify their exact bytes.

## Reproduce after routing

Keep these sources together in, for example, `layout-revision/signal-review/native/`. They depend on the existing `layout-revision/scripts/export_native_copper.py` and `exact_native_contours.py`; no shared script changes are required. Run from `layout-revision` with KiCad's Python and, separately, Python with Shapely:

```sh
"$KICAD_PYTHON" signal-review/native/export_signal_snapshot.py \
  --board hardware/f722-heli.kicad_pcb --native-tools-dir scripts \
  --out /tmp/f722-signal-snapshot

python signal-review/native/check_signal_geometry.py \
  --board hardware/f722-heli.kicad_pcb --snapshot /tmp/f722-signal-snapshot \
  --requirements signal-review/final-native-i2c-requirements.json \
  --calculations signal-review/stock-i2c-calculations.json \
  --critical-check checks/critical-net-connectivity.json \
  --profile signal-review/native/model-inputs.template.json \
  --out /tmp/f722-signal-review.json

python signal-review/native/test_signal_geometry.py -v
```

In this executor, KiCad's Python is `../kicad10-runtime/python` relative to the work root, and analysis uses `PYTHONPATH=python-deps python3.12`. The snapshot contains a large disposable native geometry file. It need not be committed; its hash and exporter hashes are recorded in the compact report. The scripts refuse source changes during export/check, stale geometry, stale stackup binding and changed stock allocation/Rmax inputs. They never refill saved zones or save a board.

Exit codes: 0 means both conditional engineering estimates were produced within the provisional 50 pF/100 ns screens; 2 means incomplete routing, missing inputs or unsupported geometry; 3 means a conditional estimate exceeds the screen. An unexpected error or stale-source rejection exits 1. **No exit code establishes device, USB, clock or flight qualification.** `qualification_pass` stays false because the stock device/bench gaps remain.

## What the report measures

Every native track/arc is counted once in whole-net lengths by layer, including the complete pull-up branch, overlap inside pads and any extra copper. This is not a shortest MCU-to-sensor path. Widths, all terminal pad shapes/sizes/poses, native component membership, every via's diameter/drill/span and exact source hashes are retained. Track-level projections show copper on **each adjacent layer**, including which projected nets are GND, power or other signals. Nearest same-layer foreign copper is identified by UUID/net/gap.

Straight track centerlines are split at intersections and clipped at actual pad/via lands. Conductive lands are contracted to graph nodes. The report identifies branch nodes, dangling nonterminal endpoints, loops and the unique pull-up branch in a complete tree. Branch/path lengths exclude travel inside a land; the native whole-net length includes it. A source-to-sensor path alone cannot establish total load. Copper-only/tangential contacts, arcs and signal zones explicitly refuse the narrow topology/model instead of receiving an inferred pass. Exact native arc lengths and chorded reference projections remain available.

## Inputs that are still missing

`model-inputs.template.json` is deliberately unfilled. Each numeric input needs a source or an explicitly reviewed engineering assumption, with its applicable manufacturing/environmental range:

1. **Actual stackup identity and each layer's thickness range.** The native nominal stack is the calculator's JLC06101H-3313: outer PP 0.0994 mm, cores 0.25 mm and central PP 0.2028 mm. The manufacturer order diagram instead showed 0.21040 mm central PP. Resolve the production version. A total board thickness of 1.03 mm ±10% does not establish individual dielectric or copper min/max thicknesses.
2. **A relative-permittivity ceiling** covering all dielectric, soldermask, coating, underfill and surrounding material over the relevant frequency, temperature and moisture ranges. The derivation requires a pointwise permittivity ceiling (or the largest tensor eigenvalue for an anisotropic model), including glass/resin constituents; a bulk effective Dk requires an explicit homogenization assumption at these feature scales. Native 4.1/4.23/4.4 values are nominal; none is a documented maximum. The template provides 4.1/4.6/5.5 sensitivity parameters, not manufacturer bounds. Values below an actual material permittivity are sensitivity examples only.
3. **Copper edge growth and registration bounds.** Supply separate maximum outward error for signal and foreign copper and the maximum relative interlayer displacement. These must cover etch/feature-placement/plating effects; the native 10 nm polygon approximation is not a fabrication tolerance.
4. **External conductor proximity.** Supply a lower bound from every modeled track centerline/via axis to any package, fixture, enclosure or other conducting material absent from the native PCB copper. Package/assembly parasitics remain an allocation, not a manufacturer guarantee. If this distance cannot be justified, the model refuses a bound.
5. **Probe and extra model/assembly allowance.** Record the actual probe maximum or explicitly unprobed case, plus any added allowance. Zero must be deliberate and justified. The existing 10 pF STM32 + 10 pF DPS368 + 5 pF pad/pull-up/assembly allocations are not verified component maxima.

See the existing `docs/jlc-stackup-evidence.md`, `signal-review/stock-i2c-review.md` and their pinned sources. This check makes no new fabrication-tolerance claim. A fully populated profile may explicitly use assumed engineering corners and show permittivity sensitivity; label its output accordingly. `production_stackup_confirmed=false` remains visible.

## Conditional conservative route model

The underlying Dirichlet variational and conductor-enclosure principles are described in Jackson, *Classical Electrodynamics*, 3rd ed., section 1.12 and problems 1.17–1.18, in the [publisher's chapter excerpt](https://catalogimages.wiley.com/images/db/pdf/9780471309321.excerpt.pdf). They provide an upper bound from an admissible trial potential, including all prescribed conductor boundaries. The following covering construction is this tool's explicit engineering implementation of that principle.

For a unit-potential conductor, C equals the integral of epsilon times the squared electric-field magnitude. The true Dirichlet solution minimizes that integral. Cover the track/via volume with spheres of inner radius a. At each center, choose b strictly less than the minimum conservative 3D distance to **every foreign conductor**, including saved zone fills and plated barrels on unflashed layers. Use the radial trial potential:

```
u(r) = 1                                      r <= a
       (1/r - 1/b) / (1/a - 1/b)               a < r < b
       0                                      r >= b
```

This trial is zero on all foreign conductors because its support ends before any of them. It therefore accounts for nearby planes; using the capacitance of an isolated sphere would not do so. With epsilon(x) no greater than epsilon0 × er_max, one sphere contributes at most `4*pi*epsilon0*er_max*a*b/(b-a)`. For overlapping spheres, `u=max(u_i)` remains admissible. Almost everywhere its gradient is one active sphere's gradient, so its integral is no larger than the sum of the individual integrals. That sum conditionally bounds the covered route's static capacitance.

The implementation covers each straight track's rectangular body by successive spheres of radius `sqrt((step/2)^2 + (width_max/2)^2 + (copper_thickness_max/2)^2)`. Two additional spheres cover its rounded ends. It tries several subdivisions and retains the smallest **valid** sum; choosing among valid covers preserves the upper-bound property. The full track is included even inside pads. For a via, the entire span is conservatively replaced with a filled cylinder having the largest land radius, then covered in the same way. Foreign plated lands are conservatively extruded through their native span so an unflashed barrel cannot be omitted.

For track-to-other-layer distances, copper centers are separated using the supplied minimum individual thicknesses. Foreign outward copper error and relative registration reduce lateral separation; signal outward error and maximum thickness enlarge the covering volume. A further 1 nm numerical reserve shrinks b. Via covers conservatively use the closest projected foreign copper on any layer, with no vertical-separation credit. External conductors impose an additional b limit. If `b <= a`, the tool refuses that cover; if no cover fits, it refuses an estimate. Invalid polygons are never geometrically repaired.

All foreign nets are grounded in the static calculation. The ledger uses twice the static route bound as an intentionally conservative screen for equal-amplitude, equal-slew opposite transitions. This is not a bound for arbitrary aggressor slew, ringing, inductance or nonlinear device behavior. The code also exposes the static value separately. Permittivity sensitivity is linear while the supplied geometric bounds stay fixed.

The resulting ledger adds the provisional device/pad allowances, the covered route, probe and extra allowance. It uses external pull-up Rmax = 2244.22 ohms, no internal-pull-up credit, and `tr_30_70 = 0.8473 * Rmax * C`. This remains **estimated under the supplied assumptions and allocations**. A large conservative bound is inconclusive: exceeding 50 pF does not prove the physical board exceeds 50 pF. A tighter supported established extraction or a revised layout may be needed. An unsupported dielectric maximum or an engineering pin allowance cannot become a guaranteed total by passing this calculation.

## Controls and remaining qualification

The original eighteen synthetic tests cover mid-segment branching, full pull-up inclusion, stubs, floating copper, loops, native/topology disagreement, off-center contacts, arc refusal, incomplete-route refusal, exact concentric-sphere capacitance, the distant-conductor limit, dielectric/geometry monotonicity, wire-over-plane and parallel-plate analytical scaling comparisons, close foreign-copper sensitivity/refusal, stale/tampered source refusal, and a merged-antipad control that preserves the distant void as a real interval. The latter two analytical comparisons are limiting sanity checks, not a precision validation against a finite-board field solution. The derivation and admissible boundary/cover conditions carry the conservative claim; these small tests guard its implementation. A complete synthetic ledger still reports `qualification_pass=false`.

Missing DPS368 pin-capacitance maxima, ordinary 800 kHz compatibility and 3.3 V output-low guarantees remain unresolved. Actual installed stock firmware/settings/registers, rail extremes, MCU- and DPS-driven waveforms and first-article error behavior still need the checks specified by the existing stock-I2C review. No hardware, part or firmware change is proposed here.

## Source37 to35 DSM closure

`comparison-37-to-35.json` retains all critical/I2C native copper and both clean BARO trees. Refilled geometry changes SCL missing centerline/width by −4.27721e−7 mm/−1.41570e−8 mm² and USB_N by +2.90241e−8 mm/+1.06245e−8 mm². The fresh source-bound classifier locates all changed projection geometry inside unchanged own-via windows; exact centerline equality and strict actual-hole containment remain false, with four predicate disagreements preserved. This is geometric WIP evidence only. The new BEC bend and five vias require fresh numerical power applicability.

The current35-to34 reference comparison preserves its raw false complete-record equality flag: 83 exported net_code integers changed after the TP5 side move. A separate source-bound exact-record proof confirms identical UUID/net names, physical copper/drills/pads, saved zones and per-net reference reports. No physical or numerical deltas were discarded.

Current source54/14 preserves critical copper and all missing-centerline/outside-own-window geometry against source52/17. `comparison-17-to-14.json` retains the USB_N width delta of 2.6376462125554667e-10 mm²; the exact changed polygon lies within its unchanged own-via window and actual saved hole. The direct final ground reconstruction adds one GND drill and leaves all 1,259 retained signal projections disjoint from that plane change. This is geometric evidence only; R52/ADC_BEC shared-return noise and fresh loaded power/VCAP remain unresolved.
