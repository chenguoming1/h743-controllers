"""Small geometry controls only. No board mesh, field or circuit is solved."""
import json,math,unittest,tempfile
from pathlib import Path
import numpy as np
import shapely as s
from shapely.geometry import Polygon,MultiPolygon,GeometryCollection,LineString,box
from copper_fem import Refused,parts,area_overlay,triangle_geometry,grid_coordinate
from native_edge_noding import canonicalize
import test_static_validation as static_fixtures
from validate_static import preflight,run_screen,sha256,remember_geometry_certificate


def edges(g):
    return [(a,b)for p in parts(g)for ring in [p.exterior,*p.interiors]
            for a,b in zip(list(ring.coords)[:-1],list(ring.coords)[1:])]


def partition_triangles(domain,ideal):
    return [list(t.exterior.coords)[:3]for op in ['intersection','difference']
      for p in parts(area_overlay(domain,ideal,op))
      for t in s.constrained_delaunay_triangles(p).geoms if t.area>0]


class NativeNodingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads((Path(__file__).parent/'geometry-repro/local-edge-arrangement.json').read_text())
        cls.shapes=[s.from_wkb(bytes.fromhex(cls.fixture[k]))for k in ['cut_wkb_hex','ideal_wkb_hex']]

    def test_saved_native_edge_intersection_and_partition_conservation(self):
        original=[g.wkb for g in self.shapes]
        fixed,r=canonicalize(self.shapes,self.fixture['source_edges'])
        self.assertEqual(original,[g.wkb for g in self.shapes])
        self.assertEqual(r['native_vertices_changed'],0)
        self.assertEqual(r['changed_derived_vertices'],1)
        self.assertEqual(r['coordinate_changes'][0]['signed_ULP_change'],[1.,0.])
        self.assertEqual(r['maximum_derived_vertex_displacement_mm'],math.ulp(14.354591053009024))
        self.assertTrue(all(x['rational_area_preserved_exactly']for x in r['ring_certificates']))
        self.assertTrue(all(x['orientation_preserved']for x in r['ring_certificates']))
        tris=np.asarray(partition_triangles(*fixed));area,condition=triangle_geometry(tris)
        self.assertLess(float(max(condition)),1e5)
        self.assertAlmostEqual(sum(abs(area))/2,fixed[0].area,14)
        self.assertAlmostEqual(sum(area_overlay(*fixed,op).area for op in ['intersection','difference']),fixed[0].area,15)
        points=np.unique(tris.reshape(-1,2),axis=0)
        for tri in tris:
            for a,b in zip(tri,np.roll(tri,-1,axis=0)):
                ab=b-a;t=(points-a)@ab/(ab@ab);distance=np.linalg.norm(points-(a+t[:,None]*ab),axis=1)
                self.assertFalse(np.any((t>1e-7)&(t<1-1e-7)&(distance<1e-10)))

    def test_repeated_shared_strip_and_cell_clipping(self):
        fixed,_=canonicalize(self.shapes,self.fixture['source_edges'])
        for h in [.2,.1,.05]:
            total=0;all_triangles=[]
            x0,y0,x1,y1=fixed[0].bounds
            for ix in range(math.floor(x0/h),math.ceil(x1/h)):
                strip=box(grid_coordinate(ix,h),grid_coordinate(math.floor(y0/h),h),grid_coordinate(ix+1,h),grid_coordinate(math.ceil(y1/h),h))
                d,i=[area_overlay(g,strip,'intersection')for g in fixed]
                for iy in range(math.floor(y0/h),math.ceil(y1/h)):
                    cell=box(grid_coordinate(ix,h),grid_coordinate(iy,h),grid_coordinate(ix+1,h),grid_coordinate(iy+1,h))
                    cut=area_overlay(d,cell,'intersection')
                    tris=partition_triangles(cut,i)
                    if tris:
                        a,_=triangle_geometry(np.asarray(tris));total+=sum(abs(a))/2;all_triangles.extend(tris)
            self.assertAlmostEqual(total,fixed[0].area,14)
            # All adjacent cells must retain the same seam subdivisions.
            # A long edge opposite two shorter edges is a hanging node.
            tri_array=np.asarray(all_triangles);points=np.unique(tri_array.reshape(-1,2),axis=0)
            for tri in tri_array:
                for a,b in zip(tri,np.roll(tri,-1,axis=0)):
                    ab=b-a;t=(points-a)@ab/(ab@ab);distance=np.linalg.norm(points-(a+t[:,None]*ab),axis=1)
                    self.assertFalse(np.any((t>1e-7)&(t<1-1e-7)&(distance<1e-10)),f'Hanging seam at {h} mm')

    def test_native_edge_and_exact_grid_intersection(self):
        triangle=Polygon([(0,0),(3,1),(0,2)]);cell=box(0,0,1,2)
        clipped=triangle.intersection(cell)
        coordinates=[(x,math.nextafter(y,math.inf)if x==1 and y<1 else y)for x,y in clipped.exterior.coords]
        perturbed=Polygon(coordinates)
        fixed,r=canonicalize([perturbed,triangle],edges(triangle)+edges(cell))
        self.assertEqual(r['native_vertices_changed'],0)
        self.assertTrue(all(x['rational_area_preserved_exactly']for x in r['ring_certificates']))
        self.assertTrue(fixed[0].is_valid)
        self.assertIn((1.,1/3),set(fixed[0].exterior.coords))
        self.assertIn((1.,1/3),set(fixed[1].exterior.coords))

    def test_cached_certificate_serialization_preserves_exact_guard(self):
        r=json.loads((Path(__file__).parent/'geometry-repro/uncertified-edge-ancestry.json').read_text())
        first,second=[row['edge']for row in r['native_edges']];p=r['point'];a=first[0];c=second[0]
        _,fresh=canonicalize([Polygon([p,a,c])],[first,second,[a,c]])
        cached=json.loads(json.dumps(fresh));self.assertNotEqual(fresh,cached)
        context={};remember_geometry_certificate(context,'test','F.Cu',cached)
        remember_geometry_certificate(context,'test','F.Cu',fresh)
        self.assertEqual(context['geometry_certificates']['test/F.Cu'],cached)
        fresh['native_vertices_changed']=1
        with self.assertRaisesRegex(Refused,'certificate changed')as caught:
            remember_geometry_certificate(context,'test','F.Cu',fresh)
        repro=caught.exception.geometry_reproduction
        self.assertNotEqual(repro['previous_sha256'],repro['current_sha256'])
        self.assertEqual(repro['previous_receipt']['native_vertices_changed'],0)
        self.assertEqual(repro['current_receipt']['native_vertices_changed'],1)

    def test_holes_islands_and_native_vertices_are_preserved(self):
        ring=box(0,0,3,3).difference(box(1,1,2,2));island=box(4,0,5,1)
        source=MultiPolygon([ring,island]);fixed,r=canonicalize([source],edges(source))
        self.assertTrue(fixed[0].equals(source))
        self.assertEqual(r['changed_derived_vertices'],0)
        self.assertEqual(r['geometry_checks'][0]['contours'],2)
        self.assertEqual(r['geometry_checks'][0]['holes'],1)

    def test_missing_and_distinct_nearby_ancestries_refuse(self):
        malformed=Polygon([(0,0),(1,0),(.2345678901,.4321)])
        with self.assertRaisesRegex(Refused,'ancestry'):canonicalize([malformed],edges(box(0,0,1,1)))
        # Large coordinates deliberately bring two distinct exact intersections
        # within the candidate-search guard. Proximity cannot choose one.
        x=1e9+.5;shape=Polygon([(x,1),(x+.1,1),(x+.1,1.1)])
        lines=[[(1e9,1),(1e9+1,1)],[(x,0),(x,2)],[(x+.000001,0),(x+.000001,2)]]
        with self.assertRaises(Refused):canonicalize([shape],lines)

    def test_mixed_pretiling_constraints_refuse_instead_of_disappearing(self):
        p=box(0,0,1,1);mixed=GeometryCollection([p,LineString([(1,1),(2,1)])])
        with self.assertRaisesRegex(Refused,'cannot be discarded'):canonicalize([mixed],edges(p))

    def test_line_residual_guard_refuses_unproved_displacement(self):
        triangle=Polygon([(0,0),(3,1),(0,2)]);cell=box(0,0,1,2);clipped=triangle.intersection(cell)
        coords=[(x,y+1e-7 if x==1 and y<1 else y)for x,y in clipped.exterior.coords]
        with self.assertRaisesRegex(Refused,'ancestry'):canonicalize([Polygon(coords)],edges(triangle)+edges(cell))

    def test_shallow_exact_crossing_uses_conditioned_distance_certificate(self):
        r=json.loads((Path(__file__).parent/'geometry-repro/uncertified-edge-ancestry.json').read_text())
        first,second=[row['edge']for row in r['native_edges']]
        p=r['point'];a=first[0];c=second[0]
        shape=Polygon([p,a,c]);fixed,proof=canonicalize([shape],[first,second,[a,c]])
        row=proof['coordinate_changes'][0]
        self.assertEqual(row['signed_ULP_change'],[44.,8.])
        self.assertLess(row['displacement_mm'],row['admission_certificate']['conditioned_distance_bound_mm'])
        self.assertLess(row['displacement_mm'],1e-9)
        self.assertTrue(proof['ring_certificates'][0]['rational_area_preserved_exactly'])

    def test_nearby_distinct_native_edge_intersections_remain_ambiguous(self):
        # Two integer-nm lines are only ~3.5e-14 mm apart normally. Both
        # intersect the vertical edge near p, but are distinct rational points.
        p=(10.,20000000*10./20000001);a=(0.,0.);top=(10.,20.1)
        source=[[(0.,0.),(20.000001,20.)],[(.000001,.000001),(20.000002,20.000001)],
                [(10.,0.),top],[a,top]]
        with self.assertRaisesRegex(Refused,'ambiguous'):canonicalize([Polygon([a,p,top])],source)

    def test_full_displacement_search_includes_nearby_segment_endpoints(self):
        q=(10.,10.);a=(9.,10.000001);b=(9.,9.999999);p=(10.+1e-12,10.)
        fixed,proof=canonicalize([Polygon([p,a,b])],[[q,a],[q,b],[a,b]])
        self.assertIn(q,set(fixed[0].exterior.coords))
        row=proof['coordinate_changes'][0]
        self.assertGreater(row['displacement_mm'],row['admission_certificate']['line_residual_guard_mm'])
        self.assertLess(row['displacement_mm'],row['admission_certificate']['conditioned_distance_bound_mm'])

    def test_competing_near_endpoint_intersection_cannot_be_omitted(self):
        horizontal=[(0.,10.),(20.,10.)]
        diagonal=[(9.999999,9.999999),(19.999998,19.999999)]
        p=(9.9999999999999,10.)
        source=[horizontal,diagonal,[diagonal[0],horizontal[0]],[(10.,10.),(20.,10.01)]]
        with self.assertRaisesRegex(Refused,'ambiguous'):
            canonicalize([Polygon([p,diagonal[0],horizontal[0]])],source)

    def test_source_bound_mesh_path_keeps_conservation_and_receipts(self):
        with tempfile.TemporaryDirectory()as tmp:
            root,freeze,ledger=static_fixtures.SourceTests().fixture(tmp)
            freeze['analysis_source_sha256']={'native_edge_noding.py':sha256(Path(__file__).parent/'native_edge_noding.py')}
            (root/'freeze.json').write_text(json.dumps(freeze));ledger['freeze_manifest_sha256']=sha256(root/'freeze.json')
            (root/'ledger.json').write_text(json.dumps(ledger))
            result=run_screen(preflight(root/'freeze.json',root/'ledger.json'))
            self.assertTrue(result['conditional_static_screen_pass'])
            for run in result['runs']:
                transfer=run['unit_transfers'][0]
                self.assertAlmostEqual(transfer['resistance_ohm'],3.4*result['material']['sheet_ohm'],10)
                proof=transfer['field']['native_edge_noding']['F.Cu']
                self.assertEqual(proof['native_vertices_changed'],0)
                self.assertTrue(all(row['rational_area_preserved_exactly']for row in proof['ring_certificates']))

    def test_distinct_intersection_cannot_hide_under_a_native_vertex(self):
        x=1e9+.5;shape=Polygon([(x,1),(x+1,1),(x,2)])
        source=edges(shape)+[[(x,0),(x+.000001,100)]]
        with self.assertRaisesRegex(Refused,'collapses onto'):canonicalize([shape],source)


if __name__=='__main__':unittest.main(verbosity=2)
