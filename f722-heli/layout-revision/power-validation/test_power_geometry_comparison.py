"""Read-only scope-transfer controls; no mesh or circuit solve."""
import copy,json,tempfile,unittest
from pathlib import Path
from compare_power_geometry import compare
import test_static_validation as fixtures
from copper_fem import Refused

class GeometryComparisonTests(unittest.TestCase):
    def test_exact_scope_and_foreign_drill_fill_port_changes(self):
        with tempfile.TemporaryDirectory()as tmp:
            root,_,_=fixtures.SourceTests().fixture(tmp);p=root/'geometry.json';g=json.loads(p.read_text())
            g.update(maximum_polygon_error_mm=1e-5,copper_error_location='outside',pad_cut_error_location='inside',native_version='synthetic')
            g['zones'][0]['uuid']='zone';p.write_text(json.dumps(g));other=root/'other.json';other.write_text(json.dumps(g))
            run=lambda:compare(p,other,root/'toy-board.txt',root/'toy-board.txt',root/'ledger.json')
            self.assertTrue(run()['exact_structured_inputs_identical'])
            for mode in ['foreign_drill','fill','port']:
                h=copy.deepcopy(g)
                if mode=='foreign_drill':h['objects'].append({'uuid':'foreign','kind':'via','net':'OTHER','plated':True,'drill':{'outside':[],'width':.25},'barrel_layers':['F.Cu']})
                elif mode=='fill':h['zones'][0]['filled']['F.Cu'][0]['outer'][0][0]+=.01
                else:h['objects'][0]['copper']['F.Cu'][0]['outer'][0][0]+=.01
                other.write_text(json.dumps(h));r=run()
                self.assertFalse(r['exact_structured_inputs_identical'],mode)
                if mode=='foreign_drill':
                    self.assertTrue(r['categories']['selected_net_objects']['identical'])
                    self.assertFalse(r['categories']['all_physical_drills']['identical'])
                    self.assertEqual(r['differences']['all_physical_drills']['added_uuids'],['foreign'])
    def test_stale_export_cannot_establish_equivalence(self):
        with tempfile.TemporaryDirectory()as tmp:
            root,_,_=fixtures.SourceTests().fixture(tmp);p=root/'geometry.json';r=json.loads(p.read_text());r['board_sha256']='0'*64;p.write_text(json.dumps(r))
            with self.assertRaises(Refused):compare(p,p,root/'toy-board.txt',root/'toy-board.txt',root/'ledger.json')

if __name__=='__main__':unittest.main()
