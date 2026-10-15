#!/usr/bin/env python3
"""Draw the power-module schematic: real wires inside each block, power symbols for the rails, local labels on
the internal nodes, and global labels only on the three signals that leave through J2.

  python3 tools/gen_power_schematic.py            (writes hardware/nexus-style-fc-power-module.kicad_sch)

Parts and nets come from design_power.py; the layout below only says where things go. check_netlist() exports
the KiCad netlist of the result and fails unless its connectivity is exactly the design's.
"""
import math
import os
import subprocess
import sys
import tempfile

import design_power as dp      # also puts the nexus-style-fc tools on sys.path
import gen_schematic as gs
import sexpr as sx

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = "nexus-style-fc-power-module"
OUT = os.path.normpath(os.path.join(HERE, "..", "hardware", PROJECT + ".kicad_sch"))
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
PARTS = {p["ref"]: p for p in dp.PARTS}
S, prop, uid = gs.S, gs.prop, gs.uid


def key(pt):
    return (round(pt[0], 3), round(pt[1], 3))


class Sheet:
    def __init__(self):
        self.symdefs = {}
        self.items = []
        self.wires = []          # [(a, b)]
        self.pins = {}           # ref -> {num: (x, y)}
        self.points = []         # every connection point that is not a wire end (pins, labels)
        self.npwr = 0
        self.root = uid(PROJECT, "root")

    def lib(self, lib_id):
        if lib_id not in self.symdefs:
            self.symdefs[lib_id] = gs.load_symbol(lib_id)
        return self.symdefs[lib_id]

    # -- symbols
    def _inst(self, lib_id, ref, value, x, y, rot, mirror, fields, uuid, in_bom=True, extra=()):
        if rot in (90, 270):          # field angles are relative to the symbol: keep the text horizontal
            for fld in fields:
                fld[3][3] = 90
        sym = self.lib(lib_id)
        pins = sx.symbol_pins(sym)
        pos = {}
        for num, (px, py, *_rest) in pins.items():
            if mirror:
                px = -px
            r = math.radians(rot)
            pos[num] = (round(x + px * math.cos(r) - py * math.sin(r), 3),
                        round(y - (px * math.sin(r) + py * math.cos(r)), 3))
        inst = ["symbol", ["lib_id", S(lib_id)], ["at", x, y, rot]]
        if mirror:
            inst.append(["mirror", "y"])
        inst += [["unit", 1], ["exclude_from_sim", "no"], ["in_bom", "yes" if in_bom else "no"],
                 ["on_board", "yes" if in_bom else "no"], ["dnp", "no"], ["uuid", uuid]]
        inst += fields
        inst += list(extra)
        for num in pins:
            inst.append(["pin", S(num), ["uuid", uid(PROJECT, "pin", ref, num)]])
        inst.append(["instances", ["project", S(PROJECT), ["path", S("/" + self.root), ["reference", S(ref)], ["unit", 1]]]])
        self.items.append(inst)
        return pos

    @staticmethod
    def _field(name, value, x, y, just=None, hide=False, angle=0):
        p = ["property", S(name), S(value), ["at", round(x, 3), round(y, 3), angle]]
        eff = ["effects", ["font", ["size", 1.27, 1.27]]]
        if just:
            eff.append(["justify", just])
        if hide:
            eff.append(["hide", "yes"])
        p.append(eff)
        return p

    def part(self, ref, x, y, rot=0, mirror=False, text="right"):
        """Place a design part. text: where Reference / Value go (right, left, above, ic)."""
        p = PARTS[ref]
        sym = self.lib(p["sym"])
        xa, ya, xb, yb = sx.symbol_bbox(sym)
        f = self._field
        if text == "right":          # vertical two-pin part
            fl = [f("Reference", ref, x + 2.54, y - 1.27, "left"), f("Value", p["value"], x + 2.54, y + 1.27, "left")]
        elif text == "left":
            fl = [f("Reference", ref, x - 2.54, y - 1.27, "right"), f("Value", p["value"], x - 2.54, y + 1.27, "right")]
        elif text == "top":          # horizontal two-pin part, both fields above
            fl = [f("Reference", ref, x, y - 5.08), f("Value", p["value"], x, y - 2.54)]
        elif text == "above":        # horizontal two-pin part
            fl = [f("Reference", ref, x, y - 3.81), f("Value", p["value"], x, y + 3.81 if p["sym"] != "NexusFC:SMD0805P050TF" else y - 6.35)]
        else:                        # IC: reference centred over the body, value centred under it
            fl = [f("Reference", ref, x, y - yb - 1.27), f("Value", p["value"], x, y - ya + 2.54)]
        fl += [f("Footprint", p["fp"], x, y, hide=True), f("Datasheet", "", x, y, hide=True),
               f("LCSC", p["lcsc"], x, y, hide=True)]
        if p.get("note"):
            fl.append(f("Description", p["note"], x, y, hide=True))
        pos = self._inst(p["sym"], ref, p["value"], x, y, rot, mirror, fl, uid(PROJECT, "sym", ref))
        self.pins[ref] = pos
        for num, pt in pos.items():
            if p["pins"].get(num) is None:
                self.items.append(["no_connect", ["at", *pt], ["uuid", uid(PROJECT, "nc", ref, num)]])
            else:
                self.points.append(key(pt))
        return pos

    def power(self, net, x, y, d="up"):
        """Rail symbol whose pin is at (x, y); d is where its body points."""
        self.npwr += 1
        ref = f"#PWR{self.npwr:02d}"
        gnd = net == "GND"
        lib_id = "power:GND" if gnd else "power:VCC"
        rot = {"up": 0, "down": 0, "left": 90, "right": 270}[d] if not gnd else {"down": 0, "right": 90, "left": 270, "up": 180}[d]
        off = 3.81
        tx, ty, just = {"up": (x, y - off, None), "down": (x, y + off, None),
                        "left": (x - off, y, "right"), "right": (x + off, y, "left")}[d]
        if rot == 90 and just:        # KiCad mirrors the field justification of a symbol rotated by 90
            just = {"left": "right", "right": "left"}[just]
        fl = [self._field("Reference", ref, x, y, hide=True), self._field("Value", net, tx, ty, just),
              self._field("Footprint", "", x, y, hide=True), self._field("Datasheet", "", x, y, hide=True)]
        self._inst(lib_id, ref, net, x, y, rot, False, fl, uid(PROJECT, "pwr", ref), in_bom=False)
        self.points.append(key((x, y)))

    def flag(self, x, y, d="up"):
        self.npwr += 1
        ref = f"#FLG{self.npwr:02d}"
        ty = y - 3.81 if d == "up" else y + 3.81
        fl = [self._field("Reference", ref, x, y, hide=True), self._field("Value", "PWR_FLAG", x, ty),
              self._field("Footprint", "", x, y, hide=True), self._field("Datasheet", "", x, y, hide=True)]
        self._inst("power:PWR_FLAG", ref, "PWR_FLAG", x, y, 0 if d == "up" else 180, False, fl,
                   uid(PROJECT, "flg", ref), in_bom=False)
        self.points.append(key((x, y)))

    # -- connections
    def pin(self, ref, num):
        return self.pins[ref][num]

    def wire(self, *pts):
        pts = [key(self.pin(*p) if isinstance(p[0], str) else p) for p in pts]
        for a, b in zip(pts, pts[1:]):
            if a[0] != b[0] and a[1] != b[1]:
                raise SystemExit(f"diagonal wire {a} -> {b}")
            self.wires.append((a, b))
        return pts[-1]

    def label(self, name, x, y, d="right", glob=False):
        """Label whose anchor is at (x, y); local labels sit on a wire, global ones point d."""
        angle = {"right": 0, "up": 90, "left": 180, "down": 270}[d]
        just = "left" if d in ("right", "up") else "right"
        u = uid(PROJECT, "label", name, x, y)
        if glob:
            self.items.append(gs.glabel(name, x, y, angle, just, u))
        else:
            self.items.append(["label", S(name), ["at", x, y, angle], ["fields_autoplaced", "yes"],
                               ["effects", ["font", ["size", 1.27, 1.27]], ["justify", just, "bottom"]], ["uuid", u]])
        self.points.append(key((x, y)))

    def text(self, t, x, y, size=1.27, bold=False):
        font = ["font", ["size", size, size]] + ([["bold", "yes"]] if bold else [])
        self.items.append(["text", S(t), ["exclude_from_sim", "no"], ["at", x, y, 0],
                           ["effects", font, ["justify", "left", "bottom"]], ["uuid", uid(PROJECT, "text", t)]])

    def box(self, title, x0, y0, x1, y1):
        self.items.append(["rectangle", ["start", x0, y0], ["end", x1, y1],
                           ["stroke", ["width", 0.2], ["type", "dash"]], ["fill", ["type", "none"]],
                           ["uuid", uid(PROJECT, "box", title)]])
        self.text(title, x0 + 1.27, y0 + 3.81, 1.8, bold=True)

    # -- output
    def _segments(self):
        """Split every wire at each connection point inside it, so all joins are end-to-end."""
        stops = {key(p) for p in self.points} | {p for w in self.wires for p in w}
        out = []
        for a, b in self.wires:
            on = [s for s in stops if s not in (a, b) and min(a[0], b[0]) <= s[0] <= max(a[0], b[0])
                  and min(a[1], b[1]) <= s[1] <= max(a[1], b[1]) and (a[0] == b[0] == s[0] or a[1] == b[1] == s[1])]
            pts = sorted([a, b] + on, key=lambda s: (s[0] - a[0]) ** 2 + (s[1] - a[1]) ** 2)
            out += [(p, q) for p, q in zip(pts, pts[1:]) if p != q]
        return out

    def write(self, path):
        segs = self._segments()
        ends = {}
        for a, b in segs:
            ends[a] = ends.get(a, 0) + 1
            ends[b] = ends.get(b, 0) + 1
        pts = {key(p) for p in self.points}
        for i, (a, b) in enumerate(segs):
            self.items.append(["wire", ["pts", ["xy", *a], ["xy", *b]], ["stroke", ["width", 0], ["type", "default"]],
                               ["uuid", uid(PROJECT, "wire", a, b)]])
        for p, n in sorted(ends.items()):
            if n >= 3 or (n >= 2 and p in pts):
                self.items.append(["junction", ["at", *p], ["diameter", 0], ["color", 0, 0, 0, 0],
                                   ["uuid", uid(PROJECT, "junction", p)]])
        sch = ["kicad_sch", ["version", 20250114], ["generator", S("eeschema")], ["generator_version", S("10.0")],
               ["uuid", self.root], ["paper", S("A3")],
               ["title_block", ["title", S(dp.TITLE)], ["date", S("2026-10-15")], ["rev", S(dp.REV)],
                ["comment", 1, S("Generated: edit tools/gen_power_schematic.py, then run tools/build.sh")],
                ["comment", 2, S("Parts from nexus-style-fc/tools/design.py (POWER block)")]],
               ["lib_symbols"] + list(self.symdefs.values())]
        sch += self.items
        sch.append(["sheet_instances", ["path", S("/"), ["page", S("1")]]])
        sch.append(["embedded_fonts", "no"])
        open(path, "w", encoding="utf-8").write(sx.dump(sch) + "\n")


