#!/usr/bin/env python3
"""Host-only narrow-delta controls. No pcbnew, shapely, graph, router or subprocess."""
import copy
import datetime as dt
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('io4v2', HERE / 'import_native7_u15_io4_v2.py')
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)


class ExactSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native, cls.logical, cls.hardware = v.g.source_inputs()
        cls.source, cls.preview, cls.raw = v.validated_source_plan(cls.native, cls.hardware)
        cls.plan = v.template_plan(cls.source)

    def test_exact_native11_scope(self):
        got = v.validate_plan(self.plan, self.native, self.logical, self.source, require_complete=False)
        self.assertEqual(set(got['removed']), v.EXACT_CUT_IDS)
        self.assertEqual(len(got['removed']), 11)
        self.assertEqual(self.source['preservation']['unchanged_pad_nets'], 554)

    def test_host_imports_no_native_or_geometry(self):
        self.assertNotIn('pcbnew', sys.modules)
        self.assertNotIn('shapely', sys.modules)
        self.assertNotIn('export_native_copper', sys.modules)

    def test_empty_template_not_constructible(self):
        with self.assertRaisesRegex(ValueError, 'Both RX branches'):
            v.validate_plan(self.plan, self.native, self.logical, self.source)

    def test_copper_scope_foreign_removal_rejected(self):
        plan = copy.deepcopy(self.plan)
        cut = next(o for o in self.native['objects'] if o['kind'] == 'track' and o['uuid'] not in v.EXACT_CUT_IDS)
        plan['removed_native_records'][0] = {'record': cut, 'full_record_sha256': v.g.record_sha(cut)}
        with self.assertRaisesRegex(ValueError, 'Exact eleven'):
            v.validate_plan(plan, self.native, self.logical, self.source, False)

    def test_legacy_68_cut_scope_rejected(self):
        plan = copy.deepcopy(self.plan); plan['cut_scope_sha256'] = '072f788ef6dd5f758033754a6ab7a0d8124e8a7b0a632ad1c1a94ea624221096'
        with self.assertRaisesRegex(ValueError, 'scope binding'):
            v.validate_plan(plan, self.native, self.logical, self.source, False)

    def test_record_contour_tamper_rejected(self):
        plan = copy.deepcopy(self.plan); plan['removed_native_records'][0]['record']['copper'] = {}
        with self.assertRaisesRegex(ValueError, 'Exact eleven'):
            v.validate_plan(plan, self.native, self.logical, self.source, False)

    def recipes(self):
        plan = copy.deepcopy(self.plan)
        for role, net in v.ROLES.items():
            recipe = {'kind': 'track', 'name': 'synthetic-' + role, 'net': net, 'logical_net': net,
                      'layer': 'F.Cu', 'points': [[1, 1], [1, 2]], 'width': .25 if role == 'ground' else .127}
            plan['added_copper'].append(recipe)
            plan['recipe_roles'].append({k: recipe[k] for k in ['name', 'net', 'logical_net']} | {'role': role})
        return plan

    def test_complete_roles_only_structurally_valid(self):
        result = v.validate_plan(self.recipes(), self.native, self.logical, self.source)
        self.assertEqual(result['segments'], 4)

    def test_missing_hold_role_rejected(self):
        plan = self.recipes(); plan['added_copper'].pop(); plan['recipe_roles'].pop()
        with self.assertRaisesRegex(ValueError, 'Both RX branches'):
            v.validate_plan(plan, self.native, self.logical, self.source)

    def test_RX_role_cannot_assign_TX(self):
        plan = self.recipes(); plan['added_copper'][0]['net'] = 'PORT_C_TX_EXT'
        plan['added_copper'][0]['logical_net'] = 'PORT_C_TX_EXT'
        plan['recipe_roles'][0]['net'] = 'PORT_C_TX_EXT'; plan['recipe_roles'][0]['logical_net'] = 'PORT_C_TX_EXT'
        with self.assertRaisesRegex(ValueError, 'role/net scope'):
            v.validate_plan(plan, self.native, self.logical, self.source)

    def test_ground_narrowing_rejected(self):
        plan = self.recipes(); plan['added_copper'][2]['width'] = .127
        with self.assertRaisesRegex(ValueError, 'GND at source'):
            v.validate_plan(plan, self.native, self.logical, self.source)

    def test_plane_track_rejected(self):
        plan = self.recipes(); plan['added_copper'][0]['layer'] = 'In1.Cu'
        with self.assertRaisesRegex(ValueError, 'ordinary layers'):
            v.validate_plan(plan, self.native, self.logical, self.source)

    def test_offgrid_recipe_rejected(self):
        plan = self.recipes(); plan['added_copper'][0]['points'][0][0] = 1.0000001
        with self.assertRaisesRegex(ValueError, 'native grid'):
            v.validate_plan(plan, self.native, self.logical, self.source)

    def test_unknown_field_rejected(self):
        plan = self.recipes(); plan['poses'] = {'C12': [2, 3]}
        with self.assertRaisesRegex(ValueError, 'Unexpected/missing'):
            v.validate_plan(plan, self.native, self.logical, self.source)

    def test_contracts_change_only_RX_check(self):
        contracts = v.bound_contracts(self.source, 'a' * 64, 'b' * 64, 'c' * 64, 'd' * 64)
        for template in self.source['contract_templates']:
            contract = contracts[template['kind']]; checks = copy.deepcopy(contract['checks'])
            self.assertEqual(next(c for c in checks if c['id'] == 'published-06')['clamp'], 'U15.5')
            next(c for c in checks if c['id'] == 'published-06')['clamp'] = 'U15.1'
            self.assertEqual(checks, v.read(v.ROOT / template['source_path'])['checks'])
            self.assertEqual(contract['U15_actual_clamps']['PORT_C_TX_EXT'], 'U15.2')
            self.assertFalse(contract['package_internal_NC_conduction'])

    def test_schematic_recipe_exact_and_canonical_names(self):
        v.p.verify_metadata_preview(self.raw, self.preview, v.g.parser_helper())
        delta = {r['key']: r['after_net'] for r in self.source['pad_net_delta']}
        self.assertEqual(delta['U15.10'], 'unconnected-(U15-NC10-Pad10)')
        self.assertEqual(delta['U15.5'], 'PORT_C_RX_EXT')
        self.assertEqual(len(self.source['schematic_operations']), 9)

    def test_exact_four_net_syntax_prediction(self):
        syntax = v.g.syntax_inventory(v.g.SOURCE / 'f722-heli.kicad_pcb', v.g.parser_helper())
        new = v.expected_board_syntax(syntax)
        self.assertEqual(new['routes'], syntax['routes'])
        self.assertEqual(new['all_ids'], syntax['all_ids'])
        v.verify_board_syntax(syntax, new, [], [])
        with self.assertRaisesRegex(ValueError, 'Undeclared non-route'):
            v.verify_board_syntax(syntax, syntax, [], [])


