#!/usr/bin/env python3
"""Native geometric through-via escape diagnostic, not routing or board editing."""
import collections
import argparse
import hashlib
import json
import math
import time
from pathlib import Path

import shapely
from shapely import unary_union
from shapely.geometry import Polygon, Point, box

ROOT = Path(__file__).resolve().parents[2]
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", type=Path, default=ROOT / "model-candidate05-ready/native.json")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_suffix(".json"))
    ARGS = parser.parse_args()
SOURCE = ARGS.native if __name__ == "__main__" else ROOT / "model-candidate05-ready/native.json"
N = json.loads(SOURCE.read_text())
QUAD = 64
FACTOR = 1 / math.cos(math.pi / (4 * QUAD))
TRACE_HALF = .0635
VIA_RADIUS = .225
DRILL_RADIUS = .1


def geom(ps):
    shapes = [Polygon(p["outer"], p.get("holes", [])) for p in ps]
    assert all(s.is_valid for s in shapes), "Native geometry invalid; no repair allowed"
    result = unary_union(shapes)
    assert result.is_valid
    return result


def parts(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [p for child in g.geoms for p in parts(child)]


OUTLINE = geom(N["outline_with_npth"]["polygons"])
SOURCE_OBJECTS = []
for o in N["objects"]:
    label = o.get("key", o["uuid"])
    copper = {layer: geom(ps) for layer, ps in o["copper"].items()}
    masks = [geom(m["polygons"]) for m in o.get("mask", {}).values()] if o.get("smd") else []
    drill = geom(o["drill"]["outside"]) if o.get("drill") else None
    SOURCE_OBJECTS.append((o, label, copper, masks, drill))


def audit(net, layer):
    started = time.monotonic()
    trace_obstacles = []
    via_obstacles = []
    targets = {}
    skipped = []
    for o, label, copper, masks, drill in SOURCE_OBJECTS:
        if o["kind"] == "pad" and o["net"] == net:
            targets[label] = geom(o["inside"][layer]).buffer(-TRACE_HALF, quad_segs=QUAD)
        if o["net"] != net:
            if layer in copper:
                trace_obstacles.append((label, "foreign_copper", copper[layer], .127 + TRACE_HALF))
            if copper:
                via_obstacles.append((label, "foreign_copper_all_layers", unary_union(list(copper.values())), .127 + VIA_RADIUS))
        for mask in masks:
            via_obstacles.append((label, "all_smt_masks_both_faces", mask, .20 + DRILL_RADIUS))
        if drill is not None:
            via_obstacles.append((label, "all_drills_no_net_exception", drill, .25 + DRILL_RADIUS))
            if o.get("npth"):
                trace_obstacles.append((label, "npth_copper", drill, .254 + TRACE_HALF))
                via_obstacles.append((label, "npth_copper", drill, .254 + VIA_RADIUS))
    for z in N["zones"]:
        if z["rule"]:
            g = geom(z["outline"])
            if layer in z["layers"] and (z["forbid"]["tracks"] or z["forbid"]["copper"]):
                trace_obstacles.append((z["uuid"], "rule_copper_track", g, TRACE_HALF))
            if z["layers"] and (z["forbid"]["vias"] or z["forbid"]["copper"]):
                via_obstacles.append((z["uuid"], "rule_copper_via", g, VIA_RADIUS))
        elif z["net"] == "GND" and set(z["layers"]) <= {"In1.Cu", "In4.Cu"}:
            skipped.append(z["uuid"])
        elif z["net"] != net:
            for l, ps in z["filled"].items():
                g = geom(ps)
                if l == layer:
                    trace_obstacles.append((z["uuid"], "zone_copper", g, .127 + TRACE_HALF))
                via_obstacles.append((z["uuid"], "zone_copper_all_layers", g, .127 + VIA_RADIUS))
    result = {"net": net, "layer": layer, "excluded_regenerable_gnd_zone_ids": skipped, "trace_obstacle_count": len(trace_obstacles), "via_obstacle_count": len(via_obstacles), "via_obstacle_category_counts": dict(collections.Counter(o[1] for o in via_obstacles))}
    for mode, factor, extra in [("optimistic_native", 1., 0.), ("conservative_native", FACTOR, .000002)]:
        trace_occ = unary_union([g.buffer(d * factor + extra, quad_segs=QUAD) for _, _, g, d in trace_obstacles])
        trace_free = OUTLINE.buffer(-((.254 + TRACE_HALF) * factor + extra), quad_segs=QUAD).difference(trace_occ)
        via_occ = unary_union([g.buffer(d * factor + extra, quad_segs=QUAD) for _, _, g, d in via_obstacles])
        via_free = OUTLINE.buffer(-((.254 + VIA_RADIUS) * factor + extra), quad_segs=QUAD).difference(via_occ)
        assert trace_free.is_valid and via_free.is_valid
        components = parts(trace_free)
        report = {}
        for label, target in targets.items():
            hits = [g for g in components if g.intersection(target).area > 1e-12]
            region = unary_union(hits).intersection(via_free)
            entry = {"target_area_mm2": target.area, "legal_target_area_mm2": target.intersection(trace_free).area, "trace_component_area_mm2": sum(g.area for g in hits), "legal_via_region_area_mm2": region.area, "legal_via_region_component_count": len(parts(region)), "via_center_exists": region.area > 1e-12}
            if entry["via_center_exists"]:
                # Retain a robust witness in the largest region, plus a nearer candidate.
                chosen = max(parts(region), key=lambda g: g.area)
                p = chosen.representative_point()
                candidates = [(p.distance(g) - d, label2, category) for label2, category, g, d in via_obstacles]
                candidates.append((p.distance(OUTLINE.boundary) - (.254 + VIA_RADIUS), "board-outline-including-npth", "edge_npth_copper"))
                candidates.sort()
                assert candidates[0][0] >= -1e-9, "Witness violates a native exact distance"
                entry["witness_mm"] = [p.x, p.y]
                entry["witness_minimum_extra_clearance_mm"] = candidates[0][0]
                entry["witness_nearest_constraints"] = [{"extra_clearance_mm": d, "object": ob, "category": cat} for d, ob, cat in candidates[:5]]
                for radius in [1., 2., 4., 8.]:
                    local = region.intersection(box(*target.bounds).buffer(radius, join_style="mitre"))
                    if local.area <= 1e-12:
                        continue
                    q = max(parts(local), key=lambda g: g.area).representative_point()
                    margin = min([q.distance(g) - d for _, _, g, d in via_obstacles] + [q.distance(OUTLINE.boundary) - (.254 + VIA_RADIUS)])
                    assert margin >= -1e-9
                    entry["local_witness"] = {"xy_mm": [q.x, q.y], "target_box_extension_mm": radius, "minimum_extra_clearance_mm": margin}
                    break
                if sum(g.area for g in hits) < 10:
                    entry["legal_via_regions"] = [{"area_mm2": g.area, "bounds_mm": list(g.bounds), "distance_to_target_mm": g.distance(target)} for g in parts(region)]
            report[label] = entry
        result[mode] = report
    result["seconds"] = time.monotonic() - started
    print(json.dumps(result), flush=True)
    return result


if __name__ == "__main__":
    receipt = {
        "board_sha256": N["board_sha256"],
        "native_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "native_polygon_max_error_mm": N["maximum_polygon_error_mm"],
        "shapely_version": shapely.__version__,
        "rules_mm": {"trace_width": .127, "via_diameter": .45, "via_drill": .20, "copper_gap": .127, "drill_mask_gap": .20, "drill_drill_gap": .25, "edge_npth_copper_gap": .254},
        "scope": "Full native board free-space diagnostic only. No geometry repair, route search, board/model edits or engine acceptance claim. All six layers retain native copper; only In1/In4 regenerable GND fills excluded. SMT mask and drill obstacles have no same-net exception.",
        "results": [audit("ADC_DIV_MID", "F.Cu"), audit("FLASH_WP_N", "B.Cu")],
    }
    ARGS.output.write_text(json.dumps(receipt, indent=2) + "\n")
