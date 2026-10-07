# Assembly and procurement notes

**VERIFIED PROTOTYPE FILES / FACTORY CAM AND ASSEMBLY ACCEPTANCE REQUIRED.** The final exact-board electrical review is complete. CSVs are prepared for factory review/import; procurement and assembly still require the conditions below. No production or flight qualification is claimed.

All CSV quantities are per board. Exact values and footprints come from PCB `4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f`; manufacturer/MPN/code identities come from its paired `hardware/parts.json`. No blank LCSC code was replaced with another part. Current inventory, lead times, feeder quantities, attrition and assembler acceptance have not been established.

## File scope

| File | Scope |
|---|---|
| procurement-full-per-reference.csv | 151 populated references, exact values/footprints/MPNs, manufacturer, code, source URLs, route and exceptions |
| procurement-full-grouped.csv | Same 151 references in 86 value/footprint/identity groups; no omissions or duplicates |
| jlc-bom-SMT-HELD.csv | Four standard columns: Comment, Designator, Footprint, LCSC Part #; 79 groups / 144 SMT candidate references |
| jlc-cpl-SMT-HELD.csv | Designator, Mid X, Mid Y, Layer, Rotation; exactly the same 144 references, 59 top and 85 bottom |
| native-all-pos.csv | Unmodified KiCad native CSV, 151 populated references including THT headers |
| placement-all-populated-reference.csv | Native positions joined to exact MPN and full footprint identifier |
| placement-manual-THT.csv | J2–J8, seven headers and 21 pins; exact native side/pose and procurement notes |
| excluded-board-features.csv | TP1–TP5, five bare SWD test pads excluded by native flags; no purchased/placed item |
| factory-rotation-verification-required.csv | All 144 SMT poses with zero applied correction and required factory preview check |

There are **no DNP parts**. The connector and test-pad omissions from the SMT files are deliberate handling classifications, not accidental BOM/CPL mismatches. J1 remains in the machine candidate set because its signal contacts are SMT; its shell stakes need the additional operation below. Do not use a blanket “exclude footprints with through-hole pads” option that would drop J1 unnoticed.

## Exact exceptions

- **R31:** YAGEO **AC0201FR-0722RL / C144830**, 22 Ω ±1%, EIA0201, exact local `F722_YAGEO:R_0201_0603Metric_YAGEO_AC` footprint. Rated **50 mW at 70°C**, with manufacturer derating; working-voltage ceiling 25 V and TCR ±200 ppm/°C per retained evidence. Do not carry over the previous larger-package rating. Current board R30 retains its separate source selection; the historical two-resistor feasibility note is not a substitution instruction. The retained source marks C144830 Standard Only; confirm factory process and small-board handling
- **R16:** Panasonic **ERJ3RSFR12V / C4059772**, 0.12 Ω ±1%, 0.1 W, exact dedicated `F722_Heli:R_Panasonic_ERJ3R_0603` footprint. The supplier display form is ERJ-3RSFR12V; exact identity is preserved. **Assembly supply is pending confirmation / private-stock route**. Its presence in the JLC BOM does not mean that public assembly stock is available. No substitute is authorized. Confirm actual part sourcing, stencil/reflow, installed R16/C7/copper impedance, startup and regulator stability
- **J2–J8:** Seven Samtec **HTSW-101-08-L-T-RA** right-angle three-position/triple-row THT headers. **No LCSC code exists in the supplied source**. They remain in procurement and the separate manual/THT placement reference, with supplier URL retained. Arrange actual procurement and accepted consigned/THT/manual assembly handling. Confirm all 21 pin solder joints, pin-1/net order, connector seating, tail projection, fillets and mating clearance. Do not drop these headers from the finished-assembly scope or select an unrelated coded header
- **J1:** GCT **USB4145-03-0170-C / C5181332**, true vertical/top-entry USB-C; selected shell-stake length is **1.70 mm**, not the 0.70 mm preview variant. Four 1.10×0.60 mm plated shell slots must be soldered for mechanical retention. **No shell paste apertures are specified or exported**. The 16 SMT contact apertures remain. Factory acceptance must cover shell-slot solder filling, compatible process, pickup cap, reflow/assembly order, access from below, rotation/pickup mapping, and any difficulty-related handling. SMT-only contact reflow does not complete this connector

J1 nominal shell height is 7.46 mm above PCB; the temporary pickup cap reaches 8.46 mm. The provisional footprint reserve below the four stakes is 1.20 mm; it is not a certified 3D clearance. With minimum finished PCB thickness 0.927 mm and maximum stake length 1.80 mm, bare stake projection can be 0.873 mm before solder fillets. Confirm the real assembly envelope, mating cable/overmold space, final PCB thickness and fixture clearance.

## Factory placement and inspection

The exported origin is (0,0), mm. Signed X/Y values and rotations are copied from native KiCad; no guessed factory rotation offsets or bottom-side X flips were applied. Negative Y values are intentional and align with Gerber/drill data. Import these together and verify the complete placement preview on both sides. Approve every library pin-1/polarity/pickup mapping against the native board, especially custom/local packages, J1 and sensors. The checklist records that this remains required; it does not assert the preview was inspected on a factory website.

Confirm stencil/reflow capability for 0201, fine-pitch ICs and the dedicated R16 footprint. Preserve the existing split/thermal paste aperture designs. Confirm bottom-side assembly sequence and USB/THT access. Full maximum-body connector depth/height and all mating/fillet tolerances remain part of final mechanical acceptance.

After assembly, first-article power, shorts/isolation, startup, rail regulation/stability, USB, sensor orientation/noise, receiver, output and failsafe checks remain necessary with motors disconnected. Original Nexus pinout and firmware are unchanged. The user's Hobbywing Platinum 200A SBEC and KST servo combination are electrical operating-context inputs to the completed final electrical review, not added BOM items or a current-capability claim by this package.
