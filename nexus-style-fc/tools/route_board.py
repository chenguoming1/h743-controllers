#!/usr/bin/env python3
"""Turn the placed main board into a routed 6-layer JLCPCB board.

Run with KiCad's bundled Python after build_floorplan.py:
  .../Python.framework/Versions/Current/bin/python3 tools/route_board.py

Stackup (Altium-style: every signal layer next to a plane), JLC06161H-2116-like 1.6 mm:
  F.Cu  signal (connectors, sensors)        1 oz
  In1   GND plane                           0.5 oz
  In2   signal                              0.5 oz
  In3   3V3 plane (paired with In4 GND)   0.5 oz
  In4   GND plane                           0.5 oz
  B.Cu  signal (MCU side)                   1 oz
Rules follow JLCPCB 6-layer capabilities at no surcharge: 0.09 mm (3.5 mil) min track/space (we route
0.1 mm), and one via size only - 0.2 mm drill / 0.45 mm pad, the smallest via JLC builds without extra cost
(drill < 0.2 mm, or 0.2-0.25 mm drill with pad < 0.45 mm, is charged). Via-in-pad is free on 6+ layers (POFV).
Routing: Specctra DSN -> Freerouting (headless) -> SES import, then GND pours on all layers.
"""
import os
import re
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, "..", "hardware"))
PCB = os.environ.get("ROUTE_PCB", os.path.join(HW, "nexus-style-fc.kicad_pcb"))
PLANE3 = os.environ.get("ROUTE_PLANE3", "0") == "1"      # In3 as 3V3 plane (1) or as a signal layer (0)
WORK = os.environ.get("ROUTE_WORK", os.path.join(HERE, "..", ".route"))
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
JAVA = os.environ.get("JAVA", "/opt/homebrew/opt/openjdk/bin/java")
FREEROUTING = os.environ.get("FREEROUTING_JAR", "")
PASSES = int(os.environ.get("ROUTE_PASSES", "100"))
ROUNDS = int(os.environ.get("ROUTE_ROUNDS", "4"))
FINISH_TRIES = int(os.environ.get("ROUTE_FINISH_TRIES", "6"))          # Freerouting sessions, each starting from the last

HIGH_CURRENT_NETS = ["VX", "5V_BUCK", "SW_5V"]           # buck input/output path, up to ~2.6 A
PORT5V_NETS = ["5V"]                                     # receiver ports, 2 A total, branches per port
POWER_NETS = ["VBUS", "VBUS_C", "VSYS", "3V3_DSM", "3V3_SENS", "SW_3V3"]
PLANE_3V3 = "3V3"                                        # In3 is a solid 3V3 plane
USB_NETS = ["USB_DP", "USB_DM"]

STACKUP = """    (stackup
      (layer "F.SilkS" (type "Top Silk Screen"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 1" (type "prepreg") (thickness 0.1164) (material "2116") (epsilon_r 4.16) (loss_tangent 0.02))
      (layer "In1.Cu" (type "copper") (thickness 0.0152))
      (layer "dielectric 2" (type "core") (thickness 0.55) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
      (layer "In2.Cu" (type "copper") (thickness 0.0152))
      (layer "dielectric 3" (type "prepreg") (thickness 0.1532) (material "2116") (epsilon_r 4.16) (loss_tangent 0.02))
      (layer "In3.Cu" (type "copper") (thickness 0.0152))
      (layer "dielectric 4" (type "core") (thickness 0.55) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
      (layer "In4.Cu" (type "copper") (thickness 0.0152))
      (layer "dielectric 5" (type "prepreg") (thickness 0.1164) (material "2116") (epsilon_r 4.16) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen"))
      (copper_finish "ENIG")
      (dielectric_constraints no)
    )
"""


def mm(v):
    return pcbnew.FromMM(v)


def outline_poly(board):
    bb = board.GetBoardEdgesBoundingBox()
    return [(bb.GetX(), bb.GetY()), (bb.GetRight(), bb.GetY()), (bb.GetRight(), bb.GetBottom()),
            (bb.GetX(), bb.GetBottom())]


def add_zone(board, layer, netname, priority, clearance=0.2, min_width=0.2, conn=None):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNetCode(board.GetNetInfo().GetNetItem(netname).GetNetCode())
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(min_width))
    z.SetPadConnection(conn if conn is not None else pcbnew.ZONE_CONNECTION_THT_THERMAL)  # default: SMD solid, THT thermal
    z.SetThermalReliefGap(mm(0.2))
    z.SetThermalReliefSpokeWidth(mm(0.25))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in outline_poly(board):
        ol.Append(x, y)
    board.Add(z)
    return z