def draw():
    s = Sheet()
    G = "GND"

    # ---------------------------------------------------------------- input: J1, VX TVS, power flags
    s.box("INPUT  J1", 15.24, 40.64, 83.82, 81.28)
    s.part("J1", 30.48, 55.88, mirror=True, text="ic")
    for num, net in (("1", "VX"), ("2", G), ("3", "VBUS"), ("4", G)):
        x, y = s.pin("J1", num)
        s.wire((x, y), (x + 7.62, y))
        s.power(net, x + 7.62, y, "right")
    s.wire((58.42, 50.8), (73.66, 50.8))
    s.power("VX", 58.42, 50.8)
    s.flag(73.66, 50.8)
    s.part("D4", 63.5, 55.88, rot=270, text="left")    # K on the VX line, A to GND
    s.wire(s.pin("D4", "2"), (63.5, 63.5), (73.66, 63.5))
    s.power(G, 63.5, 63.5, "down")
    s.flag(73.66, 63.5, "down")
    s.wire((58.42, 73.66), (73.66, 73.66))
    s.power("VBUS", 58.42, 73.66)
    s.flag(73.66, 73.66, "down")

    # ---------------------------------------------------------------- 5 V buck
    s.box(dp.GROUP_TITLES["BUCK5"], 88.9, 40.64, 210.82, 106.68)
    u = s.part("U5", 139.7, 78.74, text="ic")
    s.wire((96.52, 57.15), (119.38, 57.15), (119.38, u["13"][1]))
    s.power("VX", 96.52, 57.15)
    for n in ("11", "12", "10", "13"):                 # PVIN, PVIN, AVIN, EN all on VX
        s.wire(u[n], (119.38, u[n][1]))
    for ref, x in (("C21", 101.6), ("C22", 111.76)):
        s.part(ref, x, 60.96)
        s.power(G, x, 64.77, "down")
    s.part("C23", 114.3, 81.28)
    s.wire(u["9"], (114.3, u["9"][1]))
    s.label("SS_5V", 115.57, u["9"][1])
    s.power(G, 114.3, 85.09, "down")
    s.wire(u["8"], (119.38, u["8"][1]), (119.38, 97.79))
    s.wire(u["7"], (119.38, u["7"][1]))
    s.power(G, 119.38, 97.79, "down")
    for n in ("1", "2", "3"):                          # SW
        s.wire(u[n], (160.02, u[n][1]))
    s.wire((160.02, u["3"][1]), (160.02, u["1"][1]))
    s.part("L1", 170.18, 62.23, rot=90, text="above")
    s.wire((160.02, u["1"][1]), s.pin("L1", "1"))
    s.label("SW_5V", 160.02, 62.23)
    s.wire(s.pin("L1", "2"), (199.39, 62.23))         # 5V_BUCK node
    s.label("5V_BUCK", 199.39, 62.23)
    s.wire(u["14"], (176.53, u["14"][1]), (176.53, 62.23))   # VOS senses the output
    s.part("C24", 180.34, 66.04)
    s.power(G, 180.34, 69.85, "down")
    s.part("R11", 194.31, 66.04)
    s.part("R12", 194.31, 77.47)
    s.wire(s.pin("R11", "2"), s.pin("R12", "1"))
    s.power(G, 194.31, 81.28, "down")
    s.wire(u["5"], (189.23, u["5"][1]), (189.23, 71.12), (194.31, 71.12))
    s.label("FB_5V", 163.83, u["5"][1])
    for n in ("17", "6", "15", "16"):                  # EP, AGND, PGND
        s.wire(u[n], (160.02, u[n][1]))
    s.wire((160.02, u["17"][1]), (160.02, 97.79))
    s.power(G, 160.02, 97.79, "down")
    s.text("FSW = GND: 2.5 MHz,  DEF = GND", 93.98, 104.14)
    s.text("Vout = 0.8 V x (1 + 120k / 22k) = 5.16 V", 166.37, 104.14)

    # ---------------------------------------------------------------- 5 V priority mux
    s.box(dp.GROUP_TITLES["MUX"], 218.44, 40.64, 340.36, 106.68)
    m = s.part("U9", 279.4, 76.2, text="ic")
    s.wire(m["1"], (262.89, m["1"][1]))
    s.power(G, 262.89, m["1"][1], "left")
    s.wire(m["2"], (262.89, m["2"][1]))
    s.power("5V", 262.89, m["2"][1], "left")
    s.wire(m["3"], (233.68, m["3"][1]))               # VIN1 = buck
    s.label("5V_BUCK", 233.68, m["3"][1])
    s.part("R13", 243.84, 81.28, text="left")
    s.part("R14", 243.84, 91.44, text="left")
    s.wire(s.pin("R13", "2"), s.pin("R14", "1"))
    s.wire(m["4"], (254.0, m["4"][1]), (254.0, 87.63), (243.84, 87.63))
    s.label("PR1", 255.27, m["4"][1])
    s.power(G, 243.84, 95.25, "down")
    s.wire(m["7"], (297.18, m["7"][1]), (297.18, 63.5), (325.12, 63.5))     # VOUT -> 5V bus
    s.power("5V", 304.8, 63.5)
    s.flag(325.12, 63.5)
    s.part("C26", 314.96, 67.31)
    s.power(G, 314.96, 71.12, "down")
    s.wire(m["6"], (309.88, m["6"][1]))               # VIN2 = USB
    s.power("VBUS", 302.26, m["6"][1])
    s.part("C25", 309.88, 81.28)
    s.power(G, 309.88, 85.09, "down")
    s.wire(m["5"], (294.64, m["5"][1]))               # MODE high: VIN1 has priority
    s.label("5V_BUCK", 294.64, m["5"][1])
    s.text("switches to USB below 1.0 V x (100k + 27k) / 27k = 4.7 V", 220.98, 104.14)

    # ---------------------------------------------------------------- output connector
    s.box("OUTPUT  J2", 345.44, 40.64, 405.13, 106.68)
    s.part("J2", 396.24, 73.66, text="right")
    for num, net in (("1", "5V"), ("2", G), ("3", "VSYS"), ("4", "3V3"), ("5", "3V3_DSM"), ("6", G),
                     ("7", "VX_SENSE"), ("8", "5V_SENSE")):
        x, y = s.pin("J2", num)
        s.wire((x, y), (x - 7.62, y))
        if num in ("5", "7", "8"):
            s.label(net, x - 7.62, y, "left", glob=True)
        else:
            s.power(net, x - 7.62, y, "left")

    # ---------------------------------------------------------------- VSYS OR + 3V3 buck
    s.box(dp.GROUP_TITLES["BUCK3"].split("  +")[0], 15.24, 132.08, 190.5, 190.5)
    s.part("D5", 40.64, 156.21, rot=180, text="above")
    s.part("D6", 40.64, 166.37, rot=180, text="above")
    s.wire((30.48, 156.21), s.pin("D5", "2"))
    s.power("VX", 30.48, 156.21)
    s.wire((30.48, 166.37), s.pin("D6", "2"))
    s.power("VBUS", 30.48, 166.37)
    s.wire(s.pin("D5", "1"), (50.8, 156.21), (50.8, 166.37))
    k = s.part("U14", 114.3, 165.1, mirror=True, text="ic")
    s.wire(s.pin("D6", "1"), k["6"])                  # VSYS -> VIN
    s.power("VSYS", 55.88, 166.37)
    s.flag(63.5, 166.37, "down")
    s.part("C27", 71.12, 170.18)
    s.power(G, 71.12, 173.99, "down")
    s.wire(k["7"], (88.9, k["7"][1]), (88.9, k["6"][1]))   # EN tied to VIN
    s.part("R15", 83.82, k["8"][1], rot=270, text="top")        # pin 1 on S-CONF, pin 2 to GND
    s.wire(s.pin("R15", "1"), k["8"])
    s.label("SCONF", 87.63, k["8"][1])
    s.wire(s.pin("R15", "2"), (76.2, k["8"][1]))
    s.power(G, 76.2, k["8"][1], "left")
    s.wire(k["5"], (91.44, k["5"][1]), (91.44, 176.53))
    s.power(G, 91.44, 176.53, "down")
    s.part("L2", 147.32, k["4"][1], rot=90, text="above")
    s.wire(k["4"], s.pin("L2", "1"))
    s.label("SW_3V3", 135.89, k["4"][1])
    s.wire(s.pin("L2", "2"), (177.8, k["4"][1]))
    s.wire(k["3"], (137.16, k["3"][1]), (137.16, 156.21), (157.48, 156.21), (157.48, k["4"][1]))   # VOS
    s.part("C28", 162.56, 172.72)
    s.power(G, 162.56, 176.53, "down")
    s.power("3V3", 167.64, k["4"][1])
    s.flag(177.8, k["4"][1], "down")
    s.text("S-CONF 27.4k = setting 9: VSET mode, FB/VSET open = 3.3 V, auto PFM", 20.32, 187.96)

    # ---------------------------------------------------------------- DSM port fuse
    s.box("DSM 3V3 PORT FUSE", 200.66, 132.08, 279.4, 165.1)
    s.part("F2", 233.68, 149.86, text="above")
    s.wire((215.9, s.pin("F2", "1")[1]), s.pin("F2", "1"))
    s.power("3V3", 215.9, s.pin("F2", "1")[1])
    s.wire(s.pin("F2", "2"), (254.0, s.pin("F2", "2")[1]))
    s.label("3V3_DSM", 254.0, s.pin("F2", "2")[1], "right", glob=True)

    # ---------------------------------------------------------------- ADC sense dividers
    s.box(dp.GROUP_TITLES["SENSE"], 200.66, 172.72, 340.36, 236.22)
    for top, r1, r2, c, x, net, note in (("VX", "R16", "R17", "C29", 210.82, "VX_SENSE", "-> MCU PC0"),
                                         ("5V", "R18", "R19", "C30", 266.7, "5V_SENSE", "-> MCU PC1")):
        s.power(top, x, 190.5)
        s.part(r1, x, 198.12)
        s.wire((x, 190.5), s.pin(r1, "1"))
        s.part(r2, x, 214.63)
        s.wire(s.pin(r1, "2"), s.pin(r2, "1"))
        s.power(G, x, 218.44, "down")
        s.part(c, x + 12.7, 214.63)
        s.wire((x, 205.74), (x + 12.7, 205.74), s.pin(c, "1"))
        s.power(G, x + 12.7, 218.44, "down")
        s.wire((x + 12.7, 205.74), (x + 22.86, 205.74))
        s.label(net, x + 22.86, 205.74, "right", glob=True)
        s.text(note, x + 22.86, 201.93)
    return s


