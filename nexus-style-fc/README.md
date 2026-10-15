# Nexus-style FBL controller

This is a fresh KiCad 10 design modelled on the [RadioMaster Nexus](https://radiomasterrc.com/products/nexus-control-system) flybarless controller. It uses LCSC-purchasable parts and keeps the stock Rotorflight `RDMS-NEXUS_F7` pinout, as its resource-map basis. Stock-target orientation and hardware bring-up remain unverified.

**Status: unfinished F722-rule reroute. Do not fabricate or assemble from this checkpoint.**
The requested rule floor is now 0.127 mm track/clearance, with 0.15 mm preferred signal width,
0.254 mm minimum copper-to-edge (the main board retains its stricter 0.30 mm),
0.20 mm drill-to-copper, 0.25 mm drill-to-drill, and 0.125 mm via annulus.
Existing stronger header-board rules are retained. Main vias remain 0.45/0.20 mm.

## Which PCB should I open?

For the latest improved routing, open **[routing-wip/current/hardware/nexus-style-fc.kicad_pro](routing-wip/current/hardware/nexus-style-fc.kicad_pro)**. Its [PCB](routing-wip/current/hardware/nexus-style-fc.kicad_pcb) is r61 with **two clearance errors**, zero opens and electrical/footprint-filter parity. This simple stable folder contains the matching schematic, project, rules and libraries. [Read the current candidate guide](routing-wip/current/README.md).

The root `hardware/` remains the earlier canonical reference with 627 inherited errors and its coherent approved schematic/part fixes. It is not the improved route. All-visible r61 diagnostics retain 13 centering, five footprint-type and 54 silk warnings; the exact unchanged schematic retains its ERC 0 binding. Historical snapshots and [exact validation evidence](routing-wip/2026-10-15/r61-interface-checkpoint/README.md) are retained separately.

The approved capacitor pair/D5 relocation is undergoing atomic source/PCB validation and is not in this freeze. Separate mechanical progress has 24 errors on the main board and zero child errors/opens; historical native mechanical baselines with an automatic via-net reassignment are explicitly rejected. USB impedance, power/current/thermal/transient, via-in-paste process, mechanical fit/strength and assembly remain open. CAM/CPL are historical/stale. **Do not fabricate, assemble or fly.**


![Floorplan](docs/images/floorplan.svg)

| Path | Contents |
|---|---|
| `hardware/nexus-style-fc.kicad_pro` | Main board: full schematic + routed 6-layer PCB |
| `hardware/header-board/` | Servo-header child board, a separate KiCad project |
| `hardware/library/` | LCSC footprints, symbols and 3D models, plus the project footprints |
| `firmware/RDMS-NEXUS_F7.config` | Upstream Rotorflight target config, used for the pin map (see below) |
| `tools/` | `design.py` (single source of truth) + generators and routing; `build_all.sh` rebuilds everything and runs the checks |
| `manufacturing/` | Per board: JLCPCB Gerber zip, BOM and CPL; plus KiCad BOMs |
| `docs/` | Review notes and renders |

The firmware config is copied unchanged from [rotorflight-targets `configs/RDMS-NEXUS_F7.config`](https://github.com/rotorflight/rotorflight-targets/blob/master/configs/RDMS-NEXUS_F7.config) (master, latest commit `b89676f`, 2026-03-02) and stays attributed to its upstream authors. No firmware binary is included. RadioMaster branding is not used on the board.

The power block is also available as a separate board: [../nexus-style-fc-power-module](../nexus-style-fc-power-module/) takes its parts from `tools/design.py` and uses the generators in `tools/`.
