# Nexus-style FBL controller

This is a fresh KiCad 10 design modelled on the [RadioMaster Nexus](https://radiomasterrc.com/products/nexus-control-system) flybarless controller. It uses LCSC-purchasable parts and keeps the stock Rotorflight `RDMS-NEXUS_F7` pinout, so the standard Nexus firmware target can run on it.

**Status: revision 5 — fully routed, ready to order from JLCPCB.** It has a 22.4 × 33.1 mm 6-layer main board (88 parts, 82 placed by JLC) and a vertical servo-header child board that joins it VBar style: two tabs through two non-plated slots, soldered on the main board's bottom face. It is sized to the Nexus 41.3 × 25.4 mm case. Both boards pass ERC, DRC (0 errors, 0 unconnected) and schematic/PCB parity, using only JLCPCB's no-extra-cost rules (0.09 mm track and space, one 0.2/0.45 mm via). See [docs/layout-review.md](docs/layout-review.md), the [schematic PDF](docs/schematic-main.pdf) and the [manufacturing files](manufacturing/).

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
