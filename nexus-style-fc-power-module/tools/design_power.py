"""Power module: the nexus-style-fc main board's POWER block (../../nexus-style-fc/tools/design.py, group "POWER")
on its own board.

Parts, values, LCSC codes, nets and reference designators come straight from design.py, so the module
always matches the main board; only the grouping, the placement and the two headers are added here.

  J1 in  : VX, GND, VBUS (USB 5 V after the main board's PTC), GND
  J2 out : 5V, GND, VSYS, 3V3, 3V3_DSM, GND, VX_SENSE, 5V_SENSE

Placement: ("xy", x, y, rot, side) or ("near", ref, pad, side), top-view mm from the PCB top-left corner.
All parts sit on the top side (single-sided JLC assembly).
"""
import copy
import os
import sys

# the main board's design and generators live in the sibling nexus-style-fc project
NEXUS_TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "nexus-style-fc", "tools"))
sys.path.insert(1, NEXUS_TOOLS)

import design  # noqa: E402

TITLE = "Nexus-style FBL - power module"
REV = "0.1"
PAGE = ("A3", 420.0, 297.0)
W, L = 26.0, 22.0                      # board outline, mm

GROUP_TITLES = {
    "IO": "MODULE I/O  J1 in | J2 out",
    "BUCK5": "5V BUCK  TPS62130 3 A, 2.5 MHz  + VX input TVS",
    "MUX": "5V PRIORITY MUX  TPS2116: buck (VIN1) first, USB VBUS (VIN2) second",
    "BUCK3": "3V3 MCU BUCK  TPS629210 1 A, fed from VSYS (VX or VBUS through Schottky OR)  + DSM 3V3 port fuse",
    "SENSE": "ADC SENSE  VX x0.161 (vbec_divider 160) | 5V x0.323 (vbus_divider 320)",
}

SAME_ROW = {"SENSE"}                   # the dividers sit beside J2 on the schematic, as on the board
ORDER = ["IO", "SENSE", "BUCK5", "MUX", "BUCK3"]

# main-board ref -> module sub-block
BLOCK = {"D4": "BUCK5", "U5": "BUCK5", "L1": "BUCK5", "U9": "MUX", "D5": "BUCK3", "D6": "BUCK3",
         "U14": "BUCK3", "L2": "BUCK3", "F2": "BUCK3"}
NOTE_BLOCK = {"buck in, 25 V (TI typical: 10 uF)": "BUCK5", "AVIN": "BUCK5", "soft start": "BUCK5",
              "buck out (TI typical: 22 uF)": "BUCK5", "Vout = 0.8 x (1 + 120/22) = 5.16 V": "BUCK5",
              "switch-over at 1.0 V x 127/27 = 4.7 V": "MUX", "VIN2": "MUX", "5 V bus bulk": "MUX",
              "S-CONF #9: VSET, auto PFM, discharge": "BUCK3", "buck in, 25 V": "BUCK3",
              "buck out (TI typical 22 uF), 10 V": "BUCK3"}


def _block(p):
    if p["ref"] in BLOCK:
        return BLOCK[p["ref"]]
    if p["note"] in NOTE_BLOCK:
        return NOTE_BLOCK[p["note"]]
    nets = set(p["pins"].values())
    if nets & {"VX_SENSE", "5V_SENSE"}:
        return "SENSE"
    if nets & {"FB_5V"}:
        return "BUCK5"
    if nets & {"PR1"}:
        return "MUX"
    raise SystemExit(f"design_power: no block for {p['ref']} ({p['note']})")


PARTS = []
for _p in sorted((p for p in design.PARTS if p["group"] == "POWER"), key=lambda p: ("UDLFRC".index(p["ref"][0]), int(p["ref"][1:]))):
    q = copy.deepcopy(_p)
    q["group"] = _block(q)
    PARTS.append(q)
_by_ref = {p["ref"]: p for p in PARTS}

