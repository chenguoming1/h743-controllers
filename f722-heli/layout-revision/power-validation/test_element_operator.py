"""Physical element condensation, gauge and conditioning controls; synthetic only."""
from itertools import permutations
import time
import unittest
import numpy as np
from scipy.sparse import coo_matrix
from copper_fem import Mesh,Limits,triangle_geometry
from test_linear_backend import mesh as rectangle_mesh


def element(points,mapping):
    m=Mesh.__new__(Mesh);m.limits=Limits(linear_solver='sparse-direct');m.start_time=time.monotonic()
    xy=np.asarray([points],dtype=float);twice,_=triangle_geometry(xy)
    m.areas=abs(twice)/2;m.grad=np.empty((1,3,2));m.sheet=1.;m.barrels=[]
    m.grad[:,:,0]=np.stack((xy[:,1,1]-xy[:,2,1],xy[:,2,1]-xy[:,0,1],xy[:,0,1]-xy[:,1,1]),axis=1)/twice[:,None]
    m.grad[:,:,1]=np.stack((xy[:,2,0]-xy[:,1,0],xy[:,0,0]-xy[:,2,0],xy[:,1,0]-xy[:,0,0]),axis=1)/twice[:,None]
    m.triangles=np.asarray([[0,1,2]]);m.mapping=np.asarray(mapping);m.n=max(mapping)+1
    local=np.einsum('tik,tjk,t->tij',m.grad,m.grad,m.areas)
    nodes=m.mapping[m.triangles]
    m.K=coo_matrix((local.ravel(),(np.repeat(nodes,3,axis=1).ravel(),np.tile(nodes,(1,3)).ravel())),shape=(m.n,m.n)).tocsr()
    return m


class ElementOperatorTests(unittest.TestCase):
    def test_identical_node_is_exact_zero_without_deleting_triangle(self):
        m=element([(0,1),(1e-10,0),(0,0)],[0,0,0]);operator=m.physical_operator()
        self.assertEqual(operator.nnz,0)
        self.assertTrue(np.all(m.physical_field(np.asarray([1e9],dtype=np.longdouble))==0))
        d=m.physical_operator_diagnostics
        self.assertEqual(d['all_equal_ideal_node_zero_energy_triangles'],1)
        self.assertEqual(d['triangles_retained'],1)
        self.assertEqual(d['positive_area_elements_discarded'],0)
        self.assertGreater(m.areas[0],0)

    def test_partial_condensation_uses_singleton_gradient_all_positions(self):
        for singleton in range(3):
            mapping=[0,0,0];mapping[singleton]=1
            m=element([(0,1),(1e-10,0),(0,0)],mapping)
            v=np.asarray([.125,.375],dtype=np.longdouble)
            field=m.physical_field(v)
            expected=m.grad[0,singleton]*np.longdouble(.25)
            np.testing.assert_array_equal(field[0],expected)
            g=m.grad[0,singleton].astype(np.longdouble)
            conductance=np.dot(g,g)*np.longdouble(m.areas[0])
            np.testing.assert_array_equal(m.physical_operator().toarray(),conductance*np.asarray([[1,-1],[-1,1]]))
            np.testing.assert_array_equal(m.physical_field(v+2**30),field)

    def test_skinny_three_node_small_positive_response_survives_every_order(self):
        original=np.asarray([(0,1),(1e-10,0),(0,0)])
        for perm in permutations(range(3)):
            m=element(original[list(perm)],list(perm));v=np.asarray([1.,0.,0.],dtype=np.longdouble)
            field=m.physical_field(v);energy=np.sum(field*field*m.areas[:,None]);quadratic=v@(m.physical_operator()@v)
            self.assertGreater(quadratic,0.)
            self.assertAlmostEqual(float(quadratic/np.longdouble(5e-11)),1.,14)
            self.assertLess(float(abs(quadratic-energy)/energy),1e-15)
            self.assertGreater(m.physical_operator()[0,0],0.)
            np.testing.assert_array_equal(m.physical_field(v+2**30),field)

    def test_obtuse_element_keeps_positive_off_diagonal_and_energy(self):
        m=element([(0,0),(2,0),(.2,.1)],[0,1,2]);operator=m.physical_operator().toarray()
        self.assertTrue(any(operator[i,j]>0 for i in range(3)for j in range(3)if i!=j))
        for voltage in [[.125,.25,.75],[10.,10.,10.]]:
            v=np.asarray(voltage,dtype=np.longdouble);field=m.physical_field(v)
            energy=np.sum(field*field*m.areas[:,None]);quadratic=v@operator@v
            self.assertLess(abs(float(energy-quadratic)),1e-13)

    def test_refinement_targets_physical_operator_despite_preconditioner_row_error(self):
        m=rectangle_mesh();node=m.contact_nodes['b'];m.K[node,node]+=1e-5
        result=m.solve({'a':1.,'b':-1.},'a')
        self.assertAlmostEqual(result['contact_voltage_V']['b'],-.034,10)
        self.assertLess(result['KCL_max_residual_A'],1e-8)
        self.assertAlmostEqual(result['copper_loss_W'],.034,10)
        d=result['linear_solver_diagnostics']
        self.assertGreater(d['physical_element_operator']['maximum_difference_from_double_preconditioner_S'],1e-6)
        self.assertLessEqual(d['last_direct_solve']['residual_norm_history_A'][-1],d['last_direct_solve']['required_residual_norm_A'])


if __name__=='__main__':unittest.main(verbosity=2)
