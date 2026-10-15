from pathlib import Path
import sys,json,subprocess,csv,hashlib,io
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');S=R/'mechanical-integration/main-signal-slot-08';C=Path(sys.argv[1]).resolve();M=json.loads(Path(sys.argv[2]).read_text());O=C/'wip-bom-cpl';assert not O.exists();O.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();H=sha(C/'hardware/nexus-style-fc.kicad_pcb');K=R/'runtime/kicad-cli'
code="""import sys,pathlib,importlib.util
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'tools'));spec=importlib.util.spec_from_file_location('checked_export',root/'tools/export_fab.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.K=sys.argv[3];m.bom_cpl('nexus-style-fc',str(root/'hardware/nexus-style-fc.kicad_pcb'),'design',sys.argv[2])
"""
p=subprocess.run([sys.executable,'-c',code,str(C),str(O),str(K)],capture_output=True,text=True,timeout=90);(O/'export.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
bom='nexus-style-fc-bom-jlc.csv';cpl='nexus-style-fc-cpl-jlc.csv';assert (O/cpl).read_bytes()==(S/'wip-bom-cpl'/cpl).read_bytes(),'CPL changed'
before=list(csv.DictReader((S/'wip-bom-cpl'/bom).open()));after=list(csv.DictReader((O/bom).open()));assert len(before)==len(after)==48
expanded=lambda rows:{ref:{k:v for k,v in row.items() if k!='Designator'} for row in rows for ref in row['Designator'].split(',')}
b=expanded(before);a=expanded(after);assert set(a)==set(b) and len(a)==83;changes=[]
for ref in a:
 row=dict(a[ref])
 if ref in M:
  assert row['Footprint']==M[ref]['after'].split(':')[1];assert b[ref]['Footprint']==M[ref]['before'].split(':')[1];changes.append({'ref':ref,'before':b[ref],'after':row.copy()});row['Footprint']=M[ref]['before'].split(':')[1]
 assert row==b[ref],ref
assert set(q['ref'] for q in changes)==set(M)
assert 'J1' not in a and 'J6' in a
assert sha(C/'hardware/nexus-style-fc.kicad_pcb')==H
result={'status':'PASS actual native WIP BOM/CPL; CPL byte-exact, only five approved BOM footprint identifiers change','board_sha256':H,'source_board_sha256':sha(S/'hardware/nexus-style-fc.kicad_pcb'),'exporter_sha256':sha(C/'tools/export_fab.py'),'design_sha256':sha(C/'tools/design.py'),'machine_part_count':83,'BOM_group_count':48,'CPL_sha256':sha(O/cpl),'BOM_sha256':sha(O/bom),'CPL_byte_identical_to_stage08':True,'BOM_exact_except_five_named_footprint_fields':True,'changes':changes,'J1_omitted_J6_mixed_retained':True,'qualification':'Diagnostic WIP only. No release CAM or assembly qualification.'};(O/'source-binding.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
