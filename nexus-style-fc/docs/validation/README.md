# Nexus validation and provenance

Latest assembly sourcing update: [R23 replacement, 18 October 2026](reviews/r23-replacement-2026-10-18/REVIEW.md). R23 is C2766886 / Uniroyal 0402WGJ012KTCE, 0.12 Ω ±5%. Only component metadata and BOM change; Gerbers, routing and CPL remain unchanged.

This is the single evidence location. **The working design is `../../hardware/`, not any historical report or illustration here. Nothing here grants fabrication, assembly or flight approval.**

## Current order package

Latest source/CAM binding: [standard-stack adaptation](reviews/standard-stack-2026-10-17/REVIEW.md). Main Gerbers now use standard JLC06161H-3313, exchanged In1/In2 copper contents and 0.132/0.165 mm USB trunks. Earlier revision reports remain historical; assembly/process requirements still apply.

The [17 October order-fixes review](reviews/order-fixes-2026-10-17/REVIEW.md) records the preceding electrical/mechanical fixes. Its main PCB/CAM hashes predate the standard-stack change; its assembly/process findings still apply. Main native ERC/DRC/opens/parity are all zero; child has zero errors/opens/parity with 11 bare-contact courtyard warnings. Fresh JLCDFM uses current main 53-group / 84-placement assembly files and both current Gerber ZIPs. Remaining factory process requirements and physical qualification limits are detailed in that review and [manufacturing instructions](../../manufacturing/ORDER-INSTRUCTIONS.txt).

## Earlier checks and historical gates

The entries and gate descriptions below retain their historical scope. Use the standard-stack review above for present files and hashes, together with the order-fixes review for assembly/process findings.


