"""Compiler/schema controls only; real-board meshes or circuits are never run."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from copper_fem import Refused,polygonal_area,area_overlay,grid_coordinate,triangle_geometry
import numpy as np
from compile_power_ledger import build_cases,check_cases,stamp_cases
from activate_ranked_slices import select_vertices
from dc_circuit import solve_circuit
import test_static_validation as static_fixtures
from validate_static import preflight,run_screen,sha256
from audit_native_ports import ideal_land_contact_groups
from shapely.geometry import box,Point,GeometryCollection,LineString,Polygon


class CompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).parent
        cls.plan=json.loads((root/'case-plan.disabled.json').read_text())
        cls.settings=json.loads((root/'compiler-settings.json').read_text())
        cls.families,cls.deferred=build_cases(cls.plan,cls.settings)
        registry=json.loads((root/'terminal-registry.disabled.json').read_text())
        nets={}
        for name,spec in registry['contacts'].items():nets.setdefault(spec['net'],{})[name]=spec
        cls.networks=[{'net':net,'contacts':contacts}for net,contacts in nets.items()]

    def test_complete_case_budgets_and_no_unset_endpoints(self):
        self.assertEqual({k:len(v)for k,v in self.families.items()},{'baseline':170,'upper':40,'servo':100})
        self.assertEqual(len(self.deferred),178)
        check_cases([c for f in self.families.values()for c in f],self.networks)
        for c in self.families['servo']:
            self.assertIn(c['parameters']['allocation_vertex'],self.settings['servo_sample_allocations'])
            self.assertIn('not selected',c['allocation_basis'])
        self.assertTrue(all(c['parameters']['DSM_A']==0 for c in self.families['upper']))

    def test_unresolved_measured_and_ideal_return_shortcuts_refuse(self):
        base=self.families['servo'][0]
        for kind in ['null','return','second_source','endpoint','budget']:
            c=copy.deepcopy(base)
            if kind=='null':c['resistors'][0]['ohm']=None
            elif kind=='return':c['sources'].append({'name':'J6_return_reference','p':'J6.1','n':'SOURCE_GND','voltage_V':0})
            elif kind=='second_source':c['sources'].append({'name':'invented','p':'J8.2','n':'J8.1','voltage_V':7.4})
            elif kind=='endpoint':c['loads'][0]['p']=None
            else:c['parameters']['CORE_aggregate_A']+=.5
            with self.subTest(kind=kind),self.assertRaises(Refused):check_cases([c],self.networks)

    def test_compute_release_guard_runs_before_mesh(self):
        with patch('validate_static.Mesh',side_effect=AssertionError('must never construct a mesh')):
            with self.assertRaisesRegex(Refused,'compute slot'):
                run_screen({'manifest':{'numerical_execution_authorized':False}})
        with patch.dict('os.environ',{'OPENBLAS_NUM_THREADS':'8','OMP_NUM_THREADS':'1'}):
            with self.assertRaisesRegex(Refused,'per-process'):
                run_screen({'manifest':{'numerical_execution_authorized':True}})

    def test_resolved_case_hash_changes_with_a_load(self):
        cases=[copy.deepcopy(self.families['baseline'][0])]
        stamp_cases(cases);first=cases[0]['case_definition_sha256']
        stamp_cases(cases);self.assertEqual(first,cases[0]['case_definition_sha256'])
        cases[0]['loads'][0]['current_A']+=.001
        stamp_cases(cases);self.assertNotEqual(first,cases[0]['case_definition_sha256'])

    def test_additional_evidence_is_hash_checked(self):
        with tempfile.TemporaryDirectory()as tmp:
            d,f,l=static_fixtures.SourceTests().fixture(tmp)
            extra=d/'extra.txt';extra.write_text('bound evidence')
            f['files']['additional']={'path':'extra.txt','sha256':sha256(extra)}
            (d/'freeze.json').write_text(json.dumps(f));l['freeze_manifest_sha256']=sha256(d/'freeze.json')
            (d/'ledger.json').write_text(json.dumps(l));preflight(d/'freeze.json',d/'ledger.json')
            extra.write_text('changed evidence')
            with self.assertRaisesRegex(Refused,'changed'):preflight(d/'freeze.json',d/'ledger.json')

    def test_report_only_headroom_does_not_masquerade_as_acceptance(self):
        c={'name':'toy','reference_node':'g','sources':[{'name':'s','p':'s','n':'g','voltage_V':5}],
           'resistors':[{'name':'r','p':'s','n':'p','ohm':.3}],'loads':[{'name':'l','p':'p','n':'g','current_A':1}],
           'probes':[{'name':'operating','p':'p','n':'g','minimum_V':3}],
           'report_only_probes':[{'name':'accuracy','p':'p','n':'g','comparison_floor_V':4.8}]}
        r=solve_circuit(c)
        self.assertTrue(r['static_probe_pass']);self.assertAlmostEqual(r['report_only_probes'][0]['margin_to_comparison_floor_V'],-.1)
        self.assertFalse(r['report_only_probes'][0]['acceptance_limit'])

    def test_rankings_retain_distinct_voltage_constraints(self):
        candidates=[{'name':v,'parameters':{'allocation_vertex':v}}for v in ['a','b','c']]
        rows={v:{'probes':[{'name':'receiver','voltage_V':x,'minimum_V':3.1}],
                 'report_only_probes':[{'name':'input','voltage_V':y,'comparison_floor_V':4.3},
                                       {'name':'sink','voltage_V':z}]}for v,x,y,z in [('a',3.11,4.5,3.2),('b',3.2,4.31,3.2),('c',3.2,4.5,3.1)]}
        self.assertEqual(set(select_vertices(candidates,rows)),{'a','b','c'})
        del rows['b']
        with self.assertRaisesRegex(Refused,'incomplete'):select_vertices(candidates,rows)

    def test_same_layer_ideal_annulus_merger_is_detected(self):
        contacts={'a':('F.Cu',box(0,0,.3,1)),'b':('F.Cu',box(.7,0,1,1))}
        land={'uuid':'v','copper':{'F.Cu':static_fixtures.records(box(.2,0,.8,1))}}
        r=ideal_land_contact_groups({'F.Cu':box(0,0,1,1)},contacts,[land])
        self.assertEqual(r['terminal_collisions'][0]['contacts'],['a','b'])
        r=ideal_land_contact_groups({'F.Cu':box(0,0,1,1),'B.Cu':box(0,0,1,1)},
             {'a':('F.Cu',box(0,0,.3,1)),'b':('B.Cu',box(.7,0,1,1))},
             [{'uuid':'v','copper':{'F.Cu':land['copper']['F.Cu'],'B.Cu':land['copper']['F.Cu']}}])
        self.assertEqual(r['terminal_collisions'],[])

    def test_exact_strip_clipping_preserves_holes(self):
        domain=box(0,0,3,2).difference(Point(.97,1).buffer(.3,quad_segs=16)).union(box(3.2,.4,3.8,1.6))
        total=0
        for ix in range(8):
            strip=domain.intersection(box(ix*.5,0,(ix+1)*.5,2))
            for iy in range(4):
                cell=box(ix*.5,iy*.5,(ix+1)*.5,(iy+1)*.5)
                direct=domain.intersection(cell);partitioned=strip.intersection(cell)
                self.assertTrue(partitioned.is_valid)
                self.assertLess(direct.symmetric_difference(partitioned).area,1e-12)
                total+=partitioned.area
        self.assertAlmostEqual(total,domain.area,12)

    def test_empty_mixed_dimension_overlay_preserves_area_and_holes(self):
        polygon=box(0,0,2,2).difference(box(.5,.5,1.5,1.5))
        mixed=GeometryCollection([polygon,LineString([(2,2),(3,2)]),Point(4,4)])
        area=polygonal_area(mixed)
        self.assertEqual(area.wkb,polygon.wkb)
        self.assertEqual(area.area,mixed.area)
        self.assertEqual(len(area.interiors),1)
        self.assertTrue(area_overlay(mixed,Polygon(),'intersection').is_empty)
        self.assertEqual(area_overlay(mixed,Polygon(),'difference').wkb,mixed.wkb)
        self.assertEqual(polygonal_area(area_overlay(mixed,Polygon(),'difference')).wkb,polygon.wkb)
        self.assertTrue(polygonal_area(area_overlay(GeometryCollection([Point(0,0)]),polygon,'intersection')).is_empty)

    def test_boundary_line_is_retained_to_node_contact_seam(self):
        # A contact in the next tile intersects this tile only on its edge.
        # Its zero-area line must still subdivide this triangle boundary.
        tile=box(1,0,1.5,.5)
        contact=box(1.5,.1,2,.3)
        seam=area_overlay(contact,tile,'intersection')
        self.assertEqual(seam.geom_type,'LineString')
        partition=area_overlay(tile,seam,'difference')
        coordinates=set(partition.exterior.coords)
        self.assertIn((1.5,.1),coordinates);self.assertIn((1.5,.3),coordinates)
        self.assertEqual(partition.area,tile.area)
        # Preserve the counterexample: filtering before overlay loses the
        # exact nodes while leaving polygon area unchanged.
        prematurely_filtered=area_overlay(tile,polygonal_area(seam),'difference')
        self.assertNotIn((1.5,.1),set(prematurely_filtered.exterior.coords))
        self.assertEqual(prematurely_filtered.area,partition.area)

    def test_canonical_decimal_grid_removes_floating_seam_without_snapping_native(self):
        self.assertNotEqual(61*.2,12.2)
        self.assertEqual(grid_coordinate(61,.2),12.2)
        self.assertEqual(grid_coordinate(77,.15),11.55)
        native=box(12.2,11.4,12.4,11.6)
        raw_cell=box(60*.2,57*.2,61*.2,58*.2)
        exact_cell=box(grid_coordinate(60,.2),grid_coordinate(57,.2),grid_coordinate(61,.2),grid_coordinate(58,.2))
        self.assertGreater(native.intersection(raw_cell).area,0)
        self.assertEqual(native.intersection(exact_cell).area,0)
        before=native.wkb
        area_overlay(native,exact_cell,'intersection')
        self.assertEqual(native.wkb,before)

    def test_triangle_condition_guard_retains_geometry_and_refuses_unresolved_elements(self):
        xy=np.asarray([[(12.2,11.6),(12.200000000000001,11.6),(12.200000000000001,11.4)]])
        unchanged=xy.tobytes()
        with self.assertRaisesRegex(Refused,'conditioning'):triangle_geometry(xy)
        self.assertEqual(xy.tobytes(),unchanged)
        # Small absolute area is valid when the local element is well-shaped.
        tiny=np.asarray([[(0.,0.),(1e-10,0.),(0.,1e-10)]])
        area,condition=triangle_geometry(tiny)
        self.assertAlmostEqual(area[0]/1e-20,1.);self.assertEqual(condition[0],2.)


if __name__=='__main__':unittest.main()