class SyntheticNative(unittest.TestCase):
    def pair(self):
        before = {'objects': [], 'zones': [], 'footprints': [{'uuid': 'fp', 'xy': [25.5, 17.6]}]}
        for key in ['edge_cuts', 'outline_with_npth', 'copper_layers', 'copper_layer_ids', 'board_thickness_mm',
                    'native_version', 'native_build', 'maximum_polygon_error_mm', 'copper_error_location', 'pad_cut_error_location']:
            before[key] = 'fixed-' + key
        names = {'1': v.p.RX, '10': v.p.RX, '5': v.RETIRED_NETS[0], '6': v.RETIRED_NETS[1]}
        for i, (pin, uid) in enumerate(v.p.PINS.items()):
            before['objects'].append({'kind': 'pad', 'uuid': uid, 'key': 'U15.' + pin, 'number': pin, 'ref': 'U15',
                                      'net': names[pin], 'net_code': 15 if pin in ['1', '10'] else 18 + i,
                                      'copper': {'F.Cu': ['fixed contour']}, 'xy': [1, i]})
        before['objects'].append({'uuid': 'retained', 'kind': 'track', 'net': 'GND', 'net_code': 1, 'copper': {'F.Cu': ['ground contour']}})
        after = copy.deepcopy(before)
        codes = {v.p.RX: 101, v.NEW_NETS[0]: 102, v.NEW_NETS[1]: 103, 'GND': 104}
        for row in after['objects']:
            if row['kind'] == 'pad': row['net'] = v.p.PIN_NETS[row['number']]
            row['net_code'] = codes[row['net']]
        validation = {'old': v.g.unique(before['objects']), 'removed': {}}
        return before, after, validation

    def test_bijective_numeric_remap_only_accepted(self):
        a, b, check = self.pair(); now, fills, parity = v.verify_native(a, b, check, [])
        self.assertEqual(len(now), 5); self.assertEqual(fills, [])
        self.assertEqual(parity['net_codes_by_name']['GND'], 104)

    def test_undeclared_retained_copper_mutation_fails(self):
        a, b, check = self.pair(); b['objects'][-1]['copper']['F.Cu'] = ['shifted']
        with self.assertRaisesRegex(ValueError, 'Undeclared full native'):
            v.verify_native(a, b, check, [])

    def test_any_pad_geometry_mutation_fails(self):
        a, b, check = self.pair(); b['objects'][0]['xy'][0] += .01
        with self.assertRaisesRegex(ValueError, 'pad geometry'):
            v.verify_native(a, b, check, [])

    def test_numeric_alias_fails(self):
        a, b, check = self.pair(); b['objects'][-1]['net_code'] = 101
        with self.assertRaisesRegex(ValueError, 'aliases'):
            v.verify_native(a, b, check, [])

    def test_footprint_pose_mutation_fails(self):
        a, b, check = self.pair(); b['footprints'][0]['xy'][0] += .25
        with self.assertRaisesRegex(ValueError, 'poses fixed'):
            v.verify_native(a, b, check, [])

    def test_extra_native_copper_fails(self):
        a, b, check = self.pair(); b['objects'].append(dict(b['objects'][-1], uuid='rogue'))
        with self.assertRaisesRegex(ValueError, 'Native additions differ'):
            v.verify_native(a, b, check, [])


