"""Servo-header child board: straight 3x7 header on two long tabs (VBar style), one pad per net.

Coordinates are in the child frame (see make_footprints.py): seen from the outer face,
S1 on the left, y = 0 on the main-board surface line, board body at negative y.
Net names match the main board (design.py) so the joint is easy to check.
"""
import make_footprints as mf

TITLE = "Nexus-style FBL - servo header child board"
REV = "0.3"
PARTS = []

hdr = {}
for k, sig in enumerate(mf.COLS):
    hdr[str(3 * k + 1)] = sig
    hdr[str(3 * k + 2)] = "VX"
    hdr[str(3 * k + 3)] = "GND"
PARTS.append(dict(ref="J1", sym="NexusFC:HXPZ2.54-3X7PZZ", value="Servo header 3x7", lcsc="C32713294",
                  fp="NexusFC:Header_3x07_P2.54_Vertical_Servo", pins=hdr,
                  place=("xy", mf.CHILD_W / 2, -mf.ROW_Z["VX"], 0, "F"), group="CHILD",
                  note="columns S1..SBUS; rows signal / VX / GND (top to bottom)"))
PARTS.append(dict(ref="T1", sym="Connector_Generic:Conn_01x01", value="GND tab pad", lcsc="",
                  fp="NexusFC:ChildBoard_TabPad_Pwr", pins={"1": "GND"},
                  place=("xy", mf.pad_x_child("GND"), 0, 0, "F"), group="CHILD", note="inner face; main-board joint pad 2"))
PARTS.append(dict(ref="T2", sym="Connector_Generic:Conn_01x01", value="VX tab pad", lcsc="",
                  fp="NexusFC:ChildBoard_TabPad_Pwr", pins={"1": "VX"},
                  place=("xy", mf.pad_x_child("VX"), 0, 0, "F"), group="CHILD", note="inner face; main-board joint pad 1"))
# outer face: one long strip per tab; the child frame is the mirror of the main board, so the main board's
# left (VX) strip is the child's right one
OUTER_NETS_CHILD = {"1": "VX", "2": "GND"}
for i, ((a, b), n) in enumerate(zip(mf.BARS_CHILD, reversed(mf.OUTER_NETS_MAIN))):
    net = OUTER_NETS_CHILD[n]
    w = round(b - a - 2 * mf.STRIP_INSET, 3)
    PARTS.append(dict(ref=f"K{i + 1}", sym="Connector_Generic:Conn_01x01", value=f"{net} strip", lcsc="",
                      fp="NexusFC:" + mf.strip_name(w), pins={"1": net},
                      place=("xy", (a + b) / 2, 0, 0, "F"), group="CHILD",
                      note="outer face strip, soldered to the main-board outer-edge strip (bottom)"))
for k, sig in enumerate(mf.COLS):
    PARTS.append(dict(ref=f"P{k + 1}", sym="Connector_Generic:Conn_01x01", value=f"{sig} tab pad", lcsc="",
                      fp="NexusFC:ChildBoard_TabPad_Sig", pins={"1": sig},
                      place=("xy", mf.pad_x_child(sig), 0, 0, "F"), group="CHILD",
                      note="inner face; soldered to the main-board joint pad (bottom)"))
PWR_FLAGS = ["VX", "GND"]
