#!/usr/bin/env python3
"""Generate the project-specific footprints for the main board + servo-header child board.

  Header_3x07_P2.54_Vertical_Servo   child: straight 3x7 header (hanxia HX PZ2.54-3x7P ZZ, C32713294)
  ChildBoard_TabPad_Sig / _Pwr       child: per-net pad on the tab's inner face
  ChildBoard_TabStrip_W*             child: full-width GND / VX strip on the tab's outer face
  HeaderBoard_Joint                  main:  2 routed 9.8 x 2.1 mm R0.5 cutouts, bottom-side pads only (per-net pads on the
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
import header_interface_geometry as hig

HERE = os.path.dirname(os.path.abspath(__file__))
PRETTY = os.path.normpath(os.path.join(HERE, "..", "hardware", "library", "NexusFC.pretty"))

PITCH = 2.54
COLS = ["S1", "S2", "S3", "TAIL", "ESC", "RPM", "SBUS"]   # child-board left -> right
ROW_Z = {"GND": 2.3, "VX": 2.3 + PITCH, "SIG": 2.3 + 2 * PITCH}  # height above main board (top pad 0.27 from the edge)
HDR_PAD, HDR_DRILL = 1.5, 1.0
CHILD_W = hig.WIDTH
CHILD_TOP = hig.TOP          # child board top edge above the main-board top surface
CHILD_T = hig.CHILD_THICKNESS            # child board thickness
OUTER_Y = hig.SLOT_CENTERS[0][1] - CHILD_T / 2            # main-board y of the child board's outer face (main board runs on under the header body)
DESIGN_SHIFT = OUTER_Y - 0.8   # design.py coordinates were laid out for OUTER_Y = 0.8; shift them by this
MAIN_T = hig.MAIN_THICKNESS
TAB_LEN = hig.TAB_LENGTH   # tabs stick out 1.0 mm below the main board for the bottom-side fillet
BAR_GAP = 2.8            # the small space between bars
BARS_CHILD = list(hig.TABS)   # bar x-ranges in the child frame (symmetric: same in the main frame)
SLOT_CLR = (hig.SLOT_WIDTH - CHILD_T) / 2          # transverse gap only; routed length is independently defined
SIG_W, PWR_W = 1.2, 1.6  # pad widths: signals / VX + GND
PAD_ABOVE = -hig.CHILD_PAD_TOP          # child pads start at the main-board top surface (no solder on the top side)
PAD_INSET = hig.CONTACT_EDGE         # child pad inset from the tab end
MAIN_PAD = hig.MAIN_INNER_Y  # 0.30 from the widened slot (edge rule 0.3)
OUTER_PAD = hig.MAIN_OUTER_Y   # bottom-side pad on the slot's outer edge (0.35 from external edge, 0.30 from slot)
KEEPOUT_Y = MAIN_PAD[1] + 0.35                  # no other parts closer than this to the header edge, either side
STRIP_TOP = -hig.CHILD_PAD_TOP          # outer-face strip starts at the main-board top surface
STRIP_INSET = hig.CONTACT_EDGE        # strip inset from the bar ends
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
    return hig.inner_pads_main()


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
    return f"ChildBoard_TabStrip_W{w:.3f}"


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
          f'  (descr "Child-board outer-face strip, {w:.3f} mm wide (F.Cu), from {STRIP_TOP} mm above the main-board surface (below the header body) to the tab end. Origin on the seating line, tab centre")',
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
          '  (descr "Servo-header child board joint (VBar style): 2 routed 9.8 x 2.1 mm R0.5 cutouts (bar-gap-bar); all solder on the bottom face: inner slot edge one pad per net, outer slot edge one long strip per slot (VX left, GND right). Courtyard = no-parts band on both sides. Origin = main PCB top-left corner")',
          '  (attr smd)',
          f'  (fp_text reference "REF**" (at 11.2 {KEEPOUT_Y - 0.3:.2f}) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))',
          f'  (fp_text value "HeaderBoard" (at 11.2 {KEEPOUT_Y + 0.5:.2f}) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))',
          f'  (fp_rect (start 0 {OUTER_Y:.2f}) (end {CHILD_W} {OUTER_Y + CHILD_T:.2f}) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))',
          f'  (fp_rect (start 0.05 0.1) (end {CHILD_W - 0.05} {KEEPOUT_Y:.2f}) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))',
          f'  (fp_rect (start 0.05 0.1) (end {CHILD_W - 0.05} {KEEPOUT_Y:.2f}) (stroke (width 0.05) (type solid)) (fill none) (layer "B.CrtYd"))',
          f'  (fp_text user "no parts in this band (top and bottom)" (at 11.2 {KEEPOUT_Y - 0.3:.2f}) (layer "B.Fab") (effects (font (size 0.45 0.45) (thickness 0.07)) (justify mirror)))']
    # Actual routed R0.5 contours, never oval drill pads or illustrative lines.
    for cx, cy in hig.SLOT_CENTERS:
        for shape in hig.rounded_slot(cx, cy):
            L.append("  " + hig.kicad_shape(shape))
    for n, net, x, w in inner_pads_main():          # inner edge, bottom: one pad per net
        L.append(f'  (pad "{n}" smd rect (at {x:.6f} {(py0 + py1) / 2:.6f}) (size {w} {py1 - py0:.2f}) (layers "B.Cu" "B.Mask"))')
    oy0, oy1 = OUTER_PAD
    for (a, b), n in zip(bars_main(), OUTER_NETS_MAIN):                # outer edge, bottom: VX strip, GND strip
        L.append(f'  (pad "{n}" smd rect (at {(a + b) / 2:.3f} {(oy0 + oy1) / 2:.3f}) (size {hig.MAIN_OUTER_STRIP_WIDTH:.3f} {oy1 - oy0:.3f}) (layers "B.Cu" "B.Mask"))')
    L += [f'  (model "{MODEL}/{hig.MODEL_FILE}"',
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
    widths = [hig.CHILD_STRIP_WIDTH]  # Electrical strip unchanged when physical tabs widen
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
