#!/usr/bin/env python3
"""Bind a routed main-board placement to an isolated source overlay.

Run only with the approved KiCad 10.0.7 Python runtime. This tool does not
modify the supplied PCB or source tree. It never refills or runs DRC. Native
floorplan generation and position export are explicit, separate options so
the caller can coordinate the shared native-operation lane.
"""
import argparse
import copy
import csv
import hashlib
import importlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

import pcbnew


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def ref_key(ref):
    match = re.fullmatch(r"(.*?)(\d+)", ref)
    return (match[1], int(match[2])) if match else (ref, 0)


def norm_angle(degrees):
    return round(degrees % 360, 6) % 360


def near_equal(expected, actual):
    """Allow only 2 nm of coordinate quantization from KiCad FromMM floats."""
    if isinstance(expected, float) and isinstance(actual, (int, float)):
        return math.isclose(expected, actual, rel_tol=0, abs_tol=0.000002)
    if isinstance(expected, dict) and isinstance(actual, dict):
        return set(expected) == set(actual) and all(near_equal(expected[k], actual[k]) for k in expected)
    if isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        return len(expected) == len(actual) and all(near_equal(x, y) for x, y in zip(expected, actual))
    return expected == actual


def mm(point):
    return [round(pcbnew.ToMM(point.x), 6), round(pcbnew.ToMM(point.y), 6)]


def footprint_id(fp):
    return fp.GetFPID().GetUniStringLibId()


def board_snapshot(board):
    result = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        assert ref not in result, ("duplicate reference", ref)
        pads = []
        for pad in fp.Pads():
            pads.append({
                "number": pad.GetNumber(), "net": pad.GetNetname(),
                "position_mm": mm(pad.GetPosition()),
                "orientation_deg": norm_angle(pad.GetOrientationDegrees()),
                "size_mm": mm(pad.GetSize()),
                "drill_mm": mm(pad.GetDrillSize()),
                "shape": int(pad.GetShape()),
                "roundrect_radius_mm": round(pcbnew.ToMM(pad.GetRoundRectCornerRadius()), 6),
                "attribute": int(pad.GetAttribute()),
                "copper_layers": [int(layer) for layer in pad.GetLayerSet().CuStack()],
                "surface_layers": [name for name, layer in (
                    ("F.Paste", pcbnew.F_Paste), ("B.Paste", pcbnew.B_Paste),
                    ("F.Mask", pcbnew.F_Mask), ("B.Mask", pcbnew.B_Mask)) if pad.IsOnLayer(layer)],
            })
        result[ref] = {
            "footprint": footprint_id(fp), "value": fp.GetValue(),
            "lcsc": fp.GetFieldText("LCSC"),
            "position_mm": mm(fp.GetPosition()),
            "orientation_deg": norm_angle(fp.GetOrientationDegrees()),
            "side": "B" if fp.GetLayer() == pcbnew.B_Cu else "F",
            "pads": sorted(pads, key=lambda p: (p["number"], p["position_mm"], p["net"])),
        }
    return result


def verify_identities_and_nets(parts, snapshot):
    expected = {p["ref"]: p for p in parts}
    assert set(expected) == set(snapshot), {
        "missing": sorted(set(expected) - set(snapshot)),
        "extra": sorted(set(snapshot) - set(expected)),
    }
    failures = []
    for ref, part in expected.items():
        actual = snapshot[ref]
        for source_name, actual_name in (("fp", "footprint"), ("value", "value"), ("lcsc", "lcsc")):
            if part[source_name] != actual[actual_name]:
                failures.append([ref, source_name, part[source_name], actual[actual_name]])
        found = {pad["number"] for pad in actual["pads"]}
        for number in part["pins"]:
            if number not in found:
                failures.append([ref, "missing physical pin", number])
        for pad in actual["pads"]:
            number, net = pad["number"], pad["net"]
            intended = part["pins"].get(number)
            if intended is not None and net != intended:
                failures.append([ref, number, intended, net])
            elif intended is None and net and not net.startswith("unconnected-(" + ref):
                failures.append([ref, number, "no-connect or no assigned net", net])
    assert not failures, failures


