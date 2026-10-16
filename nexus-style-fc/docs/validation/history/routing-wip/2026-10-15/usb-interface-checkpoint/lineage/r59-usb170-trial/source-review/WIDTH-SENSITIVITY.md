# Bounded inner-width sensitivity, separate from the complete .150 mm baseline

Parent selected the .170 mm variant for a conditional native trial, using `NATIVE-170-OVERLAY.json`; no electrical acceptance is implied.

The .160, .170 and .180 mm In3 trunk variants all pass the read-only retained-object and unchanged-port/MCU screen at .127 mm clearance. None replaces the source or the complete .150 mm transaction. Exact separate geometry is in `width-160-variant.json`, `width-170-variant.json` and `width-180-variant.json`.

| Inner width | Full envelope | Minimum foreign copper gap | Covered In2/In4 proxy | Remote In1/In4 proxy | Minimum inside copper bend radius |
|---|---:|---:|---:|---:|---:|
| .150 baseline | .427 mm | .1715 mm | 90.6–101.0 Ω | 104.3–115.3 Ω | .0365 mm |
| .160 | .447 mm | .1615 mm | 88.4–98.3 Ω | 102.8–113.4 Ω | .0265 mm |
| .170 | .467 mm | .1515 mm | 86.3–95.8 Ω | 101.5–111.7 Ω | .0165 mm |
| .180 | .487 mm | .1415 mm | 84.4–93.5 Ω | 100.2–110.1 Ω | .0065 mm |

The limiting foreign object is the retained IMU_INT via `33fe43e9-c4cc-45bc-a9cc-df1353a05aaf`. These are geometric gaps, not fabrication tolerances. Every width retains the original .127 mm intended pair gap. Analytic impedance intervals are the same deliberately approximate sensitivity cases as the main report; they are not confidence intervals or field-solver output. Representative covered/remote values are 90.6/105.4, 88.5/104.0 and 86.5/102.7 Ω. Wider copper reduces remote-section impedance but lowers the nearer-referenced sections too, so it does not remove the reference-dependent discontinuity.

## Explicit finite transitions

Outer launches and their original handoff ports remain .150 mm. Each rail has two explicit .200 mm axial copper trapezoids, whose inner edges stay vertical at ±.0635 mm from the pair center and whose outer edges expand to the wider width. This maintains the actual .127 mm copper gap rather than approximating a taper with a constant-width diagonal track.

- South pair-center x109.65: unchanged narrow ends at y124.000, wide ends at y123.800.
- North pair-center x110.90: unchanged narrow ends at y110.850, wide ends at y111.050.
- Narrow ports remain DP/DM (109.5115/109.7885,124.0) and (110.7615/111.0385,110.85).
- Wide centerlines are pair-center x ± (width+.127)/2. Exact four vertices per taper and all wider line/arc primitives are in each JSON.

Both tapers fit the already straight end portions; they overlap the wider round-ended primitive and unchanged finite terminal copper. The .200 mm value is a construction coordinate, not a route-length limit. These shapes have not been converted to native KiCad net copper, and this study does not endorse arbitrary zone-based trace construction. A native implementation must preserve their geometry and connectivity explicitly, then repeat complete-port DRC/refill/return checks.

The .250 mm pair-center bend radius stays fixed. Widening shrinks the innermost copper radius to only 6.5 µm at .180 mm. That is an explicit etch/corner and discontinuity concern even though the analytical envelopes do not intersect; increasing bend radius was not included because it would change this bounded topology.

## Electrical disposition

A layer-specific width is a genuine option: .160–.180 mm can be carried into actual-stack extraction without silently narrowing the outer launches or moving neighboring parts/power/returns. This study does not select a fabricated impedance from the proxy. The .180 mm case is useful as the wider sensitivity endpoint, but its near-reference under-impedance tendency and very small inside bend radius prevent an unqualified recommendation. Six independent In2 crossings and the uncoupled compact launch remain.

Each variant additionally records its own saved In1/In2/In4 reference projections and component IDs, including the variable-width tapers. This does not establish post-refill finite return connectivity. The concrete next engineering choice remains extraction/qualification of the actual post-refill multiconductor cross sections and transitions before adopting a width. No arbitrary length or skew acceptance gate is introduced.

Saved-fill follow-up for .160/.170/.180: In1 and In4 cover all seven sampled rays for each variant; In2 center absence remains 5.370791 mm and any-ray absence is 7.484618/7.543611/7.603605 mm respectively. These are source projections before proposed refill.
