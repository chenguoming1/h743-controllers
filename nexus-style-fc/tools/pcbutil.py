"""Shared helpers for building the KiCad boards from a design module (KiCad bundled Python)."""
import os
import uuid

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
LIBDIR = os.path.normpath(os.path.join(HERE, "..", "hardware", "library", "NexusFC.pretty"))
STOCK = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
NS = uuid.UUID("6f3c2a1e-9b7d-4c55-8a10-2d4e5f6a7b80")   # same namespace as gen_schematic.py


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


class Board:
    def __init__(self, ox, oy, layers):
        self.ox, self.oy = ox, oy
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(layers)
        self.nets = {}

    # -- geometry
    def mm(self, v):
        return pcbnew.FromMM(v)

    def pt(self, x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(self.ox + x), pcbnew.FromMM(self.oy + y))

    def seg(self, layer, a, b, w=0.1):
        s = pcbnew.PCB_SHAPE(self.board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(self.pt(*a))
        s.SetEnd(self.pt(*b))
        s.SetLayer(layer)
        s.SetWidth(self.mm(w))
        self.board.Add(s)

    def arc(self, layer, c, a, b, w=0.1):
        s = pcbnew.PCB_SHAPE(self.board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetCenter(self.pt(*c))
        s.SetStart(self.pt(*a))
        s.SetEnd(self.pt(*b))
        s.SetLayer(layer)
        s.SetWidth(self.mm(w))
        self.board.Add(s)

    def rect(self, layer, x0, y0, x1, y1, w=0.1):
        for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            self.seg(layer, a, b, w)

    def text(self, layer, x, y, t, size=0.8, angle=0):
        tx = pcbnew.PCB_TEXT(self.board)
        tx.SetText(t)
        tx.SetPosition(self.pt(x, y))
        tx.SetLayer(layer)
        tx.SetTextSize(pcbnew.VECTOR2I(self.mm(size), self.mm(size)))
        tx.SetTextThickness(self.mm(size * 0.15))
        tx.SetTextAngleDegrees(angle)
        self.board.Add(tx)

    # -- nets / parts
    def net(self, name):
        if name not in self.nets:
            n = pcbnew.NETINFO_ITEM(self.board, name)
            self.board.Add(n)
            self.nets[name] = n
        return self.nets[name]

    def footprint(self, part, project, root, pin_names=None):
        lib, name = part["fp"].split(":")
        path = LIBDIR if lib == "NexusFC" else os.path.join(STOCK, lib + ".pretty")
        fp = pcbnew.FootprintLoad(path, name)
        if fp is None:
            raise SystemExit(f"missing footprint {part['fp']}")
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(part["ref"])
        fp.SetValue(part["value"])
        fp.SetField("LCSC", part["lcsc"])
        fp.GetField("LCSC").SetVisible(False)
        if part.get("note"):
            fp.SetField("Description", part["note"])
            fp.GetField("Description").SetVisible(False)
        # link to the generated schematic symbol (root sheet path / symbol uuid)
        fp.SetPath(pcbnew.KIID_PATH(f"/{uid(project, 'sym', part['ref'])}"))
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(self.mm(0.5), self.mm(0.5)))
        fp.Reference().SetTextThickness(self.mm(0.08))
        self.board.Add(fp)
        for pad in fp.Pads():
            num = pad.GetNumber()
            netname = part["pins"].get(num)
            if netname:
                pad.SetNet(self.net(netname))
            elif num in part["pins"] and pin_names is not None:
                # same name KiCad gives an unconnected schematic pin, so parity checks stay clean
                name = pin_names.get(num, "")
                name = "" if name in ("", "~", num) else "-" + name.replace("/", "{slash}")
                pad.SetNet(self.net(f"unconnected-({part['ref']}{name}-Pad{num})"))
        return fp

    def put(self, fp, x, y, rot, side):
        fp.SetPosition(self.pt(x, y))
        fp.SetOrientationDegrees(rot)
        if side == "B" and fp.GetLayer() != pcbnew.B_Cu:
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.Reference().SetLayer(pcbnew.B_Fab if side == "B" else pcbnew.F_Fab)

    def save(self, path):
        # fabrication origin (Gerber, drill, pick-and-place) on the board's lower-left corner, so JLC's CPL
        # coordinates come out positive and match the Gerbers
        bb = self.board.GetBoardEdgesBoundingBox()
        self.board.GetDesignSettings().SetAuxOrigin(pcbnew.VECTOR2I(bb.GetX(), bb.GetBottom()))
        pcbnew.SaveBoard(path, self.board)


def courtyard_boxes(fp, layer, ox, oy):
    """List of (x0, y0, x1, y1) boxes in board-relative mm for each courtyard outline (or pad bbox)."""
    fp.BuildCourtyardCaches()          # caches are stale after moves/flips
    poly = fp.GetCourtyard(layer)
    boxes = []
    for i in range(poly.OutlineCount()):
        b = poly.Outline(i).BBox()
        boxes.append((pcbnew.ToMM(b.GetX()) - ox, pcbnew.ToMM(b.GetY()) - oy,
                      pcbnew.ToMM(b.GetRight()) - ox, pcbnew.ToMM(b.GetBottom()) - oy))
    if not boxes:
        on_side = [p for p in fp.Pads() if p.IsOnLayer(pcbnew.F_Cu if layer == pcbnew.F_CrtYd else pcbnew.B_Cu)]
        for p in on_side:
            b = p.GetBoundingBox()
            boxes.append((pcbnew.ToMM(b.GetX()) - ox - 0.1, pcbnew.ToMM(b.GetY()) - oy - 0.1,
                          pcbnew.ToMM(b.GetRight()) - ox + 0.1, pcbnew.ToMM(b.GetBottom()) - oy + 0.1))
    return boxes
