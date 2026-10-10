# F722 V18: accepted ADC checkpoint, unfinished

V18 is the compact source/evidence delta over immutable V17 for owner-adopted candidate48: **30 opens, 0 native geometric errors, 0 warnings**. ADC_BUS is a complete four-terminal tree through C31.1, R42.2, R43.1 and U1.10. Overall routing, electrical and physical qualification remain unfinished.

Accepted board SHA256: `dcdd0e5655d098ceaffa7f40b6a21f1ca101429ac8eb142c50fa96df86697e68`.
Source candidate47 SHA256: `f7d5731bb0bf1ad314aca6d507da004993671bce413fbdeba545083168e28161`.

The exact transaction adds 12 tracks and 2 signal vias, removes the old C31 ground track and its dedicated ground via, moves R43 on F.Cu from (22.5,17.6,0°) to (22.5,17.9,0°), and moves C31 on B.Cu from (14,24.1,0°) to (15.9,8,180°). The other 154 complete footprint structures remain exact. Source-bound owner receipts preserve native pose prediction, all 156 pose/558 full-pad placement reproduction, and front/back previews.

The packet contains 187 selected source/evidence paths, 13 explicit raw-input exclusions, and standard-library exact recovery of the 61-file paired candidate47 and candidate48 projects. It preserves the constructor, proposal, finite entry/support audits, source-bound owner adoption and classifier, conditional ADC screen, and placement recipe/orchestrator. No unaccepted flash, servo or PORT_C experiments are added. Older accepted source dependencies are inherited from immutable V17. A few historical servo/DSM audit helpers and classifier receipts are retained solely because the accepted ADC handoff or classifier explicitly hash-binds them.

## Results and limits

- All 28 actual support groups are preserved. The support adapter's `typed_audit_binding_checked` remains false; the V18 verifier separately checks the complete wrapper/audit/source binding.
- All 24 new track endpoints are finitely resolved. The audit also contains 7 direct pad-entry, 18 full-width-join and 6 actual-annulus proof records; these overlap and include retained dependents, so they are not a partition of the 24 endpoints. The retained ADC_BUS diagonal's direct R43.1 entry **fails** (0.03521572875253453 mm missing section); its explicit composite entry passes using the new finite pad entry and exact full-width join. The false direct predicate is preserved.
- Actual clamp protection remains **13/22 endpoint cases and 11/20 channels**. The global all-pass predicate remains false.
- Critical signal copper remains exact. Saved ground planes changed. The current owner classifier is bound to `e5b3c1ef472def8d40b5d5f3ba43d817bdcb06d11376cdac8590344b308908da`: all changed critical projections lie in unchanged own-via windows, but exact missing-centerline equality and strict actual-hole containment remain false, with **2 actual-hole predicate disagreements**. Numerical deltas and whole-plane changes are retained.
- ADC acquisition is conditional on valid VDDA/VREF and stock 216 MHz timing: 480 cycles at 13.5 MHz gives 35.5556 µs versus a 1.88731 µs quarter-LSB settling calculation. This is not total ADC accuracy, a guaranteed effective C31 capacitance floor, or noise qualification. The capacitor branch is 4.283655 mm and its 0.25 mm ground lead is 1.379246 mm.
- Two ADC full-width reference fragments remain outside explicit own-via windows: 4.793389240990453e-5 and 1.2930920115704463e-5 mm², totaling 6.086481252560899e-5 mm². Centerline residuals are empty; the full-width all-inside predicate remains false.
- Source43 numerical power evidence applies only to historical source43/37. **Current48/30 numerical power/VCAP applicability is false.** I2C remains NOT_QUALIFIED; ADC functional, manufacturing and flight qualification remain incomplete.

## What was checked for this package

Portable checks reconstruct the paired sources exactly, verify every selected byte and all sealed dependency digests, independently parse the copper transaction/zone designs/154 unchanged footprints/all poses and 558 pads, bind the stored native prediction's complete footprint semantic hash, check deterministic constructor UUIDs and paths, replay the support adapter, and recompute conditional ADC acquisition arithmetic. Clean delta application and refusal controls run without the historical workspace.

**No native geometry, KiCad pose/placement replay, DRC, actual pad cuts, finite geometry audit, reference classifier, JVM routing, refill, FEM or numerical power solve was rerun while packaging.** The saved 5 finite-entry controls and 7 classifier controls are preserved historical results, separate from newly executed portable refusal controls. Native replay needs the explicit omitted raw inputs and matching runtime.

The historical candidate48 handoff/README says owner adoption was pending; those sealed bytes are intentionally unchanged. The later owner-adoption.json and checkpoint30-review are authoritative for adoption. The historical phrase “Reference copper is exactly identical” only describes critical signal copper; saved plane geometry is demonstrably changed.

See [REPRODUCE.md](REPRODUCE.md), [SOURCE_EVIDENCE.md](SOURCE_EVIDENCE.md), [EXCLUDED_INPUTS.md](EXCLUDED_INPUTS.md) and [EVIDENCE_INDEX.json](EVIDENCE_INDEX.json). V17 top-level documentation is preserved under docs/historical-v17. This source package is a recovery and review deliverable, not a fabrication release.