- [USB 90 ohm correction](reviews/usb-compliance-2026-10-17/REVIEW.md): historical custom-stack correction, superseded by the standard-stack adaptation above, zero native violations/opens and unchanged 29 fresh DFM category triples; supplier impedance and full-port electrical qualification pending
- [Latest child cleanup DFM](reviews/child-dfm-20261017-200904/REVIEW.md): current child PCB/CAM, zero native errors/opens/parity issues and zero JLCDFM danger / 38 warnings; unchanged by the USB revision
- [Four-layer child power upgrade](reviews/child-full-load-2026-10-17/REVIEW.md): earlier child calculation/source, dedicated inner VX/GND planes and 27 added power vias; unchanged interface/signals, no native errors/opens/parity issues; 19.6 A electrical stress loss reduced from 0.767 to 0.282 W on the same grid. Requires specified 2 oz inner copper; thermal/contact/BEC limits remain open.
- [Owner VX/3V3 cleanup recheck](reviews/owner-vx-recheck-2026-10-17/REVIEW.md): predecessor main PCB/CAM, preserved owner route geometry, native zero violations/opens, matching refreshed pours/exports and identical fresh PCB DFM category counts
- [Uniform VX corner links](reviews/vx-corner-width-2026-10-17/REVIEW.md): predecessor PCB/CAM, only the In2/In3 child-board corner links at 0.60 mm, one VX via shifted 0.06 mm; other VX widths unchanged, zero native DRC violations/opens; fresh PCB DFM preserves all danger/warning counts
- [Rounded slot keepouts](reviews/rounded-keepout-2026-10-17/REVIEW.md): predecessor PCB/CAM, R0.35 mm keepout corners preserving nominal 0.35 mm slot buffer and the owner's 0.60 mm VX entry; 227 vias, zero native DRC violations/opens; fresh PCB DFM preserves all predecessor category counts
- [Applied VX copper improvement](reviews/vx-copper-2026-10-17/REVIEW.md): predecessor PCB/CAM, 0.60/0.30 mm back link and wider inner copper, unchanged physical slots and 228 vias; native checks and fresh PCB DFM preserve all predecessor category counts
- [VX copper feasibility](reviews/vx-feasibility-2026-10-17/REVIEW.md): earlier isolated DRC-checked proposal, subsequently applied by the VX copper review above
- [SMT pin-edge review](reviews/pin-edges-2026-10-17/REVIEW.md): leave the ten left/right edge flags on D1-D3 and F1/F2 unchanged based on manufacturer drawings and native pad geometry; limited engineering disposition, other assembly gates remain open
- [C8 via review](reviews/c8-via-2026-10-17/REVIEW.md): predecessor PCB/CAM, final two mask-to-trace warnings cleared by the owner, native checks and unchanged BOM/CPL; C8 via-in-pad requires filled/capped production process
- [Solder-mask correction](reviews/solder-mask-2026-10-17/REVIEW.md): predecessor PCB/CAM, mask-to-trace warnings 82 to 2 and negative-expansion flags 10 to 5, preserved green spacing/width/corners, native checks and two X-only CPL changes
- [Pad-spacing correction](reviews/pad-spacing-2026-10-17/REVIEW.md): predecessor PCB/CAM, pad spacing green (0 danger/0 warnings), native checks and five coordinate-only CPL changes
- [Owner cleanup DFM recheck](reviews/cleanup-recheck4-2026-10-17/REVIEW.md): earlier owner-cleaned PCB/CAM, refreshed native fills, preserved source geometry, native and website checks
- [Earlier owner cleanup DFM recheck](reviews/cleanup-recheck3-2026-10-17/REVIEW.md): earlier owner-cleaned PCB/CAM, preserved source geometry, native and website checks
- [Earlier owner cleanup DFM recheck](reviews/cleanup-recheck2-2026-10-17/REVIEW.md): earlier owner-cleaned PCB/CAM, preserved source geometry, native and website checks
- [Owner cleanup DFM recheck](reviews/cleanup-recheck-2026-10-17/REVIEW.md): earlier owner-cleaned PCB/CAM, preserved source geometry, native and website checks
- [Final outer-layer 0.14 mm routing](reviews/width-final-2026-10-17/REVIEW.md): earlier PCB/CAM, all outer tracks at least 0.14 mm, local route adjustments and 0.016 mm IMU_CS via shift; native/website checks
- [Partial-segment 0.14 mm width improvement](reviews/width-profile-2026-10-17/REVIEW.md): earlier PCB/CAM, 57.8 mm widened across 25 nets with short narrow necks retained; fresh native/website checks
- [Gerber regeneration and JLCDFM reupload](reviews/gerber-reupload-2026-10-17/REVIEW.md): earlier saved PCB/CAM, unchanged assembly files and native/website PCB check
- [0.14 mm outer trace widths](reviews/width-014-2026-10-17/REVIEW.md): earlier copper/CAM, 456 clearance-safe width changes, 70 constrained sections retained, native checks and website comparison
- [TAIL loop cleanup](reviews/tail-route-2026-10-17/REVIEW.md): earlier copper/CAM, preserved protection and exact connectivity; incoming schematic/library warnings retained
- [Trace DFM correction](reviews/trace-dfm-2026-10-17/REVIEW.md): earlier corner/spacing correction and its exact PCB screening
- [Fabrication cleanup](fabrication-fixes/REPORT.md): predecessor copper checks, artwork changes and open gates
- [Pre-fix JLCDFM PCB/SMT recheck](reviews/jlcdfm-current-2026-10-17/REVIEW.md): earlier Gerbers, unchanged 51-group BOM and corrected 83-placement CPL screened; remaining assembly flags recorded

- [Consolidation report](consolidation/REPORT.md): fresh read-only KiCad 10.0.7 ERC/DRC, native/source/BOM/CPL checks and path inventory
- [Main stage36 engineering report](stage36/MAIN-PLACEMENT-CHECKPOINT.md) and [original source seal](stage36/ENGINEERING-CHECKPOINT-SEAL.json)
- [17 October CPL correction and assembly check](reviews/cpl-2026-10-17/REVIEW.md): verified bottom angles and U10 offset for the unchanged pad placements; 83 placements checked on predecessor CAM with its 48-group BOM
- [Stage36 predecessor PCB/SMT JLCDFM](reviews/jlcdfm-main-stage36/REVIEW-STATUS.md): completed numerical screening; historical findings and process limits, not current CAM approval
- [Child b49ef410 JLCDFM](reviews/jlcdfm-child-b49ef410/REVIEW-STATUS.md), [child engineering review](child-b49ef410/ENGINEERING-REVIEW.md) and [mechanical proposal](child-b49ef410/verification/mechanical/PCB_ONLY_PROPOSAL.md)
- [Stage35 DFM](reviews/jlcdfm-main-stage35/REVIEW-STATUS.md) and [stage10 DFM](reviews/jlcdfm-stage10/REVIEW-STATUS.md) are historical main-board evidence

