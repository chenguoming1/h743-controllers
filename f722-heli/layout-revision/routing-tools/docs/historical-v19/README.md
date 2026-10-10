# F722 V19: accepted PORT_A MCU checkpoint, unfinished

V19 is the compact source/evidence delta over immutable V18 for owner-adopted candidate49: **29 opens, 0 native geometric errors, 0 warnings**. PORT_A_TX_MCU is now complete; the coordinated change restores the complete PORT_A_RX_MCU and ADC_BUS trees. PORT_A external protected routes and overall routing remain unfinished.

Accepted49 board SHA256: `15499b28bb63a8c2326c8c7e73dbac4198b8333b05325ab35653825848ae9069`.
Source48 board SHA256: `dcdd0e5655d098ceaffa7f40b6a21f1ca101429ac8eb142c50fa96df86697e68`.

The exact transaction replaces six source tracks with 19 tracks and two ordinary tented vias, changing only PORT_A_TX_MCU, PORT_A_RX_MCU and ADC_BUS. All 156 complete footprint structures, 558 pad structures, poses, existing vias and unrelated retained copper remain exact. TX track length is 8.370079 mm; RX is 10.988722 mm including an 8.872218 mm In2.Cu trunk. There are no footprint transforms in this increment.

The package contains 153 selected source/evidence paths, 11 explicitly excluded raw inputs, 43 frozen helper paths and exact standard-library recovery of the 61-file paired48 and49 projects. The original 138-file worker seal is preserved alongside the separate owner import/pending-power extensions and final owner adoption. No unaccepted PORT_B, TAIL, flash or servo transaction is included. Proposal references to peer reservations remain planning constraints, not adopted peer geometry.

## Results and limits

- All 38 new track endpoints have finite proof. The audit contains 5 strict pad-entry, 29 full-width-join and 5 actual-annulus proof records. These overlap and are not mutually exclusive endpoint counts. All 28 actual support groups and both BARO partitions are preserved.
- The support adapter still reports `typed_audit_binding_checked=false`. V19 separately verifies the full wrapper/audit/source binding rather than interpreting that legacy adapter flag as full validation.
- Actual clamp protection remains **13/22 endpoint cases and 11/20 channels**; its global all-pass predicate remains false. PORT_A external routes remain incomplete.
- The 48→49 critical signal copper and all critical reference numerical deltas are exact. Its source-bound classifier has no changed critical projection regions and zero actual-hole predicate disagreements. This does not erase V18's historical 47→48 limitations. Saved whole-plane geometry changes in the current increment remain real and are not qualified by exact critical projections.
- Every new or changed track has complete saved-plane centerline and finite-width projection outside its explicit own-via windows. The two prior ADC width fragments are unchanged: 4.793389240990453e-5 and 1.2930920115704463e-5 mm², totaling 6.086481252560899e-5 mm². The overall ADC full-width coverage predicate remains false. Own-via windows are not claimed to contain solid reference copper.
- The updated ADC capacitor branch is 4.448361 mm; capacitor-to-MCU path is 6.963362 mm; the ground lead remains 1.379246 mm. Acquisition remains conditional on valid VDDA/VREF and stock 216 MHz timing: 35.5556 µs sample time versus 1.88731 µs quarter-LSB settling calculation. No effective-capacitance floor, total accuracy, AC return or noise qualification is established.
- The stored remaining-access screen covers 17 originally unresolved MCU pads and reports no newly sealed unresolved pad via access; it preserves the RPM portal at (15.1,9.59). Legal via access is a necessary geometric condition, not proof of a complete route.
- **Current49/29 numerical power/VCAP applicability remains false.** Corrected source43 results remain historical source43/37 only. Source48 mesh-free preparation is historical preparation, not numerical qualification. I2C remains NOT_QUALIFIED; ADC functional, manufacturing and flight qualification remain incomplete.

## Package verification scope

Portable checks reconstruct paired sources exactly; verify selected bytes, all sealed dependency hashes and the separate owner extensions; compare all unchanged footprint/pad/copper structures and zone designs; reproduce deterministic constructor UUID/path geometry; execute the original owner's pure-parser coordinated integration and support adapter; and recompute conditional ADC acquisition arithmetic. Clean delta application runs without the historical workspace.

No native geometry, KiCad pose/placement operations, DRC, actual pad cuts, finite geometric audit, reference classifier, access screen, JVM routing, refill, FEM or numerical power solve is rerun for this package. Six finite-entry and six classifier controls are saved historical receipts, distinct from newly executed portable refusal controls. Native replay needs the documented omitted inputs and matching runtime.

The worker handoff/README still says adoption was pending; those original bytes are unchanged. The later owner-adoption.json and checkpoint29-review establish owner adoption as partial geometric WIP. Also, construction-provenance.json's `all_other_source_native_objects_exact_except_net_code=1981` is the original source object count. After six removals, 1975 source objects are retained; 21 additions give 1996 total native objects. V19 derives these counts separately and does not relabel the sealed historical field.

See [REPRODUCE.md](REPRODUCE.md), [SOURCE_EVIDENCE.md](SOURCE_EVIDENCE.md), [EXCLUDED_INPUTS.md](EXCLUDED_INPUTS.md) and [EVIDENCE_INDEX.json](EVIDENCE_INDEX.json). V18 documentation is preserved under docs/historical-v18. This is a recovery/review package, not a fabrication release.
