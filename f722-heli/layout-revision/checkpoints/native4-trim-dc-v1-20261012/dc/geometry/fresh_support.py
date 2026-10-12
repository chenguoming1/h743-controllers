"""Fresh exact-native-contour topology producer. Production execution disabled.

No buffer, distance threshold, geometry repair, same-name or package-internal
edge is used. This establishes contour topology, not finite-width current paths.
Native ERROR_OUTSIDE/ERROR_INSIDE approximation bounds remain explicit.
"""
from collections import defaultdict
import copy
import json
from pathlib import Path
import sys
import disabled_binding as b

PRODUCTION_EXECUTION_ENABLED = False
MAX_FIXTURE_OBJECTS = 64


def geometry(rows):
    from shapely.geometry import GeometryCollection, Polygon
    from shapely.ops import unary_union
    shapes = []
    for row in rows:
        b.require(len(row["outer"]) >= 3, "Degenerate native contour")
        shape = Polygon(row["outer"], row.get("holes", []))
        b.require(shape.is_valid and not shape.is_empty and shape.area > 0,
                  "Invalid native contour; repair is prohibited")
        shapes.append(shape)
    combined = unary_union(shapes) if shapes else GeometryCollection()
    b.require(combined.is_valid, "Invalid contour union")
    return combined


def fragments(shape):
    if shape.is_empty:
        return []
    if shape.geom_type == "Polygon":
        return [shape]
    b.require(hasattr(shape, "geoms"), "Unexpected non-area native geometry")
    return [piece for part in shape.geoms for piece in fragments(part)]


def native_header(native):
    b.require(native.get("schema") == "kicad-native-copper/v1" and
              native.get("native_version") == "10.0.6" and native.get("units") == "mm",
              "Unreviewed native schema/version/units")
    error = native.get("maximum_polygon_error_mm")
    b.require(isinstance(error, (int, float)) and 0 < error <= 0.00001,
              "Native polygon precision differs")
    b.require(native.get("copper_error_location") == "ERROR_OUTSIDE" and
              native.get("pad_cut_error_location") == "ERROR_INSIDE",
              "Native approximation directions differ")
    b.require(native.get("source_unchanged") is True, "Native source changed")
    layers = native.get("copper_layers", [])
    b.require(layers and len(layers) == len(set(layers)), "Ambiguous native copper layers")


def exact_board_material(native):
    """Use the actual four straight board edges; curved/unreviewed outlines refuse."""
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union
    edges = native.get("edge_cuts", [])
    b.require(len(edges) == 4 and all(e["shape"] == "Line" for e in edges),
              "Exact F722 straight-edge material outline required")
    degrees = defaultdict(int)
    for edge in edges:
        degrees[tuple(edge["start"])] += 1; degrees[tuple(edge["end"])] += 1
    b.require(len(degrees) == 4 and all(v == 2 for v in degrees.values()), "Board edges do not form one exact closed ring")
    rings = list(polygonize(unary_union([LineString([e["start"], e["end"]]) for e in edges])))
    b.require(len(rings) == 1 and rings[0].is_valid and rings[0].area > 0, "Invalid exact board material")
    return rings[0]


def global_drills(native):
    """Every hole removes copper irrespective of owner net, including NPTH."""
    from shapely.geometry import GeometryCollection
    from shapely.ops import unary_union
    holes, records = defaultdict(list), defaultdict(list)
    for obj in native["objects"]:
        drill = obj.get("drill")
        if not drill:
            continue
        outside, inside = geometry(drill["outside"]), geometry(drill["inside"])
        b.require(obj["kind"] in {"pad", "via"} and drill.get("width", 0) > 0 and
                  not outside.is_empty and not inside.is_empty and outside.covers(inside), "Invalid global physical drill")
        if obj.get("npth") is True:
            span = native["copper_layers"]
        else:
            b.require(obj.get("plated") is True and obj.get("barrel_layers"), "Unsupported drill span")
            span = obj["barrel_layers"]
        b.require(set(span) <= set(native["copper_layers"]), "Global drill span uses undeclared layers")
        for layer in span:
            holes[layer].append(outside)
            records[layer].append((obj["uuid"], outside))
    return ({layer: unary_union(holes[layer]) if holes[layer] else GeometryCollection() for layer in native["copper_layers"]}, records)


