#!/usr/bin/env python3
"""Small synthetic controls; no native board edits or heavy simulations."""
import copy
import json
import math
from pathlib import Path
import unittest

from shapely.geometry import Polygon, box

from check_signal_geometry import (estimate, route_capacitance, sphere_cap_pf,
                                   topology, validate_profile, usb_reference_intervals, validate_bindings)


def rectangle(x0, y0, x1, y1):
    return [{"outer": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], "holes": []}]


def pad(uid, xy):
    x, y = xy
    return {"uuid": uid, "kind": "pad", "key": uid, "net": "BARO_SCL", "xy": xy,
            "copper": {"F.Cu": rectangle(x - .1, y - .1, x + .1, y + .1)}}


def track(uid, a, b):
    from shapely.geometry import LineString
    copper = LineString([a, b]).buffer(.02)
    return {"uuid": uid, "kind": "track", "net": "BARO_SCL", "start": a, "end": b,
            "width": .04, "copper": {"F.Cu": [{"outer": list(copper.exterior.coords), "holes": []}]}}


def native(connected=True):
    return {"zone_uuids": [], "all_native_copper_connected": connected,
            "all_terminals_connected": connected, "terminal_inventory_matches": True,
            "required_terminals": ["U1.61", "U4.4", "R7.2"]}


def example():
    return [pad("U1.61", [0, 0]), pad("U4.4", [4, 0]), pad("R7.2", [2, 2]),
            track("main", [0, 0], [4, 0]), track("branch", [2, 0], [2, 2])]


class TopologyControls(unittest.TestCase):
    def test_midtrack_pullup_branch_and_whole_tree(self):
        r = topology(example(), native())
        self.assertTrue(r["clean_complete_tree"])
        self.assertEqual(len(r["branches"]), 1)
        self.assertAlmostEqual(r["pullup_branch"]["outside_land_length_mm"], 1.9)
        self.assertAlmostEqual(r["terminal_paths"][0]["outside_land_length_mm"], 3.8)

    def test_dangling_stub_detected(self):
        r = topology(example() + [track("stub", [3, 0], [3, -1])], native())
        self.assertFalse(r["clean_complete_tree"])
        self.assertEqual(len(r["dangling_nonterminal_endpoints"]), 1)

    def test_disconnected_copper_detected(self):
        r = topology(example() + [track("floating", [8, 0], [9, 0])], native(False))
        self.assertFalse(r["clean_complete_tree"])
        self.assertEqual(r["component_count"], 2)

    def test_loop_detected(self):
        r = topology(example() + [track("a", [1, 0], [1, -1]), track("b", [1, -1], [3, -1]),
                                 track("c", [3, -1], [3, 0])], native())
        self.assertFalse(r["clean_complete_tree"])
        self.assertEqual(r["cycle_rank"], 1)

    def test_native_mismatch_rejected(self):
        r = topology(example()[:-1], native())
        self.assertFalse(r["supported"])

    def test_arc_refuses_topology(self):
        data = example(); data[-1]["kind"] = "arc"
        self.assertFalse(topology(data, native())["supported"])

    def test_offcenter_copper_junction_refused(self):
        data = example() + [track("edge_contact", [1, .03], [1, 1])]
        self.assertFalse(topology(data, native())["supported"])

    def test_incomplete_route_refuses_even_numeric_model(self):
        n = native(False); n["topology"] = topology(example()[:-1], n)
        result = estimate(n, example()[:-1], [], {"stackup": {"native_block_sha256": "x", "layers": []}}, None)
        self.assertIsNone(result["estimated_total_pF"])
        self.assertFalse(result["qualification_pass"])


