# C12-only translation importer successor

`import_native7_c12_translation_v1.py` prepares one narrowly declared edit of checked native7: C12 moves from F(26.0625,12.0), -90° to F(26.3125,12.0), -90°. Its footprint UUID, value, library ID, pad UUIDs/numbers/nets, and all local land definitions remain fixed. Native pad angles remain 270°. Frozen ordinary importer v1 and final-contact validator v2 are unchanged.

Status: pure-plan and synthetic implementation only. Twenty-one host identity/synthetic tests pass. No real native prediction, PCB save, refill, export, native geometry audit or router was run for this successor. The included tests' straight recipe declarations are synthetic host examples, not routed candidates. No completed C12 routing plan or accepted candidate is supplied.

## Current applicability and resolved static findings

This frozen source version is **not eligible for a current routed native import**. The later saved-domain control found the .20 mm C11→C12 path unreachable after RX; its .18 mm alternative is outside this exact scope. R3 still needs relocation/closure, also outside the C12-only transform. Keep these 94-cut/.20 sources as a bounded implementation checkpoint; do not change its constants to accept evolving geometry. Any native smoke still needs a fresh owner lease and serialized lane.

Independent static review found two generic defects in the initial sixteen-test draft, both corrected before sealing without widening the C12 pose or feed minima:

1. The original catch-all GND assignment rejected separate common `recovered-U2-9-ground-0/1` .18 mm restoration. The scope now binds both exact existing proposal recipes independently. They must be present unchanged and cannot be reassigned to the C12 .20 return. The regression preserves the original false-rejection predicate and verifies mixed common/C12 recipes pass.
2. The original pose prediction checked original routes and UUIDs, and final non-route syntax against prediction, allowing an identical native save-time board-setting change to escape. Prediction now directly matches original non-route structures excluding only the complete C12 footprint and the existing zone-fill exclusions. A synthetic changed-setting example demonstrates that both old predicates pass while the new check rejects it; unrelated footprint changes also fail.

The original review findings remain recorded in the static-review artifact, with resolution/test evidence. Twenty-one passing tests cover host identities, these regressions and fabricated translation behavior. They do not establish native API compatibility, complete routed connectivity or clearance. Native integration remains unexecuted; no owner lease has been issued for this version.

## Frozen source and scope

The successor imports the unchanged v1 helpers (SHA `cf783fd61fd229927f89aa2741d88500d598a445f306ab1031fca9ef49232653`) and requires the original native7 source board/native/project/logical-map hashes. It copies only the exact 61 paired hardware files during a later authorized native run.

`native7-c12-translation-import-scope-v1.json` pins C's `native7-C12-east-source-MISO_retained-v1.json` SHA `57041cb919967ac1f7a3e12be3f5079a8009f52f26c6343ce0f7e0dfc8bd8207`, including its prerequisite hashes. This first importer version does not authorize the alternative MISO-source-released proposal.

The cut set is derived independently: the original common packet's 90 IDs, minus restored original IMU_CS tracks `296bfec5-72b7-4194-9568-a88d79de25ed` and `8a55abc3-716e-448f-887e-c4ef9f2907bd`, plus exactly six C12 tracks. All 94 expected UUID/full-record hashes are in the scope; the actual plan must contain every complete source record and matching hash. Same-count substitutions, missing cuts, pads in route removals, altered records and additional cuts fail. The count alone grants no permission. The retained `.20` supply track `d9731330-cda6-44f0-811a-9cdea7ea0676`, ground barrel `3a66a0d8-a4b0-4282-9936-fdae79b412fc`, restored IMU_CS tracks and every undeclared record remain exact.

Four named restoration obligations bind full recipe lists and source-hashed actual terminals: U2 supply boundary→new C12.1 (.20 minimum), C11.1→new C12.1 (.20), new C12.2→held ground barrel (.20), and new C12.1→R3.1 exclusive pull-up leaf (.127). Host validation checks the declared recipe endpoint/layer graph, exact terminal coordinates, physical/logical net identities and minimum widths. Every new +3V3_IMU/GND recipe must belong to a C12 obligation or match one of the two separately pinned common U2.9 ground recipes exactly. This is declared centerline completeness, not native full-width contact or connectivity proof. Final native gates must examine annuli, copper coverage and all terminal groups.

The scope retains the complete historical source terminal ledger and adds all seven original +3V3_IMU pad UUIDs, bound to the checked source-group/electrical evidence. Existing source limitations remain visible. Final gates must partition the revised cut set independently; the old nine-merge count does not describe this successor automatically.

Any further native cut, restored common track, pose, minimum-width or terminal-group change requires a new frozen scope and importer version. Do not edit a published scope hash in place.

## Plan and API

Plan schema: `f722-native7-c12-translation-routing-plan/v1`. Exact fields:

