# Nexus-style FBL controller

This is a fresh KiCad 10 design modelled on the [RadioMaster Nexus](https://radiomasterrc.com/products/nexus-control-system) flybarless controller. It uses LCSC-purchasable parts and keeps the stock Rotorflight `RDMS-NEXUS_F7` pinout, so the standard Nexus firmware target can run on it.

**Status: revision 4 — full schematic, every part placed, not routed yet.** It has a 22.4 × 33.1 mm 4-layer main board (88 parts) and a vertical servo-header child board on three long tabs (bar–gap–bar–gap–bar) through non-plated slots, soldered on both faces, with no parts within 5.0 mm of the header edge, sized to the Nexus 41.3 × 25.4 mm case. Both boards pass ERC, DRC and schematic/PCB parity. See [docs/layout-review.md](docs/layout-review.md), the [schematic PDF](docs/schematic-main.pdf) and the [BOM](manufacturing/bom-main.csv).

![Floorplan](docs/images/floorplan.svg)

| Path | Contents |
|---|---|
| `hardware/nexus-style-fc.kicad_pro` | Main board: full schematic + placed PCB (not routed) |
| `hardware/header-board/` | Servo-header child board, a separate KiCad project |
| `hardware/library/` | LCSC footprints, symbols and 3D models, plus the project footprints |
| `firmware/RDMS-NEXUS_F7.config` | Upstream Rotorflight target config, used for the pin map (see below) |
| `tools/` | `design.py` (single source of truth) + generators; `build_all.sh` rebuilds everything and runs the checks |
| `manufacturing/` | BOMs with LCSC part numbers |
| `docs/` | Review notes and renders |

The firmware config is copied unchanged from [rotorflight-targets `configs/RDMS-NEXUS_F7.config`](https://github.com/rotorflight/rotorflight-targets/blob/master/configs/RDMS-NEXUS_F7.config) (master, latest commit `b89676f`, 2026-03-02) and stays attributed to its upstream authors. No firmware binary is included. RadioMaster branding is not used on the board.
