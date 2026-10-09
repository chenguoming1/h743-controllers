#!/usr/bin/env python3
"""Read-only KiCad 10 native geometry snapshot in millimetres.

Run with KiCad's Python (pcbnew). No polygons are inferred from footprint
names. UUIDs, duplicate pad numbers, real layers, drill capsules, mask openings,
zone holes and provenance are retained. Run physical checks separately with
Shapely so the KiCad and analysis Python ABIs need not match.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pcbnew as p

ERROR_IU = 10  # 0.00001 mm at KiCad's 1 nm integer resolution.


def xy(v):
    return [v.x / 1e6, v.y / 1e6]


def polygons(s):
    return [{"outer": [xy(s.Outline(i).CPoint(j)) for j in range(s.Outline(i).PointCount())],
             "holes": [[xy(s.Hole(i, h).CPoint(j)) for j in range(s.Hole(i, h).PointCount())]
                       for h in range(s.HoleCount(i))]}
            for i in range(s.OutlineCount())]


def shape_polygons(item, layer, error_loc=p.ERROR_OUTSIDE, clearance=0):
    s = p.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(s, layer, clearance, ERROR_IU, error_loc)
    return polygons(s)


def drill(item):
    h = item.GetEffectiveHoleShape()
    if not h or h.GetWidth() <= 0:
        return None
    d = {"start": xy(h.GetStart()), "end": xy(h.GetEnd()), "width": h.GetWidth() / 1e6}
    for key, loc in [("outside", p.ERROR_OUTSIDE), ("inside", p.ERROR_INSIDE)]:
        poly = p.SHAPE_POLY_SET()
        h.TransformToPolygon(poly, ERROR_IU, loc)
        d[key] = polygons(poly)
    return d


def drawing(item, board):
    d = {"uuid": item.m_Uuid.AsString(), "layer": board.GetLayerName(item.GetLayer()),
         "shape": item.GetShapeStr(), "start": xy(item.GetStart()), "end": xy(item.GetEnd()),
         "width": item.GetWidth() / 1e6}
    if d["shape"] == "Arc":
        d["mid"] = xy(item.GetArcMid())
    if d["shape"] == "Circle":
        d["center"] = xy(item.GetCenter())
    if d["shape"] == "Polygon":
        d["polygons"] = polygons(item.GetPolyShape())
    return d


def export(board_path):
    before = hashlib.sha256(board_path.read_bytes()).hexdigest()
    b = p.LoadBoard(str(board_path))
    layers = list(b.GetEnabledLayers().CuStack())
    layer_names = [b.GetLayerName(x) for x in layers]
    items, fps, zones = [], [], []
    for f in sorted(b.GetFootprints(), key=lambda x: x.GetReference()):
        fid = f.m_Uuid.AsString()
        fps.append({"uuid": fid, "ref": f.GetReference(), "value": f.GetValue(),
                    "fpid": str(f.GetFPID().GetLibNickname()) + ":" + str(f.GetFPID().GetLibItemName()),
                    "xy": xy(f.GetPosition()), "angle": f.GetOrientationDegrees(), "side": f.GetLayerName(),
                    "graphics": [drawing(g, b) for g in f.GraphicalItems() if isinstance(g, p.PCB_SHAPE)]})
        for a in f.Pads():
            at = a.GetAttribute()
            q = {"uuid": a.m_Uuid.AsString(), "kind": "pad", "footprint_uuid": fid,
                 "ref": f.GetReference(), "number": a.GetNumber(), "key": f.GetReference() + "." + a.GetNumber(),
                 "net": a.GetNetname(), "net_code": a.GetNetCode(), "xy": xy(a.GetPosition()),
                 "angle": a.GetOrientationDegrees(), "size": xy(a.GetSize()), "offset": xy(a.GetOffset()),
                 "attribute": at, "smd": at == p.PAD_ATTRIB_SMD, "npth": at == p.PAD_ATTRIB_NPTH,
                 "plated": at == p.PAD_ATTRIB_PTH, "all_layers": [b.GetLayerName(l) for l in a.GetLayerSet().Seq()],
                 "copper": {}, "inside": {}, "mask": {}, "shape_by_layer": {}, "drill": drill(a)}
            for l in layers:
                if a.IsOnLayer(l):
                    name = b.GetLayerName(l)
                    q["shape_by_layer"][name] = a.GetShape(l)
                    if a.FlashLayer(l):
                        q["copper"][name] = shape_polygons(a, l)
                        q["inside"][name] = shape_polygons(a, l, p.ERROR_INSIDE)
            for l in [p.F_Mask, p.B_Mask]:
                if a.IsOnLayer(l):
                    expansion = a.GetSolderMaskExpansion(l)
                    q["mask"][b.GetLayerName(l)] = {"expansion": expansion / 1e6,
                                                   "polygons": shape_polygons(a, l, clearance=expansion)}
            q["barrel_layers"] = layer_names if q["plated"] and q["drill"] else []
            items.append(q)
        for z in f.Zones():
            zones.append((z, fid, f.GetReference()))
    for a in b.GetTracks():
        via = isinstance(a, p.PCB_VIA)
        q = {"uuid": a.m_Uuid.AsString(), "kind": "via" if via else "arc" if isinstance(a, p.PCB_ARC) else "track",
             "net": a.GetNetname(), "net_code": a.GetNetCode(), "start": xy(a.GetStart()), "end": xy(a.GetEnd()),
             "width": (a.GetWidth(a.TopLayer()) if via else a.GetWidth()) / 1e6, "copper": {}, "plated": via, "mask": {}, "drill": drill(a) if via else None}
        if isinstance(a, p.PCB_ARC):
            q["mid"] = xy(a.GetMid())
        if via:
            q.update(xy=xy(a.GetPosition()), via_type=a.GetViaType(),
                     top_layer=b.GetLayerName(a.TopLayer()), bottom_layer=b.GetLayerName(a.BottomLayer()),
                     tented={b.GetLayerName(l): a.IsTented(l) for l in [p.F_Mask, p.B_Mask]})
        q["barrel_layers"] = [b.GetLayerName(l) for l in layers if a.IsOnLayer(l)] if via else []
        q["width_by_layer"] = {b.GetLayerName(l): a.GetWidth(l) / 1e6 for l in layers if a.IsOnLayer(l)} if via else {b.GetLayerName(a.GetLayer()): a.GetWidth() / 1e6}
        for l in layers:
            if a.IsOnLayer(l) and (not via or a.FlashLayer(l)):
                q["copper"][b.GetLayerName(l)] = shape_polygons(a, l)
        if via:
            for l, cu in [(p.F_Mask, p.F_Cu), (p.B_Mask, p.B_Cu)]:
                if a.IsOnLayer(cu) and not a.IsTented(l):
                    q["mask"][b.GetLayerName(l)] = {"polygons": shape_polygons(a, l)}
        items.append(q)
    zones += [(z, None, None) for z in b.Zones()]
    zone_data = []
    for z, fid, ref in zones:
        q = {"uuid": z.m_Uuid.AsString(), "owner_uuid": fid, "owner_ref": ref, "name": z.GetZoneName(),
             "net": z.GetNetname(), "net_code": z.GetNetCode(), "rule": z.GetIsRuleArea(),
             "layers": [b.GetLayerName(l) for l in z.GetLayerSet().Seq()], "outline": polygons(z.Outline()),
             "forbid": {kind: getattr(z, method)() for kind, method in [
                 ("tracks", "GetDoNotAllowTracks"), ("vias", "GetDoNotAllowVias"), ("pads", "GetDoNotAllowPads"),
                 ("footprints", "GetDoNotAllowFootprints"), ("copper", "GetDoNotAllowZoneFills")]}, "filled": {}}
        if not q["rule"]:
            for l in layers:
                if z.IsOnLayer(l) and z.HasFilledPolysForLayer(l):
                    q["filled"][b.GetLayerName(l)] = polygons(z.GetFilledPolysList(l))
        zone_data.append(q)
    outline = p.SHAPE_POLY_SET()
    native_outline_error = b.GetDesignSettings().m_MaxError / 1e6
    outline_ok = b.GetBoardPolygonOutlines(outline, False, None, False, True)
    result = {"schema": "kicad-native-copper/v1", "board_name": board_path.name, "board_sha256": before,
              "native_version": p.Version(), "native_build": p.GetBuildVersion(),
              "units": "mm", "maximum_polygon_error_mm": ERROR_IU / 1e6,
              "copper_error_location": "ERROR_OUTSIDE", "pad_cut_error_location": "ERROR_INSIDE",
              "copper_layers": layer_names, "copper_layer_ids": {b.GetLayerName(l): l for l in layers},
              "board_thickness_mm": b.GetDesignSettings().GetBoardThickness() / 1e6,
              "outline_with_npth": {"valid": outline_ok, "native_design_max_error_mm": native_outline_error, "polygons": polygons(outline)},
              "edge_cuts": [drawing(g, b) for g in b.GetDrawings() if isinstance(g, p.PCB_SHAPE) and g.GetLayer() == p.Edge_Cuts],
              "footprints": fps, "objects": sorted(items, key=lambda x: x["uuid"]),
              "zones": sorted(zone_data, key=lambda x: x["uuid"])}
    if hashlib.sha256(board_path.read_bytes()).hexdigest() != before:
        raise RuntimeError("Input board changed during read-only export")
    result["source_unchanged"] = True
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = export(args.board)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print(json.dumps({"sha256": result["board_sha256"], "objects": len(result["objects"]),
                      "zones": len(result["zones"]), "out": str(args.out)}))


if __name__ == "__main__":
    main()
