#!/usr/bin/env python3
"""Draw an annotated floorplan SVG (top view + bottom X-ray) from the PCB.

Run with KiCad's bundled Python after build_floorplan.py:
  .../Python.framework/Versions/Current/bin/python3 tools/floorplan_svg.py
"""
import os

import pcbnew

import build_floorplan as bf
import make_footprints as mf

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.normpath(os.path.join(HERE, "..", "hardware", "nexus-style-fc.kicad_pcb"))
OUT = os.path.normpath(os.path.join(HERE, "..", "docs", "images", "floorplan.svg"))

OX, OY, W, L = bf.OX, bf.OY, bf.W, bf.L
CASE_W, CASE_L, OVER = bf.CASE_W, bf.CASE_L, bf.OVERHANG
S = 14.0                      # px per mm
PAD = 30                      # px margin around each panel
SHORT = {  # short labels; small parts split on the first space
    "J1": "HEADER CHILD BOARD SLOTS", "J2": "DSM", "J3": "A-CRSF", "J4": "C", "J5": "B",
    "J6": "USB-C", "SW1": "BOOT", "U4": "FLASH 128MB", "U1": "STM32F722RET6",
    "U2": "IMU", "U3": "BARO", "Y1": "8MHz", "U5": "BUCK 5V", "L1": "L 5V",
    "U8": "DSM 3V3", "L3": "L DSM", "U9": "PWR MUX", "U7": "USB ESD", "F1": "USB PTC",
    "U10": "LDO SENS", "U14": "BUCK 3V3", "L2": "L 3V3", "U11": "ESD HDR", "U12": "ESD HDR",
    "U13": "ESD A/B", "U15": "ESD C/DSM", "D4": "VX TVS", "D5": "OR VX", "D6": "OR USB",
    "D1": "G", "D2": "R", "D3": "PWR",
    "TP1": "DIO", "TP2": "CLK", "TP3": "3V3", "TP4": "GND", "TP5": "RST", "L1": "L 5V",
}


def to_mm(v):
    return pcbnew.ToMM(v)


def bbox(fp, side):
    layer = pcbnew.F_CrtYd if side == "F" else pcbnew.B_CrtYd
    poly = fp.GetCourtyard(layer)
    if poly.OutlineCount():
        b = poly.BBox()
    else:
        b = fp.GetBoundingBox(False)
    return (to_mm(b.GetX()) - OX, to_mm(b.GetY()) - OY,
            to_mm(b.GetRight()) - OX, to_mm(b.GetBottom()) - OY)


def panel(x0, title, items, ghost, blocks=()):
    out = []
    cx0 = (W - CASE_W) / 2
    X = lambda v: x0 + PAD + (v - cx0) * S
    Y = lambda v: PAD + 40 + (v + OVER) * S
    out.append(f'<text x="{X(W / 2):.1f}" y="{PAD + 14}" class="title">{title}</text>')
    out.append(f'<rect x="{X(cx0):.1f}" y="{Y(-OVER):.1f}" width="{CASE_W * S:.1f}" height="{CASE_L * S:.1f}" class="case"/>')
    out.append(f'<rect x="{X(0):.1f}" y="{Y(0):.1f}" width="{W * S:.1f}" height="{L * S:.1f}" rx="{0.7 * S:.1f}" class="pcb"/>')
    yb = mf.OUTER_Y - 2.5                     # header body on the child board's outer face
    for k in range(7):
        px = X(W / 2 + (k - 3) * 2.54)
        out.append(f'<line x1="{px:.1f}" y1="{Y(-OVER):.1f}" x2="{px:.1f}" y2="{Y(yb):.1f}" class="pin"/>')
    out.append(f'<rect x="{X(W / 2 - 8.9):.1f}" y="{Y(yb):.1f}" width="{17.8 * S:.1f}" height="{2.5 * S:.1f}" class="hdr"/>')
    out.append(f'<rect x="{X(0):.1f}" y="{Y(mf.OUTER_Y):.1f}" width="{W * S:.1f}" height="{mf.CHILD_T * S:.1f}" class="child"/>')
    for ref, (a, b, c, d), cls in ghost:
        out.append(f'<rect x="{X(a):.1f}" y="{Y(b):.1f}" width="{(c - a) * S:.1f}" height="{(d - b) * S:.1f}" class="ghost"/>')
    for (a, b, c, d, label) in blocks:
        out.append(f'<rect x="{X(a):.1f}" y="{Y(b):.1f}" width="{(c - a) * S:.1f}" height="{(d - b) * S:.1f}" class="blk"/>')
        for i, line in enumerate(label.split("\n")):
            out.append(f'<text x="{X((a + c) / 2):.1f}" y="{Y(b) + 13 + 11 * i:.1f}" class="blkt">{line}</text>')
    for ref, (a, b, c, d), cls in items:
        if ref == "J1":
            continue                          # drawn as the child board above
        out.append(f'<rect x="{X(a):.1f}" y="{Y(b):.1f}" width="{(c - a) * S:.1f}" height="{(d - b) * S:.1f}" class="{cls}"/>')
        label = SHORT.get(ref, ref)
        mx, my = X((a + c) / 2), Y((b + d) / 2)
        tc = " dark" if cls in ("conn", "pas") else ""
        if cls == "pas":
            out.append(f'<text x="{mx:.1f}" y="{my + 2.5:.1f}" class="ref dark" font-size="6">{ref}</text>')
            continue
        if (c - a) < 4.2 and (d - b) < 4.2:
            # small part: two stacked lines inside the box, compact font
            words = label.split(" ", 1)
            out.append(f'<text x="{mx:.1f}" y="{my - 1:.1f}" class="lbl{tc}" font-size="8">{words[0]}</text>')
            if len(words) > 1:
                out.append(f'<text x="{mx:.1f}" y="{my + 8:.1f}" class="lbl{tc}" font-size="8">{words[1]}</text>')
            continue
        vertical = (d - b) > 1.6 * (c - a) and len(label) > 3
        rot = f' transform="rotate(-90 {mx:.1f} {my:.1f})"' if vertical else ""
        fs = 9 if len(label) > 10 else 10
        out.append(f'<text x="{mx:.1f}" y="{my - 2:.1f}" class="lbl{tc}" font-size="{fs}"{rot}>{label}</text>')
        out.append(f'<text x="{mx:.1f}" y="{my + 9:.1f}" class="ref{tc}"{rot}>{ref}</text>')
    out.append(f'<text x="{X(W / 2):.1f}" y="{Y(-OVER) - 6:.1f}" class="note">servo plugs</text>')
    return out


