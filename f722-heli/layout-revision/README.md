# F722 layout revision — work in progress

**Unrouted placement checkpoint. Do not manufacture or fly this revision.**

This replacement placement moves components inward from the through-hole headers, spreads the side sockets, keeps the LEDs and switch beside the upward USB connector, and uses orthogonal component orientations. The converter and its support parts are grouped on the right, with servo/RPM/SBUS protection on the left. It retains six copper layers, the 47.5 × 25.4 mm overall assembly, the board outline and stock Nexus external/MCU pin assignments.

The paired project is `hardware/f722-heli.kicad_pro`. All 156 target poses are explicit in `placement.json`; 104 differ from the published source. R7/R8 are changed to 2.2 kΩ (UNI-ROYAL 0402WGF2201TCE, C25879), and U13 uses equivalent protection channels 3/6/1 for ESC/RPM/SBUS. Native PCB, schematics and parts metadata agree. Published U14 mapping is retained.

## Checked checkpoint

KiCad 10.0.6 reports **378 unfinished connections, 0 geometric errors, 0 warnings and 0 ERC violations**. All assigned native pad nets and component values match the paired schematic. All 29 firmware pin checks pass. Rebuilding from the pinned published source reproduces the native PCB bytes.

Fresh body/courtyard, bounded process, header-access, USB-keepout, edge and mounting-hole screens also pass. Some courtyard gaps remain very small (0.001 mm inherited U1–C4; 0.005 mm near R66); the physical-body/solder screen is bounded and does not establish assembly qualification.

These results validate the placement reconstruction and schematic consistency. All old routing and filled-copper zones were deliberately removed. Complete routing, power/ground copper, physical protection-path checks, reference continuity, current-capacity analysis and new manufacturing exports remain outstanding. This is a new build from GitHub source, not the previously routed intermediate board.

Machine-readable source identity and results are in `source.json`, `placement-build.json` and `checks/current-status.json`. The original published `../hardware`, `../manufacturing` and electrical reports describe the previous layout; their routing and electrical results do not validate this candidate.

## Reproduce

Use KiCad 10.0.6 with a Python environment providing `pcbnew`. From this directory, build into a new output directory:

```sh
python scripts/rebuild_placement.py --source ../hardware --out /path/to/new/hardware
python scripts/patch_metadata.py --hardware /path/to/new/hardware --report /path/to/metadata-changes.json --apply
kicad-cli sch export netlist --format kicadxml --output /path/to/reconstructed.net /path/to/new/hardware/f722-heli.kicad_sch
python scripts/check_native_parity.py --board /path/to/new/hardware/f722-heli.kicad_pcb --netlist /path/to/reconstructed.net --out /path/to/parity.json
kicad-cli pcb drc --format json --output /path/to/drc.json /path/to/new/hardware/f722-heli.kicad_pcb
kicad-cli sch erc --format json --output /path/to/erc.json /path/to/new/hardware/f722-heli.kicad_sch
```

The builder requires published board SHA256 `4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f` and refuses to reuse an output directory. Subsequent routing checkpoints will update this draft branch with their exact checks and remaining work.

## Placement previews

[Front placement](checks/placement-front.svg) · [Mirrored back placement](checks/placement-back.svg)
