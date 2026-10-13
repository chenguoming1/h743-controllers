#!/usr/bin/env python3
"""Build the Nexus-style main board PCB from design.py: outline, all parts, nets.

Run with KiCad's bundled Python (after make_footprints.py, gen_schematic.py, build_header_board.py):
  .../Python.framework/Versions/Current/bin/python3 tools/build_floorplan.py

Fixed parts use the ("xy", ...) positions in design.py; every ("near", ref, pad, side) part is
auto-placed as close as possible to that pad without courtyard overlaps. Nets come from design.py
and footprints are linked to the generated schematic symbols, so KiCad's "Update PCB from
Schematic" works afterwards. No routing yet.
"""
import math
import os

import pcbnew

import design
import gen_schematic as gs
import make_footprints as mf
import sexpr as sx
from pcbutil import Board, courtyard_boxes, uid

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, "..", "hardware"))
PROJECT = "nexus-style-fc"
OUT = os.path.join(HW, PROJECT + ".kicad_pcb")

CASE_W, CASE_L = 25.4, 41.3     # RadioMaster Nexus outer case
CASE_WALL_END = 1.3             # case wall at the USB end
PIN_OUT = 6.0 + 2.5             # straight header: 6 mm pins above a 2.5 mm body
OVERHANG = PIN_OUT - mf.OUTER_Y  # pin tips beyond the main-board header edge
OX, OY = 100.0, 100.0
W = mf.CHILD_W
L = round(CASE_L - CASE_WALL_END - OVERHANG, 2)   # 32.3 mm
R_HDR, R_USB = 0.5, 1.0
EDGE = 0.25                     # courtyard-to-edge margin for auto-placed parts
GAP = 0.05                      # extra courtyard gap


def outline(b):
    e, a, c = pcbnew.Edge_Cuts, R_HDR, R_USB
    b.seg(e, (a, 0), (W - a, 0))
    b.arc(e, (W - a, a), (W - a, 0), (W, a))
    b.seg(e, (W, a), (W, L - c))
    b.arc(e, (W - c, L - c), (W, L - c), (W - c, L))
    b.seg(e, (W - c, L), (c, L))
    b.arc(e, (c, L - c), (c, L), (0, L - c))
    b.seg(e, (0, L - c), (0, a))
    b.arc(e, (a, a), (0, a), (a, 0))


def overlaps(box, others):
    x0, y0, x1, y1 = box
    for a0, b0, a1, b1 in others:
        if x0 < a1 + GAP and a0 < x1 + GAP and y0 < b1 + GAP and b0 < y1 + GAP:
            return True
    return False


class Placer:
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
            if side == "B":   # flip back to F before the next rotation trial
                fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        ax, ay = anchor_xy
        r = 0.4
        while r < rmax:
            n = max(36, int(2 * math.pi * r / 0.3))   # ~0.3 mm steps along the arc
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


def main():
    b = Board(OX, OY, 4)
    ds = b.board.GetDesignSettings()
    ds.SetBoardThickness(b.mm(1.6))
    ds.m_TrackMinWidth = b.mm(0.1)          # JLCPCB 4-layer capability
    ds.m_MinClearance = b.mm(0.1)
    ds.m_ViasMinSize = b.mm(0.4)
    ds.m_MinThroughDrill = b.mm(0.2)
    ds.m_CopperEdgeClearance = b.mm(0.3)
    ds.m_HoleClearance = b.mm(0.2)
    ds.m_MinSilkTextHeight = b.mm(0.5)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(b.mm(0.15))
    nc.SetTrackWidth(b.mm(0.15))
    nc.SetViaDiameter(b.mm(0.45))
    nc.SetViaDrill(b.mm(0.25))
    outline(b)

    cx0 = (W - CASE_W) / 2
    b.rect(pcbnew.Dwgs_User, cx0, -OVERHANG, cx0 + CASE_W, -OVERHANG + CASE_L, 0.12)
    b.text(pcbnew.Dwgs_User, W / 2, -OVERHANG + CASE_L + 1.4,
           f"Nexus case envelope 41.3 x 25.4 mm (main PCB {W} x {L})", 0.7)
    b.text(pcbnew.Dwgs_User, W / 2, -OVERHANG - 1.2, "servo plugs enter here", 0.7)

    root = uid(PROJECT, "root")
    names = {}
    for p in design.PARTS:
        if p["sym"] not in names:
            lib, name = p["sym"].split(":")
            sym = sx.symbol_from_lib(gs.lib_path(lib), name)
            names[p["sym"]] = {k: v[4] for k, v in sx.symbol_pins(sym).items()}
    placer = Placer(b)
    fps = {}
    for p in design.PARTS:                        # fixed parts first
        if p["place"][0] == "xy":
            fp = b.footprint(p, PROJECT, root, names[p["sym"]])
            _, x, y, rot, side = p["place"]
            if p["ref"] != "J1":                  # J1's origin is the board corner
                y += mf.DESIGN_SHIFT
            b.put(fp, x, y, rot, side)
            fps[p["ref"]] = fp
            placer.add(fp)
    failed, moved, retry = [], [], []
    todo = [p for p in design.PARTS if p["place"][0] == "near"]
    ordered = []
    while todo:                                   # anchors must be placed before their dependants
        ready = [p for p in todo if p["place"][1] in fps or p["place"][1] in {q["ref"] for q in ordered}]
        if not ready:
            raise SystemExit("unresolvable anchors: " + ", ".join(p["ref"] for p in todo))
        ordered += ready
        todo = [p for p in todo if p not in ready]
    for p in ordered:                             # then everything else next to its anchor pad
        _, aref, apad, side = p["place"]
        pad = [q for q in fps[aref].Pads() if q.GetNumber() == apad][0]
        pos = pad.GetPosition()
        anchor = (pcbnew.ToMM(pos.x) - OX, pcbnew.ToMM(pos.y) - OY)
        fp = b.footprint(p, PROJECT, root, names[p["sym"]])
        fps[p["ref"]] = fp
        if not placer.near(fp, anchor, side):
            retry.append((p, fp, anchor, side))
    for p, fp, anchor, side in retry:             # second pass: other side (via), then anywhere on the board
        if placer.near(fp, anchor, "F" if side == "B" else "B"):
            moved.append(p["ref"])
        elif placer.near(fp, anchor, side, rmax=40.0) or placer.near(fp, anchor, "F" if side == "B" else "B", 40.0):
            moved.append(p["ref"] + " (far)")
        else:
            failed.append(p["ref"])
            b.put(fp, W + 3, 2 + 2 * len(failed), 0, side)   # parked off-board for manual placement

    s = pcbnew.F_SilkS
    b.text(s, 0.95, 21.6 + mf.DESIGN_SHIFT, "C", 1.0)
    b.text(s, 21.45, 21.6 + mf.DESIGN_SHIFT, "B", 1.0)
    b.text(s, 13.4, 29.0 + mf.DESIGN_SHIFT, ">", 1.0)
    b.text(pcbnew.F_Fab, 3.05, 12.4 + mf.DESIGN_SHIFT, "DSM", 0.7, angle=90)
    b.text(pcbnew.F_Fab, 19.0, 12.4 + mf.DESIGN_SHIFT, "A-CRSF", 0.7, angle=90)
    b.save(OUT)
    print("wrote", OUT, f"({W} x {L} mm, {len(design.PARTS)} parts, {len(b.nets)} nets)")
    if moved:
        print("placed on the opposite side of their anchor:", ", ".join(moved))
    if failed:
        print("could not auto-place (parked off-board):", ", ".join(failed))


if __name__ == "__main__":
    main()