The consolidation preserved the owner-restored source. The current fabrication cleanup adds main-only artwork identities and reviewed symbol filters while retaining parts, pad geometry and placement. The restored CPL correction changes 25 rotation fields only; coordinates, sides and reference coverage are preserved. The current BOM has 51 groups/83 parts. The CPL review's website result remains bound to its recorded predecessor PCB/CAM and 48-group BOM. The subsequent PCB/SMT recheck screens the fabrication-cleanup CAM and 51-group BOM with the corrected CPL. The pad-spacing correction adjusts copper and five small component positions. The solder-mask correction adjusts outer pours/routes and shifts C9/C11 0.025 mm. The owner-added C8 ground via opens the LED2_K corridor and clears the remaining mask-to-trace warnings. The VX improvement adds a back-layer link and widens inner copper. The latest owner edit widens its entry to 0.60 mm and removes a redundant GND via, leaving 227 vias. Rounded slot keepouts preserve that owner edit and the physical slots. The latest corner-only VX update makes the In2/In3 slot-corner links 0.60 mm, with one 0.06 mm via shift while retaining all other VX widths; its report retains that revision binding. The latest owner VX/3V3 cleanup preserves geometry through a fresh native refill/check; the owner-recheck report binds its predecessor CAM and unchanged BOM/CPL. The earlier USB correction bound its then-current main CAM to the custom JLC06161H-2116A stack and records nominal 90 ohm calculations; supplier impedance and full-port electrical qualification remain pending. C8 via-in-pad requires epoxy filling and copper capping on the production order. The BOM is unchanged. SMT was not rerun for this revision. Historical seals and input bindings retain their original hashes, including the pre-correction CPL entry in the fabrication-cleanup binding. Excluded historical generators have not been restored.

## How evidence is bound to a revision

[Source map](SOURCE-MAP.json) maps retained files to their original paths and Git blob IDs at source commit [fad6207](https://github.com/chenguoming1/h743-controllers/tree/fad62076054229a1d3de79106984d8b71906379e/nexus-style-fc). Main and child source files were promoted from its `routing-wip/2026-10-15/stage36-main-child-checkpoint/candidate/`. Existing root 3D model dependencies and the firmware reference were retained.

Reports, seals, hashes and historical reproduction scripts retain their original bytes. Their embedded paths and relative links describe the original sealed layout and are not instructions to regenerate the canonical design. Use `source_path` in the source map with the pinned commit above to inspect a report in its original context. Historical scripts may require historical inputs that now exist only in Git; they are evidence, not supported current build entrypoints. Unrouted comparison boards, duplicate CAD project copies, old CAM exports and source ZIPs were intentionally removed from the working tree and remain recoverable from that commit.

`history/` holds unique earlier review evidence, deduplicated by Git blob identity. Revision folders here are evidence only; they contain no `.kicad_pcb`, `.kicad_sch`, `.kicad_pro` or generator copies. Older claims apply only to the revision named by each report. Exact project states and redundant copies belong in Git history.

## Open release gates

The inherited detailed reviews do not supersede these current limits:

- Current PCB DFM has green pad spacing, width, spacing and corners, but requires the C8 filled/capped via-in-pad production process and retains five unconfirmed negative-mask flags, three via-to-pad and four slot-width danger flags, plus capped silkscreen findings; the prior assembly DFM recorded 24 danger flags and 13 warnings
- U10's CPL orientation and model overlap were clear in the prior assembly preview; real assembly fit remains unqualified
- C10/NRST local placement remains unresolved; no electrical redesign was attempted here
- Matched main/child fit, edge access and mechanical/vibration tests remain open
- Supplier stackup, board thickness, copper weight, tenting/stencil and other process approval remain open
- Header/contact current and physical joints need qualification; retained header rating is 3 A, not a 10 A system rating
- Effective capacitance, thermal/transient, SI/PI/EMI, firmware orientation/bring-up and flight tests remain open

The fresh ERC reports each retain four inherited ignored checks: `single_global_label`, `four_way_junction`, `simulation_model_issue`, `footprint_filter`. DRC disables no checks. Read the reports rather than interpreting zero errors as unconditional sign-off.
