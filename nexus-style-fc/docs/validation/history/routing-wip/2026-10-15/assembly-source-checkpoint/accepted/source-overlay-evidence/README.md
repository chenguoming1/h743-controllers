# Nexus main-only source-consistent annotation variants

Status: prepared source remedy for the sole native lane. No native loading, DRC,
ERC, Gerber plotting, assembly-placement export or production signoff was performed
in this source lane. Stage09 remains a conditional trial until the successor passes.

## Authoritative handoff

Use `source-candidate-final/source-variant-transaction.json`:
`109a1aeb7c6161543404f984fa99586dade230cd1c30ae8c4c3e93974c5bb365`.
The earlier `source-candidate` is superseded only because its mechanical checker
still binds the old schematic SHA. Variant artwork, selector and schematic match
those in the final candidate.

Input stage08 PCB:
`ccd8865f6785fd1cdec0214a08fe409faed4d47bb01e8474f09264ee36acab99`.
Approved stage09 artwork PCB:
`282e48d05d5adb1a6933b5f29ea851c7452183f508bc3fae8264982b5e1121aa`.
The source candidate's routed PCB is still byte-exact stage08. **Do not adopt it as
an artwork or routed-board successor.** The sole native owner owns the PCB edits.

There are eleven source overlay files:
- Five new NexusFC local footprint variants, one each for J4/J6/D1/D2/D3.
- Three existing libraries corrected only from `through_hole` to `smd`: U3/L2/U14.
- `tools/design.py`, selecting only the five variant FPIDs inside `get_main_parts()`.
- Regenerated `hardware/nexus-style-fc.kicad_sch`.
- One exact schematic-SHA rebind in `tools/check_header_interface_static.py`.

The transaction contains every source input hash, every overlay before/after hash,
all five FPID and target-footprint guards, and exact changed library nodes. The
review-only unified patch contains these source changes and no PCB patch.

## Source and library consistency

Variant names are the corresponding generic footprint name plus
`__NexusMain_J4`, `__NexusMain_J6`, `__NexusMain_D1`, `__NexusMain_D2`, or
`__NexusMain_D3`. The source selector guards each original FPID and exact LCSC
before substituting the variant. `PARTS` remains byte-for-byte identical as Python
data; sibling projects that import it retain their generic footprints. J3 and J5
retain the shared generic connector library.

Each new variant is a narrowly cloned generic library: the one approved graphic
node is replaced (split into two lines for J4/J6), the name is changed, and the
outer file header is `footprint` rather than legacy `module`. That project-owned
header makes the existing `fix_courtyards.py` skip it; no generic courtyard
regeneration is permitted to redraw this bounded artwork. All remaining library
source nodes and all raw pad nodes are exact copies. The five generic artwork
libraries remain byte-identical. No custom DRC waiver, warning suppression,
filter relaxation, shared symbol edit or shared generic artwork change is used.

All five selected symbols have no `ki_fp_filters` restriction. Their shared symbol
library Footprint defaults stay generic; only the main schematic's instance
Footprint properties select the variants. `build_floorplan.py`, `gen_schematic.py`
and `export_fab.py` already use `get_main_parts()` only for the main project.
`pcbutil.py` stays exact stage08 and loads the chosen local library without a
runtime artwork mutation. `assembly_annotations.py` must not enter this successor.

U3/L2/U14 are physically all-SMD libraries. Their intrinsic assembly-type fixes
are the previously approved attribute-only corrections, not graphic changes.
J1 remains the manual child-board slot/fillet joint. J6 retains its 16 SMT contacts,
4 plated shell lugs and 2 NPTH locators; the mixed assembly process is not normalized.

## Exact preservation evidence

- 89 main parts and all 349 pin assignments, including 26 no-connects, are exact.
- Every main part field is exact except five explicitly mapped FPID names.
- The original schematic regenerates byte-exact from stage08 source.
- The new regenerated schematic differs only in the five instance Footprint
  properties; its UUID set and all other source nodes are exact.
- Schematic SHA: `7bfd6617e7d0285c738615fd2b6d7b6d6958675c095e50de87a8ed44111b972b`.
- The mechanical checker changes only its exact expected schematic digest from
  `7a133c241ba24a688d2d2490ae423ff74d26f57cf6578f871cc757093584de42`
  to the new digest. All geometry/specification/check logic stays exact. This
  rebind is recorded separately under `guard_rebinding` in the transaction.
- Stage08 and stage09 were read-only. No PCB was edited in this lane.
- Fifteen pure-source tests cover full replay, selector isolation, exact overlay
  installation, and fail-closed wrong board/source/duplicate/helper cases.

The artwork retains the corrected 0.250 mm connector-outline stroke and the
conservative 0.150 mm text gaps. The approved LED circles are the same stage09
0.150 mm stroke filled markers with conservative 0.300 mm outer ink diameter.
Primary selected-part polarity drawings and source mask/silk screens remain in
the parent annotation package; actual plotted/assembly checks remain separate.

## Sole-lane adoption

Start with a new isolated copy of stage08's hardware/tools. The installer guards
all stage08 source-file hashes except the routed PCB, whose exact current SHA the
owner supplies. It rejects an obsolete runtime annotation helper and never
writes the PCB. It will reject stage09 tools intentionally.

```sh
python3 -B install_source_overlay.py \
  --candidate /absolute/path/to/new-isolated-stage \
  --expected-pcb-sha256 EXACT_CURRENT_PCB_SHA \
  --expected-transaction-sha256 109a1aeb7c6161543404f984fa99586dade230cd1c30ae8c4c3e93974c5bb365
```

The native owner applies the already-approved eight artwork/attribute edits to
that candidate PCB and changes only the five footprint root FPIDs to the mapped
variant names. Alternatively the owner's verified stage09 PCB can seed the
isolated candidate, with its protected-board equivalence independently checked.
Preserve all existing component UUIDs, properties, pads, pin nets, placements,
copper, zone fills and meaningful board text. `fpid-mapping.json` includes exact
stage08 and stage09 footprint canonical hashes for this guarded operation.

First load the five new library files using real native KiCad. Then validate
library/instance geometry parity and the complete successor: DRC with schematic
parity, ERC, mechanical static checker, source preservation, actual CAM/visual
checks, and assembly exports. Do not reuse stage08/stage09 receipts as successor
results. The new libraries must eliminate the five real `lib_footprint_mismatch`
warnings without reintroducing the three assembly-type or five silk warnings.

`native_verify_variant_assembly.py` is provided for the sole native lane only. It
uses the unchanged reviewed exporter and requires exact source/candidate PCB
hashes. The actual CPL must be byte-identical. Actual BOM content must be exact
per designator after normalizing **only** the five authorized Footprint-name
changes; values, LCSC codes and selected counts are unchanged. J1 must remain
absent and J6 present, with 83 machine placements. The exporter does not establish
reel zero-angle convention, shell solder process or physical-fit qualification.
