#!/usr/bin/env python3
"""Build the power-module PCB from design_power.py: outline, stackup, rules, all parts, nets. No routing.

Run through tools/build.sh, or with KiCad's bundled Python after gen_power_schematic.py:
  .../Python.framework/Versions/Current/bin/python3 tools/build_power_module.py

Parts and generators come from the sibling nexus-style-fc project; the footprints, symbols and 3D models this
board uses are copied into hardware/library/, so this project opens on its own.

4-layer JLC04161H-7628-like 1.6 mm: F.Cu parts + signal, In1 GND, In2 GND / power, B.Cu signal.
Rules are JLCPCB's no-surcharge limits, as on the main board: 0.09 mm track / space, one via 0.2 / 0.45 mm.
Fixed parts use the ("xy", ...) positions; ("near", ref, pad, side) parts are auto-placed next to that pad.
Footprints are linked to the schematic symbols and pads take the schematic's net names, so the board matches
"Update PCB from Schematic" exactly.
"""
import json
import math
import os
import re
import shutil

import pcbnew

import design_power as dp      # also puts the nexus-style-fc tools on sys.path
import gen_power_schematic as gps
import sexpr as sx
from pcbutil import Board, courtyard_boxes, uid

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.normpath(os.path.join(HERE, "..", "hardware"))
PROJECT = "nexus-style-fc-power-module"
OUT = os.path.join(OUTDIR, PROJECT + ".kicad_pcb")
SCH = os.path.join(OUTDIR, PROJECT + ".kicad_sch")
NEXUS_HW = os.path.normpath(os.path.join(dp.NEXUS_TOOLS, "..", "hardware"))
NEXUS_LIB = os.path.join(NEXUS_HW, "library")
TEMPLATE_PRO = os.path.join(NEXUS_HW, "header-board", "nexus-header-board.kicad_pro")

OX, OY = 100.0, 100.0
W, L, R = dp.W, dp.L, 1.0
EDGE = 0.3                      # courtyard-to-edge margin for auto-placed parts
GAP = 0.05                      # extra courtyard gap

VIA_DIA, VIA_DRILL = 0.45, 0.2  # the one via: JLC's cheapest multilayer via
CLASSES = (  # name, track, clearance, nets
    ("HighCurrent", 0.5, 0.12, ["VX", "SW_5V", "5V_BUCK", "5V"]),
    ("Power", 0.3, 0.10, ["VBUS", "VSYS", "3V3", "SW_3V3", "3V3_DSM"]),
)
JLC_RULES = {"min_clearance": 0.09, "min_track_width": 0.09, "min_via_diameter": 0.45,
             "min_via_annular_width": 0.125, "min_through_hole_diameter": 0.2, "min_hole_to_hole": 0.25,
             "min_hole_clearance": 0.2, "min_copper_edge_clearance": 0.3, "min_resolved_spokes": 2,
             "min_text_height": 0.5, "min_text_thickness": 0.08}

STACKUP = """    (stackup
      (layer "F.SilkS" (type "Top Silk Screen"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 1" (type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02))
      (layer "In1.Cu" (type "copper") (thickness 0.0152))
      (layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
      (layer "In2.Cu" (type "copper") (thickness 0.0152))
      (layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen"))
      (copper_finish "ENIG")
      (dielectric_constraints no)
    )
"""


def outline(b):
    e = pcbnew.Edge_Cuts
    b.seg(e, (R, 0), (W - R, 0))
    b.arc(e, (W - R, R), (W - R, 0), (W, R))
    b.seg(e, (W, R), (W, L - R))
    b.arc(e, (W - R, L - R), (W, L - R), (W - R, L))
    b.seg(e, (W - R, L), (R, L))
    b.arc(e, (R, L - R), (R, L), (0, L - R))
    b.seg(e, (0, L - R), (0, R))
    b.arc(e, (R, R), (0, R), (R, 0))


def overlaps(box, others):
    x0, y0, x1, y1 = box
    return any(x0 < a1 + GAP and a0 < x1 + GAP and y0 < b1 + GAP and b0 < y1 + GAP for a0, b0, a1, b1 in others)


