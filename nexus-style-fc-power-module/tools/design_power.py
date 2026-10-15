"""Power module: the nexus-style-fc main board's POWER and USB blocks (../../nexus-style-fc/tools/design.py,
groups "POWER" and "USB") on their own board.

Parts, values, LCSC codes, nets and reference designators come straight from design.py, so the module
always matches the main board; only the grouping, the placement and the two headers are added here.
The schematic drawing is in gen_power_schematic.py, the PCB in build_power_module.py.

  J1 in  : VX, GND
  J6     : USB-C (VBUS through the F1 PTC, Rd 5.1k on CC, USBLC6 ESD)
  J2 out : 5V, GND, VSYS, 3V3, 3V3_DSM, VX_SENSE, 5V_SENSE, GND, USB_DM, USB_DP

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
W, L = 28.0, 25.0                      # board outline, mm

GROUP_TITLES = {
    "BUCK5": "5V BUCK  TPS62130 3 A, 2.5 MHz  + VX input TVS",
    "MUX": "5V PRIORITY MUX  TPS2116: buck (VIN1) first, USB VBUS (VIN2) second",
    "BUCK3": "3V3 MCU BUCK  TPS629210 1 A, fed from VSYS (VX or VBUS through Schottky OR)  + DSM 3V3 port fuse",
    "SENSE": "ADC SENSE  VX x0.161 (vbec_divider 160) | 5V x0.323 (vbus_divider 320)",
    "USB": "USB-C  (VBUS PTC, Rd 5.1k on CC, USBLC6 ESD on D+ / D-)",
}

# main-board ref -> module sub-block
BLOCK = {"D4": "BUCK5", "U5": "BUCK5", "L1": "BUCK5", "U9": "MUX", "D5": "BUCK3", "D6": "BUCK3",
         "U14": "BUCK3", "L2": "BUCK3", "F2": "BUCK3", "J6": "USB", "F1": "USB", "U7": "USB"}
NOTE_BLOCK = {"buck in, 25 V (TI typical: 10 uF)": "BUCK5", "AVIN": "BUCK5", "soft start": "BUCK5",
              "buck out (TI typical: 22 uF)": "BUCK5", "Vout = 0.8 x (1 + 120/22) = 5.16 V": "BUCK5",
              "switch-over at 1.0 V x 127/27 = 4.7 V": "MUX", "VIN2": "MUX", "5 V bus bulk": "MUX",
              "S-CONF #9: VSET, auto PFM, discharge": "BUCK3", "buck in, 25 V": "BUCK3",
              "buck out (TI typical 22 uF), 10 V": "BUCK3", "UFP Rd": "USB"}


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
for _p in sorted((p for p in design.PARTS if p["group"] in ("POWER", "USB")),
                 key=lambda p: ("JUDLFRC".index(p["ref"][0]), int(p["ref"][1:]))):
    q = copy.deepcopy(_p)
    q["group"] = _block(q)
    PARTS.append(q)
_by_ref = {p["ref"]: p for p in PARTS}

PARTS.insert(0, dict(ref="J1", sym="Connector_Generic:Conn_01x02", value="PWR IN",
                     fp="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", lcsc="",
                     pins={"1": "VX", "2": "GND"}, place=None, group="IO",
                     note="input: VX (BEC / servo bus)"))
PARTS.insert(1, dict(ref="J2", sym="Connector_Generic:Conn_01x10", value="PWR OUT",
                     fp="Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical", lcsc="",
                     pins={"1": "5V", "2": "GND", "3": "VSYS", "4": "3V3", "5": "3V3_DSM", "6": "VX_SENSE",
                           "7": "5V_SENSE", "8": "GND", "9": "USB_DM", "10": "USB_DP"}, place=None, group="IO",
                     note="outputs to the main board; sense lines go to MCU PC0 (VX) / PC1 (5V), USB to PA11 / PA12"))

# ---------------------------------------------------------------- placement (top side only)
# VX header, its TVS and the USB-C socket along the top edge, output header along the bottom edge (pins run
# left to right, pin names on the silkscreen between header and parts); 5V buck on the left, mux in the
# middle, USB ESD and 3V3 buck on the right
LAYOUT = {
    "D4": ("xy", 4.0, 1.8, 180, "F"),        # TVS right beside the VX pin
    "J1": ("xy", 8.6, 1.6, 90, "F"),         # pins left to right: VX GND
    "F1": ("xy", 14.2, 3.2, 90, "F"),        # VBUS fuse between the socket and the rest
    "J6": ("xy", 21.4, 3.4, 0, "F"),         # USB-C, top entry
    "U7": ("xy", 21.4, 8.6, 90, "F"),        # ESD right under the socket's data pins
    "L1": ("xy", 2.6, 11.4, 90, "F"),        # SW pad at the bottom, 5V_BUCK pad at the top
    "U5": ("xy", 7.3, 11.0, 0, "F"),         # SW pins face L1, VIN pins face the input caps
    "D5": ("xy", 11.6, 7.6, 90, "F"),        # VX -> VSYS
    "D6": ("xy", 14.2, 7.6, 90, "F"),        # VBUS -> VSYS, under F1
    "U9": ("xy", 14.4, 14.4, 0, "F"),
    "U14": ("xy", 22.4, 13.2, 0, "F"),
    "L2": ("xy", 21.7, 16.4, 0, "F"),        # SW pad under U14 pin 4
    "F2": ("xy", 15.4, 18.6, 0, "F"),        # above the 3V3 / DSM pins of J2
    "J2": ("xy", 2.57, 23.4, 90, "F"),       # pins left to right: 5V GND VSYS 3V3 DSM VX_S 5V_S GND D- D+
}
for _p in PARTS:
    _p["place"] = LAYOUT.get(_p["ref"])
    if _p["place"]:
        continue
    # passives: next to the pin of their block's IC that they serve (pins in priority order)
    ic, pads = {"BUCK5": ("U5", ("5", "9", "10", "14")), "MUX": ("U9", ("4", "6", "2")),
                "BUCK3": ("U14", ("8", "6", "3")), "SENSE": ("J2", ("6", "7")),
                "USB": ("J6", ("A5", "B5"))}[_p["group"]]
    anchor = _by_ref.get(ic) or next(p for p in PARTS if p["ref"] == ic)
    hit = [pad for pad in pads if anchor["pins"][pad] in set(_p["pins"].values())]
    if not hit:
        raise SystemExit(f"design_power: no placement for {_p['ref']}")
    _p["place"] = ("near", ic, hit[0], "F")



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
