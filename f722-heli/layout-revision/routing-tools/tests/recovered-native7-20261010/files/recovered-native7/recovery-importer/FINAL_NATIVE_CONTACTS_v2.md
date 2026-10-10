# Separate native7 final contact validator v2

`audit_native7_final_contacts_v2.py` adds a separate contact/topology gate. Frozen v4 sources, the importer, publication-v1, and the historical tangent-sensitive ledger remain unchanged. Twenty-nine small synthetic tests pass. No real-board geometry, native API, router, or full-board integration job has been run for this validator.

## Version 2 correction

V1 remains frozen. Its final-contact enumeration accidentally treated every retained track as moving geometry. That could reject a new .18 mm branch entering the interior of an unchanged .254 mm primary because it demanded the primary's full width inside the narrower branch.

V2 separates `contact_ids` (which contacts to report) from `moving_ids` (new or geometrically affected tracks). Every new/affected track keeps its own full nominal-width witness. A wider retained primary can omit its redundant width-in-branch obligation only when the report proves all of the following:

- The complete native record is identical to its pinned source record; both canonical hashes are reported.
- Its actual conductive geometry on every layer, after all drill subtraction, is identical to the source.
- The branch has a passing full-width witness, and the projection of that witness lies more than half the primary width plus twice the exporter error from either primary endpoint.
- An exact, unbuffered rectangular strip through that interior station is fully covered by the primary's native conductive polygon. Its length is the primary width and its width is the primary width minus the explicit two-boundary exporter tolerance. The strip extends on both sides of the join.

If any proof is absent or fails, the wider retained track's width obligation remains. New/affected wider tracks always retain it. A narrow serial replacement at a wide track endpoint therefore fails. An unchanged primary with a local notch cannot use the exception. The certificate is deliberately local: primary endpoint joins conservatively retain the wider obligation, and this gate does not certify network-wide serial width/current capacity. Source and unchanged inherited rows retain their raw two-sided findings rather than being silently reclassified by the new-branch exception.

Seven added controls reproduce the old false rejection and exercise the corrected branch, a true serial bottleneck, changed primary attribution, missing source evidence, changed conductive geometry, an unchanged local notch, and source/final/inherited separation. The first control includes the raw failing v1-equivalent call and the passing v2 attribution call.

## API and exact bindings

- `load_bound_inputs(request_path)` checks hashes and JSON identities only. No Shapely or native geometry is loaded.
- `audit_final_native_contacts(request_path, lease_path, absolute_new_report_path)` performs the actual audit after a separately bound owner job lease. It returns the report and writes it once to the leased new path.

V2 report schema: `f722-native7-final-native-contact-audit/v2`. Request and lease formats remain compatible with v1; new v2-named templates select the new validator hash. Request schema: `f722-native7-final-contact-request/v1`. Exactly two fields: `schema` and `files`. The latter contains exactly ten entries, each with `path` (absolute) and `sha256`:

1. `source_native`: native7 source export, SHA `53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505`
2. `source_logical_map`: source map, SHA `a1175806ea39f0212f67e13b760782838c858dbaf285f6e4ac8919994e7364c0`
3. `final_native`: exact final native export
4. `candidate_board`: actual PCB bytes bound by that export
5. `plan`: exact serialized incremental plan
6. `provenance`: successful frozen-importer construction receipt, separately hash-pinned
7. `role_sidecar`: root-produced plan-bound protected C roles
8. `historical_ledger`: `native7-shared-restoration-obligations-v1.json`, SHA `f321cb2ea9aff2dc601f7b762ac09c03b6f95d286d634ee2140692726d91b450`
9. `common_packet`: `native7-common-planning-packet-v1.json`, SHA `b161ae1c4df8632c38bea543c4ddb07e5dcb67afd734f86ef4d931cc1584a051`
10. `C_scope`: `native7-C-compact-scope-receipt-v4.json`, SHA `b70b00911dbcade6e97470d6a5cb593a122b20af1dcc4672e00711c107f61534`

The request template supplies these frozen hashes. Missing evidence and mismatched hashes fail closed. The validator reruns the frozen importer's pure plan checks; requires exactly the packet's 90 cuts; verifies every retained native record, footprint, board structure and zone metadata; independently recomputes added UUIDs; and matches all new native records to the pinned construction provenance. No importer/native job is launched.