class Placer:
    """Spiral search for the closest courtyard-free spot next to an anchor pad (see build_floorplan.py)."""

    def __init__(self, b):
        self.b = b
        self.obs = {"F": [], "B": []}

    def add(self, fp):
        for side, layer in (("F", pcbnew.F_CrtYd), ("B", pcbnew.B_CrtYd)):
            self.obs[side] += courtyard_boxes(fp, layer, OX, OY)
        for p in fp.Pads():   # through-hole copper blocks both sides
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                bb = p.GetBoundingBox()
                box = (pcbnew.ToMM(bb.GetX()) - OX - 0.1, pcbnew.ToMM(bb.GetY()) - OY - 0.1,
                       pcbnew.ToMM(bb.GetRight()) - OX + 0.1, pcbnew.ToMM(bb.GetBottom()) - OY + 0.1)
                self.obs["F"].append(box)
                self.obs["B"].append(box)

    def near(self, fp, anchor_xy, side, rmax=12.0):
        layer = pcbnew.F_CrtYd if side == "F" else pcbnew.B_CrtYd
        rel = {}
        for rot in (0, 90):
            self.b.put(fp, 0, 0, rot, side)
            rel[rot] = courtyard_boxes(fp, layer, OX, OY)
            if side == "B":
                fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        ax, ay = anchor_xy
        r = 0.4
        while r < rmax:
            n = max(36, int(2 * math.pi * r / 0.3))
            for k in range(n):
                t = 2 * math.pi * k / n
                x, y = round(ax + r * math.cos(t), 2), round(ay + r * math.sin(t), 2)
                for rot in (0, 90):
                    boxes = [(x + a, y + c, x + d, y + e) for a, c, d, e in rel[rot]]
                    if any(bx0 < EDGE or by0 < EDGE or bx1 > W - EDGE or by1 > L - EDGE
                           for bx0, by0, bx1, by1 in boxes):
                        continue
                    if any(overlaps(bx, self.obs[side]) for bx in boxes):
                        continue
                    self.b.put(fp, x, y, rot, side)
                    self.obs[side] += boxes
                    return True
            r += 0.15
        return False


def setup_rules(b):
    ds = b.board.GetDesignSettings()
    ds.SetBoardThickness(b.mm(1.6))
    ds.m_TrackMinWidth = b.mm(0.09)
    ds.m_MinClearance = b.mm(0.09)
    ds.m_ViasMinSize = b.mm(VIA_DIA)
    ds.m_ViasMinAnnularWidth = b.mm((VIA_DIA - VIA_DRILL) / 2)
    ds.m_MinThroughDrill = b.mm(VIA_DRILL)
    ds.m_HoleToHoleMin = b.mm(0.25)
    ds.m_HoleClearance = b.mm(0.2)
    ds.m_CopperEdgeClearance = b.mm(0.3)
    ds.m_MinSilkTextHeight = b.mm(0.5)


def write_project(names):
    """KiCad 10 keeps net classes and rule minimums in the .kicad_pro."""
    d = json.load(open(TEMPLATE_PRO))
    d["meta"]["filename"] = PROJECT + ".kicad_pro"
    d["schematic"]["top_level_sheets"] = [{"filename": PROJECT + ".kicad_sch", "name": PROJECT,
                                          "uuid": "00000000-0000-0000-0000-000000000000"}]
    ns = d["net_settings"]
    base = dict(ns["classes"][0])
    out = []
    for i, (name, width, clr) in enumerate([("Default", 0.12, 0.10)] + [c[:3] for c in CLASSES]):
        c = dict(base)
        c.update(name=name, track_width=width, clearance=clr, via_diameter=VIA_DIA, via_drill=VIA_DRILL,
                 priority=2147483647 if name == "Default" else i - 1)
        out.append(c)
    ns["classes"] = out
    ns["netclass_patterns"] = [{"netclass": c[0], "pattern": names[n]} for c in CLASSES for n in c[3]]
    d["board"]["design_settings"]["rules"].update(JLC_RULES)
    tv = d["board"]["design_settings"].get("track_widths")
    if tv is not None:
        d["board"]["design_settings"]["track_widths"] = [0.0, 0.12, 0.3, 0.5]
        d["board"]["design_settings"]["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0},
                                                           {"diameter": VIA_DIA, "drill": VIA_DRILL}]
    json.dump(d, open(os.path.join(OUTDIR, PROJECT + ".kicad_pro"), "w"), indent=2)


def write_stackup(path):
    txt = open(path).read()
    i = txt.find("(stackup")
    if i >= 0:                                     # drop the default stackup KiCad wrote
        depth, j = 0, i
        while True:
            depth += (txt[j] == "(") - (txt[j] == ")")
            j += 1
            if depth == 0:
                break
        txt = txt[:txt.rfind("\n", 0, i) + 1] + txt[j:].lstrip("\n")
    txt = txt.replace("(setup\n", "(setup\n" + STACKUP, 1)
    open(path, "w").write(txt)


