"""Inventory all source-component obligations of the shared proposal's 90 cuts."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import time

import native7_recovered_context_v3 as adapter
from prepare_native7_coordinated_context_v3 import replay

H = Path(__file__).resolve().parent
PACKET = H / "native7-common-planning-packet-v1.json"
PACKET_SHA = "b161ae1c4df8632c38bea543c4ddb07e5dcb67afd734f86ef4d931cc1584a051"
OUT = H / "native7-shared-restoration-obligations-v1.json"


def partition(objects, net):
    from shapely.strtree import STRtree
    fragments, bylayer, barrels = [], defaultdict(list), defaultdict(list)
    for record, copper, masks, drill in objects:
        if record["net"] != net:
            continue
        for layer, shape in copper.items():
            for polygon in (list(shape.geoms) if hasattr(shape, "geoms") else [shape]):
                assert polygon.geom_type == "Polygon" and polygon.is_valid
                i = len(fragments)
                fragments.append((record["uuid"], layer, polygon))
                bylayer[layer].append(i)
                if record["kind"] == "via" or record.get("plated"):
                    barrels[record["uuid"]].append(i)
    parent = list(range(len(fragments)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        i, j = find(i), find(j)
        if i != j:
            parent[j] = i

    for ids in bylayer.values():
        tree = STRtree([fragments[i][2] for i in ids])
        for position, i in enumerate(ids):
            for j in tree.query(fragments[i][2], predicate="intersects"):
                if int(j) > position:
                    union(i, ids[int(j)])
    for ids in barrels.values():
        for i in ids[1:]:
            union(ids[0], i)
    groups, byid = defaultdict(set), defaultdict(set)
    for i, (uid, layer, polygon) in enumerate(fragments):
        groups[find(i)].add(uid)
        byid[uid].add(find(i))
    return list(groups.values()), byid


def run():
    start = time.monotonic()
    assert adapter.digest(PACKET) == PACKET_SHA
    g = adapter.load()
    proposal, c, cuts, held, added, reservation, reserved_via = replay(g)
    packet = json.loads(PACKET.read_text())
    assert sorted(cuts) == packet["removed_native_ids"]
    affected = sorted({g.by[uid]["net"] for uid in cuts})
    zones = []
    for zone in g.N["zones"]:
        if zone["rule"] or zone["net"] not in affected:
            continue
        copper = {layer: g.s.geom(polygons) for layer, polygons in zone["filled"].items() if polygons}
        if copper:
            zones.append(({"uuid": zone["uuid"], "net": zone["net"], "kind": "saved_native_zone"}, copper, {}, None))
    before = list(g.BASE) + zones
    after = held + added + [reserved_via] + zones
    boundary = defaultdict(set)
    for row in packet["donor_boundary_contacts"]:
        boundary[row["net"]].add(row["retained_uuid"])
    for contacts in packet["C_scope_restoration_contacts"].values():
        for row in contacts:
            uid = row["retained_uuid"]
            if uid not in cuts:
                boundary[g.by[uid]["net"]].add(uid)
    results = []
    for net in affected:
        terminals = {o["uuid"] for o in g.N["objects"] if o["net"] == net and o["kind"] == "pad"}
        terminals.update(boundary[net])
        assert not terminals.intersection(cuts)
        old, _ = partition(before, net)
        new, _ = partition(after, net)
        old_terminal_groups = [sorted(group.intersection(terminals)) for group in old if group.intersection(terminals)]
        new_terminal_groups = [sorted(group.intersection(terminals)) for group in new if group.intersection(terminals)]
        broken = []
        for group in old_terminal_groups:
            pieces = [sorted(set(group).intersection(other)) for other in new_terminal_groups if set(group).intersection(other)]
            if len(pieces) > 1:
                broken.append({"source_connected_terminals": group, "proposal_partition": pieces,
                               "required_merges_to_restore_source_connectivity": len(pieces) - 1})
        keys = {uid: g.by[uid].get("key", uid) for uid in terminals}
        results.append({"net": net, "removed_native_count": sum(g.by[uid]["net"] == net for uid in cuts),
                        "retained_terminal_count": len(terminals), "terminal_labels": keys,
                        "source_terminal_components": old_terminal_groups,
                        "proposal_terminal_components": new_terminal_groups,
                        "source_component_restorations_required": broken,
                        "new_required_merges": sum(q["required_merges_to_restore_source_connectivity"] for q in broken),
                        "existing_source_open_components_preserved_as_separate_obligations": len(old_terminal_groups),
                        "includes_saved_native_filled_zones": any(z[0]["net"] == net for z in zones),
                        "all_terminal_UUIDs_present": all(uid in g.by for uid in terminals)})
    out = {"schema": "f722-native7-shared-restoration-obligations/v1", "source": g.binding(),
           "packet_sha256": PACKET_SHA, "script_sha256": adapter.digest(__file__),
           "native_cut_count": len(cuts), "affected_nets": affected, "nets": results,
           "required_complete_functions": packet["required_complete_functions"],
           "all_declared_removed_nets_accounted": {q["net"] for q in results} == set(affected),
           "method": "Exact copper polygon fragments and physical plated/via barrels; all retained pads and finite cut-boundary terminals; no topology tolerance or contour repair.",
           "ground_plane_limit": "Saved source-native filled zones are included for original DC component bookkeeping only. New signal antipads and final fill/neck/reference/AC/VCAP performance are not qualified.",
           "no_complete_candidate_claimed": True, "routing_started": False,
           "seconds": time.monotonic() - start}
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"nets": [{"net": q["net"], "cuts": q["removed_native_count"],
                                "source_components": len(q["source_terminal_components"]),
                                "proposal_components": len(q["proposal_terminal_components"]),
                                "restoration_merges": q["new_required_merges"]} for q in results],
                      "seconds": out["seconds"], "sha256": adapter.digest(OUT)}), flush=True)


if __name__ == "__main__":
    run()
