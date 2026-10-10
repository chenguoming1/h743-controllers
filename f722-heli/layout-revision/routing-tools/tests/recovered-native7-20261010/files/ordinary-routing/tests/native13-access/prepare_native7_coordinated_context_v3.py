"""Exact shared proposal replay and finite/contact gate; never searches routes."""
import hashlib
import json
import math
from pathlib import Path
import time

import native7_recovered_context_v3 as adapter

H = Path(__file__).resolve().parent
ROOT = H.parents[2]
PROPOSAL = H / "native7-coordinated-engineering-proposal-v1.json"
C_SCOPE = ROOT / "recovered-native7/recovery-C/native7-C-compact-scope-receipt-v4.json"
EXPECTED_PROPOSAL = "c08b9dbf202cfb81abc19022d97d7b152cc02a333e435e7a0b0611ae6be69291"
EXPECTED_C_SCOPE = "b70b00911dbcade6e97470d6a5cb593a122b20af1dcc4672e00711c107f61534"
OUT = H / "native7-coordinated-context-finite-v3.json"


def read_bound(path, expected):
    if adapter.digest(path) != expected:
        raise ValueError("Input hash differs: " + str(path))
    return json.loads(path.read_text())


def replay(g):
    proposal = read_bound(PROPOSAL, EXPECTED_PROPOSAL)
    c = read_bound(C_SCOPE, EXPECTED_C_SCOPE)
    assert proposal["source"]["native_sha256"] == c["native_binding"]["sha256"] == adapter.NATIVE_SHA256
    cuts = {uid for group in proposal["native_removal_groups"].values() for uid in group["native_ids"]}
    assert len(cuts) == proposal["native_removal_count"] == 66
    for group in proposal["native_removal_groups"].values():
        for member in group["members"]:
            source = g.by[member["uuid"]]
            digest = hashlib.sha256(json.dumps(source, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            assert digest == member["source_record_sha256"]
    c_cuts = set(c["mandatory_C_replacement_native_ids"])
    assert len(c_cuts) == 30 and len(cuts.intersection(c_cuts)) == 6
    cuts.update(c_cuts)
    assert len(cuts) == 90 and all(uid in g.by for uid in cuts)
    held = [entry for entry in g.BASE if entry[0]["uuid"] not in cuts]
    added = []
    for row in proposal["proposed_common_routes"]:
        added.append(g.track(row["net"], row["layer"], row["points"], row["name"], row["width"]))
    for row in proposal["proposed_common_vias"]:
        added.append(g.via(row["net"], row["xy"], row["name"]))
    reservation = dict(proposal["planning_only_reservations"][0], name="planning-RX-up-eastern-via")
    q = g.via(reservation["net"], reservation["xy"], reservation["name"])
    q = (dict(q[0], role="upstream", planning_only=True), q[1], q[2], q[3])
    return proposal, c, cuts, held, added, reservation, q


def run():
    from shapely.geometry import LineString, Point
    start = time.monotonic()
    g = adapter.load()
    proposal, c, cuts, held, added, reservation, reserved_via = replay(g)
    objects = held + added + [reserved_via]
    out = {"schema": "f722-native7-coordinated-context-finite/v3", "source": g.binding(),
           "proposal_sha256": EXPECTED_PROPOSAL, "C_scope_sha256": EXPECTED_C_SCOPE,
           "script_sha256": adapter.digest(__file__), "removed_native_ids": sorted(cuts),
           "held_native_count": len(held), "proposed_routes": proposal["proposed_common_routes"],
           "proposed_vias": proposal["proposed_common_vias"], "planning_only_reservation": reservation,
           "finite_checks": [], "source_pad_entry_checks": [], "barrel_contacts": [],
           "native_retained_records_unchanged": True, "routing_started": False,
           "complete_transaction": False, "native_selected": False}
    for row in proposal["proposed_common_routes"]:
        checks = g.check_track(row["net"], row["layer"], row["points"], width=row["width"], objects=objects)
        out["finite_checks"].append({"name": row["name"], "kind": "track", "width": row["width"],
                                     "passed": all(x["pass_with_polygon_error"] for x in checks),
                                     "nearest": checks[:5], "failed": [x for x in checks if not x["pass_with_polygon_error"]]})
    for row in proposal["proposed_common_vias"] + [reservation]:
        peers = [q for q in objects if q[0]["uuid"] != row["name"]]
        # Preserve the other physical branch as a foreign obstacle for the RX-up
        # planning barrel. Other actual bonded U15 pads remain foreign normally.
        if row["name"] == reservation["name"]:
            roles = c["protected_branch_role_metadata"]
            peers = [(dict(o, net=o["net"] + "::downstream") if
                      roles.get(o["uuid"], {}).get("role") == "downstream" and o["net"] == row["net"] else o,
                      copper, masks, drill) for o, copper, masks, drill in peers]
        checks = g.check_via(row["net"], row["xy"], objects=peers)
        out["finite_checks"].append({"name": row["name"], "kind": "via",
                                     "passed": all(x["pass_with_polygon_error"] for x in checks),
                                     "nearest": checks[:5], "failed": [x for x in checks if not x["pass_with_polygon_error"]]})
    # Full-width actual-pad cross-sections at every proposed terminal endpoint.
    target_keys = {"recovered-four-source-1": "U1.33", "recovered-four-source-2": "U1.34",
                   "recovered-four-source-3": "U1.35", "recovered-four-source-4": "U1.36",
                   "recovered-flash-target-0": "U3.6", "recovered-flash-target-1": "U3.5",
                   "recovered-B-access-0": "U1.37", "recovered-B-access-1": "R32.2",
                   "recovered-B-access-2": "U1.38", "recovered-C-source-0": "U1.28",
                   "recovered-C-source-1": "U1.29", "recovered-U2-9-ground-0": "U2.9"}
    for row in proposal["proposed_common_routes"]:
        if row["name"] not in target_keys:
            continue
        pad = g.one_pad(target_keys[row["name"]])
        shape = g.s.geom(pad["inside"][row["layer"]])
        choices = [(row["points"][0], row["points"][1]), (row["points"][-1], row["points"][-2])]
        witnesses = []
        for point, neighbor in choices:
            if not shape.covers(Point(point)):
                continue
            dx, dy = neighbor[0] - point[0], neighbor[1] - point[1]
            length = math.hypot(dx, dy)
            radius = row["width"] / 2 / math.cos(math.pi / 512)
            nx, ny = -dy / length * radius, dx / length * radius
            section = LineString([(point[0] - nx, point[1] - ny), (point[0] + nx, point[1] + ny)])
            witnesses.append({"point": point, "cross_section": list(section.coords),
                              "cross_section_mm": section.length, "covered_by_actual_pad_inside": shape.covers(section)})
        out["source_pad_entry_checks"].append({"route": row["name"], "actual_pad": pad["key"],
                                               "pad_uuid": pad["uuid"], "width_mm": row["width"],
                                               "witnesses": witnesses,
                                               "passed": any(x["covered_by_actual_pad_inside"] for x in witnesses)})
    # Exact same-net finite contact list for each new route, including inherited
    # returns. This records sharing rather than assuming any same-net join is safe.
    for entry in added:
        record, copper, masks, drill = entry
        if record["kind"] != "track":
            continue
        for peer, pc, pm, pd in objects:
            if peer["kind"] != "via" or peer["net"] != record["net"]:
                continue
            shared = []
            for layer in set(copper).intersection(pc):
                area = copper[layer].intersection(pc[layer]).area
                if area > 0:
                    shared.append({"layer": layer, "overlap_mm2": area})
            if shared:
                out["barrel_contacts"].append({"route": record["uuid"], "via_uuid": peer["uuid"],
                                                "via_xy": peer["xy"], "shared": shared})
    # Preserve the exact replacement scope boundary as complete obligations.
    out["donor_boundary_contacts"] = []
    for label, group in proposal["native_removal_groups"].items():
        for uid in group["native_ids"]:
            old = next(q for q in g.BASE if q[0]["uuid"] == uid)
            for peer in held:
                if peer[0]["net"] != old[0]["net"]:
                    continue
                for layer in set(old[1]).intersection(peer[1]):
                    area = old[1][layer].intersection(peer[1][layer]).area
                    if area > 0:
                        out["donor_boundary_contacts"].append({"group": label, "removed_uuid": uid,
                          "retained_uuid": peer[0]["uuid"], "retained_key": peer[0].get("key"),
                          "net": peer[0]["net"], "layer": layer, "overlap_mm2": area})
    out["C_scope_restoration_contacts"] = {name: scope["finite_contacts"] for name, scope in c["scopes"].items() if scope.get("remove_for_v24", False)}
    out["finite_gate_passed"] = all(x["passed"] for x in out["finite_checks"]) and all(x["passed"] for x in out["source_pad_entry_checks"])
    out["pending_complete_donors"] = list(proposal["native_removal_groups"]) + [name for name, scope in c["scopes"].items() if scope.get("remove_for_v24", False)]
    out["seconds"] = time.monotonic() - start
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"finite_gate_passed": out["finite_gate_passed"], "failures": [x["name"] for x in out["finite_checks"] if not x["passed"]],
                      "pad_failures": [x["route"] for x in out["source_pad_entry_checks"] if not x["passed"]],
                      "native_cuts": len(cuts), "seconds": out["seconds"], "receipt_sha256": adapter.digest(OUT)}), flush=True)


if __name__ == "__main__":
    run()
