"""Two-phase C construction for the exact recovered native7 common packet.

Import performs no geometry work. The integrated routing owner calls prepare()
before shared trunks, keeps every returned object, then calls finish(). Neither
phase edits the board or selects a transaction. Failure returns its input object
list unchanged and retains all attempted centerlines in the receipt.
"""
from __future__ import annotations

from contextlib import contextmanager
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
COMMON = ROOT / "ordinary-routing/tests/native13-access/native7-common-planning-packet-v1.json"
COMMON_SHA = "b161ae1c4df8632c38bea543c4ddb07e5dcb67afd734f86ef4d931cc1584a051"
SCOPE = HERE / "native7-C-compact-scope-receipt-v4.json"
SCOPE_SHA = "b70b00911dbcade6e97470d6a5cb593a122b20af1dcc4672e00711c107f61534"
BRANCH = HERE / "native7_C_branch_view_v1.py"
BRANCH_SHA = "3f059b65ff3844a3256c1bcfe62f5cd285ac4cf90d0d6e22142aadd9832ddadc"
ADAPTER_SHA = "981a753c8f2df863cd358aa7f4d7ed8ef57100ccdf516e73f31690ac0ae151cf"
ORDINARY = ("B.Cu", "In3.Cu", "In2.Cu", "F.Cu")
PROTECTED = {"PORT_C_RX_EXT", "PORT_C_TX_EXT"}
IO2_PREFIX = "d064e04c-5bdc-5e75-8c28-5bec007d243e"
SEED_RECEIPT = ROOT / "ordinary-routing/tests/native13-access/native7-exact-RX-up-seed-v1.json"
SEED_RECEIPT_SHA = "fcc92a44c45f931a9df665fd78ac3f37d9112f72c8d024a6d79dd0a0d78a84e6"


class CFailure(RuntimeError):
    pass


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def read_bound(path, sha):
    if digest(path) != sha:
        raise CFailure("Bound input changed: " + str(path))
    return json.loads(Path(path).read_text())


def _deadline(deadline):
    if time.monotonic() >= deadline:
        raise CFailure("Shared construction deadline reached")


def _passed(checks):
    return bool(checks) and all(x["pass_with_polygon_error"] for x in checks)


def _xy(point):
    return [round(float(x), 6) for x in point]


def _fingerprint(entry):
    o, copper, mask, drill = entry
    return {"record": canonical(o),
            "copper": {k: hashlib.sha256(v.wkb).hexdigest() for k, v in sorted(copper.items())},
            "mask": {k: hashlib.sha256(v.wkb).hexdigest() for k, v in sorted(mask.items())},
            "drill": None if drill is None else hashlib.sha256(drill.wkb).hexdigest()}


def _snapshot(objects):
    result = {q[0]["uuid"]: _fingerprint(q) for q in objects}
    if len(result) != len(objects):
        raise CFailure("Duplicate object identity")
    return result


def _preserved(snapshot, objects, exceptions=()):
    current = {q[0]["uuid"]: q for q in objects}
    for uid, old in snapshot.items():
        if uid in exceptions:
            continue
        if uid not in current or _fingerprint(current[uid]) != old:
            raise CFailure("Supplied peer changed or disappeared: " + uid)


