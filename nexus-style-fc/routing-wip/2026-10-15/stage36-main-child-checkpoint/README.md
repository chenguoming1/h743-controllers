# Nexus stage36 main + redesigned child: unfinished engineering checkpoint

**Incomplete source draft:** the owner requested exclusion of all newly added design.py files from GitHub, including the latest and historical generators and the prepared-design.py near-copy. [Exact exclusion and reproduction limit](EXCLUDED-SOURCE.md). The saved PCB/schematic are reviewable, but the complete main generator is not included.

## Open this matched candidate

[KiCad project](candidate/hardware/nexus-style-fc.kicad_pro), [main PCB](candidate/hardware/nexus-style-fc.kicad_pcb), [child PCB](candidate/hardware/header-board/nexus-header-board.kicad_pcb), [matching schematic](candidate/hardware/nexus-style-fc.kicad_sch).

[Stage36 engineering report](candidate/MAIN-PLACEMENT-CHECKPOINT.md) and [exact source seal](candidate/ENGINEERING-CHECKPOINT-SEAL.json) describe the accepted scope, warnings and limits. This checkpoint leaves routing-wip/current unchanged. **Do not fabricate, assemble or fly.**

Main PCB SHA256 bed37199e8d62b8135a27b9e182f8e8f584f1a9fb722cb6efb5d4c87b2a320b8. Child PCB SHA256 b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6. Stage36 seal SHA256 3c778d236ba3876dbde64401e8edc67409db6e59547cb30dfc11b40dc6638270.

Main native KiCad 10.0.7 checks: zero errors, zero opens and zero schematic parity violations; 61 warnings remain. Source consistency covers 89 footprints, 356 pads, 48 BOM groups and 83 placements. Stage36 improves the ADC filter placement/routes while retaining stage35 power, decoupling, USB and local DFM repairs. NRST/crystal routing remains unchanged and local NRST placement is still unresolved. Matching review-only manufacturing/BOM/CPL files are under candidate/manufacturing; never combine historical exports with this candidate.

The child retains standard 3×7 servo plugs and continuous VX copper on a declared two-layer, 2 oz-per-face design. Retained header rating is 3 A; this does not establish a 10 A system rating. Matched-profile fit, supplier copper/thickness/process acceptance, contact/current, thermal/transient and physical joint/vibration qualification remain open.

## External checks, with exact revision boundaries

- [Fresh stage36 PCB-only DFM](reviews/jlcdfm-main-stage36/REVIEW-STATUS.md): pad-spacing dangers 7 → 6; the prior mask-exposure and free-end targets remain clear. Matching BOM accepted; CPL upload executed but acceptance unverified, so **no stage36 assembly DFM result**.

- [Child JLCDFM](reviews/jlcdfm-child-b49ef410/REVIEW-STATUS.md): same b49ef410 child, PCB 0 danger / 32 warnings, assembly 0 danger / 7 warnings. No factory 2 oz process approval or downloaded report PDF.
- [Stage35 main JLCDFM](reviews/jlcdfm-main-stage35/REVIEW-STATUS.md): predecessor main bf9a1056 only. Targeted mask-sliver and free-end findings cleared; U10 model/overlap and other process findings remain. **This is not fresh stage36 DFM.**
- [Stage10 DFM](reviews/jlcdfm-stage10/REVIEW-STATUS.md) is historical baseline evidence only.
- [Original placement review](reviews/placement/REVIEW.md), [PDF](reviews/placement/Nexus-stage10-placement-audit.pdf) and [copper diagram](reviews/placement/critical-paths.png) describe stage10, not unresolved defects inferred afresh in stage36.
- [U10 audit](reviews/u10/AUDIT.md) records native pinout/origin evidence, model uncertainty and exploratory land-pattern checks. Read its source boundaries; do not apply its early isolated candidate to stage36.

## Child design evidence

[Child engineering overview](historical-child-engineering/ENGINEERING-REVIEW.md), [review PDF](historical-child-engineering/verification/preview/child-continuous-vx-review.pdf), [original seal](historical-child-engineering/CHILD-ENGINEERING-SEAL.json), [matched-fit review](historical-child-engineering/verification/mechanical/PCB_ONLY_PROPOSAL.md).

The historical-child-engineering folder preserves the original child review and its then-matching stage10-slot main snapshot, except the explicitly excluded historical design.py. Its main PCB is historical; the sole latest matched main/child source is candidate/. The unchanged child hash binds its child-specific receipts. No main-stage acceptance is inferred from child-only validation.

No private account/session/project identifiers or credentials are included. Standalone power module, F722 and B-RID are untouched. No manufacturing, assembly, flight, USB compliance, SI/PI or power/thermal release is claimed.
