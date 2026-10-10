# V19 accepted source/evidence map

All paths resolve through tests/checkpoint49/raw-evidence.json and materialize.py. Files larger than 100,000 bytes use lossless XZ with compressed and original hashes. Original worker bytes are preserved.

| Evidence | Paths | Scope |
|---|---|---|
| Exact transaction | ordinary-routing/candidate49/{construct_mcu.used.py,proposal.json,construction-provenance.json,coordinated-change-receipt.json} | Six removals, 19 tracks and 2 vias; only PORT_A_TX_MCU, PORT_A_RX_MCU and ADC_BUS change |
| Worker seal | candidate49/route-handoff.json | 138 source-bound files, including explicitly excluded raw inputs |
| Owner extensions/adoption | candidate49/{f722-heli.import.json,power-revalidation-required.json,owner-receipt-extensions.json,owner-adoption.json}; checkpoint29-review/* | Owner metadata remains separate; later partial-WIP adoption supersedes historical pending wording |
| Finite entries/support | candidate49/{entry-support-audit.json,endpoint-audit.json,power-audit.json,support-wrapper-compatibility.json} | 38 new endpoints ; 5 pad, 29 join, 5 annular proof records ; 28 support groups; legacy typed flag false, separate full binding verified |
| Native unchanged structures | candidate49/native-coordinated-integration.json; checkpoint29-review/owner-coordinated-integration.json | 156 complete footprints, 558 full pads, existing vias and retained unrelated copper unchanged; portable parser replay also passes |
| Actual protection | candidate49/protection-actual-io.json; checkpoint29-review/actual-io22.json | 13/22 cases, 11/20 channels; all_pass=false; external PORT_A incomplete |
| Critical reference | candidate49/reference-comparison48.json; reference-region-review/reference-classification.json; checkpoint29-review/comparison-30-to-29.json | Exact critical signal copper and zero numeric deltas for 48→49; whole-plane changes retained |
| New UART/ADC reference | candidate49/new-route-reference-review.json; reference_routes.used.py | All new/changed centerline and width projections complete outside own-via windows; two old ADC width fragments remain unchanged |
| ADC conditional screen | candidate49/adc-electrical-screen.json; electrical_screen.used.py | Updated branch/path lengths; acquisition arithmetic conditional; effective capacitance/noise/rail limits retained |
| Access screen | candidate49/remaining-access.json; final_access.used.py | 17 originally unresolved MCU pads; no newly sealed unresolved via-access pocket; reserved RPM portal; no route-completion guarantee |
| Frozen construction inputs | ordinary-routing/tests/port-a48/* | Frozen original names reconstructed from sealed .used.py bytes plus final proposal/trunk inputs; peer planning references are not adopted geometry |

Unqualified candidate prefixes above mean ordinary-routing/candidate49. The exact raw-evidence.json allowlist defines inclusion. A small set of historical servo/DSM classifier/audit helpers is included only because the accepted source chain imports or hash-binds it; no new peer experiment is packaged.

Proof counts overlap and are not mutually exclusive endpoint categories. Six saved finite-entry and six saved classifier controls are historical, not reexecuted geometry tests. Newly executed portable controls reject missing excluded raw inputs, corrupt support/reference bindings, erased inherited ADC residuals, unsupported qualification claims, invalid acquisition assumptions, bad recovery deltas and unsafe paths. Delta controls additionally reject altered archives and duplicate members.

The frozen provenance 1981 count is a source inventory count despite its historical field name. The portable parser independently derives 1981 source objects, 1975 retained objects (including 558 pads), 21 additions and 1996 target objects. Historical bytes remain unchanged.

No current numerical power/VCAP result exists in this package. Source43 corrected numerical results are 37-only; source48 mesh-free stage preparation does not qualify 49 numerically. ADC functional and I2C electrical status remain unqualified. No manufacturing or flight acceptance follows from the geometric receipts.
