"""Bounded routing primitives for one exact native7 joint transaction.

Imported geometry helpers are supplied by the verified adapter.  Every inset
solver domain must be wholly covered by its original domain; every completed
centerline is checked against the original finite obstacles at its actual width.
"""
import math
from decimal import Decimal
import time
from shapely.geometry import LineString, Point, box
from shapely.ops import nearest_points


class JointRoutingFailure(RuntimeError):
    pass


def require_native_grid(points):
    for point in points:
        if len(point) != 2:
            raise JointRoutingFailure({"stage":"native_coordinate_grid", "point":point})
        for value in point:
            if not math.isfinite(value) or Decimal(str(value))*1000000 != (Decimal(str(value))*1000000).to_integral_value():
                raise JointRoutingFailure({"stage":"native_coordinate_grid", "point":point,
                                           "reason":"Proposed geometry is off the exact 1 nm grid"})


def trace_recipe(net, layer, points, name, width):
    return dict(kind="track", name=name, net=net, logical_net=net, layer=layer,
                points=points, width=width)


def via_recipe(g, net, xy, name):
    return dict(kind="via", name=name, net=net, logical_net=net, xy=xy,
                diameter=.45, drill=.20, layers=list(g.N["copper_layers"]),
                tented_front=True, tented_back=True)


def route_conservative(g, component, a, b, deadline):
    """Conservative local domains first; no outward contour approximation."""
    attempts = []
    if component is None or not component.covers(Point(a)) or not component.covers(Point(b)):
        return None, [{"reason": "Endpoints do not share the exact finite component."}]
    for points in g.s.paths2(a, b):
        if component.covers(LineString(points)):
            return points, [{"method": "exact_direct_or_octilinear", "passed": True}]
    # These are execution heuristics only. A rejected inset does not imply that
    # the original domain is infeasible.
    xmin, xmax = min(a[0], b[0]), max(a[0], b[0])
    ymin, ymax = min(a[1], b[1]), max(a[1], b[1])
    for margin, tolerance in [(2, .0001), (5, .0001), (9, .00005), (None, .00002), (None, 0)]:
        if time.monotonic() >= deadline:
            break
        local = component if margin is None else component.intersection(box(xmin-margin, ymin-margin, xmax+margin, ymax+margin))
        if tolerance:
            local = local.simplify(tolerance, preserve_topology=True).buffer(-2*tolerance)
        candidates = [p for p in g.rt.parts(local) if p.covers(Point(a)) and p.covers(Point(b))]
        row = {"margin_mm": margin, "conservative_inset_tolerance_mm": tolerance,
               "original_domain_covers_solver_domain": False, "passed": False}
        attempts.append(row)
        if not candidates:
            row["reason"] = "Inset or crop lacks both endpoints."
            continue
        candidate = max(candidates, key=lambda p: p.area)
        if not candidate.is_valid or not component.covers(candidate):
            row["reason"] = "Solver domain not wholly covered by original finite polygon."
            continue
        row["original_domain_covers_solver_domain"] = True
        remaining = deadline - time.monotonic()
        subdeadline = deadline if tolerance == 0 else min(deadline, time.monotonic() + max(1, remaining * .45))
        points = g.rt.route(candidate, a, b, subdeadline)
        if points is not None and component.covers(LineString(points)):
            row["passed"] = True
            row["original_domain_covers_final_centerline"] = True
            return points, attempts
        row["reason"] = "No completed exact-covered centerline within this solver budget."
    return None, attempts


def source_target_frontier(g, graph, plan):
    def reachable(starts):
        seen, pending = set(starts), list(starts)
        while pending:
            i = pending.pop()
            for j, weight, edge in graph["adj"][i]:
                if j not in seen:
                    seen.add(j)
                    pending.append(j)
        return seen
    left = reachable(plan["start_nodes"])
    right = reachable(plan["end_nodes"])
    rows = []
    for layer in ("B.Cu", "In3.Cu", "In2.Cu", "F.Cu"):
        pairs = [(graph["nodes"][a][1].distance(graph["nodes"][b][1]), a, b)
                 for a in left if graph["nodes"][a][0] == layer
                 for b in right if graph["nodes"][b][0] == layer]
        for distance, a, b in sorted(pairs)[:2]:
            x, y = nearest_points(graph["nodes"][a][1], graph["nodes"][b][1])
            bridge = LineString([x, y])
            blockers = []
            for obstacle in graph["obstacles"][layer]:
                gap = bridge.distance(obstacle["geometry"]) - obstacle["required_center_distance_mm"]
                if gap < g.s.ERROR:
                    blockers.append({k: v for k, v in obstacle.items() if k != "geometry"} | {"extra_clearance_mm": gap})
            rows.append({"layer": layer, "gap_mm": distance, "source_node": a, "target_node": b,
                         "source_witness": list(x.coords[0]), "target_witness": list(y.coords[0]),
                         "blockers": sorted(blockers, key=lambda q: q["extra_clearance_mm"])})
    return rows


