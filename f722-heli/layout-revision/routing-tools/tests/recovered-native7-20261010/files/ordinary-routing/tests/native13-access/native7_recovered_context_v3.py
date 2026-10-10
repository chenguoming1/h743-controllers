"""Explicit native7 adapter; import never loads geometry or starts routing.

Call input_status() first, then load() only during a granted geometry job.  The
four historical helpers remain byte-identical.  Only their named function ASTs
are compiled into isolated namespaces, after their hashes are verified; their
historical candidate44/source11 import-time loaders are never executed.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import heapq
import json
import math
from pathlib import Path
import time
from types import ModuleType, SimpleNamespace
import uuid

HERE = Path(__file__).resolve().parent
REBUILD = HERE.parents[2]
DEFAULT_WORKSPACE = REBUILD / "recovered-native7"
IMPORTER = Path("ordinary-routing/tests/native13-access/joint-native-import11-v1")
REFERENCE = IMPORTER / "candidates/published-reference02"
SOURCE_BOARD_SHA256 = "454b7bb2454695b49c039f3d97e5edefb1946912363bab00ef5ced6ba2b0ea16"
BOARD_SHA256 = "a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f"
NATIVE_SHA256 = "53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505"
TRANSACTION_SHA256 = "b7ca08e59b4316c8a88c0ff9d3c0fe3cffac4d0f0ad2b407028cd1ef3050f497"
MAP_SHA256 = "a1175806ea39f0212f67e13b760782838c858dbaf285f6e4ac8919994e7364c0"
HELPERS = {
    "geometry": (HERE.parent / "flash-candidate43-structural/native44_geometry.py",
                 "ff10a432b973733209ca11fc84d4adde463ea4f7bc681d4bab712104535c2aa3"),
    "context": (HERE / "native11_context.py",
                "95fc032ac4011985bced19296e719e17a5a4a904321f86369982bcc34bdb4482"),
    "route": (HERE / "route_native11.py",
              "34e745a038ae823f88d25eb2e87496f70a869277d4c7769009017b18915d43b8"),
    "graph": (HERE / "graph_native11.py",
              "3d21c3b9cd61863db02c6309f6cb493264a9ffaeb7d82457240d5f163775077c"),
}


class Native7InputError(RuntimeError):
    """Required exact recovered input is absent or differs from the binding."""


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def input_paths(workspace=DEFAULT_WORKSPACE, *, native=None, board=None,
                transaction=None, logical_map=None):
    w = Path(workspace).resolve()
    return {
        "board": Path(board) if board is not None else w / REFERENCE / "f722-heli.kicad_pcb",
        "native": Path(native) if native is not None else w / REFERENCE / "f722-heli.native.json",
        "transaction": Path(transaction) if transaction is not None else w / IMPORTER / "selected-transaction.json",
        "logical_map": Path(logical_map) if logical_map is not None else REBUILD / "repo/f722-heli/layout-revision/checkpoints/joint-native7-20261010/repro/logical-route-map.json",
    }


def input_status(workspace=DEFAULT_WORKSPACE, **overrides):
    """Read-only byte checks only; never imports Shapely or converts geometry."""
    paths = input_paths(workspace, **overrides)
    expected = {"board": BOARD_SHA256, "native": NATIVE_SHA256,
                "transaction": TRANSACTION_SHA256, "logical_map": MAP_SHA256}
    rows = []
    for key, path in paths.items():
        exists = path.is_file()
        actual = digest(path) if exists else None
        rows.append({"name": key, "path": str(path), "exists": exists,
                     "expected_sha256": expected[key], "sha256": actual,
                     "passed": exists and actual == expected[key]})
    for key, (path, sha) in HELPERS.items():
        exists = path.is_file()
        actual = digest(path) if exists else None
        rows.append({"name": "helper_" + key, "path": str(path), "exists": exists,
                     "expected_sha256": sha, "sha256": actual,
                     "passed": exists and actual == sha})
    ready = all(row["passed"] for row in rows)
    return {"schema": "f722-recovered-native7-input-status/v1", "ready": ready,
            "state": "exact_inputs_ready" if ready else "native7_not_yet_exported_or_input_mismatch",
            "geometry_loaded": False, "routing_started": False, "inputs": rows}


def require_inputs(workspace=DEFAULT_WORKSPACE, **overrides):
    result = input_status(workspace, **overrides)
    if not result["ready"]:
        failures = ", ".join(row["name"] + (" absent" if not row["exists"] else " hash mismatch")
                             for row in result["inputs"] if not row["passed"])
        raise Native7InputError("Native7 input guard: " + failures + "; no geometry loaded.")
    return result


def recipe_uuid_groups(transaction):
    """Reproduce the published importer's UUID rule, without geometry or cuts."""
    if transaction["source_board_sha256"] != SOURCE_BOARD_SHA256:
        raise Native7InputError("Selected transaction source board differs")
    groups, roles, seen = {}, {}, set()
    for row in transaction["added_copper"]:
        recipe = row["recipe"]
        name = recipe["name"]
        if name in groups:
            raise Native7InputError("Duplicate recipe name: " + name)
        if recipe["kind"] == "track":
            suffixes = [name + "/segment/" + str(i) for i in range(len(recipe["points"]) - 1)]
        elif recipe["kind"] == "via":
            suffixes = [name + "/via"]
        else:
            raise Native7InputError("Unsupported recipe kind: " + recipe["kind"])
        if not suffixes:
            raise Native7InputError("Empty recipe: " + name)
        members = tuple(str(uuid.uuid5(uuid.NAMESPACE_URL,
                            SOURCE_BOARD_SHA256 + "/" + TRANSACTION_SHA256 + "/" + suffix))
                        for suffix in suffixes)
        if seen.intersection(members):
            raise Native7InputError("Native UUID collision")
        seen.update(members)
        groups[name] = members
        role = row.get("selected_object_record", {}).get("role") or recipe.get("role")
        if role is not None:
            roles.update({uid: role for uid in members})
    return groups, roles


