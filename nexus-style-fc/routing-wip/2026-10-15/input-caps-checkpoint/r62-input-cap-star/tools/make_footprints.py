#!/usr/bin/env python3
"""Generate the project-specific footprints for the main board + servo-header child board.

  Header_3x07_P2.54_Vertical_Servo   child: straight 3x7 header (hanxia HX PZ2.54-3x7P ZZ, C32713294)
  ChildBoard_TabPad_Sig / _Pwr       child: per-net pad on the tab's inner face
  ChildBoard_TabStrip_W*             child: full-width GND / VX strip on the tab's outer face
  HeaderBoard_Joint                  main:  2 long NPTH slots, bottom-side pads only (per-net pads on the
                                     inner slot edge, one long VX / GND strip on each outer edge); its
                                     courtyard is the no-parts band near the header

Joint (VBar style): the child board's bottom edge is two long tabs with a small gap (bar - gap - bar)
that pass through two non-plated slots and stick out 1 mm below the main board. All soldering is on
the main board's bottom face: every net has its own pad on the tab's inner face, soldered to a pad on
the slot's inner edge; the tab's outer face carries one long strip per tab (VX, GND), soldered to a
long strip on the slot's outer edge.

Child board frame (its own PCB, seen from the OUTER face, header on F.Cu): x 0..22.4 with S1
on the left, y = 0 on the main-board top surface, board body above (negative y), tabs below.

Servo header pad numbering is per column, S1 first:
  pad 3*k+1 = signal (row farthest from the main board)
  pad 3*k+2 = VX (centre row, Rotorflight requirement)
  pad 3*k+3 = GND (row nearest the main board)
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PRETTY = os.path.normpath(os.path.join(HERE, "..", "hardware", "library", "NexusFC.pretty"))

PITCH = 2.54
COLS = ["S1", "S2", "S3", "TAIL", "ESC", "RPM", "SBUS"]   # child-board left -> right
ROW_Z = {"GND": 2.3, "VX": 2.3 + PITCH, "SIG": 2.3 + 2 * PITCH}  # height above main board (top pad 0.27 from the edge)
HDR_PAD, HDR_DRILL = 1.5, 1.0
CHILD_W = 22.4
CHILD_TOP = 8.4          # child board top edge above the main-board top surface
CHILD_T = 1.6            # child board thickness
OUTER_Y = 1.6            # main-board y of the child board's outer face (main board runs on under the header body)
DESIGN_SHIFT = OUTER_Y - 0.8   # design.py coordinates were laid out for OUTER_Y = 0.8; shift them by this
MAIN_T = 1.6
TAB_LEN = MAIN_T + 1.0   # tabs stick out 1.0 mm below the main board for the bottom-side fillet
BAR_GAP = 1.0            # the small space between bars
BARS_CHILD = [(0.5, 10.7), (11.7, 21.9)]   # bar x-ranges in the child frame (symmetric: same in the main frame)
SLOT_CLR = 0.1           # NPTH slot clearance around the bar, each side
SIG_W, PWR_W = 1.2, 1.6  # pad widths: signals / VX + GND
PAD_ABOVE = 0.0          # child pads start at the main-board top surface (no solder on the top side)
PAD_INSET = 0.15         # child pad inset from the tab end
MAIN_PAD = (OUTER_Y + CHILD_T + SLOT_CLR + 0.35, OUTER_Y + CHILD_T + SLOT_CLR + 1.35)  # 0.35 from the slot (edge rule 0.3)
OUTER_PAD = (0.35, OUTER_Y - SLOT_CLR - 0.35)   # bottom-side pad on the slot's outer edge (0.35 from edge and slot)
KEEPOUT_Y = MAIN_PAD[1] + 0.35                  # no other parts closer than this to the header edge, either side
STRIP_TOP = 0.0          # outer-face strip starts at the main-board top surface
STRIP_INSET = 0.2        # strip inset from the bar ends
OUTER_NETS_MAIN = ("1", "2")   # joint pad numbers of the outer strips, main-board left to right: VX, GND
# inner-edge pads, main-board left to right, per bar; VX and GND sit next to the centre bridge so the
# main board ties each outer strip to its inner pad with a short link through the bridge
INNER_MAIN = [[("3", "SBUS"), ("4", "RPM"), ("5", "ESC"), ("6", "TAIL"), ("1", "VX")],
              [("2", "GND"), ("7", "S3"), ("8", "S2"), ("9", "S1")]]
MODEL = "${KIPRJMOD}/library/NexusFC.3dshapes"


def col_x_child(k):
    return 3.58 + k * PITCH            # S1 at child-left


def col_x_main(k):
    return CHILD_W - col_x_child(k)    # S1 at main-right


def inner_pads_main():
    """[(pad number, net, x centre, width)] on the main board, evenly spread over each bar."""
    out = []
    for (a, b), pads in zip(bars_main(), INNER_MAIN):
        ws = [PWR_W if net in ("VX", "GND") else SIG_W for _, net in pads]
        lo, hi = a + STRIP_INSET, b - STRIP_INSET
        gap = (hi - lo - sum(ws)) / (len(ws) - 1)
        x = lo
        for (n, net), w in zip(pads, ws):
            out.append((n, net, x + w / 2, w))
            x += w + gap
    return out


def pad_x_child(net):
    """Child-frame x of a net's inner tab pad (mirror of the main board)."""
    return next(CHILD_W - x for _, n, x, _ in inner_pads_main() if n == net)


