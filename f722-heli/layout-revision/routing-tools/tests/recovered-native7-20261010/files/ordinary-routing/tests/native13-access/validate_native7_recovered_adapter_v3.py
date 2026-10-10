"""Reproduce adapter identity, moving-width and physical-connectivity controls.

No graph search, board mutation, contour repair or tolerance bridging is used.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import time

import native7_recovered_context_v3 as adapter


def copper_components(g, net):
    from shapely.strtree import STRtree
    fragments, layers, barrels = [], defaultdict(list), defaultdict(list)
    for record, copper, masks, drill in g.BASE:
        if record["net"] != net:
            continue
        for layer, geometry in copper.items():
            parts = list(geometry.geoms) if hasattr(geometry, "geoms") else [geometry]
            for polygon in parts:
                assert polygon.geom_type == "Polygon" and polygon.is_valid
                i = len(fragments)
                fragments.append((record["uuid"], layer, polygon))
                layers[layer].append(i)
                if record["kind"] == "via" or record.get("plated"):
                    barrels[record["uuid"]].append(i)
    parent = list(range(len(fragments)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[b] = a

    for ids in layers.values():
        tree = STRtree([fragments[i][2] for i in ids])
        for pos, i in enumerate(ids):
            for j in tree.query(fragments[i][2], predicate="intersects"):
                if int(j) > pos:
                    union(i, ids[int(j)])
    for ids in barrels.values():
        for i in ids[1:]:
            union(ids[0], i)
    groups, memberships = defaultdict(set), defaultdict(set)
    for i, (uid, layer, geometry) in enumerate(fragments):
        groups[find(i)].add(uid)
        memberships[uid].add(find(i))
    return list(groups.values()), memberships


def validate(workspace, drc_path):
    from shapely.geometry import Point, box
    start = time.monotonic()
    g = adapter.load(workspace)
    assert len(g.N["footprints"]) == 156
    assert len(g.recipe_groups) == 100 and len(g.recipe_member_provenance) == 233
    negative = []
    for width in (.18, .20, .25):
        distance = (.0635 + width / 2) / 2 + .127
        foreign = ({"uuid": "width-negative-control", "kind": "track", "net": "CONTROL_FOREIGN"},
                   {"F.Cu": box(10, 10 + distance, 11, 10 + distance + .05)}, {}, None)
        narrow = g.check_track("CONTROL_MOVING", "F.Cu", [[10, 10], [11, 10]], width=.127, objects=[foreign])
        actual = g.check_track("CONTROL_MOVING", "F.Cu", [[10, 10], [11, 10]], width=width, objects=[foreign])
        a = next(row for row in narrow if row["uuid"] == "width-negative-control")
        b = next(row for row in actual if row["uuid"] == "width-negative-control")
        assert a["pass_with_polygon_error"] and not b["pass_with_polygon_error"]
        assert b["moving_radius_mm"] == width / 2
        negative.append({"moving_width_mm": width, "foreign_gap_from_centerline_mm": distance,
                         "incorrect_127_predicate": a, "actual_width_predicate": b})
    hole = g.s.geom([{"outer": [[0, 0], [2, 0], [2, 2], [0, 2]],
                     "holes": [[[.5, .5], [1.5, .5], [1.5, 1.5], [.5, 1.5]]]}])
    assert hole.is_valid and hole.area == 3 and not hole.covers(Point(1, 1))
    assert len(hole.interiors) == 1
    native_holes = 0
    for record, copper, masks, drill in g.BASE:
        for layer, polygons in record["copper"].items():
            native_holes += sum(len(p.get("holes", [])) for p in polygons)
            assert copper[layer].is_valid and copper[layer].equals(g.s.geom(polygons))
    expected = {"PORT_C_RX_EXT": 3, "PORT_C_TX_MCU": 2, "PORT_C_RX_MCU": 2,
                "FLASH_MISO": 2, "FLASH_MOSI": 2, "FLASH_SCK": 2}
    physical = {net: copper_components(g, net) for net in expected}
    counts = {net: len(value[0]) for net, value in physical.items()}
    assert counts == expected, (counts, expected)
    drc = json.loads(drc_path.read_text())
    checks = []
    for issue in drc["unconnected_items"]:
        a, b = [item["uuid"] for item in issue["items"]]
        net = g.by[a]["net"]
        assert g.by[b]["net"] == net
        memberships = physical[net][1]
        separate = not memberships[a].intersection(memberships[b])
        checks.append({"net": net, "a": a, "b": b, "separate": separate})
    assert len(checks) == 7 and all(row["separate"] for row in checks)
    return {"schema": "f722-recovered-native7-adapter-reproducible-validation/v1",
            "binding": g.binding(), "validation_script_sha256": adapter.digest(__file__),
            "native_drc_reference_sha256": adapter.digest(drc_path),
            "width_negative_controls": negative, "native_open_endpoint_checks": checks,
            "affected_net_component_counts": counts,
            "sum_component_excess_for_native_open_nets": sum(n - 1 for n in counts.values()),
            "all_seven_native_opens_reproduced": True,
            "connectivity_method": "Native polygon-fragment intersections on each layer; only physical via/plated barrels join layers; no tolerance bridge.",
            "synthetic_hole_control": {"passed": True, "area_mm2": hole.area, "interior_ring_count": 1},
            "native_copper_hole_rings": native_holes,
            "contours_repaired": False, "all_native_copper_matches_exported_polygons": True,
            "loaded_objects": len(g.BASE), "native_recipe_members": len(g.recipe_member_provenance),
            "routing_started": False, "new_route_acceptance": False,
            "fresh_full_finite_reference_review": False, "seconds": time.monotonic() - start}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--workspace", type=Path, default=adapter.DEFAULT_WORKSPACE)
    p.add_argument("--drc", type=Path, default=adapter.REBUILD / "repo/f722-heli/layout-revision/checkpoints/joint-native7-20261010/evidence/drc-all.json")
    p.add_argument("--output", type=Path, default=Path(__file__).with_name("native7-recovered-adapter-validation-v3-repro.json"))
    args = p.parse_args()
    result = validate(args.workspace, args.drc)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": True, "opens": 7, "seconds": result["seconds"],
                      "output": str(args.output), "sha256": adapter.digest(args.output)}))