def _functions(key, names, namespace):
    """Compile only fixed named functions from a hash-verified published source."""
    path, expected = HELPERS[key]
    if digest(path) != expected:
        raise Native7InputError("Helper changed: " + str(path))
    tree = ast.parse(path.read_text(), filename=str(path))
    funcs = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    if not set(names).issubset(funcs):
        raise Native7InputError("Published function set is incomplete: " + key)
    selected = ast.Module(body=[funcs[name] for name in names], type_ignores=[])
    exec(compile(selected, str(path) + "::verified-functions", "exec"), namespace)


def load(workspace=DEFAULT_WORKSPACE, **overrides):
    """Load exact native7 objects. Caller must hold the shared geometry-job lane."""
    status = require_inputs(workspace, **overrides)
    paths = input_paths(workspace, **overrides)
    # These imports and all polygon construction occur only after the input guard.
    import shapely
    from shapely import unary_union
    from shapely.geometry import Polygon, Point, LineString, box
    from shapely.ops import nearest_points, polylabel
    from shapely.strtree import STRtree

    native = json.loads(paths["native"].read_text())
    transaction = json.loads(paths["transaction"].read_text())
    logical = json.loads(paths["logical_map"].read_text())
    if native["board_sha256"] != BOARD_SHA256 or logical["board_sha256"] != BOARD_SHA256:
        raise Native7InputError("Native/map board binding differs")
    if logical["source_sha256"] != SOURCE_BOARD_SHA256:
        raise Native7InputError("Logical-map source binding differs")
    records = {o["uuid"]: o for o in native["objects"]}
    if len(records) != len(native["objects"]):
        raise Native7InputError("Native UUIDs are not unique")
    groups, roles = recipe_uuid_groups(transaction)
    recipe_by_name = {row["recipe"]["name"]: row["recipe"] for row in transaction["added_copper"]}
    member_provenance = {}
    rounded = lambda xy: [int(round(v * 1e6)) / 1e6 for v in xy]
    for name, members in groups.items():
        recipe = recipe_by_name[name]
        for index, uid in enumerate(members):
            if uid not in records or records[uid]["net"] != recipe["net"]:
                raise Native7InputError("Recorded recipe member missing or wrong net: " + name)
            if logical["logical_route_map"].get(uid) != recipe["net"]:
                raise Native7InputError("Recorded recipe logical mapping differs: " + name)
            record = records[uid]
            if record["kind"] != recipe["kind"]:
                raise Native7InputError("Native recipe kind differs: " + name)
            if recipe["kind"] == "track":
                width = int(round(recipe["width"] * 1e6)) / 1e6
                if not (record["start"] == rounded(recipe["points"][index]) and
                        record["end"] == rounded(recipe["points"][index + 1]) and
                        record["width"] == width and
                        record["width_by_layer"] == {recipe["layer"]: width}):
                    raise Native7InputError("Native segment/endpoints/width differ: " + name)
            elif not (record["xy"] == rounded(recipe["xy"]) and
                      record["width"] == .45 and record["drill"]["width"] == .20 and
                      record["barrel_layers"] == native["copper_layers"] and
                      record["top_layer"] == "F.Cu" and record["bottom_layer"] == "B.Cu" and
                      record["tented"] == {"F.Mask": True, "B.Mask": True} and not record["mask"]):
                raise Native7InputError("Native via geometry/tenting differs: " + name)
            member_provenance[uid] = {"recipe_name": name, "net": recipe["net"],
                                      "kind": recipe["kind"], "role": roles.get(uid),
                                      "segment_index": index if recipe["kind"] == "track" else None}
    missing_map = set(logical["logical_route_map"]) - set(records)
    if missing_map:
        raise Native7InputError("Logical map references absent native UUIDs")

    env = {"math": math, "shapely": shapely, "unary_union": unary_union,
           "Polygon": Polygon, "Point": Point, "LineString": LineString,
           "box": box, "nearest_points": nearest_points, "N": native,
           "HALF": .0635, "VR": .225, "DR": .1,
           "ERROR": native["maximum_polygon_error_mm"]}
    rules = ModuleType("native7_recovered_finite_rules_v3")
    rules.__dict__.update(env)
    _functions("geometry", ("geom", "obstacles", "check", "paths2"), rules.__dict__)
    rules.OUTLINE = rules.geom(native["outline_with_npth"]["polygons"])

    def entry(record):
        return (record, {layer: rules.geom(polys) for layer, polys in record["copper"].items()},
                {layer: rules.geom(mask["polygons"]) for layer, mask in record.get("mask", {}).items()}
                if record.get("smd") else {},
                rules.geom(record["drill"]["outside"]) if record.get("drill") else None)

    base = tuple(entry(record) for record in native["objects"])
    rules.OBJECTS = base
    pads = {}
    for record in native["objects"]:
        if record["kind"] == "pad":
            pads.setdefault(record["key"], []).append(record)
    if sum(map(len, pads.values())) != 558:
        raise Native7InputError("Native7 pad inventory differs from 558")

    def one_pad(key):
        if len(pads[key]) != 1:
            raise Native7InputError("Expected one physical pad for " + key)
        return pads[key][0]

    def track(net, layer, points, name, width=.127):
        pts = copy.deepcopy(points)
        if name in records or name in groups:
            raise Native7InputError("New route name collides with native provenance: " + name)
        record = dict(uuid=name, net=net, kind="track", width=width,
                      start=pts[0], end=pts[-1], points=pts,
                      recovery_proposal=True)
        return (record, {layer: LineString(pts).buffer(width / 2 / math.cos(math.pi / 512), quad_segs=128)}, {}, None)

    def via(net, xy, name):
        if name in records or name in groups:
            raise Native7InputError("New via name collides with native provenance: " + name)
        return (dict(uuid=name, net=net, kind="via", xy=list(xy), width=.45,
                     drill_diameter_mm=.20, tented_front=True, tented_back=True,
                     barrel_layers=native["copper_layers"], recovery_proposal=True),
                {layer: Point(xy).buffer(.225 / math.cos(math.pi / 512), quad_segs=128)
                 for layer in native["copper_layers"]}, {},
                Point(xy).buffer(.1 / math.cos(math.pi / 512), quad_segs=128))

    def check_track(net, layer, points, *, width, objects=None):
        """Finite centerline test with required explicit full moving-track width.

        Use this wrapper for .18/.20/.25 support tracks.  The low-level historical
        s.check() does not infer width, and s.HALF is mutable routing state.
        """
        if not math.isfinite(width) or width <= 0:
            raise ValueError("Moving-track width must be finite and positive")
        old_half, old_objects = rules.HALF, rules.OBJECTS
        try:
            rules.HALF = width / 2
            rules.OBJECTS = base if objects is None else objects
            obstacles, _, _ = rules.obstacles(net, layer)
            return rules.check(LineString(points), obstacles, True)
        finally:
            rules.HALF, rules.OBJECTS = old_half, old_objects

    def check_via(net, xy, *, objects=None):
        old_objects = rules.OBJECTS
        try:
            rules.OBJECTS = base if objects is None else objects
            _, obstacles, _ = rules.obstacles(net, "B.Cu")
            return rules.check(Point(xy), obstacles, True)
        finally:
            rules.OBJECTS = old_objects

    def resolve_ids(name_or_uuid):
        if name_or_uuid in groups:
            return groups[name_or_uuid]
        if name_or_uuid in records:
            return (name_or_uuid,)
        raise Native7InputError("Unknown exact recipe/native identity: " + name_or_uuid)

    def group_records(name_or_uuid):
        return tuple(records[uid] for uid in resolve_ids(name_or_uuid))

    def binding():
        return {"schema": "f722-recovered-native7-context-binding/v1",
                "board_sha256": BOARD_SHA256, "native_sha256": NATIVE_SHA256,
                "transaction_sha256": TRANSACTION_SHA256, "logical_map_sha256": MAP_SHA256,
                "adapter_sha256": digest(__file__), "input_paths": {k: str(v) for k, v in paths.items()},
                "helper_sha256": {k: sha for k, (p, sha) in HELPERS.items()},
                "candidate_base": "published-reference02", "new_proposals_selected": False,
                "historical_v25_v26_bytes_recovered": False,
                "native_record_count": len(base), "pads": 558,
                "native_records_preserved_without_alias_renaming": True,
                "role_metadata_kept_separately": True,
                "check_track_requires_actual_width": True,
                "native_polygons_repaired": False,
                "finite_reference_electrical_checks_pending_for_new_proposals": True}

    context = SimpleNamespace(N=native, BASE=base, by=records, pads=pads, s=rules,
                              entry=entry, track=track, via=via, one_pad=one_pad,
                              check_track=check_track, check_via=check_via,
                              binding=binding, ROOT=Path(workspace).resolve(),
                              SOURCE=paths["native"], BOARD=paths["board"], EXPECTED=BOARD_SHA256,
                              logical_route_map=logical["logical_route_map"],
                              recipe_groups=groups, recipe_by_name=recipe_by_name,
                              role_by_uuid=roles,
                              recipe_name_by_uuid={uid: row["recipe_name"] for uid, row in member_provenance.items()},
                              segment_index_by_uuid={uid: row["segment_index"] for uid, row in member_provenance.items()},
                              recipe_member_provenance=member_provenance, resolve_ids=resolve_ids,
                              group_records=group_records, input_validation=status,
                              REMOVED_NATIVE_IDS=frozenset())
    routing = ModuleType("native7_recovered_route_v3")
    routing.__dict__.update(dict(heapq=heapq, math=math, time=time, shapely=shapely,
                                 unary_union=unary_union, Point=Point, LineString=LineString,
                                 g=context, s=rules))
    _functions("route", ("parts", "expanded", "domain", "component", "route"), routing.__dict__)
    graph = ModuleType("native7_recovered_graph_v3")
    graph.__dict__.update(dict(heapq=heapq, math=math, Point=Point, STRtree=STRtree,
                               polylabel=polylabel, g=context, r=routing, s=rules))
    _functions("graph", ("build", "terminals", "connect"), graph.__dict__)
    context.rt, context.gg = routing, graph
    return context


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check exact native7 adapter inputs without geometry")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--board", type=Path)
    parser.add_argument("--transaction", type=Path)
    parser.add_argument("--logical-map", type=Path)
    args = parser.parse_args()
    opts = {k: v for k, v in vars(args).items() if v is not None}
    report = input_status(**opts)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["ready"] else 2)
