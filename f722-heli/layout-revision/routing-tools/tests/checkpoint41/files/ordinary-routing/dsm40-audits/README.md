# Candidate40 DSM entry and return audit

Result: **PASS with one narrowly verified retained-track junction classification.** This is nominal copper/continuity evidence, not board adoption or electrical transient qualification.

Run from the rebuild root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=python-deps python ordinary-routing/dsm40-audits/audit_dsm40_entries_return.py
```

The executable is read-only to both boards and their exports. Its report is `candidate40-entry-return.json`. It imports geometry primitives from the existing SERVO audits, but defines and enforces a separate candidate39→40 source contract. It does not bypass or change the SERVO source validator.

## Source contract

- Source39 board SHA-256: `246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7`
- Candidate40 board SHA-256: `ea6c41fef86c1f66dbf6e2ce24b58858313c5c83f2a518e53385d48aad734ed5`
- Four source copper objects removed; thirteen added; four pads and two footprints translated exactly at native 1 nm coordinate precision.
- All other 1,849 object records remain exact. R38/R70 translations preserve pad geometry, mask geometry, nets, widths, graphics, identity, angle, and side. Outline, stackup, zone definitions, and the original J12 branch are exact.
- The report binds the boards, native exports, construction receipt, proposal, constructor, original support audit, and imported geometry helpers by SHA-256 and rechecks them at completion. Changed records have separate canonical digests, without copying large raw exports.

## Entry results

Seven of eight directly checked new/translated-pad endpoint entries pass the strict predicate: native ERROR_INSIDE pad interior, complete transverse width, a positive transverse interval after a 0.000001 mm inward guard, and an explicit finite full-width rectangle.

The remaining direct result deliberately stays **false**. New SBUS track `c757d812-b2ab-5312-b48b-a9c5f876313e` starts inside R26.2 at `(12.36223,24.3097)`, but its horizontal-track transverse section extends to `y=24.3732`, beyond the pad boundary `y=24.35`. Missing section length is 0.0232 mm; direct finite full-width entry is zero. The removed source39 track has the identical direct failure.

That exact endpoint instead has a narrowly verified retained-track junction classification:

- Retained track `24af4ff1-59b1-43d4-8282-48cf7056a156`, the pad, and their source records remain exact. The retained .127 mm track has 0.237843778 mm of strict finite pad entry.
- A .127 mm-wide, 0.259129433 mm-long rectangle runs from `(12.40223,24.3097)` in the new track to actual pad center `(12.25,24.1)`.
- The rectangle is fully contained in the actual pad plus the new/retained track polygons contracted by the full 0.00001 mm export error. Missing area is zero; minimum boundary reserve is 0.024488237 mm. Its start section is wholly in the new track and its end section wholly in the actual pad.
- No other shared-pad endpoint is exempted. The direct-pad failure remains in a dedicated report field.

All 24 new track endpoints are explicitly classified. Twelve changed ordinary joins retain the required .127/.25 mm native widths and have exact common native endpoints plus positive native copper overlap. Because native straight track primitives are round-ended capsules, these conditions prove a common disk with the full required diameter, rather than accepting a generic center/sliver contact.

Both retained R70 entries pass after the 0.08 mm footprint translation: R70.1 has 0.253416304 mm and R70.2 0.251868059 mm of finite full-width entry.

## D7 return and protection

- The new .25 mm return length is 0.448284271 mm. Its two tracks and via connect directly to D7.2 without other serial copper.
- D7.2's diagonal .25 mm track has 0.028284271 mm of finite full-width pad entry. The vertical track has 0.098615605 mm. The .25 mm pad-height tangency hazard remains an explicit failing negative control; it is not accepted through a zero-length section.
- After contracting the via polygon by export error and removing the ERROR_OUTSIDE drill, the B.Cu entry has an explicit .25 × .01 mm annular strip. Its section has 0.0312475 mm boundary reserve and zero missing area.
- Both saved In1.Cu and In4.Cu GND fills cover the entire conservative annulus. All drill voids are removed from saved copper. Each plane has a .25 × .6 mm corridor into its dominant component after .125 mm erosion, excluding a new sub-.25 mm neck near this return.
- All 28 source support pad groups remain exactly preserved and connected. RPM_LV, SBUS_HV, and DSM_RX_MCU retain their source pad-group topology; DSM_RX_EXT now contains J12.3, D7.1, and R38.1 in one group.
- Removing actual D7.1 pad copper separates J12.3 from R38.1. Their conservative outside-pad minimum gap is 0.148136761 mm, exceeding the .127 mm requirement. No outside-pad bypass survives.

## Controls and limits

All twelve in-memory negative controls reject: D7 tangency, drill-only contact, unlisted retained-track change, translated-pad net change, narrow shared-center join, R70 support disconnection, D7 bypass, .20 mm saved-plane neck, isolated annulus, removed/narrowed required R26 entry, and an internal R26 corridor cut with both terminal sections intact. No source board, export, prior audit, or paired project is modified.

Native DRC/process/reference/parity/mechanical and adoption gates are separately owned. This audit does not claim completed DSM_RX_MCU/SBUS routing, fabrication tolerance, ESD performance, transient current capacity, impedance, inductance, or thermal qualification.
