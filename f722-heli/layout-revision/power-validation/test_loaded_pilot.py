"""Case-selection controls only; no native export, matrix or board solve."""
import copy,json,unittest
from pathlib import Path
from compile_power_ledger import build_cases
from prepare_loaded_pilot import select_cases
from copper_fem import Refused

class LoadedPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).parent
        plan=json.loads((root/'case-plan.disabled.json').read_text())
        settings=json.loads((root/'compiler-settings.json').read_text())
        families,_=build_cases(plan,settings);cls.cases=[c for rows in families.values()for c in rows]
    def test_exact_scope_and_allocation_vertices(self):
        cases=select_cases(self.cases);self.assertEqual(len(cases),73)
        minimum=[c for c in cases if c['scope']in ['classic','capacity']]
        self.assertEqual(len(minimum),60)
        for scope in ['classic','capacity']:
            for ports in [['J9','J10'],['J9','J11'],['J10','J11']]:
                self.assertEqual(len({c['parameters']['allocation_vertex']for c in minimum if c['scope']==scope and c['parameters']['ABC_ports']==ports}),10)
        self.assertEqual(len([c for c in cases if c['scope']=='usb_configuration']),2)
        self.assertEqual(len([c for c in cases if c['scope']=='same_BEC_illustrative']),11)
    def test_servo_disconnects_and_no_capacity_accuracy_claim(self):
        for c in select_cases(self.cases):
            if c['parameters']['input_at_defined_source_V']==5.:
                self.assertFalse(any(x['name'].endswith('_servo_illustration')for x in c['loads']))
            if c['scope']=='capacity':self.assertNotIn('classic_DSM_pad',[p['name']for p in c['probes']])
            self.assertIn('U9_input_accuracy_window_headroom',[p['name']for p in c['report_only_probes']])
    def test_missing_or_incompatible_case_refuses(self):
        cases=copy.deepcopy(self.cases);selected=select_cases(cases)[0]
        with self.assertRaisesRegex(Refused,'selection changed'):select_cases([c for c in cases if c['name']!=selected['name']])
        match=next(c for c in cases if c['name']==selected['name']);match['loads'].append({'name':'bad_servo_illustration'})
        with self.assertRaisesRegex(Refused,'Incompatible servo'):select_cases(cases)

if __name__=='__main__':unittest.main()
