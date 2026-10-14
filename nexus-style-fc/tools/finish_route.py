#!/usr/bin/env python3
"""Finish what Freerouting left: a grid maze router with rip-up for the last connections, then GND stitching.

  KiCad python:  ROUTE_PCB=... finish_route.py [--no-stitch]

Works on the routed main board with the signal-layer pours lifted (route_board.py strips and re-pours
them). Copper is rasterised on a 0.05 mm grid per layer and per net. A connection is routed with A* over
F.Cu / In2.Cu / In3.Cu / B.Cu (In1/In4 stay solid GND), changing layer only where JLC's cheapest via
(0.2/0.45 mm) clears every layer. Each net is split into copper islands and the islands are joined one by
one. When a join is walled in, the search may cross other nets' tracks at a cost; the tracks it crosses
are ripped up and their nets go back in the queue (pads, locked copper and GND are never ripped).
Afterwards GND stitching vias go wherever they fit, so every scrap of the signal-layer pours reaches the
In1/In4 planes.
"""
import heapq
import math
import os
import sys

import numpy as np
import pcbnew
from PIL import Image, ImageDraw

import route_board as rb

G = 0.05                                       # grid, mm
CLR = rb.CLR                                   # must be >= the 0.127 mm manufacturing floor
CLR_HC = max(rb.CLR, rb.MIN_CLEARANCE)                                  # next to HighCurrent copper
MARGIN = 0.05                                  # rasterising and 45-degree steps on the grid
HOLE_CLR = 0.20                                # copper to any drill (JLC: via/NPTH hole to track 0.2)
BORDER = 1.0                                   # grid reaches this far past the board outline
EDGE = 0.33                                    # copper to board edge (0.30 + half the outline line)
HOLE_GAP = 0.25                                # drill to drill
VIA_R, VIA_DRILL_R = rb.VIA_DIA / 2, rb.VIA_DRILL / 2
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.B_Cu]          # routing layers
ALL_CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu]
VIA_COST = 10.0
RIP_COST = 25.0                                # per cell of someone else's track crossed
WIDTHS = {"HighCurrent": [0.5, 0.35, 0.25], "Port5V": [0.35, 0.25], "Power": [0.25],
          "USB": [0.15], "Default": [rb.SIG_W, rb.MIN_TRACK]}


def mm(v):
    return pcbnew.FromMM(v)


def to_mm(v):
    return pcbnew.ToMM(v)


def class_of(net):
    for cls, nets in (("HighCurrent", rb.HIGH_CURRENT_NETS), ("Port5V", rb.PORT5V_NETS),
                      ("Power", rb.POWER_NETS + [rb.PLANE_3V3]), ("USB", rb.USB_NETS)):
        if net in nets:
            return cls
    return "Default"


