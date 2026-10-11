"""Small synthetic geometry only. No source board, native runtime, or routing job."""
import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest

from shapely.geometry import LineString, Polygon, box

import audit_native7_final_contacts_v2 as audit


def exported(shape):
    return [{'outer': list(map(list, p.exterior.coords)),
             'holes': [list(map(list, h.coords)) for h in p.interiors]}
            for p in audit.polygon_parts(shape)]


def object_record(uid, shape, layer='F.Cu', kind='pad'):
    return {'uuid': uid, 'net': 'TEST_NET', 'kind': kind, 'copper': {layer: exported(shape)},
            'plated': False, 'barrel_layers': [], 'drill': None}


def track_record(uid, start, end, width=.2):
    # Test geometry is intentionally fabricated; no real-board geometry is read.
    shape = LineString([start, end]).buffer(width / 2, quad_segs=16)
    row = object_record(uid, shape, kind='track')
    row.update(start=list(start), end=list(end), width=width)
    return row


def via_record(uid='via', layers=('F.Cu', 'B.Cu')):
    row = object_record(uid, box(-1, -1, 1, 1), kind='via')
    row.update(plated=True, barrel_layers=list(layers), drill={'outside': exported(box(-.5, -.5, .5, .5))})
    row['copper'] = {layer: exported(box(-1, -1, 1, 1)) for layer in ('F.Cu', 'B.Cu')}
    return row


