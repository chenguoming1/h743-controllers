#!/usr/bin/env python3
"""Read-only KiCad 10 signal inventory; run using KiCad's pcbnew Python.

The existing exact native exporter supplies copper contours. This file does not
fill zones, save a board, alter a project, or silently substitute a board.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import pcbnew as p

I2C = {"BARO_SCL": ["U1.61", "U4.4", "R7.2"],
       "BARO_SDA": ["U1.62", "U4.3", "R8.2"]}
CRITICAL = ["USB_P", "USB_N", "HSE_IN", "HSE_OUT", "HSE_XTAL_OUT"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def uid(item):
    return item.m_Uuid.AsString()


def block(text, name):
    start = text.index("(" + name)
    depth = 0
    quoted = escaped = False
    for i in range(start, len(text)):
        c = text[i]
        if escaped:
            escaped = False
            continue
        if quoted and c == "\\":
            escaped = True
        elif c == '"':
            quoted = not quoted
        elif not quoted:
            depth += (c == "(") - (c == ")")
            if depth == 0:
                return text[start:i + 1]
    raise ValueError("Unclosed native " + name)


def stackup(text):
    raw = block(text, "stackup")
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]', raw)
    roots, stack = [], []
    for t in tokens:
        if t == "(":
            row = []
            (stack[-1] if stack else roots).append(row)
            stack.append(row)
        elif t == ")":
            stack.pop()
        else:
            stack[-1].append(json.loads(t) if t.startswith('"') else t)
    rows = []
    for entry in roots[0][1:]:
        if isinstance(entry, list) and entry[0] == "layer":
            row = {"name": entry[1]}
            for child in entry[2:]:
                if not isinstance(child, list) or len(child) != 2:
                    raise ValueError("Unsupported multi-material/native stackup entry")
                row[child[0]] = (float(child[1]) if child[0] in
                                ["thickness", "epsilon_r", "loss_tangent"] else child[1])
            rows.append(row)
    return {"native_block_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "layers": rows, "manufacturing_confirmation": "Not established by native file"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", type=Path, required=True)
    ap.add_argument("--native-tools-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    board = args.board.resolve()
    before = sha(board)
    project = board.with_suffix(".kicad_pro")
    project_before = sha(project) if project.exists() else None
    tools_dir = args.native_tools_dir.resolve()
    sys.path.insert(0, str(tools_dir))
    spec = importlib.util.spec_from_file_location("exact_signal_export", tools_dir / "export_native_copper.py")
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    geometry = exporter.export(board)
    if geometry["board_sha256"] != before:
        raise RuntimeError("Board changed between read-only reads")
    b = p.LoadBoard(str(board))
    if project_before:
        settings = p.GetSettingsManager()
        settings.LoadProject(str(project))
        b.SetProject(settings.GetProject(str(project)))
        b.SynchronizeNetsAndNetClasses(False)
    b.BuildConnectivity()
    cn = b.GetConnectivity()
    pads, tracks = list(b.GetPads()), list(b.GetTracks())
    zones = [z for z in b.Zones() if not z.GetIsRuleArea()]
    net_rows = {}
    for net in list(I2C) + CRITICAL:
        ps = [x for x in pads if x.GetNetname() == net]
        ts = [x for x in tracks if x.GetNetname() == net]
        zs = [x for x in zones if x.GetNetname() == net]
        members = ps + ts + zs
        by_id = {uid(x): x for x in members}
        remaining = set(by_id)
        components = []
        while remaining:
            seed = min(remaining)
            reached = ({uid(x) for x in cn.GetConnectedItems(by_id[seed])} | {seed}) & set(by_id)
            components.append(sorted(reached))
            remaining -= reached
        labels = {uid(x): x.GetParentFootprint().GetReference() + "." + x.GetNumber() for x in ps}
        lengths = {uid(x): x.GetLength() / 1e6 for x in ts if not isinstance(x, p.PCB_VIA)}
        net_rows[net] = {
            "required_terminals": I2C.get(net), "pad_labels_by_uuid": labels,
            "actual_terminals": sorted(labels.values()),
            "terminal_inventory_matches": sorted(labels.values()) == sorted(I2C[net]) if net in I2C else None,
            "native_copper_components": components,
            "all_native_copper_connected": bool(members) and len(components) == 1,
            "all_terminals_connected": bool(ps) and any(set(labels) <= set(c) for c in components),
            "track_native_lengths_mm": lengths,
            "via_own_clearance_by_layer_mm": {uid(x): {b.GetLayerName(l): x.GetOwnClearance(l) / 1e6
                 for l in b.GetEnabledLayers().CuStack() if x.IsOnLayer(l)} for x in ts if isinstance(x, p.PCB_VIA)},
            "zone_uuids": sorted(uid(z) for z in zs),
        }
    ground = []
    for pad in pads:
        ref = pad.GetParentFootprint().GetReference()
        if pad.GetNetname() != "GND" or ref not in {"J1", "D3", "D4", "Y1", "C18", "C19", "U1", "U4"}:
            continue
        connected = list(cn.GetConnectedItems(pad))
        ground.append({"pad": ref + "." + pad.GetNumber(), "uuid": uid(pad),
                       "connected_to_saved_GND_zone": any(isinstance(x, p.ZONE) and x.GetNetname() == "GND" for x in connected)})
    if sha(board) != before or (project_before and sha(project) != project_before):
        raise RuntimeError("Source board/project changed during read-only snapshot")
    args.out.mkdir(parents=True, exist_ok=True)
    geometry_path = args.out / "native-geometry.json"
    geometry_path.write_text(json.dumps(geometry, separators=(",", ":")) + "\n")
    meta = {"schema": "f722-native-signal-snapshot/v1", "board_name": board.name,
            "board_sha256": before, "project_sha256": project_before,
            "native_version": p.Version(), "native_build": p.GetBuildVersion(),
            "geometry_sha256": sha(geometry_path), "source_unchanged": True,
            "sources": {"export_signal_snapshot.py": sha(__file__),
                        "export_native_copper.py": sha(tools_dir / "export_native_copper.py"),
                        "exact_native_contours.py": sha(tools_dir / "exact_native_contours.py")},
            "stackup": stackup(board.read_text()), "nets": net_rows,
            "native_design_max_error_mm": b.GetDesignSettings().m_MaxError / 1e6,
            "ground_zone_clearances": [{"uuid": uid(z), "layers": [b.GetLayerName(l) for l in z.GetLayerSet().Seq()],
                                         "local_clearance_mm": z.GetLocalClearance() / 1e6} for z in zones if z.GetNetname() == "GND"],
            "critical_ground_returns": ground,
            "limits": "Saved native fill and connectivity only; no zone refill, DRC or manufacture qualification."}
    (args.out / "native-signals.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps({"board_sha256": before, "native_version": p.Version(),
                      "I2C": {k: {x: net_rows[k][x] for x in ["actual_terminals", "all_terminals_connected", "all_native_copper_connected"]} for k in I2C}}))


if __name__ == "__main__":
    main()
