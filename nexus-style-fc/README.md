# Nexus-style FBL controller

This is a fresh KiCad 10 design modelled on the [RadioMaster Nexus](https://radiomasterrc.com/products/nexus-control-system) flybarless controller. It uses LCSC-purchasable parts and keeps the stock Rotorflight `RDMS-NEXUS_F7` pinout, as its resource-map basis. Stock-target orientation and hardware bring-up remain unverified.

**Status: unfinished F722-rule reroute. Do not fabricate or assemble from this checkpoint.**
The requested rule floor is now 0.127 mm track/clearance, with 0.15 mm preferred signal width,
0.254 mm minimum copper-to-edge (the main board retains its stricter 0.30 mm),
0.20 mm drill-to-copper, 0.25 mm drill-to-drill, and 0.125 mm via annulus.
Existing stronger header-board rules are retained. Main vias remain 0.45/0.20 mm.

## Which PCB should I open?

Open **[routing-wip/current/hardware/nexus-style-fc.kicad_pro](routing-wip/current/hardware/nexus-style-fc.kicad_pro)** for the latest improved PCB. The [current guide](routing-wip/current/README.md) links its board, matching schematic, PDFs and review exports.

Current r62 has **zero native main-board errors, zero opens and zero schematic parity issues**, including the approved C27/C31 capacitor pair and D5 0.400 mm move. All-visible diagnostics retain 11 centering, five footprint-type and 54 silk warnings. Enabled ERC has zero findings; all-visible ERC retains 13 single-global-label advisories. [Exact evidence](routing-wip/2026-10-15/input-caps-checkpoint/README.md).

The root `hardware/` remains the older coherent canonical reference with 627 inherited errors. The redesigned mechanical interface is still separate: main 24 errors, child zero errors/opens with warnings. Its integration and physical tests remain unfinished. The current project still carries the original header with 11 edge errors.

USB impedance/compliance, actual capacitor/input-loop and BEC-transient behavior, power/current/thermal, via-in-paste process, enclosure/assembly and mechanical qualification remain open. Current BOM/CPL are review-only WIP; old canonical CAM/CPL are historical/stale. **Do not fabricate, assemble or fly.**


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
