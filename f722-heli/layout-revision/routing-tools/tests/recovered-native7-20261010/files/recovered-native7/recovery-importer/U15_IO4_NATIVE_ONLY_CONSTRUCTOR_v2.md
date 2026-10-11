# Native7-only U15 IO4 constructor preparation, v2

This sealed host-verified preparation admits exactly eleven source-native route
records and the exact four-pad IO4 semantic reassignment. It does not inherit the
earlier 68-cut IO4 source plan or the common 90-cut routing proposal. It leaves
those earlier artifacts unchanged.

**No native execution is eligible for this scope.** C's joint first-barrel
capacity check rejected the complete eleven-cut routing attempt: the two RX
branches reach one usable cell, whose 0.195 mm maximum barrel-center separation
is below the 0.577 mm requirement. `NATIVE_EXECUTION_ENABLED = False` rejects the
constructor before importing KiCad, looking at an output path or copying files,
even with an otherwise valid owner lease. A complete additional donor scope
must be reviewed and source-bound in a separately named successor. Changing a
count, role, lease or supplied JSON does not enlarge this source scope.

## Exact inputs and semantic change

The PCB is native7 `published-reference02`, SHA-256
`a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f`.
The native export is
`53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505`.
All 61 paired hardware files are checked against the published checkpoint.

`../recovery-C/native7-IO4-native-only-source-scope-v2.json`, SHA-256
`815df90a2ae84d774acc993b100d110405db7b3d4e9a5f965450943cc4aed487`,
is the explicit allowed-cut manifest. Its eleven full records must match the
source objects, including native contours and numeric codes. A separate exact
UUID allowlist prevents a replacement manifest from silently broadening scope:
four old RX prefixes, two U15 GND tracks plus its old stitch, and four HOLD
transition records. Original C12, R3, IMU, TX and all other copper are retained.

U15.1 becomes `unconnected-(U15-IO1-Pad1)`; U15.10 becomes
`unconnected-(U15-NC10-Pad10)`; U15.5 and U15.6 become `PORT_C_RX_EXT`.
The earlier route model's `unconnected-(U15-NC-Pad10)` placeholder is rejected.
Pad UUIDs, physical numbers, all 558 pad geometries and all 156 poses are fixed.
NC6 remains an upstream PCB land without an assumed internal connection.

The pinned paired-source helper provides only its exact nine schematic/library
operations and pure semantic validators. Its obsolete copper plan is never
loaded as routing input. The native-only source plan derives both 18/22 contract
check arrays from the original source, changing only `published-06.clamp` from
`U15.1` to `U15.5`. All TX checks and all other endpoints/thresholds remain fixed.

## Interfaces and retained evidence

`validate_plan(plan, native, logical, source_plan=None, require_complete=True)`
returns the ordinary importer's `old`, `removed`, `segments` and `vias` fields,
plus `roles`. The exact routing schema is
`f722-native7-U15-IO4-routing-plan/v2`. Top-level fields are:

- `schema`, `source`, `paired_source_plan_sha256`, `cut_scope_sha256`
- `removed_native_records`: eleven `{record, full_record_sha256}` entries
- `added_copper`: complete ordinary track/via recipes
- `recipe_roles`: one `{name, net, logical_net, role}` row for every recipe

Roles are `upstream`, `downstream`, `ground`, and `hold`, with exact physical
nets RX, RX, GND and FLASH_HOLD_N respectively. GND tracks retain the source
0.25 mm minimum. Signal tracks use only F/In2/In3/B; new through-vias are
0.45/0.20 mm and tented on both faces. Schema validity proves complete declared
recipes, not connectivity, clearance, GND return or actual-clamp traversal.
The empty route template is deliberately rejected as an executable plan.

The prepared native path would copy the exact paired hardware, apply only the
two metadata-file recipes, export and independently verify the full fresh XML
netlist, change four pad nets, remove eleven exact objects, add the declared
copper, refill and export with the unchanged official KiCad contour helper.
Only successful structural verification writes construction provenance. This
path is present for review but remains unexecuted and disabled in v2.

Fresh numeric net codes may be renumbered by KiCad. The independent comparator
requires a bijective semantic-name/code map across every object and zone,
normalizes only numeric codes plus the four exact pad net names, then compares
every retained full native record. A second full board S-expression comparison
admits only those four pad net atoms, exact route removals/additions, and zone
fill payloads. Full original geometry is never normalized, repaired or weakened.
Changed zone fills are separately recorded. Fresh semantic parity checks every
assigned physical pin, including all physical pads sharing a pin number.

The proposed receipt retains `recipe_to_native_UUIDs` and
`added_native_records`, binding source/plan/board/native/paired-netlist/source-
plan/role-sidecar hashes. It also records the complete numeric net map. Bound
contracts and roles are candidate outputs; no candidate exists for v2.

## Host checks and limits

Run from the `f722-layout-rebuild` workspace root:

```sh
python recovered-native7/recovery-importer/import_native7_u15_io4_v2.py
python -m unittest discover -s recovered-native7/recovery-importer -p test_import_native7_u15_io4_v2.py -v
```

The controls cover exact source/cut identity; rejection of the obsolete68-cut
scope and unrelated copper; missing restoration roles; foreign TX role; ground
narrowing; plane tracks; off-grid points; arbitrary pose fields; canonical NC10
semantics; unchanged 18/22 contract rows; exact full-board pad syntax; numeric
aliases; native geometry mutations; extra copper; lease scope/expiry; and the
unconditional eleven-cut native-execution block. Host checks import neither
pcbnew nor geometry packages and perform no graph/router/native work.

No PCB or schematic candidate was written. No DRC, ERC, native export, contact,
route-closure or electrical acceptance is claimed. Current power evidence is
still stale. Final route selection, GND/HOLD restoration, fresh native checks,
all22 actual-I/O checks, complete original-group preservation and power
qualification remain separate obligations.