LINK_W = 0.18           # fixed links through the 0.8 mm bridges between header slots (0.31 mm to each slot)


def joint_copper(board):
    """Pre-route the header joint (J1) so the autorouter never goes near the slots.

    - all joint pads are on the bottom face (VBar style); vias in the outer strips and in the inner VX / GND
      pads tie them to the inner layers (GND strip and pad straight into the In1/In4 planes)
    - the outer VX strip reaches the inner VX pad through the centre bridge on In2 + In3
    - the outer GND strip is tied to the GND planes through the bridge on In1 + In4
    - keep-out (tracks, vias) around every slot, 0.3 mm = the board-edge rule
    """
    j = board.FindFootprintByReference("J1")
    pads = list(j.Pads())
    slots = sorted((p.GetBoundingBox() for p in pads if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH), key=lambda b: b.GetX())
    sy0, sy1 = slots[0].GetY(), slots[0].GetBottom()
    bridges = [(slots[i].GetRight() + slots[i + 1].GetX()) // 2 for i in range(len(slots) - 1)]
    net = lambda n: board.GetNetInfo().GetNetItem(n)

    def via(x, y, n):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
        v.SetWidth(mm(VIA_DIA))
        v.SetDrill(mm(VIA_DRILL))
        v.SetNet(net(n))
        v.SetLocked(True)
        board.Add(v)

    def track(pts, layer, n):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(int(x0), int(y0)))
            t.SetEnd(pcbnew.VECTOR2I(int(x1), int(y1)))
            t.SetWidth(mm(LINK_W))
            t.SetLayer(layer)
            t.SetNet(net(n))
            t.SetLocked(True)
            board.Add(t)

    strips, inner = [], {}
    for p in pads:
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or not p.IsOnLayer(pcbnew.B_Cu):
            continue
        bb = p.GetBoundingBox()
        cy = bb.GetCenter().y
        if bb.GetBottom() <= sy0:          # outer strip: vias along it
            xs = [bb.GetX() + mm(0.5), bb.GetCenter().x, bb.GetRight() - mm(0.5)]
            for x in xs:
                via(x, cy, p.GetNetname())
            strips.append((p.GetNetname(), xs, cy))
        elif p.GetNetname() in ("VX", "GND"):
            via(bb.GetCenter().x, cy, p.GetNetname())
            inner[p.GetNetname()] = (bb.GetCenter().x, cy, bb.GetBottom())
    # VX: outer strip -> nearest bridge -> under the inner pad row -> inner VX pad
    vx_x, vx_y, pad_bottom = inner["VX"]
    xs, sy = next((xs, y) for n, xs, y in strips if n == "VX")
    bx = min(bridges, key=lambda b: abs(b - vx_x))
    sx = min(xs, key=lambda x: abs(x - bx))
    low = pad_bottom + mm(0.45)
    for lyr in (pcbnew.In2_Cu, pcbnew.In3_Cu):
        track([(sx, sy), (bx, sy), (bx, low), (vx_x, low), (vx_x, vx_y)], lyr, "VX")
    # GND: both bridges on the plane layers, from the nearest GND strip via down into the plane
    for b in bridges:
        xs, gy = min(((xs, y) for n, xs, y in strips if n == "GND"), key=lambda s: min(abs(x - b) for x in s[0]))
        gx = min(xs, key=lambda x: abs(x - b))
        for lyr in (pcbnew.In1_Cu, pcbnew.In4_Cu):
            track([(gx, gy), (b, gy), (b, sy1 + mm(0.6))], lyr, "GND")
    # keep-outs around the slots
    for s in slots:
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowZoneFills(False)
        z.SetDoNotAllowFootprints(False)
        z.SetLayerSet(pcbnew.LSET.AllCuMask())
        e = mm(0.3)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((s.GetX() - e, s.GetY() - e), (s.GetRight() + e, s.GetY() - e),
                     (s.GetRight() + e, s.GetBottom() + e), (s.GetX() - e, s.GetBottom() + e)):
            ol.Append(int(x), int(y))
        board.Add(z)
    print(f"joint: {len(slots)} slot keep-outs, VX link via bridge x={pcbnew.ToMM(bx):.2f}, GND links {len(bridges)}")