def seg_dist(a, b, c, d):
    """Distance between segments ab and cd (2-D tuples)."""
    def pt_seg(p, s0, s1):
        vx, vy = s1[0] - s0[0], s1[1] - s0[1]
        L = vx * vx + vy * vy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - s0[0]) * vx + (p[1] - s0[1]) * vy) / L))
        return math.hypot(p[0] - s0[0] - t * vx, p[1] - s0[1] - t * vy)

    def ccw(p, q, r):
        return (r[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (r[0] - p[0])
    if (ccw(a, c, d) > 0) != (ccw(b, c, d) > 0) and (ccw(a, b, c) > 0) != (ccw(a, b, d) > 0):
        return 0.0
    return min(pt_seg(a, c, d), pt_seg(b, c, d), pt_seg(c, a, b), pt_seg(d, a, b))


class Item:
    """One piece of copper: a pad (fixed), or a track / via (soft unless locked or GND)."""

    def __init__(self, obj, kind, new=False):
        self.obj, self.kind, self.new = obj, kind, new
        self.net = obj.GetNetname()
        self.soft = kind in ("track", "via") and not obj.IsLocked() and self.net != "GND"
        if kind == "track":
            s, e = obj.GetStart(), obj.GetEnd()
            self.a, self.b = (to_mm(s.x), to_mm(s.y)), (to_mm(e.x), to_mm(e.y))
            self.w = to_mm(obj.GetWidth())
            self.layer = obj.GetLayer()
        elif kind == "via":
            p = obj.GetPosition()
            self.a = self.b = (to_mm(p.x), to_mm(p.y))
            self.w = to_mm(obj.GetWidth(pcbnew.F_Cu))
            self.layer = None
        self.removed = False

    def layers(self):
        return [l for l in ALL_CU if self.obj.IsOnLayer(l)]

    def through(self):
        return self.kind == "via" or (self.kind == "pad" and self.obj.GetDrillSize().x > 0
                                      and self.obj.GetAttribute() == pcbnew.PAD_ATTRIB_PTH)


class Model:
    def __init__(self, board):
        self.board = board
        bb = board.GetBoardEdgesBoundingBox()
        self.x0, self.y0 = to_mm(bb.GetX()) - BORDER, to_mm(bb.GetY()) - BORDER
        self.nx = int(math.ceil((to_mm(bb.GetWidth()) + 2 * BORDER) / G)) + 1
        self.ny = int(math.ceil((to_mm(bb.GetHeight()) + 2 * BORDER) / G)) + 1
        self.items = []
        for f in board.GetFootprints():
            for p in f.Pads():
                self.items.append(Item(p, "pad"))
        for t in board.GetTracks():
            self.items.append(Item(t, "via" if t.Type() == pcbnew.PCB_VIA_T else "track"))
        self.keepout = self.blank()
        for z in board.Zones():
            if z.GetIsRuleArea():
                ol = z.Outline().Outline(0)
                ImageDraw.Draw(self.keepout).polygon(
                    [self.px(ol.CPoint(n).x, ol.CPoint(n).y) for n in range(ol.PointCount())], fill=1)
        self.keepout = np.array(self.keepout, dtype=bool)
        # Unapproved ordinary tented vias must not drill through pasted SMD copper,
        # including pads of the via's own net. This applies to every via-placing path.
        pasted = self.blank()
        if os.environ.get("ROUTE_APPROVED_VIA_IN_PAD") != "1":
            for f in board.GetFootprints():
                for p in f.Pads():
                    if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                        continue
                    for copper, paste in ((pcbnew.F_Cu, pcbnew.F_Paste), (pcbnew.B_Cu, pcbnew.B_Paste)):
                        if not p.IsOnLayer(paste):
                            continue
                        poly = pcbnew.SHAPE_POLY_SET()
                        p.TransformShapeToPolygon(poly, copper, 0, mm(0.005), pcbnew.ERROR_OUTSIDE)
                        for k in range(poly.OutlineCount()):
                            outline = poly.Outline(k)
                            ImageDraw.Draw(pasted).polygon(
                                [self.px(outline.CPoint(n).x, outline.CPoint(n).y)
                                 for n in range(outline.PointCount())], fill=1)
        self.pasted_smd = np.array(pasted, dtype=bool)
        ps = pcbnew.SHAPE_POLY_SET()
        board.GetBoardPolygonOutlines(ps, False)
        inside = self.blank()
        for k in range(ps.OutlineCount()):
            ol = ps.Outline(k)
            ImageDraw.Draw(inside).polygon([self.px(ol.CPoint(n).x, ol.CPoint(n).y) for n in range(ol.PointCount())], fill=1)
        self.outside = ~np.array(inside, dtype=bool)
        self.rips = {}
        self.raster = {}                                    # (net, soft) -> {layer: bool array}, through
        self.rebuild_all()

    # --- rasters -----------------------------------------------------------------------------------
    def blank(self):
        return Image.new("1", (self.nx, self.ny), 0)

    def px(self, x_nm, y_nm):
        return ((to_mm(x_nm) - self.x0) / G - 0.5, (to_mm(y_nm) - self.y0) / G - 0.5)

    def nm(self, i, j):
        return pcbnew.VECTOR2I(mm(self.x0 + (i + 0.5) * G), mm(self.y0 + (j + 0.5) * G))

    def circle(self, img, pos, r_nm):
        cx, cy = self.px(pos.x, pos.y)
        r = to_mm(r_nm) / G
        ImageDraw.Draw(img).ellipse([cx - r, cy - r, cx + r, cy + r], fill=1)

    def draw(self, item, imgs, thr):
        for layer in ALL_CU:
            if not item.obj.IsOnLayer(layer):
                continue
            ps = pcbnew.SHAPE_POLY_SET()
            item.obj.TransformShapeToPolygon(ps, layer, 0, mm(0.005), pcbnew.ERROR_OUTSIDE)
            img = imgs.setdefault(layer, self.blank())
            d = ImageDraw.Draw(img)
            for k in range(ps.OutlineCount()):
                ol = ps.Outline(k)
                d.polygon([self.px(ol.CPoint(n).x, ol.CPoint(n).y) for n in range(ol.PointCount())], fill=1)
        if item.through():
            r = item.obj.GetWidth(pcbnew.F_Cu) / 2 if item.kind == "via" else item.obj.GetDrillSize().x / 2
            self.circle(thr, item.obj.GetPosition(), r)

    def rebuild(self, net):
        for soft in (False, True):
            imgs, thr = {}, self.blank()
            for it in self.items:
                if it.net == net and it.soft == soft and not it.removed:
                    self.draw(it, imgs, thr)
            self.raster[(net, soft)] = ({l: np.array(im, dtype=bool) for l, im in imgs.items()},
                                        np.array(thr, dtype=bool))
        self.rebuild_holes()

    def rebuild_all(self):
        for net in {it.net for it in self.items}:
            for soft in (False, True):
                imgs, thr = {}, self.blank()
                for it in self.items:
                    if it.net == net and it.soft == soft and not it.removed:
                        self.draw(it, imgs, thr)
                self.raster[(net, soft)] = ({l: np.array(im, dtype=bool) for l, im in imgs.items()},
                                            np.array(thr, dtype=bool))
        self.rebuild_holes()

    def rebuild_holes(self):
        """Drills per net ('' for NPTH): hole-to-hole applies to all of them, hole-to-copper to other nets."""
        imgs = {}
        for it in self.items:
            if it.removed:
                continue
            img = None
            if it.kind == "via":
                img = imgs.setdefault(it.net, self.blank())
                self.circle(img, it.obj.GetPosition(), it.obj.GetDrillValue() / 2)
            elif it.kind == "pad" and it.obj.GetDrillSize().x > 0:
                img = imgs.setdefault(it.net, self.blank())
                sz = it.obj.GetDrillSize()
                if sz.x == sz.y:
                    self.circle(img, it.obj.GetPosition(), sz.x / 2)
                else:
                    seg = it.obj.GetEffectiveHoleShape()
                    a, b, w = seg.GetSeg().A, seg.GetSeg().B, seg.GetWidth()
                    for k in range(13):
                        self.circle(img, pcbnew.VECTOR2I(int(a.x + (b.x - a.x) * k / 12),
                                                         int(a.y + (b.y - a.y) * k / 12)), w / 2)
        self.holes_by_net = {n: np.array(im, dtype=bool) for n, im in imgs.items()}
        self.holes = np.zeros((self.ny, self.nx), bool)
        for h in self.holes_by_net.values():
            self.holes |= h

    def other_holes(self, net):
        out = np.zeros((self.ny, self.nx), bool)
        for n, h in self.holes_by_net.items():
            if n != net or not n:
                out |= h
        return out

    def own(self, net, layer):
        out = np.zeros((self.ny, self.nx), bool)
        for soft in (False, True):
            r = self.raster.get((net, soft))
            if r and layer in r[0]:
                out |= r[0][layer]
        return out

    # --- masks -------------------------------------------------------------------------------------
    @staticmethod
    def dilate(a, r_mm):
        out = a.copy()
        ny, nx = a.shape
        rc = r_mm / G
        r = int(math.ceil(rc))
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if (dx or dy) and dx * dx + dy * dy <= rc * rc:
                    xs0, xs1 = max(0, -dx), nx - max(0, dx)
                    ys0, ys1 = max(0, -dy), ny - max(0, dy)
                    out[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] |= a[ys0:ys1, xs0:xs1]
        return out

    def masks(self, net, width, rip):
        """Hard-blocked track/via centre masks and (if rip) the cost of crossing soft copper."""
        hc = class_of(net) == "HighCurrent"
        tr_h, tr_c = [], []
        edge_t = (self.dilate(self.outside, EDGE + width / 2 + MARGIN) | self.dilate(self.keepout, width / 2 + MARGIN)
                  | self.dilate(self.other_holes(net), HOLE_CLR + width / 2 + MARGIN))
        via_h = self.dilate(self.outside, EDGE + VIA_R + MARGIN) | self.dilate(self.keepout, VIA_R + MARGIN)
        via_h |= self.dilate(self.holes, HOLE_GAP + VIA_DRILL_R + MARGIN)
        via_h |= self.dilate(self.other_holes(net), HOLE_CLR + VIA_R + MARGIN)
        via_h |= self.dilate(self.pasted_smd, VIA_DRILL_R + HOLE_CLR + MARGIN)
        via_c = np.zeros((self.ny, self.nx), np.float32)
        for layer in ALL_CU:
            hard = np.zeros((self.ny, self.nx), bool)
            cost = np.zeros((self.ny, self.nx), np.float32)
            hard_hc = np.zeros((self.ny, self.nx), bool)
            softs = {}                                   # rip count -> union of soft copper
            for (n, soft), (imgs, _) in self.raster.items():
                if n == net or layer not in imgs:
                    continue
                if soft and rip:
                    k = self.rips.get(n, 0)
                    softs[k] = softs.get(k, np.zeros((self.ny, self.nx), bool)) | imgs[layer]
                elif class_of(n) == "HighCurrent":
                    hard_hc |= imgs[layer]
                else:
                    hard |= imgs[layer]
            c = CLR_HC if hc else CLR
            for k, m in softs.items():
                cost += self.dilate(m, c + width / 2 + MARGIN) * (RIP_COST * (1 + 2 * k))
                via_c += self.dilate(m, c + VIA_R + MARGIN) * (RIP_COST * (1 + 2 * k))
            # one dilation for all hard copper on the layer
            hard_t = self.dilate(hard, c + width / 2 + MARGIN) | self.dilate(hard_hc, CLR_HC + width / 2 + MARGIN)
            via_h |= self.dilate(hard, c + VIA_R + MARGIN) | self.dilate(hard_hc, CLR_HC + VIA_R + MARGIN)
            if layer in LAYERS:
                tr_h.append(hard_t | edge_t)
                tr_c.append(cost)
        if not rip:
            via_c = None
        return tr_h, tr_c, via_h, via_c

    def islands(self, net):
        """Copper islands of a net, found geometrically (what touches what, as KiCad sees it), then drawn
        on the grid (routing layers; through items on all of them) for the router."""
        its = [it for it in self.items if it.net == net and not it.removed]
        parent = list(range(len(its)))

        def find(k):
            while parent[k] != k:
                parent[k] = parent[parent[k]]
                k = parent[k]
            return k

        def touch(p, q):
            if p.kind == "pad" and q.kind == "pad":
                return False
            if q.kind == "pad":
                p, q = q, p
            if p.kind == "pad":
                if q.kind == "via":
                    return p.obj.HitTest(q.obj.GetPosition(), int(mm(q.w / 2)))
                if not p.obj.IsOnLayer(q.layer):
                    return False
                tol = int(mm(q.w / 2))
                mid = pcbnew.VECTOR2I(mm((q.a[0] + q.b[0]) / 2), mm((q.a[1] + q.b[1]) / 2))
                return any(p.obj.HitTest(pt, tol) for pt in (q.obj.GetStart(), q.obj.GetEnd(), mid))
            if p.kind == "via" and q.kind == "via":
                return math.dist(p.a, q.a) <= (p.w + q.w) / 2
            if p.kind == "track" and q.kind == "track" and p.layer != q.layer:
                return False
            return seg_dist(p.a, p.b, q.a, q.b) <= (p.w + q.w) / 2 + 1e-4

        boxes = []
        for it in its:
            if it.kind == "pad":
                bb = it.obj.GetBoundingBox()
                boxes.append((to_mm(bb.GetX()), to_mm(bb.GetY()), to_mm(bb.GetRight()), to_mm(bb.GetBottom())))
            else:
                r = it.w / 2
                boxes.append((min(it.a[0], it.b[0]) - r, min(it.a[1], it.b[1]) - r,
                              max(it.a[0], it.b[0]) + r, max(it.a[1], it.b[1]) + r))
        for a in range(len(its)):
            for b in range(a + 1, len(its)):
                A, B = boxes[a], boxes[b]
                if A[0] > B[2] or B[0] > A[2] or A[1] > B[3] or B[1] > A[3]:
                    continue
                if find(a) != find(b) and touch(its[a], its[b]):
                    parent[find(a)] = find(b)
        roots = {}
        for k in range(len(its)):
            roots.setdefault(find(k), len(roots) + 1)
        label = np.zeros((len(LAYERS), self.ny, self.nx), np.int32)
        for k, it in enumerate(its):
            imgs, thr = {}, self.blank()
            self.draw(it, imgs, thr)
            lid = roots[find(k)]
            for L, layer in enumerate(LAYERS):
                if layer in imgs:
                    label[L][np.array(imgs[layer], dtype=bool)] = lid
        self.last_islands = (net, its, [roots[find(k)] for k in range(len(its))])
        return label, len(roots)


def prune(model, net):
    """Drop tracks / vias on an island with no pad (stubs left by Freerouting or by a rip-up)."""
    label, n = model.islands(net)
    _, its, ids = model.last_islands
    anchored = {i for it, i in zip(its, ids) if not it.soft}
    gone = 0
    for it, i in zip(its, ids):
        if it.soft and i not in anchored:
            it.removed = True
            gone += 1
    if gone:
        model.rebuild(net)
    return gone


def astar(sources, tgt, tr_h, tr_c, via_h, via_c, shape):
    ny, nx = shape
    ty, tx = np.nonzero(tgt.any(axis=0))
    bx0, bx1, by0, by1 = tx.min(), tx.max(), ty.min(), ty.max()

    def h(y, x):
        return math.hypot(max(bx0 - x, 0, x - bx1), max(by0 - y, 0, y - by1))

    dist, prev, pq = {}, {}, []
    for s in sources:
        dist[s] = 0.0
        heapq.heappush(pq, (h(s[1], s[2]), 0.0, s))
    steps = [(dy, dx, math.hypot(dy, dx)) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
    nL = len(tr_h)
    while pq:
        f, d, node = heapq.heappop(pq)
        if d > dist.get(node, 1e18):
            continue
        l, y, x = node
        if tgt[l, y, x]:
            path = [node]
            while node in prev:
                node = prev[node]
                path.append(node)
            return path[::-1]
        th, tc = tr_h[l], tr_c[l] if tr_c else None
        for dy, dx, c in steps:
            yy, xx = y + dy, x + dx
            if not (0 <= yy < ny and 0 <= xx < nx) or th[yy, xx]:
                continue
            if dy and dx and (th[y, xx] or th[yy, x]):
                continue
            cc = c + (float(tc[yy, xx]) * c if tc is not None else 0.0)
            if tc is None and False:
                pass
            nb, nd = (l, yy, xx), d + cc
            if nd < dist.get(nb, 1e18):
                dist[nb], prev[nb] = nd, node
                heapq.heappush(pq, (nd + h(yy, xx), nd, nb))
        if not via_h[y, x]:
            vc = VIA_COST + (float(via_c[y, x]) if via_c is not None else 0.0)
            for m in range(nL):
                if m != l and not tr_h[m][y, x]:
                    nb, nd = (m, y, x), d + vc
                    if nd < dist.get(nb, 1e18):
                        dist[nb], prev[nb] = nd, node
                        heapq.heappush(pq, (nd + h(y, x), nd, nb))
    return None


def path_items(model, path):
    """Grid path -> [('t', layer, (x0,y0), (x1,y1)) | ('v', (x,y))] in mm, collinear runs merged."""
    pt = lambda n: (model.x0 + (n[2] + 0.5) * G, model.y0 + (n[1] + 0.5) * G)
    out = []
    run = [path[0]]
    for nxt in path[1:]:
        cur = run[-1]
        if nxt[0] != cur[0]:
            if len(run) > 1:
                out.append(("t", LAYERS[cur[0]], pt(run[0]), pt(cur)))
            out.append(("v", pt(cur)))
            run = [nxt]
            continue
        if len(run) >= 2:
            d0 = (cur[1] - run[-2][1], cur[2] - run[-2][2])
            d1 = (nxt[1] - cur[1], nxt[2] - cur[2])
            if d0 != d1:
                out.append(("t", LAYERS[cur[0]], pt(run[0]), pt(cur)))
                run = [cur]
        run.append(nxt)
    if len(run) > 1:
        out.append(("t", LAYERS[run[-1][0]], pt(run[0]), pt(run[-1])))
    return out


def colliders(model, net, width, prims):
    """Soft items of other nets that the new copper would violate."""
    hit = set()
    for it in model.items:
        if it.removed or not it.soft or it.net == net:
            continue
        c = CLR_HC if "HighCurrent" in (class_of(net), class_of(it.net)) else CLR
        for p in prims:
            if p[0] == "t":
                _, layer, a, b = p
                if it.kind == "track":
                    if it.layer == layer and seg_dist(a, b, it.a, it.b) < c + width / 2 + it.w / 2:
                        hit.add(it)
                elif seg_dist(a, b, it.a, it.a) < c + width / 2 + it.w / 2:
                    hit.add(it)
            else:
                _, a = p
                if it.kind == "track":
                    if seg_dist(a, a, it.a, it.b) < c + VIA_R + it.w / 2:
                        hit.add(it)
                elif math.dist(a, it.a) < max(c + VIA_R + it.w / 2, HOLE_GAP + 2 * VIA_DRILL_R):
                    hit.add(it)
    return hit


def emit(model, net, width, prims):
    board = model.board
    netinfo = board.GetNetInfo().GetNetItem(net)
    for p in prims:
        if p[0] == "t":
            _, layer, a, b = p
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
            t.SetWidth(mm(width))
            t.SetLayer(layer)
            kind = "track"
        else:
            t = pcbnew.PCB_VIA(board)
            t.SetPosition(pcbnew.VECTOR2I(mm(p[1][0]), mm(p[1][1])))
            t.SetWidth(mm(rb.VIA_DIA))
            t.SetDrill(mm(rb.VIA_DRILL))
            kind = "via"
        t.SetNet(netinfo)
        model.items.append(Item(t, kind, new=True))          # goes on the board in commit()


def route_between(model, net, src, tgt, rip, widths=None):
    """A* from src cells to tgt cells for a net; rip-up of other nets' soft copper if allowed."""
    for w in widths or WIDTHS[class_of(net)]:
        tr_h, tr_c, via_h, via_c = model.masks(net, w, rip)
        path = astar(src, tgt, tr_h, tr_c if rip else None, via_h, via_c, (model.ny, model.nx))
        if not path:
            continue
        prims = path_items(model, path)
        hit = colliders(model, net, w, prims) if rip else set()
        ripped = set()
        for it in hit:
            it.removed = True
            ripped.add(it.net)
        emit(model, net, w, prims)
        for n_ in ripped | {net}:
            model.rebuild(n_)
        print(f"  {net}: joined ({len(prims)} pieces, {w} mm{', ripped ' + ' '.join(sorted(ripped)) if ripped else ''})")
        return True, ripped
    return False, set()


def join_once(model, net, rip):
    """Join one island of the net to the largest one. Returns (ok, ripped nets)."""
    label, n = model.islands(net)
    if n <= 1:
        return True, set()
    sizes = sorted(((int((label == k).sum()), k) for k in range(1, n + 1)), reverse=True)
    main = sizes[0][1]
    src = [tuple(map(int, s)) for s in zip(*np.nonzero(label == main))]
    tgt = (label > 0) & (label != main)
    return route_between(model, net, src, tgt, rip)


def rejoin(model, nets):
    """Re-join nets cut by a rip-up (no further rip-up). Returns the nets that stay open."""
    bad = set()
    for r in nets:
        for _ in range(8):
            if model.islands(r)[1] <= 1:
                break
            if not join_once(model, r, False)[0]:
                bad.add(r)
                break
    return bad


def snapshot(model):
    return len(model.items), {id(it) for it in model.items if it.removed}


def revert(model, snap):
    n, removed = snap
    touched = {it.net for it in model.items[n:]}
    del model.items[n:]
    for it in model.items:
        r = id(it) in removed
        if it.removed != r:
            touched.add(it.net)
            it.removed = r
    for net in touched:
        model.rebuild(net)


def connect_tx(model, net, src, tgt, tries, depth):
    """Transactional src->tgt connection with rip-up; nets it cuts are re-joined with depth - 1."""
    if route_between(model, net, src, tgt, False)[0]:
        return True
    for _ in range(tries):
        snap = snapshot(model)
        ok, ripped = route_between(model, net, src, tgt, True)
        if not ok:
            return False
        bad = set()
        for r in ripped:
            for _ in range(8):
                if model.islands(r)[1] <= 1:
                    break
                if not (join_once(model, r, False)[0] or (depth > 1 and join_net(model, r, tries=3, depth=depth - 1))):
                    bad.add(r)
                    break
        if not bad:
            return True
        revert(model, snap)
        for r in bad:
            model.rips[r] = model.rips.get(r, 0) + 3
    return False


def join_net(model, net, tries=4, depth=1):
    """Join one island of a net. A rip-up is kept only if every net it cut can be re-joined (with rip-up
    one level less deep); otherwise it is undone and the nets that would not re-join get more expensive."""
    ok, _ = join_once(model, net, False)
    if ok:
        return True
    if depth == 0:
        return False
    for _ in range(tries):
        snap = snapshot(model)
        ok, ripped = join_once(model, net, True)
        if not ok:
            return False
        bad = set()
        for r in ripped:
            for _ in range(8):
                if model.islands(r)[1] <= 1:
                    break
                if not join_net(model, r, tries=2, depth=depth - 1):
                    bad.add(r)
                    break
        if not bad:
            return True
        print(f"  {net}: rip-up undone ({' '.join(sorted(bad))} would stay open)")
        revert(model, snap)
        for r in bad:
            model.rips[r] = model.rips.get(r, 0) + 3
    return False


def open_count(model, nets):
    return sum(model.islands(n)[1] - 1 for n in nets)


def clear_out(model, net, nets, radius=1.0, grow=(1.0, 1.6, 2.4)):
    """Last resort for a walled-in pad: lift other nets' soft copper around the smallest island of the
    net, route this net first, then let the lifted nets find new ways. Kept only if fewer stay open."""
    label, n = model.islands(net)
    if n <= 1:
        return True
    sizes = sorted((int((label == k).sum()), k) for k in range(1, n + 1))
    small = label == sizes[0][1]
    ys, xs = np.nonzero(small.any(axis=0))
    cx, cy = model.x0 + xs.mean() * G, model.y0 + ys.mean() * G
    before = open_count(model, nets)
    for r in grow:
        snap = snapshot(model)
        lifted = set()
        for it in model.items:
            if it.removed or not it.soft or it.net == net:
                continue
            if seg_dist(it.a, it.b, (cx, cy), (cx, cy)) < r + it.w / 2:
                it.removed = True
                lifted.add(it.net)
        for n_ in lifted:
            model.rebuild(n_)
        while model.islands(net)[1] > 1 and join_net(model, net):
            pass
        for n_ in sorted(lifted):
            while model.islands(n_)[1] > 1 and join_net(model, n_, tries=4, depth=1):
                pass
        after = open_count(model, nets)
        print(f"  {net}: clear-out r={r} mm lifted {' '.join(sorted(lifted))}: {before} -> {after} open")
        if after < before:
            return True
        revert(model, snap)
    return False


def commit(model):
    added = removed = 0
    for it in model.items:
        if getattr(it, "done", False):
            continue
        if it.new and not it.removed:
            model.board.Add(it.obj)
            added += 1
            it.done = True
        elif not it.new and it.removed:
            model.board.Remove(it.obj)
            removed += 1
            it.done = True
    print(f"commit: +{added} / -{removed} tracks and vias")


def stitch_gnd(model, pitch=1.2):
    """GND vias on a grid wherever one fits: ties every scrap of the signal-layer pours to In1/In4."""
    _, _, via_h, _ = model.masks("GND", 0.2, False)
    step = int(round(pitch / G))
    netinfo = model.board.GetNetInfo().GetNetItem("GND")
    yy, xx = np.ogrid[:model.ny, :model.nx]
    rr = ((max(HOLE_GAP + 2 * VIA_DRILL_R, CLR + 2 * VIA_R) + MARGIN) / G) ** 2
    n = 0
    for j in range(step // 2, model.ny, step):
        for i in range(step // 2, model.nx, step):
            for dj, di in ((0, 0), (0, 3), (3, 0), (0, -3), (-3, 0), (3, 3), (-3, -3), (3, -3), (-3, 3)):
                y, x = j + dj, i + di
                if 0 <= y < model.ny and 0 <= x < model.nx and not via_h[y, x]:
                    v = pcbnew.PCB_VIA(model.board)
                    v.SetPosition(model.nm(x, y))
                    v.SetWidth(mm(rb.VIA_DIA))
                    v.SetDrill(mm(rb.VIA_DRILL))
                    v.SetNet(netinfo)
                    model.board.Add(v)
                    model.items.append(Item(v, "via"))
                    via_h |= (yy - y) ** 2 + (xx - x) ** 2 <= rr
                    n += 1
                    break
    model.rebuild("GND")
    print(f"GND stitching: {n} vias")


def label_cells(mask):
    """4-connected components of a bool array -> (labels, count)."""
    lab = np.zeros(mask.shape, np.int32)
    n = 0
    ny, nx = mask.shape
    for y0, x0 in zip(*np.nonzero(mask)):
        if lab[y0, x0]:
            continue
        n += 1
        lab[y0, x0] = n
        stack = [(y0, x0)]
        while stack:
            y, x = stack.pop()
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < ny and 0 <= xx < nx and mask[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    stack.append((yy, xx))
    return lab, n


def fill_pieces(model, layer):
    """The pieces of the GND pour as KiCad filled it (needs a filled board), one mask per piece."""
    out = []
    for z in model.board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != "GND" or not z.IsOnLayer(layer) or not z.IsFilled():
            continue
        polys = z.GetFilledPolysList(layer)
        for k in range(polys.OutlineCount()):
            img = model.blank()
            ol = polys.Outline(k)
            ImageDraw.Draw(img).polygon([model.px(ol.CPoint(n).x, ol.CPoint(n).y) for n in range(ol.PointCount())], fill=1)
            out.append(np.array(img, dtype=bool))
    return out


def estimated_pieces(model, layer, zone_clr, min_w):
    """Without a fill: guess the pour (clear of other nets, wider than the zone's minimum width)."""
    other = np.zeros((model.ny, model.nx), bool)
    for (n, soft), (imgs, _) in model.raster.items():
        if n != "GND" and layer in imgs:
            other |= imgs[layer]
    blocked = Model.dilate(other, zone_clr) | Model.dilate(model.outside, EDGE) | model.keepout
    blocked |= Model.dilate(model.other_holes("GND"), HOLE_CLR)
    pour = ~Model.dilate(blocked, min_w / 2)
    pour = Model.dilate(pour, min_w / 2) & ~blocked
    pour |= model.own("GND", layer)
    lab, n = label_cells(pour)
    return [lab == k for k in range(1, n + 1)]


def gnd_reached(model, pieces):
    """GND copper (pads, tracks, vias, pour pieces) reachable from a GND via / PTH, i.e. from the planes."""
    thr = np.zeros((model.ny, model.nx), bool)
    for soft in (False, True):
        r = model.raster.get(("GND", soft))
        if r:
            thr |= r[1]
    own = []
    for layer in LAYERS:
        m = model.own("GND", layer)
        for p in pieces[layer]:
            m = m | p
        own.append(m)
    reached = np.zeros((len(LAYERS), model.ny, model.nx), bool)
    stack = []
    for L in range(len(LAYERS)):
        seed = own[L] & thr
        reached[L] |= seed
        stack += [(L, int(y), int(x)) for y, x in zip(*np.nonzero(seed))]
    while stack:
        l, y, x = stack.pop()
        nb = [(l, y + dy, x + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
        if thr[y, x]:
            nb += [(m, y, x) for m in range(len(LAYERS)) if m != l]
        for m, yy, xx in nb:
            if 0 <= yy < model.ny and 0 <= xx < model.nx and own[m][yy, xx] and not reached[m, yy, xx]:
                reached[m, yy, xx] = True
                stack.append((m, yy, xx))
    return reached


def stitch_islands(model, zone_clr=0.2, min_w=0.2):
    """The GND pour on each signal layer breaks into pieces; give every piece that holds GND copper but
    no GND via / PTH its own via, so the zone filler keeps it and it reaches the In1/In4 planes."""
    _, _, via_h, _ = model.masks("GND", 0.2, False)
    netinfo = model.board.GetNetInfo().GetNetItem("GND")
    added = 0
    pieces = {layer: fill_pieces(model, layer) or estimated_pieces(model, layer, zone_clr, min_w) for layer in LAYERS}
    reached = gnd_reached(model, pieces)
    for L, layer in enumerate(LAYERS):
        for piece in pieces[layer]:
            if (piece & reached[L]).any() or not (piece & model.own("GND", layer)).any():
                continue
            cand = piece & ~via_h
            if not cand.any():
                # no room for a via: a short track from the GND copper of this piece to the nearest GND via
                ys, xs = np.nonzero(piece & model.own("GND", layer))
                L = LAYERS.index(layer)
                src = [(L, int(y), int(x)) for y, x in zip(ys, xs)]
                tgt = np.zeros((len(LAYERS), model.ny, model.nx), bool)
                tgt[:] = reached & ~piece[None, :, :]
                done = connect_tx(model, "GND", src, tgt, tries=8, depth=1)
                if not done:                   # clear the neighbourhood, tie GND first, re-route the rest
                    sig = [n for n in {it.net for it in model.items} if n and n != "GND" and not n.startswith("unconnected-")]
                    before = open_count(model, sig)
                    cx, cy = model.x0 + xs.mean() * G, model.y0 + ys.mean() * G
                    for r in (1.0, 1.6, 2.4):
                        snap = snapshot(model)
                        lifted = set()
                        for it in model.items:
                            if not it.removed and it.soft and seg_dist(it.a, it.b, (cx, cy), (cx, cy)) < r + it.w / 2:
                                it.removed = True
                                lifted.add(it.net)
                        for n_ in lifted:
                            model.rebuild(n_)
                        if route_between(model, "GND", src, tgt, False, widths=(0.15, rb.MIN_TRACK))[0]:
                            for n_ in sorted(lifted):
                                while model.islands(n_)[1] > 1 and join_net(model, n_, tries=4, depth=1):
                                    pass
                            after = open_count(model, sig)
                            print(f"  GND clear-out r={r} mm lifted {' '.join(sorted(lifted))}: {before} -> {after} open")
                            if after <= before:
                                done = True
                                break
                        revert(model, snap)
                if done:
                    commit(model)
                    added += 1
                    reached[L] |= piece
                    print(f"  GND piece on {pcbnew.LayerName(layer)}: tied to a via by a track")
                if not done:
                    print(f"  GND piece on {pcbnew.LayerName(layer)} near "
                          f"({model.x0 + xs.mean() * G:.1f}, {model.y0 + ys.mean() * G:.1f}) has no way to a via")
                continue
            ys, xs = np.nonzero(cand)
            cy, cx = np.nonzero(piece)
            i = int(np.argmin((ys - cy.mean()) ** 2 + (xs - cx.mean()) ** 2))
            v = pcbnew.PCB_VIA(model.board)
            v.SetPosition(model.nm(int(xs[i]), int(ys[i])))
            v.SetWidth(mm(rb.VIA_DIA))
            v.SetDrill(mm(rb.VIA_DRILL))
            v.SetNet(netinfo)
            model.board.Add(v)
            yy, xx = np.ogrid[:model.ny, :model.nx]
            via_h |= (yy - ys[i]) ** 2 + (xx - xs[i]) ** 2 <= ((HOLE_GAP + 2 * VIA_DRILL_R + MARGIN) / G) ** 2
            reached[L] |= piece
            added += 1
    print(f"GND island vias: {added}")


def main():
    board = pcbnew.LoadBoard(rb.PCB)
    model = Model(board)
    if "--islands" in sys.argv:            # after a pour + fill: stitch the GND pieces KiCad left floating
        stitch_islands(model)
        pcbnew.SaveBoard(rb.PCB, board)
        return
    nets = sorted(n for n in {it.net for it in model.items} if n and n != "GND" and not n.startswith("unconnected-"))
    thin = set()
    for it in model.items:
        if it.kind == "track" and it.w < rb.MIN_TRACK - 1e-6:
            if not it.soft:
                raise SystemExit(f"Protected track {it.obj.m_Uuid.AsString()} on {it.net} is below 0.127 mm; resolve explicitly")
            it.removed = True              # no blind widening: reroute and verify native DRC
            thin.add(it.net)
    for n in thin:
        model.rebuild(n)
    if thin:
        print("re-routing thin tracks of", " ".join(sorted(thin)))
    stubs = sum(prune(model, n) for n in nets)
    print(f"pruned {stubs} orphan tracks / vias")
    todo = [n for n in nets if model.islands(n)[1] > 1]
    seed = int(os.environ.get("FINISH_SEED", "0"))
    if seed:                               # another order gives another result; route_board tries a few
        import random
        random.Random(seed).shuffle(todo)
    print("nets with islands:", " ".join(todo))
    for net in todo:
        while model.islands(net)[1] > 1:
            if not join_net(model, net) and not join_net(model, net, tries=8, depth=2):
                print(f"  {net}: stuck")
                break
    for net in nets:                       # walled-in pads: clear the neighbourhood and route them first
        if model.islands(net)[1] > 1:
            clear_out(model, net, nets)
    for n in nets:
        prune(model, n)
    commit(model)
    left = {n: model.islands(n)[1] - 1 for n in nets}
    left = {n: k for n, k in left.items() if k > 0}
    if "--no-stitch" not in sys.argv:
        stitch_gnd(model)
    pcbnew.SaveBoard(rb.PCB, board)
    print(f"finish_route: {sum(left.values())} connection(s) left {left if left else ''}")


if __name__ == "__main__":
    main()