PARTS.insert(0, dict(ref="J1", sym="Connector_Generic:Conn_01x04", value="PWR IN",
                     fp="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", lcsc="",
                     pins={"1": "VX", "2": "GND", "3": "VBUS", "4": "GND"}, place=None, group="IO",
                     note="input: VX (BEC / servo bus), VBUS (USB 5 V, already fused on the main board)"))
PARTS.insert(1, dict(ref="J2", sym="Connector_Generic:Conn_01x08", value="PWR OUT",
                     fp="Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", lcsc="",
                     pins={"1": "5V", "2": "GND", "3": "VSYS", "4": "3V3", "5": "3V3_DSM", "6": "GND",
                           "7": "VX_SENSE", "8": "5V_SENSE"}, place=None, group="IO",
                     note="outputs to the main board; sense lines go to MCU PC0 (VX) / PC1 (5V)"))

# ---------------------------------------------------------------- placement (top side only)
# input header along the top edge, output header along the bottom edge (pins run left to right, pin names
# on the silkscreen between header and parts); 5V buck on the left, mux in the middle, 3V3 buck on the right
LAYOUT = {
    "J1": ("xy", 12.0, 1.6, 90, "F"),        # pins left to right: VX GND VBUS GND
    "J2": ("xy", 4.1, 20.4, 90, "F"),        # pins left to right: 5V GND VSYS 3V3 DSM GND VX_S 5V_S
    "D4": ("xy", 7.6, 1.8, 180, "F"),        # TVS right beside the VX pin
    "L1": ("xy", 2.6, 9.0, 90, "F"),         # SW pad at the bottom, 5V_BUCK pad at the top
    "U5": ("xy", 7.3, 8.6, 0, "F"),          # SW pins face L1, VIN pins face the input caps
    "D5": ("xy", 12.4, 6.4, 90, "F"),        # VX -> VSYS, under the VX pin
    "D6": ("xy", 17.1, 6.4, 90, "F"),        # VBUS -> VSYS, under the VBUS pin
    "U9": ("xy", 13.6, 12.6, 0, "F"),
    "U14": ("xy", 21.4, 8.6, 0, "F"),
    "L2": ("xy", 20.7, 11.8, 0, "F"),        # SW pad under U14 pin 4
    "F2": ("xy", 14.3, 16.2, 0, "F"),        # above the 3V3 / DSM pins of J2
}
for _p in PARTS:
    _p["place"] = LAYOUT.get(_p["ref"])
    if _p["place"]:
        continue
    # passives: next to the pin of their block's IC that they serve (pins in priority order)
    ic, pads = {"BUCK5": ("U5", ("5", "9", "10", "14")), "MUX": ("U9", ("4", "6", "2")),
                "BUCK3": ("U14", ("8", "6", "3")), "SENSE": ("J2", ("7", "8"))}[_p["group"]]
    anchor = _by_ref.get(ic) or PARTS[1]
    hit = [pad for pad in pads if anchor["pins"][pad] in set(_p["pins"].values())]
    if not hit:
        raise SystemExit(f"design_power: no placement for {_p['ref']}")
    _p["place"] = ("near", ic, hit[0], "F")

PARTS.sort(key=lambda p: ORDER.index(p["group"]))     # schematic block order (stable within a block)
PWR_FLAGS = ["VX", "GND", "VBUS"]


def nets():
    out = {}
    for p in PARTS:
        for pad, net in p["pins"].items():
            if net:
                out.setdefault(net, []).append((p["ref"], pad))
    return out


if __name__ == "__main__":
    n = nets()
    print(len(PARTS), "parts,", len(n), "nets")
    for p in PARTS:
        print(f"  {p['ref']:4} {p['value']:14} {p['group']:6} {p['place']}  {p['note']}")
    for name, conns in sorted(n.items()):
        if len(conns) < 2:
            print("single-pin net:", name, conns)