def write_project_rules(pcb_path, classes, patterns, rules):
    """KiCad 10 keeps net classes in the .kicad_pro, so write them there before loading the board."""
    import json
    pro = pcb_path[:-len(".kicad_pcb")] + ".kicad_pro"
    d = json.load(open(pro))
    ns = d["net_settings"]
    base = dict(ns["classes"][0])
    out = []
    for i, (name, width, clr, via, drill) in enumerate(classes):
        c = dict(base)
        c.update(name=name, track_width=width, clearance=clr, via_diameter=via, via_drill=drill,
                 priority=2147483647 if name == "Default" else i)
        out.append(c)
    ns["classes"] = out
    ns["netclass_patterns"] = [{"netclass": c, "pattern": n} for c, nets in patterns for n in nets]
    d["board"]["design_settings"]["rules"].update(rules)
    json.dump(d, open(pro, "w"), indent=2)


# Freerouting necks every class down to 75 % of its width at crowded pads, so 0.12 mm signals end up no
# thinner than 0.09 mm (JLC's no-surcharge minimum); the board rule is 0.09 mm track and space.
SIG_W = float(os.environ.get("ROUTE_SIG_W", "0.12"))
VIA_DIA, VIA_DRILL = 0.45, 0.2     # the one via on the main board: JLC's cheapest 6-layer via
JLC6_RULES = {"min_clearance": 0.09, "min_track_width": 0.09, "min_via_diameter": 0.45, "min_via_annular_width": 0.125,
              "min_through_hole_diameter": 0.2, "min_hole_to_hole": 0.25, "min_hole_clearance": 0.2,
              "min_copper_edge_clearance": 0.3, "min_resolved_spokes": 2}


def setup_rules(board):
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.09)
    ds.m_MinClearance = mm(0.09)
    ds.m_ViasMinSize = mm(VIA_DIA)
    ds.m_ViasMinAnnularWidth = mm((VIA_DIA - VIA_DRILL) / 2)
    ds.m_MinThroughDrill = mm(0.2)
    ds.m_HoleToHoleMin = mm(0.25)
    ds.m_HoleClearance = mm(0.2)
    ds.m_CopperEdgeClearance = mm(0.3)
    ns = ds.m_NetSettings
    nc = ns.GetDefaultNetclass()
    nc.SetClearance(mm(0.1))
    nc.SetTrackWidth(mm(SIG_W))
    nc.SetViaDiameter(mm(VIA_DIA))
    nc.SetViaDrill(mm(VIA_DRILL))
    for name, width, clr, nets in (("HighCurrent", 0.5, 0.12, HIGH_CURRENT_NETS),
                                   ("Port5V", 0.35, 0.1, PORT5V_NETS),
                                   ("Power", 0.25, 0.1, POWER_NETS + ([] if PLANE3 else [PLANE_3V3])),
                                   ("USB", 0.15, 0.1, USB_NETS)):
        via, drill = VIA_DIA, VIA_DRILL
        c = pcbnew.NETCLASS(name)
        c.SetTrackWidth(mm(width))
        c.SetClearance(mm(clr))
        c.SetViaDiameter(mm(via))
        c.SetViaDrill(mm(drill))
        ns.SetNetclass(name, c)
        for n in nets:
            ns.SetNetclassPatternAssignment(n, name)
    ns.RecomputeEffectiveNetclasses()


VIP_DIA, VIP_DRILL = VIA_DIA, VIA_DRILL   # via-in-pad (JLC 6-layer: filled + capped, free)
VIP_MIN_PAD = 0.47                # pad must be at least this wide to take a via