class CapacitanceControls(unittest.TestCase):
    def test_exact_concentric_sphere_and_distant_limit(self):
        eps = 8.8541878128e-3
        self.assertAlmostEqual(sphere_cap_pf(1, 2, 1), 8 * math.pi * eps)
        self.assertAlmostEqual(sphere_cap_pf(1, 1e10, 1), 4 * math.pi * eps, places=10)

    def test_geometry_material_monotonicity(self):
        c = sphere_cap_pf(.1, .3, 4)
        self.assertGreater(sphere_cap_pf(.11, .3, 4), c)
        self.assertGreater(sphere_cap_pf(.1, .29, 4), c)
        self.assertGreater(sphere_cap_pf(.1, .3, 4.1), c)

    def test_invalid_shell_refused(self):
        for b in [.09, .1]:
            with self.assertRaises(ValueError):
                sphere_cap_pf(.1, b, 4)

    def test_wire_above_ground_analytic_per_length_screen(self):
        # A long circular wire, h=0.2, r=0.01 mm. A=cover radius
        # contains each cylindrical slice. Infinite-wire analytic comparator
        # is 2*pi*eps/acosh(h/r); finite-end effects are deliberately not called exact.
        eps, er, h, r, step = 8.8541878128e-3, 4.1, .2, .01, .1
        exact_per_length = 2 * math.pi * eps * er / math.acosh(h / r)
        bound_per_length = sphere_cap_pf(math.hypot(r, step / 2), h, er) / step
        self.assertGreater(bound_per_length, exact_per_length)

    def test_parallel_plate_analytic_area_screen(self):
        # Tiled zero-thickness signal sheet at h above a ground plane.
        # Each square is enclosed by a sphere; all trial shells end at the plane.
        eps, er, h, side = 8.8541878128e-3, 4.1, .1, .06
        parallel_plate_per_area = eps * er / h
        bound_per_area = sphere_cap_pf(side / math.sqrt(2), h, er) / side ** 2
        self.assertGreater(bound_per_area, parallel_plate_per_area)

    def test_close_foreign_copper_increases_or_refuses(self):
        obj = track("signal", [0, 0], [1, 0])
        meta = {"stackup": {"layers": [{"name": "F.Cu", "type": "copper", "thickness": .01},
                                            {"name": "dielectric 1", "type": "prepreg", "thickness": .2},
                                            {"name": "In1.Cu", "type": "copper", "thickness": .01}]}}
        p = {"epsilon_r_max": 4.1, "signal_edge_growth_mm": 0., "foreign_edge_growth_mm": 0.,
             "relative_layer_registration_mm": 0., "unmodeled_external_copper_min_distance_mm": 10.,
             "thickness_bounds_mm": {x["name"]: {"min": x["thickness"], "max": x["thickness"]} for x in meta["stackup"]["layers"]}}
        plane = {"layer": "In1.Cu", "net": "GND", "shape": box(-10, -10, 10, 10)}
        a = route_capacitance([obj], [plane], meta, p)["static_route_bound_pF"]
        neighbor = {"layer": "F.Cu", "net": "other", "shape": box(-10, .05, 10, 1)}
        b = route_capacitance([obj], [plane, neighbor], meta, p)["static_route_bound_pF"]
        self.assertGreater(b, a)
        neighbor["shape"] = box(-10, .019, 10, 1)
        with self.assertRaises(ValueError):
            route_capacitance([obj], [plane, neighbor], meta, p)

    def test_complete_conditional_ledger_never_claims_qualification(self):
        objects = example(); n = native(); n["topology"] = topology(objects, n)
        meta = {"stackup": {"native_block_sha256": "control", "layers": [
            {"name": "F.Cu", "type": "copper", "thickness": .01},
            {"name": "dielectric 1", "type": "prepreg", "thickness": .2},
            {"name": "In1.Cu", "type": "copper", "thickness": .01}]}}
        p = {"native_stackup_sha256": "control", "reviewed_engineering_assumptions": True,
             "production_stackup_confirmed": False, "epsilon_r_max": 4.1,
             "epsilon_r_sensitivity": [4.1, 5.5], "signal_edge_growth_mm": 0.,
             "foreign_edge_growth_mm": 0., "relative_layer_registration_mm": 0.,
             "unmodeled_external_copper_min_distance_mm": 10., "probe_capacitance_pF": 1.,
             "additional_model_allowance_pF": .5,
             "thickness_bounds_mm": {x["name"]: {"min": x["thickness"], "max": x["thickness"]} for x in meta["stackup"]["layers"]},
             "evidence": {k: "Synthetic control, not board/supplier evidence" for k in ["dielectric_bound", "thickness_bounds", "etch_registration", "probe", "external_copper", "assembly_allocation"]}}
        entries = [{"layer": "In1.Cu", "net": "GND", "shape": box(-10, -10, 10, 10)}]
        r = estimate(n, objects, entries, meta, p)
        self.assertEqual(r["status"], "conditional_engineering_estimate")
        self.assertFalse(r["qualification_pass"])
        self.assertFalse(r["internal_pullup_credit"])
        self.assertAlmostEqual(r["external_pullup_Rmax_ohm"], 2244.22)
        self.assertEqual(len(r["route"]["rows"]), 2)  # Main plus full pull-up branch.
        self.assertGreater(r["epsilon_r_sensitivity"][1]["engineering_total_pF"], r["estimated_total_pF"])
        n["terminal_inventory_matches"] = False
        self.assertIsNone(estimate(n, objects, entries, meta, p)["estimated_total_pF"])
        p["native_stackup_sha256"] = "stale"
        self.assertIn("Profile does not bind this exact native stackup", validate_profile(p, meta))


class ReferenceControls(unittest.TestCase):
    def test_tampered_geometry_rejected(self):
        with self.assertRaises(ValueError):
            validate_bindings({"board_sha256": "board"}, {"board_sha256": "board", "geometry_sha256": "geometry", "source_unchanged": True}, "tampered", "board")

    def test_stale_board_rejected(self):
        with self.assertRaises(ValueError):
            validate_bindings({"board_sha256": "board"}, {"board_sha256": "board", "geometry_sha256": "geometry", "source_unchanged": True}, "geometry", "changed")

    def test_merged_antipad_does_not_exempt_distant_void(self):
        via = {"uuid": "v", "kind": "via", "net": "USB_P", "xy": [0, 0],
               "width_by_layer": {"In1.Cu": .45, "In4.Cu": .45}}
        t = track("t", [0, 0], [0, 3]); t["net"] = "USB_P"
        g = {"objects": [via, t]}
        plane = Polygon([[-5, -5], [5, -5], [5, 5], [-5, 5]],
                        [[[-.4, -.4], [.4, -.4], [.4, 2], [-.4, 2]]])
        entries = [{"shape": plane, "layer": l, "net": "GND", "kind": "zone"} for l in ["In1.Cu", "In4.Cu"]]
        meta = {"nets": {"USB_P": {"via_own_clearance_by_layer_mm": {"v": {"In1.Cu": .127, "In4.Cu": .127}}}},
                "ground_zone_clearances": [{"layers": ["In1.Cu", "In4.Cu"], "local_clearance_mm": .127}],
                "native_design_max_error_mm": .005}
        r = usb_reference_intervals(g, meta, entries)
        self.assertAlmostEqual(r["totals_mm"]["USB_P"]["local_own_via_antipad_interval"], .362)
        self.assertAlmostEqual(r["totals_mm"]["USB_P"]["plane_edge_void_or_crossing_outside_local_via_window"], 1.638)
        self.assertTrue(r["intervals"][0]["containing_void"]["extends_beyond_local_window"])


if __name__ == "__main__":
    unittest.main()
