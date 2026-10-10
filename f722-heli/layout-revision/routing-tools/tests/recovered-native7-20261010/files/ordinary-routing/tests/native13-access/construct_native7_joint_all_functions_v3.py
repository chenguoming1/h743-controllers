"""One bounded native7 transaction: all flash/B/C paths and every full donor.

Requires a frozen source contract and an explicit owner-granted routing slot.
No native PCB is edited here. A native incremental plan is emitted only after
complete physical-terminal, retained-source and width-aware finite gates pass.
"""
import argparse
import hashlib
import importlib.util
import importlib.metadata
import json
import math
from pathlib import Path
import signal
import time

from shapely.geometry import LineString, Point
from shapely.ops import polylabel
import native7_recovered_context_v3 as adapter
import native7_joint_routing_helpers_v2 as routing
from prepare_native7_coordinated_context_v3 import replay
from audit_native7_shared_restoration_obligations_v1 import partition

H = Path(__file__).resolve().parent
ROOT = H.parents[2]
ALL_LAYERS = ("B.Cu", "In3.Cu", "In2.Cu", "F.Cu")


class StopJoint(RuntimeError):
    pass


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main(contract_path):
    start = time.monotonic()
    contract = json.loads(contract_path.read_text())
    for row in contract["source_files"]:
        assert adapter.digest(ROOT / row["path"]) == row["sha256"], row["path"]
    for package, version in contract["runtime_versions"].items():
        assert importlib.metadata.version(package) == version, package
    deadline = start + contract["internal_seconds"]
    output = ROOT / contract["receipt"]
    out = {"schema": "f722-native7-joint-all-functions-search/v1", "contract_sha256": adapter.digest(contract_path),
           "script_sha256": adapter.digest(__file__), "complete": False, "selected": False,
           "native_candidate": False, "stages": [], "attempts": [], "routing_started": True,
           "required_existing_open_closures": 7, "required_new_source_component_restorations": 9}
    router = None
    extra_routes, extra_vias = [], []

    def save():
        out["seconds"] = time.monotonic() - start
        if router is not None:
            out["routed_tracks"] = router.routes
            out["routed_vias"] = router.vias
            out["router_attempts"] = router.attempts
        out["C_tracks"] = extra_routes
        out["C_vias"] = extra_vias
        output.write_text(json.dumps(out, indent=2) + "\n")

    def stop(reason, detail=None):
        out["terminal_reason"] = reason
        if detail is not None:
            out["terminal_detail"] = detail
        save()
        raise StopJoint(reason)

    def alarm(signum, frame):
        stop("Overall bounded search deadline; incomplete geometry is not selected.")

    signal.signal(signal.SIGALRM, alarm)
    signal.alarm(contract["internal_seconds"])
    try:
        g = adapter.load()
        out["source"] = g.binding()
        proposal, c_scope, cuts, held, common_added, reservation, reserved_via = replay(g)
        initial = held + common_added + [reserved_via]
        router = routing.Router(g, initial, deadline)
        common_packet = json.loads((H / "native7-common-planning-packet-v1.json").read_text())
        ledger = json.loads((H / "native7-shared-restoration-obligations-v1.json").read_text())
        c_helper = module(ROOT / contract["C_helper"], "native7_integrated_C_helper")
        branch_helper = module(ROOT / contract["C_branch_helper"], "native7_integrated_branch_helper")
        branch_view = branch_helper.load_branch_view(g)
        out["removed_native_ids"] = sorted(cuts)
        out["common_routes"] = proposal["proposed_common_routes"]
        out["common_vias"] = proposal["proposed_common_vias"]

        jobs = [
            ("FLASH_SCK", "U1.34", "U3.6"), ("FLASH_MISO", "U1.35", "U3.2"),
            ("FLASH_MOSI", "U1.36", "U3.5"), ("PORT_B_RX_MCU", "U1.37", "R32.2"),
            ("PORT_B_TX_MCU", "U1.38", "R33.2"), ("FLASH_CS", "U1.33", "U3.1"),
            ("FLASH_CS", "U1.33", "R4.2"), ("DSM_RX_MCU", "U1.43", "R38.2"),
            ("DSM_RX_MCU", "U1.43", "R71.2"), ("IMU_CS", "U1.20", "U2.12"),
            ("IMU_CS", "U1.20", "R3.2"), ("LED_GREEN_K", "U1.3", "D1.1")]

        def peer_guard(context, objects, stage, stage_deadline):
            checks, graphs, physical = [], {}, {}
            for net, akey, bkey in jobs:
                if time.monotonic() >= min(deadline, stage_deadline):
                    return {"passed": False, "checks": checks, "reason": "guard budget ended"}
                a, b = g.one_pad(akey), g.one_pad(bkey)
                if net not in physical:
                    physical[net] = partition(objects, net)[1]
                memberships = physical[net]
                if memberships[a["uuid"]].intersection(memberships[b["uuid"]]):
                    checks.append({"net": net, "start_key": akey, "target_key": bkey,
                                   "already_physically_connected": True, "connected": True})
                    continue
                if net not in graphs:
                    graphs[net] = g.gg.build(net, objects)
                plan = g.gg.connect(graphs[net], a["xy"], b["xy"], tuple(a["copper"]), tuple(b["copper"]))
                row = {"net": net, "start_key": akey, "target_key": bkey, "plan": plan,
                       "connected": plan["connected"]}
                if not plan["connected"]:
                    row["frontier"] = routing.source_target_frontier(g, graphs[net], plan)
                checks.append(row)
            result = {"stage": stage, "passed": all(row["connected"] for row in checks), "checks": checks}
            out["stages"].append({"peer_guard": result})
            save()
            return result

        def accept_C(result, phase):
            out["stages"].append({"C_phase": phase, "result": {k: result[k] for k in ("complete", "terminal_reason", "checks", "removed_records", "routes", "vias", "source", "plans", "guards") if k in result}})
            if not result.get("complete"):
                stop("C " + phase + " could not complete its bounded joint allocation.", result.get("terminal_reason"))
            router.objects = result["objects"]
            extra_routes.extend(result.get("routes", []))
            extra_vias.extend(result.get("vias", []))
            for row in result.get("removed_records", []):
                record = row.get("record", row)
                assert record == g.by[record["uuid"]]
                cuts.add(record["uuid"])
            out["removed_native_ids"] = sorted(cuts)
            save()

        def C_progress(receipt):
            out["C_active"] = receipt
            save()

        prepared = c_helper.prepare(g, router.objects, min(deadline-300, time.monotonic()+150),
                                    "joint-C", peer_guard=peer_guard, allow_full_io2=True, progress=C_progress)
        accept_C(prepared, "prepare")

        def C_guard(stage):
            result = c_helper.access_guard(g, prepared, router.objects, stage, deadline)
            out["stages"].append({"C_access_guard": result})
            save()
            if not result["passed"]:
                raise routing.JointRoutingFailure({"stage": stage, "C_access_guard": result})

        # MISO's MID is already reached by its complete In3 source leg. Its
        # middle must begin here on In2, never retreat through the old source cell.
        mid = [25.384531, 14.536071]
        target = [30.361319, 23.075378]
        cs = [32.582039, 21.210477]
        old_far = Point(32.159059, 21.806762)
        f2, _, via_obstacles = g.rt.domain("FLASH_MISO", "In2.Cu", objects=router.objects)
        f3, _, _ = g.rt.domain("FLASH_MISO", "In3.Cu", objects=router.objects)
        source_component, target_component = g.rt.component(f2, mid), g.rt.component(f3, target)
        if source_component is None or target_component is None:
            stop("MISO MID or actual U3-side entry lacks its exact ordinary-layer component.")
        legal_via = g.s.OUTLINE.buffer(-.479-g.s.ERROR-.0001).difference(g.rt.expanded(via_obstacles))
        legal = source_component.intersection(target_component).intersection(legal_via)
        spacing = .45+.127+2*.127+2*g.s.ERROR+.0002
        corridor_domain = legal.difference(Point(cs).buffer(spacing))
        out["MISO_far_transition_domain"] = {"legal_wkb_hex": legal.wkb_hex,
                "corridor_wkb_hex": corridor_domain.wkb_hex, "area_mm2": legal.area,
                "required_pair_spacing_mm": spacing,
                "spacing_is_engineering_corridor_test_not_global_design_rule": True}
        candidates = sorted(g.rt.parts(corridor_domain), key=lambda q: q.distance(old_far))[:3]
        if not candidates:
            graph, plan = router.graph("FLASH_MISO", mid, target, ("In2.Cu",), ("In3.Cu",))
            stop("No legal MISO far-center region supports the explicit MOSI neck in this C-reserved allocation.",
                 {"plan": plan, "frontier": routing.source_target_frontier(g, graph, plan) if not plan["connected"] else []})
        initial_state = router.snapshot()
        successful = None
        for index, region in enumerate(candidates):
            router.restore(initial_state)
            trial = {"index": index, "region_wkb_hex": region.wkb_hex, "complete": False}
            out["attempts"].append(trial)
            center = polylabel(region, tolerance=.00005)
            far = [round(center.x, 6), round(center.y, 6)]
            trial["far_xy"] = far
            if not region.covers(Point(far)):
                trial["failure"] = "Rounded center left exact legal domain."
                continue
            try:
                router.add_via("FLASH_MISO", far, "joint-MISO-far-via")
                router.layer_route("FLASH_MISO", "In3.Cu", far, target, "joint-MISO-U3-entry", budget=40)
                # Allocate the diagnosed MOSI passage as actual finite copper
                # before any SCK trunk. Its endpoints must remain source-connected.
                dx, dy = cs[0]-far[0], cs[1]-far[1]
                distance = math.hypot(dx, dy)
                midpoint = [(cs[0]+far[0])/2, (cs[1]+far[1])/2]
                nx, ny = -dy/distance, dx/distance
                free, _, _ = g.rt.domain("FLASH_MOSI", "In2.Cu", objects=router.objects)
                mosicomp = g.rt.component(free, [19.126809,13.183997])
                neck = None
                for half in (.30, .20, .12):
                    points = [[round(midpoint[0]+sign*nx*half,6), round(midpoint[1]+sign*ny*half,6)] for sign in (-1,1)]
                    if mosicomp is not None and mosicomp.covers(LineString(points)):
                        checks = g.check_track("FLASH_MOSI", "In2.Cu", points, width=.127, objects=router.objects)
                        if all(q["pass_with_polygon_error"] for q in checks):
                            neck = points
                            break
                if neck is None:
                    raise routing.JointRoutingFailure({"stage":"MOSI_target_neck", "far":far,
                                                        "spacing":distance, "midpoint":midpoint})
                router.add_track("FLASH_MOSI", "In2.Cu", neck, "joint-MOSI-reserved-target-neck")
                trial["MOSI_neck"] = neck
                guard = peer_guard(g, router.objects, "MISO-far-and-MOSI-neck", deadline)
                if not guard["passed"]:
                    raise routing.JointRoutingFailure({"stage":"shared_access_after_target_neck", "guard":guard})
                C_guard("MISO-far-and-MOSI-neck")
                router.connect("FLASH_SCK", [21.222473,11.478438], [41.008497,18.15549],
                               "joint-SCK-trunk", ALL_LAYERS, ALL_LAYERS, budget=70)
                C_guard("SCK-complete")
                router.layer_route("FLASH_MISO", "In2.Cu", mid, far, "joint-MISO-MID-to-far", budget=60)
                C_guard("MISO-complete")
                # Connect both ends of the reserved passage, preserving it as a
                # real series portion of the completed MOSI route.
                source, end = [19.126809,13.183997], [36.79011,17.88793]
                if math.dist(source,neck[1])+math.dist(end,neck[0]) < math.dist(source,neck[0])+math.dist(end,neck[1]):
                    neck = list(reversed(neck))
                router.connect("FLASH_MOSI", source, neck[0], "joint-MOSI-source-to-neck", ALL_LAYERS, ("In2.Cu",), budget=55)
                router.connect("FLASH_MOSI", neck[1], end, "joint-MOSI-neck-to-target", ("In2.Cu",), ALL_LAYERS, budget=55)
                C_guard("three-SPI-complete")
                trial["complete"] = True
                successful = index
                save()
                break
            except routing.JointRoutingFailure as exc:
                trial["failure"] = exc.args[0]
                trial["attempted_routes"] = router.routes[initial_state[1]:]
                trial["attempted_vias"] = router.vias[initial_state[2]:]
                save()
        if successful is None:
            stop("No simultaneous three-SPI allocation completed in the bounded exact far-domain assignments.")
        for net, a, b in [("PORT_B_RX_MCU",[17.9,10.45],[30.429952,11.156137]),
                          ("PORT_B_TX_MCU",[24.697426,15.276897],[27.104906,6.594077])]:
            router.connect(net,a,b,"joint-"+net+"-trunk",ALL_LAYERS,ALL_LAYERS,budget=65)
            C_guard(net+"-complete")
        # Complete the short IMU branch first, then all released full corridors.
        router.connect("IMU_CS",[24.259999,10.365],[25.7,8.99],"joint-IMU-CS-R3",("F.Cu",),("F.Cu",),budget=40)
        for name in ("CSfirst-0-leg-0","CSfirst-1-leg-0","CSfirst-3-leg-0"):
            recipe = g.recipe_by_name[name]
            router.connect(recipe["net"],recipe["points"][0],recipe["points"][-1],
                           "joint-restore-"+name,(recipe["layer"],),(recipe["layer"],),budget=55)
            C_guard(name+"-restored")
        finished = c_helper.finish(g,prepared,router.objects,deadline,peer_guard=peer_guard,progress=C_progress)
        accept_C(finished,"finish")

        # Full physical partitions, including every retained source-boundary
        # terminal. Saved GND fill is only a DC bookkeeping control.
        zones=[]
        for zone in g.N["zones"]:
            if not zone["rule"] and zone["net"]=="GND":
                zones.append(({"uuid":zone["uuid"],"net":"GND","kind":"saved_native_zone"},
                              {l:g.s.geom(p) for l,p in zone["filled"].items() if p},{},None))
        final_checks=[]
        required_nets={net for net,a,b in jobs}|{"PORT_C_RX_EXT","PORT_C_TX_EXT","PORT_C_RX_MCU","PORT_C_TX_MCU","VX_PROTECTED"}
        for net in sorted(required_nets):
            groups,_=partition(router.objects,net)
            final_checks.append({"net":net,"physical_components":len(groups),"passed":len(groups)==1})
        for row in ledger["nets"]:
            _,membership=partition(router.objects+(zones if row["net"]=="GND" else []),row["net"])
            for old in row["source_terminal_components"]:
                roots=[membership[uid] for uid in old]
                passed=bool(set.intersection(*roots))
                final_checks.append({"net":row["net"],"retained_source_terminals":old,"passed":passed,
                                     "saved_fill_only":row["net"]=="GND"})
        out["final_physical_partition_checks"]=final_checks
        if not all(row["passed"] for row in final_checks):
            stop("Complete source-component/actual-function ledger is not closed.",final_checks)
        # Actual physical dictionaries must remain exact, including every pad.
        current={o["uuid"]:o for o,c,m,d in router.objects}
        assert len(current)==len(router.objects)
        assert all(current[uid]==record for uid,record in g.by.items() if uid not in cuts)
        assert all(uid not in current for uid in cuts)
        roles={o["uuid"]:o["role"] for o,c,m,d in router.objects if "role" in o}
        all_recipes={}
        for row in proposal["proposed_common_routes"]+proposal["proposed_common_vias"]+router.routes+router.vias+extra_routes+extra_vias:
            name=row["name"]
            if name in current:
                all_recipes[name]=row
        # The reserved RX barrel is exported only after full C closure.
        if reservation["name"] in current:
            all_recipes[reservation["name"]]=reservation
        assert set(current)-set(g.by)==set(all_recipes), "Every new copper object needs full recorded constructor arguments"
        final_finite=[]
        exported=[]
        for name,row in all_recipes.items():
            net=row["net"];objects=[q for q in router.objects if q[0]["uuid"]!=name]
            role=roles.get(name) or row.get("role")
            alias=net
            if net in ("PORT_C_RX_EXT","PORT_C_TX_EXT"):
                if role is None:
                    stop("New protected C copper lacks explicit physical branch role.",name)
                alias,objects=branch_view(net,role,objects,additional_roles=roles)
            if "points" in row:
                checks=g.check_track(alias,row["layer"],row["points"],width=row["width"],objects=objects)
                recipe=routing.trace_recipe(net,row["layer"],row["points"],name,row["width"])
            else:
                checks=g.check_via(alias,row["xy"],objects=objects)
                recipe=routing.via_recipe(g,net,row["xy"],name)
            final_finite.append({"name":name,"passed":all(q["pass_with_polygon_error"] for q in checks),"nearest":checks[:4]})
            exported.append(recipe)
        out["final_mutual_finite_checks"]=final_finite
        if not all(q["passed"] for q in final_finite):
            stop("Final width-aware mutual finite check failed.",final_finite)
        plan=json.loads((ROOT/"recovered-native7/recovery-importer/empty-plan-v1.json").read_text())
        plan["removed_native_records"]=[{"record":g.by[uid],"full_record_sha256":hashlib.sha256(json.dumps(g.by[uid],sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()} for uid in sorted(cuts)]
        plan["added_copper"]=exported
        target_plan=ROOT/contract["incremental_plan"]
        target_plan.write_text(json.dumps(plan,indent=2)+"\n")
        out["complete"]=True
        out["incremental_plan"]={"path":str(target_plan.relative_to(ROOT)),"sha256":adapter.digest(target_plan)}
        out["terminal_reason"]="All seven original opens and nine source-connectivity restorations close in the exact planning model; native/reference/electrical gates remain pending."
        save()
    except (StopJoint,routing.JointRoutingFailure) as exc:
        if "terminal_reason" not in out:
            out["terminal_reason"]="Exact joint construction stopped before full closure."
            out["terminal_detail"]=exc.args[0]
            save()
    except Exception as exc:
        out["terminal_reason"]="Construction implementation error; no candidate selected."
        out["exception"]={"type":type(exc).__name__,"message":str(exc)}
        save()
        raise
    finally:
        signal.alarm(0)
        print("TERMINAL",out.get("terminal_reason"),"seconds",time.monotonic()-start,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--contract",type=Path,required=True)
    args=p.parse_args()
    main(args.contract)
