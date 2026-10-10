#!/usr/bin/env python3
"""Read-only saved-fill critical-reference geometry, including drills and IMU.

No copper is repaired, refilled or saved. A local antipad classification is an
explanation of a missing projection, never an electrical acceptance criterion.
"""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path

from shapely.geometry import GeometryCollection, Point, Polygon
from shapely.ops import unary_union
from check_signal_geometry import CRITICAL, I2C, EPS, centerline, copper_entries, pieces, poly, sha, validate_bindings

REFERENCE = {"F.Cu": "In1.Cu", "In2.Cu": "In1.Cu", "In3.Cu": "In4.Cu", "B.Cu": "In4.Cu"}
PLANES = ["In1.Cu", "In4.Cu"]
CLASSES = ["local_own_via_window_in_saved_hole", "drill_void_outside_own_window", "saved_void_or_edge_outside_own_window"]


def drill_layers(o, layers):
    if not o.get("drill"):
        return []
    # NPTH holes pass through this board; blind/buried plated holes only span
    # their exported native barrel layers. Never infer an all-layer via span.
    return layers if o.get("npth") else o.get("barrel_layers", [])


def ground_geometry(g, entries, drill_side="outside"):
    drills = {l: [] for l in g["copper_layers"]}
    for o in g["objects"]:
        for l in drill_layers(o, g["copper_layers"]):
            drills[l].append(poly(o["drill"][drill_side]))
    cuts = {l: unary_union(v) for l, v in drills.items()}
    raw, zone, physical = {}, {}, {}
    for l in PLANES:
        raw[l] = unary_union([e["shape"] for e in entries if e["net"] == "GND" and e["layer"] == l])
        zone[l] = unary_union([e["shape"] for e in entries if e["net"] == "GND" and e["layer"] == l and e["kind"] == "zone"])
        physical[l] = raw[l].difference(cuts[l])
    return raw, zone, physical, cuts


def ground_ties(g, zones, cuts):
    ties, rejected = [], []
    for o in g["objects"]:
        if o["net"] != "GND" or not o.get("plated") or not o.get("drill"):
            continue
        contacts = {}
        for l in PLANES:
            land = poly(o["copper"].get(l, []))
            # Use saved ZONE copper, excluding every drill, not a union that
            # includes this same land. A mere tangent has zero contact area.
            contacts[l] = land.difference(cuts[l]).intersection(zones[l].difference(cuts[l])).area
        spans = all(l in o.get("barrel_layers", []) for l in PLANES)
        item = {"uuid": o["uuid"], "kind": o["kind"], "label": o.get("key"),
                "xy_mm": o.get("xy", o.get("start")), "barrel_layers": o.get("barrel_layers", []),
                "drill_mm": {k: o["drill"][k] for k in ["start", "end", "width"]},
                "positive_saved_zone_contact_area_mm2": contacts,
                "barrel_spans_both_reference_planes": spans}
        (ties if spans and all(a > 1e-10 for a in contacts.values()) else rejected).append(item)
    return ties, rejected


def local_masks(g, meta, zones):
    holes = {l: [Polygon(h) for p in pieces(zones[l], "Polygon") for h in p.interiors] for l in PLANES}
    masks, facts = {}, {}
    for v in g["objects"]:
        if v["kind"] != "via" or v["net"] not in meta["nets"]:
            continue
        for l in PLANES:
            if l not in v.get("barrel_layers", []) or l not in v["width_by_layer"]:
                continue
            own = meta["nets"][v["net"]]["via_own_clearance_by_layer_mm"][v["uuid"]][l]
            zone_clear = max([x["local_clearance_mm"] for x in meta["ground_zone_clearances"] if l in x["layers"]] + [0])
            radius = v["width_by_layer"][l] / 2 + max(own, zone_clear) + 2 * meta["native_design_max_error_mm"]
            window = Point(v["xy"]).buffer(radius, quad_segs=96)
            containing = [(i, h) for i, h in enumerate(holes[l]) if h.covers(Point(v["xy"]))]
            masks[v["uuid"], l] = window.intersection(unary_union([h for _, h in containing]))
            facts[v["uuid"], l] = {"via_uuid": v["uuid"], "via_xy_mm": v["xy"],
                "local_window_radius_mm": radius, "nominal_land_radius_mm": v["width_by_layer"][l] / 2,
                "via_own_clearance_mm": own, "maximum_ground_zone_clearance_mm": zone_clear,
                "classification_allowance_mm": 2 * meta["native_design_max_error_mm"],
                "saved_holes": [{"hole_index": i, "bounds_mm": list(h.bounds), "area_mm2": h.area,
                    "extends_beyond_local_window": not window.covers(h),
                    "contained_vias": [{"uuid": x["uuid"], "net": x["net"], "xy_mm": x["xy"]}
                                       for x in g["objects"] if x["kind"] == "via" and l in x.get("barrel_layers", []) and h.covers(Point(x["xy"]))]}
                                 for i, h in containing]}
    return masks, facts, holes