def main():
    board = pcbnew.LoadBoard(PCB)
    top, bot = [], []
    for fp in board.GetFootprints():
        side = "B" if fp.GetLayer() == pcbnew.B_Cu else "F"
        ref = fp.GetReference()
        passive = ref[0] in "RC" and ref[1:].isdigit()
        cls = "conn" if ref.startswith(("J", "SW")) else "pas" if passive else ("ic" if side == "F" else "icb")
        entry = (ref, bbox(fp, side), cls)
        (top if side == "F" else bot).append(entry)
    ghost_b = [e for e in top if e[0] in ("J1", "J6")]  # through-hole parts block the bottom too
    pw = int((CASE_W * S) + 2 * PAD)
    ph = int((CASE_L * S) + 2 * PAD + 60)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{2 * pw + 20}" height="{ph + 40}" viewBox="0 0 {2 * pw + 20} {ph + 40}">',
           '<style>'
           '.title{font:600 15px sans-serif;text-anchor:middle;fill:#1f2328}'
           '.case{fill:none;stroke:#8a8f98;stroke-dasharray:5 4;stroke-width:1.2}'
           '.pcb{fill:#2f5d3a;stroke:#1d3a24;stroke-width:1.5}'
           '.pin{stroke:#d9b44a;stroke-width:5}'
           '.conn{fill:#efe6cf;stroke:#8c7a4b;stroke-width:1}'
           '.ic{fill:#4a4f57;stroke:#1f2328;stroke-width:1}'
           '.icb{fill:#3d6fb6;stroke:#1d3d6e;stroke-width:1}'
           '.ghost{fill:none;stroke:#efe6cf;stroke-dasharray:3 3;stroke-width:1}'
           '.lbl{font-family:sans-serif;font-weight:600;text-anchor:middle;fill:#fff;paint-order:stroke;stroke:#00000088;stroke-width:2px}'
           '.ref{font:9px sans-serif;text-anchor:middle;fill:#e8e8e8}'
           '.note{font:11px sans-serif;text-anchor:middle;fill:#57606a}'
           '.dark{fill:#1f2328;stroke:none}'
           '.blk{fill:#ffffff14;stroke:#9ec3ff;stroke-dasharray:4 3;stroke-width:1}'
           '.blkt{font:9px sans-serif;text-anchor:middle;fill:#cfe0ff}'
           '.hdr{fill:#2b2b2b;stroke:#000;stroke-width:1}'
           '.pas{fill:#d8c9a8;stroke:#7a6a48;stroke-width:0.6}'
           '.child{fill:#5b8f63;stroke:#1d3a24;stroke-width:1}'
           '</style>',
           '<rect width="100%" height="100%" fill="#ffffff"/>']
    svg += panel(0, "TOP side (connectors)", top, [])
    svg += panel(pw + 20, "BOTTOM side, X-ray from top", bot, ghost_b)
    svg.append(f'<text x="{pw + 10}" y="{ph + 22}" class="note">Main PCB {W} x {L} mm + vertical header child board, inside the Nexus 25.4 x 41.3 mm case (dashed).</text>')
    svg.append(f'<text x="{pw + 10}" y="{ph + 36}" class="note">Bottom panel dashed outlines: child-board slots and USB shell tabs (through-hole).</text>')
    svg.append('</svg>')
    open(OUT, "w").write("\n".join(svg))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
