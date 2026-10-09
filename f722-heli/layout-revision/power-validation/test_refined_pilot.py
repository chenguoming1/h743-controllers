"""Pure selector/resource controls; no native geometry, matrix or board solve."""
import copy,json,unittest,tempfile
from pathlib import Path
from compile_power_ledger import build_cases
from copper_fem import Refused
from prepare_loaded_pilot import select_cases,select_scope,checked_extra_evidence
from run_bounded_pilot import validate_budget


class RefinedPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).parent
        plan=json.loads((root/'case-plan.disabled.json').read_text())
        settings=json.loads((root/'compiler-settings.json').read_text())
        families,_=build_cases(plan,settings);cls.cases=select_cases([c for rows in families.values()for c in rows])
        registry=json.loads((root/'terminal-registry.disabled.json').read_text())
        nets={}
        for name,spec in registry['contacts'].items():nets.setdefault(spec['net'],{})[name]=spec
        cls.primary={'networks':[{'net':n,'contacts':c}for n,c in sorted(nets.items())],
                     'loops':plan['VCAP_copper_loops'],'mesh_spacings_mm':[.12,.09]}
    def test_combined_contact_operator_and_loops(self):
        cases=copy.deepcopy(self.cases);before=copy.deepcopy(cases)
        networks,loops=select_scope(self.primary,cases,True)
        self.assertEqual(cases,before);self.assertEqual((len(networks),sum(len(n['contacts'])for n in networks),len(loops)),(13,99,5))
        self.assertEqual(len(next(n['contacts']for n in networks if n['net']=='GND')),41)
        self.assertIn('C7.2',next(n['contacts']for n in networks if n['net']=='GND'))
    def test_default_scope_is_preserved(self):
        networks,loops=select_scope(self.primary,self.cases,False)
        self.assertEqual((len(networks),sum(len(n['contacts'])for n in networks),len(loops)),(11,94,0))
    def test_wrong_refinement_or_loop_budget_refuses(self):
        p=copy.deepcopy(self.primary);p['mesh_spacings_mm']=[.2,.15]
        with self.assertRaises(Refused):select_scope(p,self.cases,True)
        p=copy.deepcopy(self.primary);p['loops'][0]['maximum_ohm']=.04
        with self.assertRaises(Refused):select_scope(p,self.cases,True)
        p=copy.deepcopy(self.primary);p['loops'].pop()
        with self.assertRaises(Refused):select_scope(p,self.cases,True)
    def test_exact_release_and_resource_caps(self):
        old={'numerical_execution_authorized':True}
        validate_budget(1200,4096,old)
        with self.assertRaises(ValueError):validate_budget(1500,4096,old)
        refined={'numerical_execution_authorized':True,'pilot_resource_limits':{'overall_wall_seconds':1500,'address_space_MiB':4096}}
        validate_budget(1500,4096,refined)
        for seconds,memory in [(1501,4096),(1500,4097),(0,4096),(1500,511)]:
            with self.assertRaises(ValueError):validate_budget(seconds,memory,refined)
        refined['numerical_execution_authorized']=False
        with self.assertRaises(ValueError):validate_budget(1500,4096,refined)
    def test_additional_native_evidence_is_exact_and_passed(self):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'endpoint.json';data={'board_sha256':'board','native_sha256':'native','passed':True}
            path.write_text(json.dumps(data));rows=checked_extra_evidence([path],'board','native')
            self.assertEqual(rows[0]['name'],'endpoint.json');self.assertEqual(len(rows[0]['sha256']),64)
            for change in [{'board_sha256':'other'},{'native_sha256':'other'},{'passed':False}]:
                path.write_text(json.dumps({**data,**change}))
                with self.assertRaises(Refused):checked_extra_evidence([path],'board','native')
    def test_additional_evidence_basename_collision_refuses(self):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'endpoint.json';path.write_text(json.dumps({'board_sha256':'board'}))
            with self.assertRaises(Refused):checked_extra_evidence([path,path],'board','native')


if __name__=='__main__':unittest.main()