def partition_missing(missing, own_masks, drill_cut):
    """Disjoint, conservative labels; all outside-window merged void remains."""
    mask = unary_union(own_masks)
    own = missing.intersection(mask)
    rest = missing.difference(mask)
    drilled = rest.intersection(drill_cut)
    other = rest.difference(drill_cut)
    return dict(zip(CLASSES, [own, drilled, other]))


def describe_missing(shape, kind, holes, g, reference):
    rows = []
    for part in pieces(shape, kind):
        measure = part.length if kind == "LineString" else part.area
        if measure <= (EPS if kind == "LineString" else 1e-10):
            continue
        holes_hit = [i for i, h in enumerate(holes) if part.intersection(h).length > EPS or part.intersection(h).area > 1e-10]
        drills_hit = [{"uuid": o["uuid"], "net": o["net"], "kind": o["kind"], "label": o.get("key"),
                       "start_mm": o["drill"]["start"], "end_mm": o["drill"]["end"], "width_mm": o["drill"]["width"]}
                      for o in g["objects"] if reference in drill_layers(o, g["copper_layers"])
                      and part.intersects(poly(o["drill"]["outside"]))]
        row = {"length_mm" if kind == "LineString" else "area_mm2": measure,
               "bounds_mm": list(part.bounds), "saved_hole_indices": holes_hit, "intersecting_drills": drills_hit}
        if kind == "LineString":
            row["coordinates_mm"] = [list(x) for x in part.coords]
        else:
            row["outer_mm"] = [list(x) for x in part.exterior.coords]
            row["holes_mm"] = [[list(x) for x in h.coords] for h in part.interiors]
        rows.append(row)
    return rows


