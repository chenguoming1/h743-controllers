# F722 controller: native1 MOSI/BARO layout, work in progress

**Open [hardware/f722-heli.kicad_pro](hardware/f722-heli.kicad_pro). One connection remains: PORT_C_RX_EXT (J11.1 to R34.1). This is an adopted prototype routing baseline, not fabrication-ready or flight-qualified.**

The normal paired project binds all 61 design files; only the PCB differs from native2. PCB SHA-256: `b31e6b9ca47e8e5a0b8967ec25f8390a66541b0c374ebedde77a39380e7d73ca`. See [canonical provenance](hardware/CANONICAL-SOURCE.json) and the [immutable native1 checkpoint](layout-revision/checkpoints/native1-mosi-baro-v1-20261013/README.md).

FLASH_MOSI is closed with 25 added tracks and two through vias, plus one removed PORT_B_RX_MCU track for its repair. No footprint pose or pad mapping changes; all 2,479 retained objects and the complete native2 RX path remain exact. Recorded geometric DRC, warnings, ERC and parity findings are zero. The raw inherited contact-applicability and aggregate flags remain false; a fresh narrow VX review supports the exact changed window without relaxing the general predicate.

Fresh DC passes all 294 required cases on both grids, 15 numerical comparisons and five VCAP copper-loop checks. The raw overall screen remains false for the approximately 18.56 A lost-J6-feed illustration: J2-J5 fine-grid board pads are 5.86372-5.87853 V against 6 V floors. These conditional model results do not establish servo terminal voltage, thermal performance or ampacity.

SPI/BARO finite return paths are approximately 9.887/10.103 mm. They support only a conditional 27 MHz prototype/bench envelope, with flash settling, BARO/IMU noise, GPIO edge and ESD/EMC checks still required. 30 MHz remains a stress case, and the installed binary/live registers are unverified. The approved 400 kHz I2C setup retains its overshoot/measurement caveat; 385 kHz remains pending. No firmware setting changes here. JLC ordinary-via process/stack, USB slots and StandardPCBA panel acceptance are unresolved.

The checkpoint includes tested byte-exact board reconstruction, a distinct unrun native replay recipe, complete native exports and lossless raw DC evidence. Portable DC source/hash/model checks passed; heavy portable replay remains unrun. Native1 reference measurement sources and required inputs are preserved; their archival launcher requires path rebinding and runtime setup, and heavy geometry replay is unrun. All prior checkpoints, including the native2 portable source supplement, and all B-RID files remain unchanged.

## Historical manufacturing records

The [final95 overview](README-final95-historical.md), older docs/ images, validation/ status and manufacturing/ outputs describe earlier geometry. They do not qualify this unfinished one-open board. Regenerate final BOM/CPL/Gerber/stencil data from the eventual completed project and verify factory orientation, including R35's retained B.Cu 270-degree pose. See the [layout history](layout-revision/README.md). No manufacturing or flight release is made here.
