"""One source-bound northern-cell RX-down transition control; no native board edits."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
HELPERS=ROOT/"ordinary-routing/tests/native13-access"
sys.path.insert(0,str(HELPERS))
import native7_recovered_context_v3 as adapter
from prepare_native7_coordinated_context_v3 import replay


def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def main(contract_file):
    start=time.monotonic()
    contract=json.loads(contract_file.read_text())
    for row in contract["source_files"]:
        assert adapter.digest(ROOT/row["path"])==row["sha256"],row["path"]
    deadline=start+contract["internal_seconds"]
    output=ROOT/contract["receipt"]
    out={"schema":"f722-native7-northern-RX-down-control/v2","source_contract_sha256":adapter.digest(contract_file),
         "script_sha256":adapter.digest(__file__),"complete":False,"selected":False,"native_board_edited":False,
         "stages":[],"attempts":[],"corridor_y_max_mm":contract["corridor_y_max_mm"],
         "local_window_is_candidate_choice_not_global_rule":True,
         "full_C_SPI_B_support_donor_restoration_pending":True}

    def save():
        out["seconds"]=time.monotonic()-start
        output.write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")

    def stage(name,event):
        now=time.monotonic()
        out["stages"].append({"stage":name,"event":event,"elapsed_seconds":now-start,"remaining_seconds":deadline-now})
        save()

    def alarm(signum,frame):
        out["terminal_reason"]="Overall bounded control deadline; no candidate selected"
        save()
        raise TimeoutError(out["terminal_reason"])

    signal.signal(signal.SIGALRM,alarm);signal.alarm(contract["internal_seconds"])
    try:
        from shapely import unary_union
        from shapely.geometry import Point,LineString,box
        from shapely.ops import nearest_points,polylabel
        C=load_module(ROOT/contract["C_helper"],"early_RX_C_bound_helper")
        g=adapter.load();out["source"]=g.binding()
        proposal,scope,cuts,held,added,reservation,reserved_via=replay(g)
        original=held+added+[reserved_via]
        packet,scope,view=C._load(g,original)
        objects=held+added
        out["removed_native_ids"]=sorted(cuts)
        out["retired_planning_only_reservation"]=reservation["name"]
        jobs=C._jobs(g);job=next(j for j in jobs if j["name"]=="RX_down")
        net,peers=C._view(view,job,objects)
        stage("exact_source_and_inner_target_domains","start")
        with C._width_state(g,.127):
            ffree,fobs,vobs=g.rt.domain(net,"F.Cu",objects=peers)
            fsource=g.rt.component(ffree,job["a"])
            inner_graph=g.gg.build(net,peers,layers=("B.Cu","In3.Cu","In2.Cu"))
        if fsource is None:
            raise C.CFailure("Actual RX-down source has no F centerline component")
        target_nodes=g.gg.terminals(inner_graph,job["b"],("B.Cu",))
        reachable=set(target_nodes);pending=list(target_nodes)
        while pending:
            for other,weight,edge in inner_graph["adj"][pending.pop()]:
                if other not in reachable:reachable.add(other);pending.append(other)
        legal=g.s.OUTLINE.buffer(-.479-g.s.ERROR-.0001).difference(g.rt.expanded(vobs))
        source_legal=fsource.intersection(legal)
        target_shapes=[inner_graph["nodes"][i][1] for i in sorted(reachable)]
        target_union=unary_union(target_shapes)
        unbounded=source_legal.intersection(target_union)
        xmin,ymin,xmax,ymax=g.s.OUTLINE.bounds
        local_trace=fsource.intersection(box(xmin-1,ymin-1,xmax+1,contract["corridor_y_max_mm"]))
        local_component=g.rt.component(local_trace,job["a"])
        local=unbounded.intersection(local_component) if local_component is not None else unbounded.difference(unbounded)
        out["domains"]={"source_F_wkb_hex":fsource.wkb_hex,
             "source_connected_unclipped_legal_via_area_mm2":source_legal.area,
             "source_connected_unclipped_legal_via_wkb_hex":source_legal.wkb_hex,
             "target_compatible_unclipped_area_mm2":unbounded.area,"target_compatible_unclipped_wkb_hex":unbounded.wkb_hex,
             "local_source_trace_wkb_hex":None if local_component is None else local_component.wkb_hex,
             "local_target_compatible_area_mm2":local.area,"local_target_compatible_wkb_hex":local.wkb_hex,
             "actual_source":job["a"],"actual_target_pad":g.one_pad("R34.1"),
             "target_nodes":sorted(target_nodes),"inner_target_reachable_nodes":sorted(reachable),
             "inner_target_layers":[inner_graph["nodes"][i][0] for i in sorted(reachable)],
             "ordinary_inner_layers":["B.Cu","In3.Cu","In2.Cu"]}
        stage("exact_source_and_inner_target_domains","complete")
        parts=sorted(g.rt.parts(local),key=lambda p:(p.distance(Point(job["a"])),-p.area))
        if not parts:
            raise C.CFailure("No northern legal barrel reached before the former descending F wall; unrestricted domain retained separately")
        # Reassign exactly the previously reserved northern cell to downstream
        # RX. The center is chosen inside its measured legal domain, not fixed to
        # the old upstream representative. No other region or order is searched.
        reference=Point(contract["northern_reference_center"])
        matches=[p for p in parts if p.covers(reference)]
        if len(matches)!=1:
            raise C.CFailure("The former northern reference cell is not in the current source/target-connected northward chamber")
        region=matches[0]
        pole=polylabel(region,tolerance=.00001)
        xy=C._xy((pole.x,pole.y))
        if not region.covers(Point(xy)):
            raise C.CFailure("Rounded northern center left the exact legal domain")
        candidates=[("northern_cell_interior_representative",xy)]
        out["candidate_scope"]={"domain_count":len(parts),"sampled_domain_wkb_hex":region.wkb_hex,
             "reference_center":contract["northern_reference_center"],"reference_center_is_not_immutable":True,
             "representatives":candidates,"one_specific_cell_only":True,
             "F_approach_stays_north_of_former_wall_start_y":contract["corridor_y_max_mm"]}
        save()
        peer_jobs=[("FLASH_SCK","U1.34","U3.6"),("FLASH_MISO","U1.35","U3.2"),
                   ("FLASH_MOSI","U1.36","U3.5"),("PORT_B_RX_MCU","U1.37","R32.2"),
                   ("PORT_B_TX_MCU","U1.38","R33.2"),("FLASH_CS","U1.33","U3.1"),
                   ("FLASH_CS","U1.33","R4.2"),("DSM_RX_MCU","U1.43","R38.2"),
                   ("DSM_RX_MCU","U1.43","R71.2"),("IMU_CS","U1.20","U2.12"),
                   ("IMU_CS","U1.20","R3.2"),("LED_GREEN_K","U1.3","D1.1")]
        for index,(label,xy) in enumerate(candidates):
            C._deadline(deadline)
            trial={"index":index,"choice":label,"xy":xy,"routes":[],"vias":[],"checks":[],"complete":False}
            out["attempts"].append(trial);work=list(objects)
            prefix="northern-RX-down-"+str(index)
            stage("candidate_"+str(index),"start")
            try:
                C._add_via(g,view,job,work,xy,prefix+"-source-via",trial["vias"],trial["checks"])
                points,attempts=C._route(g,local_component,job["a"],xy,min(deadline-75,time.monotonic()+30))
                trial["source_F_solver"]=attempts
                if points is None:raise C.CFailure("No complete F entry inside this local source chamber")
                points=[C._xy(p) for p in points]
                if not local_component.covers(LineString(points)):
                    raise C.CFailure("Rounded F entry left exact local source chamber")
                row={"kind":"track","name":prefix+"-source-F","net":job["net"],"logical_net":job["net"],
                     "layer":"F.Cu","width":.127,"points":points,"role":"downstream"}
                trial["routes"].append(row)
                alias,branch=C._view(view,job,work)
                checks=g.check_track(alias,"F.Cu",points,width=.127,objects=branch)
                witnesses=C._section(g,row,work)
                check={"name":row["name"],"passed":C._passed(checks) and all(any(w["point"]==p and w["passed"] for w in witnesses) for p in (points[0],points[-1])),
                       "nearest":checks[:5],"full_width_contacts":witnesses}
                trial["checks"].append(check)
                if not check["passed"]:raise C.CFailure("Early F entry failed actual finite/contact proof")
                entry=g.track(row["net"],row["layer"],points,row["name"],.127)
                work.append((dict(entry[0],role="downstream"),*entry[1:]))
                stage("candidate_"+str(index)+"_F_entry","complete")
                entry_gate={"passed":False,"checks":[]}
                trial["source_entry_C_support"]=entry_gate
                C._all_C_plans(g,view,jobs,work,deadline,record=entry_gate)
                if not entry_gate["passed"]:
                    raise C.CFailure("Northern F approach/barrel itself consumes another actual C/VX path before the inner trunk")
                stage("candidate_"+str(index)+"_F_entry_C_support","passed")
                inner=dict(job,a=xy,start_layers=["B.Cu","In3.Cu","In2.Cu"],layers=["B.Cu","In3.Cu","In2.Cu"])
                plan,graph=C._plan(g,view,inner,work,deadline)
                trial["inner_actual_target_plan"]=plan
                if not plan["connected"]:raise C.CFailure("Early barrel cannot reach actual R34.1 on ordinary inner layers")
                C._allocate(g,view,inner,plan,work,prefix+"-inner",trial["routes"],trial["vias"],trial["checks"],
                            min(deadline-65,time.monotonic()+70),complete=True)
                if not C._already_connected(g,view,job,work):raise C.CFailure("Full RX-down actual copper path is missing")
                stage("candidate_"+str(index)+"_inner_route","complete")
                c_gate={"passed":False,"checks":[]};trial["remaining_C_support"]=c_gate
                C._all_C_plans(g,view,jobs,work,deadline,record=c_gate)
                if not c_gate["passed"]:raise C.CFailure("Complete early RX-down consumes another C/support path")
                trial["peer_access"]={"passed":False,"checks":[]};graphs={}
                for physical,a_key,b_key in peer_jobs:
                    C._deadline(deadline)
                    a,b=g.one_pad(a_key),g.one_pad(b_key)
                    jp={"name":physical,"net":physical,"role":None,"width":.127,"a":a["xy"],"b":b["xy"],
                        "start_layers":list(a["copper"]),"end_layers":list(b["copper"]),"layers":list(C.ORDINARY)}
                    if C._already_connected(g,view,jp,work):
                        row={"net":physical,"start_key":a_key,"end_key":b_key,"connected":True,"actual_copper_connected":True}
                    else:
                        if physical not in graphs:
                            with C._width_state(g,.127):graphs[physical]=g.gg.build(physical,work)
                        plan=g.gg.connect(graphs[physical],a["xy"],b["xy"],tuple(a["copper"]),tuple(b["copper"]))
                        row={"net":physical,"start_key":a_key,"end_key":b_key,"connected":plan["connected"],"plan":plan}
                    trial["peer_access"]["checks"].append(row);save()
                trial["peer_access"]["passed"]=all(x["connected"] for x in trial["peer_access"]["checks"])
                if not trial["peer_access"]["passed"]:raise C.CFailure("Complete early RX-down consumes an actual shared peer channel")
                groups=C._physical_groups(g,work,job["net"])
                cut=C._physical_groups(g,work,job["net"],"U15.1")
                contact=any({"U15.1","R34.1"}.issubset(x["keys"]) for x in groups)
                bypass=any({"U15.10","R34.1"}.issubset(x["keys"]) for x in cut)
                trial["actual_contacts_and_cut"]={"groups":groups,"cut_groups":cut,"U15_1_to_R34_1_connected":contact,
                                                  "no_NC10_to_R34_bypass_after_actual_pad_cut":not bypass}
                if not contact or bypass:raise C.CFailure("Actual bonded IO path or pad-cut proof failed")
                finite=[];annular=[]
                for row in trial["routes"]+trial["vias"]:
                    others=[q for q in work if q[0]["uuid"]!=row["name"]]
                    alias,branch=C._view(view,job,others)
                    check=(g.check_track(alias,row["layer"],row["points"],width=row["width"],objects=branch)
                           if row["kind"]=="track" else g.check_via(alias,row["xy"],objects=branch))
                    finite.append({"name":row["name"],"passed":C._passed(check),"nearest":check[:5]})
                    if row["kind"]=="track":annular.extend(C._annular_entries(g,row,work))
                trial["final_mutual_finite"]=finite;trial["annular_entries"]=annular
                if not all(x["passed"] for x in finite+annular):raise C.CFailure("Final finite or annular entry gate failed")
                C._preserved(C._snapshot(objects),work)
                trial["complete"]=True
                out["complete"]=True;out["accepted_attempt"]=index
                out["terminal_reason"]="Complete northern ordinary RX-down route preserves measured C/support and peer access; full joint routing and native validation remain pending"
                break
            except C.CFailure as error:
                trial["terminal_reason"]=str(error)
                stage("candidate_"+str(index),"failed")
        if not out["complete"]:
            out["terminal_reason"]="No complete compatible route through this specific northern cell and northward F approach"
        save()
    except TimeoutError:
        pass
    except Exception as error:
        out["terminal_reason"]=str(error)
        out["exception_type"]=type(error).__name__
        save()
    finally:
        signal.alarm(0)
        print(json.dumps({"complete":out["complete"],"terminal_reason":out.get("terminal_reason"),
                          "seconds":time.monotonic()-start,"receipt_sha256":adapter.digest(output)},indent=2),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--contract",type=Path,required=True)
    main(parser.parse_args().contract)