def inverse_source_angle(actual_angle, side):
    # Derive the inverse through the running KiCad implementation. Do not
    # assume a backside convention or simply copy the final orientation.
    probe_board = pcbnew.BOARD()
    probe = pcbnew.FOOTPRINT(probe_board)
    probe.SetLayer(pcbnew.B_Cu if side == "B" else pcbnew.F_Cu)
    probe.SetOrientationDegrees(actual_angle)
    if side == "B":
        probe.Flip(probe.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    return norm_angle(probe.GetOrientationDegrees())


def extract_placements(snapshot, origin, shift, Board):
    placements = {}
    replay = Board(*origin, 4)
    for ref in sorted(snapshot, key=ref_key):
        fp = snapshot[ref]
        x, y = fp["position_mm"]
        angle = inverse_source_angle(fp["orientation_deg"], fp["side"])
        source_y = round(y - origin[1] - (0 if ref == "J1" else shift), 6)
        placements[ref] = ("xy", round(x - origin[0], 6), source_y, angle, fp["side"])
        probe = pcbnew.FOOTPRINT(replay.board)
        probe.SetLayer(pcbnew.F_Cu)
        replay.put(probe, x - origin[0], source_y + (0 if ref == "J1" else shift), angle, fp["side"])
        assert near_equal(mm(probe.GetPosition()), fp["position_mm"]), (ref, "position replay failed")
        assert norm_angle(probe.GetOrientationDegrees()) == fp["orientation_deg"], (ref, "rotation replay failed")
        assert ("B" if probe.GetLayer() == pcbnew.B_Cu else "F") == fp["side"], (ref, "side replay failed")
    return placements


def source_literal(placements):
    return "\n".join("    " + repr(ref) + ": " + repr(tuple(placements[ref])) + ","
                     for ref in sorted(placements, key=ref_key))


def patched_design(original, placements, source_hash, geometry_hash):
    if "MAIN_ROUTED_PLACEMENT" in original:
        # Only replace the exact block installed by this helper. Unknown
        # placement implementations must be inspected rather than guessed.
        first = original.index("# Routed main-board placement checkpoint.")
        last = original.index("\ndef get_main_parts():\n", first)
        original = original[:first] + original[last:]
        binding = (
            '    assert set(MAIN_ROUTED_PLACEMENT) == {p["ref"] for p in selected}, "Main placement coverage changed"\n'
            '    for p in selected:\n'
            '        p["place"] = MAIN_ROUTED_PLACEMENT[p["ref"]]\n'
        )
        assert original.count(binding) == 1, "Unknown existing main placement binding"
        original = original.replace(binding, "")
    start = original.index("MAIN_INPUT_CAP_PLACEMENT = {")
    end = original.index("\n}", start) + 2
    input_caps = {ref: placements[ref] for ref in ("C27", "C31", "D5")}
    text = original[:start] + "MAIN_INPUT_CAP_PLACEMENT = {\n" + source_literal(input_caps) + "\n}" + original[end:]
    marker = "\ndef get_main_parts():\n"
    assert text.count(marker) == 1
    manifest = (
        "\n# Routed main-board placement checkpoint. This overrides main-only placement\n"
        "# after component selection; legacy PARTS and sibling projects are unchanged.\n"
        "# Coordinates are generator inputs, not raw PCB angles: Board.put mirrors\n"
        "# bottom footprints, and build_floorplan adds DESIGN_SHIFT except for J1.\n"
        f"# Source PCB SHA256: {source_hash}\n"
        f"# Footprint/pad placement SHA256: {geometry_hash}\n"
        "MAIN_ROUTED_PLACEMENT = {\n" + source_literal(placements) + "\n}\n"
    )
    text = text.replace(marker, "\n" + manifest + marker)
    end_of_selection = '    return selected\n'
    assert text.count(end_of_selection) == 1
    text = text.replace(end_of_selection,
        '    assert set(MAIN_ROUTED_PLACEMENT) == {p["ref"] for p in selected}, "Main placement coverage changed"\n'
        '    for p in selected:\n'
        '        p["place"] = MAIN_ROUTED_PLACEMENT[p["ref"]]\n'
        '    return selected\n')
    compile(text, "design.py", "exec")
    return text


def identity(parts):
    return sorted([{k: v for k, v in p.items() if k != "place"} for p in parts], key=lambda p: ref_key(p["ref"]))


def verify_approved_baseline(baseline, current):
    """Permit exactly the documented main-only U10 land-pattern variant."""
    assert baseline.PARTS == current.PARTS, "Legacy PARTS changed from approved baseline"
    original = identity(baseline.get_main_parts())
    updated = identity(current.get_main_parts())
    old = next(p for p in original if p["ref"] == "U10")
    new = next(p for p in updated if p["ref"] == "U10")
    changes = []
    if old["fp"] != new["fp"]:
        assert (old["fp"], new["fp"]) == (
            "NexusFC:SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BL", "NexusFC:TPS70933DBVR_TI_DBV0005A")
        assert (new["value"], new["lcsc"], new["pins"]) == (
            "TPS70933DBVR", "C89347", {"1": "VSYS", "2": "GND", "3": None, "4": None, "5": "3V3_SENS"})
        changes.append({"ref": "U10", "from_footprint": old["fp"], "to_footprint": new["fp"],
                        "part_lcsc_pin_roles_unchanged": True})
        old["fp"] = new["fp"]
    assert original == updated, "Undocumented identity or pin-role change from approved baseline"
    return {"legacy_parts_unchanged": True, "all_main_identity_fields_except_documented_variant_unchanged": True,
            "documented_footprint_variants": changes}


def compare_floorplan(expected, actual):
    failures = []
    if set(expected) != set(actual):
        failures.append({"field": "references", "expected": sorted(expected), "actual": sorted(actual)})
    for ref in sorted(set(expected) & set(actual), key=ref_key):
        exp, got = expected[ref], actual[ref]
        for key in exp:
            if not near_equal(exp[key], got[key]):
                failures.append({"ref": ref, "field": key, "expected": exp[key], "actual": got[key]})
    return failures


def verify_bom_cpl(out, parts, board, snapshot):
    ordered = {p["ref"]: p for p in parts if p.get("lcsc", "").startswith("C")}
    bom = list(csv.DictReader((out / "nexus-style-fc-bom-jlc.csv").open()))
    bom_refs = {}
    for row in bom:
        for ref in row["Designator"].split(","):
            assert ref not in bom_refs, ("duplicate BOM ref", ref)
            bom_refs[ref] = row
    assert set(bom_refs) == set(ordered), "BOM coverage mismatch"
    for ref, part in ordered.items():
        row = bom_refs[ref]
        assert (row["Comment"], row["Footprint"], row["LCSC Part #"]) == (part["value"], part["fp"].split(":")[1], part["lcsc"]), (ref, row)
    cpl = list(csv.DictReader((out / "nexus-style-fc-cpl-jlc.csv").open()))
    assert len(cpl) == len(ordered), "CPL count mismatch"
    assert {row["Designator"] for row in cpl} == set(ordered), "CPL coverage mismatch"
    ox, oy = mm(board.GetDesignSettings().GetAuxOrigin())
    max_position_error = 0.0
    angles = []
    for row in cpl:
        ref = row["Designator"]
        fp = snapshot[ref]
        x, y = fp["position_mm"]
        err = math.hypot(float(row["Mid X"].removesuffix("mm")) - (x - ox), float(row["Mid Y"].removesuffix("mm")) - (oy - y))
        assert err <= 0.00008, (ref, "CPL origin/position mismatch", err)
        max_position_error = max(max_position_error, err)
        assert row["Layer"] == ("Top" if fp["side"] == "F" else "Bottom"), (ref, "CPL side mismatch")
        angle = float(row["Rotation"])
        angles.append({"ref": ref, "side": fp["side"], "pcb_degrees": fp["orientation_deg"], "cpl_degrees": angle})
        assert norm_angle(angle) == norm_angle(round(fp["orientation_deg"])), (ref, "CPL rotation mismatch", fp["orientation_deg"], angle)
    return {"bom_group_count": len(bom), "ordered_part_count": len(ordered), "cpl_part_count": len(cpl),
            "max_cpl_position_error_mm": max_position_error, "aux_origin_mm": [ox, oy], "rotations": angles}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--pcb", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--verify-floorplan", action="store_true")
    ap.add_argument("--bom-cpl", action="store_true")
    ap.add_argument("--kicad-cli", type=Path)
    ap.add_argument("--approved-baseline-root", type=Path)
    ap.add_argument("--expected-pcb-sha256")
    ap.add_argument("--stock-footprints", type=Path, default=Path("/usr/share/kicad/footprints"))
    args = ap.parse_args()
    assert pcbnew.Version() == "10.0.7", ("Unexpected KiCad runtime", pcbnew.Version())
    assert not args.bom_cpl or args.kicad_cli, "Position export requires the approved kicad-cli path"
    source = args.source_root.resolve()
    pcb = args.pcb.resolve()
    output = args.output.resolve()
    assert output != source and source not in output.parents, "Keep synchronization outputs separate from the source tree"
    assert not output.exists(), "Use a fresh output directory to prevent stale evidence"
    initial_board_hash = digest(pcb)
    if args.expected_pcb_sha256:
        assert initial_board_hash == args.expected_pcb_sha256, "PCB changed after the final native check"
    project = pcb.with_suffix(".kicad_pro")
    source_project = source / "hardware" / "nexus-style-fc.kicad_pro"
    assert project.is_file() and source_project.is_file(), "Native checks require existing project files beside input/source boards"
    project_hash = digest(project)
    source_project_hash = digest(source_project)
    approved_project_hash = None
    if args.approved_baseline_root:
        approved_project_hash = digest(args.approved_baseline_root / "hardware" / "nexus-style-fc.kicad_pro")
        assert project_hash == approved_project_hash, "Input board project does not match approved rules"
        assert source_project_hash == approved_project_hash, "Source project does not match approved rules"
    sys.path.insert(0, str(source / "tools"))
    import design
    import build_floorplan
    import make_footprints
    import pcbutil
    original_parts = copy.deepcopy(design.PARTS)
    original_main = design.get_main_parts()
    board = pcbnew.LoadBoard(str(pcb))
    snapshot = board_snapshot(board)
    verify_identities_and_nets(original_main, snapshot)
    origin = (build_floorplan.OX, build_floorplan.OY)
    shift = make_footprints.DESIGN_SHIFT
    placements = extract_placements(snapshot, origin, shift, pcbutil.Board)
    geometry_hash = stable_hash(snapshot)
    tools_out = output / "source" / "tools"
    tools_out.mkdir(parents=True)
    source_file = source / "tools" / "design.py"
    patched = patched_design(source_file.read_text(), placements, initial_board_hash, geometry_hash)
    (tools_out / "design.py").write_text(patched)
    spec = importlib.util.spec_from_file_location("design", tools_out / "design.py")
    new_design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(new_design)
    assert new_design.PARTS == original_parts, "Legacy PARTS changed"
    new_parts = new_design.get_main_parts()
    assert identity(new_parts) == identity(original_main), "Approved main part identities or pin assignments changed"
    assert new_design.PARTS == original_parts, "Main selection mutated legacy PARTS"
    assert all(p["place"][0] == "xy" for p in new_parts), "Unresolved main auto placement remains"
    baseline_verification = "not requested"
    if args.approved_baseline_root:
        baseline_spec = importlib.util.spec_from_file_location("approved_baseline_design", args.approved_baseline_root / "tools" / "design.py")
        baseline_design = importlib.util.module_from_spec(baseline_spec)
        baseline_spec.loader.exec_module(baseline_design)
        baseline_verification = verify_approved_baseline(baseline_design, new_design)
    report = {
        "status": "source synchronization only; not manufacturing acceptance",
        "kicad_version": pcbnew.Version(), "source_pcb": str(pcb),
        "source_pcb_sha256": initial_board_hash, "source_design_sha256": digest(source_file),
        "generated_design_sha256": digest(tools_out / "design.py"),
        "input_project_sha256": project_hash, "source_project_sha256": source_project_hash,
        "approved_project_sha256": approved_project_hash,
        "approved_baseline_verification": baseline_verification,
        "placement_geometry_sha256": geometry_hash,
        "origin_mm": origin, "design_shift_mm": shift,
        "main_part_count": len(new_parts), "legacy_part_count": len(original_parts),
        "legacy_parts_unchanged": True, "approved_main_parts_and_pin_nets_unchanged": True,
        "all_source_placements_replayed_through_Board_put": True,
        "placements": placements,
        "floorplan_verification": "not requested", "bom_cpl_verification": "not requested",
    }
    verification = output / "verification"
    verification.mkdir()
    if args.verify_floorplan:
        build_floorplan.design = new_design
        build_floorplan.OUT = str(verification / "main-regenerated-floorplan.kicad_pcb")
        pcbutil.STOCK = str(args.stock_footprints)
        build_floorplan.main()
        regenerated = pcbnew.LoadBoard(build_floorplan.OUT)
        differences = compare_floorplan(snapshot, board_snapshot(regenerated))
        report["floorplan_verification"] = {
            "path": build_floorplan.OUT, "routed_pcb_not_overwritten": True,
            "difference_count": len(differences), "differences": differences,
            "coordinate_tolerance_mm": 0.000002,
            "expected_footprints": len(snapshot), "expected_pads": sum(len(fp["pads"]) for fp in snapshot.values()),
        }
    if args.bom_cpl:
        sys.modules["design"] = new_design
        import export_fab
        export_fab.K = str(args.kicad_cli)
        assembly = verification / "bom-cpl"
        assembly.mkdir()
        export_fab.bom_cpl("nexus-style-fc", str(pcb), "design", str(assembly))
        report["bom_cpl_verification"] = verify_bom_cpl(assembly, new_parts, board, snapshot)
    assert digest(pcb) == initial_board_hash, "Input board changed during synchronization"
    assert digest(source_file) == report["source_design_sha256"], "Input source changed during synchronization"
    assert digest(project) == project_hash, "Input project changed during synchronization"
    assert digest(source_project) == source_project_hash, "Source project changed during synchronization"
    report["source_pcb_unchanged"] = True
    report["source_design_unchanged"] = True
    report["input_and_source_projects_unchanged"] = True
    (output / "synchronization-report.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "placement-pad-snapshot.json").write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "main_part_count", "legacy_parts_unchanged", "approved_main_parts_and_pin_nets_unchanged", "source_pcb_unchanged")}, indent=2))
    if args.verify_floorplan:
        assert not report["floorplan_verification"]["differences"], "Floorplan pad/placement parity failed; see synchronization-report.json"


if __name__ == "__main__":
    main()