def export_netlist(path):
    """{net name: {(ref, pin)}} of a schematic, from kicad-cli's s-expression netlist (power symbols left out)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "power.net")
        subprocess.run([KICAD_CLI, "sch", "export", "netlist", "-o", out, path], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return netlist(out)


def check_netlist(sch):
    """Fail unless the schematic's nets are exactly design_power's (same pin sets, NC pins left alone).
    Returns {design net name: schematic net name}."""
    want = {}
    for p in dp.PARTS:
        for pad, net in p["pins"].items():
            if net:
                want.setdefault(net, set()).add((p["ref"], pad))
    got = {frozenset(v): k for k, v in sch.items() if len(v) > 1}
    bad = [n for n, pins in want.items() if frozenset(pins) not in got]
    extra = [k for k, v in sch.items() if len(v) > 1 and frozenset(v) not in {frozenset(x) for x in want.values()}]
    if bad or extra:
        for n in bad:
            print("design net not matched:", n, sorted(want[n]))
        for n in extra:
            print("schematic net not in design:", n, sorted(sch[n]))
        raise SystemExit("schematic connectivity differs from design_power.py")
    return {net: sch_name for net, pins in want.items() for sch_name in [got[frozenset(pins)]]}


def netlist(path):
    """{net name: {(ref, pin)}} from a KiCad s-expression netlist, power symbols left out."""
    tree = sx.parse(open(path, encoding="utf-8").read())
    nets = {}
    for n in sx.walk(tree, "net"):
        name = sx.text(sx.find(n, "name")[0][1])
        nodes = {(sx.text(sx.find(x, "ref")[0][1]), sx.text(sx.find(x, "pin")[0][1])) for x in sx.find(n, "node")}
        nodes = {x for x in nodes if not x[0].startswith("#")}
        if nodes:
            nets[name] = nodes
    return nets


def main():
    s = draw()
    s.write(OUT)
    names = check_netlist(export_netlist(OUT))
    renamed = {k: v for k, v in names.items() if k != v}
    print("wrote", OUT, f"({len(PARTS)} parts, {len(names)} nets match design_power.py)")
    if renamed:
        print("  local-label nets:", ", ".join(f"{k} -> {v}" for k, v in sorted(renamed.items())))


if __name__ == "__main__":
    main()
