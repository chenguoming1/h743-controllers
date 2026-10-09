"""Analytical direct/iterative solver controls; no project board is loaded."""
import unittest,json,tempfile,time
from pathlib import Path
from unittest.mock import patch
import numpy as np
from shapely.geometry import box
from scipy.sparse import csr_matrix
import copper_fem
from copper_fem import Mesh,Limits,Refused
import test_static_validation as static_fixtures
from validate_static import preflight,run_screen


def mesh(**settings):
    return Mesh({'F.Cu':box(0,0,4,1)},
       {'a':('F.Cu',box(0,0,.3,1)),'b':('F.Cu',box(3.7,0,4,1))},
       .125,.01,.015,limits=Limits(linear_solver='sparse-direct',**settings))


class LinearBackendTests(unittest.TestCase):
    def test_direct_conservation_and_fixed_reference_factor_reuse(self):
        original=copper_fem.splu
        with patch('copper_fem.splu',wraps=original)as factor:
            m=mesh();a=m.solve({'a':1.,'b':-1.},'a');b=m.solve({'a':1.,'b':-1.},'b')
            self.assertEqual(factor.call_count,1)
        self.assertAlmostEqual(a['contact_voltage_V']['b'],-.034,10)
        self.assertAlmostEqual(b['contact_voltage_V']['a'],.034,10)
        self.assertAlmostEqual(a['copper_loss_W'],.034,10)
        self.assertLess(b['KCL_max_residual_A'],1e-8)
        d=b['linear_solver_diagnostics'];self.assertEqual(d['anchored_connected_components'],1)
        self.assertGreater(d['factorization']['factor_stored_array_bytes'],0)
        self.assertGreater(d['last_direct_solve']['residual_and_solution_mantissa_bits'],52)
        self.assertEqual(d['factorization']['ordering'],'MMD_AT_PLUS_A')

    def test_failed_iterative_diagnostic_is_not_used_as_result(self):
        m=mesh(cg_diagnostic_iterations=1)
        result=m.solve({'a':1.,'b':-1.},'b');d=result['linear_solver_diagnostics']
        self.assertEqual(d['cg_diagnostic']['info'],1)
        self.assertTrue(d['cg_diagnostic']['diagnostic_only'])
        self.assertAlmostEqual(result['contact_voltage_V']['a'],.034,10)
        self.assertLessEqual(d['last_direct_solve']['residual_norm_history_A'][-1],d['last_direct_solve']['required_residual_norm_A'])

    def test_extended_refinement_resolves_canceling_rows_without_relaxation(self):
        # A tiny strongly connected conductor with a weak path to its reference.
        conductance=7.92e8
        A=csr_matrix([[conductance+1.,-conductance],[-conductance,conductance+1.]])
        rhs=np.array([1.,0.]);m=Mesh.__new__(Mesh)
        m.limits=Limits(linear_solver='sparse-direct');m.start_time=time.monotonic();m.linear_diagnostics={}
        value,_=m.direct_solution(A,rhs,A.diagonal())
        self.assertEqual(value.dtype,np.dtype(np.longdouble))
        diagnostic=m.linear_diagnostics['last_direct_solve']
        self.assertEqual(diagnostic['required_residual_norm_A'],1e-10)
        self.assertTrue(diagnostic['converged'])
        self.assertLessEqual(diagnostic['residual_norm_history_A'][-1],1e-10)
        self.assertGreater(diagnostic['float64_projection_residual_norm_history_A'][-1],1e-10)
        self.assertGreater(diagnostic['residual_and_solution_mantissa_bits'],52)

    def test_failed_refinement_retains_actual_history(self):
        m=mesh();m.solve({'a':1.,'b':-1.})
        class NoCorrection:
            def solve(self,rhs):return np.zeros_like(rhs)
        m._direct_factor=NoCorrection()
        with self.assertRaisesRegex(Refused,'unchanged linear tolerance')as caught:
            m.solve({'a':1.,'b':-1.})
        diagnostic=caught.exception.linear_solver_diagnostics['last_direct_solve']
        self.assertFalse(diagnostic['converged'])
        self.assertEqual(diagnostic['residual_norm_history_A'],[1.]*5)
        self.assertEqual(diagnostic['required_residual_norm_A'],1e-10)

    def test_factor_caps_and_invalid_matrix_refuse(self):
        with self.assertRaisesRegex(Refused,'nonzero budget'):mesh(max_factor_nonzeros=1).solve({'a':1.,'b':-1.})
        m=mesh();m.K.data[0]=np.nan
        with self.assertRaisesRegex(Refused,'Nonfinite'):m.solve({'a':1.,'b':-1.})
        m=mesh();row,col=m.K.nonzero();k=next(i for i,(a,b)in enumerate(zip(row,col))if a!=b)
        m.K[row[k],col[k]]*=.5
        with self.assertRaisesRegex(Refused,'symmetric'):m.solve({'a':1.,'b':-1.})

    def test_completed_coarse_grid_is_retained_unqualified_after_fine_refusal(self):
        with tempfile.TemporaryDirectory()as tmp:
            root,_,_=static_fixtures.SourceTests().fixture(tmp)
            context=preflight(root/'freeze.json',root/'ledger.json')
            original=copper_fem.Mesh
            def fail_fine(domains,contacts,spacing,*args,**kwargs):
                if spacing==.25:raise Refused('synthetic fine-grid refusal')
                return original(domains,contacts,spacing,*args,**kwargs)
            with patch('validate_static.Mesh',side_effect=fail_fine):
                with self.assertRaisesRegex(Refused,'fine-grid refusal'):run_screen(context)
            self.assertEqual(len(context['partial_runs']),1)
            self.assertEqual(context['partial_runs'][0]['spacing_mm'],.5)
            self.assertGreater(context['partial_runs'][0]['unit_transfers'][0]['resistance_ohm'],0)

    def test_source_bound_runner_reuses_checkpoint_after_solver_selection(self):
        with tempfile.TemporaryDirectory()as tmp:
            root,_,ledger=static_fixtures.SourceTests().fixture(tmp)
            context=preflight(root/'freeze.json',root/'ledger.json');context['mesh_cache_dir']=root/'cache'
            first=run_screen(context)
            self.assertTrue(first['conditional_static_screen_pass'])
            self.assertTrue(all(not row['hit']for row in first['mesh_cache_receipts']))
            ledger.setdefault('limits',{})['linear_solver']='sparse-direct'
            (root/'ledger.json').write_text(json.dumps(ledger))
            context=preflight(root/'freeze.json',root/'ledger.json');context['mesh_cache_dir']=root/'cache'
            with patch('validate_static.Mesh',side_effect=AssertionError('must reuse the valid checkpoint')):
                second=run_screen(context)
            self.assertTrue(second['conditional_static_screen_pass'])
            self.assertTrue(all(row['hit']for row in second['mesh_cache_receipts']))
            for a,b in zip(first['runs'],second['runs']):
                self.assertAlmostEqual(a['unit_transfers'][0]['resistance_ohm'],b['unit_transfers'][0]['resistance_ohm'],12)


if __name__=='__main__':unittest.main(verbosity=2)