- `schema`, original `source`, `scope_contract_sha256`
- `declared_footprint_transforms`: exactly the scope's one full C12 declaration
- `removed_native_records`: full records with canonical SHA256, exactly the derived source set
- `added_copper`: ordinary v1 complete polyline / .45/.20 tented through-via recipes
- `obligation_recipe_bindings`: one `{name, recipe_names}` entry per four scope obligations

The JSON schema is a format aid. `validate_plan(plan, native, logical)` additionally enforces exact identities, source contract, record set, all terminal declarations and recipe graph completeness. Plan-file hashing continues to seed deterministic UUIDs for every new track segment/via; C12's existing IDs survive. Caller plans must retain current role metadata in a separately plan-hash-bound protected-role sidecar.

`--check-inputs` never imports pcbnew or Shapely, creates a candidate, or transforms real polygons:

```sh
python recovered-native7/recovery-importer/import_native7_c12_translation_v1.py --plan ABSOLUTE_COMPLETE_PLAN --check-inputs
python -m unittest discover -s recovered-native7/recovery-importer -p 'test_import_native7_c12_translation_v1.py' -v
```

A future native run requires the official pinned runtime, new absolute candidate directory, external owner-approved timeout and a fresh `f722-native7-c12-translation-owner-lease/v1` binding this successor's exact SHA, scope SHA, plan bytes, original source, output and single stage `c12_translate_construct_refill_export`. The included template is inactive. Old importer/smoke/contact leases fail.

## Three independent pose checks in the authored native path

1. Load the untouched original PCB independently; apply only the fixed C12 native position operation; save/reload/export a disposable pose-only prediction. No routes are changed by this prediction. Its route syntax and all UUIDs must remain identical.
2. Require every predicted native field to equal an exact integer +250000 nm translation of the two source pad contours and C12 graphic coordinates. Preserve inside/outside polygons, holes, mask expansion, dimensions, orientation, IDs and metadata without approximation, snapping or contour repair. All other records remain source-identical. The actual routed/refilled/reloaded export must match the same expected records; all route additions keep v1's full native recipe checks.
3. Invoke the pinned recovered `verify_footprint_transforms.py` and exact original parser only inside the leased stage. It independently predicts the native pose again from the original PCB and compares complete footprint S-expression structures, including paste and properties not fully represented in the native copper export. Require 155 unchanged footprints and exactly one predicted transform. First compare all original/prediction non-route structures excluding only the exact complete C12 footprint and existing fill payloads; then compare all final non-route board/zone-metadata structures to the independent prediction, excluding only the original allowed fill payloads.

The receipt reports `155 unchanged + 1 predicted footprint` and `556 unchanged + 2 predicted pads`. It binds original/final/prediction PCB and native exports, declaration, independent footprint proof, plan, scope, helper hashes and owner lease. Source/project inputs are rechecked; all non-board hardware remains byte-identical. Zone outlines/settings remain exact and fill changes are reported. A mismatch fails without altering the source; disposable failed outputs are unaccepted evidence.

The native path has not been exercised. Independent code review and an owner-leased disposable transform smoke are still required before relying on it for a real candidate. A passing construction receipt does not prove DRC, electrical, contact, routing or placement acceptance.

## Necessary contact-validator successor

Final-contact v2 intentionally rejects this new receipt, moved pad/footprint records and revised cuts. Keep it frozen. A separately versioned validator must bind this new importer/scope/declaration/prediction/proof receipt and exact recipe UUID map; independently verify all 94 source cuts and 155/556 unchanged objects; and compare the two moved pads only against the verified exact prediction.

It must carry every original complete terminal group, add the full seven-pad +3V3_IMU group, retain C12.2's complete GND obligations, and prove all four declared replacement branches at their minimum widths on actual final copper. Treat both C12 pads and every affected/new join as changed geometry; preserve inherited findings separately. Continue protected C role/TVS isolation, endpoint/annular/full-width checks, positive-area and declared-barrel connectivity, exact fill reporting and actual retained-donor continuity. Sidecar identity may retain its v1 format but must bind the extended serialized plan; the consumer must recognize this new construction schema deliberately.

No new contact-validator implementation or waiver is included here. Complete C12 routing, final physical/reference/electrical checks and current power/VCAP assessment remain pending.

A future justified .18 mm feed meeting an unchanged .20 mm endpoint is an intentional width transition when the source-bound approved electrical/branch minimum permits it. The generic contact-v2 wider-primary endpoint rule would reject that transition. A successor must preserve that raw finding, bind the approved branch/current role and minimum width, require a full contiguous .18 mm witness with no unintended thinner neck, and retain any real electrical minimum. Do not introduce that exception until the complete width/pose plan and native geometry exist.
