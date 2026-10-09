"""Scope decisions keep failed illustrations and the raw runner boolean visible."""
from copy import deepcopy
import unittest
from summarize_combined_pilot import classify_scopes


def fixture():
    ledger={'mesh_spacings_mm':[.12,.09],'convergence':{'absolute_voltage_V':.001},
      'cases':[{'name':'required','scope':'classic','nets':['P','GND']},
               {'name':'illustration','scope':'same_BEC_illustrative','nets':['P','GND']}],
      'loops':[{'name':'VCAP','legs':[{'net':'C'},{'net':'GND'}]}]}
    run={'cases':[{'case':'required','static_probe_pass':True},{'case':'illustration','static_probe_pass':False}],
         'loops':[{'name':'VCAP','pass':True}]}
    result={'conditional_static_screen_pass':False,
      'runs':[dict(deepcopy(run),spacing_mm=h)for h in ledger['mesh_spacings_mm']],
      'impedance_sensitivity':[{'net':net,'pass':True}for net in ['P','GND','C']],
      'voltage_margin_checks':[{'case':'required','change_V':.0001,'pass':True},
                               {'case':'illustration','change_V':.0002,'pass':False}],
      'resistance_margin_checks':[{'name':'VCAP','pass':True}]}
    return result,ledger


class CombinedSummaryTests(unittest.TestCase):
    def test_failed_illustration_does_not_relabel_required_scope_or_runner_boolean(self):
        result,ledger=fixture();before=deepcopy(result);r=classify_scopes(result,ledger)
        self.assertTrue(r['required_scope_acceptance']);self.assertTrue(r['VCAP_acceptance'])
        self.assertTrue(r['numerical_acceptance']);self.assertFalse(r['illustrative_threshold_and_margin_pass'])
        self.assertFalse(r['runner_overall_boolean']);self.assertEqual(result,before)

    def test_failed_required_convergence_and_loop_are_distinct(self):
        result,ledger=fixture();result['voltage_margin_checks'][0].update({'change_V':.0011,'pass':False})
        r=classify_scopes(result,ledger)
        self.assertFalse(r['required_scope_acceptance']);self.assertFalse(r['numerical_acceptance']);self.assertTrue(r['VCAP_acceptance'])
        result,ledger=fixture();result['impedance_sensitivity'][-1]['pass']=False
        r=classify_scopes(result,ledger)
        self.assertTrue(r['required_scope_acceptance']);self.assertFalse(r['VCAP_acceptance'])

    def test_refusal_cannot_qualify_complete_scopes(self):
        result,ledger=fixture();result.update(status='REFUSED')
        r=classify_scopes(result,ledger)
        self.assertIsNone(r['required_scope_acceptance']);self.assertIsNone(r['VCAP_acceptance']);self.assertFalse(r['numerical_acceptance'])


if __name__=='__main__':unittest.main(verbosity=2)
