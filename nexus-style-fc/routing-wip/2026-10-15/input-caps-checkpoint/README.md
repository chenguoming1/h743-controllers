# Approved input-capacitor update: zero native errors, qualification open

Open the [stable current project](../../current/hardware/nexus-style-fc.kicad_pro), [PCB](../../current/hardware/nexus-style-fc.kicad_pcb), [matching schematic](../../current/hardware/nexus-style-fc.kicad_sch), or [short guide](../../current/README.md). Canonical root hardware and unrelated projects are unchanged.

## Exact accepted experimental result

PCB SHA256 `ee1b9b1c814998b957b03777644b531f78b5301856c2a5eb823a6ef07c99059c`; schematic SHA256 `7a133c241ba24a688d2d2490ae423ff74d26f57cf6578f871cc757093584de42`. Native KiCad 10.0.7 refill/save reports **zero errors, zero opens and zero schematic parity findings**. All-visible PCB diagnostics also have zero errors and zero footprint-filter findings, while retaining 11 centering, five footprint-type and 54 silk warnings. Enabled ERC reports zero findings; a separate all-visible ERC diagnostic exposes 13 single-global-label warnings and no errors. All inherited severity settings are disclosed; no new waiver is used.

[Full accepted verification](r62-input-cap-star/verification.json), [native DRC](r62-input-cap-star/native-drc.json), [source and export equality](r62-input-cap-star/source-export-verification.json), [actual cap return paths](r62-input-cap-star/cap-input-actual-return-verification.json), [VIN transition detail](r62-input-cap-star/vin-transition-reference-detail.json), [geometry](r62-input-cap-star/geometry-verification.json) and all-visible diagnostics are retained in the sealed r62 directory.

## Approved source and copper scope

- C27 is replaced and C31 added: Samsung CL21A226MAYNNNE / JLC C602037, 22 uF, 25 V, X5R, ±20%, 0805. The exact manufacturer minimum land pattern uses 0.910 × 1.350 mm rectangles with 0.830 mm gap. Maximum capacitor body height is 1.450 mm.
- D5 moves exactly 0.400 mm south; its selected part and electrical connections remain unchanged.
- The two J4 clearance errors are removed by the complete source-bound cap-star/VIN/EN and coordinated donor transaction. All original 347 physical pin connections remain exact; C31 adds only VSYS and GND, producing 349 pairs. Retained source-net identities and all complete ports pass.
- The readable schematic, explicit main-only part selector, generator, custom footprint and actual WIP BOM/CPL are synchronized. Legacy selections used by the separate power-module project remain unchanged; it does not inherit this capacitor remedy. No standalone project file changes.

The C27-to-VIN path improves from 12.271 to 9.401 mm, with nominal 20 C trace resistance 38.04 to 18.52 mOhm, excluding barrels and spreading. EN is a separate capacitor-star leaf; physical cuts prove it cannot serve as an alternate VIN load feed. A 3.471 mm direct C27 ground witness is retained; C31's farther branch and actual finite ground connections are documented. In1/In4 remain connected main-ground components, and all measured VIN projection gaps lie within the explicitly bounded transition openings. This is measurable geometry, not a demonstrated low-inductance or frequency-domain result.

All 96 USB shield regions and existing protection/LDO paths survive. One LDO witness-list change is an additional C18 ground-via witness; all original paths and weights remain. Actual exported mask/paste changes are restricted to C27/C31/D5, and the 11 new/moved holes remain outside every aperture with a conservative minimum edge gap of 0.130 mm. The original USB taper Gerber geometry is unchanged. These CAM exports are diagnostics, not release manufacturing data.

## Electrical and physical qualifications still open

[Capacitor selection review](C27-selection-review.txt), [screens](qualification-screens.json), [aging scenario](aging-guidance-scenario.json) distinguish typical curves from guaranteed combined corners and include the primary-source links. The ancillary source archive is omitted from this checkpoint because its encoded upload exceeds the connector limit; this does not omit the sealed PCB, schematic, native receipts or source-bound engineering checks. The favorable static capacitor sum does not establish effective VIN impedance over the switching spectrum. Actual BEC tolerance/transients, service life, temperature/ripple heating, startup/load-step behavior and input-loop performance need verification. The intended source is Hobbywing Platinum 120A V4 SKU30203401, configured by the user for 7.4 V; that setting and a transient ceiling are not measured. A 25 V capacitor does not extend U14's input limits. Never apply raw 6S to the FC.

The exact D5 maximum package fits its courtyard, but its minimum standoff is zero. Under-body and adjacent tented vias require process-qualified tent integrity, seating/coplanarity and solder-wicking checks. Capacitor 1.450 mm maximum height and enclosure/child-board Z clearance remain physical gates. Ordinary tenting is not filled/capped via-in-pad approval. Sixteen pasted vias/seventeen contacts remain elsewhere.

USB still has explicit 0.170 mm inner/0.150 mm launch widths, varying reference and coupling. Actual production-stack impedance and USB electrical compliance remain unqualified; no 90-ohm claim. Overall power/current/thermal/fault and U2 orientation/FSYNC/connector mapping questions remain.

## Mechanical integration is separate

The latest separately validated mechanical main remains [24 errors](../r61-interface-checkpoint/mechanical/main-right-vias-02/verification.json), while its matching redesigned child has zero errors/opens/ERC with 11 courtyard and 11 filter warnings. The corrected original GND identity and historical rejected native baselines remain documented there. This redesigned interface has not been replayed onto r62 or selected in the current folder yet. The original header in the current project still has 11 edge errors. Physical fit/fixture/solder/strength/vibration tests remain pending.

**Do not fabricate, assemble or fly.** Zero main-board geometric errors is an engineering milestone, not production release. Canonical root remains the older coherent 627-error reference; historical CAM/CPL remain stale. Current candidate BOM/CPL are clearly marked WIP and are bound to this saved board only.