class SyntheticContacts(unittest.TestCase):
    def test_tangent_contact_is_not_a_connection(self):
        a = object_record('a', box(0, 0, 1, 1))
        b = object_record('b', box(1, 0, 2, 1))
        graph = audit.partition_native([a, b])
        self.assertEqual(len(graph['groups']), 2)
        self.assertEqual(graph['contacts'], {})

    def test_positive_area_contact_connects(self):
        a = object_record('a', box(0, 0, 1, 1))
        b = object_record('b', box(.9, 0, 2, 1))
        graph = audit.partition_native([a, b])
        self.assertEqual(len(graph['groups']), 1)
        self.assertGreater(graph['contacts'][('a', 'b', 'F.Cu')], 0)

    def test_copper_inside_drill_cannot_connect(self):
        via = via_record()
        phantom = object_record('phantom', box(-.1, -.1, .1, .1))
        graph = audit.partition_native([via, phantom])
        self.assertEqual(len(graph['groups']), 1)
        self.assertFalse(graph['memberships']['via'].intersection(graph['memberships']['phantom']))
        self.assertTrue(graph['shapes']['phantom']['F.Cu'].is_empty)

    def test_other_net_drill_removes_copper_before_connectivity(self):
        via = via_record()
        via['net'] = 'FOREIGN_NET'
        a = track_record('a', (-.2, 0), (.2, 0))
        b = track_record('b', (0, -.2), (0, .2))
        holes = audit.hole_map([via], ['F.Cu', 'B.Cu'])
        graph = audit.partition_native([a, b], global_holes=holes)
        self.assertEqual(graph['groups'], [])

    def test_inherited_limitation_is_not_labeled_new_regression(self):
        self.assertEqual(audit.group_disposition(False, False), 'inherited_positive_area_limitation_still_unresolved')
        self.assertEqual(audit.group_disposition(True, False), 'new_positive_area_connectivity_regression')
        self.assertEqual(audit.group_disposition(False, True), 'restored_positive_area_connectivity')

    def test_vertical_edges_require_declared_barrel_layer(self):
        full = audit.partition_native([via_record(layers=('F.Cu', 'B.Cu'))])
        missing = audit.partition_native([via_record(layers=('F.Cu',))])
        self.assertEqual(len(full['groups']), 1)
        self.assertEqual(len(missing['groups']), 2)

    def test_unplated_hole_is_not_a_vertical_edge(self):
        via = via_record()
        via['plated'] = False
        self.assertEqual(len(audit.partition_native([via])['groups']), 2)

    def test_disconnected_plated_island_is_not_implicitly_bonded(self):
        via = via_record()
        via['copper']['F.Cu'] += exported(box(4, 4, 5, 5))
        graph = audit.partition_native([via])
        self.assertEqual(len(graph['groups']), 2)

    def test_full_width_witness_distinguishes_narrow_contact(self):
        track = track_record('track', (-1, 0), (1, 0))
        own = audit.conductive_shapes(track)[0]['F.Cu']
        good = audit.full_width_witness(track, own, box(-.5, -.2, .5, .2), 'F.Cu', .00001)
        narrow = audit.full_width_witness(track, own, box(-.5, -.05, .5, .05), 'F.Cu', .00001)
        self.assertTrue(good['passed'])
        self.assertFalse(narrow['passed'])
        self.assertAlmostEqual(narrow['native_contiguous_covered_width_mm'], .1)

    def test_line_tangent_does_not_pass_even_with_long_intersection(self):
        track = track_record('track', (-1, 0), (1, 0))
        own = audit.conductive_shapes(track)[0]['F.Cu']
        touching = box(-.5, .1, .5, .3)
        witness = audit.full_width_witness(track, own, touching, 'F.Cu', .00001)
        self.assertFalse(witness['passed'])

    def test_drill_subtracted_annular_section_can_pass(self):
        track = track_record('track', (0, 0), (2, 0))
        graph = audit.partition_native([track, via_record()])
        witnesses = audit.boundary_witnesses([track, via_record()], graph, {'track'}, .00001)
        self.assertEqual(len(witnesses), 1)
        self.assertTrue(witnesses[0]['passed'])
        self.assertTrue(witnesses[0]['drill_subtraction_applied'])
        self.assertGreater(witnesses[0]['witnesses'][0]['point'][0], .5)

    def test_contiguous_width_required_not_sum_of_disjoint_spans(self):
        track = track_record('track', (-1, 0), (1, 0))
        own = audit.conductive_shapes(track)[0]['F.Cu']
        peer = box(-.5, -.1, .5, -.001).union(box(-.5, .001, .5, .1))
        witness = audit.full_width_witness(track, own, peer, 'F.Cu', .00001, at_endpoint=[0, 0])
        self.assertFalse(witness['passed'])

    def test_full_annulus_to_plane_is_supported(self):
        via = via_record()
        plane = object_record('plane', box(-2, -2, 2, 2), kind='saved_native_zone')
        graph = audit.partition_native([via, plane])
        rows = audit.boundary_witnesses([via, plane], graph, {'via'}, .00001)
        self.assertTrue(rows[0]['passed'])
        self.assertTrue(rows[0]['full_annular_witnesses'][0]['passed'])

    def test_partial_bare_annular_contact_fails_missing_evidence(self):
        via = via_record()
        pad = object_record('pad', box(.7, -.2, 2, .2))
        graph = audit.partition_native([via, pad])
        rows = audit.boundary_witnesses([via, pad], graph, {'via'}, .00001)
        self.assertFalse(rows[0]['passed'])
        self.assertIsNotNone(rows[0]['missing_evidence_reason'])

    def test_invalid_native_polygon_is_not_repaired(self):
        with self.assertRaisesRegex(ValueError, 'Invalid/degenerate'):
            audit.native_polygons([{'outer': [[0, 0], [1, 1], [0, 1], [1, 0]], 'holes': []}])

    def test_actual_pad_cut_prevents_bonding_through_removed_region(self):
        left = object_record('left', box(-2, -.2, .2, .2))
        right = object_record('right', box(-.2, -.2, 2, .2))
        self.assertEqual(len(audit.partition_native([left, right])['groups']), 1)
        cut = {'F.Cu': box(-.3, -.3, .3, .3)}
        self.assertEqual(len(audit.partition_native([left, right], subtract_region=cut)['groups']), 2)

    def test_actual_polyline_endpoints_require_full_width_support(self):
        track = track_record('new', (0, 0), (2, 0))
        start = object_record('source', box(-.2, -.2, .2, .2))
        narrow_target = object_record('target', box(1.8, -.04, 2.2, .04))
        records = [track, start, narrow_target]
        plan = {'added_copper': [{'kind': 'track', 'name': 'route', 'net': 'TEST_NET',
                                 'layer': 'F.Cu', 'points': [[0, 0], [2, 0]], 'width': .2}]}
        proof = {'recipe_to_native_UUIDs': [{'name': 'route', 'segment_index': 0, 'uuid': 'new'}]}
        rows = audit.endpoint_witnesses(plan, proof, records, audit.partition_native(records), .00001)
        self.assertTrue(rows[0]['passed'])
        self.assertFalse(rows[1]['passed'])

    def test_rounded_end_only_contact_is_not_full_width_entry(self):
        track = track_record('track', (0, 0), (2, 0))
        own = audit.conductive_shapes(track)[0]['F.Cu']
        pad = box(2.05, -.3, 2.5, .3)
        self.assertGreater(own.intersection(pad).area, 0)
        self.assertFalse(audit.full_width_witness(track, own, pad, 'F.Cu', .00001)['passed'])


