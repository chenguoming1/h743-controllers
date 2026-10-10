#!/usr/bin/env python3
"""Focused controls for drill-aware saved-zone reference logic."""
import unittest
from shapely.geometry import LineString, Point, box
from check_critical_reference import ground_geometry, ground_ties, partition_missing
from check_signal_geometry import copper_entries, usb_reference_intervals


def rows(shape):
    return [{"outer": list(shape.exterior.coords), "holes": [list(r.coords) for r in shape.interiors]}]


def fixture():
    land = Point(0, 0).buffer(.225, quad_segs=96)
    drill = Point(0, 0).buffer(.1, quad_segs=96)
    via = {"uuid": "gnd-via", "net": "GND", "kind": "via", "plated": True, "xy": [0, 0],
           "barrel_layers": ["F.Cu", "In1.Cu", "In4.Cu", "B.Cu"],
           "copper": {l: rows(land) for l in ["In1.Cu", "In4.Cu"]},
           "drill": {"start": [0, 0], "end": [0, 0], "width": .2, "inside": rows(drill), "outside": rows(drill)}}
    g = {"copper_layers": ["F.Cu", "In1.Cu", "In4.Cu", "B.Cu"], "objects": [via],
         "zones": [{"uuid": "zone", "net": "GND", "rule": False,
                    "filled": {l: rows(box(-1, -1, 1, 1)) for l in ["In1.Cu", "In4.Cu"]}}]}
    return g


def classified(g):
    raw, zones, physical, cuts = ground_geometry(g, copper_entries(g))
    return ground_ties(g, zones, cuts)


class CriticalReferenceControls(unittest.TestCase):
    def test_valid_annular_contact_accepted(self):
        yes, no = classified(fixture())
        self.assertEqual((len(yes), len(no)), (1, 0))
        self.assertTrue(all(a > .12 for a in yes[0]["positive_saved_zone_contact_area_mm2"].values()))

    def test_self_land_contact_cannot_replace_missing_zone(self):
        g = fixture()
        g["zones"][0]["filled"]["In4.Cu"] = rows(box(2, 2, 3, 3))
        raw, zone, physical, cuts = ground_geometry(g, copper_entries(g))
        # The previous self-union criterion would falsely accept this tie.
        self.assertTrue(raw["In4.Cu"].intersects(Point(0, 0)))
        yes, no = ground_ties(g, zone, cuts)
        self.assertEqual((len(yes), len(no)), (0, 1))
        # Exercise the corrected legacy USB entry point with an actual signal
        # transition; its nearby GND self-land must not be accepted as a tie.
        signal = {"uuid": "usb", "kind": "via", "net": "USB_P", "xy": [.5, .5],
                  "width_by_layer": {"In1.Cu": .45, "In4.Cu": .45}}
        g["objects"].append(signal)
        meta = {"nets": {"USB_P": {"via_own_clearance_by_layer_mm": {"usb": {"In1.Cu": .127, "In4.Cu": .127}}}},
                "ground_zone_clearances": [], "native_design_max_error_mm": .005}
        # The legacy helper accepts synthetic signals without full copper;
        # reuse the already exported entries to isolate the GND tie check.
        legacy = usb_reference_intervals(g, meta, [e for e in copper_entries(fixture()) if e["kind"] != "zone"] + [
            {"uuid": "z1", "kind": "zone", "net": "GND", "layer": "In1.Cu", "shape": box(-1,-1,1,1)},
            {"uuid": "z4", "kind": "zone", "net": "GND", "layer": "In4.Cu", "shape": box(2,2,3,3)}])
        self.assertIsNone(legacy["transitions"][0]["nearest_GND_via_tying_In1_In4"])

    def test_short_barrel_cannot_tie_planes(self):
        g = fixture(); g["objects"][0]["barrel_layers"] = ["F.Cu", "In1.Cu"]
        yes, no = classified(g)
        self.assertEqual((len(yes), len(no)), (0, 1))

    def test_contact_only_inside_drill_rejected(self):
        g = fixture(); g["zones"][0]["filled"]["In4.Cu"] = rows(box(-.03, -.03, .03, .03))
        self.assertEqual(len(classified(g)[0]), 0)

    def test_zero_area_tangent_rejected(self):
        g = fixture(); g["zones"][0]["filled"]["In4.Cu"] = rows(box(.225, -.1, 1, .1))
        self.assertEqual(len(classified(g)[0]), 0)

    def test_drill_respects_finite_barrel_span(self):
        g = fixture(); g["objects"][0]["barrel_layers"] = ["F.Cu", "In1.Cu"]
        _, _, physical, _ = ground_geometry(g, copper_entries(g))
        self.assertFalse(physical["In1.Cu"].covers(Point(0, 0)))
        self.assertTrue(physical["In4.Cu"].covers(Point(0, 0)))

    def test_npth_removes_all_layer_copper(self):
        g = fixture(); v = g["objects"][0]; v["plated"] = False; v["npth"] = True; v["barrel_layers"] = []
        _, _, physical, _ = ground_geometry(g, copper_entries(g))
        self.assertFalse(physical["In1.Cu"].covers(Point(0, 0)))
        self.assertFalse(physical["In4.Cu"].covers(Point(0, 0)))

    def test_merged_hole_keeps_extension_and_width_only_gap(self):
        # Trace centerline can miss a void which its finite width intersects.
        trace = LineString([(0, 0), (3, 0)])
        hole = box(0, -.04, 2, .1)
        own = Point(0, 0).buffer(.362, quad_segs=96).intersection(hole)
        missing = trace.intersection(hole)
        p = partition_missing(missing, [own], Point(10, 10).buffer(.1))
        self.assertAlmostEqual(p["local_own_via_window_in_saved_hole"].length, .362)
        self.assertAlmostEqual(p["saved_void_or_edge_outside_own_window"].length, 1.638)
        edge_hole = box(1, .04, 2, .2)
        self.assertEqual(trace.intersection(edge_hole).length, 0)
        width_missing = trace.buffer(.1).intersection(edge_hole)
        width_parts = partition_missing(width_missing, [own], Point(10, 10).buffer(.1))
        self.assertAlmostEqual(width_parts["saved_void_or_edge_outside_own_window"].area, .06)
        self.assertAlmostEqual(sum(x.area for x in width_parts.values()), width_missing.area)

    def test_sloped_interval_partition_conserves_length(self):
        line = LineString([(1.321999, 3.714987), (4.619374, 8.919273)])
        mask = Point(line.coords[0]).buffer(.362, quad_segs=96)
        p = partition_missing(line, [mask], Point(10, 10).buffer(.1))
        self.assertAlmostEqual(sum(x.length for x in p.values()), line.length, places=12)


if __name__ == "__main__":
    unittest.main()