def _load(g, objects):
    packet = read_bound(COMMON, COMMON_SHA)
    scope = read_bound(SCOPE, SCOPE_SHA)
    if digest(BRANCH) != BRANCH_SHA:
        raise CFailure("Protected branch-view helper changed")
    binding = g.binding()
    for key in ("board_sha256", "native_sha256", "logical_map_sha256"):
        if binding[key] != packet["source"][key]:
            raise CFailure("Common packet source differs: " + key)
    if (binding["transaction_sha256"] != packet["source"]["selected_transaction_sha256"]
            or binding["adapter_sha256"] != ADAPTER_SHA):
        raise CFailure("Selected transaction or finite-width adapter differs")
    spec = importlib.util.spec_from_file_location("native7_C_branch_view_bound_v1", BRANCH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    view = mod.load_branch_view(g)
    by = {q[0]["uuid"]: q for q in objects}
    if len(by) != len(objects):
        raise CFailure("Duplicate supplied object identities")
    cuts = set(packet["removed_native_ids"])
    if len(cuts) != 90 or not set(scope["mandatory_C_replacement_native_ids"]).issubset(cuts):
        raise CFailure("Common removal inventory differs")
    if cuts.intersection(by):
        raise CFailure("A declared native donor cut was not applied")
    base = {q[0]["uuid"]: q for q in g.BASE}
    for uid in set(base) - cuts:
        if uid not in by or _fingerprint(by[uid]) != _fingerprint(base[uid]):
            raise CFailure("Held native geometry differs: " + uid)
    for row in packet["routes"]:
        expected = g.track(row["net"], row["layer"], row["points"], row["name"], row["width"])
        if row["name"] not in by or _fingerprint(by[row["name"]]) != _fingerprint(expected):
            raise CFailure("Common source/access route differs: " + row["name"])
    for row in packet["vias"]:
        expected = g.via(row["net"], row["xy"], row["name"])
        if row["name"] not in by or _fingerprint(by[row["name"]]) != _fingerprint(expected):
            raise CFailure("Common source/access via differs: " + row["name"])
    planning = packet["planning_only_reservation"]
    if planning["name"] in by:
        q = by[planning["name"]]
        expected = g.via(planning["net"], planning["xy"], planning["name"])
        if q[1:] != expected[1:] or q[0].get("role") != "upstream" or not q[0].get("planning_only"):
            raise CFailure("RX planning reservation differs")
    return packet, scope, view


def _view(view, job, objects):
    if job["net"] in PROTECTED:
        return view(job["net"], job["role"], objects)
    return job["net"], objects


@contextmanager
def _width_state(g, width):
    old_half, old_objects, domain = g.s.HALF, g.s.OBJECTS, g.rt.domain

    def actual_width_domain(net, layer, width=width, objects=None, reserve=.0001):
        return domain(net, layer, width=actual_width_domain.width, objects=objects, reserve=reserve)

    actual_width_domain.width = width
    try:
        g.rt.domain = actual_width_domain
        yield
    finally:
        g.rt.domain, g.s.HALF, g.s.OBJECTS = domain, old_half, old_objects


def _plan(g, view, job, objects, deadline):
    _deadline(deadline)
    net, peers = _view(view, job, objects)
    with _width_state(g, job["width"]):
        graph = g.gg.build(net, peers, layers=job["layers"])
        row = g.gg.connect(graph, job["a"], job["b"], job["start_layers"], job["end_layers"])
    # Exact legal domains remain available even when a representative seed fails.
    regions = []
    for leg in row["legs"]:
        transition = leg.get("transition", {})
        if transition.get("kind") == "new_via_region":
            a = leg["node"]
            following = row["legs"][row["legs"].index(leg) + 1]["node"]
            region = graph["eligible"][a].intersection(graph["eligible"][following])
            regions.append({"xy": transition["xy"], "from_node": a, "to_node": following,
                            "area_mm2": region.area, "bounds": list(region.bounds),
                            "wkb_hex": region.wkb_hex})
    row["exact_transition_domains"] = regions
    if not row["connected"]:
        start_nodes, end_nodes = set(row["start_nodes"]), set(row["end_nodes"])
        def reach(seeds):
            found = set(seeds)
            stack = list(seeds)
            while stack:
                for nxt, _, _ in graph["adj"][stack.pop()]:
                    if nxt not in found:
                        found.add(nxt); stack.append(nxt)
            return found
        source, target = reach(start_nodes), reach(end_nodes)
        row["source_reachable_nodes"] = sorted(source)
        row["target_reachable_nodes"] = sorted(target)
        row["actual_frontier"] = [{"node": i, "layer": graph["nodes"][i][0],
              "side": "source" if i in source else "target",
              "domain_wkb_hex": graph["nodes"][i][1].wkb_hex,
              "eligible_via_wkb_hex": graph["eligible"][i].wkb_hex if i in graph["eligible"] else None}
             for i in sorted(source | target)]
    return row, graph


def _guard(g, objects, stage, deadline, peer_guard, log):
    _deadline(deadline)
    old_half,old_objects=g.s.HALF,g.s.OBJECTS
    try:
        result = peer_guard(g, objects, stage, deadline)
    finally:
        g.s.HALF,g.s.OBJECTS=old_half,old_objects
    if (not isinstance(result, dict) or type(result.get("passed")) is not bool
            or not isinstance(result.get("checks"), list) or not result["checks"]):
        raise CFailure("Peer guard must provide nonempty actual-terminal checks and passed boolean")
    log.append({"stage": stage, "result": result})
    if not result["passed"]:
        raise CFailure("Shared peer access obligation failed at " + stage)


def _jobs(g, optional_io2=False):
    def job(name, net, a, b, start, end, role=None, width=.127, layers=ORDINARY):
        return dict(name=name, net=net, role=role, a=list(a), b=list(b), width=width,
                    start_layers=list(start), end_layers=list(end), layers=list(layers))
    pad = lambda key: g.one_pad(key)["xy"]
    return [
        job("RX_up", "PORT_C_RX_EXT", [26.35, 16.6], pad("J11.1"), ["F.Cu"], ["F.Cu"], "upstream"),
        job("RX_down", "PORT_C_RX_EXT", [24.65, 16.1], pad("R34.1"), ["F.Cu"], ["B.Cu"], "downstream"),
        job("TX_MCU", "PORT_C_TX_MCU", pad("U1.29"), pad("R35.2"), ["B.Cu"], ["B.Cu"]),
        job("TX_down", "PORT_C_TX_EXT", [24.9, 17.1] if optional_io2 else [24.65, 17.25],
            pad("R35.1"), ["F.Cu"], ["B.Cu"], "downstream"),
        job("RX_MCU", "PORT_C_RX_MCU", pad("U1.28"), pad("R34.2"), ["B.Cu"], ["B.Cu"]),
        job("TX_up", "PORT_C_TX_EXT", [26.35, 17.1], pad("J11.2"), ["F.Cu"], ["F.Cu"], "upstream"),
        job("VX", "VX_PROTECTED", pad("R57.1"), pad("C72.1"), ["F.Cu"], ["F.Cu"],
            width=.25, layers=("F.Cu",)),
    ]


def _all_C_plans(g, view, jobs, objects, deadline, record=None):
    rows = []
    if record is not None:
        record.update(passed=False,checks=rows)
    for job in jobs:
        if record is not None:
            record["current_job"]=job["name"]
        # Preserved physical paths cannot be severed by an additive operation.
        # Reuse a measured copper connection, not a previous free-space graph.
        if _already_connected(g, view, job, objects):
            rows.append({"job": job["name"], "connected": True,
                         "actual_held_copper_connection": True, "start": job["a"], "end": job["b"]})
            continue
        row, _ = _plan(g, view, job, objects, deadline)
        rows.append({"job": job["name"], **row})
    result={"passed": all(x["connected"] for x in rows), "checks": rows}
    if record is not None:
        record.update(result);record.pop("current_job",None)
    return result


def _already_connected(g, view, job, objects):
    from shapely import unary_union
    from shapely.geometry import Point
    net, peers = _view(view, job, objects)
    nodes=[]
    for layer in job["layers"]:
        copper=unary_union([c[layer] for o,c,m,d in peers if o["net"]==net and layer in c])
        nodes.extend((layer,p) for p in g.rt.parts(copper))
    parent=list(range(len(nodes)))
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for o,c,m,d in peers:
        if o["net"]!=net or not (o["kind"]=="via" or o.get("plated",False)):
            continue
        hits=[i for i,(layer,p) in enumerate(nodes) if layer in o.get("barrel_layers",[])
              and layer in c and p.intersection(c[layer]).area>0]
        for i in hits[1:]:
            parent[find(i)]=find(hits[0])
    a={find(i) for i,(layer,p) in enumerate(nodes) if layer in job["start_layers"] and p.covers(Point(job["a"]))}
    b={find(i) for i,(layer,p) in enumerate(nodes) if layer in job["end_layers"] and p.covers(Point(job["b"]))}
    return bool(a.intersection(b))


def _same_layer(g, view, job, objects, layer, a, b):
    from shapely import unary_union
    from shapely.geometry import Point
    net, peers = _view(view, job, objects)
    cu = unary_union([c[layer] for o, c, m, d in peers if o["net"] == net and layer in c])
    return any(p.covers(Point(a)) and p.covers(Point(b)) for p in g.rt.parts(cu))


def _route(g, component, a, b, deadline):
    """Contained solver simplification only; exact finite check still follows."""
    from shapely.geometry import Point, LineString, box
    if component is None or not component.covers(Point(a)) or not component.covers(Point(b)):
        return None, [{"result": "endpoints_outside_current_exact_component"}]
    attempts = []
    for points in g.s.paths2(a, b):
        if component.covers(LineString(points)):
            return points, [{"result": "exact_simple_centerline"}]
    # Crops/insets reduce triangulation cost, never expand allowed copper space.
    options = []
    for margin in (1., 3., 8.):
        crop = component.intersection(box(min(a[0], b[0]) - margin, min(a[1], b[1]) - margin,
                                          max(a[0], b[0]) + margin, max(a[1], b[1]) + margin))
        options.extend(g.rt.parts(crop))
    options.extend(g.rt.parts(component))
    seen = set()
    for region in options:
        if not region.covers(Point(a)) or not region.covers(Point(b)):
            continue
        for inset in (.003, .001, 0.):
            _deadline(deadline)
            solver = region if not inset else region.buffer(-inset)
            for part in g.rt.parts(solver):
                if not part.covers(Point(a)) or not part.covers(Point(b)) or not component.covers(part):
                    continue
                if part.wkb in seen:
                    continue
                seen.add(part.wkb)
                began = time.monotonic()
                try:
                    subdeadline=deadline if inset==0 and part.equals_exact(component,0) else min(deadline,began+4.)
                    points = g.rt.route(part, a, b, subdeadline)
                except (StopIteration, ValueError) as error:
                    points = None
                    attempts.append({"inset_mm": inset, "solver_error": type(error).__name__})
                valid = points is not None and component.covers(LineString(points))
                attempts.append({"inset_mm": inset, "area_mm2": part.area,
                                 "seconds": time.monotonic() - began, "covered": valid})
                if valid:
                    return points, attempts
    return None, attempts


def _add_track(g, view, job, objects, layer, a, b, name, routes, checks, deadline):
    _deadline(deadline)
    if _xy(a) == _xy(b) or _same_layer(g, view, job, objects, layer, a, b):
        checks.append({"name": name, "passed": True, "existing_same_layer_copper_reused": True,
                       "layer": layer, "start": a, "end": b})
        return
    net, peers = _view(view, job, objects)
    with _width_state(g, job["width"]):
        free, _, _ = g.rt.domain(net, layer, objects=peers)
        component = g.rt.component(free, a)
        points, attempts = _route(g, component, a, b, deadline)
    if points is None:
        checks.append({"name": name, "passed": False, "routing_attempts": attempts,
                       "layer": layer, "start": a, "end": b})
        raise CFailure("No finite centerline for " + name)
    points = [_xy(p) for p in points]
    finite = g.check_track(net, layer, points, width=job["width"], objects=peers)
    row = dict(kind="track", name=name, net=job["net"], logical_net=job["net"],
               layer=layer, points=points, width=job["width"])
    if job["role"]:
        row["role"] = job["role"]
    routes.append(row)
    check = {"name": name, "passed": _passed(finite), "width_mm": job["width"],
             "nearest": finite[:5], "routing_attempts": attempts}
    witnesses=_section(g,row,objects)
    check["full_width_endpoint_contacts"]=witnesses
    check["passed"] = check["passed"] and all(
        any(w["point"]==p and w["passed"] for w in witnesses) for p in (points[0],points[-1]))
    checks.append(check)
    if not check["passed"]:
        raise CFailure("Finite-width route failed: " + name)
    entry = g.track(job["net"], layer, points, name, job["width"])
    if job["role"]:
        entry = (dict(entry[0], role=job["role"]), *entry[1:])
    objects.append(entry)


def _add_via(g, view, job, objects, xy, name, vias, checks):
    net, peers = _view(view, job, objects)
    finite = g.check_via(net, xy, objects=peers)
    row = dict(kind="via", name=name, net=job["net"], logical_net=job["net"], xy=_xy(xy),
               diameter=.45, drill=.20, layers=list(g.N["copper_layers"]),
               tented_front=True, tented_back=True)
    if job["role"]:
        row["role"] = job["role"]
    vias.append(row)
    checks.append({"name": name, "passed": _passed(finite), "nearest": finite[:5]})
    if not _passed(finite):
        raise CFailure("Finite transition failed: " + name)
    entry = g.via(job["net"], xy, name)
    if job["role"]:
        entry = (dict(entry[0], role=job["role"]), *entry[1:])
    objects.append(entry)


def _target_variants(g, plan):
    """Finite domain-derived target choices, with no claim of exhaustive search."""
    from shapely import from_wkb
    from shapely.geometry import box, Point
    from shapely.ops import polylabel
    yield "graph_representative", copy.deepcopy(plan)
    if not plan["exact_transition_domains"]:
        return
    last = plan["exact_transition_domains"][-1]
    region = from_wkb(bytes.fromhex(last["wkb_hex"]))
    x0, y0, x1, y1 = region.bounds
    boxes = [box(x0, y0, (x0+x1)/2, y1), box((x0+x1)/2, y0, x1, y1),
             box(x0, y0, x1, (y0+y1)/2), box(x0, (y0+y1)/2, x1, y1)]
    seen = {tuple(last["xy"])}
    for label, clip in zip(("left_half", "right_half", "lower_half", "upper_half"), boxes):
        parts = sorted(g.rt.parts(region.intersection(clip)), key=lambda p: p.area, reverse=True)
        if not parts:
            continue
        p = polylabel(parts[0], tolerance=.00001)
        xy = _xy((p.x, p.y))
        if tuple(xy) in seen or not region.covers(Point(xy)):
            continue
        seen.add(tuple(xy))
        candidate = copy.deepcopy(plan)
        old = last["xy"]
        for leg in candidate["legs"]:
            if leg["start"] == old:
                leg["start"] = xy
            if leg["end"] == old:
                leg["end"] = xy
            if leg.get("transition", {}).get("xy") == old:
                leg["transition"]["xy"] = xy
        for row in candidate["new_vias"]:
            if row["xy"] == old:
                row["xy"] = xy
        candidate["exact_transition_domains"][-1]["selected_xy"] = xy
        yield label, candidate


def _allocate(g, view, job, plan, objects, prefix, routes, vias, checks, deadline,
              complete=False):
    for i, transition in enumerate(plan["new_vias"]):
        _add_via(g, view, job, objects, transition["xy"], f"{prefix}-via-{i}", vias, checks)
    legs = plan["legs"]
    order = [len(legs)-1, 0] if not complete else list(range(len(legs)-1, -1, -1))
    for i in dict.fromkeys(order):
        leg = legs[i]
        _add_track(g, view, job, objects, leg["layer"], leg["start"], leg["end"],
                   f"{prefix}-leg-{i}", routes, checks, deadline)


def _receipt(g, prefix, objects):
    return dict(schema="f722-native7-C-two-phase/v2", source=g.binding(),
                common_packet_sha256=COMMON_SHA, C_scope_sha256=SCOPE_SHA,
                helper_sha256=digest(__file__), branch_view_sha256=BRANCH_SHA,
                prefix=prefix, phase="prepare_access", access_complete=False, complete=False,
                C_functions_complete=False, selected=False,
                routes=[], vias=[], checks=[], peer_guards=[], C_access_gates=[],
                attempts=[], optional_removed_native_records=[], removed_records=[],
                prepared={"input_snapshot":_snapshot(objects)}, objects=list(objects),
                pending_native_fill_reference_return_power_VCAP_checks=True)


def _saved_RX_seed(g):
    source=read_bound(SEED_RECEIPT,SEED_RECEIPT_SHA)
    if source["source"]!=g.binding():
        raise CFailure("Recorded RX seed belongs to another exact native context")
    active=source["C_active"]
    if active["common_packet_sha256"]!=COMMON_SHA or active["C_scope_sha256"]!=SCOPE_SHA:
        raise CFailure("Recorded RX seed uses another common cut/peer set")
    trials=[x for x in active["attempts"] if x.get("job")=="RX_up" and x.get("choice")=="graph_representative"]
    if len(trials)!=1 or len(trials[0]["routes"])!=1 or trials[0]["vias"]:
        raise CFailure("Recorded finite zero-via RX seed is ambiguous")
    row=trials[0]["routes"][0]
    if not (row["net"]=="PORT_C_RX_EXT" and row["role"]=="upstream" and row["layer"]=="F.Cu" and row["width"]==.127):
        raise CFailure("Recorded RX seed role, layer or width differs")
    checks=[x for x in trials[0]["checks"] if x.get("name")==row["name"]]
    if len(checks)!=1 or not checks[0]["passed"]:
        raise CFailure("Recorded RX seed lacks its finite/contact proof")
    return copy.deepcopy(row)


def _replay_RX_seed(g,view,job,work,prefix,result,deadline):
    _deadline(deadline)
    row=_saved_RX_seed(g)
    row["name"]=prefix+"-recorded-RX-up-F"
    trial={"job":"RX_up","phase":"exact_recorded_seed","source_receipt_sha256":SEED_RECEIPT_SHA,
           "routes":[row],"vias":[],"checks":[],"accepted":False}
    result["attempts"].append(trial)
    net,peers=_view(view,job,work)
    finite=g.check_track(net,row["layer"],row["points"],width=row["width"],objects=peers)
    witnesses=_section(g,row,work)
    ends=row["points"][0],row["points"][-1]
    check={"name":row["name"],"passed":_passed(finite) and all(any(w["point"]==p and w["passed"] for w in witnesses) for p in ends),
           "nearest":finite[:5],"full_width_endpoint_contacts":witnesses}
    trial["checks"].append(check)
    if not check["passed"]:
        raise CFailure("Exact recorded zero-via RX-up seed failed current finite/contact checks")
    entry=g.track(row["net"],row["layer"],row["points"],row["name"],row["width"])
    work.append((dict(entry[0],role=row["role"]),*entry[1:]))
    result["routes"].append(row);result["checks"].append(check)
    return trial


def prepare(g, objects, deadline, prefix, *, peer_guard, allow_full_io2=False, progress=None):
    """Complete RX-down/VX, replay one recorded RX-up path, then other accesses.

    The eastern barrel trial is retired. A failed recorded path or capacity gate
    ends this bounded sequence; no different order or additional donor cut is tried.
    """
    original=list(objects)
    result=_receipt(g,prefix,original)
    started=time.monotonic()
    result["timings"]=[]
    def stamp(stage,event):
        now=time.monotonic()
        result["timings"].append({"stage":stage,"event":event,"elapsed_seconds":now-started,
                                  "remaining_budget_seconds":deadline-now})
    result["seed_receipt_sha256"]=SEED_RECEIPT_SHA
    result["retired_eastern_entry_attempt"]=True
    result["sequence"]=["complete_RX_down","complete_0_25mm_VX","replay_recorded_RX_up_once","remaining_C_accesses"]
    result["peer_guard_batching"]={
        "full_checkpoints":["complete_RX_down_and_VX","exact_recorded_RX_up_after_local_pair","all_C_accesses_complete"],
        "intermediate_additions_foreign_to_SPI_B_local_peer_nets":True,
        "peer_access_between_checkpoints":"unmeasured until the next full checkpoint passes",
        "actual_C_support_checks_after_each_allocation":True,
        "final_full_peer_finite_and_source_component_gates_required":True}
    result["optional_IO2_fallback_requested"]=allow_full_io2
    result["optional_IO2_fallback_executed"]=False
    if progress is not None:
        progress(receipt(result))
    try:
        stamp("source_binding","start")
        packet,scope,view=_load(g,original)
        reservation=packet["planning_only_reservation"]["name"]
        result["replaced_planning_object_ids"]=[reservation] if any(q[0]["uuid"]==reservation for q in original) else []
        work=[q for q in original if q[0]["uuid"]!=reservation]
        by_name={j["name"]:j for j in _jobs(g)}
        jobs=[by_name[n] for n in ("RX_down","VX","RX_up","TX_MCU","TX_down","RX_MCU","TX_up")]
        result["jobs"]=jobs
        stamp("source_binding","complete")
        # These two local F functions use their actual contacts and full widths.
        # Their complete traces, not bare transition points, constrain the RX-up replay.
        for name in ("RX_down","VX"):
            job=by_name[name]
            stamp("complete_"+name,"start")
            plan,_=_plan(g,view,job,work,deadline)
            trial={"job":name,"phase":"complete_constrained_F_passage","plan":plan,
                   "routes":[],"vias":[],"checks":[],"accepted":False}
            result["attempts"].append(trial)
            if not plan["connected"]:
                raise CFailure("Initial constrained local job is disconnected: "+name)
            _allocate(g,view,job,plan,work,prefix+"-local-"+name,trial["routes"],trial["vias"],
                      trial["checks"],deadline,complete=True)
            result["routes"].extend(trial["routes"]);result["vias"].extend(trial["vias"])
            result["checks"].extend(trial["checks"])
            if not _already_connected(g,view,job,work):
                raise CFailure("Constructed local job lacks actual copper connection: "+name)
            gate={"stage":"after_complete_"+name,"passed":False,"checks":[]}
            result["C_access_gates"].append(gate)
            _all_C_plans(g,view,jobs,work,deadline,record=gate)
            if not gate["passed"]:
                raise CFailure("Complete local "+name+" consumes another actual C/support path")
            trial["accepted"]=True
            stamp("complete_"+name,"complete")
        stamp("peer_guard_after_local_pair","start")
        _guard(g,work,"complete_RX_down_and_VX",deadline,peer_guard,result["peer_guards"])
        stamp("peer_guard_after_local_pair","complete")
        stamp("recorded_RX_up","start")
        trial=_replay_RX_seed(g,view,by_name["RX_up"],work,prefix,result,deadline)
        gate={"stage":"exact_RX_up_after_RX_down_VX","passed":False,"checks":[]}
        result["C_access_gates"].append(gate)
        _all_C_plans(g,view,jobs,work,deadline,record=gate)
        if not gate["passed"]:
            raise CFailure("Recorded RX-up after complete RX-down/VX blocks another actual target")
        _guard(g,work,"exact_recorded_RX_up_after_local_pair",deadline,peer_guard,result["peer_guards"])
        trial["accepted"]=True
        stamp("recorded_RX_up","complete")
        for job in jobs[3:]:
            stamp("C_access_"+job["name"],"start")
            if _already_connected(g,view,job,work):
                result["checks"].append({"job":job["name"],"passed":True,"actual_copper_already_complete":True})
                stamp("C_access_"+job["name"],"already_complete")
                continue
            plan,_=_plan(g,view,job,work,deadline)
            if not plan["connected"]:
                result["attempts"].append({"job":job["name"],"plan":plan})
                raise CFailure("Current C access graph failed: "+job["name"])
            variants=_target_variants(g,plan) if job["name"]=="TX_MCU" else [("graph_representative",plan)]
            accepted=False
            for index,(choice,candidate) in enumerate(variants):
                _deadline(deadline)
                local=list(work);routes=[];vias=[];checks=[]
                attempt={"job":job["name"],"choice":choice,"plan":candidate,"routes":routes,
                         "vias":vias,"checks":checks,"accepted":False}
                result["attempts"].append(attempt)
                try:
                    _allocate(g,view,job,candidate,local,f"{prefix}-access-{job['name']}-{index}",
                              routes,vias,checks,deadline)
                    remaining={"passed":False,"checks":[]}
                    attempt["remaining_C_targets"]=remaining
                    _all_C_plans(g,view,jobs,local,deadline,record=remaining)
                    if not remaining["passed"]:
                        raise CFailure("Actual C target/entry capacity consumed")
                except CFailure as error:
                    attempt["terminal_reason"]=str(error)
                    continue
                work=local;result["routes"].extend(routes);result["vias"].extend(vias)
                result["checks"].extend(checks);attempt["accepted"]=True;accepted=True
                break
            if not accepted:
                raise CFailure("No bounded compatible actual access allocation: "+job["name"])
            stamp("C_access_"+job["name"],"complete")
        # All additions in this batch are foreign to the guarded SPI/B/local nets.
        # Their free-space access is monotone decreasing; one complete final guard
        # cannot conceal an earlier loss that later C additions somehow repaired.
        stamp("peer_guard_all_C_accesses","start")
        _guard(g,work,"all_C_accesses_complete",deadline,peer_guard,result["peer_guards"])
        stamp("peer_guard_all_C_accesses","complete")
        _preserved(result["prepared"]["input_snapshot"],work,result["replaced_planning_object_ids"])
        result["prepared"]["snapshot"]=_snapshot(work)
        result.update(access_complete=True,complete=True,objects=work,
                      terminal_reason="Complete RX-down/VX, recorded RX-up and all C accesses constructed; inner trunks pending")
    except CFailure as error:
        result.update(objects=original,terminal_reason=str(error))
    stamp("prepare","terminal")
    return result


def _physical_groups(g, objects, net, cut_key=None):
    """Split actual polygons, with vertical edges only through real plated barrels."""
    from shapely.geometry import Polygon
    cut = {} if cut_key is None else next(q[1] for q in objects if q[0].get("key") == cut_key)
    nodes=[]
    def parts(shape):
        if shape.geom_type == "Polygon":
            return [shape] if not shape.is_empty else []
        return [p for child in getattr(shape, "geoms", []) for p in parts(child)]
    for o, copper, _, _ in objects:
        if o["net"] != net or (cut_key is not None and o.get("key") == cut_key):
            continue
        for layer, shape in copper.items():
            geometry = shape.difference(cut[layer]) if layer in cut else shape
            for part in parts(geometry):
                nodes.append((o, layer, part))
    parent=list(range(len(nodes)))
    def find(i):
        while parent[i] != i:
            parent[i]=parent[parent[i]]; i=parent[i]
        return i
    for i, (a, la, pa) in enumerate(nodes):
        for j, (b, lb, pb) in enumerate(nodes[:i]):
            plated = a["kind"] == "via" or a.get("plated", False)
            if ((la == lb and pa.intersection(pb).area > 0) or
                (a["uuid"] == b["uuid"] and plated and la in a.get("barrel_layers", []) and lb in a.get("barrel_layers", []))):
                parent[find(i)] = find(j)
    groups={}
    for i, (o, layer, shape) in enumerate(nodes):
        row=groups.setdefault(find(i), {"ids":set(), "keys":set(), "layers":set()})
        row["ids"].add(o["uuid"]); row["layers"].add(layer)
        if o.get("key"):
            row["keys"].add(o["key"])
    return [{k:sorted(v) for k,v in row.items()} for row in groups.values()]


def _section(g, route, peers, target_uid=None):
    """Actual full-width entry witness, using the native polygon-error bound."""
    from shapely.geometry import Point, LineString
    points=route["points"]; layer=route["layer"]; width=route["width"]
    witnesses=[]
    for p, neighbor in ((points[0],points[1]),(points[-1],points[-2])):
        dx,dy=neighbor[0]-p[0],neighbor[1]-p[1]; length=math.hypot(dx,dy)
        if length == 0:
            continue
        nx,ny=-dy/length*width/2,dx/length*width/2
        section=LineString([(p[0]-nx,p[1]-ny),(p[0]+nx,p[1]+ny)])
        for o,c,_,_ in peers:
            if o["uuid"] == route["name"] or o["net"] != route["net"] or layer not in c:
                continue
            if target_uid is not None and o["uuid"] != target_uid:
                continue
            if not c[layer].covers(Point(p)):
                continue
            shape = g.s.geom(o["inside"][layer]) if o.get("inside",{}).get(layer) else c[layer]
            length = section.intersection(shape).length
            witnesses.append({"retained_uuid":o["uuid"], "actual_pad":o.get("key"),
                              "point":p, "layer":layer, "cross_section_mm":length,
                              "required_width_mm":width, "section_wkb_hex":section.wkb_hex,
                              "passed":length >= width - 2*g.N["maximum_polygon_error_mm"]})
    return witnesses


def _annular_entries(g, route, peers):
    from shapely.geometry import LineString
    result=[]
    layer=route["layer"];width=route["width"]
    for p,n in ((route["points"][0],route["points"][1]),(route["points"][-1],route["points"][-2])):
        length=math.dist(p,n)
        if length<=0:
            continue
        for o,c,m,d in peers:
            if o["kind"]!="via" or o["net"]!=route["net"] or _xy(o["xy"])!=_xy(p) or layer not in c:
                continue
            # A .16 mm radial section is outside the .10 mm drill and inside the
            # .225 mm land. Measure both actual copper and actual route coverage.
            radial=min(.16,length/2)
            ux,uy=(n[0]-p[0])/length,(n[1]-p[1])/length
            center=[p[0]+radial*ux,p[1]+radial*uy]
            section=LineString([(center[0]-uy*width/2,center[1]+ux*width/2),
                                (center[0]+uy*width/2,center[1]-ux*width/2)])
            annulus=c[layer].difference(d) if d is not None else c[layer]
            route_shape=next(q[1][layer] for q in peers if q[0]["uuid"]==route["name"])
            covered=section.intersection(annulus).intersection(route_shape).length
            result.append({"via_uuid":o["uuid"],"route":route["name"],"layer":layer,
                           "radial_position_mm":radial,"section_wkb_hex":section.wkb_hex,
                           "actual_annular_connection_mm":covered,"required_width_mm":width,
                           "passed":covered>=width-2*g.N["maximum_polygon_error_mm"]})
    return result


def _validate(g, view, scope, prepared, work, deadline):
    from shapely import unary_union
    result={"finite":[],"physical_terminals":[],"donor_contacts":[],"entries":[],"annular_entries":[],"cuts":[]}
    all_routes=prepared.get("inherited_C_routes",[])+prepared["routes"]
    all_vias=prepared.get("inherited_C_vias",[])+prepared["vias"]
    for row in all_routes + all_vias:
        _deadline(deadline)
        job=dict(net=row["net"],role=row.get("role"))
        peers=[q for q in work if q[0]["uuid"] != row["name"]]
        net,peers=_view(view,job,peers)
        checks=(g.check_track(net,row["layer"],row["points"],width=row["width"],objects=peers)
                if row["kind"]=="track" else g.check_via(net,row["xy"],objects=peers))
        result["finite"].append({"name":row["name"],"passed":_passed(checks),"nearest":checks[:5]})
    terminals={"PORT_C_RX_MCU":["U1.28","R34.2"],"PORT_C_TX_MCU":["U1.29","R35.2"],
               "PORT_C_RX_EXT":["U15.1","U15.10","J11.1","R34.1"],
               "PORT_C_TX_EXT":["U15.2","U15.9","J11.2","R35.1"],
               "VX_PROTECTED":["R57.1","C72.1"]}
    groups={net:_physical_groups(g,work,net) for net in terminals}
    for net,keys in terminals.items():
        result["physical_terminals"].append({"net":net,"actual_keys":keys,"groups":groups[net],
                "passed":any(set(keys).issubset(x["keys"]) for x in groups[net])})
    by={q[0]["uuid"]:q for q in work}
    for name,donor in scope["scopes"].items():
        if not donor.get("remove_for_v24") and not (name=="TX_down_IO2_prefix" and prepared["optional_removed_native_records"]):
            continue
        contacts=sorted({x["retained_uuid"] for x in donor["finite_contacts"]
                         if x["retained_uuid"] not in scope["mandatory_C_replacement_native_ids"]
                         and x["retained_uuid"] not in {q["uuid"] for q in prepared["optional_removed_native_records"]}})
        net=g.by[donor["native_ids"][0]]["net"]
        good=all(uid in by for uid in contacts) and any(set(contacts).issubset(q["ids"]) for q in groups[net])
        result["donor_contacts"].append({"scope":name,"all_original_retained_contact_ids":contacts,"passed":good})
    # Every newly drawn route endpoint is a finite full-width join. Inherited
    # common MCU entries have separate source-bound full-width proofs in packet.
    for route in all_routes:
        witnesses=_section(g,route,work)
        ends=route["points"][0],route["points"][-1]
        result["entries"].append({"name":route["name"],"witnesses":witnesses,
                                  "passed":all(any(w["point"]==p and w["passed"] for w in witnesses) for p in ends)})
        result["annular_entries"].extend(_annular_entries(g,route,work))
    metadata=scope["protected_branch_role_metadata"]
    for net,bonded,up,down in (("PORT_C_RX_EXT","U15.1","J11.1","R34.1"),
                               ("PORT_C_TX_EXT","U15.2","J11.2","R35.1")):
        cut_groups=_physical_groups(g,work,net,bonded)
        disconnected=not any(up in q["keys"] and down in q["keys"] for q in cut_groups)
        cut_shape=next(q[1] for q in work if q[0].get("key")==bonded)
        branch={"upstream":{},"downstream":{}}
        for o,c,_,_ in work:
            if o["net"]!=net or o.get("key")==bonded:
                continue
            role=metadata.get(o["uuid"],{}).get("role",o.get("role"))
            if role not in branch:
                raise CFailure("Unclassified physical protected copper at final cut")
            for layer,shape in c.items():
                shape=shape.difference(cut_shape[layer]) if layer in cut_shape else shape
                if not shape.is_empty:
                    branch[role].setdefault(layer,[]).append(shape)
        spacing=[]
        for layer in set(branch["upstream"]).intersection(branch["downstream"]):
            gap=unary_union(branch["upstream"][layer]).distance(unary_union(branch["downstream"][layer]))
            spacing.append({"layer":layer,"physical_gap_mm":gap,
                            "passed":gap>=.127+g.N["maximum_polygon_error_mm"]})
        result["cuts"].append({"net":net,"removed_actual_bonded_pad":bonded,
                               "groups":cut_groups,"no_external_bypass":disconnected,
                               "outside_pad_branch_spacing":spacing,
                               "passed":disconnected and bool(spacing) and all(x["passed"] for x in spacing)})
    result["passed"]=all(row["passed"] for rows in result.values() if isinstance(rows,list) for row in rows)
    return result


def finish(g, prepared, objects, deadline, *, peer_guard, progress=None):
    """Finish C trunks with all prepared access and current caller peers held."""
    original=list(objects)
    result={k:copy.deepcopy(v) for k,v in prepared.items() if k!="objects"}
    result.update(objects=original,complete=False,phase="finish_trunks")
    result["inherited_C_routes"]=copy.deepcopy(prepared["routes"])
    result["inherited_C_vias"]=copy.deepcopy(prepared["vias"])
    result["routes"]=[];result["vias"]=[]
    if progress is not None:
        progress(receipt(result))
    try:
        if not prepared.get("access_complete") or prepared.get("helper_sha256")!=digest(__file__):
            raise CFailure("Prepared C state is incomplete or belongs to a different helper")
        _preserved(prepared["prepared"]["snapshot"],original)
        scope=read_bound(SCOPE,SCOPE_SHA)
        # _load expects the original optional prefix and planning state; source
        # identity is instead rechecked here and prepared snapshots bind geometry.
        if g.binding()!=prepared["source"] or digest(COMMON)!=COMMON_SHA or digest(BRANCH)!=BRANCH_SHA:
            raise CFailure("Source or dependency changed between C phases")
        spec=importlib.util.spec_from_file_location("native7_C_branch_view_finish_v1",BRANCH)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        view=mod.load_branch_view(g)
        work=list(original)
        _guard(g,work,"before_C_trunks",deadline,peer_guard,result["peer_guards"])
        for job in prepared["jobs"]:
            if _already_connected(g,view,job,work):
                result["checks"].append({"job":job["name"],"passed":True,"actual_copper_already_complete":True})
                continue
            plan,_=_plan(g,view,job,work,deadline)
            attempt={"job":job["name"],"phase":"finish","plan":plan,"routes":[],"vias":[],"checks":[]}
            result["attempts"].append(attempt)
            if not plan["connected"]:
                raise CFailure("Held shared trunks disconnect C job: "+job["name"])
            _allocate(g,view,job,plan,work,prepared["prefix"]+"-finish-"+job["name"],
                      attempt["routes"],attempt["vias"],attempt["checks"],deadline,complete=True)
            result["routes"].extend(attempt["routes"]);result["vias"].extend(attempt["vias"])
            result["checks"].extend(attempt["checks"])
            gate=_all_C_plans(g,view,prepared["jobs"],work,deadline)
            result["C_access_gates"].append({"stage":"finished_"+job["name"],**gate})
            if not gate["passed"]:
                raise CFailure("C trunk consumed another actual C/support path")
            _guard(g,work,"C_trunk_"+job["name"],deadline,peer_guard,result["peer_guards"])
        validation=_validate(g,view,scope,result,work,deadline)
        result["validation"]=validation
        if not validation["passed"]:
            raise CFailure("Complete C finite/contact/actual-pad-cut gate failed")
        _preserved(_snapshot(original),work)
        result.update(complete=True,C_functions_complete=True,objects=work,terminal_reason="All six C functions and private VX contacts complete; whole-board donor/native gates pending")
    except CFailure as error:
        result.update(objects=original,terminal_reason=str(error))
    return result


def access_guard(g, prepared, objects, stage, deadline):
    """Preserve the seven actual C/support jobs between caller-owned allocations.

    Six C functions are RX/TX MCU, RX/TX protected upstream, and RX/TX protected
    downstream; the seventh job is the original .25 mm private VX supply leaf.
    This checks current physical connections or fresh exact free-space plans.
    It never constructs copper or changes the caller's object list.
    """
    try:
        if not prepared.get("access_complete") or prepared.get("helper_sha256")!=digest(__file__):
            raise CFailure("C access guard requires this helper's completed prepare state")
        _preserved(prepared["prepared"]["snapshot"],objects)
        if g.binding()!=prepared["source"] or digest(BRANCH)!=BRANCH_SHA:
            raise CFailure("C access guard source changed")
        spec=importlib.util.spec_from_file_location("native7_C_branch_view_guard_v1",BRANCH)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        view=mod.load_branch_view(g)
        result=_all_C_plans(g,view,prepared["jobs"],objects,deadline)
        return {"stage":stage,**result}
    except CFailure as error:
        return {"stage":stage,"passed":False,"checks":[{"name":"C_access_contract","passed":False,
                                                           "terminal_reason":str(error)}]}


def receipt(result):
    """Serializable evidence without in-memory Shapely objects or large snapshots."""
    return {k:v for k,v in result.items() if k not in ("objects","prepared")}
