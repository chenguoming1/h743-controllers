"""Controls for physical corner definitions and honest numerical budget scope."""
import copy
import unittest
from unittest.mock import patch
from copper_fem import Refused

from portable_model import check_cases
from portable_model import (PLAN, REFERENCE, SOURCE_BOUNDS, apply_profile,
                                      bases, budget_margin, budget_profile, profiles, read,
                                      allowance,ensure_generator_unchanged)


class SensitivityControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(PLAN)
        cls.ledger=read(REFERENCE/'ledger.json')
        cls.lower,cls.upper,cls.usb=bases(cls.plan,cls.ledger)
        cls.bounds=read(SOURCE_BOUNDS)

    def test_complete_contexts_and_usb_scope(self):
        self.assertEqual((len(self.lower),len(self.upper),len(self.usb)),(120,80,2))
        expected=set(self.plan['proposed_case_dimensions']['electronics_allocation_vertices'])
        contexts={}
        for c in self.lower:
            p=c['parameters'];key=(c['scope'],p['input_at_defined_source_V'],tuple(p['ABC_ports']))
            contexts.setdefault(key,set()).add(p['allocation_vertex'])
        self.assertEqual(len(contexts),12)
        self.assertTrue(all(x==expected for x in contexts.values()))
        self.assertTrue(all(c['parameters']['DSM_A']==0 and c['parameters']['ABC_ports']==[] for c in self.usb))

    def test_source_packet_arithmetic_and_independent_temperature(self):
        for i,dt in [(0,0),(1,60),(2,80),(3,65)]:
            source=self.bounds['scenarios'][i]
            for high in [False,True]:
                for leakage in [0,1e-7,-1e-7]:
                    c=apply_profile(self.upper[0] if high else self.lower[0],dict(name='control',high=high,delta_temperature=dt,ifb=leakage))
                    resistors={r['name']:r['ohm'] for r in c['resistors']}
                    rt=resistors['R54_feedback_top'];rb=resistors['R55_feedback_bottom']
                    v=next(cv['voltage_V'] for cv in c['converters'] if cv['name'].startswith('U6'))*(1+rt/rb)
                    key='max' if high else 'min'
                    self.assertAlmostEqual(v,float(source['no_leakage_reference_divider_V'][key])+leakage*rt,places=11)

    def test_independent_efficiencies_no_duplicate_iq_and_no_mutation(self):
        original=copy.deepcopy(self.lower[0])
        c=apply_profile(original,dict(name='crossed',eta6=.75,eta9=.95))
        self.assertEqual([cv['efficiency'] for cv in c['converters']],[.75,.95])
        self.assertTrue(all(cv['quiescent_A']==0 for cv in c['converters']))
        self.assertEqual(original,self.lower[0])
        self.assertNotEqual(c['case_definition_sha256'],original['case_definition_sha256'])

    def test_all_profiles_bind_known_contacts_and_do_not_invent_loads(self):
        groups=[self.lower,self.upper,self.usb]
        count=0
        for group,plist in zip(groups,profiles()):
            cases=[apply_profile(c,p) for c in group for p in plist]
            check_cases(cases,self.ledger['networks']);count+=len(cases)
            for c in cases:
                self.assertFalse(any(l['name'].endswith('_servo_illustration') for l in c['loads']))
                if c['scope']=='capacity':self.assertNotIn('classic_DSM_pad',[p['name'] for p in c['probes']])
        self.assertEqual(count,5532)

    def test_report_grid_failure_cannot_be_laundered_into_allowance(self):
        pair=dict(voltage_checks=[dict(probe='accepted',guarded_margin_V=.1,voltage_grid_pass=True)],
                  report_only_grid_checks=[dict(probe='CORE',voltage_grid_pass=False)])
        self.assertEqual(budget_margin(pair,'u6_error')['probe'],'voltage_grid_convergence')

    def test_accuracy_and_operating_screens_are_distinct(self):
        pair=dict(voltage_checks=[dict(probe='U9_operating',guarded_margin_V=1.2,voltage_grid_pass=True)],
                  report_only_grid_checks=[dict(probe='U9_accuracy',guarded_comparison_headroom_V=-.1,voltage_grid_pass=True)])
        self.assertGreater(budget_margin(pair,'u8_operating')['margin_V'],0)
        self.assertLess(budget_margin(pair,'u8_accuracy')['margin_V'],0)

    def test_separate_and_joint_perturbations_are_explicit(self):
        base=dict(name='base',eta6=.75,delta_temperature=65)
        for target,key in [('u6_error','error6'),('u9_error','error9')]:
            p=budget_profile(base,target,.01)
            self.assertEqual(p[key],-.01)
            self.assertNotIn('error9' if key=='error6' else 'error6',p)
        p=budget_profile(base,'joint_error',.01)
        self.assertEqual((p['error6'],p['error9']),(-.01,-.01))
        self.assertNotIn('error6',base)

    def test_wall_timeout_cannot_be_treated_as_a_physical_boundary(self):
        with patch('portable_model.compact_pair',side_effect=Refused('Bounded circuit-only wall time exceeded')):
            with self.assertRaisesRegex(Refused,'wall time exceeded'):
                allowance([self.lower[0]],{},dict(name='control'),'u7')

    def test_source_change_after_launch_refuses_mislabeled_evidence(self):
        ensure_generator_unchanged()
        with patch('portable_model.sha256',return_value='changed'):
            with self.assertRaisesRegex(Refused,'changed after launch'):
                ensure_generator_unchanged()


if __name__=='__main__':unittest.main()
