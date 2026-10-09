#!/usr/bin/env python3
"""Extract two real F.Cu contacts for a geometry-only Java regression."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    tests = Path(__file__).resolve().parent
    output = args.output.resolve()
    if not output.is_relative_to(tests):
        raise SystemExit("Fixture output must stay inside ordinary-routing/tests")
    source_bytes = args.source_model.read_bytes()
    model = json.loads(source_bytes)
    contacts = [c for c in model["contacts"]
                if c["key"] in {"J4.3", "R22.1"} and c["layer"] == "F.Cu"]
    assert len(contacts) == 2 and {c["key"] for c in contacts} == {"J4.3", "R22.1"}
    assert all(c["net"] == "SERVO3_EXT" and c["owners"] == ["SERVO3_EXT"]
               and len(c["convex"]) == 1 for c in contacts)
    assert {c["key"]: c["plated"] for c in contacts} == {"J4.3": True, "R22.1": False}
    labels = {c["uuid"] + ":copper" for c in contacts}
    guards = [g for g in model["guards"]
              if g["label"] in labels and g["layer"] == "F.Cu" and g["kind"] == "foreign"]
    assert len(guards) == 2 and {g["label"] for g in guards} == labels
    assert all(g["owners"] == ["SERVO3_EXT"] for g in guards)
    points = [p for c in contacts for polygon in c["convex"] for p in polygon]
    x0, x1 = min(p[0] for p in points) - 2, max(p[0] for p in points) + 2
    y0, y1 = min(p[1] for p in points) - 2, max(p[1] for p in points) + 2
    layers = model["layers"]
    dsn = ['(pcb "native-target-shape-control"',
           '(parser (string_quote ") (space_in_quoted_tokens on) (host_cad "KiCad") (host_version "10.0.6"))',
           '(resolution mm 100000) (unit mm) (structure']
    dsn += [f'(layer {layer} (type signal) (property (index {i})))' for i, layer in enumerate(layers)]
    dsn += [f'(boundary (rect pcb {x0:.6f} {-y1:.6f} {x1:.6f} {-y0:.6f}))',
            '(via "VIA_450_200") (rule (width 0.127) (clearance 0.127)))',
            '(placement) (library (padstack "VIA_450_200"']
    dsn += [f'(shape (circle {layer} 0.45))' for layer in layers]
    dsn += ['(attach off)))', '(network (net "SERVO3_EXT" (pins))',
            '(class "ordinary" "SERVO3_EXT" (circuit (use_via "VIA_450_200"))',
            '(rule (width 0.127) (clearance 0.127))))', '(wiring))']
    dsn_bytes = ("\n".join(dsn) + "\n").encode()
    fixture = {
        "schema": "f722-native-target-shape-fixture/v1",
        "source_model_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_board_sha256": model["board_sha256"],
        "dsn_sha256": hashlib.sha256(dsn_bytes).hexdigest(),
        "fixture_only": True,
        "route_solver_used": False,
        "contacts": contacts,
        "guards": guards,
        "legacy_disconnected_endpoint_mm": [9.66816, 8.51561],
        "trace_half_width_engine_units": 6350,
        "target_safety_margin_engine_units": 2,
        "plated_extra_target_depth_engine_units": 10000,
        "smt_extra_target_depth_engine_units": 0,
        "depth_evidence_scope": "Nominal extra outer-boundary target depth only; not a manufacturing tolerance or a universal annulus-clearance guarantee.",
        "caveat": "These two pads are convex. Per-piece erosion of a decomposed concave pad can discard legal copper across internal seams.",
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "model.json").write_text(json.dumps(fixture, indent=2) + "\n")
    (output / "routing.dsn").write_bytes(dsn_bytes)
    print(json.dumps({"fixture": str(output), "contacts": len(contacts), "guards": len(guards),
                      "source_model_sha256": fixture["source_model_sha256"]}))


if __name__ == "__main__":
    main()