class Router:
    def __init__(self, g, objects, deadline, prefix="joint-native7", receipt=None):
        self.g, self.objects, self.deadline, self.prefix = g, list(objects), deadline, prefix
        self.routes, self.vias, self.attempts = [], [], []
        self.receipt = receipt

    def snapshot(self):
        return list(self.objects), len(self.routes), len(self.vias)

    def restore(self, snapshot):
        objects, nr, nv = snapshot
        self.objects = list(objects)
        self.routes, self.vias = self.routes[:nr], self.vias[:nv]

    def graph(self, net, start, end, start_layers=("B.Cu",), end_layers=("B.Cu",), objects=None):
        graph = self.g.gg.build(net, self.objects if objects is None else objects)
        plan = self.g.gg.connect(graph, start, end, start_layers, end_layers)
        for i, leg in enumerate(plan["legs"][:-1]):
            transition = leg.get("transition", {})
            if transition.get("kind") != "new_via_region":
                continue
            nxt = plan["legs"][i+1]["node"]
            matches = [edge["geometry"] for j, weight, edge in graph["adj"][leg["node"]]
                       if j == nxt and edge["kind"] == "new_via_region" and edge["geometry"].covers(Point(transition["xy"]))]
            if matches:
                transition["wkb_hex"] = matches[0].wkb_hex
        return graph, plan

    def add_via(self, net, xy, name):
        require_native_grid([xy])
        checks = self.g.check_via(net, xy, objects=self.objects)
        if not all(row["pass_with_polygon_error"] for row in checks):
            raise JointRoutingFailure({"stage": "via_finite", "name": name, "xy": xy, "nearest": checks[:8]})
        recipe = via_recipe(self.g, net, xy, name)
        self.objects.append(self.g.via(net, xy, name))
        self.vias.append(recipe)
        return recipe

    def add_track(self, net, layer, points, name, width=.127):
        require_native_grid(points)
        checks = self.g.check_track(net, layer, points, width=width, objects=self.objects)
        if not all(row["pass_with_polygon_error"] for row in checks):
            raise JointRoutingFailure({"stage": "track_finite", "name": name, "width": width, "nearest": checks[:8]})
        recipe = trace_recipe(net, layer, points, name, width)
        self.objects.append(self.g.track(net, layer, points, name, width))
        self.routes.append(recipe)
        return recipe

    def layer_route(self, net, layer, start, end, name, width=.127, budget=45):
        if start == end:
            return None
        free, obs, via_obs = self.g.rt.domain(net, layer, width=width, objects=self.objects)
        component = self.g.rt.component(free, start)
        deadline = min(self.deadline, time.monotonic() + budget)
        points, attempts = route_conservative(self.g, component, start, end, deadline)
        self.attempts.append({"name": name, "net": net, "layer": layer, "start": start, "end": end,
                              "routing_attempts": attempts, "complete": points is not None})
        if points is None:
            raise JointRoutingFailure({"stage": "layer_construction", "name": name, "net": net,
                                       "layer": layer, "start": start, "end": end, "attempts": attempts})
        # Quantize the proposal before its final finite check and constructor,
        # then recheck coverage by the original domain. Never round accepted copper.
        raw_points = points
        points = [[round(float(x),6),round(float(y),6)] for x,y in raw_points]
        grid_check = {"name":name,"stage":"proposal_grid_before_final_finite", "changed":points!=raw_points,
                      "original_domain_covers_grid_centerline":component.covers(LineString(points))}
        self.attempts.append(grid_check)
        if any(a==b for a,b in zip(points,points[1:])) or not grid_check["original_domain_covers_grid_centerline"]:
            raise JointRoutingFailure(grid_check | {"reason":"Grid proposal lost original-domain coverage or has a zero segment"})
        return self.add_track(net, layer, points, name, width)

    def connect(self, net, start, end, name, start_layers=("B.Cu",), end_layers=("B.Cu",), budget=60):
        before = self.snapshot()
        graph, plan = self.graph(net, start, end, start_layers, end_layers)
        attempt = {"name": name, "plan": plan, "complete": False}
        self.attempts.append(attempt)
        if not plan["connected"]:
            attempt["frontier"] = source_target_frontier(self.g, graph, plan)
            raise JointRoutingFailure({"stage": "actual_target_graph", "name": name, "plan": plan,
                                       "frontier": attempt["frontier"]})
        deadline = min(self.deadline, time.monotonic() + budget)
        try:
            for i, via in enumerate(plan["new_vias"]):
                self.add_via(net, via["xy"], name + "-via-" + str(i))
            for i, leg in enumerate(plan["legs"]):
                self.layer_route(net, leg["layer"], leg["start"], leg["end"], name + "-leg-" + str(i),
                                 budget=max(.1, deadline-time.monotonic()))
            attempt["complete"] = True
            return attempt
        except JointRoutingFailure as exc:
            attempt["attempted_routes"] = self.routes[before[1]:]
            attempt["attempted_vias"] = self.vias[before[2]:]
            attempt["failure"] = exc.args[0]
            self.restore(before)
            raise
