# Coordinated SERVO2/SERVO3 construction basis

Source: candidate37, board SHA256 `2a73d9b7dad3a14b0d00c80e81e0ba8a817b50179c15692aad39fde9920c2115`.

The sealed `plan.json` lists exactly 13 allowed removals and 14 replacement/new route groups. `screen.json` contains the exact-source nominal copper, mask, drill, pairwise logical ownership, actual-pad cut and model guard checks. All those screens passed. `supplement.json` confirms nominal complete connectivity for SERVO2 P0/P1 and SERVO3 P0 and records the proposed GND via's annular overlap with both saved reference fills.

The remaining construction is SERVO3 P1 from the new U12.4 escape via at (14.85, 9.06) to U1.25. Its optional In2 exit ends at (16.5, 9.06). The main worker may omit that dangling exit segment when preparing a routing seed; it must close U1.25 before considering joint adoption.

## Exact scope

- Replace eight SERVO2 P0 objects: the F.Cu entry to (11.01, 12.505), local via, and In3 trunk/tail back to the existing (11.77, 5.49) via.
- Replace two SERVO2 P1 In2 segments between (10.16087, 11.17593) and (12.88099, 12.9545). Preserve its existing F.Cu pad approach and long In2/via/B.Cu MCU continuation.
- Replace only U12.2's two dedicated F.Cu GND tracks and one GND via. Keep C10.2's via and every other nonallowed object exact.
- Add the complete R22.2–U12.4 branch and the U12.4–P1 escape seed. Keep every footprint at its source pose.

This exact conflict group closes the southwest bottleneck that return-only or ordinary-only changes do not close. It is the smallest complete group identified by this bounded construction, not a proof of globally minimum ripup count.

## TVS return geometry

Before: 0.25 mm wide, 2.192 mm centerline, one 0.45/0.20 mm via at (11.404, 10.7915).
After: 0.25 mm wide, 2.2275 mm centerline, one 0.45/0.20 mm tented via at (11.27, 10.89).
Length increase: 0.0355 mm. No added shared serial return segment is proposed. The new annulus is entirely within source37's saved In1/In4 GND fills, but fresh saved-board GND continuity, refill necks and reference coverage must be checked. Connectivity alone does not establish transient return quality.

## Margins and limitations

The narrowest new-to-existing copper clearance is the new GND via to U12.1: 0.1271174 mm. That is only 0.0001174 mm above the 0.127 mm minimum; this is a nominal construction candidate, not a manufacturing-margin claim. Native geometry verification is mandatory. Source native maximum polygon error is 0.00001 mm.

The exact actual-pad outside gaps are 0.132 mm at U12.3 on F.Cu and 0.533 mm at U12.4 on F.Cu for the proposed branches. The minimum new-via drill gap is 0.380517 mm. All existing model37 via guards and native-derived rule guards were screened. Passing those guards does not prove post-refill critical-reference/antipad geometry.

No live board, routing model or shared helper was changed. No JVM, KiCad, FEM or geometry maze search was run. The current owner coordinated helper only covers SERVO2 and must not be silently generalized to this ordinary-plus-GND change.

## Sealed files

- plan.json: `1c359be7580340a182738f556cb9becb22106d66d88b06b011de61a263c81f88`
- screen.json: `8c72c56fd3f766620c42c8ff717f30a487896f2aab7c64ea62aff25f0cd02101`

Do not rerun `write_plan.py` against a different source or overwrite these sealed files. Any refinement should be a new, clearly identified output.
