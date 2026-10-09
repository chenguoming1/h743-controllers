# Native I2C route and reference screen

This is a read-only, narrow check for the final BARO_SCL/BARO_SDA route. It does not change stock firmware, the PCB, the project or R7/R8. The current evidence is an **unfinished-board checkpoint**, not a final signal qualification.

## Current result

The inspected KiCad 10.0.6 board is SHA-256 `1ff8ee645bd5fea7bbbc30cd4e5269aab76a2032efe3e2c4e77a0becd85e9edf`.

- SCL contains exactly U1.61, U4.4 and R7.2; SDA contains exactly U1.62, U4.3 and R8.2.
- Each net has three disconnected pad components, no tracks and no vias. Their zero recorded trace lengths are **not** complete-route results. Final capacitance and RC values are deliberately null.
- R7/R8 native values are both `2.2k / 1%`.
- The existing `checks/critical-net-connectivity.json` is bound to this same PCB and reports no faults in its stated scope. It has not been substituted for a global DRC.
- Fresh saved-plane projection shows HSE_IN/HSE_OUT/HSE_XTAL_OUT have no missing adjacent In4.Cu GND beneath their centerlines. Their complete native planar lengths are 6.428539 / 5.370822 / 3.279505 mm.
- USB_P/USB_N complete native planar lengths are 18.101786 / 18.712550 mm. Missing adjacent-GND centerline projection totals are 0.705014 / 2.478245 mm, including via antipads. All of these missing intervals lie in actual saved holes within the local own-via windows; the length outside those windows is zero. Nine exact track/layer/coordinate intervals are in `USB_reference_interval_review` in the JSON report. Local windows have radius 0.362 mm = 0.225 mm land radius + 0.127 mm native clearance + 0.010 mm polygon-classification allowance. Merged-hole extensions are not exempted. The nearest GND vias geometrically tying In1/In4 are 0.603515 mm from the P transition and 1.466640 / 1.429490 / 1.100000 mm from the N transitions at (34.27,12.65), (36.5,12.95), (39.35,13.35). These are geometry facts, not impedance or return-current passes. The intentionally narrow centerline-tree model refuses existing off-center USB contacts; native connectivity is independently complete. Do not infer a USB disconnection from that modeling limitation.

The historical `critical-verification-trial15/usb-reference-audit.json` uses board hash `e9a61776…` and cannot qualify this board. Its geometric findings are context only. The new report retains exact track IDs, lengths and layer projections rather than copying the historical pass.

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

Eighteen synthetic tests cover mid-segment branching, full pull-up inclusion, stubs, floating copper, loops, native/topology disagreement, off-center contacts, arc refusal, incomplete-route refusal, exact concentric-sphere capacitance, the distant-conductor limit, dielectric/geometry monotonicity, wire-over-plane and parallel-plate analytical scaling comparisons, close foreign-copper sensitivity/refusal, stale/tampered source refusal, and a merged-antipad control that preserves the distant void as a real interval. The latter two analytical comparisons are limiting sanity checks, not a precision validation against a finite-board field solution. The derivation and admissible boundary/cover conditions carry the conservative claim; these small tests guard its implementation. A complete synthetic ledger still reports `qualification_pass=false`.

Missing DPS368 pin-capacitance maxima, ordinary 800 kHz compatibility and 3.3 V output-low guarantees remain unresolved. Actual installed stock firmware/settings/registers, rail extremes, MCU- and DPS-driven waveforms and first-article error behavior still need the checks specified by the existing stock-I2C review. No hardware, part or firmware change is proposed here.