def via_in_pad(board, nets):
    """Drop a locked via in the centre of every big-enough SMD pad on a plane net, after checking the
    via is clear of other-net copper on every layer. Large pads (exposed pads) get a small via grid."""
    others = []                                           # (x0, y0, x1, y1, netcode) of all pads
    for fp in board.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            others.append((bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom(), p.GetNetCode()))
    edge = board.GetBoardEdgesBoundingBox()
    keep = mm(VIP_DIA / 2 + 0.12)                         # via radius + clearance
    placed, vias = [], 0
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() not in nets or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            sz = p.GetSize(p.GetPrincipalLayer())
            w, h = pcbnew.ToMM(min(sz.x, sz.y)), pcbnew.ToMM(max(sz.x, sz.y))
            if w < VIP_MIN_PAD:
                continue
            c = p.GetPosition()
            pts = [(c.x, c.y)]
            if w > 1.5:                                   # exposed pad: 2x2 grid
                d = mm(0.55)
                pts = [(c.x + dx, c.y + dy) for dx in (-d, d) for dy in (-d, d)]
            for x, y in pts:
                if not (edge.GetX() + mm(0.5) < x < edge.GetRight() - mm(0.5)
                        and edge.GetY() + mm(5.2) < y < edge.GetBottom() - mm(0.5)):
                    continue                              # stay out of the header joint band and edges
                if any(x0 - keep < x < x1 + keep and y0 - keep < y < y1 + keep and nc != p.GetNetCode()
                       for x0, y0, x1, y1, nc in others):
                    continue
                if any(abs(x - px) < mm(VIP_DIA + 0.25) and abs(y - py) < mm(VIP_DIA + 0.25) for px, py in placed):
                    continue
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
                v.SetWidth(mm(VIP_DIA))
                v.SetDrill(mm(VIP_DRILL))
                v.SetNet(p.GetNet())
                v.SetLocked(True)
                board.Add(v)
                placed.append((x, y))
                vias += 1
    print(f"via-in-pad: {vias} vias on {', '.join(nets)}")


def sexpr_end(txt, i):
    """Index just past the s-expression that opens at txt[i]."""
    depth = 0
    while True:
        depth += (txt[i] == "(") - (txt[i] == ")")
        i += 1
        if depth == 0:
            return i


def write_stackup(path):
    txt = open(path).read()
    i = txt.find("(stackup")
    if i >= 0:
        txt = txt[:txt.rfind("\n", 0, i) + 1] + txt[sexpr_end(txt, i):].lstrip("\n")
    txt = txt.replace("(setup\n", "(setup\n" + STACKUP, 1)
    open(path, "w").write(txt)


def allow_via_in_pad(dsn):
    """JLC 6-layer boards get filled + capped vias for free, so let the router put vias in SMD pads."""
    txt = open(dsn).read()
    if "(via_at_smd" not in txt:
        txt = txt.replace("    (rule\n", "    (control\n      (via_at_smd on)\n    )\n    (rule\n", 1)
        open(dsn, "w").write(txt)


def drop_dangling_vias(board):
    """Vias the router left behind on an unfinished net (fewer than two tracks end on them, no pad under)."""
    ends = {}
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_TRACE_T:
            for p in (t.GetStart(), t.GetEnd()):
                ends.setdefault((t.GetNetCode(), p.x, p.y), []).append(t)
    gone = []
    for v in board.GetTracks():
        if v.Type() != pcbnew.PCB_VIA_T or v.IsLocked() or v.GetNetname() == "GND":
            continue
        p = v.GetPosition()
        if len(ends.get((v.GetNetCode(), p.x, p.y), [])) < 2:
            gone.append(v)
    for v in gone:
        board.Remove(v)
    print(f"removed {len(gone)} dangling vias")


def run_freerouting(dsn, ses, work=None, edge_um=310, hole_um=210, log="freerouting.log"):
    if not FREEROUTING or not os.path.exists(FREEROUTING):
        raise SystemExit("set FREEROUTING_JAR to the freerouting jar")
    cmd = [JAVA, "-Djava.awt.headless=true", "-jar", FREEROUTING, "--gui.enabled=false",
           "--router.automatic_neckdown=false", "--router.neck_width_um=100",
           f"--router.copper_to_edge_clearance_um={edge_um}",
           f"--router.hole_clearance_um={hole_um}",
           "-de", dsn, "-do", ses, "-mp", str(PASSES), "-mt", "8"]
    print("running:", " ".join(cmd))
    with open(os.path.join(work or WORK, log), "w") as f:
        subprocess.run(cmd, check=True, stdout=f, stderr=subprocess.STDOUT, timeout=3600)


