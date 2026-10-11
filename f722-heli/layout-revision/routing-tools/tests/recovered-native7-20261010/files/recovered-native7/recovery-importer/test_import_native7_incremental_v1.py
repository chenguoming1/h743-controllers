"""Host-only boundary tests; no pcbnew import, candidate writes, or native jobs."""
import copy
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import import_native7_incremental_v1 as imp


class ImportBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native, cls.logical, cls.hardware = imp.source_inputs()
        cls.old = imp.unique(cls.native['objects'])
        cls.track = next(o for o in cls.old.values() if o['kind'] == 'track' and
                         set(o['width_by_layer']) <= set(imp.LAYERS))
        cls.pad = next(o for o in cls.old.values() if o['kind'] == 'pad')
        cls.base = {'schema': imp.PLAN_SCHEMA, 'source': dict(imp.SOURCE_BINDINGS),
                    'removed_native_records': [], 'added_copper': []}
        cls.recipe = {'kind': 'track', 'name': 'host-test-only', 'net': 'FLASH_HOLD_N',
                      'logical_net': 'FLASH_HOLD_N', 'layer': 'F.Cu',
                      'points': [[1.000001, 2], [3, 4], [5, 4]], 'width': .127}

    def validate(self, plan):
        return imp.validate_plan(plan, self.native, self.logical)

    def plan_with(self, recipe=None):
        plan = copy.deepcopy(self.base)
        if recipe is not None:
            plan['added_copper'] = [copy.deepcopy(recipe)]
        return plan

    def removal(self, record):
        return {'record': copy.deepcopy(record), 'full_record_sha256': imp.record_sha(record)}

    def test_exact_source_and_empty_plan(self):
        self.assertEqual(len(self.hardware), 61)
        self.assertNotIn('f722-heli.kicad_prl', self.hardware)
        self.assertNotIn('f722-heli.native.json', self.hardware)
        self.assertEqual(self.validate(self.base)['segments'], 0)
        self.assertNotIn('pcbnew', sys.modules)

    def test_full_polyline_count_and_source_record(self):
        plan = self.plan_with(self.recipe)
        plan['removed_native_records'] = [self.removal(self.track)]
        result = self.validate(plan)
        self.assertEqual(result['segments'], 2)
        self.assertEqual(set(result['removed']), {self.track['uuid']})

    def test_all_source_hashes_bound(self):
        for key in imp.SOURCE_BINDINGS:
            with self.subTest(key=key):
                plan = self.plan_with()
                plan['source'][key] = '0' * 64
                with self.assertRaisesRegex(ValueError, 'source/schema'):
                    self.validate(plan)

    def test_hash_does_not_authorize_changed_record(self):
        row = self.removal(self.track)
        row['record']['net_code'] += 1
        row['full_record_sha256'] = imp.record_sha(row['record'])
        plan = self.plan_with()
        plan['removed_native_records'] = [row]
        with self.assertRaisesRegex(ValueError, 'full-record'):
            self.validate(plan)

    def test_record_does_not_authorize_wrong_hash(self):
        row = self.removal(self.track)
        row['full_record_sha256'] = '0' * 64
        plan = self.plan_with()
        plan['removed_native_records'] = [row]
        with self.assertRaisesRegex(ValueError, 'full-record'):
            self.validate(plan)

    def test_foreign_duplicate_and_pad_removals_rejected(self):
        for kind in ('foreign', 'duplicate', 'pad'):
            with self.subTest(kind=kind):
                row = self.removal(self.pad if kind == 'pad' else self.track)
                if kind == 'foreign':
                    row['record']['uuid'] = '00000000-0000-4000-8000-000000000000'
                plan = self.plan_with()
                plan['removed_native_records'] = [row, row] if kind == 'duplicate' else [row]
                with self.assertRaises(ValueError):
                    self.validate(plan)

    def test_pose_netmap_and_unexpected_fields_rejected(self):
        for key in ('poses', 'changed_pad_records', 'approved_pad_net_changes', 'process', 'zone_changes'):
            with self.subTest(key=key):
                plan = self.plan_with()
                plan[key] = []
                with self.assertRaisesRegex(ValueError, 'fields'):
                    self.validate(plan)

    def test_unsafe_recipe_mutations_rejected(self):
        changes = [('layer', 'In1.Cu'), ('layer', 'In4.Cu'), ('layer', 'F.Mask'),
                   ('points', [[1, 2], [1, 2]]), ('points', [[1, 2]]),
                   ('points', [[True, 2], [3, 4]]), ('points', [[1.0000001, 2], [3, 4]]),
                   ('points', [[2148, 2], [3, 4]]), ('points', [[float('nan'), 2], [3, 4]]),
                   ('width', .126999), ('width', True), ('width', float('inf')),
                   ('net', 'invented-net'), ('net', ''), ('logical_net', 'FLASH_HOLD_N::invented'),
                   ('logical_net', 'FLASH_WP_N'), ('kind', 'arc')]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                recipe = copy.deepcopy(self.recipe)
                recipe[key] = value
                with self.assertRaises(ValueError):
                    self.validate(self.plan_with(recipe))

    def test_split_logical_identity_not_inferred(self):
        recipe = copy.deepcopy(self.recipe)
        recipe.update(net='ESC_MCU', logical_net='ESC_MCU')
        with self.assertRaisesRegex(ValueError, 'logical identity'):
            self.validate(self.plan_with(recipe))
        recipe['logical_net'] = 'ESC_MCU::P0'
        self.validate(self.plan_with(recipe))
        recipe.update(net='PORT_A_RX_EXT', logical_net='PORT_A_RX_EXT')
        self.validate(self.plan_with(recipe))  # Canonical name explicitly present in source map.

    def test_fixed_through_via_recipe(self):
        recipe = {'kind': 'via', 'name': 'via-host-test-only', 'net': 'FLASH_HOLD_N',
                  'logical_net': 'FLASH_HOLD_N', 'xy': [1, 2], 'diameter': .45, 'drill': .20,
                  'layers': self.native['copper_layers'], 'tented_front': True, 'tented_back': True}
        self.assertEqual(self.validate(self.plan_with(recipe))['vias'], 1)
        for key, value in [('diameter', .4), ('drill', .1), ('layers', ['F.Cu', 'B.Cu']),
                           ('tented_front', False), ('tented_back', 1)]:
            with self.subTest(key=key):
                altered = copy.deepcopy(recipe)
                altered[key] = value
                with self.assertRaises(ValueError):
                    self.validate(self.plan_with(altered))

    def test_duplicate_recipes_rejected(self):
        plan = self.plan_with(self.recipe)
        plan['added_copper'] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.validate(plan)

    def test_json_duplicates_and_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'invalid.json'
            for content in ('{"schema": 1, "schema": 2}', '{"width": NaN}', '{"width": Infinity}'):
                path.write_text(content)
                with self.assertRaises(ValueError):
                    imp.read(path)

    def test_unrelated_output_and_existing_output_rejected(self):
        for path in (imp.SOURCE, imp.HERE, imp.HERE / 'candidates/../elsewhere', Path('relative')):
            with self.subTest(path=path), self.assertRaises(ValueError):
                imp.validate_output(path)

    def test_lease_is_exact_bounded_and_current(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'plan.json'
            path.write_text(json.dumps(self.base))
            output = imp.HERE / 'candidates/host-validation-only'
            now = dt.datetime(2026, 10, 10, 0, 30, tzinfo=dt.timezone.utc)
            lease = {'schema': imp.LEASE_SCHEMA, 'active': True, 'owner': 'host-test', 'lease_id': 'host-test-only',
                     'allowed_stages': [imp.STAGE], 'source': imp.SOURCE_BINDINGS,
                     'plan_sha256': imp.sha(path), 'importer_sha256': imp.sha(imp.__file__),
                     'candidate_directory': str(output), 'issued_utc': '2026-10-10T00:00:00Z',
                     'expires_utc': '2026-10-10T01:00:00Z'}
            imp.validate_lease(lease, path, output, now=now)
            changes = [('active', False), ('owner', ''), ('allowed_stages', [imp.STAGE, 'drc']),
                       ('plan_sha256', '0' * 64), ('importer_sha256', '0' * 64),
                       ('candidate_directory', str(imp.SOURCE)), ('issued_utc', '2026-10-10T00:40:00Z'),
                       ('expires_utc', '2026-10-10T00:20:00Z'), ('expires_utc', '2026-10-10T03:00:00Z'),
                       ('expires_utc', '2026-10-10T01:00:00')]
            for key, value in changes:
                with self.subTest(key=key, value=value):
                    altered = copy.deepcopy(lease)
                    altered[key] = value
                    with self.assertRaises(ValueError):
                        imp.validate_lease(altered, path, output, now=now)

    def test_full_record_verification_catches_undeclared_change(self):
        validation = self.validate(self.base)
        imp.verify_native(self.native, self.native, validation, [])
        for field in ('net', 'net_code', 'width', 'copper'):
            with self.subTest(field=field):
                altered = dict(self.native)
                changed = dict(self.track)
                changed[field] = 'tampered'
                altered['objects'] = [changed if o['uuid'] == changed['uuid'] else o for o in self.native['objects']]
                with self.assertRaisesRegex(ValueError, 'Undeclared full native'):
                    imp.verify_native(self.native, altered, validation, [])

    def test_zone_fill_allowed_but_outline_rejected(self):
        validation = self.validate(self.base)
        altered = dict(self.native)
        altered['zones'] = copy.deepcopy(self.native['zones'])
        zone = next(z for z in altered['zones'] if not z['rule'])
        layer = next(iter(zone['filled']))
        zone['filled'][layer] = []
        _, changes = imp.verify_native(self.native, altered, validation, [])
        self.assertEqual(changes[0]['zone_uuid'], zone['uuid'])
        zone['outline'] = []
        with self.assertRaisesRegex(ValueError, 'Zone outline/settings'):
            imp.verify_native(self.native, altered, validation, [])

    def test_exact_new_contours_and_every_segment_required(self):
        expected = copy.deepcopy(self.track)
        expected['uuid'] = imp.native_uuid('a' * 64, 'full-native-shape-test', 0)
        recipe = {'kind': 'track', 'name': 'full-native-shape-test', 'net': expected['net'],
                  'logical_net': self.logical.get(self.track['uuid'], expected['net']),
                  'width': expected['width'], 'layer': next(iter(expected['width_by_layer'])),
                  'points': [expected['start'], expected['end']]}
        validation = self.validate(self.plan_with(recipe))
        additions = [{'uuid': expected['uuid'], 'recipe': recipe, 'segment_index': 0,
                      'expected_native_record': expected}]
        altered = dict(self.native)
        altered['objects'] = self.native['objects'] + [expected]
        imp.verify_native(self.native, altered, validation, additions)
        changed = copy.deepcopy(expected)
        changed['copper'][recipe['layer']] = []
        altered['objects'] = self.native['objects'] + [changed]
        with self.assertRaisesRegex(ValueError, 'Full new native geometry'):
            imp.verify_native(self.native, altered, validation, additions)
        with self.assertRaisesRegex(ValueError, 'Native additions'):
            imp.verify_native(self.native, self.native, validation, additions)

    def test_uuid_collision_with_any_board_identity_rejected(self):
        plan = self.plan_with(self.recipe)
        uid = imp.native_uuid('a' * 64, self.recipe['name'], 0)
        with self.assertRaisesRegex(ValueError, 'UUID collision'):
            imp.prepare_additions(plan, 'a' * 64, {'all_ids': {uid}})

    def test_native_entry_without_permission_fails_before_import_or_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'plan.json'
            path.write_text(json.dumps(self.base))
            output = imp.HERE / 'candidates/host-test-must-not-exist'
            self.assertFalse(output.exists())
            run = subprocess.run([sys.executable, imp.__file__, '--plan', str(path), '--output', str(output)],
                                 capture_output=True, text=True, timeout=30)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('explicit --lease', run.stderr)
            self.assertFalse(output.exists())

    def test_canonical_record_digest_and_uuid_repeatable(self):
        self.assertEqual(imp.record_sha({'b': 2, 'a': 1}), imp.record_sha({'a': 1, 'b': 2}))
        one = imp.native_uuid('a' * 64, 'route', 0)
        self.assertEqual(one, imp.native_uuid('a' * 64, 'route', 0))
        self.assertNotEqual(one, imp.native_uuid('a' * 64, 'route', 1))
        self.assertNotEqual(one, imp.native_uuid('b' * 64, 'route', 0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
