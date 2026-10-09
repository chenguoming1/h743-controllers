# F722 layout revision — work in progress

**Partially routed checkpoint. Do not manufacture or fly this revision.**

This replacement placement moves components inward from the through-hole headers, spreads the side sockets, keeps the LEDs and switch beside the upward USB connector, and uses orthogonal component orientations. The converter and its support parts are grouped on the right, with servo/RPM/SBUS protection on the left. It retains six copper layers, the 47.5 × 25.4 mm overall assembly, the board outline and stock Nexus external/MCU pin assignments.

The paired project is `hardware/f722-heli.kicad_pro`. All 156 target poses are explicit in `placement.json`; 108 differ from the published source. R7/R8 are changed to 2.2 kΩ (UNI-ROYAL 0402WGF2201TCE, C25879), and U13 uses equivalent protection channels 3/6/1 for ESC/RPM/SBUS. Native PCB, schematics and parts metadata agree. Published U14 mapping is retained.

## Checked checkpoint

KiCad 10.0.6 reports **158 unfinished connections, 0 geometric errors, 17 dangling-interface warnings and 0 ERC violations**. All assigned native pad nets and component values match the paired schematic. All 29 firmware pin checks pass. Sixteen critical clock, IMU, VCAP and USB nets are connected; all ground pads belong to one connected pad group. Loaded power trunks and ordinary signals remain incomplete.

The native via/drill/mask process screen passes. Only 1 of the original 18 protection-path checks passes because the ordinary protection routes are unfinished. Five of seven supplemental checks pass, covering USB data and CC2; RPM/SBUS remain incomplete. The CC2 route was rebuilt to remove its inherited bypass and now has a 0.187102 mm outside-pad gap. These counts are separate scopes, not interchangeable totals.
Fresh body/courtyard, bounded process, header-access, USB-keepout, edge and mounting-hole screens also pass. Some courtyard gaps remain very small (0.001 mm inherited U1–C4; 0.005 mm near R66); the physical-body/solder screen is bounded and does not establish assembly qualification.

These results establish partial connectivity and geometric consistency. Loaded copper current/return analysis, remaining routing, signal timing/reference review and manufacturing exports are still outstanding. USB uses nominal manufacturer pair geometry, but nearby power pads and the connector crossover require qualification of the actual stackup and assembly. No controlled-impedance or flight qualification is claimed.

The native PCB is the authoritative routed source. The placement recipe below recreates the current component arrangement without its routing. The source-only local router and its recorded controls are under `routing-tools/`; no actual ordinary autorouting run has yet been accepted.
Machine-readable source identity and results are in `source.json`, `placement-build.json`, `routing-build.json` and `checks/current-status.json`. The original published `../hardware`, `../manufacturing` and electrical reports describe the previous layout; their routing and electrical results do not validate this candidate.

## Reproduce

Use KiCad 10.0.6 with a Python environment providing `pcbnew`. From this directory, rebuild the placement (routing deliberately excluded) into a new output directory:

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
