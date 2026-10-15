# Nexus-style FBL controller

This is a fresh KiCad 10 design modelled on the [RadioMaster Nexus](https://radiomasterrc.com/products/nexus-control-system) flybarless controller. It uses LCSC-purchasable parts and keeps the stock Rotorflight `RDMS-NEXUS_F7` pinout, as its resource-map basis. Stock-target orientation and hardware bring-up remain unverified.

**Status: unfinished F722-rule reroute. Do not fabricate or assemble from this checkpoint.**
The requested rule floor is now 0.127 mm track/clearance, with 0.15 mm preferred signal width,
0.254 mm minimum copper-to-edge (the main board retains its stricter 0.30 mm),
0.20 mm drill-to-copper, 0.25 mm drill-to-drill, and 0.125 mm via annulus.
Existing stronger header-board rules are retained. Main vias remain 0.45/0.20 mm.

The canonical board retains the approved U10 EN isolation, C19-only 10uF/C19702 upgrade and conventional schematic across all 15 functional sections. Fresh KiCad 10.0.7 validation reports 627 inherited errors. The separate [current experimental route](routing-wip/2026-10-15/local-r57-checkpoint/README.md) has 13 clearance errors. Both have zero opens, electrical/footprint-filter parity and ERC findings. All-visible checks additionally disclose 21 canonical / 17 experimental off-center warnings, five footprint-type warnings and 54 silk warnings each. The unchanged accepted header has 11 contact-edge errors. All remain unfinished.

Review the [fresh single-sheet schematic](docs/schematic-main.pdf), [visually equivalent functional-unit booklet](docs/nexus-schematic-review.pdf), [current schematic source archive](docs/nexus-drafted-schematic-source-and-validation.zip), and [exact validation/open gates](docs/f722-reroute-status.md). The main-only reviewed-library binding preserves shared design imports and all selected parts. The approved mechanical redesign is separately preserved as an unfinished candidate with known copper conflicts and physical tests pending. CAM/CPL remain historical/stale and manufacturing stays on hold.


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