def fp_header(L):
    L += ['(footprint "Header_3x07_P2.54_Vertical_Servo"',
          '  (version 20240108) (generator "nexus-style-fc") (layer "F.Cu")',
          '  (descr "Straight 3x7 2.54mm servo/ESC/RPM/SBUS header on the vertical child board; hanxia HX PZ2.54-3x7P ZZ (LCSC C32713294)")',
          '  (tags "servo header 3x7 vertical")',
          '  (attr through_hole)',
          '  (fp_text reference "REF**" (at 0 -5.2) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))',
          '  (fp_text value "Servo_3x7" (at 0 5.2) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))',
          '  (fp_rect (start -8.89 -3.81) (end 8.89 3.81) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))',
          '  (fp_rect (start -9.14 -4.06) (end 9.14 4.06) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))']
    for k in range(7):
        x = (k - 3) * PITCH
        for r, y in enumerate((-PITCH, 0.0, PITCH)):   # signal, VX, GND
            n = 3 * k + r + 1
            shape = "rect" if n == 1 else "circle"
            L.append(f'  (pad "{n}" thru_hole {shape} (at {x:.3f} {y:.3f}) (size {HDR_PAD} {HDR_PAD}) (drill {HDR_DRILL}) (layers "*.Cu" "*.Mask"))')
    L += [f'  (model "{MODEL}/CONN-TH_HX-PZ2.54-3X7P-ZZ.wrl"',
          '    (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))', ')']


def strip_name(w):
    return f"ChildBoard_TabStrip_W{w:.1f}"


def bars_main():
    """Bar x-ranges in the main-board frame (mirror of the child frame)."""
    return sorted((CHILD_W - b, CHILD_W - a) for a, b in BARS_CHILD)


def fp_tabpad(L, name, w):
    """Per-net pad on the tab's inner face (B.Cu), from PAD_ABOVE above the main-board surface to the tab end."""
    top, bot = -PAD_ABOVE, TAB_LEN - PAD_INSET
    L += [f'(footprint "{name}"',
          '  (version 20240108) (generator "nexus-style-fc") (layer "F.Cu")',
          f'  (descr "Child-board tab pad, {w} mm wide, inner face (B.Cu), from {PAD_ABOVE} mm above the main-board surface to the tab end. Origin on the seating line")',
          '  (attr smd)',
          '  (fp_text reference "REF**" (at 0 -1.6) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))',
          '  (fp_text value "tab pad" (at 0 3.2) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))',
          f'  (pad "1" smd rect (at 0 {(top + bot) / 2:.3f}) (size {w} {bot - top:.3f}) (layers "B.Cu" "B.Mask"))',
          ')']


def fp_tabstrip(L, name, w):
    """Full-width GND / VX strip on the tab's outer face (F.Cu), starting below the header body."""
    top, bot = -STRIP_TOP, TAB_LEN - PAD_INSET
    L += [f'(footprint "{name}"',
          '  (version 20240108) (generator "nexus-style-fc") (layer "F.Cu")',
          f'  (descr "Child-board outer-face strip, {w:.2f} mm wide (F.Cu), from {STRIP_TOP} mm above the main-board surface (below the header body) to the tab end. Origin on the seating line, tab centre")',
          '  (attr smd)',
          '  (fp_text reference "REF**" (at 0 -1.6) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))',
          '  (fp_text value "tab strip" (at 0 3.2) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))',
          f'  (pad "1" smd rect (at 0 {(top + bot) / 2:.3f}) (size {w:.3f} {bot - top:.3f}) (layers "F.Cu" "F.Mask"))',
          ')']