def route_header():
    """2-layer servo-header child board: wide VX/GND, signals, GND pours on both faces."""
    pcb = os.path.join(HW, "header-board", "nexus-header-board.kicad_pcb")
    work = os.path.join(WORK, "header")
    os.makedirs(work, exist_ok=True)
    write_project_rules(pcb, [("Default", 0.2, 0.15, 0.6, 0.3), ("Power", 0.5, 0.15, 0.8, 0.4)],
                        [("Power", ["VX", "GND"])],
                        {"min_clearance": 0.15, "min_track_width": 0.15, "min_through_hole_diameter": 0.3,
                         "min_copper_edge_clearance": 0.15, "min_via_annular_width": 0.15})
    board = pcbnew.LoadBoard(pcb)
    if len(board.Zones()) or len(board.Tracks()):
        raise SystemExit("header board already has copper; rebuild it with build_header_board.py first")
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_MinClearance = mm(0.15)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(0.15)
    ns = ds.m_NetSettings
    nc = ns.GetDefaultNetclass()
    nc.SetClearance(mm(0.15))
    nc.SetTrackWidth(mm(0.2))
    nc.SetViaDiameter(mm(0.6))
    nc.SetViaDrill(mm(0.3))
    c = pcbnew.NETCLASS("Power")
    c.SetTrackWidth(mm(0.5))
    c.SetClearance(mm(0.15))
    c.SetViaDiameter(mm(0.8))
    c.SetViaDrill(mm(0.4))
    ns.SetNetclass("Power", c)
    for n in ("VX", "GND"):
        ns.SetNetclassPatternAssignment(n, "Power")
    ns.RecomputeEffectiveNetclasses()
    dsn, ses = os.path.join(work, "board.dsn"), os.path.join(work, "board.ses")
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        raise SystemExit("DSN export failed")
    run_freerouting(dsn, ses, work, edge_um=160, hole_um=210)
    if not pcbnew.ImportSpecctraSES(board, ses):
        raise SystemExit("SES import failed")
    for lyr in (pcbnew.F_Cu, pcbnew.B_Cu):
        add_zone(board, lyr, "GND", 0, clearance=0.25, conn=pcbnew.ZONE_CONNECTION_FULL)  # servo ground return
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(pcb, board)
    print("wrote", pcb)


def strip_pours(path):
    """Drop the GND pours on the signal layers (keep the In1/In4 planes and the keep-out areas)."""
    txt = open(path).read()
    out, i = [], 0
    while True:
        m = re.compile(r"\(zone\s").search(txt, i)      # not (zone_connect ...
        if not m:
            break
        j = m.start()
        k = sexpr_end(txt, j)
        block = txt[j:k]
        keep = "(keepout" in block or re.search(r'\(layers? "In[14]\.Cu"\)', block)
        out.append(txt[i:k] if keep else txt[i:j])
        i = k
    out.append(txt[i:])
    open(path, "w").write("".join(out))


def one_round():
    """One Freerouting session on the board as saved (run in its own process, see route_rounds)."""
    board = pcbnew.LoadBoard(PCB)
    k = 1
    while os.path.exists(os.path.join(WORK, f"board{k}.ses")):
        k += 1
    if k > 1:
        drop_dangling_vias(board)
    dsn, ses = os.path.join(WORK, f"board{k}.dsn"), os.path.join(WORK, f"board{k}.ses")
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        raise SystemExit("DSN export failed")
    allow_via_in_pad(dsn)
    run_freerouting(dsn, ses, log=f"freerouting{k}.log")
    if not pcbnew.ImportSpecctraSES(board, ses):
        raise SystemExit("SES import failed")
    pcbnew.SaveBoard(PCB, board)
    m = re.findall(r"final score: [0-9.]+ \((\d+) unrouted", open(os.path.join(WORK, f"freerouting{k}.log")).read())
    print(f"ROUND {k} {m[-1] if m else -1}")


def route_rounds(rounds):
    """Freerouting stops when a pass no longer beats its best score; a new session that starts from the
    routed board (existing wires kept, rip-up allowed) usually connects more. Stop when done or stuck.
    Each round runs in its own process: in KiCad 10's SWIG bindings a board goes stale after
    BOARD.Remove or a second LoadBoard."""
    import shutil
    best, keep = None, PCB + ".best"
    for _ in range(rounds):
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "--one"], capture_output=True, text=True)
        m = re.search(r"ROUND (\d+) (-?\d+)", r.stdout)
        if not m:
            sys.stderr.write(r.stdout[-2000:] + r.stderr[-2000:])
            raise SystemExit("routing round failed")
        left = int(m.group(2))
        print(f"round {m.group(1)}: {left} unrouted")
        if best is None or left < best:
            best = left
            shutil.copy(PCB, keep)
        else:
            break
        if left == 0:
            break
    shutil.move(keep, PCB)          # the best round, not the last one
    print(f"kept the best round: {best} unrouted")


