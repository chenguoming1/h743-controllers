#!/usr/bin/env python3
"""Draw a to-scale cross-section of the header child-board joint (one servo column).

  python3 tools/joint_section.py   ->  docs/images/joint-section.svg
"""
import os

import make_footprints as mf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "docs", "images", "joint-section.svg"))
S = 42.0                       # px per mm
Y0, Z0 = -8.2, 10.2            # drawing window: main-board y from Y0, height z from Z0 down
W_MM, H_MM = 21.0, 13.6


def X(y):
    return (y - Y0) * S + 20


def Yp(z):
    return (Z0 - z) * S + 20


def rect(y0, z0, y1, z1, cls):
    return (f'<rect x="{X(min(y0, y1)):.1f}" y="{Yp(max(z0, z1)):.1f}" width="{abs(y1 - y0) * S:.1f}" '
            f'height="{abs(z1 - z0) * S:.1f}" class="{cls}"/>')


def poly(points, cls):
    pts = " ".join(f"{X(y):.1f},{Yp(z):.1f}" for y, z in points)
    return f'<polygon points="{pts}" class="{cls}"/>'


def text(y, z, s, cls="t", anchor="start"):
    return f'<text x="{X(y):.1f}" y="{Yp(z):.1f}" class="{cls}" text-anchor="{anchor}">{s}</text>'


def line(y0, z0, y1, z1, cls):
    return f'<line x1="{X(y0):.1f}" y1="{Yp(z0):.1f}" x2="{X(y1):.1f}" y2="{Yp(z1):.1f}" class="{cls}"/>'


def main():
    ct, mt = mf.CHILD_T, mf.MAIN_T
    co, ci = mf.OUTER_Y, mf.OUTER_Y + ct                       # child outer / inner face (main y)
    s0, s1 = co - mf.SLOT_CLR, ci + mf.SLOT_CLR                  # slot
    tab = mf.TAB_LEN
    ip0, ip1 = mf.MAIN_PAD
    op0, op1 = mf.OUTER_PAD
    cu = 0.07                                                    # drawn copper thickness
    g = []
    # main board (cut through a slot)
    g.append(rect(0, 0, s0, -mt, "fr4"))
    g.append(rect(s1, 0, Y0 + W_MM, -mt, "fr4"))
    # child board
    g.append(rect(co, mf.CHILD_TOP, ci, -tab, "fr4c"))
    # header body + pins on the outer face, tails through the inner face
    g.append(rect(co - 2.5, mf.ROW_Z["GND"] - 1.27, co, mf.ROW_Z["SIG"] + 1.27, "body"))
    for name, z in (("GND", mf.ROW_Z["GND"]), ("VX", mf.ROW_Z["VX"]), ("signal", mf.ROW_Z["SIG"])):
        g.append(rect(co - 2.5 - 6.0, z - 0.32, ci + 1.4, z + 0.32, "pin"))
        g.append(text(co - 8.6, z - 0.12, name, "ts", "end"))
    # copper: child inner pad (per net) and outer strip (VX / GND), main-board pads on the bottom only
    g.append(rect(ci, mf.PAD_ABOVE, ci + cu, -tab + mf.PAD_INSET, "cu"))
    g.append(rect(co - cu, mf.STRIP_TOP, co, -tab + mf.PAD_INSET, "cu"))
    g.append(rect(ip0, -mt, ip1, -mt - cu, "cu"))
    g.append(rect(op0, -mt, op1, -mt - cu, "cu"))
    # solder fillets: bottom face only (VBar style)
    g.append(poly([(ci, -tab + 0.25), (ci, -mt), (ip1 - 0.15, -mt)], "solder"))
    g.append(poly([(co, -tab + 0.25), (co, -mt), (op0 + 0.1, -mt)], "solder"))
    g.append(text(co - 2.6, 0.95, "no solder on the top face", "ts", "end"))
    # keep-out band
    g.append(line(mf.KEEPOUT_Y, 3.0, mf.KEEPOUT_Y, -3.2, "ko"))
    g.append(text(mf.KEEPOUT_Y + 0.15, 2.6, f"{mf.KEEPOUT_Y:.1f} mm: no parts on either side", "ts"))
    # labels
    g.append(text(Y0 + W_MM - 0.2, -0.9, "main board 1.6 mm", "t", "end"))
    g.append(text(ci + 0.25, mf.CHILD_TOP - 0.6, "child board 1.6 mm", "t"))
    g.append(text(co - 2.6, mf.CHILD_TOP - 0.3, "3x7 header body", "ts", "end"))
    g.append(text(ip0, -mt - 0.45, "bottom pad, per net", "ts"))
    g.append(text(op1, -mt - 1.6, "bottom strip VX | GND (one per slot)", "ts", "end"))
    g.append(text(ci + 0.2, -tab - 0.45, f"tab sticks out {tab - mt:.1f} mm", "ts"))
    g.append(text(co - 0.15, -tab + 0.1, "outer strip", "ts", "end"))
    g.append(text(ci + 0.2, 1.05, "inner pad", "ts"))
    g.append(line(0, 0.4, 0, -3.3, "edge"))
    g.append(text(-0.1, -3.5, "main-board edge", "ts", "end"))
    g.append(line(co - 8.5, 3.0, co - 8.5, 8.0, "edge"))
    g.append(text(co - 8.4, 8.3, "pin tips = case end", "ts"))
    g.append(text(Y0 + 0.2, Z0 - 0.5, "Header joint, section through one servo column (to scale)", "h"))
    w, h = W_MM * S + 40, H_MM * S + 40
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}">',
           '<style>'
           '.fr4{fill:#2f5d3a;stroke:#1d3a24;stroke-width:1}.fr4c{fill:#3f7a4c;stroke:#1d3a24;stroke-width:1}'
           '.body{fill:#2b2b2b}.pin{fill:#d9b44a}.cu{fill:#c98a2b}.solder{fill:#c9ccd1;stroke:#8a8f98;stroke-width:0.8}'
           '.ko{stroke:#d1242f;stroke-width:1.5;stroke-dasharray:6 4}.edge{stroke:#57606a;stroke-width:1;stroke-dasharray:3 3}'
           '.t{font:13px sans-serif;fill:#1f2328}.ts{font:11px sans-serif;fill:#1f2328}.h{font:600 15px sans-serif;fill:#1f2328}'
           '</style><rect width="100%" height="100%" fill="#ffffff"/>'] + g + ['</svg>']
    open(OUT, "w").write("\n".join(svg))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
