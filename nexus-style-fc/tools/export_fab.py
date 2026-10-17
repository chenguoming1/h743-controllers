#!/usr/bin/env python3
"""JLCPCB fabrication + assembly outputs for both boards.

  python3 tools/export_fab.py            Gerbers + drill + BOM + CPL
  python3 tools/export_fab.py --bom-cpl  BOM + CPL only (placement is final before routing is)

For each board writes manufacturing/<board>/:
  gerbers/ + <board>-gerbers.zip   Gerber RS-274X (Protel extensions, no X2, mask subtracted from
                                   silk) + Excellon drill (PTH and NPTH separate) - JLC's KiCad settings
  <board>-bom-jlc.csv              Comment, Designator, Footprint, LCSC Part #
  <board>-cpl-jlc.csv              Designator, Mid X, Mid Y, Layer, Rotation (same origin as the Gerbers)
Parts without an LCSC number (test pads, the header joint, tab pads) are left out of BOM/CPL.
Verified JLC library rotation corrections are applied only to assembly output;
see docs/validation/reviews/cpl-2026-10-17/REVIEW.md.
"""
import csv
import importlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
K = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
BOARDS = [
    ("nexus-style-fc", "hardware/nexus-style-fc.kicad_pcb", "design", 6),
    ("nexus-header-board", "hardware/header-board/nexus-header-board.kicad_pcb", "design_header", 2),
]


def run(*args):
    subprocess.run([K, *args], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def layers(n):
    cu = ["F.Cu"] + [f"In{i}.Cu" for i in range(1, n - 1)] + ["B.Cu"]
    return ",".join(cu + ["F.Mask", "B.Mask", "F.Paste", "B.Paste", "F.Silkscreen", "B.Silkscreen", "Edge.Cuts"])


def jlc_rotation(name, part, rotation, layer):
    angle = float(rotation)
    if layer == "Bottom":
        # Native KiCad bottom angles use the opposite handedness and zero from
        # JLC's component-side view. Verified against native pin 1 / cathodes
        # for every bottom IC, D4-D6 and Y1 in a fresh JLCDFM import.
        angle = 180 - angle
    if name == "nexus-style-fc" and part["ref"] == "U10":
        # C89347's JLC zero has three leads on the right and pin 1 lower-right.
        # This native footprint has three pads below and pin 1 lower-left.
        # Reimport of 270 degrees verified the clockwise correction in JLCDFM.
        if (part.get("lcsc"), part.get("fp"), layer) != (
                "C89347", "NexusFC:TPS70933DBVR_TI_DBV0005A", "Top"):
            raise ValueError("U10 part, footprint or side changed; reverify its JLC rotation correction")
        angle -= 90
    return f"{angle % 360:.0f}"


def main():
    for name, pcb, mod, ncu in BOARDS:
        out = os.path.join(ROOT, "manufacturing", name)
        gdir = os.path.join(out, "gerbers")
        if "--bom-cpl" not in sys.argv:
            shutil.rmtree(gdir, ignore_errors=True)
        os.makedirs(gdir, exist_ok=True)
        pcb = os.path.join(ROOT, pcb)
        if "--bom-cpl" in sys.argv:          # placement only: no Gerbers from a board still being routed
            pass
        else:
            export_gerbers(name, pcb, ncu, out, gdir)
        bom_cpl(name, pcb, mod, out)


def export_gerbers(name, pcb, ncu, out, gdir):
    if True:
        run("pcb", "export", "gerbers", "--no-x2", "--no-netlist", "--subtract-soldermask", "--use-drill-file-origin",
            "--layers", layers(ncu), "-o", gdir + "/", pcb)
        run("pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm",
            "--excellon-separate-th", "--excellon-oval-format", "route", "--drill-origin", "plot", "-o", gdir + "/", pcb)
        shutil.make_archive(os.path.join(out, f"{name}-gerbers"), "zip", gdir)


def bom_cpl(name, pcb, mod, out):
    if True:
        d = importlib.import_module(mod)
        selected = d.get_main_parts() if mod == "design" and name == "nexus-style-fc" else d.PARTS
        parts = {p["ref"]: p for p in selected if p.get("lcsc") and p["lcsc"].startswith("C")}
        groups = {}
        for p in parts.values():
            groups.setdefault((p["value"], p["fp"].split(":")[1], p["lcsc"]), []).append(p["ref"])
        with open(os.path.join(out, f"{name}-bom-jlc.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
            for (val, fp, lcsc), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
                w.writerow([val, ",".join(sorted(refs, key=lambda r: (r.rstrip("0123456789"), int("0" + r[len(r.rstrip("0123456789")):])))), fp, lcsc])

        with tempfile.TemporaryDirectory() as tmp:
            pos = os.path.join(tmp, "pos.csv")
            run("pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "--use-drill-file-origin", "-o", pos, pcb)
            rows = list(csv.DictReader(open(pos)))
        with open(os.path.join(out, f"{name}-cpl-jlc.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
            for r in rows:
                if r["Ref"] not in parts:
                    continue
                layer = "Top" if r["Side"].lower().startswith("top") else "Bottom"
                w.writerow([r["Ref"], f'{float(r["PosX"]):.4f}mm', f'{float(r["PosY"]):.4f}mm', layer,
                            jlc_rotation(name, parts[r["Ref"]], r["Rot"], layer)])
        print(f"{name}: BOM ({len(groups)} lines, {len(parts)} parts), CPL -> {out}")


if __name__ == "__main__":
    main()