def finish():
    """What Freerouting could not finish: finish_route.py (maze router with rip-up + GND stitching) in a few
    net orders at once; the board with the fewest open connections wins."""
    import shutil
    base = os.path.join(WORK, "freerouted.kicad_pcb")
    shutil.copy(PCB, base)
    runs = []
    for seed in range(FINISH_TRIES):
        path = os.path.join(WORK, f"finish{seed}.kicad_pcb")
        shutil.copy(base, path)
        runs.append((seed, path, subprocess.Popen(
            [sys.executable, os.path.join(HERE, "finish_route.py")], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, env=dict(os.environ, ROUTE_PCB=path, FINISH_SEED=str(seed)))))
    best = None
    for seed, path, p in runs:
        out = p.communicate()[0]
        m = re.search(r"finish_route: (\d+) connection\(s\) left(.*)", out)
        left = int(m.group(1)) if m else 999
        print(f"finish order {seed}: {left} left{m.group(2) if m else ''}")
        if best is None or left < best[0]:
            best = (left, path)
    shutil.copy(best[1], PCB)


def pour():
    """Ground everywhere that is left, on every signal layer."""
    board = pcbnew.LoadBoard(PCB)
    for lyr in (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu) if PLANE3 else (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.B_Cu):
        add_zone(board, lyr, "GND", 0, conn=pcbnew.ZONE_CONNECTION_FULL)   # no starved thermals in tight spots
    pcbnew.SaveBoard(PCB, board)


def refill(path):
    """Fill every zone with kicad-cli (the pcbnew filler leaves stale fills after an SES import)."""
    subprocess.run([KICAD_CLI, "pcb", "drc", "--refill-zones", "--save-board", "-o", os.devnull, path],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    if "header" in sys.argv:
        return route_header()
    if "--one" in sys.argv:
        return one_round()
    os.makedirs(WORK, exist_ok=True)
    v = (VIA_DIA, VIA_DRILL)
    write_project_rules(PCB, [("Default", SIG_W, 0.1, *v), ("HighCurrent", 0.5, 0.12, *v),
                              ("Port5V", 0.35, 0.1, *v), ("Power", 0.25, 0.1, *v), ("USB", 0.15, 0.1, *v)],
                        [("HighCurrent", HIGH_CURRENT_NETS), ("Port5V", PORT5V_NETS),
                         ("Power", POWER_NETS + ([] if PLANE3 else [PLANE_3V3])), ("USB", USB_NETS)], JLC6_RULES)
    if "--more" in sys.argv or "--finish" in sys.argv:
        # continue a finished run: lift the signal-layer GND pours (as text, see route_rounds), route more
        strip_pours(PCB)
    else:
        board = pcbnew.LoadBoard(PCB)
        board.SetCopperLayerCount(6)
        for lyr in (pcbnew.In1_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu) if PLANE3 else (pcbnew.In1_Cu, pcbnew.In4_Cu):
            board.SetLayerType(lyr, pcbnew.LT_POWER)
        setup_rules(board)
        if len(board.Zones()) or len(board.Tracks()):
            raise SystemExit("board already has copper; rebuild it with build_floorplan.py first")
        add_zone(board, pcbnew.In1_Cu, "GND", 0)
        if PLANE3:
            add_zone(board, pcbnew.In3_Cu, PLANE_3V3, 0)
        add_zone(board, pcbnew.In4_Cu, "GND", 0)
        joint_copper(board)
        if os.environ.get("ROUTE_VIP", "0") == "1":
            via_in_pad(board, ["GND", PLANE_3V3] if PLANE3 else ["GND"])
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(PCB, board)
    if "--finish" in sys.argv:
        finish()
    elif "--no-route" not in sys.argv:
        route_rounds(ROUNDS)
        finish()
    pour()
    write_stackup(PCB)
    refill(PCB)
    # GND pieces the fill left floating get a via (or a short track to one), then fill again
    r = subprocess.run([sys.executable, os.path.join(HERE, "finish_route.py"), "--islands"],
                       capture_output=True, text=True, env=dict(os.environ, ROUTE_PCB=PCB))
    print("\n".join(l for l in r.stdout.splitlines() if "GND" in l))
    refill(PCB)
    print("wrote", PCB)


if __name__ == "__main__":
    main()