class Lease(unittest.TestCase):
    def test_failed_scope_blocks_before_any_native_or_output_use(self):
        self.assertFalse(v.NATIVE_EXECUTION_ENABLED)
        with self.assertRaisesRegex(ValueError, 'failed joint barrel capacity'):
            v.construct(None, None, None, None, None, None, None, None, None)

    def test_inactive_template_cannot_authorize_native(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = Path(directory) / 'plan.json'; plan.write_text('{}')
            now = dt.datetime.now(dt.timezone.utc)
            lease = {'schema': v.LEASE_SCHEMA, 'active': False, 'owner': 'owner', 'lease_id': 'test',
                     'allowed_stages': [v.STAGE], 'source': v.SOURCE_BINDINGS, 'plan_sha256': v.sha(plan),
                     'importer_sha256': v.sha(v.__file__), 'paired_source_plan_sha256': v.sha(v.SOURCE_PLAN_PATH),
                     'cut_scope_sha256': v.CUT_SCOPE_SHA256, 'candidate_directory': directory,
                     'issued_utc': now.isoformat(), 'expires_utc': (now + dt.timedelta(minutes=10)).isoformat()}
            with self.assertRaisesRegex(ValueError, 'No active owner'):
                v.validate_lease(lease, plan, Path(directory), now)
            lease['active'] = True
            self.assertEqual(v.validate_lease(lease, plan, Path(directory), now), lease)
            expired = copy.deepcopy(lease); expired['expires_utc'] = now.isoformat()
            with self.assertRaisesRegex(ValueError, 'Lease expired'):
                v.validate_lease(expired, plan, Path(directory), now)
            bad_scope = copy.deepcopy(lease); bad_scope['cut_scope_sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'scope mismatch'):
                v.validate_lease(bad_scope, plan, Path(directory), now)
            bad_plan = copy.deepcopy(lease); bad_plan['plan_sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'source/plan mismatch'):
                v.validate_lease(bad_plan, plan, Path(directory), now)
            lease['allowed_stages'] = ['incremental_construct_refill_export']
            with self.assertRaisesRegex(ValueError, 'only bounded IO4'):
                v.validate_lease(lease, plan, Path(directory), now)


if __name__ == '__main__': unittest.main()
