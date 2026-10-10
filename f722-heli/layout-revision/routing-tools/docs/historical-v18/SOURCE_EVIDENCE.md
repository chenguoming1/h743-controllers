# V18 source and evidence map

All paths below resolve through tests/checkpoint48/raw-evidence.json and its materialize.py. Selected files over 100,000 bytes are losslessly XZ-compressed with both compressed and original hashes. Original sealed receipts are not rewritten.

| Evidence | Primary selected paths | Verified scope |
|---|---|---|
| Exact source transaction | candidate48/construct.used.py, proposal.json, construction-provenance.json, coordinated-change-receipt.json, native-coordinated-integration.json under ordinary-routing | Exact47→48 paired recovery; deterministic12-track/2-via geometry;2 removals; unchanged retained copper/zone designs |
| Source and adopted owner identity | candidate48/route-handoff.json, owner-adoption.json; checkpoint30-review/owner-review-run.json | Original handoff remains pending; later owner receipts establish adopted30/0/0 WIP |
| Finite composite endpoint proof | candidate48/entry-support-audit.json and endpoint-audit.json |24 endpoints,7 direct pad entries,18 full-width joins,6 actual annular entries; retained R43 diagonal direct predicate false, finite composite true |
| Actual support | candidate48/power-audit.json, support-wrapper-compatibility.json; candidate47/power-audit.json | All28 actual pad groups preserved; wrapper schema is legacy/native and typed flag false; separate complete bindings checked |
| Actual clamp protection | candidate48/protection-actual-io.json; checkpoint30-review/actual-io22.json |13/22 cases,11/20 channels; remaining failures retained |
| Two exact pose changes | candidate48/declared-footprint-transforms.json and native-coordinated-integration.json |C31 B(14,24.1,0)→B(15.9,8,180);R43 F(22.5,17.6,0)→F(22.5,17.9,0);154 others exact |
| Native placement recipe | repro-30-placement/*; integrated-routing/reproduce_placement_checkpoint.py | Stored156pose/558 complete native pad reproduction and paired parity, bound to accepted48; no native replay during packaging |
| Placement views | checkpoint30-placement-preview/*; candidate48/placement-detail.png | Native source/pose binding, front/back SVG/PNG, original crop/scope limits |
| Critical reference | checkpoint30-review/comparison-32-to-30.json; reference-region/owner/reference-classification.json | Current source binding; exact critical signal copper; nonzero deltas;2 actual-hole disagreements; whole-plane changes outside critical windows remain real |
| ADC electrical screen | candidate48/adc-electrical-screen.json; electrical_screen.used.py; checkpoint30-review/owner-adc-source-binding.json | Conditional35.56µs acquisition/1.887µs settling; effective-capacitance/noise/rail caveats;2 width-edge fragments retained |
| Primary ADC sources | independent-core-voltage-review/sources/adc_stm32f7xx.c and STM32F722-DS11853-Rev9.txt; pinned firmware startup source; passive BOM/circuit manifest | Primary URLs and exact hashes retained. Original vendor PDF omitted with hash |

Candidate prefixes in this table are ordinary-routing/candidate48 or candidate47. The exact allowlist is raw-evidence.json, not wildcard permission to include experiments. The accepted ADC input and classification chains reference some historical servo/DSM helper sources and receipts; these dependency bytes do not add a new servo transaction. No unrelated unaccepted experiment or private task note is included.

The pad/join/annulus counts are overlapping proof-record totals, including retained dependents; they are not a partition of the 24 new endpoints. The historical total of 12 negative controls comprises 5 finite-entry controls plus 7 reference-classifier binding controls. These saved controls are not rerun by V18. New portable controls reject missing excluded inputs, corrupt bindings, incomplete composite claims, erased raw false predicates, invalid ADC assumptions, malformed recovery operations, unsafe paths, and altered/doubled delta payloads. See checks/v18-incremental-verification.json and the separately generated clean-application result for the exact executed count.

The independently parsed current board's complete footprint semantic hash matches the stored native transform prediction, but this is not native pose-operation replay. Similarly the stored156/558 placement reproduction is hash-bound without rebuilding a placement-only board. Saved native DRC/process/mechanical/parity/firmware/critical checks are source-bound historical receipts, not fresh package-time native runs.

Current numerical power/VCAP is false. Source43 corrected numerical evidence applies only to source43/37; no result is carried forward to48/30. ADC and I2C functional qualification remain absent.
