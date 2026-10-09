"""Portable geometry-reference controls; no native geometry or solver is run."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from copper_fem import Refused
import validate_static
from validate_static import compact_result_evidence


def fixture(case_count=1):
    fresh={'native_vertices_changed':0,'coordinate_changes':[(1.25,2.5)],
           'ring_certificates':[{'vertices':[(i,i+.25) for i in range(200)],
                                 'rational_area_preserved_exactly':True}]}
    stored=json.loads(json.dumps(fresh))
    field={'contact_voltage_V':{'source':.012,'sink':0.},'copper_loss_W':.012,
           'sheet_loss_W':.01,'port_power_W':.012,'KCL_max_residual_A':1e-12,
           'barrels':[{'uuid':'test','current_A':1.,'loss_W':.002}],
           'peak_element_density_A_per_mm2':23.,'density_is_ampacity_rating':False,
           'linear_solver_diagnostics':{'last_direct_solve':{'converged':True}},
           'native_edge_noding':{'F.Cu':fresh}}
    transfer={'name':'test','net':'P','resistance_ohm':.012,'field':field}
    run={'spacing_mm':.2,'ports':[{'net':'P','contacts':['source','sink'],
          'impedance_ohm':[[.012]],'reciprocity_error_ohm':0.,'native_edge_noding':{'F.Cu':fresh}}],
         'unit_transfers':[transfer],
         'loops':[{'name':'loop','legs':[transfer],'resistance_ohm':.012,'pass':True}],
         'cases':[{'case':str(i),'fields':{'P':field},'static_probe_pass':True,
                   'power_W':{'copper_loss':.012},'port_injections':[{'net':'P',
                   'injections_A':{'source':1.,'sink':-1.}}]} for i in range(case_count)]}
    return {'schema':'f722-scoped-static-result/v1','board_sha256':'board',
            'freeze_sha256':'freeze','ledger_sha256':'ledger','conditional_static_screen_pass':True,
            'geometry_certificates':{'P/F.Cu':stored},'runs':[run]}


class ResultEvidenceTests(unittest.TestCase):
    def test_all_port_and_field_locations_preserve_numerical_data_and_input(self):
        result=fixture();before=json.dumps(result,sort_keys=True)
        compact=compact_result_evidence(result)
        digest=hashlib.sha256(json.dumps(result['geometry_certificates']['P/F.Cu'],
          sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        expected={'F.Cu':{'certificate_key':'P/F.Cu','sha256':digest}}
        a=result['runs'][0];b=compact['runs'][0]
        pairs=[(a['ports'][0],b['ports'][0]),
               (a['unit_transfers'][0]['field'],b['unit_transfers'][0]['field']),
               (a['loops'][0]['legs'][0]['field'],b['loops'][0]['legs'][0]['field']),
               (a['cases'][0]['fields']['P'],b['cases'][0]['fields']['P'])]
        for original,rewritten in pairs:
            self.assertNotIn('native_edge_noding',rewritten)
            self.assertEqual(rewritten['native_edge_noding_refs'],expected)
            self.assertEqual({k:v for k,v in original.items() if k!='native_edge_noding'},
                             {k:v for k,v in rewritten.items() if k!='native_edge_noding_refs'})
            for key,value in original.items():
                if isinstance(value,(dict,list)) and key!='native_edge_noding':
                    self.assertIs(rewritten[key],value)
        self.assertIs(compact['geometry_certificates'],result['geometry_certificates'])
        self.assertEqual(json.dumps(result,sort_keys=True),before)
        for key in ['board_sha256','freeze_sha256','ledger_sha256','conditional_static_screen_pass']:
            self.assertEqual(compact[key],result[key])

    def test_shared_receipts_are_hashed_once_per_identity_and_size_is_bounded(self):
        result=fixture(case_count=80);seen=[]
        original=json.JSONEncoder.iterencode
        def record(encoder,value,*args,**kwargs):
            seen.append(id(value));return original(encoder,value,*args,**kwargs)
        with patch.object(json.JSONEncoder,'iterencode',record):
            compact=compact_result_evidence(result)
        # The cached list receipt and fresh tuple receipt are distinct objects,
        # with equal canonical JSON. Eighty case occurrences share the latter.
        self.assertEqual(len(seen),2)
        self.assertEqual(len(set(seen)),2)
        self.assertLess(len(json.dumps(compact)),len(json.dumps(result))*.25)

    def test_compact_references_are_revalidated_and_idempotent(self):
        compact=compact_result_evidence(fixture())
        self.assertEqual(compact_result_evidence(compact),compact)
        field=compact['runs'][0]['cases'][0]['fields']['P']
        field['native_edge_noding_refs']['F.Cu']['sha256']='0'*64
        with self.assertRaisesRegex(Refused,'hash mismatch'):
            compact_result_evidence(compact)

    def test_missing_changed_and_cross_net_certificates_refuse(self):
        for issue in ['missing','changed','wrong-net','wrong-reference-key','both-forms','nonfinite']:
            with self.subTest(issue=issue):
                result=fixture()
                if issue=='missing':result['geometry_certificates'].clear()
                elif issue=='changed':result['geometry_certificates']['P/F.Cu']['native_vertices_changed']=1
                elif issue=='wrong-net':result['runs'][0]['ports'][0]['net']='OTHER'
                elif issue=='wrong-reference-key':
                    result=compact_result_evidence(result)
                    result['runs'][0]['ports'][0]['native_edge_noding_refs']['F.Cu']['certificate_key']='OTHER/F.Cu'
                elif issue=='both-forms':result['runs'][0]['ports'][0]['native_edge_noding_refs']={}
                else:result['geometry_certificates']['P/F.Cu']['not_finite']=float('nan')
                with self.assertRaises(Refused):compact_result_evidence(result)

    def test_partial_refusal_preserves_status_bindings_and_diagnostic_evidence(self):
        result=fixture();result['partial_runs_unqualified']=result.pop('runs')
        result.update(status='REFUSED',reason='fine grid failed',conditional_static_screen_pass=False,
                      partial_runs_are_converged=False,geometry_reproduction={'previous_receipt':{'detail':'preserved'}})
        compact=compact_result_evidence(result)
        self.assertFalse(compact['conditional_static_screen_pass'])
        self.assertFalse(compact['partial_runs_are_converged'])
        self.assertEqual(compact['reason'],'fine grid failed')
        self.assertIs(compact['geometry_reproduction'],result['geometry_reproduction'])
        self.assertIn('native_edge_noding_refs',compact['partial_runs_unqualified'][0]['loops'][0]['legs'][0]['field'])
        self.assertEqual(compact_result_evidence({'status':'PREFLIGHT ONLY'}),{'status':'PREFLIGHT ONLY'})

    def cli(self,root,result,refuse=False):
        context={key:result[key] for key in ['board_sha256','freeze_sha256','ledger_sha256']}
        context['geometry_certificates']=result['geometry_certificates']
        context['partial_runs']=result['runs']
        def screen(_):
            if refuse:raise Refused('synthetic later-grid refusal')
            return result
        stdout=io.StringIO();output=root/'result.json'
        argv=['validate_static.py','--freeze',str(root/'freeze.json'),
              '--ledger',str(root/'ledger.json'),'--out',str(output),'--run']
        with patch('sys.argv',argv),patch('validate_static.preflight',return_value=context),\
             patch('validate_static.run_screen',side_effect=screen),\
             contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(io.StringIO()):
            code=validate_static.main()
        return code,stdout.getvalue(),output

    def test_cli_writes_compact_success_and_refused_partial_json(self):
        for refuse in [False,True]:
            with self.subTest(refuse=refuse),tempfile.TemporaryDirectory() as tmp:
                result=fixture();code,_,output=self.cli(Path(tmp),result,refuse)
                self.assertEqual(code,2 if refuse else 0)
                saved=json.loads(output.read_text())
                self.assertEqual(saved['conditional_static_screen_pass'],not refuse)
                runs=saved['partial_runs_unqualified' if refuse else 'runs']
                self.assertIn('native_edge_noding_refs',runs[0]['ports'][0])
                self.assertNotIn('native_edge_noding',runs[0]['ports'][0])
                self.assertEqual(saved['geometry_certificates'],result['geometry_certificates'])
                for key in ['board_sha256','freeze_sha256','ledger_sha256']:
                    self.assertEqual(saved[key],result[key])
                if refuse:self.assertFalse(saved['partial_runs_are_converged'])

    def test_cli_rejects_unverifiable_evidence_without_overwriting_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);output=root/'result.json';output.write_text('preserved existing result')
            result=fixture();result['geometry_certificates'].clear()
            code,stdout,_=self.cli(root,result)
            self.assertEqual(code,2)
            refusal=json.loads(stdout)
            self.assertEqual(refusal['status'],'REFUSED')
            self.assertFalse(refusal['conditional_static_screen_pass'])
            self.assertFalse(refusal['output_written'])
            self.assertEqual(refusal['board_sha256'],'board')
            self.assertEqual(output.read_text(),'preserved existing result')


if __name__=='__main__':unittest.main(verbosity=2)