class ChangedContactAttribution(unittest.TestCase):
    def compare(self, source, final, changed):
        return audit.compare_contact_findings(final, audit.partition_native(final), source,
                                              audit.partition_native(source), changed, .00001)

    def test_narrow_new_branch_joins_unchanged_wide_primary(self):
        primary = track_record('primary', (-2, 0), (2, 0), .254)
        branch = track_record('branch', (0, 1), (0, 0), .18)
        graph = audit.partition_native([primary, branch])
        raw = audit.boundary_witnesses([primary, branch], graph, set(graph['shapes']), .00001)
        self.assertFalse(raw[0]['passed'])  # Reproduces the v1 all-moving false rejection.
        old, changed, inherited = self.compare([primary], [primary, branch], {'branch'})
        self.assertEqual(old, [])
        self.assertEqual(inherited, [])
        self.assertEqual(len(changed), 1)
        self.assertTrue(changed[0]['passed'])
        self.assertEqual(changed[0]['moving_track_UUIDs'], ['branch'])
        self.assertEqual([r['track_uuid'] for r in changed[0]['witnesses']], ['branch'])
        proof = changed[0]['unchanged_primary_continuity_witnesses'][0]
        self.assertTrue(proof['passed'])
        self.assertTrue(proof['exact_native_record_unchanged'])
        self.assertTrue(proof['all_layer_conductive_geometry_unchanged'])
        self.assertEqual(proof['source_record_sha256'], proof['final_record_sha256'])
        self.assertEqual(proof['uncovered_strip_area_mm2'], 0)

    def test_narrow_serial_replacement_at_wide_primary_endpoint_fails(self):
        primary = track_record('primary', (-2, 0), (0, 0), .254)
        removed = track_record('removed', (0, 0), (2, 0), .254)
        replacement = track_record('new', (0, 0), (2, 0), .18)
        old, changed, inherited = self.compare([primary, removed], [primary, replacement], {'new'})
        self.assertTrue(old[0]['passed'])
        self.assertFalse(changed[0]['passed'])
        self.assertEqual(inherited, [])
        self.assertEqual({r['track_uuid'] for r in changed[0]['witnesses']}, {'primary', 'new'})
        self.assertFalse(changed[0]['unchanged_primary_continuity_witnesses'][0]['passed'])

    def test_changed_wider_primary_retains_its_width_obligation(self):
        primary = track_record('primary', (-2, 0), (2, 0), .254)
        branch = track_record('branch', (0, 1), (0, 0), .18)
        _, changed, _ = self.compare([primary], [primary, branch], {'primary', 'branch'})
        self.assertFalse(changed[0]['passed'])
        self.assertEqual(changed[0]['moving_track_UUIDs'], ['branch', 'primary'])
        self.assertEqual(changed[0]['unchanged_primary_continuity_witnesses'], [])

    def test_missing_source_primary_evidence_does_not_waive_width(self):
        primary = track_record('primary', (-2, 0), (2, 0), .254)
        branch = track_record('branch', (0, 1), (0, 0), .18)
        _, changed, _ = self.compare([], [primary, branch], {'branch'})
        self.assertFalse(changed[0]['passed'])
        self.assertFalse(changed[0]['unchanged_primary_continuity_witnesses'][0]['exact_native_record_unchanged'])

    def test_source_geometry_change_does_not_waive_width(self):
        primary = track_record('primary', (-2, 0), (2, 0), .254)
        branch = track_record('branch', (0, 1), (0, 0), .18)
        original = audit.partition_native([primary])
        graph = audit.partition_native([primary, branch])
        graph['shapes']['primary']['F.Cu'] = graph['shapes']['primary']['F.Cu'].difference(box(-.5, -.2, -.3, .2))
        rows = audit.boundary_witnesses([primary, branch], graph, set(graph['shapes']), .00001,
                                       moving_ids={'branch'}, source_records=[primary], source_partition=original)
        self.assertFalse(rows[0]['passed'])
        proof = rows[0]['unchanged_primary_continuity_witnesses'][0]
        self.assertTrue(proof['exact_native_record_unchanged'])
        self.assertFalse(proof['all_layer_conductive_geometry_unchanged'])

    def test_unchanged_primary_with_local_width_loss_cannot_supply_exception(self):
        primary = track_record('primary', (-2, 0), (2, 0), .254)
        native = audit.native_polygons(primary['copper']['F.Cu'])
        primary['copper']['F.Cu'] = exported(native.difference(box(-.05, -.2, .05, -.06)))
        branch = track_record('branch', (0, 1), (0, 0), .18)
        _, changed, _ = self.compare([primary], [primary, branch], {'branch'})
        self.assertFalse(changed[0]['passed'])
        proof = changed[0]['unchanged_primary_continuity_witnesses'][0]
        self.assertTrue(proof['exact_native_record_unchanged'])
        self.assertTrue(proof['all_layer_conductive_geometry_unchanged'])
        self.assertGreater(proof['uncovered_strip_area_mm2'], 0)
        self.assertFalse(proof['passed'])

    def test_source_inherited_and_changed_findings_remain_separate(self):
        primary = track_record('primary', (-2, 0), (2, 0), .254)
        old_branch = track_record('old-branch', (1, 1), (1, 0), .18)
        new_branch = track_record('new-branch', (-1, 1), (-1, 0), .18)
        old, changed, inherited = self.compare([primary, old_branch], [primary, old_branch, new_branch], {'new-branch'})
        self.assertEqual(len(old), 1)
        self.assertFalse(old[0]['passed'])
        self.assertEqual(len(changed), 1)
        self.assertTrue(changed[0]['passed'])
        self.assertEqual(len(inherited), 1)
        self.assertTrue(inherited[0]['inherited_limitation_still_unresolved'])
        self.assertFalse(inherited[0]['source_native_finding']['passed'])
        self.assertFalse(inherited[0]['final_native_finding']['passed'])
        self.assertFalse(inherited[0]['treated_as_new_regression'])
        self.assertFalse(inherited[0]['waived'])


