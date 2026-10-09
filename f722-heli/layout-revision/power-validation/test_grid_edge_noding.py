"""Exact grid subdivisions and local refusal replay; no native board solve."""
from copy import deepcopy
from fractions import Fraction as F
import json
import math
from pathlib import Path
import unittest
import numpy as np
import shapely as s
from shapely.geometry import Polygon,box
from copper_fem import Refused,Mesh,area_overlay,parts,triangle_geometry,grid_coordinate
from native_edge_noding import canonicalize
from test_native_edge_noding import edges,partition_triangles
from test_result_evidence import fixture as evidence_fixture
from validate_static import remember_geometry_certificate,compact_result_evidence,geometry_certificate_key


class GridNodingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads((Path(__file__).parent/'geometry-repro/candidate19-grid-annulus.json').read_text())
        cls.shapes=[s.from_wkb(bytes.fromhex(cls.fixture[key]))for key in ['domain_wkb_hex','land_wkb_hex']]

    def test_exact_native_annulus_refusal_replays_and_grid_nodes_prevent_artifact(self):
        domain,land=self.shapes;cell=box(*self.fixture['cell_bounds'])
        cut=domain.intersection(cell)
        with self.assertRaisesRegex(Refused,'conditioning'):
            triangle_geometry(np.asarray(partition_triangles(cut,land)))
        before=[g.wkb for g in self.shapes]
        fixed,receipt=canonicalize(self.shapes,self.fixture['source_edges'],grid_spacing_mm=.12)
        self.assertEqual([g.wkb for g in self.shapes],before)
        self.assertEqual(receipt['inserted_exact_grid_vertices'],24)
        self.assertEqual(receipt['native_vertices_changed'],0)
        self.assertEqual(receipt['changed_derived_vertices'],0)
        self.assertTrue(all(r['rational_area_preserved_exactly']for r in receipt['ring_certificates']))
        for original,noded in zip(self.shapes,fixed):
            original_points={tuple(p)for poly in parts(original)for ring in [poly.exterior,*poly.interiors]for p in ring.coords}
            noded_points={tuple(p)for poly in parts(noded)for ring in [poly.exterior,*poly.interiors]for p in ring.coords}
            self.assertLessEqual(original_points,noded_points)
        noded_cut=fixed[0].intersection(cell)
        self.assertEqual(noded_cut.difference(fixed[1]).area,0.)
        areas,condition=triangle_geometry(np.asarray(partition_triangles(noded_cut,fixed[1])))
        self.assertLess(float(max(condition)),100.)
        self.assertAlmostEqual(sum(abs(areas))/2,noded_cut.area,15)
        self.assertEqual(len(fixed[0].interiors),1)

    def test_two_grid_strip_cell_coverage_and_conforming_seams(self):
        for spacing in [.12,.09]:
            fixed,proof=canonicalize(self.shapes,self.fixture['source_edges'],grid_spacing_mm=spacing)
            x0,y0,x1,y1=fixed[0].bounds;all_triangles=[]
            iy0,iy1=math.floor(y0/spacing),math.ceil(y1/spacing)
            anchor=lambda i:grid_coordinate(i,spacing)
            for ix in range(math.floor(x0/spacing),math.ceil(x1/spacing)):
                strip_box=box(anchor(ix),anchor(iy0),anchor(ix+1),anchor(iy1))
                strip,ideal=[area_overlay(g,strip_box,'intersection')for g in fixed]
                for iy in range(iy0,iy1):
                    cut=area_overlay(strip,box(anchor(ix),anchor(iy),anchor(ix+1),anchor(iy+1)),'intersection')
                    all_triangles.extend(partition_triangles(cut,ideal))
            triangles=np.asarray(all_triangles);areas,condition=triangle_geometry(triangles)
            self.assertAlmostEqual(sum(abs(areas))/2,fixed[0].area,14)
            self.assertLess(float(max(condition)),1e6)
            points=np.unique(triangles.reshape(-1,2),axis=0)
            for tri in triangles:
                for a,b in zip(tri,np.roll(tri,-1,axis=0)):
                    ab=b-a;t=(points-a)@ab/(ab@ab)
                    distance=np.linalg.norm(points-(a+t[:,None]*ab),axis=1)
                    self.assertFalse(np.any((t>1e-7)&(t<1-1e-7)&(distance<1e-10)))

    def test_distinct_near_grid_intersections_remain_distinct(self):
        narrow=Polygon([(0,0),(20.000001,20),(20.000002,20.000001),(.000001,.000001)])
        fixed,proof=canonicalize([narrow],edges(narrow),grid_spacing_mm=10.)
        expected=[float(F(200000000,20000001)),float(F(200000000,20000001)+F(1,20000001000000))]
        actual=sorted(y for x,y in fixed[0].exterior.coords if x==10.)
        self.assertEqual(actual,expected)
        self.assertGreater(actual[1]-actual[0],0.)
        self.assertGreater(fixed[0].area,0.)
        self.assertTrue(all(r['rational_area_preserved_exactly']for r in proof['ring_certificates']))

    def test_distinct_exact_crossings_with_one_float_refuse(self):
        shape=Polygon([(-1000,-989.9),(1000,1010.100001),(1000.000001,1010.100002),(-999.999999,-989.899999)])
        with self.assertRaisesRegex(Refused,'Distinct exact grid intersections collapse'):
            canonicalize([shape],edges(shape),grid_spacing_mm=1000.)

    def test_grid_bounds_and_native_grid_vertices_preserved(self):
        shape=box(-.24,-.24,.24,.24)
        fixed,proof=canonicalize([shape],edges(shape),grid_spacing_mm=.12)
        self.assertEqual(proof['inserted_exact_grid_vertices'],12)
        self.assertLessEqual(set(shape.exterior.coords),set(fixed[0].exterior.coords))
        self.assertEqual(fixed[0].area,shape.area)
        for value in [0.,-.1,float('nan')]:
            with self.assertRaises(Refused):canonicalize([shape],edges(shape),grid_spacing_mm=value)
        with self.assertRaisesRegex(Refused,'cap exceeded'):
            canonicalize([shape],edges(shape),grid_spacing_mm=.12,grid_vertex_limit=2)

    def test_synthetic_conservation_and_two_grid_resistance(self):
        domain=box(0,0,1,.3)
        contacts={'a':('F.Cu',box(0,0,.1,.3)),'b':('F.Cu',box(.9,0,1,.3))}
        source=edges(domain)+[e for _,g in contacts.values()for e in edges(g)]
        values=[]
        for spacing in [.12,.09]:
            mesh=Mesh({'F.Cu':domain},contacts,spacing,.01,.015,native_edge_provider=lambda layer:source)
            result=mesh.solve({'a':1.,'b':-1.},'b');values.append(result['contact_voltage_V']['a'])
            self.assertLess(result['KCL_max_residual_A'],1e-8)
            self.assertAlmostEqual(values[-1],.8/.3*.01,10)
            self.assertEqual(mesh.native_edge_noding['F.Cu']['grid_spacing_mm'],spacing)
        self.assertLess(abs(values[1]-values[0]),1e-10)

    def test_grid_bound_receipts_keep_exact_comparison_and_references(self):
        context={};result=evidence_fixture();first=result['runs'][0]
        for spacing in [.2,.15]:
            run=deepcopy(first);run['spacing_mm']=spacing
            blocks=[run['ports'][0],run['unit_transfers'][0]['field'],run['loops'][0]['legs'][0]['field'],run['cases'][0]['fields']['P']]
            for block in blocks:
                receipt=block['native_edge_noding']['F.Cu'];receipt['grid_spacing_mm']=spacing
                remember_geometry_certificate(context,'P','F.Cu',receipt)
            if spacing==.2:result['runs']=[run]
            else:result['runs'].append(run)
        result['geometry_certificates']=context['geometry_certificates']
        self.assertEqual(len(result['geometry_certificates']),2)
        compact=compact_result_evidence(result)
        self.assertEqual(compact_result_evidence(compact),compact)
        changed=deepcopy(result['geometry_certificates']['P/F.Cu/grid=0.2']);changed['native_vertices_changed']=1
        with self.assertRaisesRegex(Refused,'changed between meshes'):
            remember_geometry_certificate(context,'P','F.Cu',changed)
        result['runs'][0]['spacing_mm']=.15
        with self.assertRaisesRegex(Refused,'another mesh grid'):compact_result_evidence(result)
        compact['runs'][0]['spacing_mm']=.15
        with self.assertRaisesRegex(Refused,'another mesh grid'):compact_result_evidence(compact)


if __name__=='__main__':unittest.main(verbosity=2)
