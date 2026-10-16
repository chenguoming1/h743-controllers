#!/usr/bin/env python3
"""Focused regression tests. All writes stay in the chosen test-work directory."""
import argparse
import copy
import json
import os
from pathlib import Path
import unittest
import tempfile

import pcbnew
import validate_nexus_reroute as v

BASE = Path(os.environ.get('NEXUS_REROUTE_TEST_BASE', str(Path(__file__).resolve().parent / 'validation-fixtures')))
WORK = Path(tempfile.mkdtemp(prefix='nexus-validator-test-'))


class ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = BASE / 'backups/main-before-rule-refill.kicad_pcb'
        cls.project = BASE / 'baseline/hardware/nexus-style-fc.kicad_pro'
        cls.drc = BASE / 'reports/main-baseline-native.json'
        cls.erc = BASE / 'reports/main-erc-libraries.json'
        cls.tree = v.parse_sexpr(cls.original.read_text())
        cls.board = pcbnew.LoadBoard(str(cls.original))

    def dump(self, name, data):
        p = WORK / name
        p.write_text(json.dumps(data))
        return p

    def test_01_exact_baseline(self):
        self.assertEqual(v.invariant_checks(self.board, self.board, self.tree, self.tree)['status'], 'pass')
        p = v.route_profile(self.board)
        self.assertEqual(len(p['subminimum_tracks']), 937)
        self.assertEqual(len(p['nonconforming_vias']), 0)
        self.assertEqual(p['totals']['segments'], 1450)
        self.assertEqual(p['totals']['vias'], 225)
        self.assertTrue(p['usb_profile'])
        for net in p['per_net'].values():
            self.assertAlmostEqual(sum(x['length_mm'] for x in net['width_profile'].values()), net['length_mm'], places=7)

    def test_02_native_exact_contact_count(self):
        contacts = v.drill_paste_contacts(self.board)
        self.assertEqual(v.contact_summary(contacts), {'contact_pairs': 19, 'unique_vias': 18, 'same_net_pairs': 19, 'different_net_pairs': 0})
        self.assertEqual(v.added_records(contacts, contacts), [])

    def test_03_native_footprint_move_caught(self):
        changed = pcbnew.LoadBoard(str(self.original))
        fp = next(iter(changed.GetFootprints()))
        pos = fp.GetPosition()
        fp.SetPosition(pcbnew.VECTOR2I(pos.x + 1, pos.y))
        check = v.invariant_checks(self.board, changed, self.tree, self.tree)
        self.assertEqual(check['checks']['footprint_and_pad_native_geometry']['status'], 'fail')

    def test_04_source_stack_outline_pad_changes_caught(self):
        for tag in ['setup', 'layers']:
            changed = copy.deepcopy(self.tree)
            v.children(changed, tag)[0].append(['test_changed', '1'])
            check = v.invariant_checks(self.board, self.board, self.tree, changed)
            self.assertEqual(check['checks'][tag]['status'], 'fail')
        changed = copy.deepcopy(self.tree)
        edge = next(n for n in changed if isinstance(n, list) and any(len(x) > 1 and v.atom(x[1]) == 'Edge.Cuts' for x in v.children(n, 'layer')))
        edge.append(['test_changed', '1'])
        self.assertEqual(v.invariant_checks(self.board, self.board, self.tree, changed)['checks']['outline']['status'], 'fail')
        changed = copy.deepcopy(self.tree)
        fp = v.children(changed, 'footprint')[0]
        v.children(fp, 'pad')[0].append(['test_changed', '1'])
        self.assertEqual(v.invariant_checks(self.board, self.board, self.tree, changed)['checks']['complete_footprint_definitions']['status'], 'fail')

    def test_05_subminimum_native_threshold(self):
        b = pcbnew.BOARD()
        for width in [127000, 126999]:
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(0, 0)); t.SetEnd(pcbnew.VECTOR2I(1000000, 0))
            t.SetWidth(width); t.SetLayer(pcbnew.F_Cu); b.Add(t)
        result = v.route_profile(b)
        self.assertEqual(len(result['subminimum_tracks']), 1)
        self.assertEqual(result['subminimum_tracks'][0]['width_mm'], .126999)

    def test_06_power_5v_reduction_fails(self):
        b = pcbnew.LoadBoard(str(self.original))
        t = next(x for x in b.GetTracks() if not isinstance(x, pcbnew.PCB_VIA) and x.GetNetname() == '5V')
        t.SetWidth(127000)
        result = v.power_width_preservation(self.board, b)
        self.assertEqual(result['per_net']['5V']['required_floor_mm'], .25)
        self.assertEqual(result['per_net']['5V']['status'], 'fail')
        self.assertEqual(result['per_net']['5V']['candidate_minimum_mm'], .127)

    def test_07_new_same_net_and_different_net_contact(self):
        b = pcbnew.LoadBoard(str(self.original))
        before = v.drill_paste_contacts(b)
        pad = next(p for fp in b.GetFootprints() for p in fp.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.IsOnLayer(pcbnew.F_Cu) and p.IsOnLayer(pcbnew.F_Paste) and p.GetNetCode())
        via = pcbnew.PCB_VIA(b)
        via.SetPosition(pad.GetPosition()); via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetViaType(pcbnew.VIATYPE_THROUGH); via.SetWidth(450000); via.SetDrill(200000)
        via.SetNetCode(pad.GetNetCode()); b.Add(via)
        after = v.drill_paste_contacts(b)
        added = v.added_records(before, after)
        self.assertTrue(any(x['via_uuid'] == v.uid(via) and x['same_net'] for x in added))
        via.SetNetCode(0)
        added = v.added_records(before, v.drill_paste_contacts(b))
        self.assertTrue(any(x['via_uuid'] == v.uid(via) and not x['same_net'] for x in added))

    def test_08_missing_reports_are_incomplete(self):
        self.assertEqual(v.drc_checks(None, None)['status'], 'incomplete')
        self.assertEqual(v.drc_checks(None, self.drc)['status'], 'incomplete')
        self.assertEqual(v.erc_checks(None)['status'], 'incomplete')
        self.assertEqual(v.project_suppressions(None, None)['status'], 'incomplete')

    def test_09_drc_errors_opens_parity_new_warnings(self):
        original = json.loads(self.drc.read_text())
        for name, bucket, severity in [('error', 'violations', 'error'), ('open', 'unconnected_items', 'warning'),
                                       ('parity', 'schematic_parity', 'warning'), ('new_warning', 'violations', 'warning')]:
            j = copy.deepcopy(original)
            j[bucket].append({'severity': severity, 'type': 'test_failure', 'description': name, 'items': []})
            self.assertEqual(v.drc_checks(self.drc, self.dump(name+'.json', j))['status'], 'fail')
        j = copy.deepcopy(original); j['included_severities'] = ['warning']
        self.assertEqual(v.drc_checks(self.drc, self.dump('drc-filtered.json', j))['status'], 'incomplete')
        self.assertEqual(v.drc_checks(self.drc, self.drc)['silkscreen_warnings'], 54)

    def test_10_new_suppressions_rejected(self):
        original = json.loads(self.project.read_text())
        j = copy.deepcopy(original); j['board']['design_settings']['rule_severities']['clearance'] = 'ignore'
        self.assertEqual(v.project_suppressions(self.project, self.dump('ignored.kicad_pro', j))['status'], 'fail')
        j = copy.deepcopy(original); j['board']['design_settings']['drc_exclusions'].append('test new exclusion')
        self.assertEqual(v.project_suppressions(self.project, self.dump('excluded.kicad_pro', j))['status'], 'fail')
        j = copy.deepcopy(original); j['board']['design_settings']['rule_severities']['clearance'] = 'warning'
        self.assertEqual(v.project_suppressions(self.project, self.dump('downgraded.kicad_pro', j))['status'], 'fail')
        j = json.loads(self.drc.read_text()); j['ignored_checks'].append({'key': 'clearance', 'description': 'clearance'})
        self.assertEqual(v.drc_checks(self.drc, self.dump('new-report-ignore.json', j))['status'], 'fail')

    def test_11_erc_errors_rejected(self):
        self.assertEqual(v.erc_checks(self.erc)['status'], 'pass')
        j = json.loads(self.erc.read_text())
        j['sheets'][0]['violations'].append({'severity': 'error', 'type': 'test_error', 'description': 'test', 'items': []})
        self.assertEqual(v.erc_checks(self.dump('erc-error.json', j))['status'], 'fail')

    def test_12_numeric_spelling_and_missing_footprint(self):
        self.assertEqual(v.canonical(v.parse_sexpr('(at 1.000 0.000)')), v.canonical(v.parse_sexpr('(at 1 -0)')))
        changed = copy.deepcopy(self.tree); changed.remove(v.children(changed, 'footprint')[0])
        self.assertEqual(v.invariant_checks(self.board, self.board, self.tree, changed)['status'], 'fail')


    def test_13_zone_and_keepout_definition_changes_caught(self):
        self.assertEqual(v.zone_counts(self.tree), {'total': 8, 'keepouts': 2, 'ground_copper_zones': 6})
        def check_change(field, value, keepout=False):
            changed = copy.deepcopy(self.tree)
            zone = next(z for z in v.children(changed, 'zone') if bool(v.children(z, 'keepout')) == keepout)
            if field == 'boundary':
                v.children(v.children(v.children(zone, 'polygon')[0], 'pts')[0], 'xy')[0][1] = value
            elif field == 'thermal_gap':
                v.children(v.children(zone, 'fill')[0], 'thermal_gap')[0][1] = value
            elif field == 'keepout_tracks':
                v.children(v.children(zone, 'keepout')[0], 'tracks')[0][1] = value
            elif field == 'priority':
                zone.append(['priority', value])
            else:
                v.children(zone, field)[0][1] = value
            result = v.invariant_checks(self.board, self.board, self.tree, changed)
            self.assertEqual(result['checks']['zone_and_keepout_definitions']['status'], 'fail', field)
        check_change('boundary', '100.0001')
        check_change('net', ('string', '5V'))
        check_change('layer', ('string', 'B.Cu'))
        check_change('thermal_gap', '0.3')
        check_change('priority', '2')
        check_change('keepout_tracks', 'allowed', keepout=True)
        changed = copy.deepcopy(self.tree)
        changed.remove(v.children(changed, 'zone')[0])
        self.assertNotEqual(v.zone_definitions(self.tree), v.zone_definitions(changed))

    def test_14_generated_zone_fill_geometry_and_state_ignored(self):
        changed = copy.deepcopy(self.tree)
        for zone in v.children(changed, 'zone'):
            zone[:] = [x for x in zone if not isinstance(x, list) or not x or x[0] not in {'filled_polygon', 'fill_segments'}]
            zone.append(['filled_polygon', ['layer', ('string', 'F.Cu')], ['pts', ['xy', '1', '2'], ['xy', '3', '4'], ['xy', '5', '6']]])
            zone.append(['fill_segments', ['layer', ('string', 'F.Cu')], ['pts', ['xy', '7', '8'], ['xy', '9', '10']]])
            fill = v.children(zone, 'fill')[0]
            fill[:] = [x for x in fill if not (isinstance(x, str) and x in {'yes', 'no'})]
        self.assertEqual(v.invariant_checks(self.board, self.board, self.tree, changed)['status'], 'pass')
        for zone in v.children(changed, 'zone'):
            v.children(zone, 'fill')[0].insert(1, 'no')
        self.assertEqual(v.zone_definitions(self.tree), v.zone_definitions(changed))
        for zone in v.children(changed, 'zone'):
            v.children(zone, 'fill')[0][1] = 'yes'
        self.assertEqual(v.zone_definitions(self.tree), v.zone_definitions(changed))



if __name__ == '__main__':
    unittest.main(verbosity=2)