def export_library():
    """Copy the NexusFC footprints, symbols and 3D models this board uses from nexus-style-fc."""
    lib = os.path.join(OUTDIR, "library")
    shutil.rmtree(lib, ignore_errors=True)
    os.makedirs(os.path.join(lib, "NexusFC.pretty"))
    os.makedirs(os.path.join(lib, "NexusFC.3dshapes"))
    fps = sorted({p["fp"].split(":")[1] for p in dp.PARTS if p["fp"].startswith("NexusFC:")})
    for name in fps:
        src = os.path.join(NEXUS_LIB, "NexusFC.pretty", name + ".kicad_mod")
        shutil.copy(src, os.path.join(lib, "NexusFC.pretty"))
        for m in re.findall(r'\(model "\$\{KIPRJMOD\}/library/NexusFC\.3dshapes/([^"]+)"', open(src).read()):
            for ext in (os.path.splitext(m)[0] + e for e in (".step", ".wrl")):
                if os.path.exists(os.path.join(NEXUS_LIB, "NexusFC.3dshapes", ext)):
                    shutil.copy(os.path.join(NEXUS_LIB, "NexusFC.3dshapes", ext), os.path.join(lib, "NexusFC.3dshapes"))
    syms = {p["sym"].split(":")[1] for p in dp.PARTS if p["sym"].startswith("NexusFC:")}
    full = sx.parse(open(os.path.join(NEXUS_LIB, "NexusFC.kicad_sym"), encoding="utf-8").read())
    keep = [e for e in full if not (isinstance(e, list) and e and e[0] == "symbol") or sx.text(e[1]) in syms]
    open(os.path.join(lib, "NexusFC.kicad_sym"), "w").write(sx.dump(keep) + "\n")


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    b = Board(OX, OY, 4)
    setup_rules(b)
    outline(b)

    # net names exactly as the schematic has them (as "Update PCB from Schematic" would set them): power-symbol
    # rails keep their names, local-label nets get KiCad's "/" prefix, unused pins their "unconnected-(...)" net
    sch_nets = gps.export_netlist(SCH)
    names = gps.check_netlist(sch_nets)
    pin_net = {rp: n for n, rps in sch_nets.items() for rp in rps}

    def footprint(p):
        q = dict(p, pins={pad: pin_net[(p["ref"], pad)] for pad in p["pins"]})
        return b.footprint(q, PROJECT, root)

    root = uid(PROJECT, "root")
    placer = Placer(b)
    fps = {}
    for p in dp.PARTS:                            # fixed parts first
        if p["place"][0] == "xy":
            fp = footprint(p)
            _, x, y, rot, side = p["place"]
            b.put(fp, x, y, rot, side)
            fps[p["ref"]] = fp
            placer.add(fp)
    # pin names next to the headers on the silkscreen; they also keep the auto-placed parts out of that band
    short = {"3V3_DSM": "DSM", "VX_SENSE": "VX_S", "5V_SENSE": "5V_S"}
    for ref, dy in (("J1", 1.9), ("J2", -1.9)):
        part = next(p for p in dp.PARTS if p["ref"] == ref)
        for pad in fps[ref].Pads():
            pos = pad.GetPosition()
            net = part["pins"][pad.GetNumber()]
            name = short.get(net, net)
            x, y = pcbnew.ToMM(pos.x) - OX, pcbnew.ToMM(pos.y) - OY + dy
            b.text(pcbnew.F_SilkS, x, y, name, 0.6)
            hw = len(name) * 0.3 + 0.15
            placer.obs["F"].append((x - hw, y - 0.5, x + hw, y + 0.5))
    failed = []
    near = [p for p in dp.PARTS if p["place"][0] == "near"]
    for p in sorted(near, key=lambda p: p["ref"][0] != "C"):   # every passive next to its pin, caps first
        _, aref, apad, side = p["place"]
        pad = [q for q in fps[aref].Pads() if q.GetNumber() == apad][0]
        pos = pad.GetPosition()
        fp = footprint(p)
        fps[p["ref"]] = fp
        if not placer.near(fp, (pcbnew.ToMM(pos.x) - OX, pcbnew.ToMM(pos.y) - OY), side):
            failed.append(p["ref"])
            b.put(fp, W + 3, 2 + 2 * len(failed), 0, side)   # parked off-board for manual placement

    b.text(pcbnew.F_Fab, W / 2, L + 1.5, f"Nexus-style FC power module {W} x {L} mm, rev {dp.REV}", 0.8)
    b.save(OUT)
    write_stackup(OUT)
    write_project(names)
    export_library()
    open(os.path.join(OUTDIR, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (version 7)\n  (lib (name "NexusFC") (type "KiCad") '
        '(uri "${KIPRJMOD}/library/NexusFC.pretty") (options "") (descr "parts copied from nexus-style-fc"))\n)\n')
    open(os.path.join(OUTDIR, "sym-lib-table"), "w").write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "NexusFC") (type "KiCad") '
        '(uri "${KIPRJMOD}/library/NexusFC.kicad_sym") (options "") (descr "parts copied from nexus-style-fc"))\n)\n')
    print("wrote", OUT, f"({W} x {L} mm, {len(dp.PARTS)} parts, {len(b.nets)} nets)")
    if failed:
        print("could not auto-place (parked off-board):", ", ".join(failed))


if __name__ == "__main__":
    main()
