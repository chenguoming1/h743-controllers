#!/usr/bin/env python3
"""Narrow, source-bound signal topology/reference and conditional loading screen.

Use Python with Shapely, after export_signal_snapshot.py. Never writes a PCB.
Exit 2 means a final I2C estimate is refused/pending; it is expected on WIP.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import heapq
import json
import math
from pathlib import Path

import shapely
from shapely.geometry import GeometryCollection, LineString, Point, Polygon
from shapely.ops import unary_union

I2C = {"BARO_SCL": ["U1.61", "U4.4", "R7.2"], "BARO_SDA": ["U1.62", "U4.3", "R8.2"]}
CRITICAL = ["USB_P", "USB_N", "HSE_IN", "HSE_OUT", "HSE_XTAL_OUT"]
EPS = 0.000001  # 1 nm endpoint key/roundoff; not a copper gap closure.


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_bindings(g, meta, geometry_sha, board_sha):
    if geometry_sha != meta["geometry_sha256"] or g["board_sha256"] != meta["board_sha256"] or not meta["source_unchanged"]:
        raise ValueError("Native source binding mismatch")
    if board_sha != meta["board_sha256"]:
        raise ValueError("Board changed after the native snapshot; re-export")


def poly(rows):
    parts = [Polygon(x["outer"], x.get("holes", [])) for x in rows]
    if not all(x.is_valid for x in parts):
        raise ValueError("Invalid exact native contour; no buffer/repair allowed")
    return unary_union(parts)


def pieces(g, kind="LineString"):
    if g.is_empty:
        return []
    if g.geom_type == kind:
        return [g]
    if hasattr(g, "geoms"):
        return [p for x in g.geoms for p in pieces(x, kind)]
    return []


def centerline(o):
    if o["kind"] == "track":
        return LineString([o["start"], o["end"]])
    if o["kind"] != "arc":
        raise ValueError("Not a track")
    # Used for reference projection only; detailed topology/model refuses arcs.
    a, m, b = o["start"], o["mid"], o["end"]
    ax, ay = a; mx, my = m; bx, by = b
    d = 2 * (ax * (my - by) + mx * (by - ay) + bx * (ay - my))
    if abs(d) < 1e-16:
        raise ValueError("Degenerate native arc")
    aa, mm, bb = ax * ax + ay * ay, mx * mx + my * my, bx * bx + by * by
    cx = (aa * (my - by) + mm * (by - ay) + bb * (ay - my)) / d
    cy = (aa * (bx - mx) + mm * (ax - bx) + bb * (mx - ax)) / d
    r = math.dist(a, [cx, cy]); t0 = math.atan2(ay - cy, ax - cx)
    tm = (math.atan2(my - cy, mx - cx) - t0) % math.tau
    te = (math.atan2(by - cy, bx - cx) - t0) % math.tau
    sweep = te if tm <= te else te - math.tau
    steps = max(2, math.ceil(abs(sweep) / (2 * math.acos(max(-1, 1 - 0.00001 / r)))))
    return LineString([a] + [[cx + r * math.cos(t0 + sweep * i / steps),
                             cy + r * math.sin(t0 + sweep * i / steps)] for i in range(1, steps)] + [b])


def topology(objects, native):
    """Centerline tree outside pads/via lands, with native completeness separate."""
    tracks = [x for x in objects if x["kind"] in ["track", "arc"]]
    if any(x["kind"] == "arc" for x in tracks) or native["zone_uuids"]:
        return {"supported": False, "reason": "Arc or signal zone needs explicit topology extension"}
    anchors = [x for x in objects if x["kind"] in ["pad", "via"]]
    labels = {x["uuid"]: x["key"] for x in anchors if x["kind"] == "pad"}
    graph, vertices, edges = defaultdict(list), {}, []
    # Contract overlapping same-net pad/via lands on any common layer.
    parent = {x["uuid"]: x["uuid"] for x in anchors}
    def root(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for i, a in enumerate(anchors):
        for b in anchors[i + 1:]:
            if any(poly(a["copper"][l]).intersects(poly(b["copper"][l]))
                   for l in a["copper"].keys() & b["copper"].keys()):
                parent[root(a["uuid"])] = root(b["uuid"])
    for a in anchors:
        k = "anchor:" + root(a["uuid"])
        vertices.setdefault(k, {"anchor_uuids": [], "terminals": [], "xy_mm": a.get("xy", a.get("start"))})
        vertices[k]["anchor_uuids"].append(a["uuid"])
        if a["uuid"] in labels:
            vertices[k]["terminals"].append(labels[a["uuid"]])
    for layer in sorted({l for x in tracks for l in x["copper"]}):
        lands = [(x, poly(x["copper"][layer])) for x in anchors if layer in x["copper"]]
        land_union = unary_union([p for _, p in lands])
        local_tracks = [x for x in tracks if layer in x["copper"]]
        lines = [centerline(x) for x in local_tracks]
        for i, t in enumerate(local_tracks):
            cu = poly(t["copper"][layer])
            for anchor, shape in lands:
                if cu.intersects(shape) and lines[i].distance(shape) > EPS:
                    return {"supported": False, "reason": "Off-center trace/land contact requires explicit topology review", "track": t["uuid"], "anchor": anchor["uuid"]}
            for j in range(i + 1, len(local_tracks)):
                if lines[i].distance(lines[j]) <= EPS:
                    continue
                contact = cu.intersection(poly(local_tracks[j]["copper"][layer])).difference(land_union)
                if contact.area > EPS * EPS:
                    return {"supported": False, "reason": "Copper-only track junction requires explicit topology review", "tracks": [t["uuid"], local_tracks[j]["uuid"]]}
        noded = unary_union([piece for line in lines for piece in pieces(line.difference(land_union))])
        def node(xy):
            point = Point(xy)
            touching = [a for a, p in lands if p.distance(point) <= EPS]
            if touching:
                k = "anchor:" + root(touching[0]["uuid"])
            else:
                k = layer + ":" + ":".join(str(round(v / EPS)) for v in xy)
                vertices.setdefault(k, {"xy_mm": list(xy), "layer": layer, "terminals": []})
            return k
        for line in pieces(noded):
            a, b = node(line.coords[0]), node(line.coords[-1])
            if line.length <= EPS:
                continue
            eid = len(edges)
            edges.append({"id": eid, "a": a, "b": b, "layer": layer, "outside_land_length_mm": line.length})
            graph[a].append((b, line.length, eid)); graph[b].append((a, line.length, eid))
    nodes = set(vertices)
    comps = []
    while nodes:
        seen, todo = set(), [min(nodes)]
        while todo:
            x = todo.pop()
            if x in seen:
                continue
            seen.add(x); todo += [a for a, _, _ in graph[x]]
        nodes -= seen; comps.append(sorted(seen))
    branches = [{"node": k, "degree": len(graph[k]), **v} for k, v in vertices.items() if len(graph[k]) >= 3]
    stubs = [{"node": k, **v} for k, v in vertices.items() if len(graph[k]) == 1 and not v["terminals"]]
    term_nodes = {t: k for k, v in vertices.items() for t in v["terminals"]}
    result = {"supported": True, "component_count": len(comps), "cycle_rank": len(edges) - len(vertices) + len(comps),
              "native_all_copper_connected": native["all_native_copper_connected"],
              "native_all_terminals_connected": native["all_terminals_connected"],
              "branches": branches, "dangling_nonterminal_endpoints": stubs,
              "vertices": vertices, "edges": edges,
              "method": "Exact straight centerlines noded at intersections; pad/via-land copper contracted. Whole-net native lengths are reported separately and include in-land portions. No arbitrary gap snapping."}
    if native["all_native_copper_connected"] != (len(comps) == 1):
        result.update(supported=False, reason="Centerline/land graph disagrees with native copper connectivity; inspect off-center or tangential copper contacts")
    def path(src, dst):
        if src not in term_nodes or dst not in term_nodes:
            return None
        start, goal = term_nodes[src], term_nodes[dst]
        queue, dist, prev = [(0, start)], {start: 0}, {}
        while queue:
            d, x = heapq.heappop(queue)
            if d != dist[x]:
                continue
            if x == goal:
                break
            for y, length, e in graph[x]:
                nd = d + length
                if nd < dist.get(y, math.inf):
                    dist[y] = nd; prev[y] = (x, e); heapq.heappush(queue, (nd, y))
        if goal not in dist:
            return None
        out, nodes = [], [goal]
        while goal != start:
            goal, e = prev[goal]; out.append(e); nodes.append(goal)
        return {"source": src, "target": dst, "outside_land_length_mm": dist[term_nodes[dst]],
                "edge_ids": list(reversed(out)), "nodes": list(reversed(nodes))}
    terminals = native.get("required_terminals")
    if terminals:
        mcu, sensor, pullup = terminals
        paths = [path(mcu, sensor), path(mcu, pullup), path(sensor, pullup)]
        result["terminal_paths"] = paths
        if all(paths) and result["cycle_rank"] == 0 and len(comps) == 1:
            trunk = set(paths[0]["edge_ids"])
            branch = set(paths[1]["edge_ids"]) - trunk
            result["pullup_branch"] = {"terminal": pullup, "edge_ids": sorted(branch),
                                        "outside_land_length_mm": sum(edges[e]["outside_land_length_mm"] for e in branch),
                                        "definition": "Unique pull-up-to-MCU/sensor-trunk branch in a tree, excluding lengths inside pad/via copper. A pull-up on the trunk has zero branch length."}
    result["clean_complete_tree"] = bool(result["supported"] and len(comps) == 1 and not stubs and result["cycle_rank"] == 0 and native["all_native_copper_connected"])
    return result


def copper_entries(g):
    out = []
    for o in g["objects"]:
        for layer, rows in o["copper"].items():
            if rows:
                out.append({"uuid": o["uuid"], "kind": o["kind"], "net": o["net"],
                            "label": o.get("key"), "layer": layer, "shape": poly(rows)})
    for z in g["zones"]:
        if z["rule"]:
            continue
        for layer, rows in z["filled"].items():
            if rows:
                out.append({"uuid": z["uuid"], "kind": "zone", "net": z["net"],
                            "layer": layer, "shape": poly(rows)})
    return out


def geometry_rows(g, meta, entries, nets):
    layers = g["copper_layers"]
    grouped = defaultdict(list)
    for entry in entries:
        grouped[(entry["layer"], entry["net"])].append(entry["shape"])
    unions = {k: unary_union(v) for k, v in grouped.items()}
    rows = []
    for t in g["objects"]:
        if t["net"] not in nets or t["kind"] not in ["track", "arc"]:
            continue
        layer = next(iter(t["copper"])); line = centerline(t); copper = poly(t["copper"][layer]); index = layers.index(layer)
        adj = []
        for reference in layers[max(0, index - 1):index] + layers[index + 1:index + 2]:
            ground = unions.get((reference, "GND"), GeometryCollection())
            projected = []
            for (l, net), cu in unions.items():
                if l == reference and net != t["net"]:
                    overlap = line.intersection(cu).length
                    area = copper.intersection(cu).area
                    if overlap > EPS or area > 1e-10:
                        projected.append({"net": net, "centerline_overlap_mm": overlap, "copper_overlap_mm2": area})
            adj.append({"layer": reference, "GND_centerline_missing_mm": line.difference(ground).length,
                        "GND_copper_missing_mm2": copper.difference(ground).area,
                        "projected_copper_by_net": sorted(projected, key=lambda x: (-x["centerline_overlap_mm"], x["net"]))})
        nearby = []
        for e in entries:
            if e["layer"] == layer and e["net"] != t["net"]:
                d = copper.distance(e["shape"])
                nearby.append({k: v for k, v in e.items() if k != "shape"} | {"edge_gap_mm": d})
        nearby.sort(key=lambda x: (x["edge_gap_mm"], x["uuid"]))
        rows.append({"uuid": t["uuid"], "net": t["net"], "kind": t["kind"], "layer": layer,
                     "start_mm": t["start"], "end_mm": t["end"], "width_mm": t["width"],
                     "native_centerline_length_mm": meta["nets"][t["net"]]["track_native_lengths_mm"][t["uuid"]],
                     "adjacent_layers": adj, "nearest_unrelated_same_layer_copper": nearby[:3]})
    return rows


def usb_reference_intervals(g, meta, entries):
    """Explain every missing USB reference interval; never exempt a merged hole."""
    plane_layers = ["In1.Cu", "In4.Cu"]
    planes = {l: unary_union([e["shape"] for e in entries if e["layer"] == l and e["net"] == "GND"]) for l in plane_layers}
    zone_planes = {l: unary_union([e["shape"] for e in entries if e["layer"] == l and e["net"] == "GND" and e["kind"] == "zone"]) for l in plane_layers}
    holes = {l: [Polygon(ring) for p in pieces(zone_planes[l], "Polygon") for ring in p.interiors] for l in plane_layers}
    ties = []
    for o in g["objects"]:
        if o["net"] != "GND" or not o.get("plated"):
            continue
        if all(l in o["copper"] and poly(o["copper"][l]).intersects(planes[l]) for l in plane_layers):
            ties.append({"uuid": o["uuid"], "kind": o["kind"], "label": o.get("key"), "xy_mm": o.get("xy", o.get("start"))})
    all_vias = [o for o in g["objects"] if o["kind"] == "via"]
    windows, transitions = {}, []
    for v in all_vias:
        if v["net"] not in ["USB_P", "USB_N"]:
            continue
        neighbors = sorted([x | {"distance_mm": math.dist(v["xy"], x["xy_mm"])} for x in ties], key=lambda x: (x["distance_mm"], x["uuid"]))
        via_neighbors = [x for x in neighbors if x["kind"] == "via"]
        transitions.append({"net": v["net"], "via_uuid": v["uuid"], "xy_mm": v["xy"],
                            "nearest_GND_via_tying_In1_In4": via_neighbors[0] if via_neighbors else None,
                            "nearest_GND_plated_tie_In1_In4": neighbors[0] if neighbors else None})
        for l in plane_layers:
            own = meta["nets"][v["net"]]["via_own_clearance_by_layer_mm"][v["uuid"]][l]
            zone = max([x["local_clearance_mm"] for x in meta["ground_zone_clearances"] if l in x["layers"]] + [0])
            radius = v["width_by_layer"][l] / 2 + max(own, zone) + 2 * meta["native_design_max_error_mm"]
            containing = [h for h in holes[l] if h.covers(Point(v["xy"]))]
            windows[(v["uuid"], l)] = (Point(v["xy"]).buffer(radius, quad_segs=96), containing,
                {"via_uuid": v["uuid"], "via_xy_mm": v["xy"], "local_window_radius_mm": radius,
                 "nominal_via_land_radius_mm": v["width_by_layer"][l] / 2,
                 "own_clearance_mm": own, "zone_clearance_mm": zone,
                 "polygon_classification_allowance_mm": 2 * meta["native_design_max_error_mm"]})
    intervals, unsupported_tracks = [], []
    for t in g["objects"]:
        if t["net"] not in ["USB_P", "USB_N"] or t["kind"] not in ["track", "arc"]:
            continue
        l = next(iter(t["copper"])); reference = {"F.Cu": "In1.Cu", "B.Cu": "In4.Cu"}.get(l)
        if not reference:
            unsupported_tracks.append({"uuid": t["uuid"], "layer": l, "net": t["net"]})
            continue
        missing = centerline(t).difference(planes[reference])
        for part in pieces(missing):
            if part.length <= EPS:
                continue
            remainder = part
            for v in [x for x in all_vias if x["net"] == t["net"]]:
                window, containing, facts = windows[(v["uuid"], reference)]
                # Restrict to both the small local window AND an actual saved
                # zone hole containing that via. Never exempt the whole hole.
                mask = window.intersection(unary_union(containing))
                local = remainder.intersection(mask)
                for piece in pieces(local):
                    if piece.length <= EPS:
                        continue
                    hole = next(h for h in containing if h.intersects(piece))
                    contained_vias = [{"uuid": x["uuid"], "net": x["net"]} for x in all_vias if hole.covers(Point(x["xy"]))]
                    transition = next(x for x in transitions if x["via_uuid"] == v["uuid"])
                    intervals.append({"net": t["net"], "track_uuid": t["uuid"], "signal_layer": l, "reference_layer": reference,
                         "classification": "local_own_via_antipad_interval", "length_mm": piece.length,
                         "coordinates_mm": [list(x) for x in piece.coords], **facts,
                         "containing_void": {"bounds_mm": list(hole.bounds), "area_mm2": hole.area,
                                             "contained_vias": contained_vias,
                                             "extends_beyond_local_window": not window.covers(hole)},
                         "nearest_GND_via_tying_In1_In4": transition["nearest_GND_via_tying_In1_In4"]})
                remainder = remainder.difference(mask)
            for piece in pieces(remainder):
                if piece.length <= EPS:
                    continue
                intervals.append({"net": t["net"], "track_uuid": t["uuid"], "signal_layer": l, "reference_layer": reference,
                                  "classification": "plane_edge_void_or_crossing_outside_local_via_window",
                                  "length_mm": piece.length, "coordinates_mm": [list(x) for x in piece.coords]})
    totals = {n: {c: sum(x["length_mm"] for x in intervals if x["net"] == n and x["classification"] == c)
                  for c in ["local_own_via_antipad_interval", "plane_edge_void_or_crossing_outside_local_via_window"]}
              for n in ["USB_P", "USB_N"]}
    for net in totals:
        actual = sum(centerline(t).difference(planes[{"F.Cu": "In1.Cu", "B.Cu": "In4.Cu"}[next(iter(t["copper"]))]]).length
                     for t in g["objects"] if t["net"] == net and t["kind"] in ["track", "arc"]
                     and next(iter(t["copper"])) in ["F.Cu", "B.Cu"])
        if abs(actual - sum(totals[net].values())) > EPS:
            raise ValueError("USB interval classification failed length conservation")
    return {"totals_mm": totals, "intervals": intervals, "transitions": transitions,
            "unsupported_tracks": unsupported_tracks,
            "method": "Each missing interval is split by the intersection of its actual containing native zone hole and a small own-via window (land radius + max native via/zone clearance + twice native polygon error). Merged-hole extensions receive no blanket exemption. Ground ties geometrically contact both saved GND planes.",
            "limits": "Local antipad classification explains the gap; it does not prove adequate return inductance, impedance or USB compliance. Distances are geometric, with no asserted universal maximum."}


def validate_profile(profile, meta):
    missing = []
    if not profile:
        return ["No model-input profile supplied"]
    if profile.get("native_stackup_sha256") != meta["stackup"]["native_block_sha256"]:
        missing.append("Profile does not bind this exact native stackup")
    if profile.get("reviewed_engineering_assumptions") is not True:
        missing.append("Document and review the engineering assumptions")
    for name in ["epsilon_r_max", "signal_edge_growth_mm", "foreign_edge_growth_mm", "relative_layer_registration_mm",
                 "probe_capacitance_pF", "additional_model_allowance_pF", "unmodeled_external_copper_min_distance_mm"]:
        x = profile.get(name)
        if not isinstance(x, (float, int)) or not math.isfinite(x) or x < 0 or (name in ["epsilon_r_max", "unmodeled_external_copper_min_distance_mm"] and x == 0):
            missing.append("Missing/invalid " + name)
    if profile.get("epsilon_r_max", 0) and profile["epsilon_r_max"] < 1:
        missing.append("epsilon_r_max must cover every dielectric, mask, coating and air")
    if profile.get("epsilon_r_max", 0) and profile["epsilon_r_max"] < max([x.get("epsilon_r", 1) for x in meta["stackup"]["layers"]] + [1]):
        missing.append("epsilon_r_max is below a native nominal dielectric value")
    for row in meta["stackup"]["layers"]:
        if row["type"] == "copper" or row["name"].startswith("dielectric"):
            values = profile.get("thickness_bounds_mm", {}).get(row["name"], {})
            lo, hi = values.get("min"), values.get("max")
            if not isinstance(lo, (float, int)) or not isinstance(hi, (float, int)) or not 0 < lo <= row["thickness"] <= hi:
                missing.append("Missing/invalid min/max thickness: " + row["name"])
    evidence = profile.get("evidence", {})
    for name in ["dielectric_bound", "thickness_bounds", "etch_registration", "probe", "external_copper", "assembly_allocation"]:
        if not isinstance(evidence.get(name), str) or not evidence[name].strip():
            missing.append("Missing evidence/explicit engineering rationale: " + name)
    return missing


def sphere_cap_pf(a, b, er):
    """Exact concentric sphere C with a,b in mm; upper-bound trial energy."""
    if not 0 < a < b:
        raise ValueError("Enclosing sphere intersects the conservatively nearest foreign conductor")
    return 4 * math.pi * 8.8541878128e-3 * er * a * b / (b - a)


def route_capacitance(objects, entries, meta, profile):
    """Conditional geometric upper bound via a covering of enclosing spheres.

    No generic pF/mm assumption, FEM, pin capacitance claim or solder mask credit.
    """
    if any(o["kind"] not in ["pad", "track", "via"] for o in objects):
        raise ValueError("Only native straight tracks and ordinary vias are supported")
    net = objects[0]["net"]
    foreign = {l: unary_union([e["shape"] for e in entries if e["layer"] == l and e["net"] != net])
               for l in {e["layer"] for e in entries}}
    bounds = profile["thickness_bounds_mm"]
    z, zmin, thickness = 0., {}, {}
    for row in meta["stackup"]["layers"]:
        if row["type"] == "copper" or row["name"].startswith("dielectric"):
            name = row["name"]; low, high = bounds[name]["min"], bounds[name]["max"]
            if row["type"] == "copper":
                zmin[name] = z + low / 2; thickness[name] = (low, high)
            z += low
    er = profile["epsilon_r_max"]
    grow = profile["signal_edge_growth_mm"]
    foreign_grow = profile["foreign_edge_growth_mm"]
    reg = profile["relative_layer_registration_mm"]
    # Geometry is ERROR_OUTSIDE (10 nm); an extra 1 nm numeric reserve only shrinks b.
    numeric = EPS
    external = profile["unmodeled_external_copper_min_distance_mm"]
    def distance(xy, layer=None):
        point = Point(xy)
        ds = [external]
        for l, copper in foreign.items():
            if copper.is_empty:
                continue
            lateral = max(0., copper.distance(point) - foreign_grow - (reg if layer is None or l != layer else 0.))
            vertical = 0. if layer is None or l == layer else max(0., abs(zmin[l] - zmin[layer]) - thickness[l][0] / 2)
            ds.append(math.hypot(lateral, vertical))
        return min(ds) - numeric
    ledger = []
    for o in objects:
        if o["kind"] == "pad":
            continue  # Explicit 5 pF aggregate engineering allocation, not a bound.
        if o["kind"] == "track":
            layer = next(iter(o["copper"])); line = centerline(o); length = line.length
            halfwidth = o["width"] / 2 + grow
            halfthick = thickness[layer][1] / 2
            # Split rectangular body; separate end spheres cover its rounded caps.
            radius = math.hypot(halfwidth, halfthick)
            candidates = []
            for desired_step in [0.02, 0.035, 0.05, 0.07, 0.09, 0.12, 0.16, 0.22, 0.3]:
                count = max(1, math.ceil(length / desired_step)); step = length / count
                a = math.sqrt((step / 2) ** 2 + radius ** 2)
                try:
                    values = [sphere_cap_pf(a, distance(line.interpolate((i + .5) * step).coords[0], layer), er) for i in range(count)]
                    values += [sphere_cap_pf(radius, distance(xy, layer), er) for xy in [o["start"], o["end"]]]
                    candidates.append((sum(values), count, step))
                except ValueError:
                    pass
            if not candidates:
                raise ValueError("No valid sphere cover for track " + o["uuid"] + "; tighter geometry treatment required")
            value, count, step = min(candidates)
            ledger.append({"uuid": o["uuid"], "kind": "track", "layer": layer,
                           "whole_track_length_mm": length, "covering_body_spheres": count,
                           "covering_end_spheres": 2, "body_step_mm": step, "static_geometric_bound_pF": value})
        elif o["kind"] == "via":
            span = o["barrel_layers"]
            if not span:
                raise ValueError("Via without a native layer span")
            stack = [x for x in meta["stackup"]["layers"] if x["type"] == "copper" or x["name"].startswith("dielectric")]
            names = [x["name"] for x in stack]
            ia, ib = names.index(span[0]), names.index(span[-1])
            length = sum(bounds[n]["max"] for n in names[ia:ib + 1])
            radius = max(o["width_by_layer"].values()) / 2 + grow
            b = distance(o["xy"])
            candidates = []
            for desired_step in [.04, .07, .1, .15, .2, .3, .5]:
                count = max(1, math.ceil(length / desired_step)); step = length / count
                a = math.hypot(radius, step / 2)
                try:
                    candidates.append((count * sphere_cap_pf(a, b, er) + 2 * sphere_cap_pf(radius, b, er), count, step))
                except ValueError:
                    pass
            if not candidates:
                raise ValueError("No valid enclosing-cylinder cover for via " + o["uuid"])
            value, count, step = min(candidates)
            ledger.append({"uuid": o["uuid"], "kind": "via", "conservative_full_span_mm": length,
                           "filled_cylinder_radius_mm": radius, "covering_body_spheres": count,
                           "covering_end_spheres": 2, "body_step_mm": step, "static_geometric_bound_pF": value})
    value = sum(x["static_geometric_bound_pF"] for x in ledger)
    return {"method": "Dirichlet spherical-cover route bound, conditional on supplied geometric/material bounds",
            "static_route_bound_pF": value, "opposite_equal_slew_route_screen_pF": 2 * value,
            "rows": ledger,
            "note": "All foreign copper treated as grounded for the static bound. The 2x screen conservatively allows equal-amplitude opposite transitions; arbitrary faster aggressor dV/dt, inductance, losses and waveform behavior need separate checks."}


def capacitive_copper_entries(g, entries):
    """Include shafts on unflashed layers; deliberately overfill plated barrels.

    For every plated object, extrude the union of all native copper lands across
    its span. This contains its physical shaft even where a land is suppressed.
    It can be pessimistic; omitting such barrels could invalidate the bound.
    """
    out = list(entries)
    for o in g["objects"]:
        if not o.get("plated") or not o.get("barrel_layers"):
            continue
        shape = unary_union([poly(rows) for rows in o["copper"].values()])
        if shape.is_empty:
            raise ValueError("Plated object has no enclosing native copper land")
        for layer in o["barrel_layers"]:
            out.append({"uuid": o["uuid"], "kind": "conservative_barrel_envelope", "net": o["net"],
                        "layer": layer, "shape": shape})
    return out


def estimate(netrow, objects, entries, meta, profile):
    reasons = validate_profile(profile, meta)
    if not netrow["terminal_inventory_matches"]:
        reasons.append("Exact required three-terminal inventory not present")
    if not netrow["all_native_copper_connected"] or not netrow["all_terminals_connected"]:
        reasons.append("Native net incomplete: no final whole-net capacitance or RC result")
    if not netrow["topology"].get("clean_complete_tree"):
        reasons.append("Complete supported tree without dangling copper not established")
    if reasons:
        return {"status": "refused_pending_inputs_or_route", "reasons": reasons,
                "estimated_total_pF": None, "estimated_rise_ns": None, "qualification_pass": False}
    try:
        route = route_capacitance(objects, entries, meta, profile)
    except ValueError as exc:
        return {"status": "refused_unsupported_geometry", "reasons": [str(exc)],
                "estimated_total_pF": None, "estimated_rise_ns": None, "qualification_pass": False}
    ledger = {"STM32_pin_engineering_allocation_pF": 10., "DPS368_pin_engineering_allocation_pF": 10.,
              "pads_pullup_assembly_engineering_allocation_pF": 5.,
              "route_with_opposite_equal_slew_screen_pF": route["opposite_equal_slew_route_screen_pF"],
              "probe_pF": profile["probe_capacitance_pF"], "additional_model_allowance_pF": profile["additional_model_allowance_pF"]}
    total = sum(ledger.values()); rmax = 2200 * 1.01 * (1 + .0001 * 100)
    return {"status": "conditional_engineering_estimate", "route": route, "ledger": ledger,
            "estimated_total_pF": total, "estimated_rise_ns": .8473 * rmax * total * .001,
            "external_pullup_Rmax_ohm": rmax, "internal_pullup_credit": False,
            "within_provisional_50pF_allocation": total <= 50, "within_100ns_RC_screen": .8473 * rmax * total * .001 <= 100,
            "production_stackup_confirmed": profile.get("production_stackup_confirmed") is True,
            "epsilon_r_status": profile.get("epsilon_r_status", "engineering_assumption_not_manufacturer_maximum"),
            "epsilon_r_sensitivity": [{"epsilon_r_assumed": er,
                 "route_opposite_equal_slew_screen_pF": route["opposite_equal_slew_route_screen_pF"] * er / profile["epsilon_r_max"],
                 "engineering_total_pF": total - route["opposite_equal_slew_route_screen_pF"] + route["opposite_equal_slew_route_screen_pF"] * er / profile["epsilon_r_max"]}
                 for er in profile.get("epsilon_r_sensitivity", []) if isinstance(er, (int, float)) and math.isfinite(er) and er >= 1],
            "qualification_pass": False,
            "limits": "Estimated under supplied bounds and unverified device/assembly allocations. Does not close missing DPS368 pin maximum, ordinary 800 kHz/3.3 V output guarantee, actual firmware/register readback or first-article waveform requirements."}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--profile", type=Path)
    ap.add_argument("--critical-check", type=Path)
    ap.add_argument("--board", type=Path, required=True, help="Refuse a stale snapshot if canonical board changed")
    ap.add_argument("--requirements", type=Path, required=True)
    ap.add_argument("--calculations", type=Path, required=True)
    args = ap.parse_args()
    gp, mp = args.snapshot / "native-geometry.json", args.snapshot / "native-signals.json"
    g, meta = json.loads(gp.read_text()), json.loads(mp.read_text())
    validate_bindings(g, meta, sha(gp), sha(args.board))
    requirements, calculations = json.loads(args.requirements.read_text()), json.loads(args.calculations.read_text())
    if requirements["required_terminals"] != I2C or requirements["provisional_total_capacitance_target_pF_each_line"] != 50:
        raise ValueError("Stock-I2C requirements changed; explicitly review/update this narrow checker")
    if requirements["edge_targets_ns"] != {"rise_30_to_70_percent_max": 100, "fall_70_to_30_percent_max": 100}:
        raise ValueError("Reviewed stock edge targets changed")
    pullups = [x for x in g["footprints"] if x["ref"] in ["R7", "R8"]]
    if len(pullups) != 2 or any(x["value"].replace(" ", "") != "2.2k/1%" for x in pullups):
        raise ValueError("Reviewed native 2.2k 1% pull-up values changed")
    allocation = requirements["illustrative_engineering_allocation_pF"]
    if (allocation["STM32_pin"], allocation["DPS368_pin"], allocation["pads_pullup_and_assembly"]) != (10, 10, 5):
        raise ValueError("Reviewed device/assembly allocation changed")
    if abs(calculations["pullup_cases"][-1]["r_external_max_ohm"] - 2244.22) > 1e-6:
        raise ValueError("Stock external-pullup corner changed")
    profile = json.loads(args.profile.read_text()) if args.profile else None
    entries = copper_entries(g)
    cap_entries = capacitive_copper_entries(g, entries)
    refs = geometry_rows(g, meta, entries, list(I2C) + CRITICAL)
    reports = {}
    for net in list(I2C) + CRITICAL:
        objects = [x for x in g["objects"] if x["net"] == net]
        native = meta["nets"][net]
        tracks = [x for x in objects if x["kind"] in ["track", "arc"]]
        lengths = defaultdict(float)
        for t in tracks:
            lengths[next(iter(t["copper"]))] += native["track_native_lengths_mm"][t["uuid"]]
        report = {**native, "whole_net_planar_length_by_layer_mm": dict(lengths),
                  "whole_net_planar_length_mm": sum(lengths.values()), "track_count": len(tracks),
                  "widths_mm": sorted({x["width"] for x in tracks}),
                  "pads": [{k: x[k] for k in ["uuid", "key", "xy", "size", "angle", "offset", "all_layers", "shape_by_layer"]} |
                           {"copper_geometry": {l: {"area_mm2": poly(v).area, "bounds_mm": list(poly(v).bounds)} for l, v in x["copper"].items()}}
                           for x in objects if x["kind"] == "pad"],
                  "vias": [{k: x[k] for k in ["uuid", "xy", "via_type", "top_layer", "bottom_layer", "barrel_layers", "width_by_layer"]} |
                           {"drill": {k: x["drill"][k] for k in ["start", "end", "width"]}}
                           for x in objects if x["kind"] == "via"],
                  "track_geometry": [x for x in refs if x["net"] == net],
                  "topology": topology(objects, native)}
        if net in I2C:
            report["capacitance"] = estimate(report, objects, cap_entries, meta, profile)
        reports[net] = report
    critical = None
    if args.critical_check:
        check = json.loads(args.critical_check.read_text())
        bound = check.get("board_sha256") == meta["board_sha256"]
        critical = {"file": args.critical_check.name, "sha256": sha(args.critical_check), "exact_board_match": bound,
                    "reuse_status": "source-matched subset evidence" if bound else "STALE: rerun existing native check on this board",
                    "fullnet_connectivity": check.get("fullnet_connectivity") if bound else None,
                    "fault_count": len(check.get("faults", [])) if bound else None}
    result = {"schema": "f722-native-signal-review/v1", "board_sha256": meta["board_sha256"],
              "project_sha256": meta["project_sha256"], "native_version": meta["native_version"],
              "native_build": meta["native_build"], "shapely_version": shapely.__version__,
              "sources": {**meta["sources"], "check_signal_geometry.py": sha(__file__),
                          "native-geometry.json": sha(gp), "native-signals.json": sha(mp),
                          "final-native-i2c-requirements.json": sha(args.requirements),
                          "stock-i2c-calculations.json": sha(args.calculations),
                          "model_profile": sha(args.profile) if args.profile else None},
              "stackup": meta["stackup"], "I2C_final_status": "NOT_QUALIFIED",
              "pullup_native_values": [{k: x[k] for k in ["ref", "value", "fpid"]} for x in g["footprints"] if x["ref"] in ["R7", "R8"]],
              "remaining_qualification_gaps": requirements["remaining_qualification_gaps"],
              "nets": reports, "critical_ground_returns": meta["critical_ground_returns"],
              "USB_reference_interval_review": usb_reference_intervals(g, meta, entries),
              "existing_critical_check": critical,
              "limits": ["Whole-net length sums every native track once, including pull-up branches, pad overlap, stubs and any duplicated geometry. It is not a shortest route length.",
                         "Reference projection uses actual saved exact copper; it reports gaps and other copper, not impedance or return-current performance. No broad own-via antipad exemption is applied.",
                         "Arc projection is chorded at 10 nm sagitta; exact native lengths remain authoritative. Arc topology/loading is explicitly unsupported.",
                         "USB/clock connectivity and saved-plane projections do not establish USB impedance, eye compliance, oscillator startup or drive level.",
                         "Stock firmware and 2.2k 1% R7/R8 remain untouched. Device guarantees and bench requirements remain open."]}
    if sha(args.board) != meta["board_sha256"]:
        raise ValueError("Board changed while checking; re-export")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"board_sha256": result["board_sha256"], "I2C": {net: {
        "terminals_connected": reports[net]["all_terminals_connected"],
        "whole_net_planar_length_mm": reports[net]["whole_net_planar_length_mm"],
        "capacitance_status": reports[net]["capacitance"]["status"]} for net in I2C}}, indent=2))
    if any(reports[n]["capacitance"]["status"] != "conditional_engineering_estimate" for n in I2C):
        return 2
    if any(not reports[n]["capacitance"]["within_provisional_50pF_allocation"] or
           not reports[n]["capacitance"]["within_100ns_RC_screen"] for n in I2C):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
