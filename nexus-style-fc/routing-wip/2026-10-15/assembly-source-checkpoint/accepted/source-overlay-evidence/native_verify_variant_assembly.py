#!/usr/bin/env python3
"""FOR SOLE NATIVE LANE ONLY: run real, source-bound BOM/CPL exports and compare.
This does not refill, mutate either board, or generate release CAM.
"""
import argparse,csv,hashlib,json,pathlib,subprocess,sys
if not __debug__: raise SystemExit('Refusing optimized Python: active guards are required')
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
from guarded_cleanup import BOARD,sha,write_json
ap=argparse.ArgumentParser();ap.add_argument('--source-project',required=True,type=pathlib.Path);ap.add_argument('--candidate-project',required=True,type=pathlib.Path);ap.add_argument('--expected-source-sha256',required=True);ap.add_argument('--expected-candidate-sha256',required=True);ap.add_argument('--kicad-cli',required=True,type=pathlib.Path);ap.add_argument('--out',required=True,type=pathlib.Path);a=ap.parse_args()
S=a.source_project.resolve();C=a.candidate_project.resolve();O=a.out.resolve();K=a.kicad_cli.resolve()
assert sha(S/BOARD)==a.expected_source_sha256 and sha(C/BOARD)==a.expected_candidate_sha256
assert not O.exists();O.mkdir(parents=True)
assert sha(S/'tools/export_fab.py')==sha(C/'tools/export_fab.py')
T=pathlib.Path(__file__).resolve().parent/'source-candidate-final/source-variant-transaction.json';transaction=json.loads(T.read_text());mapping=transaction['fpid_mapping']
assert sha(S/'tools/design.py')==transaction['source_input_sha256']['tools/design.py']
assert sha(C/'tools/design.py')==next(r['new_sha256'] for r in transaction['overlay_files'] if r['path']=='tools/design.py')
version=subprocess.run([str(K),'--version'],check=True,text=True,capture_output=True).stdout.strip();assert version.startswith('10.'),version
code='''import importlib.util,pathlib,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'tools'))
spec=importlib.util.spec_from_file_location('native_checked_export_fab',root/'tools/export_fab.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.K=sys.argv[3];m.bom_cpl('nexus-style-fc',str(root/'hardware/nexus-style-fc.kicad_pcb'),'design',sys.argv[2])
'''
records={}
for label,root in [('before',S),('after',C)]:
 out=O/label;out.mkdir();run=subprocess.run([sys.executable,'-c',code,str(root),str(out),str(K)],text=True,capture_output=True);(out/'export.log').write_text(run.stdout+run.stderr);assert run.returncode==0,(label,run.returncode,run.stderr)
 bom=out/'nexus-style-fc-bom-jlc.csv';cpl=out/'nexus-style-fc-cpl-jlc.csv';br=list(csv.DictReader(bom.open()));cr=list(csv.DictReader(cpl.open()));brefs={r for x in br for r in x['Designator'].split(',')};crefs={x['Designator'] for x in cr};assert len(crefs)==len(cr) and brefs==crefs
 assert 'J1' not in brefs and 'J1' not in crefs
 assert all(r in brefs for r in ['U3','L2','U14','J6','D1','D2','D3'])
 records[label]={'board_sha256':sha(root/BOARD),'BOM_sha256':sha(bom),'CPL_sha256':sha(cpl),'machine_part_count':len(crefs),'BOM_group_count':len(br),'included_selected_targets':[x for x in cr if x['Designator'] in ['U3','L2','U14','J6','D1','D2','D3']],'J1_absent_from_actual_BOM_and_CPL':True,'refs':sorted(crefs)}
name='nexus-style-fc-cpl-jlc.csv';assert (O/'before'/name).read_bytes()==(O/'after'/name).read_bytes(),'Actual CPL changed'
def normalized_bom(path,after):
 rows=list(csv.DictReader(path.open()));out={}
 for row in rows:
  assert set(row)=={'Comment','Designator','Footprint','LCSC Part #'}
  for ref in row['Designator'].split(','):
   assert ref not in out;v={k:x for k,x in row.items() if k!='Designator'}
   if ref in mapping:
    m=mapping[ref];assert v['Footprint']==m['new_fpid' if after else 'old_fpid'].split(':')[1]
    assert v['Comment']==m['value'] and v['LCSC Part #']==m['lcsc']
    if after:v['Footprint']=m['old_fpid'].split(':')[1]
   out[ref]=v
 return out
assert normalized_bom(O/'before/nexus-style-fc-bom-jlc.csv',False)==normalized_bom(O/'after/nexus-style-fc-bom-jlc.csv',True),'BOM changed beyond five authorized FPID names'
assert records['before']['machine_part_count']==records['after']['machine_part_count']==83
assert sha(S/BOARD)==a.expected_source_sha256 and sha(C/BOARD)==a.expected_candidate_sha256
write_json(O/'native-assembly-verification.json',{'status':'PASS real-native CPL byte-identical; BOM per-reference exact after only five authorized Footprint-name normalizations','kicad_cli':str(K),'version':version,'exporter_sha256':sha(C/'tools/export_fab.py'),'design_sha256':sha(C/'tools/design.py'),'records':records,'normalized_FPID_refs':sorted(mapping),'source_transaction_sha256':sha(T),'no_board_mutation':True,'process_notes':{'J1':'Manual child-board slot/fillet joint, omitted from real machine BOM/CPL by empty LCSC selection; preserved smd pad attribute is not a machine-placement decision.','J6':'Included mixed SMT/PTH connector: 16 SMT signal contacts, 4 plated GND shell lugs, 2 NPTH locators. Shell soldering process still requires qualification.'},'qualification':'BOM/CPL equivalence only. Native DRC, assembly/Gerber visual and selected-package orientation checks remain separate; no production signoff.'})
print('PASS actual native CPL byte equality and bounded BOM-name equivalence; 83 placements, J1 omitted, J6 retained')
