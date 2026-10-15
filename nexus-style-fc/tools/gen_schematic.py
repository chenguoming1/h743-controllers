#!/usr/bin/env python3
"""Generate a KiCad schematic from a design module (design.py / design_header.py).

Every symbol pin gets a short wire stub and a net label (or a no-connect flag), so the
connectivity is exactly the netlist in the design module. Symbols are grouped by function.

  python3 tools/gen_schematic.py design  hardware/nexus-style-fc.kicad_sch  nexus-style-fc
  python3 tools/gen_schematic.py design_header  hardware/header-board/nexus-header-board.kicad_sch  nexus-header-board
"""
import importlib
from functools import lru_cache
import math
import os
import sys
import uuid

import sexpr as sx

HERE = os.path.dirname(os.path.abspath(__file__))
STOCK = os.environ.get("KICAD_SYMBOL_DIR", "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols" if sys.platform == "darwin" else "/usr/share/kicad/symbols")
LIBS = {"NexusFC": os.path.normpath(os.path.join(HERE, "..", "hardware", "library", "NexusFC.kicad_sym"))}
NS = uuid.UUID("6f3c2a1e-9b7d-4c55-8a10-2d4e5f6a7b80")
GRID = 1.27
STUB = 2.54
PAGE = ("A1", 841.0, 594.0)
GROUP_TITLES = {
    "MCU": "MCU  STM32F722RET6  (Rotorflight RDMS-NEXUS_F7 pinout)",
    "SENSORS": "SENSORS  ICM-42688-P (SPI1)  DPS368 (I2C1 0x76)  3V3_SENS LDO",
    "FLASH": "BLACKBOX  W25N01GV 128MB (SPI2)",
    "POWER": "POWER  VX TVS | 5V buck + USB priority mux | VSYS -> 3V3 MCU buck | DSM 3V3 buck | ADC sense",
    "USB": "USB-C  (PTC + ESD, Rd 5.1k)",
    "PORTS": "RECEIVER PORTS  A-CRSF UART4 | B UART6 | C UART3 | DSM UART1  + ESD",
    "HEADER": "SERVO HEADER CHILD BOARD JOINT + clamps",
    "LED": "LEDs  (PC14/PC15 sink only, <=3 mA)",
    "CHILD": "SERVO HEADER CHILD BOARD",
}


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def snap(v):
    return round(round(v / GRID) * GRID, 4)


def lib_path(lib):
    return LIBS.get(lib) or os.path.join(STOCK, lib + ".kicad_sym")


@lru_cache(maxsize=1)
def pinned_stock_symbols():
    """Exact stock definitions from the reviewed schematic, independent of host version."""
    path = os.path.normpath(os.path.join(HERE, "..", "hardware", "library", "SchematicStock.kicad_sym"))
    if not os.path.exists(path):
        return {}
    return {sx.text(s[1]): s for s in sx.find(sx.parse(open(path, encoding="utf-8").read()), "symbol")}


def load_symbol(lib_id, use_pinned=False):
    if use_pinned and lib_id in pinned_stock_symbols():
        return pinned_stock_symbols()[lib_id]
    lib, name = lib_id.split(":")
    sym = sx.symbol_from_lib(lib_path(lib), name)
    if sx.find(sym, "extends"):
        raise SystemExit(f"{lib_id} uses extends; not supported")
    emb = list(sym)
    emb[1] = ("s", lib_id)
    return emb


def S(v):
    return ("s", v)


def font(size=1.27):
    return ["effects", ["font", ["size", size, size]]]


def prop(name, value, x, y, hide=False, angle=0):
    p = ["property", S(name), S(value), ["at", x, y, angle]]
    eff = font()
    if hide:
        eff.append(["hide", "yes"])
    p.append(eff)
    return p


def glabel(net, x, y, angle, just, u):
    """Global label, so net names match the PCB exactly (no sheet-path prefix)."""
    return ["global_label", S(net), ["shape", "passive"], ["at", x, y, angle], ["fields_autoplaced", "yes"],
            ["effects", ["font", ["size", 1.27, 1.27]], ["justify", just]], ["uuid", u],
            ["property", S("Intersheetrefs"), S("${INTERSHEET_REFS}"), ["at", x, y, 0],
             ["effects", ["font", ["size", 1.27, 1.27]], ["hide", "yes"]]]]


