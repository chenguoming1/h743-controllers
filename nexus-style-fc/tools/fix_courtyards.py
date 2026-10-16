#!/usr/bin/env python3
"""Replace the body-only courtyards of the EasyEDA-converted footprints with proper ones.

easyeda2kicad courtyards follow the package body and leave pads outside, so KiCad's courtyard
checks (and the auto-placer) cannot see the pads. New courtyard = bounding box of pads and
the 3D body (VRML model) + 0.15 mm, as a rectangle on the courtyard layer.
Idempotent: works only from pads and the body, never from the old courtyard.
"""
import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PRETTY = os.path.normpath(os.path.join(HERE, "..", "hardware", "library", "NexusFC.pretty"))
MARGIN = 0.15


def pad_extents(text):
    xs, ys = [], []
    for m in re.finditer(r'\(pad\s+"?[^"\s]*"?\s+\w+\s+\w+\s+\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)\s+\(size\s+([-\d.]+)\s+([-\d.]+)\)', text):
        x, y, rot, w, h = float(m.group(1)), float(m.group(2)), float(m.group(3) or 0), float(m.group(4)), float(m.group(5))
        if int(round(rot)) % 180 == 90:
            w, h = h, w
        xs += [x - w / 2, x + w / 2]
        ys += [y - h / 2, y + h / 2]
    return xs, ys


def graphic_extents(text):
    xs, ys = [], []
    for line in text.splitlines():
        if ("F.SilkS" in line or "F.Fab" in line) and ("fp_line" in line or "fp_arc" in line or "fp_circle" in line):
            for m in re.finditer(r'\((?:start|end|mid|center)\s+([-\d.]+)\s+([-\d.]+)\)', line):
                xs.append(float(m.group(1)))
                ys.append(float(m.group(2)))
    return xs, ys


def model_extents(text):
    """x/y extents of the footprint's VRML body (0.1 inch units, y up), in footprint mm."""
    m = re.search(r'\(model "[^"]*/([^"/]+)\.(?:step|wrl)"', text)
    if not m:
        return [], []
    wrl = os.path.join(os.path.dirname(PRETTY), "NexusFC.3dshapes", m.group(1) + ".wrl")
    if not os.path.exists(wrl):
        return [], []
    xs, ys = [], []
    for blk in re.findall(r"point\s*\[([^\]]*)\]", open(wrl).read()):
        nums = blk.replace(",", " ").split()
        for i in range(0, len(nums) - 2, 3):
            xs.append(float(nums[i]) * 2.54)
            ys.append(-float(nums[i + 1]) * 2.54)
    return xs, ys


# VRML bodies that are not aligned with their footprint; use the silk/fab outline instead
SILK_BODY = {"WSON-8_L8.0-W6.10-P1.27-BL-EP"}


def fix(path):
    if os.path.basename(path) == "TPS70933DBVR_TI_DBV0005A.kicad_mod":
        # Exact TI-derived lands/courtyard are owned by the main-only generator.
        # Reformatting this variant would break its guarded idempotence check.
        return False
    text = open(path).read()
    if not text.lstrip().startswith("(module"):
        return False                      # project-generated footprints are already correct
    px, py = pad_extents(text)
    name = os.path.basename(path)[:-len(".kicad_mod")]
    bx, by = graphic_extents(text) if name in SILK_BODY else model_extents(text)
    if not bx:
        bx, by = graphic_extents(text)
    xs, ys = px + bx, py + by
    x0, x1, y0, y1 = min(xs) - MARGIN, max(xs) + MARGIN, min(ys) - MARGIN, max(ys) + MARGIN
    lines = [l for l in text.splitlines() if "CrtYd" not in l]
    rect = [f"\t(fp_line (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y0:.3f}) (layer F.CrtYd) (width 0.05))",
            f"\t(fp_line (start {x1:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f}) (layer F.CrtYd) (width 0.05))",
            f"\t(fp_line (start {x1:.3f} {y1:.3f}) (end {x0:.3f} {y1:.3f}) (layer F.CrtYd) (width 0.05))",
            f"\t(fp_line (start {x0:.3f} {y1:.3f}) (end {x0:.3f} {y0:.3f}) (layer F.CrtYd) (width 0.05))"]
    i = next(k for k, l in enumerate(lines) if l.strip().startswith("(pad"))
    lines[i:i] = rect
    open(path, "w").write("\n".join(lines) + "\n")
    return True


if __name__ == "__main__":
    n = sum(fix(p) for p in sorted(glob.glob(os.path.join(PRETTY, "*.kicad_mod"))))
    print(f"courtyards rebuilt for {n} converted footprints")
