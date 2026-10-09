#!/usr/bin/env python3
"""Read-only native snapshot free-space diagnostic; never emits board routes."""
import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path

import shapely
from shapely.geometry import Polygon, box, Point
from shapely import unary_union

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "model-candidate05-ready/native.json"
NATIVE = json.loads(SOURCE.read_text())
MODEL = json.loads((ROOT / "model-candidate05-ready/model.json").read_text())
MUTABLE = set(MODEL["mutable_source_ids"])
NATIVE_OBJECTS = {o.get("key", o["uuid"]): o for o in NATIVE["objects"]}
HALF = .0635
CLEAR = .127
EDGE = .254
SEGMENTS = 64
COS = math.cos(math.pi / (4 * SEGMENTS))


def geom(polygons):
    shapes = [Polygon(p["outer"], p.get("holes", [])) for p in polygons]
    assert all(g.is_valid for g in shapes), "Invalid native polygon; no repairs allowed"
    result = unary_union(shapes)
    assert result.is_valid
    return result


def components(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [p for part in g.geoms for p in components(part)]


def run(net, layer, window):
    started = time.monotonic()
    pads = [o for o in NATIVE["objects"] if o["kind"] == "pad" and o["net"] == net]
    targets = {p["key"]: geom(p["inside"][layer]).buffer(-HALF, quad_segs=SEGMENTS) for p in pads}
    outline = geom(NATIVE["outline_with_npth"]["polygons"])
    bounds = box(*window)
    objects = []
    foreign = []
    for o in NATIVE["objects"]:
        if o["net"] != net and layer in o["copper"]:
            g = geom(o["copper"][layer])
            if g.distance(bounds) <= CLEAR + HALF:
                objects.append((o.get("key", o["uuid"]), g, CLEAR + HALF))
                foreign.append((o.get("key", o["uuid"]), o["net"], g))
        if o["kind"] == "pad" and o["npth"] and o["drill"]:
            g = geom(o["drill"]["outside"])
            if g.distance(bounds) <= EDGE + HALF:
                objects.append((o["uuid"] + ":npth", g, EDGE + HALF))
    for z in NATIVE["zones"]:
        if z["rule"] and layer in z["layers"] and (z["forbid"]["tracks"] or z["forbid"]["copper"]):
            objects.append((z["uuid"] + ":rule", geom(z["outline"]), HALF))
        elif not z["rule"] and z["net"] != net and layer in z["filled"]:
            objects.append((z["uuid"] + ":filled", geom(z["filled"][layer]), CLEAR + HALF))
    result = {"net": net, "layer": layer, "window_mm": window, "obstacle_count": len(objects)}
    for mode, factor in [("optimistic_native_polygon_bound", 1.0), ("conservative_native_polygon_bound", 1 / COS)]:
        occupied = unary_union([g.buffer(d * factor, quad_segs=SEGMENTS) for _, g, d in objects])
        free = outline.buffer(-(EDGE + HALF) * factor, quad_segs=SEGMENTS).intersection(bounds).difference(occupied)
        assert free.is_valid, "Invalid result; no repairs allowed"
        pieces = components(free)
        target_report = {}
        target_component_sets = []
        for name, target in targets.items():
            hit = [i for i, p in enumerate(pieces) if target.intersection(p).area > 1e-12]
            target_component_sets.append(set(hit))
            target_report[name] = {
                "target_area_mm2": target.area,
                "legal_target_area_mm2": target.intersection(free).area,
                "free_component_ids": hit,
                "components": [{"id": i, "area_mm2": pieces[i].area, "bounds_mm": list(pieces[i].bounds), "reaches_window_boundary": pieces[i].distance(bounds.boundary) < 1e-9} for i in hit],
            }
            for component in target_report[name]["components"]:
                if component["area_mm2"] >= 10:
                    continue
                borders = []
                for label, g, d in objects:
                    if g.distance(pieces[component["id"]]) <= d * factor + 1e-7:
                        source = NATIVE_OBJECTS.get(label, {})
                        borders.append({"object": label, "net": source.get("net"), "kind": source.get("kind", "region"), "mutable_source": source.get("uuid") in MUTABLE})
                component["boundary_net_counts"] = dict(Counter(b["net"] for b in borders))
                component["boundary_mutable_count"] = sum(b["mutable_source"] for b in borders)
                if component["area_mm2"] < 10:
                    component["boundary_objects"] = borders
        common = sorted(set.intersection(*target_component_sets))
        result[mode] = {"component_count": len(pieces), "same_component": bool(common), "common_component_ids": common, "targets": target_report}
    result["nearest_foreign_to_targets"] = {
        name: [{"object": label, "net": other_net, "distance_from_target_mm": g.distance(target)} for label, other_net, g in sorted(foreign, key=lambda row: row[2].distance(target))[:8]]
        for name, target in targets.items()
    }
    result["seconds"] = time.monotonic() - started
    print(json.dumps({"net": net, "window": window, "seconds": result["seconds"], "bounds": {mode: result[mode] for mode in ["optimistic_native_polygon_bound", "conservative_native_polygon_bound"]}}), flush=True)
    return result


receipt = {
    "native_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "board_sha256": NATIVE["board_sha256"],
    "native_polygon_max_error_mm": NATIVE["maximum_polygon_error_mm"],
    "shapely_version": shapely.__version__,
    "scope": "All extant native foreign-net copper, actual filled zones on tested layers, track/copper keepouts, board edge and NPTH; no route generation, no geometry repair, no model or board changes.",
    "trace_halfwidth_mm": HALF,
    "foreign_clearance_mm": CLEAR,
    "foreign_centerline_reserve_mm": CLEAR + HALF,
    "edge_npth_centerline_reserve_mm": EDGE + HALF,
    "buffer_quad_segments": SEGMENTS,
    "conservative_radius_factor": 1 / COS,
    "results": [run("ADC_DIV_MID", "F.Cu", [20.74, 14.24, 28.12, 19.92]), run("FLASH_WP_N", "B.Cu", [24.965, 19.115, 33.275, 25.4]), run("ADC_DIV_MID", "F.Cu", [0, 0, 41.66, 25.4]), run("FLASH_WP_N", "B.Cu", [0, 0, 41.66, 25.4])],
}
Path(__file__).with_suffix(".json").write_text(json.dumps(receipt, indent=2) + "\n")