def review(g, meta):
    entries = copper_entries(g)
    raw, zones, physical, cuts = ground_geometry(g, entries)
    _, _, physical_inside, _ = ground_geometry(g, entries, "inside")
    ties, rejected = ground_ties(g, zones, cuts)
    masks, facts, holes = local_masks(g, meta, zones)
    target_nets = list(I2C) + CRITICAL
    rows, transitions, unsupported = [], [], []
    for v in g["objects"]:
        if v["kind"] != "via" or v["net"] not in target_nets:
            continue
        attached = []
        for t in g["objects"]:
            if t["net"] != v["net"] or t["kind"] not in ["track", "arc"]:
                continue
            l = next(iter(t["copper"]))
            if l in v["copper"] and poly(t["copper"][l]).intersection(poly(v["copper"][l])).area > 1e-10:
                attached.append({"track_uuid": t["uuid"], "layer": l,
                                 "centerline_endpoint_at_via_center": any(math.dist(x, v["xy"]) < EPS for x in [t["start"], t["end"]])})
        neighbors = sorted([t | {"center_distance_mm": math.dist(t["xy_mm"], v["xy"])} for t in ties],
                           key=lambda t: (t["center_distance_mm"], t["uuid"]))
        nearest_vias = [t for t in neighbors if t["kind"] == "via"]
        transitions.append({"net": v["net"], "via_uuid": v["uuid"], "xy_mm": v["xy"],
                            "barrel_layers": v["barrel_layers"], "attached_tracks": attached,
                            "connected_signal_layers": sorted({t["layer"] for t in attached}),
                            "nearest_GND_via_with_saved_zone_contact_both_planes": nearest_vias[0] if nearest_vias else None,
                            "nearest_GND_plated_tie_with_saved_zone_contact_both_planes": neighbors[0] if neighbors else None})
    for t in g["objects"]:
        if t["net"] not in target_nets or t["kind"] not in ["track", "arc"]:
            continue
        l = next(iter(t["copper"])); r = REFERENCE.get(l)
        if r is None:
            unsupported.append({"uuid": t["uuid"], "net": t["net"], "signal_layer": l}); continue
        line, copper = centerline(t), poly(t["copper"][l])
        own_keys = [(v["uuid"], r) for v in g["objects"] if v["kind"] == "via" and v["net"] == t["net"] and (v["uuid"], r) in masks]
        own_masks = [masks[k] for k in own_keys]
        missing_line, missing_width = line.difference(physical[r]), copper.difference(physical[r])
        line_parts = partition_missing(missing_line, own_masks, cuts[r])
        width_parts = partition_missing(missing_width, own_masks, cuts[r])
        if abs(sum(x.length for x in line_parts.values()) - missing_line.length) > EPS or abs(sum(x.area for x in width_parts.values()) - missing_width.area) > 1e-9:
            raise ValueError("Critical reference partition failed conservation: " + repr((t["uuid"], t["net"], missing_line.length, sum(x.length for x in line_parts.values()), missing_width.area, sum(x.area for x in width_parts.values()))))
        rows.append({"track_uuid": t["uuid"], "net": t["net"], "signal_layer": l, "reference_layer": r,
            "start_mm": t["start"], "end_mm": t["end"], "width_mm": t["width"],
            "raw_GND_centerline_missing_mm": line.difference(raw[r]).length,
            "raw_GND_trace_width_missing_mm2": copper.difference(raw[r]).area,
            "physical_GND_centerline_missing_mm": missing_line.length,
            "physical_GND_trace_width_missing_mm2": missing_width.area,
            "drill_polygon_envelope_uncertainty_centerline_mm": missing_line.length - line.difference(physical_inside[r]).length,
            "drill_polygon_envelope_uncertainty_area_mm2": missing_width.area - copper.difference(physical_inside[r]).area,
            "local_own_windows_intersecting_missing": [facts[k] for k in own_keys if missing_line.intersects(masks[k]) or missing_width.intersects(masks[k])],
            "centerline_missing_by_class": {c: describe_missing(x, "LineString", holes[r], g, r) for c, x in line_parts.items()},
            "trace_width_missing_by_class": {c: describe_missing(x, "Polygon", holes[r], g, r) for c, x in width_parts.items()}})
    totals = {}
    for net in target_nets:
        rs = [x for x in rows if x["net"] == net]
        native = meta["nets"][net]
        totals[net] = {"native_complete": native["all_native_copper_connected"], "all_terminals_connected": native["all_terminals_connected"],
            "native_planar_length_mm": sum(native["track_native_lengths_mm"].values()), "track_count": len(rs),
            **{k: sum(r[k] for r in rs) for k in ["raw_GND_centerline_missing_mm", "raw_GND_trace_width_missing_mm2", "physical_GND_centerline_missing_mm", "physical_GND_trace_width_missing_mm2", "drill_polygon_envelope_uncertainty_centerline_mm", "drill_polygon_envelope_uncertainty_area_mm2"]},
            "physical_missing_centerline_mm_by_class": {c: sum(p["length_mm"] for r in rs for p in r["centerline_missing_by_class"][c]) for c in CLASSES},
            "physical_missing_trace_width_mm2_by_class": {c: sum(p["area_mm2"] for r in rs for p in r["trace_width_missing_by_class"][c]) for c in CLASSES}}
    return {"schema": "f722-critical-reference-geometry/v1", "board_sha256": meta["board_sha256"],
            "project_sha256": meta["project_sha256"], "native_version": meta["native_version"],
            "nets": totals, "tracks": rows, "transitions": transitions,
            "GND_ties": {"accepted": ties, "rejected": rejected}, "unsupported_tracks": unsupported,
            "saved_holes": {l: [{"hole_index": i, "bounds_mm": list(h.bounds), "area_mm2": h.area,
                "contained_vias": [{"uuid": v["uuid"], "net": v["net"], "xy_mm": v["xy"]} for v in g["objects"]
                                   if v["kind"] == "via" and l in v.get("barrel_layers", []) and h.covers(Point(v["xy"]))]}
                                  for i, h in enumerate(hs)] for l, hs in holes.items()},
            "method": ["Physical GND is the union of actual saved zone fills and GND lands/tracks minus native outside drill polygons on their actual spans; native inside drill polygons bound the drill approximation sensitivity.",
                       "GND ties require an actual plated hole spanning both reference layers and positive-area annular overlap with actual saved GND zone fill on each layer, after drill subtraction. A land intersecting itself cannot establish a tie.",
                       "Every straight/arc track is projected at its centerline and across its actual native copper width; the chosen adjacent reference is In1 for F/In2 and In4 for B/In3. Other layer tracks are explicitly unsupported.",
                       "Missing geometry is partitioned by same-net local via windows intersected with the actual saved hole containing each via, then remaining drill void, then all other remaining void or edge. Merged holes are never exempted as a whole.",
                       "Totals sum tracks, including overlaps at corners and inside pads. They are source-bound geometry screens, not a non-overlapping net area or route-path timing calculation."],
            "limits": ["No impedance, return-current inductance, timing, signal integrity, USB eye, oscillator, IMU performance or AC qualification is established.",
                       "Local own-window is a location classification, not proof that only its own via caused that gap. Hole memberships retain neighboring unrelated vias and all extensions outside the window remain counted.",
                       "Drill outside/inside contours have the exporter's 10 nm approximation envelope; saved native plane polygons keep their stored vertices. No invalid polygon repair or smoothing occurs.",
                       "Native electrical connectivity is independently reported; absence of centerline projection is not itself a connectivity fault. Incomplete I2C routes do not acquire zero-length or capacitance approval."]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", type=Path, required=True); ap.add_argument("--snapshot", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True); args = ap.parse_args()
    gp, mp = args.snapshot / "native-geometry.json", args.snapshot / "native-signals.json"
    g, m = json.loads(gp.read_text()), json.loads(mp.read_text())
    validate_bindings(g, m, sha(gp), sha(args.board))
    result = review(g, m)
    result["sources"] = {**m["sources"], "check_critical_reference.py": sha(__file__),
        "check_signal_geometry.py": sha(Path(__file__).with_name("check_signal_geometry.py")),
        "native-geometry.json": sha(gp), "native-signals.json": sha(mp)}
    validate_bindings(g, m, sha(gp), sha(args.board))
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"board_sha256": result["board_sha256"], "nets": result["nets"], "accepted_ties": len(result["GND_ties"]["accepted"]), "rejected_ties": len(result["GND_ties"]["rejected"])}, indent=2))

if __name__ == "__main__":
    main()