The sidecar schema is exactly `f722-native7-protected-role-sidecar/v1`, with `schema`, `source` (verbatim plan.source), `plan_sha256`, and `recipes`. Each recipe has exactly `name`, `net`, `logical_net`, `role`. Include all and only new PORT_C_RX_EXT/PORT_C_TX_EXT recipes; role is `upstream` or `downstream`. Missing, duplicate, extra or mismatched rows fail. Final UUIDs come from the independently pinned construction receipt, not the pre-import sidecar.

## Geometry and witnesses

The pinned raw `intersects` ledger remains historical evidence. Independent source/final partitions use positive-area lateral overlap; point/edge tangency is insufficient. Physical drill polygons are subtracted from every affected copper object and net, including fills. Vertical links require declared plated barrel layers and nonzero-length drill-boundary contact. Disconnected islands do not gain implicit vertical links.

Every required physical net and every complete original terminal group is checked. All nine restoration merges are covered: six outside C, two PORT_C_TX_EXT merges, and one VX merge. Original source and final statuses distinguish inherited limitations, regressions and restorations.

For every actual new or geometrically affected contact, contiguous normal-section coverage is measured on native copper at each changed track’s declared width, with the wider-primary continuity rule above. Positive overlap area or the sum of disjoint spans is insufficient. Drill-centered endpoints use actual annular material. A join without a straight-track witness requires complete native annular-land coverage; otherwise it fails as missing evidence. Both exterior ends of each complete new polyline need support outside that recipe. New drill cuts or changed saved fills bring affected retained geometry into the changed-contact scope.

Final C checks remove actual U15.1/U15.2 copper, require upstream/downstream separation, and recheck source-bound role spacing outside those pads. Roles are never inferred.

No contour repair, snapping, simplification or buffering occurs. Only native polygon unions, exact drill/cut subtraction, intersections and native-coordinate section measurements are used. Input geometry is never rewritten.

## Inherited limitations and qualification

`source_native_contact_findings` and `unchanged_inherited_contact_findings` keep source/final width findings separate. Existing U2.9 rounded-end-only or J11 annular-width limitations are labeled inherited when unchanged. They are not erased, silently waived or called new regressions.

`new_or_affected_full_width_contact_gate_passed` covers changed joins, new endpoints and added-object contact inventory. `contact_and_topology_gate_passed` additionally requires all terminal-group restorations, complete required nets and final TVS isolation. Unchanged inherited width limitations remain visible and unresolved outside the changed-contact gate. An inherited positive-area group limitation may still leave a required final restoration unproved; it is labeled accurately. No whole-board contact acceptance is claimed.

The exporter error bound is .00001 mm. Full-width here means native contiguous coverage at least declared width minus the explicitly reported .00002 mm two-boundary tolerance. Each witness reports an error-adjusted width lower bound. This is not an exact analytic-copper/manufacturing-tolerance certificate.

Missing section evidence is not a global routing-impossibility claim. Partial bare pad/via or via/via joins need a track-width or full-annular witness. Entirely drilled-away new segments or unsupported endpoints fail closed. Full-board integration and independent review remain unexecuted and necessary.

Final saved ground fill supplies DC bookkeeping only. Passing establishes no DRC, ERC/parity, plane-neck/reference/return quality, AC/ESD performance, thermal/current capacity, manufacturing acceptance, adoption or overall completion. Reports keep `acceptance_claimed: false`, `adoption_claimed: false`, and `whole_board_contact_acceptance_claimed: false`.

## Owner permission and commands

The separate `f722-native7-contact-audit-owner-lease/v1` lease binds exact request SHA, validator SHA, new absolute report path, owner, unique lease ID, issue/expiry timestamps (at most two hours), and stage `final_native_contact_audit`. The template is inactive and grants no permission. The owner must also grant the serialized geometry lane and an external timeout. All evidence and job bindings are rechecked before report creation.

```sh
python recovered-native7/recovery-importer/audit_native7_final_contacts_v2.py --request ABSOLUTE_REQUEST --check-inputs
timeout OWNER_APPROVED_SECONDS env PYTHONPATH=python-deps python recovered-native7/recovery-importer/audit_native7_final_contacts_v2.py --request ABSOLUTE_REQUEST --lease ABSOLUTE_OWNER_LEASE --out ABSOLUTE_NEW_REPORT
env PYTHONPATH=python-deps python -m unittest discover -s recovered-native7/recovery-importer -p 'test_audit_native7_final_contacts_v2.py' -v
```

The public API and CLI have identical permission checks. Lower-level geometry helpers support synthetic tests only; their availability grants no permission for real-board audits outside the owner-controlled entry point.

The CLI writes failed geometric findings and exits 2 when the contact/topology gate is false. Binding or permission errors exit 1. The callable returns the report; callers must inspect its explicit gate fields.
