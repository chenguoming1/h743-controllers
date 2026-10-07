# Fabrication/CAM notes

**VERIFIED PROTOTYPE FILES / FACTORY CAM AND ASSEMBLY ACCEPTANCE REQUIRED. Prototype files; no production or flight qualification. Factory acceptance and explicit purchase authorization remain required.**

Source PCB SHA-256: `4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f`. Native KiCad 10.0.6 export, 2026-10-07 UTC. All layer/drill outputs use the saved (0,0) origin, metric coordinates; output Y is negative native PCB Y. No zone refill or source modification was performed during export.

## Board and layers

- Single board, rectangular Edge.Cuts centerline **41.66 × 25.40 mm**. The overall assembly target is nominal **47.5 × 25.4 mm**; that is not the PCB route dimension or a qualified maximum component envelope
- Native Gerber job GeneralSpecs.Size is **41.71 × 25.45 mm** because its bounding box includes the 0.05 mm outline stroke. Route to the **Edge.Cuts centerline**, not the stroke's outside edges. The native job was preserved exactly, not edited to conceal this distinction
- Six copper layers in order: F.Cu/L1, In1.Cu/L2, In2.Cu/L3, In3.Cu/L4, In4.Cu/L5, B.Cu/L6. L2/L5 are GND-reference layers; the manufacturer's CAM must preserve the supplied copper and stackup intent
- Native CAD thickness **1.0324 mm**. Existing selected factory candidate: **JLC06101H-3313**, nominal finished **1.03 mm ±10%**, 1 oz outer/0.5 oz inner copper, Nan Ya NP-155F, ENIG, green soldermask. Retained evidence was checked 2026-10-04, not reconfirmed by this export task
- Production confirmation is mandatory: retained calculator central 7628 prepreg is **0.2028 mm**, while the order drawing shows **0.21040 mm**. Do not guess, average, scale or silently combine stackups. CAD/job preserve the existing 0.2028 mm value. Obtain the selected factory's final production stackup and confirm impedance/mechanical implications before release
- Native job design-rule fields and its generic revision label `rev?` are untouched generated metadata, not independent fabrication acceptance or this package's release identifier. The exact PCB hash identifies the revision
- All 13 Gerbers are separate layers; profile is not duplicated on copper. X2 attributes and aperture macros are retained. Gerber precision is 4.6 mm; mask polarity metadata is native. No mirrored fabrication layers or extra soldermask/paste modifications were introduced

## Drills and slots

Separate PTH and NPTH Excellon files are mandatory; do not merge away plating distinctions. Decimal metric format uses 0.001 mm coordinate precision. Slot routing uses G00/M15/G01/M16 commands; CAM must interpret these as slots, not endpoint drill hits. SVG maps/report are references and are not fabrication geometry.

| Features | Count | Finished nominal geometry |
|---|---:|---|
| PTH vias | 246 | 0.200 mm drill |
| PTH vias | 77 | 0.300 mm drill |
| J2–J8 PTH header holes | 21 | 1.100 mm round |
| J1 plated shell slots | 4 | 1.100 × 0.600 mm; 0.600 mm tool, 0.500 mm center travel |
| J1 NPTH locator | 1 | 0.710 mm round |
| J1 NPTH locator slot | 1 | 1.010 × 0.710 mm; 0.710 mm tool, 0.300 mm center travel |

There are **348 PTH features and 2 NPTH features**. The USB shell slots lie at exported centers (37.570,−9.000), (37.570,−17.000), (40.430,−9.000), (40.430,−17.000) mm; slots run in output Y. Locator centers are (39.000,−17.000) round and (39.000,−9.000) slotted. Obtain factory agreement for finished slot dimensions, plating compensation, NPTH slot capability and tolerances. No holes were enlarged or changed to suit a factory limit.

## Process acceptance still required

The copper, mask, paste and holes are exported exactly from the verified prototype candidate. All 323 vias passed the owner's mask audit; do not introduce unintended via-mask openings. Paste layers contain the existing aperture geometry; stencil thickness, process window, fine-pitch/0201 printing, split thermal apertures and bottom-side reflow have not been factory qualified.

This is a single-board output without newly designed panelization, tooling rails or panel fiducials. R31's retained supplier evidence marks the 0201 selection as Standard Only. Confirm current service eligibility, double-sided process, factory minimum panel/handling envelope, rails/fiducials, depanelization and fixture clearance. Any panel geometry is a separate reviewed deliverable; do not scale the board or silently add features to these files.

The final exact-board electrical/power review is complete and found no additional copper defect. Its operating limits remain in force. Nine retained reviewed DRC warnings, full connector maximum-body/access/underside-envelope review, supplier/factory acceptance and first-article testing remain gates. No production or flight suitability is established by these exports.
