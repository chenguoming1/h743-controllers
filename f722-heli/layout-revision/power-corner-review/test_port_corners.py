"""Endpoint definitions and circuit-only scope controls; no native solve."""
import copy
import json
from pathlib import Path
import unittest
from copper_fem import Refused
from portable_model import check_cases,stamp_cases
from portable_model import endpoint_cases,solve_pair,replay_archive


class PortCornerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).parent
        cls.plan=json.loads((root/'inputs/case-plan.disabled.json').read_text())
        cls.networks=json.loads((root/'inputs/verified-ports.json').read_text())['networks']

    def test_complete_endpoint_dimensions_and_budgets(self):
        cases=endpoint_cases(self.plan);check_cases(cases,self.networks)
        self.assertEqual(len(cases),140)
        self.assertEqual(len({c['name']for c in cases}),140)
        loaded=[c for c in cases if c['extension_family']=='loaded_12p6_endpoint']
        upper=[c for c in cases if c['extension_family']=='upper_output_endpoint']
        self.assertEqual((len(loaded),len(upper)),(60,80))
        self.assertEqual({c['parameters']['input_at_defined_source_V']for c in loaded},{12.6})
        self.assertEqual({c['parameters']['input_at_defined_source_V']for c in upper},{5.,12.6})
        self.assertTrue(all(c['parameters']['DSM_A']==0 for c in upper))
        self.assertTrue(all(not any(x['name'].endswith('_servo_illustration')for x in c['loads'])for c in cases))
        self.assertTrue(all(x['quiescent_A']==0 for c in cases for x in c['converters']))

    def test_upper_limits_and_reports_do_not_invent_guarantees(self):
        c=endpoint_cases(self.plan)[60]
        self.assertEqual([p['maximum_V']for p in c['probes']if p['name']=='unloaded_classic_DSM_upper'],[3.465])
        reports=[p for p in c['report_only_probes']if p['name'].endswith('_pad_upper_report')]
        self.assertEqual(len(reports),3);self.assertTrue(all('maximum_V'not in p for p in reports))
        self.assertEqual(next(x['voltage_V']for x in c['converters']if x['name'].startswith('U9')),3.432)

    def toy(self):
        c={'name':'toy','scope':'classic','nets':['P'],'reference_node':'g',
           'sources':[{'name':'s','p':'s','n':'g','voltage_V':5}],
           'loads':[{'name':'l','p':'p','n':'g','current_A':1}],
           'probes':[{'name':'pad','p':'p','n':'g','minimum_V':4.8}],
           'report_only_probes':[{'name':'headroom','p':'p','n':'g','comparison_floor_V':4.95}]}
        stamp_cases([c]);p={'convergence':{'absolute_voltage_V':.001},'grids':[]}
        for spacing,z in [(.12,.1),(.09,.1005)]:
            p['grids'].append({'spacing_mm':spacing,'port_set_sha256':str(z),
                'ports':[{'net':'P','contacts':['s','p'],'impedance_ohm':[[z]]}]})
        return c,p

    def test_small_circuit_preserves_voltage_guard_and_field_unknown(self):
        c,p=self.toy();r=solve_pair(c,p)
        self.assertTrue(r['port_voltage_checks_pass']);self.assertIsNone(r['loaded_field_acceptance'])
        self.assertAlmostEqual(r['voltage_checks'][0]['numerical_guard_V'],.001)
        self.assertAlmostEqual(r['voltage_checks'][0]['guarded_margin_V'],.0985)
        self.assertLess(r['report_only_grid_checks'][0]['guarded_comparison_headroom_V'],0)
        self.assertFalse(r['report_only_grid_checks'][0]['acceptance_limit'])
        p['grids'][1]['ports'][0]['impedance_ohm']=[[.103]]
        r=solve_pair(c,p);self.assertFalse(r['voltage_grid_pass']);self.assertFalse(r['port_voltage_checks_pass'])

    def test_missing_port_network_refuses(self):
        c,p=self.toy();c['nets'].append('unbound')
        with self.assertRaises(Refused):solve_pair(c,p)

    def test_replay_requires_exact_original_cases_and_voltages(self):
        c,p=self.toy();rows=solve_pair(c,p)['runs']
        archive={'runs':[{'spacing_mm':r['spacing_mm'],'cases':[r]}for r in rows]}
        self.assertTrue(replay_archive({'cases':[c]},archive,p)['passed'])
        archive['runs'][0]['cases'][0]['voltage_V']['p']+=1e-8
        with self.assertRaises(Refused):replay_archive({'cases':[c]},archive,p)


if __name__=='__main__':unittest.main()
