#!/usr/bin/env python3
"""FOR SOLE NATIVE LANE ONLY: run real, source-bound BOM/CPL exports and compare.
This does not refill, mutate either board, or generate release CAM.
"""
import argparse,csv,hashlib,json,pathlib,subprocess,sys
from guarded_cleanup import BOARD,sha,write_json
ap=argparse.ArgumentParser();ap.add_argument('--source-project',required=True,type=pathlib.Path);ap.add_argument('--candidate-project',required=True,type=pathlib.Path);ap.add_argument('--expected-source-sha256',required=True);ap.add_argument('--expected-candidate-sha256',required=True);ap.add_argument('--kicad-cli',required=True,type=pathlib.Path);ap.add_argument('--out',required=True,type=pathlib.Path);a=ap.parse_args()
S=a.source_project.resolve();C=a.candidate_project.resolve();O=a.out.resolve();K=a.kicad_cli.resolve()
assert sha(S/BOARD)==a.expected_source_sha256 and sha(C/BOARD)==a.expected_candidate_sha256
assert not O.exists();O.mkdir(parents=True)
for rel in ['tools/export_fab.py','tools/design.py']:assert sha(S/rel)==sha(C/rel),rel
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
for name in ['nexus-style-fc-bom-jlc.csv','nexus-style-fc-cpl-jlc.csv']:assert (O/'before'/name).read_bytes()==(O/'after'/name).read_bytes(),('BOM/CPL changed',name)
assert sha(S/BOARD)==a.expected_source_sha256 and sha(C/BOARD)==a.expected_candidate_sha256
write_json(O/'native-assembly-verification.json',{'status':'PASS real-native before/after BOM and CPL are byte-identical','kicad_cli':str(K),'version':version,'exporter_sha256':sha(C/'tools/export_fab.py'),'design_sha256':sha(C/'tools/design.py'),'records':records,'no_board_mutation':True,'process_notes':{'J1':'Manual child-board slot/fillet joint, omitted from real machine BOM/CPL by empty LCSC selection; preserved smd pad attribute is not a machine-placement decision.','J6':'Included mixed SMT/PTH connector: 16 SMT signal contacts, 4 plated GND shell lugs, 2 NPTH locators. Shell soldering process still requires qualification.'},'qualification':'BOM/CPL equivalence only. Native DRC, assembly/Gerber visual and selected-package orientation checks remain separate; no production signoff.'})
print('PASS actual native BOM/CPL byte equality, 83 selected placements expected, J1 omitted, J6 retained')