def bind_inner_contours(native, sidecar):
    """Bind a separate official export; original route-model bytes stay unchanged."""
    objects = copy.deepcopy(native["objects"])
    missing = [o for o in objects if o["kind"] in {"track", "arc", "via"}]
    if missing:
        b.require(sidecar and sidecar.get("schema") == "f722-native-inner-copper-sidecar/v1" and
                  sidecar.get("board_sha256") == native["board_sha256"] and
                  sidecar.get("native_version") == "10.0.6" and sidecar.get("source_unchanged") is True and
                  sidecar.get("error_location") == "ERROR_INSIDE" and sidecar.get("maximum_polygon_error_mm") == .00001,
                  "Missing source-bound official inner track/via contour sidecar")
        rows = sidecar["objects"]
        b.require(set(rows) == {o["uuid"] for o in missing}, "Sidecar conductor UUID inventory differs")
        for obj in missing:
            row = rows[obj["uuid"]]
            b.require(row["kind"] == obj["kind"] and row["net"] == obj["net"] and
                      set(row["inside"]) == set(obj["copper"]), "Sidecar conductor name/layer identity differs")
            obj["inside"] = row["inside"]
    return objects


def physical_groups(objects, layers, material, drill_voids, all_drills):
    """Exact intersections on layers; only real bore-contacting barrels join layers."""
    from shapely.strtree import STRtree
    nodes, by_layer, barrels = [], defaultdict(list), defaultdict(list)
    seen = set()
    for obj in objects:
        uid = obj["uuid"]
        b.require(uid not in seen, "Duplicate native conductor UUID")
        seen.add(uid)
        b.require(obj["kind"] in {"pad", "via", "track", "arc", "zone", "copper_polygon"}, "Unknown conductor kind")
        b.require(set(obj["copper"]) <= set(layers), "Native conductor uses undeclared layer")
        drill = obj.get("drill")
        bore = geometry(drill["outside"]) if drill else None
        if drill:
            b.require(drill.get("width", 0) > 0 and not bore.is_empty,
                      "Missing or degenerate actual drill")
            inside = geometry(drill["inside"])
            b.require(not inside.is_empty and bore.covers(inside),
                      "Inside drill contour exceeds outside bound")
        plated = obj.get("plated") is True
        declared_barrel = obj.get("barrel_layers", [])
        if plated:
            b.require(obj["kind"] in {"pad", "via"} and drill and not obj.get("npth", False),
                      "False plated conductor without a real permitted bore")
            b.require(declared_barrel and len(declared_barrel) == len(set(declared_barrel)) and
                      set(declared_barrel) <= set(layers), "Invalid native barrel layer span")
        else:
            b.require(not declared_barrel, "Unplated conductor declares a barrel")
        b.require(set(obj.get("inside", {})) == set(obj["copper"]), "Missing conservative inner copper layer")
        for layer, raw in obj["inside"].items():
            guaranteed = geometry(raw)
            b.require(geometry(obj["copper"][layer]).covers(guaranteed), "Inner copper exceeds outer native bound")
            # Clip to real board material and subtract ALL outside drill bounds.
            shape = guaranteed.intersection(material).difference(drill_voids[layer])
            b.require(shape.is_valid, "Invalid copper after native bore subtraction")
            for piece in fragments(shape):
                i = len(nodes)
                nodes.append({"object": obj, "layer": layer, "geometry": piece})
                by_layer[layer].append(i)
                # Exact intersection, not dwithin/positive buffering. A fragment
                # away from this object's bore cannot acquire a barrel edge.
                if (plated and layer in declared_barrel and guaranteed.intersection(material).covers(bore) and
                        not any(other_uid != uid and other.intersects(bore) for other_uid, other in all_drills[layer]) and
                        piece.intersects(bore.boundary)):
                    barrels[uid].append(i)
    parent = list(range(len(nodes)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, c):
        a, c = find(a), find(c)
        if a != c:
            parent[c] = a

    for ids in by_layer.values():
        tree = STRtree([nodes[i]["geometry"] for i in ids])
        for position, i in enumerate(ids):
            for j in tree.query(nodes[i]["geometry"], predicate="intersects"):
                if int(j) > position:
                    union(i, ids[int(j)])
    for ids in barrels.values():
        for i in ids[1:]:
            union(ids[0], i)
    groups = defaultdict(list)
    for i, node in enumerate(nodes):
        groups[find(i)].append(node)
    return list(groups.values())


def audit_native(native, scope, *, sidecar=None, fixture=False):
    """Compute scoped groups; production cannot run until code receives new review."""
    b.require(not sys.flags.optimize, "Nonoptimized Python is required")
    if fixture:
        b.require(native.get("fixture_only") is True and len(native["objects"]) <= MAX_FIXTURE_OBJECTS
                  and len(scope["pad_inventory"]) <= 4 and len(native["zones"]) <= 8,
                  "Fixture limits exclude a full-board audit")
    else:
        b.require(PRODUCTION_EXECUTION_ENABLED, "Full-board support execution is disabled pending owner lane grant and independent review")
    return _audit_native_verified(native, scope, sidecar=sidecar, fixture=fixture)


def _audit_native_verified(native, scope, *, sidecar=None, fixture=False):
    """Internal geometry body; public production and owner-control gates are separate."""
    native_header(native)
    material = exact_board_material(native)
    drill_voids, all_drills = global_drills(native)
    bound_objects = bind_inner_contours(native, sidecar)
    actual = b.pad_inventory(native, scope["pad_inventory"])
    b.require(actual == scope["pad_inventory"], "Actual support UUID/net/key inventory differs")
    all_uids = [o["uuid"] for o in native["objects"]] + [z["uuid"] for z in native["zones"]]
    b.require(len(all_uids) == len(set(all_uids)), "Duplicate object/zone UUID")
    rows, return_results = {}, {}
    for net in sorted(scope["pad_inventory"]):
        objects = [o for o in bound_objects if o["net"] == net]
        for zone in native["zones"]:
            if zone["rule"] or zone["net"] != net:
                continue
            b.require(set(zone["filled"]) <= set(zone["layers"]), "Saved fill on undeclared zone layer")
            objects.append({"uuid": zone["uuid"], "kind": "zone", "net": net,
                            "copper": zone["filled"], "inside": zone["filled"], "drill": None, "plated": False,
                            "barrel_layers": []})
        groups = physical_groups(objects, native["copper_layers"], material, drill_voids, all_drills)
        pad_groups = []
        for group in groups:
            pads = {n["object"]["uuid"]: n["object"]["key"] for n in group
                    if n["object"]["kind"] == "pad" and n["object"].get("number")}
            if not pads:
                continue
            planes = sorted({(n["object"]["uuid"], n["layer"]) for n in group
                             if n["object"]["kind"] == "zone" and net == "GND"})
            witnesses = [{"uuid": uid, "layer": layer} for uid, layer in planes]
            pad_groups.append({"pad_uuids": sorted(pads), "pad_identity": pads,
                               "saved_plane_witnesses": witnesses})
            for uid, required_layers in scope["required_return_uuids"].items():
                if uid in pads:
                    # A physical pad with disconnected islands must not hide
                    # an unconnected fragment behind another connected fragment.
                    result = return_results.setdefault(uid, {"component_count": 0,
                        "reaches_saved_planes": True, "saved_plane_witnesses": []})
                    result["component_count"] += 1
                    result["reaches_saved_planes"] &= bool(witnesses) and set(required_layers) <= {w["layer"] for w in witnesses}
                    result["saved_plane_witnesses"].extend(witnesses)
        observed = [uid for group in pad_groups for uid in group["pad_uuids"]]
        complete = len(pad_groups) == 1 and len(observed) == len(set(observed)) and set(observed) == set(actual[net])
        rows[net] = {"complete": complete, "pad_group_count": len(pad_groups),
                     "groups": pad_groups, "physical_pad_count": len(actual[net])}
    for uid in scope["required_return_uuids"]:
        row = return_results.setdefault(uid, {"component_count": 0, "reaches_saved_planes": False,
                                             "saved_plane_witnesses": []})
        row["reaches_saved_planes"] &= row["component_count"] == 1
    gates = dict.fromkeys(b.SUPPORT_GATES, True)
    gates["all_required_groups_complete"] = all(row["complete"] for row in rows.values())
    gates["required_returns_reach_saved_planes"] = all(row["reaches_saved_planes"] for row in return_results.values())
    return {"schema": b.SUPPORT_SCHEMA, "passed": all(gates.values()), "gates": gates,
            "board_sha256": native["board_sha256"], "support_scope_sha256": b.digest(scope),
            "producer_sha256": copy.deepcopy(scope["producer_sha256"]),
            "input_hashes": copy.deepcopy(scope["expected_input_hashes"]),
            "nets": rows, "required_returns": return_results,
            "numerical_acceptance_claimed": False, "fixture_only": fixture,
            "method": "Exact intersections of native ERROR_INSIDE conductor contours and exact saved fill, clipped to actual straight board edges and ALL ERROR_OUTSIDE drill voids. Real plated bores join only guaranteed enclosing copper that reaches the outside bore boundary. No buffering, epsilon, repair, same-name or package edges. Inconclusive bound contacts remain disconnected.",
            "contact_epsilon_mm": 0,
            "native_polygon_error_mm": native["maximum_polygon_error_mm"],
            "full_width_annular_reference_and_power_qualification": False}


def produce(board_path, native_path, scope_path, sidecar_path, output_path):
    """Final CLI producer boundary, intentionally unavailable in this proposal."""
    b.require(PRODUCTION_EXECUTION_ENABLED, "Production support producer is disabled; no owner lane grant or final independent review exists")
    actual_paths = {"board": Path(board_path), "route_model_native": Path(native_path),
                    "inner_sidecar": Path(sidecar_path), "support_producer": Path(__file__),
                    "binding_verifier": Path(b.__file__), "support_scope": Path(scope_path)}
    observed = {key: b.sha(path) for key, path in actual_paths.items()}
    board_sha, native_sha = observed["board"], observed["route_model_native"]
    native = b.read_json_bound(native_path, observed["route_model_native"])
    scope = b.read_json_bound(scope_path, observed["support_scope"])
    b.require(native["board_sha256"] == board_sha, "Final native/board identity differs")
    b.require(scope["expected_input_hashes"] == {key: value for key, value in observed.items() if key != "support_scope"},
              "Producer actual inputs differ from reviewed scope")
    b.require(set(scope["producer_sha256"].values()) == {observed["support_producer"], observed["binding_verifier"]},
              "Actual producer/verifier differ from reviewed scope")
    sidecar = b.read_json_bound(sidecar_path, observed["inner_sidecar"])
    b.require(sidecar.get("native_sha256") == native_sha, "Inner contour sidecar belongs to different native bytes")
    report = audit_native(native, scope, sidecar=sidecar)
    report["native_sha256"] = native_sha
    report["input_hashes"] = observed
    b.require(all(b.sha(path) == observed[key] for key, path in actual_paths.items()),
              "Producer input moved during physical support audit")
    b.require(not Path(output_path).exists(), "Use a fresh support receipt path")
    Path(output_path).write_text(json.dumps(report, indent=2) + "\n")
    return report
