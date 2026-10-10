# Candidate41 complete coordinated DSM entry/support audit

Result: **PASS within the nominal geometry scope**, with two explicitly proved
full-width junction corridors. Both underlying direct-pad predicate failures
remain false in the report. This is not whole-board completion or loaded-power
qualification.

Reproduce from the rebuild root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=python-deps python ordinary-routing/dsm41-audits/audit_dsm41_entries_return.py
```

The script writes only this audit directory. It imports the sealed DSM40
geometry predicates without changing their criteria, source contract, inputs,
or prior output. Controls modify in-memory copies only.

## Deliverables and binding

- `candidate41-entry-return.json`: schema `f722-dsm41-entry-return-audit/v1`;
  complete finite-entry, track-junction, annular-entry, saved-plane, support and
  actual-D7-cut witnesses plus mutation controls.
- `coordinated-change-receipt.json`: schema
  `f722-explicit-coordinated-native-transaction/v1`; full eight removed records,
  21 added records, six before/after pad records, three before/after footprint
  records, logical owners and exact composed provenance.
- `input-hashes.json`: bound boards, exports, route maps, proposals, constructors,
  prior geometry implementation, source support receipt, isolated40 DRC and
  complete candidate41 actual-I/O report. All are checked before and after.
- `check.log`: final executable outcome. The report binds the executable and
  input manifest separately by SHA-256.

Accepted origin39 board:
`246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7`.

Isolated stage40 board:
`ea6c41fef86c1f66dbf6e2ce24b58858313c5c83f2a518e53385d48aad734ed5`.

Final candidate41 board:
`539d9547eb8c4d5984481293ae10cee34355ee838dff11ab43b00cca270ceae2`.

The first construction stage has four removals, 13 additions, four translated
pads and two footprints. The second has five removals, nine additions, six
translated pads and three footprints. One DSM tail was added in40 and removed
in41; this yields the direct39→41 inventory of eight removals, 21 additions
(20 tracks and the D7 GND via), six pad translations and three footprints.
All other 1,843 origin39 native object records are exact. All undeclared poses,
pad geometry, masks, nets, graphics, copper widths, outlines, zone definitions
and stackup are exact; the retained logical owners and original J12 branch
are exact. Filled polygons are re-evaluated from the saved candidate41 export.

Stage40 remains rejected for its three courtyard errors. The report preserves
all three violations and their source-bound DRC evidence; validating the
two-stage construction does not accept stage40.

## Endpoint and junction evidence

The complete scan checks all 40 new-track endpoints, 13 direct-pad predicates,
20 exact full-width track junctions and two finite actual-annular entries. It
also enumerates every endpoint inside a translated pad, including the whole
short horizontal segment inside R38.1. R38.2 has no track entry and retains its
open MCU continuation.

Eleven of 13 direct-pad predicates pass: native ERROR_INSIDE copper, endpoint
interior, full transverse width, positive guarded transverse interval, and an
explicit finite full-width rectangle. The two failures are junction vertices,
not unproved terminal entries:

- **R26.2 retained junction:** the original sealed source39-bound classification
  remains unchanged. The incoming .127 mm track's section misses the pad by
  0.0232 mm. Its retained source track and pad are exact. The explicit .127 mm
  corridor reaches the actual pad through conservative incoming/retained
  copper, with 0.024488237 mm boundary reserve. The retained track separately
  satisfies strict pad entry. No other endpoint uses this R26 declaration.
- **R38.1 new intermediate bend:** diagonal
  `eab3f753-c84f-52be-b8d6-98fc84242d63` ends at `(16.83,23.46)`, coincident with
  horizontal `ace32a9d-722d-57a5-9890-0e87e2a8f1a5`. Its diagonal transverse
  section misses the pad by 0.049357864 mm, so its direct predicate stays false.
  The horizontal track's two strict entries pass. A separate .127 mm-wide,
  0.280713377 mm-long rectangle runs from `(16.81,23.48)` in the diagonal to
  actual pad center `(17.09,23.46)`. Missing area is zero and boundary reserve
  is 0.013693913 mm. Both track polygons are contracted by the full .00001 mm
  export error, and terminal sections fit the named incoming track and actual
  pad. This is independently identified new-track junction evidence.

All 20 junctions have exact coincident native endpoints, required native widths
and positive native polygon overlap. Native straight round-ended capsules
therefore share an analytic full-width disk. Requirements are .127 mm for
ordinary DSM/SBUS/RPM, .25 mm for the D7 return and CORE feed, and .20 mm for
R70. No generic center/sliver-contact acceptance is used.

## CORE, C70 and R70

The four new CORE segments are .25 mm wide and total 2.466979964 mm. At each
retained .30 mm feed endpoint, the entire analytic .25 mm disk fits inside the
conservative retained copper, after its export-error contraction. This is
stronger than accepting a small positive contact. All other CORE objects are
exact origin39 records.

Removing either the old two-segment bridge or the new four-segment bridge
produces the same two physical pad partitions. The isolated side is exactly
`C4.1, C6.1, U1.1, U1.64, U13.5`. U11.4 and the DSM supply stay on the source
side. Reconstructed CORE has one component with 47 native pad objects and 46
distinct pad keys; SW1.1 has two native pad objects. No chip-internal path is
assumed.

C70's source39 .30 mm supply track and .40 mm ground track are retained exactly.
Both translated-pad strict entries pass, and each entire endpoint disk is
inside the actual pad. C70 moves only 0.06 mm; C4 pad and footprint records are
exact. This checks local copper and support, not decoupling transients.

The new .20 mm R70 ILIM and GND tracks have full finite pad entries. The GND
track reaches its retained plated via with a finite .20 mm annular strip,
after contracting outward copper and subtracting the outward drill void.
Its pad/track/via graph is direct. Both saved In1.Cu and In4.Cu planes cover the
conservative annulus and provide an explicit .25 mm corridor into the dominant
eroded plane component; every native drill is subtracted.

All 28 source support pad groups are exactly preserved and remain connected.
RPM_LV, SBUS_HV, DSM_RX_MCU and GND preserve their complete source pad partitions.

## D7 protection and return

The dedicated .25 mm D7 return pair and .45/.20 mm tented via from40 remain exact.
The direct return is 0.448284271 mm long, with strict finite D7.2 entries and a
.25 mm actual-annular strip. Saved In1.Cu and In4.Cu copper cover the conservative
annulus and each provide a finite .25 mm-wide corridor into their dominant
component. No narrow local plane neck is substituted.

After removing only actual native D7.1 pad copper from every relevant object,
J12.3 and R38.1 disconnect. The conservative outside-pad gap is 0.148136761 mm,
above the .127 mm requirement. There is no enlarged pad cut, chip-internal
conduction or geometry snapping.

The standard `actual_io_receipt_sha256` separately binds
`candidate41/protection-actual-io.json`, the complete fresh 22-case report.
Its status remains **11/22, all_pass=false**. The internal D7-only cut is labeled
separately and cannot substitute for complete actual-I/O evidence.

## Mutation controls and limits

All 28 controls reject. They cover retained source changes, new CORE width/layer
and missing/unlisted/restored objects, moved pad net/pose and footprint pose,
C70 retained width/lost entry, R70 support disconnection and drill-only entry,
D7 tangency/bypass/drill-only entry, narrowed or sliver track junctions,
isolated/necked saved copper, and removed/narrowed/interior-cut R26/R38 paths.
Interior-cut controls preserve both terminal sections while destroying the
finite corridor, so terminal contact alone cannot pass.

Numerical power and VCAP validation are explicitly stale/pending and separately
owned. Narrowing .30 mm to .25 mm is recorded honestly. This audit does not
apply the classic DSM floor to CORE sinks or invent a CORE voltage budget.
The bound proposal's rectangular-strip estimate is not a fresh numerical solve.
No FEM/JVM or other power solver runs here. Native DRC, mechanical, parity,
firmware, reference and adoption decisions remain with their owners. No sealed
source39/source40 evidence, project, board, canonical file, Git state or public
artifact is changed by this audit.
