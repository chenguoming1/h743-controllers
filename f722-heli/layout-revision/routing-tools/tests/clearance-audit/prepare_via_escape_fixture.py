#!/usr/bin/env python3
"""Hash-bind four existing witnesses and revalidate their exact 10 nm points."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import Point, Polygon
from shapely import unary_union

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def geom(ps):
    pieces = [Polygon(p["outer"], p.get("holes", [])) for p in ps]
    assert all(p.is_valid for p in pieces)
    return unary_union(pieces)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("native", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    model = json.loads((args.model / "model.json").read_text())
    native = json.loads(args.native.read_text())
    receipt = json.loads(args.receipt.read_text())
    assert model["board_sha256"] == native["board_sha256"] == receipt["board_sha256"]
    assert model["native_sha256"] == sha(args.native) == receipt["native_sha256"]
    assert sha(model["physical_board"]) == model["board_sha256"]
    assert sha(args.model / "routing.dsn") == model["dsn_sha256"]
    native_objects = []
    for o in native["objects"]:
        label = o.get("key", o["uuid"])
        copper = {layer: geom(ps) for layer, ps in o["copper"].items()}
        masks = [geom(m["polygons"]) for m in o.get("mask", {}).values()] if o.get("smd") else []
        drill = geom(o["drill"]["outside"]) if o.get("drill") else None
        native_objects.append((o, label, copper, masks, drill))
    outline = geom(native["outline_with_npth"]["polygons"])
    fixture = {"schema": "f722-native-via-escape-control/v1", "board_sha256": model["board_sha256"], "rules_mm": receipt["rules_mm"], "native_receipt": str(args.receipt.resolve().relative_to(ROOT)), "engine_grid_mm": .00001, "route_search_authorized_by_fixture": False, "cases": []}
    for row in receipt["results"]:
        net, layer = row["net"], row["layer"]
        constraints = []
        trace_constraints = []
        for o, label, copper, masks, drill in native_objects:
            if o["net"] != net:
                for l, g in copper.items():
                    constraints.append((label, "foreign_copper:" + l, g, .352))
                    if l == layer:
                        trace_constraints.append((g, .1905))
            for mask in masks:
                constraints.append((label, "all_smt_mask_no_same_net_exception", mask, .30))
            if drill is not None:
                constraints.append((label, "all_drills_no_same_net_exception", drill, .35))
                if o.get("npth"):
                    constraints.append((label, "npth_copper", drill, .479))
                    trace_constraints.append((drill, .3175))
        excluded = []
        for z in native["zones"]:
            if z["rule"]:
                g = geom(z["outline"])
                if z["layers"] and (z["forbid"]["vias"] or z["forbid"]["copper"]):
                    constraints.append((z["uuid"], "rule_via_copper", g, .225))
                if layer in z["layers"] and (z["forbid"]["tracks"] or z["forbid"]["copper"]):
                    trace_constraints.append((g, .0635))
            elif z["net"] == "GND" and z["layers"] and set(z["layers"]) <= {"In1.Cu", "In4.Cu"}:
                excluded.append(z["uuid"])
            elif z["net"] != net:
                for l, ps in z["filled"].items():
                    g = geom(ps)
                    constraints.append((z["uuid"], "zone_copper:" + l, g, .352))
                    if l == layer:
                        trace_constraints.append((g, .1905))
        assert sorted(excluded) == sorted(model["regenerable_reference_zones"])
        for pad, result in row["conservative_native"].items():
            raw = result["witness_mm"]
            integer = [math.floor(raw[0] * 1e5 + .5), -math.floor(raw[1] * 1e5 + .5)]
            xy = [integer[0] / 1e5, -integer[1] / 1e5]
            original, quantized = Point(raw), Point(xy)
            displacement = original.distance(quantized)
            assert displacement <= math.sqrt(2) * .000005 + 1e-12
            margins = sorted([(quantized.distance(g) - required, label, category) for label, category, g, required in constraints] + [(quantized.distance(outline.boundary) - .479, "board-outline-with-npth", "edge_npth_copper")])
            assert outline.contains(quantized) and margins[0][0] > 0
            original_trace_margin = min([original.distance(g) - required for g, required in trace_constraints] + [original.distance(outline.boundary) - .3175])
            assert original_trace_margin > displacement, "Quantization might cross a trace component boundary"
            fixture["cases"].append({"pad": pad, "logical_net": net, "pad_layer": layer, "original_xy_mm": raw, "engine_xy": integer, "quantized_xy_mm": xy, "quantization_displacement_mm": displacement, "native_quantized_allowed": True, "quantized_minimum_extra_clearance_mm": margins[0][0], "same_component_as_native_receipt_proved_by_margin": True, "original_trace_margin_mm": original_trace_margin, "native_constraint_count": len(constraints) + 1, "native_nearest_constraints": [{"extra_clearance_mm": d, "object": ob, "category": cat} for d, ob, cat in margins[:5]], "excluded_regenerable_gnd_zone_ids": excluded})
    assert len(fixture["cases"]) == 4
    paths = [args.model / "model.json", args.model / "routing.dsn", args.native, Path(model["physical_board"]), args.receipt,
             ROOT / "vendor/freerouting-2.1.0.jar", ROOT / "tests/clearance-audit/NativeViaEscapeControl.java",
             ROOT / "tests/clearance-audit/native_via_escape_audit.py", Path(__file__),
             ROOT / "tests/clearance-audit/build/app/freerouting/board/NativeViaEscapeControl.class"]
    paths += [ROOT / name for name in model["adapter_sources"]]
    paths += list((ROOT / "build").rglob("*.class"))
    fixture["bound_files_sha256"] = {str(p.resolve().relative_to(ROOT)): sha(p) for p in sorted(set(paths))}
    args.output.write_text(json.dumps(fixture, indent=2) + "\n")
    print(json.dumps({"fixture": str(args.output), "sha256": sha(args.output), "board_sha256": fixture["board_sha256"], "cases": [{"pad": c["pad"], "xy_mm": c["quantized_xy_mm"], "native_minimum_extra_clearance_mm": c["quantized_minimum_extra_clearance_mm"]} for c in fixture["cases"]]}))


if __name__ == "__main__":
    main()
