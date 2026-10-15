#!/usr/bin/env python3
"""Build the servo-header child board PCB from design_header.py and export its VRML
for the main-board 3D view.

Run with KiCad's bundled Python (after make_footprints.py and gen_schematic.py):
  .../Python.framework/Versions/Current/bin/python3 tools/build_header_board.py
"""
import os
import subprocess
import sys

import pcbnew

import design_header as dh
import make_footprints as mf
from pcbutil import Board, uid

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, "..", "hardware"))
OUTDIR = os.path.join(HW, "header-board")
PROJECT = "nexus-header-board"
OUT = os.path.join(OUTDIR, PROJECT + ".kicad_pcb")
WRL = os.path.join(HW, "library", "NexusFC.3dshapes", mf.hig.MODEL_FILE)
KICAD_CLI = os.environ.get("KICAD_CLI", "kicad-cli")

W, TOP, TAB = mf.CHILD_W, mf.CHILD_TOP, mf.TAB_LEN
R = 0.5


def outline(b):
    e = pcbnew.Edge_Cuts
    b.seg(e, (R, -TOP), (W - R, -TOP), 0.05)
    b.arc(e, (W - R, -TOP + R), (W - R, -TOP), (W, -TOP + R), 0.05)
    b.seg(e, (W, -TOP + R), (W, 0), 0.05)
    b.arc(e, (R, -TOP + R), (0, -TOP + R), (R, -TOP), 0.05)
    b.seg(e, (0, -TOP + R), (0, 0), 0.05)
    # Root reliefs are actual contour arcs with explicit midpoints.
    for shape in mf.hig.tab_outline():
        typ, *points = shape
        if typ == "line":
            b.seg(e, points[0], points[1], 0.05)
        else:
            arc = pcbnew.PCB_SHAPE(b.board)
            arc.SetShape(pcbnew.SHAPE_T_ARC)
            arc.SetStart(b.pt(*points[0]))
            arc.SetMid(b.pt(*points[1]))
            arc.SetEnd(b.pt(*points[2]))
            arc.SetLayer(e)
            arc.SetWidth(b.mm(0.05))
            b.board.Add(arc)



def main():
    os.makedirs(OUTDIR, exist_ok=True)
    b = Board(100.0, 100.0 + TOP, 2)
    ds = b.board.GetDesignSettings()
    ds.SetBoardThickness(b.mm(mf.CHILD_T))
    ds.m_CopperEdgeClearance = b.mm(0.254)
    ds.m_MinSilkTextHeight = b.mm(0.5)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(b.mm(0.15))
    nc.SetTrackWidth(b.mm(0.25))
    outline(b)
    root = uid(PROJECT, "root")
    for p in dh.PARTS:
        fp = b.footprint(p, PROJECT, root)
        _, x, y, rot, side = p["place"]
        b.put(fp, x, y, rot, side)
        if p["ref"] != "J1":
            fp.Reference().SetVisible(False)
    for k, name in enumerate(mf.COLS):
        b.text(pcbnew.F_Fab, mf.pad_x_child(name), 1.2, name, 0.45)
    b.text(pcbnew.F_Fab, W / 2, -TOP - 0.8, "outer face (header side): S1 left ... SBUS right", 0.5)
    for lbl, key in (("SIG", "SIG"), ("VX", "VX"), ("GND", "GND")):
        b.text(pcbnew.F_Fab, 1.0, -mf.ROW_Z[key], lbl, 0.45)
    b.text(pcbnew.F_Fab, W / 2, TAB + 0.9, "UNFINISHED: 2 relieved tabs through R0.5 cutouts, soldered on the main-board bottom; one pad per net", 0.45)
    b.save(OUT)
    # the child project sits one level below the shared library
    txt = open(OUT).read().replace("${KIPRJMOD}/library/", "${KIPRJMOD}/../library/")
    open(OUT, "w").write(txt)
    open(os.path.join(OUTDIR, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (version 7)\n  (lib (name "NexusFC") (type "KiCad") '
        '(uri "${KIPRJMOD}/../library/NexusFC.pretty") (options "") (descr "shared project library"))\n)\n')
    open(os.path.join(OUTDIR, "sym-lib-table"), "w").write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "NexusFC") (type "KiCad") '
        '(uri "${KIPRJMOD}/../library/NexusFC.kicad_sym") (options "") (descr "shared project library"))\n)\n')
    print("wrote", OUT)
    export_vrml()


def export_vrml():
    """The child board as a 3D model for the main board's joint footprint (rerun after routing)."""
    subprocess.run([KICAD_CLI, "pcb", "export", "vrml", "--force", "--units", "tenths",
                    "--user-origin", f"100x{100.0 + TOP}mm", "-o", WRL, OUT],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", WRL)


if __name__ == "__main__":
    export_vrml() if "--vrml" in sys.argv else main()