def label_width(name):
    return len(name) * 1.0 + 3.0


def main(mod_name, out_path, project):
    d = importlib.import_module(mod_name)
    root = uid(project, "root")
    symdefs = {}
    for p in d.PARTS:
        if p["sym"] not in symdefs:
            symdefs[p["sym"]] = load_symbol(p["sym"], use_pinned=mod_name == "design")
    flags = getattr(d, "PWR_FLAGS", [])
    if flags:
        symdefs["power:PWR_FLAG"] = load_symbol("power:PWR_FLAG", use_pinned=mod_name == "design")

    items = []
    texts = []
    _, PW, PH = PAGE
    x0, y0, xmax = 20.0, 30.0, PW - 20.0
    cx, cy, row_h = x0, y0, 0.0
    group = None

    def place_block(width, height):
        nonlocal cx, cy, row_h
        if cx + width > xmax and cx > x0:
            cx, cy, row_h = x0, cy + row_h + 8.0, 0.0
        px, py = cx, cy
        cx += width + 6.0
        row_h = max(row_h, height)
        return px, py

    order = list(dict.fromkeys(p["group"] for p in d.PARTS))
    for g in order:
        # new group always starts a new row with a title
        if cx > x0:
            cx, cy, row_h = x0, cy + row_h + 14.0, 0.0
        texts.append(["text", S(GROUP_TITLES.get(g, g)), ["exclude_from_sim", "no"],
                      ["at", snap(x0), snap(cy - 4.0), 0], ["effects", ["font", ["size", 2.5, 2.5], ["bold", "yes"]],
                                                            ["justify", "left", "bottom"]], ["uuid", uid(project, "title", g)]])
        for p in [q for q in d.PARTS if q["group"] == g]:
            sym = symdefs[p["sym"]]
            pins = sx.symbol_pins(sym)
            extra = set(p["pins"]) - set(pins)
            if extra:
                raise SystemExit(f"{p['ref']}: design pins {sorted(extra)} not on symbol {p['sym']}")
            xa, ya, xb, yb = sx.symbol_bbox(sym)
            lw = max([label_width(n) for n in p["pins"].values() if n] + [2.0])
            left = -xa + STUB + lw
            right = xb + STUB + lw
            width = left + right
            # vertical labels on top / bottom pins stick out of the symbol: reserve room so they clear the row above
            up = max([label_width(p["pins"][n]) for n, v in pins.items() if v[2] == 270 and p["pins"].get(n)] + [0.0])
            down = max([label_width(p["pins"][n]) for n, v in pins.items() if v[2] == 90 and p["pins"].get(n)] + [0.0])
            height = (yb - ya) + 2 * STUB + 6.0 + up + down
            px, py = place_block(width, height)
            sxp, syp = snap(px + left), snap(py + yb + STUB + 3.0 + up)   # symbol origin (y down)
            ref = p["ref"]
            inst = ["symbol", ["lib_id", S(p["sym"])], ["at", sxp, syp, 0], ["unit", 1],
                    ["exclude_from_sim", "no"], ["in_bom", "no" if p["fp"].startswith("TestPoint:") else "yes"],
                    ["on_board", "yes"], ["dnp", "no"], ["uuid", uid(project, "sym", ref)]]
            inst.append(prop("Reference", ref, snap(sxp + xb + 1.27), snap(syp + ya - 1.5)))
            inst.append(prop("Value", p["value"], snap(sxp + xb + 1.27), snap(syp - ya + 1.5)))
            inst.append(prop("Footprint", p["fp"], sxp, syp, hide=True))
            inst.append(prop("Datasheet", "", sxp, syp, hide=True))
            inst.append(prop("LCSC", p["lcsc"], sxp, syp, hide=True))
            if p.get("note"):
                inst.append(prop("Description", p["note"], sxp, syp, hide=True))
            for num in pins:
                inst.append(["pin", S(num), ["uuid", uid(project, "pin", ref, num)]])
            inst.append(["instances", ["project", S(project), ["path", S("/" + root), ["reference", S(ref)], ["unit", 1]]]])
            items.append(inst)
            for num, (px_, py_, ang, length, _name) in pins.items():
                ex, ey = snap(sxp + px_), snap(syp - py_)
                net = p["pins"].get(num, None) if num in p["pins"] else None
                if num not in p["pins"]:
                    raise SystemExit(f"{ref} pin {num} not assigned in design")
                if net is None:
                    items.append(["no_connect", ["at", ex, ey], ["uuid", uid(project, "nc", ref, num)]])
                    continue
                a = math.radians(ang + 180.0)
                dx, dy = round(math.cos(a)), -round(math.sin(a))
                lx, ly = snap(ex + dx * STUB), snap(ey + dy * STUB)
                items.append(["wire", ["pts", ["xy", ex, ey], ["xy", lx, ly]],
                              ["stroke", ["width", 0], ["type", "default"]], ["uuid", uid(project, "w", ref, num)]])
                if dx > 0:
                    langle, just = 0, "left"
                elif dx < 0:
                    langle, just = 180, "right"
                elif dy < 0:
                    langle, just = 90, "left"
                else:
                    langle, just = 270, "right"
                items.append(glabel(net, lx, ly, langle, just, uid(project, "lbl", ref, num)))
    # power flags
    if flags:
        if cx > x0:
            cx, cy, row_h = x0, cy + row_h + 14.0, 0.0
        texts.append(["text", S("POWER FLAGS"), ["exclude_from_sim", "no"], ["at", snap(x0), snap(cy - 4.0), 0],
                      ["effects", ["font", ["size", 2.5, 2.5], ["bold", "yes"]], ["justify", "left", "bottom"]],
                      ["uuid", uid(project, "title", "flags")]])
        for i, net in enumerate(flags):
            ref = f"#FLG{i + 1:02d}"
            px, py = place_block(20.0, 12.0)
            sxp, syp = snap(px + 5.0), snap(py + 6.0)
            inst = ["symbol", ["lib_id", S("power:PWR_FLAG")], ["at", sxp, syp, 0], ["unit", 1],
                    ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"], ["dnp", "no"],
                    ["uuid", uid(project, "sym", ref)],
                    prop("Reference", ref, sxp, snap(syp - 3.0), hide=True),
                    prop("Value", "PWR_FLAG", sxp, snap(syp - 4.0)),
                    prop("Footprint", "", sxp, syp, hide=True), prop("Datasheet", "", sxp, syp, hide=True),
                    ["pin", S("1"), ["uuid", uid(project, "pin", ref, "1")]],
                    ["instances", ["project", S(project), ["path", S("/" + root), ["reference", S(ref)], ["unit", 1]]]]]
            items.append(inst)
            ex, ey = sxp, syp
            items.append(["wire", ["pts", ["xy", ex, ey], ["xy", ex, snap(ey + STUB)]],
                          ["stroke", ["width", 0], ["type", "default"]], ["uuid", uid(project, "w", ref)]])
            items.append(glabel(net, ex, snap(ey + STUB), 270, "right", uid(project, "lbl", ref)))

    sch = ["kicad_sch", ["version", 20250114], ["generator", S("eeschema")], ["generator_version", S("10.0")],
           ["uuid", root], ["paper", S(PAGE[0])],
           ["title_block", ["title", S(getattr(d, "TITLE", project))], ["date", S("2026-10-13")],
            ["rev", S(getattr(d, "REV", "0.2"))],
            ["comment", 1, S("Generated from tools/" + mod_name + ".py - edit the design file, then regenerate")],
            ["comment", 2, S("Rotorflight RDMS-NEXUS_F7 target; LCSC part numbers in the LCSC field")]],
           ["lib_symbols"] + list(symdefs.values())]
    sch += texts + items
    sch.append(["sheet_instances", ["path", S("/"), ["page", S("1")]]])
    sch.append(["embedded_fonts", "no"])
    if mod_name == "design":
        from draft_circuits import arrange
        sch = arrange(sch, d, project)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "w", encoding="utf-8").write(sx.dump(sch) + "\n")
    print("wrote", out_path, f"({len(d.PARTS)} symbols)")


if __name__ == "__main__":
    main(*sys.argv[1:4])
