"""Host identity checks and tiny fabricated translation tests; no native/geometry job."""
import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import import_native7_c12_translation_v1 as imp


class SourceBoundPlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native, cls.logical, _ = imp.source_inputs()
        cls.scope = imp.bound_scope(cls.native)
        old = imp.unique(cls.native['objects'])
        recipes = [{'kind': 'track', 'name': row['name'] + '-synthetic-host-example',
                    'net': row['net'], 'logical_net': row['net'], 'layer': 'F.Cu',
                    'points': [t['xy'] for t in row['terminals']], 'width': row['minimum_track_width_mm']}
                   for row in cls.scope['restoration_obligations']]
        recipes += copy.deepcopy(cls.scope['required_common_ground_recipes'])
        cls.plan = {'schema': imp.PLAN_SCHEMA, 'source': imp.SOURCE_BINDINGS, 'scope_contract_sha256': imp.SCOPE_SHA,
                    'declared_footprint_transforms': [cls.scope['declared_footprint_transform']],
                    'removed_native_records': [{'record': old[r['uuid']], 'full_record_sha256': r['full_record_sha256']}
                                               for r in cls.scope['expected_removed_record_hashes']],
                    'added_copper': recipes,
                    'obligation_recipe_bindings': [{'name': row['name'], 'recipe_names': [recipe['name']]}
                                                  for row, recipe in zip(cls.scope['restoration_obligations'], recipes)]}

    def check(self, plan):
        return imp.validate_plan(plan, self.native, self.logical)

    def test_exact_scope_accepts_host_recipe_declarations_without_native_import(self):
        import sys
        result = self.check(self.plan)
        self.assertEqual(len(result['removed']), 94)
        self.assertEqual(imp.record_sha(sorted(result['removed'])), '66347d7681b00ac148cc7e63f26d9617b6635c1429f20fe2b573b6c09ac81cb4')
        self.assertNotIn('pcbnew', sys.modules)
        self.assertNotIn('shapely', sys.modules)

    def test_same_count_foreign_cut_cannot_substitute_for_declared_record(self):
        plan = copy.deepcopy(self.plan)
        old = imp.unique(self.native['objects'])
        uid = next(iter(imp.KEEP))
        plan['removed_native_records'][0] = {'record': old[uid], 'full_record_sha256': imp.record_sha(old[uid])}
        with self.assertRaisesRegex(ValueError, 'exact coordinated'):
            self.check(plan)

    def test_missing_cut_is_rejected(self):
        plan = copy.deepcopy(self.plan); plan['removed_native_records'].pop()
        with self.assertRaisesRegex(ValueError, 'exact coordinated'):
            self.check(plan)

    def test_modified_full_removal_record_is_rejected(self):
        plan = copy.deepcopy(self.plan); plan['removed_native_records'][0]['record']['width'] = .3
        with self.assertRaisesRegex(ValueError, 'full-record'):
            self.check(plan)

    def test_wrong_or_extra_pose_rejected(self):
        for field, value in [('after', [26.4, 12, -90, 'F.Cu']), ('footprint_uuid', 'other')]:
            plan = copy.deepcopy(self.plan);plan['declared_footprint_transforms'][0][field] = value
            with self.assertRaisesRegex(ValueError, 'pose'):
                self.check(plan)
        plan = copy.deepcopy(self.plan);plan['declared_footprint_transforms'] *= 2
        with self.assertRaisesRegex(ValueError, 'pose'):
            self.check(plan)

    def test_scope_hash_cannot_be_swapped(self):
        plan = copy.deepcopy(self.plan); plan['scope_contract_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'scope'):
            self.check(plan)

    def test_missing_obligation_fails(self):
        plan = copy.deepcopy(self.plan);plan['obligation_recipe_bindings'].pop()
        with self.assertRaisesRegex(ValueError, 'restoration recipe bindings'):
            self.check(plan)

    def test_supply_width_and_wrong_net_fail(self):
        for field, value in [('width', .127), ('net', 'GND')]:
            plan = copy.deepcopy(self.plan);plan['added_copper'][0][field] = value
            if field == 'net':plan['added_copper'][0]['logical_net'] = value
            with self.assertRaises(ValueError):
                self.check(plan)

    def test_disconnected_declared_branch_fails(self):
        plan = copy.deepcopy(self.plan);plan['added_copper'][0]['points'][-1] = [26.4, 11.52]
        with self.assertRaisesRegex(ValueError, 'Disconnected or incomplete'):
            self.check(plan)

    def test_extra_power_recipe_cannot_escape_obligations(self):
        plan = copy.deepcopy(self.plan);extra = copy.deepcopy(plan['added_copper'][0]);extra['name'] = 'unassigned';plan['added_copper'].append(extra)
        with self.assertRaisesRegex(ValueError, 'Unassigned'):
            self.check(plan)

    def test_declared_source_terminal_group_is_complete(self):
        ids = self.scope['additional_terminal_groups'][0]['all_original_pad_UUIDs']
        self.assertEqual(len(ids), 7)
        self.assertEqual(set(ids), {r['uuid'] for r in self.native['objects'] if r['kind'] == 'pad' and r['net'] == '+3V3_IMU'})

    def test_exact_common_point18_ground_is_separate_from_c12_point20_return(self):
        assigned = {name for r in self.plan['obligation_recipe_bindings'] for name in r['recipe_names']}
        power_names = {r['name'] for r in self.plan['added_copper'] if r['net'] in ('GND', '+3V3_IMU')}
        self.assertFalse(power_names <= assigned)  # Preserves the original erroneous catch-all result.
        self.assertEqual(power_names - assigned, {'recovered-U2-9-ground-0', 'recovered-U2-9-ground-1'})
        self.assertEqual([r['width'] for r in self.plan['added_copper'] if r['name'] in power_names - assigned], [.18, .18])
        self.check(self.plan)

    def test_common_ground_cannot_be_changed_or_omitted(self):
        for change in ('omit', 'narrow', 'move'):
            plan = copy.deepcopy(self.plan)
            if change == 'omit':plan['added_copper'].pop()
            elif change == 'narrow':plan['added_copper'][-1]['width'] = .127
            else:plan['added_copper'][-1]['points'][-1] = [24.5, 9.85]
            with self.assertRaisesRegex(ValueError, 'exact common U2.9'):
                self.check(plan)


class SyntheticNativePrediction(unittest.TestCase):
    def fixture(self):
        polygon = {'outer': [[0, 0], [.000001, 0], [.000001, .000001]], 'holes': []}
        pads = [{'uuid': uid, 'kind': 'pad', 'footprint_uuid': imp.C12_UUID, 'drill': None,
                 'xy': [0, 1], 'angle': 270, 'net': 'PRESERVED_NET', 'size': [.56, .62],
                 'offset': [0, 0], 'copper': {'F.Cu': [copy.deepcopy(polygon)]},
                 'inside': {'F.Cu': [copy.deepcopy(polygon)]},
                 'mask': {'F.Mask': {'expansion': .05, 'polygons': [copy.deepcopy(polygon)]}}}
                for uid in sorted(imp.PAD_IDS)]
        return {'objects': pads + [{'uuid': 'retained', 'kind': 'track', 'arbitrary_identity': 9}],
                'footprints': [{'uuid': imp.C12_UUID, 'xy': [0, 0], 'angle': -90,
                               'graphics': [{'start': [0, 0], 'end': [1, 0], 'width': .12}]},
                              {'uuid': 'other', 'xy': [2, 2]}], 'zones': [{'unchanged': True}]}

    def test_exact_integer_translation_preserves_shapes_and_identities(self):
        before = self.fixture(); original = copy.deepcopy(before); after = imp.predict_translation(before)
        self.assertEqual(before, original)
        self.assertEqual(after['objects'][0]['xy'], [.25, 1])
        self.assertEqual(after['objects'][0]['copper']['F.Cu'][0]['outer'][1], [.250001, 0])
        self.assertEqual(after['objects'][0]['inside']['F.Cu'][0]['outer'][1], [.250001, 0])
        self.assertEqual(after['objects'][0]['mask']['F.Mask']['polygons'][0]['outer'][1], [.250001, 0])
        self.assertEqual(after['objects'][0]['angle'], 270)
        self.assertEqual(after['objects'][0]['offset'], [0, 0])
        self.assertEqual(after['footprints'][0]['angle'], -90)
        self.assertEqual(after['footprints'][0]['graphics'][0]['end'], [1.25, 0])
        self.assertEqual(after['objects'][2], before['objects'][2])
        self.assertEqual(after['footprints'][1], before['footprints'][1])
        self.assertEqual(after['zones'], before['zones'])

    def test_drilled_pad_cannot_use_c12_translation(self):
        before = self.fixture();before['objects'][0]['drill'] = {'invented': True}
        with self.assertRaisesRegex(ValueError, 'undrilled'):
            imp.predict_translation(before)

    def test_off_grid_coordinate_not_silently_rounded(self):
        before = self.fixture();before['objects'][0]['xy'] = [.0000001, 0]
        with self.assertRaisesRegex(ValueError, 'off the exact'):
            imp.predict_translation(before)

    def test_native_full_record_comparison_rejects_extra_change(self):
        before = self.fixture();after = imp.predict_translation(before)
        # Exercise the strict inherited primitive on tiny complete native envelopes.
        keys = ('edge_cuts','outline_with_npth','copper_layers','copper_layer_ids','board_thickness_mm',
                'native_version','native_build','maximum_polygon_error_mm','copper_error_location','pad_cut_error_location')
        expected = imp.predict_translation(before)
        for row in (after, expected):
            row['zones'] = []
            row.update({key: [] for key in keys})
        validation = {'old': imp.unique(expected['objects']), 'removed': {}}
        imp.base.verify_native(expected, after, validation, [])
        after['objects'][2]['arbitrary_identity'] = 10
        with self.assertRaisesRegex(ValueError, 'Undeclared full native'):
            imp.base.verify_native(expected, after, validation, [])


class OriginalNonposeSyntax(unittest.TestCase):
    def board(self, x=26.0625, clearance=0, other_x=1, fill_x=1):
        return f"""(kicad_pcb (version 1) (setup (pad_to_mask_clearance {clearance}))
          (footprint "C" (at {x} 12 -90) (uuid {imp.C12_UUID}))
          (footprint "OTHER" (at {other_x} 1) (uuid other-footprint))
          (segment (start 0 0) (end 1 0) (width .127) (uuid route))
          (zone (uuid zone) (polygon (pts (xy 0 0) (xy 2 0) (xy 2 2)))
            (filled_polygon (pts (xy 0 0) (xy {fill_x} 0) (xy 1 1)))))"""

    def files(self, folder, prediction):
        source, predicted = Path(folder)/'source.pcb', Path(folder)/'prediction.pcb'
        source.write_text(self.board());predicted.write_text(prediction)
        return source,predicted

    def test_only_c12_translation_and_existing_fill_payload_exclusions_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            source,predicted=self.files(folder,self.board(x=26.3125,fill_x=1.5))
            imp.verify_original_nonpose_syntax(source,predicted,imp.parser_helper())

    def test_shared_save_time_board_setting_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source,predicted=self.files(folder,self.board(x=26.3125,clearance=.05))
            candidate=Path(folder)/'candidate.pcb';candidate.write_text(predicted.read_text())
            h=imp.parser_helper()
            old,pred,final=[imp.syntax_inventory(p,h) for p in (source,predicted,candidate)]
            # Both predicates of the old prediction/final check still pass.
            self.assertEqual(old['routes'],pred['routes'])
            self.assertEqual(old['all_ids'],pred['all_ids'])
            self.assertEqual(pred['structures'],final['structures'])
            with self.assertRaisesRegex(ValueError,'original non-C12 board syntax'):
                imp.verify_original_nonpose_syntax(source,predicted,h)

    def test_other_footprint_change_is_not_hidden_by_c12_exclusion(self):
        with tempfile.TemporaryDirectory() as folder:
            source,predicted=self.files(folder,self.board(x=26.3125,other_x=1.25))
            with self.assertRaisesRegex(ValueError,'original non-C12 board syntax'):
                imp.verify_original_nonpose_syntax(source,predicted,imp.parser_helper())


class LeaseBindings(unittest.TestCase):
    def test_old_importer_lease_or_wrong_scope_cannot_authorize_successor(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = Path(folder) / 'plan.json';plan.write_text('{}\n');output = Path(folder) / 'candidate'
            now = dt.datetime.now(dt.timezone.utc)
            lease = {'schema': imp.LEASE_SCHEMA, 'active': True, 'owner': 'synthetic', 'lease_id': 'synthetic',
                     'allowed_stages': [imp.STAGE], 'source': imp.SOURCE_BINDINGS,
                     'scope_contract_sha256': imp.SCOPE_SHA, 'plan_sha256': imp.sha(plan),
                     'importer_sha256': imp.sha(imp.__file__), 'candidate_directory': str(output),
                     'issued_utc': (now-dt.timedelta(seconds=1)).isoformat(),
                     'expires_utc': (now+dt.timedelta(seconds=30)).isoformat()}
            imp.validate_lease(lease,plan,output)
            for key,value in [('schema',imp.base.LEASE_SCHEMA),('scope_contract_sha256','0'*64),
                              ('importer_sha256',imp.BASE_SHA),('active',False)]:
                bad=copy.deepcopy(lease);bad[key]=value
                with self.assertRaises(ValueError):imp.validate_lease(bad,plan,output)


if __name__ == '__main__':
    unittest.main(verbosity=2)