def fp_joint(L):
    """Main-board joint in main top-view coordinates (origin = PCB top-left corner)."""
    y0, y1 = OUTER_Y - SLOT_CLR, OUTER_Y + CHILD_T + SLOT_CLR      # slot y-range
    py0, py1 = MAIN_PAD
    L += ['(footprint "HeaderBoard_Joint"',
          '  (version 20240108) (generator "nexus-style-fc") (layer "F.Cu")',
          '  (descr "Servo-header child board joint (VBar style): 2 long NPTH slots (bar-gap-bar); all solder on the bottom face: inner slot edge one pad per net, outer slot edge one long strip per slot (VX left, GND right). Courtyard = no-parts band on both sides. Origin = main PCB top-left corner")',
          '  (attr through_hole)',
          f'  (fp_text reference "REF**" (at 11.2 {KEEPOUT_Y - 0.3:.2f}) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))',
          f'  (fp_text value "HeaderBoard" (at 11.2 {KEEPOUT_Y + 0.5:.2f}) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))',
          f'  (fp_rect (start 0 {OUTER_Y:.2f}) (end {CHILD_W} {OUTER_Y + CHILD_T:.2f}) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))',
          f'  (fp_rect (start 0.05 0.1) (end {CHILD_W - 0.05} {KEEPOUT_Y:.2f}) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))',
          f'  (fp_rect (start 0.05 0.1) (end {CHILD_W - 0.05} {KEEPOUT_Y:.2f}) (stroke (width 0.05) (type solid)) (fill none) (layer "B.CrtYd"))',
          f'  (fp_text user "no parts in this band (top and bottom)" (at 11.2 {KEEPOUT_Y - 0.3:.2f}) (layer "B.Fab") (effects (font (size 0.45 0.45) (thickness 0.07)) (justify mirror)))']
    for a, b in bars_main():                        # non-plated slots
        sx, sy = (b - a) + 2 * SLOT_CLR, y1 - y0
        L.append(f'  (pad "" np_thru_hole oval (at {(a + b) / 2:.3f} {(y0 + y1) / 2:.3f}) (size {sx:.3f} {sy:.3f}) (drill oval {sx:.3f} {sy:.3f}) (layers "*.Cu" "*.Mask"))')
    for n, net, x, w in inner_pads_main():          # inner edge, bottom: one pad per net
        L.append(f'  (pad "{n}" smd rect (at {x:.3f} {(py0 + py1) / 2:.3f}) (size {w} {py1 - py0:.2f}) (layers "B.Cu" "B.Mask"))')
    oy0, oy1 = OUTER_PAD
    for (a, b), n in zip(bars_main(), OUTER_NETS_MAIN):                # outer edge, bottom: VX strip, GND strip
        L.append(f'  (pad "{n}" smd rect (at {(a + b) / 2:.3f} {(oy0 + oy1) / 2:.3f}) (size {b - a - 2 * STRIP_INSET:.3f} {oy1 - oy0:.2f}) (layers "B.Cu" "B.Mask"))')
    L += [f'  (model "{MODEL}/nexus-header-board.wrl"',
          f'    (offset (xyz {CHILD_W} {-(OUTER_Y + CHILD_T / 2):.2f} 0)) (scale (xyz 1 1 1)) (rotate (xyz -90 0 180)))',
          ')']


def write(name, lines):
    path = os.path.join(PRETTY, name + ".kicad_mod")
    open(path, "w").write("\n".join(lines) + "\n")
    print("wrote", path)


def main():
    for name, fn in (("Header_3x07_P2.54_Vertical_Servo", fp_header), ("HeaderBoard_Joint", fp_joint)):
        L = []
        fn(L)
        write(name, L)
    for name, w in (("ChildBoard_TabPad_Sig", SIG_W), ("ChildBoard_TabPad_Pwr", PWR_W)):
        L = []
        fp_tabpad(L, name, w)
        write(name, L)
    widths = sorted({round(b - a - 2 * STRIP_INSET, 2) for a, b in BARS_CHILD})
    for f in os.listdir(PRETTY):                     # strips from an older bar layout
        if f.startswith("ChildBoard_TabStrip_W") and f[:-len(".kicad_mod")] not in {strip_name(w) for w in widths}:
            os.remove(os.path.join(PRETTY, f))
            print("removed", f)
    for w in widths:
        L = []
        fp_tabstrip(L, strip_name(w), w)
        write(strip_name(w), L)
    for old in ("HeaderBoard_Slots", "ChildBoard_Tab_W1.0", "ChildBoard_Tab_W1.3", "ChildBoard_FilletPad"):
        path = os.path.join(PRETTY, old + ".kicad_mod")
        if os.path.exists(path):
            os.remove(path)
            print("removed", path)


if __name__ == "__main__":
    main()