class OwnerPermission(unittest.TestCase):
    def test_expired_or_misbound_lease_cannot_authorize_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            request = Path(temp) / 'request.json'
            request.write_text('{"synthetic": true}\n')
            output, path = Path(temp) / 'out.json', Path(temp) / 'lease.json'
            now = dt.datetime.now(dt.timezone.utc)
            lease = {'schema': 'f722-native7-contact-audit-owner-lease/v1', 'active': True,
                     'owner': 'synthetic-test', 'lease_id': 'synthetic-only', 'stage': audit.STAGE,
                     'request_sha256': audit.imp.sha(request), 'validator_sha256': audit.imp.sha(audit.__file__),
                     'output_path': str(output), 'issued_utc': (now - dt.timedelta(seconds=30)).isoformat(),
                     'expires_utc': (now + dt.timedelta(seconds=30)).isoformat()}
            path.write_text(json.dumps(lease))
            audit.validate_lease(path, request, output)
            for key, value in [('active', False), ('stage', 'construct'), ('request_sha256', '0' * 64),
                               ('validator_sha256', '0' * 64), ('output_path', str(request)),
                               ('expires_utc', (now - dt.timedelta(seconds=1)).isoformat())]:
                bad = dict(lease)
                bad[key] = value
                path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):
                    audit.validate_lease(path, request, output)


class SidecarBindings(unittest.TestCase):
    def setUp(self):
        self.plan = {'source': {'synthetic': True}, 'added_copper': [
            {'name': 'rx', 'net': 'PORT_C_RX_EXT', 'logical_net': 'PORT_C_RX_EXT'},
            {'name': 'ordinary', 'net': 'FLASH_CS', 'logical_net': 'FLASH_CS'}]}
        self.proof = {'recipe_to_native_UUIDs': [{'name': 'rx', 'uuid': 'native-rx'},
                                                {'name': 'ordinary', 'uuid': 'native-ordinary'}]}
        self.sidecar = {'schema': 'f722-native7-protected-role-sidecar/v1', 'source': self.plan['source'],
                        'plan_sha256': 'a' * 64, 'recipes': [{'name': 'rx', 'net': 'PORT_C_RX_EXT',
                         'logical_net': 'PORT_C_RX_EXT', 'role': 'upstream'}]}

    def check(self, value):
        return audit.validate_role_sidecar(value, self.plan, 'a' * 64, self.proof)

    def test_exact_role_mapping(self):
        self.assertEqual(self.check(self.sidecar), {'native-rx': 'upstream'})

    def test_missing_duplicate_and_extra_roles_fail(self):
        for rows in ([], self.sidecar['recipes'] * 2,
                     self.sidecar['recipes'] + [{'name': 'extra', 'net': 'PORT_C_TX_EXT',
                                                'logical_net': 'PORT_C_TX_EXT', 'role': 'downstream'}]):
            bad = copy.deepcopy(self.sidecar)
            bad['recipes'] = rows
            with self.assertRaises(ValueError):
                self.check(bad)

    def test_bad_plan_hash_role_or_net_fails(self):
        for field, value in [('role', 'invented'), ('net', 'PORT_C_TX_EXT'), ('logical_net', 'PORT_C_RX_EXT::upstream')]:
            bad = copy.deepcopy(self.sidecar)
            bad['recipes'][0][field] = value
            with self.assertRaises(ValueError):
                self.check(bad)
        bad = copy.deepcopy(self.sidecar)
        bad['plan_sha256'] = 'b' * 64
        with self.assertRaises(ValueError):
            self.check(bad)


if __name__ == '__main__':
    unittest.main(verbosity=2)
